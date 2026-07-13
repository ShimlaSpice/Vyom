"""Reusable technical indicator calculations for Vyom scanner workflows.

The engine is intentionally backend-only and exposes a clean result object that
can be consumed by the scoring layer without coupling it to raw DataFrame
manipulation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import pandas as pd

try:  # pragma: no cover - optional dependency
    import pandas_ta as pta
except ImportError:  # pragma: no cover - fallback path
    pta = None

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class IndicatorResult:
    """Container for the latest technical indicator values for a symbol."""

    close: Optional[float] = None
    volume: Optional[float] = None
    momentum: Optional[float] = None
    ema20: Optional[float] = None
    ema50: Optional[float] = None
    sma20: Optional[float] = None
    sma50: Optional[float] = None
    vwap: Optional[float] = None
    rsi14: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    atr14: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_middle: Optional[float] = None
    bollinger_lower: Optional[float] = None
    relative_volume: Optional[float] = None
    average_volume: Optional[float] = None
    valid: bool = False
    missing_columns: list[str] = field(default_factory=list)

    def to_mapping(self) -> dict[str, Any]:
        """Expose indicator values in a dictionary suitable for scoring."""

        return {
            "price": self.close,
            "volume": self.volume,
            "momentum": self.momentum,
            "ema20": self.ema20,
            "ema50": self.ema50,
            "sma20": self.sma20,
            "sma50": self.sma50,
            "vwap": self.vwap,
            "rsi": self.rsi14,
            "macd": self.macd,
            "macd_signal": self.macd_signal,
            "macd_histogram": self.macd_histogram,
            "atr14": self.atr14,
            "bollinger_upper": self.bollinger_upper,
            "bollinger_middle": self.bollinger_middle,
            "bollinger_lower": self.bollinger_lower,
            "relative_volume": self.relative_volume,
            "average_volume": self.average_volume,
            "valid": self.valid,
        }


class TechnicalIndicatorEngine:
    """Calculate a standard set of technical indicators for OHLCV data."""

    def __init__(self, logger_instance: Optional[logging.Logger] = None) -> None:
        self.logger = logger_instance or logger
        self._cache: dict[int, IndicatorResult] = {}

    def calculate(self, dataframe: pd.DataFrame) -> IndicatorResult:
        """Calculate the full indicator set for a DataFrame.

        The engine accepts an OHLCV-style DataFrame and returns an IndicatorResult
        object without raising for empty or malformed data.
        """

        if dataframe is None:
            return IndicatorResult(valid=False, missing_columns=["dataframe"])

        frame = self._coerce_frame(dataframe)
        cache_key = id(frame)
        if cache_key in self._cache:
            return self._cache[cache_key]

        prepared = self._prepare_frame(frame)
        if prepared.empty:
            result = IndicatorResult(valid=False, missing_columns=["dataframe"])
            self._cache[cache_key] = result
            return result

        result = IndicatorResult(
            close=self._last_value(prepared["Close"]),
            volume=self._last_value(prepared["Volume"]),
            momentum=self._calculate_momentum(prepared),
            ema20=self._calculate_ema(prepared["Close"], 20),
            ema50=self._calculate_ema(prepared["Close"], 50),
            sma20=self._calculate_sma(prepared["Close"], 20),
            sma50=self._calculate_sma(prepared["Close"], 50),
            vwap=self._calculate_vwap(prepared),
            rsi14=self._calculate_rsi(prepared["Close"]),
            macd=self._calculate_macd(prepared["Close"])[0],
            macd_signal=self._calculate_macd(prepared["Close"])[1],
            macd_histogram=self._calculate_macd(prepared["Close"])[2],
            atr14=self._calculate_atr(prepared),
            bollinger_upper=self._calculate_bollinger(prepared)[0],
            bollinger_middle=self._calculate_bollinger(prepared)[1],
            bollinger_lower=self._calculate_bollinger(prepared)[2],
            relative_volume=self._calculate_relative_volume(prepared),
            average_volume=self._calculate_average_volume(prepared),
            valid=True,
            missing_columns=[],
        )
        self._cache[cache_key] = result
        return result

    def clear_cache(self) -> None:
        """Clear cached indicator results."""

        self._cache.clear()

    def _coerce_frame(self, dataframe: Any) -> pd.DataFrame:
        """Ensure the input is a pandas DataFrame."""

        if isinstance(dataframe, pd.DataFrame):
            return dataframe.copy()
        if hasattr(dataframe, "to_frame"):
            try:
                return pd.DataFrame(dataframe)
            except Exception:
                return pd.DataFrame()
        return pd.DataFrame()

    def _prepare_frame(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Normalize OHLCV columns and coerce values to numeric types."""

        if dataframe.empty:
            return dataframe

        normalized = dataframe.copy()
        column_map = {col.lower(): col for col in normalized.columns}
        for lower_name, canonical_name in {
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }.items():
            if lower_name in column_map and canonical_name not in normalized.columns:
                normalized[canonical_name] = normalized[column_map[lower_name]]

        required_columns = ["Open", "High", "Low", "Close", "Volume"]
        missing_columns = [column for column in required_columns if column not in normalized.columns]
        if missing_columns:
            self.logger.warning("Missing OHLCV columns for indicator calculation: %s", missing_columns)
            return pd.DataFrame()

        for column in required_columns:
            normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
        normalized = normalized.dropna(subset=["Open", "High", "Low", "Close", "Volume"])
        return normalized

    def _calculate_momentum(self, dataframe: pd.DataFrame) -> Optional[float]:
        """Calculate percentage momentum from the latest close change."""

        if dataframe.empty or len(dataframe) < 2:
            return None
        latest_close = self._last_value(dataframe["Close"])
        previous_close = self._last_value(dataframe["Close"].shift(1))
        if latest_close is None or previous_close in (None, 0):
            return None
        return round(((latest_close - previous_close) / previous_close) * 100.0, 2)

    def _calculate_ema(self, series: pd.Series, length: int) -> Optional[float]:
        """Calculate an EMA using pandas rolling logic."""

        if series.empty:
            return None
        values = pd.to_numeric(series, errors="coerce")
        ema = values.ewm(span=length, adjust=False).mean()
        return self._last_value(ema)

    def _calculate_sma(self, series: pd.Series, length: int) -> Optional[float]:
        """Calculate an SMA using pandas rolling logic."""

        if series.empty:
            return None
        values = pd.to_numeric(series, errors="coerce")
        sma = values.rolling(window=length, min_periods=1).mean()
        return self._last_value(sma)

    def _calculate_vwap(self, dataframe: pd.DataFrame) -> Optional[float]:
        """Calculate the VWAP from OHLC and volume."""

        if dataframe.empty or dataframe["Volume"].dropna().empty:
            return None
        typical_price = (dataframe["High"] + dataframe["Low"] + dataframe["Close"]) / 3.0
        vwap = (typical_price * dataframe["Volume"]).cumsum() / dataframe["Volume"].cumsum()
        return self._last_value(vwap)

    def _calculate_rsi(self, series: pd.Series) -> Optional[float]:
        """Calculate a 14-period RSI using pandas-ta when available."""

        if series.empty:
            return None
        values = pd.to_numeric(series, errors="coerce").dropna()
        if values.empty:
            return None
        if pta is not None:
            try:
                result = pta.rsi(values, length=14)
                rsi_value = self._last_value(result)
                if rsi_value is not None:
                    return round(rsi_value, 2)
            except Exception as exc:  # pragma: no cover - defensive guard
                self.logger.debug("pandas_ta RSI calculation failed: %s", exc)

        if len(values) < 2:
            return None

        delta = values.diff().dropna()
        if delta.empty:
            return None
        gains = delta.clip(lower=0).fillna(0.0)
        losses = (-delta).clip(lower=0).fillna(0.0)

        avg_gain = gains.iloc[:14].mean() if len(gains) >= 14 else gains.mean()
        avg_loss = losses.iloc[:14].mean() if len(losses) >= 14 else losses.mean()

        for index in range(14, len(gains)):
            avg_gain = ((avg_gain * 13) + gains.iloc[index]) / 14.0
            avg_loss = ((avg_loss * 13) + losses.iloc[index]) / 14.0

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return round(float(rsi), 2)

    def _calculate_macd(self, series: pd.Series) -> tuple[Optional[float], Optional[float], Optional[float]]:
        """Calculate MACD, signal line and histogram values."""

        if series.empty:
            return None, None, None
        values = pd.to_numeric(series, errors="coerce")
        if pta is not None:
            try:
                macd_result = pta.macd(values, fast=12, slow=26, signal=9)
                if isinstance(macd_result, pd.DataFrame):
                    macd = self._last_value(macd_result.iloc[:, 0])
                    signal = self._last_value(macd_result.iloc[:, 1])
                    histogram = self._last_value(macd_result.iloc[:, 2])
                    return macd, signal, histogram
            except Exception as exc:  # pragma: no cover - defensive guard
                self.logger.debug("pandas_ta MACD calculation failed: %s", exc)

        ema_fast = values.ewm(span=12, adjust=False).mean()
        ema_slow = values.ewm(span=26, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line
        return self._last_value(macd_line), self._last_value(signal_line), self._last_value(histogram)

    def _calculate_atr(self, dataframe: pd.DataFrame) -> Optional[float]:
        """Calculate the ATR(14) from OHLC values."""

        if dataframe.empty or len(dataframe) < 2:
            return None
        high_low = dataframe["High"] - dataframe["Low"]
        high_close = (dataframe["High"] - dataframe["Close"].shift()).abs()
        low_close = (dataframe["Low"] - dataframe["Close"].shift()).abs()
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=14, min_periods=1).mean()
        return self._last_value(atr)

    def _calculate_bollinger(self, dataframe: pd.DataFrame) -> tuple[Optional[float], Optional[float], Optional[float]]:
        """Calculate Bollinger Bands from the close price."""

        if dataframe.empty:
            return None, None, None
        close = pd.to_numeric(dataframe["Close"], errors="coerce")
        middle = close.rolling(window=20, min_periods=1).mean()
        std = close.rolling(window=20, min_periods=1).std(ddof=0)
        upper = middle + (2 * std)
        lower = middle - (2 * std)
        return self._last_value(upper), self._last_value(middle), self._last_value(lower)

    def _calculate_relative_volume(self, dataframe: pd.DataFrame) -> Optional[float]:
        """Calculate relative volume versus the trailing 20-period average."""

        if dataframe.empty:
            return None
        volume = pd.to_numeric(dataframe["Volume"], errors="coerce")
        average = volume.rolling(window=20, min_periods=1).mean()
        latest_volume = self._last_value(volume)
        latest_average = self._last_value(average)
        if latest_volume is None or latest_average in (None, 0):
            return None
        return round(latest_volume / latest_average, 2)

    def _calculate_average_volume(self, dataframe: pd.DataFrame) -> Optional[float]:
        """Calculate a 20-period average volume."""

        if dataframe.empty:
            return None
        volume = pd.to_numeric(dataframe["Volume"], errors="coerce")
        avg = volume.rolling(window=20, min_periods=1).mean()
        return self._last_value(avg)

    def _last_value(self, series: Any) -> Optional[float]:
        """Return the latest numeric value from a Series-like object."""

        if series is None:
            return None
        try:
            if hasattr(series, "dropna"):
                values = series.dropna()
                if values.empty:
                    return None
                return float(values.iloc[-1])
            return float(series)
        except Exception:
            return None
