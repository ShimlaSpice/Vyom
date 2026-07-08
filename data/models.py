"""Shared SQLAlchemy model primitives."""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models in the application."""

    # The skeleton intentionally keeps the ORM surface minimal until concrete
    # domain tables are introduced.
