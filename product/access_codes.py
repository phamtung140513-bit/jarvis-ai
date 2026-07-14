"""Access codes customers redeem with /activate (SaaS sales)."""

from __future__ import annotations

import secrets
import string
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import AccessCode, BotUser
from product.plans import get_plan


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def generate_code(prefix: str = "JV") -> str:
    alphabet = string.ascii_uppercase + string.digits
    body = "".join(secrets.choice(alphabet) for _ in range(10))
    return f"{prefix}-{body[:5]}-{body[5:]}"


async def create_access_code(
    session: AsyncSession,
    *,
    plan_id: str,
    days: int | None = None,
    max_uses: int = 1,
    note: str = "",
    created_by: int | None = None,
) -> AccessCode:
    plan = get_plan(plan_id)
    code = AccessCode(
        code=generate_code(),
        plan_id=plan.id,
        days=days if days is not None else plan.days,
        max_uses=max_uses,
        uses=0,
        note=note or None,
        created_by=created_by,
        active=True,
        created_at=_utcnow(),
    )
    session.add(code)
    await session.commit()
    await session.refresh(code)
    return code


async def redeem_access_code(
    session: AsyncSession,
    *,
    code_str: str,
    telegram_id: int,
    username: str | None,
    full_name: str | None,
) -> tuple[bool, str]:
    code_str = code_str.strip().upper()
    result = await session.execute(
        select(AccessCode).where(AccessCode.code == code_str)
    )
    row = result.scalar_one_or_none()
    if row is None or not row.active:
        return False, "Mã không hợp lệ hoặc đã tắt."
    if row.uses >= row.max_uses:
        return False, "Mã đã hết lượt sử dụng."

    plan = get_plan(row.plan_id)
    now = _utcnow()
    exp = now + timedelta(days=row.days)

    ures = await session.execute(
        select(BotUser).where(BotUser.telegram_id == telegram_id)
    )
    user = ures.scalar_one_or_none()
    if user is None:
        user = BotUser(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
            plan_id=plan.id,
            active=True,
            is_admin=False,
            expires_at=exp,
            created_at=now,
            updated_at=now,
        )
        session.add(user)
    else:
        user.plan_id = plan.id
        user.active = True
        user.username = username or user.username
        user.full_name = full_name or user.full_name
        # Extend from max(now, current expiry)
        base = user.expires_at if user.expires_at and user.expires_at > now else now
        if base.tzinfo is None:
            base = base.replace(tzinfo=timezone.utc)
        user.expires_at = base + timedelta(days=row.days) if user.expires_at and user.expires_at > now else exp
        # Simpler: always set from now + days for clean renewals
        user.expires_at = exp
        user.updated_at = now

    row.uses += 1
    if row.uses >= row.max_uses:
        row.active = False

    await session.commit()
    return (
        True,
        f"✅ Kích hoạt *{plan.name}* — {plan.daily_messages if plan.daily_messages >= 0 else '∞'} tin/ngày đến {exp.date().isoformat()}",
    )
