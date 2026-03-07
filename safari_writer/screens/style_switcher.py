"""Style Switcher screen — choose and persist a UI colour theme."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual import events
from textual.widgets import Static

from safari_writer.themes import THEMES, THEME_LABELS, DEFAULT_THEME, save_settings, load_settings


SS_CSS = """
StyleSwitcherScreen {
    align: center middle;
    background: $background;
}

#ss-container {
    width: 60;
    height: auto;
    border: solid $accent;
    background: $surface;
    padding: 1 2;
}

#ss-title {
    text-align: center;
    text-style: bold;
    color: $accent;
    margin-bottom: 1;
}

.ss-item {
    height: 1;
    color: $foreground;
}

.ss-item-selected {
    height: 1;
    color: $background;
    background: $accent;
    text-style: bold;
}

#ss-hint {
    dock: bottom;
    height: 1;
    background: $primary;
    color: $foreground;
    padding: 0 1;
}
"""

THEME_NAMES = list(THEMES.keys())


class StyleSwitcherScreen(Screen):
    """Choose a UI theme; persists to settings.json."""

    CSS = SS_CSS

    BINDINGS = [
        Binding("escape", "exit_switcher", "Back", show=False),
        Binding("enter", "apply_theme", "Apply", show=False),
    ]

    def __init__(self, current_theme: str) -> None:
        super().__init__()
        # Resolve to a valid index
        if current_theme in THEME_NAMES:
            self._selected = THEME_NAMES.index(current_theme)
        else:
            self._selected = 0

    def compose(self) -> ComposeResult:
        from textual.containers import Container
        with Container(id="ss-container"):
            yield Static("*** STYLE SWITCHER ***", id="ss-title")
            for name in THEME_NAMES:
                label = THEME_LABELS.get(name, name)
                yield Static(label, classes="ss-item", id=f"ss-{name}")
        yield Static(
            " Up/Down choose  Enter apply  Esc back  (theme previews live)",
            id="ss-hint",
        )

    def on_mount(self) -> None:
        self._highlight()

    def _highlight(self) -> None:
        for i, name in enumerate(THEME_NAMES):
            widget = self.query_one(f"#ss-{name}", Static)
            if i == self._selected:
                widget.set_classes("ss-item-selected")
            else:
                widget.set_classes("ss-item")
        # Live preview: switch the app theme immediately
        chosen = THEME_NAMES[self._selected]
        self.app.theme = chosen  # type: ignore[attr-defined]

    def on_key(self, event: events.Key) -> None:
        if event.key == "up":
            self._selected = (self._selected - 1) % len(THEME_NAMES)
            self._highlight()
            event.stop()
        elif event.key == "down":
            self._selected = (self._selected + 1) % len(THEME_NAMES)
            self._highlight()
            event.stop()

    def action_apply_theme(self) -> None:
        chosen = THEME_NAMES[self._selected]
        self.app.theme = chosen  # type: ignore[attr-defined]
        settings = load_settings()
        settings["theme"] = chosen
        save_settings(settings)
        self.app.pop_screen()  # type: ignore[attr-defined]

    def action_exit_switcher(self) -> None:
        # Restore the theme that was active before we entered (the one saved)
        settings = load_settings()
        saved = settings.get("theme", DEFAULT_THEME)
        self.app.theme = saved  # type: ignore[attr-defined]
        self.app.pop_screen()  # type: ignore[attr-defined]
