export const TAG_GLYPHS: Record<string, string> = {
  '\\B':  '←',
  '\\b':  '←',
  '\\U':  '▄',
  '\\u':  '▄',
  '\\G':  'E',
  '\\g':  'E',
  '\\[':  '↑',
  '\\]':  '↓',
  '\\E':  '↔',
  '\\R':  '→→',
  '\\M':  '¶',
  '\\H:': 'H:',
  '\\F:': 'F:',
  '\\P':  '↡',
  '\\C':  '»',
  '\\_':  '_',
};

// All recognized tags sorted longest-first for greedy matching
const ALL_TAGS = Object.keys(TAG_GLYPHS).sort((a, b) => b.length - a.length);

export interface Segment {
  text: string;
  isTag: boolean;
  tag?: string;
}

export function parseLineSegments(line: string): Segment[] {
  const segments: Segment[] = [];
  let i = 0;
  while (i < line.length) {
    if (line[i] === '\\') {
      let matched = false;
      for (const tag of ALL_TAGS) {
        if (line.substring(i, i + tag.length) === tag) {
          segments.push({ text: TAG_GLYPHS[tag], isTag: true, tag });
          i += tag.length;
          matched = true;
          break;
        }
      }
      if (!matched) {
        segments.push({ text: line[i], isTag: false });
        i++;
      }
    } else {
      // Collect plain text until next backslash
      let end = i + 1;
      while (end < line.length && line[end] !== '\\') end++;
      segments.push({ text: line.substring(i, end), isTag: false });
      i = end;
    }
  }
  return segments;
}

export function insertTag(line: string, col: number, tag: string): string {
  // col is a *display* column; convert to raw string position
  const rawPos = displayColToRawPos(line, col);
  return line.substring(0, rawPos) + tag + line.substring(rawPos);
}

export function stripTags(text: string): string {
  let result = text;
  for (const tag of ALL_TAGS) {
    while (result.includes(tag)) {
      result = result.replace(tag, '');
    }
  }
  return result;
}

export function encodeBuffer(buffer: string[]): string {
  return buffer.join('\n');
}

export function decodeBuffer(content: string): string[] {
  const lines = content.split('\n');
  if (lines.length === 0) return [''];
  return lines;
}

// Convert a display column to a raw string position
export function displayColToRawPos(line: string, displayCol: number): number {
  let dc = 0;
  let i = 0;
  while (i < line.length && dc < displayCol) {
    if (line[i] === '\\') {
      let matched = false;
      for (const tag of ALL_TAGS) {
        if (line.substring(i, i + tag.length) === tag) {
          dc += TAG_GLYPHS[tag].length;
          i += tag.length;
          matched = true;
          break;
        }
      }
      if (!matched) {
        dc++;
        i++;
      }
    } else {
      dc++;
      i++;
    }
  }
  return i;
}

// Convert a raw string position to a display column
export function rawPosToDisplayCol(line: string, rawPos: number): number {
  let dc = 0;
  let i = 0;
  while (i < line.length && i < rawPos) {
    if (line[i] === '\\') {
      let matched = false;
      for (const tag of ALL_TAGS) {
        if (line.substring(i, i + tag.length) === tag) {
          dc += TAG_GLYPHS[tag].length;
          i += tag.length;
          matched = true;
          break;
        }
      }
      if (!matched) {
        dc++;
        i++;
      }
    } else {
      dc++;
      i++;
    }
  }
  return dc;
}

// Get display length of a line
export function displayLength(line: string): number {
  let len = 0;
  const segments = parseLineSegments(line);
  for (const seg of segments) {
    len += seg.text.length;
  }
  return len;
}
