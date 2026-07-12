"""Filtering utilities for the Vyom scanner engine.

The filter engine keeps the scanning workflow modular by separating stock
eligibility checks from scoring and orchestration.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping, Optional

logger = logging.getLogger(__name__)


class FilterEngine:
    """Filter out unsuitable stock candidates based on configurable rules."""

    DEFAULT_RULES: dict[str, float] = {
        "min_price": 50.0,
        "max_volatility": 0.06,
        "min_volume": 1_000_000.0,
        "min_quality": 55.0,
    }

    def __init__(self, rules: Optional[Mapping[str, float]] = None) -> None:
        """Create a filter engine with optional overrides.

        Args:
            rules: Optional overrides for the filter thresholds.
        """

        self.rules = dict(self.DEFAULT_RULES)
        if rules:
            self.rules.update({key: float(value) for key, value in rules.items()})
        self.logger = logger

    def filter_candidates(self, candidates: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
        """Return only candidates that satisfy the configured rules.

        Args:
            candidates: Candidate stock records to evaluate.

        Returns:
            A filtered list of candidates.
        """

        filtered_candidates: list[dict[str, Any]] = []
        for candidate in candidates:
            if self.passes(candidate):
                filtered_candidates.append(dict(candidate))

        self.logger.debug("Filtered %d candidates down to %d", len(candidates), len(filtered_candidates))
        return filtered_candidates

    def passes(self, candidate: Mapping[str, Any]) -> bool:
        """Return True when a candidate passes the configured filter rules."""

        price = float(candidate.get("price", 0.0))
        volatility = float(candidate.get("volatility", 0.0))
        volume = float(candidate.get("volume", 0.0))
        quality = float(candidate.get("quality", 0.0))

        if price < self.rules["min_price"]:
            return False
        if volatility > self.rules["max_volatility"]:
            return False
        if volume < self.rules["min_volume"]:
            return False
        if quality < self.rules["min_quality"]:
            return False

        return True
