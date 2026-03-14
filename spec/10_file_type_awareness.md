# Spec 10: File Type Awareness

## 1. Overview

Safari Writer already distinguishes `.sfw` files from everything else when loading and saving documents. This spec extends that behavior into a full **file type awareness** model that controls:

1. whether Safari Writer formatting codes are allowed in the buffer;
1. how the editor labels the current document mode; and
1. how text is colorized inside the Textual UI.

The key rule is simple:

- **`.sfw` means Safari Writer formatted text** — the buffer may contain Safari Writer control codes mixed with visible text.
- **Every other text extension means plain text** — the buffer must not contain Safari Writer formatting codes.

This spec also requires **Textual-compatible colorization** so code files such as `.py` render with syntax highlighting, while prose-oriented files such as `.en.md` and `.en.txt` receive English-aware highlighting.

______________________________________________________________________

## 2. Relationship to Existing Specs

This spec **refines and partially supersedes Spec 07**:

- Spec 07 remains the source of truth for `.sfw` encoding and print/export behavior.
- This document **replaces Spec 07 Section 4 ("Plain Text Mode Behavior")**.

The old plain-text rule said formatting commands could still insert control codes into non-`.sfw` buffers and those codes would be stripped only on save. That is no longer sufficient. Under this spec, non-`.sfw` documents are plain text **throughout the editing session**, not just on disk.

______________________________________________________________________

## 3. Design Goals

- Keep `.sfw` as the only format that preserves Safari Writer inline formatting codes.
- Make plain-text editing predictable: a `.txt`, `.md`, `.py`, `.json`, or similar file behaves like plain text all the way through load, edit, and save.
- Add syntax-aware colorization for common file types without introducing raw ANSI escape handling into the editor.
- Support prose-aware highlighting for human-language text files, starting with English (`.en.txt`, `.en.md`, and similar patterns).
- Preserve extension-driven behavior: no MIME sniffing, content sniffing, or magic-byte detection is required.

### Non-goals

- No language server integration is required by this spec.
- No automatic reformatting of source code is required.
- No spellcheck replacement is required here; Proofreader remains a separate feature.
- No binary file support is added.

______________________________________________________________________

## 4. Core Concepts

### 4.1 Storage mode

Each open document has one storage mode:

| Mode | Trigger | Safari Writer control codes allowed? |
|---|---|---|
| `formatted` | final extension is `.sfw` | Yes |
| `plain` | any other extension, or no extension | No |

### 4.2 Highlight profile

Each open document also has a highlight profile derived from the filename. Highlighting is independent from storage mode, except that `.sfw` always uses the Safari Writer formatted-text renderer as its base profile.

Examples:

| Filename | Storage mode | Highlight profile |
|---|---|---|
| `letter.sfw` | formatted | safari-writer |
| `notes.txt` | plain | plain-text |
| `outline.md` | plain | markdown |
| `script.py` | plain | python |
| `config.json` | plain | json |
| `chapter.en.txt` | plain | english-text |
| `chapter.en.md` | plain | english-markdown |

______________________________________________________________________

## 5. Filename Classification Rules

### 5.1 Storage mode resolution

Storage mode is determined solely by the final suffix:

- final suffix `.sfw` -> `formatted`
- anything else -> `plain`

Examples:

- `draft.sfw` -> formatted
- `draft.SFW` -> formatted
- `draft.txt` -> plain
- `draft.en.md` -> plain
- `README` -> plain

### 5.2 Highlight profile resolution

Highlight profile is determined by suffix pattern, using these rules in order:

1. If the final suffix is `.sfw`, use `safari-writer`.
1. Otherwise, inspect the final suffix for a base text/code type.
1. If the filename also includes a penultimate natural-language suffix such as `.en`, use that as a prose overlay when supported.

### 5.3 Base highlight types

The implementation should support at least the following initial mapping:

| Final suffix | Highlight profile |
|---|---|
| `.txt` | plain-text |
| `.md` | markdown |
| `.py` | python |
| `.js` | javascript |
| `.ts` | typescript |
| `.json` | json |
| `.toml` | toml |
| `.yaml`, `.yml` | yaml |
| `.ini`, `.cfg` | ini |
| anything else | plain-text |

This table may grow later, but unknown extensions must still open successfully and fall back to `plain-text`.

### 5.4 Natural-language overlays

Compound names may specify a natural-language overlay:

| Filename pattern | Meaning |
|---|---|
| `name.en.txt` | English prose in plain text |
| `name.en.md` | English prose in Markdown |
| `name.en.rst` | English prose in reStructuredText if supported later |

Initial required support:

- `.en.txt` -> `english-text`
- `.en.md` -> `english-markdown`

