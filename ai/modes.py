"""Chat modes — specialist system extras (pro coding / defensive security / sales)."""

from __future__ import annotations

from dataclasses import dataclass

# In-process per-user mode (reset on bot restart — OK)
_user_modes: dict[int, str] = {}


@dataclass(frozen=True)
class Mode:
    id: str
    name: str
    description: str
    prompt: str
    temperature: float | None = None


MODES: dict[str, Mode] = {
    "default": Mode(
        id="default",
        name="Default",
        description="Trợ lý đa năng — coding + tư vấn",
        prompt="",
        temperature=None,
    ),
    "coder": Mode(
        id="coder",
        name="Coder Pro",
        description="Sinh code / kiến trúc / debug mạnh",
        temperature=0.25,
        prompt="""\
Bạn đang ở MODE CODER PRO — trợ lý lập trình cấp senior.

Bắt buộc:
1. Trả lời bằng tiếng Việt khi user dùng tiếng Việt; code/identifier tiếng Anh.
2. Ưu tiên code chạy được, type hints (Python), error handling, edge cases.
3. Khi viết code: nêu file path, ngôn ngữ, và đoạn code đầy đủ (không pseudo nửa vời).
4. Nếu thiếu thông tin: hỏi 1–2 câu ngắn HOẶC nêu giả định rõ ràng rồi code.
5. Không bịa API; không chắc thì nói "cần verify docs".
6. Với task lớn: tóm tắt plan 3–7 bước rồi implement phần quan trọng nhất.
7. Security: tránh SQL injection, XSS, secret hardcode, RCE từ input user.
8. Telegram: gọn, chia phần; ưu tiên code + bullet ngắn.
""",
    ),
    "security": Mode(
        id="security",
        name="Security (defensive)",
        description="Phân tích bảo mật phòng thủ / review code",
        temperature=0.2,
        prompt="""\
Bạn đang ở MODE SECURITY — chuyên phân tích bảo mật *phòng thủ* (defensive).

Phạm vi được phép:
- Review code tìm bug/lỗ hổng để *sửa* (OWASP, auth, crypto misuse, injection, SSRF, IDOR…).
- Hardening checklist, threat model, secure coding.
- Giải thích CVE/khái niệm để học và tự bảo vệ hệ thống mình sở hữu.
- Patch/fix gợi ý tối thiểu, test case.

Không được:
- Hướng dẫn tấn công hệ thống không được ủy quyền.
- Viết malware, ransomware, stealer, botnet, dark-web dump credential để lạm dụng.
- Bypass bảo mật của bên thứ ba (bank, school, social) ngoài phạm vi lab hợp pháp.

Format trả lời khi review:
1) Tóm tắt rủi ro
2) Findings: Critical / High / Medium / Low (mô tả + vị trí + impact)
3) PoC *khái niệm* an toàn (không exploit sẵn dùng tấn công)
4) Fix cụ thể (code/patch)
5) Checklist hardening
""",
    ),
    "sales": Mode(
        id="sales",
        name="Sales",
        description="Tư vấn bán gói bot",
        temperature=0.5,
        prompt="""\
Bạn đang ở MODE SALES — tư vấn viên bán gói AI Telegram.

Nhiệm vụ:
- Hiểu nhu cầu (cá nhân / freelancer / agency).
- Gợi ý gói phù hợp, nêu giá đúng (không bịa).
- Hướng dẫn: /buy → QR → /activate MÃ.
- Giọng thân thiện, ngắn, chốt nhẹ không ép.
- Nếu hỏi kỹ thuật sâu: trả lời gọn rồi mời mua gói Pro/Business nếu cần quota.
""",
    ),
    "research": Mode(
        id="research",
        name="Research",
        description="Phân tích sâu, so sánh, tóm tắt kỹ thuật",
        temperature=0.35,
        prompt="""\
Bạn đang ở MODE RESEARCH — nghiên cứu / phân tích kỹ thuật sâu.

- Cấu trúc: tóm tắt → chi tiết → so sánh → kết luận / next steps.
- Phân biệt: đã biết chắc / suy đoán / cần verify.
- Đưa nguồn khái niệm (docs chính thức, RFC, paper) khi có thể; không bịa URL.
- Ưu tiên bảng so sánh, bullet, checklist hành động.
""",
    ),
}


# Presets model mạnh hơn (owner /setmodel). Cần đúng provider + key.
MODEL_PRESETS: dict[str, dict[str, str]] = {
    # Groq free-ish
    "fast": {
        "provider": "groq",
        "model": "llama-3.3-70b-versatile",
        "label": "Groq Llama 3.3 70B (nhanh, free tier)",
    },
    "qwen": {
        "provider": "groq",
        "model": "qwen/qwen3-32b",
        "label": "Groq Qwen3 32B",
    },
    # xAI
    "grok": {
        "provider": "xai",
        "model": "grok-3-mini",
        "label": "xAI Grok 3 Mini",
    },
    "grok-full": {
        "provider": "xai",
        "model": "grok-3",
        "label": "xAI Grok 3 (mạnh hơn, tốn credit)",
    },
    # OpenRouter — cần OPENROUTER key; model id có thể đổi theo catalog
    "deepseek": {
        "provider": "openrouter",
        "model": "deepseek/deepseek-chat",
        "label": "OpenRouter DeepSeek Chat",
    },
    "claude": {
        "provider": "openrouter",
        "model": "anthropic/claude-3.5-sonnet",
        "label": "OpenRouter Claude 3.5 Sonnet (rất mạnh, trả phí)",
    },
    "gpt4o": {
        "provider": "openrouter",
        "model": "openai/gpt-4o",
        "label": "OpenRouter GPT-4o (rất mạnh, trả phí)",
    },
}


def get_mode(mode_id: str) -> Mode:
    return MODES.get((mode_id or "default").lower(), MODES["default"])


def set_user_mode(user_id: int, mode_id: str) -> Mode:
    mode = get_mode(mode_id)
    if mode.id == "default":
        _user_modes.pop(user_id, None)
    else:
        _user_modes[user_id] = mode.id
    return mode


def get_user_mode(user_id: int) -> Mode:
    return get_mode(_user_modes.get(user_id, "default"))


def list_modes_text() -> str:
    lines = ["🎛 *Chế độ AI* — `/mode <id>`", ""]
    for m in MODES.values():
        lines.append(f"• `{m.id}` — *{m.name}*: {m.description}")
    lines.append("\nVD: `/mode coder` · `/mode security` · `/mode default`")
    return "\n".join(lines)


def list_model_presets_text() -> str:
    lines = [
        "🧠 *Model presets* (chỉ owner) — `/setmodel <id>`",
        "",
        "Muốn mạnh như site multi-model (GPT/Claude): cần *API trả phí* "
        "(OpenRouter / xAI), không chỉ prompt.",
        "",
    ]
    for key, p in MODEL_PRESETS.items():
        lines.append(f"• `{key}` → {p['label']}\n  `{p['provider']}` / `{p['model']}`")
    lines.append("\nHoặc: `/setmodel raw provider model`")
    lines.append("VD: `/setmodel raw openrouter deepseek/deepseek-chat`")
    return "\n".join(lines)


def merge_prompt_layers(
    *,
    mode_prompt: str | None,
    teachings: str | None,
) -> str | None:
    parts = [p.strip() for p in (mode_prompt, teachings) if p and p.strip()]
    if not parts:
        return None
    return "\n\n".join(parts)
