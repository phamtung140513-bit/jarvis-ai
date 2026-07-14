"""Reviewer agent — code review (Phase 3 scaffold)."""

from __future__ import annotations

from ai.grok import GrokClient
from ai.prompts import REVIEWER_PROMPT


class ReviewerAgent:
    def __init__(self, grok: GrokClient) -> None:
        self.grok = grok

    async def review(self, code: str) -> str:
        return await self.grok.chat(
            [{"role": "user", "content": f"Review the following code:\n\n{code}"}],
            system=REVIEWER_PROMPT,
            temperature=0.2,
        )
