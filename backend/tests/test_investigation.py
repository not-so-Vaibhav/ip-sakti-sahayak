"""Unit and integration tests for IP Investigation Pipeline."""

import pytest
from fastapi.testclient import TestClient

from backend.app.investigation.comparator import comparator_service
from backend.app.investigation.evidence_orchestrator import evidence_orchestrator
from backend.app.investigation.extractor import FormulationExtractor
from backend.app.investigation.models import (
    EvidenceSource,
    FormulationElement,
    InvestigationCase,
    InvestigationStatus,
    StructuredFormulation,
)
from backend.app.investigation.patent_search import patent_search_service
from backend.app.investigation.report_generator import report_generator_service
from backend.app.investigation.research_search import research_search_service
from backend.app.investigation.risk_assessor import risk_assessor_service
from backend.app.investigation.tk_formulation_search import tk_search_service
from backend.app.main import app

client = TestClient(app)


def test_extractor_regex_fallback():
    """Verify that regex fallback correctly extracts ingredients, ratios, and uses."""
    extractor = FormulationExtractor()
    sample_text = (
        "Turmeric and Neem powder, 3:1 ratio, steam extraction, "
        "churna tablet for inflammation and wound healing"
    )
    extracted = extractor._regex_fallback(sample_text)

    # Check extracted ingredients
    ing_names = [i["name"].lower() for i in extracted["ingredients"]]
    assert any("turmeric" in name for name in ing_names)
    assert any("neem" in name for name in ing_names)

    # Check ratio
    assert len(extracted["ratios"]) > 0
    assert any("3:1" in (r.get("value") or "") for r in extracted["ratios"])

    # Check processes
    proc_names = [p["name"] for p in extracted["processes"]]
    assert "steam extraction" in proc_names

    # Check dosage forms
    form_names = [d["name"] for d in extracted["dosage_forms"]]
    assert "churna" in form_names or "tablet" in form_names

    # Check intended uses
    use_names = [u["name"].lower() for u in extracted["intended_uses"]]
    assert any("inflammation" in u or "wound" in u for u in use_names)


def test_extractor_structured_output():
    """Verify StructuredFormulation output format."""
    extractor = FormulationExtractor()
    formulation = extractor.extract("Turmeric and Black Pepper extract 10:1 for joint pain")
    assert isinstance(formulation, StructuredFormulation)
    assert len(formulation.ingredients) >= 1
    assert formulation.raw_input == "Turmeric and Black Pepper extract 10:1 for joint pain"


def test_patent_search_matches():
    """Verify patent search service finds relevant seed patents."""
    formulation = StructuredFormulation(
        raw_input="Turmeric and neem formulation",
        ingredients=[
            FormulationElement(name="Turmeric", element_type="ingredient"),
            FormulationElement(name="Neem", element_type="ingredient"),
        ],
    )
    results = patent_search_service._search_seed_data(formulation, jurisdiction="india")
    assert len(results) > 0
    assert any(
        "turmeric" in r.title.lower() or "curcuma" in r.title.lower()
        or "neem" in r.title.lower() or "azadirachta" in r.title.lower()
        for r in results
    )
    assert results[0].source_type == "patent"
    assert results[0].relevance_score > 0


def test_tk_formulation_search():
    """Verify traditional knowledge and classical formulation search."""
    formulation = StructuredFormulation(
        raw_input="Classical Haridra formulation",
        ingredients=[
            FormulationElement(name="Haridra", element_type="ingredient"),
            FormulationElement(name="Nimba", element_type="ingredient"),
        ],
    )
    results = tk_search_service._search_seed_formulations(formulation)
    assert len(results) > 0
    assert any(r.source_type in ("tk_source", "formulation") for r in results)


@pytest.mark.asyncio
async def test_evidence_orchestrator_search():
    """Verify evidence orchestrator fans out and returns deduplicated sources."""
    formulation = StructuredFormulation(
        raw_input="Curcumin extract with piperine for inflammation",
        ingredients=[
            FormulationElement(name="Curcumin", element_type="ingredient"),
            FormulationElement(name="Piperine", element_type="ingredient"),
        ],
    )
    sources = await evidence_orchestrator.search_all_sources(
        formulation=formulation,
        jurisdiction="india",
        formulation_category="classical_generic",
    )
    assert len(sources) > 0
    assert any(s.source_type in ("patent", "formulation", "tk_source", "research_paper") for s in sources)


def test_comparator_build_matrix():
    """Verify comparison matrix generation and element matching."""
    formulation = StructuredFormulation(
        raw_input="Turmeric and Neem formulation",
        ingredients=[
            FormulationElement(name="Turmeric", element_type="ingredient"),
            FormulationElement(name="Neem", element_type="ingredient"),
        ],
        processes=[
            FormulationElement(name="steam distillation", element_type="process"),
        ],
    )

    evidence_sources = [
        EvidenceSource(
            source_id="pat_1",
            source_type="patent",
            title="Extraction of Turmeric using steam distillation",
            relevant_text="A method comprising Turmeric and steam distillation for anti-inflammatory use.",
            extracted_elements=[
                FormulationElement(name="Turmeric", element_type="ingredient"),
                FormulationElement(name="steam distillation", element_type="process"),
            ],
            relevance_score=0.85,
        ),
        EvidenceSource(
            source_id="tk_1",
            source_type="tk_source",
            title="Haridra and Nimba in Charaka Samhita",
            relevant_text="Haridra combined with Nimba for kustha roga.",
            extracted_elements=[
                FormulationElement(name="Haridra", element_type="ingredient"),
                FormulationElement(name="Nimba", element_type="ingredient"),
            ],
            relevance_score=0.75,
        ),
    ]

    matrix = comparator_service.build_comparison(formulation, evidence_sources)
    assert matrix is not None
    assert len(matrix.comparisons) >= 2
    assert "pat_1" in matrix.overlap_scores
    assert matrix.overlap_scores["pat_1"] > 0


