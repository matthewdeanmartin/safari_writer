# Safari Writer - Implementation TODO

## Architecture Notes
- Framework: Python + Textual (TUI)
- "What you see is what you mean" — inline control chars displayed as symbols, not rendered
- Three main app screens: Main Menu, Editor, and module screens (Global Format, Proofreader, Mail Merge)

---

## Phase 1: Project Scaffold

- [x] Create `pyproject.toml` with dependencies (`textual`, `pyenchant` or `symspellpy` for spellcheck)
- [x] Create entry point `main.py`
- [x] Set up basic Textual `App` class
- [x] Define app-level state: document buffer, clipboard, format settings, mode flags

---

## Phase 2: Main Menu Screen

- [x] `MainMenuScreen` — list of options with highlighted first letter
- [x] Key bindings: C, E, V, P, G, M, 1, 2, L, S, D, F
- [x] Routing: each key navigates to appropriate screen/action
- [x] Status bar: "Bytes Free" display

---

## Phase 3: Editor Screen (Core)

### 3a. Status Header
- [x] Message window (top line) — prompts, errors, questions
- [x] System status line: Bytes Free | Insert/Type-over mode | Lower/Uppercase mode
- [x] Tab indicator row: 16 downward arrows reflecting current tab stops

### 3b. Document Buffer & Rendering
- [x] In-memory text buffer (list of lines or rope structure)
- [x] Word wrap logic (auto-wrap at right margin, hard CR only for paragraphs)
- [x] Paragraph mark (`Ctrl+M`) — non-printing symbol stored in buffer, displayed as special char
- [x] Render inline control characters as visible symbols (bold marker, underline, etc.)
- [ ] Blinking block cursor (Textual renders reverse-video block; true blink not yet implemented)

### 3c. Navigation
- [x] Arrow keys (char/line movement)
- [x] `Ctrl+Left/Right` — word jump
- [x] `Home/End` — line start/end
- [x] `Ctrl+Home/End` — top/bottom of file
- [x] `Page Up/Down` — page scroll
- [x] `Tab` — advance to next tab stop (inserts spaces in insert mode)
- [x] `Ctrl+T` — toggle tab stop at cursor column
- [x] `Ctrl+Shift+T` — clear all tab stops

### 3d. Edit Modes
- [x] `Insert` key — toggle Insert vs. Type-over mode
- [x] Insert mode: push text right
- [x] Type-over mode: replace text under cursor

### 3e. Deletion
- [x] `Backspace` / `Delete` — character deletion
- [x] `Shift+Delete` — delete to end of screen line (store for undelete)
- [x] `Ctrl+Z` — undelete (restore last deleted line at cursor)
- [x] `Ctrl+Shift+Delete` — delete to end of file

### 3f. Case Toggle
- [x] `Shift+F3` — toggle case of character under cursor

### 3g. Help Screen
- [x] `F1` / `?` — modal overlay listing all key commands

---

## Phase 4: Block Operations

- [x] Standard text selection — Shift+Arrow/Home/End/Ctrl+Home/End; rendered in inverse blue
- [x] `Ctrl+X` — cut selection (or current line) to failsafe buffer
- [x] `Ctrl+C` — copy selection (or current line) to failsafe buffer
- [x] `Ctrl+V` — paste at cursor inline (replaces selection if active); multi-line clipboard supported
- [x] `Alt+W` — word count (selection or whole file), display in message window
- [x] `Alt+A` — alphabetize selected lines (or all lines)

---

## Phase 5: Search & Replace

- [x] `Ctrl+F` — prompt for search string (up to 37 chars), find first occurrence
- [x] `Ctrl+H` — prompt for replacement string
- [x] `F3` — find next occurrence (wraps around end of file)
- [x] `Shift+F3` — kept as case toggle; replace-occurrence mapped to `Alt+F3` instead
- [x] `Alt+F3` — replace current occurrence, then find next
- [x] `Alt+R` — global replace to end of file, reports count
- [x] Wildcard `?` support in search strings

---

## Phase 6: Inline Formatting

