"""Pydantic models for Hybrid Retrieval and Confidence Scoring."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RetrievalQuery(BaseModel):
    query_text: str
    jurisdiction: str = "india"
    formulation_category: str
    language: str = "en"
    top_k: int = 5


class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: Optional[str] = None
    instrument_name: str
    jurisdiction: str
    regime_category: str
    authority_level: str
    section_number: Optional[str] = None
    parent_section_label: Optional[str] = None
    text_content: str
    language: str = "en"
    source_url: str
    formulation_category_relevance: List[str] = Field(default_factory=list)
    dense_score: float = 0.0
    sparse_score: float = 0.0
    combined_score: float = 0.0


class RetrievalResult(BaseModel):
    query_text: str
    jurisdiction: str
    formulation_category: str
    language: str = "en"
    chunks: List[RetrievedChunk] = Field(default_factory=list)
    confidence_score: float = 0.0
    abstained: bool = False
    abstention_reason: Optional[str] = None
    corroborating_chunks_count: int = 0
    top_score: float = 0.0
