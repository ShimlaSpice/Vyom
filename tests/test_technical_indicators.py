"""Tests for the technical indicator engine."""

from __future__ import annotations

import pandas as pd
import unittest

from app.scanner.technical_indicators import IndicatorResult, TechnicalIndicatorEngine


class TechnicalIndicatorEngineTests(unittest.TestCase):
    """Verify technical indicator calculations and edge-case handling."""

    def setUp(self) -> None:
        self.engine = TechnicalIndicatorEngine()
        self.frame = pd.DataFrame(
            {
                "Open": [100.0, 102.0, 101.0, 103.0, 105.0, 107.0],
                "High": [103.0, 104.0, 105.0, 107.0, 108.0, 110.0],
                "Low": [98.0, 100.0, 99.0, 101.0, 103.0, 105.0],
                "Close": [101.0, 103.0, 102.0, 104.0, 106.0, 109.0],
                "Volume": [1_000_000, 1_100_000, 1_200_000, 1_300_000, 1_400_000, 1_500_000],
            },
            index=pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05", "2024-01-06"]),
        )

    def test_normal_data_calculates_expected_indicators(self) -> None:
        """A normal OHLCV dataset should populate every indicator."""

        result = self.engine.calculate(self.frame)

        self.assertIsInstance(result, IndicatorResult)
        self.assertTrue(result.valid)
        self.assertIsNotNone(result.ema20)
        self.assertIsNotNone(result.ema50)
        self.assertIsNotNone(result.sma20)
        self.assertIsNotNone(result.sma50)
        self.assertIsNotNone(result.rsi14)
        self.assertIsNotNone(result.macd)
        self.assertIsNotNone(result.macd_signal)
        self.assertIsNotNone(result.macd_histogram)
        self.assertIsNotNone(result.atr14)
        self.assertIsNotNone(result.bollinger_upper)
        self.assertIsNotNone(result.bollinger_middle)
        self.assertIsNotNone(result.bollinger_lower)
        self.assertIsNotNone(result.relative_volume)
        self.assertIsNotNone(result.average_volume)

    def test_empty_dataframe_returns_invalid_result(self) -> None:
        """Empty data should not crash and should return an invalid result."""

        result = self.engine.calculate(pd.DataFrame())

        self.assertFalse(result.valid)
        self.assertEqual(result.missing_columns, ["dataframe"])

    def test_missing_columns_returns_invalid_result(self) -> None:
        """Missing OHLCV columns should be gracefully handled."""

        frame = pd.DataFrame({"Open": [1.0], "High": [2.0], "Low": [0.5]})
        result = self.engine.calculate(frame)

        self.assertFalse(result.valid)

    def test_short_dataset_still_returns_safe_values(self) -> None:
        """Short datasets should not raise and should return something meaningful."""

        short_frame = self.frame.head(2)
        result = self.engine.calculate(short_frame)

        self.assertTrue(result.valid)
        self.assertIsNotNone(result.close)

    def test_indicator_result_to_mapping_contains_expected_keys(self) -> None:
        """IndicatorResult should be consumable by the scoring engine."""

        result = self.engine.calculate(self.frame)
        mapping = result.to_mapping()

        self.assertIn("price", mapping)
        self.assertIn("rsi", mapping)
        self.assertIn("macd", mapping)
        self.assertIn("relative_volume", mapping)


if __name__ == "__main__":
    unittest.main()
