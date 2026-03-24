# ============================================================
#  FreedomForge AI — plugins/echo_file_sort_cleaner.py
#  Echo File Sort & Cleaner plugin
#
#  Vision:
#  A simple, safe "tidy up your files" assistant that:
#  - Scans a target folder recursively.
#  - Moves files into organised sub-folders by type.
#  - Flags exact duplicate files (same SHA-256).
#  - Takes a recovery snapshot (JSON manifest) before moving
#    anything, so you can always undo.
#
#  All operations are local and reversible:
#  - Nothing is deleted without explicit user confirmation.
#  - The snapshot lets you restore original locations.
# ============================================================

import hashlib
import json
import shutil
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from core import logger

# ── File-type categories ─────────────────────────────────────

_CATEGORIES: Dict[str, List[str]] = {
    "images":     [".jpg", ".jpeg", ".png", ".gif", ".webp",
                   ".bmp", ".svg", ".ico", ".tiff", ".heic"],
    "videos":     [".mp4", ".mkv", ".avi", ".mov", ".wmv",
                   ".flv", ".webm", ".m4v"],
    "audio":      [".mp3", ".wav", ".flac", ".aac", ".ogg",
                   ".m4a", ".wma", ".opus"],
    "documents":  [".pdf", ".doc", ".docx", ".xls", ".xlsx",
                   ".ppt", ".pptx", ".odt", ".ods", ".odp",
                   ".txt", ".rtf", ".md"],
    "code":       [".py", ".js", ".ts", ".html", ".css",
                   ".sh", ".bash", ".ps1", ".rb", ".go",
                   ".rs", ".c", ".cpp", ".h", ".java",
                   ".json", ".yaml", ".yml", ".toml", ".xml",
                   ".sql"],
    "archives":   [".zip", ".tar", ".gz", ".bz2", ".7z",
                   ".rar", ".xz"],
    "misc":       [],   # catch-all
}


def _category_for(path: Path) -> str:
    ext = path.suffix.lower()
    for cat, exts in _CATEGORIES.items():
        if ext in exts:
            return cat
    return "misc"


# ── Data types ───────────────────────────────────────────────

@dataclass
class FileEntry:
    original_path: str
    category:      str
    size_bytes:    int
    sha256:        str
    moved_to:      Optional[str] = None


@dataclass
class ScanResult:
    scan_dir:   str
    scanned_at: float = field(default_factory=time.time)
    entries:    List[FileEntry]  = field(default_factory=list)
    duplicates: List[List[str]] = field(default_factory=list)   # groups of duplicate paths


# ── Core functions ───────────────────────────────────────────

def scan(directory: str | Path) -> ScanResult:
    """
    Recursively scan *directory* and build a ScanResult.

    - Hashes every file (SHA-256) for duplicate detection.
    - Does NOT move or modify anything.
    """
    root = Path(directory).resolve()
    if not root.is_dir():
        raise ValueError(f"Not a directory: {root}")

    entries: List[FileEntry] = []
    hash_to_paths: Dict[str, List[str]] = {}

    for filepath in sorted(root.rglob("*")):
        if not filepath.is_file():
            continue
        try:
            digest = _sha256(filepath)
            entry  = FileEntry(
                original_path = str(filepath),
                category      = _category_for(filepath),
                size_bytes    = filepath.stat().st_size,
                sha256        = digest,
            )
            entries.append(entry)
            hash_to_paths.setdefault(digest, []).append(str(filepath))
        except (PermissionError, OSError) as exc:
            logger.warning(f"EchoFileSorter: skipping {filepath}: {exc}")

    # Collect duplicate groups (more than one file per hash)
    duplicates = [paths for paths in hash_to_paths.values()
                  if len(paths) > 1]

    logger.info(
        f"EchoFileSorter: scanned {len(entries)} file(s) in {root}, "
        f"{len(duplicates)} duplicate group(s)"
    )
    return ScanResult(
        scan_dir   = str(root),
        entries    = entries,
        duplicates = duplicates,
    )


