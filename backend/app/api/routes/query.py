"""Main RAG Pipeline API Route (/query).

Orchestrates Phase 2 Hybrid Retrieval, Phase 2 Abstention Bypass, Citation-Constrained Generation,
and Supabase Audit Logging per schema_mvp.sql.
"""

import logging
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, status

from backend.app.db.supabase_client import supabase_manager
from backend.app.generation.generator import CitationConstrainedGenerator, get_default_generator
from backend.app.generation.models import QueryRequest, QueryResponse
from backend.app.retrieval.service import retrieval_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["query"])

# Default generator instance
generator = get_default_generator()


@router.post("", response_model=QueryResponse, summary="Execute citation-constrained RAG query")
async def execute_query(request: QueryRequest) -> QueryResponse:
    """
    Main RAG pipeline:
    1. Runs Phase 2 Hybrid Retrieval with hard metadata pre-filter (jurisdiction + category).
    2. If Phase 2 abstains (low confidence / 0 chunks): immediately bypasses LLM call and returns abstention.
    3. If retrieval passes: calls LLM with strict grounding prompt and multi-turn citation validation.
    4. Logs outcome to Supabase query_logs and query_citations.
    """
    query_id = str(uuid.uuid4())
    logger.info(
        f"Processing query '{request.query_text[:50]}...' "
        f"[jur={request.jurisdiction}, cat={request.formulation_category}, lang={request.language}]"
    )

    try:
        # Step 1: Execute Hybrid Retrieval with Hard Metadata Pre-Filtering
        retrieval_res = retrieval_service.retrieve(
            query_text=request.query_text,
            jurisdiction=request.jurisdiction,
            formulation_category=request.formulation_category,
            top_k=request.top_k,
            language=request.language,
        )

        # Step 2: Phase 2 Abstention Check (Immediate LLM Bypass)
        if retrieval_res.abstained:
            logger.info(
                f"Phase 2 retrieval triggered safe abstention (Score={retrieval_res.confidence_score}). "
                "Bypassing LLM call completely."
            )
            # Log abstained query to Supabase query_logs
            supabase_manager.record_query_log(
                query_id=query_id,
                query_text=request.query_text,
                language=request.language,
                jurisdiction_selected=request.jurisdiction,
                confidence_score=retrieval_res.confidence_score,
                abstained=True,
                escalated=False,
                answer_text=None,
                user_id=request.user_id,
                classification_session_id=request.session_id,
            )

            return QueryResponse(
                query_id=query_id,
                query_text=request.query_text,
                jurisdiction=request.jurisdiction,
                formulation_category=request.formulation_category,
                language=request.language,
                answer=None,
                citations=[],
                confidence_score=retrieval_res.confidence_score,
                abstained=True,
                abstention_reason=retrieval_res.abstention_reason,
                escalation_offered=True,
                generation_attempts=0,
            )

        # Step 3: Citation-Constrained Generation & Validation
        answer, citations, gen_abstained, gen_reason, attempts = generator.generate_answer(
            query_text=request.query_text,
            jurisdiction=request.jurisdiction,
            formulation_category=request.formulation_category,
            retrieved_chunks=retrieval_res.chunks,
            language=request.language,
            confidence_score=retrieval_res.confidence_score,
        )

        if gen_abstained:
            logger.warning(f"Generation layer forced terminal abstention: {gen_reason}")
            # Log generation-level abstention
            supabase_manager.record_query_log(
                query_id=query_id,
                query_text=request.query_text,
                language=request.language,
                jurisdiction_selected=request.jurisdiction,
                confidence_score=retrieval_res.confidence_score,
                abstained=True,
                escalated=False,
                answer_text=None,
                user_id=request.user_id,
                classification_session_id=request.session_id,
            )

            return QueryResponse(
                query_id=query_id,
                query_text=request.query_text,
                jurisdiction=request.jurisdiction,
                formulation_category=request.formulation_category,
                language=request.language,
                answer=None,
                citations=[],
                confidence_score=retrieval_res.confidence_score,
                abstained=True,
                abstention_reason=gen_reason,
                escalation_offered=True,
                generation_attempts=attempts,
            )

        # Step 4: Successful Grounded Response -> Log to Supabase query_logs & query_citations
        supabase_manager.record_query_log(
            query_id=query_id,
            query_text=request.query_text,
            language=request.language,
            jurisdiction_selected=request.jurisdiction,
            confidence_score=retrieval_res.confidence_score,
            abstained=False,
            escalated=False,
            answer_text=answer,
            user_id=request.user_id,
            classification_session_id=request.session_id,
        )

        citation_records = [
            {
                "id": str(uuid.uuid4()),
                "query_id": query_id,
                "chunk_id": c.chunk_id,
                "rank_position": c.rank_position,
                "retrieval_score": c.retrieval_score,
            }
            for c in citations
        ]
        supabase_manager.record_query_citations(citation_records)

        return QueryResponse(
            query_id=query_id,
            query_text=request.query_text,
            jurisdiction=request.jurisdiction,
            formulation_category=request.formulation_category,
            language=request.language,
            answer=answer,
            citations=citations,
            confidence_score=retrieval_res.confidence_score,
            abstained=False,
            abstention_reason=None,
            escalation_offered=False,
            generation_attempts=attempts,
        )

    except Exception as e:
        logger.exception("Error executing /query endpoint")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query execution error: {str(e)}",
        )
