# Safari Basic REPL Support TODO

This document tracks the remaining features from `REPL_EXPANSION.md` and other planned improvements for the Safari Basic REPL environment.

## 1. Core REPL Commands & Features
- [x] **`EDIT <line>`**: Retrieve a stored line into the input buffer for modification.
- [x] **`DELETE <start>[,<end>]`**: Delete a range of lines.
- [x] **Dirty State Tracking**: Show `[modified]` status and warn before `NEW`, `LOAD`, or `EXIT` if changes are unsaved.
- [x] **`FILES` / `DIR`**: List files in the current directory (with optional glob pattern).
- [x] **`PWD` / `CD`**: Basic directory navigation within the REPL.

## 2. Advanced Editing
- [x] **`FIND "text"`**: Search for string or keyword in the program source (case-insensitive, with pointer).
- [x] **`REPLACE "old","new"`**: Global search and replace (case-insensitive, with undo support).

## 3. Debugging Tools
- [x] **Enhanced `TRON`**:
    - [x] Support `TRON VARS` to show variable changes during execution.

## 4. Usability & UI
- [x] **Command History** (up/down arrows in TUI)
- [x] **Command History persistent**: Save REPL history to a file (e.g., `.safari_history`).
- [x] **Tab Completion**:
    - [x] Keywords (PRINT, GOTO, etc.)
    - [x] Filenames
    - [x] Line numbers (contextual)
- [x] **Better Error Reporting**:
    - [x] Show the offending line with a pointer to the syntax error.
    - [x] Provide more descriptive error messages (e.g., "EXPECTED ')' AT LINE 10").
- [x] **Status Line**: Optional single-line status bar at bottom of terminal showing filename, modified state, and last error.

## 5. Compatibility & Robustness
- [x] **AUTOSAVE ON/ AUTOSAVE OFF**: Commands to enable Periodically save a temporary version of the current program, every 15 seconds.

## 6. Documentation & Help
- [x] **`HELP <topic>`**: Expand the help system to provide detailed syntax for every keyword and command.
- [x] **Examples**: Add a set of demo `.bas` files to the repository (`safari_basic/examples/`).
