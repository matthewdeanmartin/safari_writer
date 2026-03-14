"""Application-level state shared across screens."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import TYPE_CHECKING

from safari_writer.file_types import (
    FileProfile,
    HighlightProfile,
    StorageMode,
    resolve_file_profile,
)

__all__ = ["AppState", "GlobalFormat"]

if TYPE_CHECKING:
    from safari_writer.mail_merge_db import MailMergeDB


@dataclass
class GlobalFormat:
    """Master document layout settings (Global Format screen parameters)."""

    top_margin: int = 12  # T: half-lines from top edge
    bottom_margin: int = 12  # B: half-lines from bottom edge
    left_margin: int = 10  # L: character spaces from left
    right_margin: int = 70  # R: character spaces from left
    line_spacing: int = 2  # S: half-lines (2=single, 4=double, 6=triple)
    para_spacing: int = 2  # D: half-lines between paragraphs
    col2_left: int = 8  # M: 2nd column left margin
    col2_right: int = 70  # N: 2nd column right margin
    type_font: int = 1  # G: 1=pica, 2=condensed, 3=proportional, 6=elite
    para_indent: int = 5  # I: spaces to indent first line of paragraph
    justification: int = 0  # J: 0=ragged right, 1=justified
    page_number_start: int = 1  # Q: starting page number
    page_length: int = 132  # Y: half-lines per page
    page_wait: int = 0  # W: 0=off, 1=pause between pages

    def reset_defaults(self) -> None:
        defaults = GlobalFormat()
        for data_field in fields(self):
            setattr(self, data_field.name, getattr(defaults, data_field.name))


@dataclass
class AppState:
    """Top-level mutable state for the running application."""

    # Document buffer: list of raw line strings (may contain control char markers)
    buffer: list[str] = field(default_factory=lambda: [""])
    # Cursor position
    cursor_row: int = 0
    cursor_col: int = 0
    # Edit mode
    insert_mode: bool = True  # True=Insert, False=Type-over
    caps_mode: bool = False  # True=Uppercase lock
    # Failsafe (clipboard) buffer
    clipboard: str = ""
    # Last deleted line (for undelete)
    last_deleted_line: str = ""
    # Global format settings
    fmt: GlobalFormat = field(default_factory=GlobalFormat)
    # Current filename
    filename: str = ""
    # Dirty flag
    modified: bool = False
    # Session-kept spellings (Proofreader "Keep This Spelling")
    kept_spellings: set[str] = field(default_factory=set)
    # Selection anchor: (row, col) where the selection started, or None
    selection_anchor: tuple[int, int] | None = None
    # Search / replace state
    search_string: str = ""
    replace_string: str = ""
    last_search_row: int = 0
    last_search_col: int = 0
    mail_merge_db: MailMergeDB | None = None
    # Document language for spellcheck (i18n Level 1)
    doc_language: str = ""
    # Document title (display name without filesystem save)
    doc_title: str = ""
    # File type awareness (spec 10)
    file_profile: FileProfile = field(
        default_factory=lambda: resolve_file_profile("untitled.sfw")
    )
    # Undo stack: list of (buffer_snapshot, cursor_row, cursor_col) tuples
    _undo_stack: list[tuple[list[str], int, int]] = field(
        default_factory=list, repr=False
    )
    UNDO_MAX: int = field(default=50, repr=False)

    @property
    def storage_mode(self) -> StorageMode:
        return self.file_profile.storage_mode

    @property
    def highlight_profile(self) -> HighlightProfile:
        return self.file_profile.highlight_profile

    @property
    def allows_formatting(self) -> bool:
        return self.file_profile.allows_formatting_codes

    def update_file_profile(self) -> None:
        """Re-resolve file profile from current filename."""
        name = self.filename or "untitled.sfw"
        self.file_profile = resolve_file_profile(name)

    def push_undo(self) -> None:
        """Snapshot current buffer state onto the undo stack."""
        snapshot = ([line for line in self.buffer], self.cursor_row, self.cursor_col)
        self._undo_stack.append(snapshot)
        if len(self._undo_stack) > self.UNDO_MAX:
            self._undo_stack.pop(0)

    def pop_undo(self) -> bool:
        """Restore previous state from the undo stack. Returns True if performed."""
        if not self._undo_stack:
            return False
        buf, row, col = self._undo_stack.pop()
        self.buffer = buf
        self.cursor_row = min(row, len(self.buffer) - 1)
        self.cursor_col = min(col, len(self.buffer[self.cursor_row]))
        self.modified = True
        return True

    def clear_undo(self) -> None:
        """Clear the undo stack (e.g. after creating a new document)."""
        self._undo_stack.clear()

    @property
    def bytes_free(self) -> int:
        """Available disk space on the volume containing the working directory."""
        import os
        import shutil

        return shutil.disk_usage(os.getcwd()).free
