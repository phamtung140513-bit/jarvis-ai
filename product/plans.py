"""Subscription plans for selling bot access (SaaS)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Plan:
    id: str
    name: str
    daily_messages: int  # -1 = unlimited
    price_vnd: int
    description: str
    days: int = 30  # default subscription length when sold


PLANS: dict[str, Plan] = {
    "trial": Plan(
        id="trial",
        name="Trial",
        daily_messages=20,
        price_vnd=0,
        description="Dùng thử 20 tin/ngày",
        days=3,
    ),
    "basic": Plan(
        id="basic",
        name="Basic",
        daily_messages=100,
        price_vnd=49_000,
        description="100 tin nhắn/ngày — cá nhân",
        days=30,
    ),
    "pro": Plan(
        id="pro",
        name="Pro",
        daily_messages=500,
        price_vnd=99_000,
        description="500 tin/ngày — freelancer / team nhỏ",
        days=30,
    ),
    "business": Plan(
        id="business",
        name="Business",
        daily_messages=-1,
        price_vnd=199_000,
        description="Không giới hạn tin — agency / shop",
        days=30,
    ),
    "owner": Plan(
        id="owner",
        name="Owner",
        daily_messages=-1,
        price_vnd=0,
        description="Chủ bot — full quyền",
        days=36500,
    ),
}


def get_plan(plan_id: str) -> Plan:
    return PLANS.get(plan_id, PLANS["trial"])


def format_price_list(currency_note: str = "VND") -> str:
    lines = ["📦 *Bảng giá gói:*", ""]
    for p in PLANS.values():
        if p.id == "owner":
            continue
        limit = "∞" if p.daily_messages < 0 else str(p.daily_messages)
        price = "Miễn phí" if p.price_vnd <= 0 else f"{p.price_vnd:,} {currency_note}"
        lines.append(
            f"• *{p.name}* (`{p.id}`) — {price}/{p.days} ngày\n"
            f"  {limit} tin/ngày — {p.description}"
        )
    lines.append("")
    lines.append("Sau khi thanh toán, admin gửi mã → bạn gõ `/activate MÃ`")
    return "\n".join(lines)
