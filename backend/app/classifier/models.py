"""Pydantic models for the Formulation Classifier."""

from enum import Enum
from typing import Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


class FormulationCategoryCode(str, Enum):
    CLASSICAL_GENERIC = "classical_generic"
    PATENT_OR_PROPRIETARY = "patent_or_proprietary"
    NEW_NON_CLASSICAL_DRUG = "new_non_classical_drug"
    PHYTOPHARMACEUTICAL = "phytopharmaceutical"
    AYURVEDA_AAHAR_NUTRACEUTICAL = "ayurveda_aahar_nutraceutical"
    COSMETIC = "cosmetic"


class Language(str, Enum):
    EN = "en"
    HI = "hi"


class QuestionOption(BaseModel):
    id: str
    label_en: str
    label_hi: str
    next_node_id: str


class QuestionNode(BaseModel):
    type: Literal["question"] = "question"
    id: str
    question_en: str
    question_hi: str
    description_en: Optional[str] = None
    description_hi: Optional[str] = None
    options: List[QuestionOption]


class OutcomeNode(BaseModel):
    type: Literal["outcome"] = "outcome"
    id: str
    category: FormulationCategoryCode
    notes_en: str
    notes_hi: str
    abs_guidance_en: str
    abs_guidance_hi: str


TreeNode = Union[QuestionNode, OutcomeNode]


class DecisionTree(BaseModel):
    version: str
    start_node_id: str
    nodes: Dict[str, Union[QuestionNode, OutcomeNode]]


class CategoryInfo(BaseModel):
    code: FormulationCategoryCode
    display_name_en: str
    display_name_hi: str
    ip_posture_summary_en: str
    ip_posture_summary_hi: str


# API Request/Response models

class OptionView(BaseModel):
    id: str
    label: str
    next_node_id: str


class QuestionView(BaseModel):
    node_id: str
    question: str
    description: Optional[str] = None
    options: List[OptionView]


class OutcomeView(BaseModel):
    category_code: FormulationCategoryCode
    display_name: str
    notes: str
    abs_guidance: str
    ip_posture_summary: str


class ClassificationStep(BaseModel):
    node_id: str
    question: str
    selected_option_id: str
    selected_option_label: str


class ClassificationResult(BaseModel):
    status: Literal["in_progress", "completed"]
    tree_version_tag: str
    language: Language
    session_id: Optional[str] = None
    # Present if status == in_progress
    current_question: Optional[QuestionView] = None
    # Present if status == completed
    outcome: Optional[OutcomeView] = None
    history: List[ClassificationStep] = Field(default_factory=list)


class ClassifyRequest(BaseModel):
    session_id: Optional[str] = None
    language: Language = Language.EN
    # For interactive single step:
    current_node_id: Optional[str] = None
    selected_option_id: Optional[str] = None
    # For batch answers: {"q1_classical_text_match": "no", "q2_modification_type": "clinical_evidence"}
    answers: Optional[Dict[str, str]] = None
