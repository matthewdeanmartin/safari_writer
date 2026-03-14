# TODO_BASE

This document compares the current `safari_base` implementation with the Safari Base spec in `spec\12_safari_base.md` and the screen sketches in `spec\12_b_safari_base_screens.md`.

## Current state

Right now `safari_base` is an early shell, not a full dBASE-style environment. It can:

- launch a Textual app and open an SQLite database
- bootstrap a single `ADDRESS` table in a new database
- show a browse-style table view, a table list, a structure view, startup help, and a simple append form
- switch tables with `USE <table>`
- accept a small set of prompt commands and function keys

It does **not** yet match the spec for screen layout, keybindings, command language coverage, work-area behavior, browse/edit interaction, delete semantics, or programming support.

## Priority 0: make the shell match the spec

- [x] Adopt a roomier shell target instead of a strict 80x25 recreation.
  - Keep the DOS-like structure and information density.
  - Use more of a modern terminal so browse and form screens have elbow room.
  - Treat the 80x25 spec as the historical reference, not a hard size limit.
- [x] Replace the current multi-row prompt box / extra help bars with the spec layout.
  - The spec has a single active dot prompt line and one high-contrast status bar.
  - Completed in the current shell refresh: the extra `button-bar` and `help-bar` are gone.
- [ ] Redesign the status area so it shows the real pieces the spec requires:
  - current drive / database / table
  - active work area (`[A]` through `[J]`)
  - record pointer and total count
  - status toggles like `Num`, `Caps`, `Ins`, delete mark
  - Partially done: the shell now shows database, table, work area `A`, record position, current field focus, and `Caps` / `Ins`.
  - Still open: true multi-area state, delete-mark state, and future `Num` / deleted indicators tied to real backend behavior.
- [x] Make the scoreboard reflect actual modal state instead of placeholder text.
  - It should show meaningful insert/delete/caps indicators tied to real behavior.
- [x] Make the browse screen look and behave like a dBASE browse grid rather than a read-only text dump.
  - Fixed-width columns
  - stable cursor position
  - active cell / row highlighting
  - room for more historically accurate headers and record markers

## Priority 0: implement real keyboard behavior

- [x] Replace the temporary function-key mapping with the spec's modern mapping.
  - `F1` help
  - `F10` or `Alt` for ASSIST
  - `Esc` cancel / abandon changes
  - `Ctrl+S` and/or `Ctrl+W` save-and-exit in edit screens
  - `Ctrl+D` as the modern equivalent of delete-mark toggle
  - `Home` / `End` for field start/end
- [x] Stop using development-only shortcuts that are not in the spec unless they are explicitly retained as aliases.
  - `Ctrl+Q` quit
  - `Ctrl+A` append
  - `Ctrl+L` caps toggle
  - These remain as legacy aliases for now rather than primary bindings.
- [x] Add proper browse navigation.
  - `Tab` and arrow keys move between fields
  - `Up` / `Down` move the record pointer
  - `PgUp` / `PgDn` move by visible page
  - horizontal movement works across columns, not just the prompt
- [ ] Add proper edit / append navigation.
  - `Tab`, `Shift+Tab`, arrows, `Home`, `End`
  - save / cancel behavior consistent with the spec
  - clear distinction between moving within a field and moving between fields
  - Partially done: append now supports `Tab`, `Shift+Tab`, arrows, `Home`, `End`, and `Ctrl+S` / `Ctrl+W`.
- [x] Decide how to expose `Alt` reliably in modern terminals and make the ASSIST menu reachable without relying on unsupported key combos.
  - `F10` is the reliable primary ASSIST binding.
  - `Alt` remains a best-effort alias where the terminal reports it cleanly.

## Priority 0: implement the missing data model

- [ ] Add the 10-work-area model described in the spec.
  - Areas `A-J`
  - each area owns its own open table
  - each area tracks its own record pointer
  - switching work areas must preserve per-area state
- [ ] Add dBASE-style soft delete support via a hidden `_d_deleted` column on every managed table.
  - `DELETE` marks
  - `RECALL` unmarks
  - `PACK` permanently removes marked rows and vacuums
  - `SET DELETED ON/OFF` controls visibility
- [ ] Expand the schema model beyond the hard-coded address-book table.
  - current bootstrap creates only text fields
  - spec requires Character, Numeric, Logical, Date, and Memo support
  - field width / decimals need to be tracked as metadata, not guessed from `DEFAULT_ADDRESS_SCHEMA`
- [ ] Add real record-pointer semantics instead of treating browse offset alone as the current position.
- [ ] Add database/session state for environment settings such as:
  - default path
  - exact comparison mode
  - deleted visibility
  - intensity mode

## Priority 0: build a real command interpreter

- [ ] Replace the current `if/elif` command switch with a parser / dispatcher that matches the spec.
- [ ] Support case-insensitive command parsing with four-character abbreviations.
  - `BROWSE` -> `BROW`
  - `REPLACE` -> `REPL`
  - same rule should apply consistently across supported commands
- [ ] Implement the core data commands from the spec:
  - `USE <table>`
  - `APPEND`
  - `EDIT [RECNO]`
  - `BROWSE`
  - `LIST`
  - `DISPLAY`
  - `REPLACE <field> WITH <expr> [FOR <cond>]`
  - `DELETE`
  - `RECALL`
  - `PACK`
- [ ] Implement command scopes and filters.
  - `FIELDS <list>`
  - `FOR <cond>`
  - record / paging behavior for `LIST` vs `DISPLAY`
