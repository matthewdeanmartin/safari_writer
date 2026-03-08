"""Editor screen — the main text editing workspace."""

import logging
import os
from pathlib import Path

from textual.app import ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widgets import Static
from textual.widget import Widget
from textual import events
from textual.containers import Container

from safari_writer.file_types import HighlightProfile, StorageMode
from safari_writer.state import AppState
from safari_writer.syntax_highlight import create_highlighter

_log = logging.getLogger("safari_writer.editor")
if os.environ.get("SAFARI_LOG"):
    _log.setLevel(logging.DEBUG)
    if not _log.handlers:
        _fh = logging.FileHandler(
            Path(__file__).resolve().parent.parent / "debug.log", mode="a"
        )
        _fh.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        _log.addHandler(_fh)
else:
    _log.addHandler(logging.NullHandler())

# Control character display symbols embedded in the buffer
CTRL_BOLD = "\x01"  # bold toggle marker
CTRL_UNDERLINE = "\x02"  # underline toggle
CTRL_CENTER = "\x03"  # center line
CTRL_RIGHT = "\x04"  # flush right
CTRL_ELONGATE = "\x05"  # elongated (double-width) toggle
CTRL_SUPER = "\x06"  # superscript
CTRL_SUB = "\x07"  # subscript
CTRL_PARA = "\x10"  # paragraph mark (non-printing indent)
CTRL_MERGE = "\x11"  # mail merge @ marker
CTRL_HEADER = "\x12"  # header line marker
CTRL_FOOTER = "\x13"  # footer line marker
CTRL_HEADING = "\x14"  # section heading marker (followed by level digit 1-9)
CTRL_EJECT = "\x15"  # hard page break / page eject
CTRL_CHAIN = "\x16"  # chain print file (followed by filename)
CTRL_FORM = "\x17"  # form printing blank

# Human-readable glyphs for control chars (shown in editor, not printed)
CTRL_GLYPHS = {
    CTRL_BOLD: "←",
    CTRL_UNDERLINE: "▄",
    CTRL_CENTER: "↔",
    CTRL_RIGHT: "→→",
    CTRL_ELONGATE: "E",
    CTRL_SUPER: "↑",
    CTRL_SUB: "↓",
    CTRL_PARA: "¶",
    CTRL_MERGE: "@",
    CTRL_HEADER: "H:",
    CTRL_FOOTER: "F:",
    CTRL_HEADING: "H",  # followed by level digit in buffer
    CTRL_EJECT: "↡",
    CTRL_CHAIN: "»",
    CTRL_FORM: "_",
}

# These markers toggle a rendering state — text after them is styled differently
TOGGLE_MARKERS = {CTRL_BOLD, CTRL_UNDERLINE, CTRL_ELONGATE, CTRL_SUPER, CTRL_SUB}

EDITOR_CSS = """
EditorScreen {
    background: $surface;
}

#tab-bar {
    dock: top;
    height: 1;
    background: $surface;
    color: $accent;
    padding: 0 1;
}

EditorArea {
    height: 1fr;
    background: $surface;
    overflow-y: auto;
}

#message-bar {
    height: 1;
    background: $accent;
    color: $text;
    text-style: bold;
    padding: 0 1;
}

#status-bar {
    height: 1;
    background: $secondary;
    color: $text;
    padding: 0 1;
}

#help-bar {
    height: 1;
    background: $primary;
    color: $text;
    padding: 0 1;
}

#editor-footer {
    dock: bottom;
    height: 3;
    layout: vertical;
}

HelpScreen {
    align: center middle;
}

#help-dialog {
    width: 72;
    height: auto;
    max-height: 90%;
    border: solid $primary;
    background: $surface;
    padding: 1 2;
}

#help-title {
    text-align: center;
    text-style: bold;
    color: $accent;
    margin-bottom: 1;
}

#help-content {
    color: $text;
}

#help-footer {
    text-align: center;
    color: $primary;
    margin-top: 1;
}
"""

HELP_TEXT = (
    "^X Cut  ^C Copy  ^V Paste  ^F Find  ^B Bold  ^U Underline  "
    "^E Center  ^G Elongate  F1 Help  Esc Menu"
)
EDITOR_RESERVED_LINES = 4

HELP_CONTENT = """\
NAVIGATION
  Arrow keys              Move cursor (clears selection)
  Shift+Arrow             Extend selection
  Shift+Home/End          Extend selection to line start/end
  Shift+Ctrl+Home/End     Extend selection to file start/end
  Ctrl+Left/Right         Jump word
  Home / End              Line start / end
  Ctrl+Home/End           Top / bottom of file
  Page Up/Down            Scroll page
  Tab                     Jump to next tab stop
  Ctrl+T                  Toggle tab stop at cursor column
  Ctrl+Shift+T            Clear all tab stops

EDITING
  Insert                  Toggle Insert / Type-over mode
  Caps Lock               Toggle Uppercase / Lowercase mode
  Shift+F3                Toggle case of character at cursor
  Ctrl+M                  Insert paragraph mark (¶)
  Enter                   New line (hard carriage return)

DELETION
  Backspace               Delete char before cursor (or selection)
  Delete                  Delete char at cursor (or selection)
  Shift+Delete            Delete to end of line
  Ctrl+Z                  Undo
  Ctrl+Shift+Delete       Delete to end of file

BLOCK OPERATIONS
  Ctrl+X                  Cut selection (or current line) to clipboard
  Ctrl+C                  Copy selection (or current line) to clipboard
  Ctrl+V                  Paste clipboard at cursor (replaces selection)
  Alt+W                   Word count (selection or whole file)
  Alt+A                   Alphabetize selected lines (or all lines)

SEARCH & REPLACE
  Ctrl+F                  Find (prompt for search string)
  F3                      Find next occurrence
  Alt+H                   Set replacement string
  Alt+N                   Replace current occurrence, find next
  Alt+R                   Global replace to end of file

INLINE FORMATTING (markers visible in editor, invisible when printed)
  Ctrl+B                  Bold toggle          ← marker, bold text
  Ctrl+U                  Underline toggle     ▄ marker, inverse-video text
  Ctrl+G                  Elongated toggle     E marker, dim text
  Ctrl+[                  Superscript toggle   ↑ marker, bright text
  Ctrl+]                  Subscript toggle     ↓ marker, bright text
  Ctrl+E                  Center line          ↔ marker at line start
  Ctrl+R                  Flush right          →→ marker at line start
  Ctrl+M                  Paragraph indent     ¶ marker
  Alt+M                   Mail merge field     @ marker

DOCUMENT STRUCTURE
  Ctrl+Shift+H            Insert header line   (H: marker, own line)
  Ctrl+Shift+F            Insert footer line   (F: marker, own line)
  Ctrl+Shift+S            Insert section heading  (H + level 1-9)
  Ctrl+Shift+E            Page eject / hard page break  (↡ marker)
  Ctrl+Shift+C            Chain print file     (» marker + filename)
  Alt+F                   Form printing blank  (_ marker, prompts at print)

OTHER
  Ctrl+P                  Print / Export menu
  F1 / ?                  Show this help screen
  Escape                  Return to Main Menu\
"""

