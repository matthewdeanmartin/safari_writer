"""Textual screens for Safari REPL."""

# -----------------------------------------------------------------------
# Textual reserved keys (do not rebind without care):
#   Ctrl+Q   quit (App default, priority)
#   Ctrl+C   copy text / help-quit (App + Screen default)
#   Ctrl+P   command palette (App.COMMAND_PALETTE_BINDING)
#   Tab      focus next widget (Screen default)
#   Shift+Tab focus previous widget (Screen default)
# -----------------------------------------------------------------------

from __future__ import annotations

import io
from pathlib import Path
from typing import cast

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import RichLog, Static

from safari_basic.interpreter import BasicError
from safari_basic.repl import SafariREPL
from safari_repl.state import ReplState

__all__ = [
    "ReplMainMenuScreen",
    "ReplEditorScreen",
]

REPL_CSS = """
Screen {
    background: $background;
    color: $foreground;
}

ReplMainMenuScreen {
    align: center middle;
    background: $background;
}

#repl-menu-container {
    width: 46;
    height: auto;
    border: solid $accent;
    background: $surface;
    padding: 1 2;
}

#repl-menu-title {
    text-align: center;
    text-style: bold;
    margin-bottom: 1;
    color: $accent;
}

.menu-item {
    height: 1;
    color: $foreground;
}

#repl-status-bar {
    dock: bottom;
    height: 1;
    background: $primary;
    color: $foreground;
    padding: 0 1;
}

/* REPL screen */
#repl-container {
    width: 100%;
    height: 100%;
}

#repl-header {
    dock: top;
    height: 3;
    background: $primary;
    color: $foreground;
    padding: 0 1;
}

#repl-title {
    color: $accent;
    text-style: bold;
    text-align: center;
}

#repl-file {
    color: $foreground;
}

#repl-output {
    height: 1fr;
    padding: 0 1;
    color: $foreground;
}

#repl-input-row {
    dock: bottom;
    height: 3;
    background: $surface;
    padding: 0 1;
}

#repl-prompt-label {
    color: $accent;
    text-style: bold;
}

#repl-input-line {
    color: $foreground;
}

#repl-footer {
    dock: bottom;
    height: 1;
    background: $primary;
    color: $foreground;
    padding: 0 1;
}
"""


class MenuItem(Static):
    """Menu item with selection highlighting."""

    def __init__(self, key: str, label: str, action: str) -> None:
        self.key_char = key
        self.label_text = label
        self.action_name = action
        super().__init__("", classes="menu-item")
        self._is_selected = False

    def set_selected(self, selected: bool) -> None:
        self._is_selected = selected
        self._update_markup()

    def _update_markup(self) -> None:
        markup = f"[bold underline]{self.key_char}[/]{self.label_text}"
        if self._is_selected:
            markup = f"[reverse]{markup}[/reverse]"
        self.update(markup)

    def on_mount(self) -> None:
        self._update_markup()


