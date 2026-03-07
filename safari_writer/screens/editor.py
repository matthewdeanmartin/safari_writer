"""Editor screen — the main text editing workspace."""

from textual.app import ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widgets import Static
from textual.widget import Widget
from textual import events

# Control character display symbols embedded in the buffer
CTRL_BOLD      = "\x01"  # bold toggle marker
CTRL_UNDERLINE = "\x02"  # underline toggle
CTRL_CENTER    = "\x03"  # center line
CTRL_RIGHT     = "\x04"  # flush right
CTRL_ELONGATE  = "\x05"  # elongated (double-width) toggle
CTRL_SUPER     = "\x06"  # superscript
CTRL_SUB       = "\x07"  # subscript
CTRL_PARA      = "\x10"  # paragraph mark (non-printing indent)
CTRL_MERGE     = "\x11"  # mail merge @ marker

# Human-readable glyphs for control chars (shown in editor, not printed)
CTRL_GLYPHS = {
    CTRL_BOLD:      "←",
    CTRL_UNDERLINE: "▄",
    CTRL_CENTER:    "↔",
    CTRL_RIGHT:     "→→",
    CTRL_ELONGATE:  "E",
    CTRL_SUPER:     "↑",
    CTRL_SUB:       "↓",
    CTRL_PARA:      "¶",
    CTRL_MERGE:     "@",
}

EDITOR_CSS = """
EditorScreen {
    background: $surface;
}

#message-bar {
    dock: top;
    height: 1;
    background: $primary;
    color: $text;
    padding: 0 1;
}

#status-bar {
    dock: top;
    height: 1;
    background: $secondary;
    color: $text;
    padding: 0 1;
}

#tab-bar {
    dock: top;
    height: 1;
    background: $surface;
    color: $accent;
    padding: 0 1;
}

#help-bar {
    dock: bottom;
    height: 1;
    background: $primary;
    color: $text;
    padding: 0 1;
}

EditorArea {
    height: 1fr;
    background: $surface;
    overflow-y: auto;
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
    "^X Cut  ^C Copy  ^V Paste  ^F Find  ^H Replace  "
    "^B Bold  ^U Underline  ^E Center  "
    "F1 Help  Esc Menu"
)

HELP_CONTENT = """\
NAVIGATION
  Arrow keys          Move cursor
  Ctrl+Left/Right     Jump word
  Home / End          Line start / end
  Ctrl+Home/End       Top / bottom of file
  Page Up/Down        Scroll page
  Tab                 Jump to next tab stop

EDITING
  Insert              Toggle Insert / Type-over mode
  Shift+F3            Toggle case of character at cursor
  Ctrl+M              Insert paragraph mark (¶)
  Enter               New line (hard carriage return)

DELETION
  Backspace           Delete character before cursor
  Delete              Delete character at cursor
  Shift+Delete        Delete to end of line (saved for Undelete)
  Ctrl+Z              Undelete (restore last deleted line)
  Ctrl+Shift+Delete   Delete to end of file

BLOCK OPERATIONS
  Ctrl+X              Cut current line to clipboard
  Ctrl+C              Copy current line to clipboard
  Ctrl+V              Paste clipboard below cursor
  Alt+W               Word count (whole file)
  Alt+A               Alphabetize lines

SEARCH & REPLACE
  Ctrl+F              Find (prompt for search string)
  F3                  Find next occurrence
  Ctrl+H              Set replacement string
  Alt+F3              Replace current occurrence, find next
  Alt+R               Global replace to end of file

INLINE FORMATTING
  Ctrl+B              Bold toggle (← marker)
  Ctrl+U              Underline toggle (▄ marker)
  Ctrl+E              Center line (↔ marker)
  Ctrl+R              Flush right (→→ marker)
  Alt+M               Mail merge field marker (@)

OTHER
  Ctrl+P              Print Preview (not yet implemented)
  F1 / ?              Show this help screen
  Escape              Return to Main Menu\