# Default tab stop every 5 columns (16 stops shown in header)
DEFAULT_TAB_STOPS = set(range(5, 81, 5))


# ---------------------------------------------------------------------------
# Helpers: flat-position ↔ (row, col) conversion
# ---------------------------------------------------------------------------


def _to_flat(buffer: list[str], row: int, col: int) -> int:
    """Convert (row, col) to a flat character position in the joined buffer."""
    return sum(len(buffer[r]) + 1 for r in range(row)) + col


def _from_flat(buffer: list[str], pos: int) -> tuple[int, int]:
    """Convert a flat position back to (row, col)."""
    for i, line in enumerate(buffer):
        if pos <= len(line):
            return i, pos
        pos -= len(line) + 1
    last = len(buffer) - 1
    return last, len(buffer[last])


def _selection_range(
    buffer: list[str],
    anchor: tuple[int, int],
    cursor: tuple[int, int],
) -> tuple[tuple[int, int], tuple[int, int]]:
    """Return (start, end) in (row, col) order, start <= end."""
    a = _to_flat(buffer, *anchor)
    c = _to_flat(buffer, *cursor)
    if a <= c:
        return anchor, cursor
    return cursor, anchor


# ---------------------------------------------------------------------------
# Help overlay
# ---------------------------------------------------------------------------


class HelpScreen(ModalScreen):
    """Full key-command reference, shown as a modal overlay."""

    def compose(self) -> ComposeResult:
        from textual.containers import Container

        with Container(id="help-dialog"):
            yield Static("=== SAFARI WRITER — KEY COMMANDS ===", id="help-title")
            yield Static(HELP_CONTENT, id="help-content")
            yield Static("Press any key to close", id="help-footer")

    def on_key(self, event: events.Key) -> None:
        self.dismiss()


# ---------------------------------------------------------------------------
# Editor area widget
# ---------------------------------------------------------------------------


