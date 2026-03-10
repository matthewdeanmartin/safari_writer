"""Backup & Restore screen for Safari Writer."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Static, ListView, ListItem, Label

import safari_writer.locale_info as _locale_info
from safari_writer.autosave import BackupMeta, list_backups, delete_backup


def _(s: str) -> str:
    return _locale_info.get_translation().gettext(s)


_CSS = """
BackupScreen {
    background: $background;
    layout: vertical;
}

#backup-title {
    text-align: center;
    text-style: bold;
    color: $accent;
    height: 1;
    margin-bottom: 1;
}

#backup-list {
    height: 1fr;
    border: solid $accent;
    background: $surface;
}

BackupItem {
    height: 1;
    padding: 0 1;
    color: $foreground;
}

BackupItem:focus, BackupItem:hover {
    background: $accent 30%;
}

#backup-footer {
    dock: bottom;
    height: 3;
    layout: vertical;
}

#backup-help {
    height: 1;
    background: $secondary;
    color: $foreground;
    padding: 0 1;
}

#backup-status {
    height: 1;
    background: $primary;
    color: $foreground;
    padding: 0 1;
}

#backup-empty {
    text-align: center;
    color: $secondary;
    margin-top: 2;
}
"""


class BackupItem(ListItem):
    """A single row in the backup list."""

    def __init__(self, meta: BackupMeta) -> None:
        super().__init__()
        self.meta = meta

    def compose(self) -> ComposeResult:
        name = self.meta.display_name
        ts = self.meta.time_str
        yield Label(f"{ts}  {name}")


class BackupScreen(Screen):
    """Browse abandoned backups and resume editing or discard them."""

    CSS = _CSS

    BINDINGS = [
        Binding("r", "resume", "Resume editing", show=True),
        Binding("x", "discard", "Discard backup", show=True),
        Binding("escape", "go_back", "Back", show=True),
    ]

    def __init__(
        self,
        on_resume: Callable[[Path, str], None] | None = None,
    ) -> None:
        super().__init__()
        self._on_resume = on_resume
        self._backups: list[BackupMeta] = []
        self._status = ""

    def compose(self) -> ComposeResult:
        from textual.containers import Container

        yield Static(_("*** BACKUP & RESTORE ***"), id="backup-title")
        self._backups = list_backups()

        with Container():
            if self._backups:
                lv = ListView(id="backup-list")
                yield lv
            else:
                yield Static(
                    _("No backups found."), id="backup-empty"
                )

        with Container(id="backup-footer"):
            yield Static(
                _("R=Resume editing  X=Discard  Esc=Back"),
                id="backup-help",
            )
            yield Static(self._status, id="backup-status")

    def on_mount(self) -> None:
        try:
            lv = self.query_one("#backup-list", ListView)
        except Exception:
            return
        for meta in self._backups:
            lv.append(BackupItem(meta))

    def _selected_meta(self) -> BackupMeta | None:
        try:
            lv = self.query_one("#backup-list", ListView)
            item = lv.highlighted_child
            if isinstance(item, BackupItem):
                return item.meta
        except Exception:
            pass
        return None

    def _set_status(self, msg: str) -> None:
        self._status = msg
        try:
            self.query_one("#backup-status", Static).update(msg)
        except Exception:
            pass

    def action_resume(self) -> None:
        meta = self._selected_meta()
        if meta is None:
            self._set_status(_("No backup selected"))
            return
        if self._on_resume:
            self._on_resume(meta.path, meta.original_filename)

    def action_discard(self) -> None:
        meta = self._selected_meta()
        if meta is None:
            self._set_status(_("No backup selected"))
            return
        # Remove from list widget
        try:
            lv = self.query_one("#backup-list", ListView)
            item = lv.highlighted_child
            if item is not None:
                item.remove()
        except Exception:
            pass
        delete_backup(meta.path)
        self._backups = [b for b in self._backups if b.path != meta.path]
        self._set_status(f"Discarded: {meta.display_name}  {meta.time_str}")

    def action_go_back(self) -> None:
        self.dismiss()
