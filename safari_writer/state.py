"""Application-level state shared across screens."""

from dataclasses import dataclass, field


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
        self.__init__()


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
    # Search / replace state
    search_string: str = ""
    replace_string: str = ""
    last_search_row: int = 0
    last_search_col: int = 0

    @property
    def bytes_free(self) -> int:
        """Rough estimate of memory remaining (simulated, 64K ceiling)."""
        used = sum(len(line) for line in self.buffer)
        return max(0, 65536 - used)
