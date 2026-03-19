# Safari Writer Web — Overview & Scope

> **For the implementation bot:** Read this file first. Then read the other spec files in order.

## What This Is

Safari Writer Web is a zero-install, browser-based TypeScript port of the Safari Writer TUI word processor. It runs entirely client-side with no backend, no downloads, and no registration. The primary goal is a **live demo** that lets people experience the retro AtariWriter 80 aesthetic immediately.

## Technology Stack

- **Language:** TypeScript (strict mode)
- **Bundler:** Vite (zero-config, fast HMR, produces a single deployable `dist/`)
- **UI paradigm:** A single `<canvas>` element (or a grid of `<div>` cells) that renders a fixed 80×25 terminal grid. No CSS framework. No React/Vue/Svelte. The DOM is minimal — the app owns its rendering.
- **Font:** "Atari Classic" or "Atari ST" bitmap font served as a WOFF2. Fallback: Courier New. Load it with `@font-face` in a `<style>` tag injected at startup.
- **Storage:** `localStorage` for all files and settings. No server, no IndexedDB for v1.
- **Spellcheck:** `nspell` (npm) — pure-JS port of Hunspell. Ships with en-US dictionary (~500 KB gzipped). Additional dictionaries downloadable client-side.
- **PDF export:** `jsPDF` (npm) — pure-JS, zero binary dependencies. Produces `.pdf` blobs for `<a download>`.
- **Markdown export:** Hand-rolled (trivial — strip control codes, output `.md` text).
- **Plain text export:** Strip control codes, offer `<a download>` for `.txt`.
- **PostScript export:** Hand-rolled text generation (PS is just a text format). Offer `<a download>` for `.ps`.

## Out of Scope

- **Mail Merge** — omitted entirely.
- **Safari DOS, Base, Fed, Feed, Reader, Slides, View, Chat, Basic, ASM** — all out of scope. The web app is the word processor only.
- **Any binary dependency** (wkhtmltopdf, ghostscript, etc.) — no subprocess calls exist in a browser; we use pure-JS libraries only.
- **i18n** — English only for v1. The architecture should allow adding it later (wrap user-facing strings in a `t()` call) but no .po pipeline is needed now.
- **Git integration** — not applicable.
- **Themes / style switcher** — one built-in theme: black background, white/green text, retro phosphor look.
- **Demo Mode** — yes, included: a bundled sample `.sfw` document loaded on first visit (or via **T** from main menu).

## What Is In Scope

| Feature | Notes |
|---------|-------|
| Main menu screen | Simplified — Words column + minimal DOS column (file list only) |
| Editor screen | Full-featured: navigation, modes, block ops, search/replace, inline formatting |
| File list (Index) | 1 and 2 on main menu — both show localStorage file list (no real filesystem) |
| File ops | New, Load (from localStorage), Save, Save As, Delete |
| Global Format screen | All 14 parameters |
| Inline formatting | All control codes stored as `\X` tags, displayed as glyphs |
| Spellcheck (Proofreader) | nspell, Highlight / Correct Errors modes |
| Print / Export | Plain text download, Markdown download, PDF download (jsPDF), PostScript download |
| ANSI Preview | In-browser paged preview (render formatted text in a modal) |
| Demo Mode | Bundled sample document |
| Tab stops | 16 tab stops, displayed in tab bar |
| Undo | Up to 50 snapshots |
| Word count | Simple modal |
| Alphabetize | Selected lines |

## Deployment

`vite build` → `web/dist/` → deployable to GitHub Pages, Netlify, Vercel, or any static host. The entry point is `index.html` at the root of `dist/`. No server-side rendering, no API routes.

## Project Layout

```
web/
  spec/           ← these planning docs (not shipped)
  src/
    main.ts       ← entry point, mounts App
    app.ts        ← App class: screen router, global state
    state.ts      ← AppState, GlobalFormat dataclasses
    screens/
      main_menu.ts
      editor.ts
      global_format.ts
      proofreader.ts
      print_screen.ts
      file_ops.ts
    terminal/
      renderer.ts  ← 80×25 grid renderer (canvas or div-grid)
      keyboard.ts  ← raw key event → action mapping
      colors.ts    ← color palette constants
    format/
      codec.ts     ← encode/decode .sfw \X tags ↔ glyph display
      export_md.ts
      export_pdf.ts
      export_ps.ts
      export_txt.ts
    storage/
      files.ts     ← localStorage file CRUD
    spell/
      checker.ts   ← nspell wrapper
  public/
    fonts/         ← Atari bitmap font WOFF2
    dict/          ← en-US .dic + .aff for nspell (served statically)
  index.html
  vite.config.ts
  tsconfig.json
  package.json
```

## Two-Bot Strategy

This spec is written to be handed directly to an implementation bot. Because the full implementation is large, it is split across two bots:

**Bot 1** (files: `01_bot1_scope.md`):
- Project scaffold: Vite + TypeScript setup, `index.html`, `package.json`, `tsconfig.json`, `vite.config.ts`
- Terminal renderer (80×25 grid with keyboard input)
- App router (screen switching)
- State management (`AppState`, `GlobalFormat`)
- localStorage file layer
- Main menu screen (all keyboard nav, simplified menu)
- Editor screen (full: navigation, editing modes, block ops, search/replace, inline formatting, tab stops, undo)
- File operations (new, load, save, save as, delete)

**Bot 2** (files: `02_bot2_scope.md`):
- Global Format screen
- Proofreader / spellcheck (nspell integration)
- Print / Export screen (text, markdown, PDF via jsPDF, PostScript)
- ANSI in-browser preview
- Demo Mode (bundled sample document)
- Word count modal
- Alphabetize
- Polish: focus management, scroll clamping, status bar updates, help bar content
