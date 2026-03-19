import { TerminalRenderer } from '../terminal/renderer';
import { KeyboardHandler, KeyAction } from '../terminal/keyboard';
import { COLORS } from '../terminal/colors';
import { AppState } from '../state';
import { SpellChecker, loadSpellChecker } from '../spell/checker';
import { stripTags } from '../format/codec';

interface WordLocation {
  row: number;
  start: number;  // column in stripped text
  end: number;
  word: string;
}

function tokenizeBuffer(buffer: string[]): WordLocation[] {
  const words: WordLocation[] = [];
  const re = /[a-zA-Z']+/g;
  for (let row = 0; row < buffer.length; row++) {
    const plain = stripTags(buffer[row]);
    let m: RegExpExecArray | null;
    while ((m = re.exec(plain)) !== null) {
      words.push({
        row,
        start: m.index,
        end: m.index + m[0].length,
        word: m[0],
      });
    }
  }
  return words;
}

export function showProofreader(
  renderer: TerminalRenderer,
  keyboard: KeyboardHandler,
  state: AppState,
  onDone: () => void,
): void {
  let checker: SpellChecker | null = null;

  function renderLoading(): void {
    renderer.clearScreen();
    renderer.writeString(12, 25, 'Loading dictionary...', COLORS.bright, COLORS.bg);
    renderer.setCursor(null, null);
    renderer.flush();
  }

  function renderSubMenu(): void {
    renderer.clearScreen();
    renderer.setCursor(null, null);

    const top = 10;
    const left = 25;
    const w = 30;
    renderer.writeString(top, left, '╔' + '══ PROOFREADER ══' + '═'.repeat(w - 17) + '╗', COLORS.dim, COLORS.bg);
    for (let r = 1; r <= 4; r++) {
      renderer.writeString(top + r, left, '║' + ' '.repeat(w) + '║', COLORS.dim, COLORS.bg);
    }
    renderer.writeString(top + 5, left, '╚' + '═'.repeat(w) + '╝', COLORS.dim, COLORS.bg);

    renderer.writeString(top + 1, left + 3, 'H', COLORS.bright, COLORS.bg, true);
    renderer.writeString(top + 1, left + 4, '  Highlight errors', COLORS.fg, COLORS.bg);
    renderer.writeString(top + 2, left + 3, 'C', COLORS.bright, COLORS.bg, true);
    renderer.writeString(top + 2, left + 4, '  Correct errors', COLORS.fg, COLORS.bg);
    renderer.writeString(top + 3, left + 3, 'Esc', COLORS.dim, COLORS.bg);
    renderer.writeString(top + 3, left + 8, '  Return to editor', COLORS.fg, COLORS.bg);

    renderer.flush();
  }

  function findErrors(): WordLocation[] {
    if (!checker) return [];
    const words = tokenizeBuffer(state.buffer);
    return words.filter(w => {
      if (w.word.length <= 1) return false;
      if (state.keptSpellings.has(w.word.toLowerCase())) return false;
      return !checker!.check(w.word);
    });
  }

  // --- Highlight mode ---
  function showHighlight(): void {
    const errors = findErrors();
    renderer.clearScreen();
    renderer.setCursor(null, null);

    // Render buffer with errors highlighted
    const errorSet = new Map<number, Set<number>>();
    for (const err of errors) {
      if (!errorSet.has(err.row)) errorSet.set(err.row, new Set());
      const s = errorSet.get(err.row)!;
      for (let c = err.start; c < err.end; c++) s.add(c);
    }

    const maxRows = 22;
    for (let i = 0; i < maxRows && i < state.buffer.length; i++) {
      const plain = stripTags(state.buffer[i]);
      const rowErrors = errorSet.get(i);
      for (let c = 0; c < Math.min(plain.length, 80); c++) {
        const isErr = rowErrors?.has(c);
        renderer.setCell(i, c, {
          char: plain[c],
          fg: isErr ? COLORS.inverse_fg : COLORS.fg,
          bg: isErr ? COLORS.inverse_bg : COLORS.bg,
        });
      }
    }

    const msg = `${errors.length} possible error${errors.length !== 1 ? 's' : ''} found. Press any key to return.`;
    renderer.writeString(23, 1, msg, COLORS.bright, COLORS.bg);
    renderer.flush();

    keyboard.setHandler(() => {
      keyboard.setHandler(subMenuHandler);
      renderSubMenu();
    });
  }

  // --- Correct mode ---
  function showCorrect(): void {
    const errors = findErrors();
    if (errors.length === 0) {
      renderer.clearScreen();
      renderer.writeString(12, 20, 'No spelling errors found!', COLORS.bright, COLORS.bg);
      renderer.writeString(14, 20, 'Press any key to return.', COLORS.dim, COLORS.bg);
      renderer.setCursor(null, null);
      renderer.flush();
      keyboard.setHandler(() => {
        keyboard.setHandler(subMenuHandler);
        renderSubMenu();
      });
      return;
    }

    let errorIdx = 0;
    let suggestions: string[] = [];
    let promptMode = false;
    let promptBuffer = '';

    function renderCorrectView(): void {
      renderer.clearScreen();
      renderer.setCursor(null, null);

      const err = errors[errorIdx];

      // Show context: the line with the error word highlighted
      const plain = stripTags(state.buffer[err.row]);
      for (let c = 0; c < Math.min(plain.length, 80); c++) {
        const isErr = c >= err.start && c < err.end;
        renderer.setCell(10, c, {
          char: plain[c],
          fg: isErr ? COLORS.inverse_fg : COLORS.fg,
          bg: isErr ? COLORS.inverse_bg : COLORS.bg,
        });
      }

      // Show suggestions
      suggestions = checker ? checker.suggest(err.word) : [];
      for (let i = 0; i < 5; i++) {
        const row = 14 + i;
        if (i < suggestions.length) {
          renderer.writeString(row, 5, `${i + 1} ${suggestions[i]}`, COLORS.fg, COLORS.bg);
        }
      }

      // Message bar
      const msg = `Unknown word: '${err.word}' (${errorIdx + 1} of ${errors.length} errors)`;
      renderer.writeString(22, 1, msg, COLORS.warning, COLORS.bg);

      if (promptMode) {
        renderer.writeString(23, 1, 'Replace with: ' + promptBuffer, COLORS.bright, COLORS.bg);
        renderer.setCursor(23, 15 + promptBuffer.length);
      } else {
        renderer.writeString(23, 1, 'R=Replace  K=Keep  A=Add to dict  S=Skip  Esc=Done', COLORS.dim, COLORS.bg);
      }

      renderer.flush();
    }

    function replaceWord(replacement: string): void {
      const err = errors[errorIdx];
      const raw = state.buffer[err.row];
      // Find the word in the raw line by scanning
      let rawPos = 0;
      let plainPos = 0;
      const rawLine = raw;
      // Advance through raw to find the position corresponding to err.start
      while (plainPos < err.start && rawPos < rawLine.length) {
        if (rawLine[rawPos] === '\\') {
          // Try to match a tag
          let matched = false;
          for (const tag of ['\\H:', '\\F:', '\\B', '\\b', '\\U', '\\u', '\\G', '\\g', '\\[', '\\]', '\\E', '\\R', '\\M', '\\P', '\\C', '\\_']) {
            if (rawLine.substring(rawPos, rawPos + tag.length) === tag) {
              rawPos += tag.length;
              matched = true;
              break;
            }
          }
          if (!matched) {
            rawPos++;
            plainPos++;
          }
        } else {
          rawPos++;
          plainPos++;
        }
      }
      const rawStart = rawPos;
      // Now advance through the word
      let wordPlain = 0;
      while (wordPlain < err.word.length && rawPos < rawLine.length) {
        if (rawLine[rawPos] === '\\') {
          let matched = false;
          for (const tag of ['\\H:', '\\F:', '\\B', '\\b', '\\U', '\\u', '\\G', '\\g', '\\[', '\\]', '\\E', '\\R', '\\M', '\\P', '\\C', '\\_']) {
            if (rawLine.substring(rawPos, rawPos + tag.length) === tag) {
              rawPos += tag.length;
              matched = true;
              break;
            }
          }
          if (!matched) {
            rawPos++;
            wordPlain++;
          }
        } else {
          rawPos++;
          wordPlain++;
        }
      }
      const rawEnd = rawPos;

      state.buffer[err.row] = rawLine.substring(0, rawStart) + replacement + rawLine.substring(rawEnd);
      state.modified = true;
    }

    function advance(): void {
      errorIdx++;
      if (errorIdx >= errors.length) {
        renderer.clearScreen();
        renderer.writeString(12, 20, 'Spellcheck complete!', COLORS.bright, COLORS.bg);
        renderer.writeString(14, 20, 'Press any key to return.', COLORS.dim, COLORS.bg);
        renderer.setCursor(null, null);
        renderer.flush();
        keyboard.setHandler(() => {
          keyboard.setHandler(subMenuHandler);
          renderSubMenu();
        });
        return;
      }
      renderCorrectView();
    }

    function correctHandler(action: KeyAction): void {
      if (promptMode) {
        if (action === 'escape') {
          promptMode = false;
          renderCorrectView();
          return;
        }
        if (action === 'enter') {
          if (promptBuffer.length > 0) {
            replaceWord(promptBuffer);
            promptMode = false;
            advance();
          }
          return;
        }
        if (action === 'backspace') {
          promptBuffer = promptBuffer.slice(0, -1);
          renderCorrectView();
          return;
        }
        if (typeof action === 'object' && action.type === 'char') {
          promptBuffer += action.char;
          renderCorrectView();
        }
        return;
      }

      if (action === 'escape') {
        keyboard.setHandler(subMenuHandler);
        renderSubMenu();
        return;
      }

      if (typeof action === 'object' && action.type === 'char') {
        const ch = action.char;
        // Number keys for suggestions
        if (ch >= '1' && ch <= '5') {
          const idx = parseInt(ch, 10) - 1;
          if (idx < suggestions.length) {
            replaceWord(suggestions[idx]);
            advance();
          }
          return;
        }
        const upper = ch.toUpperCase();
        if (upper === 'R') {
          promptMode = true;
          promptBuffer = '';
          renderCorrectView();
          return;
        }
        if (upper === 'K' || upper === 'S') {
          advance();
          return;
        }
        if (upper === 'A') {
          const err = errors[errorIdx];
          checker?.addWord(err.word);
          state.keptSpellings.add(err.word.toLowerCase());
          advance();
          return;
        }
      }
    }

    keyboard.setHandler(correctHandler);
    renderCorrectView();
  }

  // --- Sub-menu handler ---
  function subMenuHandler(action: KeyAction): void {
    if (action === 'escape') {
      onDone();
      return;
    }
    if (typeof action === 'object' && action.type === 'char') {
      const ch = action.char.toUpperCase();
      if (ch === 'H') { showHighlight(); return; }
      if (ch === 'C') { showCorrect(); return; }
    }
  }

  // --- Init ---
  renderLoading();
  loadSpellChecker().then((c) => {
    checker = c;
    keyboard.setHandler(subMenuHandler);
    renderSubMenu();
  }).catch(() => {
    renderer.clearScreen();
    renderer.writeString(12, 15, 'Failed to load dictionary. Press Esc to return.', COLORS.warning, COLORS.bg);
    renderer.setCursor(null, null);
    renderer.flush();
    keyboard.setHandler((action: KeyAction) => {
      if (action === 'escape') onDone();
    });
  });
}
