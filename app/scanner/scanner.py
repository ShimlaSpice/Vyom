"""Scanner orchestration for the Vyom desktop application.

The scanner engine is intentionally modular so future versions can swap the
mock universe for live market data without changing the surrounding workflow.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

from app.market.market_data_provider import MarketDataProvider
from app.scanner.filters import FilterEngine
from app.scanner.scoring import ScoringEngine

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class StockData:
    """Normalized stock candidate data ready for filtering and scoring."""

    symbol: str
    name: str
    sector: str = "Unknown"
    price: float = 0.0
    momentum: float = 0.0
    volume: float = 0.0
    quality: float = 0.0
    volatility: float = 0.0
    volume_score: float = 0.0
    price_score: float = 0.0

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "StockData":
        """Create a StockData object from a mapping payload."""

        return cls(
            symbol=str(payload.get("symbol", "")).strip().upper(),
            name=str(payload.get("name") or payload.get("symbol") or "Unknown"),
            sector=str(payload.get("sector") or "Unknown"),
            price=float(payload.get("price", 0.0) or 0.0),
            momentum=float(payload.get("momentum", 0.0) or 0.0),
            volume=float(payload.get("volume", 0.0) or 0.0),
            quality=float(payload.get("quality", 0.0) or 0.0),
            volatility=float(payload.get("volatility", 0.0) or 0.0),
            volume_score=float(payload.get("volume_score", 0.0) or 0.0),
            price_score=float(payload.get("price_score", 0.0) or 0.0),
        )

    def to_mapping(self) -> dict[str, Any]:
        """Convert the stock data into the mapping format the scoring engine expects."""

        return {
            "symbol": self.symbol,
            "name": self.name,
            "sector": self.sector,
            "price": self.price,
            "momentum": self.momentum,
            "volume": self.volume,
            "quality": self.quality,
            "volatility": self.volatility,
            "volume_score": self.volume_score,
            "price_score": self.price_score,
        }


class ScannerEngine:
    """Orchestrate scanning, filtering, scoring, and ranking of candidates."""

    def __init__(
        self,
        scoring_engine: Optional[ScoringEngine] = None,
        filter_engine: Optional[FilterEngine] = None,
        market_data_provider: Optional[MarketDataProvider] = None,
        logger_instance: Optional[logging.Logger] = None,
    ) -> None:
        """Create a scanner engine.

        Args:
            scoring_engine: Optional scoring engine implementation.
            filter_engine: Optional filtering engine implementation.
            logger_instance: Optional logger for diagnostics.
        """

        self.scoring_engine = scoring_engine or ScoringEngine()
        self.filter_engine = filter_engine or FilterEngine()
        self.market_data_provider = market_data_provider or MarketDataProvider()
        self.logger = logger_instance or logger

    def scan(self, limit: int = 10, universe: Optional[Sequence[Mapping[str, Any]]] = None) -> list[dict[str, Any]]:
        """Scan a universe of stocks and return ranked results.

        Args:
            limit: Maximum number of results to return.
            universe: Optional predefined universe of candidates. When omitted,
                mock stock data is generated.

        Returns:
            A list of ranked scan results.
        """

        candidates = self.build_candidates(universe=universe)
        if not candidates:
            self.logger.warning("No candidates available for scanning")
            return []

        self.logger.info("Scanning %d candidates", len(candidates))
        candidate_payloads = [candidate.to_mapping() for candidate in candidates]
        filtered_candidates = self.filter_engine.filter_candidates(candidate_payloads)
        scored_results: list[dict[str, Any]] = []

        for candidate in filtered_candidates:
            score = self.scoring_engine.score_candidate(candidate)
            reasons = self._build_reasons(candidate, score)
            scored_results.append(
                {
                    "symbol": candidate["symbol"],
                    "name": candidate.get("name", candidate["symbol"]),
                    "sector": candidate.get("sector", "Unknown"),
                    "score": score,
                    "price": candidate.get("price"),
                    "momentum": candidate.get("momentum"),
                    "volume": candidate.get("volume"),
                    "quality": candidate.get("quality"),
                    "reasons": reasons,
                }
            )

        scored_results.sort(key=lambda item: item["score"], reverse=True)
        self.logger.info("Scanner produced %d ranked results", len(scored_results))
        return scored_results[:limit]

    def build_candidates(self, universe: Optional[Sequence[Mapping[str, Any]] | Sequence[str]] = None) -> list[StockData]:
        """Build a list of StockData candidates from live market data or explicit input."""

        if universe is not None:
            if not universe:
                return []
            if all(isinstance(item, str) for item in universe):
                return self._build_candidates_from_provider(list(universe))
            return [StockData.from_mapping(candidate) for candidate in universe]

        return self._build_candidates_from_provider()

    def _build_candidates_from_provider(self, symbols: Optional[Sequence[str]] = None) -> list[StockData]:
        """Fetch OHLCV data from the market provider and convert it into StockData objects."""

        try:
            future = self.market_data_provider.fetch_ohlcv_async(list(symbols) if symbols else None)
            market_frames = future.result(timeout=self.market_data_provider.timeout + 5)
        except Exception as exc:  # pragma: no cover - defensive guard
            self.logger.warning("Live market data fetch failed: %s", exc)
            return self._build_mock_candidates()

        if not market_frames:
            self.logger.warning("No market data available from provider")
            return self._build_mock_candidates()

        candidates: list[StockData] = []
        for symbol, frame in market_frames.items():
            candidates.append(self._build_candidate_from_frame(symbol, frame))
        return candidates or self._build_mock_candidates()

    def _build_candidate_from_frame(self, symbol: str, frame: Any) -> StockData:
        """Convert a provider DataFrame into a normalized StockData object."""

        if not hasattr(frame, "empty"):
            return StockData(symbol=symbol, name=symbol)

        if frame.empty:
            return StockData(symbol=symbol, name=symbol)

        close_series = frame.get("Close") if isinstance(frame, Mapping) else None
        if close_series is None and hasattr(frame, "__getitem__"):
            try:
                close_series = frame["Close"]
            except Exception:
                close_series = None

        price = 0.0
        momentum = 0.0
        volume = 0.0
        quality = 0.0
        volatility = 0.0
        volume_score = 0.0
        price_score = 0.0

        if close_series is not None and len(close_series) > 0:
            prices = [float(value) for value in close_series if value is not None]
            if prices:
                price = prices[-1]
                if len(prices) >= 2:
                    momentum = ((prices[-1] - prices[-2]) / prices[-2]) * 100 if prices[-2] else 0.0
                price_score = min(100.0, max(0.0, (price / 1000.0) * 10.0))

        volume_series = None
        if hasattr(frame, "get"):
            volume_series = frame.get("Volume")
        elif hasattr(frame, "__getitem__"):
            try:
                volume_series = frame["Volume"]
            except Exception:
                volume_series = None

        if volume_series is not None:
            try:
                volume = float(volume_series.iloc[-1]) if hasattr(volume_series, "iloc") else float(volume_series[-1])
            except Exception:
                volume = 0.0

        volume_score = min(100.0, max(0.0, (volume / 1_000_000.0) * 20.0))
        quality = min(100.0, max(0.0, 70.0 + (momentum / 2.0)))
        volatility = 0.02 + (abs(momentum) / 1000.0) if momentum else 0.02
        return StockData(
            symbol=symbol,
            name=symbol,
            sector="Unknown",
            price=price,
            momentum=momentum,
            volume=volume,
            quality=quality,
            volatility=volatility,
            volume_score=volume_score,
            price_score=price_score,
        )

    def _build_mock_candidates(self) -> list[StockData]:
        """Return a small mock universe of stock candidates for fallback use."""

        return [StockData.from_mapping(candidate) for candidate in self._build_mock_universe()]

    def _build_mock_universe(self) -> list[dict[str, Any]]:
        """Return a small mock universe of stocks for development use."""

        return [
            {
                "symbol": "RELIANCE",
                "name": "Reliance Industries",
                "sector": "Energy",
                "price": 2700.0,
                "momentum": 88.0,
                "volume": 4_500_000.0,
                "quality": 90.0,
                "volatility": 0.035,
                "volume_score": 92.0,
                "price_score": 88.0,
            },
            {
                "symbol": "TCS",
                "name": "Tata Consultancy Services",
                "sector": "Technology",
                "price": 3600.0,
                "momentum": 78.0,
                "volume": 2_300_000.0,
                "quality": 82.0,
                "volatility": 0.042,
                "volume_score": 76.0,
                "price_score": 70.0,
            },
            {
                "symbol": "HDFCBANK",
                "name": "HDFC Bank",
                "sector": "Financials",
                "price": 1680.0,
                "momentum": 71.0,
                "volume": 1_800_000.0,
                "quality": 74.0,
                "volatility": 0.039,
                "volume_score": 68.0,
                "price_score": 74.0,
            },
            {
                "symbol": "INFY",
                "name": "Infosys",
                "sector": "Technology",
                "price": 1450.0,
                "momentum": 62.0,
                "volume": 900_000.0,
                "quality": 58.0,
                "volatility": 0.05,
                "volume_score": 55.0,
                "price_score": 60.0,
            },
        ]

    def _build_reasons(self, candidate: Mapping[str, Any], score: int) -> list[str]:
        """Create concise human-readable reasons for a scored result."""

        reasons: list[str] = []
        if score >= 80:
            reasons.append("Strong overall momentum")
        elif score >= 65:
            reasons.append("Solid risk-adjusted profile")
        else:
            reasons.append("Moderate setup")

        if float(candidate.get("quality", 0)) >= 80:
            reasons.append("High quality")
        if float(candidate.get("volume", 0)) >= 2_000_000:
            reasons.append("Healthy trading volume")
        if float(candidate.get("volatility", 0)) <= 0.04:
            reasons.append("Low volatility")

        return reasons