class EditorArea(Widget, can_focus=True):
    """The main text editing widget."""

    from textual.binding import Binding

    BINDINGS = [
        Binding("ctrl+c", "editor_copy", "Copy", show=False, priority=True),
        Binding("ctrl+v", "editor_paste", "Paste", show=False, priority=True),
        Binding("ctrl+x", "editor_cut", "Cut", show=False, priority=True),
    ]

    def __init__(self, state: AppState) -> None:
        super().__init__(id="editor-area")
        self.state = state
        self.tab_stops: set[int] = set(DEFAULT_TAB_STOPS)
        self._search_active = False
        self._replace_active = False
        self._heading_active = False
        self._chain_active = False
        self._input_buffer = ""
        self._highlighter = create_highlighter(state.file_profile)
        self._last_undo_action: str = ""

    def update_highlighter(self) -> None:
        """Re-create the highlighter when the file profile changes."""
        self._highlighter = create_highlighter(self.state.file_profile)
        self._highlighter.invalidate()

    def _push_undo(self, action: str) -> None:
        """Push an undo snapshot if the action type changed (coalesces typing)."""
        if action != self._last_undo_action:
            self.state.push_undo()
            self._last_undo_action = action

    def _undo(self) -> None:
        if self.state.pop_undo():
            self._last_undo_action = ""
            self.screen.set_message("Undo")  # type: ignore[attr-defined]
        else:
            self.screen.set_message("Nothing to undo")  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Selection helpers
    # ------------------------------------------------------------------

    def _has_selection(self) -> bool:
        s = self.state
        return s.selection_anchor is not None and s.selection_anchor != (
            s.cursor_row,
            s.cursor_col,
        )

    def _clear_selection(self) -> None:
        self.state.selection_anchor = None

    def _begin_selection(self) -> None:
        """Start a selection anchored at the current cursor position."""
        s = self.state
        if s.selection_anchor is None:
            s.selection_anchor = (s.cursor_row, s.cursor_col)

    def _selected_text(self) -> str:
        """Return the selected text as a single string (newlines between lines)."""
        s = self.state
        if not self._has_selection():
            return ""
        anchor = s.selection_anchor
        if anchor is None:
            return ""
        start, end = _selection_range(s.buffer, anchor, (s.cursor_row, s.cursor_col))
        sr, sc = start
        er, ec = end
        if sr == er:
            return s.buffer[sr][sc:ec]
        parts = [s.buffer[sr][sc:]]
        for r in range(sr + 1, er):
            parts.append(s.buffer[r])
        parts.append(s.buffer[er][:ec])
        return "\n".join(parts)

    def _delete_selection(self) -> None:
        """Delete the selected region, leaving cursor at the start."""
        s = self.state
        if not self._has_selection():
            return
        anchor = s.selection_anchor
        if anchor is None:
            return
        start, end = _selection_range(s.buffer, anchor, (s.cursor_row, s.cursor_col))
        sr, sc = start
        er, ec = end
        if sr == er:
            line = s.buffer[sr]
            s.buffer[sr] = line[:sc] + line[ec:]
        else:
            head = s.buffer[sr][:sc]
            tail = s.buffer[er][ec:]
            s.buffer[sr] = head + tail
            del s.buffer[sr + 1 : er + 1]
        s.cursor_row, s.cursor_col = sr, sc
        s.selection_anchor = None
        s.modified = True

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self) -> str:
        s = self.state
        start: tuple[int, int] | None
        end: tuple[int, int] | None
        if self._has_selection():
            anchor = s.selection_anchor
            if anchor is None:
                start = end = None
            else:
                start, end = _selection_range(
                    s.buffer, anchor, (s.cursor_row, s.cursor_col)
                )
        else:
            start = end = None

        # For non-SFW files with syntax highlighting, get highlighted lines
        use_syntax_hl = (
            s.file_profile.highlight_profile != HighlightProfile.SAFARI_WRITER
            and s.file_profile.highlight_profile != HighlightProfile.PLAIN_TEXT
        )
        if use_syntax_hl:
            self._highlighter.invalidate()
            highlighted = self._highlighter.highlight_buffer(s.buffer)
        else:
            highlighted = None

        # Carry toggle state across lines (bold/underline/etc. can span lines)
        fmt_state: dict[str, bool] = {
            CTRL_BOLD: False,
            CTRL_UNDERLINE: False,
            CTRL_ELONGATE: False,
            CTRL_SUPER: False,
            CTRL_SUB: False,
        }

        lines = []
        for row, line in enumerate(s.buffer):
            hl_text = (
                highlighted[row] if highlighted and row < len(highlighted) else None
            )
            rendered, fmt_state = self._render_line(
                line, row, start, end, fmt_state, hl_text
            )
            lines.append(rendered)
        return "\n".join(lines)

    def _render_line(
        self,
        line: str,
        row: int,
        sel_start: tuple[int, int] | None,
        sel_end: tuple[int, int] | None,
        fmt_state: dict[str, bool],
        hl_text: object = None,
    ) -> tuple[str, dict[str, bool]]:
        """Render one buffer line, applying format state and returning updated state.

        If *hl_text* is a rich.text.Text with syntax highlighting spans, those
        styles are used as the base layer for non-SFW files. Cursor and selection
        are overlaid on top.
        """
        s = self.state

        # For syntax-highlighted plain files, build Rich markup from the
        # highlighted Text object while overlaying cursor/selection.
        if hl_text is not None and not s.allows_formatting:
            return self._render_highlighted_line(
                hl_text, line, row, sel_start, sel_end
            ), fmt_state

        out = ""
        for col, ch in enumerate(line):
            is_cursor = row == s.cursor_row and col == s.cursor_col
            in_sel = self._in_selection(row, col, sel_start, sel_end)

            if ch in TOGGLE_MARKERS:
                # Toggle the format state and emit the glyph as a marker
                fmt_state[ch] = not fmt_state[ch]
                glyph = CTRL_GLYPHS[ch]
                if is_cursor:
                    out += f"[reverse]{glyph}[/reverse]"
                elif in_sel:
                    out += f"[on blue]{glyph}[/on blue]"
                else:
                    out += f"[dim]{glyph}[/dim]"
            else:
                glyph = CTRL_GLYPHS.get(ch, ch)
                # Escape Rich markup characters in literal text
                if ch not in CTRL_GLYPHS and ch == "[":
                    glyph = "\\["
                # Build markup based on active format state
                markup = self._format_markup(fmt_state, is_cursor, in_sel)
                if markup:
                    out += f"[{markup}]{glyph}[/{markup}]"
                else:
                    out += glyph

        # Cursor at end of line
        if row == s.cursor_row and s.cursor_col >= len(line):
            out += "[reverse] [/reverse]"

        return out, fmt_state

    def _render_highlighted_line(
        self,
        hl_text: object,
        line: str,
        row: int,
        sel_start: tuple[int, int] | None,
        sel_end: tuple[int, int] | None,
    ) -> str:
        """Render a syntax-highlighted line with cursor/selection overlay.

        Converts the rich.text.Text spans into Rich markup strings, overlaying
        cursor and selection styles.
        """
        from rich.text import Text as RichText

        s = self.state
        out = ""

        if not isinstance(hl_text, RichText):
            # Fallback: render as plain
            for col, ch in enumerate(line):
                is_cursor = row == s.cursor_row and col == s.cursor_col
                in_sel = self._in_selection(row, col, sel_start, sel_end)
                glyph = ch if ch != "[" else "\\["
                if is_cursor:
                    out += f"[reverse]{glyph}[/reverse]"
                elif in_sel:
                    out += f"[on blue]{glyph}[/on blue]"
                else:
                    out += glyph
            if row == s.cursor_row and s.cursor_col >= len(line):
                out += "[reverse] [/reverse]"
            return out

        # Build a per-character style map from the highlighted Text spans
        char_styles: list[str] = [""] * len(line)
        for span in hl_text._spans:
            style_str = str(span.style) if span.style else ""
            if not style_str or style_str == "none":
                continue
            for i in range(span.start, min(span.end, len(line))):
                char_styles[i] = style_str

        for col, ch in enumerate(line):
            is_cursor = row == s.cursor_row and col == s.cursor_col
            in_sel = self._in_selection(row, col, sel_start, sel_end)
            glyph = ch if ch != "[" else "\\["

            if is_cursor:
                out += f"[reverse]{glyph}[/reverse]"
            elif in_sel:
                out += f"[on blue]{glyph}[/on blue]"
            elif char_styles[col]:
                out += f"[{char_styles[col]}]{glyph}[/{char_styles[col]}]"
            else:
                out += glyph

        if row == s.cursor_row and s.cursor_col >= len(line):
            out += "[reverse] [/reverse]"

        return out

    def _format_markup(
        self,
        fmt: dict[str, bool],
        is_cursor: bool,
        in_sel: bool,
    ) -> str:
        """Return a Rich markup tag string for the current format state."""
        if is_cursor:
            return "reverse"
        if in_sel:
            return "on blue"
        parts = []
        if fmt.get(CTRL_BOLD):
            parts.append("bold")
        if fmt.get(CTRL_UNDERLINE):
            parts.append("reverse")  # inverse video = underline in TUI
        if fmt.get(CTRL_ELONGATE):
            parts.append("dim")
        if fmt.get(CTRL_SUPER) or fmt.get(CTRL_SUB):
            parts.append("bright_white")
        return " ".join(parts)

    def _in_selection(
        self,
        row: int,
        col: int,
        sel_start: tuple[int, int] | None,
        sel_end: tuple[int, int] | None,
    ) -> bool:
        if sel_start is None or sel_end is None:
            return False
        sr, sc = sel_start
        er, ec = sel_end
        if row < sr or row > er:
            return False
        if row == sr and col < sc:
            return False
        if row == er and col >= ec:
            return False
        return True

    # ------------------------------------------------------------------
    # Key handling
    # ------------------------------------------------------------------

    def on_key(self, event: events.Key) -> None:
        _log.debug("on_key: key=%r char=%r", event.key, event.character)
        if (
            self._search_active
            or self._replace_active
            or self._heading_active
            or self._chain_active
        ):
            self._handle_prompt_key(event)
            return

        s = self.state
        key = event.key.lower()
        handled = True

        # Help
        if key == "f1":
            self.app.push_screen(HelpScreen())

        # --- Selection-extending navigation ---
        elif key == "shift+left":
            self._begin_selection()
            self._move_left()
        elif key == "shift+right":
            self._begin_selection()
            self._move_right()
        elif key == "shift+up":
            self._begin_selection()
            self._move_up()
        elif key == "shift+down":
            self._begin_selection()
            self._move_down()
        elif key == "shift+home":
            self._begin_selection()
            s.cursor_col = 0
        elif key == "shift+end":
            self._begin_selection()
            s.cursor_col = len(s.buffer[s.cursor_row])
        elif key == "shift+ctrl+home":
            self._begin_selection()
            s.cursor_row, s.cursor_col = 0, 0
        elif key == "shift+ctrl+end":
            self._begin_selection()
            s.cursor_row = len(s.buffer) - 1
            s.cursor_col = len(s.buffer[s.cursor_row])

        # --- Plain navigation (clears selection) ---
        elif key == "up":
            self._clear_selection()
            self._move_up()
        elif key == "down":
            self._clear_selection()
            self._move_down()
        elif key == "left":
            self._clear_selection()
            self._move_left()
        elif key == "right":
            self._clear_selection()
            self._move_right()
        elif key == "ctrl+left":
            self._clear_selection()
            self._word_jump(-1)
        elif key == "ctrl+right":
            self._clear_selection()
            self._word_jump(1)
        elif key == "home":
            self._clear_selection()
            s.cursor_col = 0
        elif key == "end":
            self._clear_selection()
            s.cursor_col = len(s.buffer[s.cursor_row])
        elif key == "ctrl+home":
            self._clear_selection()
            s.cursor_row, s.cursor_col = 0, 0
        elif key == "ctrl+end":
            self._clear_selection()
            s.cursor_row = len(s.buffer) - 1
            s.cursor_col = len(s.buffer[s.cursor_row])
        elif key == "pageup":
            self._clear_selection()
            self._page_scroll(-1)
        elif key == "pagedown":
            self._clear_selection()
            self._page_scroll(1)
        elif key == "tab":
            self._clear_selection()
            self._tab_forward()
        elif key == "ctrl+t":
            self._clear_selection()
            self._tab_toggle()
        elif key == "ctrl+shift+t":
            self._clear_selection()
            self._tab_clear_all()

        # Enter — split line
        elif key == "enter":
            self._push_undo("enter")
            if self._has_selection():
                self._delete_selection()
            self._insert_newline()

        # Mode toggles
        elif key == "insert":
            s.insert_mode = not s.insert_mode
            self._update_status()
        elif key == "caps_lock":
            s.caps_mode = not s.caps_mode
            self._update_status()
        elif key == "shift+f3":
            self._clear_selection()
            self._toggle_case_at_cursor()

        # Deletion
        elif key == "backspace":
            self._push_undo("backspace")
            if self._has_selection():
                self._delete_selection()
            else:
                self._backspace()
        elif key == "delete":
            self._push_undo("delete")
            if self._has_selection():
                self._delete_selection()
            else:
                self._delete_char()
        elif key == "shift+delete":
            self._push_undo("delete_eol")
            self._clear_selection()
            self._delete_to_eol()
        elif key == "ctrl+z":
            self._clear_selection()
            self._undo()
        elif key == "ctrl+shift+delete":
            self._push_undo("delete_eof")
            self._clear_selection()
            self._delete_to_eof()

        # Block ops (ctrl+x/c/v handled via BINDINGS with priority=True)
        elif key == "alt+w":
            self._word_count()
        elif key == "alt+a":
            self._push_undo("alphabetize")
            self._alphabetize()

        # Search & replace
        elif key == "ctrl+f":
            self._prompt_search()
        elif key == "f3":
            self._find_next()
        elif key == "alt+h":
            self._prompt_replace()
        elif key == "alt+n":
            self._replace_current_and_find_next()
        elif key == "alt+r":
            self._global_replace()

        # Inline formatting
        elif key == "ctrl+b":
            self._insert_control(CTRL_BOLD)
        elif key == "ctrl+u":
            self._insert_control(CTRL_UNDERLINE)
        elif key == "ctrl+g":
            self._insert_control(CTRL_ELONGATE)
        elif key == "ctrl+left_square_bracket":
            self._insert_control(CTRL_SUPER)
        elif key == "ctrl+right_square_bracket":
            self._insert_control(CTRL_SUB)
        elif key == "ctrl+e":
            self._insert_control(CTRL_CENTER)
        elif key == "ctrl+r":
            self._insert_control(CTRL_RIGHT)
        elif key == "ctrl+m":
            self._insert_control(CTRL_PARA)
        elif key == "alt+m":
            self._insert_control(CTRL_MERGE)
        elif key == "alt+f":
            self._insert_control(CTRL_FORM)

        # Document structure markers
        elif key == "ctrl+shift+h":
            self._insert_structure_marker(CTRL_HEADER)
        elif key == "ctrl+shift+f":
            self._insert_structure_marker(CTRL_FOOTER)
        elif key == "ctrl+shift+s":
            self._prompt_heading()
        elif key == "ctrl+shift+e":
            self._insert_structure_marker(CTRL_EJECT)
        elif key == "ctrl+shift+c":
            self._prompt_chain()

        # Print / Export — delegate to app-level handler
        elif key == "ctrl+p":
            self.app._action_print()  # type: ignore[attr-defined]

        # Exit to main menu
        elif key == "escape":
            self._clear_selection()
            self.app.pop_screen()

        # Printable characters
        elif event.character and event.character.isprintable():
            self._push_undo("type")
            if self._has_selection():
                self._delete_selection()
            if event.character == "@":
                self._insert_control(CTRL_MERGE)
            else:
                self._type_char(event.character)

        else:
            handled = False

        if handled:
            event.stop()
            self.refresh()
            self._update_status()

    def on_paste(self, event: events.Paste) -> None:
        """Terminal sends bracketed paste on Ctrl+V — ignore its text, use internal clipboard."""
        _log.debug(
            "on_paste: ignoring terminal text=%r, using internal clipboard=%r",
            event.text,
            self.state.clipboard,
        )
        event.stop()
        # Ctrl+V arrives as a Paste event, not a Key event, so the binding never fires.
        # Paste from our internal clipboard instead.
        self._paste()
        self.refresh()
        self._update_status()

    # ------------------------------------------------------------------
    # Prompt input handling (search / replace)
    # ------------------------------------------------------------------

    def _prompt_search(self) -> None:
        self._search_active = True
        self._input_buffer = ""
        self.screen.set_message("Find: ")  # type: ignore[attr-defined]

    def _prompt_replace(self) -> None:
        self._replace_active = True
        self._input_buffer = ""
        self.screen.set_message("Replace with: ")  # type: ignore[attr-defined]

    def _handle_prompt_key(self, event: events.Key) -> None:
        key = event.key.lower()

        if key == "escape":
            self._search_active = False
            self._replace_active = False
            self._heading_active = False
            self._chain_active = False
            self._input_buffer = ""
            self.screen.set_message("Cancelled")  # type: ignore[attr-defined]
            event.stop()
            self.refresh()
            return

        if key == "enter":
            if self._search_active:
                self.state.search_string = self._input_buffer
                self._search_active = False
                self.state.last_search_row = 0
                self.state.last_search_col = 0
                if self._find_next():
                    self.screen.set_message(
                        f"Find: {self.state.search_string!r} — F3=next, Alt+H=replace"
                    )  # type: ignore[attr-defined]
            elif self._replace_active:
                self.state.replace_string = self._input_buffer
                self._replace_active = False
                self.screen.set_message(
                    f"Replace: {self.state.replace_string!r} — Alt+N=one, Alt+R=all"
                )  # type: ignore[attr-defined]
            elif self._heading_active:
                self._heading_active = False
                level = self._input_buffer.strip()
                if level and level in "123456789":
                    s = self.state
                    row = s.cursor_row
                    s.buffer.insert(row, CTRL_HEADING + level)
                    s.cursor_row = row + 1
                    s.cursor_col = 0
                    s.modified = True
                    self.screen.set_message(f"Heading level {level} inserted")  # type: ignore[attr-defined]
                else:
                    self.screen.set_message("Cancelled — level must be 1-9")  # type: ignore[attr-defined]
            elif self._chain_active:
                self._chain_active = False
                filename = self._input_buffer.strip()
                if filename:
                    s = self.state
                    s.buffer.append(CTRL_CHAIN + filename)
                    s.cursor_row = len(s.buffer) - 1
                    s.cursor_col = len(s.buffer[s.cursor_row])
                    s.modified = True
                    self.screen.set_message(f"Chain: {filename}")  # type: ignore[attr-defined]
                else:
                    self.screen.set_message("Cancelled")  # type: ignore[attr-defined]
        elif key == "backspace":
            self._input_buffer = self._input_buffer[:-1]
            self.screen.set_message(self._current_prompt() + self._input_buffer + "█")  # type: ignore[attr-defined]
        elif event.character and event.character.isprintable():
            max_len = 1 if self._heading_active else 37
            if len(self._input_buffer) < max_len:
                self._input_buffer += event.character
                self.screen.set_message(
                    self._current_prompt() + self._input_buffer + "█"
                )  # type: ignore[attr-defined]

        event.stop()
        self.refresh()

    def _current_prompt(self) -> str:
        if self._search_active:
            return "Find: "
        if self._replace_active:
            return "Replace with: "
        if self._heading_active:
            return "Heading level (1-9): "
        if self._chain_active:
            return "Chain to file: "
        return ""

    # ------------------------------------------------------------------
    # Search & replace logic
    # ------------------------------------------------------------------

    def _find_next(self, wrap: bool = True) -> bool:
        """Find next occurrence of search string, starting after current cursor."""
        s = self.state
        needle = s.search_string
        if not needle:
            self.screen.set_message("No search string set — press Ctrl+F")  # type: ignore[attr-defined]
            return False

        # Start search AFTER current cursor position
        curr_row, curr_col = s.cursor_row, s.cursor_col
        start_row, start_col = curr_row, curr_col + 1

        # Search from current line (after cursor) to end
        for row in range(start_row, len(s.buffer)):
            line = s.buffer[row]
            col_start = start_col if row == start_row else 0
            idx = self._find_in_line(line, needle, col_start)
            if idx != -1:
                s.cursor_row = row
                s.cursor_col = idx
                s.last_search_row = row
                s.last_search_col = idx
                self.screen.set_message(f"Found: {needle!r}")  # type: ignore[attr-defined]
                return True

        # Wrap to top if enabled
        if wrap:
            for row in range(0, start_row + 1):
                line = s.buffer[row]
                # Stop if we hit original cursor pos
                # col_end = start_col if row == start_row else len(line)
                idx = self._find_in_line(line, needle, 0)
                if idx != -1 and (row < start_row or idx < curr_col):
                    s.cursor_row = row
                    s.cursor_col = idx
                    s.last_search_row = row
                    s.last_search_col = idx
                    self.screen.set_message(f"Found (wrapped): {needle!r}")  # type: ignore[attr-defined]
                    return True

        self.screen.set_message(f"Not found: {needle!r}")  # type: ignore[attr-defined]
        return False

    def _find_in_line(self, line: str, needle: str, start: int = 0) -> int:
        """Find needle in line starting from 'start', supports '?' as wildcard."""
        if "?" not in needle:
            return line.find(needle, start)
        nl, nn = len(line), len(needle)
        for i in range(start, nl - nn + 1):
            if all(needle[j] == "?" or line[i + j] == needle[j] for j in range(nn)):
                return i
        return -1

    def _replace_current_and_find_next(self) -> None:
        """Replace needle at current cursor (if it matches) then find next."""
        self._push_undo("replace")
        s = self.state
        needle = s.search_string
        repl = s.replace_string
        if not needle:
            self.screen.set_message("No search string — press Ctrl+F first")  # type: ignore[attr-defined]
            return

        row, col = s.cursor_row, s.cursor_col
        line = s.buffer[row]
        # Check if needle is actually at the cursor
        idx = self._find_in_line(line, needle, col)
        if idx == col:
            s.buffer[row] = line[:idx] + repl + line[idx + len(needle) :]
            s.cursor_col = idx + len(repl)
            s.modified = True
            # Find NEXT occurrence after this replacement
            self._find_next(wrap=True)
        else:
            # Not at cursor? Just find next.
            self._find_next(wrap=True)

    def _global_replace(self) -> None:
        """Global replace from current cursor to end of file."""
        self._push_undo("global_replace")
        s = self.state
        needle = s.search_string
        repl = s.replace_string
        if not needle:
            self.screen.set_message("No search string — press Ctrl+F first")  # type: ignore[attr-defined]
            return

        count = 0
        # Start at current cursor
        start_row, start_col = s.cursor_row, s.cursor_col

        for row in range(start_row, len(s.buffer)):
            line = s.buffer[row]
            col_start = start_col if row == start_row else 0

            if "?" not in needle:
                # Optimized for non-wildcard
                n = line.count(needle, col_start)
                if n > 0:
                    # We only replace from col_start onwards
                    head = line[:col_start]
                    tail = line[col_start:].replace(needle, repl)
                    s.buffer[row] = head + tail
                    count += n
            else:
                # Wildcard replacement
                new_line, n = self._replace_all_in_line_from(
                    line, needle, repl, col_start
                )
                if n:
                    s.buffer[row] = new_line
                    count += n

        if count:
            s.modified = True
            self.screen.set_message(f"Replaced {count} occurrence(s)")  # type: ignore[attr-defined]
        else:
            self.screen.set_message(f"Not found: {needle!r}")  # type: ignore[attr-defined]

    def _replace_all_in_line_from(
        self, line: str, needle: str, repl: str, start: int
    ) -> tuple[str, int]:
        """Replace all occurrences in a line starting from 'start', handling wildcards."""
        nn = len(needle)
        result = line[:start]
        count = 0
        i = start
        while i <= len(line) - nn:
            if all(needle[j] == "?" or line[i + j] == needle[j] for j in range(nn)):
                result += repl
                i += nn
                count += 1
            else:
                result += line[i]
                i += 1
        result += line[i:]
        return result, count

    # ------------------------------------------------------------------
    # Cursor movement
    # ------------------------------------------------------------------

    def _move_up(self) -> None:
        s = self.state
        if s.cursor_row > 0:
            s.cursor_row -= 1
            s.cursor_col = min(s.cursor_col, len(s.buffer[s.cursor_row]))

    def _move_down(self) -> None:
        s = self.state
        if s.cursor_row < len(s.buffer) - 1:
            s.cursor_row += 1
            s.cursor_col = min(s.cursor_col, len(s.buffer[s.cursor_row]))

    def _move_left(self) -> None:
        s = self.state
        if s.cursor_col > 0:
            s.cursor_col -= 1
        elif s.cursor_row > 0:
            s.cursor_row -= 1
            s.cursor_col = len(s.buffer[s.cursor_row])

    def _move_right(self) -> None:
        s = self.state
        line = s.buffer[s.cursor_row]
        if s.cursor_col < len(line):
            s.cursor_col += 1
        elif s.cursor_row < len(s.buffer) - 1:
            s.cursor_row += 1
            s.cursor_col = 0

    def _word_jump(self, direction: int) -> None:
        s = self.state
        text = "\n".join(s.buffer)
        flat_pos = sum(len(s.buffer[r]) + 1 for r in range(s.cursor_row)) + s.cursor_col
        if direction > 0:
            while flat_pos < len(text) and not text[flat_pos].isspace():
                flat_pos += 1
            while flat_pos < len(text) and text[flat_pos].isspace():
                flat_pos += 1
        else:
            flat_pos -= 1
            while flat_pos > 0 and text[flat_pos].isspace():
                flat_pos -= 1
            while flat_pos > 0 and not text[flat_pos - 1].isspace():
                flat_pos -= 1
        for i, line in enumerate(s.buffer):
            if flat_pos <= len(line):
                s.cursor_row, s.cursor_col = i, flat_pos
                return
            flat_pos -= len(line) + 1

    def _page_scroll(self, direction: int) -> None:
        s = self.state
        page_lines = max(1, self.size.height - EDITOR_RESERVED_LINES)
        s.cursor_row = max(
            0, min(len(s.buffer) - 1, s.cursor_row + direction * page_lines)
        )
        s.cursor_col = min(s.cursor_col, len(s.buffer[s.cursor_row]))

    def _tab_forward(self) -> None:
        s = self.state
        col = s.cursor_col
        next_stop = min((t for t in self.tab_stops if t > col), default=col + 1)
        spaces = next_stop - col
        if s.insert_mode:
            row = s.cursor_row
            line = s.buffer[row]
            s.buffer[row] = line[:col] + " " * spaces + line[col:]
            s.modified = True
        s.cursor_col = next_stop

    def _tab_toggle(self) -> None:
        """Set or clear a tab stop at the current cursor column."""
        col = self.state.cursor_col
        if col in self.tab_stops:
            self.tab_stops.discard(col)
            self.screen.set_message(f"Tab stop cleared at column {col}")  # type: ignore[attr-defined]
        else:
            self.tab_stops.add(col)
            self.screen.set_message(f"Tab stop set at column {col}")  # type: ignore[attr-defined]
        self._update_tab_bar()

    def _tab_clear_all(self) -> None:
        """Clear all tab stops."""
        self.tab_stops.clear()
        self.screen.set_message("All tab stops cleared")  # type: ignore[attr-defined]
        self._update_tab_bar()

    def _update_tab_bar(self) -> None:
        try:
            self.screen.update_tab_bar()  # type: ignore[attr-defined]
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Editing
    # ------------------------------------------------------------------

    def _insert_newline(self) -> None:
        s = self.state
        row, col = s.cursor_row, s.cursor_col
        line = s.buffer[row]
        s.buffer[row] = line[:col]
        s.buffer.insert(row + 1, line[col:])
        s.cursor_row += 1
        s.cursor_col = 0
        s.modified = True

    def _type_char(self, ch: str) -> None:
        s = self.state
        if s.caps_mode:
            ch = ch.upper()
        row, col = s.cursor_row, s.cursor_col
        line = s.buffer[row]
        if s.insert_mode:
            s.buffer[row] = line[:col] + ch + line[col:]
        else:
            s.buffer[row] = (
                line[:col] + ch + (line[col + 1 :] if col < len(line) else "")
            )
        s.cursor_col += 1
        self._apply_word_wrap(row)
        s.modified = True

    def _apply_word_wrap(self, row: int) -> None:
        s = self.state
        right = s.fmt.right_margin
        line = s.buffer[row]
        if len(line) <= right:
            return
        wrap_at = line.rfind(" ", 0, right + 1)
        if wrap_at == -1:
            wrap_at = right
        head = line[:wrap_at]
        tail = line[wrap_at:].lstrip(" ")
        s.buffer[row] = head
        if row + 1 < len(s.buffer):
            next_line = s.buffer[row + 1]
            s.buffer[row + 1] = tail + (" " if tail and next_line else "") + next_line
        else:
            s.buffer.insert(row + 1, tail)
        if s.cursor_col > len(head):
            s.cursor_col = max(
                0, s.cursor_col - len(head) - (len(line[wrap_at:]) - len(tail))
            )
            s.cursor_row = row + 1

    def _insert_control(self, ctrl: str) -> None:
        s = self.state
        if not s.allows_formatting:
            self.screen.set_message("Formatting is only available in .sfw files")  # type: ignore[attr-defined]
            return
        row, col = s.cursor_row, s.cursor_col
        line = s.buffer[row]
        s.buffer[row] = line[:col] + ctrl + line[col:]
        s.cursor_col += 1
        s.modified = True

    def _insert_structure_marker(self, marker: str) -> None:
        """Insert a structure marker on its own line at the cursor position."""
        s = self.state
        if not s.allows_formatting:
            self.screen.set_message("Formatting is only available in .sfw files")  # type: ignore[attr-defined]
            return
        row = s.cursor_row
        # Insert a new line above cursor containing just the marker
        s.buffer.insert(row, marker)
        s.cursor_row = row + 1
        s.cursor_col = 0
        s.modified = True

    def _prompt_heading(self) -> None:
        """Prompt for heading level and insert CTRL_HEADING + digit."""
        self.screen.set_message("Heading level (1-9): ")  # type: ignore[attr-defined]
        self._search_active = False
        self._replace_active = False
        self._heading_active = True
        self._input_buffer = ""

    def _prompt_chain(self) -> None:
        """Prompt for chain filename."""
        self.screen.set_message("Chain to file: ")  # type: ignore[attr-defined]
        self._chain_active = True
        self._input_buffer = ""

    def _backspace(self) -> None:
        s = self.state
        row, col = s.cursor_row, s.cursor_col
        if col > 0:
            line = s.buffer[row]
            s.buffer[row] = line[: col - 1] + line[col:]
            s.cursor_col -= 1
            s.modified = True
        elif row > 0:
            prev = s.buffer[row - 1]
            s.buffer[row - 1] = prev + s.buffer[row]
            s.buffer.pop(row)
            s.cursor_row -= 1
            s.cursor_col = len(prev)
            s.modified = True

    def _delete_char(self) -> None:
        s = self.state
        row, col = s.cursor_row, s.cursor_col
        line = s.buffer[row]
        if col < len(line):
            s.buffer[row] = line[:col] + line[col + 1 :]
            s.modified = True
        elif row < len(s.buffer) - 1:
            s.buffer[row] = line + s.buffer[row + 1]
            s.buffer.pop(row + 1)
            s.modified = True

    def _delete_to_eol(self) -> None:
        s = self.state
        row, col = s.cursor_row, s.cursor_col
        line = s.buffer[row]
        s.last_deleted_line = line[col:]
        s.buffer[row] = line[:col]
        s.modified = True

    def _undelete(self) -> None:
        s = self.state
        if not s.last_deleted_line:
            return
        row, col = s.cursor_row, s.cursor_col
        line = s.buffer[row]
        s.buffer[row] = line[:col] + s.last_deleted_line + line[col:]
        s.modified = True

    def _delete_to_eof(self) -> None:
        s = self.state
        row, col = s.cursor_row, s.cursor_col
        s.buffer[row] = s.buffer[row][:col]
        del s.buffer[row + 1 :]
        s.modified = True

    def _toggle_case_at_cursor(self) -> None:
        s = self.state
        row, col = s.cursor_row, s.cursor_col
        line = s.buffer[row]
        if col < len(line):
            ch = line[col]
            toggled = ch.lower() if ch.isupper() else ch.upper()
            s.buffer[row] = line[:col] + toggled + line[col + 1 :]
            s.modified = True

    # ------------------------------------------------------------------
    # Block / clipboard ops
    # ------------------------------------------------------------------

    def _cut(self) -> None:
        s = self.state
        if self._has_selection():
            s.clipboard = self._selected_text()
            self._delete_selection()
        else:
            # Fall back: cut current line
            row = s.cursor_row
            s.clipboard = s.buffer[row]
            if len(s.buffer) > 1:
                s.buffer.pop(row)
                s.cursor_row = min(row, len(s.buffer) - 1)
            else:
                s.buffer[row] = ""
            s.cursor_col = 0
            s.modified = True

    def _copy(self) -> None:
        s = self.state
        if self._has_selection():
            s.clipboard = self._selected_text()
        else:
            s.clipboard = s.buffer[s.cursor_row]

    def _paste(self) -> None:
        s = self.state
        if not s.clipboard:
            return
        if self._has_selection():
            self._delete_selection()
        row, col = s.cursor_row, s.cursor_col
        lines = s.clipboard.split("\n")
        if len(lines) == 1:
            # Single-line paste: insert inline
            line = s.buffer[row]
            s.buffer[row] = line[:col] + lines[0] + line[col:]
            s.cursor_col = col + len(lines[0])
        else:
            # Multi-line paste: split current line and insert
            line = s.buffer[row]
            before = line[:col]
            after = line[col:]
            s.buffer[row] = before + lines[0]
            for i, ln in enumerate(lines[1:], start=1):
                s.buffer.insert(row + i, ln)
            s.buffer[row + len(lines) - 1] += after
            s.cursor_row = row + len(lines) - 1
            s.cursor_col = len(lines[-1])
        s.modified = True

    def action_editor_copy(self) -> None:
        _log.debug(
            "action_editor_copy: selection=%r clipboard_before=%r",
            self._has_selection(),
            self.state.clipboard,
        )
        self._copy()
        _log.debug("action_editor_copy: clipboard_after=%r", self.state.clipboard)
        self.refresh()
        self._update_status()

    def action_editor_paste(self) -> None:
        _log.debug(
            "action_editor_paste: clipboard=%r cursor=(%d,%d)",
            self.state.clipboard,
            self.state.cursor_row,
            self.state.cursor_col,
        )
        self._push_undo("paste")
        self._paste()
        _log.debug(
            "action_editor_paste: buffer[row]=%r cursor=(%d,%d)",
            self.state.buffer[self.state.cursor_row],
            self.state.cursor_row,
            self.state.cursor_col,
        )
        self.refresh()
        self._update_status()

    def action_editor_cut(self) -> None:
        _log.debug("action_editor_cut: selection=%r", self._has_selection())
        self._push_undo("cut")
        self._cut()
        _log.debug("action_editor_cut: clipboard=%r", self.state.clipboard)
        self.refresh()
        self._update_status()

    def _word_count(self) -> None:
        if self._has_selection():
            text = self._selected_text()
            label = "Selection"
        else:
            text = "\n".join(self.state.buffer)
            label = "Document"
        count = len(text.split())
        self.screen.set_message(f"Word count ({label}): {count}")  # type: ignore[attr-defined]

    def _alphabetize(self) -> None:
        s = self.state
        if self._has_selection():
            anchor = s.selection_anchor
            if anchor is None:
                return
            start, end = _selection_range(
                s.buffer, anchor, (s.cursor_row, s.cursor_col)
            )
            sr, _ = start
            er, _ = end
            # Sort only the lines covered by the selection
            s.buffer[sr : er + 1] = sorted(s.buffer[sr : er + 1])
            s.cursor_row = sr
            s.cursor_col = 0
            s.selection_anchor = None
        else:
            s.buffer.sort()
            s.cursor_row = 0
            s.cursor_col = 0
        s.modified = True

    def _update_status(self) -> None:
        try:
            self.screen.update_status()  # type: ignore[attr-defined]
        except Exception:
            pass


