______________________________________________________________________

## name: i18n_audit description: Audit and update release-ready internationalization strings without re-learning the repo's i18n basics.

# i18n Audit

Use this skill when you need to add or update translations for a release pass. Do not start by re-inventing the i18n architecture. This repo already has one.

## The short version

- The locale runtime lives in `safari_writer\locale_info.py`.
- The active gettext domain is `safari_writer`.
- Translation catalogs live in `safari_writer\locales\*\LC_MESSAGES\safari_writer.po`.
- Catalogs are compiled with `make locale`, which runs `scripts\compile_mo.py`.
- Existing language catalogs are `en`, `eo`, `es`, `fr`, `is`, and `ru`.
- The common screen pattern is a local helper:

```python
import safari_writer.locale_info as _locale_info

def _(s: str) -> str:
    return _locale_info.get_translation().gettext(s)
```

- Many `safari_writer` screens already follow that pattern.
- Non-writer modules currently share locale-aware date formatting in places, but full UI-string translation is not broadly wired outside `safari_writer`. Audit those modules explicitly; do not assume coverage.

## Read these files first

Read these before roaming:

- `safari_writer\locale_info.py`
  - Runtime locale detection, gettext lookup, `.po` fallback, and date/time formatting.
- `safari_writer\locales\fr\LC_MESSAGES\safari_writer.po`
  - Good example catalog shape and header format.
- `scripts\compile_mo.py`
  - How `.po` files are turned into `.mo`.
- `Makefile`
  - `make locale` target.
- `tests\test_writer\test_locale_info.py`
  - Translation lookup expectations and `.po` fallback tests.
- `tests\test_writer\test_i18n_integration.py`
  - Broader i18n integration coverage.
- `spec\16_internationalization.md`
  - Intended architecture and release expectations.
- `spec\16_internationalization_TODO.md`
  - Known remaining gaps.
- `docs\go_live_tasks.md`
  - Release reminder to check new strings and translation catalogs.

## What is already true in this repo

1. The repo does **not** have a separate i18n framework per module.
1. The repo does **not** currently use a generated `.pot` workflow in day-to-day code.
1. The repo **does** already ship real `.po` catalogs under `safari_writer\locales`.
1. The repo **does** already resolve translations through `safari_writer.locale_info.get_translation()`.
1. The repo **does** already support `SAFARI_LOCALE` overrides for testing and manual verification.
1. The repo **does** already compile `.mo` files with a pure-Python script.

## Fast path: adding new translatable strings

When the task is "make this UI text translatable" or "update translations for release", do this:

1. Find the user-facing English string in code.
1. Reuse the existing `_()` helper pattern in that file. If the file already has `_()`, use it. If not, add the same tiny wrapper rather than inventing a new helper style.
1. Keep the English source string as the `msgid`.
1. Add or update that same `msgid` in every existing catalog:
   - `safari_writer\locales\en\LC_MESSAGES\safari_writer.po`
   - `safari_writer\locales\eo\LC_MESSAGES\safari_writer.po`
   - `safari_writer\locales\es\LC_MESSAGES\safari_writer.po`
   - `safari_writer\locales\fr\LC_MESSAGES\safari_writer.po`
   - `safari_writer\locales\is\LC_MESSAGES\safari_writer.po`
   - `safari_writer\locales\ru\LC_MESSAGES\safari_writer.po`
1. Run `make locale`.
1. Run the i18n tests.

Do not only update one language and call it done for a release pass unless the user explicitly asks for partial coverage.

## Release-pass audit order

For a major release, audit in this order:

### 1. Confirm runtime assumptions

- `safari_writer\locale_info.py`
- `safari_writer\__init__.py`
- `README.md` language section

You are checking:

- current supported locale override behavior
- current supported languages
- whether any new runtime helper behavior changed catalog expectations

### 2. Audit primary Writer screens first

These are the highest-signal places for release string churn:

- `safari_writer\screens\main_menu.py`
- `safari_writer\screens\editor.py`
- `safari_writer\screens\proofreader.py`
- `safari_writer\screens\global_format.py`
- `safari_writer\screens\doctor.py`
- `safari_writer\screens\mail_merge.py`
- `safari_writer\screens\print_screen.py`
- `safari_writer\screens\backup_screen.py`
- `safari_writer\app.py`

Look for:

- newly added English literals not wrapped in `_()`
- status messages
- prompts and confirmation text
- help text
- menu labels
- headings and banners
- string formatting placeholders that must stay intact, for example `{lang}` or `{needle!r}`

### 3. Then audit the sibling app modules

The app family includes:

- `safari_dos`
- `safari_chat`
- `safari_fed`
- `safari_base`
- `safari_repl`
- `safari_reader`
- `safari_slides`
- `safari_view`
- `safari_asm`
- `safari_basic`

Important: these modules are not all on the same translation-helper pattern yet.

For these modules, first determine which of the following is true:

- the module already imports `safari_writer.locale_info` and can reuse the existing gettext domain immediately
- the module only uses locale-aware formatting today and still has untranslated UI strings
- the module has user-facing text that should be translated before release but needs runtime wiring first

Default action:

- Reuse `safari_writer.locale_info.get_translation()` and the existing `safari_writer` catalog unless the task explicitly asks you to create a separate domain.
- Do **not** invent `safari_dos.po`, `safari_chat.po`, etc. as a speculative refactor.

## String-handling rules

- Keep English hotkey letters stable unless the task explicitly changes key bindings. The spec says translated labels do not imply translated hotkeys.
- Preserve placeholder names and formatting syntax exactly.
- Preserve punctuation and surrounding whitespace where it affects layout.
- Do not translate internal identifiers, file extensions, or command names unless the existing catalog already does so.
- Prefer updating existing `msgid` entries in place over creating near-duplicate strings.

## Catalog editing rules

- Keep the existing header style.
- Keep entries sorted and grouped consistently with the surrounding file style.
- If a string is intentionally untranslated in `en`, keep `msgstr` equal to `msgid`.
- If `.mo` files are stale, regenerate them with `make locale`; do not hand-edit `.mo` binaries.

## Search strategy that avoids thrashing

Start narrow before broad:

1. Search the specific files above for new English user-facing strings.
1. Search for local `_()` helpers and `get_translation()` usage.
1. Search the locale catalogs for the exact `msgid`.
1. Only then broaden to the rest of the repo for untranslated literals.

Useful patterns:

- `_locale_info.get_translation().gettext`
- `def _(s: str) -> str:`
- direct English UI literals in `screens.py`, `app.py`, `main.py`
- catalog entries in `safari_writer\locales\*\LC_MESSAGES\safari_writer.po`

## Validation

After translation edits:

1. Run `make locale`
1. Run:

```powershell
uv run pytest tests\test_writer\test_locale_info.py tests\test_writer\test_i18n_integration.py
```

3. If you changed runtime wiring, run the broader existing checks the task warrants, preferably `make check` if the change is substantial.
1. Manually spot-check with `SAFARI_LOCALE` if needed.

Examples:

```powershell
$env:SAFARI_LOCALE="fr"; safari-writer
$env:SAFARI_LOCALE="eo"; safari-writer
```

## Known gaps to remember

- Config-file locale override is still listed as not implemented in `spec\16_internationalization_TODO.md`.
- `ngettext` plural support is still listed as not wired into runtime helpers.
- CLI help/output localization is still incomplete.

Do not waste time "discovering" those again during a release pass. Either work on them directly or leave them alone if they are out of scope.
