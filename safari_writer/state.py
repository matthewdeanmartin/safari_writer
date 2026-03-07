"""Application-level state shared across screens."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import TYPE_CHECKING

__all__ = ["AppState", "GlobalFormat"]

if TYPE_CHECKING:
    from safari_writer.mail_merge_db import MailMergeDB


@dataclass
class GlobalFormat:
    """Master document layout settings (Global Format screen parameters)."""
    top_margin: int = 12        # T: half-lines from top edge
    bottom_margin: int = 12     # B: half-lines from bottom edge
    left_margin: int = 10       # L: character spaces from left
    right_margin: int = 70      # R: character spaces from left
    line_spacing: int = 2       # S: half-lines (2=single, 4=double, 6=triple)
    para_spacing: int = 2       # D: half-lines between paragraphs
    col2_left: int = 8          # M: 2nd column left margin
    col2_right: int = 70        # N: 2nd column right margin
    type_font: int = 1          # G: 1=pica, 2=condensed, 3=proportional, 6=elite
    para_indent: int = 5        # I: spaces to indent first line of paragraph
    justification: int = 0      # J: 0=ragged right, 1=justified
    page_number_start: int = 1  # Q: starting page number
    page_length: int = 132      # Y: half-lines per page
    page_wait: int = 0          # W: 0=off, 1=pause between pages

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
    insert_mode: bool = True        # True=Insert, False=Type-over
    caps_mode: bool = False         # True=Uppercase lock
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

    @property
    def bytes_free(self) -> int:
        """Available disk space on the volume containing the working directory."""
        import shutil
        import os
        return shutil.disk_usage(os.getcwd()).free
