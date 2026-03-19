import { TerminalRenderer } from '../terminal/renderer';
import { KeyboardHandler, KeyAction } from '../terminal/keyboard';
import { COLORS } from '../terminal/colors';
import { AppState, GlobalFormat } from '../state';

interface FieldDef {
  key: string;
  label: string;
  prop: keyof GlobalFormat;
  type: 'number' | 'toggle' | 'font';
  min?: number;
  max?: number;
  toggleValues?: string[];
}

const FIELDS: FieldDef[] = [
  { key: 'T', label: 'Top Margin', prop: 'topMargin', type: 'number', min: 0, max: 20 },
  { key: 'B', label: 'Bottom Margin', prop: 'bottomMargin', type: 'number', min: 0, max: 20 },
  { key: 'L', label: 'Left Margin', prop: 'leftMargin', type: 'number', min: 0, max: 40 },
  { key: 'R', label: 'Right Margin', prop: 'rightMargin', type: 'number', min: 40, max: 79 },
  { key: 'S', label: 'Line Spacing', prop: 'lineSpacing', type: 'toggle', toggleValues: ['S', 'D'] },
  { key: 'M', label: 'Double Column', prop: 'doubleColumn', type: 'toggle', toggleValues: ['N', 'Y'] },
  { key: 'G', label: 'Font', prop: 'font', type: 'font' },
  { key: 'I', label: 'Paragraph Indent', prop: 'paragraphIndent', type: 'number', min: 0, max: 20 },
  { key: 'J', label: 'Justification', prop: 'justification', type: 'toggle', toggleValues: ['N', 'Y'] },
  { key: 'Q', label: 'Page Numbering', prop: 'pageNumbering', type: 'toggle', toggleValues: ['N', 'Y'] },
  { key: 'Y', label: 'Page Length', prop: 'pageLength', type: 'number', min: 20, max: 132 },
  { key: 'W', label: 'Page Wait', prop: 'pageWait', type: 'toggle', toggleValues: ['N', 'Y'] },
];

const FONTS = ['STANDARD', 'DRAFT', 'BOLD'];

