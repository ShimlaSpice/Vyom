"""Domain services for market data, news, and decisioning."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from data.models import DecisionRun, MarketSnapshot, MarketSymbol, NewsItem


class MarketService:
    """Market-data persistence and query helpers."""

    def list_symbols(self, session: Session) -> list[MarketSymbol]:
        """Return all tracked symbols."""

        statement = select(MarketSymbol).order_by(MarketSymbol.symbol.asc())
        return list(session.scalars(statement).all())

    def create_symbol(
        self,
        session: Session,
        *,
        symbol: str,
        exchange: str,
        instrument_type: str,
        is_active: bool = True,
    ) -> MarketSymbol:
        """Create and persist a market symbol."""

        record = MarketSymbol(
            symbol=symbol.upper(),
            exchange=exchange.upper(),
            instrument_type=instrument_type.upper(),
            is_active=is_active,
        )
        session.add(record)
        session.flush()
        return record

    def get_symbol_by_name(self, session: Session, symbol: str) -> MarketSymbol | None:
        """Look up a symbol by its ticker."""

        statement = select(MarketSymbol).where(MarketSymbol.symbol == symbol.upper())
        return session.scalar(statement)

    def list_snapshots(self, session: Session, *, limit: int = 20) -> list[MarketSnapshot]:
        """Return the latest market snapshots."""

        statement = (
            select(MarketSnapshot)
            .order_by(MarketSnapshot.snapshot_at.desc(), MarketSnapshot.id.desc())
            .limit(limit)
        )
        return list(session.scalars(statement).all())

    def create_snapshot(
        self,
        session: Session,
        *,
        symbol_id: int,
        snapshot_at: datetime,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        volume: int,
        source: str = "manual",
    ) -> MarketSnapshot:
        """Create and persist a market snapshot."""

        record = MarketSnapshot(
            symbol_id=symbol_id,
            snapshot_at=snapshot_at,
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
            volume=volume,
            source=source,
        )
        session.add(record)
        session.flush()
        return record

    def latest_snapshot_for_symbol(
        self,
        session: Session,
        *,
        symbol_id: int,
    ) -> MarketSnapshot | None:
        """Return the newest snapshot for a symbol."""

        statement = (
            select(MarketSnapshot)
            .where(MarketSnapshot.symbol_id == symbol_id)
            .order_by(MarketSnapshot.snapshot_at.desc(), MarketSnapshot.id.desc())
            .limit(1)
        )
        return session.scalar(statement)

    def count_snapshots(self, session: Session) -> int:
        """Count snapshot rows."""

        return int(session.scalar(select(func.count()).select_from(MarketSnapshot)) or 0)


class NewsService:
    """News persistence and query helpers."""

    def list_news(self, session: Session, *, limit: int = 20) -> list[NewsItem]:
        """Return the latest news items."""

        statement = (
            select(NewsItem)
            .order_by(NewsItem.published_at.desc(), NewsItem.id.desc())
            .limit(limit)
        )
        return list(session.scalars(statement).all())

    def create_news(
        self,
        session: Session,
        *,
        symbol_id: int,
        title: str,
        summary: str,
        published_at: datetime,
        source: str = "manual",
        url: str = "",
        sentiment_score: float = 0.0,
    ) -> NewsItem:
        """Create and persist a news article."""

        record = NewsItem(
            symbol_id=symbol_id,
            title=title,
            summary=summary,
            source=source,
            url=url,
            published_at=published_at,
            sentiment_score=sentiment_score,
        )
        session.add(record)
        session.flush()
        return record

    def latest_news_for_symbol(
        self,
        session: Session,
        *,
        symbol_id: int,
        limit: int = 3,
    ) -> list[NewsItem]:
        """Return the newest news items for a symbol."""

        statement = (
            select(NewsItem)
            .where(NewsItem.symbol_id == symbol_id)
            .order_by(NewsItem.published_at.desc(), NewsItem.id.desc())
            .limit(limit)
        )
        return list(session.scalars(statement).all())

    def count_news(self, session: Session) -> int:
        """Count news rows."""

        return int(session.scalar(select(func.count()).select_from(NewsItem)) or 0)


class DecisionEngine:
    """Simple explainable decision engine for the local application."""

    def run(
        self,
        session: Session,
        *,
        symbol: MarketSymbol,
        horizon: str,
    ) -> DecisionRun:
        """Generate and persist a decision for a symbol."""

        market_service = MarketService()
        news_service = NewsService()
        snapshot = market_service.latest_snapshot_for_symbol(session, symbol_id=symbol.id)
        if snapshot is None:
            raise ValueError(f"No market snapshot available for {symbol.symbol}")

        recent_news = news_service.latest_news_for_symbol(session, symbol_id=symbol.id, limit=3)
        sentiment_score = self._average_sentiment(recent_news)
        momentum = 0.0 if snapshot.open_price == 0 else (snapshot.close_price - snapshot.open_price) / snapshot.open_price
        score = momentum * 100 + sentiment_score

        if score >= 0.75:
            decision = "BUY"
        elif score <= -0.75:
            decision = "SELL"
        else:
            decision = "HOLD"

        confidence = min(0.95, max(0.55, 0.60 + abs(score) / 4))
        rationale = (
            f"Momentum {momentum:+.2%}, sentiment {sentiment_score:+.2f}, "
            f"latest close {snapshot.close_price:.2f} versus open {snapshot.open_price:.2f}."
        )

        record = DecisionRun(
            symbol_id=symbol.id,
            horizon=horizon,
            decision=decision,
            confidence=confidence,
            rationale=rationale,
            model_name="heuristic-v1",
            close_price=snapshot.close_price,
            sentiment_score=sentiment_score,
        )
        session.add(record)
        session.flush()
        return record

    def list_decisions(self, session: Session, *, limit: int = 20) -> list[DecisionRun]:
        """Return the latest decision runs."""

        statement = (
            select(DecisionRun)
            .order_by(DecisionRun.created_at.desc(), DecisionRun.id.desc())
            .limit(limit)
        )
        return list(session.scalars(statement).all())

    def count_decisions(self, session: Session) -> int:
        """Count decision rows."""

        return int(session.scalar(select(func.count()).select_from(DecisionRun)) or 0)

    def _average_sentiment(self, news_items: list[NewsItem]) -> float:
        """Average recent sentiment while handling missing articles gracefully."""

        if not news_items:
            return 0.0
        total = sum(item.sentiment_score for item in news_items)
        return total / len(news_items)


def seed_demo_data(session: Session) -> None:
    """Seed a small, deterministic dataset for local development."""

    if session.scalar(select(func.count()).select_from(MarketSymbol)):
        return

    market_service = MarketService()
    news_service = NewsService()
    decision_engine = DecisionEngine()
    now = datetime.utcnow()

    symbols = [
        market_service.create_symbol(session, symbol="RELIANCE", exchange="NSE", instrument_type="EQUITY"),
        market_service.create_symbol(session, symbol="TCS", exchange="NSE", instrument_type="EQUITY"),
        market_service.create_symbol(session, symbol="INFY", exchange="NSE", instrument_type="EQUITY"),
    ]

    for index, symbol in enumerate(symbols, start=1):
        base = 2500.0 + (index * 150)
        market_service.create_snapshot(
            session,
            symbol_id=symbol.id,
            snapshot_at=now - timedelta(minutes=15 * index),
            open_price=base,
            high_price=base * 1.015,
            low_price=base * 0.992,
            close_price=base * (1.004 if index % 2 else 0.996),
            volume=1_000_000 + (index * 50_000),
            source="seed",
        )
        news_service.create_news(
            session,
            symbol_id=symbol.id,
            title=f"{symbol.symbol} momentum stays active",
            summary="Seed news item for the local development dashboard.",
            published_at=now - timedelta(hours=index),
            source="seed",
            url="",
            sentiment_score=0.15 if index != 2 else -0.08,
        )
        decision_engine.run(session, symbol=symbol, horizon="intraday")