"""

# Default tab stop every 5 columns (16 stops shown in header)
DEFAULT_TAB_STOPS = set(range(5, 81, 5))


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

    def __init__(self, state) -> None:
        super().__init__(id="editor-area")
        self.state = state
        self.tab_stops: set[int] = set(DEFAULT_TAB_STOPS)
        self._search_active = False  # True when prompting for search string
        self._replace_active = False  # True when prompting for replace string
        self._input_buffer = ""  # accumulates prompt input

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self) -> str:
        lines = []
        for row, line in enumerate(self.state.buffer):
            lines.append(self._render_line(line, row))
        return "\n".join(lines)

    def _render_line(self, line: str, row: int) -> str:
        out = ""
        for col, ch in enumerate(line):
            glyph = CTRL_GLYPHS.get(ch, ch)
            if row == self.state.cursor_row and col == self.state.cursor_col:
                out += f"[reverse]{glyph}[/reverse]"
            else:
                out += glyph
        # Cursor at end of line
        if row == self.state.cursor_row and self.state.cursor_col >= len(line):
            out += "[reverse] [/reverse]"
        return out

    # ------------------------------------------------------------------
    # Key handling
    # ------------------------------------------------------------------

    def on_key(self, event: events.Key) -> None:
        # If a prompt is active, route all input there
        if self._search_active or self._replace_active:
            self._handle_prompt_key(event)
            return

        state = self.state
        key = event.key
        handled = True

        # Help
        if key in ("f1", "question_mark"):
            self.app.push_screen(HelpScreen())

        # Navigation
        elif key == "up":
            self._move_up()
        elif key == "down":
            self._move_down()
        elif key == "left":
            self._move_left()
        elif key == "right":
            self._move_right()
        elif key == "ctrl+left":
            self._word_jump(-1)
        elif key == "ctrl+right":
            self._word_jump(1)
        elif key == "home":
            state.cursor_col = 0
        elif key == "end":
            state.cursor_col = len(state.buffer[state.cursor_row])
        elif key == "ctrl+home":
            state.cursor_row = 0
            state.cursor_col = 0
        elif key == "ctrl+end":
            state.cursor_row = len(state.buffer) - 1
            state.cursor_col = len(state.buffer[state.cursor_row])
        elif key == "pageup":
            self._page_scroll(-1)
        elif key == "pagedown":
            self._page_scroll(1)
        elif key == "tab":
            self._tab_forward()

        # Enter — split line
        elif key == "enter":
            self._insert_newline()

        # Mode toggles
        elif key == "insert":
            state.insert_mode = not state.insert_mode
            self._update_status()
        elif key == "shift+f3":
            self._toggle_case_at_cursor()

        # Deletion
        elif key == "backspace":
            self._backspace()
        elif key == "delete":
            self._delete_char()
        elif key == "shift+delete":
            self._delete_to_eol()
        elif key == "ctrl+z":
            self._undelete()
        elif key == "ctrl+shift+delete":
            self._delete_to_eof()

        # Block ops
        elif key == "ctrl+x":
            self._cut()
        elif key == "ctrl+c":
            self._copy()
        elif key == "ctrl+v":
            self._paste()
        elif key == "alt+w":
            self._word_count()
        elif key == "alt+a":
            self._alphabetize()

        # Search & replace
        elif key == "ctrl+f":
            self._prompt_search()
        elif key == "f3":
            self._find_next()
        elif key == "ctrl+h":
            self._prompt_replace()
        elif key == "alt+f3":
            self._replace_current_and_find_next()
        elif key == "alt+r":
            self._global_replace()

        # Inline formatting
        elif key == "ctrl+b":
            self._insert_control(CTRL_BOLD)
        elif key == "ctrl+u":
            self._insert_control(CTRL_UNDERLINE)
        elif key == "ctrl+e":
            self._insert_control(CTRL_CENTER)
        elif key == "ctrl+r":
            self._insert_control(CTRL_RIGHT)
        elif key == "ctrl+m":
            self._insert_control(CTRL_PARA)
        elif key == "alt+m":
            self._insert_control(CTRL_MERGE)

        # Print preview stub
        elif key == "ctrl+p":
            self.screen.set_message("Print Preview: not yet implemented")  # type: ignore[attr-defined]

        # Exit to main menu
        elif key == "escape":
            self.app.pop_screen()

        # Printable characters
        elif event.character and event.character.isprintable():
            self._type_char(event.character)

        else:
            handled = False

        if handled:
            event.stop()
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
        key = event.key
        if key == "enter":
            if self._search_active:
                self.state.search_string = self._input_buffer
                self._search_active = False
                self.screen.set_message(f"Find: {self._input_buffer!r}  — press F3 to find")  # type: ignore[attr-defined]
                # Jump to first occurrence from start of doc
                self.state.last_search_row = 0
                self.state.last_search_col = 0
                self._find_next()
            else:
                self.state.replace_string = self._input_buffer
                self._replace_active = False
                self.screen.set_message(f"Replace: {self._input_buffer!r}  — Alt+F3 replace, Alt+R global")  # type: ignore[attr-defined]
        elif key == "escape":
            self._search_active = False
            self._replace_active = False
            self.screen.set_message("")  # type: ignore[attr-defined]
        elif key == "backspace":
            self._input_buffer = self._input_buffer[:-1]
            prompt = "Find: " if self._search_active else "Replace with: "
            self.screen.set_message(prompt + self._input_buffer)  # type: ignore[attr-defined]
        elif event.character and event.character.isprintable():
            if len(self._input_buffer) < 37:
                self._input_buffer += event.character
                prompt = "Find: " if self._search_active else "Replace with: "
                self.screen.set_message(prompt + self._input_buffer)  # type: ignore[attr-defined]
        event.stop()
        self.refresh()

    # ------------------------------------------------------------------
    # Search & replace logic
    # ------------------------------------------------------------------

    def _find_next(self) -> bool:
        """Find next occurrence of search_string from last_search position.

        Returns True if found, False otherwise.
        """
        s = self.state
        needle = s.search_string
        if not needle:
            self.screen.set_message("No search string set — press Ctrl+F")  # type: ignore[attr-defined]
            return False

        start_row = s.last_search_row
        start_col = s.last_search_col

        # Search from current position forward, wrapping around
        rows = list(range(start_row, len(s.buffer))) + list(range(0, start_row))
        for i, row in enumerate(rows):
            line = s.buffer[row]
            col_start = start_col if (i == 0 and row == start_row) else 0
            idx = self._find_in_line(line, needle, col_start)
            if idx != -1:
                s.cursor_row = row
                s.cursor_col = idx
                # Next search starts after this match
                s.last_search_row = row
                s.last_search_col = idx + len(needle)
                self.screen.set_message(f"Found: {needle!r}")  # type: ignore[attr-defined]
                return True

        self.screen.set_message(f"Not found: {needle!r}")  # type: ignore[attr-defined]
        return False

    def _find_in_line(self, line: str, needle: str, start: int = 0) -> int:
        """Find needle in line from start, supporting '?' wildcard."""
        if "?" not in needle:
            return line.find(needle, start)
        # Wildcard match
        nl, nn = len(line), len(needle)
        for i in range(start, nl - nn + 1):
            if all(needle[j] == "?" or line[i + j] == needle[j] for j in range(nn)):
                return i
        return -1

    def _replace_current_and_find_next(self) -> None:
        """Replace match at cursor position then find next."""
        s = self.state
        needle = s.search_string
        repl = s.replace_string
        if not needle:
            self.screen.set_message("No search string — press Ctrl+F first")  # type: ignore[attr-defined]
            return
        row, col = s.cursor_row, s.cursor_col
        line = s.buffer[row]
        # Check if the cursor is actually sitting on a match
        idx = self._find_in_line(line, needle, col)
        if idx == col:
            # Replace in-place
            s.buffer[row] = line[:idx] + repl + line[idx + len(needle):]
            s.cursor_col = idx + len(repl)
            s.last_search_row = row
            s.last_search_col = idx + len(repl)
            s.modified = True
            self._find_next()
        else:
            # Cursor not on a match — just find next
            self._find_next()

    def _global_replace(self) -> None:
        """Replace all occurrences from cursor to end of file."""
        s = self.state
        needle = s.search_string
        repl = s.replace_string
        if not needle:
            self.screen.set_message("No search string — press Ctrl+F first")  # type: ignore[attr-defined]
            return
        count = 0
        for row in range(s.cursor_row, len(s.buffer)):
            line = s.buffer[row]
            new_line, n = self._replace_all_in_line(line, needle, repl)
            if n:
                s.buffer[row] = new_line
                count += n
        if count:
            s.modified = True
        self.screen.set_message(f"Replaced {count} occurrence(s)")  # type: ignore[attr-defined]

    def _replace_all_in_line(self, line: str, needle: str, repl: str) -> tuple[str, int]:
        """Replace all occurrences of needle in line (wildcard-aware)."""
        if "?" not in needle:
            count = line.count(needle)
            return line.replace(needle, repl), count
        # Wildcard: build manually
        result = ""
        count = 0
        i = 0
        nn = len(needle)
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
        # Convert flat_pos back to row/col
        for i, line in enumerate(s.buffer):
            if flat_pos <= len(line):
                s.cursor_row, s.cursor_col = i, flat_pos
                return
            flat_pos -= len(line) + 1

    def _page_scroll(self, direction: int) -> None:
        s = self.state
        page_lines = max(1, self.size.height - 4)
        s.cursor_row = max(0, min(len(s.buffer) - 1, s.cursor_row + direction * page_lines))
        s.cursor_col = min(s.cursor_col, len(s.buffer[s.cursor_row]))

    def _tab_forward(self) -> None:
        """Advance cursor to the next tab stop, inserting spaces in insert mode."""
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
            s.buffer[row] = line[:col] + ch + (line[col + 1:] if col < len(line) else "")
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
        # If cursor was in the wrapped portion, move it to the next line
        if s.cursor_col > len(head):
            s.cursor_col = s.cursor_col - len(head) - (len(line[wrap_at:]) - len(tail))
            s.cursor_row = row + 1

    def _insert_control(self, ctrl: str) -> None:
        s = self.state
        row, col = s.cursor_row, s.cursor_col
        line = s.buffer[row]
        s.buffer[row] = line[:col] + ctrl + line[col:]
        s.cursor_col += 1
        s.modified = True

    def _backspace(self) -> None:
        s = self.state
        row, col = s.cursor_row, s.cursor_col
        if col > 0:
            line = s.buffer[row]
            s.buffer[row] = line[:col - 1] + line[col:]
            s.cursor_col -= 1
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
            s.buffer[row] = line[:col] + line[col + 1:]
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
        del s.buffer[row + 1:]
        s.modified = True

    def _toggle_case_at_cursor(self) -> None:
        s = self.state
        row, col = s.cursor_row, s.cursor_col
        line = s.buffer[row]
        if col < len(line):
            ch = line[col]
            toggled = ch.lower() if ch.isupper() else ch.upper()
            s.buffer[row] = line[:col] + toggled + line[col + 1:]
            s.modified = True

    # ------------------------------------------------------------------
    # Block / clipboard ops
    # ------------------------------------------------------------------

    def _cut(self) -> None:
        s = self.state
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
        self.state.clipboard = self.state.buffer[self.state.cursor_row]

    def _paste(self) -> None:
        s = self.state
        if not s.clipboard:
            return
        row = s.cursor_row
        s.buffer.insert(row + 1, s.clipboard)
        s.cursor_row += 1
        s.cursor_col = 0
        s.modified = True

    def _word_count(self) -> None:
        text = "\n".join(self.state.buffer)
        count = len(text.split())
        self.screen.set_message(f"Word count: {count}")  # type: ignore[attr-defined]

    def _alphabetize(self) -> None:
        s = self.state
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

    def __init__(self, state) -> None:
        super().__init__()
        self.state = state
        self._message = ""

    def compose(self) -> ComposeResult:
        yield Static(self._message or "", id="message-bar")
        yield Static(self._status_text(), id="status-bar")
        yield Static(self._tab_bar_text(), id="tab-bar")
        yield EditorArea(self.state)
        yield Static(HELP_TEXT, id="help-bar")

    def on_mount(self) -> None:
        self.query_one(EditorArea).focus()

    def _status_text(self) -> str:
        s = self.state
        mode = "Insert" if s.insert_mode else "Type-over"
        caps = "Uppercase" if s.caps_mode else "Lowercase"
        return f" Bytes Free: {s.bytes_free:,}   [{mode}]   [{caps}]"

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
