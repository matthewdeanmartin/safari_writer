# Safari Writer Web — Bot 1 Implementation Scope

## Your Job

Build the **scaffold, terminal renderer, state, main menu, and editor** for Safari Writer Web. When you are done, a user can:

1. Open `index.html` in a browser (via `npm run dev` or the built `dist/`)
2. See the main menu
3. Create/load/save/delete files in localStorage
4. Edit documents with full keyboard navigation, inline formatting, block operations, and search/replace
5. Navigate to Global Format screen (stub it — show "Coming in Bot 2" and return on Escape)
6. Navigate to Proofreader and Print (stub them the same way)

Bot 2 will fill in Global Format, Proofreader, and Print/Export.

---

## Step 1 — Project Scaffold

### `web/package.json`

```json
{
  "name": "safari-writer-web",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "nspell": "^2.1.5"
  },
  "devDependencies": {
    "typescript": "^5.4.5",
    "vite": "^5.2.11"
  }
}
```

### `web/tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "exactOptionalPropertyTypes": true,
    "lib": ["ES2022", "DOM"],
    "outDir": "dist",
    "rootDir": "src",
    "sourceMap": true
  },
  "include": ["src"]
}
```

### `web/vite.config.ts`

```ts
import { defineConfig } from 'vite';

export default defineConfig({
  root: '.',
  publicDir: 'public',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
});
```

### `web/index.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Safari Writer</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body { width: 100%; height: 100%; background: #000; display: flex; align-items: center; justify-content: center; overflow: hidden; }
    #app { display: flex; flex-direction: column; align-items: center; justify-content: center; }
    canvas#terminal { display: block; image-rendering: pixelated; cursor: none; }
  </style>
</head>
<body>
  <div id="app">
    <canvas id="terminal"></canvas>
  </div>
  <script type="module" src="/src/main.ts"></script>
</body>
</html>
```

---

## Step 2 — Terminal Renderer

### `web/src/terminal/colors.ts`

Define the color palette. Use a "phosphor green on black" theme with inverse video support.

```ts
export const COLORS = {
  bg:      '#0a0a0a',   // near-black background
  fg:      '#33ff33',   // phosphor green foreground
  dim:     '#1a7a1a',   // dimmer green for inactive
  bright:  '#66ff66',   // bright green for highlights/bold
  inverse_bg: '#33ff33',
  inverse_fg: '#000000',
  cursor:  '#33ff33',
  status_bg: '#33ff33',
  status_fg: '#000000',
} as const;
```

Optionally expose a `setTheme('green' | 'amber' | 'white')` for future use.

### `web/src/terminal/renderer.ts`

The renderer owns the `<canvas id="terminal">` element and exposes a simple cell-based API.

**Cell model:**

```ts
export interface Cell {
  char: string;      // single character (or space)
  fg: string;        // CSS color
  bg: string;        // CSS color
  bold?: boolean;
  underline?: boolean;
  blink?: boolean;   // optional, low priority
}
```

**Public API:**

```ts
class TerminalRenderer {
  readonly cols = 80;
  readonly rows = 25;

  // Write a single cell. Row and col are 0-based.
  setCell(row: number, col: number, cell: Cell): void;

  // Write a string of cells with the same attributes starting at (row, col).
  writeString(row: number, col: number, text: string, fg: string, bg: string, bold?: boolean): void;

  // Fill a row with spaces (clear it).
  clearRow(row: number, bg?: string): void;

  // Clear entire screen.
  clearScreen(bg?: string): void;

  // Draw cursor at (row, col). Pass null to hide cursor.
  setCursor(row: number | null, col: number | null): void;

  // Flush all pending changes to canvas. Call once per frame.
  flush(): void;
}
```

**Implementation notes:**
- Allocate a `Cell[][]` grid (25 rows × 80 cols) and a matching "dirty" boolean grid.
- `flush()` iterates dirty cells and repaints only those (use `ctx.fillRect` + `ctx.fillText`).
- Cell width = canvas.width / 80; cell height = canvas.height / 25.
- Resize the canvas in the constructor to be the largest multiple of 80×25 that fits the viewport while maintaining the correct aspect ratio (80:25 = 3.2:1). A good starting size is 960×300 (12px × 12px cells).
- On `window.resize`, recalculate and redraw everything.
- Font: `"12px 'Courier New', monospace"` initially. If an Atari font is loaded, switch to it.
- The cursor blinks: use `setInterval(500ms)` to toggle cursor visibility and call `flush()`.

---

## Step 3 — Keyboard Handler

### `web/src/terminal/keyboard.ts`

Convert raw DOM `KeyboardEvent` into normalized action names. The editor and other screens register a handler; only one handler is active at a time.

```ts
export type KeyAction =
  // Navigation
  | 'arrow_up' | 'arrow_down' | 'arrow_left' | 'arrow_right'
  | 'ctrl_left' | 'ctrl_right' | 'ctrl_up' | 'ctrl_down'
  | 'home' | 'end' | 'ctrl_home' | 'ctrl_end'
  | 'page_up' | 'page_down'
  | 'shift_arrow_up' | 'shift_arrow_down' | 'shift_arrow_left' | 'shift_arrow_right'
  // Editing
  | 'insert' | 'delete' | 'backspace' | 'tab' | 'enter'
  | 'shift_delete'          // delete to end of line
  | 'ctrl_shift_delete'     // delete to end of file
  | 'ctrl_z'                // undo
  // Block ops
  | 'ctrl_x' | 'ctrl_c' | 'ctrl_v'
  | 'alt_w'                 // word count
  | 'alt_a'                 // alphabetize
  // Search
  | 'ctrl_f'                // find
  | 'f3'                    // find next
  | 'alt_h'                 // set replace string
  | 'alt_n'                 // replace current + find next
  | 'alt_r'                 // global replace
  // Formatting
  | 'ctrl_b'                // bold
  | 'ctrl_u'                // underline
  | 'ctrl_g'                // elongated
  | 'ctrl_bracket_left'     // superscript
  | 'ctrl_bracket_right'    // subscript
  | 'ctrl_e'                // center
  | 'ctrl_r'                // flush right
  | 'ctrl_m'                // paragraph indent
  | 'ctrl_t'                // toggle tab stop
  | 'ctrl_shift_t'          // clear all tab stops
  // Document structure
  | 'ctrl_shift_h'          // header
  | 'ctrl_shift_f'          // footer
  | 'ctrl_shift_s'          // section heading
  | 'ctrl_shift_e'          // page break
  // App
  | 'ctrl_p'                // print
  | 'f1'                    // help
  | 'f5'                    // (unused in web, stub)
  | 'escape'
  | 'shift_f3'              // toggle case
  // Catch-all for printable characters
  | { type: 'char'; char: string };

export class KeyboardHandler {
  private handler: ((action: KeyAction) => void) | null = null;

  mount(element: HTMLElement): void; // attach keydown listener
  unmount(): void;
  setHandler(fn: (action: KeyAction) => void): void;
  clearHandler(): void;
}
```

**Implementation notes:**
- Call `event.preventDefault()` for all keys that have mapped actions.
- For printable chars (letters, digits, symbols, space), emit `{ type: 'char', char: event.key }`.
- For modifier combos not in the list, ignore or pass through.

---

## Step 4 — State

### `web/src/state.ts`

```ts
export interface GlobalFormat {
  topMargin: number;        // T: lines, default 3
  bottomMargin: number;     // B: lines, default 3
  leftMargin: number;       // L: columns, default 5
  rightMargin: number;      // R: columns, default 75
  lineSpacing: 'S' | 'D';  // S=single, D=double, default S
  doubleColumn: boolean;    // M/N, default false
  font: string;             // G: font name, default 'STANDARD'
  paragraphIndent: number;  // I: spaces, default 5
  justification: boolean;   // J: true=on, default false
  pageNumbering: boolean;   // Q: true=on, default false
  pageLength: number;       // Y: lines, default 66
  pageWait: boolean;        // W: pause between pages, default false
}

export function defaultGlobalFormat(): GlobalFormat { ... }

export interface AppState {
  buffer: string[];               // document lines (with \X tags in .sfw mode)
  cursorRow: number;
  cursorCol: number;
  insertMode: boolean;            // true = insert, false = typeOver
  capsMode: boolean;
  clipboard: string;
  lastDeletedLine: string;
  fmt: GlobalFormat;
  filename: string | null;        // null = untitled
  modified: boolean;
  fileProfile: 'sfw' | 'txt';    // controls whether formatting codes are active
  selectionAnchor: [number, number] | null;
  searchString: string;
  replaceString: string;
  lastSearchRow: number;
  lastSearchCol: number;
  tabStops: boolean[];            // length 80, true = tab stop at that column
  undoStack: string[][];          // up to 50 snapshots (each is a copy of buffer)
  keptSpellings: Set<string>;     // session-kept spellings
}

export function defaultAppState(): AppState { ... }
```

---

## Step 5 — localStorage File Layer

### `web/src/storage/files.ts`

```ts
export interface FileEntry {
  name: string;       // filename with extension (.sfw or .txt)
  content: string;    // raw file content (UTF-8 string)
  savedAt: string;    // ISO timestamp
}

// Returns list of all file names sorted alphabetically
export function listFiles(): string[];

// Load a file by name. Returns null if not found.
export function loadFile(name: string): FileEntry | null;

// Save a file. Overwrites if name already exists.
export function saveFile(name: string, content: string): void;

// Delete a file by name.
export function deleteFile(name: string): void;

// Export a file to the user's downloads via <a download>
export function downloadBlob(filename: string, content: string, mimeType: string): void;
```

**Implementation notes:**
- Storage key pattern: `safari_writer:file:<name>`
- Index key: `safari_writer:index` — JSON array of names (keep sorted)
- Prefer reading the index and then fetching individual keys.
- Max recommended storage: no artificial limit in v1, but warn if `localStorage` throws `QuotaExceededError`.

---

## Step 6 — Format Codec

### `web/src/format/codec.ts`

The `.sfw` format stores inline control codes as backslash-escaped tags. The editor buffer stores the raw tags. The renderer translates tags to display glyphs.

```ts
// Tag → display glyph mapping (same as Python version)
export const TAG_GLYPHS: Record<string, string> = {
  '\\B':  '←',   // bold on
  '\\b':  '←',   // bold off (same glyph, toggled)
  '\\U':  '▄',   // underline
  '\\u':  '▄',
  '\\G':  'E',   // elongated
  '\\g':  'E',
  '\\[':  '↑',   // superscript
  '\\]':  '↓',   // subscript
  '\\E':  '↔',   // center
  '\\R':  '→→',  // flush right
  '\\M':  '¶',   // paragraph indent
  '\\H:': 'H:',  // header (followed by text)
  '\\F:': 'F:',  // footer
  '\\P':  '↡',   // page break
  '\\C':  '»',   // chain print
  '\\_':  '_',   // form blank
};

// Insert a tag at a position in a line string.
// Returns the new line string.
export function insertTag(line: string, col: number, tag: string): string;

// Strip all \X tags from a string (for plain text export).
export function stripTags(text: string): string;

// Parse a line into segments: { text: string; tags: string[] }[]
// Used by the renderer to apply per-character formatting.
export function parseLineSegments(line: string): Segment[];

// Encode the entire buffer to .sfw file content (join lines with \n).
export function encodeBuffer(buffer: string[]): string;

// Decode .sfw file content into buffer lines.
export function decodeBuffer(content: string): string[];
```

---

## Step 7 — Main Menu Screen

### `web/src/screens/main_menu.ts`

**Layout (80 columns × 25 rows):**

```
Row 0:  ┌──────────────────── SAFARI WRITER ─────────────────────────┐
Row 1:  │                                                              │
Row 2:  │    WORDS               FILES              TOOLS             │
Row 3:  │    ─────               ─────              ─────             │
Row 4:  │    C Create File       1 Index Storage    T Try Demo        │
Row 5:  │    E Edit File         2 Index Storage    ? Doctor          │
Row 6:  │    V Verify Spelling                                         │
Row 7:  │    P Print/Export                                            │
Row 8:  │    G Global Format                                           │
Row 9:  │                                                              │
Row 10: │    Q Quit (close tab)                                        │
...
Row 22: │                                                              │
Row 23: │  [filename]  [profile]   Safari Writer 0.1.0 Web            │
Row 24: └──────────────────────────────────────────────────────────────┘
```

Highlight the first letter of each action (the key to press) in `COLORS.bright`.

The "1 Index Storage" and "2 Index Storage" items both open the same `IndexScreen` (they're the same localStorage — there's no "external drive"). Show the same list for both.

**Keyboard handling in main menu:**

| Key | Action |
|-----|--------|
| C   | New document → open Editor |
| E   | Load file prompt → IndexScreen → Editor |
| V   | Open Proofreader (stub in Bot 1) |
| P   | Open Print screen (stub in Bot 1) |
| G   | Open Global Format (stub in Bot 1) |
| 1   | Open IndexScreen (show file list, then load → Editor) |
| 2   | Same as 1 |
| T   | Load demo document → Editor |
| ?   | Show Doctor screen (simple diagnostic modal) |
| Q   | Alert "Close this browser tab to quit." |

**Status row (row 23):**
- Left: current filename or `[No File]`
- Center: profile `[SFW]` or `[TXT]`
- Right: `Safari Writer Web`

**Clock:** Show current time HH:MM in row 23 far right. Update every second.

---

## Step 8 — Index Screen (File List)

### `web/src/screens/index_screen.ts`

This is the file browser backed by localStorage. Displays a list of saved files with old-school formatting.

**Layout:**

```
Row 0:  ╔══════════════════════════════════════════════════════════════╗
Row 1:  ║  INDEX — SAFARI WRITER STORAGE                              ║
Row 2:  ║  ──────────────────────────────────────────────────────────  ║
Row 3:  ║  #   FILENAME                   SIZE     SAVED              ║
Row 4:  ║  ─   ────────                   ────     ─────              ║
Row 5+: ║  1   hello_world.sfw             1.2 KB   2024-01-15 14:32  ║
...
Row 22: ║  [no more files]                                             ║
Row 23: ║  Enter=Load  D=Delete  N=New  Esc=Back                      ║
Row 24: ╚══════════════════════════════════════════════════════════════╝
```

- Cursor: highlight selected row in inverse video.
- Up/Down: move cursor. Enter: load selected file.
- D: prompt "Delete <name>? Y/N" → delete on Y.
- N: prompt for new filename → create blank → open Editor.
- Esc: return to main menu without loading.
- If no files exist: show "No files saved yet. Press N to create one."

---

## Step 9 — Editor Screen

### `web/src/screens/editor.ts`

This is the core of the app. The editor renders the document buffer onto the terminal grid and handles all editing keys.

### 9.1 Layout (25 rows × 80 cols)

```
Row 0:   Tab bar — 80 chars, downward arrows (▼) at each tab stop, dots otherwise
Row 1–20: Editor area — 20 visible lines of document text
Row 21:   (spacer / empty)
Row 22:   Message bar — prompts, errors, one line
Row 23:   Status bar — [INSERT] [CAPS] [SFW] [filename] [row:col] [words]
Row 24:   Help bar — quick reference shortcuts
```

### 9.2 Tab Bar (row 0)

80-character string. At each column where `state.tabStops[col]` is true, show `▼` (bright). Elsewhere show `·` (dim).

### 9.3 Editor Area (rows 1–20)

**Viewport:** Show 20 lines of the buffer starting at `viewportRow`. Scroll so the cursor is always visible.

**Rendering each line:**
- For `.sfw` files: parse `\X` tags and render the tag glyphs in a dim color with the text in normal color. Tags occupy one display column each (except `\R→→` which is 2).
- For `.txt` files: render the raw text with no tag interpretation.
- Selection: rows/cols within the selection range render in inverse video.

**Cursor:** Blinking block or underline at `cursorRow - viewportRow + 1`, `cursorCol`.

**Word wrap:** No automatic word wrap. Lines scroll horizontally if they exceed 80 chars. Show a horizontal scroll indicator in the status bar if needed. (For v1, simply truncate display at col 79 — keep it simple.)

### 9.4 Status Bar (row 23)

```
[INSERT]  [CAPS]  [SFW]  hello_world.sfw  42:15  312 words
```

Show `[TYPE-OVR]` when `insertMode = false`. Dim `[CAPS]` when caps lock is off.

### 9.5 Help Bar (row 24)

Fixed string: `Ctrl+F=Find  F3=Next  Ctrl+B=Bold  Ctrl+U=Undln  Ctrl+P=Print  Esc=Menu`

### 9.6 Message Bar (row 22)

Used for prompts (find, replace, filename entry) and transient status messages (cleared after 3 seconds). Show a blinking cursor in the message bar when accepting text input.

### 9.7 All Key Bindings

Implement all of these. Reference the `KeyAction` type from Step 3.

#### Navigation

| Action | Effect |
|--------|--------|
| arrow_up / arrow_down | Move cursor row, clamp to buffer bounds, clear selection |
| arrow_left / arrow_right | Move cursor col, wrap to prev/next line at edges, clear selection |
| ctrl_left / ctrl_right | Jump to start/end of current word |
| home / end | Move to col 0 / end of current line |
| ctrl_home / ctrl_end | Move to (0,0) / last line, last col |
| page_up / page_down | Scroll viewport by 20 rows, move cursor with it |
| shift_arrow_* | Move cursor and extend selection from anchor |
| tab | Jump to next tab stop (or insert spaces to next stop in insert mode) |

#### Editing

| Action | Effect |
|--------|--------|
| char | If insert mode: insert character at cursor, advance cursor. If typeOver: overwrite character at cursor. Respect caps mode. Set `modified = true`. Push undo snapshot if last action was not also a char (debounce: push every ~20 chars or on every non-char action). |
| enter | Insert newline (split line at cursor). Push undo snapshot. |
| backspace | Delete char before cursor (or join with prev line if at col 0). Delete selection if any. |
| delete | Delete char at cursor (or join with next line if at end). Delete selection if any. |
| shift_delete | Delete from cursor to end of line. |
| ctrl_shift_delete | Delete from cursor to end of file. |
| insert | Toggle `state.insertMode`. |
| shift_f3 | Toggle case of char at cursor (upper→lower→upper). |
| ctrl_z | Pop undo stack and restore. |

#### Block Operations

| Action | Effect |
|--------|--------|
| ctrl_x | Cut selection to clipboard. Delete selection from buffer. |
| ctrl_c | Copy selection to clipboard. |
| ctrl_v | Paste clipboard at cursor. If selection, replace it first. |
| alt_w | Show word count modal (words, lines, chars). Dismiss on any key. |
| alt_a | Sort selected lines alphabetically (case-insensitive). |

#### Search & Replace

| Action | Effect |
|--------|--------|
| ctrl_f | Prompt in message bar: "Find: ". Accept string input, then find first occurrence from cursor. Highlight match. |
| f3 | Find next occurrence of `state.searchString`. Wrap around. |
| alt_h | Prompt in message bar: "Replace with: ". Store in `state.replaceString`. |
| alt_n | Replace current match (at `lastSearchRow/Col`), then find next. |
| alt_r | Global replace: replace all occurrences from cursor to end of file. Show count. |

**Search implementation:** Case-insensitive string search across joined buffer lines. Track `lastSearchRow` / `lastSearchCol`. Wrap from end back to start with a "Wrapped" message.

#### Inline Formatting (`.sfw` mode only — no-op for `.txt` files)

| Action | Tag pair | Glyph |
|--------|----------|-------|
| ctrl_b | `\B` … `\b` | `←` |
| ctrl_u | `\U` … `\u` | `▄` |
| ctrl_g | `\G` … `\g` | `E` |
| ctrl_bracket_left | `\[` | `↑` |
| ctrl_bracket_right | `\]` | `↓` |
| ctrl_e | `\E` | `↔` (inserts at line start, replaces existing alignment tag) |
| ctrl_r | `\R` | `→→` (inserts at line start) |
| ctrl_m | `\M` | `¶` (inserts at cursor) |
| ctrl_shift_h | `\H:` | prefix line with `H:` glyph |
| ctrl_shift_f | `\F:` | prefix line with `F:` glyph |
| ctrl_shift_e | `\P` | insert `↡` glyph (page break) on its own line |

**Toggle logic for paired tags:** If cursor is inside a formatted region (between `\B` and `\b`), remove both tags. If not, insert `\B` at cursor and `\b` at end of word (or selection end). For simplicity in v1, insert the open tag at cursor and the close tag at the next space or end of word.

#### Tab Stops

| Action | Effect |
|--------|--------|
| ctrl_t | Toggle tab stop at current cursor column (`state.tabStops[cursorCol]`). |
| ctrl_shift_t | Clear all tab stops (`state.tabStops.fill(false)`). |

#### File Operations (invoke File Ops helpers)

| Key | Effect |
|-----|--------|
| escape | If `state.modified`, prompt "Save changes? Y/N/C". On Y: save then return to main menu. On N: return to main menu. On C: cancel (stay in editor). Otherwise return to main menu. |
| ctrl_s (bonus) | Save current file (prompt for name if untitled). |

### 9.8 File Operations Modal

When saving or loading, show a simple inline modal using the message bar and a few rows of the editor area:

**Save As:** Prompt in message bar: "Save as: " + text input. Accept `.sfw` or `.txt` extension. Auto-append `.sfw` if no extension given and `fileProfile = 'sfw'`.

**Load (from Index screen):** Select file from `IndexScreen`, then `loadFile(name)`, decode buffer, set state, open editor.

**New:** Confirm if modified. Reset state to defaults, `filename = null`, `buffer = ['']`.

---

## Step 10 — App Router

### `web/src/app.ts`

```ts
type Screen = 'main_menu' | 'editor' | 'index' | 'global_format' | 'proofreader' | 'print' | 'doctor';

class App {
  private screen: Screen = 'main_menu';
  private state: AppState;
  private renderer: TerminalRenderer;
  private keyboard: KeyboardHandler;

  navigate(screen: Screen): void;
  getState(): AppState;
  setState(patch: Partial<AppState>): void;
}
```

The `App` class instantiates `TerminalRenderer` and `KeyboardHandler` once. Each screen object receives a reference to the `App` (for navigation and state), `TerminalRenderer` (for drawing), and `KeyboardHandler` (to register its key handler).

### `web/src/main.ts`

```ts
import { App } from './app';

const app = new App(
  document.getElementById('terminal') as HTMLCanvasElement
);
app.start(); // navigate to main_menu
```

---

## Step 11 — Stub Screens

### `web/src/screens/stub_screen.ts`

A reusable stub for screens Bot 2 will implement:

```ts
export function stubScreen(renderer: TerminalRenderer, title: string, onEscape: () => void): void {
  renderer.clearScreen();
  renderer.writeString(12, 20, `[ ${title} ]`, COLORS.bright, COLORS.bg);
  renderer.writeString(13, 20, 'Coming soon. Press Esc to return.', COLORS.fg, COLORS.bg);
  renderer.flush();
  // Set keyboard handler to call onEscape on 'escape' action
}
```

---

## Step 12 — Doctor Screen

### `web/src/screens/doctor.ts`

Simple diagnostic overlay. Show:

```
┌─────────── Doctor ─────────────┐
│ Platform:  Browser / Web       │
│ Storage:   localStorage        │
│ Files:     3 saved             │
│ Storage used: 12.4 KB          │
│ User agent: Chrome 124         │
│                                │
│ Press any key to return.       │
└────────────────────────────────┘
```

---

## Step 13 — Demo Document

### `web/src/demo.ts`

Export a constant `DEMO_SFW_CONTENT: string` — a hardcoded `.sfw` format string that demonstrates:
- Bold, underline, center, flush right
- Tab stops
- Section headings
- A page break
- Multiple paragraphs of descriptive text explaining the app

Write this as a multi-line template string. The demo is loaded when the user presses **T** from the main menu.

---

## Deliverables Checklist for Bot 1

- [ ] `web/package.json`, `web/tsconfig.json`, `web/vite.config.ts`, `web/index.html`
- [ ] `web/src/terminal/colors.ts`
- [ ] `web/src/terminal/renderer.ts` (canvas-based, 80×25, dirty-cell redraw)
- [ ] `web/src/terminal/keyboard.ts` (KeyboardHandler + KeyAction union type)
- [ ] `web/src/state.ts` (AppState + GlobalFormat + defaults)
- [ ] `web/src/storage/files.ts` (localStorage CRUD)
- [ ] `web/src/format/codec.ts` (tag ↔ glyph, encode/decode)
- [ ] `web/src/app.ts` (App router)
- [ ] `web/src/main.ts` (entry point)
- [ ] `web/src/screens/main_menu.ts`
- [ ] `web/src/screens/index_screen.ts`
- [ ] `web/src/screens/editor.ts` (full implementation)
- [ ] `web/src/screens/stub_screen.ts`
- [ ] `web/src/screens/doctor.ts`
- [ ] `web/src/demo.ts`
- [ ] `npm run dev` works and shows the main menu
- [ ] `npm run build` produces `dist/` with no TypeScript errors

## Notes for Bot 1

- Keep it all client-side. No fetch() to any server. No external CDN dependencies.
- The canvas approach means zero CSS complexity — own the pixels.
- Use `requestAnimationFrame` for the main render loop if you implement one, but the dirty-cell approach with explicit `flush()` calls is also fine.
- All keyboard input goes through `KeyboardHandler.setHandler()`. Never attach `addEventListener` directly in screen files.
- Prefer composition over inheritance. Each screen is a plain object/class that calls renderer methods and registers a keyboard handler.
- When in doubt, keep it simple. This is a retro word processor, not a modern web app.
