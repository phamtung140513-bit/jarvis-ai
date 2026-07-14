"""User access, quotas, admin helpers."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import Settings
from database.models import BotUser, UsageCounter
from product.plans import get_plan


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


async def ensure_owner_users(session: AsyncSession, settings: Settings) -> None:
    """Seed owner/admin accounts from env on startup."""
    now = _utcnow()
    for tid in settings.owner_ids | settings.allowed_ids:
        res = await session.execute(select(BotUser).where(BotUser.telegram_id == tid))
        user = res.scalar_one_or_none()
        if user is None:
            session.add(
                BotUser(
                    telegram_id=tid,
                    plan_id="owner",
                    active=True,
                    is_admin=tid in settings.owner_ids or tid in settings.allowed_ids,
                    expires_at=None,
                    created_at=now,
                    updated_at=now,
                )
            )
        else:
            user.active = True
            user.is_admin = True
            user.plan_id = "owner"
            user.expires_at = None
            user.updated_at = now
    await session.commit()


async def get_user(session: AsyncSession, telegram_id: int) -> Optional[BotUser]:
    res = await session.execute(
        select(BotUser).where(BotUser.telegram_id == telegram_id)
    )
    return res.scalar_one_or_none()


async def is_allowed(session: AsyncSession, settings: Settings, telegram_id: int) -> tuple[bool, str]:
    if telegram_id in settings.owner_ids or telegram_id in settings.allowed_ids:
        return True, "owner"

    user = await get_user(session, telegram_id)
    if user is None:
        return False, "not_registered"
    if not user.active:
        return False, "disabled"
    exp = _as_utc(user.expires_at)
    if exp is not None and exp < _utcnow():
        return False, "expired"
    return True, "ok"


async def is_admin(session: AsyncSession, settings: Settings, telegram_id: int) -> bool:
    if telegram_id in settings.owner_ids or telegram_id in settings.allowed_ids:
        return True
    user = await get_user(session, telegram_id)
    return bool(user and user.is_admin and user.active)


async def get_daily_usage(session: AsyncSession, telegram_id: int) -> int:
    today = date.today().isoformat()
    res = await session.execute(
        select(UsageCounter).where(
            UsageCounter.telegram_id == telegram_id,
            UsageCounter.day == today,
        )
    )
    row = res.scalar_one_or_none()
    return row.count if row else 0


async def check_quota(
    session: AsyncSession, settings: Settings, telegram_id: int
) -> tuple[bool, str, int, int]:
    """Returns (ok, message, used, limit). limit -1 = unlimited."""
    if telegram_id in settings.owner_ids or telegram_id in settings.allowed_ids:
        used = await get_daily_usage(session, telegram_id)
        return True, "ok", used, -1

    user = await get_user(session, telegram_id)
    if user is None:
        return False, "Chưa kích hoạt. Gõ /buy hoặc /activate MÃ", 0, 0
    plan = get_plan(user.plan_id)
    used = await get_daily_usage(session, telegram_id)
    if plan.daily_messages < 0:
        return True, "ok", used, -1
    if used >= plan.daily_messages:
        return (
            False,
            f"Hết quota hôm nay ({used}/{plan.daily_messages}). Nâng gói: /buy",
            used,
            plan.daily_messages,
        )
    return True, "ok", used, plan.daily_messages


async def increment_usage(session: AsyncSession, telegram_id: int) -> int:
    today = date.today().isoformat()
    res = await session.execute(
        select(UsageCounter).where(
            UsageCounter.telegram_id == telegram_id,
            UsageCounter.day == today,
        )
    )
    row = res.scalar_one_or_none()
    if row is None:
        row = UsageCounter(telegram_id=telegram_id, day=today, count=1)
        session.add(row)
    else:
        row.count += 1
    await session.commit()
    return row.count


async def list_users(session: AsyncSession, limit: int = 30) -> list[BotUser]:
    res = await session.execute(
        select(BotUser).order_by(BotUser.created_at.desc()).limit(limit)
    )
    return list(res.scalars().all())


async def set_user_plan(
    session: AsyncSession,
    telegram_id: int,
    plan_id: str,
    days: int | None = None,
    *,
    username: str | None = None,
) -> BotUser:
    plan = get_plan(plan_id)
    now = _utcnow()
    user = await get_user(session, telegram_id)
    exp = None if plan.id == "owner" else now + timedelta(
        days=days if days is not None else plan.days
    )
    if user is None:
        user = BotUser(
            telegram_id=telegram_id,
            username=username,
            plan_id=plan.id,
            active=True,
            is_admin=plan.id == "owner",
            expires_at=exp,
            created_at=now,
            updated_at=now,
        )
        session.add(user)
    else:
        user.plan_id = plan.id
        user.active = True
        user.expires_at = exp
        user.is_admin = user.is_admin or plan.id == "owner"
        user.updated_at = now
        if username:
            user.username = username
    await session.commit()
    await session.refresh(user)
    return user


async def deactivate_user(session: AsyncSession, telegram_id: int) -> bool:
    user = await get_user(session, telegram_id)
    if user is None:
        return False
    user.active = False
    user.updated_at = _utcnow()
    await session.commit()
    return True


async def stats_summary(session: AsyncSession) -> dict:
    users = (await session.execute(select(func.count()).select_from(BotUser))).scalar() or 0
    active = (
        await session.execute(
            select(func.count()).select_from(BotUser).where(BotUser.active.is_(True))
        )
    ).scalar() or 0
    today = date.today().isoformat()
    msgs = (
        await session.execute(
            select(func.coalesce(func.sum(UsageCounter.count), 0)).where(
                UsageCounter.day == today
            )
        )
    ).scalar() or 0
    return {"users": users, "active": active, "messages_today": int(msgs)}
