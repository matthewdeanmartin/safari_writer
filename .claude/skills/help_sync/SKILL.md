---
name: help_sync
description: Systematically sync in-app help screens, README, TODO, and spec files against current safari_writer code.
---

# Help Sync

Use this skill when a feature, command, shortcut, screen, or module changed and you need to make sure the documentation changed with it.

This skill is for **systematic documentation synchronization**. Your job is to compare each help surface against current code and visible UI text so new behavior does not ship undocumented.

## The short version

- Treat **code and visible in-app text** as ground truth unless the task explicitly says the docs define the intended behavior.
- Audit **one help area at a time**. Do not bounce between unrelated docs and screens.
- For each area, compare:
  - what the code exposes,
  - what the user sees on screen,
  - what the docs/spec say,
  - what `README.md` says.
- Do not stop after updating one file. New features often require updates in multiple surfaces.

## Ground truth hierarchy

1. Actual code paths and bindings.
1. On-screen titles, menus, help modals, command bars.
1. Root `README.md` and `TODO.md`.
1. Spec files in `spec/`.

## Read these files first

- `README.md` — main product overview
- `TODO.md` — 12-phase implementation plan; shows what is done vs. planned
- `spec/` — per-feature design specs; compare against what is actually implemented

## Primary screen/title sources

- `safari_writer/screens/main_menu.py` — main hub, top-level menu labels, `_COL1_DEFS`, `_COL2_DEFS`, `_COL3_DEFS`, `BINDINGS`, `#title` Static
- `safari_writer/screens/editor.py` — primary editor help: `HELP_CONTENT`, `HELP_CONTENT_PLAIN`, `BINDINGS`
- `safari_writer/screens/mail_merge.py` — `HELP_CONTENT` and screen bindings
- `safari_writer/screens/proofreader.py`
- `safari_writer/screens/global_format.py`
- `safari_writer/screens/backup_screen.py`
- `safari_writer/screens/style_switcher.py`
- `safari_writer/app.py` — app-level title and top-level wiring

## Safari Base Language Processor

- `safari_base/lang/` — standalone dBASE III+ interpreter
- `spec/18_safari_base_language.md` — language spec
- CLI: `python -m safari_base.lang repl` / `python -m safari_base.lang run script.prg`

## What to keep synchronized

For each feature or module you touch, check all relevant surfaces:

1. **Root docs** — `README.md`, `TODO.md`
1. **Spec files** — `spec/` — check if spec matches implementation or diverged
1. **In-app help** — `HELP_CONTENT` constants, title widgets, modal titles, footer text
1. **i18n catalogs** — `safari_writer/locales/*/LC_MESSAGES/safari_writer.po` — run `make locale` after any string changes

## Systematic audit workflow

### Phase 1: pick one area

Choose exactly one area before editing: one module, one screen/workflow, one command family, or one newly added feature.

### Phase 2: establish ground truth

Read the specific code first: bindings, actions, visible titles/labels, help constants, menu entries.

### Phase 3: compare every dependent help surface

For the same area, compare in this order:

1. in-app `HELP_CONTENT` / modal text
1. matching spec file in `spec/`
1. `README.md` and `TODO.md`

### Phase 4: update only the surfaces affected by that area

- Module names must match current UI wording.
- Shortcuts must match `BINDINGS` / `on_key()`.
- Removed behavior must be deleted from docs/help.

### Phase 5: move to the next area

## Required compare points

### Names and headings
- Does the module name in docs match the on-screen title?
- Does the main menu label match the docs wording?

### Commands and shortcuts
- Do docs list commands that still exist?
- Are any new commands, flags, or shortcuts missing?

### Coverage
- Is there a help constant for each screen?
- Is a new feature only described in code but nowhere in docs?
- Does a spec file describe behavior that was never implemented?

## Search strategy

```text
grep -rn "HELP_CONTENT\|BINDINGS\s*=\s*\[" safari_writer/
grep -rn "yield Static\(" safari_writer/
grep -rn "^# \|^## " README.md spec/ TODO.md
```

## Common failure modes

- Updating `README.md` but forgetting in-app `HELP_CONTENT`.
- Updating help text but forgetting `.po` catalog strings.
- Treating an old spec file as ground truth when the code has moved on.
- Editing many help areas at once and losing track of what was actually verified.

## Validation

1. Re-read the edited files and the corresponding code together.
1. If strings changed, run `make locale` then `make test`.

## Expected output

- `Area audited`
- `Ground truth checked`
- `Docs updated`
- `Help text updated`
- `Missing docs discovered`
- `Validation run`
