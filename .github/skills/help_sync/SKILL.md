______________________________________________________________________

## name: help_sync description: Systematically sync docs, module help screens, README, and Safari Chat default help against current code.

# Help Sync

Use this skill when a feature, command, shortcut, screen, workflow, or whole module changed and you need to make sure the documentation changed with it.

This skill is for **systematic documentation synchronization**, not just writing nice prose. Your job is to compare each help surface against current code and visible UI text so new behavior does not ship undocumented.

## The short version

- Treat **code and visible in-app text** as ground truth unless the task explicitly says the docs define the intended behavior.
- Audit **one help area at a time**. Do not bounce between unrelated docs and screens.
- For each area, compare:
  - what the code exposes,
  - what the user sees on screen,
  - what the docs say,
  - what `mkdocs.yml` exposes in site navigation,
  - what `safari_chat\default_help.md` teaches.
- If a module exists in the app family but has no matching docs page, call that out and add one when the task scope requires user-facing documentation completeness.
- Do not stop after updating one file. New features often require updates in multiple surfaces.

## Ground truth hierarchy

Prefer this order when deciding what is real:

1. Actual code paths and bindings.
1. On-screen titles, menus, help modals, command bars, and CLI parsers.
1. Root `README.md` and `docs\` pages.
1. `safari_chat\default_help.md`.

Reason: `default_help.md` is a knowledge document for Safari Chat. It should reflect reality, but it is not the source of truth.

## Read these files first

Read these before broad searching:

- `README.md`
  - Main product/module overview that should mention user-facing modules and capabilities.
- `docs\README.md`
  - Docs landing summary for the suite.
- `docs\index.md`
  - User-facing intro and suite overview.
- `mkdocs.yml`
  - Confirms which docs pages are actually exposed in the published site and which existing files are omitted from nav.
- `docs\modules\*.md`
  - Per-module documentation pages that commonly drift or go missing.
- `safari_chat\default_help.md`
  - Bundled help knowledge base used by Safari Chat.
- `safari_chat\app.py`
  - Confirms bundled default help wiring.
- `safari_chat\screens.py`
  - Chat help modal, command list, visible shortcut/help text.

## Primary screen/title sources by module

Use these files as the first stop for module names, visible headings, and user-facing help text:

### Safari Writer

- `safari_writer\screens\main_menu.py`
  - Main suite hub and top-level module menu labels.
  - Read `_COL1_DEFS`, `_COL2_DEFS`, `_COL3_DEFS`, `BINDINGS`, and the `#title` `Static`.
- `safari_writer\screens\editor.py`
  - Primary Writer help content and editor commands.
  - Read `HELP_CONTENT`, `HELP_CONTENT_PLAIN`, and `BINDINGS`.
- `safari_writer\screens\mail_merge.py`
  - Has `HELP_CONTENT` and screen bindings.
- `safari_writer\screens\proofreader.py`
- `safari_writer\screens\global_format.py`
- `safari_writer\screens\backup_screen.py`
- `safari_writer\screens\style_switcher.py`

### Safari Chat

- `safari_chat\app.py`
  - `TITLE = "Safari Chat"` and bundled help loading.
- `safari_chat\screens.py`
  - `CHAT_HELP_CONTENT`, slash commands, visible modal titles, command bar text.
- `safari_chat\default_help.md`
  - Must stay aligned with actual module names, workflows, and feature descriptions.

### Safari DOS

- `safari_dos\screens.py`
  - Main menu/help content and visible headings.
  - Read `DOS_HELP_CONTENT`, `SafariDosHelpScreen`, and menu/browser titles.
- `safari_dos\main.py`
  - CLI commands and parser help text.

### Safari Fed

- `safari_fed\screens.py`
  - `FED_HELP_CONTENT`, help title, folder/action labels, and visible main-screen chrome.
- `safari_fed\main.py`
  - CLI parser help.

### Safari REPL

- `safari_repl\screens.py`
  - Main menu title, REPL title, and bindings.

### Safari Reader

- `safari_reader\screens.py`
  - Main menu title/banner, help/menu labels, library/catalog wording.

### Safari Slides

- `safari_slides\screens.py`
  - Header/footer wording and navigation hints.

### Safari View

- `safari_view\ui_terminal\textual_app.py`
  - App header/footer behavior, `BINDINGS`, and `self.app.title`.

### Safari Basic / other modules

