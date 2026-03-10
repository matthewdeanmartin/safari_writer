# Internationalization TODO

These items are described in `spec/16_internationalization.md` but are still missing or only partially implemented.

## 1. Config-file locale override is not implemented

Spec intent:

- support `~/.safari_writer/config.toml`
- priority should be `SAFARI_LOCALE > config file > OS detection > fallback`

Current implementation:

- locale resolution checks `SAFARI_LOCALE`, then the OS, then `en_US`
- there is no config-file locale read path in `locale_info.py`

Implementation reference:

- `safari_writer/locale_info.py`

## 2. `ngettext` plural support is not wired into runtime helpers

Spec intent:

- expose/use `ngettext` for plural-aware UI strings

Current implementation:

- translation catalogs include plural-form metadata
- runtime helper wiring is centered on `gettext`
- there is no repository use of `ngettext`

Implementation references:

- `safari_writer/locale_info.py`
- `safari_writer/locales/*/LC_MESSAGES/safari_writer.po`

## 3. CLI help/output localization is still incomplete

Spec intent:

- CLI help text and CLI output messages should be localizable

Current implementation:

- `main.py` defines argparse help text and status strings directly in English
- the CLI module does not use the screen-level translation helper pattern

Implementation reference:

- `safari_writer/main.py`
