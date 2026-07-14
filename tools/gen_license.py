#!/usr/bin/env python3
"""Generate software license keys for white-label installs.

Usage:
  python tools/gen_license.py --customer "shop_a" --days 365
  python tools/gen_license.py --secret "your-secret" --customer "agency" --days 90
"""

from __future__ import annotations

import argparse
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from product.license_keys import generate_software_license, verify_software_license  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description="Generate JV software license")
    p.add_argument("--customer", required=True, help="Customer / shop name")
    p.add_argument("--days", type=int, default=365, help="Validity days")
    p.add_argument(
        "--secret",
        default="",
        help="LICENSE_SECRET (default: from env or generate new)",
    )
    args = p.parse_args()

    secret = args.secret
    if not secret:
        try:
            from config import clear_settings_cache, get_settings

            clear_settings_cache()
            s = get_settings()
            secret = s.license_secret
        except Exception:
            secret = ""

    if not secret:
        secret = secrets.token_urlsafe(24)
        print(f"# New LICENSE_SECRET (save to .env):\nLICENSE_SECRET={secret}\n")

    key = generate_software_license(secret, args.customer, args.days)
    info = verify_software_license(secret, key)
    print(f"Customer : {args.customer}")
    print(f"Days     : {args.days}")
    print(f"Valid    : {info.valid} ({info.reason})")
    print(f"\nSOFTWARE_LICENSE_KEY={key}")
    print("\n# Buyer .env snippet:")
    print(f"REQUIRE_SOFTWARE_LICENSE=true")
    print(f"LICENSE_SECRET={secret}")
    print(f"SOFTWARE_LICENSE_KEY={key}")


if __name__ == "__main__":
    main()
