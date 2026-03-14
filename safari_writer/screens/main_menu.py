"""Main Menu screen — the hub for all Safari Writer operations."""

from datetime import datetime

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import Static

from safari_writer.path_utils import leaf_name
import safari_writer.locale_info as _locale_info


def _(s: str) -> str:
    return _locale_info.get_translation().gettext(s)


def _menu_label_suffix(key: str, text: str) -> str:
    """Return the display label content after the hotkey character."""
    if text and text[0].upper() == key.upper() and key.isalpha():
        return text[1:]
    return " " + text


def _menu_items(definitions: list[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
    """Return exported menu items using the legacy label-suffix format."""
    return [
        (key, _menu_label_suffix(key, text), action)
        for key, text, action in definitions
    ]


# Column 1: Words
_COL1_DEFS = [
    ("C", "Create File", "create"),
    ("E", "Edit File", "edit"),
    ("V", "Verify Spelling", "verify"),
    ("P", "Print File", "print"),
    ("G", "Global Format", "global_format"),
    ("M", "Mail Merge", "mail_merge"),
    ("I", "lIbrary Reader", "safari_reader"),
    ("?", "Doctor (diagnostics)", "doctor"),
]

# Column 2: DOS
_COL2_DEFS = [
    ("1", "Index Current Folder", "index1"),
    ("2", "Index External Drive", "index2"),
    ("K", "Backup & Restore", "backup_restore"),
    ("L", "Load File", "load"),
    ("S", "Save File", "save"),
    ("A", "Save As...", "save_as"),
    ("D", "Delete File", "delete"),
    ("F", "Folder (New)", "new_folder"),
    ("Q", "Quit", "quit"),
]

# Column 3: Tools
_COL3_DEFS = [
    ("O", "Open Safari DOS", "safari_dos"),
    ("B", "Base (Address Book)", "safari_base"),
    ("H", "Help Chat", "safari_chat"),
    ("N", "Net Safari Fed", "safari_fed"),
    ("J", "Slide Projector", "safari_slides"),
    ("R", "Run Safari REPL", "safari_repl"),
    ("W", "atari VieWer", "safari_view"),
    ("X", "Style Switcher", "style_switcher"),
    ("T", "Try Demo Mode", "demo"),
]

COL1_ITEMS = _menu_items(_COL1_DEFS)
COL2_ITEMS = _menu_items(_COL2_DEFS)
COL3_ITEMS = _menu_items(_COL3_DEFS)
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

.menu-header {
    height: 1;
    text-align: center;
    text-style: bold;
    background: $accent;
    color: $surface;
    margin-bottom: 1;
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
    def __init__(self, key: str, label: str, action: str = "") -> None:
        self.key_char = key
        self.label_text = label
        self.action_name = action
        super().__init__("", classes="menu-item")
        self._is_selected = False
        self._update_markup()

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
        Binding("k", "menu_action('backup_restore')", "Backup & Restore", show=False),
        Binding("l", "menu_action('load')", "Load File", show=False),
        Binding("s", "menu_action('save')", "Save File", show=False),
        Binding("a", "menu_action('save_as')", "Save As", show=False),
        Binding("d", "menu_action('delete')", "Delete File", show=False),
        Binding("f", "menu_action('new_folder')", "New Folder", show=False),
        Binding("q", "menu_action('quit')", "Quit", show=False),
        Binding("o", "menu_action('safari_dos')", "Open Safari DOS", show=False),
        Binding("b", "menu_action('safari_base')", "Base (Address Book)", show=False),
        Binding("h", "menu_action('safari_chat')", "Help Chat", show=False),
        Binding("n", "menu_action('safari_fed')", "Open Safari Fed", show=False),
        Binding("j", "menu_action('safari_slides')", "Slide Projector", show=False),
        Binding("r", "menu_action('safari_repl')", "Run Safari REPL", show=False),
        Binding("i", "menu_action('safari_reader')", "Library Reader", show=False),
        Binding("w", "menu_action('safari_view')", "Image Viewer", show=False),
        Binding("x", "menu_action('style_switcher')", "Style Switcher", show=False),
        Binding("t", "menu_action('demo')", "Try Demo Mode", show=False),
        Binding("question_mark", "menu_action('doctor')", "Doctor", show=False),
        # Arrow navigation
        Binding("up", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("left", "cursor_left", "Left", show=False),
        Binding("right", "cursor_right", "Right", show=False),
        Binding("enter", "activate", "Activate", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._message = ""
        self._clock_timer: Timer | None = None
        self._selected_index = 0
        self._menu_widgets: list[MenuItem] = []

    def compose(self) -> ComposeResult:
        from textual.containers import Container, Horizontal

        def _label(key: str, msgid: str) -> str:
            """Translate msgid and derive the label portion (after the hotkey)."""
            return _menu_label_suffix(key, _(msgid))

        with Container(id="menu-body"):
            with Container(id="menu-container"):
                yield Static(_("*** SAFARI WRITER ***"), id="title")
                with Horizontal(id="menu-columns"):
                    with Container(id="menu-col-1"):
                        yield Static(_("*** Words ***"), classes="menu-header")
                        for key, msgid, action in _COL1_DEFS:
                            yield MenuItem(key, _label(key, msgid), action)
                    with Container(id="menu-col-2"):
                        yield Static(_("*** DOS ***"), classes="menu-header")
                        for key, msgid, action in _COL2_DEFS:
                            yield MenuItem(key, _label(key, msgid), action)
                    with Container(id="menu-col-3"):
                        yield Static(_("*** Tools ***"), classes="menu-header")
                        for key, msgid, action in _COL3_DEFS:
                            yield MenuItem(key, _label(key, msgid), action)

        with Container(id="menu-footer"):
            yield Static(self._context_text(), id="context-bar")
            with Horizontal(id="status-bar"):
                yield Static(self._status_line(), id="status-text")
                yield Static(self._clock_text(), id="status-clock")

    def on_mount(self) -> None:
        self._menu_widgets = list(self.query(MenuItem))
        self._refresh_menu()
        self._refresh_footer()
        self._clock_timer = self.set_interval(1, self._update_clock)

    def _refresh_menu(self) -> None:
        for i, widget in enumerate(self._menu_widgets):
            widget.set_selected(i == self._selected_index)

    def action_cursor_up(self) -> None:
        # If in first column, wrap or stop? Stop at top.
        col1_len = len(_COL1_DEFS)
        col2_len = len(_COL2_DEFS)
        # col3_len = len(_COL3_DEFS)

        if self._selected_index < col1_len:
            # Col 1
            if self._selected_index > 0:
                self._selected_index -= 1
        elif self._selected_index < col1_len + col2_len:
            # Col 2
            if self._selected_index > col1_len:
                self._selected_index -= 1
        else:
            # Col 3
            if self._selected_index > col1_len + col2_len:
                self._selected_index -= 1
        self._refresh_menu()

    def action_cursor_down(self) -> None:
        col1_len = len(_COL1_DEFS)
        col2_len = len(_COL2_DEFS)
        col3_len = len(_COL3_DEFS)

        if self._selected_index < col1_len:
            # Col 1
            if self._selected_index < col1_len - 1:
                self._selected_index += 1
        elif self._selected_index < col1_len + col2_len:
            # Col 2
            if self._selected_index < col1_len + col2_len - 1:
                self._selected_index += 1
        else:
            # Col 3
            if self._selected_index < col1_len + col2_len + col3_len - 1:
                self._selected_index += 1
        self._refresh_menu()

    def action_cursor_left(self) -> None:
        col1_len = len(_COL1_DEFS)
        col2_len = len(_COL2_DEFS)

        if self._selected_index < col1_len:
            # Already in Col 1
            pass
        elif self._selected_index < col1_len + col2_len:
            # In Col 2, go to Col 1
            row = self._selected_index - col1_len
            self._selected_index = min(row, col1_len - 1)
        else:
            # In Col 3, go to Col 2
            row = self._selected_index - (col1_len + col2_len)
            self._selected_index = col1_len + min(row, col2_len - 1)
        self._refresh_menu()

    def action_cursor_right(self) -> None:
        col1_len = len(_COL1_DEFS)
        col2_len = len(_COL2_DEFS)
        col3_len = len(_COL3_DEFS)

        if self._selected_index < col1_len:
            # In Col 1, go to Col 2
            row = self._selected_index
            self._selected_index = col1_len + min(row, col2_len - 1)
        elif self._selected_index < col1_len + col2_len:
            # In Col 2, go to Col 3
            row = self._selected_index - col1_len
            self._selected_index = col1_len + col2_len + min(row, col3_len - 1)
        else:
            # Already in Col 3
            pass
        self._refresh_menu()

    def action_activate(self) -> None:
        if 0 <= self._selected_index < len(self._menu_widgets):
            action = self._menu_widgets[self._selected_index].action_name
            self.action_menu_action(action)

    def _clock_text(self) -> str:
        from safari_writer.locale_info import format_datetime

        return format_datetime(datetime.now(), style="full")

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
        from safari_writer.locale_info import LANGUAGE
        from pathlib import Path

        state = self.app.state  # type: ignore[attr-defined]

        # Document name: title > filename leaf > "(new document)"
        if state.doc_title:
            edit_file = state.doc_title
        else:
            edit_file = self._display_name(state.filename, _("(new document)"))

        merge_filename = (
            state.mail_merge_db.filename if state.mail_merge_db is not None else ""
        )
        merge_file = self._display_name(merge_filename, _("(no merge data)"))
        lang = state.doc_language or LANGUAGE

        parts = [
            f"Edit: {edit_file}",
            f"Merge: {merge_file}",
            f"Lang: {lang}",
        ]

        # Mastodon account from Safari Fed state
        fed_state = getattr(self.app, "fed_state", None)
        if fed_state is not None:
            parts.append(f"Masto: {fed_state.account_label}")

        # Git folder indicator
        doc_path = state.filename
        if doc_path:
            folder = Path(doc_path).resolve().parent
        else:
            folder = Path.cwd()
        if (folder / ".git").exists() or any(
            (folder / (".git")).exists()
            for folder in [folder] + list(folder.parents)[:3]
        ):
            # Find the git root name
            git_root = folder
            for candidate in [folder] + list(folder.parents)[:4]:
                if (candidate / ".git").exists():
                    git_root = candidate
                    break
            parts.append(f"Git: {git_root.name}")

        return " " + "   ".join(parts)

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

    def on_show(self) -> None:
        self._refresh_footer()

    def on_screen_resume(self) -> None:
        self._refresh_footer()

    def set_message(self, msg: str) -> None:
        self._message = msg
        self._refresh_footer()

    def action_menu_action(self, action: str) -> None:
        self.app.handle_menu_action(action)  # type: ignore[attr-defined]
