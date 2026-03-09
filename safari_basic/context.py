"""MacroContext — bridges the Safari Basic interpreter to app state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

__all__ = ["MacroContext"]


@dataclass
class MacroContext:
    """State snapshot passed into a macro at invocation time.

    The interpreter reads document/post data from this object and appends
    PRINT output to ``output_lines``.  After the macro finishes the caller
    splices ``output_lines`` into the document buffer (editor) or creates a
    draft post (Fed).
    """

    # --- Document snapshot (read-only inside the macro) ---
    document_lines: list[str] = field(default_factory=list)
    cursor_row: int = 0   # 0-based at invocation
    cursor_col: int = 0

    # Selection bounds — (row, col) or None
    selection_start: tuple[int, int] | None = None
    selection_end: tuple[int, int] | None = None

    # Clipboard text
    clipboard: str = ""

    # Fed post context (None when run from the editor without a post)
    current_post: Any | None = None

    # --- Outputs populated by the interpreter ---
    output_lines: list[str] = field(default_factory=list)

    # --- Helpers ---

    def selected_lines(self) -> list[str]:
        """Return the lines covered by the selection, or [] if none."""
        if self.selection_start is None or self.selection_end is None:
            return []
        sr, _ = self.selection_start
        er, _ = self.selection_end
        if sr > er:
            sr, er = er, sr
        return self.document_lines[sr : er + 1]

    def build_variable_map(self) -> dict[str, object]:
        """Return all macro-visible variables as a flat name→value dict.

        String variables end with ``$``; numeric variables do not.
        Variable names are plain uppercase identifiers (no dots) so that the
        Atari BASIC scanner can parse them as normal tokens.

        Naming conventions (injected into the interpreter):
          DOCLINES    — number of lines in the document
          CURSORROW   — cursor row at invocation (1-based)
          CURSORCOL   — cursor column (1-based)
          SELCOUNT    — number of selected lines
          CLIPBOARD$  — clipboard text
          PAUTHOR$    — post author name
          PHANDLE$    — post @handle
          PDATE$      — post date string
          PTAGS$      — space-joined tags
          PLINES      — number of content lines in the post
          PBOOSTS     — boost count
          PFAVES      — favourite count
          PLINE1$ … PLINE9$  — individual post content lines (up to 9)
          DOC1$ … DOC200$    — individual document lines (injected by runner)
          SEL1$ … SELN$      — selected lines (injected by runner)
        """
        doc = self.document_lines
        m: dict[str, object] = {
            "DOCLINES": float(len(doc)),
            "CURSORROW": float(self.cursor_row + 1),  # 1-based for BASIC
            "CURSORCOL": float(self.cursor_col + 1),
            "SELCOUNT": float(len(self.selected_lines())),
            "CLIPBOARD$": self.clipboard,
        }

        post = self.current_post
        if post is not None:
            m["PAUTHOR$"] = getattr(post, "author", "")
            m["PHANDLE$"] = getattr(post, "handle", "")
            m["PDATE$"] = getattr(post, "posted_at", "")
            content = list(getattr(post, "content_lines", []))
            m["PLINES"] = float(len(content))
            tags = getattr(post, "tags", ())
            m["PTAGS$"] = " ".join(tags)
            m["PBOOSTS"] = float(getattr(post, "boosts", 0))
            m["PFAVES"] = float(getattr(post, "favourites", 0))
            for i, line in enumerate(content[:9], start=1):
                m[f"PLINE{i}$"] = line
            # Pad missing lines with empty string so macros don't error
            for i in range(len(content) + 1, 10):
                m[f"PLINE{i}$"] = ""
        else:
            m["PAUTHOR$"] = ""
            m["PHANDLE$"] = ""
            m["PDATE$"] = ""
            m["PLINES"] = 0.0
            m["PTAGS$"] = ""
            m["PBOOSTS"] = 0.0
            m["PFAVES"] = 0.0
            for i in range(1, 10):
                m[f"PLINE{i}$"] = ""

        return m
