"""Doctor screen — diagnostic info for troubleshooting."""

from __future__ import annotations

import os
import platform
import sys
from importlib import metadata
from pathlib import Path

from textual import events
from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Static

import safari_writer.locale_info as _locale_info


def _(s: str) -> str:
    return _locale_info.get_translation().gettext(s)


_DOCTOR_CSS = """
DoctorScreen {
    align: center middle;
    background: $background;
}

#doc-outer {
    width: 78;
    height: 28;
    border: solid $accent;
    background: $surface;
    padding: 0;
}

#doc-title {
    height: 1;
    text-align: center;
    text-style: bold;
    color: $accent;
    margin-top: 1;
}

#doc-body {
    height: 1fr;
    padding: 1 2;
    color: $foreground;
    overflow-y: auto;
}

#doc-help {
    height: 1;
    background: $primary;
    color: $foreground;
    padding: 0 1;
}
"""


def _pkg_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "(not installed)"


def _check_enchant() -> str:
    try:
        import enchant

        d = enchant.Dict("en_US")
        provider = d.provider
        return f"OK  provider={provider.name}  lang=en_US"
    except Exception as exc:
        return f"UNAVAILABLE  ({exc})"


def _file_status(path: Path) -> str:
    if path.is_file():
        size = path.stat().st_size
        return f"exists ({size:,} bytes)"
    if path.is_dir():
        return "directory (unexpected)"
    return "not found"


def _dir_status(path: Path) -> str:
    if path.is_dir():
        try:
            count = sum(1 for _ in path.iterdir())
        except OSError:
            count = -1
        return f"exists ({count} items)"
    return "not found"


def gather_doctor_info(doc_language: str = "") -> str:
    """Collect diagnostic info and return formatted text."""
    home = Path.home()
    safari_home = home / ".safari"
    config_dir = home / ".config" / "safari_writer"
    settings_file = config_dir / "settings.json"
    personal_dict = safari_home / "personal.dict"
    macros_dir = safari_home / "macros"
    safari_dos_dir = home / ".safari_dos"

    lines: list[str] = []

    # -- Versions --
    lines.append("[bold]Versions[/]")
    lines.append(f"  Safari Writer:  {_pkg_version('safari-writer')}")
    lines.append(f"  Python:         {sys.version.split()[0]}")
    lines.append(f"  Textual:        {_pkg_version('textual')}")
    lines.append(f"  pyenchant:      {_pkg_version('pyenchant')}")
    lines.append(f"  Pygments:       {_pkg_version('pygments')}")
    lines.append(f"  mastodon.py:    {_pkg_version('mastodon-py')}")
    lines.append(f"  python-dotenv:  {_pkg_version('python-dotenv')}")
    lines.append("")

    # -- Platform --
    lines.append("[bold]Platform[/]")
    lines.append(f"  OS:             {platform.system()} {platform.release()}")
    lines.append(f"  Machine:        {platform.machine()}")
    lines.append(f"  Python path:    {sys.executable}")
    lines.append(f"  Working dir:    {os.getcwd()}")
    lines.append("")

    # -- Paths --
    lines.append("[bold]Paths[/]")
    lines.append(f"  Home:           {home}")
    lines.append(f"  Safari home:    {safari_home}  ({_dir_status(safari_home)})")
    lines.append(f"  Config dir:     {config_dir}  ({_dir_status(config_dir)})")
    lines.append(f"  Settings file:  {settings_file}  ({_file_status(settings_file)})")
    lines.append(f"  Personal dict:  {personal_dict}  ({_file_status(personal_dict)})")
    lines.append(f"  Macros dir:     {macros_dir}  ({_dir_status(macros_dir)})")
    lines.append(f"  Safari DOS dir: {safari_dos_dir}  ({_dir_status(safari_dos_dir)})")
    lines.append("")

    # -- Settings content --
    lines.append("[bold]Settings[/]")
    if settings_file.is_file():
        try:
            import json

            data = json.loads(settings_file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                for k, v in data.items():
                    lines.append(f"  {k}: {v}")
                if not data:
                    lines.append("  (empty)")
            else:
                lines.append(f"  (unexpected type: {type(data).__name__})")
        except Exception as exc:
            lines.append(f"  (error reading: {exc})")
    else:
        lines.append("  (no settings file — using defaults)")
    lines.append("")

    # -- Locale (i18n) --
    from safari_writer.locale_info import LANGUAGE, LOCALE, REGION, available_languages

    lines.append("[bold]Locale[/]")
    lines.append(f"  Detected:       {LOCALE}")
    lines.append(f"  Language:       {LANGUAGE}")
    lines.append(f"  Region:         {REGION or '(none)'}")
    active = doc_language or LOCALE
    lines.append(f"  Active (doc):   {active}{'' if doc_language else ' (auto)'}")
    env_locale = os.environ.get("SAFARI_LOCALE")
    lines.append(f"  SAFARI_LOCALE:  {env_locale or '(not set)'}")
    lines.append("")

    # -- Spell checker --
    lines.append("[bold]Spell Checker[/]")
    lines.append(f"  enchant:        {_check_enchant()}")
    langs = available_languages()
    lines.append(f"  dictionaries:   {', '.join(langs) if langs else '(none found)'}")
    lines.append("")

    # -- Environment hints --
    lines.append("[bold]Environment[/]")
    env_vars = [
        "TERM",
        "COLORTERM",
        "LANG",
        "LC_ALL",
        "MASTODON_BASE_URL",
        "MASTODON_ACCESS_TOKEN",
    ]
    for var in env_vars:
        val = os.environ.get(var)
        if var in ("MASTODON_ACCESS_TOKEN",) and val:
            val = val[:8] + "..."
        lines.append(f"  {var}: {val or '(not set)'}")

    return "\n".join(lines)


class DoctorScreen(Screen):
    """Diagnostic information screen."""

    CSS = _DOCTOR_CSS

    def __init__(self, doc_language: str = "") -> None:
        super().__init__()
        self._doc_language = doc_language

    def compose(self) -> ComposeResult:
        with Container(id="doc-outer"):
            yield Static(_("*** SAFARI WRITER — DOCTOR ***"), id="doc-title")
            yield Static(
                gather_doctor_info(doc_language=self._doc_language), id="doc-body"
            )
            yield Static(
                " Esc Return to menu",
                id="doc-help",
            )

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.app.pop_screen()
            event.stop()
