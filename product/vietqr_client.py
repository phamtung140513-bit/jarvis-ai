"""Client gọi vietqr-pay server (tạo đơn + status)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from config import Settings

logger = logging.getLogger(__name__)


@dataclass
class PayOrder:
    order_id: str
    amount: int
    plan: str
    status: str
    content: str
    qr_image_url: str | None
    pay_page: str | None
    bank_code: str
    bank_account: str
    bank_name: str
    raw: dict[str, Any]


def vietqr_pay_enabled(settings: Settings) -> bool:
    return bool((settings.vietqr_pay_url or "").strip())


def make_user_transfer_content(telegram_id: int) -> str:
    """Nội dung CK riêng mỗi người: AI + telegram_id + random (không dấu)."""
    import secrets
    import string

    tid = "".join(c for c in str(telegram_id) if c.isdigit())[:12]
    r = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(3))
    return f"AI{tid}{r}"[:25]


async def create_pay_order(
    settings: Settings,
    *,
    amount: int,
    plan: str,
    telegram_id: int,
    note: str = "",
    content: str | None = None,
) -> PayOrder:
    base = settings.vietqr_pay_url.rstrip("/")
    transfer = (content or make_user_transfer_content(telegram_id)).strip()
    payload = {
        "amount": int(amount),
        "plan": plan,
        "telegramId": str(telegram_id),
        "note": note or f"tg:{telegram_id}:{plan}",
        "content": transfer,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(f"{base}/api/orders", json=payload)
        data = res.json() if res.content else {}
        if res.status_code >= 400:
            raise RuntimeError(data.get("error") or f"HTTP {res.status_code}")
    return _parse_order(data)


async def get_order_status(settings: Settings, order_id: str) -> dict[str, Any]:
    base = settings.vietqr_pay_url.rstrip("/")
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(f"{base}/api/orders/{order_id}/status")
        data = res.json() if res.content else {}
        if res.status_code >= 400:
            raise RuntimeError(data.get("error") or f"HTTP {res.status_code}")
        return data


async def health_check(settings: Settings) -> dict[str, Any]:
    base = settings.vietqr_pay_url.rstrip("/")
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.get(f"{base}/api/health")
        res.raise_for_status()
        return res.json()


def _parse_order(data: dict[str, Any]) -> PayOrder:
    bank = data.get("bank") or {}
    return PayOrder(
        order_id=str(data.get("orderId") or ""),
        amount=int(data.get("amount") or 0),
        plan=str(data.get("plan") or ""),
        status=str(data.get("status") or "pending"),
        content=str(data.get("content") or data.get("orderId") or ""),
        qr_image_url=data.get("qrImageUrl"),
        pay_page=data.get("payPage"),
        bank_code=str(bank.get("code") or ""),
        bank_account=str(bank.get("account") or ""),
        bank_name=str(bank.get("name") or ""),
        raw=data,
    )
