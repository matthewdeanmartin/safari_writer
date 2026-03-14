"""Textual screens for Safari DOS."""

# -----------------------------------------------------------------------
# Textual reserved keys (do not rebind without care):
#   Ctrl+Q   quit (App default, priority)
#   Ctrl+C   copy text / help-quit (App + Screen default)
#   Ctrl+P   command palette (App.COMMAND_PALETTE_BINDING)
#   Tab      focus next widget (Screen default)
#   Shift+Tab focus previous widget (Screen default)
#   Ctrl+I   alias for Tab (terminal limitation)
#   Ctrl+J   alias for Enter (terminal limitation)
#   Ctrl+M   alias for Enter (terminal limitation)
# -----------------------------------------------------------------------

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import ModalScreen, Screen
from textual.widgets import Static

from safari_dos.services import (CODE_EXTENSIONS, DirectoryEntry, GarbageEntry,
                                 copy_paths, create_folder, discover_locations,
                                 duplicate_path, format_timestamp,
                                 get_entry_info, get_preview_syntax,
                                 list_directory, list_favorites, list_garbage,
                                 list_recent_documents, list_recent_locations,
                                 move_paths, move_to_garbage,
                                 record_recent_document,
                                 record_recent_location, rename_path,
                                 set_protected, toggle_favorite, unzip_path,
                                 zip_paths)
from safari_dos.state import SafariDosState
from safari_writer.program_runner import (decode_stdin_text, is_runnable_path,
                                          path_may_need_stdin,
                                          run_program_file)
from safari_writer.screens.output_screen import OutputScreen

__all__ = [
    "ConfirmScreen",
    "InputScreen",
    "MessageScreen",
    "SafariDosBrowserScreen",
    "SafariDosDevicesScreen",
    "SafariDosFavoritesScreen",
    "SafariDosGarbageScreen",
    "SafariDosHelpScreen",
    "SafariDosMainMenuScreen",
]

DOS_CSS = """
Screen {
    background: $background;
    color: $foreground;
}

SafariDosMainMenuScreen {
    align: center middle;
    background: $background;
}

#dos-container {
    width: 100%;
    height: 100%;
}

#dos-menu-container {
    width: 42;
    height: auto;
    border: solid $accent;
    background: $surface;
    padding: 1 2;
}

#dos-menu-title {
    text-align: center;
    text-style: bold;
    margin-bottom: 1;
    color: $accent;
}

.menu-item {
    height: 1;
    color: $foreground;
}

#dos-status-bar {
    dock: bottom;
    height: 1;
    background: $primary;
    color: $foreground;
    padding: 0 1;
}

#dos-header {
    dock: top;
    height: 4;
    background: $primary;
    color: $foreground;
    padding: 0 1;
}

#dos-title {
    color: $accent;
    text-style: bold;
    text-align: center;
}

#dos-path {
    color: $foreground;
}

#dos-columns {
    color: $foreground;
    text-style: bold;
}

#dos-body {
    height: 1fr;
    padding: 0 1;
    color: $foreground;
}

#dos-browser-main {
    height: 1fr;
    layout: horizontal;
    padding: 0 1;
}

#dos-browser-menu {
    width: 26;
    min-width: 26;
    height: 100%;
    border: solid $accent;
    background: $surface;
    padding: 1;
    margin-right: 1;
}

#dos-browser-menu-title {
    color: $accent;
    text-style: bold;
    margin-bottom: 1;
}

#dos-browser-menu-items {
    color: $foreground;
    text-style: bold;
}

#dos-browser-content {
    width: 1fr;
    height: 100%;
    layout: horizontal;
}

#dos-browser-list {
    width: 1fr;
    height: 100%;
}

#dos-browser-list.hidden {
    display: none;
}

#dos-preview-pane {
    width: 40%;
    height: 100%;
    border-left: solid $accent;
    background: $surface;
    padding: 1;
}

#dos-preview-pane.hidden {
    display: none;
}

#dos-preview-pane.fullscreen {
    width: 100%;
    border-left: none;
}

#dos-preview-title {
    color: $accent;
    text-style: bold;
    margin-bottom: 1;
    text-align: center;
}

#dos-preview-body {
    color: $foreground;
    height: 1fr;
}

#dos-footer {
    dock: bottom;
    height: 2;
    background: $primary;
    color: $foreground;
    padding: 0 1;
}

#dos-status {
    color: $success;
}

#dos-help {
    color: $foreground;
}

InputScreen, ConfirmScreen, MessageScreen {
    align: center middle;
    background: $background 60%;
}

#dos-dialog {
    width: 72;
    height: auto;
    border: solid $accent;
    background: $surface;
    padding: 1 2;
}

#dos-dialog-title {
    color: $accent;
    text-style: bold;
    text-align: center;
}

#dos-dialog-body {
    margin-top: 1;
    color: $foreground;
}

#dos-dialog-hint {
    color: $foreground;
    margin-top: 1;
}

SafariDosHelpScreen {
    align: center middle;
}

#dos-help-dialog {
    width: 80;
    height: auto;
    max-height: 90%;
    border: solid $primary;
    background: $surface;
    padding: 1 2;
}

#dos-help-title {
    text-align: center;
    text-style: bold;
    color: $accent;
    margin-bottom: 1;
}

#dos-help-content {
    height: 1fr;
    color: $foreground;
}

#dos-help-footer {
    text-align: center;
    color: $text-muted;
    margin-top: 1;
}
"""


