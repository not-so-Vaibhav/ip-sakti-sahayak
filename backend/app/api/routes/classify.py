"""Formulation Classifier API Route (/classify)."""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.app.classifier.engine import DecisionTreeEngine
from backend.app.classifier.models import (
    ClassificationResult,
    ClassifyRequest,
    Language,
)
from backend.app.config import settings
from backend.app.db.supabase_client import supabase_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/classify", tags=["classifier"])

# Initialize decision tree engine
tree_path = settings.resolve_path(settings.tree_config_path)
categories_path = settings.resolve_path(settings.categories_config_path)
engine = DecisionTreeEngine(tree_path=tree_path, categories_path=categories_path)


@router.post("", response_model=ClassificationResult, summary="Run or step through formulation decision tree")
async def classify(request: ClassifyRequest) -> ClassificationResult:
    """
    Run deterministic formulation classifier.
    - If `answers` dict is passed: batch evaluates the entire answer path.
    - If `current_node_id` + `selected_option_id` are passed: steps to the next question or final category.
    - If neither is passed: returns the start question.
    """
    try:
        # Case 1: Batch answers evaluation
        if request.answers:
            result = engine.evaluate_answers(
                answers=request.answers,
                language=request.language,
                session_id=request.session_id,
            )
        # Case 2: Interactive step
        elif request.current_node_id and request.selected_option_id:
            result = engine.step(
                current_node_id=request.current_node_id,
                selected_option_id=request.selected_option_id,
                language=request.language,
                session_id=request.session_id,
            )
        # Case 3: Initial start question
        else:
            result = engine.get_start_result(
                language=request.language,
                session_id=request.session_id,
            )

        # If completed, persist to Supabase classification_sessions
        if result.status == "completed" and result.outcome:
            session_answers = request.answers or {
                step.node_id: step.selected_option_id for step in result.history
            }
            supabase_manager.record_classification_session(
                answers_json=session_answers,
                resulting_category=result.outcome.category_code.value,
                tree_version_tag=result.tree_version_tag,
                session_id=request.session_id,
            )

        return result

    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Classification error")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/tree", summary="Get decision tree structure and metadata")
async def get_tree_info():
    """Returns current decision tree version and start node."""
    return {
        "version": engine.tree.version,
        "start_node_id": engine.tree.start_node_id,
        "nodes_count": len(engine.tree.nodes),
        "tree_config_path": str(engine.tree_path),
    }


@router.post("/reload", summary="Hot-reload decision tree configuration from disk")
async def reload_tree():
    """Reloads decision_tree.json from disk without server restart."""
    try:
        engine.reload()
        return {
            "status": "success",
            "message": "Decision tree config successfully reloaded from disk.",
            "version": engine.tree.version,
            "nodes_count": len(engine.tree.nodes),
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to reload tree: {e}")
