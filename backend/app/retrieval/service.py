"""Retrieval Service coordinating Hybrid Search, BM25 Index, and Ingestion."""

import logging
from typing import Optional

from backend.app.retrieval.hybrid import HybridRetriever, get_default_retriever
from backend.app.retrieval.models import RetrievalQuery, RetrievalResult

logger = logging.getLogger(__name__)


class RetrievalService:
    def __init__(self, retriever: Optional[HybridRetriever] = None):
        self.retriever = retriever or get_default_retriever()

    def retrieve(
        self,
        query_text: str,
        jurisdiction: str = "india",
        formulation_category: str = "classical_generic",
        top_k: Optional[int] = None,
        language: str = "en",
    ) -> RetrievalResult:
        """High-level retrieval interface."""
        from backend.app.config import settings
        query = RetrievalQuery(
            query_text=query_text,
            jurisdiction=jurisdiction,
            formulation_category=formulation_category,
            top_k=top_k if top_k is not None else settings.top_k_retrieval,
            language=language,
        )
        return self.retriever.retrieve(query)

    def refresh(self) -> int:
        """Refreshes the retrieval index from storage."""
        return self.retriever.refresh_index()


retrieval_service = RetrievalService()