- [ ] Add proper command errors and feedback instead of placeholder "not implemented yet" messages.
- [ ] Make dot-prompt input behave like a real command line rather than a passive text buffer.
  - cursor movement
  - editing inside the prompt
  - command history
  - better feedback for parse / runtime failures

## Priority 1: turn browse into a real interactive mode

- [ ] Support in-grid editing with updates committed when the cursor leaves the record, per spec.
- [ ] Track both current row and current field in browse mode.
- [ ] Support horizontal scrolling when the table is wider than the viewport.
- [ ] Show delete-mark state directly in the browse display.
- [ ] Respect `SET DELETED` when listing or browsing rows.
- [ ] Add page-sized movement and maintain cursor visibility cleanly as the record pointer moves.
- [ ] Ensure browse works with arbitrary tables, not only the default address schema.

## Priority 1: implement real EDIT and APPEND screens

- [ ] Replace the current plain-text append form with a proper full-screen form layout.
- [ ] Implement `EDIT [RECNO]` against existing rows.
- [ ] Support both default vertical forms and future formatted forms (`SET FORMAT TO <file>`).
- [ ] Add field typing, validation, and display formatting.
  - numeric width / decimals
  - logical `.T.` / `.F.`
  - date storage as `YYYYMMDD` with UI display as `MM/DD/YY`
  - memo editing workflow
- [ ] Separate append, edit, save, cancel, and dirty-state handling cleanly.
- [ ] Make save/cancel semantics match the keyboard spec rather than using only `F2` / `F3`.

## Priority 1: implement CREATE / MODIFY STRUCTURE

- [ ] Replace the current read-only structure view with an actual structure editor.
- [ ] Support:
  - field name (max 10 chars)
  - type (`C`, `N`, `L`, `D`, `M`)
  - width
  - decimals
- [ ] Add insert/delete/reorder field operations where appropriate.
- [ ] Define how schema changes are applied safely to SQLite tables.
- [ ] Preserve dBASE constraints while mapping to SQLite types underneath.

## Priority 1: implement ASSIST and menu-driven workflows

- [ ] Build an ASSIST menu that can be opened from `F10` / `Alt`.
- [ ] Add menu flows for the common tasks the spec and screen sketches imply:
  - open / choose table
  - browse records
  - append / edit / delete / recall
  - structure work
  - query / report entry points
- [ ] Make the menu system feel like a DOS pull-down workflow, not a generic Textual popup.

## Priority 1: support the `SET` environment commands

- [ ] Implement `SET DEFAULT TO <path>`.
- [ ] Implement `SET EXACT ON/OFF`.
- [ ] Implement `SET DELETED ON/OFF`.
- [ ] Implement `SET INTENSITY ON/OFF`.
- [ ] Surface those settings in the UI where appropriate and ensure they affect command execution.

## Priority 2: programming-language support

- [ ] Add `.prg` execution via `DO <filename>`.
- [ ] Implement control flow:
  - `IF ... ELSE ... ENDIF`
  - `DO WHILE ... ENDDO`
  - `DO CASE ... CASE ... OTHERWISE ... ENDCASE`
- [ ] Add PUBLIC / PRIVATE variable scoping.
- [ ] Implement `@ row,col SAY`
- [ ] Implement `@ row,col GET`
- [ ] Implement `READ` as an input-buffer activation step
- [ ] Decide how script execution interacts with open work areas, prompt state, and full-screen modes.

## Priority 2: command output and reporting behavior

- [ ] Implement `LIST` as scrolling output.
- [ ] Implement `DISPLAY` as paged output with pauses every 20 records.
- [ ] Add display formatting for selected fields and filtered scopes.
- [ ] Design a workspace output model that can show command results without breaking the 25-row shell illusion.

## Priority 2: architecture cleanup

- [ ] Split the monolithic screen logic into clearer layers:
  - shell / layout widgets
  - command interpreter
  - browse controller
  - form controller
  - table / record services
- [ ] Introduce a table metadata layer instead of deriving behavior from `DEFAULT_ADDRESS_SCHEMA` alone.
- [ ] Remove or gate the persistent `debug.log` file behavior if it is only for development.
- [ ] Define a safer abstraction for quoting identifiers, schema migration, and row updates.
- [ ] Add a central state model for current mode, work areas, environment settings, and prompt history.

## Priority 2: tests we will need

- [ ] Parser tests for abbreviations, case-insensitivity, and command syntax.
- [ ] Database tests for soft delete, recall, pack, and multi-work-area behavior.
- [ ] UI tests for:
  - 80x25 shell layout
  - status-bar segments
  - browse navigation
  - append/edit save and cancel flows
  - ASSIST menu navigation
- [ ] Integration tests for `USE`, `LIST`, `DISPLAY`, `REPLACE`, `DELETE`, `RECALL`, and `PACK`.
- [ ] Script execution tests for `DO`, control flow, variables, and `READ`.

## Suggested implementation order

1. layout stuff
1. Add work areas, `_d_deleted`, and environment settings.
1. Build the real command parser / dispatcher.
1. Upgrade browse into a true interactive grid.
1. Implement full edit / append / structure screens.
1. Add ASSIST workflows.
1. Add `SET` commands and command-output modes.
1. Add `.prg` / `READ` language support.

## Bottom line

Safari Base already has a promising bootstrap: app launch, SQLite session creation, a visible shell, table switching, and a simple append path. The big remaining job is to turn that prototype into a spec-faithful dBASE environment by fixing the shell layout, replacing placeholder commands with a real interpreter, adding work areas and delete semantics, and building proper browse/edit/assist/programming workflows.
