# ATARI BASIC–Style REPL Specification

## 1. Purpose

This document specifies a modern REPL for an ATARI BASIC–inspired language. The goal is to preserve the feel of classic line-numbered BASIC while adding practical developer features expected from a modern interactive environment.

The REPL must support both:

* **program mode**, where numbered lines are entered, listed, edited, saved, loaded, renumbered, and run
* **immediate mode**, where unnumbered commands and expressions are executed directly

The system should feel recognizably like an 8-bit BASIC environment, but be safer, friendlier, and more productive on modern machines.

---

## 2. Design Goals

The REPL shall:

* preserve the line-numbered workflow of classic BASIC
* support traditional commands such as `LIST`, `RUN`, `NEW`, `SAVE`, `LOAD`, and `REN`
* allow fast experimentation in immediate mode
* improve error messages and editability
* support modern conveniences without breaking the retro feel
* remain keyboard-centric and text-oriented
* avoid requiring external editors for normal use

The REPL should feel like a complete working environment, not merely a command prompt.

---

## 3. Core Concepts

### 3.1 Program Storage Model

A BASIC program is stored as an ordered collection of source lines.

Each stored line has:

* a positive integer line number
* a source text payload

Example:

```basic
10 PRINT "HELLO"
20 GOTO 10
```

A line entered with a line number replaces any existing line with the same line number.

A line entered with only a line number deletes that line.

Example:

```basic
10
```

deletes line 10.

### 3.2 Immediate Mode

Any input line that does not begin with a line number is interpreted as an immediate command, statement, or expression.

Examples:

```basic
PRINT 2+2
RUN
LIST 100,200
```

Immediate mode is used for:

* REPL commands
* one-off BASIC statements
* variable inspection
* quick arithmetic or experimentation

### 3.3 Program Mode

Any input line beginning with a valid line number is stored in the current program rather than executed immediately.

---

## 4. REPL States

The REPL has one active session with the following state:

* current in-memory program
* current variables and arrays
* runtime status
* current working filename, if any
* options and preferences
* command history
* undo/redo history for source changes

The REPL should keep source editing state separate from runtime variable state where practical.

---

## 5. Prompt and Interaction Model

### 5.1 Prompt

The default prompt should be concise and retro in spirit.

Example:

```text
READY
```

or

```text
OK
```

The prompt should reappear after successful command completion, program stop, or error.

### 5.2 Multiline Input

The REPL may support multiline entry for modern usability, but the default experience should prioritize classic single-line entry.

Multiline input should be optional and especially useful for:

* entering long statements
* editing compound constructs
* pasting larger blocks

If multiline input is supported, it must still compile back into numbered stored lines or explicit immediate blocks.

### 5.3 Keyboard Interaction

The REPL should support:

* up/down command history
* left/right cursor movement
* Home/End
* insert/delete
* Ctrl+C to interrupt a running program
* tab completion where appropriate
* recall of prior entered lines for editing

---

## 6. Traditional BASIC Commands

## 6.1 `LIST`

Displays stored program lines.

### Required behaviors

* `LIST` lists the whole program
* `LIST n` lists line `n`
* `LIST n,m` lists inclusive range from `n` to `m`
* `LIST n,` lists from `n` to end
* `LIST ,m` lists from start through `m`

Examples:

```basic
LIST
LIST 100
LIST 100,200
LIST 500,
LIST ,90
```

### Modern enhancements

* optional syntax highlighting
* optional line wrapping
* optional pager for long listings
* optional current-line marker in debugging contexts

---

## 6.2 `RUN`

Executes the current program from the beginning.

### Required behaviors

* clears runtime execution position
* initializes control flow state
* by default preserves or resets variables according to configured compatibility mode

Two modes are recommended:

* **classic mode**: `RUN` clears variable state
* **modern mode**: behavior configurable, but default should be explicit and documented

### Optional extension

```basic
RUN n
```

may begin execution at line `n` for debugging or development use, but this is a modern extension and should be clearly marked as such.

---

## 6.3 `NEW`

Clears the in-memory program.

### Required behaviors

* deletes all stored lines
* resets modified/dirty flag
* should warn before destructive action if there are unsaved changes

Example:

```basic
NEW
```

Suggested prompt:

```text
UNSAVED PROGRAM. REALLY NEW? (Y/N)
```

A configuration option may disable confirmation.

---

## 6.4 `SAVE`

Writes the current program to disk.

### Required forms

```basic
SAVE "filename.bas"
SAVE
```

Behavior:

* `SAVE "filename.bas"` saves to specified file and makes it current
* `SAVE` saves to current associated filename if one exists
* if no current filename exists, REPL should prompt for one or raise a clear error

### Save format

Default shall be plain text source, preserving line numbers.

Example file content:

```basic
10 PRINT "HELLO"
20 END
```

Optional alternate formats may be supported later, but plain text source is mandatory.

### Safety

Saving should be atomic where practical.

---

## 6.5 `LOAD`

Loads a program from disk into memory.

### Required forms

```basic
LOAD "filename.bas"
LOAD
```

Behavior:

* `LOAD "filename.bas"` loads the named program
* `LOAD` may reload current associated filename if one exists

