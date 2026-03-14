This specification defines the functional requirements and architectural design for **Project Safari Base**, a modern, clean-room reimplementation of the dBASE III Plus environment. The goal is to provide a historically accurate User Interface (TUI) and command language compatibility while leveraging a modern SQLite backend.

______________________________________________________________________

# Project Safari Base: Technical Specification

## 1. System Overview

**Safari Base** is a character-mode database management system (DBMS) and programming language. It provides an interactive "Dot Prompt" environment, a menu-driven "Assistant," and a procedural programming language for building database applications.

### 1.1 Core Principles

- **Backend:** SQLite 3 is the exclusive data engine. Legacy `.dbf` file support is omitted to prioritize performance and reliability.
- **Interface:** A Terminal User Interface (TUI) built on the Python **Textual** framework.
- **Copyright Compliance:** The system implements functional syntax and logic found in public domain documentation and historical language handbooks. It avoids copying original source code or proprietary branding.

______________________________________________________________________

## 2. Data Architecture & SQLite Mapping

The system maps dBASE logical constructs to SQLite relational structures.

### 2.1 Work Areas

The system maintains 10 independent **Work Areas** (1-10, or A-J).

- Each area can host one open SQLite table.
- Each area maintains its own **Record Pointer** (an integer representing the current row index).
- **Internal Table Tracking:** Each table in the SQLite database includes a hidden column `_d_deleted` (Boolean) to support the dBASE "Soft Delete" logic.

### 2.2 Field Type Mapping

| dBASE Type | SQLite Type | Notes |
| --- | --- | --- |
| **Character** | `TEXT` | Fixed-width behavior enforced by the TUI layer. |
| **Numeric** | `REAL` / `INTEGER` | Supports precision and scale definitions. |
| **Logical** | `BOOLEAN` | Maps `.T.`/`.F.` to `1`/`0`. |
| **Date** | `TEXT` | Stored as `YYYYMMDD` for sorting; formatted as `MM/DD/YY` for UI. |
| **Memo** | `TEXT` | Unlimited length, replacing the separate `.dbt` file. |

______________________________________________________________________

## 3. The TUI Environment

The UI mimics the 25-row by 80-column layout of the 1980s, rendered in a modern terminal.

### 3.1 Screen Layout

1. **Header (Row 0):** The "Scoreboard." Displays status toggles like `Ins`, `Del`, and `Caps`.
1. **Main Workspace (Rows 1–21):** The scrollable output area for commands like `LIST` or `DISPLAY`.
1. **The Dot Prompt (Row 22):** An active command line starting with a single period (`.`).
1. **Status Bar (Row 24):** A high-contrast bar divided into segments:

- **Current Drive/File:** e.g., `C: CUSTOMER`
- **Work Area:** e.g., `[A]`
- **Record Count:** e.g., `Rec: 15/1000`
- **Status Indicators:** `Num`, `Caps`, `Ins`.

______________________________________________________________________

## 4. The Command Language (Interpreter)

The interpreter is a procedural, non-case-sensitive parser. It supports abbreviation of commands to the first four characters (e.g., `REPLACE` can be `REPL`).

### 4.1 Data Management Commands

- **`USE <table>`**: Opens a table in the current work area. If the table doesn't exist in the SQLite file, it throws an error.

- **`APPEND`**: Opens the full-screen Append mode to add new records.

- **`EDIT [RECNO]`**: Opens the full-screen Edit mode for the current or specified record.

- **`BROWSE`**: Opens the tabular spreadsheet view.

- **`LIST / DISPLAY [<scope>] [FIELDS <list>] [FOR <cond>]`**:

- `LIST` scrolls without pausing.

- `DISPLAY` pauses every 20 records (standard page size).

- **`REPLACE <field> WITH <expr> [FOR <cond>]`**: Executes a bulk update in SQLite.

- \*\*`DELETE` / `RECALL**`: Toggles the `_d_deleted` flag.

- **`PACK`**: Executes `DELETE FROM table WHERE _d_deleted = 1` followed by `VACUUM`.

### 4.2 Environmental "SET" Commands

