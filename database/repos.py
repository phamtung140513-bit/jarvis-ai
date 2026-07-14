"""Repository helpers: conversation messages + projects (Phase 2)."""

from __future__ import annotations

import logging
from typing import Sequence

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import ConversationMessage, Project, UserTeaching, utcnow

logger = logging.getLogger(__name__)


# ── Conversation ──────────────────────────────────────────


async def save_message(
    session: AsyncSession,
    user_id: int,
    role: str,
    content: str,
) -> ConversationMessage:
    row = ConversationMessage(user_id=user_id, role=role, content=content)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def load_recent_messages(
    session: AsyncSession,
    user_id: int,
    limit: int = 40,
) -> list[dict[str, str]]:
    """Load last N messages (oldest first) for chat context."""
    # Subquery approach: get latest ids then order ascending
    subq = (
        select(ConversationMessage.id)
        .where(ConversationMessage.user_id == user_id)
        .order_by(ConversationMessage.id.desc())
        .limit(limit)
        .subquery()
    )
    stmt = (
        select(ConversationMessage)
        .where(ConversationMessage.id.in_(select(subq.c.id)))
        .order_by(ConversationMessage.id.asc())
    )
    result = await session.execute(stmt)
    rows = result.scalars().all()
    return [{"role": r.role, "content": r.content} for r in rows]


async def count_messages(session: AsyncSession, user_id: int) -> int:
    stmt = select(func.count()).select_from(ConversationMessage).where(
        ConversationMessage.user_id == user_id
    )
    result = await session.execute(stmt)
    return int(result.scalar_one() or 0)


async def clear_messages(session: AsyncSession, user_id: int) -> int:
    stmt = delete(ConversationMessage).where(ConversationMessage.user_id == user_id)
    result = await session.execute(stmt)
    await session.commit()
    n = result.rowcount or 0
    logger.info("Cleared %d conversation rows for user=%s", n, user_id)
    return n


async def prune_old_messages(
    session: AsyncSession,
    user_id: int,
    keep: int = 200,
) -> int:
    """Keep only the newest `keep` messages per user (storage hygiene)."""
    total = await count_messages(session, user_id)
    if total <= keep:
        return 0
    excess = total - keep
    # Delete oldest excess rows
    oldest = (
        select(ConversationMessage.id)
        .where(ConversationMessage.user_id == user_id)
        .order_by(ConversationMessage.id.asc())
        .limit(excess)
    )
    result = await session.execute(
        delete(ConversationMessage).where(ConversationMessage.id.in_(oldest))
    )
    await session.commit()
    return result.rowcount or 0


# ── Projects ──────────────────────────────────────────────


async def create_project(
    session: AsyncSession,
    user_id: int,
    name: str,
    path: str = "",
    notes: str | None = None,
) -> Project:
    name = name.strip()[:128]
    path = (path or f"workspace/{user_id}/{name}").strip()[:512]
    proj = Project(user_id=user_id, name=name, path=path, notes=notes)
    session.add(proj)
    await session.commit()
    await session.refresh(proj)
    return proj


