"""Async SQLite helpers (SQLAlchemy 2.0)."""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import Settings, get_settings
from database.models import Base

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.engine: AsyncEngine = create_async_engine(
            self.settings.database_url,
            echo=False,
        )
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def init(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized: %s", self.settings.database_url)

    async def close(self) -> None:
        await self.engine.dispose()

    def session(self) -> AsyncSession:
        return self.session_factory()


_db: Optional[Database] = None


def get_db() -> Database:
    if _db is None:
        raise RuntimeError("Database not initialized. Call set_db() first.")
    return _db


def set_db(db: Database) -> None:
    global _db
    _db = db
