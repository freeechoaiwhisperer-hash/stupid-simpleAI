# ============================================================
#  FreedomForge AI — modules/tools.py
#  Agent tool registry (wraps core/tool_repo.py)
# ============================================================

from __future__ import annotations

from core.tool_repo import (  # noqa: F401
    ToolRepo,
    get_tool_repo,
)

__all__ = ["ToolRepo", "get_tool_repo"]