### Safety

If unsaved changes exist, the REPL should warn before replacing the current in-memory program.

### Errors

Must clearly report:

* file not found
* parse errors
* duplicate or invalid line numbers
* unsupported encoding

---

## 6.6 `REN` / `RENUMBER`

Renumbers program lines.

The REPL should support both a compact retro form and a more discoverable full name.

### Required forms

```basic
REN
RENUMBER
REN start,step
REN start,step,from
```

Recommended semantics:

* `REN` renumbers all lines starting at 10 with step 10
* `REN start,step` renumbers all lines starting at `start` incrementing by `step`
* `REN start,step,from` renumbers only lines at or after `from`

### Required behavior

Renumbering must update all line-number references in the program, including at least:

* `GOTO`
* `GOSUB`
* `THEN` line targets
* `RESTORE` targets if supported
* `TRAP` targets if supported

If some references cannot be safely rewritten, the command must fail with a diagnostic rather than silently corrupting control flow.

### Output

The REPL should report what happened, for example:

```text
RENUMBERED 42 LINES
```

---

## 7. Additional Traditional Commands Worth Supporting

## 7.1 `CONT`

Continues execution after a stop or break, when safe.

## 7.2 `CLR`

Clears variables and runtime state without deleting the program.

## 7.3 `TRON` / `TROFF`

Turns execution tracing on and off.

Tracing may display executed line numbers or full lines.

## 7.4 `BYE` / `EXIT` / `QUIT`

Ends the REPL session.

At least one of these shall exist. Alias support is recommended.

## 7.5 `REM`

Stored comment lines must behave as normal BASIC source comments.

---

## 8. Modern REPL Features

These features are explicitly modern additions and need not mimic 8-bit behavior.

## 8.1 Command History

The REPL should remember previous immediate commands and optionally previous stored-line edits.

Required:

* up/down recall
* persistent history between sessions, optional
* searchable history, optional but recommended

---

## 8.2 Line Editing Shortcut

The REPL should provide a way to pull an existing program line into the editor for modification.

Recommended commands:

```basic
EDIT 120
```

or

```basic
ED 120
```

Behavior:

* retrieves stored line 120 into editable input
* after editing and submit, replaces line 120
* if canceled, makes no change

This is one of the most valuable modern improvements.

---

## 8.3 Tab Completion

Recommended completion targets:

* REPL commands
* BASIC keywords
* intrinsic function names
* filenames in `SAVE`, `LOAD`, `MERGE`, etc.
* line numbers in commands like `LIST`, `DELETE`, `EDIT`

Tab completion should never alter source unexpectedly.

---

## 8.4 Better Error Messages

The REPL should improve upon terse vintage errors while optionally supporting classic messages.

Each error should ideally include:

* error category
* offending line number if relevant
* source excerpt if relevant
* human-readable explanation

Example:

```text
SYNTAX ERROR AT LINE 120: EXPECTED ")" AFTER EXPRESSION
```

A compatibility option may additionally show:

```text
ERROR 12
```

---

## 8.5 Source Undo/Redo

The REPL should support undo and redo for editing operations that affect stored program source.

Recommended commands:

```basic
UNDO
REDO
```

Undoable operations should include:

* line insertion
* line replacement
* line deletion
* renumbering
* load
* merge
* delete range

This is a major modern safety improvement.

---

## 8.6 Dirty/Modified State

The REPL should track whether the current program differs from the last saved or loaded version.

The UI should make this visible, for example in a status line or prompt decoration.

---

## 8.7 Autosave / Recovery

Recommended modern feature:

* optional periodic autosave
* crash recovery file
* prompt to restore recovered program on startup

This must not overwrite the canonical saved source without consent.

---

## 8.8 Search

Recommended commands:

```basic
FIND "PRINT"
FIND "GOTO"
```

Behavior:

* searches program source text
* displays matching lines
* case sensitivity configurable

Very useful in larger programs.

---

## 8.9 Replace

Optional but desirable:

```basic
REPLACE "FOO","BAR"
```

This should preview changes or require confirmation.

---

## 8.10 Delete Range

Recommended command:

```basic
DELETE 100,300
```

Deletes a range of stored lines.

Should be undoable.

---

## 8.11 Merge

Recommended command:

```basic
MERGE "other.bas"
```

Loads lines from another source file into the current program without discarding existing lines.

Conflicts should be explicit:

* overwrite existing lines by line number, with warning or option
* or fail unless forced

---

## 8.12 Export Without Line Numbers

Recommended command:

```basic
EXPORT "file.txt"
```

Exports source in a modern readable form, optionally stripping line numbers.

This is useful for documentation or migration, but should not replace normal `SAVE`.

---

## 8.13 Session Transcript Logging

Optional command:

```basic
TRANSCRIPT ON
TRANSCRIPT OFF
```

Logs interactive session input/output for teaching, debugging, or demos.

---

## 8.14 Help System

Required modern command:

```basic
HELP
HELP LIST
HELP FOR
HELP ERRORS
```

The REPL should include a built-in help system covering:

* commands
* syntax
* functions
* statements
* examples
* error messages

