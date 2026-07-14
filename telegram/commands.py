"""Bot command descriptions & help text."""

from __future__ import annotations

from aiogram.types import BotCommand

from config import Settings

BOT_COMMANDS = [
    BotCommand(command="start", description="Bắt đầu"),
    BotCommand(command="help", description="Hướng dẫn"),
    BotCommand(command="buy", description="Xem gói & mua (QR auto)"),
    BotCommand(command="qr", description="Tạo QR theo gói"),
    BotCommand(command="activate", description="Kích hoạt mã"),
    BotCommand(command="payhealth", description="Admin: check vietqr-pay"),
    BotCommand(command="account", description="Tài khoản & quota"),
    BotCommand(command="status", description="Trạng thái bot"),
    BotCommand(command="clear", description="Xóa memory"),
    BotCommand(command="plan", description="Planner agent"),
    BotCommand(command="code", description="Coder agent"),
    BotCommand(command="review", description="Reviewer agent"),
    BotCommand(command="debug", description="Debugger agent"),
    BotCommand(command="build", description="Pipeline plan→code→review"),
    BotCommand(command="project", description="Project notes"),
    BotCommand(command="projects", description="Danh sách project"),
    BotCommand(command="teach", description="Dạy AI (chỉ chủ bot)"),
    BotCommand(command="mode", description="Chế độ AI (coder/security/…)"),
    BotCommand(command="model", description="Model + mode hiện tại"),
    BotCommand(command="setmodel", description="Đổi model (chủ bot)"),
    BotCommand(command="support", description="Liên hệ hỗ trợ"),
    BotCommand(command="admin", description="Admin (chủ bot)"),
]


def help_text(settings: Settings) -> str:
    return f"""\
🤖 *{settings.app_name}*
_{settings.product_tagline}_

*Khách hàng:*
/start — chào
/buy — bảng giá + QR ngân hàng
/qr — QR CK (hoặc `/qr basic`)
/activate `MÃ` — kích hoạt gói
/account — gói & quota
/status — trạng thái
/clear — xóa nhớ hội thoại (RAM + DB)
/support — hỗ trợ ({settings.support_contact})

*Agents (Phase 3):*
/plan `task` — lập kế hoạch
/code `spec` — sinh code
/review `code…` — review code
/debug `lỗi…` — phân tích lỗi
/build `task` — pipeline plan→code→review

*Projects (Phase 2):*
/projects — danh sách
/project new `tên` — tạo
/project show `ID` — xem notes
/project note `ID` `nội dung` — ghi note
/project del `ID` — xóa

*Dạy AI (chỉ chủ bot):*
/teach `luật…` — thêm luật toàn bot
/teach style `…` — phong cách
/teach fact `…` — thông tin shop/sản phẩm
/teach list · /teach del `ID` · /teach clear

*Làm AI mạnh hơn:*
/mode `coder|security|sales|research|default` — chuyên môn
/model — xem model + mode
/setmodel — đổi model (chỉ chủ bot; model trả phí = mạnh hơn)

*Chat:* gửi tin → AI (quota + memory + luật owner + mode).

*Admin:* /admin /stats /users /gencode /adduser /deluser
"""


# Back-compat
HELP_TEXT = "Gõ /help"
