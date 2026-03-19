# Safari Writer Web — UX Reference

## Terminal Grid

- **Dimensions:** 80 columns × 25 rows (fixed, never scrolls as a whole)
- **Cell size:** Implementation-defined, but aim for 12px wide × 18px tall (monospace)
- **Canvas size:** 960px × 450px at 1× pixel density; scale for device pixel ratio
- **Font:** Courier New (system) initially. If Atari ST or Atari 8-bit font is bundled, use it.

## Color Palette (Phosphor Green Theme)

| Name | Hex | Use |
|------|-----|-----|
| Background | `#0a0a0a` | Screen background |
| Foreground | `#33ff33` | Normal text |
| Dim | `#1a7a1a` | Inactive elements, dots in tab bar |
| Bright | `#66ff66` | Highlighted letters, cursor, menu keys |
| Inverse BG | `#33ff33` | Inverse video background (selection, status bar) |
| Inverse FG | `#000000` | Inverse video foreground |
| Warning | `#ffff33` | Error messages, misspelled words in highlight mode |

## Screen Inventory

| Screen | Entry | Exit |
|--------|-------|------|
| Main Menu | App startup | Q (alert), any selection navigates away |
| Index Screen | 1, 2, or E from main menu | Esc → main menu; Enter → Editor |
| Editor | C (new), E→Index→Enter (load), T (demo) | Esc → main menu (with save prompt if modified) |
| Global Format | G from main menu or Ctrl+G from editor | Esc / Enter → caller |
| Proofreader | V from main menu or Ctrl+V from editor | Esc → caller |
| Print/Export | P from main menu or Ctrl+P from editor | Esc → caller |
| Preview (ANSI) | A from Print screen | Esc → Print screen |
| Word Count | Alt+W from editor | Any key → editor |
| Doctor | ? from main menu | Any key → main menu |

## Screen Transitions

All transitions are instant (no animation). The renderer calls `clearScreen()` then the new screen's `render()` method. No fade, no slide.

## Prompt Input Model

When a screen needs text input (filename, search string, etc.):
1. Clear the message bar (row 22).
2. Write the prompt text: e.g., `"Find: "` in bright color.
3. Show a blinking cursor at the end of the prompt.
4. Accumulate characters in a local string buffer.
5. Backspace removes the last character.
6. Enter confirms. Esc cancels.
7. After confirmation/cancellation, clear the message bar.

This model is used for: Find, Replace With, Save As, New File (name), Delete confirm (Y/N).

## Cursor Styles

| Context | Style |
|---------|-------|
| Editor (insert mode) | Blinking vertical bar (`|`) or thin underline |
| Editor (type-over mode) | Blinking block |
| Message bar input | Blinking underline |
| Not focused | Cursor hidden |

Implement blink with `setInterval(500ms)` toggling cursor visibility + `flush()`.

## Keyboard Navigation Conventions

- **Single letter keys** (A–Z, 0–9): trigger actions in menu screens. In the editor, they type characters.
- **Ctrl+Key**: app shortcuts, always prevented from browser.
- **Alt+Key**: secondary app shortcuts.
- **Function keys** (F1–F5): used for specific actions, prevented from browser.
- **Escape**: always goes "back" (exit screen, cancel prompt, return to menu).
- **Enter**: confirms selection or input.
- **Arrow keys**: navigation in menus and editor.

## Menu Screen Conventions

- The **first letter** of each action label is the hotkey. Render it in `COLORS.bright`.
- Arrow Up/Down can also navigate a cursor through menu items if preferred — but single-key activation (no cursor navigation) is acceptable and simpler.
- The menu does not require Enter to confirm — pressing the letter immediately executes.

## Error / Status Messages

- **Transient messages** (3 seconds then auto-clear): "Saved.", "File deleted.", "Replaced 12 occurrences."
- **Persistent prompts** (wait for input): "Find: ", "Save as: ", "Delete hello.sfw? (Y/N)"
- **Errors** (red/warning color, 5 seconds): "File not found.", "Storage full!"

Show all messages in row 22 (message bar). Never show a JavaScript `alert()` except for the "Q Quit" action (which is a special case since the web has no real quit).

## Main Menu Clock

