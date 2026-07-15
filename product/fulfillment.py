"""Fulfill paid orders from vietqr-pay: activate plan + notify Telegram/web."""

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
from product.web_plans import set_web_user_plan, user_public

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
    telegram_id: int | None = None,
    web_user_id: int | None = None,
    web_email: str | None = None,
    note: str = "",
) -> dict[str, Any]:
    """
    Activate customer plan after payment (Telegram and/or Web).
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

    has_tg = telegram_id is not None and int(telegram_id) > 0
    has_web = bool(
        (web_user_id is not None and int(web_user_id) > 0)
        or (web_email and str(web_email).strip())
    )
    if not has_tg and not has_web:
        logger.warning("Paid order %s has no telegramId/web user", order_id)
        return {
            "ok": False,
            "error": "missing_customer",
            "orderId": order_id,
            "hint": "Cần telegramId hoặc webEmail/webUserId",
        }

    db = get_db()
    code_str = ""
    exp = "∞"
    web_user_out: dict[str, Any] | None = None
    tg_user_out: dict[str, Any] | None = None

    async with db.session() as session:
        code = await create_access_code(
            session,
            plan_id=plan.id,
            days=plan.days,
            max_uses=2 if (has_tg and has_web) else 1,
            note=f"auto:{order_id}" + (f" {note}" if note else ""),
            created_by=None,
        )
        code_str = code.code

        if has_tg:
            user = await set_user_plan(
                session,
                int(telegram_id),  # type: ignore[arg-type]
                plan.id,
                plan.days,
            )
            exp = user.expires_at.date().isoformat() if user.expires_at else "∞"
            tg_user_out = {
                "telegram_id": int(telegram_id),  # type: ignore[arg-type]
                "plan_id": user.plan_id,
                "expires": exp,
            }

        if has_web:
            try:
                wuser = await set_web_user_plan(
                    session,
                    email=(web_email or "").strip().lower() or None,
                    user_id=int(web_user_id) if web_user_id else None,
                    plan_id=plan.id,
                    days=plan.days,
                )
                web_user_out = user_public(wuser)
                if not exp or exp == "∞":
                    exp = (
                        wuser.plan_expires_at.date().isoformat()
                        if wuser.plan_expires_at
                        else "∞"
                    )
            except ValueError as exc:
                logger.warning("Web fulfill failed order=%s: %s", order_id, exc)
                if not has_tg:
                    return {
                        "ok": False,
                        "error": "web_user_not_found",
                        "detail": str(exc),
                        "orderId": order_id,
                    }

    _remember(order_id)

    limit = "∞" if plan.daily_messages < 0 else str(plan.daily_messages)

    customer_text = (
        f"✅ *Thanh toán thành công!*\n\n"
        f"Mã đơn: `{order_id}`\n"
        f"Số tiền: *{amount:,}* {settings.currency}\n"
        f"Gói: *{plan.name}* — {limit} tin/ngày\n"
        f"Hết hạn: `{exp}`\n\n"
        f"Mã kích hoạt (đã auto-active):\n`{code_str}`\n\n"
        f"• Telegram: chat ngay — /account\n"
        f"• Web: đăng nhập lại → gói hiện trên avatar\n"
        f"  (hoặc gõ `/activate {code_str}` trong web chat)"
    )

    admin_text = (
        f"💰 *Paid (autobank)*\n"
        f"Order: `{order_id}`\n"
        f"TG: `{telegram_id or '-'}`\n"
        f"Web: `{web_email or web_user_id or '-'}`\n"
        f"Plan: *{plan.name}* ({plan.id})\n"
        f"Amount: {amount:,} {settings.currency}\n"
        f"Code: `{code_str}`"
    )

    if has_tg:
        try:
            await bot.send_message(
                int(telegram_id), customer_text, parse_mode="Markdown"  # type: ignore[arg-type]
            )
        except Exception:
            logger.exception("Cannot message customer %s", telegram_id)

    for admin_id in settings.owner_ids:
        if has_tg and admin_id == int(telegram_id):  # type: ignore[arg-type]
            continue
        try:
            await bot.send_message(admin_id, admin_text, parse_mode="Markdown")
        except Exception:
            logger.exception("Cannot message admin %s", admin_id)

    logger.info(
        "Fulfilled order=%s tg=%s web=%s plan=%s code=%s",
        order_id,
        telegram_id,
        web_email or web_user_id,
        plan.id,
        code_str,
    )
    return {
        "ok": True,
        "orderId": order_id,
        "plan": plan.id,
        "telegramId": int(telegram_id) if has_tg else None,
        "webUser": web_user_out,
        "telegramUser": tg_user_out,
        "code": code_str,
        "expires": exp,
        "message": f"Đã kích hoạt gói {plan.name}",
    }
