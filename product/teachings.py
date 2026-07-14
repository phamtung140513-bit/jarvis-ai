"""Owner-only teachings — global AI rules for every chat."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import UserTeaching
from database.repos import (
    add_teaching,
    clear_teachings,
    count_teachings,
    count_teachings_for_users,
    delete_teaching,
    list_teachings,
    list_teachings_for_users,
)

KIND_LABEL = {
    "rule": "📌 Luật",
    "style": "🎨 Style",
    "fact": "📝 Fact",
}


async def teach(
    session: AsyncSession,
    user_id: int,
    content: str,
    kind: str = "rule",
) -> UserTeaching:
    return await add_teaching(session, user_id, content, kind=kind)


async def teachings_for(
    session: AsyncSession,
    user_id: int,
) -> list[UserTeaching]:
    return list(await list_teachings(session, user_id, active_only=True))


async def owner_teachings(
    session: AsyncSession,
    owner_ids: set[int] | frozenset[int],
) -> list[UserTeaching]:
    """Global rules: all teachings created by bot owners."""
    return list(await list_teachings_for_users(session, owner_ids, active_only=True))


async def remove_teaching(
    session: AsyncSession,
    user_id: int,
    teaching_id: int,
) -> bool:
    return await delete_teaching(session, user_id, teaching_id)


async def wipe_teachings(session: AsyncSession, user_id: int) -> int:
    return await clear_teachings(session, user_id)


async def teaching_count(session: AsyncSession, user_id: int) -> int:
    return await count_teachings(session, user_id)


async def owner_teaching_count(
    session: AsyncSession,
    owner_ids: set[int] | frozenset[int],
) -> int:
    return await count_teachings_for_users(session, owner_ids)


def format_teachings_list(rows: list[UserTeaching]) -> str:
    if not rows:
        return (
            "Chưa có luật nào.\n\n"
            "Chỉ *chủ bot* được thêm. Luật áp dụng cho *mọi* khách chat.\n\n"
            "Ví dụ:\n"
            "`/teach luôn trả lời tiếng Việt, ngắn`\n"
            "`/teach style tư vấn thân thiện, chốt nhẹ`\n"
            "`/teach fact Basic 49k / Pro 99k / Business 199k`\n"
            "`/teach list` · `/teach del ID` · `/teach clear`"
        )
    lines = [f"📚 *Luật chủ bot* ({len(rows)}) — áp dụng mọi chat:"]
    for t in rows:
        label = KIND_LABEL.get(t.kind, t.kind)
        preview = t.content.replace("\n", " ")
        if len(preview) > 120:
            preview = preview[:120] + "…"
        lines.append(f"• `#{t.id}` {label}: {preview}")
    lines.append(
        "\nThêm: `/teach …` · Xóa: `/teach del ID` · Xóa hết: `/teach clear`"
    )
    return "\n".join(lines)


def format_teachings_for_prompt(rows: list[UserTeaching]) -> str | None:
    """Build system-prompt extra that the model must obey."""
    if not rows:
        return None
    rules = [t for t in rows if t.kind == "rule"]
    styles = [t for t in rows if t.kind == "style"]
    facts = [t for t in rows if t.kind == "fact"]
    other = [t for t in rows if t.kind not in {"rule", "style", "fact"}]

    parts: list[str] = [
        "QUAN TRỌNG — Chủ bot (owner) đã đặt các quy tắc sau cho toàn hệ thống. "
        "BẮT BUỘC tuân thủ với mọi người dùng (ưu tiên cao hơn phong cách mặc định):"
    ]
    if rules or other:
        parts.append("\n## Luật bắt buộc (chủ bot)")
        for t in rules + other:
            parts.append(f"- {t.content.strip()}")
    if styles:
        parts.append("\n## Phong cách / giọng điệu")
        for t in styles:
            parts.append(f"- {t.content.strip()}")
    if facts:
        parts.append("\n## Sự thật / thông tin shop / sản phẩm")
        for t in facts:
            parts.append(f"- {t.content.strip()}")
    parts.append(
        "\nNếu mâu thuẫn nhẹ với mặc định, ưu tiên luật chủ bot. "
        "Không nhắc lại danh sách luật trừ khi được hỏi."
    )
    return "\n".join(parts)
