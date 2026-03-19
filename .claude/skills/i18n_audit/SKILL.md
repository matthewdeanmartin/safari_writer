---
name: i18n_audit
description: Audit and update release-ready internationalization strings without re-learning the safari_writer i18n setup.
---

# i18n Audit

Use this skill when you need to add or update translations for a release pass. Do not start by re-inventing the i18n architecture. This repo already has one.

## The short version

- The locale runtime lives in `safari_writer/locale_info.py`.
- The active gettext domain is `safari_writer`.
- Translation catalogs live in `safari_writer/locales/*/LC_MESSAGES/safari_writer.po`.
- Catalogs are compiled with `make locale`, which runs `scripts/compile_mo.py`.
- Existing language catalogs are `en`, `eo`, `es`, `fr`, `is`, and `ru`.
- The common screen pattern is a local helper:

```python
import safari_writer.locale_info as _locale_info

def _(s: str) -> str:
    return _locale_info.get_translation().gettext(s)
```

- Many `safari_writer` screens already follow that pattern.

## Read these files first

- `safari_writer/locale_info.py` — runtime locale detection, gettext lookup, `.po` fallback, and date/time formatting
- `safari_writer/locales/fr/LC_MESSAGES/safari_writer.po` — good example catalog shape and header format
- `scripts/compile_mo.py` — how `.po` files are turned into `.mo`
- `Makefile` — `make locale` target
- `tests/test_writer/test_locale_info.py` — translation lookup expectations and `.po` fallback tests
- `tests/test_writer/test_i18n_integration.py` — broader i18n integration coverage
- `spec/16_internationalization.md` — intended architecture and release expectations
- `spec/16_internationalization_TODO.md` — known remaining gaps

## What is already true in this repo

1. The repo does **not** have a separate i18n framework per module.
1. The repo does **not** currently use a generated `.pot` workflow in day-to-day code.
1. The repo **does** already ship real `.po` catalogs under `safari_writer/locales`.
1. The repo **does** already resolve translations through `safari_writer.locale_info.get_translation()`.
1. The repo **does** already support `SAFARI_LOCALE` overrides for testing and manual verification.
1. The repo **does** already compile `.mo` files with a pure-Python script (`scripts/compile_mo.py`).

## Fast path: adding new translatable strings

1. Find the user-facing English string in code.
1. Reuse the existing `_()` helper pattern in that file.
1. Keep the English source string as the `msgid`.
1. Add or update that same `msgid` in every existing catalog:
   - `safari_writer/locales/en/LC_MESSAGES/safari_writer.po`
   - `safari_writer/locales/eo/LC_MESSAGES/safari_writer.po`
   - `safari_writer/locales/es/LC_MESSAGES/safari_writer.po`
   - `safari_writer/locales/fr/LC_MESSAGES/safari_writer.po`
   - `safari_writer/locales/is/LC_MESSAGES/safari_writer.po`
   - `safari_writer/locales/ru/LC_MESSAGES/safari_writer.po`
1. Run `make locale`.
1. Run the i18n tests.

Do not only update one language and call it done for a release pass unless the user explicitly asks for partial coverage.

## Release-pass audit order

### 1. Confirm runtime assumptions

- `safari_writer/locale_info.py`
- `safari_writer/__init__.py`

Check: current supported locale override behavior, current supported languages, whether any new runtime helper behavior changed catalog expectations.

### 2. Audit primary Writer screens first

These are the highest-signal places for release string churn:

- `safari_writer/screens/main_menu.py`
- `safari_writer/screens/editor.py`
- `safari_writer/screens/proofreader.py`
- `safari_writer/screens/global_format.py`
- `safari_writer/screens/mail_merge.py`
- `safari_writer/screens/backup_screen.py`
- `safari_writer/app.py`

Look for:

- newly added English literals not wrapped in `_()`
- status messages, prompts, confirmation text
- help text, menu labels, headings and banners
- string formatting placeholders that must stay intact, e.g. `{lang}` or `{needle!r}`

## String-handling rules

- Keep English hotkey letters stable unless the task explicitly changes key bindings. Translated labels do not imply translated hotkeys.
- Preserve placeholder names and formatting syntax exactly.
- Preserve punctuation and surrounding whitespace where it affects layout.
- Do not translate internal identifiers, file extensions, or command names unless the existing catalog already does so.
- Prefer updating existing `msgid` entries in place over creating near-duplicate strings.

## Catalog editing rules

- Keep the existing header style.
- Keep entries sorted and grouped consistently with the surrounding file style.
- If a string is intentionally untranslated in `en`, keep `msgstr` equal to `msgid`.
- If `.mo` files are stale, regenerate them with `make locale`; do not hand-edit `.mo` binaries.

## Search strategy

```text
grep -rn "def _(s" safari_writer/
grep -rn "get_translation().gettext" safari_writer/
grep -rn "msgid" safari_writer/locales/fr/LC_MESSAGES/safari_writer.po
```

## Validation

1. Run `make locale`
1. Run: `uv run pytest tests/test_writer/test_locale_info.py tests/test_writer/test_i18n_integration.py`
1. Manually spot-check with `SAFARI_LOCALE` if needed:

```bash
SAFARI_LOCALE=fr uv run --no-sync python -m safari_writer
SAFARI_LOCALE=eo uv run --no-sync python -m safari_writer
```

## Known gaps to remember

- Config-file locale override is still not implemented (`spec/16_internationalization_TODO.md`).
- `ngettext` plural support is still not wired into runtime helpers.
- CLI help/output localization is still incomplete.

Do not waste time re-discovering these during a release pass. Either work on them directly or leave them alone if out of scope.