class InputScreen(ModalScreen[str | None]):
    """Prompt the user for a text value."""

    CSS = DOS_CSS

    def __init__(self, title: str, default: str = "") -> None:
        super().__init__()
        self._title = title
        self._buffer = default

    def compose(self) -> ComposeResult:
        with Container(id="dos-dialog"):
            yield Static(self._title, id="dos-dialog-title")
            yield Static(self._render_input(), id="dos-dialog-body")
            yield Static("Enter accept  Esc cancel", id="dos-dialog-hint")

    def _render_input(self) -> str:
        return f"> {self._buffer}[reverse] [/reverse]"

    def _refresh(self) -> None:
        self.query_one("#dos-dialog-body", Static).update(self._render_input())

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.dismiss(None)
        elif event.key == "enter":
            value = self._buffer.strip()
            self.dismiss(value if value else None)
        elif event.key == "backspace":
            self._buffer = self._buffer[:-1]
            self._refresh()
        elif event.character and event.character.isprintable():
            self._buffer += event.character
            self._refresh()
        event.stop()


class ConfirmScreen(ModalScreen[bool | None]):
    """Yes/no confirmation dialog."""

    CSS = DOS_CSS

    def __init__(self, prompt: str) -> None:
        super().__init__()
        self._prompt = prompt

    def compose(self) -> ComposeResult:
        with Container(id="dos-dialog"):
            yield Static(self._prompt, id="dos-dialog-title")
            yield Static("Proceed (Y/N)?", id="dos-dialog-hint")

    def on_key(self, event: events.Key) -> None:
        if event.key == "y":
            self.dismiss(True)
        elif event.key in {"n", "escape"}:
            self.dismiss(False)
        event.stop()


class MessageScreen(ModalScreen[None]):
    """Display informational text until dismissed."""

    CSS = DOS_CSS

    def __init__(self, title: str, body: str) -> None:
        super().__init__()
        self._title = title
        self._body = body

    def compose(self) -> ComposeResult:
        with Container(id="dos-dialog"):
            yield Static(self._title, id="dos-dialog-title")
            yield Static(self._body, id="dos-dialog-body")
            yield Static("Enter or Esc close", id="dos-dialog-hint")

    def on_key(self, event: events.Key) -> None:
        if event.key in {"enter", "escape"}:
            self.dismiss(None)
        event.stop()


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


