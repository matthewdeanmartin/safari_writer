# Spec 07: File Formats & Print/Export

## 1. Overview

Safari Writer needs to handle two realities:

1. **Plain text files** — the user opens a `.txt` or any other file and edits it as-is. No formatting codes, no special interpretation. What's on disk is what's in the buffer.

2. **Formatted files** — the user writes a document with inline formatting (bold, underline, headers, footers, merge fields, page breaks, etc.). These formatting codes need to survive a save/load round-trip.

The original AtariWriter 80 used a proprietary binary format with embedded control bytes. We are **not** supporting that format. Instead we define our own lightweight text-based encoding for formatted documents.

---

## 2. File Extensions

| Extension | Meaning |
|-----------|---------|
| `.sfw`    | **Safari Writer Formatted** — our native format with embedded control sequences encoded as human-inspectable escape tags |
| anything else (`.txt`, `.md`, `.log`, no extension, etc.) | **Plain text** — loaded and saved verbatim, no control-code interpretation |

The extension is the sole discriminator. There is no magic-byte header or BOM.

### Behavior by extension

- **Save to `.sfw`**: control characters in the buffer are encoded to their tag form (see Section 3). The file is valid UTF-8 text.
- **Save to anything else**: control characters are **stripped** from the buffer before writing. The user gets a clean plain-text file. A warning is shown if formatting codes were present: `"Formatting codes removed (plain text save)"`.
- **Load `.sfw`**: tags are decoded back to internal control characters.
- **Load anything else**: file bytes are read as UTF-8 (with replacement for bad bytes). No tag decoding. Raw content goes straight into the buffer.

### "Save As" semantics

When the user saves, the filename prompt pre-fills the current filename. Changing the extension changes the format. If a document with formatting is saved as `.txt`, the formatting is lost on disk (though it remains in the live buffer until the next load).

---

## 3. Safari Writer Format (`.sfw`) Encoding

### Design goals

- Files must be **valid UTF-8 text**, viewable in any editor.
- Round-trip fidelity: load what you saved, byte-for-byte in the buffer.
- Human-inspectable: a user reading the `.sfw` in Notepad should see intelligible tags, not garbage control bytes.

### Tag syntax

Each internal control character is encoded as a **backslash-escaped tag**:

| Internal byte | Buffer constant  | Tag in `.sfw` file | Notes |
|---------------|------------------|---------------------|-------|
| `\x01`        | `CTRL_BOLD`      | `\B`               | Bold toggle |
| `\x02`        | `CTRL_UNDERLINE` | `\U`               | Underline toggle |
| `\x03`        | `CTRL_CENTER`    | `\C`               | Center line |
| `\x04`        | `CTRL_RIGHT`     | `\R`               | Flush right |
| `\x05`        | `CTRL_ELONGATE`  | `\G`               | Elongated toggle |
| `\x06`        | `CTRL_SUPER`     | `\^`               | Superscript toggle |
| `\x07`        | `CTRL_SUB`       | `\v`               | Subscript toggle |
| `\x10`        | `CTRL_PARA`      | `\P`               | Paragraph indent mark |
| `\x11`        | `CTRL_MERGE`     | `\@`               | Mail merge field (followed by field number) |
| `\x12`        | `CTRL_HEADER`    | `\H:`              | Header line marker |
| `\x13`        | `CTRL_FOOTER`    | `\F:`              | Footer line marker |
| `\x14`        | `CTRL_HEADING`   | `\S`               | Section heading (followed by level digit) |
| `\x15`        | `CTRL_EJECT`     | `\E`               | Hard page break |
| `\x16`        | `CTRL_CHAIN`     | `\>`               | Chain print file (followed by filename) |
| `\x17`        | `CTRL_FORM`      | `\_`               | Form printing blank |

Literal backslashes in user text are escaped as `\\`.

### Example

Buffer contents (conceptual):
```
\x12My Document Header
\x01Hello\x01 world
This is \x02underlined\x02 text.
\x15
```

