"""Shared SQLAlchemy model primitives for the web application."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models in the application."""


class TimestampMixin:
    """Add created and updated timestamps to concrete tables."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class MarketSymbol(TimestampMixin, Base):
    """Listed instrument tracked by market-data workflows."""

    __tablename__ = "market_symbols"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    exchange: Mapped[str] = mapped_column(String(32), nullable=False)
    instrument_type: Mapped[str] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    snapshots: Mapped[list["MarketSnapshot"]] = relationship(
        back_populates="symbol_ref",
        cascade="all, delete-orphan",
    )
    news_items: Mapped[list["NewsItem"]] = relationship(
        back_populates="symbol_ref",
        cascade="all, delete-orphan",
    )
    decisions: Mapped[list["DecisionRun"]] = relationship(
        back_populates="symbol_ref",
        cascade="all, delete-orphan",
    )


class MarketSnapshot(TimestampMixin, Base):
    """Single OHLCV observation for a symbol."""

    __tablename__ = "market_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol_id: Mapped[int] = mapped_column(ForeignKey("market_symbols.id"), nullable=False)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False, index=True)
    open_price: Mapped[float] = mapped_column(Float, nullable=False)
    high_price: Mapped[float] = mapped_column(Float, nullable=False)
    low_price: Mapped[float] = mapped_column(Float, nullable=False)
    close_price: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="seed")

    symbol_ref: Mapped["MarketSymbol"] = relationship(back_populates="snapshots")


class NewsItem(TimestampMixin, Base):
    """News headline linked to a symbol."""

    __tablename__ = "news_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol_id: Mapped[int] = mapped_column(ForeignKey("market_symbols.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="seed")
    url: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    symbol_ref: Mapped["MarketSymbol"] = relationship(back_populates="news_items")


class DecisionRun(TimestampMixin, Base):
    """Explainable decision produced by the engine."""

    __tablename__ = "decision_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol_id: Mapped[int] = mapped_column(ForeignKey("market_symbols.id"), nullable=False)
    horizon: Mapped[str] = mapped_column(String(32), nullable=False)
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False, default="heuristic-v1")
    close_price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    symbol_ref: Mapped["MarketSymbol"] = relationship(back_populates="decisions")


Index("ix_market_snapshots_symbol_id_snapshot_at", MarketSnapshot.symbol_id, MarketSnapshot.snapshot_at.desc())
Index("ix_news_items_symbol_id_published_at", NewsItem.symbol_id, NewsItem.published_at.desc())
Index("ix_decision_runs_symbol_id_created_at", DecisionRun.symbol_id, DecisionRun.created_at.desc())
