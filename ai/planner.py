"""Planner agent — breaks tasks into steps (Phase 3 scaffold)."""

from __future__ import annotations

from ai.grok import GrokClient
from ai.prompts import PLANNER_PROMPT


class PlannerAgent:
    def __init__(self, grok: GrokClient) -> None:
        self.grok = grok

    async def plan(self, goal: str) -> str:
        return await self.grok.chat(
            [{"role": "user", "content": goal}],
            system=PLANNER_PROMPT,
            temperature=0.3,
        )
