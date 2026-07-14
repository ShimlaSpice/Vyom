"""Decision engine for converting scoring output into trade recommendations.

The module is intentionally backend-only and does not calculate indicators or
scores on its own. Instead, it consumes a structured :class:`ScoreResult` and
translates it into a final trade recommendation with explanations and risk
metadata.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.scanner.scoring import ScoreResult

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class TradeRecommendation:
    """Structured recommendation emitted by the decision engine."""

    symbol: str
    action: str
    trade_quality: str
    confidence: float
    risk_level: str
    entry_price: Optional[float]
    stop_loss: Optional[float]
    target_price: Optional[float]
    risk_reward_ratio: Optional[float]
    positive_signals: list[str] = field(default_factory=list)
    negative_signals: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    summary: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class DecisionEngine:
    """Translate score results into a final, explainable trade recommendation."""

    def __init__(self, logger_instance: Optional[logging.Logger] = None) -> None:
        """Create a decision engine with optional dependency injection for logging."""

        self.logger = logger_instance or logger

    def make_recommendation(self, score_result: ScoreResult) -> TradeRecommendation:
        """Create a trade recommendation from an existing score result."""

        if not isinstance(score_result, ScoreResult):
            raise TypeError("score_result must be a ScoreResult instance")

        action, trade_quality, risk_level = self._derive_action(score_result)
        positive_signals, negative_signals, warnings = self._build_signals(score_result, action, risk_level)
        entry_price, stop_loss, target_price, risk_reward_ratio = self._build_price_targets(action,  score_result,)
        summary = self._build_summary(score_result, action, trade_quality)

        self.logger.debug(
            "Decision engine produced %s for %s with quality %s",
            action,
            score_result.symbol,
            trade_quality,
        )

        return TradeRecommendation(
            symbol=score_result.symbol,
            action=action,
            trade_quality=trade_quality,
            confidence=round(score_result.confidence, 2),
            risk_level=risk_level,
            entry_price=entry_price,
            stop_loss=stop_loss,
            target_price=target_price,
            risk_reward_ratio=risk_reward_ratio,
            positive_signals=positive_signals,
            negative_signals=negative_signals,
            warnings=warnings,
            summary=summary,
        )

    def _derive_action(self, score_result: ScoreResult) -> tuple[str, str, str]:
        """Determine the trading action using decision matrix logic."""

        trend_ok = score_result.technical_score >= 20
        momentum_ok = score_result.momentum_score >= 8
        volume_ok = score_result.volume_score >= 8
        market_ok = score_result.market_score >= 6

        confidence = score_result.confidence

        risk = self._assess_risk(
        confidence,
        score_result.market_score,
        score_result.volume_score,
        score_result.momentum_score,
        score_result.technical_score,
    )

        # High conviction BUY
        if trend_ok and momentum_ok and volume_ok and market_ok and confidence >= 75:
            return "BUY", "A+", risk

        # Good BUY
        if trend_ok and momentum_ok and market_ok and confidence >= 60:
            return "BUY", "A", risk

        # Watchlist candidate
        if trend_ok and confidence >= 45:
            return "WATCH", "B", risk

        # Weak watch
        if confidence >= 35:
            return "WATCH", "C", risk

        return "NO_TRADE", "REJECT", risk

    def _assess_risk(
        self,
        confidence: float,
        market_score: int,
        volume_score: int,
        momentum_score: int,
        technical_score: int,
    ) -> str:
        """Assess risk based on confidence and supporting market conditions."""

        if confidence < 45.0 or market_score <= 4 or volume_score <= 3 or momentum_score <= 3 or technical_score <= 6:
            return "HIGH"
        if confidence < 70.0 or market_score <= 8 or volume_score <= 6 or momentum_score <= 6 or technical_score <= 15:
            return "MEDIUM"
        return "LOW"

    def _build_signals(
        self,
        score_result: ScoreResult,
        action: str,
        risk_level: str,
    ) -> tuple[list[str], list[str], list[str]]:
        """Build positive, negative, and warning signals from the score result."""

        positive_signals: list[str] = []
        negative_signals: list[str] = []
        warnings: list[str] = []

        if score_result.technical_score >= 20:
            positive_signals.append("Strong technical structure")
        else:
            negative_signals.append("Weak technical structure")

        if score_result.momentum_score >= 10:
            positive_signals.append("Bullish momentum")
        else:
            negative_signals.append("Momentum is not compelling")

        if score_result.volume_score >= 10:
            positive_signals.append("Above-average volume")
        elif score_result.volume_score >= 6:
            positive_signals.append("Healthy participation")
        else:
            negative_signals.append("Volume participation is weak")

        if score_result.market_score >= 8:
            positive_signals.append("Supportive market context")
        else:
            negative_signals.append("Market context is mixed")

        if score_result.confidence < 45.0:
            warnings.append("Low confidence in the setup")
        if risk_level == "HIGH":
            warnings.append("High risk profile")
        if action == "WATCH":
            warnings.append("Waiting for confirmation before entry")
        elif action == "NO_TRADE":
            warnings.append("No trade recommended at this time")
        elif action == "SELL":
            warnings.append("Consider reducing exposure")

        return positive_signals, negative_signals, warnings

    def _build_price_targets(
        self,
        action: str,
        score_result: ScoreResult,
    ) -> tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
        """Generate entry, stop-loss and target using live price and ATR."""

        if score_result.current_price is None:
            return None, None, None, None
        
        if action == "NO_TRADE":
            return None, None, None, None
        
        entry_price = round(score_result.current_price, 2)
        atr = score_result.atr or (entry_price * 0.02)

        if action == "BUY":
            stop_loss = round(entry_price - (1.5 * atr), 2)
            target_price = round(entry_price + (3.0 * atr), 2)

        elif action == "WATCH":
            stop_loss = round(entry_price - (2.0 * atr), 2)
            target_price = round(entry_price + (2.0 * atr), 2)

        else:
            stop_loss = round(entry_price - (2.5 * atr), 2)
            target_price = round(entry_price + (1.0 * atr), 2)

        risk = max(entry_price - stop_loss, 0.01)
        reward = target_price - entry_price

        risk_reward_ratio = round(reward / risk, 2)

        return entry_price, stop_loss, target_price, risk_reward_ratio

    def _build_summary(
        self,
        score_result: ScoreResult,
        action: str,
        trade_quality: str
    ) -> str:
        """Create a human-readable summary from the score result."""

        symbol = score_result.symbol or "UNKNOWN"
        
        if action == "BUY":
            return (
                f"{symbol} shows strong trend continuation with above-average volume and bullish momentum. "
                f"Overall trade quality is {trade_quality}."
            )
        if action == "WATCH":
            return (
                f"{symbol} is a watch setup with mixed confirmation and moderate conviction. "
                f"Overall trade quality is {trade_quality}."
            )
        if action == "SELL":
            return (
                f"{symbol} is showing weak trend characteristics and should sell or be avoided. "
                f"Overall trade quality is {trade_quality}."
            )
        return (
            f"{symbol} has insufficient quality for a trade right now; no trade is recommended. "
            f"Overall trade quality is {trade_quality}."
        )
