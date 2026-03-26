# ============================================================
#  FreedomForge AI — core/tool_repo.py
#  The Sovereign Forge: on-disk tool library
#
#  Vision:
#  Every time Free Echo Assistant or any attached model creates
#  a useful tool, program, or workflow, it is written here
#  automatically.  No ratings, no voting, no external approval:
#  if it is syntactically valid and passes a basic sandbox test
#  it is stored.  Other agents and future modes can reuse or copy
#  tools directly from here.
#
#  Long-term goals:
#  - Offline-first storage of all local tools & workflows.
#  - Simple, inspectable JSON index on disk.
#  - A place where the "smart scout" can keep upgrading itself.
# ============================================================

import json
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Optional

from core import logger

_TOOLS_DIR: Path = Path.home() / ".free_echo" / "tools"


@dataclass
class ToolRecord:
    name:         str
    description:  str
    language:     str            # "python", "bash", "powershell", …
    path:         str            # absolute path on disk
    created_by:   str            # "FreeEchoAssistant", model id, or "user"
    created_at:   float
    last_used_at: Optional[float] = None
    tags:         List[str]      = field(default_factory=list)


class ToolRepo:
    """
    On-disk repository of tools.

    Files:
    - ~/.free_echo/tools/index.json  — metadata for every tool.
    - ~/.free_echo/tools/<lang>/<name>.<ext>  — source files.

    Responsibilities:
    - Register tools (write code, record metadata).
    - List and fetch tool records.
    - Run tools in a shallow sandbox (isolated temp directory).
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir   = base_dir or _TOOLS_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.base_dir / "index.json"

        self._tools: Dict[str, ToolRecord] = {}
        self._load_index()

    # ── Index management ─────────────────────────────────────

    def _load_index(self) -> None:
        if not self.index_path.exists():
            self._tools = {}
            return
        try:
            raw  = self.index_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            self._tools = {}
            for name, rec_dict in data.items():
                # Back-compat: fill missing optional fields
                rec_dict.setdefault("last_used_at", None)
                rec_dict.setdefault("tags", [])
                self._tools[name] = ToolRecord(**rec_dict)
        except Exception as exc:
            logger.error(f"ToolRepo: failed to load index: {exc}")
            self._tools = {}

    def _save_index(self) -> None:
        data = {name: asdict(rec) for name, rec in self._tools.items()}
        self.index_path.write_text(
            json.dumps(data, indent=2), encoding="utf-8")

    # ── Public API ───────────────────────────────────────────

    def register_tool(
        self,
        name:        str,
        description: str,
        language:    str,
        code:        str,
        created_by:  str       = "FreeEchoAssistant",
        tags:        Optional[List[str]] = None,
    ) -> ToolRecord:
        """
        Save a new tool (or overwrite an existing one with the same name).

        Writes code to  ~/.free_echo/tools/<language>/<name>.<ext>
        and updates index.json.
        """
        language = language.lower()
        ext      = _ext_for_language(language)
        tool_dir = self.base_dir / language
        tool_dir.mkdir(parents=True, exist_ok=True)
        tool_path = tool_dir / f"{name}{ext}"

        tool_path.write_text(code, encoding="utf-8")

        rec = ToolRecord(
            name         = name,
            description  = description,
            language     = language,
            path         = str(tool_path),
            created_by   = created_by,
            created_at   = time.time(),
            tags         = tags or [],
        )
        self._tools[name] = rec
        self._save_index()

        logger.info(
            f"ToolRepo: registered '{name}' ({language}) "
            f"by {created_by} → {tool_path}"
        )
        return rec

    def list_tools(self) -> List[ToolRecord]:
        """Return all registered tool records."""
        return list(self._tools.values())

    def get_tool(self, name: str) -> Optional[ToolRecord]:
        """Return a single tool record by name, or None."""
        return self._tools.get(name)

    def run_tool(
        self,
        name: str,
        args: Optional[List[str]] = None,
    ) -> subprocess.CompletedProcess:
        """
        Execute a tool in an isolated temp working directory.

        The tool is run in a fresh temp directory so it cannot
        accidentally write to the project root.  Environment
        variables are inherited (future: we can scrub them here).

        Returns the CompletedProcess object so callers can check
        stdout, stderr and returncode.
        """
        rec = self.get_tool(name)
        if rec is None:
            raise ValueError(f"Tool {name!r} not found in ToolRepo")

        cmd = _command_for_tool(rec, args or [])

        with tempfile.TemporaryDirectory() as tmpdir:
            proc = subprocess.run(
                cmd,
                cwd           = tmpdir,
                env           = os.environ.copy(),
                capture_output = True,
                text           = True,
            )

        rec.last_used_at    = time.time()
        self._tools[rec.name] = rec
        self._save_index()

        logger.info(
            f"ToolRepo: ran '{name}' → rc={proc.returncode}"
        )
        return proc

    def delete_tool(self, name: str) -> bool:
        """
        Remove a tool from the index and delete its source file.
        Returns True if the tool existed, False otherwise.
        """
        rec = self._tools.pop(name, None)
        if rec is None:
            return False
        try:
            Path(rec.path).unlink(missing_ok=True)
        except Exception as exc:
            logger.error(f"ToolRepo: could not delete file {rec.path}: {exc}")
        self._save_index()
        logger.info(f"ToolRepo: deleted tool '{name}'")
        return True

    # ── Idle growth hook ─────────────────────────────────────

    def idle_optimize(self, max_tools: int = 3) -> None:
        """
        Called when the system is idle.

        Logs tools that have never been used — these are candidates
        for the model to review and improve.

        TODO: call a model that reads each tool, improves it, and
              re-registers the updated version automatically.
        """
        unused = [t for t in self._tools.values() if not t.last_used_at]
        unused = sorted(unused, key=lambda t: t.created_at)[:max_tools]
        if unused:
            names = ", ".join(t.name for t in unused)
            logger.info(f"ToolRepo: idle optimization candidates: {names}")


# ── Helpers ──────────────────────────────────────────────────

def _ext_for_language(language: str) -> str:
    return {
        "python":     ".py",
        "bash":       ".sh",
        "powershell": ".ps1",
    }.get(language, ".txt")


def _command_for_tool(rec: ToolRecord, args: List[str]) -> List[str]:
    if rec.language == "python":
        return [sys.executable, rec.path] + args
    if rec.language == "bash":
        return ["bash", rec.path] + args
    if rec.language == "powershell":
        return ["powershell", "-File", rec.path] + args
    return [sys.executable, rec.path] + args


# ── Singleton helper ─────────────────────────────────────────

_repo_instance: Optional[ToolRepo] = None


def get_tool_repo() -> ToolRepo:
    """Return the process-wide singleton ToolRepo instance."""
    global _repo_instance
    if _repo_instance is None:
        _repo_instance = ToolRepo()
    return _repo_instance
