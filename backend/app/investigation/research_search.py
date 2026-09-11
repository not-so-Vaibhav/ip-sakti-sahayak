"""Research Paper Search Module for IP Investigation System.

Searches for published research papers using:
1. Semantic Scholar API (free, no key required for basic search)
2. Fallback: returns empty results with a warning
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

import httpx

from backend.app.config import settings
from backend.app.investigation.models import (
    EvidenceSource,
    EvidenceSourceType,
    FormulationElement,
    StructuredFormulation,
)

logger = logging.getLogger(__name__)

SEMANTIC_SCHOLAR_BASE = "https://api.semanticscholar.org/graph/v1/paper/search"


class ResearchSearchService:
    """Searches academic databases for published research on formulation ingredients."""

    def _build_search_query(self, formulation: StructuredFormulation) -> str:
        """Build an academic search query from formulation elements."""
        parts = []
        for ing in formulation.ingredients[:3]:
            parts.append(ing.name)
        for use in formulation.intended_uses[:2]:
            parts.append(use.name)
        # Add domain context
        parts.append("ayurvedic pharmacology")
        return " ".join(parts)

    def _extract_elements_from_abstract(
        self, abstract: str, formulation: StructuredFormulation
    ) -> List[FormulationElement]:
        """Simple keyword-based element extraction from paper abstracts."""
        elements = []
        abstract_lower = abstract.lower()

        # Check which user ingredients are mentioned
        for ing in formulation.ingredients:
            if ing.name.lower() in abstract_lower:
                elements.append(
                    FormulationElement(
                        name=ing.name,
                        element_type="ingredient",
                    )
                )

        # Check processes
        for proc in formulation.processes:
            if proc.name.lower() in abstract_lower:
                elements.append(
                    FormulationElement(
                        name=proc.name,
                        element_type="process",
                    )
                )

        # Check intended uses
        for use in formulation.intended_uses:
            if use.name.lower() in abstract_lower:
                elements.append(
                    FormulationElement(
                        name=use.name,
                        element_type="intended_use",
                    )
                )

        return elements

    async def search(
        self,
        formulation: StructuredFormulation,
        jurisdiction: str = "india",
    ) -> List[EvidenceSource]:
        """Search Semantic Scholar for relevant research papers."""
        query = self._build_search_query(formulation)
        max_results = getattr(settings, "max_evidence_per_source", 10)
        timeout = getattr(settings, "semantic_scholar_timeout", 10.0)

        try:
            params = {
                "query": query,
                "limit": max_results,
                "fields": "title,abstract,year,authors,externalIds,url",
            }
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.get(SEMANTIC_SCHOLAR_BASE, params=params)
                res.raise_for_status()
                data = res.json()

            results = []
            for paper in data.get("data", []):
                title = paper.get("title", "Untitled")
                abstract = paper.get("abstract") or ""
                year = paper.get("year")
                external_ids = paper.get("externalIds") or {}
                doi = external_ids.get("DOI", "")
                paper_url = paper.get("url") or (
                    f"https://doi.org/{doi}" if doi else ""
                )

                # Extract elements from abstract
                extracted = self._extract_elements_from_abstract(
                    abstract, formulation
                )

                # Score by number of matching elements
                total_user_elements = len(formulation.all_elements)
                match_count = len(extracted)
                relevance = (
                    match_count / max(total_user_elements, 1)
                    if total_user_elements > 0
                    else 0.3
                )
                relevance = min(1.0, relevance + 0.2)  # Base boost for being found

                results.append(
                    EvidenceSource(
                        source_type=EvidenceSourceType.RESEARCH_PAPER,
                        title=title,
                        identifier=doi or None,
                        url=paper_url,
                        publication_date=str(year) if year else None,
                        relevant_text=abstract[:500] if abstract else title,
                        extracted_elements=extracted,
                        relevance_score=round(relevance, 3),
                        jurisdiction="international",
                    )
                )

            logger.info(
                f"Research search: {len(results)} papers found for '{query[:50]}'"
            )
            return results

        except httpx.TimeoutException:
            logger.warning(f"Semantic Scholar API timed out after {timeout}s")
            return []
        except Exception as e:
            logger.warning(f"Research paper search failed: {e}")
            return []


research_search_service = ResearchSearchService()
