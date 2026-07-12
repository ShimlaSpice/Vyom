"""Tests for the V0.5 stock scoring engine."""

from __future__ import annotations

import unittest

from app.scanner.scoring import ScoreResult, ScoringEngine


class ScoringEngineTests(unittest.TestCase):
    """Validate detailed stock scoring and recommendation logic."""

    def test_buy_case_returns_high_score(self) -> None:
        """A bullish setup should be recommended for buying."""

        engine = ScoringEngine()
        candidate = {
            "symbol": "BEL",
            "price": 250.0,
            "ema20": 240.0,
            "ema50": 220.0,
            "rsi": 65.0,
            "macd": 1.4,
            "momentum": 8.0,
            "trend_continuation": True,
            "relative_volume": 2.5,
            "volume_spike": True,
            "market_regime": "bullish",
            "news_sentiment": "positive",
        }

        result = engine.score_stock(candidate)

        self.assertIsInstance(result, ScoreResult)
        self.assertGreaterEqual(result.total_score, 80)
        self.assertEqual(result.recommendation, "BUY")
        self.assertGreaterEqual(result.technical_score, 30)
        self.assertGreaterEqual(result.volume_score, 10)
        self.assertIn("Above EMA20", result.reasons)
        self.assertIn("MACD bullish", result.reasons)

    def test_watch_case_returns_mixed_signal(self) -> None:
        """A mixed setup should be watched rather than bought."""

        engine = ScoringEngine()
        candidate = {
            "symbol": "TCS",
            "price": 3500.0,
            "ema20": 3480.0,
            "ema50": 3490.0,
            "rsi": 58.0,
            "macd": 0.1,
            "momentum": 3.0,
            "trend_continuation": True,
            "relative_volume": 1.0,
            "volume_spike": False,
            "market_regime": "neutral",
            "news_sentiment": "neutral",
        }

        result = engine.score_stock(candidate)

        self.assertEqual(result.recommendation, "WATCH")
        self.assertGreaterEqual(result.total_score, 50)
        self.assertLess(result.total_score, 80)

    def test_avoid_case_returns_low_score(self) -> None:
        """A weak setup should be avoided."""

        engine = ScoringEngine()
        candidate = {
            "symbol": "XYZ",
            "price": 100.0,
            "ema20": 110.0,
            "ema50": 105.0,
            "rsi": 40.0,
            "macd": -0.8,
            "momentum": -4.0,
            "trend_continuation": False,
            "relative_volume": 0.4,
            "volume_spike": False,
            "market_regime": "bearish",
            "news_sentiment": "negative",
        }

        result = engine.score_stock(candidate)

        self.assertEqual(result.recommendation, "AVOID")
        self.assertLess(result.total_score, 50)
        self.assertIn("Price below EMA20", result.reasons)

    def test_low_volume_case_reduces_score(self) -> None:
        """Low relative volume should lower the volume component and overall score."""

        engine = ScoringEngine()
        candidate = {
            "symbol": "INFY",
            "price": 1500.0,
            "ema20": 1480.0,
            "ema50": 1450.0,
            "rsi": 62.0,
            "macd": 0.9,
            "momentum": 5.0,
            "trend_continuation": True,
            "relative_volume": 0.5,
            "volume_spike": False,
            "market_regime": "bullish",
            "news_sentiment": "positive",
        }

        result = engine.score_stock(candidate)

        self.assertLess(result.volume_score, 8)
        self.assertNotEqual(result.recommendation, "BUY")

    def test_missing_data_returns_low_confidence(self) -> None:
        """Missing inputs should not crash and should signal low confidence."""

        engine = ScoringEngine()
        result = engine.score_stock({"symbol": "NO DATA"})

        self.assertEqual(result.recommendation, "AVOID")
        self.assertLessEqual(result.confidence, 30.0)
        self.assertIn("Insufficient data", result.reasons)


if __name__ == "__main__":
    unittest.main()
