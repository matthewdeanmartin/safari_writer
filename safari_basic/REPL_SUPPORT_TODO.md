# Safari Basic REPL Support TODO

This document tracks the remaining features from `REPL_EXPANSION.md` and other planned improvements for the Safari Basic REPL environment.

## 1. Core REPL Commands & Features
- [ ] **`EDIT <line>`**: Retrieve a stored line into the input buffer for modification.
- [ ] **`DELETE <start>[,<end>]`**: Delete a range of lines.
- [ ] **`MERGE "file"`**: Load lines from another file into the current program without clearing it.
- [ ] **Dirty State Tracking**: Show `[modified]` status and warn before `NEW`, `LOAD`, or `EXIT` if changes are unsaved.
- [ ] **`FILES` / `DIR`**: List files in the current directory.
- [ ] **`PWD` / `CD`**: Basic directory navigation within the REPL.

## 2. Advanced Editing
- [ ] **`FIND "text"`**: Search for string or keyword in the program source.
- [ ] **`REPLACE "old","new"`**: Global or range-based search and replace.
- [ ] **`EXPORT "file.txt"`**: Save program without line numbers for modern readability.
- [ ] **Syntax Highlighting**: Add optional ANSI color coding for `LIST` and immediate mode.

## 3. Debugging Tools
- [ ] **Breakpoints**: 
    - [ ] `BREAK <line>`: Set a breakpoint.
    - [ ] `BREAK CLEAR <line>`: Remove a breakpoint.
    - [ ] `BREAK LIST`: Show all active breakpoints.
- [ ] **Stepping**:
    - [ ] `STEP`: Execute exactly one statement/line.
    - [ ] `NEXT`: (In debugger context) step over or to next line.
- [ ] **`STACK`**: Display the current `GOSUB` call stack.
- [ ] **Enhanced `TRON`**:
    - [ ] Support `TRON VARS` to show variable changes during execution.

## 4. Usability & UI
- [x] **Command History** (up/down arrows in TUI)
- [ ] **Command History persistent**: Save REPL history to a file (e.g., `.safari_history`).
- [ ] **Tab Completion**:
    - [ ] Keywords (PRINT, GOTO, etc.)
    - [ ] Filenames
    - [ ] Line numbers (contextual)
- [ ] **Better Error Reporting**: 
    - [ ] Show the offending line with a pointer to the syntax error.
    - [ ] Provide more descriptive error messages (e.g., "EXPECTED ')' AT LINE 10").
- [x] **Status Line**: Optional single-line status bar at bottom of terminal showing filename, modified state, and last error.

## 5. Compatibility & Robustness
- [ ] **Classic vs. Enhanced Modes**: Toggle between strict 8-bit feel and modern helpfulness.
- [ ] **Autosave / Crash Recovery**: Periodically save a temporary version of the current program.
- [ ] **Atomic Saves**: Use temporary files and rename to prevent data loss during `SAVE`.

## 6. Documentation & Help
- [ ] **`HELP <topic>`**: Expand the help system to provide detailed syntax for every keyword and command.
- [ ] **Examples**: Add a set of demo `.bas` files to the repository.
