"""Patent Search Module for IP Investigation System.

Searches for existing patents related to a formulation using:
1. SerpAPI / Google Custom Search (if API key configured)
2. Curated seed dataset of landmark Ayurvedic patent cases (fallback)
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import httpx

from backend.app.config import settings
from backend.app.investigation.models import (
    EvidenceSource,
    EvidenceSourceType,
    FormulationElement,
    StructuredFormulation,
)

logger = logging.getLogger(__name__)


class PatentSearchService:
    """Searches patent databases for prior art matching the user's formulation."""

    def __init__(self):
        self._seed_patents: Optional[List[Dict]] = None

    def _load_seed_patents(self) -> List[Dict]:
        """Load curated seed patents from config."""
        if self._seed_patents is not None:
            return self._seed_patents

        seed_path = settings.resolve_path(
            getattr(settings, "seed_patents_path", "config/seed_patents.json")
        )
        if seed_path.exists():
            with open(seed_path, "r", encoding="utf-8") as f:
                self._seed_patents = json.load(f)
        else:
            logger.warning(f"Seed patents file not found: {seed_path}")
            self._seed_patents = []
        return self._seed_patents

    def _build_search_query(self, formulation: StructuredFormulation) -> str:
        """Build a search query string from extracted formulation elements."""
        parts = []
        for ing in formulation.ingredients[:5]:  # Limit to top 5
            parts.append(ing.name)
        for use in formulation.intended_uses[:2]:
            parts.append(use.name)
        for proc in formulation.processes[:2]:
            parts.append(proc.name)
        return " ".join(parts) + " ayurvedic patent"

    async def _search_serpapi(
        self, query: str, jurisdiction: str
    ) -> List[EvidenceSource]:
        """Search Google Patents via SerpAPI (requires API key)."""
        api_key = getattr(settings, "serpapi_key", None)
        if not api_key:
            return []

        try:
            params = {
                "engine": "google_patents",
                "q": query,
                "api_key": api_key,
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(
                    "https://serpapi.com/search", params=params
                )
                res.raise_for_status()
                data = res.json()

            results = []
            for item in data.get("organic_results", [])[:10]:
                results.append(
                    EvidenceSource(
                        source_type=EvidenceSourceType.PATENT,
                        title=item.get("title", "Unknown Patent"),
                        identifier=item.get("patent_id", ""),
                        url=item.get("pdf", item.get("link", "")),
                        publication_date=item.get("priority_date", ""),
                        relevant_text=item.get("snippet", ""),
                        relevance_score=0.7,
                        jurisdiction=jurisdiction,
                    )
                )
            return results
        except Exception as e:
            logger.warning(f"SerpAPI patent search failed: {e}")
            return []

    def _search_seed_data(
        self,
        formulation: StructuredFormulation,
        jurisdiction: str,
    ) -> List[EvidenceSource]:
        """Search curated seed patents by ingredient overlap."""
        seed_patents = self._load_seed_patents()
        if not seed_patents:
            return []

        user_ingredients = {
            ing.name.lower() for ing in formulation.ingredients
        }
        user_uses = {use.name.lower() for use in formulation.intended_uses}

        scored_results: List[tuple] = []
        for patent in seed_patents:
            patent_ingredients = {i.lower() for i in patent.get("ingredients", [])}
            patent_uses = {u.lower() for u in patent.get("intended_uses", [])}

            # Score by ingredient + use overlap
            ing_overlap = len(user_ingredients & patent_ingredients)
            use_overlap = len(user_uses & patent_uses)

            if ing_overlap == 0 and use_overlap == 0:
                continue

            total_user = len(user_ingredients) + len(user_uses)
            score = (ing_overlap + use_overlap * 0.5) / max(total_user, 1)
            score = min(1.0, score)

            # Build extracted elements from patent data
            extracted = []
            for ing in patent.get("ingredients", []):
                extracted.append(
                    FormulationElement(name=ing, element_type="ingredient")
                )
            for proc in patent.get("processes", []):
                extracted.append(
                    FormulationElement(name=proc, element_type="process")
                )
            for use in patent.get("intended_uses", []):
                extracted.append(
                    FormulationElement(name=use, element_type="intended_use")
                )

            source = EvidenceSource(
                source_type=EvidenceSourceType.PATENT,
                title=patent.get("title", "Unknown Patent"),
                identifier=patent.get("patent_number", ""),
                url=patent.get("source_url", ""),
                publication_date=patent.get("filing_date", ""),
                relevant_text=(
                    f"{patent.get('abstract', '')} "
                    f"Outcome: {patent.get('outcome', 'Unknown')}"
                ).strip(),
                extracted_elements=extracted,
                relevance_score=round(score, 3),
                jurisdiction=patent.get("jurisdiction", jurisdiction),
            )
            scored_results.append((score, source))

        # Sort by relevance descending
        scored_results.sort(key=lambda x: x[0], reverse=True)
        max_results = getattr(settings, "max_evidence_per_source", 10)
        return [s for _, s in scored_results[:max_results]]

    async def search(
        self,
        formulation: StructuredFormulation,
        jurisdiction: str = "india",
    ) -> List[EvidenceSource]:
        """Search for patents — tries live API first, falls back to seed data."""
        # Try live API search
        query = self._build_search_query(formulation)
        live_results = await self._search_serpapi(query, jurisdiction)

        if live_results:
            logger.info(f"Patent search: {len(live_results)} live results for '{query[:50]}'")
            return live_results

        # Fallback to seed data
        seed_results = self._search_seed_data(formulation, jurisdiction)
        logger.info(f"Patent search: {len(seed_results)} seed results (API unavailable)")
        return seed_results


patent_search_service = PatentSearchService()
