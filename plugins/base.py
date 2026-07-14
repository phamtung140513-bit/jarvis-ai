"""Minimal plugin interface."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class Plugin(ABC):
    name: str = "base"

    @abstractmethod
    async def setup(self) -> None:
        ...

    @abstractmethod
    async def teardown(self) -> None:
        ...

    async def health(self) -> dict[str, Any]:
        return {"name": self.name, "ok": True}


class PluginManager:
    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}

    def register(self, plugin: Plugin) -> None:
        self._plugins[plugin.name] = plugin
        logger.info("Registered plugin: %s", plugin.name)

    async def setup_all(self) -> None:
        for p in self._plugins.values():
            await p.setup()

    async def teardown_all(self) -> None:
        for p in self._plugins.values():
            await p.teardown()

    def get(self, name: str) -> Plugin | None:
        return self._plugins.get(name)

    def list_names(self) -> list[str]:
        return sorted(self._plugins)
