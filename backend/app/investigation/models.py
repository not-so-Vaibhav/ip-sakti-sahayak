"""Pydantic models for the IP Investigation System.

Defines the complete investigation domain: formulation extraction, evidence sources,
element-wise comparison, multi-dimensional risk assessment, and the top-level
investigation case lifecycle.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class InvestigationStatus(str, Enum):
    EXTRACTING = "extracting"
    SEARCHING = "searching"
    COMPARING = "comparing"
    ASSESSING = "assessing"
    COMPLETE = "complete"
    ERROR = "error"


class EvidenceSourceType(str, Enum):
    PATENT = "patent"
    RESEARCH_PAPER = "research_paper"
    TK_SOURCE = "tk_source"
    FORMULATION = "formulation"
    REGULATION = "regulation"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskDimensionType(str, Enum):
    NOVELTY_RISK = "novelty_risk"
    TK_OVERLAP = "tk_overlap"
    REGULATORY_COMPLEXITY = "regulatory_complexity"
    ABS_COMPLIANCE = "abs_compliance"
    PRIOR_ART_EXPOSURE = "prior_art_exposure"


# ---------------------------------------------------------------------------
# Formulation Extraction
# ---------------------------------------------------------------------------

class FormulationElement(BaseModel):
    """Single extracted element from a formulation description."""
    name: str
    element_type: str  # "ingredient" | "ratio" | "process" | "dosage_form" | "intended_use"
    value: Optional[str] = None
    classical_text_ref: Optional[str] = None


class StructuredFormulation(BaseModel):
    """Complete parsed formulation from user input."""
    raw_input: str
    ingredients: List[FormulationElement] = Field(default_factory=list)
    ratios: List[FormulationElement] = Field(default_factory=list)
    processes: List[FormulationElement] = Field(default_factory=list)
    dosage_forms: List[FormulationElement] = Field(default_factory=list)
    intended_uses: List[FormulationElement] = Field(default_factory=list)

    @property
    def all_elements(self) -> List[FormulationElement]:
        """Flattened union of all element types."""
        return self.ingredients + self.ratios + self.processes + self.dosage_forms + self.intended_uses


# ---------------------------------------------------------------------------
# Evidence Sources
# ---------------------------------------------------------------------------

class EvidenceSource(BaseModel):
    """Unified evidence object across all source types (patents, papers, TK, regulations)."""
    source_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_type: EvidenceSourceType
    title: str
    identifier: Optional[str] = None  # Patent number, DOI, Act section
    url: Optional[str] = None
    publication_date: Optional[str] = None
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    relevant_text: str = ""
    extracted_elements: List[FormulationElement] = Field(default_factory=list)
    relevance_score: float = 0.0
    jurisdiction: Optional[str] = None


# ---------------------------------------------------------------------------
# Comparison Matrix
# ---------------------------------------------------------------------------

class ElementComparison(BaseModel):
    """Single row in the element-wise comparison matrix."""
    element_name: str
    element_type: str
    user_has: bool = True
    matches: Dict[str, bool] = Field(default_factory=dict)  # {source_id: True/False}


class ComparisonMatrix(BaseModel):
    """Full element-wise comparison across user formulation and all evidence sources."""
    user_formulation: StructuredFormulation
    evidence_sources: List[EvidenceSource] = Field(default_factory=list)
    comparisons: List[ElementComparison] = Field(default_factory=list)
    overlap_scores: Dict[str, float] = Field(default_factory=dict)  # {source_id: 0.0-1.0}


# ---------------------------------------------------------------------------
# Risk Assessment
# ---------------------------------------------------------------------------

class RiskDimension(BaseModel):
    """Single risk axis with level, reasoning, and supporting evidence."""
    dimension: RiskDimensionType
    level: RiskLevel = RiskLevel.MEDIUM
    score: float = 0.5  # 0.0-1.0
    reasoning: str = ""
    supporting_evidence: List[str] = Field(default_factory=list)  # List of source_ids


class RiskAssessment(BaseModel):
    """Complete multi-dimensional risk profile."""
    dimensions: List[RiskDimension] = Field(default_factory=list)
    overall_risk: RiskLevel = RiskLevel.MEDIUM
    overall_confidence: float = 0.0
    recommended_actions: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Investigation Case (Top-Level)
# ---------------------------------------------------------------------------

class InvestigationCase(BaseModel):
    """Top-level investigation object — the full case lifecycle."""
    case_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    language: str = "en"
    jurisdiction: str = "india"
    status: InvestigationStatus = InvestigationStatus.EXTRACTING

    # Phase outputs (populated progressively)
    classification_category: Optional[str] = None
    formulation: Optional[StructuredFormulation] = None
    evidence_sources: List[EvidenceSource] = Field(default_factory=list)
    comparison_matrix: Optional[ComparisonMatrix] = None
    risk_assessment: Optional[RiskAssessment] = None
    regulatory_analysis: Optional[str] = None  # Grounded legal RAG answer
    report_markdown: Optional[str] = None  # Final rendered dossier


# ---------------------------------------------------------------------------
# API Request / Response
# ---------------------------------------------------------------------------

class InvestigateRequest(BaseModel):
    """API request to start a new investigation."""
    formulation_description: str
    formulation_category: str
    jurisdiction: str = "india"
    language: str = "en"
    session_id: Optional[str] = None


class InvestigateResponse(BaseModel):
    """API response with full investigation results."""
    case: InvestigationCase
    phases_completed: List[str] = Field(default_factory=list)
    current_phase: str = "complete"
