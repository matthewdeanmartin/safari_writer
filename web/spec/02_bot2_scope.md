# Safari Writer Web — Bot 2 Implementation Scope

## Prerequisites

Bot 1 has already delivered:
- Project scaffold (Vite + TypeScript, `web/package.json`, `web/tsconfig.json`)
- Terminal renderer (`web/src/terminal/renderer.ts`)
- Keyboard handler (`web/src/terminal/keyboard.ts`)
- State (`web/src/state.ts`)
- localStorage file layer (`web/src/storage/files.ts`)
- Format codec (`web/src/format/codec.ts`)
- App router (`web/src/app.ts`)
- Main menu, Index screen, Editor screen (full)
- Stub screens for: Global Format, Proofreader, Print

Your job is to **replace the stubs** with full implementations and add the remaining features.

---

## Step 1 — Global Format Screen

### `web/src/screens/global_format.ts`

Replace the stub. This screen edits all 14 parameters of `GlobalFormat`.

**Layout (80×25):**

```
Row 0:  ╔══════════════════════ GLOBAL FORMAT ════════════════════════╗
Row 1:  ║  Press the highlighted letter to change a value.           ║
Row 2:  ║  Enter or Esc to return to editor.                         ║
Row 3:  ║  ──────────────────────────────────────────────────────── ║
Row 4:  ║  T  Top Margin       [ 3]   lines from top                 ║
Row 5:  ║  B  Bottom Margin    [ 3]   lines from bottom              ║
Row 6:  ║  L  Left Margin      [ 5]   columns                        ║
Row 7:  ║  R  Right Margin     [75]   columns                        ║
Row 8:  ║  S  Line Spacing     [ S]   S=Single  D=Double             ║
Row 9:  ║  M  Double Column    [ N]   M=On  N=Off                    ║
Row 10: ║  G  Font             [STANDARD]                            ║
Row 11: ║  I  Paragraph Indent [ 5]   spaces                         ║
Row 12: ║  J  Justification    [ N]   J=On  N=Off                    ║
Row 13: ║  Q  Page Numbering   [ N]   Q=On  N=Off                    ║
Row 14: ║  Y  Page Length      [66]   lines per page                 ║
Row 15: ║  W  Page Wait        [ N]   W=On  N=Off                    ║
Row 16: ║                                                             ║
Row 17: ║  ──────────────────────────────────────────────────────── ║
Row 18: ║                                                             ║
Row 19: ║                                                             ║
Row 20: ║                                                             ║
Row 21: ║                                                             ║
Row 22: ║                                                             ║
Row 23: ║  Enter/Esc = Done                                           ║
Row 24: ╚════════════════════════════════════════════════════════════╝
```

**Interaction model:**
- Each parameter has a key letter (T, B, L, R, S, M, G, I, J, Q, Y, W). Highlight that letter in bright color.
- When the user presses T: the value field for Top Margin becomes editable. Show a cursor in the value field. Accept number input. Enter or Tab confirm and move to next field. Esc cancels edit.
- For boolean/enum params (S=spacing, M=double-column, J, Q, W): pressing the key letter toggles the value directly (no text input needed).
- For numeric params (T, B, L, R, I, Y): pressing the key letter activates inline editing of the number.
- For G (font): pressing G opens a mini-picker showing available font names: `STANDARD`, `DRAFT`, `BOLD`. Arrow keys select. Enter confirms.
- Enter or Esc (when not in a field edit): save changes to `state.fmt` and navigate back to editor.

**Validation:**
- Top/Bottom margin: 0–20
- Left margin: 0–40
- Right margin: 40–79
- Paragraph indent: 0–20
- Page length: 20–132

---

## Step 2 — Spellcheck / Proofreader

### `web/src/spell/checker.ts`

Wrap `nspell` for use in the editor.

**Setup:**
```ts
import nspell from 'nspell';

// Load dictionary files from /public/dict/en_US.aff and en_US.dic
// These are plain text files fetched via fetch() at startup.
export async function loadSpellChecker(): Promise<SpellChecker>;

export class SpellChecker {
  check(word: string): boolean;           // true = correct
  suggest(word: string): string[];        // up to 5 suggestions
  addWord(word: string): void;            // add to session dictionary
}
```

**Dictionary files:** Download `en_US.aff` and `en_US.dic` from the `hunspell-en-us` npm package or a public domain source. Place them in `web/public/dict/`. They will be served as static assets by Vite. Total size: ~3 MB uncompressed, ~700 KB gzipped (acceptable for a demo).

