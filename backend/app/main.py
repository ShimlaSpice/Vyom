"""FastAPI entrypoint for the local VYOM Trader AI web application."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Iterator

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import uvicorn
from sqlalchemy.orm import Session

from config import ConfigManager
from core.cache import CacheManager
from core.database import DatabaseManager
from core.logger import LoggerManager
from core.scheduler import SchedulerManager
from data.models import DecisionRun, MarketSnapshot, MarketSymbol, NewsItem

from .schemas import (
    DashboardResponse,
    DashboardSummary,
    DecisionRead,
    DecisionRunRequest,
    NewsCreate,
    NewsRead,
    SnapshotCreate,
    SnapshotRead,
    SymbolCreate,
    SymbolRead,
)
from .services import DecisionEngine, MarketService, NewsService, seed_demo_data


class AppState:
    """Container for application-level singletons."""

    def __init__(self) -> None:
        self.config_manager = ConfigManager()
        self.settings = self.config_manager.settings
        self.logger_manager = LoggerManager(self.settings)
        self.database_manager = DatabaseManager(self.settings)
        self.scheduler_manager = SchedulerManager(self.settings)
        self.cache_manager = CacheManager(self.settings)
        self.market_service = MarketService()
        self.news_service = NewsService()
        self.decision_engine = DecisionEngine()


state = AppState()


def _get_state(request: Request) -> AppState:
    return request.app.state.container


def _session_dependency(request: Request) -> Iterator[Session]:
    container = _get_state(request)
    with container.database_manager.session_scope() as session:
        yield session


def _symbol_to_read(symbol: MarketSymbol) -> SymbolRead:
    return SymbolRead.model_validate(symbol)


def _snapshot_to_read(snapshot: MarketSnapshot) -> SnapshotRead:
    return SnapshotRead.model_validate(snapshot)


def _news_to_read(news_item: NewsItem) -> NewsRead:
    return NewsRead.model_validate(news_item)


def _decision_to_read(decision: DecisionRun, symbol: MarketSymbol) -> DecisionRead:
    return DecisionRead(
        id=decision.id,
        symbol_id=decision.symbol_id,
        symbol=symbol.symbol,
        horizon=decision.horizon,
        decision=decision.decision,
        confidence=decision.confidence,
        rationale=decision.rationale,
        model_name=decision.model_name,
        close_price=decision.close_price,
        sentiment_score=decision.sentiment_score,
        created_at=decision.created_at,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Bootstrap database and logging before serving requests."""

    app.state.container = state
    state.logger_manager.configure()
    state.database_manager.initialize(create_schema=False)
    with state.database_manager.session_scope() as session:
        seed_demo_data(session)
    logger.info("VYOM Trader AI web app bootstrapped")
    yield
    state.scheduler_manager.shutdown(wait=False)
    state.database_manager.dispose()