Saved as `.sfw`:
```
\H:My Document Header
\BHello\B world
This is \Uunderlined\U text.
\E
```

### Encoding/decoding rules

1. **Encode** (buffer → disk): First escape all literal `\` as `\\`, then replace each control byte with its tag.
2. **Decode** (disk → buffer): Scan for `\` sequences, convert recognized tags back to control bytes, convert `\\` back to `\`. Unrecognized `\X` sequences are left as-is (forward compatibility).

---

## 4. Plain Text Mode Behavior

When working with a non-`.sfw` file:

- Formatting keybindings (Ctrl+B, Ctrl+U, etc.) **still work** and insert control characters into the buffer. The editor behaves identically.
- The status bar shows `[TXT]` instead of `[SFW]` to remind the user that formatting will be lost on save.
- On save, if the buffer contains any control characters and the filename is not `.sfw`, the user sees: `"Warning: formatting codes will be stripped. Save as .sfw to keep them. Continue? Y/N"`.
- If the user confirms, control characters are stripped and the plain text is written.
- If the user declines, they return to the filename prompt where they can change the extension.

---

## 5. Main Menu: Print Entry Point

The Main Menu already has **P**rint File. Currently it's a stub. The "P" key on the main menu opens the **Print/Export dialog** described below.

No changes needed to `MainMenuScreen` menu items — "P" is already wired to `action == "print"`. The app routes this to the new print screen.

Additionally, `Ctrl+P` in the editor should also open the same Print/Export dialog (currently shows "not yet implemented").

---

## 6. Print/Export Dialog

Print is implemented as a **modal dialog screen** (`PrintScreen`) pushed from either the main menu or the editor. It offers four output modes:

```
  *** PRINT / EXPORT ***

  [A]  ANSI Preview
  [M]  Export to Markdown (.md)
  [P]  Export to PostScript (.ps)
  [D]  Export to PDF (.pdf)

  [Esc]  Cancel
```

### 6a. ANSI Preview

Opens a full-screen **read-only preview** (`PrintPreviewScreen`) showing the document as it would appear on a printed page, rendered with ANSI/Rich formatting:

- **Bold** → terminal bold
- **Underline** → terminal underline
- **Elongated** → rendered as dim (terminal limitation, same as editor)
- **Superscript/Subscript** → rendered as bright white (same as editor)
- **Center/Right** → text aligned within the margin columns
- **Headers/Footers** → rendered at top/bottom of each page
- **Page breaks** → horizontal rule (`───`) + "Page N" indicator
- **Paragraph marks** → indentation applied
- **Mail merge fields** → shown as `<<field_name>>` placeholders (or filled if a merge DB is loaded)
- **Form blanks** → shown as `[________]`

Global format settings (margins, spacing, page length, justification) are applied to compute pagination and layout.

Navigation in preview:
- `Page Up / Page Down` — scroll by pages
- `Up / Down` — scroll by lines
- `Home / End` — jump to start/end
- `Esc` — close preview, return to editor/menu

### 6b. Export to Markdown

Converts the document to Markdown syntax:

| Safari Writer construct | Markdown output |
|------------------------|-----------------|
| Bold (`\B...\B`)       | `**...**` |
| Underline (`\U...\U`)  | `<u>...</u>` (HTML in Markdown) |
| Elongated              | `**...**` (treated as bold) |
| Superscript            | `<sup>...</sup>` |
| Subscript              | `<sub>...</sub>` |
| Center                 | `<center>...</center>` |
| Flush right            | Not representable — left as-is with a comment |
| Header line            | Rendered as text at top (not mapped to `#` headings) |
| Footer line            | Rendered as text at bottom |
| Section heading (level N) | `#` repeated N times + auto-number + heading text |
| Page break             | `---` (horizontal rule) |
| Paragraph mark         | Blank line (paragraph separator) |
| Chain file             | Ignored (comment appended) |
| Form blank             | `[________]` |
| Mail merge field       | `{{field_N}}` |

