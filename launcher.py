"""Convenient launcher with preflight checks."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root on sys.path when run as script
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def preflight() -> None:
    env = ROOT / ".env"
    if not env.exists():
        example = ROOT / ".env.example"
        print("❌ Thiếu file .env")
        print(f"   Copy {example.name} → .env và điền TELEGRAM_BOT_TOKEN, XAI_API_KEY, ALLOWED_TELEGRAM_IDS")
        sys.exit(1)

    try:
        from config import get_settings

        s = get_settings()
    except Exception as exc:
        print(f"❌ Config lỗi: {exc}")
        sys.exit(1)

    if not s.allowed_ids:
        print("❌ ALLOWED_TELEGRAM_IDS trống — thêm Telegram user ID của bạn")
        sys.exit(1)

    print(
        f"✅ Config OK — provider={s.provider} model={s.resolved_model} "
        f"allowed={sorted(s.allowed_ids)}"
    )


def main() -> None:
    preflight()
    from bot import main as bot_main

    bot_main()


if __name__ == "__main__":
    main()
