"""Cross-platform locale detection and locale-aware formatting.

Detection priority:
    1. SAFARI_LOCALE environment variable
    2. OS-native query (Windows / macOS / Linux)
    3. Fallback: en_US
"""

from __future__ import annotations

import gettext as _gettext_mod
import locale
import os
import platform
import re
from datetime import datetime
from pathlib import Path

from safari_writer.windows_api import get_kernel32

__all__ = [
    "LANGUAGE",
    "LOCALE",
    "REGION",
    "available_languages",
    "format_datetime",
    "get_locale",
    "get_translation",
    "refresh",
]

# ---------------------------------------------------------------------------
# Internal: Windows LCID → IETF tag mapping (common subset)
# ---------------------------------------------------------------------------

_LCID_MAP: dict[int, str] = {
    0x0409: "en_US",
    0x0809: "en_GB",
    0x0C09: "en_AU",
    0x1009: "en_CA",
    0x0407: "de_DE",
    0x0807: "de_CH",
    0x0C07: "de_AT",
    0x040C: "fr_FR",
    0x080C: "fr_BE",
    0x0C0C: "fr_CA",
    0x0410: "it_IT",
    0x0C0A: "es_ES",
    0x080A: "es_MX",
    0x2C0A: "es_AR",
    0x0416: "pt_BR",
    0x0816: "pt_PT",
    0x0413: "nl_NL",
    0x0813: "nl_BE",
    0x041D: "sv_SE",
    0x0414: "nb_NO",
    0x0814: "nn_NO",
    0x0406: "da_DK",
    0x040B: "fi_FI",
    0x0415: "pl_PL",
    0x0405: "cs_CZ",
    0x040E: "hu_HU",
    0x0418: "ro_RO",
    0x0419: "ru_RU",
    0x0422: "uk_UA",
    0x0411: "ja_JP",
    0x0412: "ko_KR",
    0x0804: "zh_CN",
    0x0404: "zh_TW",
    0x0401: "ar_SA",
    0x040D: "he_IL",
    0x041E: "th_TH",
    0x042A: "vi_VN",
    0x0421: "id_ID",
    0x041F: "tr_TR",
    0x0408: "el_GR",
}

_IETF_RE = re.compile(r"^[a-z]{2,3}([_-][A-Za-z]{2,4})?$")


def _normalize_tag(raw: str) -> str:
    """Normalize a locale tag like 'fr-FR', 'fr_FR.UTF-8', 'French' → 'fr_FR'."""
    # Strip encoding suffix
    tag = raw.split(".")[0].split("@")[0].strip()
    tag = tag.replace("-", "_")
    if _IETF_RE.match(tag):
        parts = tag.split("_")
        if len(parts) == 2:
            return f"{parts[0].lower()}_{parts[1].upper()}"
        return parts[0].lower()
    return ""


