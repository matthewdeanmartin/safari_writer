"""Proofreader screen — integrated spelling verification module."""

from __future__ import annotations

from pathlib import Path
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Static
from textual import events
import safari_writer.locale_info as _locale_info


def _(s: str) -> str:
    return _locale_info.get_translation().gettext(s)


_DEFAULT_PERSONAL_DICT = "personal.dict"


def _default_personal_dict_path() -> str:
    """Return the default personal dictionary path under ~/.safari/."""
    return str(Path.home() / ".safari" / _DEFAULT_PERSONAL_DICT)


from safari_writer.proofing import (
    check_word as _check_word,
    dict_lookup as _dict_lookup,
    extract_words as _extract_words,
    load_personal_dictionary,
    make_checker as _make_checker,
)
from safari_writer.state import AppState
from safari_writer.typed import SpellChecker, WordMatch


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

PR_CSS = """
ProofreaderScreen {
    align: center middle;
    background: $background;
}

#pr-outer {
    width: 76;
    height: 28;
    border: solid $accent;
    background: $surface;
    padding: 0;
}

#pr-message {
    height: 1;
    background: $primary;
    color: $foreground;
    padding: 0 1;
}

#pr-title {
    height: 1;
    text-align: center;
    text-style: bold;
    color: $accent;
    margin-top: 1;
}

#pr-body {
    height: 1fr;
    padding: 1 2;
    color: $foreground;
    overflow-y: auto;
}

#pr-help {
    height: 1;
    background: $primary;
    color: $foreground;
    padding: 0 1;
}
"""

# ---------------------------------------------------------------------------
# Mode constants
# ---------------------------------------------------------------------------

MODE_MENU = "menu"
MODE_HIGHLIGHT = "highlight"
MODE_PRINT = "print"
MODE_CORRECT = "correct"
MODE_CORRECT_MENU = "correct_menu"
MODE_CORRECT_WORD = "correct_word"
MODE_CORRECT_CONFIRM = "correct_confirm"
MODE_DICT_SEARCH = "dict_search"
MODE_DICT_RESULTS = "dict_results"
MODE_SAVE_PERSONAL = "save_personal"
MODE_LOAD_PERSONAL = "load_personal"


