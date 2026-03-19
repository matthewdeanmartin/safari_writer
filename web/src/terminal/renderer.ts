import { COLORS } from './colors';

export interface Cell {
  char: string;
  fg: string;
  bg: string;
  bold?: boolean;
  underline?: boolean;
}

function defaultCell(): Cell {
  return { char: ' ', fg: COLORS.fg, bg: COLORS.bg };
}

export class TerminalRenderer {
  readonly cols = 80;
  readonly rows = 25;

  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private grid: Cell[][];
  private dirty: boolean[][];
  private cellW = 0;
  private cellH = 0;
  private cursorRow: number | null = null;
  private cursorCol: number | null = null;
  private cursorVisible = true;
  private blinkInterval: number;
  private fontFamily = "'Courier New', monospace";

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas;
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Could not get 2d context');
    this.ctx = ctx;

    this.grid = [];
    this.dirty = [];
    for (let r = 0; r < this.rows; r++) {
      this.grid[r] = [];
      this.dirty[r] = [];
      for (let c = 0; c < this.cols; c++) {
        this.grid[r][c] = defaultCell();
        this.dirty[r][c] = true;
      }
    }

    this.resize();
    window.addEventListener('resize', () => this.resize());

    this.blinkInterval = window.setInterval(() => {
      if (this.cursorRow !== null) {
        this.cursorVisible = !this.cursorVisible;
        this.drawCursor();
      }
    }, 500);
  }

  private resize(): void {
    const dpr = window.devicePixelRatio || 1;
    const maxW = window.innerWidth * 0.95;
    const maxH = window.innerHeight * 0.95;
    const aspect = this.cols / this.rows;

    let w = maxW;
    let h = w / aspect;
    if (h > maxH) {
      h = maxH;
      w = h * aspect;
    }

    this.cellW = Math.floor(w / this.cols);
    this.cellH = Math.floor(h / this.rows);
    w = this.cellW * this.cols;
    h = this.cellH * this.rows;

    this.canvas.style.width = w + 'px';
    this.canvas.style.height = h + 'px';
    this.canvas.width = w * dpr;
    this.canvas.height = h * dpr;
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    this.markAllDirty();
    this.flush();
  }

  private markAllDirty(): void {
    for (let r = 0; r < this.rows; r++) {
      for (let c = 0; c < this.cols; c++) {
        this.dirty[r][c] = true;
      }
    }
  }

  setCell(row: number, col: number, cell: Cell): void {
    if (row < 0 || row >= this.rows || col < 0 || col >= this.cols) return;
    const existing = this.grid[row][col];
    if (existing.char === cell.char && existing.fg === cell.fg &&
        existing.bg === cell.bg && existing.bold === cell.bold &&
        existing.underline === cell.underline) return;
    this.grid[row][col] = { ...cell };
    this.dirty[row][col] = true;
  }

  writeString(row: number, col: number, text: string, fg: string, bg: string, bold?: boolean): void {
    for (let i = 0; i < text.length; i++) {
      if (col + i >= this.cols) break;
      this.setCell(row, col + i, { char: text[i], fg, bg, bold });
    }
  }

  clearRow(row: number, bg?: string): void {
    for (let c = 0; c < this.cols; c++) {
      this.setCell(row, c, { char: ' ', fg: COLORS.fg, bg: bg ?? COLORS.bg });
    }
  }

  clearScreen(bg?: string): void {
    for (let r = 0; r < this.rows; r++) {
      this.clearRow(r, bg);
    }
  }

  setCursor(row: number | null, col: number | null): void {
    if (this.cursorRow !== null && this.cursorCol !== null) {
      this.dirty[this.cursorRow][this.cursorCol] = true;
    }
    this.cursorRow = row;
    this.cursorCol = col;
    this.cursorVisible = true;
    if (row !== null && col !== null && row >= 0 && row < this.rows && col >= 0 && col < this.cols) {
      this.dirty[row][col] = true;
    }
  }

  flush(): void {
    const ctx = this.ctx;
    const cw = this.cellW;
    const ch = this.cellH;
    const fontSize = Math.max(10, Math.floor(ch * 0.75));

    for (let r = 0; r < this.rows; r++) {
      for (let c = 0; c < this.cols; c++) {
        if (!this.dirty[r][c]) continue;
        this.dirty[r][c] = false;
        const cell = this.grid[r][c];
        const x = c * cw;
        const y = r * ch;

        ctx.fillStyle = cell.bg;
        ctx.fillRect(x, y, cw, ch);

        if (cell.char && cell.char !== ' ') {
          ctx.fillStyle = cell.fg;
          const weight = cell.bold ? 'bold ' : '';
          ctx.font = `${weight}${fontSize}px ${this.fontFamily}`;
          ctx.textBaseline = 'top';
          const textX = x + Math.floor((cw - ctx.measureText(cell.char).width) / 2);
          const textY = y + Math.floor((ch - fontSize) / 2);
          ctx.fillText(cell.char, textX, textY);
        }

        if (cell.underline) {
          ctx.fillStyle = cell.fg;
          ctx.fillRect(x, y + ch - 2, cw, 1);
        }
      }
    }
    this.drawCursor();
  }

  private drawCursor(): void {
    if (this.cursorRow === null || this.cursorCol === null) return;
    if (this.cursorRow < 0 || this.cursorRow >= this.rows) return;
    if (this.cursorCol < 0 || this.cursorCol >= this.cols) return;

    const r = this.cursorRow;
    const c = this.cursorCol;
    const x = c * this.cellW;
    const y = r * this.cellH;
    const cell = this.grid[r][c];
    const fontSize = Math.max(10, Math.floor(this.cellH * 0.75));

    // Redraw the cell background
    this.ctx.fillStyle = cell.bg;
    this.ctx.fillRect(x, y, this.cellW, this.cellH);

    if (this.cursorVisible) {
      // Draw block cursor
      this.ctx.fillStyle = COLORS.cursor;
      this.ctx.fillRect(x, y, this.cellW, this.cellH);

      // Draw character on top in inverse
      if (cell.char && cell.char !== ' ') {
        this.ctx.fillStyle = COLORS.bg;
        this.ctx.font = `${fontSize}px ${this.fontFamily}`;
        this.ctx.textBaseline = 'top';
        const textX = x + Math.floor((this.cellW - this.ctx.measureText(cell.char).width) / 2);
        const textY = y + Math.floor((this.cellH - fontSize) / 2);
        this.ctx.fillText(cell.char, textX, textY);
      }
    } else {
      // Cursor hidden phase — just draw normal cell
      if (cell.char && cell.char !== ' ') {
        this.ctx.fillStyle = cell.fg;
        this.ctx.font = `${fontSize}px ${this.fontFamily}`;
        this.ctx.textBaseline = 'top';
        const textX = x + Math.floor((this.cellW - this.ctx.measureText(cell.char).width) / 2);
        const textY = y + Math.floor((this.cellH - fontSize) / 2);
        this.ctx.fillText(cell.char, textX, textY);
      }
    }
  }

  destroy(): void {
    clearInterval(this.blinkInterval);
  }
}
