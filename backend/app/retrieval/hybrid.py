"""Hybrid Retrieval Engine combining Dense Vectors and Sparse BM25 with Metadata Pre-Filtering."""

import logging
from typing import Dict, List, Optional, Set
from qdrant_client import models

from backend.app.config import settings
from backend.app.db.qdrant_client import QdrantManager, qdrant_manager
from backend.app.ingestion.embedder import MultilingualEmbedder, get_default_embedder
from backend.app.retrieval.bm25 import BM25Index, bm25_index
from backend.app.retrieval.confidence import ConfidenceEvaluator
from backend.app.retrieval.models import (
    RetrievalQuery,
    RetrievalResult,
    RetrievedChunk,
)

logger = logging.getLogger(__name__)


class HybridRetriever:
    """Orchestrates metadata pre-filtering, dense embedding search, BM25 sparse search, and confidence evaluation."""

    def __init__(
        self,
        embedder: Optional[MultilingualEmbedder] = None,
        qdrant: Optional[QdrantManager] = None,
        sparse_index: Optional[BM25Index] = None,
        dense_weight: Optional[float] = None,
        sparse_weight: Optional[float] = None,
        confidence_threshold: Optional[float] = None,
    ):
        self.embedder = embedder or get_default_embedder()
        self.qdrant = qdrant or qdrant_manager
        self.bm25 = sparse_index or bm25_index
        self.dense_weight = dense_weight if dense_weight is not None else settings.hybrid_dense_weight
        self.sparse_weight = sparse_weight if sparse_weight is not None else settings.hybrid_sparse_weight
        self.confidence_evaluator = ConfidenceEvaluator(threshold=confidence_threshold)
        self._in_memory_corpus: Dict[str, Dict] = {}

    def register_in_memory_chunk(self, chunk_data: Dict) -> None:
        """Register a chunk for in-memory retrieval when Qdrant is in offline/test mode."""
        cid = chunk_data.get("chunk_id") or str(chunk_data.get("id"))
        self._in_memory_corpus[cid] = chunk_data
        self.bm25.add_chunks([chunk_data])

    def clear_in_memory_corpus(self) -> None:
        self._in_memory_corpus.clear()
        self.bm25.clear()

    def refresh_index(self) -> int:
        """
        Refresh/hydrate in-memory BM25 index and chunk cache from active storage.
        """
        count = 0
        if self.qdrant.is_healthy():
            try:
                # Scroll all active points from Qdrant
                res, _ = self.qdrant.client.scroll(
                    collection_name=self.qdrant.collection_name,
                    limit=1000,
                    with_payload=True,
                    with_vectors=False,
                )
                chunks_to_index = []
                for pt in res:
                    payload = pt.payload or {}
                    payload["chunk_id"] = pt.id
                    self._in_memory_corpus[pt.id] = payload
                    chunks_to_index.append(payload)
                self.bm25.add_chunks(chunks_to_index)
                count = len(chunks_to_index)
                logger.info(f"Refreshed BM25 index with {count} chunks from Qdrant.")
            except Exception as e:
                logger.warning(f"Could not refresh from Qdrant: {e}")
        return count or len(self._in_memory_corpus)

    def _build_qdrant_filter(self, jurisdiction: str, formulation_category: str) -> models.Filter:
        """
        Build hard metadata pre-filter for Qdrant BEFORE ranking:
        1. jurisdiction == target_jurisdiction
        2. formulation_category_relevance CONTAINS target_category OR 'all'
        """
        must_conditions = [
            models.FieldCondition(
                key="jurisdiction",
                match=models.MatchValue(value=jurisdiction.lower()),
            ),
            models.FieldCondition(
                key="formulation_category_relevance",
                match=models.MatchAny(any=[formulation_category.lower(), "all"]),
            ),
        ]
        return models.Filter(must=must_conditions)

    def _filter_in_memory_candidates(self, jurisdiction: str, formulation_category: str) -> List[Dict]:
        """Apply the hard metadata pre-filter across the in-memory corpus."""
        target_jur = jurisdiction.lower()
        target_cat = formulation_category.lower()

        survivors = []
        for cid, data in self._in_memory_corpus.items():
            jur = (data.get("jurisdiction") or "").lower()
            rel_list = [r.lower() for r in (data.get("formulation_category_relevance") or [])]

            if jur == target_jur and (target_cat in rel_list or "all" in rel_list):
                survivors.append(data)
        return survivors

    def retrieve(self, query: RetrievalQuery) -> RetrievalResult:
        """
        Executes hybrid retrieval:
        1. Hard metadata pre-filtering on jurisdiction and formulation_category.
        2. Dense vector search via embedder.
        3. Sparse BM25 search across full filtered candidate set.
        4. Weighted combination.
        5. Confidence scoring & abstention check.
        """
        jurisdiction = query.jurisdiction.lower()
        formulation_category = query.formulation_category.lower()
        top_k = query.top_k

        # 1. Pre-filtered dense search & candidate discovery
        dense_scores: Dict[str, float] = {}
        candidate_payloads: Dict[str, Dict] = {}

        use_qdrant = self.qdrant.is_healthy()
        query_vector = self.embedder.embed_query(query.query_text)

        if use_qdrant:
            try:
                q_filter = self._build_qdrant_filter(jurisdiction, formulation_category)
                # Search dense vectors with hard metadata pre-filter applied in Qdrant
                search_res = self.qdrant.client.search(
                    collection_name=self.qdrant.collection_name,
                    query_vector=query_vector,
                    query_filter=q_filter,
                    limit=max(50, top_k * 5),
                    with_payload=True,
                )
                for pt in search_res:
                    # Qdrant cosine distance score is in [-1, 1], normalize to [0, 1]
                    norm_dense = max(0.0, min(1.0, (pt.score + 1.0) / 2.0 if pt.score <= 1.0 else pt.score))
                    dense_scores[pt.id] = norm_dense
                    candidate_payloads[pt.id] = pt.payload or {}
            except Exception as e:
                logger.warning(f"Qdrant search error ({e}); using local memory candidates.")
                use_qdrant = False

        if not use_qdrant:
            # In-memory candidate filtering
            filtered_candidates = self._filter_in_memory_candidates(jurisdiction, formulation_category)
            if filtered_candidates:
                # Compute dense cosine similarities in memory
                import numpy as np
                q_vec = np.array(query_vector, dtype=float)
                q_norm = np.linalg.norm(q_vec) or 1.0

                texts = [c.get("text_content", "") for c in filtered_candidates]
                doc_vectors = self.embedder.embed_passages(texts)

                for i, c in enumerate(filtered_candidates):
                    cid = c.get("chunk_id") or str(c.get("id"))
                    d_vec = np.array(doc_vectors[i], dtype=float)
                    d_norm = np.linalg.norm(d_vec) or 1.0
                    cos_sim = float(np.dot(q_vec, d_vec) / (q_norm * d_norm))
                    norm_dense = max(0.0, min(1.0, (cos_sim + 1.0) / 2.0))
                    dense_scores[cid] = norm_dense
                    candidate_payloads[cid] = c

        candidate_ids = set(candidate_payloads.keys())

        # If zero chunks survived the metadata pre-filter, immediately abstain
        if not candidate_ids:
            return RetrievalResult(
                query_text=query.query_text,
                jurisdiction=query.jurisdiction,
                formulation_category=query.formulation_category,
                language=query.language,
                chunks=[],
                confidence_score=0.0,
                abstained=True,
                abstention_reason=f"No legal instruments or clauses found in jurisdiction '{jurisdiction}' applicable to '{formulation_category}'.",
                corroborating_chunks_count=0,
                top_score=0.0,
            )

        # 2. Sparse BM25 search across ALL pre-filtered candidate chunks
        sparse_scores = self.bm25.search(
            query=query.query_text,
            candidate_chunk_ids=candidate_ids,
        )

        # 3. Combine dense and sparse scores
        retrieved_chunks: List[RetrievedChunk] = []
        for cid in candidate_ids:
            payload = candidate_payloads[cid]
            d_score = dense_scores.get(cid, 0.0)
            s_score = sparse_scores.get(cid, 0.0)
            combined = (self.dense_weight * d_score) + (self.sparse_weight * s_score)

            retrieved_chunks.append(
                RetrievedChunk(
                    chunk_id=cid,
                    document_id=payload.get("document_id"),
                    instrument_name=payload.get("instrument_name", "Unknown Instrument"),
                    jurisdiction=payload.get("jurisdiction", jurisdiction),
                    regime_category=payload.get("regime_category", "general"),
                    authority_level=payload.get("authority_level", "primary_law"),
                    section_number=payload.get("section_number"),
                    parent_section_label=payload.get("parent_section_label"),
                    text_content=payload.get("text_content", ""),
                    language=payload.get("language", query.language),
                    source_url=payload.get("source_url", ""),
                    formulation_category_relevance=payload.get("formulation_category_relevance", []),
                    dense_score=round(d_score, 4),
                    sparse_score=round(s_score, 4),
                    combined_score=round(combined, 4),
                )
            )

        # 4. Rank by combined score descending and take top_k
        retrieved_chunks.sort(key=lambda x: x.combined_score, reverse=True)
        top_chunks = retrieved_chunks[:top_k]

        # 5. Evaluate confidence score and safe abstention
        confidence, abstained, reason, corroborating_count, top_score = self.confidence_evaluator.evaluate(
            top_chunks
        )

        return RetrievalResult(
            query_text=query.query_text,
            jurisdiction=query.jurisdiction,
            formulation_category=query.formulation_category,
            language=query.language,
            chunks=top_chunks,
            confidence_score=confidence,
            abstained=abstained,
            abstention_reason=reason,
            corroborating_chunks_count=corroborating_count,
            top_score=top_score,
        )


def get_default_retriever() -> HybridRetriever:
    return HybridRetriever()
