"""Coder agent — generates code from a plan/spec (Phase 3 scaffold)."""

from __future__ import annotations

from ai.grok import GrokClient
from ai.prompts import CODER_PROMPT


class CoderAgent:
    def __init__(self, grok: GrokClient) -> None:
        self.grok = grok

    async def code(self, specification: str) -> str:
        return await self.grok.chat(
            [{"role": "user", "content": specification}],
            system=CODER_PROMPT,
            temperature=0.2,
        )