Row 23, far right: `HH:MM` in dim color. Updates every second. Does not need to show seconds (keeps it uncluttered).

## Editor — Viewport Scrolling

The editor shows 20 lines at a time (rows 1–20). The viewport scrolls to keep the cursor visible:
- If cursor moves above the viewport: `viewportRow = cursorRow`.
- If cursor moves below the viewport: `viewportRow = cursorRow - 19`.
- On Page Up/Down: move viewport by 20, then clamp cursor to visible area.

## Editor — Long Lines

Lines longer than 80 characters: truncate display at column 79. Show a `→` indicator at column 79 if the line continues beyond the viewport (stretch goal). For v1, simply truncate. The user can still navigate off-screen by pressing End (moves cursor to line end, scrolling the view to show it).

Horizontal scrolling is a stretch goal. For v1, only vertical scrolling is required.

## Selection Model

- Selection is a range: `[anchorRow, anchorCol]` to `[cursorRow, cursorCol]`.
- Shift+Arrow extends the selection.
- Any non-shift navigation clears the selection.
- Render selected cells in inverse video.
- Cut/copy/paste operate on the selection.

## File Naming Rules

- Valid characters: A–Z, a–z, 0–9, `-`, `_`, `.`
- Max length: 64 characters
- Required extension: `.sfw` for formatted files, `.txt` for plain text
- Auto-append `.sfw` if user types just a name with no extension and is in SFW mode

## Inline Formatting — Display Rules

In the editor, control tags are rendered as single-character glyphs:

| Tag | Glyph | Color |
|-----|-------|-------|
| `\B` (bold on) | `←` | dim |
| `\b` (bold off) | `←` | dim |
| `\U` (underline on) | `▄` | dim |
| `\u` (underline off) | `▄` | dim |
| `\G` (elongated on) | `E` | dim |
| `\g` (elongated off) | `E` | dim |
| `\[` (superscript) | `↑` | dim |
| `\]` (subscript) | `↓` | dim |
| `\E` (center) | `↔` | dim |
| `\R` (flush right) | `→→` | dim (2 chars) |
| `\M` (para indent) | `¶` | dim |
| `\H:` (header) | `H:` | dim |
| `\F:` (footer) | `F:` | dim |
| `\P` (page break) | `↡` | dim |
| `\C` (chain) | `»` | dim |

Text between a `\B` and `\b` pair renders in `COLORS.bright`. Text between `\U` and `\u` renders with underline cell attribute. These visual hints help the user see formatting without hiding it.

## Help Bar (Row 24)

Always visible in the editor. Content:
```
Ctrl+F=Find  F3=Next  Ctrl+B=Bold  Ctrl+U=Undln  Ctrl+P=Print  Esc=Menu
```

The help bar does not change based on mode. It shows the most-used shortcuts.

## Status Bar (Row 23)

In the editor:
```
[INSERT]  [CAPS]  [SFW]  filename.sfw  42:15  312 words  14:32
```

- `[INSERT]` or `[TYPE-OVR]` based on `insertMode`
- `[CAPS]` when `capsMode` is true (dim when false, but still shown)
- `[SFW]` or `[TXT]` based on `fileProfile`
- Filename (or `Untitled` if null)
- `row:col` (1-based)
- Word count (updated on each keystroke, debounced)
- Clock HH:MM

## Global Format — Parameter Reference

| Key | Parameter | Type | Default | Range |
|-----|-----------|------|---------|-------|
| T | Top Margin | integer | 3 | 0–20 |
| B | Bottom Margin | integer | 3 | 0–20 |
| L | Left Margin | integer | 5 | 0–40 |
| R | Right Margin | integer | 75 | 40–79 |
| S | Line Spacing | enum | S | S, D |
| M | Double Column | boolean | N | M/N |
| G | Font | enum | STANDARD | STANDARD, DRAFT, BOLD |
| I | Paragraph Indent | integer | 5 | 0–20 |
| J | Justification | boolean | N | J/N |
| Q | Page Numbering | boolean | N | Q/N |
| Y | Page Length | integer | 66 | 20–132 |
| W | Page Wait | boolean | N | W/N |

In the web version, "Double Column", "Font" (DRAFT/BOLD), and "Page Wait" have no visible effect in the browser editor — they are preserved in the file and honored during export.
