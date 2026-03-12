"""Autosave / backup engine for Safari Writer.

Backups are written to ~/.config/safari_writer/backups/ as plain .sfw files.
Each backup captures the in-memory buffer, the original filename (if any),
and a timestamp.  Empty (whitespace-only) documents are never backed up.

Public API
----------
backup_dir()          -> Path
list_backups()        -> list[BackupMeta]
write_backup(state)   -> Path | None   (returns path, or None if skipped)
delete_backup(path)   -> None
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from safari_writer.state import AppState

__all__ = [
    "BackupMeta",
    "backup_dir",
    "list_backups",
    "write_backup",
    "delete_backup",
]

# Backup interval used by the app (seconds)
BACKUP_INTERVAL_SECONDS = 60

_SLUG_RE = re.compile(r"[^a-zA-Z0-9_.-]")


def backup_dir() -> Path:
    """Return (and create) the backup directory under the config root."""
    d = Path.home() / ".config" / "safari_writer" / "backups"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _buffer_is_empty(buffer: list[str]) -> bool:
    return not any(line.strip() for line in buffer)


def _slug(filename: str) -> str:
    """Turn an arbitrary path string into a safe short filename component."""
    if not filename:
        return "untitled"
    stem = Path(filename).stem or "untitled"
    return _SLUG_RE.sub("_", stem)[:40]


def write_backup(state: "AppState") -> Path | None:
    """Write a backup for *state*.

    Returns the backup path, or None if the document was empty / not modified.
    Only writes when the buffer has non-whitespace content.
    """
    if _buffer_is_empty(state.buffer):
        return None

    bdir = backup_dir()
    slug = _slug(state.filename)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = bdir / f"{slug}_{ts}.sfw"

    # Serialize buffer to plain text (no control-char encoding needed for
    # recovery purposes — readability wins).
    content = "\n".join(state.buffer)

    # Write a tiny JSON sidecar alongside the .sfw so we can restore metadata.
    meta = {
        "original_filename": state.filename,
        "backup_time": datetime.now().isoformat(),
        "slug": slug,
    }
    meta_path = backup_path.with_suffix(".json")

    backup_path.write_text(content, encoding="utf-8")
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return backup_path


@dataclass
class BackupMeta:
    """Describes one backup entry in the browser."""

    path: Path
    original_filename: str
    backup_time: datetime
    slug: str

    @property
    def display_name(self) -> str:
        if self.original_filename:
            return Path(self.original_filename).name
        return self.slug

    @property
    def time_str(self) -> str:
        return self.backup_time.strftime("%Y-%m-%d %H:%M:%S")


def _load_meta(meta_path: Path) -> BackupMeta | None:
    try:
        data = json.loads(meta_path.read_text(encoding="utf-8"))
        sfw_path = meta_path.with_suffix(".sfw")
        if not sfw_path.exists():
            return None
        bt_raw = data.get("backup_time", "")
        try:
            bt = datetime.fromisoformat(bt_raw)
        except (ValueError, TypeError):
            bt = datetime.fromtimestamp(sfw_path.stat().st_mtime)
        return BackupMeta(
            path=sfw_path,
            original_filename=data.get("original_filename", ""),
            backup_time=bt,
            slug=data.get("slug", sfw_path.stem),
        )
    except (OSError, json.JSONDecodeError, KeyError):
        return None


def list_backups() -> list[BackupMeta]:
    """Return all valid backups, newest first."""
    bdir = backup_dir()
    results: list[BackupMeta] = []
    for meta_path in sorted(bdir.glob("*.json"), reverse=True):
        entry = _load_meta(meta_path)
        if entry is not None:
            results.append(entry)
    return results


def delete_backup(path: Path) -> None:
    """Delete an .sfw backup and its sidecar .json."""
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass
    meta = path.with_suffix(".json")
    try:
        meta.unlink(missing_ok=True)
    except OSError:
        pass
