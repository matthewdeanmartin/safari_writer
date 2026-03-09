"""Main Menu screen — the hub for all Safari Writer operations."""

from datetime import datetime

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import Static

from safari_writer.path_utils import leaf_name

# Column 1: document operations
COL1_ITEMS = [
    ("C", "reate File", "create"),
    ("E", "dit File", "edit"),
    ("V", "erify Spelling", "verify"),
    ("P", "rint File", "print"),
    ("G", "lobal Format", "global_format"),
    ("M", "ail Merge", "mail_merge"),
]

# Column 2: file/disk operations
COL2_ITEMS = [
    ("1", " Index Current Folder", "index1"),
    ("2", " Index External Drive", "index2"),
    ("L", "oad File", "load"),
    ("S", "ave File", "save"),
    ("A", " Save As...", "save_as"),
    ("D", "elete File", "delete"),
    ("F", "older (New)", "new_folder"),
    ("Q", "uit", "quit"),
]

# Column 3: tools & extras (separator + special items)
COL3_ITEMS = [
    ("O", "pen Safari DOS", "safari_dos"),
    ("H", "elp Chat", "safari_chat"),
    ("N", " et Safari Fed", "safari_fed"),
    ("R", "un Safari REPL", "safari_repl"),
    ("X", " Style Switcher", "style_switcher"),
    ("T", "ry Demo Mode", "demo"),
]

# Combined for binding generation
MENU_ITEMS = COL1_ITEMS + COL2_ITEMS + COL3_ITEMS

MENU_CSS = """
MainMenuScreen {
    background: $background;
    layout: vertical;
}

#menu-body {
    height: 1fr;
    align: center middle;
}

#menu-container {
    width: 78;
    height: auto;
    border: solid $accent;
    background: $surface;
    padding: 1 2;
}

#title {
    text-align: center;
    text-style: bold;
    margin-bottom: 1;
    color: $accent;
}

#menu-columns {
    layout: horizontal;
    height: auto;
}

#menu-col-1, #menu-col-2, #menu-col-3 {
    width: 1fr;
    height: auto;
}

.menu-item {
    height: 1;
    color: $foreground;
}

.menu-separator {
    height: 1;
    color: $secondary;
}

.menu-key {
    color: $accent;
    text-style: bold underline;
}

#menu-footer {
    dock: bottom;
    height: 2;
    layout: vertical;
}

#context-bar {
    height: 1;
    background: $secondary;
    color: $foreground;
    padding: 0 1;
}

#status-bar {
    height: 1;
    background: $primary;
    color: $foreground;
    padding: 0 1;
    layout: horizontal;
}

#status-text {
    width: 1fr;
    height: 1;
}

#status-clock {
    width: auto;
    height: 1;
}
"""


class MenuItem(Static):
    def __init__(self, key: str, label: str) -> None:
        markup = f"[bold underline]{key}[/]{label}"
        super().__init__(markup, classes="menu-item")


class MainMenuScreen(Screen):
    CSS = MENU_CSS

    BINDINGS = [
        Binding("c", "menu_action('create')", "Create File", show=False),
        Binding("e", "menu_action('edit')", "Edit File", show=False),
        Binding("v", "menu_action('verify')", "Verify Spelling", show=False),
        Binding("p", "menu_action('print')", "Print File", show=False),
        Binding("g", "menu_action('global_format')", "Global Format", show=False),
        Binding("m", "menu_action('mail_merge')", "Mail Merge", show=False),
        Binding("1", "menu_action('index1')", "Index Current Folder", show=False),
        Binding("2", "menu_action('index2')", "Index External Drive", show=False),
        Binding("l", "menu_action('load')", "Load File", show=False),
        Binding("s", "menu_action('save')", "Save File", show=False),
        Binding("a", "menu_action('save_as')", "Save As", show=False),
        Binding("d", "menu_action('delete')", "Delete File", show=False),
        Binding("f", "menu_action('new_folder')", "New Folder", show=False),
        Binding("q", "menu_action('quit')", "Quit", show=False),
        Binding("o", "menu_action('safari_dos')", "Open Safari DOS", show=False),
        Binding("h", "menu_action('safari_chat')", "Help Chat", show=False),
        Binding("n", "menu_action('safari_fed')", "Open Safari Fed", show=False),
        Binding("r", "menu_action('safari_repl')", "Run Safari REPL", show=False),
        Binding("x", "menu_action('style_switcher')", "Style Switcher", show=False),
        Binding("t", "menu_action('demo')", "Try Demo Mode", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._message = ""
        self._clock_timer: Timer | None = None

    def compose(self) -> ComposeResult:
        from textual.containers import Container, Horizontal

        with Container(id="menu-body"):
            with Container(id="menu-container"):
                yield Static("*** SAFARI WRITER ***", id="title")
                with Horizontal(id="menu-columns"):
                    with Container(id="menu-col-1"):
                        for key, label, _ in COL1_ITEMS:
                            yield MenuItem(key, label)
                    with Container(id="menu-col-2"):
                        for key, label, _ in COL2_ITEMS:
                            yield MenuItem(key, label)
                    with Container(id="menu-col-3"):
                        yield Static("--- Tools ---", classes="menu-separator")
                        for key, label, _ in COL3_ITEMS:
                            yield MenuItem(key, label)

        with Container(id="menu-footer"):
            yield Static(self._context_text(), id="context-bar")
            with Horizontal(id="status-bar"):
                yield Static(self._status_line(), id="status-text")
                yield Static(self._clock_text(), id="status-clock")

    def _clock_text(self) -> str:
        now = datetime.now()
        return now.strftime("%Y-%m-%d %H:%M:%S")

    def _update_clock(self) -> None:
        try:
            self.query_one("#status-clock", Static).update(self._clock_text())
        except Exception:
            pass

    def _status_text(self) -> str:
        state = self.app.state  # type: ignore[attr-defined]
        return f" Bytes Free: {state.bytes_free:,}"

    def _status_line(self) -> str:
        return f" {self._message}" if self._message else self._status_text()

    def _context_text(self) -> str:
        state = self.app.state  # type: ignore[attr-defined]
        edit_file = self._display_name(state.filename, "(new document)")
        merge_filename = (
            state.mail_merge_db.filename if state.mail_merge_db is not None else ""
        )
        merge_file = self._display_name(merge_filename, "(no merge data)")
        return f" Edit: {edit_file}   Merge: {merge_file}"

    def _display_name(self, filename: str, empty_label: str) -> str:
        if not filename:
            return empty_label
        return leaf_name(filename)

    def _refresh_footer(self) -> None:
        if not self.is_mounted:
            return
        self.query_one("#context-bar", Static).update(self._context_text())
        self.query_one("#status-text", Static).update(self._status_line())
        self._update_clock()

    def on_mount(self) -> None:
        self._refresh_footer()
        self._clock_timer = self.set_interval(1, self._update_clock)

    def on_show(self) -> None:
        self._refresh_footer()

    def on_screen_resume(self) -> None:
        self._refresh_footer()

    def set_message(self, msg: str) -> None:
        self._message = msg
        self._refresh_footer()

    def action_menu_action(self, action: str) -> None:
        self.app.handle_menu_action(action)  # type: ignore[attr-defined]
