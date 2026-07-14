"""Fulfill paid orders from vietqr-pay: activate plan + notify Telegram."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from config import ROOT_DIR, Settings
from database.sqlite import get_db
from product.access_codes import create_access_code
from product.plans import get_plan
from product.users import set_user_plan

logger = logging.getLogger(__name__)

_FULFILLED_FILE = ROOT_DIR / "cache" / "fulfilled_orders.txt"
_fulfilled: set[str] = set()
_loaded = False


def _load_fulfilled() -> None:
    global _loaded
    if _loaded:
        return
    _loaded = True
    try:
        if _FULFILLED_FILE.is_file():
            for line in _FULFILLED_FILE.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    _fulfilled.add(line)
    except OSError:
        logger.exception("Cannot load fulfilled orders file")


def _remember(order_id: str) -> None:
    _fulfilled.add(order_id)
    try:
        _FULFILLED_FILE.parent.mkdir(parents=True, exist_ok=True)
        with _FULFILLED_FILE.open("a", encoding="utf-8") as f:
            f.write(order_id + "\n")
    except OSError:
        logger.exception("Cannot append fulfilled order")


def already_fulfilled(order_id: str) -> bool:
    _load_fulfilled()
    return order_id in _fulfilled


async def fulfill_paid_order(
    bot: Bot,
    settings: Settings,
    *,
    order_id: str,
    plan_id: str,
    amount: int,
    telegram_id: int | None,
    note: str = "",
) -> dict[str, Any]:
    """
    Activate customer plan after payment.
    Idempotent by order_id.
    """
    order_id = (order_id or "").strip()
    if not order_id:
        return {"ok": False, "error": "missing_order_id"}

    if already_fulfilled(order_id):
        logger.info("Order %s already fulfilled — skip", order_id)
        return {"ok": True, "duplicate": True, "orderId": order_id}

    plan_id = (plan_id or "basic").strip().lower()
    if plan_id in ("", "owner"):
        plan_id = "basic"
    plan = get_plan(plan_id)

    if not telegram_id:
        logger.warning("Paid order %s has no telegramId", order_id)
        return {"ok": False, "error": "missing_telegram_id", "orderId": order_id}

    db = get_db()
    async with db.session() as session:
        code = await create_access_code(
            session,
            plan_id=plan.id,
            days=plan.days,
            max_uses=1,
            note=f"auto:{order_id}" + (f" {note}" if note else ""),
            created_by=None,
        )
        user = await set_user_plan(
            session,
            int(telegram_id),
            plan.id,
            plan.days,
        )

    _remember(order_id)

    exp = user.expires_at.date().isoformat() if user.expires_at else "∞"
    limit = "∞" if plan.daily_messages < 0 else str(plan.daily_messages)

    customer_text = (
        f"✅ *Thanh toán thành công!*\n\n"
        f"Mã đơn: `{order_id}`\n"
        f"Số tiền: *{amount:,}* {settings.currency}\n"
        f"Gói: *{plan.name}* — {limit} tin/ngày\n"
        f"Hết hạn: `{exp}`\n\n"
        f"Mã kích hoạt (đã auto-active):\n`{code.code}`\n\n"
        f"Bạn có thể chat ngay. Gõ /account hoặc /help."
    )

    admin_text = (
        f"💰 *Paid*\n"
        f"Order: `{order_id}`\n"
        f"User: `{telegram_id}`\n"
        f"Plan: *{plan.name}* ({plan.id})\n"
        f"Amount: {amount:,} {settings.currency}\n"
        f"Code: `{code.code}`"
    )

    try:
        await bot.send_message(
            int(telegram_id), customer_text, parse_mode="Markdown"
        )
    except Exception:
        logger.exception("Cannot message customer %s", telegram_id)

    for admin_id in settings.owner_ids:
        if admin_id == int(telegram_id):
            continue
        try:
            await bot.send_message(admin_id, admin_text, parse_mode="Markdown")
        except Exception:
            logger.exception("Cannot message admin %s", admin_id)

    logger.info(
        "Fulfilled order=%s user=%s plan=%s code=%s",
        order_id,
        telegram_id,
        plan.id,
        code.code,
    )
    return {
        "ok": True,
        "orderId": order_id,
        "plan": plan.id,
        "telegramId": int(telegram_id),
        "code": code.code,
        "expires": exp,
    }