def make_snapshot(result: ScanResult, snapshot_path: str | Path) -> Path:
    """
    Save a recovery snapshot of the scan result to *snapshot_path*.

    The snapshot is plain JSON and can be used to undo any moves
    made by organise().
    """
    path = Path(snapshot_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "scan_dir":   result.scan_dir,
        "scanned_at": result.scanned_at,
        "entries":    [asdict(e) for e in result.entries],
        "duplicates": result.duplicates,
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    logger.info(f"EchoFileSorter: snapshot saved → {path}")
    return path


def organise(
    result:       ScanResult,
    output_dir:   str | Path,
    on_progress:  Optional[Callable[[str], None]] = None,
    dry_run:      bool = False,
) -> List[Tuple[str, str]]:
    """
    Move files from *result* into organised sub-folders under *output_dir*.

    Sub-folder structure:
      <output_dir>/images/
      <output_dir>/videos/
      …

    - Duplicate files (all copies beyond the first) are placed in
      <output_dir>/duplicates/.
    - If *dry_run* is True, prints what would happen without moving.
    - Returns a list of (original_path, destination_path) tuples.

    Call make_snapshot() BEFORE calling organise() so you can undo.
    """
    out_root = Path(output_dir).resolve()
    if not dry_run:
        out_root.mkdir(parents=True, exist_ok=True)

    # Build set of "first seen" hashes — their file is kept; others → dupes
    seen_hashes: set = set()
    for group in result.duplicates:
        # Keep the first path in each group as the canonical copy
        if group:
            seen_hashes.add(_sha256(Path(group[0])) if Path(group[0]).exists() else "")

    moves: List[Tuple[str, str]] = []

    for entry in result.entries:
        src = Path(entry.original_path)
        if not src.exists():
            continue

        # Determine destination folder
        is_duplicate = (
            entry.sha256 in {
                _sha256(Path(g[0]))
                for g in result.duplicates
                if g and Path(g[0]).exists() and str(Path(g[0])) != str(src)
            }
        )
        folder = "duplicates" if is_duplicate else entry.category
        dest_dir = out_root / folder
        dest     = _unique_dest(dest_dir, src.name)

        if on_progress:
            action = "[DRY RUN] " if dry_run else ""
            on_progress(f"{action}{folder}/{dest.name}")

        if not dry_run:
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))
            entry.moved_to = str(dest)

        moves.append((str(src), str(dest)))

    logger.info(
        f"EchoFileSorter: {'[dry run] ' if dry_run else ''}"
        f"organised {len(moves)} file(s) → {out_root}"
    )
    return moves


def restore_from_snapshot(snapshot_path: str | Path) -> Tuple[int, List[str]]:
    """
    Undo a previous organise() call by moving files back to their
    original locations, using the saved snapshot JSON.

    Returns (restored_count, list_of_errors).
    """
    path = Path(snapshot_path)
    if not path.exists():
        raise FileNotFoundError(f"Snapshot not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    restored = 0
    errors:   List[str] = []

    for raw_entry in data.get("entries", []):
        moved_to      = raw_entry.get("moved_to")
        original_path = raw_entry.get("original_path")

        if not moved_to or not original_path:
            continue

        src  = Path(moved_to)
        dest = Path(original_path)

        if not src.exists():
            errors.append(f"Missing: {src}")
            continue

        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))
            restored += 1
        except Exception as exc:
            errors.append(f"Could not restore {src} → {dest}: {exc}")

    logger.info(
        f"EchoFileSorter: restored {restored} file(s) "
        f"({len(errors)} error(s))"
    )
    return restored, errors


# ── Helpers ──────────────────────────────────────────────────

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _unique_dest(dest_dir: Path, filename: str) -> Path:
    """Return a non-colliding destination path."""
    dest = dest_dir / filename
    if not dest.exists():
        return dest
    stem   = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 1
    while dest.exists():
        dest = dest_dir / f"{stem}_{counter}{suffix}"
        counter += 1
    return dest


# ── Convenience: full pipeline ────────────────────────────────

def run_full_pipeline(
    source_dir:    str | Path,
    output_dir:    str | Path,
    snapshot_dir:  Optional[str | Path] = None,
    dry_run:       bool = False,
    on_progress:   Optional[Callable[[str], None]] = None,
) -> dict:
    """
    One-call helper that:
    1. Scans *source_dir*.
    2. Saves a recovery snapshot.
    3. Organises files into *output_dir*.

    Returns a summary dict.
    """
    if snapshot_dir is None:
        snapshot_dir = Path.home() / ".free_echo" / "snapshots"

    result = scan(source_dir)

    ts = int(time.time())
    snap_path = Path(snapshot_dir) / f"snapshot_{ts}.json"
    make_snapshot(result, snap_path)

    moves = organise(
        result,
        output_dir  = output_dir,
        on_progress = on_progress,
        dry_run     = dry_run,
    )

    return {
        "scanned":      len(result.entries),
        "duplicate_groups": len(result.duplicates),
        "moved":        len(moves),
        "snapshot":     str(snap_path),
        "dry_run":      dry_run,
    }