async def list_projects(
    session: AsyncSession,
    user_id: int,
    limit: int = 20,
) -> Sequence[Project]:
    stmt = (
        select(Project)
        .where(Project.user_id == user_id)
        .order_by(Project.id.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_project(
    session: AsyncSession,
    user_id: int,
    project_id: int,
) -> Project | None:
    stmt = select(Project).where(
        Project.id == project_id,
        Project.user_id == user_id,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_project_by_name(
    session: AsyncSession,
    user_id: int,
    name: str,
) -> Project | None:
    stmt = (
        select(Project)
        .where(Project.user_id == user_id, Project.name == name.strip())
        .order_by(Project.id.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def update_project_notes(
    session: AsyncSession,
    user_id: int,
    project_id: int,
    notes: str,
    append: bool = False,
) -> Project | None:
    proj = await get_project(session, user_id, project_id)
    if proj is None:
        return None
    if append and proj.notes:
        proj.notes = f"{proj.notes.rstrip()}\n\n{notes}"
    else:
        proj.notes = notes
    await session.commit()
    await session.refresh(proj)
    return proj


async def delete_project(
    session: AsyncSession,
    user_id: int,
    project_id: int,
) -> bool:
    proj = await get_project(session, user_id, project_id)
    if proj is None:
        return False
    await session.delete(proj)
    await session.commit()
    return True


async def set_active_project_note(
    session: AsyncSession,
    user_id: int,
    project_id: int,
    note_line: str,
) -> Project | None:
    """Append a short timestamped note line to project."""
    stamp = utcnow().strftime("%Y-%m-%d %H:%M")
    line = f"[{stamp}] {note_line.strip()}"
    return await update_project_notes(
        session, user_id, project_id, line, append=True
    )


# ── Teachings (user custom rules for AI) ──────────────────


MAX_TEACHINGS_PER_USER = 40
MAX_TEACHING_LEN = 800


async def add_teaching(
    session: AsyncSession,
    user_id: int,
    content: str,
    kind: str = "rule",
) -> UserTeaching:
    kind = (kind or "rule").lower().strip()
    if kind not in {"rule", "style", "fact"}:
        kind = "rule"
    content = content.strip()[:MAX_TEACHING_LEN]
    if not content:
        raise ValueError("empty teaching")

    # Cap per user
    total = await count_teachings(session, user_id)
    if total >= MAX_TEACHINGS_PER_USER:
        # Drop oldest
        oldest = (
            select(UserTeaching.id)
            .where(UserTeaching.user_id == user_id)
            .order_by(UserTeaching.id.asc())
            .limit(total - MAX_TEACHINGS_PER_USER + 1)
        )
        await session.execute(
            delete(UserTeaching).where(UserTeaching.id.in_(oldest))
        )

    row = UserTeaching(user_id=user_id, kind=kind, content=content, active=True)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def list_teachings(
    session: AsyncSession,
    user_id: int,
    *,
    active_only: bool = True,
) -> Sequence[UserTeaching]:
    stmt = select(UserTeaching).where(UserTeaching.user_id == user_id)
    if active_only:
        stmt = stmt.where(UserTeaching.active.is_(True))
    stmt = stmt.order_by(UserTeaching.id.asc())
    result = await session.execute(stmt)
    return result.scalars().all()


async def list_teachings_for_users(
    session: AsyncSession,
    user_ids: set[int] | frozenset[int] | list[int],
    *,
    active_only: bool = True,
) -> Sequence[UserTeaching]:
    """Load teachings belonging to any of the given user ids (e.g. all owners)."""
    ids = list(user_ids)
    if not ids:
        return []
    stmt = select(UserTeaching).where(UserTeaching.user_id.in_(ids))
    if active_only:
        stmt = stmt.where(UserTeaching.active.is_(True))
    stmt = stmt.order_by(UserTeaching.id.asc())
    result = await session.execute(stmt)
    return result.scalars().all()


async def count_teachings(session: AsyncSession, user_id: int) -> int:
    stmt = select(func.count()).select_from(UserTeaching).where(
        UserTeaching.user_id == user_id
    )
    result = await session.execute(stmt)
    return int(result.scalar_one() or 0)


async def count_teachings_for_users(
    session: AsyncSession,
    user_ids: set[int] | frozenset[int] | list[int],
) -> int:
    ids = list(user_ids)
    if not ids:
        return 0
    stmt = select(func.count()).select_from(UserTeaching).where(
        UserTeaching.user_id.in_(ids)
    )
    result = await session.execute(stmt)
    return int(result.scalar_one() or 0)


async def delete_teaching(
    session: AsyncSession,
    user_id: int,
    teaching_id: int,
) -> bool:
    stmt = select(UserTeaching).where(
        UserTeaching.id == teaching_id,
        UserTeaching.user_id == user_id,
    )
    result = await session.execute(stmt)
    row = result.scalar_one_or_none()
    if row is None:
        return False
    await session.delete(row)
    await session.commit()
    return True


async def clear_teachings(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(
        delete(UserTeaching).where(UserTeaching.user_id == user_id)
    )
    await session.commit()
    return result.rowcount or 0
