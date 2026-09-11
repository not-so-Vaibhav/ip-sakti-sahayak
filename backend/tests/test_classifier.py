"""Unit tests for the Formulation Classifier Engine."""

import pytest
from pathlib import Path

from backend.app.classifier.engine import DecisionTreeEngine
from backend.app.classifier.models import FormulationCategoryCode, Language


@pytest.fixture
def engine():
    backend_root = Path(__file__).resolve().parent.parent
    tree_path = backend_root / "config" / "decision_tree.json"
    categories_path = backend_root / "config" / "formulation_categories_seed.json"
    return DecisionTreeEngine(tree_path=tree_path, categories_path=categories_path)


def test_load_and_validate_tree(engine):
    """Test that decision tree loads and passes DAG structural validation."""
    assert engine.tree.version == "1.0.0"
    assert engine.tree.start_node_id == "q1_classical_text_match"
    assert len(engine.tree.nodes) >= 6
    assert len(engine.categories_map) == 6


def test_classify_classical_generic(engine):
    """Path: q1 = yes -> classical_generic."""
    res = engine.evaluate_answers({"q1_classical_text_match": "yes"}, language=Language.EN)
    assert res.status == "completed"
    assert res.outcome is not None
    assert res.outcome.category_code == FormulationCategoryCode.CLASSICAL_GENERIC
    assert "Section 3(p)" in res.outcome.notes
    assert "Biological Diversity Act" in res.outcome.abs_guidance
    assert len(res.history) == 1


def test_classify_new_drug(engine):
    """Path: q1 = no, q2 = clinical_evidence -> new_non_classical_drug."""
    res = engine.evaluate_answers(
        {"q1_classical_text_match": "no", "q2_modification_type": "clinical_evidence"},
        language=Language.EN,
    )
    assert res.status == "completed"
    assert res.outcome is not None
    assert res.outcome.category_code == FormulationCategoryCode.NEW_NON_CLASSICAL_DRUG
    assert len(res.history) == 2


def test_classify_phytopharmaceutical(engine):
    """Path: q1 = no, q2 = phytopharmaceutical -> phytopharmaceutical."""
    res = engine.evaluate_answers(
        {"q1_classical_text_match": "no", "q2_modification_type": "phytopharmaceutical"},
        language=Language.EN,
    )
    assert res.status == "completed"
    assert res.outcome is not None
    assert res.outcome.category_code == FormulationCategoryCode.PHYTOPHARMACEUTICAL
    assert "Rule 122E" in res.outcome.notes


def test_classify_ayurveda_aahar(engine):
    """Path: q1 = no, q2 = intended_category, q3 = ayurveda_aahar -> ayurveda_aahar_nutraceutical."""
    res = engine.evaluate_answers(
        {
            "q1_classical_text_match": "no",
            "q2_modification_type": "intended_category",
            "q3_non_drug_intended_category": "ayurveda_aahar",
        },
        language=Language.EN,
    )
    assert res.status == "completed"
    assert res.outcome is not None
    assert res.outcome.category_code == FormulationCategoryCode.AYURVEDA_AAHAR_NUTRACEUTICAL
    assert "FSSAI" in res.outcome.notes


def test_classify_cosmetic(engine):
    """Path: q1 = no, q2 = intended_category, q3 = cosmetic -> cosmetic."""
    res = engine.evaluate_answers(
        {
            "q1_classical_text_match": "no",
            "q2_modification_type": "intended_category",
            "q3_non_drug_intended_category": "cosmetic",
        },
        language=Language.EN,
    )
    assert res.status == "completed"
    assert res.outcome is not None
    assert res.outcome.category_code == FormulationCategoryCode.COSMETIC


def test_classify_patent_or_proprietary(engine):
    """Path: q1 = no, q2 = intended_category, q3 = proprietary_medicine -> patent_or_proprietary."""
    res = engine.evaluate_answers(
        {
            "q1_classical_text_match": "no",
            "q2_modification_type": "intended_category",
            "q3_non_drug_intended_category": "proprietary_medicine",
        },
        language=Language.EN,
    )
    assert res.status == "completed"
    assert res.outcome is not None
    assert res.outcome.category_code == FormulationCategoryCode.PATENT_OR_PROPRIETARY


def test_step_by_step_interactive(engine):
    """Test interactive step by step traversal through nodes."""
    # Step 0: Start
    start_res = engine.get_start_result(language=Language.EN)
    assert start_res.status == "in_progress"
    assert start_res.current_question.node_id == "q1_classical_text_match"
    assert len(start_res.current_question.options) == 2

    # Step 1: Choose 'no'
    step1_res = engine.step(
        current_node_id="q1_classical_text_match",
        selected_option_id="no",
        language=Language.EN,
        history=start_res.history,
    )
    assert step1_res.status == "in_progress"
    assert step1_res.current_question.node_id == "q2_modification_type"
    assert len(step1_res.history) == 1

    # Step 2: Choose 'clinical_evidence'
    step2_res = engine.step(
        current_node_id="q2_modification_type",
        selected_option_id="clinical_evidence",
        language=Language.EN,
        history=step1_res.history,
    )
    assert step2_res.status == "completed"
    assert step2_res.outcome.category_code == FormulationCategoryCode.NEW_NON_CLASSICAL_DRUG
    assert len(step2_res.history) == 2


def test_hindi_localization(engine):
    """Test that Hindi mode returns Hindi text for questions, options, and outcomes."""
    res = engine.evaluate_answers({"q1_classical_text_match": "yes"}, language=Language.HI)
    assert res.status == "completed"
    assert res.outcome is not None
    assert "शास्त्रीय" in res.outcome.display_name
    assert "धारा 3(p)" in res.outcome.notes
    assert "जैव विविधता अधिनियम" in res.outcome.abs_guidance


def test_invalid_option_raises_error(engine):
    """Test that invalid option selection raises ValueError."""
    with pytest.raises(ValueError):
        engine.step(
            current_node_id="q1_classical_text_match",
            selected_option_id="invalid_choice_123",
        )


def test_incomplete_batch_answers(engine):
    """Passing partial answers returns next question in_progress."""
    res = engine.evaluate_answers({"q1_classical_text_match": "no"}, language=Language.EN)
    assert res.status == "in_progress"
    assert res.current_question.node_id == "q2_modification_type"
    assert len(res.history) == 1