class ProofreaderScreen(Screen):
    """Integrated spelling verification module."""

    CSS = PR_CSS

    BINDINGS = [
        Binding("escape", "exit_proofreader", "Exit", show=False),
    ]

    def __init__(
        self,
        state: AppState,
        initial_mode: str | None = None,
        personal_dict_paths: list[Path] | tuple[Path, ...] | None = None,
    ) -> None:
        super().__init__()
        self._state = state
        self._initial_mode = initial_mode
        self._personal_dict_paths = tuple(personal_dict_paths or ())
        self._checker: SpellChecker | None = None
        self._checker_loaded = False
        self._personal: set[str] = set()
        self._mode = MODE_MENU
        self._input_buf = ""
        self._message_text = ""
        self._body_text = ""
        self._help_text = ""

        self._words: list[WordMatch] = []
        self._scan_idx = 0
        self._errors: list[WordMatch] = []

        self._current_error: WordMatch | None = None
        self._replacement: str = ""

        self._dict_results: list[str] = []
        self._dict_page = 0
        self._dict_prefix = ""
        self._dict_exact = False
        self._from_correct = False
        self._enter_menu()

    # ------------------------------------------------------------------
    # Compose
    # ------------------------------------------------------------------

    def _title_text(self) -> str:
        from safari_writer.locale_info import LOCALE

        lang = self._state.doc_language or LOCALE
        return _("*** SAFARI WRITER — PROOFREADER ***  [Dict: {lang}]").format(lang=lang)

    def compose(self) -> ComposeResult:
        from textual.containers import Container

        with Container(id="pr-outer"):
            yield Static(self._message_text, id="pr-message")
            yield Static(self._title_text(), id="pr-title")
            yield Static(self._body_text, id="pr-body")
            yield Static(self._help_text, id="pr-help")

    def on_mount(self) -> None:
        self._enter_menu()
        for path in self._personal_dict_paths:
            self._personal.update(load_personal_dictionary(path))
        if self._initial_mode == "highlight":
            self._enter_highlight()
        elif self._initial_mode == "print":
            self._enter_print()
        elif self._initial_mode == "correct":
            self._enter_correct()
        elif self._initial_mode == "search":
            self._enter_dict_search(from_correct=False)

    def _ensure_checker(self) -> SpellChecker | None:
        if not self._checker_loaded:
            lang = self._state.doc_language or None
            self._checker = _make_checker(lang)
            self._checker_loaded = True
        return self._checker

    def _require_current_error(self) -> WordMatch:
        if self._current_error is None:
            raise RuntimeError("Proofreader correction state is unavailable.")
        return self._current_error

    # ------------------------------------------------------------------
    # Mode entry helpers
    # ------------------------------------------------------------------

    def _enter_menu(self) -> None:
        from safari_writer.locale_info import LOCALE

        self._mode = MODE_MENU
        lang = self._state.doc_language or LOCALE
        self._set_body(
            f"[bold]Dictionary:[/] {lang}\n\n"
            "[bold]H[/]  Highlight Errors\n"
            "[bold]P[/]  Print Errors (list on-screen)\n"
            "[bold]C[/]  Correct Errors\n"
            "[bold]S[/]  Dictionary Search\n"
            "[bold]L[/]  Load Personal Dictionary\n"
            "[bold]W[/]  Write (save) Personal Dictionary\n"
            "\n"
            "[dim]Esc  Return to Main Menu[/]"
        )
        self._set_message(f"Proofing in [{lang}]. Select a mode.")
        self._set_help(
            " H Highlight  P Print  C Correct  S Search  L Load  W Write  Esc Exit"
        )

    def _enter_highlight(self) -> None:
        self._mode = MODE_HIGHLIGHT
        self._errors = []
        self._ensure_checker()
        self._words = _extract_words(self._state.buffer)
        self._set_message("Scanning document… (any key to abort)")
        self._set_help(" Any key to abort scan")
        self._render_highlight_scan()

    def _enter_print(self) -> None:
        self._mode = MODE_PRINT
        checker = self._ensure_checker()
        self._words = _extract_words(self._state.buffer)
        self._errors = [
            (r, c, w)
            for r, c, w in self._words
            if not _check_word(w, checker, self._state.kept_spellings, self._personal)
        ]
        if not self._errors:
            self._set_body(_("No spelling errors found."))
        else:
            lines = [f"[bold]Spelling Errors ({len(self._errors)} found):[/]\n"]
            for r, c, w in self._errors:
                lines.append(f"  Line {r + 1}, col {c + 1}: [reverse]{w}[/]")
            self._set_body("\n".join(lines))
        self._set_message(_("Scan complete. Press any key to return to menu."))
        self._set_help(" Any key → return to menu")

    def _enter_correct(self) -> None:
        self._mode = MODE_CORRECT
        self._ensure_checker()
        self._words = _extract_words(self._state.buffer)
        self._scan_idx = 0
        self._errors = []
        self._advance_to_next_error()

    def _advance_to_next_error(self) -> None:
        checker = self._ensure_checker()
        while self._scan_idx < len(self._words):
            r, c, w = self._words[self._scan_idx]
            if not _check_word(w, checker, self._state.kept_spellings, self._personal):
                self._current_error = (r, c, w)
                self._enter_correct_menu()
                return
            self._scan_idx += 1
        self._current_error = None
        kept_count = len(self._state.kept_spellings)
        self._set_body(
            f"[bold green]Spell check complete.[/]\n\n"
            f"Words kept this session: {kept_count}\n\n"
            f"[bold]W[/]  Save kept words to personal dictionary\n"
            f"[bold]Esc[/]  Return to menu"
        )
        self._set_message(_("No more errors found."))
        self._set_help(" W Save personal dict  Esc Return to menu")
        self._mode = MODE_MENU

    def _enter_correct_menu(self) -> None:
        self._mode = MODE_CORRECT_MENU
        r, c, w = self._require_current_error()
        self._render_document_with_highlight(r, c, w)
        self._set_message(
            f"Unrecognized: [reverse]{w}[/]  — C Correct  S Search dict  Enter Keep"
        )
        self._set_help(
            " C Correct Word  S Search Dictionary  Enter Keep This Spelling  Esc Abort"
        )

    def _enter_dict_search(self, from_correct: bool = False) -> None:
        self._mode = MODE_DICT_SEARCH
        self._input_buf = ""
        self._from_correct = from_correct
        self._set_message(
            "Dictionary Search: type 2+ letters, Enter to search, Esc to cancel"
        )
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
            default = _default_personal_dict_path()
            self._input_buf = default
            self._set_message(
                "Load Personal Dictionary: edit path or Enter to confirm"
            )
            self._set_body(f"Load personal dictionary file:\n\n> {default}")
            self._set_help(" Enter Load  Esc Cancel")
        elif k == "w":
            self._mode = MODE_SAVE_PERSONAL
            default = _default_personal_dict_path()
            self._input_buf = default
            self._set_message(
                "Save Personal Dictionary: edit path or Enter to confirm"
            )
            self._set_body(f"Save personal dictionary to file:\n\n> {default}")
            self._set_help(" Enter Save  Esc Cancel")
        elif key == "escape":
            self.action_exit_proofreader()

    def _handle_correct_menu_key(self, key: str) -> None:
        k = key.lower()
        if k == "c":
            self._mode = MODE_CORRECT_WORD
            self._input_buf = ""
            _, _, w = self._require_current_error()
            self._set_message(f"Correct [{w}]: type replacement word, Enter to confirm")
            self._set_help(" Enter Confirm  Esc Cancel")
        elif k == "s":
            self._enter_dict_search(from_correct=True)
        elif key == "enter":
            _, _, w = self._require_current_error()
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
                _, _, w = self._require_current_error()
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
        _, _, w = self._require_current_error()
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
        r, c, w = self._require_current_error()
        repl = self._replacement
        line = self._state.buffer[r]
        if line[c : c + len(w)] == w:
            self._state.buffer[r] = line[:c] + repl + line[c + len(w) :]
            self._state.modified = True
        self._set_message(f"Replaced '{w}' with '{repl}'.")
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
            exact, results = _dict_lookup(prefix, self._ensure_checker())
            self._dict_prefix = prefix
            self._dict_exact = exact
            self._dict_results = results
            self._dict_page = 0
            self._show_dict_results_page()
        elif key == "backspace":
            self._input_buf = self._input_buf[:-1]
            self._set_body(
                f"Enter search prefix (at least 2 letters):\n\n> {self._input_buf}"
            )
        elif event.character and event.character.isprintable():
            self._input_buf += event.character
            self._set_body(
                f"Enter search prefix (at least 2 letters):\n\n> {self._input_buf}"
            )

    def _show_dict_results_page(self) -> None:
        self._mode = MODE_DICT_RESULTS
        page_size = 126
        results = self._dict_results
        exact = getattr(self, "_dict_exact", False)
        start = self._dict_page * page_size
        page = results[start : start + page_size]
        total = len(results)

        if not page and not exact:
            self._set_body(f"No words found for '{self._dict_prefix}'.")
            self._set_message("No matches. Press any key to search again.")
            self._set_help(" Any key → new search")
            return

        lines: list[str] = []
        if exact:
            lines.append(
                f"[bold green]'{self._dict_prefix}'[/] is a valid word.\n"
            )

        if page:
            cols = 3
            col_width = 26
            col_lines = [page[i::cols] for i in range(cols)]
            max_rows = max(len(c) for c in col_lines)
            label = "Related" if exact else "Suggestions"
            lines.append(
                f"[bold]{label} for '{self._dict_prefix}'[/]"
                f"  ({total} found)\n"
            )
            for row_i in range(max_rows):
                row_parts = []
                for col_i in range(cols):
                    word = (
                        col_lines[col_i][row_i]
                        if row_i < len(col_lines[col_i])
                        else ""
                    )
                    row_parts.append(word.ljust(col_width))
                lines.append("".join(row_parts))
        elif exact:
            lines.append("[dim]No additional suggestions.[/]")

        has_next = (start + page_size) < total
        has_prev = self._dict_page > 0
        nav = []
        if has_prev:
            nav.append("PgUp Prev")
        if has_next:
            nav.append("PgDn Next")
        nav.append("Esc New search")

        self._set_body("\n".join(lines))
        page_count = max(1, (total - 1) // page_size + 1) if total else 1
        self._set_message(
            f"Page {self._dict_page + 1} of {page_count}"
        )
        self._set_help("  ".join(nav))

    def _handle_dict_results_key(self, key: str) -> None:
        page_size = 126
        if key == "pagedown" and (self._dict_page + 1) * page_size < len(
            self._dict_results
        ):
            self._dict_page += 1
            self._show_dict_results_page()
        elif key == "pageup" and self._dict_page > 0:
            self._dict_page -= 1
            self._show_dict_results_page()
        elif key == "escape":
            self._enter_dict_search(from_correct=self._from_correct)
        else:
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
            self._set_message(_("No words to save."))
            self._enter_menu()
            return
        words = words[:256]
        try:
            out_path = Path(filename)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(" ".join(words))
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
            new_words = load_personal_dictionary(Path(filename))
            self._personal.update(new_words)
            self._set_message(f"Loaded {len(new_words)} words from '{filename}'.")
        except OSError as e:
            self._set_message(f"Error loading: {e}")
        self._enter_menu()

    # ------------------------------------------------------------------
    # Highlight scan renderer
    # ------------------------------------------------------------------

    def _render_highlight_scan(self) -> None:
        words = _extract_words(self._state.buffer)
        error_positions: set[tuple[int, int, int]] = set()
        for r, c, w in words:
            if not _check_word(
                w, self._ensure_checker(), self._state.kept_spellings, self._personal
            ):
                error_positions.add((r, c, len(w)))

        lines_out = []
        for row, line in enumerate(self._state.buffer):
            mask = [False] * len(line)
            for er, ec, ew in error_positions:
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
            _("Highlight scan complete — {error_count} error(s) found. Press any key to return.").format(error_count=error_count)
        )
        self._set_help(" Any key → return to menu")
        self._mode = MODE_HIGHLIGHT

    def _render_document_with_highlight(
        self, hi_row: int, hi_col: int, hi_word: str
    ) -> None:
        lines_out = []
        for row, line in enumerate(self._state.buffer):
            if row == hi_row:
                before = line[:hi_col]
                word = line[hi_col : hi_col + len(hi_word)]
                after = line[hi_col + len(hi_word) :]
                out = f"{before}[reverse]{word}[/reverse]{after}"
            else:
                out = line
            lines_out.append(out)
        self._set_body("\n".join(lines_out))

    # ------------------------------------------------------------------
    # Widget helpers
    # ------------------------------------------------------------------

    def _set_message(self, msg: str) -> None:
        self._message_text = f" {msg}"
        if self.is_mounted:
            self.query_one("#pr-message", Static).update(self._message_text)

    def _set_body(self, content: str) -> None:
        self._body_text = content
        if self.is_mounted:
            self.query_one("#pr-body", Static).update(self._body_text)

    def _set_help(self, text: str) -> None:
        self._help_text = text
        if self.is_mounted:
            self.query_one("#pr-help", Static).update(self._help_text)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_exit_proofreader(self) -> None:
        self.app.pop_screen()  # type: ignore[attr-defined]
