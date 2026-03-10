"""MacroPickerScreen — modal screen for selecting a .BAS macro file."""

from __future__ import annotations

import re
from importlib.resources import files
from pathlib import Path

from textual import events
from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Static

__all__ = ["MacroPickerScreen", "bundled_macros_dir", "default_macros_dir"]


def bundled_macros_dir() -> Path | None:
    """Return the path to the package-bundled macros directory, or None."""
    try:
        ref = files("safari_writer").joinpath("macros")
        # importlib.resources traversable → convert to Path
        p = Path(str(ref))
        if p.is_dir():
            return p
    except Exception:
        pass
    return None

_PICKER_CSS = """
MacroPickerScreen {
    align: center middle;
}

#macro-dialog {
    width: 72;
    height: auto;
    max-height: 80%;
    border: solid $primary;
    background: $surface;
    padding: 1 2;
}

#macro-title {
    text-align: center;
    text-style: bold;
    color: $accent;
    margin-bottom: 1;
}

#macro-list {
    height: auto;
    max-height: 20;
    color: $foreground;
}

#macro-footer {
    text-align: center;
    color: $text-muted;
    margin-top: 1;
}
"""

_DESCRIPTION_RE = re.compile(r"^\d*\s*REM\s+(.*)", re.IGNORECASE)


def default_macros_dir() -> Path:
    """Return the default macros directory, creating it if absent."""
    d = Path.home() / ".safari" / "macros"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _first_rem(path: Path) -> str:
    """Return the text of the first REM line in a .BAS file, or ''."""
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            m = _DESCRIPTION_RE.match(raw.strip())
            if m:
                return m.group(1).strip()
    except OSError:
        pass
    return ""


def _list_macros(directory: Path) -> list[Path]:
    try:
        return sorted(directory.glob("*.bas")) + sorted(directory.glob("*.BAS"))
    except OSError:
        return []


def _merged_macros(user_dir: Path) -> list[Path]:
    """Return bundled macros + user macros, user macros shadow same stem."""
    bundled: dict[str, Path] = {}
    bd = bundled_macros_dir()
    if bd is not None:
        for p in _list_macros(bd):
            bundled[p.stem.lower()] = p

    user: dict[str, Path] = {}
    for p in _list_macros(user_dir):
        user[p.stem.lower()] = p

    # Merge: user overrides bundled; sort alphabetically
    merged = {**bundled, **user}
    return sorted(merged.values(), key=lambda p: p.stem.lower())


class MacroPickerScreen(ModalScreen[Path | None]):
    """Modal list of .BAS files from the macros directory."""

    CSS = _PICKER_CSS

    def __init__(self, macros_dir: Path | None = None) -> None:
        super().__init__()
        self._dir = macros_dir or default_macros_dir()
        self._macros: list[Path] = _merged_macros(self._dir)
        self._index = 0

    def compose(self) -> ComposeResult:
        with Container(id="macro-dialog"):
            yield Static("=== SAFARI BASIC — SELECT MACRO ===", id="macro-title")
            yield Static(self._render_list(), id="macro-list")
            yield Static(
                "Up/Down Move  Enter Select  Esc Cancel", id="macro-footer"
            )

    def _render_list(self) -> str:
        if not self._macros:
            return (
                f"No macros found in:\n  {self._dir}\n\n"
                "Place .bas files there to get started."
            )
        lines: list[str] = []
        for i, path in enumerate(self._macros):
            cursor = ">" if i == self._index else " "
            desc = _first_rem(path)
            name = path.stem
            if desc:
                lines.append(f"{cursor} {name:<24} {desc}")
            else:
                lines.append(f"{cursor} {name}")
        return "\n".join(lines)

    def _refresh_list(self) -> None:
        self.query_one("#macro-list", Static).update(self._render_list())

    def on_key(self, event: events.Key) -> None:
        key = event.key
        if key in {"up", "k"}:
            if self._macros:
                self._index = max(0, self._index - 1)
                self._refresh_list()
        elif key in {"down", "j"}:
            if self._macros:
                self._index = min(len(self._macros) - 1, self._index + 1)
                self._refresh_list()
        elif key == "enter":
            if self._macros:
                self.dismiss(self._macros[self._index])
            else:
                self.dismiss(None)
        elif key == "escape":
            self.dismiss(None)