app = FastAPI(
    title="VYOM Trader AI Web",
    version=state.settings.application.version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check(session: Session = Depends(_session_dependency)) -> dict[str, Any]:
    """Return a simple health payload for the frontend."""

    container = state
    return {
        "status": "ok",
        "application": container.settings.application.name,
        "symbols": len(container.market_service.list_symbols(session)),
        "snapshots": container.market_service.count_snapshots(session),
        "news_items": container.news_service.count_news(session),
        "decisions": container.decision_engine.count_decisions(session),
    }


@app.get("/api/dashboard", response_model=DashboardResponse)
def dashboard(session: Session = Depends(_session_dependency)) -> DashboardResponse:
    """Return the starter dashboard payload."""

    container = state
    symbols = container.market_service.list_symbols(session)
    snapshots = container.market_service.list_snapshots(session, limit=6)
    news_items = container.news_service.list_news(session, limit=6)
    decisions = container.decision_engine.list_decisions(session, limit=6)
    decision_reads: list[DecisionRead] = []
    for decision in decisions:
        symbol = session.get(MarketSymbol, decision.symbol_id)
        if symbol is None:
            continue
        decision_reads.append(_decision_to_read(decision, symbol))
    return DashboardResponse(
        summary=DashboardSummary(
            symbols=len(symbols),
            snapshots=len(snapshots),
            news_items=len(news_items),
            decisions=len(decisions),
        ),
        symbols=[_symbol_to_read(symbol) for symbol in symbols],
        latest_snapshots=[_snapshot_to_read(snapshot) for snapshot in snapshots],
        latest_news=[_news_to_read(news_item) for news_item in news_items],
        latest_decisions=decision_reads,
    )


@app.get("/api/symbols", response_model=list[SymbolRead])
def list_symbols(session: Session = Depends(_session_dependency)) -> list[SymbolRead]:
    """Return all tracked symbols."""

    return [_symbol_to_read(symbol) for symbol in state.market_service.list_symbols(session)]


@app.post("/api/symbols", response_model=SymbolRead, status_code=201)
def create_symbol(payload: SymbolCreate, session: Session = Depends(_session_dependency)) -> SymbolRead:
    """Create a tracked symbol."""

    existing = state.market_service.get_symbol_by_name(session, payload.symbol)
    if existing is not None:
        raise HTTPException(status_code=409, detail="Symbol already exists")
    symbol = state.market_service.create_symbol(
        session,
        symbol=payload.symbol,
        exchange=payload.exchange,
        instrument_type=payload.instrument_type,
        is_active=payload.is_active,
    )
    return _symbol_to_read(symbol)


@app.get("/api/market/snapshots", response_model=list[SnapshotRead])
def list_snapshots(session: Session = Depends(_session_dependency)) -> list[SnapshotRead]:
    """Return recent market snapshots."""

    return [_snapshot_to_read(snapshot) for snapshot in state.market_service.list_snapshots(session)]


@app.post("/api/market/snapshots", response_model=SnapshotRead, status_code=201)
def create_snapshot(
    payload: SnapshotCreate,
    session: Session = Depends(_session_dependency),
) -> SnapshotRead:
    """Create a market snapshot."""

    if session.get(MarketSymbol, payload.symbol_id) is None:
        raise HTTPException(status_code=404, detail="Symbol not found")
    snapshot = state.market_service.create_snapshot(
        session,
        symbol_id=payload.symbol_id,
        snapshot_at=payload.snapshot_at,
        open_price=payload.open_price,
        high_price=payload.high_price,
        low_price=payload.low_price,
        close_price=payload.close_price,
        volume=payload.volume,
        source=payload.source,
    )
    return _snapshot_to_read(snapshot)


@app.get("/api/news/items", response_model=list[NewsRead])
def list_news(session: Session = Depends(_session_dependency)) -> list[NewsRead]:
    """Return recent news items."""

    return [_news_to_read(item) for item in state.news_service.list_news(session)]


@app.post("/api/news/items", response_model=NewsRead, status_code=201)
def create_news(payload: NewsCreate, session: Session = Depends(_session_dependency)) -> NewsRead:
    """Create a news item."""

    if session.get(MarketSymbol, payload.symbol_id) is None:
        raise HTTPException(status_code=404, detail="Symbol not found")
    item = state.news_service.create_news(
        session,
        symbol_id=payload.symbol_id,
        title=payload.title,
        summary=payload.summary,
        published_at=payload.published_at,
        source=payload.source,
        url=payload.url,
        sentiment_score=payload.sentiment_score,
    )
    return _news_to_read(item)


@app.get("/api/decisions", response_model=list[DecisionRead])
def list_decisions(session: Session = Depends(_session_dependency)) -> list[DecisionRead]:
    """Return recent decision runs."""

    decisions = state.decision_engine.list_decisions(session)
    results: list[DecisionRead] = []
    for decision in decisions:
        symbol = session.get(MarketSymbol, decision.symbol_id)
        if symbol is None:
            continue
        results.append(_decision_to_read(decision, symbol))
    return results


@app.post("/api/decisions/run", response_model=DecisionRead, status_code=201)
def run_decision(
    payload: DecisionRunRequest,
    session: Session = Depends(_session_dependency),
) -> DecisionRead:
    """Run the heuristic decision engine for a symbol."""

    symbol = state.market_service.get_symbol_by_name(session, payload.symbol)
    if symbol is None:
        raise HTTPException(status_code=404, detail="Symbol not found")
    decision = state.decision_engine.run(session, symbol=symbol, horizon=payload.horizon)
    return _decision_to_read(decision, symbol)


def main() -> int:
    """Run the application with Uvicorn."""

    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=False)
    return 0
