"""Main Menu screen — the hub for all Safari Writer operations."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Static

from safari_writer.path_utils import leaf_name

# Left column: document operations
LEFT_ITEMS = [
    ("C", "reate File", "create"),
    ("E", "dit File", "edit"),
    ("T", "ry Demo Mode", "demo"),
    ("V", "erify Spelling", "verify"),
    ("P", "rint File", "print"),
    ("G", "lobal Format", "global_format"),
    ("M", "ail Merge", "mail_merge"),
]

# Right column: file/system operations (Index starts the column)
RIGHT_ITEMS = [
    ("1", " Index Current Folder", "index1"),
    ("2", " Index External Drive", "index2"),
    ("O", "pen Safari DOS", "safari_dos"),
    ("L", "oad File", "load"),
    ("S", "ave File", "save"),
    ("A", " Save As...", "save_as"),
    ("D", "elete File", "delete"),
    ("F", "older (New)", "new_folder"),
    ("X", " Style Switcher", "style_switcher"),
    ("Q", "uit", "quit"),
]

# Combined for binding generation
MENU_ITEMS = LEFT_ITEMS + RIGHT_ITEMS

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
    width: 72;
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

#menu-col-left, #menu-col-right {
    width: 1fr;
    height: auto;
}

.menu-item {
    height: 1;
    color: $foreground;
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
        Binding("t", "menu_action('demo')", "Try Demo Mode", show=False),
        Binding("v", "menu_action('verify')", "Verify Spelling", show=False),
        Binding("p", "menu_action('print')", "Print File", show=False),
        Binding("g", "menu_action('global_format')", "Global Format", show=False),
        Binding("m", "menu_action('mail_merge')", "Mail Merge", show=False),
        Binding("1", "menu_action('index1')", "Index Current Folder", show=False),
        Binding("2", "menu_action('index2')", "Index External Drive", show=False),
        Binding("o", "menu_action('safari_dos')", "Open Safari DOS", show=False),
        Binding("l", "menu_action('load')", "Load File", show=False),
        Binding("s", "menu_action('save')", "Save File", show=False),
        Binding("a", "menu_action('save_as')", "Save As", show=False),
        Binding("d", "menu_action('delete')", "Delete File", show=False),
        Binding("f", "menu_action('new_folder')", "New Folder", show=False),
        Binding("x", "menu_action('style_switcher')", "Style Switcher", show=False),
        Binding("q", "menu_action('quit')", "Quit", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._message = ""

    def compose(self) -> ComposeResult:
        from textual.containers import Container, Horizontal

        with Container(id="menu-body"):
            with Container(id="menu-container"):
                yield Static("*** SAFARI WRITER ***", id="title")
                with Horizontal(id="menu-columns"):
                    with Container(id="menu-col-left"):
                        for key, label, _ in LEFT_ITEMS:
                            yield MenuItem(key, label)
                    with Container(id="menu-col-right"):
                        for key, label, _ in RIGHT_ITEMS:
                            yield MenuItem(key, label)

        with Container(id="menu-footer"):
            yield Static(self._context_text(), id="context-bar")
            yield Static(self._status_line(), id="status-bar")

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
        self.query_one("#status-bar", Static).update(self._status_line())

    def on_mount(self) -> None:
        self._refresh_footer()

    def on_show(self) -> None:
        self._refresh_footer()

    def on_screen_resume(self) -> None:
        self._refresh_footer()

    def set_message(self, msg: str) -> None:
        self._message = msg
        self._refresh_footer()

    def action_menu_action(self, action: str) -> None:
        self.app.handle_menu_action(action)  # type: ignore[attr-defined]
