"""Traditional Knowledge & Classical Formulation Search Module.

Searches for TK prior art and classical formulation matches using:
1. Existing HybridRetriever (regulation/classical corpus in Qdrant/in-memory)
2. Curated seed formulations dataset (config/seed_formulations.json)
"""

import json
import logging
from pathlib import Path
import re
from typing import Dict, List, Optional, Set

from backend.app.config import settings
from backend.app.investigation.models import (
    EvidenceSource,
    EvidenceSourceType,
    FormulationElement,
    StructuredFormulation,
)

logger = logging.getLogger(__name__)


class TKFormulationSearchService:
    """Searches TK/classical formulation corpus for overlapping prior art."""

    def __init__(self):
        self._seed_formulations: Optional[List[Dict]] = None
        self._synonyms: Optional[Dict[str, List[str]]] = None

    def _load_seed_formulations(self) -> List[Dict]:
        """Load curated classical formulations from config."""
        if self._seed_formulations is not None:
            return self._seed_formulations

        seed_path = settings.resolve_path(
            getattr(settings, "seed_formulations_path", "config/seed_formulations.json")
        )
        if seed_path.exists():
            with open(seed_path, "r", encoding="utf-8") as f:
                self._seed_formulations = json.load(f)
        else:
            logger.warning(f"Seed formulations file not found: {seed_path}")
            self._seed_formulations = []
        return self._seed_formulations

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
        """Resolve a text string to all canonical ingredient keys it contains or references."""
        synonyms = self._load_synonyms()
        name_lower = name.lower().strip()
        candidates: Set[str] = set()

        if name_lower in synonyms:
            candidates.add(name_lower)

        for canonical, syn_list in synonyms.items():
            if name_lower in [s.lower() for s in syn_list]:
                candidates.add(canonical)

        paren_matches = re.findall(r"\((.*?)\)", name_lower)
        for pm in paren_matches:
            pm_clean = pm.strip()
            if pm_clean in synonyms:
                candidates.add(pm_clean)
            for canonical, syn_list in synonyms.items():
                if pm_clean in [s.lower() for s in syn_list]:
                    candidates.add(canonical)

        stripped = re.sub(r"\(.*?\)", "", name_lower).strip()
        if stripped in synonyms:
            candidates.add(stripped)
        for canonical, syn_list in synonyms.items():
            if stripped in [s.lower() for s in syn_list]:
                candidates.add(canonical)

        for canonical, syn_list in synonyms.items():
            all_names = [canonical] + [s.lower() for s in syn_list]
            for term in all_names:
                pattern = r"\b" + re.escape(term) + r"\b"
                if re.search(pattern, name_lower):
                    candidates.add(canonical)
                    break

        if not candidates:
            candidates.add(stripped or name_lower)

        return candidates

    def _get_canonical_name(self, ingredient: str) -> str:
        """Resolve an ingredient to its canonical key using synonym map."""
        candidates = self._resolve_canonical_candidates(ingredient)
        if candidates:
            return sorted(candidates)[0]
        return ingredient.lower().strip()

    def _ingredients_match(self, name_a: str, name_b: str) -> bool:
        """Check if two ingredient names refer to the same substance."""
        cand_a = self._resolve_canonical_candidates(name_a)
        cand_b = self._resolve_canonical_candidates(name_b)
        return bool(cand_a & cand_b)

    def _search_seed_formulations(
        self,
        formulation: StructuredFormulation,
    ) -> List[EvidenceSource]:
        """Search curated classical formulations by ingredient overlap."""
        seed_data = self._load_seed_formulations()
        if not seed_data:
            return []

        user_ingredients_canonical: Set[str] = set()
        for ing in formulation.ingredients:
            user_ingredients_canonical.update(self._resolve_canonical_candidates(ing.name))

        results: List[tuple] = []
        for form in seed_data:
            # Build canonical ingredient set for this classical formulation
            form_ingredients_canonical: Set[str] = set()
            all_ing_names = form.get("ingredients", []) + form.get("botanical_names", [])
            for name in all_ing_names:
                form_ingredients_canonical.update(self._resolve_canonical_candidates(name))

            # Calculate overlap
            overlap = user_ingredients_canonical & form_ingredients_canonical
            if not overlap:
                continue

            overlap_ratio = len(overlap) / max(len(user_ingredients_canonical), 1)

            # Build extracted elements
            extracted = []
            for ing in form.get("ingredients", []):
                extracted.append(
                    FormulationElement(name=ing, element_type="ingredient")
                )
            for ratio in form.get("ratios", []):
                if ratio:
                    extracted.append(
                        FormulationElement(
                            name=f"ratio {ratio}",
                            element_type="ratio",
                            value=ratio,
                        )
                    )
            for proc in form.get("processes", []):
                extracted.append(
                    FormulationElement(name=proc, element_type="process")
                )
            for use in form.get("intended_uses", []):
                extracted.append(
                    FormulationElement(name=use, element_type="intended_use")
                )

            source = EvidenceSource(
                source_type=EvidenceSourceType.TK_SOURCE,
                title=f"{form.get('name', 'Unknown')} (Classical Formulation)",
                identifier=form.get("tkdl_classification", ""),
                url=None,
                publication_date=None,
                relevant_text=(
                    f"Classical Text: {form.get('classical_text', 'Unknown')}. "
                    f"Ingredients: {', '.join(form.get('ingredients', []))}. "
                    f"Uses: {', '.join(form.get('intended_uses', []))}."
                ),
                extracted_elements=extracted,
                relevance_score=round(overlap_ratio, 3),
                jurisdiction="india",
            )
            results.append((overlap_ratio, source))

        results.sort(key=lambda x: x[0], reverse=True)
        max_results = getattr(settings, "max_evidence_per_source", 10)
        return [s for _, s in results[:max_results]]

    def _search_existing_corpus(
        self,
        formulation: StructuredFormulation,
        jurisdiction: str,
    ) -> List[EvidenceSource]:
        """Search existing legal/TK corpus via existing retrieval service."""
        from backend.app.retrieval.service import retrieval_service

        # Build query from formulation ingredients
        query_parts = [ing.name for ing in formulation.ingredients[:5]]
        query_parts.extend([use.name for use in formulation.intended_uses[:2]])
        query_text = " ".join(query_parts) + " traditional knowledge prior art"

        try:
            result = retrieval_service.retrieve(
                query_text=query_text,
                jurisdiction=jurisdiction,
                formulation_category="classical_generic",
                top_k=5,
            )

            evidence = []
            for chunk in result.chunks:
                evidence.append(
                    EvidenceSource(
                        source_type=EvidenceSourceType.REGULATION,
                        title=chunk.instrument_name,
                        identifier=chunk.section_number,
                        url=chunk.source_url,
                        relevant_text=chunk.text_content[:500],
                        relevance_score=round(chunk.combined_score, 3),
                        jurisdiction=chunk.jurisdiction,
                    )
                )
            return evidence
        except Exception as e:
            logger.warning(f"Existing corpus TK search failed: {e}")
            return []

    async def search(
        self,
        formulation: StructuredFormulation,
        jurisdiction: str = "india",
    ) -> List[EvidenceSource]:
        """Search for TK prior art and classical formulation matches."""
        # Search curated seed formulations
        seed_results = self._search_seed_formulations(formulation)
        logger.info(
            f"TK search: {len(seed_results)} classical formulation matches found"
        )

        # Search existing legal/TK corpus
        corpus_results = self._search_existing_corpus(formulation, jurisdiction)
        logger.info(
            f"TK search: {len(corpus_results)} corpus regulation matches found"
        )

        # Merge and deduplicate
        all_results = seed_results + corpus_results
        all_results.sort(key=lambda x: x.relevance_score, reverse=True)

        max_results = getattr(settings, "max_evidence_per_source", 10)
        return all_results[:max_results]


tk_search_service = TKFormulationSearchService()
