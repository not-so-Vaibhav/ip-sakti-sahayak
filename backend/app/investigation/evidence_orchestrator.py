"""Evidence Orchestrator for IP Investigation System.

Fans out searches to all evidence sources concurrently, normalizes results,
and deduplicates by title similarity.
"""

import asyncio
import logging
from typing import Dict, List, Set

from backend.app.investigation.models import (
    EvidenceSource,
    EvidenceSourceType,
    StructuredFormulation,
)
from backend.app.investigation.patent_search import patent_search_service
from backend.app.investigation.research_search import research_search_service
from backend.app.investigation.tk_formulation_search import tk_search_service

logger = logging.getLogger(__name__)


def _tokenize(text: str) -> Set[str]:
    """Simple whitespace tokenizer for deduplication."""
    return set(text.lower().split())


def _jaccard_similarity(a: str, b: str) -> float:
    """Jaccard similarity between two tokenized strings."""
    tokens_a = _tokenize(a)
    tokens_b = _tokenize(b)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


def _deduplicate_evidence(sources: List[EvidenceSource], threshold: float = 0.7) -> List[EvidenceSource]:
    """Remove near-duplicate evidence sources by title similarity."""
    unique: List[EvidenceSource] = []
    for src in sources:
        is_dup = False
        for existing in unique:
            if _jaccard_similarity(src.title, existing.title) >= threshold:
                # Keep the one with higher relevance
                if src.relevance_score > existing.relevance_score:
                    unique.remove(existing)
                    unique.append(src)
                is_dup = True
                break
        if not is_dup:
            unique.append(src)
    return unique


class EvidenceOrchestrator:
    """Orchestrates multi-source evidence retrieval for an investigation."""

    async def search_all_sources(
        self,
        formulation: StructuredFormulation,
        jurisdiction: str = "india",
        formulation_category: str = "classical_generic",
    ) -> List[EvidenceSource]:
        """Fan out searches to all sources concurrently, normalize, and deduplicate.

        Sources:
        1. Patent search (SerpAPI or seed data)
        2. Research paper search (Semantic Scholar)
        3. TK / classical formulation search (seed data + existing corpus)
        """
        # Run all searches concurrently with individual error isolation
        patent_task = asyncio.create_task(
            self._safe_search("patents", patent_search_service.search, formulation, jurisdiction)
        )
        research_task = asyncio.create_task(
            self._safe_search("research", research_search_service.search, formulation, jurisdiction)
        )
        tk_task = asyncio.create_task(
            self._safe_search("tk_formulations", tk_search_service.search, formulation, jurisdiction)
        )

        results = await asyncio.gather(patent_task, research_task, tk_task)

        # Flatten all results
        all_evidence: List[EvidenceSource] = []
        source_names = ["patents", "research", "tk_formulations"]
        for name, evidence_list in zip(source_names, results):
            logger.info(f"Evidence from {name}: {len(evidence_list)} results")
            all_evidence.extend(evidence_list)

        # Deduplicate by title similarity
        deduplicated = _deduplicate_evidence(all_evidence)

        # Sort by relevance_score descending
        deduplicated.sort(key=lambda x: x.relevance_score, reverse=True)

        logger.info(
            f"Evidence orchestrator: {len(all_evidence)} total → "
            f"{len(deduplicated)} after dedup"
        )
        return deduplicated

    async def _safe_search(
        self,
        source_name: str,
        search_fn,
        formulation: StructuredFormulation,
        jurisdiction: str,
    ) -> List[EvidenceSource]:
        """Run a single search with error isolation and timeout."""
        try:
            return await asyncio.wait_for(
                search_fn(formulation, jurisdiction),
                timeout=30.0,
            )
        except asyncio.TimeoutError:
            logger.warning(f"{source_name} search timed out after 30s")
            return []
        except Exception as e:
            logger.error(f"{source_name} search failed: {e}")
            return []


evidence_orchestrator = EvidenceOrchestrator()
