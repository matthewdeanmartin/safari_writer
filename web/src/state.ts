export interface GlobalFormat {
  topMargin: number;
  bottomMargin: number;
  leftMargin: number;
  rightMargin: number;
  lineSpacing: 'S' | 'D';
  doubleColumn: boolean;
  font: string;
  paragraphIndent: number;
  justification: boolean;
  pageNumbering: boolean;
  pageLength: number;
  pageWait: boolean;
}

export function defaultGlobalFormat(): GlobalFormat {
  return {
    topMargin: 3,
    bottomMargin: 3,
    leftMargin: 5,
    rightMargin: 75,
    lineSpacing: 'S',
    doubleColumn: false,
    font: 'STANDARD',
    paragraphIndent: 5,
    justification: false,
    pageNumbering: false,
    pageLength: 66,
    pageWait: false,
  };
}

export interface AppState {
  buffer: string[];
  cursorRow: number;
  cursorCol: number;
  insertMode: boolean;
  capsMode: boolean;
  clipboard: string;
  lastDeletedLine: string;
  fmt: GlobalFormat;
  filename: string | null;
  modified: boolean;
  fileProfile: 'sfw' | 'txt';
  selectionAnchor: [number, number] | null;
  searchString: string;
  replaceString: string;
  lastSearchRow: number;
  lastSearchCol: number;
  tabStops: boolean[];
  undoStack: string[][];
  keptSpellings: Set<string>;
}

export function defaultAppState(): AppState {
  const tabStops = new Array<boolean>(80).fill(false);
  // Default tab stops every 8 columns
  for (let i = 8; i < 80; i += 8) {
    tabStops[i] = true;
  }
  return {
    buffer: [''],
    cursorRow: 0,
    cursorCol: 0,
    insertMode: true,
    capsMode: false,
    clipboard: '',
    lastDeletedLine: '',
    fmt: defaultGlobalFormat(),
    filename: null,
    modified: false,
    fileProfile: 'sfw',
    selectionAnchor: null,
    searchString: '',
    replaceString: '',
    lastSearchRow: 0,
    lastSearchCol: 0,
    tabStops,
    undoStack: [],
    keptSpellings: new Set(),
  };
}
