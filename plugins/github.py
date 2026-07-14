"""Git / GitHub plugin scaffold (Phase 6)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from plugins.base import Plugin

logger = logging.getLogger(__name__)


class GitHubPlugin(Plugin):
    name = "github"

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace

    async def setup(self) -> None:
        logger.debug("GitHub plugin ready (workspace=%s)", self.workspace)

    async def teardown(self) -> None:
        pass

    async def status(self, repo_path: Path | None = None) -> dict[str, Any]:
        """Return git status summary — implemented in Phase 6 with GitPython."""
        path = repo_path or self.workspace
        return {
            "path": str(path),
            "implemented": False,
            "message": "Phase 6: GitPython commit/branch/diff",
        }
