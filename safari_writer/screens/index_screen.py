"""Index screen — directory listing in AtariWriter 80 style."""

import platform
from pathlib import Path

from textual.app import ComposeResult
from textual.screen import Screen
from textual import events
from textual.widgets import Static
from textual.containers import Container


def _find_external_drives() -> list[Path]:
    """Detect removable/external drives (USB thumb drives, etc.)."""
    system = platform.system()
    drives: list[Path] = []

    if system == "Windows":
        # Check all drive letters for removable media
        import ctypes
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()  # type: ignore[attr-defined]
        DRIVE_REMOVABLE = 2
        DRIVE_FIXED = 3
        for i in range(26):
            if bitmask & (1 << i):
                letter = chr(65 + i)
                drive_path = f"{letter}:\\"
                drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive_path)  # type: ignore[attr-defined]
                # Include removable drives and non-C: fixed drives
                if drive_type == DRIVE_REMOVABLE:
                    drives.append(Path(drive_path))
                elif drive_type == DRIVE_FIXED and letter not in ("C",):
                    drives.append(Path(drive_path))
    elif system == "Darwin":
        volumes = Path("/Volumes")
        if volumes.exists():
            for v in sorted(volumes.iterdir()):
                if v.name != "Macintosh HD" and v.is_dir():
                    drives.append(v)
    else:
        # Linux: check /media and /mnt
        for base in (Path("/media"), Path("/mnt")):
            if base.exists():
                for d in sorted(base.iterdir()):
                    if d.is_dir():
                        drives.append(d)

    return drives


def _format_size(size: int) -> str:
    """Format file size in human-readable form."""
    if size < 1024:
        return f"{size:>6}"
    elif size < 1024 * 1024:
        return f"{size // 1024:>5}K"
    elif size < 1024 * 1024 * 1024:
        return f"{size // (1024 * 1024):>4}MB"
    else:
        return f"{size // (1024 * 1024 * 1024):>4}GB"


INDEX_CSS = """
IndexScreen {
    background: #000080;
}

#idx-container {
    width: 100%;
    height: 100%;
    padding: 0;
}

#idx-header {
    dock: top;
    height: 3;
    background: #000080;
    color: #ffffff;
    padding: 0 1;
}

#idx-title {
    text-align: center;
    text-style: bold;
    color: #ffff00;
}

#idx-path {
    color: #00ffff;
}

#idx-columns {
    color: #ffffff;
    text-style: bold;
}

#idx-listing {
    height: 1fr;
    background: #000080;
    color: #ffffff;
    overflow-y: auto;
    padding: 0 1;
}

#idx-footer {
    dock: bottom;
    height: 2;
    background: #000080;
    color: #00ffff;
    padding: 0 1;
}

#idx-status {
    color: #00ff00;
}

#idx-help {
    color: #808080;
}
"""