If a language overlay is unknown or unsupported, the app falls back to the base highlight profile without failing to open the file.

______________________________________________________________________

## 6. Load and Save Semantics

## 6.1 Loading `.sfw`

- Files ending in `.sfw` are decoded through the Safari Writer format codec.
- Safari Writer control tags become internal control characters in the buffer.
- The editor enters `formatted` mode.

## 6.2 Loading non-`.sfw`

- Non-`.sfw` files are read as plain UTF-8 text with replacement for invalid bytes, consistent with current text loading behavior.
- No Safari Writer tag decoding is performed.
- The editor enters `plain` mode.
- The in-memory buffer for a plain document must not contain Safari Writer control characters as active formatting markers.

If a non-`.sfw` import path somehow yields Safari Writer control characters in the buffer, the implementation must sanitize them before editing continues and surface a visible message explaining that plain-text files cannot carry Safari Writer formatting codes.

## 6.3 Saving `.sfw`

- Saving to `.sfw` encodes the buffer with the Safari Writer codec.
- Safari Writer control characters are preserved.
- The document remains in `formatted` mode after save.

## 6.4 Saving non-`.sfw`

- Saving to any non-`.sfw` filename writes plain UTF-8 text.
- The written file must not contain Safari Writer control characters.
- After a successful save to a non-`.sfw` filename, the live document state also becomes `plain`.

This last rule is important: a Save As from `draft.sfw` to `draft.txt` is not just an export. It is a mode transition. Once the user confirms the plain-text save, the working buffer is normalized to plain text so the editor and the file on disk stay consistent.

## 6.5 Save As confirmation

If the current buffer contains Safari Writer formatting and the user saves to a non-`.sfw` filename:

1. the app must warn that Safari Writer formatting will be removed;
1. the user may cancel and choose a `.sfw` filename instead; and
1. if the user confirms, formatting controls are removed from both the saved output and the live buffer.

Recommended message:

```text
Safari Writer formatting is only preserved in .sfw files.
Saving as plain text will remove formatting codes. Continue?
```

______________________________________________________________________

## 7. Editor Behavior by Storage Mode

## 7.1 Formatted mode (`.sfw`)

- Existing Safari Writer formatting commands remain available.
- The buffer may contain inline control markers.
- The editor continues to render visible glyphs for Safari Writer markers and styled text spans.

## 7.2 Plain mode (all non-`.sfw`)

- Safari Writer formatting commands must not insert control codes.
- Commands such as Bold, Underline, Header, Footer, Section Heading, Page Eject, Chain File, Mail Merge marker, and Form Blank must either:
  - be disabled, or
  - show a status message such as `"Formatting is only available in .sfw files"`.

The preferred behavior is to keep the keybindings but reject the action with a clear message, because that teaches the user why nothing changed.

### Plain-mode invariants

For a plain-mode document:

- the buffer contains only user text plus normal line breaks;
- no hidden Safari Writer formatting state may exist in memory;
- cut/copy/paste within the editor must not introduce Safari Writer control characters; and
- loading, editing, and saving the file must preserve its identity as a plain-text document.

______________________________________________________________________

## 8. Status Bar and User Feedback

The editor should expose both storage mode and highlight profile.

Recommended status format:

```text
Bytes Free: 12,345   [Insert]   [Lowercase]   [PLAIN]   [Python]
```

or:

```text
Bytes Free: 12,345   [Insert]   [Lowercase]   [SFW]   [Safari Writer]
```

Minimum required behavior:

- storage mode must remain visible at all times;
- highlight profile must be visible somewhere in the editor chrome or message area; and
- mode transitions caused by Save As must be announced explicitly.

Examples:

- `"Loaded [PLAIN: Python]: C:\\work\\script.py"`
- `"Loaded [PLAIN: English Markdown]: C:\\docs\\chapter.en.md"`
- `"Saved [SFW]: C:\\docs\\letter.sfw"`
- `"Converted document to plain text mode: C:\\docs\\letter.txt"`

______________________________________________________________________

## 9. Textual-Compatible Colorization

All editor colorization must be implemented in a **Textual-compatible** way.

### 9.1 Required rendering model

The implementation must use Textual/Rich renderables and styles, such as:

- `rich.text.Text`
- Rich `Span` / `Style`
- Textual-compatible syntax token styling
- `rich.syntax.Syntax` or an equivalent token-to-style pipeline when it can be embedded cleanly

The editor must **not** depend on raw ANSI escape sequences embedded in the document text for normal editing display.

### 9.2 Layering rules

The rendered line should support these visual layers:

1. base text content
1. file-type syntax highlighting
1. Safari Writer formatting visualization (formatted mode only)
1. selection highlighting
1. cursor highlighting

Cursor and selection styling must remain legible even when syntax highlighting is active.

