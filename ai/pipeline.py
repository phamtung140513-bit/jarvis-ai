"""Agent pipeline: planner → coder → reviewer → debugger (Phase 3)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from ai.coder import CoderAgent
from ai.debugger import DebuggerAgent
from ai.grok import GrokClient
from ai.planner import PlannerAgent
from ai.reviewer import ReviewerAgent

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    goal: str
    plan: str = ""
    code: str = ""
    review: str = ""
    debug: str = ""
    steps_done: list[str] = field(default_factory=list)
    error: str | None = None

    def format_telegram(self) -> str:
        parts: list[str] = [f"🔧 *Pipeline* — `{self.goal[:80]}`"]
        if self.plan:
            parts.append(f"\n📋 *Plan*\n{self.plan}")
        if self.code:
            parts.append(f"\n💻 *Code*\n{self.code}")
        if self.review:
            parts.append(f"\n🔎 *Review*\n{self.review}")
        if self.debug:
            parts.append(f"\n🐛 *Debug notes*\n{self.debug}")
        if self.error:
            parts.append(f"\n❌ *Error*\n{self.error}")
        if self.steps_done:
            parts.append(f"\n_Steps: {', '.join(self.steps_done)}_")
        return "\n".join(parts)


class AgentPipeline:
    """Orchestrates scaffold agents into a multi-step coding flow."""

    def __init__(self, grok: GrokClient) -> None:
        self.planner = PlannerAgent(grok)
        self.coder = CoderAgent(grok)
        self.reviewer = ReviewerAgent(grok)
        self.debugger = DebuggerAgent(grok)

    async def run(
        self,
        goal: str,
        *,
        do_plan: bool = True,
        do_code: bool = True,
        do_review: bool = True,
        do_debug_hint: bool = False,
        error_context: str | None = None,
    ) -> PipelineResult:
        result = PipelineResult(goal=goal.strip())
        if not result.goal:
            result.error = "Goal rỗng"
            return result

        try:
            if do_plan:
                result.plan = await self.planner.plan(result.goal)
                result.steps_done.append("plan")
                logger.info("pipeline plan done goal_len=%d", len(result.goal))

            if do_code:
                spec = result.goal
                if result.plan:
                    spec = (
                        f"Goal:\n{result.goal}\n\n"
                        f"Plan to implement:\n{result.plan}\n\n"
                        "Implement the solution based on the plan."
                    )
                result.code = await self.coder.code(spec)
                result.steps_done.append("code")

            if do_review and result.code:
                result.review = await self.reviewer.review(result.code)
                result.steps_done.append("review")

            if do_debug_hint or error_context:
                report = error_context or (
                    f"Goal: {result.goal}\n\n"
                    f"Generated code:\n{result.code[:3000]}\n\n"
                    f"Review findings:\n{result.review[:1500]}\n\n"
                    "Suggest potential bugs and a minimal fix plan."
                )
                result.debug = await self.debugger.debug(report)
                result.steps_done.append("debug")

        except Exception as exc:
            logger.exception("Agent pipeline failed")
            result.error = str(exc)

        return result
