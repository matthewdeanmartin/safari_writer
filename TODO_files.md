# Spec 10: File Type Awareness — Implementation Progress

## Completed

### Core file type classification (`file_types.py`) — DONE
- [x] `StorageMode` enum (FORMATTED / PLAIN)
- [x] `HighlightProfile` enum (safari-writer, plain-text, markdown, python, javascript, typescript, json, toml, yaml, ini, english-text, english-markdown)
- [x] `FileProfile` dataclass with storage_mode, highlight_profile, display_name, convenience properties
- [x] `resolve_file_profile(filename)` with suffix map, case-insensitive .sfw detection, English overlay support
- [x] Pygments lexer mapping for code types

### State integration (`state.py`) — DONE
- [x] `file_profile` field on `AppState`
- [x] `storage_mode`, `highlight_profile`, `allows_formatting` convenience properties
- [x] `update_file_profile()` method
- [x] Default profile is "untitled.sfw" (formatted mode)

### Document I/O (`document_io.py`) — DONE
- [x] `load_document_state()` sets file profile and sanitizes plain buffers
- [x] `sanitize_plain_buffer()` helper
- [x] Plain-mode buffer stripping on load when control chars detected

### Editor behavior (`screens/editor.py`) — DONE
- [x] `_insert_control()` rejects formatting in plain mode with user message
- [x] `_insert_structure_marker()` rejects formatting in plain mode with user message
- [x] Status bar shows `[SFW]`/`[PLAIN]` storage mode + `[Profile Name]` highlight profile
- [x] `EditorArea` creates and maintains a `Highlighter` instance
- [x] `update_highlighter()` method for profile changes after save-as

### Syntax highlighting (`syntax_highlight.py`) — DONE
- [x] Pygments integration for code files (Python, JS, TS, JSON, TOML, YAML, INI, Markdown)
- [x] English prose highlighting with function words, punctuation, editorial markers, URLs, emails, numbers
- [x] English Markdown highlighting (Markdown structure + prose overlay)
- [x] Markdown-only highlighting (structure without English overlay)
- [x] `Highlighter` class with caching and invalidation
- [x] Rich `Text` object output compatible with Textual rendering
- [x] Editor rendering integration: syntax highlighting spans overlaid with cursor/selection

### App-level integration (`app.py`) — DONE
- [x] `_on_load_file()` sets file profile and shows `[PLAIN: Python]` or `[SFW: Safari Writer]` messages
- [x] `_do_save()` handles mode transitions (formatted → plain), updates file profile, strips buffer
- [x] `_on_save_file()` shows spec-compliant warning message for format loss
- [x] `_do_demo()` sets file profile for demo document
- [x] `_update_editor_highlighter()` notifies editor of profile changes

### Tests — DONE
- [x] `test_file_types.py` — 44 tests covering all resolution rules, properties, display names, state/IO integration
- [x] `test_syntax_highlight.py` — 20 tests covering Pygments, English, plain, SFW, caching, format guard

### Dependency and tooling — DONE
- [x] Added `pygments>=2.17.0` to project dependencies
- [x] Added `types-Pygments` to dev dependencies
- [x] All 586 tests pass, lint clean, mypy clean

---

## Remaining / Future Work

### Not yet implemented (lower priority items from spec)
- [ ] Theme compatibility: highlight colors that adapt to all Safari Writer themes (currently uses "monokai" Pygments theme)
- [ ] Configurable Pygments theme selection
- [ ] Additional language extensions (e.g., `.rs`, `.go`, `.c`, `.cpp`, `.html`, `.css`, `.sql`)
- [ ] Additional natural-language overlays beyond English (e.g., `.fr`, `.de`, `.es`)
- [ ] Rendering layer composition with full Rich `Text` objects instead of markup strings for SFW mode (currently SFW uses string markup, plain files use `Text` spans)
- [ ] Performance optimization for very large files (current approach re-highlights per-line via Pygments)

### Spec items that depend on other features
- [ ] Full English prose highlighting subsystem (spec says "there will be a whole subsystem for handling that") — current implementation covers function words, punctuation, editorial markers, URLs, emails, numbers as placeholder
- [ ] Proofreader integration with file type awareness
