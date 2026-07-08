"""Pydantic schemas for the web API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SymbolBase(BaseModel):
    """Shared symbol fields."""

    symbol: str = Field(min_length=1, max_length=32)
    exchange: str = Field(min_length=1, max_length=32)
    instrument_type: str = Field(min_length=1, max_length=32)
    is_active: bool = True


class SymbolCreate(SymbolBase):
    """Payload for creating a symbol."""


class SymbolRead(SymbolBase):
    """API representation of a symbol."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class SnapshotBase(BaseModel):
    """Shared market snapshot fields."""

    symbol_id: int
    snapshot_at: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    source: str = Field(default="manual", max_length=64)


class SnapshotCreate(SnapshotBase):
    """Payload for creating a market snapshot."""


class SnapshotRead(SnapshotBase):
    """API representation of a market snapshot."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class NewsBase(BaseModel):
    """Shared news item fields."""

    symbol_id: int
    title: str = Field(min_length=1, max_length=256)
    summary: str = Field(default="", max_length=5000)
    source: str = Field(default="manual", max_length=64)
    url: str = Field(default="", max_length=512)
    published_at: datetime
    sentiment_score: float = 0.0


class NewsCreate(NewsBase):
    """Payload for creating a news item."""


class NewsRead(NewsBase):
    """API representation of a news item."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class DecisionRunRequest(BaseModel):
    """Request payload for running the decision engine."""

    symbol: str = Field(min_length=1, max_length=32)
    horizon: str = Field(default="intraday", max_length=32)


class DecisionRead(BaseModel):
    """API representation of a decision."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol_id: int
    symbol: str
    horizon: str
    decision: str
    confidence: float
    rationale: str
    model_name: str
    close_price: float
    sentiment_score: float
    created_at: datetime


class DashboardSummary(BaseModel):
    """Top-level dashboard counts."""

    symbols: int
    snapshots: int
    news_items: int
    decisions: int


class DashboardResponse(BaseModel):
    """Initial dashboard payload for the frontend."""

    summary: DashboardSummary
    symbols: list[SymbolRead]
    latest_snapshots: list[SnapshotRead]
    latest_news: list[NewsRead]
    latest_decisions: list[DecisionRead]
