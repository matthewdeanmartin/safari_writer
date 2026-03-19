import { TerminalRenderer } from './terminal/renderer';
import { KeyboardHandler } from './terminal/keyboard';
import { AppState, defaultAppState } from './state';
import { decodeBuffer } from './format/codec';
import { DEMO_SFW_CONTENT } from './demo';
import { showMainMenu } from './screens/main_menu';
import { showIndexScreen } from './screens/index_screen';
import { showEditor } from './screens/editor';
import { showDoctorScreen } from './screens/doctor';
import { showGlobalFormat } from './screens/global_format';
import { showProofreader } from './screens/proofreader';
import { showPrintScreen } from './screens/print_screen';

export type Screen = 'main_menu' | 'editor' | 'index' | 'global_format' | 'proofreader' | 'print' | 'doctor';

export class App {
  private renderer: TerminalRenderer;
  private keyboard: KeyboardHandler;
  private state: AppState;

  constructor(canvas: HTMLCanvasElement) {
    this.renderer = new TerminalRenderer(canvas);
    this.keyboard = new KeyboardHandler();
    this.keyboard.mount(canvas);
    this.state = defaultAppState();

    // Warn on unload if modified
    window.addEventListener('beforeunload', (e) => {
      if (this.state.modified) {
        e.preventDefault();
      }
    });

    // Auto-refocus canvas when it loses focus
    canvas.addEventListener('blur', () => {
      setTimeout(() => canvas.focus(), 50);
    });
  }

  start(): void {
    this.navigate('main_menu');
  }

  navigate(screen: Screen): void {
    this.renderer.clearScreen();
    this.renderer.setCursor(null, null);
    this.keyboard.focus();

    // Update browser title
    document.title = this.state.filename
      ? `Safari Writer — ${this.state.filename}`
      : 'Safari Writer';

    switch (screen) {
      case 'main_menu':
        showMainMenu(this.renderer, this.keyboard, this.state, (action) => {
          switch (action) {
            case 'create':
              this.newDocument();
              this.navigate('editor');
              break;
            case 'edit':
            case 'index1':
            case 'index2':
              this.navigate('index');
              break;
            case 'verify':
              this.navigate('proofreader');
              break;
            case 'print':
              this.navigate('print');
              break;
            case 'global_format':
              this.navigate('global_format');
              break;
            case 'demo':
              this.loadDemo();
              this.navigate('editor');
              break;
            case 'doctor':
              this.navigate('doctor');
              break;
            case 'quit':
              alert('Close this browser tab to quit.');
              break;
          }
        });
        break;

      case 'index':
        showIndexScreen(this.renderer, this.keyboard,
          (result) => {
            this.state.buffer = decodeBuffer(result.content);
            this.state.filename = result.filename;
            this.state.modified = false;
            this.state.cursorRow = 0;
            this.state.cursorCol = 0;
            this.state.fileProfile = result.filename.endsWith('.txt') ? 'txt' : 'sfw';
            this.navigate('editor');
          },
          () => {
            // onNew — state already reset by index screen
          },
          () => {
            this.navigate('main_menu');
          },
        );
        break;

      case 'editor':
        showEditor(this.renderer, this.keyboard, this.state, () => {
          this.navigate('main_menu');
        });
        break;

      case 'doctor':
        showDoctorScreen(this.renderer, this.keyboard, () => {
          this.navigate('main_menu');
        });
        break;

      case 'global_format':
        showGlobalFormat(this.renderer, this.keyboard, this.state, () => {
          this.navigate('editor');
        });
        break;

      case 'proofreader':
        showProofreader(this.renderer, this.keyboard, this.state, () => {
          this.navigate('editor');
        });
        break;

      case 'print':
        showPrintScreen(this.renderer, this.keyboard, this.state, () => {
          this.navigate('editor');
        });
        break;
    }
  }

  private newDocument(): void {
    this.state.buffer = [''];
    this.state.filename = null;
    this.state.modified = false;
    this.state.cursorRow = 0;
    this.state.cursorCol = 0;
    this.state.selectionAnchor = null;
    this.state.undoStack = [];
    this.state.fileProfile = 'sfw';
  }

  private loadDemo(): void {
    this.state.buffer = decodeBuffer(DEMO_SFW_CONTENT);
    this.state.filename = 'demo.sfw';
    this.state.modified = false;
    this.state.cursorRow = 0;
    this.state.cursorCol = 0;
    this.state.selectionAnchor = null;
    this.state.undoStack = [];
    this.state.fileProfile = 'sfw';
  }
}