- [x] `Ctrl+B` — bold toggle; `←` marker; text after marker rendered **bold**
- [x] `Ctrl+U` — underline toggle; `▄` marker; text after marker rendered in inverse video
- [x] `Ctrl+G` — elongated toggle; `E` marker; text after marker rendered dim
- [x] `Ctrl+[` — superscript toggle; `↑` marker; text rendered bright_white
- [x] `Ctrl+]` — subscript toggle; `↓` marker; text rendered bright_white
- [x] `Ctrl+E` — center line; `↔` marker at line start
- [x] `Ctrl+R` — flush right; `→→` marker at line start
- [x] `Ctrl+M` — paragraph indent marker `¶`
- [x] `Alt+M` — mail merge `@` field marker
- [x] `Alt+F` — form printing blank `_` marker
- [x] Toggle markers carry format state across lines (bold/underline/etc. span line breaks)
- [x] `Ctrl+Shift+H` — insert header line marker (`H:`) on its own line
- [x] `Ctrl+Shift+F` — insert footer line marker (`F:`) on its own line
- [x] `@` in header/footer text = page number placeholder (typed naturally)
- [x] `Ctrl+Shift+S` — insert section heading (`H` + level 1-9, prompted), own line
- [x] `Ctrl+Shift+E` — page eject / hard page break (`↡` marker), own line
- [x] `Ctrl+Shift+C` — chain print file (`»` + filename, prompted), appended at end
- [ ] Mid-document global format override (inline margin/spacing change)
- [x] Auto-numbering of section headings at print/export time
---

## Phase 7: Global Format Screen

- [x] `GlobalFormatScreen` — vertical list of parameters with letter keys
- [x] Parameters with defaults:
  - T: Top Margin (12)
  - B: Bottom Margin (12)
  - L: Left Margin (10)
  - R: Right Margin (70)
  - S: Line Spacing (2)
  - D: Paragraph Spacing (2)
  - M: 2nd Left Margin (8)
  - N: 2nd Right Margin (70)
  - G: Type Font (1)
  - I: Paragraph Indentation (5)
  - J: Justification (0)
  - Q: Page Number start (1)
  - Y: Page Length (132)
  - W: Page Wait (0)
- [x] Press letter → cursor jumps to value field → user types new value → `Enter` confirms
- [x] `Tab` — reset all to defaults
- [x] `Esc` — accept and return to Main Menu

---

## Phase 8: File Operations

- [x] `L` Load File — prompt for filename, load into buffer
- [x] `S` Save File — prompt for filename, write buffer to disk
- [x] `D` Delete File — prompt for filename, Y/N confirm, delete
- [x] `1` Index Current Folder — directory listing with navigation, load, delete, new folder
- [x] `2` Index External Drive — detect removable/external drives, directory listing
- [x] `F` New Folder — prompt for name, create directory
- [x] IndexScreen — AtariWriter-style directory listing (name, size, type columns)
- [x] DrivePickerScreen — select from multiple external drives
- [x] ConfirmScreen — Y/N confirmation dialog for destructive actions
- [x] File format: `.sfw` (Safari Writer Formatted) with escaped tags; plain text for all other extensions
- [x] `format_codec.py` — `encode_sfw()`, `decode_sfw()`, `strip_controls()`
- [x] Load/save in `app.py` routes through codec based on file extension
- [x] Plain text save strips control chars with warning if formatting present
- [x] Status bar shows `[SFW]` or `[TXT]` based on filename extension

---

## Phase 9: Print / Export (see spec/07_file_format_and_print.md)

- [x] `Ctrl+P` — opens Print/Export dialog from editor
- [x] `PrintScreen` modal dialog: ANSI Preview / Markdown Export / PostScript Export
- [x] `Ctrl+P` in editor and `P` on main menu both open `PrintScreen`
- [x] **ANSI Preview** (`PrintPreviewScreen`):
  - [x] Read-only paginated view applying global format + inline formatting
  - [x] Headers/footers rendered per page, page numbering
  - [x] Page breaks shown as horizontal rules
  - [x] Margins, spacing, justification applied (justification is placeholder, left-aligns)
  - [x] Navigation: PgUp/PgDn, Up/Down, Home/End, Esc
- [x] **Markdown export** (`export_md.py`):
  - [x] Bold → `**...**`, underline → `<u>`, section headings → `#` levels
  - [x] Page breaks → `---`, merge fields → `{{field_N}}`
  - [x] Prompt for output filename
- [x] **PostScript export** (`export_ps.py`):
  - [x] Full page layout engine using GlobalFormat settings
  - [x] Font mapping, margins, pagination, headers/footers
  - [x] Bold/underline/super/subscript rendered with PS font changes
  - [x] Prompt for output filename
- [ ] Mail merge injection at print/export time (prompt for DB file, iterate records)
- [x] Form printing blanks — rendered as `[________]` in preview/export
- [x] Chain file support — shown as comment in markdown, ignored in PS

---

## Phase 10: Proofreader Module

