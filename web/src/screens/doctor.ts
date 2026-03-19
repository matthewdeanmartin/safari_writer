import { TerminalRenderer } from '../terminal/renderer';
import { KeyboardHandler } from '../terminal/keyboard';
import { COLORS } from '../terminal/colors';
import { listFiles } from '../storage/files';

export function showDoctorScreen(
  renderer: TerminalRenderer,
  keyboard: KeyboardHandler,
  onDismiss: () => void,
): void {
  renderer.clearScreen();

  const files = listFiles();
  let storageUsed = 0;
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key && key.startsWith('safari_writer:')) {
      const val = localStorage.getItem(key);
      storageUsed += (key.length + (val ? val.length : 0)) * 2; // UTF-16
    }
  }
  const storageStr = storageUsed < 1024
    ? `${storageUsed} B`
    : storageUsed < 1024 * 1024
      ? `${(storageUsed / 1024).toFixed(1)} KB`
      : `${(storageUsed / (1024 * 1024)).toFixed(1)} MB`;

  const ua = navigator.userAgent;
  const browserMatch = ua.match(/(Chrome|Firefox|Safari|Edge)\/([\d.]+)/);
  const browser = browserMatch ? `${browserMatch[1]} ${browserMatch[2]}` : 'Unknown';

  const left = 22;
  const top = 7;
  const width = 38;

  // Border
  renderer.writeString(top - 1, left - 1, '┌' + '─'.repeat(width) + '┐', COLORS.dim, COLORS.bg);
  for (let r = 0; r < 10; r++) {
    renderer.writeString(top + r, left - 1, '│', COLORS.dim, COLORS.bg);
    renderer.writeString(top + r, left + width, '│', COLORS.dim, COLORS.bg);
  }
  renderer.writeString(top + 10, left - 1, '└' + '─'.repeat(width) + '┘', COLORS.dim, COLORS.bg);

  // Title
  const title = '─── Doctor ───';
  renderer.writeString(top - 1, left + Math.floor((width - title.length) / 2), title, COLORS.bright, COLORS.bg);

  // Content
  const lines = [
    `Platform:       Browser / Web`,
    `Storage:        localStorage`,
    `Files:          ${files.length} saved`,
    `Storage used:   ${storageStr}`,
    `Browser:        ${browser.substring(0, 22)}`,
    ``,
    `Version:        Safari Writer 0.1.0`,
    ``,
    `Press any key to return.`,
  ];

  for (let i = 0; i < lines.length; i++) {
    const color = i === lines.length - 1 ? COLORS.dim : COLORS.fg;
    renderer.writeString(top + i + 1, left + 1, lines[i].padEnd(width - 2), color, COLORS.bg);
  }

  renderer.flush();

  keyboard.setHandler(() => {
    onDismiss();
  });
}