### 9.3 Theme compatibility

Highlight colors must respect the current Textual theme or style palette rather than hard-coding terminal-specific ANSI assumptions. The same file should remain readable under all built-in Safari Writer themes.

______________________________________________________________________

## 10. Highlighting Requirements by File Type

## 10.1 Code and data files

When a plain document opens with a recognized programming/data extension, the editor should apply a matching syntax highlighter:

- `.py` -> Python
- `.js` -> JavaScript
- `.ts` -> TypeScript
- `.json` -> JSON
- `.toml` -> TOML
- `.yaml` / `.yml` -> YAML
- `.ini` / `.cfg` -> INI-style configuration
- `.md` -> Markdown structure highlighting

The goal is not full IDE behavior. The requirement is readable, pleasant, syntax-aware colorization suitable for reviewing and lightly editing source files in the Textual UI.

## 10.2 English prose files

English-aware highlighting is required for:

- `.en.txt`
- `.en.md`

This is **prose highlighting**, not programming-language lexing.

### English prose highlighting should emphasize:

- headings and section titles;
- Markdown structure when the base type is Markdown;
- list bullets and numbered list markers;
- block quote prefixes;
- links, URLs, and email addresses;
- emphasized spans already expressed with Markdown punctuation;
- numbers, dates, and other literal-like inline tokens; and
- editorial markers such as `TODO`, `NOTE`, `WARNING`, and `FIXME`.

### English Markdown behavior

For `.en.md`:

- Markdown structure is highlighted first;
- prose spans outside code fences and inline code receive English-aware highlighting; and
- fenced code blocks continue to use code-style highlighting where the Markdown renderer can infer a language.

### English plain-text behavior

For `.en.txt`:

- no Markdown-only structures are required;
- prose tokens such as URLs, email addresses, dates, and editorial markers should still be highlighted; and
- normal sentence text must remain readable without turning the screen into a rainbow of low-value token classes.

______________________________________________________________________

## 11. Behavior for `.sfw` Rendering

`.sfw` documents are not treated as source-code files. Their primary renderer is Safari Writer's own formatting visualization:

- control markers remain visible as Safari Writer glyphs in the editor;
- toggled spans still display bold/underline/elongate/super/sub formatting cues; and
- syntax highlighting from unrelated code lexers is not required for `.sfw` in the initial version.

This keeps the mental model clear: `.sfw` is a formatted writing format, not a generic syntax-highlighted container format.

Future work may add optional content-type metadata inside `.sfw`, but that is outside the scope of this spec.

______________________________________________________________________

## 12. Suggested Implementation Shape

This is a behavior spec, not an implementation mandate, but the current codebase suggests the following split:

| Area | Suggested change |
|---|---|
| `format_codec.py` | Keep `.sfw` encode/decode behavior focused on formatted files only |
| `document_io.py` | Resolve file profile on load/save and normalize buffers during mode transitions |
| `state.py` | Add explicit file-type metadata (storage mode, highlight profile, display label) to `AppState` |
| `screens/editor.py` | Replace markup-string-only rendering with Textual-compatible styled renderables that can combine syntax highlighting and Safari Writer markers |
| new helper module such as `file_types.py` | Centralize suffix parsing and file-profile resolution |

Recommended helper:

```python
resolve_file_profile(path: Path) -> FileProfile
```

Where `FileProfile` contains at least:

- `storage_mode`
- `highlight_profile`
- `display_name`
- `allows_formatting_codes`

______________________________________________________________________

## 13. Acceptance Criteria

The feature is complete when all of the following are true:

1. Opening `notes.sfw` enables Safari Writer formatting behavior and shows Safari Writer formatting markers.
1. Opening `notes.txt` disables Safari Writer formatting insertion and treats the file as plain text for the whole session.
1. Opening `script.py` shows Python-oriented syntax highlighting in the editor.
1. Opening `chapter.en.md` shows Markdown structure highlighting plus English prose highlighting outside code spans.
1. Opening `chapter.en.txt` shows English prose highlighting without enabling Safari Writer formatting.
1. Saving a formatted `.sfw` document as `.txt` warns the user and, if confirmed, converts the live document into plain mode.
1. Editor rendering uses Textual/Rich-compatible styling rather than raw ANSI escape sequences for normal editing display.

______________________________________________________________________

## 14. Test Scenarios

At minimum, automated tests should cover:

- file profile resolution for `.sfw`, `.txt`, `.md`, `.py`, `.en.txt`, and `.en.md`;
- save/load transitions between formatted and plain modes;
- rejection of formatting insertion in plain mode;
- status text or UI labels that reflect both storage mode and highlight profile; and
- rendering-layer behavior where syntax highlighting coexists with selection and cursor styling.
