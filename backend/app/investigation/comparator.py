"""Element-Wise Comparison Engine for IP Investigation System.

Builds structured comparison matrices between user's formulation and
all retrieved evidence sources, using synonym-aware ingredient matching.
"""

import json
import logging
import re
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

    def _resolve_canonical_candidates(self, name: str) -> Set[str]:
        """Resolve a text string to all canonical ingredient keys it contains or references.
        
        Handles:
        - Direct key match ("turmeric")
        - Synonym list match ("haridra" -> "turmeric")
        - Parenthetical annotations ("haridra (turmeric)" -> {"turmeric"})
        - Multi-word botanical substrings ("Curcuma longa rhizome extract" -> {"turmeric"})
        """
        synonyms = self._load_synonyms()
        name_lower = name.lower().strip()
        candidates: Set[str] = set()

        # 1. Direct match on full string
        if name_lower in synonyms:
            candidates.add(name_lower)

        for canonical, syn_list in synonyms.items():
            if name_lower in [s.lower() for s in syn_list]:
                candidates.add(canonical)

        # 2. Check parenthetical contents, e.g. "haridra (turmeric)" -> "turmeric", "haridra"
        paren_matches = re.findall(r"\((.*?)\)", name_lower)
        for pm in paren_matches:
            pm_clean = pm.strip()
            if pm_clean in synonyms:
                candidates.add(pm_clean)
            for canonical, syn_list in synonyms.items():
                if pm_clean in [s.lower() for s in syn_list]:
                    candidates.add(canonical)

        # 3. Check text without parentheses, e.g. "haridra (turmeric)" -> "haridra"
        stripped = re.sub(r"\(.*?\)", "", name_lower).strip()
        if stripped in synonyms:
            candidates.add(stripped)
        for canonical, syn_list in synonyms.items():
            if stripped in [s.lower() for s in syn_list]:
                candidates.add(canonical)

        # 4. Word-boundary substring match against all canonical keys and synonyms
        for canonical, syn_list in synonyms.items():
            all_names = [canonical] + [s.lower() for s in syn_list]
            for term in all_names:
                pattern = r"\b" + re.escape(term) + r"\b"
                if re.search(pattern, name_lower):
                    candidates.add(canonical)
                    break

        # Fallback: if nothing matched, use stripped name
        if not candidates:
            candidates.add(stripped or name_lower)

        return candidates

    def _get_canonical_name(self, name: str) -> str:
        """Resolve a name to its primary canonical key via synonym map."""
        candidates = self._resolve_canonical_candidates(name)
        if candidates:
            return sorted(candidates)[0]
        return name.lower().strip()

    def _elements_match(self, user_elem: FormulationElement, evidence_elem: FormulationElement) -> bool:
        """Check if two elements match, with type-appropriate semantic logic."""
        if user_elem.element_type != evidence_elem.element_type:
            return False

        if user_elem.element_type == "ingredient":
            # Set intersection of resolved canonical candidates
            cand_user = self._resolve_canonical_candidates(user_elem.name)
            cand_ev = self._resolve_canonical_candidates(evidence_elem.name)
            if cand_user & cand_ev:
                return True
            # Substring containment fallback
            u_clean = re.sub(r"[^\w\s]", "", user_elem.name.lower()).strip()
            e_clean = re.sub(r"[^\w\s]", "", evidence_elem.name.lower()).strip()
            return u_clean in e_clean or e_clean in u_clean

        elif user_elem.element_type == "ratio":
            # Ratio comparison
            user_val = (user_elem.value or user_elem.name).lower().replace(" ", "")
            ev_val = (evidence_elem.value or evidence_elem.name).lower().replace(" ", "")

            # Direct string equality
            if user_val == ev_val:
                return True

            # Extract standard numerical ratio format X:Y or X:Y:Z
            user_ratio = re.search(r"\b\d+(?:\.\d+)?(?::\d+(?:\.\d+)?)+\b", user_val)
            ev_ratio = re.search(r"\b\d+(?:\.\d+)?(?::\d+(?:\.\d+)?)+\b", ev_val)
            if user_ratio and ev_ratio:
                if user_ratio.group(0) == ev_ratio.group(0):
                    return True

            # Check for "equal parts" / "samamsha" / "1:1" equivalence
            equal_indicators = ["1:1", "samamsha", "equal parts", "equal"]
            if any(eq in user_val for eq in equal_indicators) and any(eq in ev_val for eq in equal_indicators):
                return True

            return user_val in ev_val or ev_val in user_val

        elif user_elem.element_type == "process":
            # Keyword and synonym overlap for processes
            user_p = user_elem.name.lower().strip()
            ev_p = evidence_elem.name.lower().strip()

            if user_p == ev_p or user_p in ev_p or ev_p in user_p:
                return True

            # Process domain equivalences
            PROCESS_EQUIVALENCE = [
                {"decoction", "kwath", "kashayam", "kashaya", "boiling"},
                {"churna", "powder", "powdering", "pulverization", "trituration"},
                {"taila", "taila paka", "oil processing", "oil extraction", "medicated oil"},
                {"ghrita", "ghrita paka", "ghee processing", "medicated ghee", "clarified butter"},
                {"lepa", "paste", "topical paste", "poultice", "topical application"},
                {"avaleha", "leha", "herbal jam", "confection", "paka"},
                {"asava", "arishta", "fermentation", "fermented"},
                {"bhasma", "calcination", "marana", "shodhana", "purification"},
            ]
            for group in PROCESS_EQUIVALENCE:
                if any(term in user_p for term in group) and any(term in ev_p for term in group):
                    return True

            user_tokens = set(re.findall(r"\w+", user_p))
            ev_tokens = set(re.findall(r"\w+", ev_p))
            return bool(user_tokens & ev_tokens)

        elif user_elem.element_type == "intended_use":
            user_u = user_elem.name.lower().strip()
            ev_u = evidence_elem.name.lower().strip()

            if user_u == ev_u or user_u in ev_u or ev_u in user_u:
                return True

            # Clinical indication equivalences
            USE_EQUIVALENCE = [
                {"wound healing", "wound", "healing", "vrana", "vrana ropana", "ulcer", "ulcers"},
                {"skin inflammation", "inflammation", "shotha", "swelling", "anti-inflammatory"},
                {"skin disorders", "skin", "kustha", "dermatitis", "eczema", "psoriasis", "tvak roga"},
                {"joint pain", "arthritis", "sandhivata", "amavata", "osteoarthritis", "rheumatoid"},
                {"fever", "jvara", "pyrexia", "temperature"},
                {"digestion", "digestive", "deepana", "pachana", "indigestion", "agnimandya"},
                {"respiratory", "cough", "cold", "kasa", "shwasa", "asthma", "bronchitis"},
                {"immunity", "rasayana", "rejuvenation", "vitality", "immunomodulatory", "ojus"},
                {"diabetes", "blood sugar", "prameha", "madhumeha", "glycemic"},
                {"memory", "cognitive", "medhya", "intellect", "brain", "focus"},
            ]
            for group in USE_EQUIVALENCE:
                if any(term in user_u for term in group) and any(term in ev_u for term in group):
                    return True

            user_tokens = set(re.findall(r"\w+", user_u)) - {"and", "for", "in", "of", "the"}
            ev_tokens = set(re.findall(r"\w+", ev_u)) - {"and", "for", "in", "of", "the"}
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