**Lazy loading:** The spell checker is only loaded when the user opens the Proofreader screen. Show a "Loading dictionary…" message during the fetch.

### `web/src/screens/proofreader.ts`

Replace the stub. Implement two modes selectable from a sub-menu:

**Sub-menu:**
```
Row 10:  ╔═══════ PROOFREADER ════════╗
Row 11:  ║  H  Highlight errors       ║
Row 12:  ║  C  Correct errors         ║
Row 13:  ║  Esc  Return to editor     ║
Row 14:  ╚════════════════════════════╝
```

#### Mode H — Highlight

- Scan the entire buffer. For each word that `checker.check(word)` returns false, render it in inverse video.
- Show a summary in the message bar: "12 possible errors found. Press any key to return."
- Return to editor on any key. The highlights are not persistent — they exist only in this rendering pass.

#### Mode C — Correct Errors

Navigate through misspelled words one at a time:

```
Row 22: [message bar] "Unknown word: 'recieve' (12 of 34 errors)"
Row 23: [status bar]  R=Replace  K=Keep  A=Add to dict  S=Skip  Esc=Done
```

Below the message bar, show up to 5 suggestions in a mini-panel:
```
Row 18:  1 receive
Row 19:  2 relieve
Row 20:  3 retrieve
Row 21:  (no more)
```

