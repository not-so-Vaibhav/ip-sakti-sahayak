"""Multi-Dimensional Risk Assessment Engine for IP Investigation System.

Generates risk profiles across 5 dimensions using comparison matrix data,
regulatory classification, and LLM-generated reasoning.
"""

import logging
from typing import Dict, List, Optional, Tuple

import httpx

from backend.app.config import settings
from backend.app.investigation.models import (
    ComparisonMatrix,
    EvidenceSource,
    EvidenceSourceType,
    RiskAssessment,
    RiskDimension,
    RiskDimensionType,
    RiskLevel,
)

logger = logging.getLogger(__name__)

# Regulatory complexity mapping by classification category
REGULATORY_COMPLEXITY_MAP: Dict[str, Tuple[RiskLevel, float, str]] = {
    "classical_generic": (
        RiskLevel.LOW,
        0.2,
        "Classical generic formulations have minimal regulatory complexity — licensed under First Schedule texts with no new drug application required.",
    ),
    "patent_or_proprietary": (
        RiskLevel.MEDIUM,
        0.5,
        "Patent or Proprietary medicines require demonstration of synergistic interaction under Section 3(e) and licensing under Section 3(h) DCA.",
    ),
    "new_non_classical_drug": (
        RiskLevel.HIGH,
        0.8,
        "New non-classical drugs require full preclinical and clinical trial evidence under Schedule Y, with significant time and cost implications.",
    ),
    "phytopharmaceutical": (
        RiskLevel.HIGH,
        0.85,
        "Phytopharmaceutical drugs under Rule 122E require standardization to minimum 4 bioactive markers with chromatographic validation, plus IND trials.",
    ),
    "ayurveda_aahar_nutraceutical": (
        RiskLevel.MEDIUM,
        0.45,
        "Ayurveda Aahar products require FSSAI licensing under 2022 Regulations. Therapeutic disease cure claims are strictly prohibited under Regulation 5.",
    ),
    "cosmetic": (
        RiskLevel.LOW,
        0.3,
        "Ayurvedic cosmetics (Saundarya Prasadak) have moderate requirements — BIS safety compliance and topical-use-only restrictions.",
    ),
}

RISK_REASONING_PROMPT = """You are an IP risk analyst specializing in Indian Ayurvedic intellectual property law.

Given the following investigation data, provide concise reasoning (2-3 sentences each) for the risk levels assigned to each dimension.

FORMULATION CATEGORY: {category}
EVIDENCE SUMMARY:
- Patent matches found: {patent_count} (max overlap: {max_patent_overlap:.0%})
- Research papers found: {research_count}
- TK/Classical matches found: {tk_count} (max overlap: {max_tk_overlap:.0%})
- Regulatory sources found: {reg_count}

RISK DIMENSIONS:
1. Novelty Risk: {novelty_level} ({novelty_score:.0%})
2. TK Overlap: {tk_level} ({tk_score:.0%})
3. Regulatory Complexity: {reg_level} ({reg_score:.0%})
4. ABS Compliance: {abs_level} ({abs_score:.0%})
5. Prior Art Exposure: {prior_level} ({prior_score:.0%})

For each dimension, provide specific reasoning grounded in the evidence. Reference patent numbers, formulation names, or section numbers where applicable.

OUTPUT FORMAT: Return exactly 5 lines, one per dimension:
NOVELTY: <reasoning>
TK_OVERLAP: <reasoning>
REGULATORY: <reasoning>
ABS: <reasoning>
PRIOR_ART: <reasoning>"""


def _score_to_level(score: float) -> RiskLevel:
    """Convert a 0-1 score to a risk level."""
    if score >= 0.8:
        return RiskLevel.CRITICAL
    elif score >= 0.6:
        return RiskLevel.HIGH
    elif score >= 0.35:
        return RiskLevel.MEDIUM
    else:
        return RiskLevel.LOW


