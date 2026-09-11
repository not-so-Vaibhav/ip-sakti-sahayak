"""Pydantic models for Citation-Constrained Generation (/query)."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CitationItem(BaseModel):
    chunk_id: str
    instrument_name: str
    section_number: Optional[str] = None
    parent_section_label: Optional[str] = None
    authority_level: str = "primary_law"
    source_url: str = ""
    text_snippet: str = ""
    rank_position: int = 1
    retrieval_score: float = 0.0


class QueryRequest(BaseModel):
    query_text: str
    jurisdiction: str = "india"
    formulation_category: str
    language: str = "en"
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    top_k: int = 8


class QueryResponse(BaseModel):
    query_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query_text: str
    jurisdiction: str
    formulation_category: str
    language: str = "en"
    answer: Optional[str] = None
    citations: List[CitationItem] = Field(default_factory=list)
    confidence_score: float = 0.0
    abstained: bool = False
    abstention_reason: Optional[str] = None
    escalation_offered: bool = False
    generation_attempts: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