| Key | Action |
|-----|--------|
| 1–5 | Replace current word with suggestion N |
| R   | Prompt for manual replacement string, then replace |
| K   | Keep this occurrence (skip, don't add to dictionary) |
| A   | Add word to session dictionary (`checker.addWord(word)`), keep |
| S   | Skip this occurrence |
| Esc | Done — return to editor |

**Word tokenization:** Strip `\X` tags before spellchecking. Only check words that match `/[a-zA-Z']+/`. Preserve cursor position when replacing.

---

## Step 3 — Print / Export Screen

### `web/src/screens/print_screen.ts`

Replace the stub. Show a modal with export options.

**Layout:**
```
Row 8:  ╔═════════════ PRINT / EXPORT ════════════════╗
Row 9:  ║                                             ║
Row 10: ║  A  ANSI Preview (in browser)               ║
Row 11: ║  T  Plain Text   (.txt download)            ║
Row 12: ║  M  Markdown     (.md download)             ║
Row 13: ║  P  PDF          (.pdf download, jsPDF)     ║
Row 14: ║  S  PostScript   (.ps download)             ║
Row 15: ║                                             ║
Row 16: ║  Esc  Return                                ║
Row 17: ╚═════════════════════════════════════════════╝
```

#### A — ANSI Preview

Render the document as paginated text using the current `GlobalFormat` settings. Display in the terminal grid with page navigation:

- Apply left/right margins, line spacing, justification, page length.
- Render formatting tags as styled text (bold → bright color, underline → underline cell attribute, center → centered line, flush right → right-aligned line).
- Show one page at a time. Status bar shows "Page 1 of 5".
- Space / Page Down = next page. Page Up = prev page. Esc = exit preview.

#### T — Plain Text Download

- Strip all `\X` tags with `stripTags()`.
- Apply left margin (pad each line with spaces).
- Offer download as `<filename>.txt` via `downloadBlob()`.

#### M — Markdown Download

### `web/src/format/export_md.ts`

Convert the document buffer to Markdown:

| Tag | Markdown equivalent |
|-----|---------------------|
| `\B` … `\b` | `**…**` |
| `\U` … `\u` | `_…_` |
| `\E` | (center — no standard MD, use HTML `<div align="center">`) |
| `\R` | (flush right — use HTML `<div align="right">`) |
| `\H:…` | Page header comment (HTML comment `<!-- header: … -->`) |
| `\F:…` | Page footer comment |
| `\P` | `---` (page break as horizontal rule) |
| `\[` | `<sup>` |
| `\]` | `<sub>` |
| `\M` | Indent 4 spaces |

Offer download as `<filename>.md`.

#### P — PDF Download

### `web/src/format/export_pdf.ts`

Use `jsPDF` to produce a PDF. Add jsPDF to `package.json`:

```json
"jspdf": "^2.5.1"
```

**Implementation:**

```ts
import { jsPDF } from 'jspdf';

export function exportPDF(buffer: string[], fmt: GlobalFormat, filename: string): void {
  const doc = new jsPDF({ unit: 'pt', format: 'letter' });
  // Letter: 612 × 792 pt. 72 pt = 1 inch.
  // Margins from GlobalFormat (1 unit ≈ 1 line ≈ 12pt):
  const leftPt  = fmt.leftMargin * 7.2;   // rough: 1 col ≈ 7.2pt
  const rightPt = (80 - fmt.rightMargin) * 7.2;
  const topPt   = fmt.topMargin * 14;     // rough: 1 line ≈ 14pt
  const lineHt  = fmt.lineSpacing === 'D' ? 28 : 14;

  doc.setFont('Courier', 'normal');
  doc.setFontSize(12);

  let y = topPt;
  for (const rawLine of buffer) {
    const text = stripTags(rawLine);
    // Handle bold segments via jsPDF setFont('Courier', 'bold')
    // For simplicity in v1: strip tags, render plain text
    if (y + lineHt > 792 - fmt.bottomMargin * 14) {
      doc.addPage();
      y = topPt;
    }
    doc.text(text, leftPt, y);
    y += lineHt;
  }
  doc.save(filename.replace(/\.sfw$/, '.pdf'));
}
```

For v1, a plain text PDF is acceptable. Bold/underline formatting within jsPDF requires segment-by-segment rendering — implement as a stretch goal.

#### S — PostScript Download

### `web/src/format/export_ps.ts`

PostScript is a text format. Hand-roll the output:

```ts
export function exportPS(buffer: string[], fmt: GlobalFormat, filename: string): string {
  const lines: string[] = [];
  lines.push('%!PS-Adobe-3.0');
  lines.push('%%Title: ' + filename);
  lines.push('%%Pages: (atend)');
  lines.push('%%EndComments');
  lines.push('/Courier findfont 12 scalefont setfont');

  let pageNum = 1;
  let y = 720 - fmt.topMargin * 14;
  const x = fmt.leftMargin * 7.2 + 36; // 36pt = 0.5in base offset
  const lineHt = fmt.lineSpacing === 'D' ? 28 : 14;

  lines.push(`%%Page: ${pageNum} ${pageNum}`);

  for (const rawLine of buffer) {
    const text = stripTags(rawLine).replace(/[()\\]/g, '\\$&'); // escape PS special chars
    if (y < fmt.bottomMargin * 14 + 36) {
      lines.push('showpage');
      pageNum++;
      lines.push(`%%Page: ${pageNum} ${pageNum}`);
      y = 720 - fmt.topMargin * 14;
    }
    lines.push(`${x} ${y} moveto (${text}) show`);
    y -= lineHt;
  }

  lines.push('showpage');
  lines.push('%%Trailer');
  lines.push(`%%Pages: ${pageNum}`);
  lines.push('%%EOF');

  return lines.join('\n');
}
```

Offer download as `<filename>.ps`.

---

## Step 4 — ANSI Preview (in-browser pager)

Already described in Step 3 (option A). Implement as a dedicated function within `print_screen.ts` or as a separate `web/src/screens/preview_screen.ts`.

**Pagination algorithm:**
1. Apply top margin: skip `fmt.topMargin` blank lines.
2. For each buffer line, apply formatting and wrap/truncate to `rightMargin - leftMargin` cols.
3. Apply left margin padding.
4. Apply justification: if `fmt.justification` and line is not a control-code line, distribute extra spaces between words.
5. Count lines per page using `fmt.pageLength`.
6. Break into page arrays.

**Rendering on the terminal:**
- Rows 0–23: show the current page content. Lines that overflow the 25-row terminal are scrolled (the pager shows only what fits).
- Row 24: `Page N of M  Space=Next  PgUp=Prev  Esc=Exit`

---

## Step 5 — Word Count Modal

### `web/src/screens/word_count.ts`

Already wired in the editor (`alt_w`). Implement a small overlay:

```
╔══════════ WORD COUNT ══════════╗
║                                ║
║  Words:      1,234             ║
║  Lines:         87             ║
║  Characters: 6,891             ║
║                                ║
║  Press any key to continue.    ║
╚════════════════════════════════╝
```

Count words as space-separated tokens in the stripped buffer (no tags). Display centered in the terminal.

---

## Step 6 — Demo Document

### `web/src/demo.ts`

Write a real, interesting demo document in `.sfw` format. The content should:
1. Explain what Safari Writer Web is.
2. Demonstrate as many formatting features as possible inline:
   - `\B bold \b text`
   - `\U underlined \u text`
   - `\E` centered lines
   - `\R` flush-right lines
   - `\P` page break
   - `\H:Header text` on line 1
   - `\F:Page @P` on line 2
   - A section heading via `\S1 Introduction`
3. Include instructions for using the keyboard shortcuts.
4. Be about 2–3 pages of content (≈60–90 lines).

The demo is loaded on `T` from main menu (Bot 1 wires this; Bot 2 writes the actual content).

---

## Step 7 — Polish & Final Integration

### 7.1 Focus Management

- On startup and on every screen transition, call `document.body.focus()` or `canvas.focus()` and ensure `tabIndex=0` is set on the canvas so it receives keyboard events immediately.
- If the user clicks outside the canvas, refocus it automatically via a `blur` listener on `document`.

### 7.2 Scroll Clamping

In the editor:
- `viewportRow` clamps to `[0, max(0, buffer.length - 20)]`.
- `cursorRow` clamps to `[0, buffer.length - 1]`.
- `cursorCol` clamps to `[0, currentLine.length]`.

### 7.3 Status Bar Clock

In the main menu, show a clock that updates every second. In the editor, show the clock in the status bar (optional — show it only if space permits, i.e., if the filename is short).

### 7.4 Title Bar

Set `document.title` to `Safari Writer — <filename>` when a file is loaded. Reset to `Safari Writer` when no file is open.

### 7.5 Prevent Browser Shortcuts

In the `KeyboardHandler`, call `event.preventDefault()` on:
- Ctrl+F (browser find)
- Ctrl+G (Google meet shortcut)
- Ctrl+B (browser bookmark on some browsers)
- Ctrl+P (browser print)
- Ctrl+U (view source on some browsers)
- Ctrl+Z, Ctrl+X, Ctrl+C, Ctrl+V (handled by the app)
- Tab (prevent focus change)
- F1, F3, F5 (browser shortcuts)
- Backspace (browser back navigation)
- Escape (only prevent default when the app handles it)

### 7.6 localStorage Error Handling

Wrap all `localStorage` calls in try/catch. If `QuotaExceededError` is thrown:
- Show "Storage full! Delete files to free space." in the message bar.
- Do not crash the app.

### 7.7 Unsaved Changes Warning

Hook `window.beforeunload` to show the browser's native "Leave page?" dialog when `state.modified = true`.

```ts
window.addEventListener('beforeunload', (e) => {
  if (state.modified) {
    e.preventDefault();
    e.returnValue = '';
  }
});
```

---

## Deliverables Checklist for Bot 2

- [ ] `web/src/screens/global_format.ts` (full implementation, replaces stub)
- [ ] `web/src/spell/checker.ts` (nspell wrapper + lazy load)
- [ ] `web/src/screens/proofreader.ts` (full implementation: H + C modes)
- [ ] `web/src/screens/print_screen.ts` (full implementation: A/T/M/P/S options)
- [ ] `web/src/screens/preview_screen.ts` (in-browser pager with pagination)
- [ ] `web/src/format/export_md.ts`
- [ ] `web/src/format/export_pdf.ts` (jsPDF)
- [ ] `web/src/format/export_ps.ts`
- [ ] `web/src/screens/word_count.ts`
- [ ] `web/src/demo.ts` (real demo content)
- [ ] `web/public/dict/en_US.aff` and `web/public/dict/en_US.dic`
- [ ] `package.json` updated with `jspdf` dependency
- [ ] `npm run build` produces `dist/` with no TypeScript errors
- [ ] End-to-end test: create file, type text, save, spell check, export to PDF — all work

---

## Notes for Bot 2

- Read `web/src/state.ts` and `web/src/terminal/renderer.ts` from Bot 1 before writing any new screen. Match the existing API exactly.
- The spellcheck dictionary files are large (~3 MB total). Fetch them lazily, cache them in module-level variables, and never re-fetch.
- jsPDF v2 uses `doc.save(filename)` which triggers a browser download automatically.
- PostScript and Markdown are pure string generation — test them by downloading and opening in a viewer.
- The ANSI preview is the most complex part. Start with a simple version (no justification, no headers/footers) and add those features once the basic pager works.
- If Bot 1's stubs used a generic interface like `interface Screen { mount(): void; unmount(): void; }`, match that pattern for your screen implementations.
