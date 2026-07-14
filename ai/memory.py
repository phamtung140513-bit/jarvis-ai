"""Hybrid RAM + SQLite conversation memory (Phase 2)."""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from typing import Deque

from sqlalchemy.ext.asyncio import AsyncSession

from config import Settings, get_settings
from database.repos import (
    clear_messages,
    count_messages,
    load_recent_messages,
    prune_old_messages,
    save_message,
)

logger = logging.getLogger(__name__)


class ConversationMemory:
    """Per-user rolling message history for Grok chat.

    - Hot path: in-memory deque (fast).
    - Persist: optional AsyncSession → SQLite `conversation_messages`.
    - Hydrate: load from DB once per user when RAM is empty.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._max = self.settings.max_history_messages
        self._store: dict[int, Deque[dict[str, str]]] = defaultdict(
            lambda: deque(maxlen=self._max)
        )
        self._hydrated: set[int] = set()

    def get_messages(self, user_id: int) -> list[dict[str, str]]:
        return list(self._store[user_id])

    def add(self, user_id: int, role: str, content: str) -> None:
        """RAM-only append (use add_persist for DB)."""
        if role not in {"user", "assistant", "system"}:
            raise ValueError(f"Invalid role: {role}")
        self._store[user_id].append({"role": role, "content": content})
        logger.debug("memory user=%s role=%s len=%d", user_id, role, len(content))

    async def add_persist(
        self,
        session: AsyncSession,
        user_id: int,
        role: str,
        content: str,
    ) -> None:
        """Append to RAM + SQLite."""
        self.add(user_id, role, content)
        try:
            await save_message(session, user_id, role, content)
            # Occasional prune so DB does not grow unbounded
            if len(self._store[user_id]) == self._max:
                await prune_old_messages(session, user_id, keep=self._max * 3)
        except Exception:
            logger.exception("Failed to persist message user=%s", user_id)

    async def ensure_hydrated(self, session: AsyncSession, user_id: int) -> None:
        """Load history from DB into RAM if not already loaded this process."""
        if user_id in self._hydrated:
            return
        if self._store[user_id]:
            self._hydrated.add(user_id)
            return
        try:
            rows = await load_recent_messages(
                session, user_id, limit=self._max
            )
            if rows:
                dq = self._store[user_id]
                for m in rows:
                    if m["role"] in {"user", "assistant", "system"}:
                        dq.append(m)
                logger.info(
                    "Hydrated memory user=%s messages=%d", user_id, len(rows)
                )
        except Exception:
            logger.exception("Hydrate failed user=%s", user_id)
        self._hydrated.add(user_id)

    def clear(self, user_id: int) -> None:
        """Clear RAM only."""
        self._store.pop(user_id, None)
        self._hydrated.discard(user_id)
        logger.info("Cleared RAM memory for user=%s", user_id)

    async def clear_persist(self, session: AsyncSession, user_id: int) -> int:
        """Clear RAM + SQLite history."""
        self.clear(user_id)
        try:
            return await clear_messages(session, user_id)
        except Exception:
            logger.exception("Failed to clear DB memory user=%s", user_id)
            return 0

    def snapshot(self, user_id: int) -> int:
        """Return number of messages stored in RAM for user."""
        return len(self._store.get(user_id, ()))

    async def snapshot_db(self, session: AsyncSession, user_id: int) -> int:
        try:
            return await count_messages(session, user_id)
        except Exception:
            logger.exception("count_messages failed user=%s", user_id)
            return 0
