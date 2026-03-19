import { TerminalRenderer } from '../terminal/renderer';
import { KeyboardHandler, KeyAction } from '../terminal/keyboard';
import { COLORS } from '../terminal/colors';
import { AppState } from '../state';

type MenuAction = 'create' | 'edit' | 'verify' | 'print' | 'global_format'
  | 'index1' | 'index2' | 'demo' | 'doctor' | 'quit';

export function showMainMenu(
  renderer: TerminalRenderer,
  keyboard: KeyboardHandler,
  state: AppState,
  onAction: (action: MenuAction) => void,
): void {
  let clockInterval: number | undefined;

  function render(): void {
    renderer.clearScreen();
    renderer.setCursor(null, null);

    // Top border
    const titleText = ' SAFARI WRITER ';
    const borderLeft = '┌' + '─'.repeat(30) + titleText + '─'.repeat(78 - 31 - titleText.length) + '┐';
    renderer.writeString(0, 0, borderLeft, COLORS.dim, COLORS.bg);
    // Write title bright
    renderer.writeString(0, 31, titleText, COLORS.bright, COLORS.bg, true);

    // Side borders
    for (let r = 1; r < 24; r++) {
      renderer.writeString(r, 0, '│', COLORS.dim, COLORS.bg);
      renderer.writeString(r, 79, '│', COLORS.dim, COLORS.bg);
    }

    // Bottom border
    renderer.writeString(24, 0, '└' + '─'.repeat(78) + '┘', COLORS.dim, COLORS.bg);

    // Column headers
    renderer.writeString(2, 5, 'WORDS', COLORS.bright, COLORS.bg, true);
    renderer.writeString(2, 26, 'FILES', COLORS.bright, COLORS.bg, true);
    renderer.writeString(2, 48, 'TOOLS', COLORS.bright, COLORS.bg, true);
    renderer.writeString(3, 5, '─────', COLORS.dim, COLORS.bg);
    renderer.writeString(3, 26, '─────', COLORS.dim, COLORS.bg);
    renderer.writeString(3, 48, '─────', COLORS.dim, COLORS.bg);

    // WORDS column
    writeMenuItem(4, 5, 'C', ' Create File');
    writeMenuItem(5, 5, 'E', ' Edit File');
    writeMenuItem(6, 5, 'V', ' Verify Spelling');
    writeMenuItem(7, 5, 'P', ' Print/Export');
    writeMenuItem(8, 5, 'G', ' Global Format');

    // FILES column
    writeMenuItem(4, 26, '1', ' Index Storage');
    writeMenuItem(5, 26, '2', ' Index Storage');

    // TOOLS column
    writeMenuItem(4, 48, 'T', ' Try Demo');
    writeMenuItem(5, 48, '?', ' Doctor');

    // Quit
    writeMenuItem(10, 5, 'Q', ' Quit (close tab)');

    // Status row
    const filename = state.filename || '[No File]';
    const profile = `[${state.fileProfile.toUpperCase()}]`;
    renderer.writeString(23, 3, filename, COLORS.fg, COLORS.bg);
    renderer.writeString(23, 3 + filename.length + 2, profile, COLORS.dim, COLORS.bg);

    const version = 'Safari Writer 0.1.0 Web';
    renderer.writeString(23, 79 - version.length - 1, version, COLORS.dim, COLORS.bg);

    drawClock();
    renderer.flush();
  }

  function writeMenuItem(row: number, col: number, key: string, rest: string): void {
    renderer.writeString(row, col, key, COLORS.bright, COLORS.bg, true);
    renderer.writeString(row, col + 1, rest, COLORS.fg, COLORS.bg);
  }

  function drawClock(): void {
    const now = new Date();
    const hh = String(now.getHours()).padStart(2, '0');
    const mm = String(now.getMinutes()).padStart(2, '0');
    renderer.writeString(23, 73, `${hh}:${mm}`, COLORS.dim, COLORS.bg);
  }

  function handleKey(action: KeyAction): void {
    if (typeof action === 'object' && action.type === 'char') {
      const ch = action.char.toUpperCase();
      switch (ch) {
        case 'C': cleanup(); onAction('create'); return;
        case 'E': cleanup(); onAction('edit'); return;
        case 'V': cleanup(); onAction('verify'); return;
        case 'P': cleanup(); onAction('print'); return;
        case 'G': cleanup(); onAction('global_format'); return;
        case '1': cleanup(); onAction('index1'); return;
        case '2': cleanup(); onAction('index2'); return;
        case 'T': cleanup(); onAction('demo'); return;
        case '?': cleanup(); onAction('doctor'); return;
        case 'Q': cleanup(); onAction('quit'); return;
      }
    }
  }

  function cleanup(): void {
    if (clockInterval !== undefined) {
      clearInterval(clockInterval);
      clockInterval = undefined;
    }
  }

  keyboard.setHandler(handleKey);
  render();

  // Update clock every 30 seconds
  clockInterval = window.setInterval(() => {
    drawClock();
    renderer.flush();
  }, 30000);
}