- [x] `ProofreaderScreen` — terminal-style, accessed from Main Menu "V"
- [x] Mode selection: Highlight Errors / Print Errors / Correct Errors
- [x] Load master dictionary (36,000+ words) — uses `pyenchant` en_US
- [x] **Highlight mode**: scan doc, flag unrecognized words in inverse video
- [x] **Print Errors mode**: scan, display list on-screen
- [x] **Correct Errors mode**:
  - [x] Stop at each flagged word
  - [x] Correction menu: Correct Word / Search Dictionary / Keep This Spelling
  - [x] "Correct Word" → prompt for replacement → "Are you sure? Y/N" → replace
  - [x] "Search Dictionary" → prompt 2+ letters → display up to 126 matching words, pageable
  - [x] "Keep This Spelling" → add to session memory, skip on future hits
- [x] Standalone dictionary search (2+ letters → up to 126 matches per page)
- [x] Personal dictionary: save session "kept" words (up to 256) to file
- [x] Load personal dictionary file(s) before proofing session
- [ ] Manual dictionary creation via editor (space/CR-separated word list) — use editor directly

---

## Phase 11: Mail Merge Module

- [x] `MailMergeScreen` — accessed from Main Menu "M"
- [x] Status header: Bytes Free + Records Free (max 255)
- [x] **Record Format (schema)**:
  - [x] Default 15-field address template
  - [x] Add / delete / rename fields (name up to 12 chars)
  - [x] Adjust field character limits (max 20 chars per field)
  - [x] Max 15 fields per schema
- [x] **Data Entry**:
  - [x] Form-fill UI per record
  - [x] `Enter` advances to next field; empty fields allowed
  - [x] Final field → "Definitions Complete Y/N?" confirm
- [x] **Record Management (Update Menu)**:
  - [x] `Page Up/Down` — previous/next record
  - [x] `Ctrl+D` — delete record with "Are You Sure? Y/N"
  - [x] `E` — edit fields of current record inline
- [x] Append external Mail Merge file (must match schema exactly)
- [x] Save / Load database to/from JSON file
- [x] **Build Subset (filtering)**:
  - [x] Display all fields with Low Value / High Value columns
  - [x] Apply alphabetical/numeric range filter to specified field
- [ ] **Document integration**:
  - [x] `@N` merge markers in editor (inverse `@` display) — markers already supported in editor
  - [ ] At print time: prompt for DB filename, iterate records, inject field values (Phase 9)

---

## Phase 12: Polish & Edge Cases

- [x] Resolve `Shift+F3` conflict — kept as case toggle; replace-occurrence is `Alt+F3`
- [x] Bytes Free: tracked live from buffer size
- [x] Caps lock mode indicator (`[Uppercase]` / `[Lowercase]` in status bar) and `Caps Lock` key binding
- [x] Tab stop management: `Ctrl+T` toggles stop at cursor column, `Ctrl+Shift+T` clears all, tab bar updates live
- [x] Unsaved changes check on "Create File" — Y/N confirmation before discarding buffer
- [ ] Double-column layout rendering (M/N margins in preview and PostScript)
- [x] Auto-numbering of section headings at print/export time (1.0, 1.1, 2.0, etc.)
- [ ] Mail merge injection at print/export time — prompt for DB file, iterate records, substitute `@N` fields
- [ ] Mid-document global format override (inline margin/spacing change, new control chars)
- [x] Error messages displayed in message window (not dialog boxes)
- [x] Destructive actions require confirmation: Delete File ✓, plain-text save ✓, Create with unsaved changes ✓

---

## Phase 13: CLI Interface

- [x] Write exhaustive CLI specification for argparse-based subcommands and direct-entry TUI startup (`spec/08_cli_interface.md`)
- [x] Refactor `safari_writer.main` to expose a pytest-friendly `main(argv=None) -> int`
- [x] Add `argparse` parser builder with nested subcommands for `tui`, `export`, `proof`, `format`, and `mail-merge`
- [x] Add a startup request/config object so `SafariWriterApp` can launch directly into menu, editor, proofreader, global format, mail merge, print, preview, or file index flows
- [x] Support bare-file shorthand (`safari-writer FILE`) as an alias for direct-entry editor startup
- [x] Extract reusable headless helpers for document load/save, export, proofing, and mail-merge inspection so CLI commands do not depend on Textual screens
- [x] Implement headless export subcommands for Markdown, PostScript, and ANSI render output
- [x] Implement headless proof subcommands for check/list/suggest with stable exit codes
- [x] Implement headless format subcommands for `.sfw` encode/decode/strip workflows
- [x] Implement headless mail-merge subcommands for inspect/subset/append/validate workflows
- [x] Add pytest coverage for parser defaults, invalid combinations, startup request mapping, headless handlers, and exit-code contracts