class RiskAssessor:
    """Generates multi-dimensional risk assessments from investigation evidence."""

    def __init__(self):
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model
        self.api_key = settings.ollama_api_key

    def _call_llm(self, prompt: str) -> str:
        """Call LLM for reasoning generation."""
        endpoint = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an IP risk analyst for Ayurvedic formulations."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.15,
            "max_tokens": 600,
        }
        timeout = getattr(settings, "investigation_llm_timeout", 45.0)
        try:
            with httpx.Client(timeout=timeout) as client:
                res = client.post(endpoint, json=payload, headers=headers)
                res.raise_for_status()
                return res.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"Risk reasoning LLM call failed: {e}")
            return ""

    def _compute_novelty_risk(
        self,
        comparison: ComparisonMatrix,
        evidence: List[EvidenceSource],
        category: str = "classical_generic",
    ) -> Tuple[float, List[str]]:
        """Compute novelty risk from patent overlap scores."""
        patent_sources = [
            s for s in evidence if s.source_type == EvidenceSourceType.PATENT
        ]
        if not patent_sources:
            base_score = 0.85 if category == "classical_generic" else 0.15
            return base_score, []

        max_overlap = 0.0
        top_patent_ids = []
        for src in patent_sources:
            overlap = comparison.overlap_scores.get(src.source_id, 0.0)
            if overlap > max_overlap:
                max_overlap = overlap
            if overlap > 0.2:
                top_patent_ids.append(src.source_id)

        # Base score from patent overlap
        score = min(1.0, max_overlap * 1.2)
        # Classical generic formulations face strict Section 3(p) & 3(e) exclusions
        if category == "classical_generic":
            score = max(score, 0.85)

        return score, top_patent_ids

    def _compute_tk_overlap(
        self,
        comparison: ComparisonMatrix,
        evidence: List[EvidenceSource],
        category: str = "classical_generic",
    ) -> Tuple[float, List[str]]:
        """Compute TK overlap risk from classical formulation matches."""
        tk_sources = [
            s for s in evidence
            if s.source_type in (EvidenceSourceType.TK_SOURCE, EvidenceSourceType.FORMULATION)
        ]
        if not tk_sources:
            base_score = 0.80 if category == "classical_generic" else 0.1
            return base_score, []

        max_overlap = 0.0
        top_tk_ids = []
        for src in tk_sources:
            overlap = comparison.overlap_scores.get(src.source_id, 0.0)
            if overlap > max_overlap:
                max_overlap = overlap
            if overlap > 0.2:
                top_tk_ids.append(src.source_id)

        score = min(1.0, max_overlap * 1.1)
        if category == "classical_generic":
            score = max(score, 0.80)

        return score, top_tk_ids

    def _compute_abs_compliance(
        self,
        evidence: List[EvidenceSource],
        category: str,
    ) -> Tuple[float, List[str]]:
        """Compute ABS compliance risk from regulatory evidence."""
        abs_sources = [
            s for s in evidence
            if s.source_type == EvidenceSourceType.REGULATION
            and "biodiversity" in (s.title or "").lower()
        ]

        # Categories with biological resource usage
        high_abs_categories = {
            "phytopharmaceutical",
            "new_non_classical_drug",
            "patent_or_proprietary",
        }

        if category in high_abs_categories:
            base_score = 0.6
        else:
            base_score = 0.25

        supporting_ids = [s.source_id for s in abs_sources]
        return base_score, supporting_ids

    def _compute_prior_art_exposure(
        self,
        evidence: List[EvidenceSource],
    ) -> Tuple[float, List[str]]:
        """Compute prior art exposure from research + TK density."""
        research_count = sum(
            1 for s in evidence if s.source_type == EvidenceSourceType.RESEARCH_PAPER
        )
        tk_count = sum(
            1 for s in evidence
            if s.source_type in (EvidenceSourceType.TK_SOURCE, EvidenceSourceType.FORMULATION)
        )

        # More prior art = higher exposure
        total = research_count + tk_count
        if total >= 8:
            score = 0.85
        elif total >= 5:
            score = 0.65
        elif total >= 3:
            score = 0.45
        elif total >= 1:
            score = 0.3
        else:
            score = 0.1

        supporting_ids = [
            s.source_id for s in evidence
            if s.source_type in (
                EvidenceSourceType.RESEARCH_PAPER,
                EvidenceSourceType.TK_SOURCE,
                EvidenceSourceType.FORMULATION,
            )
        ]
        return score, supporting_ids[:5]

    def assess(
        self,
        comparison: ComparisonMatrix,
        evidence: List[EvidenceSource],
        category: str,
        regulatory_analysis: Optional[str] = None,
    ) -> RiskAssessment:
        """Generate complete multi-dimensional risk assessment."""
        # Compute each dimension
        novelty_score, novelty_evidence = self._compute_novelty_risk(comparison, evidence, category)
        tk_score, tk_evidence = self._compute_tk_overlap(comparison, evidence, category)
        reg_level, reg_score, reg_reason = REGULATORY_COMPLEXITY_MAP.get(
            category,
            (RiskLevel.MEDIUM, 0.5, "Unknown category — moderate regulatory complexity assumed."),
        )
        abs_score, abs_evidence = self._compute_abs_compliance(evidence, category)
        prior_score, prior_evidence = self._compute_prior_art_exposure(evidence)

        # Source counts for reasoning prompt
        patent_count = sum(1 for s in evidence if s.source_type == EvidenceSourceType.PATENT)
        research_count = sum(1 for s in evidence if s.source_type == EvidenceSourceType.RESEARCH_PAPER)
        tk_count = sum(1 for s in evidence if s.source_type in (EvidenceSourceType.TK_SOURCE, EvidenceSourceType.FORMULATION))
        reg_count = sum(1 for s in evidence if s.source_type == EvidenceSourceType.REGULATION)

        max_patent_overlap = max(
            (comparison.overlap_scores.get(s.source_id, 0) for s in evidence if s.source_type == EvidenceSourceType.PATENT),
            default=0.0,
        )
        max_tk_overlap = max(
            (comparison.overlap_scores.get(s.source_id, 0) for s in evidence if s.source_type in (EvidenceSourceType.TK_SOURCE, EvidenceSourceType.FORMULATION)),
            default=0.0,
        )

        # Generate LLM reasoning
        reasoning_map: Dict[str, str] = {}
        try:
            prompt = RISK_REASONING_PROMPT.format(
                category=category,
                patent_count=patent_count,
                max_patent_overlap=max_patent_overlap,
                research_count=research_count,
                tk_count=tk_count,
                max_tk_overlap=max_tk_overlap,
                reg_count=reg_count,
                novelty_level=_score_to_level(novelty_score).value,
                novelty_score=novelty_score,
                tk_level=_score_to_level(tk_score).value,
                tk_score=tk_score,
                reg_level=reg_level.value,
                reg_score=reg_score,
                abs_level=_score_to_level(abs_score).value,
                abs_score=abs_score,
                prior_level=_score_to_level(prior_score).value,
                prior_score=prior_score,
            )
            raw = self._call_llm(prompt)

            # Parse structured output
            for line in raw.strip().split("\n"):
                line = line.strip()
                for prefix in ["NOVELTY:", "TK_OVERLAP:", "REGULATORY:", "ABS:", "PRIOR_ART:"]:
                    if line.upper().startswith(prefix):
                        key = prefix.rstrip(":")
                        reasoning_map[key] = line[len(prefix):].strip()
        except Exception as e:
            logger.warning(f"Failed to generate risk reasoning: {e}")

        # Build dimensions
        default_novelty = (
            "Section 3(p) of the Patents Act, 1970 strictly excludes traditional knowledge from patentability. Section 3(e) prohibits combinations of known herbal ingredients absent empirical demonstration of synergistic therapeutic bio-enhancement."
            if category == "classical_generic"
            else f"Novelty risk based on {patent_count} patent matches with max {max_patent_overlap:.0%} overlap."
        )
        default_tk = (
            f"Direct traditional knowledge overlap detected ({max_tk_overlap:.0%}) with classical Ayurvedic treatises recognized under the First Schedule of the Drugs & Cosmetics Act, 1940 (e.g., Charaka Samhita, Sushruta Samhita) and the TKDL prior art corpus."
            if category == "classical_generic"
            else f"TK overlap based on {tk_count} classical source matches with max {max_tk_overlap:.0%} overlap."
        )
        default_abs = (
            "Biological Diversity Act, 2002 Section 6 mandates prior approval from the National Biodiversity Authority (NBA Form III) before applying for any IP. Domestic manufacturers require State Biodiversity Board (SBB) intimation."
        )
        default_prior = (
            f"Significant prior art exposure with {research_count} scientific papers, {tk_count} classical formulation sources, and landmark patent revocation precedents (e.g. CSIR turmeric patent revocation)."
            if category == "classical_generic"
            else f"Prior art exposure from {research_count} papers and {tk_count} TK sources."
        )

        dimensions = [
            RiskDimension(
                dimension=RiskDimensionType.NOVELTY_RISK,
                level=_score_to_level(novelty_score),
                score=round(novelty_score, 3),
                reasoning=reasoning_map.get("NOVELTY", default_novelty),
                supporting_evidence=novelty_evidence,
            ),
            RiskDimension(
                dimension=RiskDimensionType.TK_OVERLAP,
                level=_score_to_level(tk_score),
                score=round(tk_score, 3),
                reasoning=reasoning_map.get("TK_OVERLAP", default_tk),
                supporting_evidence=tk_evidence,
            ),
            RiskDimension(
                dimension=RiskDimensionType.REGULATORY_COMPLEXITY,
                level=reg_level,
                score=round(reg_score, 3),
                reasoning=reasoning_map.get("REGULATORY", reg_reason),
                supporting_evidence=[],
            ),
            RiskDimension(
                dimension=RiskDimensionType.ABS_COMPLIANCE,
                level=_score_to_level(abs_score),
                score=round(abs_score, 3),
                reasoning=reasoning_map.get("ABS", default_abs),
                supporting_evidence=abs_evidence,
            ),
            RiskDimension(
                dimension=RiskDimensionType.PRIOR_ART_EXPOSURE,
                level=_score_to_level(prior_score),
                score=round(prior_score, 3),
                reasoning=reasoning_map.get("PRIOR_ART", default_prior),
                supporting_evidence=prior_evidence,
            ),
        ]

        # Overall risk = weighted average of dimension scores
        weights = [0.25, 0.25, 0.15, 0.15, 0.20]
        scores = [d.score for d in dimensions]
        overall_score = sum(w * s for w, s in zip(weights, scores))
        overall_risk = _score_to_level(overall_score)
        overall_confidence = round(1.0 - (overall_score * 0.3), 3)  # Higher risk → slightly lower confidence

        # Generate recommended actions
        actions = self._generate_actions(dimensions, category)
        uncertainties = self._generate_uncertainties(evidence, comparison)

        return RiskAssessment(
            dimensions=dimensions,
            overall_risk=overall_risk,
            overall_confidence=round(overall_confidence, 3),
            recommended_actions=actions,
            uncertainties=uncertainties,
        )

    def _generate_actions(self, dimensions: List[RiskDimension], category: str) -> List[str]:
        """Generate recommended next actions based on risk profile."""
        actions = []
        for dim in dimensions:
            if dim.dimension == RiskDimensionType.NOVELTY_RISK and dim.level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
                actions.append("Conduct detailed prior art search with registered patent agent before filing.")
            if dim.dimension == RiskDimensionType.TK_OVERLAP and dim.level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
                actions.append("Verify against TKDL records — high overlap with classical formulations may trigger Section 3(p) bar.")
            if dim.dimension == RiskDimensionType.REGULATORY_COMPLEXITY and dim.level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
                actions.append("Engage regulatory consultant for clinical trial design and CDSCO approval pathway.")
            if dim.dimension == RiskDimensionType.ABS_COMPLIANCE and dim.level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
                actions.append("File NBA Form III for prior approval before patent application under BDA Section 6.")
            if dim.dimension == RiskDimensionType.PRIOR_ART_EXPOSURE and dim.level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
                actions.append("Document novelty claim carefully — extensive prior art requires clear differentiation strategy.")

        if not actions:
            actions.append("Proceed with standard IP filing process. Risk profile is within acceptable bounds.")

        return actions

    def _generate_uncertainties(
        self,
        evidence: List[EvidenceSource],
        comparison: ComparisonMatrix,
    ) -> List[str]:
        """Generate uncertainty disclaimers."""
        uncertainties = []

        if len(evidence) < 5:
            uncertainties.append("Limited evidence sources found — risk assessment may not capture all prior art.")

        patent_count = sum(1 for s in evidence if s.source_type == EvidenceSourceType.PATENT)
        if patent_count == 0:
            uncertainties.append("No patent matches found in current search — live patent database search recommended for comprehensive coverage.")

        if not comparison.comparisons:
            uncertainties.append("No formulation elements extracted — comparison matrix is empty.")

        uncertainties.append(
            "This assessment is based on automated analysis and does not constitute legal advice. "
            "Consult a registered patent attorney for formal IP opinions."
        )

        return uncertainties


risk_assessor_service = RiskAssessor()
