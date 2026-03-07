"""Textual screens for Safari DOS."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import ModalScreen, Screen
from textual.widgets import Static

from safari_dos.services import (
    DirectoryEntry,
    GarbageEntry,
    copy_paths,
    create_folder,
    discover_locations,
    duplicate_path,
    format_timestamp,
    get_entry_info,
    list_favorites,
    list_directory,
    list_garbage,
    list_recent_documents,
    list_recent_locations,
    move_paths,
    move_to_garbage,
    record_recent_document,
    record_recent_location,
    rename_path,
    restore_from_garbage,
    set_protected,
    toggle_favorite,
)
from safari_dos.state import SafariDosState

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
    """Lightweight menu item matching Safari Writer's shared menu style."""

    def __init__(self, key: str, label: str) -> None:
        super().__init__(f"[bold underline]{key}[/]{label}", classes="menu-item")


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
        Binding("h", "menu_action('help')", "Help", show=False),
        Binding("y", "menu_action('style_switcher')", "Style Switcher", show=False),
        Binding("q,escape", "menu_action('quit')", "Quit", show=False),
    ]

    def __init__(self, state: SafariDosState) -> None:
        super().__init__()
        self._state = state

    def compose(self) -> ComposeResult:
        with Container(id="dos-menu-container"):
            yield Static("*** SAFARI DOS ***", id="dos-menu-title")
            for key, label, _ in self.MENU_ITEMS:
                yield MenuItem(key, label)
        yield Static(f" Ready | Current Location: {self._state.current_path}", id="dos-status-bar")

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
        Binding("backspace", "parent", "Up Folder", show=False),
        Binding("space", "toggle_select", "Select", show=False),
        Binding("a", "select_all", "All", show=False),
        Binding(".", "toggle_hidden", "Hidden", show=False),
        Binding("/", "filter", "Filter", show=False),
        Binding("s", "sort", "Sort", show=False),
        Binding("f", "favorites", "Favorites", show=False),
        Binding("c", "copy", "Copy", show=False),
        Binding("m", "move", "Move", show=False),
        Binding("r", "rename", "Rename", show=False),
        Binding("u", "duplicate", "Duplicate", show=False),
        Binding("n", "new_folder", "New Folder", show=False),
        Binding("x", "garbage", "Garbage", show=False),
        Binding("i", "info", "Info", show=False),
        Binding("p", "toggle_protected", "Protect", show=False),
        Binding("tab", "choose_current_directory", "Choose Here", show=False),
        Binding("d", "devices", "Devices", show=False),
        Binding("g", "garbage_list", "Garbage List", show=False),
        Binding("h", "home", "Home", show=False),
        Binding("escape", "back_to_menu", "Menu", show=False),
    ]

    def __init__(self, state: SafariDosState, *, picker_mode: str | None = None) -> None:
        super().__init__()
        self._state = state
        self._picker_mode = picker_mode
        self._entries: list[DirectoryEntry] = []
        self._selected_index = 0
        self._message = "Ready"

    def compose(self) -> ComposeResult:
        with Container(id="dos-container"):
            with Container(id="dos-header"):
                yield Static("*** SAFARI DOS FILE LIST ***", id="dos-title")
                yield Static("", id="dos-path")
                yield Static("SEL NAME                         SIZE     TYPE   MODIFIED         F", id="dos-columns")
            yield Static("", id="dos-body")
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
            return "Enter=choose/open  Backspace=up  F=favorites  .=hidden  Esc=cancel"
        if self._picker_mode == "directory":
            return "Enter=open  Tab=choose folder  F=favorites  .=hidden  Esc=cancel"
        return "Enter=open  Space=select  C/M/R/U/N/X ops  F=favorites  P=protect  /=filter  S=sort  .=hidden  Esc=menu"

    def set_message(self, message: str) -> None:
        self._message = message
        if self.is_mounted:
            self.query_one("#dos-status", Static).update(message)

    def refresh_listing(self) -> None:
        try:
            self._entries = list_directory(
                self._state.current_path,
                show_hidden=self._state.show_hidden,
                filter_text=self._state.filter_text,
                sort_field=self._state.sort_field,
                ascending=self._state.ascending,
            )
            self._selected_index = min(self._selected_index, max(len(self._entries) - 1, 0))
        except (FileNotFoundError, NotADirectoryError, OSError, ValueError) as exc:
            self.set_message(str(exc))
            self._entries = []
        self._refresh_view()

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
        self.set_message("Hidden items shown" if self._state.show_hidden else "Hidden items hidden")
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
        self.app.push_screen(InputScreen("New Folder Name"), callback=self._on_new_folder)

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

    def _on_copy_or_move(self, operation: str, sources: list[Path], value: str | None) -> None:
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
            callback=lambda confirmed: self._perform_copy_or_move(operation, sources, destination, confirmed),
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

    def action_devices(self) -> None:
        self.app.push_screen(SafariDosDevicesScreen(self._state), callback=self._on_choose_device)

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
        self.app.push_screen(SafariDosGarbageScreen(), callback=self._on_restore_from_garbage)

    def _on_restore_from_garbage(self, restored: Path | None) -> None:
        if restored is None:
            self.set_message("Operation cancelled")
            return
        self.set_message(f"Restored: {restored.name}")
        self.refresh_listing()

    def action_back_to_menu(self) -> None:
        if self._picker_mode is not None:
            self.dismiss(None)
            return
        self.app.pop_screen()

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
        protected_now = all(path.exists() and next((entry.protected for entry in self._entries if entry.path == path), False) for path in sources)
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
                yield Static("TYPE     NAME                         PATH", id="dos-columns")
            yield Static("", id="dos-body")
            with Container(id="dos-footer"):
                yield Static("Ready", id="dos-status")
                yield Static("Enter=choose  T=toggle current folder  Esc=cancel", id="dos-help")

    def on_mount(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        favorites = self._state.favorites or list_favorites()
        recent_locations = self._state.recent_locations or list_recent_locations()
        recent_documents = self._state.recent_documents or list_recent_documents()
        entries: list[tuple[str, Path]] = []
        entries.extend(("FAVORITE", path) for path in favorites)
        entries.extend(("RECENT", path) for path in recent_locations if path not in favorites)
        entries.extend(("DOC", path) for path in recent_documents)
        self._entries = entries
        self._selected = min(self._selected, max(len(self._entries) - 1, 0))
        lines: list[str] = []
        for index, (kind, path) in enumerate(self._entries):
            line = f"{kind:<8} {path.name[:28]:<28} {str(path)[:40]}"
            if index == self._selected:
                line = f"[reverse]{line}[/reverse]"
            lines.append(line)
        self.query_one("#dos-body", Static).update("\n".join(lines) if lines else "<empty>")

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
    """Browse and restore garbage-managed items."""

    CSS = DOS_CSS

    def __init__(self) -> None:
        super().__init__()
        self._entries: list[GarbageEntry] = []
        self._selected = 0
        self._message = "Ready"

    def compose(self) -> ComposeResult:
        with Container(id="dos-container"):
            with Container(id="dos-header"):
                yield Static("*** GARBAGE ***", id="dos-title")
                yield Static("Restore discarded items", id="dos-path")
                yield Static("NAME                         DELETED            ORIGINAL", id="dos-columns")
            yield Static("", id="dos-body")
            with Container(id="dos-footer"):
                yield Static("", id="dos-status")
                yield Static("Enter=restore  A=alternate restore  Esc=cancel", id="dos-help")

    def on_mount(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        self._entries = list_garbage()
        lines: list[str] = []
        for index, entry in enumerate(self._entries):
            line = (
                f"{entry.name[:28]:<28} {format_timestamp(entry.deleted_at):<17} "
                f"{str(entry.original_path)[:30]}"
            )
            if index == self._selected:
                line = f"[reverse]{line}[/reverse]"
            lines.append(line)
        self.query_one("#dos-body", Static).update("\n".join(lines) if lines else "<empty>")
        self.query_one("#dos-status", Static).update(self._message)

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.dismiss(None)
        elif event.key == "up" and self._selected > 0:
            self._selected -= 1
            self._refresh()
        elif event.key == "down" and self._selected < len(self._entries) - 1:
            self._selected += 1
            self._refresh()
        elif event.key == "enter":
            self._restore_selected(None)
        elif event.key == "a" and self._entries:
            entry = self._entries[self._selected]
            self.app.push_screen(
                InputScreen("Restore To", str(entry.original_path)),
                callback=lambda value: self._restore_selected(value),
            )
        event.stop()

    def _restore_selected(self, destination: str | None) -> None:
        if not self._entries:
            self.dismiss(None)
            return
        entry = self._entries[self._selected]
        try:
            restored = restore_from_garbage(
                entry.item_id,
                Path(destination) if destination else None,
            )
        except (FileExistsError, FileNotFoundError, OSError, ValueError) as exc:
            self._message = str(exc)
            self._refresh()
            return
        self.dismiss(restored)


class SafariDosHelpScreen(Screen):
    """Compact help for Safari DOS."""

    CSS = DOS_CSS

    def compose(self) -> ComposeResult:
        body = "\n".join(
            [
                "Select Function",
                "",
                "File List:",
                "  Enter open folder/file",
                "  Space mark items",
                "  C copy  M move  R rename  U duplicate",
                "  N new folder  X send to Garbage",
                "  F favorites/recent  P protect toggle",
                "  / filter  S sort  . hidden toggle",
                "",
                "Garbage restores items without permanent delete.",
                "Safari DOS stays foreground-only; no background daemon.",
                "",
                "Esc returns to menu.",
            ]
        )
        with Container(id="dos-container"):
            with Container(id="dos-header"):
                yield Static("*** SAFARI DOS HELP ***", id="dos-title")
                yield Static("Operational help", id="dos-path")
                yield Static("", id="dos-columns")
            yield Static(body, id="dos-body")
            with Container(id="dos-footer"):
                yield Static("Ready", id="dos-status")
                yield Static("Esc=back", id="dos-help")

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.app.pop_screen()
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
