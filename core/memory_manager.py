# ============================================================
#  FreedomForge AI — core/memory_manager.py
#  Chat memory: rolling context window + compressed long-term storage
#
#  Vision:
#  Instead of blindly hoarding every message, the memory manager
#  keeps a short rolling window of recent turns (immediate context)
#  and compresses older exchanges into condensed summaries.
#  Important facts are flagged and always kept.
#
#  Long-term goals:
#  - "Grow with you" — the assistant remembers key facts even after
#    many sessions, without wasting context on stale small talk.
#  - Optional semantic search so the model can pull in relevant
#    old memories when a topic comes back up.
#  - All data stays local under ~/.free_echo/memory/.
# ============================================================

import json
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Optional

from core import logger

_MEMORY_DIR: Path = Path.home() / ".free_echo" / "memory"
_MAX_ROLLING: int = 40   # recent turns kept verbatim
_MAX_SUMMARIES: int = 50  # max compressed summary entries kept


@dataclass
class MemoryEntry:
    role:       str              # "user" | "assistant" | "system"
    content:    str
    timestamp:  float = field(default_factory=time.time)
    important:  bool  = False    # if True, never auto-compressed


@dataclass
class MemorySummary:
    summary:   str
    from_time: float
    to_time:   float
    turn_count: int


class MemoryManager:
    """
    Two-layer memory store:

    Layer 1 — rolling window (list of MemoryEntry, newest last).
              Kept fully verbatim.  When it exceeds _MAX_ROLLING,
              the oldest non-important entries are compressed.

    Layer 2 — summaries (list of MemorySummary).
              Condensed text produced when old entries are evicted.
              A future model call can produce rich summaries; for
              now we join content lines into a brief digest.

    Disk layout:
      ~/.free_echo/memory/rolling.json   — layer-1 entries
      ~/.free_echo/memory/summaries.json — layer-2 summaries
    """

    def __init__(self, memory_dir: Optional[Path] = None):
        self.memory_dir = memory_dir or _MEMORY_DIR
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self._rolling_path   = self.memory_dir / "rolling.json"
        self._summaries_path = self.memory_dir / "summaries.json"

        self._rolling:   List[MemoryEntry]   = []
        self._summaries: List[MemorySummary] = []
        self._load()

    # ── Persistence ──────────────────────────────────────────

    def _load(self) -> None:
        try:
            if self._rolling_path.exists():
                raw = json.loads(self._rolling_path.read_text(encoding="utf-8"))
                self._rolling = [MemoryEntry(**e) for e in raw]
        except Exception as exc:
            logger.error(f"MemoryManager: failed to load rolling: {exc}")
            self._rolling = []

        try:
            if self._summaries_path.exists():
                raw = json.loads(
                    self._summaries_path.read_text(encoding="utf-8"))
                self._summaries = [MemorySummary(**s) for s in raw]
        except Exception as exc:
            logger.error(f"MemoryManager: failed to load summaries: {exc}")
            self._summaries = []

    def _save(self) -> None:
        try:
            self._rolling_path.write_text(
                json.dumps([asdict(e) for e in self._rolling], indent=2),
                encoding="utf-8",
            )
            self._summaries_path.write_text(
                json.dumps([asdict(s) for s in self._summaries], indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.error(f"MemoryManager: failed to save: {exc}")

    # ── Public API ───────────────────────────────────────────

    def add(
        self,
        role:      str,
        content:   str,
        important: bool = False,
    ) -> None:
        """Append a single turn to the rolling window."""
        self._rolling.append(
            MemoryEntry(role=role, content=content, important=important)
        )
        self._maybe_compress()
        self._save()

    def add_turn(self, user_msg: str, assistant_reply: str) -> None:
        """Convenience: add a user + assistant exchange as one call."""
        self.add("user",      user_msg)
        self.add("assistant", assistant_reply)

    def get_context(self, max_turns: Optional[int] = None) -> List[dict]:
        """
        Return the rolling window as a list of {"role": …, "content": …}
        dicts ready for the model's messages parameter.

        If max_turns is set, return only the last N turns.
        """
        entries = self._rolling
        if max_turns is not None:
            entries = entries[-max_turns:]
        return [{"role": e.role, "content": e.content} for e in entries]

    def get_summary_text(self) -> str:
        """
        Return a plain-text digest of all compressed summaries,
        suitable for injecting as a system message at session start.
        """
        if not self._summaries:
            return ""
        lines = ["[Memory digest from previous sessions]"]
        for s in self._summaries[-10:]:          # last 10 summaries
            lines.append(f"- {s.summary}")
        return "\n".join(lines)

    def mark_important(self, content_fragment: str) -> int:
        """
        Mark all rolling entries whose content contains
        content_fragment as important (never auto-compressed).
        Returns the count of entries updated.
        """
        count = 0
        for entry in self._rolling:
            if content_fragment in entry.content:
                entry.important = True
                count += 1
        if count:
            self._save()
        return count

    def clear(self) -> None:
        """Wipe both layers (use for privacy / reset)."""
        self._rolling   = []
        self._summaries = []
        self._save()
        logger.info("MemoryManager: cleared all memory")

    def stats(self) -> dict:
        """Return a small status dict for the settings/privacy panel."""
        return {
            "rolling_entries":  len(self._rolling),
            "summary_entries":  len(self._summaries),
            "memory_dir":       str(self.memory_dir),
        }

    # ── Compression ──────────────────────────────────────────

    def _maybe_compress(self) -> None:
        """
        If the rolling window exceeds _MAX_ROLLING, compress the
        oldest non-important entries into a MemorySummary and evict them.
        """
        if len(self._rolling) <= _MAX_ROLLING:
            return

        evict_count = len(self._rolling) - _MAX_ROLLING
        to_evict    = []
        keep        = []

        for entry in self._rolling:
            if not entry.important and len(to_evict) < evict_count:
                to_evict.append(entry)
            else:
                keep.append(entry)

        if not to_evict:
            # All overflow entries are marked important — trim them anyway
            # to prevent unlimited growth, but keep a note.
            to_evict = self._rolling[:evict_count]
            keep     = self._rolling[evict_count:]

        self._rolling = keep
        summary_text  = _summarize_entries(to_evict)
        self._summaries.append(
            MemorySummary(
                summary    = summary_text,
                from_time  = to_evict[0].timestamp,
                to_time    = to_evict[-1].timestamp,
                turn_count = len(to_evict),
            )
        )

        # Trim summaries list if it grows too large
        if len(self._summaries) > _MAX_SUMMARIES:
            self._summaries = self._summaries[-_MAX_SUMMARIES:]

        logger.debug(
            f"MemoryManager: compressed {len(to_evict)} entries "
            f"into summary"
        )


def _summarize_entries(entries: List[MemoryEntry]) -> str:
    """
    Lightweight summarizer: join first ~80 chars of each entry.

    TODO: replace with a real model call so the summary is
          semantically meaningful instead of just truncated.
    """
    parts = []
    for e in entries:
        snippet = e.content[:80].replace("\n", " ")
        parts.append(f"[{e.role}] {snippet}")
    return " | ".join(parts)


# ── Singleton helper ─────────────────────────────────────────

_manager_instance: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """Return the process-wide singleton MemoryManager instance."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = MemoryManager()
    return _manager_instance
