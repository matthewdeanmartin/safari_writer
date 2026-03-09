# Spec 16 — Internationalization (i18n)

**Status: Levels 0, 1, 2, 3 implemented.** Initial languages: English (en), Esperanto (eo), French (fr), Icelandic (is), Russian (ru), Spanish (es).

Safari Writer internationalization, implemented in three progressive levels. Each level is independently shippable. The guiding principle is **transparent OS-native locale detection** — the app reads the user's locale from the operating system and adapts, with no manual configuration required (but with an override escape hatch).

---

## Level 0: Locale Detection Foundation

Before any visible i18n work, establish the plumbing that all three levels depend on.

### 0.1 Detect the OS Locale

Create a module `safari_writer/locale_info.py` that exposes a single resolved locale:

```python
def get_locale() -> str:
    """Return an IETF-style locale tag, e.g. 'en_US', 'de_DE', 'ja_JP'."""
```

Detection order:

1. **Explicit override** — environment variable `SAFARI_LOCALE` (e.g. `SAFARI_LOCALE=fr_FR`). This is the escape hatch for testing, CI, and users whose OS locale doesn't reflect their preference.
2. **OS-native query** (cross-platform):
   - **Windows**: `ctypes.windll.kernel32.GetUserDefaultUILanguage()` → map the LCID to an IETF tag. Fall back to `locale.getdefaultlocale()`.
   - **macOS**: Read `defaults read .GlobalPreferences AppleLanguages` (returns an ordered list). Parse the first entry. Fall back to `locale.getdefaultlocale()`.
   - **Linux / other**: `locale.getdefaultlocale()`, or parse `$LANG` / `$LC_ALL` / `$LC_MESSAGES`.
3. **Fallback**: `en_US`.

The result is cached at startup and exposed as `locale_info.LOCALE` (the full tag, e.g. `fr_FR`) and convenience properties `locale_info.LANGUAGE` (`fr`) and `locale_info.REGION` (`FR`).

### 0.2 Config File Override

