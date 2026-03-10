# Safari Writer v2 Notes

This document records Safari Writer behavior that exists in the implementation but is not described, or is only partially described, in `spec/01_safari_writer.md`.

## Main menu has grown beyond the original spec

The current main menu includes several writer-facing actions that are not in the original menu description:

- `?` Doctor / diagnostics
- `K` Backup & Restore
- `A` Save As...
- `X` Style Switcher
- `T` Try Demo Mode
- integrations opened from the Writer hub: Safari DOS, Safari Base, Safari Chat, Safari Fed, Safari REPL, Safari Reader

Implementation references:

- `safari_writer/screens/main_menu.py`
- `safari_writer/screens/doctor.py`
- `safari_writer/screens/backup_screen.py`
- `safari_writer/screens/style_switcher.py`
- `safari_writer/document_io.py`

## Block marking has evolved into a modern selection model

The original spec describes a visible "Beginning Marked" style anchor. The implementation uses a modern selection anchor and selection-aware editing flow instead of reproducing the legacy wording and exact UI literally.

Implementation references:

- `safari_writer/state.py` (`selection_anchor`)
- `safari_writer/screens/editor.py`

## The product hub is now broader than "writer only"

The implementation treats Safari Writer as a launcher shell for adjacent tools, not just a single-purpose word processor front end. That broader hub behavior should be reflected in future spec updates.

Implementation references:

- `safari_writer/screens/main_menu.py`
- `safari_writer/app.py`
