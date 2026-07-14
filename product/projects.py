"""User project notes — thin wrapper over database.repos (Phase 2)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Project
from database.repos import (
    create_project,
    delete_project,
    get_project,
    get_project_by_name,
    list_projects,
    set_active_project_note,
    update_project_notes,
)


async def new_project(
    session: AsyncSession,
    user_id: int,
    name: str,
    notes: str | None = None,
) -> Project:
    return await create_project(
        session,
        user_id=user_id,
        name=name,
        path=f"workspace/{user_id}/{name.strip()}",
        notes=notes,
    )


async def user_projects(
    session: AsyncSession,
    user_id: int,
    limit: int = 20,
) -> list[Project]:
    rows = await list_projects(session, user_id, limit=limit)
    return list(rows)


async def project_detail(
    session: AsyncSession,
    user_id: int,
    project_id: int,
) -> Project | None:
    return await get_project(session, user_id, project_id)


async def find_project(
    session: AsyncSession,
    user_id: int,
    name: str,
) -> Project | None:
    return await get_project_by_name(session, user_id, name)


async def write_notes(
    session: AsyncSession,
    user_id: int,
    project_id: int,
    notes: str,
    *,
    append: bool = False,
) -> Project | None:
    return await update_project_notes(
        session, user_id, project_id, notes, append=append
    )


async def add_note_line(
    session: AsyncSession,
    user_id: int,
    project_id: int,
    line: str,
) -> Project | None:
    return await set_active_project_note(session, user_id, project_id, line)


async def remove_project(
    session: AsyncSession,
    user_id: int,
    project_id: int,
) -> bool:
    return await delete_project(session, user_id, project_id)


def format_project(proj: Project, *, full_notes: bool = False) -> str:
    notes = proj.notes or "_(chưa có notes)_"
    if not full_notes and len(notes) > 400:
        notes = notes[:400] + "…"
    return (
        f"📁 *#{proj.id}* `{proj.name}`\n"
        f"Path: `{proj.path}`\n"
        f"Notes:\n{notes}"
    )


def format_project_list(projects: list[Project]) -> str:
    if not projects:
        return "Chưa có project. Tạo: `/project new tên-project`"
    lines = ["📂 *Projects của bạn:*"]
    for p in projects:
        preview = (p.notes or "")[:40].replace("\n", " ")
        lines.append(f"• `#{p.id}` *{p.name}* — {preview or '—'}")
    lines.append(
        "\nXem: `/project show ID` · Note: `/project note ID nội dung` · "
        "Xóa: `/project del ID`"
    )
    return "\n".join(lines)
