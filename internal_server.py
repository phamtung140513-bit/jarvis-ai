"""HTTP webhook server: vietqr-pay → TungDevAI fulfill."""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import web
from aiogram import Bot

from config import Settings
from product.fulfillment import fulfill_paid_order

logger = logging.getLogger(__name__)


def _check_secret(request: web.Request, settings: Settings) -> bool:
    expected = (settings.payment_webhook_secret or "").strip()
    if not expected:
        # Dev-friendly: if no secret set, only allow localhost
        peer = request.remote or ""
        return peer in ("127.0.0.1", "::1", "localhost")
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:].strip() == expected
    return request.headers.get("X-Webhook-Secret", "").strip() == expected


def create_app(bot: Bot, settings: Settings) -> web.Application:
    app = web.Application()

    async def health(_request: web.Request) -> web.Response:
        return web.json_response({"ok": True, "service": "tungdevai-fulfill"})

    async def orders_paid(request: web.Request) -> web.Response:
        if not _check_secret(request, settings):
            return web.json_response({"ok": False, "error": "unauthorized"}, status=401)

        try:
            body: dict[str, Any] = await request.json()
        except Exception:
            return web.json_response({"ok": False, "error": "invalid_json"}, status=400)

        order_id = str(body.get("orderId") or body.get("order_id") or "").strip()
        plan = str(body.get("plan") or "basic").strip()
        amount = int(body.get("amount") or 0)
        note = str(body.get("note") or "")
        raw_tg = body.get("telegramId") or body.get("telegram_id")
        telegram_id: int | None = None
        if raw_tg is not None and str(raw_tg).strip():
            try:
                telegram_id = int(str(raw_tg).strip())
            except ValueError:
                return web.json_response(
                    {"ok": False, "error": "invalid_telegram_id"}, status=400
                )

        raw_wu = body.get("webUserId") or body.get("web_user_id")
        web_user_id: int | None = None
        if raw_wu is not None and str(raw_wu).strip():
            try:
                web_user_id = int(str(raw_wu).strip())
            except ValueError:
                return web.json_response(
                    {"ok": False, "error": "invalid_web_user_id"}, status=400
                )
        web_email = str(body.get("webEmail") or body.get("web_email") or "").strip() or None

        logger.info(
            "Webhook paid order=%s plan=%s amount=%s tg=%s web=%s/%s",
            order_id,
            plan,
            amount,
            telegram_id,
            web_user_id,
            web_email,
        )

        result = await fulfill_paid_order(
            bot,
            settings,
            order_id=order_id,
            plan_id=plan,
            amount=amount,
            telegram_id=telegram_id,
            web_user_id=web_user_id,
            web_email=web_email,
            note=note,
        )
        status = 200 if result.get("ok") else 400
        return web.json_response(result, status=status)

    app.router.add_get("/internal/health", health)
    app.router.add_post("/internal/orders/paid", orders_paid)
    return app


async def start_internal_server(
    bot: Bot, settings: Settings
) -> web.AppRunner | None:
    if not settings.payment_webhook_enabled:
        logger.info("Payment webhook server disabled")
        return None

    host = settings.payment_webhook_host
    port = settings.payment_webhook_port
    app = create_app(bot, settings)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logger.info("Payment webhook listening on http://%s:%s", host, port)
    return runner
