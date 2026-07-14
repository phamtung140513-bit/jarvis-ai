#!/usr/bin/env python3
"""CLI: create SaaS access codes without Telegram.

  python tools/gen_access_code.py --plan basic --days 30
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import clear_settings_cache, ensure_directories, get_settings  # noqa: E402
from database.sqlite import Database  # noqa: E402
from product.access_codes import create_access_code  # noqa: E402
from product.plans import get_plan  # noqa: E402


async def _run(plan: str, days: int | None, uses: int) -> None:
    clear_settings_cache()
    settings = get_settings()
    ensure_directories(settings)
    db = Database(settings)
    await db.init()
    async with db.session() as session:
        code = await create_access_code(
            session, plan_id=plan, days=days, max_uses=uses, note="cli"
        )
    p = get_plan(plan)
    print(f"Plan : {p.name} ({plan})")
    print(f"Days : {code.days}")
    print(f"Uses : {code.max_uses}")
    print(f"CODE : {code.code}")
    print(f"\nCustomer: /activate {code.code}")
    await db.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default="basic", choices=["trial", "basic", "pro", "business"])
    ap.add_argument("--days", type=int, default=None)
    ap.add_argument("--uses", type=int, default=1)
    args = ap.parse_args()
    asyncio.run(_run(args.plan, args.days, args.uses))


if __name__ == "__main__":
    main()
