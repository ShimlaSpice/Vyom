"""Market domain service boundaries."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class MarketUniverseRequest:
    """Describe a future market-scanner request."""

    exchange: str
    segment: str


class MarketService:
    """Encapsulate market-data related business rules."""

    def build_universe_request(self, exchange: str, segment: str) -> MarketUniverseRequest:
        """Build a typed request object for future scanner workflows."""

        return MarketUniverseRequest(exchange=exchange, segment=segment)

    def scan(self, request: MarketUniverseRequest) -> list[str]:
        """Reserve the scan boundary for future implementation."""

        raise NotImplementedError("Market scanning is not implemented yet")
