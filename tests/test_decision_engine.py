"""Tests for the V0.7 decision engine."""

from __future__ import annotations

import unittest

from app.scanner.decision_engine import TradeRecommendation, DecisionEngine
from app.scanner.scoring import ScoreResult


class DecisionEngineTests(unittest.TestCase):
    """Validate trade recommendation translation from score results."""

    def _score_result(self, *, total_score: int, confidence: float, technical: int = 20, momentum: int = 10, volume: int = 8, market: int = 8, recommendation: str = "BUY") -> ScoreResult:
        return ScoreResult(
            symbol="BEL",
            total_score=total_score,
            recommendation=recommendation,
            confidence=confidence,
            technical_score=technical,
            momentum_score=momentum,
            volume_score=volume,
            market_score=market,
            news_score=7,
            reasons=["signal"],
        )

    def test_buy_recommendation_uses_high_conviction_logic(self) -> None:
        engine = DecisionEngine()
        result = engine.make_recommendation(self._score_result(total_score=92, confidence=89.0, technical=35, momentum=18, volume=15, market=12, recommendation="BUY"))

        self.assertIsInstance(result, TradeRecommendation)
        self.assertEqual(result.action, "BUY")
        self.assertEqual(result.trade_quality, "A+")
        self.assertEqual(result.risk_level, "LOW")
        self.assertIn("strong trend", result.summary.lower())
        self.assertGreaterEqual(len(result.positive_signals), 1)

    def test_sell_recommendation_is_generated_for_bearish_score(self) -> None:
        engine = DecisionEngine()
        result = engine.make_recommendation(self._score_result(total_score=18, confidence=80.0, technical=3, momentum=2, volume=2, market=2, recommendation="AVOID"))

        self.assertEqual(result.action, "SELL")
        self.assertEqual(result.trade_quality, "REJECT")
        self.assertEqual(result.risk_level, "HIGH")
        self.assertIn("sell", result.summary.lower())
        self.assertGreaterEqual(len(result.negative_signals), 1)

    def test_watch_recommendation_is_used_for_moderate_confidence(self) -> None:
        engine = DecisionEngine()
        result = engine.make_recommendation(self._score_result(total_score=68, confidence=62.0, technical=22, momentum=12, volume=8, market=8, recommendation="WATCH"))

        self.assertEqual(result.action, "WATCH")
        self.assertEqual(result.trade_quality, "B")
        self.assertEqual(result.risk_level, "MEDIUM")
        self.assertIn("watch", result.summary.lower())

    def test_no_trade_recommendation_is_used_for_low_score_or_low_confidence(self) -> None:
        engine = DecisionEngine()
        result = engine.make_recommendation(self._score_result(total_score=40, confidence=25.0, technical=6, momentum=4, volume=3, market=4, recommendation="AVOID"))

        self.assertEqual(result.action, "NO_TRADE")
        self.assertEqual(result.trade_quality, "REJECT")
        self.assertEqual(result.risk_level, "HIGH")
        self.assertIn("no trade", result.summary.lower())

    def test_high_risk_and_low_confidence_lead_to_warnings(self) -> None:
        engine = DecisionEngine()
        result = engine.make_recommendation(self._score_result(total_score=82, confidence=35.0, technical=28, momentum=15, volume=12, market=9, recommendation="BUY"))

        self.assertEqual(result.action, "WATCH")
        self.assertIn("low confidence", result.warnings[0].lower())
        self.assertIn("high risk", result.warnings[1].lower())


if __name__ == "__main__":
    unittest.main()
