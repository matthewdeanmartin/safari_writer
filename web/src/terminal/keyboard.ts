export type KeyAction =
  | 'arrow_up' | 'arrow_down' | 'arrow_left' | 'arrow_right'
  | 'ctrl_left' | 'ctrl_right' | 'ctrl_up' | 'ctrl_down'
  | 'home' | 'end' | 'ctrl_home' | 'ctrl_end'
  | 'page_up' | 'page_down'
  | 'shift_arrow_up' | 'shift_arrow_down' | 'shift_arrow_left' | 'shift_arrow_right'
  | 'insert' | 'delete' | 'backspace' | 'tab' | 'enter'
  | 'shift_delete' | 'ctrl_shift_delete'
  | 'ctrl_z' | 'ctrl_s'
  | 'ctrl_x' | 'ctrl_c' | 'ctrl_v'
  | 'alt_w' | 'alt_a'
  | 'ctrl_f' | 'f3' | 'alt_h' | 'alt_n' | 'alt_r'
  | 'ctrl_b' | 'ctrl_u' | 'ctrl_g'
  | 'ctrl_bracket_left' | 'ctrl_bracket_right'
  | 'ctrl_e' | 'ctrl_r' | 'ctrl_m'
  | 'ctrl_t' | 'ctrl_shift_t'
  | 'ctrl_shift_h' | 'ctrl_shift_f' | 'ctrl_shift_s' | 'ctrl_shift_e'
  | 'ctrl_p' | 'f1' | 'f5' | 'escape'
  | 'shift_f3'
  | { type: 'char'; char: string };

export class KeyboardHandler {
  private handler: ((action: KeyAction) => void) | null = null;
  private element: HTMLElement | null = null;
  private listener: ((e: KeyboardEvent) => void) | null = null;

  mount(element: HTMLElement): void {
    this.element = element;
    element.tabIndex = 0;
    element.focus();

    this.listener = (e: KeyboardEvent) => this.onKey(e);
    document.addEventListener('keydown', this.listener);
  }

  unmount(): void {
    if (this.listener) {
      document.removeEventListener('keydown', this.listener);
      this.listener = null;
    }
    this.element = null;
  }

  setHandler(fn: (action: KeyAction) => void): void {
    this.handler = fn;
  }

  clearHandler(): void {
    this.handler = null;
  }

  focus(): void {
    this.element?.focus();
  }

  private onKey(e: KeyboardEvent): void {
    // Always prevent certain browser shortcuts from firing
    if (this.shouldPreventDefault(e)) {
      e.preventDefault();
    }

    if (!this.handler) return;

    const action = this.mapKey(e);
    if (action !== null) {
      e.preventDefault();
      this.handler(action);
    }
  }

  private shouldPreventDefault(e: KeyboardEvent): boolean {
    const { key, ctrlKey } = e;
    // Prevent browser shortcuts that conflict with the app
    if (ctrlKey) {
      if (['f', 'g', 'b', 'p', 'u', 'z', 'x', 'c', 'v', 's'].includes(key.toLowerCase())) return true;
    }
    if (key === 'Tab') return true;
    if (key === 'F1' || key === 'F3' || key === 'F5') return true;
    if (key === 'Backspace') return true;
    return false;
  }

  private mapKey(e: KeyboardEvent): KeyAction | null {
    const { key, ctrlKey, altKey, shiftKey } = e;

    // Function keys
    if (key === 'F1') return 'f1';
    if (key === 'F3' && shiftKey) return 'shift_f3';
    if (key === 'F3') return 'f3';
    if (key === 'F5') return 'f5';

    // Escape
    if (key === 'Escape') return 'escape';

    // Ctrl+Shift combos
    if (ctrlKey && shiftKey) {
      if (key === 'Delete') return 'ctrl_shift_delete';
      if (key === 'T' || key === 't') return 'ctrl_shift_t';
      if (key === 'H' || key === 'h') return 'ctrl_shift_h';
      if (key === 'F' || key === 'f') return 'ctrl_shift_f';
      if (key === 'S' || key === 's') return 'ctrl_shift_s';
      if (key === 'E' || key === 'e') return 'ctrl_shift_e';
    }

    // Ctrl combos
    if (ctrlKey && !altKey && !shiftKey) {
      switch (key) {
        case 'ArrowLeft': return 'ctrl_left';
        case 'ArrowRight': return 'ctrl_right';
        case 'ArrowUp': return 'ctrl_up';
        case 'ArrowDown': return 'ctrl_down';
        case 'Home': return 'ctrl_home';
        case 'End': return 'ctrl_end';
        case 'z': case 'Z': return 'ctrl_z';
        case 's': case 'S': return 'ctrl_s';
        case 'x': case 'X': return 'ctrl_x';
        case 'c': case 'C': return 'ctrl_c';
        case 'v': case 'V': return 'ctrl_v';
        case 'f': case 'F': return 'ctrl_f';
        case 'b': case 'B': return 'ctrl_b';
        case 'u': case 'U': return 'ctrl_u';
        case 'g': case 'G': return 'ctrl_g';
        case 'e': case 'E': return 'ctrl_e';
        case 'r': case 'R': return 'ctrl_r';
        case 'm': case 'M': return 'ctrl_m';
        case 't': case 'T': return 'ctrl_t';
        case 'p': case 'P': return 'ctrl_p';
        case '[': return 'ctrl_bracket_left';
        case ']': return 'ctrl_bracket_right';
      }
      return null;
    }

    // Alt combos
    if (altKey && !ctrlKey) {
      switch (key) {
        case 'w': case 'W': return 'alt_w';
        case 'a': case 'A': return 'alt_a';
        case 'h': case 'H': return 'alt_h';
        case 'n': case 'N': return 'alt_n';
        case 'r': case 'R': return 'alt_r';
      }
      return null;
    }

    // Shift+Arrow
    if (shiftKey && !ctrlKey && !altKey) {
      if (key === 'ArrowUp') return 'shift_arrow_up';
      if (key === 'ArrowDown') return 'shift_arrow_down';
      if (key === 'ArrowLeft') return 'shift_arrow_left';
      if (key === 'ArrowRight') return 'shift_arrow_right';
      if (key === 'Delete') return 'shift_delete';
      if (key === 'Insert') return 'insert';
    }

    // Plain keys
    if (!ctrlKey && !altKey) {
      switch (key) {
        case 'ArrowUp': return 'arrow_up';
        case 'ArrowDown': return 'arrow_down';
        case 'ArrowLeft': return 'arrow_left';
        case 'ArrowRight': return 'arrow_right';
        case 'Home': return 'home';
        case 'End': return 'end';
        case 'PageUp': return 'page_up';
        case 'PageDown': return 'page_down';
        case 'Insert': return 'insert';
        case 'Delete': return 'delete';
        case 'Backspace': return 'backspace';
        case 'Tab': return 'tab';
        case 'Enter': return 'enter';
      }

      // Printable character
      if (key.length === 1) {
        return { type: 'char', char: key };
      }
    }

    return null;
  }
}
