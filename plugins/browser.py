"""Browser automation plugin scaffold."""

from __future__ import annotations

from typing import Any

from plugins.base import Plugin


class BrowserPlugin(Plugin):
    name = "browser"

    async def setup(self) -> None:
        pass

    async def teardown(self) -> None:
        pass

    async def fetch(self, url: str) -> dict[str, Any]:
        return {"implemented": False, "url": url}
