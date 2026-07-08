"""News domain service boundaries."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NewsQuery:
    """Describe a future news lookup request."""

    symbol: str
    source: str | None = None


class NewsService:
    """Encapsulate news acquisition and preparation rules."""

    def build_query(self, symbol: str, source: str | None = None) -> NewsQuery:
        """Build a typed query object for future news workflows."""

        return NewsQuery(symbol=symbol, source=source)

    def fetch(self, query: NewsQuery) -> list[str]:
        """Reserve the fetch boundary for future implementation."""

        raise NotImplementedError("News analysis is not implemented yet")
