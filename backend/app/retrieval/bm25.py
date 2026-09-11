"""In-Memory BM25 Sparse Search Engine for Legal and Regulatory Text.

Performs Okapi BM25 scoring with specialized tokenization for statutory clauses
(e.g., 'Section 3(p)', 'Rule 122E', 'Chapter IV-A'). Searches across full metadata-filtered candidate set.
"""

import math
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Set, Union


# Stop words that add noise to legal keyword matching
STOP_WORDS = {
    "the", "is", "at", "which", "on", "a", "an", "and", "or", "in", "of",
    "to", "for", "from", "under", "can", "i", "this", "that", "with", "by",
    "be", "it", "as", "are", "do", "does", "have", "has", "what", "how"
}


def tokenize_legal_text(text: str) -> List[str]:
    """
    Tokenizes legal text while preserving statutory clause patterns like '3(p)', '122e', '3(a)', 'sec. 6'.
    """
    if not text:
        return []

    text_lower = text.lower()

    # 1. Extract statutory clauses like '3(p)', '2(1)(j)', '122e', '3(a)'
    clauses = re.findall(r"\b\d+[a-z]?(?:\([a-z0-9]+\))+", text_lower)

    # 2. Extract standard alphanumeric words
    words = re.findall(r"\b[a-z0-9]+\b", text_lower)
    meaningful_words = [w for w in words if w not in STOP_WORDS]

    # 3. Sub-clause parts (e.g. '3(p)' yields '3p', '3', 'p')
    sub_parts = []
    for c in clauses:
        sub_parts.append(c.replace("(", "").replace(")", ""))
        parts = re.split(r"[()]", c)
        sub_parts.extend([p for p in parts if p and p not in STOP_WORDS])

    return list(set(clauses + meaningful_words + sub_parts))


class BM25Index:
    """Okapi BM25 Index for exact legal keyword matching."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_lengths: Dict[str, int] = {}
        self.doc_token_counts: Dict[str, Counter] = {}
        self.doc_metadata: Dict[str, Dict] = {}
        self.doc_freqs: Counter = Counter()  # term -> number of docs containing term
        self.num_docs: int = 0
        self.avg_doc_length: float = 0.0

    def clear(self) -> None:
        """Clear the in-memory index."""
        self.doc_lengths.clear()
        self.doc_token_counts.clear()
        self.doc_metadata.clear()
        self.doc_freqs.clear()
        self.num_docs = 0
        self.avg_doc_length = 0.0

    def add_chunks(self, chunks: List[Any]) -> None:
        """Index or update statutory chunks in the BM25 index."""
        for chunk in chunks:
            if hasattr(chunk, "chunk_id"):
                chunk_id = getattr(chunk, "chunk_id")
                instrument = getattr(chunk, "instrument_name", "")
                sec_num = getattr(chunk, "section_number", "")
                parent_sec = getattr(chunk, "parent_section_label", "")
                content = getattr(chunk, "text_content", "")
                text = f"{instrument} {sec_num or ''} {parent_sec or ''} {content}"
            elif isinstance(chunk, dict):
                chunk_id = chunk.get("chunk_id") or str(chunk.get("id"))
                text = f"{chunk.get('instrument_name', '')} {chunk.get('section_number', '')} {chunk.get('parent_section_label', '')} {chunk.get('text_content', '')}"
                sec_num = chunk.get("section_number")
            else:
                continue

            if not chunk_id:
                continue

            # If chunk already indexed, remove its stats first
            if chunk_id in self.doc_token_counts:
                self._remove_chunk(chunk_id)

            tokens = tokenize_legal_text(text)
            token_counts = Counter(tokens)
            doc_len = len(tokens)

            self.doc_lengths[chunk_id] = doc_len
            self.doc_token_counts[chunk_id] = token_counts
            self.doc_metadata[chunk_id] = {"section_number": sec_num}

            for term in token_counts.keys():
                self.doc_freqs[term] += 1

        self.num_docs = len(self.doc_lengths)
        self.avg_doc_length = (
            sum(self.doc_lengths.values()) / self.num_docs if self.num_docs > 0 else 0.0
        )

    def _remove_chunk(self, chunk_id: str) -> None:
        if chunk_id in self.doc_token_counts:
            for term in self.doc_token_counts[chunk_id].keys():
                self.doc_freqs[term] -= 1
                if self.doc_freqs[term] <= 0:
                    del self.doc_freqs[term]
            del self.doc_token_counts[chunk_id]
            del self.doc_lengths[chunk_id]
            if chunk_id in self.doc_metadata:
                del self.doc_metadata[chunk_id]

    def _compute_idf(self, term: str) -> float:
        n = self.doc_freqs.get(term, 0)
        if n == 0:
            return 0.0
        # Standard Okapi BM25 IDF with smoothing
        return math.log(1.0 + (self.num_docs - n + 0.5) / (n + 0.5))

    def search(
        self,
        query: str,
        candidate_chunk_ids: Optional[Set[str]] = None,
        top_k: Optional[int] = None,
    ) -> Dict[str, float]:
        """
        Calculates normalized BM25 scores for candidates passing the metadata pre-filter.
        Returns a mapping of {chunk_id: normalized_score in [0, 1]}.
        """
        if self.num_docs == 0 or not query:
            return {}

        query_tokens = tokenize_legal_text(query)
        if not query_tokens:
            return {}

        target_ids = (
            [cid for cid in candidate_chunk_ids if cid in self.doc_token_counts]
            if candidate_chunk_ids is not None
            else list(self.doc_token_counts.keys())
        )

        if not target_ids:
            return {}

        raw_scores: Dict[str, float] = {}
        for chunk_id in target_ids:
            doc_len = self.doc_lengths[chunk_id]
            token_counts = self.doc_token_counts[chunk_id]
            score = 0.0

            for q_term in query_tokens:
                freq = token_counts.get(q_term, 0)
                if freq > 0:
                    idf = self._compute_idf(q_term)
                    denom = freq + self.k1 * (1.0 - self.b + self.b * (doc_len / (self.avg_doc_length or 1.0)))
                    term_score = idf * (freq * (self.k1 + 1.0)) / denom
                    score += term_score

            # Exact section number match boost
            sec_num = (self.doc_metadata.get(chunk_id, {}).get("section_number") or "").strip().lower()
            if sec_num and sec_num in query.lower():
                score += 3.0

            raw_scores[chunk_id] = score

        max_score = max(raw_scores.values()) if raw_scores else 0.0
        if max_score <= 0.0:
            return {cid: 0.0 for cid in target_ids}

        normalized = {cid: round(min(1.0, score / max_score), 4) for cid, score in raw_scores.items()}

        if top_k is not None:
            sorted_items = sorted(normalized.items(), key=lambda x: x[1], reverse=True)[:top_k]
            return dict(sorted_items)

        return normalized


# Singleton BM25 index instance
bm25_index = BM25Index()