class ReplMainMenuScreen(Screen):
    """Atari BASIC REPL main menu."""

    CSS = REPL_CSS

    MENU_ITEMS = [
        ("R", "un REPL (interactive)", "repl"),
        ("L", "oad .BAS file", "load"),
        ("H", "elp", "help"),
        ("Q", "uit", "quit"),
    ]

    BINDINGS = [
        Binding("r", "menu_action('repl')", "REPL", show=False),
        Binding("l", "menu_action('load')", "Load", show=False),
        Binding("h,f1", "menu_action('help')", "Help", show=False),
        Binding("q,escape", "menu_action('quit')", "Quit", show=False),
        # Arrow navigation
        Binding("up", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("enter", "activate", "Activate", show=False),
    ]

    def __init__(self, state: ReplState) -> None:
        super().__init__()
        self._state = state
        self._selected_index = 0
        self._menu_widgets: list[MenuItem] = []

    def compose(self) -> ComposeResult:
        with Container(id="repl-menu-container"):
            yield Static("*** SAFARI REPL ***", id="repl-menu-title")
            yield Static("Atari BASIC Interpreter", classes="menu-item")
            yield Static("", classes="menu-item")
            for key, label, action in self.MENU_ITEMS:
                yield MenuItem(key, label, action)
        file_label = (
            f" Loaded: {self._state.loaded_path.name}"
            if self._state.loaded_path
            else " No file loaded"
        )
        yield Static(file_label, id="repl-status-bar")

    def on_mount(self) -> None:
        self._menu_widgets = list(self.query(MenuItem))
        self._refresh_menu()

    def _refresh_menu(self) -> None:
        for i, widget in enumerate(self._menu_widgets):
            widget.set_selected(i == self._selected_index)

    def action_cursor_up(self) -> None:
        if self._selected_index > 0:
            self._selected_index -= 1
            self._refresh_menu()

    def action_cursor_down(self) -> None:
        if self._selected_index < len(self._menu_widgets) - 1:
            self._selected_index += 1
            self._refresh_menu()

    def action_activate(self) -> None:
        if 0 <= self._selected_index < len(self._menu_widgets):
            action = self._menu_widgets[self._selected_index].action_name
            self.action_menu_action(action)

    def action_menu_action(self, action: str) -> None:
        app = cast("SafariReplAppProtocol", self.app)
        if action == "repl":
            app.open_repl()
        elif action == "load":
            app.load_file()
        elif action == "help":
            app.open_help()
        elif action == "quit":
            app.quit_repl()


class ReplEditorScreen(Screen):
    """Interactive Atari BASIC REPL screen with LIST, RUN, and editor handoff."""

    CSS = REPL_CSS

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=True),
        Binding("f2", "action_list", "LIST", show=True),
        Binding("f5", "action_run", "RUN", show=True),
        Binding("f9", "action_open_in_writer", "Edit in Writer", show=True),
    ]

    def __init__(self, state: ReplState) -> None:
        super().__init__()
        self._state = state
        self._buf = io.StringIO()
        self._repl = SafariREPL(out_stream=self._buf)
        self._input_buffer = ""
        self._history_cursor = -1  # -1 means at the bottom (new input)
        self._temp_input = "" # Store what user typed before browsing history
        self._pending_output: list[str] = list(state.output_lines)

        # If a file is already loaded, load its program lines into the interpreter
        if state.loaded_path and state.loaded_path.exists():
            self._load_file_into_interp(state.loaded_path)

    def _load_file_into_interp(self, path: Path) -> None:
        try:
            code = path.read_text(encoding="utf-8")
        except OSError as exc:
            self._pending_output.append(f"ERROR: Cannot read {path.name}: {exc}")
            return
        self._repl.interpreter.reset()
        self._buf = io.StringIO()
        self._repl.interpreter.out_stream = self._buf
        self._repl.out_stream = self._buf
        for raw in code.splitlines():
            stripped = raw.strip()
            if stripped:
                self._repl.interpreter.add_program_line(stripped)
        self._repl.current_filename = str(path)
        self._repl.modified = False
        self._pending_output.append(f"Loaded: {path.name}")
        self._pending_output.append(f"{len(self._repl.interpreter.line_order)} line(s) in program.")

    def compose(self) -> ComposeResult:
        with Container(id="repl-container"):
            file_label = (
                self._state.loaded_path.name if self._state.loaded_path else "(none)"
            )
            with Container(id="repl-header"):
                yield Static("SAFARI REPL  —  Atari BASIC", id="repl-title")
                yield Static(f"File: {file_label}", id="repl-file")
            yield RichLog(
                highlight=False,
                markup=False,
                auto_scroll=True,
                id="repl-output",
            )
            with Container(id="repl-input-row"):
                yield Static("READY", id="repl-prompt-label")
                yield Static(self._render_input(), id="repl-input-line")
            yield Static(self._render_status(), id="repl-footer")

    def on_mount(self) -> None:
        log = self.query_one("#repl-output", RichLog)
        for line in self._pending_output:
            log.write(line)
        self._pending_output.clear()

    @staticmethod
    def _escape_markup(text: str) -> str:
        """Escape Rich markup brackets in plain text."""
        return text.replace("[", "\\[")

    def _render_input(self) -> str:
        safe = self._escape_markup(self._input_buffer)
        return f"> {safe}[reverse] [/reverse]"

    def _render_status(self) -> str:
        line_count = len(self._repl.interpreter.line_order)
        file_name = self._state.loaded_path.name if self._state.loaded_path else "Untitled"
        modified = " *" if self._repl.modified else ""
        return f" {file_name}{modified}  {line_count} lines  Esc back  F2 LIST  F5 RUN  F9 Writer"

    def _refresh_input(self) -> None:
        self.query_one("#repl-input-line", Static).update(self._render_input())
        # Also refresh footer for status updates
        self.query_one("#repl-footer", Static).update(self._render_status())

    def _append_output(self, text: str) -> None:
        log = self.query_one("#repl-output", RichLog)
        for line in text.splitlines():
            log.write(line)
            self._state.output_lines.append(line)

    def _flush_interp_output(self) -> None:
        text = self._buf.getvalue()
        if text:
            self._append_output(text)
        # Reset buffer
        self._buf = io.StringIO()
        self._repl.interpreter.out_stream = self._buf
        self._repl.out_stream = self._buf

    def _execute_line(self, line: str) -> None:
        self._append_output(f"> {line}")
        try:
            result = self._repl.process_line(line)
            if not result:
                # BYE/EXIT/QUIT — go back to menu
                self._flush_interp_output()
                self.action_go_back()
                return
        except Exception as exc:  # noqa: BLE001
            self._append_output(f"ERROR: {exc}")
        self._flush_interp_output()

    def on_key(self, event: events.Key) -> None:
        if event.key == "enter":
            line = self._input_buffer.strip()
            self._input_buffer = ""
            self._history_cursor = -1
            self._temp_input = ""
            if line:
                # Only add to history if it's different from the last entry
                if not self._state.history or self._state.history[-1] != line:
                    self._state.history.append(line)
                self._execute_line(line)
            self._refresh_input()
            event.stop()
        elif event.key == "up":
            if self._state.history:
                if self._history_cursor == -1:
                    self._temp_input = self._input_buffer
                    self._history_cursor = len(self._state.history) - 1
                else:
                    self._history_cursor = max(0, self._history_cursor - 1)
                self._input_buffer = self._state.history[self._history_cursor]
                self._refresh_input()
            event.stop()
        elif event.key == "down":
            if self._history_cursor != -1:
                self._history_cursor += 1
                if self._history_cursor >= len(self._state.history):
                    self._history_cursor = -1
                    self._input_buffer = self._temp_input
                else:
                    self._input_buffer = self._state.history[self._history_cursor]
                self._refresh_input()
            event.stop()
        elif event.key == "backspace":
            self._input_buffer = self._input_buffer[:-1]
            self._history_cursor = -1 # Editing breaks history link
            self._refresh_input()
            event.stop()
        elif event.character and event.character.isprintable():
            self._input_buffer += event.character
            self._history_cursor = -1 # Editing breaks history link
            self._refresh_input()
            event.stop()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_action_list(self) -> None:
        self._execute_line("LIST")
        self._refresh_input()

    def action_action_run(self) -> None:
        self._execute_line("RUN")
        self._refresh_input()

    def action_action_open_in_writer(self) -> None:
        if self._state.loaded_path is None:
            self._append_output("No .BAS file loaded. Use Load from main menu.")
            return
        app = cast("SafariReplAppProtocol", self.app)
        app.request_writer_launch(self._state.loaded_path)


# Protocol stub so type checkers understand app calls from screens
class SafariReplAppProtocol:
    def open_repl(self) -> None: ...
    def load_file(self) -> None: ...
    def open_help(self) -> None: ...
    def quit_repl(self) -> None: ...
    def request_writer_launch(self, path: Path) -> None: ...