def _detect_os_locale() -> str:
    """Query the OS for the user's preferred locale."""
    system = platform.system()

    # --- Windows ---
    if system == "Windows":
        try:
            kernel32 = get_kernel32()
            if kernel32 is not None:
                lcid = int(kernel32.GetUserDefaultUILanguage())
                if lcid in _LCID_MAP:
                    return _LCID_MAP[lcid]
        except Exception:
            pass

    # --- macOS ---
    if system == "Darwin":
        try:
            import subprocess

            result = subprocess.run(
                ["defaults", "read", ".GlobalPreferences", "AppleLanguages"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                # Parse plist-style array: first entry like "en-US"
                for line in result.stdout.splitlines():
                    line = line.strip().strip('",')
                    tag = _normalize_tag(line)
                    if tag:
                        return tag
        except Exception:
            pass

    # --- Generic fallback (all platforms) ---
    for var in ("LC_ALL", "LC_MESSAGES", "LANG"):
        val = os.environ.get(var, "")
        if val:
            tag = _normalize_tag(val)
            if tag:
                return tag

    # Python's own locale detection
    try:
        raw, _ = locale.getdefaultlocale()
        if raw:
            tag = _normalize_tag(raw)
            if tag:
                return tag
    except Exception:
        pass

    return "en_US"


def get_locale() -> str:
    """Return the resolved locale tag (e.g. ``'en_US'``, ``'de_DE'``).

    Priority: ``SAFARI_LOCALE`` env var → OS detection → ``en_US``.
    """
    env = os.environ.get("SAFARI_LOCALE", "").strip()
    if env:
        tag = _normalize_tag(env)
        if tag:
            return tag

    return _detect_os_locale()


# ---------------------------------------------------------------------------
# Module-level cached values
# ---------------------------------------------------------------------------

LOCALE: str = get_locale()
LANGUAGE: str = LOCALE.split("_")[0] if "_" in LOCALE else LOCALE
REGION: str = LOCALE.split("_")[1] if "_" in LOCALE else ""


def refresh() -> None:
    """Re-detect and update the module-level locale cache.

    Useful after setting ``SAFARI_LOCALE`` in tests.
    """
    global LOCALE, LANGUAGE, REGION
    LOCALE = get_locale()
    LANGUAGE = LOCALE.split("_")[0] if "_" in LOCALE else LOCALE
    REGION = LOCALE.split("_")[1] if "_" in LOCALE else ""


# ---------------------------------------------------------------------------
# Level 3: gettext-based UI string translation
# ---------------------------------------------------------------------------

_LOCALES_DIR = Path(__file__).parent / "locales"

# Cache: lang_tag → GNUTranslations (or NullTranslations for fallback)
_translation_cache: dict[str, _gettext_mod.NullTranslations] = {}


class _DictTranslations(_gettext_mod.NullTranslations):
    """Simple translation catalog backed by msgid/msgstr pairs from a .po file."""

    def __init__(self, catalog: dict[str, str]) -> None:
        super().__init__()
        self._catalog = catalog

    def gettext(self, message: str) -> str:
        return self._catalog.get(message, message)


def _parse_po_catalog(po_path: Path) -> dict[str, str]:
    """Parse a gettext .po file into a msgid → msgstr mapping."""

    def _unescape(text: str) -> str:
        return text.encode("raw_unicode_escape").decode("unicode_escape")

    catalog: dict[str, str] = {}
    msgid = ""
    msgstr = ""
    in_msgid = False
    in_msgstr = False

    for raw_line in po_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("#") or not line:
            if in_msgstr and msgid and msgstr:
                catalog[msgid] = msgstr
            msgid = ""
            msgstr = ""
            in_msgid = False
            in_msgstr = False
            continue
        if line.startswith("msgid "):
            if in_msgstr and msgid and msgstr:
                catalog[msgid] = msgstr
            msgid = _unescape(line[7:-1])
            msgstr = ""
            in_msgid = True
            in_msgstr = False
            continue
        if line.startswith("msgstr "):
            msgstr = _unescape(line[8:-1])
            in_msgid = False
            in_msgstr = True
            continue
        if line.startswith('"') and line.endswith('"'):
            chunk = _unescape(line[1:-1])
            if in_msgid:
                msgid += chunk
            elif in_msgstr:
                msgstr += chunk

    if in_msgstr and msgid and msgstr:
        catalog[msgid] = msgstr

    return catalog


def _load_po_translation(candidate: str) -> _gettext_mod.NullTranslations | None:
    """Load a translation directly from a .po catalog when .mo is unavailable."""
    po_path = _LOCALES_DIR / candidate / "LC_MESSAGES" / "safari_writer.po"
    if not po_path.is_file():
        return None
    return _DictTranslations(_parse_po_catalog(po_path))


def get_translation(lang: str | None = None) -> _gettext_mod.NullTranslations:
    """Return a GNUTranslations object for *lang* (e.g. ``'fr_FR'`` or ``'fr'``).

    Resolution order for catalog lookup:
        1. Full tag  (e.g. ``fr_FR``)
        2. Language-only  (e.g. ``fr``)
        3. NullTranslations (identity, English passthrough)

    The result is cached per resolved language tag.
    """
    raw_resolved = lang or LOCALE
    resolved = _normalize_tag(raw_resolved) or raw_resolved
    if resolved in _translation_cache:
        return _translation_cache[resolved]

    # Try candidates: full tag first, then bare language code
    lang_code = resolved.split("_")[0] if "_" in resolved else resolved
    candidates = [resolved, lang_code] if lang_code != resolved else [resolved]

    trans: _gettext_mod.NullTranslations | None = None
    for candidate in candidates:
        try:
            trans = _gettext_mod.translation(
                "safari_writer",
                localedir=str(_LOCALES_DIR),
                languages=[candidate],
            )
            break
        except FileNotFoundError:
            trans = _load_po_translation(candidate)
            if trans is not None:
                break

    if trans is None:
        trans = _gettext_mod.NullTranslations()

    _translation_cache[resolved] = trans
    return trans


# ---------------------------------------------------------------------------
# Level 1: available spell-check languages
# ---------------------------------------------------------------------------


def available_languages() -> list[str]:
    """Return language tags for all installed enchant dictionaries."""
    try:
        import enchant

        return sorted(enchant.list_languages())
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Level 2: locale-aware datetime formatting
# ---------------------------------------------------------------------------

# Try to set LC_TIME once at import time so strftime picks up locale formats.
try:
    locale.setlocale(locale.LC_TIME, "")
except locale.Error:
    pass


def format_datetime(dt: datetime, style: str = "full") -> str:
    """Format a datetime according to the user's locale.

    Styles:
        ``'full'``  — date + time with seconds  (for clocks)
        ``'short'`` — date + time, no seconds    (for file listings)
        ``'date'``  — date only
        ``'time'``  — time only

    Falls back to ISO 8601 if locale formatting fails.
    """
    try:
        if style == "full":
            return dt.strftime("%x %X")
        if style == "short":
            return dt.strftime("%x %H:%M")
        if style == "date":
            return dt.strftime("%x")
        if style == "time":
            return dt.strftime("%X")
    except Exception:
        pass

    # ISO fallback
    if style == "full":
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    if style == "short":
        return dt.strftime("%Y-%m-%d %H:%M")
    if style == "date":
        return dt.strftime("%Y-%m-%d")
    if style == "time":
        return dt.strftime("%H:%M:%S")
    return dt.isoformat()