If `~/.safari_writer/config.toml` (or the app's future config system) contains a `locale = "pt_BR"` key, that takes precedence over the OS query but not the env var. Priority:

```
SAFARI_LOCALE env var  >  config file  >  OS detection  >  en_US
```

---

## Level 1: Multilingual Spell Check

**Goal**: The Proofreader uses the correct dictionary for the user's language automatically, and supports switching languages per-document.

### 1.1 Language-Aware Dictionary Loading

Modify `proofing.make_checker()` to accept a language tag:

```python
def make_checker(lang: str | None = None) -> SpellChecker | None:
    """Return an enchant dictionary for *lang*, defaulting to the OS locale."""
    lang = lang or locale_info.LOCALE  # e.g. 'de_DE'
    try:
        import enchant
        return enchant.Dict(lang)
    except enchant.DictNotFoundError:
        # Try the bare language: 'de'
        try:
            return enchant.Dict(locale_info.LANGUAGE)
        except Exception:
            return None
    except Exception:
        return None
```

### 1.2 Available Languages Query

Add a helper to list installed dictionaries:

```python
def available_languages() -> list[str]:
    """Return language tags for all installed enchant dictionaries."""
    try:
        import enchant
        return enchant.list_languages()
    except Exception:
        return []
```

Expose this in the Doctor screen (`? Doctor`) so users can see what's installed and what's missing.

### 1.3 Per-Document Language

The `.sfw` file header (or a new metadata block) gains an optional `lang` field:

```
%%lang: de_DE
```

When present, the Proofreader uses that language instead of the OS locale. The Global Format screen gets a new **Language (K)** field that sets this value. The field shows the current effective language and lets the user pick from `available_languages()`.

### 1.4 Proofreader Screen Updates

- The Proofreader header line shows the active dictionary language (e.g. `[Dict: de_DE]`).
- If no dictionary is available for the requested language, show a clear message: `"No dictionary for 'xx_XX'. Install one or change language in Global Format."` The proofreader still runs — it just can't flag misspellings.

### 1.5 Personal Dictionaries Remain Language-Neutral

Personal dictionaries are plain word lists. They apply regardless of the active language. No changes needed.

---

## Level 2: Localized System Clock & Date/Time Formatting

**Goal**: Dates and times shown in the UI respect the user's locale conventions.

### 2.1 Identify All Date/Time Display Points

Current locations (may grow):

| Location | Current format | Code path |
|---|---|---|
| Main Menu clock | `%Y-%m-%d %H:%M:%S` | `main_menu.py:_clock_text()` |
| Safari DOS timestamps | `%Y-%m-%d %H:%M` | `safari_dos/services.py:format_timestamp()` |
| Safari Fed timestamps | `%Y-%m-%d %H:%M UTC` | `safari_fed/client.py` |

### 2.2 Locale-Aware Formatting Helper

Add to `locale_info.py`:

```python
from datetime import datetime

def format_datetime(dt: datetime, style: str = "full") -> str:
    """Format a datetime according to the user's locale.

    Styles:
        'full'  — date + time with seconds (for clocks)
        'short' — date + time without seconds (for file listings)
        'date'  — date only
        'time'  — time only
    """
```

Implementation strategy — keep it **stdlib-only** (no `babel` dependency):

- Use `locale.setlocale(locale.LC_TIME, ...)` in a thread-local or process-wide init, then use `dt.strftime()` with locale-sensitive format codes (`%x` for date, `%X` for time, `%c` for full).
- On Windows, `locale.setlocale` accepts locale names like `"German_Germany"` or `""` (system default). Map the detected IETF tag to the Windows locale name if needed, or simply call `setlocale(LC_TIME, "")` at startup to use the OS default.
- Provide a **fixed-width fallback** for TUI column alignment: if the locale-formatted string exceeds a max width, truncate or fall back to ISO 8601. The Main Menu clock widget and Safari DOS file listings need predictable widths.

### 2.3 Wire It Up

Replace all hardcoded `strftime` calls with `locale_info.format_datetime()`. The clock, file listings, and timestamps all go through this single function.

### 2.4 12-Hour vs. 24-Hour

Respect the OS convention. Most locales already handle this via `%X`. For the Main Menu clock specifically, if the user's locale uses 12-hour time, show AM/PM. No app-level toggle — just follow the OS.

---

## Level 3: Localized UI Strings

**Goal**: All user-facing text (menu labels, prompts, error messages, status lines) can be translated.

### 3.1 String Catalog Approach

Use Python's built-in `gettext` module. It's cross-platform, well-understood, and requires no external dependencies.

#### Directory layout

```
safari_writer/
  locales/
    en/
      LC_MESSAGES/
        safari_writer.po
        safari_writer.mo
    de/
      LC_MESSAGES/
        safari_writer.po
        safari_writer.mo
    ...
```

#### Initialization (in `locale_info.py` or app startup)

```python
import gettext

_translations = gettext.translation(
    "safari_writer",
    localedir=Path(__file__).parent / "locales",
    languages=[LOCALE, LANGUAGE, "en"],
    fallback=True,
)
_ = _translations.gettext
```

Export `_` so all modules can do:

```python
from safari_writer.locale_info import _
```

### 3.2 Mark All Strings

Wrap every user-facing string with `_()`:

```python
# Before
COL1_ITEMS = [
    ("C", "reate File", "create"),
    ...
]

# After
COL1_ITEMS = [
    ("C", _("reate File"), "create"),
    ...
]
```

**Scope of strings to mark** (non-exhaustive):

- Main Menu labels (COL1, COL2, COL3 items)
- Editor status line text (Insert/Type-over, Uppercase/Lowercase, "Bytes Free")
- All message-window prompts ("Save changes?", "File loaded.", etc.)
- Proofreader prompts ("Correct Word", "Keep This Spelling", etc.)
- Mail Merge field labels and prompts
- Global Format field labels
- Error messages
- Doctor diagnostics labels
- CLI `--help` text and output messages

**Do NOT translate**:

- Internal identifiers and action keys (the `"create"`, `"edit"` action strings)
- Hotkey letters — these stay as the English letter for now (translating hotkeys is a Level 4 concern, if ever)
- File format tokens (`%%lang:`, control characters)
- Log messages

### 3.3 Extraction Workflow

Use `xgettext` or `pygettext` to extract marked strings into a `.pot` template:

```bash
xgettext -d safari_writer -o locales/safari_writer.pot safari_writer/**/*.py
```

Translators work on `.po` files. Compile to `.mo` with `msgfmt`. Ship `.mo` files in the package.

### 3.4 Initial Language Support

Ship with:

- **English (en)** — the source strings, always complete
- **One proof-of-concept translation** (e.g. Spanish or German) to validate the pipeline

Community contributions welcome for additional languages.

### 3.5 Hotkey Considerations

The Main Menu uses the first letter of each English command as the hotkey (`C`reate, `E`dit, `V`erify...). In translated UIs, the hotkeys remain the same English letters. The translated label is displayed but the key binding doesn't change. This avoids confusion and keeps keyboard muscle memory consistent. A future enhancement could allow locale-specific hotkey overrides, but that's out of scope for Level 3.

### 3.6 Plurals and Interpolation

Use `ngettext` for plural forms:

```python
from safari_writer.locale_info import ngettext

msg = ngettext("{n} word", "{n} words", count).format(n=count)
```

For interpolated strings, use named placeholders so translators can reorder:

```python
_("File '{filename}' saved ({size} bytes)")
```

---

## Cross-Cutting Concerns

### Testing

- Add a `SAFARI_LOCALE` env var fixture to tests so locale behavior is deterministic.
- Test `locale_info.get_locale()` with mocked OS calls for all three platforms.
- Test spellcheck with at least two languages (en_US + one other).
- Test date formatting with a known locale to assert expected output.
- Test that all `_()` marked strings resolve without `KeyError` in the fallback (English) locale.

### Dependencies

| Level | New dependencies |
|---|---|
| 0 | None (stdlib only) |
| 1 | None (pyenchant already a dependency; users install OS dictionaries) |
| 2 | None (stdlib `locale` module) |
| 3 | None (stdlib `gettext` module) |

All four levels are **zero new dependencies**. The entire i18n stack is stdlib.

### Packaging

- `.mo` files are included in the sdist/wheel via `package_data` in `pyproject.toml`.
- Document how to install additional enchant dictionaries per OS:
  - **Linux**: `apt install hunspell-de` (or equivalent)
  - **macOS**: `brew install hunspell` + download `.dic` files
  - **Windows**: enchant bundles several dictionaries; extras go in `enchant/share/enchant/hunspell/`

### Migration / Backwards Compatibility

- All levels are additive. No existing behavior changes unless a non-English locale is detected.
- The `%%lang:` header in `.sfw` files is optional. Old files without it use the OS locale.
- English remains the default. Users on `en_US` see zero difference.
