"""Global Format screen — master document layout parameter editor."""

from dataclasses import dataclass

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Static

import safari_writer.locale_info as _locale_info
from safari_writer.state import AppState, GlobalFormat


def _(s: str) -> str:
    return _locale_info.get_translation().gettext(s)


# ---------------------------------------------------------------------------
# Parameter definitions
# ---------------------------------------------------------------------------


@dataclass
class Param:
    key: str  # single letter key
    attr: str  # attribute name on GlobalFormat
    label: str  # full description
    min_val: int
    max_val: int
    hint: str = ""  # optional hint shown on right


PARAMS: list[Param] = [
    Param("T", "top_margin", "Top Margin", 0, 999, 'half-lines (12=1")'),
    Param("B", "bottom_margin", "Bottom Margin", 0, 999, 'half-lines (12=1")'),
    Param("L", "left_margin", "Left Margin", 1, 130, "character spaces"),
    Param("R", "right_margin", "Right Margin", 2, 132, "character spaces"),
    Param("S", "line_spacing", "Line Spacing", 1, 99, "2=single 4=double 6=triple"),
    Param("D", "para_spacing", "Paragraph Spacing", 0, 99, "half-lines"),
    Param("M", "col2_left", "2nd Left Margin", 1, 130, "2nd column left"),
    Param("N", "col2_right", "2nd Right Margin", 2, 132, "2nd column right"),
    Param("G", "type_font", "Type Font", 1, 9, "1=pica 2=cond 3=prop 6=elite"),
    Param("I", "para_indent", "Paragraph Indentation", 0, 99, "spaces (0=block style)"),
    Param("J", "justification", "Justification", 0, 1, "0=ragged 1=justified"),
    Param(
        "Q", "page_number_start", "Page Number Start", 1, 999, "starting page number"
    ),
    Param("Y", "page_length", "Page Length", 1, 999, 'half-lines (132=8.5x11")'),
    Param("W", "page_wait", "Page Wait", 0, 1, "0=off 1=pause each page"),
]

KEY_TO_PARAM: dict[str, Param] = {p.key: p for p in PARAMS}


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

GF_CSS = """
GlobalFormatScreen {
    align: center middle;
    background: $background;
}

#gf-outer {
    width: 70;
    height: auto;
    border: solid $accent;
    background: $surface;
    padding: 0;
}

#gf-message {
    height: 1;
    background: $primary;
    color: $foreground;
    padding: 0 1;
}

#gf-title {
    text-align: center;
    text-style: bold;
    color: $accent;
    height: 1;
    margin: 1 0;
}

#gf-table {
    height: auto;
    padding: 0 2;
}

.gf-row {
    height: 1;
    layout: horizontal;
}

.gf-key {
    width: 3;
    color: $accent;
    text-style: bold underline;
}

.gf-label {
    width: 26;
    color: $foreground;
}

.gf-value {
    width: 6;
    color: $success;
    text-style: bold;
}

.gf-value-editing {
    width: 6;
    color: $warning;
    text-style: bold reverse;
}

.gf-hint {
    color: $foreground;
}

#gf-help {
    height: 1;
    background: $primary;
    color: $foreground;
    padding: 0 1;
    margin-top: 1;
}
"""


# ---------------------------------------------------------------------------
# Row widget
# ---------------------------------------------------------------------------


class GFRow(Static):
    """One parameter row — key, label, value, hint."""

    def __init__(self, param: Param, value: int, editing: bool = False) -> None:
        self._param = param
        self._value = value
        self._editing = editing
        super().__init__(self._row_markup(), classes="gf-row")

    def _row_markup(self) -> str:
        key = f"[bold underline]{self._param.key}[/]"
        label = self._param.label.ljust(25)
        val_str = str(self._value).ljust(5)
        if self._editing:
            val = f"[bold reverse]{val_str}[/]"
        else:
            val = f"[bold]{val_str}[/]"
        hint = f"[dim]{self._param.hint}[/]"
        return f" {key}  {label} {val} {hint}"

    def refresh_value(self, value: int, editing: bool = False) -> None:
        self._value = value
        self._editing = editing
        self.update(self._row_markup())