- **`SET DEFAULT TO <path>`**: Sets the working directory for scripts and databases.
- **`SET EXACT ON/OFF`**: Controls whether string comparisons must be an exact length match.
- **`SET DELETED ON/OFF`**: If `ON`, records marked for deletion are hidden from all commands.
- **`SET INTENSITY ON/OFF`**: Controls high-contrast rendering of input fields.

______________________________________________________________________

## 5. Full-Screen Interactive Modes

These modes are the primary way users interact with data without writing code.

### 5.1 BROWSE Mode

The BROWSE screen is a scrollable grid.

- **Horizontal Navigation:** Use `Tab` or `Arrow Keys` to move between fields.
- **Vertical Navigation:** `Up/Down Arrows` move the record pointer. `PgUp/PgDn` moves by screen page.
- **Editing:** Typing in a cell updates the record immediately upon moving the cursor off the record.
- **Deletion:** `Ctrl + U` marks the current row for deletion (displays `*` in the status bar).

### 5.2 EDIT / APPEND Mode

These modes use a vertical form layout.

- Field labels appear on the left; value boxes on the right.
- If a custom format is active (`SET FORMAT TO <file>`), the layout follows the coordinates defined in the `.fmt` file using `@...SAY...GET` commands.

### 5.3 CREATE / MODIFY STRUCTURE

A specialized table-editing screen to define the schema:

1. **Field Name:** (Max 10 characters).
1. **Type:** (C, N, L, D, M).
1. **Width:** (Total characters).
1. **Decimals:** (For Numeric types).

______________________________________________________________________

## 6. The Programming Language

Safari Base supports procedural scripts (`.prg` files) that can be executed via the `DO <filename>` command.

### 6.1 Control Structures

- **`IF...ELSE...ENDIF`**: Conditional branching.
- **`DO WHILE <cond>...ENDDO`**: Logical loops.
- **`DO CASE...CASE <cond>...OTHERWISE...ENDCASE`**: Multi-way selection.

### 6.2 The `@...SAY...GET` System

This is the core of dBASE UI programming.

- **`@ <row>, <col> SAY "<text>"`**: Displays text at specific TUI coordinates.
- **`@ <row>, <col> GET <variable>`**: Defines an input buffer at a location.
- **`READ`**: The "activation" command. When `READ` is issued, the TUI enters an interactive mode where the user can move the cursor between all `GET` fields defined since the last `CLEAR` or `READ`.

### 6.3 Variable Scoping

- **PUBLIC**: Variables persist after the script ends.
- **PRIVATE**: Variables are local to the current script and its subroutines.

______________________________________________________________________

## 7. Keybindings (Modern Mapping)

To ensure usability on modern keyboards while respecting historical workflows:

| Legacy Key | Modern Key | Function |
| --- | --- | --- |
| **Ctrl+W** | **Ctrl+S** or **Ctrl+W** | Save and Exit Screen |
| **Esc** | **Esc** | Abandon Changes / Cancel |
| **Ctrl+U** | **Ctrl+D** | Toggle Delete Mark |
| **F1** | **F1** | Open Help System |
| **F10** | **Alt** or **F10** | Open ASSIST Menu |
| **Ctrl+Home** | **Home** | Move to start of field |
| **Ctrl+End** | **End** | Move to end of field |

______________________________________________________________________

## 8. Development Roadmap for "The Clanker"

### Phase 1: The Virtual Terminal

Implement a 25x80 grid using Python Textual. Create the `Status Bar` and `Dot Prompt` widgets. Ensure the "Dot Prompt" can capture input and echo it to the workspace.

### Phase 2: The SQLite Engine

Build the `Work Area Manager`. Create functions to translate dBASE `USE`, `LIST`, and `REPLACE` commands into SQL strings. Handle the `_d_deleted` logic transparently.

### Phase 3: The Parser

Implement a Lexer/Parser for the dBASE grammar.

- Handle command abbreviations.
- Implement the expression evaluator (e.g., `(salary * 1.1) > 50000`).

### Phase 4: Full-Screen Widgets

Build the `BrowseGrid` and `FormView` components. Implement the `READ` buffer logic to handle `@...GET` inputs.

### Phase 5: Language Implementation

Add support for `.prg` file execution, including loops, conditionals, and memory variable management.
