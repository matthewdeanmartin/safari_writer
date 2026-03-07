"""Main Menu screen — the hub for all Safari Writer operations."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Static


MENU_ITEMS = [
    ("C", "reate File", "create"),
    ("E", "dit File", "edit"),
    ("T", "ry Demo Mode", "demo"),
    ("V", "erify Spelling", "verify"),
    ("P", "rint File", "print"),
    ("G", "lobal Format", "global_format"),
    ("M", "ail Merge", "mail_merge"),
    ("1", " Index Current Folder", "index1"),
    ("2", " Index External Drive", "index2"),
    ("O", "pen Safari DOS", "safari_dos"),
    ("L", "oad File", "load"),
    ("S", "ave File", "save"),
    ("D", "elete File", "delete"),
    ("F", "older (New)", "new_folder"),
    ("X", " Style Switcher", "style_switcher"),
]

MENU_CSS = """
MainMenuScreen {
    align: center middle;
    background: $background;
}

#menu-container {
    width: 42;
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

.menu-item {
    height: 1;
    color: $foreground;
}

.menu-key {
    color: $accent;
    text-style: bold underline;
}

#status-bar {
    dock: bottom;
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
        Binding("d", "menu_action('delete')", "Delete File", show=False),
        Binding("f", "menu_action('new_folder')", "New Folder", show=False),
        Binding("x", "menu_action('style_switcher')", "Style Switcher", show=False),
    ]

    def compose(self) -> ComposeResult:
        from textual.containers import Container

        with Container(id="menu-container"):
            yield Static("*** SAFARI WRITER ***", id="title")
            for key, label, _ in MENU_ITEMS:
                yield MenuItem(key, label)

        yield Static(self._status_text(), id="status-bar")

    def _status_text(self) -> str:
        state = self.app.state  # type: ignore[attr-defined]
        return f" Bytes Free: {state.bytes_free:,}"

    def on_mount(self) -> None:
        self.query_one("#status-bar", Static).update(self._status_text())

    def set_message(self, msg: str) -> None:
        if self.is_mounted:
            self.query_one("#status-bar", Static).update(f" {msg}")

    def action_menu_action(self, action: str) -> None:
        self.app.handle_menu_action(action)  # type: ignore[attr-defined]
