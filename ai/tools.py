"""Tool registry for agents (Phase 4–6 expand)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

ToolFn = Callable[..., Awaitable[Any]]


class ToolRegistry:
    """Simple name → async callable map for future agent tool-calling."""

    def __init__(self) -> None:
        self._tools: Dict[str, ToolFn] = {}

    def register(self, name: str, fn: ToolFn) -> None:
        self._tools[name] = fn

    def get(self, name: str) -> ToolFn | None:
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        return sorted(self._tools)

    async def call(self, name: str, **kwargs: Any) -> Any:
        fn = self._tools.get(name)
        if fn is None:
            raise KeyError(f"Unknown tool: {name}")
        return await fn(**kwargs)
