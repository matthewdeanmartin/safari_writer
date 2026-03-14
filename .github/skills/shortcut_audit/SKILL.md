---
name: shortcut_audit
description: Audit keyboard shortcuts for consistency, Textual conflicts, missing bindings, and documentation drift across app modules.
---

# Shortcut Audit

Use this skill near release time to verify that shortcuts:

- exist where the UX implies they should exist,
- do not conflict with Textual defaults or terminal aliases,
- are consistent between code, in-app help, and docs,
- are documented in the right help and Markdown files.

This skill is optimized to minimize repo re-reading. Start with the narrow file set below before searching more broadly.

## What to check

1. **Missing shortcuts**
   - A help screen, menu bar, command bar, spec, or docs page mentions a shortcut that is not actually implemented.
   - A screen has important actions with no accessible binding or `on_key()` path.

2. **Inconsistent shortcuts**
   - Code, in-app help, and docs disagree on key names or behavior.
   - One module documents a shortcut differently from another place describing the same feature.

3. **Textual and terminal conflicts**
   - Rebindings collide with common Textual defaults or terminal aliases.
   - Especially watch for `Ctrl+I` = `Tab`, `Ctrl+J` = `Enter`, and `Ctrl+M` = `Enter` on many terminals.

## Read these files first

### Safari Writer

- `safari_writer\screens\editor.py`
  - Primary Writer shortcut source.
  - Read `HELP_CONTENT`, `HELP_CONTENT_PLAIN`, `BINDINGS`, and `on_key()`.
  - This is the main place to compare implemented keys against documented Writer behavior.
- `safari_writer\screens\main_menu.py`
  - Main menu bindings and visible menu shortcuts.
- `safari_writer\screens\mail_merge.py`
  - Has its own `HELP_CONTENT` and `BINDINGS`.
- `safari_writer\screens\global_format.py`
  - Screen-specific bindings.
- `safari_writer\screens\proofreader.py`
  - Screen-specific bindings.
- `safari_writer\screens\backup_screen.py`
  - Screen-specific bindings.
- `safari_writer\screens\style_switcher.py`
  - Screen-specific bindings.

### Safari Chat

- `safari_chat\screens.py`
  - Primary UI shortcut source for Safari Chat.
  - Check `SafariChatMainScreen.BINDINGS`.
  - Check the visible shortcut text in `chat-menu-bar`, `chat-command-bar`, and `CHAT_HELP_CONTENT`.
- `safari_chat\app.py`
  - Shows that Safari Chat loads bundled help from `safari_chat\default_help.md`.
- `safari_chat\default_help.md`
  - Bundled help knowledge base used by the app.
  - Search this file for `shortcut`, `keyboard`, `key`, `command`, `Ctrl`, `Alt`, `F1`, and menu names.
  - If Safari Chat behavior or help UI changes, this file may also need updates.

### Safari DOS

- `safari_dos\screens.py`
  - Primary DOS shortcut source.
  - Check `BINDINGS`, browser `on_key()` logic, and `DOS_HELP_CONTENT`.

### Safari Fed

- `safari_fed\screens.py`
  - Primary Fed shortcut source.
  - Check `FED_HELP_CONTENT` and the main screen `on_key()` logic together.
  - Fed is especially important because it relies more on `on_key()` than `BINDINGS`.

### Safari Reader

- `safari_reader\screens.py`
  - Primary Reader shortcut source.
  - Multiple screens define `BINDINGS`; audit the specific screen whose help or docs changed.

### Safari REPL

- `safari_repl\screens.py`
  - Check main menu and editor `BINDINGS`.

### Safari Slides

- `safari_slides\screens.py`
  - Check presentation navigation `BINDINGS` and any supplemental `on_key()` handling.

### Safari View

- `safari_view\ui_terminal\textual_app.py`
  - Primary View shortcut source.
  - Check image-viewer `BINDINGS`.

### Other modules to spot-check

- `safari_base\`
  - Search only if the user changed Base UI behavior. It is not a frequent shortcut hotspot.
- `safari_basic\`
  - Search only if work touched the BASIC UI or launcher flow.

## Docs and specs that mention shortcuts

These files commonly drift away from the implementation and should be synchronized with code:

- `docs\usage\commands.md`
  - User-facing Writer keyboard command reference.
- `docs\modules\safari_fed.md`
  - Fed docs can mention key-driven workflow.
- `docs\modules\safari_dos.md`
  - DOS docs may mention keyboard navigation.
- `spec\02_keyboard.md`
  - Primary Writer keyboard mapping spec.
- `spec\09_safari_dos.md`
  - DOS design/spec references for navigation and commands.
- `spec\11_ai_chat.md`
  - Chat design notes; may mention help and command surfaces.
- `spec\14_safari_fed.md`
  - Fed shortcut expectations.
- `spec\15_safari_basic.md`
  - BASIC or REPL-adjacent references if relevant.
- `spec\17_reader.md`
  - Reader keyboard/navigation expectations.
- `spec\50_safari_view.md`
  - Viewer shortcut expectations.

When editing docs broadly, search `docs\**\*.md` and `spec\*.md` for:

- `shortcut`
- `shortcuts`
- `keyboard`
- `keybinding`
- `keybindings`
- `hotkey`
- `command`
- `Ctrl+`
- `Alt+`
- `F1`
- `Escape`

## Textual conflict checklist

Before proposing or validating a shortcut, compare it against these conflict surfaces:

- `Ctrl+Q` — app quit
- `Ctrl+C` — copy / interrupt semantics
- `Ctrl+P` — command palette
- `Tab` / `Shift+Tab` — focus traversal
- `Ctrl+I` — often same as `Tab`
- `Ctrl+J` — often same as `Enter`
- `Ctrl+M` — often same as `Enter`

Many screens already include a header comment describing these hazards. If you see a shortcut that depends on one of these aliases, check whether the repo already documents it as fragile or unreachable on some terminals.

## Minimal audit workflow

1. Read the module's primary shortcut file from the list above.
2. Compare:
   - `BINDINGS`
   - `on_key()`
   - in-file help constants or menu/footer text
3. Read the matching docs/spec files that describe the same module.
4. Report:
   - missing shortcuts,
   - mismatched labels,
   - duplicate or conflicting bindings,
   - docs/help drift,
   - terminal/Textual collision risks.

## Fast search commands

Use targeted search instead of reading whole files:

```text
rg -n "BINDINGS\\s*=\\s*\\[|on_key\\(|HELP_CONTENT|CHAT_HELP_CONTENT|FED_HELP_CONTENT|DOS_HELP_CONTENT" safari_*
rg -n "shortcut|shortcuts|keyboard|keybinding|keybindings|hotkey|Ctrl\\+|Alt\\+|F1|Escape" docs spec safari_chat\\default_help.md
rg -n "Binding\\(" safari_*
rg -n "ctrl\\+|alt\\+|f[1-9]|pageup|pagedown|escape|tab|shift\\+tab" safari_*
```

## Expected output

Return a compact report with sections:

- `Implemented`
- `Missing`
- `Conflicts / risky bindings`
- `Docs to update`
- `Help text to update`

Prefer file paths and exact symbol names over long prose so the next edit pass can be surgical.
