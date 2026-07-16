"""
Ranking engine for ordering trade recommendations.

This module is responsible only for ranking recommendations.
It does not filter, score, print, or modify recommendations.
"""

from __future__ import annotations

from app.scanner.decision_engine import TradeRecommendation


QUALITY_ORDER = {
    "A+": 5,
    "A": 4,
    "B": 3,
    "C": 2,
    "REJECT": 1,
}


class RankingEngine:
    """
    Rank trade recommendations from best to worst.

    Ranking Priority:
        1. Total Score
        2. Confidence
        3. Trade Quality
        4. Volume Score
        5. Momentum Score
    """

    def rank(
        self,
        recommendations: list[TradeRecommendation],
    ) -> list[TradeRecommendation]:
        """
        Return recommendations sorted in descending order.
        """

        if not recommendations:
            return []

        return sorted(
            recommendations,
            key=self._sort_key,
            reverse=True,
        )

    def _sort_key(
        self,
        recommendation: TradeRecommendation,
    ) -> tuple[int, float, int, int, int]:
        """
        Multi-level sorting key.

        Higher values receive higher priority.
        """

        return (
            recommendation.total_score,
            recommendation.confidence,
            QUALITY_ORDER.get(recommendation.trade_quality, 0),
            recommendation.volume_score,
            recommendation.momentum_score,
        )