def test_risk_assessor_full_assessment():
    """Verify multi-dimensional risk assessment scoring and logic."""
    formulation = StructuredFormulation(
        raw_input="Turmeric and Neem churna",
        ingredients=[
            FormulationElement(name="Turmeric", element_type="ingredient"),
            FormulationElement(name="Neem", element_type="ingredient"),
        ],
    )
    evidence_sources = [
        EvidenceSource(
            source_id="tk_1",
            source_type="tk_source",
            title="Charaka Samhita Haridra Lepa",
            relevant_text="Classical topical formulation using Haridra and Nimba.",
            extracted_elements=[
                FormulationElement(name="Turmeric", element_type="ingredient"),
                FormulationElement(name="Neem", element_type="ingredient"),
            ],
            relevance_score=0.9,
        ),
    ]
    matrix = comparator_service.build_comparison(formulation, evidence_sources)

    assessment = risk_assessor_service.assess(
        comparison=matrix,
        evidence=evidence_sources,
        category="classical_generic",
    )

    assert assessment is not None
    assert len(assessment.dimensions) == 5

    dim_names = [d.dimension for d in assessment.dimensions]
    assert "novelty_risk" in dim_names
    assert "tk_overlap" in dim_names
    assert "regulatory_complexity" in dim_names
    assert "abs_compliance" in dim_names
    assert "prior_art_exposure" in dim_names

    tk_dim = next(d for d in assessment.dimensions if d.dimension == "tk_overlap")
    assert tk_dim.score >= 0.5
    assert assessment.overall_risk in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert len(assessment.recommended_actions) > 0


def test_report_generator_markdown():
    """Verify generated investigation report markdown formatting."""
    case = InvestigationCase(
        case_id="test_case_123",
        language="en",
        jurisdiction="india",
        classification_category="classical_generic",
        status=InvestigationStatus.COMPLETE,
        formulation=StructuredFormulation(
            raw_input="Turmeric and Neem powder 3:1",
            ingredients=[
                FormulationElement(name="Turmeric", element_type="ingredient"),
                FormulationElement(name="Neem", element_type="ingredient"),
            ],
            ratios=[FormulationElement(name="3:1", element_type="ratio", value="3:1")],
        ),
        evidence_sources=[
            EvidenceSource(
                source_id="src_1",
                source_type="patent",
                title="Herbal Formulation for Skin Disorders",
                identifier="IN202141012345",
                relevance_score=0.82,
                relevant_text="Formulation comprising turmeric extract and neem oil.",
            ),
        ],
    )
    case.comparison_matrix = comparator_service.build_comparison(
        case.formulation, case.evidence_sources
    )
    case.risk_assessment = risk_assessor_service.assess(
        comparison=case.comparison_matrix,
        evidence=case.evidence_sources,
        category="classical_generic",
    )

    report_md = report_generator_service.render(case)
    assert report_md is not None
    assert "IP-SAKTI Sahayak" in report_md
    assert "1. Case Details" in report_md
    assert "2. Formulation Classification" in report_md
    assert "3. Structured Formulation" in report_md
    assert "4. Sources Searched" in report_md
    assert "5. Patent Findings" in report_md
    assert "8. Element-Wise Comparison Matrix" in report_md
    assert "9. Risk Assessment" in report_md
    assert "12. Recommended Next Actions" in report_md
    assert "13. Full Citation List" in report_md
    assert "Disclaimer" in report_md


def test_investigate_api_endpoint():
    """Verify /investigate API endpoint runs end-to-end and returns complete case."""
    payload = {
        "formulation_description": "Turmeric and Neem powder, 3:1 ratio, for inflammation and wound healing",
        "formulation_category": "classical_generic",
        "jurisdiction": "india",
        "language": "en",
    }
    response = client.post("/investigate", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "case" in data
    assert "phases_completed" in data

    case = data["case"]
    assert case["case_id"] is not None
    assert case["status"] == "complete"
    assert "extraction" in data["phases_completed"]
    assert "search" in data["phases_completed"]
    assert "comparison" in data["phases_completed"]
    assert "assessment" in data["phases_completed"]
    assert "report" in data["phases_completed"]

    assert case["formulation"] is not None
    assert len(case["formulation"]["ingredients"]) >= 2
    assert len(case["evidence_sources"]) > 0
    assert case["comparison_matrix"] is not None
    assert case["risk_assessment"] is not None
    assert len(case["risk_assessment"]["dimensions"]) == 5
    assert case["report_markdown"] is not None
    assert len(case["report_markdown"]) > 200
