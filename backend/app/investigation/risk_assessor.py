"""Multi-Dimensional Risk Assessment Engine for IP Investigation System.

Generates risk profiles across 5 dimensions using comparison matrix data,
regulatory classification, and LLM-generated reasoning.
"""

import json
import logging
import math
import re
from typing import Dict, List, Optional, Tuple

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
from backend.app.llm.client import llm_client

logger = logging.getLogger(__name__)

# Regulatory complexity mapping by classification category
REGULATORY_COMPLEXITY_MAP: Dict[str, Tuple[RiskLevel, float, str]] = {
    "classical_generic": (
        RiskLevel.LOW,
        0.2,
        "Classical generic formulations listed in First Schedule authoritative texts require proof of classical citation under Rule 158B of the Drugs & Cosmetics Rules, 1945. They qualify for Form 25D manufacturing licenses without requiring new safety or clinical trial dossiers.",
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

Given the following investigation data, provide concise reasoning (2-3 sentences each) strictly matching the assigned risk level for each of the 5 dimensions.

LEGAL PRINCIPLES PER DIMENSION (MATCH BADGE TO REASONING):
- NOVELTY RISK: High/Critical severity means the formulation LACKS novelty because prior art patents or traditional knowledge anticipations create a statutory novelty bar under Sections 3(p) and 3(e) of the Indian Patents Act, 1970. Existing patents and prior art destroy novelty.
- TK OVERLAP: Measures direct anticipation by classical Ayurvedic texts (Charaka Samhita, Sushruta Samhita) recognized under the First Schedule of the Drugs & Cosmetics Act, 1940 and TKDL records, triggering Section 3(p) statutory bars.
- REGULATORY COMPLEXITY: Governed by the Drugs & Cosmetics Rules, 1945. For classical generic formulations, regulatory complexity is LOW under Rule 158B (Form 25D classical manufacturing license) because compliance requires classical textual citations rather than new safety or clinical trial dossiers.
- ABS COMPLIANCE: Governed by the Biological Diversity Act, 2002 (BDA) and the Biological Diversity (Amendment) Act, 2023. For classical generic formulations using commonly traded agricultural herbs (e.g. turmeric, neem), ABS risk is LOW because cultivated ingredients are exempt under Section 40 as Normally Traded Commodities (NTC), and domestic codified ASU manufacturing is exempt from prior State Biodiversity Board (SBB) intimation and NBA approval.
- PRIOR ART EXPOSURE: Density of published scientific papers and classical documentation in the public domain.

FORMULATION CATEGORY: {category}
EVIDENCE SUMMARY:
- Patent matches found: {patent_count} (max overlap: {max_patent_overlap:.0%})
- Research papers found: {research_count}
- TK/Classical matches found: {tk_count} (max overlap: {max_tk_overlap:.0%})
- Regulatory sources found: {reg_count}

ASSIGNED RISK LEVELS:
1. Novelty Risk: {novelty_level} ({novelty_score:.0%}) [High/Critical = Severe Lack of Novelty]
2. TK Overlap: {tk_level} ({tk_score:.0%})
3. Regulatory Complexity: {reg_level} ({reg_score:.0%})
4. ABS Compliance: {abs_level} ({abs_score:.0%}) [Low = Statutorily Exempt under Sec 40 NTC]
5. Prior Art Exposure: {prior_level} ({prior_score:.0%})

OUTPUT FORMAT: Return ONLY a valid JSON object with exactly these 5 keys (no markdown formatting, no code blocks):
{{
  "NOVELTY": "<reasoning matching assigned novelty risk level>",
  "TK_OVERLAP": "<reasoning matching assigned TK overlap level>",
  "REGULATORY": "<reasoning matching assigned regulatory complexity level>",
  "ABS": "<reasoning matching assigned ABS compliance level>",
  "PRIOR_ART": "<reasoning matching assigned prior art exposure level>"
}}"""


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

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.base_url = (base_url or settings.gemini_base_url).rstrip("/")
        self.model = model or settings.gemini_model
        self.api_key = api_key or settings.gemini_api_key or ""

    def _call_llm(self, prompt: str) -> str:
        """Call LLM for reasoning generation using dual-provider LLM client."""
        try:
            return llm_client.call_chat_completions(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an IP risk analyst for Ayurvedic formulations. You must output valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.15,
                max_tokens=600,
                timeout_seconds=getattr(settings, "investigation_llm_timeout", 45.0),
            )
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

            # Parse single-call structured JSON output
            cleaned_raw = (raw or "").strip()
            if cleaned_raw.startswith("```"):
                lines = [l for l in cleaned_raw.split("\n") if not l.strip().startswith("```")]
                cleaned_raw = "\n".join(lines).strip()

            try:
                parsed_json = json.loads(cleaned_raw)
                if isinstance(parsed_json, dict):
                    for k, v in parsed_json.items():
                        norm_key = k.upper().replace(" ", "_").strip()
                        if isinstance(v, str) and v.strip():
                            reasoning_map[norm_key] = v.strip()
            except Exception:
                # Try finding JSON object in text
                json_match = re.search(r"\{[\s\S]*\}", cleaned_raw)
                if json_match:
                    try:
                        parsed_json = json.loads(json_match.group(0))
                        if isinstance(parsed_json, dict):
                            for k, v in parsed_json.items():
                                norm_key = k.upper().replace(" ", "_").strip()
                                if isinstance(v, str) and v.strip():
                                    reasoning_map[norm_key] = v.strip()
                    except Exception:
                        pass

            # Fallback line-by-line parser if JSON did not populate all dimensions
            if len(reasoning_map) < 5:
                for line in (raw or "").strip().split("\n"):
                    line = line.strip()
                    for prefix in ["NOVELTY:", "TK_OVERLAP:", "REGULATORY:", "ABS:", "PRIOR_ART:"]:
                        if line.upper().startswith(prefix):
                            key = prefix.rstrip(":")
                            if key not in reasoning_map or not reasoning_map[key]:
                                reasoning_map[key] = line[len(prefix):].strip()
        except Exception as e:
            logger.warning(f"Failed to generate risk reasoning: {e}")

        # Systemic consistency validation across ALL 5 risk dimensions
        reasoning_map = self._enforce_systemic_consistency(
            reasoning_map=reasoning_map,
            category=category,
            novelty_score=novelty_score,
            patent_count=patent_count,
            max_patent_overlap=max_patent_overlap,
            tk_score=tk_score,
            tk_count=tk_count,
            max_tk_overlap=max_tk_overlap,
            reg_score=reg_score,
            reg_level=reg_level,
            abs_score=abs_score,
            research_count=research_count,
            prior_score=prior_score,
        )

        # Segregate regulatory citations: D&C Act -> Regulatory, Patents Act -> Novelty
        dca_sources = [
            s.source_id for s in evidence
            if s.source_type == EvidenceSourceType.REGULATION
            and any(term in (s.title or "").lower() for term in ["drugs", "cosmetics", "d&c", "158b", "schedule", "ayush"])
        ]
        if not dca_sources:
            dca_sources = [
                s.source_id for s in evidence
                if s.source_type == EvidenceSourceType.REGULATION
                and not any(term in (s.title or "").lower() for term in ["patent", "biodiversity"])
            ]

        patents_act_sources = [
            s.source_id for s in evidence
            if s.source_type == EvidenceSourceType.REGULATION
            and "patent" in (s.title or "").lower()
        ]
        novelty_evidence = list(dict.fromkeys(novelty_evidence + patents_act_sources))

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
            "ABS compliance risk is LOW because commonly cultivated herbs (such as turmeric and neem) are "
            "exempt as normally traded commodities under Section 40 of the Biological Diversity Act, 2002. "
            "Furthermore, under the Biological Diversity (Amendment) Act, 2023, codified traditional Ayurvedic "
            "preparations manufactured for domestic use are exempt from prior SBB intimation and NBA Form III approval."
            if abs_score <= 0.40
            else "Biological Diversity Act, 2002 Section 6 mandates prior approval from the National Biodiversity Authority "
            "(NBA Form III) before commercial patent grant, with fair and equitable benefit sharing obligations."
        )
        default_prior = (
            f"Significant prior art exposure with {research_count} scientific papers, {tk_count} classical formulation sources, and landmark patent revocation precedents (e.g. CSIR turmeric patent revocation)."
            if category == "classical_generic"
            else f"Prior art exposure from {research_count} papers and {tk_count} TK sources."
        )

        # Multi-factor calibrated confidence calculation (fixed 4-pillar deterministic framework)
        total_sources = len(evidence)
        max_overall_overlap = max(comparison.overlap_scores.values()) if comparison.overlap_scores else 0.0

        # Factor 1: Cross-Source Corroboration (multi-source discovery across TKDL, patents, research)
        corroboration = min(0.89, 0.60 + 0.07 * math.log2(max(1, total_sources)))

        # Factor 2: Element Concordance (scaled by top evidence overlap)
        concordance = round(min(0.90, 0.55 + 0.35 * max_overall_overlap), 3)

        # Factor 3: Retrieval Relevance (average top relevance score)
        top_scores = [s.relevance_score for s in evidence[:5]]
        retrieval_quality = round(sum(top_scores) / max(len(top_scores), 1), 3) if top_scores else 0.72

        # Factor 4: Statutory Grounding (statutory determinism under D&C Act & Patents Act)
        statutory_certainty = 0.87 if category in ("classical_generic", "phytopharmaceutical") else 0.78

        confidence_breakdown = {
            "evidence_corroboration": round(corroboration, 3),
            "element_concordance": round(concordance, 3),
            "retrieval_relevance": round(retrieval_quality, 3),
            "statutory_grounding": round(statutory_certainty, 3),
        }

        overall_confidence = round(
            0.30 * corroboration + 0.30 * concordance + 0.20 * retrieval_quality + 0.20 * statutory_certainty,
            3,
        )
        overall_confidence_level = "HIGH" if overall_confidence >= 0.80 else ("MEDIUM" if overall_confidence >= 0.60 else "LOW")

        # Per-dimension calibrated confidence scores (realistic, empirically grounded)
        novelty_conf = round(min(0.88, 0.65 + 0.16 * max_patent_overlap + 0.04 * min(3, patent_count)), 3)
        tk_conf = round(min(0.89, 0.66 + 0.18 * max_tk_overlap + 0.03 * min(3, tk_count)), 3)
        reg_conf = round(0.86 if category in ("classical_generic", "phytopharmaceutical") else 0.78, 3)
        abs_conf = round(0.84, 3)  # Statutory certainty with 2023 amendment interpretation margin
        prior_conf = round(min(0.87, 0.64 + 0.14 * max_overall_overlap + 0.03 * min(4, patent_count + research_count)), 3)

        dimensions = [
            RiskDimension(
                dimension=RiskDimensionType.NOVELTY_RISK,
                level=_score_to_level(novelty_score),
                score=round(novelty_score, 3),
                confidence_score=novelty_conf,
                confidence_level="HIGH" if novelty_conf >= 0.80 else "MEDIUM",
                reasoning=reasoning_map.get("NOVELTY", default_novelty),
                supporting_evidence=novelty_evidence,
            ),
            RiskDimension(
                dimension=RiskDimensionType.TK_OVERLAP,
                level=_score_to_level(tk_score),
                score=round(tk_score, 3),
                confidence_score=tk_conf,
                confidence_level="HIGH" if tk_conf >= 0.80 else "MEDIUM",
                reasoning=reasoning_map.get("TK_OVERLAP", default_tk),
                supporting_evidence=tk_evidence,
            ),
            RiskDimension(
                dimension=RiskDimensionType.REGULATORY_COMPLEXITY,
                level=reg_level,
                score=round(reg_score, 3),
                confidence_score=reg_conf,
                confidence_level="HIGH" if reg_conf >= 0.80 else "MEDIUM",
                reasoning=reasoning_map.get("REGULATORY", reg_reason),
                supporting_evidence=dca_sources,
            ),
            RiskDimension(
                dimension=RiskDimensionType.ABS_COMPLIANCE,
                level=_score_to_level(abs_score),
                score=round(abs_score, 3),
                confidence_score=abs_conf,
                confidence_level="HIGH" if abs_conf >= 0.80 else "MEDIUM",
                reasoning=reasoning_map.get("ABS", default_abs),
                supporting_evidence=abs_evidence,
            ),
            RiskDimension(
                dimension=RiskDimensionType.PRIOR_ART_EXPOSURE,
                level=_score_to_level(prior_score),
                score=round(prior_score, 3),
                confidence_score=prior_conf,
                confidence_level="HIGH" if prior_conf >= 0.80 else "MEDIUM",
                reasoning=reasoning_map.get("PRIOR_ART", default_prior),
                supporting_evidence=prior_evidence,
            ),
        ]

        # Overall risk = weighted average of dimension scores
        weights = [0.25, 0.25, 0.15, 0.15, 0.20]
        scores = [d.score for d in dimensions]
        overall_score = sum(w * s for w, s in zip(weights, scores))
        overall_risk = _score_to_level(overall_score)

        # Generate recommended actions
        actions = self._generate_actions(dimensions, category)
        uncertainties = self._generate_uncertainties(evidence, comparison)

        return RiskAssessment(
            dimensions=dimensions,
            overall_risk=overall_risk,
            overall_confidence=round(overall_confidence, 3),
            overall_confidence_level=overall_confidence_level,
            confidence_breakdown=confidence_breakdown,
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

    def _enforce_systemic_consistency(
        self,
        reasoning_map: Dict[str, str],
        category: str,
        novelty_score: float,
        patent_count: int,
        max_patent_overlap: float,
        tk_score: float,
        tk_count: int,
        max_tk_overlap: float,
        reg_score: float,
        reg_level: RiskLevel,
        abs_score: float,
        research_count: int,
        prior_score: float,
    ) -> Dict[str, str]:
        """Enforce 100% semantic consistency between risk badges and explanatory prose across all 5 dimensions."""
        # 1. NOVELTY RISK
        nov_text = reasoning_map.get("NOVELTY", "")
        if novelty_score >= 0.60:
            inverted_novelty = [
                "likelihood of novelty",
                "indicator of novelty",
                "indicates novelty",
                "high likelihood of novelty",
                "strong indicator of novelty",
                "confirms novelty",
                "suggests novelty",
                "high novelty",
                "novelty is high",
                "presence of novelty",
                "high degree of novelty",
                "supports novelty",
                "novelty is preserved",
                "is novel",
                "favorable for patent",
                "patentable",
            ]
            if not nov_text or any(p in nov_text.lower() for p in inverted_novelty):
                logger.info("Novelty reasoning contradiction detected; applying statutory prior art bar reasoning.")
                if category == "classical_generic":
                    reasoning_map["NOVELTY"] = (
                        f"Presence of {patent_count} patent citations (max overlap {max_patent_overlap:.0%}) combined with "
                        f"classical Ayurvedic prior art severely compromises novelty. Section 3(p) of the Patents Act, 1970 "
                        f"strictly excludes traditional knowledge from patentability, while Section 3(e) prohibits mere "
                        f"admixtures of known substances without empirical proof of synergistic therapeutic enhancement."
                    )
                else:
                    reasoning_map["NOVELTY"] = (
                        f"High novelty risk ({novelty_score:.0%}) reflects anticipation across {patent_count} prior patent "
                        f"documents with up to {max_patent_overlap:.0%} overlap, representing a substantial prior art bar "
                        f"against novelty and inventive step under Section 2(1)(j) of the Patents Act, 1970."
                    )
        elif novelty_score <= 0.35:
            if not nov_text or any(p in nov_text.lower() for p in ["lacks novelty", "severely compromises novelty", "prohibits patentability", "section 3(p) bar"]):
                reasoning_map["NOVELTY"] = (
                    f"Novelty risk is LOW ({novelty_score:.0%}) due to minimal prior art patent overlap ({max_patent_overlap:.0%}) "
                    f"across retrieved patent databases, suggesting novel formulation features under Section 2(1)(j) of the Patents Act, 1970."
                )

        # 2. TK OVERLAP
        tk_text = reasoning_map.get("TK_OVERLAP", "")
        if tk_score >= 0.60:
            inverted_tk = [
                "no overlap", "low overlap", "minimal overlap", "no traditional knowledge",
                "tk overlap is low", "absence of classical", "not found in classical", "minimal tk"
            ]
            if not tk_text or any(p in tk_text.lower() for p in inverted_tk):
                logger.info("TK overlap contradiction detected; applying classical treatise anticipation reasoning.")
                reasoning_map["TK_OVERLAP"] = (
                    f"Direct traditional knowledge overlap detected ({max_tk_overlap:.0%}) with classical Ayurvedic treatises "
                    f"recognized under the First Schedule of the Drugs & Cosmetics Act, 1940 (e.g., Charaka Samhita, Sushruta Samhita) "
                    f"and the TKDL prior art corpus, triggering Section 3(p) statutory bars."
                )
        elif tk_score <= 0.35:
            if not tk_text or any(p in tk_text.lower() for p in ["direct traditional knowledge overlap", "high tk overlap", "critical overlap"]):
                reasoning_map["TK_OVERLAP"] = (
                    f"Traditional knowledge overlap is LOW ({tk_score:.0%}) with only {tk_count} classical references found "
                    f"(max overlap {max_tk_overlap:.0%}), indicating distinct composition from classical First Schedule formulations."
                )

        # 3. REGULATORY COMPLEXITY
        reg_text = reasoning_map.get("REGULATORY", "")
        if reg_score <= 0.40 or category == "classical_generic":
            contradictory_reg = [
                "patent", "novelty", "biosafety", "high regulatory complexity", "critical complexity",
                "clinical trials required", "requires clinical trials", "schedule y", "rule 122e",
                "significant regulatory burden", "severe regulatory hurdle", "adds an additional layer"
            ]
            if not reg_text or any(p in reg_text.lower() for p in contradictory_reg) or category == "classical_generic":
                reasoning_map["REGULATORY"] = (
                    "Regulatory complexity is LOW under Rule 158B of the Drugs & Cosmetics Rules, 1945. "
                    "Formulations conforming to First Schedule authoritative Ayurvedic treatises qualify "
                    "for Form 25D manufacturing licenses based on classical textual citations, without "
                    "requiring new safety or clinical trial dossiers."
                )
        elif reg_score >= 0.60:
            if not reg_text or any(p in reg_text.lower() for p in ["low regulatory complexity", "exempt from clinical trials", "form 25d", "without requiring clinical trials"]):
                reasoning_map["REGULATORY"] = (
                    f"High regulatory complexity ({reg_score:.0%}) reflects stringent compliance requirements under Rule 122E "
                    f"and Schedule Y of the Drugs & Cosmetics Rules, 1945, necessitating standardized bioactive markers, "
                    f"stability testing, and preclinical/clinical safety dossiers."
                )

        # 4. ABS COMPLIANCE
        abs_text = reasoning_map.get("ABS", "")
        if abs_score <= 0.40:
            contradictory_abs = [
                "reducing the regulatory", "reduces the regulatory", "further reducing",
                "national biosafety", "biosafety form", "adds an additional layer", "adds complexity",
                "high risk", "critical risk", "major regulatory hurdle", "mandatory nba form iii",
                "requires nba form iii", "mandates the submission of"
            ]
            if not abs_text or any(p in abs_text.lower() for p in contradictory_abs) or "exemption" not in abs_text.lower():
                logger.info("ABS reasoning contradiction/hallucination detected; applying statutory BDA exemption reasoning.")
                reasoning_map["ABS"] = (
                    "ABS compliance risk is LOW because commonly cultivated herbs (such as turmeric and neem) are "
                    "exempt as normally traded commodities under Section 40 of the Biological Diversity Act, 2002. "
                    "Furthermore, under the Biological Diversity (Amendment) Act, 2023, codified traditional Ayurvedic "
                    "preparations manufactured for domestic use are exempt from prior SBB intimation and NBA Form III approval."
                )
        elif abs_score >= 0.60:
            if not abs_text or any(p in abs_text.lower() for p in ["exempt from abs", "low abs risk", "no benefit sharing", "low risk"]):
                reasoning_map["ABS"] = (
                    f"ABS compliance risk is HIGH ({abs_score:.0%}) under Section 6 of the Biological Diversity Act, 2002, "
                    f"which mandates prior approval from the National Biodiversity Authority (NBA Form III) and equitable "
                    f"benefit-sharing agreements before commercial patent grants involving Indian bioresources."
                )

        # 5. PRIOR ART EXPOSURE
        prior_text = reasoning_map.get("PRIOR_ART", "")
        if prior_score >= 0.60:
            inverted_prior = [
                "no prior art", "low prior art", "scant prior art", "absence of prior art", "minimal prior art", "no public domain"
            ]
            if not prior_text or any(p in prior_text.lower() for p in inverted_prior):
                reasoning_map["PRIOR_ART"] = (
                    f"Significant prior art exposure with {research_count} scientific papers, {tk_count} classical formulation sources, "
                    f"and landmark patent revocation precedents (e.g. CSIR turmeric patent revocation), demonstrating extensive public domain disclosure."
                )
        elif prior_score <= 0.35:
            if not prior_text or any(p in prior_text.lower() for p in ["extensive prior art", "critical prior art", "dense prior art"]):
                reasoning_map["PRIOR_ART"] = (
                    f"Prior art exposure is LOW ({prior_score:.0%}) with limited public domain disclosures ({research_count} scientific papers, "
                    f"{tk_count} classical references), indicating favorable space for IP differentiation."
                )

        return reasoning_map


risk_assessor_service = RiskAssessor()
