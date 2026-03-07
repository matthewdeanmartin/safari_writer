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
- [ ] Auto-numbering of section headings at print time

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

- [ ] `L` Load File — file picker / prompt for filename, load into buffer
- [ ] `S` Save File — prompt for filename, write buffer to disk
- [ ] `D` Delete File — prompt for filename, confirm, delete
- [ ] `1`/`2` Index Drive — directory listing display
- [x] `F` Format Disk — stub (shows "not applicable" message)
- [ ] File format: plain text with embedded control character sequences

---

## Phase 9: Print / Print Preview

- [x] `Ctrl+P` — stub in editor (shows "not yet implemented" message)
- [ ] Print Preview screen with paginated output
- [ ] Apply global format settings to render paginated output
- [ ] Apply inline formatting during render
- [ ] Mail merge injection at print time
- [ ] Form printing blanks — prompt user to fill at print time
- [ ] Page wait support
- [ ] Chain file support
- [ ] Actual print: send to system printer or export to file (PDF/text)

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

- [ ] `MailMergeScreen` — accessed from Main Menu "M"
- [ ] Status header: Bytes Free + Records Free (max 255)
- [ ] **Record Format (schema)**:
  - [ ] Default 15-field address template
  - [ ] Add / delete / rename fields (name up to 12 chars)
  - [ ] Adjust field character limits (max 20 chars per field)
  - [ ] Max 15 fields per schema
- [ ] **Data Entry**:
  - [ ] Form-fill UI per record
  - [ ] `Enter` advances to next field; empty fields allowed
  - [ ] Final field → "Definitions Complete Y/N?" confirm
- [ ] **Record Management (Update Menu)**:
  - [ ] `Page Up/Down` — previous/next record
  - [ ] `Ctrl+D` — delete record with "Are You Sure? Y/N"
- [ ] Append external Mail Merge file (must match schema exactly)
- [ ] **Build Subset (filtering)**:
  - [ ] Display all fields with Low Value / High Value columns
  - [ ] Apply alphabetical/numeric range filter to specified field
- [ ] **Document integration**:
  - [ ] `@N` merge markers in editor (inverse `@` display)
  - [ ] At print time: prompt for DB filename, iterate records, inject field values

---

## Phase 12: Polish & Edge Cases

- [x] Resolve `Shift+F3` conflict — kept as case toggle; replace-occurrence is `Alt+F3`
- [x] Bytes Free: tracked live from buffer size
- [ ] Caps lock mode indicator and behavior
- [ ] Tab stop management (set/clear individual tabs, clear all, UI arrow row updates)
- [ ] Double-column layout rendering (M/N margins)
- [ ] Confirm all keyboard shortcuts work correctly in Textual
- [x] Error messages displayed in message window (not dialog boxes)
- [ ] All destructive actions require Y/N confirmation in message window
