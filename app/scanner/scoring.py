"""Scoring utilities for the Vyom scanner engine.

This module contains a configurable scoring engine that translates stock
characteristics into a normalized 0-100 score for ranking.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ScoreResult:
    """Detailed score output for a single stock."""

    symbol: str
    total_score: int
    recommendation: str
    confidence: float
    technical_score: int
    momentum_score: int
    volume_score: int
    market_score: int
    news_score: int
    reasons: list[str] = field(default_factory=list)


class ScoringEngine:
    """Score a stock candidate using configurable weighting rules."""

    DEFAULT_RULES: dict[str, float] = {
        "technical_weight": 0.40,
        "momentum_weight": 0.20,
        "volume_weight": 0.15,
        "market_weight": 0.15,
        "news_weight": 0.10,
    }

    DEFAULT_THRESHOLDS: dict[str, float] = {
        "buy_threshold": 80.0,
        "watch_threshold": 60.0,
        "rsi_lower": 55.0,
        "rsi_upper": 70.0,
        "relative_volume_buy": 1.5,
        "relative_volume_watch": 1.0,
        "momentum_strong": 6.0,
        "momentum_watch": 2.0,
    }

    CATEGORY_MAXIMUMS: dict[str, int] = {
        "technical": 40,
        "momentum": 20,
        "volume": 15,
        "market": 15,
        "news": 10,
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
            candidate: A mapping with stock metrics used by the scoring engine.

        Returns:
            A score between 0 and 100.
        """

        return self.score_stock(candidate).total_score

    def score_stock(self, candidate: Mapping[str, Any]) -> ScoreResult:
        """Score a stock and return the full structured result payload.

        The implementation evaluates price trend, momentum, volume, market,
        and news indicators independently so the result can be surfaced in a UI
        without coupling the scoring logic to a specific presentation layer.
        """

        if not candidate:
            return self._build_result("", 0, "AVOID", 0.0, 0, 0, 0, 0, 0, ["Insufficient data"])

        symbol = str(candidate.get("symbol") or "UNKNOWN").strip().upper()
        technical_score = self._score_technical(candidate)
        momentum_score = self._score_momentum(candidate)
        volume_score = self._score_volume(candidate)
        market_score = self._score_market(candidate)
        news_score = self._score_news(candidate)

        total_score = self._calculate_total_score(
            technical_score,
            momentum_score,
            volume_score,
            market_score,
            news_score,
        )
        recommendation = self._recommendation(total_score)
        confidence = self._calculate_confidence(candidate, total_score, technical_score, momentum_score, volume_score, market_score, news_score)
        reasons = self._build_reasons(candidate, technical_score, momentum_score, volume_score, market_score, news_score)

        return self._build_result(
            symbol=symbol,
            total_score=total_score,
            recommendation=recommendation,
            confidence=confidence,
            technical_score=technical_score,
            momentum_score=momentum_score,
            volume_score=volume_score,
            market_score=market_score,
            news_score=news_score,
            reasons=reasons,
        )

    def _score_technical(self, candidate: Mapping[str, Any]) -> int:
        """Score the technical setup on a 0-40 scale."""

        score = 0
        reasons: list[str] = []

        price = self._coerce_float(candidate.get("price"))
        ema20 = self._coerce_float(candidate.get("ema20"))
        ema50 = self._coerce_float(candidate.get("ema50"))
        rsi = self._coerce_float(candidate.get("rsi"))
        macd = self._coerce_float(candidate.get("macd"))

        if price and ema20 and price > ema20:
            score += 10
            reasons.append("Above EMA20")
        elif price and ema20 and price < ema20:
            reasons.append("Price below EMA20")

        if ema20 and ema50 and ema20 > ema50:
            score += 10
            reasons.append("EMA20 above EMA50")

        if self._has_value(rsi) and self._thresholds("rsi_lower") <= rsi <= self._thresholds("rsi_upper"):
            score += 10
            reasons.append("RSI in healthy range")

        if self._has_value(macd) and macd > 0:
            score += 10
            reasons.append("MACD bullish")

        if not any(self._has_value(value) for value in (price, ema20, ema50, rsi, macd)):
            return 0

        return self._clamp(score, 0, self.CATEGORY_MAXIMUMS["technical"])

    def _score_momentum(self, candidate: Mapping[str, Any]) -> int:
        """Score momentum on a 0-20 scale."""

        momentum = self._coerce_float(candidate.get("momentum"))
        trend_continuation = bool(candidate.get("trend_continuation"))

        if not self._has_value(momentum):
            return 0

        base_score = int(round(min(self.CATEGORY_MAXIMUMS["momentum"], max(0.0, momentum * 2.0))))
        if trend_continuation:
            base_score = min(self.CATEGORY_MAXIMUMS["momentum"], base_score + 2)

        if momentum >= self._thresholds("momentum_strong"):
            return self._clamp(base_score, 0, self.CATEGORY_MAXIMUMS["momentum"])
        if momentum >= self._thresholds("momentum_watch"):
            return self._clamp(base_score, 0, self.CATEGORY_MAXIMUMS["momentum"])
        return self._clamp(base_score, 0, self.CATEGORY_MAXIMUMS["momentum"])

    def _score_volume(self, candidate: Mapping[str, Any]) -> int:
        """Score relative volume behavior on a 0-15 scale."""

        relative_volume = self._coerce_float(candidate.get("relative_volume"))
        volume_spike = bool(candidate.get("volume_spike"))

        if not self._has_value(relative_volume):
            return 0

        if relative_volume >= self._thresholds("relative_volume_buy") and volume_spike:
            return self.CATEGORY_MAXIMUMS["volume"]
        if relative_volume >= self._thresholds("relative_volume_watch"):
            return 10
        return 2

    def _score_market(self, candidate: Mapping[str, Any]) -> int:
        """Return a neutral placeholder market score for now."""

        regime = str(candidate.get("market_regime") or "neutral").strip().lower()
        if regime == "bullish":
            return 12
        if regime == "bearish":
            return 4
        return 8

    def _score_news(self, candidate: Mapping[str, Any]) -> int:
        """Return a neutral placeholder news score for now."""

        sentiment = str(candidate.get("news_sentiment") or "neutral").strip().lower()
        if sentiment == "positive":
            return 9
        if sentiment == "negative":
            return 4
        return 7

    def _calculate_total_score(
        self,
        technical_score: int,
        momentum_score: int,
        volume_score: int,
        market_score: int,
        news_score: int,
    ) -> int:
        """Calculate a normalized 0-100 score from the category scores."""

        technical_contribution = (technical_score / self.CATEGORY_MAXIMUMS["technical"]) * 100.0 * self.rules["technical_weight"]
        momentum_contribution = (momentum_score / self.CATEGORY_MAXIMUMS["momentum"]) * 100.0 * self.rules["momentum_weight"]
        volume_contribution = (volume_score / self.CATEGORY_MAXIMUMS["volume"]) * 100.0 * self.rules["volume_weight"]
        market_contribution = (market_score / self.CATEGORY_MAXIMUMS["market"]) * 100.0 * self.rules["market_weight"]
        news_contribution = (news_score / self.CATEGORY_MAXIMUMS["news"]) * 100.0 * self.rules["news_weight"]

        return int(round(technical_contribution + momentum_contribution + volume_contribution + market_contribution + news_contribution))

    def _recommendation(self, total_score: int) -> str:
        """Translate total score into a simple recommendation."""

        if total_score >= self._thresholds("buy_threshold"):
            return "BUY"
        if total_score >= self._thresholds("watch_threshold"):
            return "WATCH"
        return "AVOID"

    def _calculate_confidence(
        self,
        candidate: Mapping[str, Any],
        total_score: int,
        technical_score: int,
        momentum_score: int,
        volume_score: int,
        market_score: int,
        news_score: int,
    ) -> float:
        """Estimate score confidence based on the amount of supporting data."""

        available_inputs = [
            self._has_value(candidate.get("price")),
            self._has_value(candidate.get("ema20")),
            self._has_value(candidate.get("ema50")),
            self._has_value(candidate.get("rsi")),
            self._has_value(candidate.get("macd")),
            self._has_value(candidate.get("momentum")),
            self._has_value(candidate.get("relative_volume")),
            self._has_value(candidate.get("market_regime")),
            self._has_value(candidate.get("news_sentiment")),
        ]
        completeness = sum(available_inputs) / len(available_inputs) if available_inputs else 0.0
        if completeness <= 0.2:
            return 20.0

        signal_strength = min(50.0, max(0.0, total_score / 2.0))
        confidence = (completeness * 50.0) + signal_strength
        return round(self._clamp(confidence, 0.0, 100.0), 2)

    def _build_reasons(
        self,
        candidate: Mapping[str, Any],
        technical_score: int,
        momentum_score: int,
        volume_score: int,
        market_score: int,
        news_score: int,
    ) -> list[str]:
        """Create human-readable reasons for the final score."""

        reasons: list[str] = []
        signal_fields = ("price", "ema20", "ema50", "rsi", "macd", "momentum", "relative_volume", "market_regime", "news_sentiment")
        if not any(self._has_value(candidate.get(field)) for field in signal_fields):
            return ["Insufficient data"]

        price = self._coerce_float(candidate.get("price"))
        ema20 = self._coerce_float(candidate.get("ema20"))
        ema50 = self._coerce_float(candidate.get("ema50"))
        momentum = self._coerce_float(candidate.get("momentum"))
        relative_volume = self._coerce_float(candidate.get("relative_volume"))
        macd = self._coerce_float(candidate.get("macd"))

        if price is not None and ema20 is not None and price > ema20:
            reasons.append("Above EMA20")
        elif price is not None and ema20 is not None and price < ema20:
            reasons.append("Price below EMA20")

        if ema20 is not None and ema50 is not None and ema20 > ema50:
            reasons.append("EMA20 above EMA50")

        if macd is not None and macd > 0:
            reasons.append("MACD bullish")

        if momentum is not None and momentum >= self._thresholds("momentum_strong"):
            reasons.append("Strong momentum")
        elif momentum is not None and momentum >= self._thresholds("momentum_watch"):
            reasons.append("Moderate momentum")

        if relative_volume is not None and relative_volume >= self._thresholds("relative_volume_buy"):
            reasons.append("High Relative Volume")
        elif relative_volume is not None and relative_volume >= self._thresholds("relative_volume_watch"):
            reasons.append("Average Relative Volume")
        elif relative_volume is not None:
            reasons.append("Low Relative Volume")

        if not reasons:
            reasons.append("Insufficient data")
        return reasons

    def _build_result(
        self,
        symbol: str,
        total_score: int,
        recommendation: str,
        confidence: float,
        technical_score: int,
        momentum_score: int,
        volume_score: int,
        market_score: int,
        news_score: int,
        reasons: list[str],
    ) -> ScoreResult:
        """Create a ScoreResult from calculated components."""

        return ScoreResult(
            symbol=symbol,
            total_score=total_score,
            recommendation=recommendation,
            confidence=confidence,
            technical_score=technical_score,
            momentum_score=momentum_score,
            volume_score=volume_score,
            market_score=market_score,
            news_score=news_score,
            reasons=reasons,
        )

    def _coerce_float(self, value: Any) -> Optional[float]:
        """Safely convert a value to a float when possible."""

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _has_value(self, value: Any) -> bool:
        """Check whether a value provides a usable signal."""

        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        return True

    def _thresholds(self, key: str) -> float:
        """Return a named scoring threshold."""

        return self.DEFAULT_THRESHOLDS[key]

    def _clamp(self, value: float, lower: float, upper: float) -> int:
        """Clamp a numeric value to the requested bounds."""

        return int(round(max(lower, min(upper, value))))
