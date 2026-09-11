"""IP Investigation Pipeline API Route (/investigate).

Orchestrates the complete investigation flow:
Formulation Extraction → Multi-Source Search → Comparison → Risk Assessment → Report.
"""

import logging
import uuid

from fastapi import APIRouter, HTTPException, status

from backend.app.investigation.comparator import comparator_service
from backend.app.investigation.evidence_orchestrator import evidence_orchestrator
from backend.app.investigation.extractor import get_default_extractor
from backend.app.investigation.models import (
    InvestigateRequest,
    InvestigateResponse,
    InvestigationCase,
    InvestigationStatus,
)
from backend.app.investigation.report_generator import report_generator_service
from backend.app.investigation.risk_assessor import risk_assessor_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/investigate", tags=["investigation"])

# Singleton extractor
extractor = get_default_extractor()


@router.post("", response_model=InvestigateResponse, summary="Run full IP investigation pipeline")
async def run_investigation(request: InvestigateRequest) -> InvestigateResponse:
    """
    Complete IP investigation pipeline:

    1. Extract structured formulation from free-text description
    2. Fan-out multi-source evidence search (patents, research, TK, regulations)
    3. Build element-wise comparison matrix
    4. Generate multi-dimensional risk assessment
    5. Render investigation dossier report

    Returns the full InvestigationCase with all phase outputs.
    """
    phases_completed = []
    case = InvestigationCase(
        case_id=str(uuid.uuid4()),
        language=request.language,
        jurisdiction=request.jurisdiction,
        classification_category=request.formulation_category,
        status=InvestigationStatus.EXTRACTING,
    )

    try:
        # Phase 1: Formulation Extraction
        logger.info(f"[Investigation {case.case_id}] Phase 1: Extracting formulation...")
        case.formulation = extractor.extract(
            request.formulation_description,
            language=request.language,
        )
        phases_completed.append("extraction")
        logger.info(
            f"[Investigation {case.case_id}] Extracted: "
            f"{len(case.formulation.ingredients)} ingredients, "
            f"{len(case.formulation.processes)} processes, "
            f"{len(case.formulation.intended_uses)} uses"
        )

        # Phase 2: Multi-Source Evidence Search
        case.status = InvestigationStatus.SEARCHING
        logger.info(f"[Investigation {case.case_id}] Phase 2: Searching evidence sources...")
        case.evidence_sources = await evidence_orchestrator.search_all_sources(
            formulation=case.formulation,
            jurisdiction=request.jurisdiction,
            formulation_category=request.formulation_category,
        )
        phases_completed.append("search")
        logger.info(
            f"[Investigation {case.case_id}] Found {len(case.evidence_sources)} evidence sources"
        )

        # Phase 3: Element-Wise Comparison
        case.status = InvestigationStatus.COMPARING
        logger.info(f"[Investigation {case.case_id}] Phase 3: Building comparison matrix...")
        case.comparison_matrix = comparator_service.build_comparison(
            formulation=case.formulation,
            evidence_sources=case.evidence_sources,
        )
        phases_completed.append("comparison")

        # Phase 4: Regulatory Analysis (reuse existing /query pipeline internally)
        regulatory_text = None
        try:
            from backend.app.retrieval.service import retrieval_service
            from backend.app.generation.generator import get_default_generator

            query_parts = [ing.name for ing in case.formulation.ingredients[:3]]
            query_text = (
                f"What are the IP and regulatory requirements for a {request.formulation_category} "
                f"formulation containing {', '.join(query_parts)}?"
            )

            retrieval_res = retrieval_service.retrieve(
                query_text=query_text,
                jurisdiction=request.jurisdiction,
                formulation_category=request.formulation_category,
                top_k=5,
                language=request.language,
            )

            if not retrieval_res.abstained and retrieval_res.chunks:
                gen = get_default_generator()
                answer, _, gen_abstained, _, _ = gen.generate_answer(
                    query_text=query_text,
                    jurisdiction=request.jurisdiction,
                    formulation_category=request.formulation_category,
                    retrieved_chunks=retrieval_res.chunks,
                    language=request.language,
                    confidence_score=retrieval_res.confidence_score,
                )
                if not gen_abstained and answer:
                    regulatory_text = answer
        except Exception as e:
            logger.warning(f"[Investigation {case.case_id}] Regulatory analysis skipped: {e}")

        case.regulatory_analysis = regulatory_text

        # Phase 5: Risk Assessment
        case.status = InvestigationStatus.ASSESSING
        logger.info(f"[Investigation {case.case_id}] Phase 4: Assessing risk...")
        case.risk_assessment = risk_assessor_service.assess(
            comparison=case.comparison_matrix,
            evidence=case.evidence_sources,
            category=request.formulation_category,
            regulatory_analysis=regulatory_text,
        )
        phases_completed.append("assessment")

        # Phase 6: Report Generation
        logger.info(f"[Investigation {case.case_id}] Phase 5: Generating report...")
        case.report_markdown = report_generator_service.render(case)
        phases_completed.append("report")

        case.status = InvestigationStatus.COMPLETE
        logger.info(f"[Investigation {case.case_id}] ✅ Complete!")

        return InvestigateResponse(
            case=case,
            phases_completed=phases_completed,
            current_phase="complete",
        )

    except Exception as e:
        logger.exception(f"[Investigation {case.case_id}] Pipeline error at {case.status}")
        case.status = InvestigationStatus.ERROR

        # Return partial results
        return InvestigateResponse(
            case=case,
            phases_completed=phases_completed,
            current_phase=f"error: {str(e)}",
        )
