"""Scanner orchestration for the Vyom desktop application.

The scanner engine is intentionally modular so future versions can swap the
mock universe for live market data without changing the surrounding workflow.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping, Optional, Sequence

from app.scanner.filters import FilterEngine
from app.scanner.scoring import ScoringEngine

logger = logging.getLogger(__name__)


class ScannerEngine:
    """Orchestrate scanning, filtering, scoring, and ranking of candidates."""

    def __init__(
        self,
        scoring_engine: Optional[ScoringEngine] = None,
        filter_engine: Optional[FilterEngine] = None,
        logger_instance: Optional[logging.Logger] = None,
    ) -> None:
        """Create a scanner engine.

        Args:
            scoring_engine: Optional scoring engine implementation.
            filter_engine: Optional filtering engine implementation.
            logger_instance: Optional logger for diagnostics.
        """

        self.scoring_engine = scoring_engine or ScoringEngine()
        self.filter_engine = filter_engine or FilterEngine()
        self.logger = logger_instance or logger

    def scan(self, limit: int = 10, universe: Optional[Sequence[Mapping[str, Any]]] = None) -> list[dict[str, Any]]:
        """Scan a universe of stocks and return ranked results.

        Args:
            limit: Maximum number of results to return.
            universe: Optional predefined universe of candidates. When omitted,
                mock stock data is generated.

        Returns:
            A list of ranked scan results.
        """

        candidates = list(universe or self._build_mock_universe())
        if not candidates:
            self.logger.warning("No candidates available for scanning")
            return []

        self.logger.info("Scanning %d candidates", len(candidates))
        filtered_candidates = self.filter_engine.filter_candidates(candidates)
        scored_results: list[dict[str, Any]] = []

        for candidate in filtered_candidates:
            score = self.scoring_engine.score_candidate(candidate)
            reasons = self._build_reasons(candidate, score)
            scored_results.append(
                {
                    "symbol": candidate["symbol"],
                    "name": candidate.get("name", candidate["symbol"]),
                    "sector": candidate.get("sector", "Unknown"),
                    "score": score,
                    "price": candidate.get("price"),
                    "momentum": candidate.get("momentum"),
                    "volume": candidate.get("volume"),
                    "quality": candidate.get("quality"),
                    "reasons": reasons,
                }
            )

        scored_results.sort(key=lambda item: item["score"], reverse=True)
        self.logger.info("Scanner produced %d ranked results", len(scored_results))
        return scored_results[:limit]

    def _build_mock_universe(self) -> list[dict[str, Any]]:
        """Return a small mock universe of stocks for development use."""

        return [
            {
                "symbol": "RELIANCE",
                "name": "Reliance Industries",
                "sector": "Energy",
                "price": 2700.0,
                "momentum": 88.0,
                "volume": 4_500_000.0,
                "quality": 90.0,
                "volatility": 0.035,
                "volume_score": 92.0,
                "price_score": 88.0,
            },
            {
                "symbol": "TCS",
                "name": "Tata Consultancy Services",
                "sector": "Technology",
                "price": 3600.0,
                "momentum": 78.0,
                "volume": 2_300_000.0,
                "quality": 82.0,
                "volatility": 0.042,
                "volume_score": 76.0,
                "price_score": 70.0,
            },
            {
                "symbol": "HDFCBANK",
                "name": "HDFC Bank",
                "sector": "Financials",
                "price": 1680.0,
                "momentum": 71.0,
                "volume": 1_800_000.0,
                "quality": 74.0,
                "volatility": 0.039,
                "volume_score": 68.0,
                "price_score": 74.0,
            },
            {
                "symbol": "INFY",
                "name": "Infosys",
                "sector": "Technology",
                "price": 1450.0,
                "momentum": 62.0,
                "volume": 900_000.0,
                "quality": 58.0,
                "volatility": 0.05,
                "volume_score": 55.0,
                "price_score": 60.0,
            },
        ]

    def _build_reasons(self, candidate: Mapping[str, Any], score: int) -> list[str]:
        """Create concise human-readable reasons for a scored result."""

        reasons: list[str] = []
        if score >= 80:
            reasons.append("Strong overall momentum")
        elif score >= 65:
            reasons.append("Solid risk-adjusted profile")
        else:
            reasons.append("Moderate setup")

        if float(candidate.get("quality", 0)) >= 80:
            reasons.append("High quality")
        if float(candidate.get("volume", 0)) >= 2_000_000:
            reasons.append("Healthy trading volume")
        if float(candidate.get("volatility", 0)) <= 0.04:
            reasons.append("Low volatility")

        return reasons
