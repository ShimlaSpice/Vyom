"""Asynchronous-friendly market data provider built on yfinance.

The provider is intentionally isolated from the scanner and UI so live market
requests can be introduced without changing existing workflows.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Iterable
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class MarketDataProvider:
    """Fetch OHLCV market data for configured symbols.

    This implementation uses yfinance for data retrieval, supports retries and
    timeouts, caches responses for a configurable interval, and is safe to use
    from threads by guarding cache access.
    """

    def __init__(
        self,
        symbols: Iterable[str] | None = None,
        cache_ttl_seconds: int = 60,
        timeout: int = 10,
        max_retries: int = 3,
        retry_delay_seconds: float = 1.0,
        logger_instance: logging.Logger | None = None,
    ) -> None:
        """Create a market data provider.

        Args:
            symbols: Optional default symbols to use for requests.
            cache_ttl_seconds: How long cached responses remain valid.
            timeout: Request timeout in seconds for each yfinance attempt.
            max_retries: Number of times to retry after transient failures.
            retry_delay_seconds: Delay between retries.
            logger_instance: Optional logger override.
        """

        self.symbols = [symbol.strip().upper() for symbol in (symbols or []) if str(symbol).strip()]
        self.cache_ttl_seconds = max(1, cache_ttl_seconds)
        self.timeout = max(1, timeout)
        self.max_retries = max(1, max_retries)
        self.retry_delay_seconds = max(0.0, retry_delay_seconds)
        self.logger = logger_instance or logger
        self._cache: dict[str, tuple[datetime, pd.DataFrame]] = {}
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="vyom-market")

    def fetch_ohlcv(
        self,
        symbols: Iterable[str] | None = None,
        *,
        period: str = "1mo",
        interval: str = "1d",
        auto_adjust: bool = True,
        prepost: bool = False,
        repair: bool = True,
    ) -> dict[str, pd.DataFrame]:
        """Retrieve OHLCV data for the provided symbols.

        Args:
            symbols: Optional override symbols to fetch. When omitted, the
                configured defaults are used.
            period: Yahoo Finance period string.
            interval: Yahoo Finance interval string.
            auto_adjust: Whether to auto-adjust historical prices.
            prepost: Whether to include pre/post market hours.
            repair: Whether to repair malformed data.

        Returns:
            A mapping from symbol to a DataFrame containing OHLCV data.
        """

        requested_symbols = self._normalize_symbols(symbols)
        if not requested_symbols:
            self.logger.warning("No symbols supplied for market data fetch")
            return {}

        results: dict[str, pd.DataFrame] = {}
        with self._lock:
            for symbol in requested_symbols:
                cached_entry = self._cache.get(symbol)
                if cached_entry and self._is_cache_fresh(cached_entry[0]):
                    self.logger.debug("Returning cached OHLCV data for %s", symbol)
                    results[symbol] = cached_entry[1].copy()
                    continue

                self.logger.info("Fetching OHLCV data for %s", symbol)
                results[symbol] = self._download_with_retries(
                    symbol,
                    period=period,
                    interval=interval,
                    auto_adjust=auto_adjust,
                    prepost=prepost,
                    repair=repair,
                )
                self._cache[symbol] = (datetime.now(timezone.utc), results[symbol])

        return results

    def fetch_ohlcv_async(
        self,
        symbols: Iterable[str] | None = None,
        *,
        period: str = "1mo",
        interval: str = "1d",
        auto_adjust: bool = True,
        prepost: bool = False,
        repair: bool = True,
    ) -> Future[dict[str, pd.DataFrame]]:
        """Fetch OHLCV data in a background thread without blocking callers."""

        return self._executor.submit(
            self.fetch_ohlcv,
            symbols,
            period=period,
            interval=interval,
            auto_adjust=auto_adjust,
            prepost=prepost,
            repair=repair,
        )

    def clear_cache(self) -> None:
        """Clear all cached market data."""

        with self._lock:
            self._cache.clear()

    def _download_with_retries(
        self,
        symbol: str,
        *,
        period: str,
        interval: str,
        auto_adjust: bool,
        prepost: bool,
        repair: bool,
    ) -> pd.DataFrame:
        """Download OHLCV data with retry and timeout handling."""

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                frame = yf.download(
                    tickers=symbol,
                    period=period,
                    interval=interval,
                    auto_adjust=auto_adjust,
                    prepost=prepost,
                    repair=repair,
                    timeout=self.timeout,
                    progress=False,
                )
                if isinstance(frame, pd.DataFrame) and not frame.empty:
                    return self._normalize_frame(frame)

                self.logger.warning("No data returned for %s on attempt %d", symbol, attempt)
                return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
            except (TimeoutError, ConnectionError, OSError, ValueError) as exc:
                last_error = exc
                self.logger.warning("Download failed for %s on attempt %d: %s", symbol, attempt, exc)
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay_seconds)
        if last_error:
            self.logger.exception("Failed to download OHLCV data for %s after %d attempts", symbol, self.max_retries)
        return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])

    def _normalize_symbols(self, symbols: Iterable[str] | None) -> list[str]:
        """Normalize and deduplicate symbols."""

        if symbols is None:
            values = self.symbols
        elif isinstance(symbols, str):
            values = [symbols]
        else:
            values = list(symbols)

        normalized_values = [str(value).strip().upper() for value in values]
        return list(dict.fromkeys([value for value in normalized_values if value]))

    def _is_cache_fresh(self, cached_at: datetime) -> bool:
        """Check whether the cached entry is still within the TTL window."""

        return datetime.now(timezone.utc) - cached_at < timedelta(seconds=self.cache_ttl_seconds)

    def _normalize_frame(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Normalize a downloaded frame to a consistent OHLCV shape."""

        normalized = frame.copy()
        if isinstance(normalized.columns, pd.MultiIndex):
            normalized.columns = normalized.columns.get_level_values(0)
        if normalized.empty:
            return normalized

        if "Open" in normalized.columns and "High" in normalized.columns and "Low" in normalized.columns and "Close" in normalized.columns and "Volume" in normalized.columns:
            return normalized[["Open", "High", "Low", "Close", "Volume"]]

        if "Adj Close" in normalized.columns:
            normalized = normalized.rename(columns={"Adj Close": "Close"})
        return normalized[[col for col in ["Open", "High", "Low", "Close", "Volume"] if col in normalized.columns]]
