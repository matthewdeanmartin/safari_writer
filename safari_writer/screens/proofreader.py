"""Proofreader screen — integrated spelling verification module."""

from __future__ import annotations

import re
from pathlib import Path
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Static
from textual import events

# Control chars that should be stripped before spell-checking
_CTRL_CHARS = re.compile(r"[\x01-\x1f]")

# ---------------------------------------------------------------------------
# Dictionary backend (pyenchant)
# ---------------------------------------------------------------------------

def _make_checker():
    """Return an enchant Dict, or None if enchant is unavailable."""
    try:
        import enchant
        return enchant.Dict("en_US")
    except Exception:
        return None


def _check_word(word: str, checker, kept: set[str], personal: set[str]) -> bool:
    """Return True if word is correctly spelled."""
    w = word.strip(".,;:!?\"'()-")
    if not w or not w[0].isalpha():
        return True
    if w.lower() in kept or w.lower() in personal:
        return True
    if checker is None:
        return True  # no dictionary — assume OK
    return checker.check(w)


def _suggest(word: str, checker) -> list[str]:
    if checker is None:
        return []
    try:
        return checker.suggest(word)[:18]
    except Exception:
        return []


def _dict_lookup(prefix: str, checker) -> list[str]:
    """Return up to 126 dictionary words starting with prefix (via suggestions heuristic)."""
    if checker is None or len(prefix) < 2:
        return []
    try:
        suggestions = checker.suggest(prefix)
        matches = [w for w in suggestions if w.lower().startswith(prefix.lower())]
        return matches[:126]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Word extraction: return list of (row, col_start, word) from buffer
# ---------------------------------------------------------------------------

def _extract_words(buffer: list[str]) -> list[tuple[int, int, str]]:
    """Yield (row, col, word) for every word token in the buffer."""
    word_re = re.compile(r"[A-Za-z']+")
    results = []
    for row, line in enumerate(buffer):
        clean = _CTRL_CHARS.sub(" ", line)
        for m in word_re.finditer(clean):
            results.append((row, m.start(), m.group()))
    return results


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

PR_CSS = """
ProofreaderScreen {
    background: $surface;
    layout: vertical;
}

#pr-message {
    dock: top;
    height: 1;
    background: $primary;
    color: $text;
    padding: 0 1;
}

#pr-title {
    height: 1;
    text-align: center;
    text-style: bold;
    color: $primary;
}

#pr-body {
    height: 1fr;
    padding: 0 1;
}

#pr-help {
    dock: bottom;
    height: 1;
    background: $primary-darken-2;
    color: $text-muted;
    padding: 0 1;
}
"""

# ---------------------------------------------------------------------------
# Mode constants
# ---------------------------------------------------------------------------

MODE_MENU       = "menu"       # choosing highlight / print / correct / search
MODE_HIGHLIGHT  = "highlight"  # auto-scrolling highlight-only scan
MODE_PRINT      = "print"      # batch scan → list errors
MODE_CORRECT    = "correct"    # scanning for next error (between errors)
MODE_CORRECT_MENU = "correct_menu"   # sub-menu: C/S/Enter
MODE_CORRECT_WORD = "correct_word"   # typing replacement
MODE_CORRECT_CONFIRM = "correct_confirm"  # "Are you sure? Y/N"
MODE_DICT_SEARCH     = "dict_search"      # standalone dict search input
MODE_DICT_RESULTS    = "dict_results"     # paging through results
MODE_SAVE_PERSONAL   = "save_personal"   # prompt filename for personal dict
MODE_LOAD_PERSONAL   = "load_personal"   # prompt filename to load personal dict


