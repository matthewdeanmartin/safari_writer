# Safari Writer - Implementation TODO

## Architecture Notes
- Framework: Python + Textual (TUI)
- "What you see is what you mean" — inline control chars displayed as symbols, not rendered
- Three main app screens: Main Menu, Editor, and module screens (Global Format, Proofreader, Mail Merge)

---

## Phase 1: Project Scaffold

- done
---

## Phase 2: Main Menu Screen

- done
---

## Phase 3: Editor Screen (Core)

- done 
---

## Phase 4: Block Operations

-  done
---

## Phase 5: Search & Replace

- done
---

## Phase 6: Inline Formatting

- [ ] Mid-document global format override (inline margin/spacing change)
---

## Phase 7: Global Format Screen

- done
---

## Phase 8: File Operations

- [ ] Replace the current ad-hoc file/index actions with a Safari DOS handoff entry point from Safari Writer
- [ ] Route load/save/save-as folder picking through Safari DOS once the integration contract exists

---

## Phase 9: Print / Export (see spec/07_file_format_and_print.md)

- [ ] Mail merge injection at print/export time (prompt for DB file, iterate records)

---

## Phase 10: Proofreader Module

- [ ] Manual dictionary creation via editor (space/CR-separated word list) — use editor directly

---

## Phase 11: Mail Merge Module

- [ ] **Document integration**:
  - [ ] At print time: prompt for DB filename, iterate records, inject field values (Phase 9)

---

## Phase 12: Polish & Edge Cases

- [ ] Double-column layout rendering (M/N margins in preview and PostScript)
- [ ] Mail merge injection at print/export time — prompt for DB file, iterate records, substitute `@N` fields
- [ ] Mid-document global format override (inline margin/spacing change, new control chars)
---

## Phase 13: CLI Interface

- basically done

---

## Phase 14: Safari DOS Module

- [ ] Create an independent `safari_dos` module/package instead of folding the feature into `safari_writer`
- [ ] Add a standalone app entry point (`safari-dos`) so Safari DOS can launch directly without opening Safari Writer first
- [ ] Add a module entry path (`python -m safari_dos` or equivalent) for direct invocation during development/tests
- [ ] Define the Safari DOS <-> Safari Writer handoff contract:
  - [ ] decide whether integration is in-process, subprocess-based, or both
  - [ ] preserve current folder/project context when handing off between apps
  - [ ] support opening a selected document in Safari Writer from Safari DOS
  - [ ] support Save As / location picking through Safari DOS from Safari Writer
  - [ ] support returning from Safari Writer to the same Safari DOS project location when practical
- [ ] Add shared recent-document / recent-project plumbing if Safari DOS and Safari Writer are meant to share history

### Safari DOS app architecture

- [ ] Create Safari DOS-specific app state for:
  - [ ] current device/location
  - [ ] selected entries / multi-select state
  - [ ] sort and filter state
  - [ ] favorites and recent locations
  - [ ] pending operation / confirmation context
  - [ ] garbage / restore metadata where platform trash is not enough
- [ ] Extract or add reusable filesystem services instead of wiring file operations directly in screen classes
- [ ] Add a cross-platform device/location discovery layer:
  - [ ] system volume / primary drive
  - [ ] removable media
  - [ ] home
  - [ ] Documents
  - [ ] Desktop / Downloads where appropriate
  - [ ] configured favorites
- [ ] Add a Python-native trash/garbage abstraction with reversible behavior and no permanent-delete UI
- [ ] Add a protect/unprotect abstraction mapped to modern read-only semantics
- [ ] Add conflict-resolution, preview, and progress/result models for state-changing operations
- [ ] Add persistence for favorites, recent locations, and any Safari DOS-managed garbage metadata

### Safari DOS screens and flows

- [ ] Build a Safari DOS main menu with stable lettered actions and Atari DOS tone
- [ ] Build the primary file-list screen with persistent regions for:
  - [ ] title/status
  - [ ] current device/path
  - [ ] listing body
  - [ ] prompt line
  - [ ] help/message line
- [ ] Add operation prompt screens for source, destination, naming, and bulk-action confirmation
- [ ] Add help screens / contextual help text for every operation and prompt
- [ ] Add devices screen
- [ ] Add favorites / recent locations screen
- [ ] Add garbage browser / restore screen
- [ ] Add info/details screen
- [ ] Add conflict-resolution screen
- [ ] Add progress screen for long-running operations

### File listing, navigation, and selection

- [ ] Show entry name, type, size, modified time, protected state, and hidden/alias indicators where relevant
- [ ] Support entering folders, going up, going home, jumping to Documents/Desktop, switching devices, and returning to previous location
- [ ] Support refresh and hidden-file toggle
- [ ] Support type-to-jump in listings
- [ ] Support single-select and multi-select modes
- [ ] Support acting on one item, all visible items, filtered results, and pattern matches
- [ ] Support list sorting by name/date/size/type with ascending/descending toggle
- [ ] Support filtering by name pattern and file type/extension

### Core file operations

- [ ] Copy files and folders with recursive handling, previews, conflicts, progress, and summaries
- [ ] Move files and folders with same-device/cross-device behavior, previews, conflicts, progress, and summaries
- [ ] Rename files and folders safely, including previewable batch rename if we support it
- [ ] Duplicate files/folders for draft workflows with safe auto-generated names
- [ ] Create new folders with validation and optional jump into the new folder
- [ ] Send files/folders to Garbage instead of deleting them
- [ ] Restore files/folders from Garbage to original or alternate location
- [ ] Show file/folder info and selected-size summaries
- [ ] Search by name in current folder and recursively from current folder

### Safety and cross-platform behavior

- [ ] Replace all current permanent-delete behavior in writer-facing flows with safe Garbage/Trash behavior
- [ ] Require confirmation for garbage moves, cross-device moves, recursive folder operations, replace-on-conflict, and restore collisions
- [ ] Never guess silently on name conflicts; support skip, rename, replace, and apply-to-rest flows where appropriate
- [ ] Report partial failures and interrupted operations in plain language
- [ ] Keep core file operations Python-native; no shelling out for copy/move/trash/search basics
- [ ] Make Windows/macOS/Linux behavior consistent enough to learn once, with help text for unavoidable differences

### Writer-focused workflow support

- [ ] Default filters/favorites for writer-friendly document locations and file types
- [ ] Open selected document in Safari Writer from Safari DOS
- [ ] Create new document from Safari DOS
- [ ] Duplicate a document as a new draft from Safari DOS
- [ ] Optionally create dated backup copy before opening

### Testing and documentation

- [ ] Add unit tests for filesystem service, conflict handling, trash/garbage behavior, and protect/unprotect logic
- [ ] Add Textual interaction tests for Safari DOS navigation and operation flows
- [ ] Add CLI tests for standalone Safari DOS launch and writer/DOS handoff paths
- [ ] Add cross-platform path/device tests where behavior differs by OS
- [ ] Update README / CLI docs once Safari DOS has a public entry point
