# Safari Writer Web — Technical Decisions & Rationale

## Why Canvas?

A `<canvas>` element gives complete control over rendering. Alternative approaches:

| Approach | Pros | Cons |
|----------|------|------|
| Canvas (chosen) | Pixel-perfect, no CSS fighting, easy inverse video, works at any DPI | No browser accessibility tree, no copy/paste from canvas |
| Div grid (80×25 divs) | Accessible, copy/paste works natively | CSS complexity, reflow cost, harder to control exact cell width |
| `xterm.js` | Full terminal emulator, accessibility | 300 KB+ bundle, overkill for a word processor |
| `<pre>` with innerHTML | Simple | XSS risk, hard to manage cursor, performance on large docs |

**Canvas wins for a retro demo.** Accessibility is a stretch goal. Copy/paste from the buffer can be offered via Ctrl+C/V through the app's own clipboard state (already in `AppState.clipboard`).

## Why No Framework?

React/Vue/Svelte add ~40–100 KB of runtime and impose a component/state model that fights against immediate-mode terminal rendering. The terminal renderer is inherently imperative. TypeScript classes are sufficient.

## Why Vite?

- Zero config for TypeScript
- Fast HMR during development
- Single-command production build
- Native ESM — no Webpack config hell
- Handles static asset serving (`public/dict/`)

## Why localStorage?

- Zero backend required
- Works offline
- No auth, no signup
- Survives page refresh
- Limit: ~5–10 MB per origin (plenty for text files)
- IndexedDB is overkill for v1

**Limitation:** Files are per-browser, per-origin. Users cannot share files between devices. That is acceptable for a demo. A future v2 could add Export to File System API (Chrome) or OPFS.

## Why nspell?

- Pure JavaScript port of Hunspell
- Works in the browser without WASM
- Accepts standard `.aff` + `.dic` files
- Same dictionary format as the Python `pyenchant` backend
- MIT licensed

**Alternative considered:** `wasm-hunspell` — more faithful but ~2 MB WASM binary and more complex initialization.

## Why jsPDF?

- Pure JavaScript, no binary dependency
- 200 KB minified (acceptable)
- MIT licensed
- Actively maintained
- Produces standard PDF 1.3

**Alternative considered:** `pdf-lib` — more capable (embeds fonts, edits existing PDFs) but more complex API for simple text output.

**Not considered:** Server-side PDF generation (requires backend, defeats zero-install goal).

## File Format Compatibility

The web version uses the same `.sfw` tag format as the Python version. A file saved in the web app can be opened in the Python TUI, and vice versa. This is a deliberate design goal.

Tags: `\B`, `\b`, `\U`, `\u`, `\G`, `\g`, `\[`, `\]`, `\E`, `\R`, `\M`, `\H:`, `\F:`, `\P`, `\C`, `\_`

## Performance Constraints

- Buffer size: tested up to 10,000 lines (a ~500 KB document). Canvas redraw at 60 fps for 20 visible rows is trivial.
- Spell checking: `nspell.check()` is synchronous and fast (~1ms per word). Checking a 500-word document takes ~500ms — acceptable for a batch "Highlight" pass. The "Correct Errors" interactive mode is not performance-sensitive.
- PDF export: jsPDF for a 100-page document takes ~2–3 seconds. Show a "Generating PDF…" message.

## Browser Support

Target: Chrome 90+, Firefox 90+, Safari 15+, Edge 90+. All support:
- Canvas 2D
- localStorage
- ESM modules
- Fetch API
- CSS `@font-face`

IE: not supported.

## Dictionary Files

Download from the `dictionary` npm package ecosystem or from LibreOffice's public dictionary repository. The en-US dictionary is public domain (based on Scrabble TWL + additional entries).

Recommended source: `hunspell-en-us` on npm.

```
web/public/dict/en_US.aff  (~90 KB)
web/public/dict/en_US.dic  (~2.7 MB)
```

Gzipped, these are served by any CDN at ~700 KB total — fine for a demo load. Vite's dev server and the production build both serve `public/` as static assets.

## Security

- No server, no attack surface.
- No `eval()` or `innerHTML` with user content.
- PostScript and PDF are generated as safe strings (user content is escaped in PS generation).
- localStorage is origin-isolated by the browser.

## Keyboard Conflicts

Some app shortcuts conflict with browser defaults:

| App Key | Browser Default | Resolution |
|---------|----------------|------------|
| Ctrl+F | Browser find dialog | `preventDefault()` always |
| Ctrl+P | Browser print | `preventDefault()` always |
| Ctrl+U | View source (Firefox) | `preventDefault()` always |
| Ctrl+B | Bookmark (Firefox) | `preventDefault()` always |
| F1 | Browser help | `preventDefault()` always |
| Backspace | Browser back | `preventDefault()` always |
| Tab | Focus next element | `preventDefault()` always |
| Escape | Stop loading | Only when app handles it |

Note: Ctrl+C/V for clipboard must be handled carefully — we want the app's clipboard (not the system clipboard). In v1, the app's own clipboard is used. Ctrl+C copies to `AppState.clipboard`, not the system clipboard. This is intentional to match the TUI behavior.

## Stretch Goals (not in scope for Bot 1 or Bot 2)

- System clipboard integration via `navigator.clipboard` API (requires HTTPS + user gesture)
- File System Access API (Chrome) for reading/writing real files
- PWA manifest + service worker for offline installability
- Atari bitmap font loading via WOFF2
- Multiple color themes (amber, white, blue)
- Export to HTML (styled with inline CSS)
- Auto-save to localStorage every 30 seconds
- Import from `.txt` files via file input `<input type="file">`
- Multi-tab support (one document per tab, shared localStorage)
- Safari Writer Web as an iframe embeddable widget
