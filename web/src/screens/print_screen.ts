import { TerminalRenderer } from '../terminal/renderer';
import { KeyboardHandler, KeyAction } from '../terminal/keyboard';
import { COLORS } from '../terminal/colors';
import { AppState } from '../state';
import { stripTags } from '../format/codec';
import { downloadBlob } from '../storage/files';
import { exportMarkdown } from '../format/export_md';
import { exportPDF } from '../format/export_pdf';
import { exportPS } from '../format/export_ps';

export function showPrintScreen(
  renderer: TerminalRenderer,
  keyboard: KeyboardHandler,
  state: AppState,
  onDone: () => void,
): void {
  function renderMenu(): void {
    renderer.clearScreen();
    renderer.setCursor(null, null);

    const top = 8;
    const left = 16;
    const w = 45;
    renderer.writeString(top, left, '╔' + '══════════ PRINT / EXPORT ═══════════' + '═'.repeat(w - 37) + '╗', COLORS.dim, COLORS.bg);
    for (let r = 1; r <= 8; r++) {
      renderer.writeString(top + r, left, '║' + ' '.repeat(w) + '║', COLORS.dim, COLORS.bg);
    }
    renderer.writeString(top + 9, left, '╚' + '═'.repeat(w) + '╝', COLORS.dim, COLORS.bg);

    renderer.writeString(top + 2, left + 3, 'A', COLORS.bright, COLORS.bg, true);
    renderer.writeString(top + 2, left + 4, '  ANSI Preview (in browser)', COLORS.fg, COLORS.bg);
    renderer.writeString(top + 3, left + 3, 'T', COLORS.bright, COLORS.bg, true);
    renderer.writeString(top + 3, left + 4, '  Plain Text   (.txt download)', COLORS.fg, COLORS.bg);
    renderer.writeString(top + 4, left + 3, 'M', COLORS.bright, COLORS.bg, true);
    renderer.writeString(top + 4, left + 4, '  Markdown     (.md download)', COLORS.fg, COLORS.bg);
    renderer.writeString(top + 5, left + 3, 'P', COLORS.bright, COLORS.bg, true);
    renderer.writeString(top + 5, left + 4, '  PDF          (.pdf download)', COLORS.fg, COLORS.bg);
    renderer.writeString(top + 6, left + 3, 'S', COLORS.bright, COLORS.bg, true);
    renderer.writeString(top + 6, left + 4, '  PostScript   (.ps download)', COLORS.fg, COLORS.bg);

    renderer.writeString(top + 8, left + 3, 'Esc  Return', COLORS.dim, COLORS.bg);

    renderer.flush();
  }

  function baseName(): string {
    const fn = state.filename || 'document';
    return fn.replace(/\.\w+$/, '');
  }

  function doPlainText(): void {
    const lines = state.buffer.map(l => {
      const text = stripTags(l);
      return ' '.repeat(state.fmt.leftMargin) + text;
    });
    downloadBlob(baseName() + '.txt', lines.join('\n'), 'text/plain');
    showMessage('Plain text downloaded.');
  }

  function doMarkdown(): void {
    const md = exportMarkdown(state.buffer);
    downloadBlob(baseName() + '.md', md, 'text/markdown');
    showMessage('Markdown downloaded.');
  }

  function doPDF(): void {
    exportPDF(state.buffer, state.fmt, state.filename || 'document.sfw');
    showMessage('PDF downloaded.');
  }

  function doPostScript(): void {
    const ps = exportPS(state.buffer, state.fmt, state.filename || 'document.sfw');
    downloadBlob(baseName() + '.ps', ps, 'application/postscript');
    showMessage('PostScript downloaded.');
  }

  function showMessage(msg: string): void {
    renderer.writeString(22, 16, msg, COLORS.bright, COLORS.bg);
    renderer.writeString(23, 16, 'Press any key to continue.', COLORS.dim, COLORS.bg);
    renderer.flush();
    keyboard.setHandler(() => {
      keyboard.setHandler(menuHandler);
      renderMenu();
    });
  }

  // --- ANSI Preview ---
  function doAnsiPreview(): void {
    const fmt = state.fmt;
    const usableWidth = fmt.rightMargin - fmt.leftMargin;
    const linesPerPage = fmt.pageLength - fmt.topMargin - fmt.bottomMargin;

    // Paginate
    const pages: string[][] = [];
    let currentPage: string[] = [];
    let lineCount = 0;

    // Add top margin
    for (let i = 0; i < fmt.topMargin; i++) {
      currentPage.push('');
      lineCount++;
    }

    for (const rawLine of state.buffer) {
      // Page break
      if (rawLine.trim() === '\\P') {
        pages.push(currentPage);
        currentPage = [];
        lineCount = 0;
        for (let i = 0; i < fmt.topMargin; i++) {
          currentPage.push('');
          lineCount++;
        }
        continue;
      }

      if (lineCount >= linesPerPage) {
        pages.push(currentPage);
        currentPage = [];
        lineCount = 0;
        for (let i = 0; i < fmt.topMargin; i++) {
          currentPage.push('');
          lineCount++;
        }
      }

      const plain = stripTags(rawLine);
      let displayLine = plain;

      // Alignment
      if (rawLine.startsWith('\\E')) {
        const pad = Math.max(0, Math.floor((usableWidth - plain.length) / 2));
        displayLine = ' '.repeat(pad) + plain;
      } else if (rawLine.startsWith('\\R')) {
        const pad = Math.max(0, usableWidth - plain.length);
        displayLine = ' '.repeat(pad) + plain;
      }

      // Left margin
      displayLine = ' '.repeat(fmt.leftMargin) + displayLine;

      currentPage.push(displayLine);
      lineCount++;

      // Double spacing
      if (fmt.lineSpacing === 'D' && lineCount < linesPerPage) {
        currentPage.push('');
        lineCount++;
      }
    }
    if (currentPage.length > 0) pages.push(currentPage);
    if (pages.length === 0) pages.push(['']);

    let pageIdx = 0;

    function renderPage(): void {
      renderer.clearScreen();
      renderer.setCursor(null, null);

      const page = pages[pageIdx];
      for (let r = 0; r < Math.min(page.length, 24); r++) {
        const line = page[r];
        for (let c = 0; c < Math.min(line.length, 80); c++) {
          renderer.setCell(r, c, { char: line[c], fg: COLORS.fg, bg: COLORS.bg });
        }
      }

      const status = `Page ${pageIdx + 1} of ${pages.length}  Space=Next  PgUp=Prev  Esc=Exit`;
      renderer.writeString(24, Math.floor((80 - status.length) / 2), status, COLORS.dim, COLORS.bg);
      renderer.flush();
    }

    function previewHandler(action: KeyAction): void {
      if (action === 'escape') {
        keyboard.setHandler(menuHandler);
        renderMenu();
        return;
      }
      if (action === 'page_down' || (typeof action === 'object' && action.type === 'char' && action.char === ' ')) {
        if (pageIdx < pages.length - 1) {
          pageIdx++;
          renderPage();
        }
        return;
      }
      if (action === 'page_up') {
        if (pageIdx > 0) {
          pageIdx--;
          renderPage();
        }
        return;
      }
    }

    keyboard.setHandler(previewHandler);
    renderPage();
  }

  function menuHandler(action: KeyAction): void {
    if (action === 'escape') {
      onDone();
      return;
    }
    if (typeof action === 'object' && action.type === 'char') {
      const ch = action.char.toUpperCase();
      switch (ch) {
        case 'A': doAnsiPreview(); return;
        case 'T': doPlainText(); return;
        case 'M': doMarkdown(); return;
        case 'P': doPDF(); return;
        case 'S': doPostScript(); return;
      }
    }
  }

  keyboard.setHandler(menuHandler);
  renderMenu();
}