class SafariDosMainMenuScreen(Screen):
    """Atari DOS-style main menu for Safari DOS."""

    CSS = DOS_CSS

    MENU_ITEMS = [
        ("F", "ile List", "browse"),
        ("D", "evices", "devices"),
        ("G", "arbage", "garbage"),
        ("H", "elp", "help"),
        ("Y", " Style Switcher", "style_switcher"),
        ("Q", "uit", "quit"),
    ]

    BINDINGS = [
        Binding("f", "menu_action('browse')", "File List", show=False),
        Binding("d", "menu_action('devices')", "Devices", show=False),
        Binding("g", "menu_action('garbage')", "Garbage", show=False),
        Binding("h,f1", "menu_action('help')", "Help", show=False),
        Binding("y", "menu_action('style_switcher')", "Style Switcher", show=False),
        Binding("q,escape", "menu_action('quit')", "Quit", show=False),
        # Arrow navigation
        Binding("up", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("enter", "activate", "Activate", show=False),
    ]

    def __init__(self, state: SafariDosState) -> None:
        super().__init__()
        self._state = state
        self._selected_index = 0
        self._menu_widgets: list[MenuItem] = []

    def compose(self) -> ComposeResult:
        with Container(id="dos-menu-container"):
            yield Static("*** SAFARI DOS ***", id="dos-menu-title")
            for key, label, action in self.MENU_ITEMS:
                yield MenuItem(key, label, action)
        yield Static(
            f" Ready | Current Location: {self._state.current_path}",
            id="dos-status-bar",
        )

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
        app = cast("SafariDosAppProtocol", self.app)
        if action == "browse":
            app.open_browser()
        elif action == "devices":
            app.open_devices()
        elif action == "garbage":
            app.open_garbage()
        elif action == "help":
            self.app.push_screen(SafariDosHelpScreen())
        elif action == "style_switcher":
            app.open_style_switcher()
        elif action == "quit":
            app.quit_dos()


class SafariDosBrowserScreen(Screen):
    """Primary directory listing and operation screen."""

    CSS = DOS_CSS

    BINDINGS = [
        Binding("up", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("home", "cursor_home", "Home", show=False),
        Binding("end", "cursor_end", "End", show=False),
        Binding("enter", "activate", "Open", show=False),
        Binding("e", "run_selected", "Run", show=False),
        Binding("backspace", "parent", "Up Folder", show=False),
        Binding("t", "toggle_select", "Select", show=False),
        Binding("a", "select_all", "All", show=False),
        Binding(".", "toggle_hidden", "Hidden", show=False),
        Binding("/", "filter", "Filter", show=False),
        Binding("s", "sort", "Sort", show=False),
        Binding("f", "favorites", "Favorites", show=False),
        Binding("c", "copy", "Copy", show=False),
        Binding("m", "move", "Move", show=False),
        Binding("r", "rename", "Rename", show=False),
        Binding("w", "duplicate", "Duplicate", show=False),
        Binding("n", "new_folder", "New Folder", show=False),
        Binding("x", "garbage", "Garbage", show=False),
        Binding("i", "info", "Info", show=False),
        Binding("p", "toggle_protected", "Protect", show=False),
        Binding("v", "toggle_preview", "View Toggle", show=False),
        Binding("space", "fullscreen_preview", "Fullscreen Preview", show=False),
        Binding("z", "zip_archive", "Zip", show=False),
        Binding("u", "unzip_archive", "Unzip", show=False),
        Binding("tab", "choose_current_directory", "Choose Here", show=False),
        Binding("d", "devices", "Devices", show=False),
        Binding("g", "garbage_list", "Garbage List", show=False),
        Binding("h", "home", "Home", show=False),
        Binding("pageup", "page_up", "Page Up", show=False),
        Binding("pagedown", "page_down", "Page Down", show=False),
        Binding("f1", "show_help", "Help", show=False),
        Binding("escape", "back_to_menu", "Menu", show=False),
    ]

    def __init__(
        self,
        state: SafariDosState,
        *,
        picker_mode: str | None = None,
        initial_selection_path: Path | None = None,
    ) -> None:
        super().__init__()
        self._state = state
        self._picker_mode = picker_mode
        self._initial_selection_path = (
            initial_selection_path.resolve()
            if initial_selection_path is not None
            else None
        )
        self._entries: list[DirectoryEntry] = []
        self._selected_index = 0
        self._message = "Ready"

    def compose(self) -> ComposeResult:
        with Container(id="dos-container"):
            with Container(id="dos-browser-main"):
                with Container(id="dos-browser-menu"):
                    yield Static(self._menu_title(), id="dos-browser-menu-title")
                    yield Static(self._render_side_menu(), id="dos-browser-menu-items")
                with Container(id="dos-browser-content"):
                    with Container(id="dos-browser-list"):
                        with Container(id="dos-header"):
                            yield Static("*** SAFARI DOS FILE LIST ***", id="dos-title")
                            yield Static("", id="dos-path")
                            yield Static(
                                "SEL NAME                         SIZE     TYPE   MODIFIED         F",
                                id="dos-columns",
                            )
                        yield Static("", id="dos-body")
                    with Container(id="dos-preview-pane"):
                        yield Static("*** PREVIEW ***", id="dos-preview-title")
                        yield Static("", id="dos-preview-body")
            with Container(id="dos-footer"):
                yield Static("", id="dos-status")
                yield Static(
                    self._help_text(),
                    id="dos-help",
                )

    def on_mount(self) -> None:
        self._sync_recent_locations()
        self.refresh_listing()

    def _help_text(self) -> str:
        if self._picker_mode == "file":
            return (
                "Enter=choose/open  Backspace=up  F=favorites  .=hidden  "
                "F1=help  Esc=cancel"
            )
        if self._picker_mode == "directory":
            return (
                "Enter=open  Tab=choose folder  F=favorites  .=hidden  "
                "F1=help  Esc=cancel"
            )
        return (
            "Enter=open  E=run  T=select  C/M/R/W/N/X ops  Z/U zip  "
            "V=view  F1=help  Esc=menu"
        )

    def _menu_title(self) -> str:
        if self._picker_mode == "file":
            return "SELECT FILE"
        if self._picker_mode == "directory":
            return "SELECT FOLDER"
        return "FILE COMMANDS"

    def _menu_entries(self) -> list[tuple[str, str]]:
        if self._picker_mode == "file":
            return [
                ("RET.", "OPEN / CHOOSE"),
                ("BS.", "PARENT FOLDER"),
                ("F.", "FAVORITES"),
                ("D.", "DEVICES"),
                ("H.", "HOME"),
                (".", "SHOW HIDDEN"),
                ("ESC.", "CANCEL"),
            ]
        if self._picker_mode == "directory":
            return [
                ("RET.", "OPEN FOLDER"),
                ("TAB.", "CHOOSE HERE"),
                ("BS.", "PARENT FOLDER"),
                ("F.", "FAVORITES"),
                ("D.", "DEVICES"),
                ("H.", "HOME"),
                (".", "SHOW HIDDEN"),
                ("ESC.", "CANCEL"),
            ]
        return [
            ("RET.", "OPEN ITEM"),
            ("E.", "EXECUTE PROGRAM"),
            ("T.", "SELECT ITEM"),
            ("C.", "COPY FILE(S)"),
            ("M.", "MOVE FILE(S)"),
            ("R.", "RENAME FILE"),
            ("W.", "DUPLICATE FILE"),
            ("N.", "NEW FOLDER"),
            ("X.", "DELETE FILE(S)"),
            ("P.", "LOCK / UNLOCK"),
            ("I.", "ITEM INFO"),
            ("Z.", "ZIP ARCHIVE"),
            ("U.", "UNZIP ARCHIVE"),
            ("V.", "VIEW TOGGLE"),
            ("SPC.", "FULL PREVIEW"),
            ("", ""),
            ("BS.", "PARENT FOLDER"),
            ("F.", "FAVORITES"),
            ("D.", "DEVICES"),
            ("G.", "GARBAGE"),
            ("H.", "HOME"),
            ("/.", "NAME FILTER"),
            ("S.", "SORT FILES"),
            (".", "SHOW HIDDEN"),
            ("ESC.", "RETURN MENU"),
        ]

    def _render_side_menu(self) -> str:
        return "\n".join(
            f"{key:<5}{label}" if key else "" for key, label in self._menu_entries()
        )

    def set_message(self, message: str) -> None:
        self._message = message
        if self.is_mounted:
            self.query_one("#dos-status", Static).update(message)

    def refresh_listing(self) -> None:
        try:
            entries = list_directory(
                self._state.current_path,
                show_hidden=self._state.show_hidden,
                filter_text=self._state.filter_text,
                sort_field=self._state.sort_field,
                ascending=self._state.ascending,
            )
        except (FileNotFoundError, NotADirectoryError, OSError, ValueError) as exc:
            self.set_message(str(exc))
            self._entries = []
            self._refresh_view()
            return
        parent = self._state.current_path.parent
        if parent != self._state.current_path:
            from datetime import datetime

            parent_entry = DirectoryEntry(
                path=parent,
                name="..",
                kind="<DIR>",
                size_bytes=None,
                modified_at=datetime.fromtimestamp(parent.stat().st_mtime),
                protected=False,
                hidden=False,
                is_dir=True,
                is_link=False,
            )
            self._entries = [parent_entry] + entries
        else:
            self._entries = entries
        self._selected_index = min(self._selected_index, max(len(self._entries) - 1, 0))
        self._apply_initial_selection()
        self._refresh_view()

    def _apply_initial_selection(self) -> None:
        if self._initial_selection_path is None:
            return
        target = self._initial_selection_path
        for index, entry in enumerate(self._entries):
            if entry.path.resolve() == target:
                self._selected_index = index
                self._initial_selection_path = None
                return
        self._initial_selection_path = None

    def _selected_entry(self) -> DirectoryEntry | None:
        if not self._entries:
            return None
        return self._entries[self._selected_index]

    def _selected_paths(self) -> list[Path]:
        names = self._state.selected_names
        if names:
            return [entry.path for entry in self._entries if entry.name in names]
        entry = self._selected_entry()
        return [entry.path] if entry is not None else []

    def _refresh_view(self) -> None:
        path_line = f"Location: {self._state.current_path}"
        if self._state.filter_text:
            path_line += f"  |  Filter: {self._state.filter_text}"
        self.query_one("#dos-path", Static).update(path_line)

        if not self._entries:
            body = "<empty>"
        else:
            lines: list[str] = []
            for index, entry in enumerate(self._entries):
                size = "---" if entry.size_bytes is None else f"{entry.size_bytes:>7}"
                selected = "*" if entry.name in self._state.selected_names else " "
                flags = [
                    "P" if entry.protected else "-",
                    "H" if entry.hidden else "-",
                    "L" if entry.is_link else "-",
                ]
                line = (
                    f" {selected}  {entry.name[:28]:<28} {size:>7}  {entry.kind:<6} "
                    f"{format_timestamp(entry.modified_at):<16} {''.join(flags)}"
                )
                if index == self._selected_index:
                    line = f"[reverse]{line}[/reverse]"
                lines.append(line)
            body = "\n".join(lines)
        self.query_one("#dos-body", Static).update(body)
        selected_count = len(self._state.selected_names)
        suffix = f" | {selected_count} selected" if selected_count else ""
        self.query_one("#dos-status", Static).update(f"{self._message}{suffix}")
        self._update_preview()

    def _update_preview(self) -> None:
        preview_pane = self.query_one("#dos-preview-pane")
        browser_list = self.query_one("#dos-browser-list")

        if self._state.fullscreen_preview:
            preview_pane.set_class(True, "fullscreen")
            preview_pane.set_class(False, "hidden")
            browser_list.set_class(True, "hidden")
        elif self._state.show_preview:
            preview_pane.set_class(False, "fullscreen")
            preview_pane.set_class(False, "hidden")
            browser_list.set_class(False, "hidden")
        else:
            preview_pane.set_class(False, "fullscreen")
            preview_pane.set_class(True, "hidden")
            browser_list.set_class(False, "hidden")

        if self._state.show_preview or self._state.fullscreen_preview:
            entry = self._selected_entry()
            if entry:
                if entry.is_dir:
                    title = f"FOLDER: {entry.name}"
                    content: Any = get_entry_info(entry.path)
                else:
                    title = f"FILE: {entry.name}"
                    ext = entry.path.suffix.lower()
                    if ext in {".png", ".jpg", ".jpeg", ".bmp", ".gif"}:
                        content = (
                            f"[Image File]\n\n{get_entry_info(entry.path)}"
                        )
                    elif ext in CODE_EXTENSIONS:
                        content = get_preview_syntax(entry.path)
                    else:
                        content = get_entry_info(entry.path)

                self.query_one("#dos-preview-title", Static).update(title)
                self.query_one("#dos-preview-body", Static).update(content)

    def action_cursor_up(self) -> None:
        if self._selected_index > 0:
            self._selected_index -= 1
            self._refresh_view()

    def action_cursor_down(self) -> None:
        if self._selected_index < len(self._entries) - 1:
            self._selected_index += 1
            self._refresh_view()

    def action_cursor_home(self) -> None:
        self._selected_index = 0
        self._refresh_view()

    def action_cursor_end(self) -> None:
        if self._entries:
            self._selected_index = len(self._entries) - 1
            self._refresh_view()

    def action_page_up(self) -> None:
        self._selected_index = max(0, self._selected_index - 5)
        self._refresh_view()

    def action_page_down(self) -> None:
        if self._entries:
            self._selected_index = min(len(self._entries) - 1, self._selected_index + 5)
            self._refresh_view()

    def action_parent(self) -> None:
        parent = self._state.current_path.parent
        if parent == self._state.current_path:
            self.set_message("Already at top level")
            return
        self._state.current_path = parent
        self._state.selected_names.clear()
        self._sync_recent_locations()
        self.set_message("Moved up")
        self.refresh_listing()

    def action_home(self) -> None:
        self._state.current_path = Path.home()
        self._state.selected_names.clear()
        self._sync_recent_locations()
        self.set_message("Home")
        self.refresh_listing()

    def action_toggle_select(self) -> None:
        if self._picker_mode is not None:
            return
        entry = self._selected_entry()
        if entry is None:
            return
        if entry.name in self._state.selected_names:
            self._state.selected_names.remove(entry.name)
        else:
            self._state.selected_names.add(entry.name)
        self._refresh_view()

    def action_select_all(self) -> None:
        if self._picker_mode is not None:
            return
        self._state.selected_names = {entry.name for entry in self._entries}
        self.set_message("All visible items selected")
        self._refresh_view()

    def action_toggle_hidden(self) -> None:
        self._state.show_hidden = not self._state.show_hidden
        self.set_message(
            "Hidden items shown" if self._state.show_hidden else "Hidden items hidden"
        )
        self.refresh_listing()

    def action_filter(self) -> None:
        if self._picker_mode is not None:
            return
        self.app.push_screen(
            InputScreen("Name Filter", self._state.filter_text),
            callback=self._on_filter,
        )

    def _on_filter(self, value: str | None) -> None:
        self._state.filter_text = value or ""
        self.set_message("Filter updated" if value else "Filter cleared")
        self.refresh_listing()

    def action_sort(self) -> None:
        if self._picker_mode is not None:
            return
        fields = ("name", "date", "size", "type")
        current_index = fields.index(self._state.sort_field)
        next_index = (current_index + 1) % len(fields)
        next_field = fields[next_index]
        if next_field == "name" and self._state.sort_field == "type":
            self._state.ascending = not self._state.ascending
        self._state.sort_field = next_field
        self.set_message(f"Sort: {self._state.sort_field}")
        self.refresh_listing()

    def action_activate(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            return
        if entry.is_dir:
            self._state.current_path = entry.path
            self._state.selected_names.clear()
            self._selected_index = 0
            self._sync_recent_locations()
            self.set_message(f"Entered {entry.name}")
            self.refresh_listing()
            return
        if self._picker_mode == "directory":
            self.set_message("Select a folder with Tab")
            return
        if self._picker_mode == "file":
            self._sync_recent_documents(entry.path)
            self.dismiss(entry.path)
            return
        self._request_open_in_writer(entry.path)

    def action_run_selected(self) -> None:
        if self._picker_mode is not None:
            return
        entry = self._selected_entry()
        if entry is None or entry.is_dir:
            self.set_message("Select a program file to run")
            return
        if not is_runnable_path(entry.path):
            self.set_message("Run supports .bas, .asm, .prg, and .py files")
            return
        if path_may_need_stdin(entry.path):
            self.app.push_screen(
                InputScreen("Program Input (use \\n for new lines)"),
                callback=lambda value: self._run_selected_program(entry.path, value),
            )
            return
        self._run_selected_program(entry.path, "")

    def _run_selected_program(self, path: Path, raw_stdin: str | None) -> None:
        if raw_stdin is None:
            self.set_message("Execution cancelled")
            return
        self._sync_recent_documents(path)
        result = run_program_file(
            path,
            stdin_text=decode_stdin_text(raw_stdin),
        )
        status = "Executed" if result.success else "Execution failed"
        self.set_message(f"{status}: {path.name}")
        self.app.push_screen(OutputScreen(result.output, title=result.title))

    def _request_open_in_writer(self, path: Path) -> None:
        self._sync_recent_locations()
        self._sync_recent_documents(path)
        app = self.app
        if hasattr(app, "handle_safari_dos_open"):
            getattr(app, "handle_safari_dos_open")(path)
            return
        if hasattr(app, "request_writer_launch"):
            getattr(app, "request_writer_launch")(path)
            return
        self.set_message("No writer integration available")

    def action_new_folder(self) -> None:
        if self._picker_mode is not None:
            return
        self.app.push_screen(
            InputScreen("New Folder Name"), callback=self._on_new_folder
        )

    def _on_new_folder(self, name: str | None) -> None:
        if not name:
            self.set_message("Operation cancelled")
            return
        try:
            folder = create_folder(self._state.current_path, name)
        except (FileExistsError, OSError, ValueError) as exc:
            self.set_message(str(exc))
            return
        self.set_message(f"Created folder: {folder.name}")
        self.refresh_listing()

    def action_rename(self) -> None:
        if self._picker_mode is not None:
            return
        entry = self._selected_entry()
        if entry is None:
            return
        self.app.push_screen(
            InputScreen("Rename To", entry.name),
            callback=lambda value: self._on_rename(entry.path, value),
        )

    def _on_rename(self, source: Path, name: str | None) -> None:
        if not name:
            self.set_message("Operation cancelled")
            return
        try:
            renamed = rename_path(source, name)
        except (FileExistsError, OSError, ValueError) as exc:
            self.set_message(str(exc))
            return
        self.set_message(f"Renamed: {renamed.name}")
        self.refresh_listing()

    def action_duplicate(self) -> None:
        if self._picker_mode is not None:
            return
        entry = self._selected_entry()
        if entry is None:
            return
        try:
            duplicated = duplicate_path(entry.path)
        except OSError as exc:
            self.set_message(str(exc))
            return
        self.set_message(f"Duplicated: {duplicated.name}")
        self.refresh_listing()

    def action_copy(self) -> None:
        if self._picker_mode is not None:
            return
        sources = self._selected_paths()
        if not sources:
            return
        default = str(self._state.current_path)
        self.app.push_screen(
            InputScreen("Copy To Folder", default),
            callback=lambda value: self._on_copy_or_move("copy", sources, value),
        )

    def action_move(self) -> None:
        if self._picker_mode is not None:
            return
        sources = self._selected_paths()
        if not sources:
            return
        default = str(self._state.current_path)
        self.app.push_screen(
            InputScreen("Move To Folder", default),
            callback=lambda value: self._on_copy_or_move("move", sources, value),
        )

    def _on_copy_or_move(
        self, operation: str, sources: list[Path], value: str | None
    ) -> None:
        if not value:
            self.set_message("Operation cancelled")
            return
        destination = Path(value)
        if not destination.exists() or not destination.is_dir():
            self.set_message(f"Destination unavailable: {destination}")
            return
        summary = f"{operation.title()} {len(sources)} item(s) to {destination}?"
        self.app.push_screen(
            ConfirmScreen(summary),
            callback=lambda confirmed: self._perform_copy_or_move(
                operation, sources, destination, confirmed
            ),
        )

    def _perform_copy_or_move(
        self,
        operation: str,
        sources: list[Path],
        destination: Path,
        confirmed: bool | None,
    ) -> None:
        if not confirmed:
            self.set_message("Operation cancelled")
            return
        try:
            if operation == "copy":
                copy_paths(sources, destination)
                self.set_message(f"{len(sources)} item(s) copied")
            else:
                move_paths(sources, destination)
                self._state.selected_names.clear()
                self.set_message(f"{len(sources)} item(s) moved")
        except (FileExistsError, NotADirectoryError, OSError) as exc:
            self.set_message(str(exc))
            return
        self.refresh_listing()

    def action_garbage(self) -> None:
        if self._picker_mode is not None:
            return
        sources = self._selected_paths()
        if not sources:
            return
        noun = "item" if len(sources) == 1 else "items"
        self.app.push_screen(
            ConfirmScreen(f"Move {len(sources)} {noun} to Garbage?"),
            callback=lambda confirmed: self._on_garbage(sources, confirmed),
        )

    def _on_garbage(self, sources: list[Path], confirmed: bool | None) -> None:
        if not confirmed:
            self.set_message("Operation cancelled")
            return
        moved = 0
        try:
            for path in sources:
                move_to_garbage(path)
                moved += 1
        except (FileNotFoundError, OSError, ValueError) as exc:
            self.set_message(str(exc))
            return
        self._state.selected_names.clear()
        self.set_message(f"{moved} item(s) moved to Garbage")
        self.refresh_listing()

    def action_info(self) -> None:
        if self._picker_mode is not None:
            return
        entry = self._selected_entry()
        if entry is None:
            return
        try:
            body = get_entry_info(entry.path)
        except (FileNotFoundError, OSError) as exc:
            self.set_message(str(exc))
            return
        self.app.push_screen(MessageScreen("Item Info", body))

    def action_toggle_preview(self) -> None:
        if self._picker_mode is not None:
            return
        self._state.show_preview = not self._state.show_preview
        if not self._state.show_preview:
            self._state.fullscreen_preview = False
        self._refresh_view()

    def action_fullscreen_preview(self) -> None:
        if self._picker_mode is not None:
            return
        self._state.fullscreen_preview = not self._state.fullscreen_preview
        if self._state.fullscreen_preview:
            self._state.show_preview = True
        self._refresh_view()

    def action_zip_archive(self) -> None:
        if self._picker_mode is not None:
            return
        sources = self._selected_paths()
        if not sources:
            return
        default = "archive.zip"
        if len(sources) == 1:
            default = f"{sources[0].stem}.zip"
        self.app.push_screen(
            InputScreen("Archive Name", default),
            callback=lambda value: self._on_zip(sources, value),
        )

    def _on_zip(self, sources: list[Path], name: str | None) -> None:
        if not name:
            self.set_message("Operation cancelled")
            return
        archive_path = self._state.current_path / name
        if archive_path.suffix.lower() != ".zip":
            archive_path = archive_path.with_suffix(".zip")

        if archive_path.exists():
            self.app.push_screen(
                ConfirmScreen(f"Overwrite existing {archive_path.name}?"),
                callback=lambda confirmed: self._perform_zip(
                    sources, archive_path, confirmed
                ),
            )
        else:
            self._perform_zip(sources, archive_path, True)

    def _perform_zip(
        self, sources: list[Path], archive_path: Path, confirmed: bool | None
    ) -> None:
        if not confirmed:
            self.set_message("Operation cancelled")
            return
        try:
            zip_paths(sources, archive_path)
            self.set_message(f"Created archive: {archive_path.name}")
        except Exception as exc:
            self.set_message(f"Zip error: {exc}")
        self.refresh_listing()

    def action_unzip_archive(self) -> None:
        if self._picker_mode is not None:
            return
        entry = self._selected_entry()
        if entry is None or entry.path.suffix.lower() != ".zip":
            self.set_message("Select a .zip file to unzip")
            return
        self.app.push_screen(
            ConfirmScreen(f"Unzip {entry.name} here?"),
            callback=lambda confirmed: self._perform_unzip(entry.path, confirmed),
        )

    def _perform_unzip(self, archive_path: Path, confirmed: bool | None) -> None:
        if not confirmed:
            self.set_message("Operation cancelled")
            return
        try:
            unzip_path(archive_path, self._state.current_path)
            self.set_message(f"Extracted archive: {archive_path.name}")
        except Exception as exc:
            self.set_message(f"Unzip error: {exc}")
        self.refresh_listing()

    def action_devices(self) -> None:
        self.app.push_screen(
            SafariDosDevicesScreen(self._state), callback=self._on_choose_device
        )

    def _on_choose_device(self, path: Path | None) -> None:
        if path is None:
            self.set_message("Operation cancelled")
            return
        self._state.current_path = path
        self._state.selected_names.clear()
        self._sync_recent_locations()
        self.set_message(f"Device: {path}")
        self.refresh_listing()

    def action_garbage_list(self) -> None:
        self.app.push_screen(
            SafariDosGarbageScreen(), callback=self._on_restore_from_garbage
        )

    def _on_restore_from_garbage(self, restored: Path | None) -> None:
        if restored is None:
            return
        self.set_message(f"Restored: {restored.name}")
        self.refresh_listing()

    def action_back_to_menu(self) -> None:
        if self._picker_mode is not None:
            self.dismiss(None)
            return
        self.app.pop_screen()

    def action_show_help(self) -> None:
        self.app.push_screen(SafariDosHelpScreen())

    def action_favorites(self) -> None:
        self.app.push_screen(
            SafariDosFavoritesScreen(self._state),
            callback=self._on_choose_favorite,
        )

    def _on_choose_favorite(self, path: Path | None) -> None:
        if path is None:
            self.set_message("Operation cancelled")
            return
        if path.is_dir():
            self._state.current_path = path.resolve()
            self._state.selected_names.clear()
            self._sync_recent_locations()
            self.set_message(f"Location: {path}")
            self.refresh_listing()
            return
        if not path.exists():
            self.set_message(f"Path not found: {path}")
            return
        self._sync_recent_documents(path)
        if self._picker_mode == "file":
            self.dismiss(path)
            return
        self._request_open_in_writer(path)

    def action_toggle_protected(self) -> None:
        if self._picker_mode is not None:
            return
        sources = self._selected_paths()
        if not sources:
            return
        protected_now = all(
            path.exists()
            and next(
                (entry.protected for entry in self._entries if entry.path == path),
                False,
            )
            for path in sources
        )
        changed = 0
        try:
            for path in sources:
                set_protected(path, not protected_now)
                changed += 1
        except (FileNotFoundError, OSError) as exc:
            self.set_message(str(exc))
            return
        action = "Unprotected" if protected_now else "Protected"
        noun = "item" if changed == 1 else "items"
        self.set_message(f"{action} {changed} {noun}")
        self.refresh_listing()

    def action_choose_current_directory(self) -> None:
        if self._picker_mode != "directory":
            return
        self._sync_recent_locations()
        self.dismiss(self._state.current_path)

    def _sync_recent_locations(self) -> None:
        self._state.recent_locations = record_recent_location(self._state.current_path)

    def _sync_recent_documents(self, path: Path) -> None:
        self._state.recent_documents = record_recent_document(path)


class SafariDosFavoritesScreen(ModalScreen[Path | None]):
    """Browse favorite and recent locations shared with Writer."""

    CSS = DOS_CSS

    def __init__(self, state: SafariDosState) -> None:
        super().__init__()
        self._state = state
        self._entries: list[tuple[str, Path]] = []
        self._selected = 0

    def compose(self) -> ComposeResult:
        with Container(id="dos-container"):
            with Container(id="dos-header"):
                yield Static("*** FAVORITES / RECENT ***", id="dos-title")
                yield Static("Shared locations and documents", id="dos-path")
                yield Static(
                    "TYPE     NAME                         PATH", id="dos-columns"
                )
            yield Static("", id="dos-body")
            with Container(id="dos-footer"):
                yield Static("Ready", id="dos-status")
                yield Static(
                    "Enter=choose  T=toggle current folder  Esc=cancel", id="dos-help"
                )

    def on_mount(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        favorites = self._state.favorites or list_favorites()
        recent_locations = self._state.recent_locations or list_recent_locations()
        recent_documents = self._state.recent_documents or list_recent_documents()
        entries: list[tuple[str, Path]] = []
        entries.extend(("FAVORITE", path) for path in favorites)
        entries.extend(
            ("RECENT", path) for path in recent_locations if path not in favorites
        )
        entries.extend(("DOC", path) for path in recent_documents)
        self._entries = entries
        self._selected = min(self._selected, max(len(self._entries) - 1, 0))
        lines: list[str] = []
        for index, (kind, path) in enumerate(self._entries):
            line = f"{kind:<8} {path.name[:28]:<28} {str(path)[:40]}"
            if index == self._selected:
                line = f"[reverse]{line}[/reverse]"
            lines.append(line)
        self.query_one("#dos-body", Static).update(
            "\n".join(lines) if lines else "<empty>"
        )

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.dismiss(None)
        elif event.key == "up" and self._selected > 0:
            self._selected -= 1
            self._refresh()
        elif event.key == "down" and self._selected < len(self._entries) - 1:
            self._selected += 1
            self._refresh()
        elif event.key == "enter" and self._entries:
            self.dismiss(self._entries[self._selected][1])
        elif event.key == "t":
            added = toggle_favorite(self._state.current_path)
            self._state.favorites = list_favorites()
            status = "Added favorite" if added else "Removed favorite"
            self.query_one("#dos-status", Static).update(status)
            self._refresh()
        event.stop()


class SafariDosDevicesScreen(ModalScreen[Path | None]):
    """Pick a device or important location."""

    CSS = DOS_CSS

    def __init__(self, state: SafariDosState) -> None:
        super().__init__()
        self._locations = discover_locations(state.current_path)
        self._selected = 0

    def compose(self) -> ComposeResult:
        with Container(id="dos-container"):
            with Container(id="dos-header"):
                yield Static("*** DEVICES ***", id="dos-title")
                yield Static("Select Device or Location", id="dos-path")
                yield Static("#   LABEL                 PATH", id="dos-columns")
            yield Static("", id="dos-body")
            with Container(id="dos-footer"):
                yield Static("Ready", id="dos-status")
                yield Static("Up/Down=select  Enter=accept  Esc=cancel", id="dos-help")

    def on_mount(self) -> None:
        self._refresh_view()

    def _refresh_view(self) -> None:
        lines: list[str] = []
        for index, location in enumerate(self._locations):
            line = f"{location.token:<3} {location.label[:20]:<20} {str(location.path)[:40]}"
            if index == self._selected:
                line = f"[reverse]{line}[/reverse]"
            lines.append(line)
        self.query_one("#dos-body", Static).update("\n".join(lines))

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.dismiss(None)
        elif event.key == "up" and self._selected > 0:
            self._selected -= 1
            self._refresh_view()
        elif event.key == "down" and self._selected < len(self._locations) - 1:
            self._selected += 1
            self._refresh_view()
        elif event.key == "enter":
            self.dismiss(self._locations[self._selected].path)
        event.stop()


class SafariDosGarbageScreen(ModalScreen[Path | None]):
    """Browse items currently visible in the OS trash / recycling bin."""

    CSS = DOS_CSS

    def __init__(self) -> None:
        super().__init__()
        self._entries: list[GarbageEntry] = []
        self._selected = 0
        self._status = "Loading recycle bin..."
        self._load_error: str | None = None

    def compose(self) -> ComposeResult:
        with Container(id="dos-container"):
            with Container(id="dos-header"):
                yield Static("*** GARBAGE ***", id="dos-title")
                yield Static("Recycle Bin contents", id="dos-path")
                yield Static(
                    "TYPE   NAME                     DELETED              ORIGINAL LOCATION",
                    id="dos-columns",
                )
            yield Static("", id="dos-body")
            with Container(id="dos-footer"):
                yield Static(self._status, id="dos-status")
                yield Static("Up/Down=select  Esc=close", id="dos-help")

    def on_mount(self) -> None:
        self._reload_entries()

    def _reload_entries(self) -> None:
        try:
            self._entries = list_garbage()
            self._load_error = None
            self._status = (
                f"Recycle Bin items: {len(self._entries)}"
                if self._entries
                else "Recycle Bin is empty"
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self._entries = []
            self._load_error = str(exc)
            self._status = "Recycle Bin unavailable"
        self._selected = min(self._selected, max(len(self._entries) - 1, 0))
        self._refresh_view()

    def _refresh_view(self) -> None:
        if self._load_error:
            body = self._load_error
            path_line = "Recycle Bin unavailable"
        elif not self._entries:
            body = "<empty>"
            path_line = "Recycle Bin contents"
        else:
            lines: list[str] = []
            for index, entry in enumerate(self._entries):
                kind = "<DIR>" if entry.is_dir else "FILE"
                deleted = format_timestamp(entry.deleted_at)
                location = str(entry.original_path)[:36]
                line = f"{kind:<6} {entry.name[:24]:<24} {deleted[:19]:<19} {location}"
                if index == self._selected:
                    line = f"[reverse]{line}[/reverse]"
                lines.append(line)
            selected = self._entries[self._selected]
            path_line = str(selected.original_path)
            body = "\n".join(lines)
        self.query_one("#dos-path", Static).update(path_line)
        self.query_one("#dos-body", Static).update(body)
        self.query_one("#dos-status", Static).update(self._status)

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.dismiss(None)
        elif event.key == "up" and self._selected > 0:
            self._selected -= 1
            self._refresh_view()
        elif event.key == "down" and self._selected < len(self._entries) - 1:
            self._selected += 1
            self._refresh_view()
        event.stop()


DOS_HELP_CONTENT = """\
MAIN MENU
  F                 File List (browser)
  D                 Devices
  G                 Garbage
  H                 Help (this screen)
  Y                 Style Switcher
  Q / Esc           Quit Safari DOS

FILE BROWSER — NAVIGATION
  Up / Down         Move cursor            Home / End        First / last
  PageUp / PageDown Scroll page            Enter             Open folder/file
  E                 Execute program        Backspace         Parent folder
  H                 Home folder
  .                 Toggle hidden files    /                 Filter by pattern
  S                 Cycle sort order       D                 Switch device

FILE BROWSER — SELECTION
  T                 Toggle select item     A                 Select all items
  Tab               Choose current folder (picker mode)

FILE BROWSER — OPERATIONS
  C                 Copy selected          M                 Move selected
  R                 Rename item            W                 Duplicate item
  N                 New folder             X                 Send to Garbage
  P                 Toggle protected       I                 File info
  Z                 Create zip archive     U                 Unzip archive
  F                 Favorites / recent     G                 Garbage list
  V                 Toggle preview pane    Space             Fullscreen preview
  Run supports .bas, .asm, .prg, and .py files.

OTHER
  F1                This help screen       Esc               Back / Cancel

Garbage shows recycle-bin contents; restore items from your system file manager.
Safari DOS stays foreground-only; no background daemon.

TEXTUAL FRAMEWORK (reserved)
  Ctrl+Q            Quit application       Ctrl+C            Copy text
  Ctrl+P            Command palette        Tab/Shift+Tab     Focus widgets\
"""


class SafariDosHelpScreen(ModalScreen):
    """Full key-command reference for Safari DOS."""

    CSS = DOS_CSS

    def compose(self) -> ComposeResult:
        with Container(id="dos-help-dialog"):
            yield Static("=== SAFARI DOS — KEY COMMANDS ===", id="dos-help-title")
            yield Static(DOS_HELP_CONTENT, id="dos-help-content")
            yield Static("Press any key to close", id="dos-help-footer")

    def on_key(self, event: events.Key) -> None:
        self.dismiss()
        event.stop()


class SafariDosAppProtocol:
    """Small protocol-like shape used by the main menu."""

    def open_browser(self) -> None:
        raise NotImplementedError

    def open_devices(self) -> None:
        raise NotImplementedError

    def open_garbage(self) -> None:
        raise NotImplementedError

    def open_style_switcher(self) -> None:
        raise NotImplementedError

    def quit_dos(self) -> None:
        raise NotImplementedError
