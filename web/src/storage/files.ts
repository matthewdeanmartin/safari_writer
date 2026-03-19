const PREFIX = 'safari_writer:file:';
const INDEX_KEY = 'safari_writer:index';

export interface FileEntry {
  name: string;
  content: string;
  savedAt: string;
}

function getIndex(): string[] {
  try {
    const raw = localStorage.getItem(INDEX_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as string[];
  } catch {
    return [];
  }
}

function setIndex(names: string[]): void {
  names.sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()));
  localStorage.setItem(INDEX_KEY, JSON.stringify(names));
}

export function listFiles(): string[] {
  return getIndex();
}

export function loadFile(name: string): FileEntry | null {
  const raw = localStorage.getItem(PREFIX + name);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as FileEntry;
  } catch {
    return null;
  }
}

export function saveFile(name: string, content: string): void {
  const entry: FileEntry = {
    name,
    content,
    savedAt: new Date().toISOString(),
  };
  try {
    localStorage.setItem(PREFIX + name, JSON.stringify(entry));
  } catch (e) {
    if (e instanceof DOMException && e.name === 'QuotaExceededError') {
      throw new Error('Storage full!');
    }
    throw e;
  }
  const index = getIndex();
  if (!index.includes(name)) {
    index.push(name);
    setIndex(index);
  }
}

export function deleteFile(name: string): void {
  localStorage.removeItem(PREFIX + name);
  const index = getIndex().filter(n => n !== name);
  setIndex(index);
}

export function getFileSize(name: string): number {
  const raw = localStorage.getItem(PREFIX + name);
  return raw ? raw.length : 0;
}

export function downloadBlob(filename: string, content: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