This matters a lot for usability.

---

## 9. Inspection and Debugging Features

## 9.1 Variable Inspection

Recommended commands:

```basic
VARS
PRINT A
PRINT A$
PRINT ARR(3)
```

`VARS` should list current variable names and values.

Options:

```basic
VARS A*
```

for prefix filtering.

---

## 9.2 Breakpoints

Modern optional feature:

```basic
BREAK 120
BREAK CLEAR 120
BREAK LIST
```

If breakpoints are implemented, execution should stop before the targeted line executes.

---

## 9.3 Single-Step Execution

Modern optional feature:

```basic
STEP
NEXT
CONT
```

Useful for debugging control flow.

---

## 9.4 Trace Mode

`TRON` should ideally support richer tracing modes:

```basic
TRON
TRON FULL
TRON LINES
TRON VARS
```

At minimum, line-number tracing is sufficient.

---

## 9.5 Stack/Call Inspection

If `GOSUB` is supported, a modern debugger may provide:

```basic
STACK
```

showing active return stack.

---

## 10. File Handling Requirements

## 10.1 Encoding

Source files should default to UTF-8.

ASCII-only compatibility mode may be offered.

## 10.2 Line Endings

The REPL should read both LF and CRLF text files.

## 10.3 Extensions

Suggested default program extension:

* `.bas`

Other accepted extensions may include:

* `.lst`
* `.txt`

## 10.4 Safe Writes

Saves should use temp-file-plus-rename where possible.

## 10.5 Backups

Optional feature:

* keep numbered backup generations
* or write `.bak` on overwrite

---

## 11. Compatibility Modes

The REPL should support at least two modes.

### 11.1 Classic Compatibility Mode

Prioritizes classic behavior:

* terse messages
* stricter syntax rules
* classic `READY`
* `RUN` clears variables
* minimal prompting

### 11.2 Enhanced Mode

Prioritizes modern usability:

* helpful diagnostics
* undo/redo
* autosave
* completions
* search/edit helpers
* optional syntax coloring

The mode should be obvious and configurable.

---

## 12. Suggested Command Set

This is a recommended command inventory.

### Core

* `LIST`
* `RUN`
* `NEW`
* `SAVE`
* `LOAD`
* `REN` / `RENUMBER`
* `CLR`
* `CONT`
* `BYE` / `EXIT`

### Editing

* `EDIT`
* `DELETE`
* `FIND`
* `REPLACE`
* `MERGE`
* `UNDO`
* `REDO`

### Debugging

* `TRON`
* `TROFF`
* `BREAK`
* `STEP`
* `NEXT`
* `VARS`
* `STACK`

### Help / Utility

* `HELP`
* `STATUS`
* `FILES`
* `PWD`
* `CD`

The last few are optional if the REPL wants light operating-environment support.

---

## 13. Status Display

A one-line status area is recommended.

It may show:

* current filename
* modified flag
* mode
* trace status
* line count
* last error

Example:

```text
[demo.bas] [modified] [enhanced] [42 lines]
```

This is a modern addition but highly worthwhile.

---

## 14. Errors and Recovery

The REPL shall distinguish between:

* syntax errors while storing source
* runtime errors during execution
* command errors
* file system errors
* internal REPL failures

Required recovery behavior:

* source should not be lost on a runtime error
* syntax error in one stored line should not corrupt other lines
* interrupted execution should return to prompt safely
* failed renumbering should leave program unchanged

---

## 15. Non-Goals

This REPL spec does not require:

* graphics commands
* sound commands
* cassette/tape operations
* hardware memory pokes
* machine-language integration
* platform-specific device syntax

Those may exist elsewhere in the language or implementation, but they are outside this REPL specification.

---

## 16. Example Session

```text
READY
10 PRINT "HELLO"
20 GOTO 10
LIST
10 PRINT "HELLO"
20 GOTO 10
REN
RENUMBERED 2 LINES
LIST
10 PRINT "HELLO"
20 GOTO 10
RUN
HELLO
HELLO
HELLO
^C
BREAK IN 20
READY
SAVE "hello.bas"
SAVED hello.bas
NEW
UNSAVED PROGRAM. REALLY NEW? (Y/N) Y
READY
LOAD "hello.bas"
LOADED hello.bas
RUN
HELLO
```

---

## 17. Recommended Minimum Viable Feature Set

If implementing in phases, the first complete usable version should include:

* numbered line entry
* immediate execution
* `LIST`
* `RUN`
* `NEW`
* `SAVE`
* `LOAD`
* `REN` / `RENUMBER`
* line deletion by entering bare line number
* command history
* interrupt with Ctrl+C
* clear error reporting
* unsaved-change warning

After that, the most valuable next additions are:

* `EDIT`
* `UNDO`
* `FIND`
* `HELP`
* `TRON` / `TROFF`
* `VARS`

---

## 18. Implementation Guidance for Feel

To preserve the intended atmosphere, the REPL should:

* keep commands short and keyboard-friendly
* favor fast interaction over menus
* preserve line numbers as first-class
* use minimal but readable output
* avoid overly chatty prompts unless help mode is enabled
* allow modern features, but not force them into every interaction
