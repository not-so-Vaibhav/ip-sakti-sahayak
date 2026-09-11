"""Element-Wise Comparison Engine for IP Investigation System.

Builds structured comparison matrices between user's formulation and
all retrieved evidence sources, using synonym-aware ingredient matching.
"""

import json
import logging
from typing import Dict, List, Optional, Set

from backend.app.config import settings
from backend.app.investigation.models import (
    ComparisonMatrix,
    ElementComparison,
    EvidenceSource,
    FormulationElement,
    StructuredFormulation,
)

logger = logging.getLogger(__name__)


class FormulationComparator:
    """Builds element-wise comparison matrices between formulations."""

    def __init__(self):
        self._synonyms: Optional[Dict[str, List[str]]] = None

    def _load_synonyms(self) -> Dict[str, List[str]]:
        """Load ingredient synonym map."""
        if self._synonyms is not None:
            return self._synonyms

        syn_path = settings.resolve_path(
            getattr(settings, "ingredient_synonyms_path", "config/ingredient_synonyms.json")
        )
        if syn_path.exists():
            with open(syn_path, "r", encoding="utf-8") as f:
                self._synonyms = json.load(f)
        else:
            self._synonyms = {}
        return self._synonyms

    def _get_canonical_name(self, name: str) -> str:
        """Resolve a name to its canonical key via synonym map."""
        synonyms = self._load_synonyms()
        name_lower = name.lower().strip()

        if name_lower in synonyms:
            return name_lower

        for canonical, syn_list in synonyms.items():
            if name_lower in [s.lower() for s in syn_list]:
                return canonical

        return name_lower

    def _elements_match(self, user_elem: FormulationElement, evidence_elem: FormulationElement) -> bool:
        """Check if two elements match, with type-appropriate logic."""
        if user_elem.element_type != evidence_elem.element_type:
            return False

        if user_elem.element_type == "ingredient":
            return self._get_canonical_name(user_elem.name) == self._get_canonical_name(evidence_elem.name)

        elif user_elem.element_type == "ratio":
            # Exact ratio string comparison
            user_val = (user_elem.value or user_elem.name).replace(" ", "")
            ev_val = (evidence_elem.value or evidence_elem.name).replace(" ", "")
            return user_val == ev_val

        elif user_elem.element_type == "process":
            # Keyword overlap for processes
            user_tokens = set(user_elem.name.lower().split())
            ev_tokens = set(evidence_elem.name.lower().split())
            overlap = user_tokens & ev_tokens
            return len(overlap) >= max(1, len(user_tokens) // 2)

        elif user_elem.element_type == "intended_use":
            # Keyword overlap for intended uses
            user_tokens = set(user_elem.name.lower().split())
            ev_tokens = set(evidence_elem.name.lower().split())
            return bool(user_tokens & ev_tokens)

        else:
            # Dosage form or other — exact match
            return user_elem.name.lower().strip() == evidence_elem.name.lower().strip()

    def build_comparison(
        self,
        formulation: StructuredFormulation,
        evidence_sources: List[EvidenceSource],
    ) -> ComparisonMatrix:
        """Build the full element-wise comparison matrix.

        For each user element, checks presence in each evidence source.
        Calculates per-source overlap scores.
        """
        if not evidence_sources:
            return ComparisonMatrix(
                user_formulation=formulation,
                evidence_sources=[],
                comparisons=[],
                overlap_scores={},
            )

        all_user_elements = formulation.all_elements
        comparisons: List[ElementComparison] = []

        # Per-source match tracking for overlap calculation
        source_match_counts: Dict[str, int] = {
            s.source_id: 0 for s in evidence_sources
        }

        for user_elem in all_user_elements:
            matches: Dict[str, bool] = {}

            for source in evidence_sources:
                found = False
                for ev_elem in source.extracted_elements:
                    if self._elements_match(user_elem, ev_elem):
                        found = True
                        break
                matches[source.source_id] = found
                if found:
                    source_match_counts[source.source_id] += 1

            comparisons.append(
                ElementComparison(
                    element_name=user_elem.name,
                    element_type=user_elem.element_type,
                    user_has=True,
                    matches=matches,
                )
            )

        # Calculate per-source overlap scores
        total_elements = max(len(all_user_elements), 1)
        overlap_scores: Dict[str, float] = {
            source_id: round(count / total_elements, 3)
            for source_id, count in source_match_counts.items()
        }

        logger.info(
            f"Comparison matrix: {len(comparisons)} elements × "
            f"{len(evidence_sources)} sources. "
            f"Max overlap: {max(overlap_scores.values()) if overlap_scores else 0:.1%}"
        )

        return ComparisonMatrix(
            user_formulation=formulation,
            evidence_sources=evidence_sources,
            comparisons=comparisons,
            overlap_scores=overlap_scores,
        )


comparator_service = FormulationComparator()
