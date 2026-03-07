"""Safari Writer theme definitions and settings persistence."""

from __future__ import annotations

import json
from pathlib import Path

from textual.theme import Theme

__all__ = [
    "THEMES",
    "DEFAULT_THEME",
    "load_settings",
    "save_settings",
]

# ---------------------------------------------------------------------------
# Theme definitions
# ---------------------------------------------------------------------------
# All themes target the classic AtariWriter/CRT aesthetic.

# Theme 1: Classic Blue (AtariWriter 80 default — blue screen, white text)
_classic_blue = Theme(
    name="classic-blue",
    primary="#0000aa",       # dark blue — used for backgrounds, bars
    secondary="#0000cc",
    accent="#ffff00",        # yellow key letters
    foreground="#ffffff",
    background="#0000aa",
    surface="#0000aa",
    panel="#000088",
    success="#00ff00",
    warning="#ffff00",
    error="#ff4444",
    dark=True,
)

# Theme 2: Green Phosphor (classic amber/green CRT monitor)
_green_phosphor = Theme(
    name="green-phosphor",
    primary="#003300",
    secondary="#004400",
    accent="#00ff44",
    foreground="#00ff44",
    background="#001a00",
    surface="#001a00",
    panel="#002200",
    success="#00ff44",
    warning="#ffff00",
    error="#ff4444",
    dark=True,
)

# Theme 3: Amber (warm CRT amber phosphor)
_amber = Theme(
    name="amber",
    primary="#2a1500",
    secondary="#331a00",
    accent="#ffcc00",
    foreground="#ffaa00",
    background="#1a0d00",
    surface="#1a0d00",
    panel="#220f00",
    success="#ffaa00",
    warning="#ffcc00",
    error="#ff4444",
    dark=True,
)

# Theme 4: High Contrast (white on black, accessibility)
_high_contrast = Theme(
    name="high-contrast",
    primary="#1a1a1a",
    secondary="#222222",
    accent="#00ccff",
    foreground="#ffffff",
    background="#000000",
    surface="#000000",
    panel="#111111",
    success="#00ff00",
    warning="#ffff00",
    error="#ff4444",
    dark=True,
)

THEMES: dict[str, Theme] = {
    t.name: t for t in [_classic_blue, _green_phosphor, _amber, _high_contrast]
}

THEME_LABELS: dict[str, str] = {
    "classic-blue":   "Classic Blue  (AtariWriter 80 default)",
    "green-phosphor": "Green Phosphor (vintage CRT monitor)",
    "amber":          "Amber         (warm phosphor CRT)",
    "high-contrast":  "High Contrast  (accessibility)",
}

DEFAULT_THEME = "classic-blue"

# ---------------------------------------------------------------------------
# Settings persistence
# ---------------------------------------------------------------------------

def _settings_path() -> Path:
    cfg = Path.home() / ".config" / "safari_writer"
    cfg.mkdir(parents=True, exist_ok=True)
    return cfg / "settings.json"


def load_settings() -> dict:
    """Load settings from disk; return defaults if missing or corrupt."""
    path = _settings_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}
        return data
    except (OSError, json.JSONDecodeError):
        return {}


def save_settings(settings: dict) -> None:
    """Persist settings dict to disk."""
    path = _settings_path()
    path.write_text(json.dumps(settings, indent=2), encoding="utf-8")
