"""Bank QR helpers — local image or VietQR dynamic URL."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from config import ROOT_DIR, Settings

# Common Vietnam bank BIN / short codes for img.vietqr.io
BANK_CODES: dict[str, str] = {
    "mb": "970422",
    "mbbank": "970422",
    "vcb": "970436",
    "vietcombank": "970436",
    "tcb": "970407",
    "techcombank": "970407",
    "acb": "970416",
    "bidv": "970418",
    "vpb": "970432",
    "vpbank": "970432",
    "tpb": "970423",
    "tpbank": "970423",
    "vib": "970441",
    "msb": "970426",
    "ocb": "970448",
    "shb": "970443",
    "lpb": "970449",
    "lienviet": "970449",
    "agribank": "970405",
    "vietinbank": "970415",
    "ctg": "970415",
    "sacombank": "970403",
    "stb": "970403",
    "hdbank": "970437",
    "hdb": "970437",
    "hd": "970437",
    "seabank": "970440",
    "eximbank": "970431",
    "abbank": "970425",
    "namabank": "970428",
    "pgbank": "970430",
    "baca": "970409",
    "pvcombank": "970412",
    "scb": "970429",
}


def resolve_bank_bin(bank: str) -> str:
    b = (bank or "").strip().lower()
    if not b:
        return ""
    if b.isdigit() and len(b) >= 6:
        return b
    return BANK_CODES.get(b, b)


def vietqr_url(
    settings: Settings,
    *,
    amount: int | None = None,
    add_info: str | None = None,
    template: str = "compact2",
) -> str | None:
    """Build VietQR image URL, or None if bank details missing."""
    bin_code = resolve_bank_bin(settings.bank_id)
    acc = (settings.bank_account or "").strip().replace(" ", "")
    if not bin_code or not acc:
        return None

    name = (settings.bank_account_name or "").strip()
    # Mặc định qr_only: chỉ ảnh QR, text viết ở caption bot
    if template == "compact2":
        template = "qr_only"
    base = f"https://img.vietqr.io/image/{bin_code}-{acc}-{template}.png"
    params: list[str] = []
    if amount and amount > 0:
        params.append(f"amount={int(amount)}")
    info = add_info if add_info is not None else settings.bank_transfer_content
    if info:
        params.append(f"addInfo={quote(info)}")
    if name:
        params.append(f"accountName={quote(name)}")
    if params:
        return base + "?" + "&".join(params)
    return base


def local_qr_path(settings: Settings) -> Path | None:
    raw = (settings.payment_qr_path or "").strip()
    if not raw:
        return None
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT_DIR / path
    if path.is_file():
        return path.resolve()
    return None


def _bank_label(code: str) -> str:
    c = (code or "").strip().lower()
    names = {
        "mb": "MB Bank",
        "mbbank": "MB Bank",
        "970422": "MB Bank",
        "hdb": "HDBank",
        "hd": "HDBank",
        "hdbank": "HDBank",
        "970437": "HDBank",
        "vcb": "Vietcombank",
        "tcb": "Techcombank",
        "bidv": "BIDV",
        "acb": "ACB",
        "vpbank": "VPBank",
        "vpb": "VPBank",
    }
    return names.get(c, code.upper() if code else "—")


def payment_caption(settings: Settings, *, plan_name: str = "", amount: int | None = None) -> str:
    """Caption text đầy đủ — ảnh chỉ còn QR."""
    lines = ["📁 *HƯỚNG DẪN NẠP TIỀN*", ""]
    lines.append(f"🏦 Ngân hàng: *{_bank_label(settings.bank_id)}*")
    if settings.bank_account_name:
        lines.append(f"👤 Chủ TK: *{settings.bank_account_name}*")
    if settings.bank_account:
        lines.append(f"💳 Số TK: `{settings.bank_account}`")
    if amount and amount > 0:
        amount_fmt = f"{int(amount):,}".replace(",", ".")
        lines.append(f"💰 Số tiền: *{amount_fmt}* {settings.currency}")
    if plan_name:
        lines.append(f"📦 Gói: *{plan_name}*")
    content = settings.bank_transfer_content
    if content:
        lines.append(f"📝 Nội dung (bắt buộc): `{content}`")
    lines.append("")
    lines.append("Quét mã QR bằng app ngân hàng (VietQR / NAPAS 247).")
    lines.append("⚠️ Ghi *đúng nội dung* — sai nội dung sẽ không được cộng tiền.")
    lines.append("")
    lines.append("Sau CK → nhấn *Gửi ảnh bill* để Admin duyệt nhanh.")
    lines.append("Admin duyệt trong 5–30 phút (hoặc hệ thống tự kích hoạt).")
    if settings.payment_info:
        lines.append("")
        lines.append(settings.payment_info)
    return "\n".join(lines)


def order_payment_caption(
    *,
    plan_name: str,
    amount: int,
    bank_code: str,
    bank_account: str,
    bank_name: str,
    content: str,
    order_id: str,
    currency: str = "VND",
    support: str = "",
) -> str:
    """Caption đầy đủ dưới ảnh QR (chỉ QR trong ảnh)."""
    amount_fmt = f"{int(amount):,}".replace(",", ".")
    lines = [
        "📁 *HƯỚNG DẪN NẠP TIỀN*",
        "",
        f"🏦 Ngân hàng: *{_bank_label(bank_code)}*",
        f"👤 Chủ TK: *{bank_name or '—'}*",
        f"💳 Số TK: `{bank_account}`",
        f"💰 Số tiền: *{amount_fmt}* {currency}",
        f"📝 *Nội dung CK (bắt buộc — của riêng bạn):*",
        f"`{content}`",
        f"🔖 Mã đơn: `{order_id}`",
        f"📦 Gói: *{plan_name}*",
        "",
        "Quét *QR trong ảnh* bằng app ngân hàng (VietQR / NAPAS 247).",
        "⚠️ *Mỗi người một nội dung khác nhau* — copy đúng dòng trên khi CK.",
        "Sai nội dung → Admin khó đối soát / không auto-active.",
        "",
        "Sau CK → nhấn *Gửi ảnh bill* để Admin duyệt nhanh.",
        "Admin duyệt / hệ thống nhận tiền → *kích hoạt* gói.",
    ]
    if support:
        lines.append(f"\n🆘 {support}")
    return "\n".join(lines)


def has_qr_source(settings: Settings) -> bool:
    return local_qr_path(settings) is not None or vietqr_url(settings) is not None