The user is prompted for an output filename (pre-filled as `<current_name>.md`). The file is written as UTF-8.

### 6c. Export to PostScript

Generates a `.ps` (PostScript) file suitable for printing or conversion to PDF via `ps2pdf` or similar tools.

The PostScript output applies full Global Format settings:

- Page dimensions derived from `page_length`
- Margins: top, bottom, left, right
- Line spacing and paragraph spacing
- Font selection based on `type_font` (mapped to PostScript base fonts: Courier for pica, Courier-Condensed or scaled for condensed, Helvetica for proportional, Courier at smaller size for elite)
- Justification (ragged right or justified)
- Bold/underline/superscript/subscript rendered with appropriate PS font changes and positioning
- Headers and footers on each page
- Page numbering (starting from `page_number_start`)
- Page breaks / ejects
- Section heading auto-numbering

The user is prompted for an output filename (pre-filled as `<current_name>.ps`).

### 6d. Export to PDF

Generates a `.pdf` file directly from Safari Writer using the same page layout rules as PostScript export:

- US Letter page size
- Global Format margins, line spacing, paragraph indent, and page numbering
- Built-in font mapping for pica, condensed, proportional, and elite
- Bold, underline, superscript, subscript, centered, and flush-right text
- Headers, footers, hard page breaks, and section heading numbering
- Mail merge expansion when a database is loaded

The user is prompted for an output filename (pre-filled as `<current_name>.pdf`).

### Mail merge at print/export time

If the document contains merge fields (`\@N`):

1. The print dialog prompts: `"Mail Merge database file? (Enter to skip)"`
2. If a database JSON is provided, the export iterates over all records (or the active subset), producing one copy per record with fields substituted.
3. If skipped, merge fields render as `<<field_N>>` placeholders.

### Form printing at export time

If the document contains form blanks (`\_`):

1. In ANSI Preview: blanks render as `[________]`.
2. In Markdown/PostScript export: same placeholder rendering.
3. **Interactive form fill** (future, not in this spec): prompt the user to type values for each blank before exporting. Deferred to Phase 12.

---

## 7. Implementation Plan

### New modules

| File | Purpose |
|------|---------|
| `safari_writer/format_codec.py` | `encode_sfw(buffer) -> str` and `decode_sfw(text) -> list[str]` plus `strip_controls(buffer) -> list[str]` |
| `safari_writer/screens/print_screen.py` | `PrintScreen` (modal menu), `PrintPreviewScreen` (ANSI paginated viewer) |
| `safari_writer/export_md.py` | `export_markdown(buffer, fmt, merge_db?) -> str` |
| `safari_writer/export_ps.py` | `export_postscript(buffer, fmt, merge_db?) -> bytes` |

### Changes to existing modules

| File | Change |
|------|--------|
| `safari_writer/app.py` | Route `"print"` action to `PrintScreen`. Update `_on_load_file` / `_on_save_file` to use codec based on extension. |
| `safari_writer/screens/editor.py` | `Ctrl+P` opens `PrintScreen` instead of showing stub message. Status bar shows `[SFW]` or `[TXT]` based on filename extension. |
| `safari_writer/state.py` | No changes needed — `filename` already stored, extension can be derived. |

### Phase ordering

1. **`format_codec.py`** — encode/decode/strip. Unit-testable in isolation.
2. **Update `app.py` load/save** — wire codec into file I/O path.
3. **`PrintScreen` dialog** — the print/export modal.
4. **ANSI Preview** — the most useful output for day-to-day use.
5. **Markdown export** — straightforward text transform.
6. **PostScript export** — most complex, requires page layout engine.

---

## 8. Out of Scope

- **Original AtariWriter binary format** — not supported. Maybe someday.
- **Direct system printing** — we export to `.ps` which can be sent to a printer externally. No `lpr` / Windows print API integration.
- **RTF / DOCX export** — not planned.
- **Interactive form fill at print time** — deferred to Phase 12.
