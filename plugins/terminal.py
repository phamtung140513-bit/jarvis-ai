"""Host terminal plugin scaffold — prefer Docker sandbox in production."""

from __future__ import annotations

from typing import Any

from plugins.base import Plugin


class TerminalPlugin(Plugin):
    name = "terminal"

    async def setup(self) -> None:
        pass

    async def teardown(self) -> None:
        pass

    async def run(self, command: str) -> dict[str, Any]:
        return {
            "implemented": False,
            "command": command,
            "message": "Disabled by default; use Docker sandbox (Phase 5)",
        }