export function showGlobalFormat(
  renderer: TerminalRenderer,
  keyboard: KeyboardHandler,
  state: AppState,
  onDone: () => void,
): void {
  let editingField: FieldDef | null = null;
  let editBuffer = '';
  let fontPickerIndex = 0;

  function getDisplayValue(field: FieldDef): string {
    const val = state.fmt[field.prop];
    if (field.type === 'number') return String(val);
    if (field.type === 'font') return String(val);
    if (field.type === 'toggle') {
      if (field.prop === 'lineSpacing') return val as string;
      if (typeof val === 'boolean') return val ? 'Y' : 'N';
      return String(val);
    }
    return String(val);
  }

  function render(): void {
    renderer.clearScreen();

    // Border
    const title = ' GLOBAL FORMAT ';
    const padLeft = Math.floor((78 - title.length) / 2);
    const padRight = 78 - padLeft - title.length;
    renderer.writeString(0, 0, '╔' + '═'.repeat(padLeft) + title + '═'.repeat(padRight) + '╗', COLORS.dim, COLORS.bg);
    renderer.writeString(0, 1 + padLeft, title, COLORS.bright, COLORS.bg, true);
    for (let r = 1; r < 24; r++) {
      renderer.writeString(r, 0, '║', COLORS.dim, COLORS.bg);
      renderer.writeString(r, 79, '║', COLORS.dim, COLORS.bg);
    }
    renderer.writeString(24, 0, '╚' + '═'.repeat(78) + '╝', COLORS.dim, COLORS.bg);

    renderer.writeString(1, 3, 'Press the highlighted letter to change a value.', COLORS.fg, COLORS.bg);
    renderer.writeString(2, 3, 'Enter or Esc to return to editor.', COLORS.fg, COLORS.bg);
    renderer.writeString(3, 3, '─'.repeat(74), COLORS.dim, COLORS.bg);

    // Fields
    for (let i = 0; i < FIELDS.length; i++) {
      const f = FIELDS[i];
      const row = 4 + i;
      const isEditing = editingField === f;

      // Key letter
      renderer.writeString(row, 3, f.key, COLORS.bright, COLORS.bg, true);

      // Label
      renderer.writeString(row, 6, f.label.padEnd(18), COLORS.fg, COLORS.bg);

      // Value
      const displayVal = isEditing ? editBuffer : getDisplayValue(f);
      const valStr = `[${displayVal.padStart(f.type === 'font' ? 8 : 2)}]`;
      renderer.writeString(row, 25, valStr, isEditing ? COLORS.bright : COLORS.fg, COLORS.bg);

      // Hint
      let hint = '';
      if (f.type === 'number') {
        if (f.prop === 'topMargin' || f.prop === 'bottomMargin') hint = 'lines';
        else if (f.prop === 'leftMargin' || f.prop === 'rightMargin') hint = 'columns';
        else if (f.prop === 'paragraphIndent') hint = 'spaces';
        else if (f.prop === 'pageLength') hint = 'lines per page';
      } else if (f.prop === 'lineSpacing') {
        hint = 'S=Single  D=Double';
      } else if (f.prop === 'doubleColumn') {
        hint = 'Y=On  N=Off';
      } else if (f.prop === 'justification' || f.prop === 'pageNumbering' || f.prop === 'pageWait') {
        hint = 'Y=On  N=Off';
      }
      if (hint) {
        renderer.writeString(row, 36, hint, COLORS.dim, COLORS.bg);
      }
    }

    // Font picker
    if (editingField && editingField.type === 'font') {
      const pickerRow = 4 + FIELDS.indexOf(editingField);
      for (let fi = 0; fi < FONTS.length; fi++) {
        const r = pickerRow + fi;
        if (r >= 23) break;
        const sel = fi === fontPickerIndex;
        renderer.writeString(r, 36, (sel ? '> ' : '  ') + FONTS[fi], sel ? COLORS.bright : COLORS.fg, COLORS.bg);
      }
    }

    renderer.writeString(17, 3, '─'.repeat(74), COLORS.dim, COLORS.bg);
    renderer.writeString(23, 3, 'Enter/Esc = Done', COLORS.dim, COLORS.bg);

    if (editingField && editingField.type === 'number') {
      const row = 4 + FIELDS.indexOf(editingField);
      renderer.setCursor(row, 26 + editBuffer.length);
    } else {
      renderer.setCursor(null, null);
    }

    renderer.flush();
  }

  function setValue(field: FieldDef, rawValue: string): void {
    if (field.type === 'number') {
      const num = parseInt(rawValue, 10);
      if (isNaN(num)) return;
      const clamped = Math.max(field.min ?? 0, Math.min(field.max ?? 999, num));
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (state.fmt as any)[field.prop] = clamped;
    } else if (field.type === 'font') {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (state.fmt as any)[field.prop] = rawValue;
    }
  }

  function toggleField(field: FieldDef): void {
    if (field.prop === 'lineSpacing') {
      state.fmt.lineSpacing = state.fmt.lineSpacing === 'S' ? 'D' : 'S';
    } else if (typeof state.fmt[field.prop] === 'boolean') {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (state.fmt as any)[field.prop] = !state.fmt[field.prop];
    }
  }

  function handleKey(action: KeyAction): void {
    // Editing a numeric field
    if (editingField && editingField.type === 'number') {
      if (action === 'enter' || action === 'tab') {
        setValue(editingField, editBuffer);
        editingField = null;
        render();
        return;
      }
      if (action === 'escape') {
        editingField = null;
        render();
        return;
      }
      if (action === 'backspace') {
        editBuffer = editBuffer.slice(0, -1);
        render();
        return;
      }
      if (typeof action === 'object' && action.type === 'char' && /[0-9]/.test(action.char)) {
        if (editBuffer.length < 3) {
          editBuffer += action.char;
          render();
        }
        return;
      }
      return;
    }

    // Font picker mode
    if (editingField && editingField.type === 'font') {
      if (action === 'arrow_up') {
        fontPickerIndex = Math.max(0, fontPickerIndex - 1);
        render();
        return;
      }
      if (action === 'arrow_down') {
        fontPickerIndex = Math.min(FONTS.length - 1, fontPickerIndex + 1);
        render();
        return;
      }
      if (action === 'enter') {
        setValue(editingField, FONTS[fontPickerIndex]);
        editingField = null;
        render();
        return;
      }
      if (action === 'escape') {
        editingField = null;
        render();
        return;
      }
      return;
    }

    // Normal mode
    if (action === 'enter' || action === 'escape') {
      onDone();
      return;
    }

    if (typeof action === 'object' && action.type === 'char') {
      const ch = action.char.toUpperCase();
      const field = FIELDS.find(f => f.key === ch);
      if (field) {
        if (field.type === 'toggle') {
          toggleField(field);
          render();
        } else if (field.type === 'number') {
          editingField = field;
          editBuffer = String(state.fmt[field.prop]);
          render();
        } else if (field.type === 'font') {
          editingField = field;
          fontPickerIndex = FONTS.indexOf(state.fmt.font);
          if (fontPickerIndex < 0) fontPickerIndex = 0;
          render();
        }
      }
    }
  }

  keyboard.setHandler(handleKey);
  render();
}
