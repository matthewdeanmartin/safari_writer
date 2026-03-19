import { TerminalRenderer } from '../terminal/renderer';
import { KeyboardHandler, KeyAction } from '../terminal/keyboard';
import { COLORS } from '../terminal/colors';
import { AppState } from '../state';
import { parseLineSegments, displayLength, displayColToRawPos, rawPosToDisplayCol, stripTags } from '../format/codec';
import { saveFile } from '../storage/files';

const EDITOR_TOP = 1;
const EDITOR_BOTTOM = 20;
const VISIBLE_LINES = EDITOR_BOTTOM - EDITOR_TOP + 1;
const STATUS_ROW = 23;
const HELP_ROW = 24;
const MESSAGE_ROW = 22;
const TAB_ROW = 0;

type PromptCallback = (value: string | null) => void;

export function showEditor(
  renderer: TerminalRenderer,
  keyboard: KeyboardHandler,
  state: AppState,
  onExit: () => void,
): void {
  let viewportRow = 0;
  let charsSinceSnapshot = 0;
  let messageTimeout: number | undefined;
  let promptMode = false;
  let promptText = '';
  let promptBuffer = '';
  let promptCallback: PromptCallback | null = null;
  let clockInterval: number | undefined;

  function pushUndo(): void {
    state.undoStack.push(state.buffer.map(l => l));
    if (state.undoStack.length > 50) state.undoStack.shift();
    charsSinceSnapshot = 0;
  }

  function popUndo(): void {
    if (state.undoStack.length === 0) return;
    const snap = state.undoStack.pop()!;
    state.buffer = snap;
    state.cursorRow = Math.min(state.cursorRow, state.buffer.length - 1);
    state.cursorCol = Math.min(state.cursorCol, displayLen(state.cursorRow));
    state.modified = true;
    clearSelection();
  }

  function displayLen(row: number): number {
    if (row < 0 || row >= state.buffer.length) return 0;
    return state.fileProfile === 'sfw'
      ? displayLength(state.buffer[row])
      : state.buffer[row].length;
  }

  function rawLine(row: number): string {
    return state.buffer[row] ?? '';
  }

  function cursorRawPos(): number {
    if (state.fileProfile === 'sfw') {
      return displayColToRawPos(rawLine(state.cursorRow), state.cursorCol);
    }
    return state.cursorCol;
  }

  function clampCursor(): void {
    if (state.cursorRow < 0) state.cursorRow = 0;
    if (state.cursorRow >= state.buffer.length) state.cursorRow = state.buffer.length - 1;
    const maxCol = displayLen(state.cursorRow);
    if (state.cursorCol > maxCol) state.cursorCol = maxCol;
    if (state.cursorCol < 0) state.cursorCol = 0;
  }

  function scrollToView(): void {
    if (state.cursorRow < viewportRow) viewportRow = state.cursorRow;
    if (state.cursorRow >= viewportRow + VISIBLE_LINES) viewportRow = state.cursorRow - VISIBLE_LINES + 1;
    if (viewportRow < 0) viewportRow = 0;
  }

  function clearSelection(): void {
    state.selectionAnchor = null;
  }

  function hasSelection(): boolean {
    return state.selectionAnchor !== null;
  }

  function getSelection(): { startRow: number; startCol: number; endRow: number; endCol: number } | null {
    if (!state.selectionAnchor) return null;
    const [ar, ac] = state.selectionAnchor;
    const cr = state.cursorRow;
    const cc = state.cursorCol;
    if (ar < cr || (ar === cr && ac <= cc)) {
      return { startRow: ar, startCol: ac, endRow: cr, endCol: cc };
    }
    return { startRow: cr, startCol: cc, endRow: ar, endCol: ac };
  }

  function deleteSelection(): string {
    const sel = getSelection();
    if (!sel) return '';
    pushUndo();
    const { startRow, startCol, endRow, endCol } = sel;

    let deleted: string;
    if (startRow === endRow) {
      const line = rawLine(startRow);
      const sp = toRawPos(startRow, startCol);
      const ep = toRawPos(startRow, endCol);
      deleted = line.substring(sp, ep);
      state.buffer[startRow] = line.substring(0, sp) + line.substring(ep);
      state.cursorRow = startRow;
      state.cursorCol = startCol;
    } else {
      const firstLine = rawLine(startRow);
      const lastLine = rawLine(endRow);
      const sp = toRawPos(startRow, startCol);
      const ep = toRawPos(endRow, endCol);
      deleted = firstLine.substring(sp) + '\n' +
        state.buffer.slice(startRow + 1, endRow).join('\n') + '\n' +
        lastLine.substring(0, ep);
      state.buffer[startRow] = firstLine.substring(0, sp) + lastLine.substring(ep);
      state.buffer.splice(startRow + 1, endRow - startRow);
      state.cursorRow = startRow;
      state.cursorCol = startCol;
    }
    clearSelection();
    state.modified = true;
    return deleted;
  }

  function toRawPos(row: number, displayCol: number): number {
    if (state.fileProfile === 'sfw') {
      return displayColToRawPos(rawLine(row), displayCol);
    }
    return displayCol;
  }

  function toDisplayCol(row: number, rawPos: number): number {
    if (state.fileProfile === 'sfw') {
      return rawPosToDisplayCol(rawLine(row), rawPos);
    }
    return rawPos;
  }

  function wordCount(): number {
    const text = state.buffer.map(l => stripTags(l)).join(' ');
    const words = text.split(/\s+/).filter(w => w.length > 0);
    return words.length;
  }

  // --- Rendering ---

  function render(): void {
    renderTabBar();
    renderEditorArea();
    renderStatusBar();
    renderHelpBar();
    if (!promptMode) {
      renderer.clearRow(MESSAGE_ROW);
    }

    const screenRow = state.cursorRow - viewportRow + EDITOR_TOP;
    if (!promptMode && screenRow >= EDITOR_TOP && screenRow <= EDITOR_BOTTOM) {
      renderer.setCursor(screenRow, Math.min(state.cursorCol, 79));
    } else if (!promptMode) {
      renderer.setCursor(null, null);
    }

    renderer.flush();
  }

  function renderTabBar(): void {
    for (let c = 0; c < 80; c++) {
      const ch = state.tabStops[c] ? '▼' : '·';
      const color = state.tabStops[c] ? COLORS.bright : COLORS.dim;
      renderer.setCell(TAB_ROW, c, { char: ch, fg: color, bg: COLORS.bg });
    }
  }

  function renderEditorArea(): void {
    const sel = getSelection();

    for (let i = 0; i < VISIBLE_LINES; i++) {
      const bufRow = viewportRow + i;
      const screenRow = EDITOR_TOP + i;
      renderer.clearRow(screenRow);

      if (bufRow >= state.buffer.length) continue;

      const line = state.buffer[bufRow];

      if (state.fileProfile === 'sfw') {
        renderSfwLine(screenRow, bufRow, line, sel);
      } else {
        renderTxtLine(screenRow, bufRow, line, sel);
      }
    }
  }

  function renderSfwLine(
    screenRow: number,
    bufRow: number,
    line: string,
    sel: { startRow: number; startCol: number; endRow: number; endCol: number } | null,
  ): void {
    const segments = parseLineSegments(line);
    let dc = 0;
    let inBold = false;
    let inUnderline = false;

    for (const seg of segments) {
      if (seg.isTag) {
        if (seg.tag === '\\B') inBold = true;
        if (seg.tag === '\\b') inBold = false;
        if (seg.tag === '\\U') inUnderline = true;
        if (seg.tag === '\\u') inUnderline = false;

        // Render tag glyph in dim
        for (let ci = 0; ci < seg.text.length; ci++) {
          if (dc + ci >= 80) break;
          const inSel = isInSelection(sel, bufRow, dc + ci);
          renderer.setCell(screenRow, dc + ci, {
            char: seg.text[ci],
            fg: inSel ? COLORS.inverse_fg : COLORS.dim,
            bg: inSel ? COLORS.inverse_bg : COLORS.bg,
          });
        }
        dc += seg.text.length;
      } else {
        for (let ci = 0; ci < seg.text.length; ci++) {
          if (dc >= 80) break;
          const inSel = isInSelection(sel, bufRow, dc);
          const fg = inSel ? COLORS.inverse_fg : (inBold ? COLORS.bright : COLORS.fg);
          const bg = inSel ? COLORS.inverse_bg : COLORS.bg;
          renderer.setCell(screenRow, dc, {
            char: seg.text[ci],
            fg,
            bg,
            bold: inBold,
            underline: inUnderline,
          });
          dc++;
        }
      }
    }
  }

  function renderTxtLine(
    screenRow: number,
    bufRow: number,
    line: string,
    sel: { startRow: number; startCol: number; endRow: number; endCol: number } | null,
  ): void {
    for (let c = 0; c < Math.min(line.length, 80); c++) {
      const inSel = isInSelection(sel, bufRow, c);
      renderer.setCell(screenRow, c, {
        char: line[c],
        fg: inSel ? COLORS.inverse_fg : COLORS.fg,
        bg: inSel ? COLORS.inverse_bg : COLORS.bg,
      });
    }
  }

  function isInSelection(
    sel: { startRow: number; startCol: number; endRow: number; endCol: number } | null,
    row: number,
    col: number,
  ): boolean {
    if (!sel) return false;
    if (row < sel.startRow || row > sel.endRow) return false;
    if (row === sel.startRow && row === sel.endRow) {
      return col >= sel.startCol && col < sel.endCol;
    }
    if (row === sel.startRow) return col >= sel.startCol;
    if (row === sel.endRow) return col < sel.endCol;
    return true;
  }

  function renderStatusBar(): void {
    renderer.clearRow(STATUS_ROW, COLORS.status_bg);
    const mode = state.insertMode ? '[INSERT]' : '[TYPE-OVR]';
    const caps = state.capsMode ? '[CAPS]' : '[caps]';
    const profile = `[${state.fileProfile.toUpperCase()}]`;
    const filename = state.filename || 'Untitled';
    const pos = `${state.cursorRow + 1}:${state.cursorCol + 1}`;
    const wc = `${wordCount()} words`;

    let col = 2;
    renderer.writeString(STATUS_ROW, col, mode, COLORS.status_fg, COLORS.status_bg);
    col += mode.length + 2;
    const capsColor = state.capsMode ? COLORS.status_fg : '#555555';
    renderer.writeString(STATUS_ROW, col, caps, capsColor, COLORS.status_bg);
    col += caps.length + 2;
    renderer.writeString(STATUS_ROW, col, profile, COLORS.status_fg, COLORS.status_bg);
    col += profile.length + 2;
    renderer.writeString(STATUS_ROW, col, filename, COLORS.status_fg, COLORS.status_bg);
    col += filename.length + 2;
    renderer.writeString(STATUS_ROW, col, pos, COLORS.status_fg, COLORS.status_bg);
    col += pos.length + 2;
    renderer.writeString(STATUS_ROW, col, wc, COLORS.status_fg, COLORS.status_bg);

    // Clock
    const now = new Date();
    const hh = String(now.getHours()).padStart(2, '0');
    const mm = String(now.getMinutes()).padStart(2, '0');
    renderer.writeString(STATUS_ROW, 73, `${hh}:${mm}`, COLORS.status_fg, COLORS.status_bg);
  }

  function renderHelpBar(): void {
    renderer.clearRow(HELP_ROW);
    renderer.writeString(HELP_ROW, 1, 'Ctrl+F=Find  F3=Next  Ctrl+B=Bold  Ctrl+U=Undln  Ctrl+P=Print  Esc=Menu', COLORS.dim, COLORS.bg);
  }

  function showMessage(text: string, color?: string, duration?: number): void {
    if (messageTimeout !== undefined) clearTimeout(messageTimeout);
    renderer.clearRow(MESSAGE_ROW);
    renderer.writeString(MESSAGE_ROW, 1, text, color ?? COLORS.fg, COLORS.bg);
    renderer.flush();
    if (duration !== undefined) {
      messageTimeout = window.setTimeout(() => {
        renderer.clearRow(MESSAGE_ROW);
        renderer.flush();
        messageTimeout = undefined;
      }, duration);
    }
  }

  function startPrompt(label: string, callback: PromptCallback): void {
    promptMode = true;
    promptText = label;
    promptBuffer = '';
    promptCallback = callback;
    renderPrompt();
  }

  function renderPrompt(): void {
    renderer.clearRow(MESSAGE_ROW);
    renderer.writeString(MESSAGE_ROW, 1, promptText + promptBuffer, COLORS.bright, COLORS.bg);
    renderer.setCursor(MESSAGE_ROW, 1 + promptText.length + promptBuffer.length);
    renderer.flush();
  }

  function handlePromptKey(action: KeyAction): void {
    if (action === 'escape') {
      promptMode = false;
      promptCallback?.(null);
      promptCallback = null;
      render();
      return;
    }
    if (action === 'enter') {
      promptMode = false;
      const val = promptBuffer;
      const cb = promptCallback;
      promptCallback = null;
      cb?.(val);
      render();
      return;
    }
    if (action === 'backspace') {
      promptBuffer = promptBuffer.slice(0, -1);
      renderPrompt();
      return;
    }
    if (typeof action === 'object' && action.type === 'char') {
      promptBuffer += action.char;
      renderPrompt();
    }
  }

  // --- Editing ---

  function insertChar(ch: string): void {
    if (state.capsMode) ch = ch.toUpperCase();
    if (hasSelection()) deleteSelection();

    const line = rawLine(state.cursorRow);
    const rp = cursorRawPos();

    if (state.insertMode) {
      state.buffer[state.cursorRow] = line.substring(0, rp) + ch + line.substring(rp);
    } else {
      state.buffer[state.cursorRow] = line.substring(0, rp) + ch + line.substring(rp + 1);
    }
    state.cursorCol++;
    state.modified = true;

    charsSinceSnapshot++;
    if (charsSinceSnapshot >= 20) pushUndo();
  }

  function insertNewline(): void {
    pushUndo();
    if (hasSelection()) deleteSelection();
    const line = rawLine(state.cursorRow);
    const rp = cursorRawPos();
    state.buffer[state.cursorRow] = line.substring(0, rp);
    state.buffer.splice(state.cursorRow + 1, 0, line.substring(rp));
    state.cursorRow++;
    state.cursorCol = 0;
    state.modified = true;
  }

  function doBackspace(): void {
    if (hasSelection()) {
      deleteSelection();
      return;
    }
    pushUndo();
    if (state.cursorCol > 0) {
      const line = rawLine(state.cursorRow);
      const rp = cursorRawPos();
      // Find how many raw chars to delete (could be a tag)
      const prevRp = displayColToRawPos(line, state.cursorCol - 1);
      state.buffer[state.cursorRow] = line.substring(0, prevRp) + line.substring(rp);
      state.cursorCol--;
    } else if (state.cursorRow > 0) {
      const prevLen = displayLen(state.cursorRow - 1);
      state.buffer[state.cursorRow - 1] += state.buffer[state.cursorRow];
      state.buffer.splice(state.cursorRow, 1);
      state.cursorRow--;
      state.cursorCol = prevLen;
    }
    state.modified = true;
  }

  function doDelete(): void {
    if (hasSelection()) {
      deleteSelection();
      return;
    }
    pushUndo();
    const line = rawLine(state.cursorRow);
    const rp = cursorRawPos();
    if (rp < line.length) {
      // Find end of current display character
      const nextDc = state.cursorCol + 1;
      const nextRp = displayColToRawPos(line, nextDc);
      state.buffer[state.cursorRow] = line.substring(0, rp) + line.substring(nextRp);
    } else if (state.cursorRow < state.buffer.length - 1) {
      state.buffer[state.cursorRow] += state.buffer[state.cursorRow + 1];
      state.buffer.splice(state.cursorRow + 1, 1);
    }
    state.modified = true;
  }

  function doShiftDelete(): void {
    pushUndo();
    const line = rawLine(state.cursorRow);
    const rp = cursorRawPos();
    state.lastDeletedLine = line.substring(rp);
    state.buffer[state.cursorRow] = line.substring(0, rp);
    state.modified = true;
  }

  function doCtrlShiftDelete(): void {
    pushUndo();
    const line = rawLine(state.cursorRow);
    const rp = cursorRawPos();
    state.buffer[state.cursorRow] = line.substring(0, rp);
    state.buffer.splice(state.cursorRow + 1);
    state.modified = true;
  }

  // --- Navigation ---

  function moveUp(): void {
    clearSelection();
    if (state.cursorRow > 0) {
      state.cursorRow--;
      clampCursor();
    }
  }

  function moveDown(): void {
    clearSelection();
    if (state.cursorRow < state.buffer.length - 1) {
      state.cursorRow++;
      clampCursor();
    }
  }

  function moveLeft(): void {
    clearSelection();
    if (state.cursorCol > 0) {
      state.cursorCol--;
    } else if (state.cursorRow > 0) {
      state.cursorRow--;
      state.cursorCol = displayLen(state.cursorRow);
    }
  }

  function moveRight(): void {
    clearSelection();
    if (state.cursorCol < displayLen(state.cursorRow)) {
      state.cursorCol++;
    } else if (state.cursorRow < state.buffer.length - 1) {
      state.cursorRow++;
      state.cursorCol = 0;
    }
  }

  function wordLeft(): void {
    clearSelection();
    const plain = stripTags(rawLine(state.cursorRow));
    let col = state.cursorCol;
    // Skip spaces
    while (col > 0 && plain[col - 1] === ' ') col--;
    // Skip word chars
    while (col > 0 && plain[col - 1] !== ' ') col--;
    state.cursorCol = col;
  }

  function wordRight(): void {
    clearSelection();
    const plain = stripTags(rawLine(state.cursorRow));
    let col = state.cursorCol;
    // Skip word chars
    while (col < plain.length && plain[col] !== ' ') col++;
    // Skip spaces
    while (col < plain.length && plain[col] === ' ') col++;
    state.cursorCol = Math.min(col, displayLen(state.cursorRow));
  }

  function extendSelection(moveFn: () => void): void {
    if (!state.selectionAnchor) {
      state.selectionAnchor = [state.cursorRow, state.cursorCol];
    }
    // Temporarily avoid clearing selection in the move function
    const savedAnchor = state.selectionAnchor;
    moveFn();
    state.selectionAnchor = savedAnchor;
  }

  // --- Search ---

  function doFind(): void {
    startPrompt('Find: ', (value) => {
      if (value !== null && value.length > 0) {
        state.searchString = value;
        state.lastSearchRow = state.cursorRow;
        state.lastSearchCol = state.cursorCol;
        findNext();
      }
    });
  }

  function findNext(): void {
    if (!state.searchString) return;
    const needle = state.searchString.toLowerCase();
    let row = state.lastSearchRow;
    let col = state.lastSearchCol + 1;

    for (let attempts = 0; attempts < state.buffer.length * 2; attempts++) {
      if (row >= state.buffer.length) {
        row = 0;
        col = 0;
        showMessage('Wrapped.', COLORS.dim, 2000);
      }
      const line = stripTags(state.buffer[row]).toLowerCase();
      const idx = line.indexOf(needle, col);
      if (idx >= 0) {
        state.cursorRow = row;
        state.cursorCol = idx;
        state.lastSearchRow = row;
        state.lastSearchCol = idx;
        state.selectionAnchor = [row, idx];
        state.cursorCol = idx + state.searchString.length;
        scrollToView();
        render();
        return;
      }
      row++;
      col = 0;
    }
    showMessage('Not found.', COLORS.warning, 3000);
  }

  function doReplace(): void {
    startPrompt('Replace with: ', (value) => {
      if (value !== null) {
        state.replaceString = value;
        showMessage(`Replace string set: "${value}"`, COLORS.fg, 2000);
      }
    });
  }

  function replaceAndNext(): void {
    if (!state.searchString || !hasSelection()) return;
    pushUndo();
    const sel = getSelection();
    if (!sel) return;
    // Replace in buffer
    const line = rawLine(sel.startRow);
    if (sel.startRow === sel.endRow) {
      const sp = toRawPos(sel.startRow, sel.startCol);
      const ep = toRawPos(sel.endRow, sel.endCol);
      state.buffer[sel.startRow] = line.substring(0, sp) + state.replaceString + line.substring(ep);
    }
    state.modified = true;
    clearSelection();
    state.lastSearchCol = sel.startCol + state.replaceString.length - 1;
    findNext();
  }

  function globalReplace(): void {
    if (!state.searchString) return;
    pushUndo();
    const needle = state.searchString;
    let count = 0;
    for (let r = 0; r < state.buffer.length; r++) {
      const line = state.buffer[r];
      const plain = stripTags(line);
      if (state.fileProfile === 'txt') {
        let newLine = '';
        let idx = 0;
        let pos = plain.toLowerCase().indexOf(needle.toLowerCase(), idx);
        while (pos >= 0) {
          newLine += plain.substring(idx, pos) + state.replaceString;
          count++;
          idx = pos + needle.length;
          pos = plain.toLowerCase().indexOf(needle.toLowerCase(), idx);
        }
        newLine += plain.substring(idx);
        state.buffer[r] = newLine;
      } else {
        // For .sfw files, do a simple string replace on the raw line
        let newLine = line;
        let lower = newLine.toLowerCase();
        let pos = lower.indexOf(needle.toLowerCase());
        while (pos >= 0) {
          newLine = newLine.substring(0, pos) + state.replaceString + newLine.substring(pos + needle.length);
          count++;
          lower = newLine.toLowerCase();
          pos = lower.indexOf(needle.toLowerCase(), pos + state.replaceString.length);
        }
        state.buffer[r] = newLine;
      }
    }
    state.modified = true;
    clearSelection();
    showMessage(`Replaced ${count} occurrence${count !== 1 ? 's' : ''}.`, COLORS.fg, 3000);
    render();
  }

  // --- Formatting ---

  function insertTagPair(openTag: string, closeTag: string): void {
    if (state.fileProfile !== 'sfw') return;
    pushUndo();
    if (hasSelection()) {
      const sel = getSelection()!;
      if (sel.startRow === sel.endRow) {
        const line = rawLine(sel.startRow);
        const sp = toRawPos(sel.startRow, sel.startCol);
        const ep = toRawPos(sel.endRow, sel.endCol);
        state.buffer[sel.startRow] = line.substring(0, sp) + openTag + line.substring(sp, ep) + closeTag + line.substring(ep);
        clearSelection();
        state.modified = true;
      }
    } else {
      // Insert open at cursor, close at end of word
      const line = rawLine(state.cursorRow);
      const rp = cursorRawPos();
      // Find end of word
      let endRp = rp;
      while (endRp < line.length && line[endRp] !== ' ') endRp++;
      state.buffer[state.cursorRow] = line.substring(0, rp) + openTag + line.substring(rp, endRp) + closeTag + line.substring(endRp);
      state.cursorCol += displayLength(openTag);
      state.modified = true;
    }
  }

  function insertSingleTag(tag: string, atLineStart: boolean): void {
    if (state.fileProfile !== 'sfw') return;
    pushUndo();
    if (atLineStart) {
      const line = rawLine(state.cursorRow);
      // Remove existing alignment tag at start if any
      let cleaned = line;
      for (const prefix of ['\\E', '\\R', '\\M']) {
        if (cleaned.startsWith(prefix)) {
          cleaned = cleaned.substring(prefix.length);
        }
      }
      state.buffer[state.cursorRow] = tag + cleaned;
    } else {
      const line = rawLine(state.cursorRow);
      const rp = cursorRawPos();
      state.buffer[state.cursorRow] = line.substring(0, rp) + tag + line.substring(rp);
      state.cursorCol += displayLength(tag);
    }
    state.modified = true;
  }

  function insertPageBreak(): void {
    if (state.fileProfile !== 'sfw') return;
    pushUndo();
    state.buffer.splice(state.cursorRow + 1, 0, '\\P');
    state.cursorRow++;
    state.cursorCol = displayLength('\\P');
    state.modified = true;
  }

  function insertHeaderFooter(tag: string): void {
    if (state.fileProfile !== 'sfw') return;
    pushUndo();
    const line = rawLine(state.cursorRow);
    if (!line.startsWith(tag)) {
      state.buffer[state.cursorRow] = tag + line;
    }
    state.modified = true;
  }

  // --- Block ops ---

  function doCut(): void {
    if (!hasSelection()) return;
    state.clipboard = deleteSelection();
    render();
  }

  function doCopy(): void {
    const sel = getSelection();
    if (!sel) return;
    if (sel.startRow === sel.endRow) {
      const line = rawLine(sel.startRow);
      const sp = toRawPos(sel.startRow, sel.startCol);
      const ep = toRawPos(sel.endRow, sel.endCol);
      state.clipboard = line.substring(sp, ep);
    } else {
      const lines: string[] = [];
      for (let r = sel.startRow; r <= sel.endRow; r++) {
        if (r === sel.startRow) {
          lines.push(rawLine(r).substring(toRawPos(r, sel.startCol)));
        } else if (r === sel.endRow) {
          lines.push(rawLine(r).substring(0, toRawPos(r, sel.endCol)));
        } else {
          lines.push(rawLine(r));
        }
      }
      state.clipboard = lines.join('\n');
    }
    showMessage('Copied.', COLORS.fg, 2000);
  }

  function doPaste(): void {
    if (!state.clipboard) return;
    pushUndo();
    if (hasSelection()) deleteSelection();
    const lines = state.clipboard.split('\n');
    if (lines.length === 1) {
      const line = rawLine(state.cursorRow);
      const rp = cursorRawPos();
      state.buffer[state.cursorRow] = line.substring(0, rp) + lines[0] + line.substring(rp);
      state.cursorCol += lines[0].length;
    } else {
      const line = rawLine(state.cursorRow);
      const rp = cursorRawPos();
      const before = line.substring(0, rp);
      const after = line.substring(rp);
      state.buffer[state.cursorRow] = before + lines[0];
      for (let i = 1; i < lines.length; i++) {
        state.buffer.splice(state.cursorRow + i, 0, lines[i]);
      }
      state.buffer[state.cursorRow + lines.length - 1] += after;
      state.cursorRow += lines.length - 1;
      state.cursorCol = toDisplayCol(state.cursorRow, lines[lines.length - 1].length);
    }
    state.modified = true;
  }

  function doAlphabetize(): void {
    const sel = getSelection();
    if (!sel) {
      showMessage('Select lines first.', COLORS.warning, 2000);
      return;
    }
    pushUndo();
    const subLines = state.buffer.slice(sel.startRow, sel.endRow + 1);
    subLines.sort((a, b) => stripTags(a).toLowerCase().localeCompare(stripTags(b).toLowerCase()));
    for (let i = 0; i < subLines.length; i++) {
      state.buffer[sel.startRow + i] = subLines[i];
    }
    clearSelection();
    state.modified = true;
    showMessage('Lines sorted.', COLORS.fg, 2000);
  }

  function doWordCount(): void {
    const text = state.buffer.map(l => stripTags(l)).join('\n');
    const words = text.split(/\s+/).filter(w => w.length > 0);
    const chars = text.length;
    const lines = state.buffer.length;

    renderer.clearScreen();
    const top = 9;
    const left = 24;
    const width = 32;
    renderer.writeString(top, left, '┌' + '─── Word Count ───' + '─'.repeat(width - 19) + '┐', COLORS.dim, COLORS.bg);
    for (let r = 1; r <= 6; r++) {
      renderer.writeString(top + r, left, '│' + ' '.repeat(width) + '│', COLORS.dim, COLORS.bg);
    }
    renderer.writeString(top + 7, left, '└' + '─'.repeat(width) + '┘', COLORS.dim, COLORS.bg);

    renderer.writeString(top + 2, left + 3, `Words:       ${words.length}`, COLORS.fg, COLORS.bg);
    renderer.writeString(top + 3, left + 3, `Lines:       ${lines}`, COLORS.fg, COLORS.bg);
    renderer.writeString(top + 4, left + 3, `Characters:  ${chars}`, COLORS.fg, COLORS.bg);
    renderer.writeString(top + 6, left + 3, 'Press any key to return.', COLORS.dim, COLORS.bg);
    renderer.setCursor(null, null);
    renderer.flush();

    keyboard.setHandler(() => {
      keyboard.setHandler(handleKey);
      render();
    });
  }

  function toggleCase(): void {
    const line = rawLine(state.cursorRow);
    const rp = cursorRawPos();
    if (rp >= line.length) return;
    const ch = line[rp];
    const toggled = ch === ch.toUpperCase() ? ch.toLowerCase() : ch.toUpperCase();
    state.buffer[state.cursorRow] = line.substring(0, rp) + toggled + line.substring(rp + 1);
    state.modified = true;
  }

  // --- Save ---

  function doSave(callback?: () => void): void {
    if (state.filename) {
      saveFile(state.filename, state.buffer.join('\n'));
      state.modified = false;
      showMessage('Saved.', COLORS.fg, 2000);
      callback?.();
    } else {
      startPrompt('Save as: ', (name) => {
        if (name !== null && name.trim().length > 0) {
          let filename = name.trim();
          if (!filename.includes('.')) {
            filename += state.fileProfile === 'sfw' ? '.sfw' : '.txt';
          }
          state.filename = filename;
          saveFile(filename, state.buffer.join('\n'));
          state.modified = false;
          showMessage('Saved.', COLORS.fg, 2000);
          callback?.();
        }
      });
    }
  }

  function doExit(): void {
    if (state.modified) {
      startPrompt('Save changes? (Y/N/C): ', (value) => {
        if (value === null) return; // cancel
        const ch = value.trim().toUpperCase();
        if (ch === 'Y' || ch === '') {
          doSave(() => { cleanup(); onExit(); });
        } else if (ch === 'N') {
          cleanup(); onExit();
        }
        // C = cancel, just return to editor
      });
    } else {
      cleanup();
      onExit();
    }
  }

  function cleanup(): void {
    if (clockInterval !== undefined) {
      clearInterval(clockInterval);
      clockInterval = undefined;
    }
    if (messageTimeout !== undefined) {
      clearTimeout(messageTimeout);
      messageTimeout = undefined;
    }
  }

  // --- Key Handler ---

  function handleKey(action: KeyAction): void {
    if (promptMode) {
      handlePromptKey(action);
      return;
    }

    // Navigation
    if (action === 'arrow_up') { moveUp(); scrollToView(); render(); return; }
    if (action === 'arrow_down') { moveDown(); scrollToView(); render(); return; }
    if (action === 'arrow_left') { moveLeft(); scrollToView(); render(); return; }
    if (action === 'arrow_right') { moveRight(); scrollToView(); render(); return; }
    if (action === 'ctrl_left') { wordLeft(); scrollToView(); render(); return; }
    if (action === 'ctrl_right') { wordRight(); scrollToView(); render(); return; }
    if (action === 'home') { clearSelection(); state.cursorCol = 0; render(); return; }
    if (action === 'end') { clearSelection(); state.cursorCol = displayLen(state.cursorRow); render(); return; }
    if (action === 'ctrl_home') { clearSelection(); state.cursorRow = 0; state.cursorCol = 0; scrollToView(); render(); return; }
    if (action === 'ctrl_end') {
      clearSelection();
      state.cursorRow = state.buffer.length - 1;
      state.cursorCol = displayLen(state.cursorRow);
      scrollToView();
      render();
      return;
    }
    if (action === 'page_up') {
      clearSelection();
      viewportRow = Math.max(0, viewportRow - VISIBLE_LINES);
      state.cursorRow = Math.max(0, state.cursorRow - VISIBLE_LINES);
      clampCursor();
      render();
      return;
    }
    if (action === 'page_down') {
      clearSelection();
      viewportRow = Math.min(Math.max(0, state.buffer.length - VISIBLE_LINES), viewportRow + VISIBLE_LINES);
      state.cursorRow = Math.min(state.buffer.length - 1, state.cursorRow + VISIBLE_LINES);
      clampCursor();
      render();
      return;
    }

    // Shift+Arrow for selection
    if (action === 'shift_arrow_up') { extendSelection(() => { state.cursorRow = Math.max(0, state.cursorRow - 1); clampCursor(); }); scrollToView(); render(); return; }
    if (action === 'shift_arrow_down') { extendSelection(() => { state.cursorRow = Math.min(state.buffer.length - 1, state.cursorRow + 1); clampCursor(); }); scrollToView(); render(); return; }
    if (action === 'shift_arrow_left') { extendSelection(() => { if (state.cursorCol > 0) state.cursorCol--; }); render(); return; }
    if (action === 'shift_arrow_right') { extendSelection(() => { if (state.cursorCol < displayLen(state.cursorRow)) state.cursorCol++; }); render(); return; }

    // Editing
    if (action === 'enter') { insertNewline(); scrollToView(); render(); return; }
    if (action === 'backspace') { doBackspace(); scrollToView(); render(); return; }
    if (action === 'delete') { doDelete(); render(); return; }
    if (action === 'shift_delete') { doShiftDelete(); render(); return; }
    if (action === 'ctrl_shift_delete') { doCtrlShiftDelete(); render(); return; }
    if (action === 'insert') { state.insertMode = !state.insertMode; render(); return; }
    if (action === 'ctrl_z') { popUndo(); scrollToView(); render(); return; }
    if (action === 'shift_f3') { toggleCase(); render(); return; }

    // Tab
    if (action === 'tab') {
      clearSelection();
      // Find next tab stop
      for (let c = state.cursorCol + 1; c < 80; c++) {
        if (state.tabStops[c]) {
          if (state.insertMode) {
            const spaces = c - state.cursorCol;
            for (let s = 0; s < spaces; s++) insertChar(' ');
          } else {
            state.cursorCol = c;
          }
          break;
        }
      }
      render();
      return;
    }

    // Block ops
    if (action === 'ctrl_x') { doCut(); render(); return; }
    if (action === 'ctrl_c') { doCopy(); return; }
    if (action === 'ctrl_v') { doPaste(); scrollToView(); render(); return; }
    if (action === 'alt_w') { doWordCount(); return; }
    if (action === 'alt_a') { doAlphabetize(); render(); return; }

    // Search
    if (action === 'ctrl_f') { doFind(); return; }
    if (action === 'f3') { findNext(); return; }
    if (action === 'alt_h') { doReplace(); return; }
    if (action === 'alt_n') { replaceAndNext(); return; }
    if (action === 'alt_r') { globalReplace(); return; }

    // Formatting
    if (action === 'ctrl_b') { insertTagPair('\\B', '\\b'); render(); return; }
    if (action === 'ctrl_u') { insertTagPair('\\U', '\\u'); render(); return; }
    if (action === 'ctrl_g') { insertTagPair('\\G', '\\g'); render(); return; }
    if (action === 'ctrl_bracket_left') { insertSingleTag('\\[', false); render(); return; }
    if (action === 'ctrl_bracket_right') { insertSingleTag('\\]', false); render(); return; }
    if (action === 'ctrl_e') { insertSingleTag('\\E', true); render(); return; }
    if (action === 'ctrl_r') { insertSingleTag('\\R', true); render(); return; }
    if (action === 'ctrl_m') { insertSingleTag('\\M', false); render(); return; }
    if (action === 'ctrl_shift_h') { insertHeaderFooter('\\H:'); render(); return; }
    if (action === 'ctrl_shift_f') { insertHeaderFooter('\\F:'); render(); return; }
    if (action === 'ctrl_shift_e') { insertPageBreak(); scrollToView(); render(); return; }

    // Tab stops
    if (action === 'ctrl_t') { state.tabStops[state.cursorCol] = !state.tabStops[state.cursorCol]; render(); return; }
    if (action === 'ctrl_shift_t') { state.tabStops.fill(false); render(); return; }

    // Save
    if (action === 'ctrl_s') { doSave(); return; }

    // Exit
    if (action === 'escape') { doExit(); return; }

    // Printable char
    if (typeof action === 'object' && action.type === 'char') {
      insertChar(action.char);
      scrollToView();
      render();
      return;
    }
  }

  // Initialize
  keyboard.setHandler(handleKey);
  clampCursor();
  scrollToView();
  render();

  clockInterval = window.setInterval(() => {
    renderStatusBar();
    renderer.flush();
  }, 30000);
}
