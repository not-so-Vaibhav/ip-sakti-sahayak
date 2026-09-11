"""Confidence Scoring and Abstention Module for IP-SAKTI Sahayak.

Calculates confidence based on top retrieval score and corroboration count.
Triggers explicit abstention when below threshold or when 0 chunks survive pre-filter.
"""

from typing import List, Optional, Tuple
from backend.app.config import settings
from backend.app.retrieval.models import RetrievedChunk


class ConfidenceEvaluator:
    def __init__(
        self,
        threshold: Optional[float] = None,
        corroboration_floor: float = 0.45,
    ):
        self.threshold = threshold if threshold is not None else settings.confidence_threshold
        self.corroboration_floor = corroboration_floor

    def evaluate(
        self,
        chunks: List[RetrievedChunk],
        threshold_override: Optional[float] = None,
    ) -> Tuple[float, bool, Optional[str], int, float]:
        """
        Evaluates retrieval chunks and returns:
        (confidence_score, abstained, abstention_reason, corroborating_count, top_score)
        """
        active_threshold = threshold_override if threshold_override is not None else self.threshold

        if not chunks:
            return (
                0.0,
                True,
                "No legal authorities or statutory provisions found matching the selected jurisdiction and formulation category.",
                0,
                0.0,
            )

        top_chunk = chunks[0]
        top_score = top_chunk.combined_score

        # Count corroborating chunks scoring above corroboration_floor
        corroborating_count = sum(1 for c in chunks if c.combined_score >= self.corroboration_floor)

        # Corroboration weighting multiplier
        if corroborating_count >= 2:
            corroboration_factor = 1.0
        elif corroborating_count == 1:
            corroboration_factor = 0.85
        else:
            corroboration_factor = 0.60

        raw_confidence = top_score * corroboration_factor
        confidence_score = round(min(1.0, max(0.0, raw_confidence)), 3)

        if confidence_score < active_threshold:
            abstained = True
            reason = (
                f"Retrieval confidence score ({confidence_score:.3f}) is below the minimum threshold ({active_threshold:.2f}). "
                "The legal authorities retrieved are insufficient or too ambiguous to formulate a definitive answer."
            )
        else:
            abstained = False
            reason = None

        return (confidence_score, abstained, reason, corroborating_count, round(top_score, 4))


def evaluate_retrieval_confidence(
    chunks: List[RetrievedChunk],
    threshold: Optional[float] = None,
    corroboration_floor: float = 0.45,
) -> Tuple[float, bool, Optional[str], int, float]:
    evaluator = ConfidenceEvaluator(threshold=threshold, corroboration_floor=corroboration_floor)
    return evaluator.evaluate(chunks)
