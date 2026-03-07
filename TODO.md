# Safari Writer - Implementation TODO

## Architecture Notes
- Framework: Python + Textual (TUI)
- "What you see is what you mean" — inline control chars displayed as symbols, not rendered
- Three main app screens: Main Menu, Editor, and module screens (Global Format, Proofreader, Mail Merge)

---

## Phase 1: Project Scaffold

- [ ] Create `pyproject.toml` with dependencies (`textual`, `pyenchant` or `symspellpy` for spellcheck)
- [ ] Create entry point `main.py`
- [ ] Set up basic Textual `App` class
- [ ] Define app-level state: document buffer, clipboard, format settings, mode flags

---

## Phase 2: Main Menu Screen

- [ ] `MainMenuScreen` — list of options with highlighted first letter
- [ ] Key bindings: C, E, V, P, G, M, 1, 2, L, S, D, F
- [ ] Routing: each key navigates to appropriate screen/action
- [ ] Status bar: "Bytes Free" display

---

## Phase 3: Editor Screen (Core)

### 3a. Status Header
- [ ] Message window (top line) — prompts, errors, questions
- [ ] System status line: Bytes Free | Insert/Type-over mode | Lower/Uppercase mode
- [ ] Tab indicator row: 16 downward arrows reflecting current tab stops

### 3b. Document Buffer & Rendering
- [ ] In-memory text buffer (list of lines or rope structure)
- [ ] Word wrap logic (auto-wrap at right margin, hard CR only for paragraphs)
- [ ] Paragraph mark (`Ctrl+M`) — non-printing symbol stored in buffer, displayed as special char
- [ ] Render inline control characters as visible symbols (bold marker, underline, etc.)
- [ ] Blinking block cursor

### 3c. Navigation
- [ ] Arrow keys (char/line movement)
- [ ] `Ctrl+Left/Right` — word jump
- [ ] `Home/End` — line start/end
- [ ] `Ctrl+Home/End` — top/bottom of file
- [ ] `Page Up/Down` — page scroll

### 3d. Edit Modes
- [ ] `Insert` key — toggle Insert vs. Type-over mode
- [ ] Insert mode: push text right
- [ ] Type-over mode: replace text under cursor

### 3e. Deletion
- [ ] `Backspace` / `Delete` — character deletion
- [ ] `Shift+Delete` — delete to end of screen line (store for undelete)
- [ ] `Ctrl+Z` — undelete (restore last deleted line at cursor)
- [ ] `Ctrl+Shift+Delete` — delete to end of file

### 3f. Case Toggle
- [ ] `Shift+F3` — toggle case of character under cursor

---

## Phase 4: Block Operations

- [ ] Standard text selection (highlight region)
- [ ] `Ctrl+X` — cut to failsafe buffer
- [ ] `Ctrl+C` — copy to failsafe buffer
- [ ] `Ctrl+V` — paste from failsafe buffer
- [ ] `Alt+W` — word count (selection or whole file), display in message window
- [ ] `Alt+A` — alphabetize selected list of lines

---

## Phase 5: Search & Replace

- [ ] `Ctrl+F` — prompt for search string (up to 37 chars), find first occurrence
- [ ] `Ctrl+H` — prompt for replacement string
- [ ] `F3` — find next occurrence
- [ ] `Shift+F3` — replace current occurrence (note: conflicts with case toggle — resolve)
- [ ] `Alt+R` — global replace to end of file
- [ ] Wildcard `?` support in search strings

---

## Phase 6: Inline Formatting

- [ ] `Ctrl+B` — bold toggle; display left-arrow marker `←` in buffer
- [ ] `Ctrl+U` — underline toggle; render affected text in inverse video
- [ ] `Ctrl+E` — center line; display center marker at line start
- [ ] `Ctrl+R` — flush right; display double-marker at line start
- [ ] Elongated (double-width) toggle; display `E` marker
- [ ] Subscript / superscript toggles; display up/down arrow markers
- [ ] Header/footer command + text (own dedicated line, ends with CR)
- [ ] `@` in header/footer = page number placeholder
- [ ] Section heading: insert `H` marker + level (1-9); auto-number on print
- [ ] Page eject (hard page break) command
- [ ] Chain print file command at document end
- [ ] `Alt+F` — form printing blank (fill-in prompt at print time)
- [ ] `Alt+M` — insert mail merge `@N` field marker
- [ ] Mid-document global format override (inline margin/spacing change)

---

## Phase 7: Global Format Screen

- [ ] `GlobalFormatScreen` — vertical list of parameters with letter keys
- [ ] Parameters with defaults:
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
- [ ] Press letter → cursor jumps to value field → user types new value → `Enter` confirms
- [ ] `Tab` — reset all to defaults
- [ ] `Esc` — accept and return to Main Menu

---

## Phase 8: File Operations

- [ ] `L` Load File — file picker / prompt for filename, load into buffer
- [ ] `S` Save File — prompt for filename, write buffer to disk
- [ ] `D` Delete File — prompt for filename, confirm, delete
- [ ] `1`/`2` Index Drive — directory listing display
- [ ] `F` Format Disk — stub / not applicable (show message)
- [ ] File format: plain text with embedded control character sequences

---

## Phase 9: Print / Print Preview

- [ ] `Ctrl+P` — Print Preview screen
- [ ] Apply global format settings to render paginated output
- [ ] Apply inline formatting during render
- [ ] Mail merge injection at print time
- [ ] Form printing blanks — prompt user to fill at print time
- [ ] Page wait support
- [ ] Chain file support
- [ ] Actual print: send to system printer or export to file (PDF/text)

---

## Phase 10: Proofreader Module

- [ ] `ProofreaderScreen` — terminal-style, accessed from Main Menu "V"
- [ ] Mode selection: Highlight Errors / Print Errors / Correct Errors
- [ ] Load master dictionary (36,000+ words) — use `pyenchant` or bundled wordlist
- [ ] **Highlight mode**: scroll through doc, flag unrecognized words in inverse video
- [ ] **Print Errors mode**: scan, display list, optionally send to printer
- [ ] **Correct Errors mode**:
  - [ ] Stop at each flagged word
  - [ ] Correction menu: Correct Word / Search Dictionary / Keep This Spelling
  - [ ] "Correct Word" → prompt for replacement → "Are you sure? Y/N" → replace
  - [ ] "Search Dictionary" → prompt 2+ letters → display up to 18 matching words, pageable
  - [ ] "Keep This Spelling" → add to session memory, skip on future hits
- [ ] Standalone dictionary search (2+ letters → up to 126 matches per page)
- [ ] Personal dictionary: save session "kept" words (up to 256) to file
- [ ] Load personal dictionary file(s) before proofing session
- [ ] Manual dictionary creation via editor (space/CR-separated word list)

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

- [ ] Resolve `Shift+F3` conflict (case toggle vs. replace — pick one or use context)
- [ ] Bytes Free: track actual buffer size and display live
- [ ] Caps lock mode indicator and behavior
- [ ] Tab stop management (set/clear individual tabs, clear all, UI arrow row updates)
- [ ] Double-column layout rendering (M/N margins)
- [ ] Confirm all keyboard shortcuts work correctly in Textual
- [ ] Error messages displayed in message window (not dialog boxes)
- [ ] All destructive actions require Y/N confirmation in message window
