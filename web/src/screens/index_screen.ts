import { TerminalRenderer } from '../terminal/renderer';
import { KeyboardHandler, KeyAction } from '../terminal/keyboard';
import { COLORS } from '../terminal/colors';
import { listFiles, loadFile, deleteFile, getFileSize } from '../storage/files';

export interface IndexResult {
  action: 'load';
  filename: string;
  content: string;
}

export function showIndexScreen(
  renderer: TerminalRenderer,
  keyboard: KeyboardHandler,
  onLoad: (result: IndexResult) => void,
  onNew: () => void,
  onCancel: () => void,
): void {
  let files = listFiles();
  let cursor = 0;
  let scrollOffset = 0;
  const maxVisible = 16; // rows 5..20
  let promptMode: 'none' | 'delete' | 'new' = 'none';
  let promptBuffer = '';
  let deleteTarget = '';

  function render(): void {
    renderer.clearScreen();
    files = listFiles();

    // Border
    renderer.writeString(0, 0, '╔' + '═'.repeat(78) + '╗', COLORS.dim, COLORS.bg);
    for (let r = 1; r < 24; r++) {
      renderer.writeString(r, 0, '║', COLORS.dim, COLORS.bg);
      renderer.writeString(r, 79, '║', COLORS.dim, COLORS.bg);
    }
    renderer.writeString(24, 0, '╚' + '═'.repeat(78) + '╝', COLORS.dim, COLORS.bg);

    // Header
    renderer.writeString(1, 3, 'INDEX — SAFARI WRITER STORAGE', COLORS.bright, COLORS.bg, true);
    renderer.writeString(2, 3, '─'.repeat(74), COLORS.dim, COLORS.bg);
    renderer.writeString(3, 3, '#   FILENAME                        SIZE       SAVED', COLORS.fg, COLORS.bg);
    renderer.writeString(4, 3, '─   ────────                        ────       ─────', COLORS.dim, COLORS.bg);

    if (files.length === 0) {
      renderer.writeString(8, 10, 'No files saved yet. Press N to create one.', COLORS.dim, COLORS.bg);
    } else {
      for (let i = 0; i < maxVisible; i++) {
        const fi = scrollOffset + i;
        if (fi >= files.length) break;
        const name = files[fi];
        const row = 5 + i;
        const isSelected = fi === cursor;
        const fg = isSelected ? COLORS.inverse_fg : COLORS.fg;
        const bg = isSelected ? COLORS.inverse_bg : COLORS.bg;

        const size = getFileSize(name);
        const sizeStr = size < 1024 ? `${size} B` : `${(size / 1024).toFixed(1)} KB`;

        const entry = loadFile(name);
        const dateStr = entry ? entry.savedAt.substring(0, 16).replace('T', ' ') : '';

        const num = String(fi + 1).padStart(2);
        const line = `${num}  ${name.padEnd(30)}  ${sizeStr.padStart(10)}   ${dateStr}`;
        renderer.writeString(row, 3, line.substring(0, 74).padEnd(74), fg, bg);
      }
    }

    // Footer
    if (promptMode === 'none') {
      renderer.writeString(23, 3, 'Enter=Load  D=Delete  N=New  Esc=Back', COLORS.dim, COLORS.bg);
    } else if (promptMode === 'delete') {
      renderer.writeString(22, 3, `Delete ${deleteTarget}? (Y/N)`, COLORS.warning, COLORS.bg);
    } else if (promptMode === 'new') {
      renderer.writeString(22, 3, 'New filename: ' + promptBuffer + '_', COLORS.bright, COLORS.bg);
    }

    if (files.length > 0 && promptMode === 'none') {
      renderer.setCursor(5 + (cursor - scrollOffset), 3);
    } else if (promptMode === 'new') {
      renderer.setCursor(22, 17 + promptBuffer.length);
    } else {
      renderer.setCursor(null, null);
    }

    renderer.flush();
  }

  function handleKey(action: KeyAction): void {
    if (promptMode === 'delete') {
      if (action === 'escape' || (typeof action === 'object' && action.char.toLowerCase() === 'n')) {
        promptMode = 'none';
        render();
      } else if (typeof action === 'object' && action.char.toLowerCase() === 'y') {
        deleteFile(deleteTarget);
        files = listFiles();
        if (cursor >= files.length && cursor > 0) cursor--;
        promptMode = 'none';
        render();
      }
      return;
    }

    if (promptMode === 'new') {
      if (action === 'escape') {
        promptMode = 'none';
        render();
      } else if (action === 'enter') {
        if (promptBuffer.trim().length > 0) {
          promptMode = 'none';
          let name = promptBuffer.trim();
          if (!name.includes('.')) name += '.sfw';
          onNew();
          // The caller will handle creating the new file state
          // We just need to communicate the name back — do it through onLoad with empty content
          onLoad({ action: 'load', filename: name, content: '' });
        }
      } else if (action === 'backspace') {
        promptBuffer = promptBuffer.slice(0, -1);
        render();
      } else if (typeof action === 'object' && action.type === 'char') {
        if (/[A-Za-z0-9._\-]/.test(action.char) && promptBuffer.length < 64) {
          promptBuffer += action.char;
          render();
        }
      }
      return;
    }

    // Normal mode
    if (action === 'escape') {
      onCancel();
    } else if (action === 'arrow_up') {
      if (cursor > 0) {
        cursor--;
        if (cursor < scrollOffset) scrollOffset = cursor;
        render();
      }
    } else if (action === 'arrow_down') {
      if (cursor < files.length - 1) {
        cursor++;
        if (cursor >= scrollOffset + maxVisible) scrollOffset = cursor - maxVisible + 1;
        render();
      }
    } else if (action === 'enter') {
      if (files.length > 0) {
        const name = files[cursor];
        const entry = loadFile(name);
        if (entry) {
          onLoad({ action: 'load', filename: name, content: entry.content });
        }
      }
    } else if (typeof action === 'object' && action.type === 'char') {
      const ch = action.char.toLowerCase();
      if (ch === 'd' && files.length > 0) {
        deleteTarget = files[cursor];
        promptMode = 'delete';
        render();
      } else if (ch === 'n') {
        promptMode = 'new';
        promptBuffer = '';
        render();
      }
    }
  }

  keyboard.setHandler(handleKey);
  render();
}
