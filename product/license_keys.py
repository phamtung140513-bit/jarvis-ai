"""Software license keys (for selling source / white-label installs)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import time
from dataclasses import dataclass


@dataclass
class LicenseInfo:
    customer: str
    expires_at: int
    valid: bool
    reason: str = ""


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def generate_software_license(
    secret: str,
    customer: str,
    days: int = 365,
) -> str:
    """Create a portable license string: JV-<payload>.<sig>"""
    customer = customer.strip().replace(":", "_")[:64] or "customer"
    exp = int(time.time()) + max(1, days) * 86400
    payload = f"{customer}:{exp}"
    sig = hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:20]
    return f"JV-{_b64(payload.encode('utf-8'))}.{sig}"


def verify_software_license(secret: str, license_key: str) -> LicenseInfo:
    if not secret:
        return LicenseInfo("", 0, True, "no_secret_configured")
    if not license_key or not license_key.startswith("JV-"):
        return LicenseInfo("", 0, False, "missing_or_bad_format")

    try:
        body = license_key[3:]
        payload_b64, sig = body.rsplit(".", 1)
        payload = _unb64(payload_b64).decode("utf-8")
        customer, exp_s = payload.split(":", 1)
        exp = int(exp_s)
    except Exception:
        return LicenseInfo("", 0, False, "parse_error")

    expect = hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:20]
    if not hmac.compare_digest(expect, sig):
        return LicenseInfo(customer, exp, False, "bad_signature")

    if exp < int(time.time()):
        return LicenseInfo(customer, exp, False, "expired")

    return LicenseInfo(customer, exp, True, "ok")