class ProofreaderScreen(Screen):
    """Integrated spelling verification module."""

    CSS = PR_CSS

    BINDINGS = [
        Binding("escape", "exit_proofreader", "Exit", show=False),
    ]

    def __init__(self, state) -> None:
        super().__init__()
        self._state = state
        self._checker = _make_checker()
        self._personal: set[str] = set()   # loaded personal dict words
        self._mode = MODE_MENU
        self._input_buf = ""

        # Scan state
        self._words: list[tuple[int, int, str]] = []  # (row, col, word) for all words
        self._scan_idx = 0                             # current position in _words
        self._errors: list[tuple[int, int, str]] = [] # flagged words

        # Correction state
        self._current_error: tuple[int, int, str] | None = None
        self._replacement: str = ""

        # Dict results paging
        self._dict_results: list[str] = []
        self._dict_page = 0
        self._dict_prefix = ""

    # ------------------------------------------------------------------
    # Compose
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Static("", id="pr-message")
        yield Static("*** SAFARI WRITER — PROOFREADER ***", id="pr-title")
        yield Static("", id="pr-body")
        yield Static("", id="pr-help")

    def on_mount(self) -> None:
        self._enter_menu()

    # ------------------------------------------------------------------
    # Mode entry helpers
    # ------------------------------------------------------------------

    def _enter_menu(self) -> None:
        self._mode = MODE_MENU
        self._set_body(
            "[bold]H[/]  Highlight Errors\n"
            "[bold]P[/]  Print Errors (list on-screen)\n"
            "[bold]C[/]  Correct Errors\n"
            "[bold]S[/]  Dictionary Search\n"
            "[bold]L[/]  Load Personal Dictionary\n"
            "[bold]W[/]  Write (save) Personal Dictionary\n"
            "\n"
            "[dim]Esc  Return to Main Menu[/]"
        )
        self._set_message("Select a proofing mode.")
        self._set_help(" H Highlight  P Print  C Correct  S Search  L Load  W Write  Esc Exit")

    def _enter_highlight(self) -> None:
        self._mode = MODE_HIGHLIGHT
        self._errors = []
        self._words = _extract_words(self._state.buffer)
        self._set_message("Scanning document… (any key to abort)")
        self._set_help(" Any key to abort scan")
        self._render_highlight_scan()

    def _enter_print(self) -> None:
        self._mode = MODE_PRINT
        self._words = _extract_words(self._state.buffer)
        self._errors = [
            (r, c, w) for r, c, w in self._words
            if not _check_word(w, self._checker, self._state.kept_spellings, self._personal)
        ]
        if not self._errors:
            self._set_body("No spelling errors found.")
        else:
            lines = [f"[bold]Spelling Errors ({len(self._errors)} found):[/]\n"]
            for r, c, w in self._errors:
                lines.append(f"  Line {r + 1}, col {c + 1}: [reverse]{w}[/]")
            self._set_body("\n".join(lines))
        self._set_message("Scan complete. Press any key to return to menu.")
        self._set_help(" Any key → return to menu")

    def _enter_correct(self) -> None:
        self._mode = MODE_CORRECT
        self._words = _extract_words(self._state.buffer)
        self._scan_idx = 0
        self._errors = []
        self._advance_to_next_error()

    def _advance_to_next_error(self) -> None:
        while self._scan_idx < len(self._words):
            r, c, w = self._words[self._scan_idx]
            if not _check_word(w, self._checker, self._state.kept_spellings, self._personal):
                self._current_error = (r, c, w)
                self._enter_correct_menu()
                return
            self._scan_idx += 1
        # No more errors
        self._current_error = None
        kept_count = len(self._state.kept_spellings)
        self._set_body(
            f"[bold green]Spell check complete.[/]\n\n"
            f"Words kept this session: {kept_count}\n\n"
            f"[bold]W[/]  Save kept words to personal dictionary\n"
            f"[bold]Esc[/]  Return to menu"
        )
        self._set_message("No more errors found.")
        self._set_help(" W Save personal dict  Esc Return to menu")
        self._mode = MODE_MENU  # reuse menu key handler, body shows completion

    def _enter_correct_menu(self) -> None:
        self._mode = MODE_CORRECT_MENU
        r, c, w = self._current_error
        self._render_document_with_highlight(r, c, w)
        self._set_message(f'Unrecognized: [reverse]{w}[/]  — C Correct  S Search dict  Enter Keep')
        self._set_help(" C Correct Word  S Search Dictionary  Enter Keep This Spelling  Esc Abort")

    def _enter_dict_search(self, from_correct: bool = False) -> None:
        self._mode = MODE_DICT_SEARCH
        self._input_buf = ""
        self._from_correct = from_correct
        self._set_message("Dictionary Search: type 2+ letters, Enter to search, Esc to cancel")
        self._set_body("Enter search prefix (at least 2 letters):\n\n> ")
        self._set_help(" Enter Search  Esc Cancel")

    # ------------------------------------------------------------------
    # Key handling
    # ------------------------------------------------------------------

    def on_key(self, event: events.Key) -> None:
        key = event.key
        mode = self._mode

        if mode == MODE_MENU:
            self._handle_menu_key(key)
        elif mode == MODE_HIGHLIGHT:
            # Any key aborts
            self._enter_menu()
        elif mode == MODE_PRINT:
            self._enter_menu()
        elif mode == MODE_CORRECT_MENU:
            self._handle_correct_menu_key(key)
        elif mode == MODE_CORRECT_WORD:
            self._handle_correct_word_key(key, event)
        elif mode == MODE_CORRECT_CONFIRM:
            self._handle_correct_confirm_key(key)
        elif mode == MODE_DICT_SEARCH:
            self._handle_dict_search_key(key, event)
        elif mode == MODE_DICT_RESULTS:
            self._handle_dict_results_key(key)
        elif mode == MODE_SAVE_PERSONAL:
            self._handle_save_personal_key(key, event)
        elif mode == MODE_LOAD_PERSONAL:
            self._handle_load_personal_key(key, event)

        event.stop()

    def _handle_menu_key(self, key: str) -> None:
        k = key.lower()
        if k == "h":
            self._enter_highlight()
        elif k == "p":
            self._enter_print()
        elif k == "c":
            self._enter_correct()
        elif k == "s":
            self._enter_dict_search(from_correct=False)
        elif k == "l":
            self._mode = MODE_LOAD_PERSONAL
            self._input_buf = ""
            self._set_message("Load Personal Dictionary: enter filename, Enter to confirm")
            self._set_body("Load personal dictionary file:\n\n> ")
            self._set_help(" Enter Load  Esc Cancel")
        elif k == "w":
            self._mode = MODE_SAVE_PERSONAL
            self._input_buf = ""
            self._set_message("Save Personal Dictionary: enter filename, Enter to confirm")
            self._set_body("Save personal dictionary to file:\n\n> ")
            self._set_help(" Enter Save  Esc Cancel")
        elif key == "escape":
            self.action_exit_proofreader()

    def _handle_correct_menu_key(self, key: str) -> None:
        k = key.lower()
        if k == "c":
            self._mode = MODE_CORRECT_WORD
            self._input_buf = ""
            r, c, w = self._current_error
            self._set_message(f"Correct [{w}]: type replacement word, Enter to confirm")
            self._set_help(" Enter Confirm  Esc Cancel")
        elif k == "s":
            self._enter_dict_search(from_correct=True)
        elif key == "enter":
            # Keep This Spelling
            _, _, w = self._current_error
            self._state.kept_spellings.add(w.lower())
            self._set_message(f"Kept: '{w}' — will not flag again this session.")
            self._scan_idx += 1
            self._advance_to_next_error()
        elif key == "escape":
            self._enter_menu()

    def _handle_correct_word_key(self, key: str, event: events.Key) -> None:
        if key == "escape":
            self._enter_correct_menu()
        elif key == "enter":
            if self._input_buf:
                self._replacement = self._input_buf
                self._mode = MODE_CORRECT_CONFIRM
                r, c, w = self._current_error
                self._set_message(
                    f"Replace '{w}' with '{self._replacement}' — Are you sure? Y/N"
                )
                self._set_help(" Y Confirm  N Cancel")
        elif key == "backspace":
            self._input_buf = self._input_buf[:-1]
            self._update_word_input()
        elif event.character and event.character.isprintable():
            self._input_buf += event.character
            self._update_word_input()

    def _update_word_input(self) -> None:
        r, c, w = self._current_error
        self._set_message(
            f"Correct [{w}]: {self._input_buf}█  (Enter confirm, Esc cancel)"
        )

    def _handle_correct_confirm_key(self, key: str) -> None:
        k = key.lower()
        if k == "y":
            self._apply_correction()
        elif k == "n" or key == "escape":
            self._enter_correct_menu()

    def _apply_correction(self) -> None:
        r, c, w = self._current_error
        repl = self._replacement
        line = self._state.buffer[r]
        # Replace first occurrence at column c
        if line[c:c + len(w)] == w:
            self._state.buffer[r] = line[:c] + repl + line[c + len(w):]
            self._state.modified = True
        self._set_message(f"Replaced '{w}' with '{repl}'.")
        # Re-extract words since buffer changed
        self._words = _extract_words(self._state.buffer)
        self._scan_idx = 0
        self._advance_to_next_error()

    def _handle_dict_search_key(self, key: str, event: events.Key) -> None:
        if key == "escape":
            if self._from_correct:
                self._enter_correct_menu()
            else:
                self._enter_menu()
        elif key == "enter":
            prefix = self._input_buf.strip()
            if len(prefix) < 2:
                self._set_message("Please enter at least 2 letters.")
                return
            results = _dict_lookup(prefix, self._checker)
            self._dict_prefix = prefix
            self._dict_results = results
            self._dict_page = 0
            self._show_dict_results_page()
        elif key == "backspace":
            self._input_buf = self._input_buf[:-1]
            self._set_body(f"Enter search prefix (at least 2 letters):\n\n> {self._input_buf}")
        elif event.character and event.character.isprintable():
            self._input_buf += event.character
            self._set_body(f"Enter search prefix (at least 2 letters):\n\n> {self._input_buf}")

    def _show_dict_results_page(self) -> None:
        self._mode = MODE_DICT_RESULTS
        page_size = 126
        results = self._dict_results
        start = self._dict_page * page_size
        page = results[start:start + page_size]
        total = len(results)

        if not page:
            self._set_body(f"No words found starting with '{self._dict_prefix}'.")
            self._set_message("No matches. Press any key to search again.")
            self._set_help(" Any key → new search")
            return

        # Lay out in columns of 3
        cols = 3
        col_width = 26
        col_lines = [page[i::cols] for i in range(cols)]
        max_rows = max(len(c) for c in col_lines)
        lines = [f"[bold]Dictionary: '{self._dict_prefix}'[/]  ({total} matches)\n"]
        for row_i in range(max_rows):
            row_parts = []
            for col_i in range(cols):
                word = col_lines[col_i][row_i] if row_i < len(col_lines[col_i]) else ""
                row_parts.append(word.ljust(col_width))
            lines.append("".join(row_parts))

        has_next = (start + page_size) < total
        has_prev = self._dict_page > 0
        nav = []
        if has_prev:
            nav.append("PgUp Prev")
        if has_next:
            nav.append("PgDn Next")
        nav.append("Esc New search")

        self._set_body("\n".join(lines))
        self._set_message(f"Page {self._dict_page + 1} of {(total - 1) // page_size + 1}")
        self._set_help("  ".join(nav))

    def _handle_dict_results_key(self, key: str) -> None:
        page_size = 126
        if key == "pagedown" and (self._dict_page + 1) * page_size < len(self._dict_results):
            self._dict_page += 1
            self._show_dict_results_page()
        elif key == "pageup" and self._dict_page > 0:
            self._dict_page -= 1
            self._show_dict_results_page()
        elif key == "escape":
            self._enter_dict_search(from_correct=self._from_correct)
        else:
            # Any other key → back to new search
            self._enter_dict_search(from_correct=self._from_correct)

    def _handle_save_personal_key(self, key: str, event: events.Key) -> None:
        if key == "escape":
            self._enter_menu()
        elif key == "enter":
            filename = self._input_buf.strip()
            if filename:
                self._save_personal_dict(filename)
            else:
                self._enter_menu()
        elif key == "backspace":
            self._input_buf = self._input_buf[:-1]
            self._set_body(f"Save personal dictionary to file:\n\n> {self._input_buf}")
        elif event.character and event.character.isprintable():
            self._input_buf += event.character
            self._set_body(f"Save personal dictionary to file:\n\n> {self._input_buf}")

    def _save_personal_dict(self, filename: str) -> None:
        words = sorted(self._state.kept_spellings | self._personal)
        if not words:
            self._set_message("No words to save.")
            self._enter_menu()
            return
        # Cap at 256 words as per spec
        words = words[:256]
        try:
            Path(filename).write_text(" ".join(words))
            self._set_message(f"Saved {len(words)} words to '{filename}'.")
        except OSError as e:
            self._set_message(f"Error saving: {e}")
        self._enter_menu()

    def _handle_load_personal_key(self, key: str, event: events.Key) -> None:
        if key == "escape":
            self._enter_menu()
        elif key == "enter":
            filename = self._input_buf.strip()
            if filename:
                self._load_personal_dict(filename)
            else:
                self._enter_menu()
        elif key == "backspace":
            self._input_buf = self._input_buf[:-1]
            self._set_body(f"Load personal dictionary file:\n\n> {self._input_buf}")
        elif event.character and event.character.isprintable():
            self._input_buf += event.character
            self._set_body(f"Load personal dictionary file:\n\n> {self._input_buf}")

    def _load_personal_dict(self, filename: str) -> None:
        try:
            text = Path(filename).read_text()
            new_words = re.split(r"[\s\n]+", text.strip().lower())
            new_words = [w for w in new_words if w]
            self._personal.update(new_words)
            self._set_message(f"Loaded {len(new_words)} words from '{filename}'.")
        except OSError as e:
            self._set_message(f"Error loading: {e}")
        self._enter_menu()

    # ------------------------------------------------------------------
    # Highlight scan renderer
    # ------------------------------------------------------------------

    def _render_highlight_scan(self) -> None:
        """Render the whole document with misspelled words in inverse video."""
        words = _extract_words(self._state.buffer)
        error_positions: set[tuple[int, int, int]] = set()
        for r, c, w in words:
            if not _check_word(w, self._checker, self._state.kept_spellings, self._personal):
                error_positions.add((r, c, len(w)))

        lines_out = []
        for row, line in enumerate(self._state.buffer):
            # Build a per-char error mask
            mask = [False] * len(line)
            for (er, ec, ew) in error_positions:
                if er == row:
                    for i in range(ec, min(ec + ew, len(line))):
                        mask[i] = True
            out = ""
            i = 0
            while i < len(line):
                ch = line[i]
                if mask[i]:
                    out += f"[reverse]{ch}[/reverse]"
                else:
                    out += ch
                i += 1
            lines_out.append(out)

        error_count = len(error_positions)
        self._set_body("\n".join(lines_out))
        self._set_message(
            f"Highlight scan complete — {error_count} error(s) found. Press any key to return."
        )
        self._set_help(" Any key → return to menu")
        self._mode = MODE_HIGHLIGHT  # wait for keypress to dismiss

    def _render_document_with_highlight(self, hi_row: int, hi_col: int, hi_word: str) -> None:
        """Render document, highlighting the current error word."""
        lines_out = []
        for row, line in enumerate(self._state.buffer):
            if row == hi_row:
                before = line[:hi_col]
                word = line[hi_col:hi_col + len(hi_word)]
                after = line[hi_col + len(hi_word):]
                out = f"{before}[reverse]{word}[/reverse]{after}"
            else:
                out = line
            lines_out.append(out)
        self._set_body("\n".join(lines_out))

    # ------------------------------------------------------------------
    # Widget helpers
    # ------------------------------------------------------------------

    def _set_message(self, msg: str) -> None:
        if self.is_mounted:
            self.query_one("#pr-message", Static).update(f" {msg}")

    def _set_body(self, content: str) -> None:
        if self.is_mounted:
            self.query_one("#pr-body", Static).update(content)

    def _set_help(self, text: str) -> None:
        if self.is_mounted:
            self.query_one("#pr-help", Static).update(text)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_exit_proofreader(self) -> None:
        self.app.pop_screen()  # type: ignore[attr-defined]