class IndexScreen(Screen):
    """Display directory contents in AtariWriter 80 style.

    AtariWriter showed: filename, size, type in a scrollable list.
    We replicate that with modern file info.
    """

    CSS = INDEX_CSS

    def __init__(self, directory: Path, label: str = "Current Folder") -> None:
        super().__init__()
        self._directory = directory
        self._label = label
        self._entries: list[tuple[str, str, str]] = []  # (name, size, type)
        self._selected = 0
        self._page_offset = 0

    def compose(self) -> ComposeResult:
        with Container(id="idx-container"):
            with Container(id="idx-header"):
                yield Static(f"*** INDEX: {self._label} ***", id="idx-title")
                yield Static(f"Path: {self._directory}", id="idx-path")
                yield Static(
                    f"{'NAME':<30} {'SIZE':>7}  {'TYPE':<10}",
                    id="idx-columns",
                )
            yield Static("", id="idx-listing")
            with Container(id="idx-footer"):
                yield Static("", id="idx-status")
                yield Static(
                    "Up/Down=scroll  Enter=load  Esc=back  D=delete  F=new folder",
                    id="idx-help",
                )

    def on_mount(self) -> None:
        self._scan_directory()
        self._render_listing()

    def _scan_directory(self) -> None:
        """Read directory contents into _entries list."""
        self._entries = []
        try:
            items = sorted(self._directory.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except OSError:
            self._entries = [("<error reading directory>", "", "")]
            return

        for item in items:
            try:
                name = item.name
                if item.is_dir():
                    entry_type = "<DIR>"
                    size_str = "---"
                else:
                    stat = item.stat()
                    size_str = _format_size(stat.st_size)
                    suffix = item.suffix.upper()
                    entry_type = suffix if suffix else "FILE"
                self._entries.append((name, size_str, entry_type))
            except OSError:
                self._entries.append((item.name, "???", "???"))

        if not self._entries:
            self._entries = [("<empty directory>", "", "")]

    def _render_listing(self) -> None:
        """Render the file listing with the selected item highlighted."""
        lines: list[str] = []
        for i, (name, size, ftype) in enumerate(self._entries):
            # Truncate long names
            display_name = name[:28] if len(name) > 28 else name
            line = f"  {display_name:<30} {size:>7}  {ftype:<10}"
            if i == self._selected:
                line = f"[reverse]{line}[/reverse]"
            lines.append(line)

        self.query_one("#idx-listing", Static).update("\n".join(lines))

        # Update status
        total = len(self._entries)
        free = self._get_free_space()
        status = f" {total} items  |  {free} free  |  [{self._selected + 1}/{total}]"
        self.query_one("#idx-status", Static).update(status)

    def _get_free_space(self) -> str:
        """Get free space on the directory's volume."""
        try:
            import shutil
            usage = shutil.disk_usage(self._directory)
            return _format_size(usage.free)
        except OSError:
            return "???"

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.app.pop_screen()
            event.stop()
            return

        if event.key == "up":
            if self._selected > 0:
                self._selected -= 1
                self._render_listing()
        elif event.key == "down":
            if self._selected < len(self._entries) - 1:
                self._selected += 1
                self._render_listing()
        elif event.key == "pageup":
            self._selected = max(0, self._selected - 20)
            self._render_listing()
        elif event.key == "pagedown":
            self._selected = min(len(self._entries) - 1, self._selected + 20)
            self._render_listing()
        elif event.key == "home":
            self._selected = 0
            self._render_listing()
        elif event.key == "end":
            self._selected = len(self._entries) - 1
            self._render_listing()
        elif event.key == "enter":
            self._action_select()
        elif event.key == "d":
            self._action_delete()
        elif event.key == "f":
            self._action_new_folder()

        event.stop()

    def _action_select(self) -> None:
        """Select the current item — open dir or load file."""
        if not self._entries or self._entries[0][0].startswith("<"):
            return

        name = self._entries[self._selected][0]
        full_path = self._directory / name

        if full_path.is_dir():
            # Navigate into subdirectory
            self._directory = full_path
            self._selected = 0
            self.query_one("#idx-path", Static).update(f"Path: {self._directory}")
            self._scan_directory()
            self._render_listing()
        else:
            # Load this file into editor
            self.app.pop_screen()
            self.app._on_load_file(str(full_path))  # type: ignore[attr-defined]

    def _action_delete(self) -> None:
        """Delete the selected file after confirmation."""
        if not self._entries or self._entries[0][0].startswith("<"):
            return

        name = self._entries[self._selected][0]
        full_path = self._directory / name

        if full_path.is_dir():
            self.query_one("#idx-status", Static).update(
                " Cannot delete directories from here"
            )
            return

        # Push confirmation screen
        from safari_writer.screens.file_ops import ConfirmScreen
        self.app.push_screen(
            ConfirmScreen(f"Delete {name}?"),
            callback=lambda confirmed: self._do_delete(full_path, confirmed),
        )

    def _do_delete(self, path: Path, confirmed: bool | None) -> None:
        if not confirmed:
            self.query_one("#idx-status", Static).update(" Delete cancelled")
            return
        try:
            path.unlink()
            self.query_one("#idx-status", Static).update(f" Deleted: {path.name}")
            self._scan_directory()
            self._selected = min(self._selected, len(self._entries) - 1)
            self._render_listing()
        except OSError as e:
            self.query_one("#idx-status", Static).update(f" Error: {e}")

    def _action_new_folder(self) -> None:
        """Create a new folder in the current directory."""
        from safari_writer.screens.file_ops import FilePromptScreen
        self.app.push_screen(
            FilePromptScreen("New Folder Name"),
            callback=self._do_new_folder,
        )

    def _do_new_folder(self, name: str | None) -> None:
        if not name:
            return
        try:
            (self._directory / name).mkdir(exist_ok=True)
            self.query_one("#idx-status", Static).update(f" Created: {name}")
            self._scan_directory()
            self._render_listing()
        except OSError as e:
            self.query_one("#idx-status", Static).update(f" Error: {e}")


class DrivePickerScreen(Screen):
    """When multiple external drives are found, let the user pick one."""

    CSS = INDEX_CSS

    def __init__(self, drives: list[Path]) -> None:
        super().__init__()
        self._drives = drives
        self._selected = 0

    def compose(self) -> ComposeResult:
        with Container(id="idx-container"):
            with Container(id="idx-header"):
                yield Static("*** SELECT EXTERNAL DRIVE ***", id="idx-title")
                yield Static("", id="idx-path")
                yield Static(
                    f"{'#':<4} {'DRIVE':<40} {'FREE':>10}",
                    id="idx-columns",
                )
            yield Static("", id="idx-listing")
            with Container(id="idx-footer"):
                yield Static("", id="idx-status")
                yield Static("Up/Down=select  Enter=open  Esc=back", id="idx-help")

    def on_mount(self) -> None:
        self._render_listing()

    def _render_listing(self) -> None:
        import shutil
        lines: list[str] = []
        for i, drive in enumerate(self._drives):
            try:
                free = _format_size(shutil.disk_usage(drive).free)
            except OSError:
                free = "???"
            line = f"  {i + 1:<4} {str(drive):<40} {free:>10}"
            if i == self._selected:
                line = f"[reverse]{line}[/reverse]"
            lines.append(line)
        self.query_one("#idx-listing", Static).update("\n".join(lines))

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.app.pop_screen()
        elif event.key == "up" and self._selected > 0:
            self._selected -= 1
            self._render_listing()
        elif event.key == "down" and self._selected < len(self._drives) - 1:
            self._selected += 1
            self._render_listing()
        elif event.key == "enter":
            drive = self._drives[self._selected]
            self.app.pop_screen()
            self.app.push_screen(IndexScreen(drive, label=f"External: {drive}"))
        event.stop()
