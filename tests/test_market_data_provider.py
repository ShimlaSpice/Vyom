"""Unit tests for the market data provider."""

from __future__ import annotations

import unittest
from unittest.mock import patch

import pandas as pd

from app.market.market_data_provider import MarketDataProvider


class MarketDataProviderTests(unittest.TestCase):
    """Validate provider behavior for caching and error handling."""

    def test_fetch_ohlcv_returns_dataframes_and_uses_cache(self) -> None:
        """The provider should return DataFrames and reuse cached results."""

        provider = MarketDataProvider(symbols=["RELIANCE"], cache_ttl_seconds=60)
        sample_frame = pd.DataFrame(
            {
                "Open": [100.0],
                "High": [101.0],
                "Low": [99.0],
                "Close": [100.5],
                "Volume": [1_000_000],
            },
            index=pd.to_datetime(["2024-01-02"]),
        )

        with patch("app.market.market_data_provider.yf.download", return_value=sample_frame) as mocked_download:
            first_result = provider.fetch_ohlcv(["RELIANCE"], period="1mo", interval="1d")
            second_result = provider.fetch_ohlcv(["RELIANCE"], period="1mo", interval="1d")

        self.assertIn("RELIANCE", first_result)
        self.assertTrue(isinstance(first_result["RELIANCE"], pd.DataFrame))
        self.assertEqual(mocked_download.call_count, 1)
        self.assertTrue(second_result["RELIANCE"].equals(sample_frame))

    def test_fetch_ohlcv_returns_empty_frame_when_download_fails(self) -> None:
        """Network failures should yield an empty DataFrame rather than crash."""

        provider = MarketDataProvider(symbols=["RELIANCE"], max_retries=1, timeout=1)

        with patch("app.market.market_data_provider.yf.download", side_effect=TimeoutError("boom")):
            result = provider.fetch_ohlcv(["RELIANCE"], period="1mo", interval="1d")

        self.assertIn("RELIANCE", result)
        self.assertTrue(result["RELIANCE"].empty)

    def test_fetch_ohlcv_async_returns_background_result(self) -> None:
        """The async wrapper should return a completed future with DataFrame data."""

        provider = MarketDataProvider(symbols=["RELIANCE"], cache_ttl_seconds=60)
        sample_frame = pd.DataFrame(
            {
                "Open": [100.0],
                "High": [101.0],
                "Low": [99.0],
                "Close": [100.5],
                "Volume": [1_000_000],
            },
            index=pd.to_datetime(["2024-01-02"]),
        )

        with patch("app.market.market_data_provider.yf.download", return_value=sample_frame):
            future = provider.fetch_ohlcv_async(["RELIANCE"], period="1mo", interval="1d")
            result = future.result(timeout=2)

        self.assertIn("RELIANCE", result)
        self.assertTrue(isinstance(result["RELIANCE"], pd.DataFrame))

    def test_fetch_ohlcv_accepts_single_symbol_string(self) -> None:
        """Passing a single symbol string should be treated as one requested symbol."""

        provider = MarketDataProvider(symbols=["RELIANCE"], cache_ttl_seconds=60)
        sample_frame = pd.DataFrame(
            {
                "Open": [100.0],
                "High": [101.0],
                "Low": [99.0],
                "Close": [100.5],
                "Volume": [1_000_000],
            },
            index=pd.to_datetime(["2024-01-02"]),
        )

        with patch("app.market.market_data_provider.yf.download", return_value=sample_frame):
            result = provider.fetch_ohlcv("RELIANCE", period="1mo", interval="1d")

        self.assertIn("RELIANCE", result)
        self.assertTrue(isinstance(result["RELIANCE"], pd.DataFrame))


if __name__ == "__main__":
    unittest.main()
