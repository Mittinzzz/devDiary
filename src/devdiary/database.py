"""Database engine and session management."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from devdiary.config import Config, DEFAULT_CONFIG_DIR
from devdiary.models import Base


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine(db_url: str | None = None) -> AsyncEngine:
    """Get or create the async database engine."""
    global _engine
    if _engine is None:
        if db_url is None:
            config = Config.load()
            db_url = config.db_url
        # Ensure the directory exists for SQLite
        if "sqlite" in db_url:
            db_path = db_url.split("///")[-1]
            if db_path:
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        _engine = create_async_engine(
            db_url,
            echo=False,
            future=True,
        )
    return _engine


def get_session_factory(engine: AsyncEngine | None = None) -> async_sessionmaker[AsyncSession]:
    """Get or create the session factory."""
    global _session_factory
    if _session_factory is None:
        if engine is None:
            engine = get_engine()
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session as a context manager."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db(db_url: str | None = None) -> None:
    """Initialize the database, creating all tables."""
    engine = get_engine(db_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close the database engine."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None


def reset_engine() -> None:
    """Reset the engine and session factory (for testing)."""
    global _engine, _session_factory
    _engine = None
    _session_factory = None
