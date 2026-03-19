import { TerminalRenderer } from '../terminal/renderer';
import { KeyboardHandler, KeyAction } from '../terminal/keyboard';
import { COLORS } from '../terminal/colors';

export function showStubScreen(
  renderer: TerminalRenderer,
  keyboard: KeyboardHandler,
  title: string,
  onEscape: () => void,
): void {
  renderer.clearScreen();
  const msg = `[ ${title} ]`;
  const col = Math.floor((80 - msg.length) / 2);
  renderer.writeString(11, col, msg, COLORS.bright, COLORS.bg, true);
  renderer.writeString(13, 20, 'Coming soon. Press Esc to return.', COLORS.fg, COLORS.bg);
  renderer.flush();

  keyboard.setHandler((action: KeyAction) => {
    if (action === 'escape') {
      onEscape();
    }
  });
}
