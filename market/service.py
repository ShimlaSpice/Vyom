"""Market domain service boundaries."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Sequence


@dataclass(slots=True, frozen=True)
class MarketUniverseRequest:
    """Describe a market-scanner request."""

    exchange: str
    segment: str


@dataclass(slots=True, frozen=True)
class MarketScanResult:
    """Represent a ranked market opportunity."""

    symbol: str
    name: str
    last_price: float
    change_pct: float
    volume: int
    score: float
    signal: str


class MarketService:
    """Encapsulate market-data related business rules."""

    _demo_universe = (
        "RELIANCE",
        "TCS",
        "INFY",
        "HDFCBANK",
        "ICICIBANK",
        "SBIN",
        "LT",
        "ITC",
        "TATAMOTORS",
        "BHARTIARTL",
        "AXISBANK",
        "HINDUNILVR",
    )

    def build_universe_request(self, exchange: str, segment: str) -> MarketUniverseRequest:
        """Build a typed request object for scanner workflows."""

        return MarketUniverseRequest(exchange=exchange, segment=segment)

    def scan(self, request: MarketUniverseRequest, limit: int = 10) -> list[MarketScanResult]:
        """Produce a synthetic market scan for the requested universe."""

        universe = self._build_universe(request)
        return self.scan_symbols(universe[:limit])

    def scan_symbols(self, symbols: Sequence[str]) -> list[MarketScanResult]:
        """Score a list of symbols and rank them for the dashboard."""

        results = [self._score_symbol(symbol) for symbol in symbols if symbol.strip()]
        return sorted(results, key=lambda item: item.score, reverse=True)

    def build_price_series(self, symbol: str, points: int = 60) -> list[float]:
        """Create a deterministic intraday-style price series for charts."""

        rng = random.Random(self._seed(symbol, bucket="chart"))
        base_price = 100 + self._symbol_bias(symbol)
        price = float(base_price)
        series: list[float] = []

        for index in range(points):
            drift = rng.uniform(-1.35, 1.65)
            wave = math.sin(index / 4.5) * 0.85
            price = max(10.0, price + drift + wave)
            series.append(round(price, 2))

        return series

    def _build_universe(self, request: MarketUniverseRequest) -> list[str]:
        """Pick a synthetic universe based on the request."""

        exchange = request.exchange.strip().upper()
        segment = request.segment.strip().upper()

        if "BANK" in segment:
            return ["HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK", "PNB"]
        if "IT" in segment:
            return ["TCS", "INFY", "WIPRO", "TECHM", "HCLTECH", "LTIM"]
        if exchange == "BSE":
            return ["RELIANCE", "TCS", "INFY", "ITC", "LT", "SBIN", "HDFCBANK"]
        return list(self._demo_universe)

    def _score_symbol(self, symbol: str) -> MarketScanResult:
        """Generate a repeatable ranking signal for a symbol."""

        normalized_symbol = symbol.strip().upper()
        rng = random.Random(self._seed(normalized_symbol, bucket="scan"))
        series = self.build_price_series(normalized_symbol, points=24)
        first_price = series[0]
        last_price = series[-1]
        change_pct = ((last_price - first_price) / first_price) * 100 if first_price else 0.0
        volume = int(250_000 + self._symbol_bias(normalized_symbol) * 12_000 + rng.uniform(0, 180_000))
        momentum = max(-12.0, min(12.0, change_pct * 2.5))
        trend = max(-8.0, min(8.0, (last_price - series[-6]) * 3.0))
        score = round(max(0.0, min(100.0, 50.0 + momentum + trend + rng.uniform(-6, 8))), 2)
        signal = self._classify_score(score)

        return MarketScanResult(
            symbol=normalized_symbol,
            name=self._company_name(normalized_symbol),
            last_price=round(last_price, 2),
            change_pct=round(change_pct, 2),
            volume=volume,
            score=score,
            signal=signal,
        )

    def _company_name(self, symbol: str) -> str:
        """Map a symbol to a readable display name."""

        return f"{symbol} Ltd."

    def _classify_score(self, score: float) -> str:
        """Convert a numeric score into a trading signal."""

        if score >= 72:
            return "Strong Buy"
        if score >= 58:
            return "Watch"
        if score >= 45:
            return "Neutral"
        return "Avoid"

    def _symbol_bias(self, symbol: str) -> int:
        """Create a stable bias from the symbol text."""

        return sum(ord(char) for char in symbol) % 40

    def _seed(self, symbol: str, *, bucket: str) -> str:
        """Build a deterministic seed string."""

        minute_bucket = datetime.now(UTC).strftime("%Y%m%d%H%M")
        return f"{symbol}:{bucket}:{minute_bucket}"
