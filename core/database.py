"""SQLite database management using SQLAlchemy."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from loguru import logger
from sqlalchemy import Engine, create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from config import Settings
from data.models import Base, WatchlistItem


class DatabaseManager:
    """Create, initialize, and dispose the SQLAlchemy engine."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._engine: Engine | None = None
        self._session_factory: sessionmaker[Session] | None = None

    @property
    def engine(self) -> Engine:
        """Return the initialized SQLAlchemy engine."""

        if self._engine is None:
            raise RuntimeError("DatabaseManager has not been initialized")
        return self._engine

    def initialize(self) -> None:
        """Create the SQLite engine and session factory."""

        if self._engine is not None:
            return

        self._settings.database.path.parent.mkdir(parents=True, exist_ok=True)
        self._engine = create_engine(
            self._build_sqlite_url(self._settings.database.path),
            echo=self._settings.database.echo,
            future=True,
            connect_args={"check_same_thread": False},
            pool_pre_ping=self._settings.database.pool_pre_ping,
        )
        self._session_factory = sessionmaker(
            bind=self._engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
        Base.metadata.create_all(self._engine)
        logger.debug("Database initialized at {}", self._settings.database.path)

    @contextmanager
    def session_scope(self) -> Iterator[Session]:
        """Provide a transactional session scope."""

        if self._session_factory is None:
            raise RuntimeError("DatabaseManager has not been initialized")

        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            logger.exception("Database transaction failed")
            raise
        finally:
            session.close()

    def list_watchlist_items(self) -> list[WatchlistItem]:
        """Return the stored watchlist sorted by symbol."""

        if self._session_factory is None:
            raise RuntimeError("DatabaseManager has not been initialized")

        with self.session_scope() as session:
            statement = select(WatchlistItem).order_by(WatchlistItem.symbol.asc())
            return list(session.scalars(statement).all())

    def upsert_watchlist_item(
        self,
        symbol: str,
        *,
        name: str = "",
        notes: str = "",
    ) -> WatchlistItem:
        """Insert or update a watchlist entry."""

        normalized_symbol = symbol.strip().upper()
        if not normalized_symbol:
            raise ValueError("symbol must not be empty")

        with self.session_scope() as session:
            item = session.get(WatchlistItem, normalized_symbol)
            if item is None:
                item = WatchlistItem(symbol=normalized_symbol, name=name, notes=notes)
                session.add(item)
            else:
                item.name = name
                item.notes = notes
            session.flush()
            return item

    def delete_watchlist_item(self, symbol: str) -> bool:
        """Delete a watchlist entry if it exists."""

        normalized_symbol = symbol.strip().upper()
        if not normalized_symbol:
            return False

        with self.session_scope() as session:
            item = session.get(WatchlistItem, normalized_symbol)
            if item is None:
                return False
            session.delete(item)
            return True

    def seed_watchlist(self, symbols: list[str]) -> None:
        """Populate the watchlist with default symbols if needed."""

        for symbol in symbols:
            self.upsert_watchlist_item(symbol, name=symbol)

    def dispose(self) -> None:
        """Dispose the SQLAlchemy engine safely."""

        if self._engine is None:
            return
        self._engine.dispose()
        logger.debug("Database engine disposed")
        self._engine = None
        self._session_factory = None

    def _build_sqlite_url(self, database_path: Path) -> str:
        """Build a SQLAlchemy SQLite connection string."""

        return f"sqlite+pysqlite:///{database_path.as_posix()}"
