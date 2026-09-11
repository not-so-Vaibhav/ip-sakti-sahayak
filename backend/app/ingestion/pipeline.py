"""Ingestion Pipeline orchestrating Chunker, Embedder, Postgres, and Qdrant."""

import logging
from typing import Any, Dict, List, Optional
from qdrant_client import models

from backend.app.config import settings
from backend.app.db.qdrant_client import QdrantManager, qdrant_manager
from backend.app.db.supabase_client import SupabaseManager, supabase_manager
from backend.app.ingestion.chunker import LegalDocumentChunker, RawInstrumentDocument, SectionChunk
from backend.app.ingestion.embedder import MultilingualEmbedder, get_default_embedder
from backend.app.retrieval.bm25 import BM25Index, bm25_index

logger = logging.getLogger(__name__)


class IngestionPipeline:
    def __init__(
        self,
        embedder: Optional[MultilingualEmbedder] = None,
        qdrant: Optional[QdrantManager] = None,
        supabase: Optional[SupabaseManager] = None,
        chunker: Optional[LegalDocumentChunker] = None,
        sparse_index: Optional[BM25Index] = None,
    ):
        self.embedder = embedder or get_default_embedder()
        self.qdrant = qdrant or qdrant_manager
        self.supabase = supabase or supabase_manager
        self.chunker = chunker or LegalDocumentChunker()
        self.sparse_index = sparse_index or bm25_index

    def ingest_document(
        self,
        doc: RawInstrumentDocument,
        sync_to_qdrant: bool = True,
        sync_to_supabase: bool = True,
    ) -> Dict[str, Any]:
        """
        Ingests a raw legal instrument through chunking, Supabase mirroring,
        Qdrant vector upsert, and BM25 index updating.
        """
        logger.info(f"Ingesting document: '{doc.instrument_name}' ({doc.jurisdiction})")

        # 1. Chunk document
        chunks: List[SectionChunk] = self.chunker.chunk_document(doc)
        logger.info(f"Created {len(chunks)} statutory chunks for '{doc.instrument_name}'.")

        # 2. Immediately update in-memory BM25 index (Lifecycle Refresh Hook)
        self.sparse_index.add_chunks(chunks)

        # 3. Mirror to Postgres / Supabase
        doc_id = doc.id
        if sync_to_supabase and self.supabase.is_connected:
            doc_id = self.supabase.upsert_corpus_document(
                instrument_name=doc.instrument_name,
                jurisdiction=doc.jurisdiction,
                regime_category=doc.regime_category,
                authority_level=doc.authority_level,
                source_url=doc.source_url,
                effective_date=doc.effective_date,
                last_amended_date=doc.last_amended_date,
                document_id=doc.id,
            ) or doc.id

            db_chunks = [
                {
                    "chunk_id": chunk.chunk_id,
                    "document_id": doc_id,
                    "section_number": chunk.section_number,
                    "parent_section_label": chunk.parent_section_label,
                    "text_content": chunk.text_content,
                    "language": chunk.language,
                    "formulation_category_relevance": chunk.formulation_category_relevance,
                    "embedding_model_version": self.embedder.model_name,
                    "qdrant_point_synced": False,
                }
                for chunk in chunks
            ]
            self.supabase.insert_corpus_chunks(db_chunks)

        # 3. Generate embeddings & Upsert to Qdrant
        qdrant_synced = False
        if sync_to_qdrant and chunks:
            try:
                # Dynamically ensure collection with active embedder dimension
                vector_dim = self.embedder.dimension
                logger.info(f"Ensuring Qdrant collection with dynamic dimension {vector_dim}...")
                self.qdrant.ensure_collection(vector_size=vector_dim)

                # Generate dense embeddings
                texts = [c.text_content for c in chunks]
                embeddings = self.embedder.embed_passages(texts)

                # Prepare Qdrant points
                points: List[models.PointStruct] = []
                for i, chunk in enumerate(chunks):
                    point_payload = {
                        "chunk_id": chunk.chunk_id,
                        "document_id": doc_id,
                        "instrument_name": chunk.instrument_name,
                        "jurisdiction": chunk.jurisdiction.lower(),
                        "regime_category": chunk.regime_category.lower(),
                        "authority_level": chunk.authority_level.lower(),
                        "section_number": chunk.section_number,
                        "parent_section_label": chunk.parent_section_label,
                        "formulation_category_relevance": chunk.formulation_category_relevance,
                        "language": chunk.language,
                        "source_url": chunk.source_url,
                        "text_content": chunk.text_content,
                    }
                    points.append(
                        models.PointStruct(
                            id=chunk.chunk_id,
                            vector=embeddings[i],
                            payload=point_payload,
                        )
                    )

                self.qdrant.upsert_chunks(points)
                qdrant_synced = True

                # Mark synced in Postgres
                if sync_to_supabase and self.supabase.is_connected:
                    chunk_ids = [c.chunk_id for c in chunks]
                    self.supabase.mark_chunks_synced(chunk_ids)

            except Exception as e:
                logger.warning(
                    f"Qdrant sync skipped or failed (ensure 'docker compose up -d' is running): {e}"
                )

        return {
            "document_id": doc_id,
            "instrument_name": doc.instrument_name,
            "chunks_count": len(chunks),
            "qdrant_synced": qdrant_synced,
            "embedding_model": self.embedder.model_name,
            "vector_dimension": self.embedder.dimension,
            "chunk_ids": [c.chunk_id for c in chunks],
        }

    def ingest_batch(self, docs: List[RawInstrumentDocument]) -> List[Dict[str, Any]]:
        """Ingests a batch of documents."""
        results = []
        for doc in docs:
            res = self.ingest_document(doc)
            results.append(res)
        return results
