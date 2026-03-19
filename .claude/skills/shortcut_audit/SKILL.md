---
name: shortcut_audit
description: Audit keyboard shortcuts for consistency, Textual conflicts, missing bindings, and documentation drift in safari_writer.
---

# Shortcut Audit

Use this skill near release time or after adding new bindings to verify that shortcuts:

- exist where the UX implies they should exist,
- do not conflict with Textual defaults or terminal aliases,
- are consistent between code, in-app help, and docs,
- are documented in the right help constants and spec files.

This skill is optimized to minimize repo re-reading. Start with the narrow file set below before searching more broadly.

## What to check

1. **Missing shortcuts** — a help screen or spec mentions a shortcut that is not actually implemented; a screen has important actions with no accessible binding or `on_key()` path.
1. **Inconsistent shortcuts** — code, in-app help, and spec disagree on key names or behavior.
1. **Textual and terminal conflicts** — rebindings collide with Textual defaults or terminal aliases.

## Read these files first

- `safari_writer/screens/editor.py` — primary shortcut source: `HELP_CONTENT`, `HELP_CONTENT_PLAIN`, `BINDINGS`, `on_key()`
- `safari_writer/screens/main_menu.py` — main menu bindings and visible menu shortcuts
- `safari_writer/screens/mail_merge.py` — `HELP_CONTENT` and `BINDINGS`
- `safari_writer/screens/global_format.py`
- `safari_writer/screens/proofreader.py`
- `safari_writer/screens/backup_screen.py`
- `safari_writer/screens/style_switcher.py`

## Specs that mention shortcuts

- `spec/02_keyboard.md` — primary Writer keyboard mapping spec
- `spec/07_global_format.md`
- `spec/08_file_operations.md`
- `spec/09_print.md`
- `spec/10_proofreader.md`
- `spec/11_mail_merge.md`

When editing docs broadly, search `spec/*.md` for: `shortcut`, `keyboard`, `keybinding`, `hotkey`, `Ctrl+`, `Alt+`, `F1`, `Escape`.

## Textual conflict checklist

Before proposing or validating a shortcut, check these:

- `Ctrl+Q` — app quit
- `Ctrl+C` — copy / interrupt semantics
- `Ctrl+P` — command palette
- `Tab` / `Shift+Tab` — focus traversal
- `Ctrl+I` — often same as `Tab`
- `Ctrl+J` — often same as `Enter`
- `Ctrl+M` — often same as `Enter`

Known conflict: `Shift+F3` is used for both case toggle and replace-occurrence — needs resolution.

## Minimal audit workflow

1. Read the module's primary shortcut file.
1. Compare: `BINDINGS`, `on_key()`, in-file help constants or menu/footer text.
1. Read the matching spec files for the same module.
1. Report: missing shortcuts, mismatched labels, duplicate/conflicting bindings, spec drift, terminal/Textual collision risks.

## Fast search commands

```text
grep -rn "BINDINGS\s*=\s*\[\|on_key\(\|HELP_CONTENT" safari_writer/
grep -rn "shortcut\|keyboard\|keybinding\|Ctrl+\|Alt+\|F1\|Escape" spec/
grep -rn "Binding(" safari_writer/
grep -rn "ctrl+\|alt+\|f[1-9]\|pageup\|pagedown\|escape\|shift+" safari_writer/
```

## Expected output

- `Implemented`
- `Missing`
- `Conflicts / risky bindings`
- `Spec drift to update`
- `Help text to update`
