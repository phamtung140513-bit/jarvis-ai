"""Debugger agent — analyze errors (Phase 3 scaffold)."""

from __future__ import annotations

from ai.grok import GrokClient
from ai.prompts import DEBUGGER_PROMPT


class DebuggerAgent:
    def __init__(self, grok: GrokClient) -> None:
        self.grok = grok

    async def debug(self, error_report: str) -> str:
        return await self.grok.chat(
            [{"role": "user", "content": error_report}],
            system=DEBUGGER_PROMPT,
            temperature=0.2,
        )
