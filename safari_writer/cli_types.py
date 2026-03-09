"""Shared CLI request types."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

__all__ = ["StartupRequest"]


@dataclass(frozen=True)
class StartupRequest:
    """Describe the initial TUI destination selected by the CLI."""

    destination: str = "menu"
    document_path: Path | None = None
    mail_merge_database_path: Path | None = None
    proofreader_mode: str | None = None
    mail_merge_mode: str | None = None
    print_target: str | None = None
    cursor_line: int | None = None
    cursor_column: int | None = None
    read_only: bool = False
    index_path: Path | None = None
    safari_dos_path: Path | None = None
    safari_repl_path: Path | None = None
    personal_dict_paths: tuple[Path, ...] = field(default_factory=tuple)