class EditorScreen(Screen):
    CSS = EDITOR_CSS

    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state
        self._message = ""

    def compose(self) -> ComposeResult:
        yield Static(self._tab_bar_text(), id="tab-bar")
        yield EditorArea(self.state)
        with Container(id="editor-footer"):
            yield Static(self._message or "Welcome to Safari Writer", id="message-bar")
            yield Static(self._status_text(), id="status-bar")
            yield Static(HELP_TEXT, id="help-bar")

    def on_mount(self) -> None:
        self.query_one(EditorArea).focus()
        self.update_status()

    def _status_text(self) -> str:
        s = self.state
        mode = "Insert" if s.insert_mode else "Type-over"
        caps = "Uppercase" if s.caps_mode else "Lowercase"
        storage = "SFW" if s.storage_mode == StorageMode.FORMATTED else "PLAIN"
        profile_name = s.file_profile.display_name
        return f" Bytes Free: {s.bytes_free:,}   [{mode}]   [{caps}]   [{storage}]   [{profile_name}]"

    def _tab_bar_text(self) -> str:
        try:
            stops = self.query_one(EditorArea).tab_stops
        except Exception:
            stops = DEFAULT_TAB_STOPS
        bar = ""
        for col in range(80):
            bar += "v" if col in stops else " "
        return bar

    def set_message(self, msg: str) -> None:
        self._message = msg
        if self.is_mounted:
            self.query_one("#message-bar", Static).update(msg)

    def update_status(self) -> None:
        if self.is_mounted:
            self.query_one("#status-bar", Static).update(self._status_text())

    def update_tab_bar(self) -> None:
        if self.is_mounted:
            self.query_one("#tab-bar", Static).update(self._tab_bar_text())
