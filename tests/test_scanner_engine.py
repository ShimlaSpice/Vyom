"""Tests for the modular scanner architecture."""

from __future__ import annotations

import unittest
from concurrent.futures import Future

import pandas as pd

from app.scanner.scanner import ScannerEngine, StockData


class StubMarketDataProvider:
    """Provide deterministic market frames for scanner tests."""

    def __init__(self, frame: pd.DataFrame) -> None:
        self.frame = frame
        self.timeout = 5

    def fetch_ohlcv_async(self, symbols=None, **_: object) -> Future[dict[str, pd.DataFrame]]:
        """Return a completed future with a single-symbol market frame."""

        future: Future[dict[str, pd.DataFrame]] = Future()
        future.set_result({"RELIANCE": self.frame})
        return future


class ScannerEngineTests(unittest.TestCase):
    """Validate the scanner workflow with mock data."""

    def test_scan_returns_ranked_candidates(self) -> None:
        """The scanner should score and rank mock stock candidates."""

        engine = ScannerEngine()
        results = engine.scan(limit=3)

        self.assertLessEqual(len(results), 3)
        self.assertTrue(results)
        self.assertEqual(results[0]["symbol"], "RELIANCE")
        self.assertGreaterEqual(results[0]["score"], 0)
        self.assertLessEqual(results[0]["score"], 100)

    def test_build_candidates_uses_injected_market_provider(self) -> None:
        """ScannerEngine should build StockData objects from an injected provider."""

        sample_frame = pd.DataFrame(
            {
                "Open": [100.0, 102.0],
                "High": [103.0, 105.0],
                "Low": [99.0, 101.0],
                "Close": [101.0, 104.0],
                "Volume": [1_000_000, 1_200_000],
            },
            index=pd.to_datetime(["2024-01-02", "2024-01-03"]),
        )
        engine = ScannerEngine(market_data_provider=StubMarketDataProvider(sample_frame))

        candidates = engine.build_candidates()

        self.assertEqual(len(candidates), 1)
        self.assertIsInstance(candidates[0], StockData)
        self.assertEqual(candidates[0].symbol, "RELIANCE")
        self.assertGreaterEqual(candidates[0].momentum, 0.0)


if __name__ == "__main__":
    unittest.main()
