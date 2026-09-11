"""Pure deterministic Decision Tree Engine for Formulation Classification."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Union

from backend.app.classifier.models import (
    CategoryInfo,
    ClassificationResult,
    ClassificationStep,
    DecisionTree,
    FormulationCategoryCode,
    Language,
    OptionView,
    OutcomeNode,
    OutcomeView,
    QuestionNode,
    QuestionView,
)


class DecisionTreeEngine:
    def __init__(self, tree_path: Union[str, Path], categories_path: Optional[Union[str, Path]] = None):
        self.tree_path = Path(tree_path)
        self.categories_path = Path(categories_path) if categories_path else None
        self.tree: DecisionTree = self._load_tree()
        self.categories_map: Dict[str, CategoryInfo] = self._load_categories()
        self.validate_tree()

    def _load_tree(self) -> DecisionTree:
        if not self.tree_path.exists():
            raise FileNotFoundError(f"Decision tree config not found at: {self.tree_path}")
        with open(self.tree_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return DecisionTree.model_validate(data)

    def _load_categories(self) -> Dict[str, CategoryInfo]:
        if not self.categories_path or not self.categories_path.exists():
            return {}
        with open(self.categories_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {item["code"]: CategoryInfo.model_validate(item) for item in data}

    def reload(self) -> None:
        """Reload configuration from disk without restarting application."""
        self.tree = self._load_tree()
        self.categories_map = self._load_categories()
        self.validate_tree()

    def validate_tree(self) -> None:
        """Validate DAG integrity (nodes existence, option target validity)."""
        nodes = self.tree.nodes
        if self.tree.start_node_id not in nodes:
            raise ValueError(f"Start node '{self.tree.start_node_id}' not found in tree nodes.")

        for node_id, node in nodes.items():
            if isinstance(node, QuestionNode):
                if not node.options:
                    raise ValueError(f"Question node '{node_id}' has no options defined.")
                for opt in node.options:
                    if opt.next_node_id not in nodes:
                        raise ValueError(
                            f"Option '{opt.id}' in node '{node_id}' targets non-existent node '{opt.next_node_id}'."
                        )
            elif isinstance(node, OutcomeNode):
                if not node.category:
                    raise ValueError(f"Outcome node '{node_id}' missing category.")

    def _format_question_view(self, node: QuestionNode, language: Language) -> QuestionView:
        is_hi = language == Language.HI
        return QuestionView(
            node_id=node.id,
            question=node.question_hi if is_hi else node.question_en,
            description=node.description_hi if is_hi else node.description_en,
            options=[
                OptionView(
                    id=opt.id,
                    label=opt.label_hi if is_hi else opt.label_en,
                    next_node_id=opt.next_node_id,
                )
                for opt in node.options
            ],
        )

    def _format_outcome_view(self, node: OutcomeNode, language: Language) -> OutcomeView:
        is_hi = language == Language.HI
        cat_info = self.categories_map.get(node.category.value)
        
        display_name = (
            cat_info.display_name_hi if (cat_info and is_hi)
            else (cat_info.display_name_en if cat_info else node.category.value)
        )
        ip_summary = (
            cat_info.ip_posture_summary_hi if (cat_info and is_hi)
            else (cat_info.ip_posture_summary_en if cat_info else "")
        )

        return OutcomeView(
            category_code=node.category,
            display_name=display_name,
            notes=node.notes_hi if is_hi else node.notes_en,
            abs_guidance=node.abs_guidance_hi if is_hi else node.abs_guidance_en,
            ip_posture_summary=ip_summary,
        )

    def get_start_result(self, language: Language = Language.EN, session_id: Optional[str] = None) -> ClassificationResult:
        start_node = self.tree.nodes[self.tree.start_node_id]
        if isinstance(start_node, QuestionNode):
            return ClassificationResult(
                status="in_progress",
                tree_version_tag=self.tree.version,
                language=language,
                session_id=session_id,
                current_question=self._format_question_view(start_node, language),
                outcome=None,
                history=[],
            )
        else:
            return ClassificationResult(
                status="completed",
                tree_version_tag=self.tree.version,
                language=language,
                session_id=session_id,
                current_question=None,
                outcome=self._format_outcome_view(start_node, language),
                history=[],
            )

    def step(
        self,
        current_node_id: str,
        selected_option_id: str,
        language: Language = Language.EN,
        history: Optional[List[ClassificationStep]] = None,
        session_id: Optional[str] = None,
    ) -> ClassificationResult:
        """Step interactively from current question node to next node based on selected option."""
        if history is None:
            history = []

        if current_node_id not in self.tree.nodes:
            raise KeyError(f"Current node '{current_node_id}' does not exist.")

        node = self.tree.nodes[current_node_id]
        if not isinstance(node, QuestionNode):
            raise ValueError(f"Node '{current_node_id}' is an outcome node, cannot transition from it.")

        # Find chosen option
        matched_option = next((opt for opt in node.options if opt.id == selected_option_id), None)
        if not matched_option:
            available = [opt.id for opt in node.options]
            raise ValueError(
                f"Invalid option '{selected_option_id}' for node '{current_node_id}'. Available: {available}"
            )

        is_hi = language == Language.HI
        # Record step in history
        new_history = list(history)
        new_history.append(
            ClassificationStep(
                node_id=node.id,
                question=node.question_hi if is_hi else node.question_en,
                selected_option_id=matched_option.id,
                selected_option_label=matched_option.label_hi if is_hi else matched_option.label_en,
            )
        )

        next_node = self.tree.nodes[matched_option.next_node_id]

        if isinstance(next_node, QuestionNode):
            return ClassificationResult(
                status="in_progress",
                tree_version_tag=self.tree.version,
                language=language,
                session_id=session_id,
                current_question=self._format_question_view(next_node, language),
                outcome=None,
                history=new_history,
            )
        elif isinstance(next_node, OutcomeNode):
            return ClassificationResult(
                status="completed",
                tree_version_tag=self.tree.version,
                language=language,
                session_id=session_id,
                current_question=None,
                outcome=self._format_outcome_view(next_node, language),
                history=new_history,
            )
        else:
            raise TypeError(f"Unknown node type: {type(next_node)}")

    def evaluate_answers(
        self,
        answers: Dict[str, str],
        language: Language = Language.EN,
        session_id: Optional[str] = None,
    ) -> ClassificationResult:
        """Batch evaluate a sequence/dictionary of answers starting from the root node."""
        curr_node_id = self.tree.start_node_id
        history: List[ClassificationStep] = []
        is_hi = language == Language.HI

        while True:
            node = self.tree.nodes[curr_node_id]
            if isinstance(node, OutcomeNode):
                return ClassificationResult(
                    status="completed",
                    tree_version_tag=self.tree.version,
                    language=language,
                    session_id=session_id,
                    current_question=None,
                    outcome=self._format_outcome_view(node, language),
                    history=history,
                )

            if isinstance(node, QuestionNode):
                if node.id not in answers:
                    # Incomplete answers: return current question needed
                    return ClassificationResult(
                        status="in_progress",
                        tree_version_tag=self.tree.version,
                        language=language,
                        session_id=session_id,
                        current_question=self._format_question_view(node, language),
                        outcome=None,
                        history=history,
                    )

                selected_opt_id = answers[node.id]
                matched_option = next((opt for opt in node.options if opt.id == selected_opt_id), None)
                if not matched_option:
                    raise ValueError(f"Invalid answer '{selected_opt_id}' for question '{node.id}'.")

                history.append(
                    ClassificationStep(
                        node_id=node.id,
                        question=node.question_hi if is_hi else node.question_en,
                        selected_option_id=matched_option.id,
                        selected_option_label=matched_option.label_hi if is_hi else matched_option.label_en,
                    )
                )
                curr_node_id = matched_option.next_node_id
