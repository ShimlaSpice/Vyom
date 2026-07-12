"""Scoring utilities for the Vyom scanner engine.

This module contains a configurable scoring engine that translates stock
characteristics into a normalized 0-100 score for ranking.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping, Optional

logger = logging.getLogger(__name__)


class ScoringEngine:
    """Score a stock candidate using configurable weighting rules."""

    DEFAULT_RULES: dict[str, float] = {
        "momentum_weight": 0.40,
        "quality_weight": 0.25,
        "volume_weight": 0.20,
        "price_weight": 0.10,
        "volatility_weight": 0.05,
    }

    def __init__(self, rules: Optional[Mapping[str, float]] = None) -> None:
        """Create a scoring engine with optional overrides.

        Args:
            rules: Optional overrides for scoring weights.
        """

        self.rules = dict(self.DEFAULT_RULES)
        if rules:
            self.rules.update({key: float(value) for key, value in rules.items()})
        self.logger = logger

    def score_candidate(self, candidate: Mapping[str, Any]) -> int:
        """Score one candidate and return an integer between 0 and 100.

        Args:
            candidate: A mapping with stock metrics such as momentum, quality,
                volume, price, and volatility.

        Returns:
            A score between 0 and 100.
        """

        momentum_score = self._coerce_score(candidate.get("momentum", 0))
        quality_score = self._coerce_score(candidate.get("quality", 0))
        volume_score = self._coerce_score(candidate.get("volume_score", 0))
        price_score = self._coerce_score(candidate.get("price_score", 0))
        volatility_score = self._volatility_score(candidate.get("volatility", 0.0))

        total_score = (
            momentum_score * self.rules["momentum_weight"]
            + quality_score * self.rules["quality_weight"]
            + volume_score * self.rules["volume_weight"]
            + price_score * self.rules["price_weight"]
            + volatility_score * self.rules["volatility_weight"]
        )

        rounded_score = round(total_score)
        return self._clamp(rounded_score, 0, 100)

    def _coerce_score(self, value: Any) -> float:
        """Normalize a metric to a 0-100 numeric score."""

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            self.logger.debug("Invalid numeric value %r; defaulting to 0", value)
            return 0.0

        return self._clamp(numeric_value, 0.0, 100.0)

    def _volatility_score(self, volatility: float) -> float:
        """Translate volatility into a score where lower volatility is better."""

        try:
            volatility_value = float(volatility)
        except (TypeError, ValueError):
            return 0.0

        normalized = max(0.0, 1.0 - volatility_value * 10.0)
        return self._clamp(normalized * 100.0, 0.0, 100.0)

    def _clamp(self, value: float, lower: float, upper: float) -> float:
        """Clamp a numeric value to a bounded range."""

        return max(lower, min(upper, value))
