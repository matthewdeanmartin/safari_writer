import { GlobalFormat } from '../state';
import { stripTags } from './codec';

export function exportPS(buffer: string[], fmt: GlobalFormat, filename: string): string {
  const lines: string[] = [];
  lines.push('%!PS-Adobe-3.0');
  lines.push('%%Title: ' + filename);
  lines.push('%%Pages: (atend)');
  lines.push('%%EndComments');
  lines.push('/Courier findfont 12 scalefont setfont');

  let pageNum = 1;
  let y = 720 - fmt.topMargin * 14;
  const x = fmt.leftMargin * 7.2 + 36; // 36pt = 0.5in base offset
  const lineHt = fmt.lineSpacing === 'D' ? 28 : 14;
  const bottomLimit = fmt.bottomMargin * 14 + 36;

  lines.push(`%%Page: ${pageNum} ${pageNum}`);

  for (const rawLine of buffer) {
    // Page break tag
    if (rawLine.trim() === '\\P') {
      lines.push('showpage');
      pageNum++;
      lines.push(`%%Page: ${pageNum} ${pageNum}`);
      y = 720 - fmt.topMargin * 14;
      continue;
    }

    const text = stripTags(rawLine).replace(/[()\\]/g, '\\$&'); // escape PS special chars

    if (y < bottomLimit) {
      lines.push('showpage');
      pageNum++;
      lines.push(`%%Page: ${pageNum} ${pageNum}`);
      y = 720 - fmt.topMargin * 14;
    }

    lines.push(`${x} ${y} moveto (${text}) show`);
    y -= lineHt;
  }

  lines.push('showpage');
  lines.push('%%Trailer');
  lines.push(`%%Pages: ${pageNum}`);
  lines.push('%%EOF');

  return lines.join('\n');
}
