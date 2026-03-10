# CLI Interface v2 Notes

This document records CLI behavior that exists in the implementation but is not captured by `spec/08_cli_interface.md`, plus places where the CLI surface has clearly evolved.

## The shorthand file-open form is implemented

The convenience form below works in the current parser:

```text
safari-writer draft.sfw
```

It normalizes to `tui edit --file draft.sfw`.

Implementation reference:

- `safari_writer/main.py` (`_normalize_argv`)

## The top-level CLI now includes `doctor`

The implementation exposes a top-level diagnostic command:

```text
safari-writer doctor
```

This is implemented but is not shown in the spec's command tree.

Implementation reference:

- `safari_writer/main.py`

## The `tui` branch has grown beyond the original tree

Additional direct-entry destinations now exist:

- `tui safari-dos`
- `tui safari-fed`
- `tui safari-repl`
- `tui safari-reader`

These reflect the current product shell behavior and should be documented as part of the real command surface.

Implementation references:

- `safari_writer/main.py`
- `safari_writer/cli_types.py`

## Splash control is now part of startup

The CLI supports `--no-splash` for TUI launches. This is implementation-level behavior not captured in the spec.

Implementation references:

- `safari_writer/main.py`
- `safari_writer/splash.py`
