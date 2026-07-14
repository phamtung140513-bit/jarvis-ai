"""Workspace file read/write plugin scaffold (Phase 4)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from plugins.base import Plugin

logger = logging.getLogger(__name__)


class FilesPlugin(Plugin):
    name = "files"

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace.resolve()

    async def setup(self) -> None:
        self.workspace.mkdir(parents=True, exist_ok=True)

    async def teardown(self) -> None:
        pass

    def _safe(self, relative: str) -> Path:
        target = (self.workspace / relative).resolve()
        if not str(target).startswith(str(self.workspace)):
            raise PermissionError("Path escapes workspace")
        return target

    async def read_text(self, relative: str) -> str:
        path = self._safe(relative)
        return path.read_text(encoding="utf-8")

    async def write_text(self, relative: str, content: str) -> dict[str, Any]:
        path = self._safe(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        logger.info("Wrote file %s (%d bytes)", path, len(content))
        return {"path": str(path), "bytes": len(content.encode("utf-8"))}

    async def list_dir(self, relative: str = ".") -> list[str]:
        path = self._safe(relative)
        if not path.is_dir():
            return []
        return sorted(p.name for p in path.iterdir())
