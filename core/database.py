"""SQLite database management using SQLAlchemy."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from loguru import logger
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import Settings
from data.models import Base


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

    def initialize(self, *, create_schema: bool = True) -> None:
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
        if create_schema:
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