# ---------------------------------------------------------------------------
# Screen
# ---------------------------------------------------------------------------


class GFLangRow(Static):
    """Special row for the document language selector."""

    def __init__(self, lang: str) -> None:
        self._lang = lang
        super().__init__(self._row_markup(), classes="gf-row")

    def _row_markup(self) -> str:
        display = self._lang or "(auto)"
        return f" [bold underline]K[/]  {'Language'.ljust(25)} [bold]{display.ljust(5)}[/] [dim]spell-check language[/]"

    def refresh_lang(self, lang: str, editing: bool = False) -> None:
        self._lang = lang
        display = lang or "(auto)"
        if editing:
            markup = f" [bold underline]K[/]  {'Language'.ljust(25)} [bold reverse]{display.ljust(5)}[/] [dim]spell-check language[/]"
        else:
            markup = self._row_markup()
        self.update(markup)


class GlobalFormatScreen(Screen):
    """Global Format parameter editor screen."""

    CSS = GF_CSS

    BINDINGS = [
        Binding("escape", "accept_and_exit", "Accept & Exit", show=False),
        Binding("tab", "reset_defaults", "Reset Defaults", show=False),
    ]

    def __init__(self, fmt: GlobalFormat, state: AppState | None = None) -> None:
        super().__init__()
        self._fmt = fmt
        self._state = state
        self._editing_key: str | None = None
        self._input_buf: str = ""
        self._rows: dict[str, GFRow] = {}
        self._lang_row: GFLangRow | None = None

    # ------------------------------------------------------------------
    # Compose
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        from textual.containers import Container

        with Container(id="gf-outer"):
            yield Static("", id="gf-message")
            yield Static(_("*** GLOBAL FORMAT ***"), id="gf-title")
            with Static(id="gf-table"):
                for p in PARAMS:
                    row = GFRow(p, getattr(self._fmt, p.attr))
                    self._rows[p.key] = row
                    yield row
                if self._state is not None:
                    self._lang_row = GFLangRow(self._state.doc_language)
                    yield self._lang_row
            yield Static(
                " Press letter to edit value | [Tab] Reset Defaults | [Esc] Exit",
                id="gf-help",
            )

    def on_mount(self) -> None:
        self.set_message(_("Press a letter key to select a parameter."))

    # ------------------------------------------------------------------
    # Key handling
    # ------------------------------------------------------------------

    def on_key(self, event: events.Key) -> None:
        key = event.key

        if self._editing_key is not None:
            if self._editing_key == "K":
                self._handle_lang_edit_key(key, event)
            else:
                self._handle_edit_key(key)
            event.stop()
            return

        upper_key = key.upper() if len(key) == 1 else key
        if upper_key == "K" and self._state is not None:
            self._start_lang_editing()
            event.stop()
            return
        if upper_key in KEY_TO_PARAM:
            self._start_editing(upper_key)
            event.stop()

    def _start_editing(self, letter: str) -> None:
        param = KEY_TO_PARAM[letter]
        self._editing_key = letter
        self._input_buf = ""
        row = self._rows[letter]
        row.refresh_value(getattr(self._fmt, param.attr), editing=True)
        self.set_message(
            f"{param.label}: enter new value, [Enter] to confirm, [Esc] to cancel"
        )

    def _handle_edit_key(self, key: str) -> None:
        letter = self._editing_key
        if letter is None:
            return
        param = KEY_TO_PARAM[letter]

        if key == "enter":
            self._commit_edit(param)
        elif key == "escape":
            self._cancel_edit(param)
        elif key == "backspace":
            self._input_buf = self._input_buf[:-1]
            self._preview_edit(param)
        elif len(key) == 1 and key.isdigit():
            if len(self._input_buf) < 5:
                self._input_buf += key
                self._preview_edit(param)

    def _preview_edit(self, param: Param) -> None:
        display_val = int(self._input_buf) if self._input_buf else 0
        self._rows[param.key].refresh_value(display_val, editing=True)

    def _commit_edit(self, param: Param) -> None:
        if not self._input_buf:
            self._cancel_edit(param)
            return

        new_val = int(self._input_buf)
        if new_val < param.min_val or new_val > param.max_val:
            self.set_message(
                f"Invalid value {new_val}. Range: {param.min_val}–{param.max_val}"
            )
            return

        setattr(self._fmt, param.attr, new_val)
        self._editing_key = None
        self._input_buf = ""
        self._rows[param.key].refresh_value(new_val, editing=False)
        self.set_message(f"{param.label} set to {new_val}.")

    def _cancel_edit(self, param: Param) -> None:
        original = getattr(self._fmt, param.attr)
        self._editing_key = None
        self._input_buf = ""
        self._rows[param.key].refresh_value(original, editing=False)
        self.set_message(_("Edit cancelled."))

    # ------------------------------------------------------------------
    # Language (K) editing  (i18n Level 1)
    # ------------------------------------------------------------------

    def _start_lang_editing(self) -> None:
        self._editing_key = "K"
        self._input_buf = ""
        if self._lang_row is not None:
            self._lang_row.refresh_lang(
                self._state.doc_language if self._state else "", editing=True
            )
        from safari_writer.locale_info import LOCALE, available_languages

        langs = available_languages()
        hint = (
            f"Available: {', '.join(langs)}" if langs else "No dictionaries installed"
        )
        current_lang = self._state.doc_language if self._state is not None else LOCALE
        self.set_message(
            f"Language (current: {current_lang or LOCALE}): "
            f"type tag or Enter=(auto). {hint}"
        )

    def _handle_lang_edit_key(self, key: str, event: events.Key) -> None:
        if key == "escape":
            self._editing_key = None
            if self._lang_row is not None:
                self._lang_row.refresh_lang(
                    self._state.doc_language if self._state else ""
                )
            self.set_message(_("Edit cancelled."))
        elif key == "enter":
            new_lang = self._input_buf.strip()
            if self._state is not None:
                self._state.doc_language = new_lang
            self._editing_key = None
            if self._lang_row is not None:
                self._lang_row.refresh_lang(new_lang)
            label = new_lang or "(auto — OS locale)"
            self.set_message(f"Language set to {label}.")
        elif key == "backspace":
            self._input_buf = self._input_buf[:-1]
            if self._lang_row is not None:
                self._lang_row.refresh_lang(self._input_buf or "…", editing=True)
        elif event.character and event.character.isprintable():
            if len(self._input_buf) < 10:
                self._input_buf += event.character
                if self._lang_row is not None:
                    self._lang_row.refresh_lang(self._input_buf, editing=True)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_accept_and_exit(self) -> None:
        if self._editing_key is not None:
            if self._editing_key == "K":
                self._editing_key = None
                if self._lang_row is not None:
                    self._lang_row.refresh_lang(
                        self._state.doc_language if self._state else ""
                    )
                self.set_message(_("Edit cancelled."))
            else:
                param = KEY_TO_PARAM[self._editing_key]
                self._cancel_edit(param)
            return
        self.app.pop_screen()

    def action_reset_defaults(self) -> None:
        if self._editing_key is not None:
            return
        self._fmt.reset_defaults()
        for p in PARAMS:
            self._rows[p.key].refresh_value(getattr(self._fmt, p.attr), editing=False)
        self.set_message(_("All settings reset to factory defaults."))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def set_message(self, msg: str) -> None:
        self.query_one("#gf-message", Static).update(f" {msg}")
