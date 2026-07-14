"""Inline / reply keyboards."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def main_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="💬 Chat")
    kb.button(text="🧠 Memory")
    kb.button(text="📋 Plan")
    kb.button(text="🔧 Build")
    kb.button(text="📂 Projects")
    kb.button(text="💎 Mua gói")
    kb.button(text="ℹ️ Help")
    kb.adjust(2, 2, 2, 1)
    return kb.as_markup(resize_keyboard=True)


def pricing_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="💎 Mua gói")
    kb.button(text="ℹ️ Help")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)


def _fmt_k(amount: int) -> str:
    if amount >= 1000:
        return f"{amount // 1000}k"
    return str(amount)


def plan_qr_keyboard() -> InlineKeyboardMarkup:
    """Inline buttons: tạo đơn + QR theo gói (vietqr-pay)."""
    from product.plans import PLANS

    kb = InlineKeyboardBuilder()
    basic = PLANS["basic"].price_vnd
    pro = PLANS["pro"].price_vnd
    biz = PLANS["business"].price_vnd
    kb.row(
        InlineKeyboardButton(
            text=f"Mua Basic {_fmt_k(basic)}", callback_data="qr:basic"
        ),
        InlineKeyboardButton(text=f"Mua Pro {_fmt_k(pro)}", callback_data="qr:pro"),
    )
    kb.row(
        InlineKeyboardButton(
            text=f"Mua Business {_fmt_k(biz)}", callback_data="qr:business"
        ),
    )
    return kb.as_markup()


def payment_order_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """Nút dưới ảnh QR — giống bot nạp tiền (bill + menu)."""
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(
            text="📷 Gửi ảnh bill xác nhận",
            callback_data=f"bill:{order_id[:20]}",
        )
    )
    kb.row(
        InlineKeyboardButton(text="🏠 Menu chính", callback_data="menu:main")
    )
    return kb.as_markup()


def confirm_clear_memory() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(text="✅ Xóa memory", callback_data="memory:clear"),
        InlineKeyboardButton(text="❌ Hủy", callback_data="memory:cancel"),
    )
    return kb.as_markup()


def agent_actions() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="📋 Plan", callback_data="agent:plan"),
        InlineKeyboardButton(text="💻 Code", callback_data="agent:code"),
    )
    kb.row(
        InlineKeyboardButton(text="🔎 Review", callback_data="agent:review"),
        InlineKeyboardButton(text="🐛 Debug", callback_data="agent:debug"),
    )
    return kb.as_markup()