- Search `safari_basic\`, `safari_base\`, `safari_asm\` when the feature touches them.
- If a module is user-facing in code or README but has no module page under `docs\modules\`, treat that as a docs completeness gap.

## What to keep synchronized

For each feature or module you touch, check all relevant surfaces:

1. **Root product docs**

   - `README.md`
   - `docs\README.md`
   - `docs\index.md`
   - `mkdocs.yml`

1. **Module docs**

   - `docs\modules\*.md`
   - Add missing module pages when appropriate.

1. **Task/topic docs**

   - `docs\usage\*.md`
   - `docs\overview\*.md`
   - `docs\reference\*.md`
   - Make sure new or existing pages are linked from `mkdocs.yml` nav if they are user-facing.

1. **In-app help / visible H1-style screen titles**

   - Help constants like `HELP_CONTENT`, `CHAT_HELP_CONTENT`, `DOS_HELP_CONTENT`, `FED_HELP_CONTENT`
   - Title widgets like `yield Static("*** SAFARI WRITER ***", id="title")`
   - Modal titles like `=== SAFARI CHAT — KEY COMMANDS ===`
   - App/window titles like `TITLE = "Safari Chat"` or `self.app.title = ...`

1. **Safari Chat knowledge base**

   - `safari_chat\default_help.md`
   - Update this when user-facing workflows, names, commands, modules, or feature summaries changed.

## Systematic audit workflow

Do **not** do a repo-wide prose rewrite. Work through one help area at a time.

### Phase 1: pick one area

Choose exactly one area before editing:

- one module,
- one screen/workflow,
- one command family,
- or one newly added feature.

Examples:

- Safari DOS file browser behavior
- Safari Fed compose flow
- Safari Chat slash commands
- Writer mail merge help
- A new module added to the main menu

### Phase 2: establish ground truth for that area

Read the specific code first:

- bindings and actions,
- visible titles and labels,
- help constants,
- parser help / CLI descriptions,
- main-menu entries and launch points.

Write down, mentally or in notes:

- exact module name,
- exact screen title text,
- exact commands/shortcuts,
- exact workflow steps,
- exact limitations or prerequisites.

### Phase 3: compare every dependent help surface

For the same area, compare in this order:

1. matching `docs\modules\...` page
1. matching `docs\usage\...` / `docs\overview\...` / `docs\reference\...` pages
1. `mkdocs.yml` navigation and omitted-file warnings
1. root `README.md`
1. `docs\README.md` and `docs\index.md`
1. `safari_chat\default_help.md`

If the area has a dedicated in-app help modal, compare that too.

### Phase 4: update only the surfaces affected by that area

Make the docs say what the code does **now**:

- module names must match current UI wording,
- command names must match parser help,
- shortcuts must match bindings,
- workflows must match actual screens,
- capability lists must include newly shipped features,
- removed behavior must be deleted from docs/help.

### Phase 5: move to the next area

After one area is fully synchronized, then continue to the next.

This prevents partial sync where one changed module updates `README.md` but not its module doc or Chat help.

## Required compare points

When you audit a help area, explicitly check these questions:

### Names and headings

- Does the module name in docs match the on-screen title?
- Do H1/H2 headings match the current product terminology?
- Does the main menu label match the docs wording?

### Commands and shortcuts

- Do docs list commands that still exist?
- Are any new commands, flags, or shortcuts missing?
- Do help screens and Markdown agree on key names?

### Workflow steps

- Does the documented path through menus/screens match current navigation?
- Are prerequisites documented, for example configuration or required files?
- Does a handoff to another module still work the way docs describe?

### Coverage

- Is there a module page for each user-facing module?
- Is a new feature only described in code but nowhere in docs?
- Is there a user-facing docs file under `docs\` that is missing from `mkdocs.yml` nav?
- Does `mkdocs.yml` still point at files that were removed, renamed, or never added?
- Is `safari_chat\default_help.md` missing the new topic entirely?

## Search strategy

Start narrow. Only broaden when the local area is complete.

Useful searches:

```text
rg -n "HELP_CONTENT|CHAT_HELP_CONTENT|DOS_HELP_CONTENT|FED_HELP_CONTENT|BINDINGS\\s*=\\s*\\[" safari_*
rg -n "TITLE = |self\\.app\\.title|yield Static\\(|Header\\(" safari_*
rg -n "^# |^## " README.md docs safari_chat\\default_help.md
rg -n "Safari Writer|Safari DOS|Safari Chat|Safari Fed|Safari REPL|Safari Reader|Safari Slides|Safari View|Safari Basic" README.md docs safari_chat\\default_help.md
```

## Common failure modes

Do not make these mistakes:

- Updating `README.md` but forgetting `docs\index.md`.
- Updating docs files but forgetting to expose them in `mkdocs.yml`.
- Updating module docs but forgetting `safari_chat\default_help.md`.
- Updating prose without checking the actual on-screen title or help modal.
- Treating an old docs page as ground truth when the code has moved on.
- Editing many help areas at once and losing track of what was actually verified.

## Validation

After doc/help updates:

1. Re-read the edited files and the corresponding code together.
1. Confirm that every changed feature/module is represented in:
   - current UI/help text,
   - user docs,
   - root README where appropriate,
   - Safari Chat default help where appropriate.
1. If behavior changed, run the relevant existing tests for that module or help surface.

Helpful examples already in this repo:

- `tests\test_chat\test_chat_app.py`
  - Verifies Safari Chat help content details.
- `tests\test_dos\test_safari_dos.py`
  - Verifies Safari DOS help content details.
- `tests\test_fed\test_safari_fed.py`
  - Verifies some Writer help content expectations.

## Expected output

When using this skill, produce a compact sync report with:

- `Area audited`
- `Ground truth checked`
- `Docs updated`
- `Help text updated`
- `Missing docs discovered`
- `Validation run`

Prefer exact file paths and exact headings/strings over vague summaries.
