import { jsPDF } from 'jspdf';
import { GlobalFormat } from '../state';
import { stripTags } from './codec';

export function exportPDF(buffer: string[], fmt: GlobalFormat, filename: string): void {
  const doc = new jsPDF({ unit: 'pt', format: 'letter' });
  // Letter: 612 × 792 pt. 72 pt = 1 inch.
  const leftPt = fmt.leftMargin * 7.2;
  const topPt = fmt.topMargin * 14;
  const bottomLimit = 792 - fmt.bottomMargin * 14;
  const lineHt = fmt.lineSpacing === 'D' ? 28 : 14;

  doc.setFont('Courier', 'normal');
  doc.setFontSize(12);

  let y = topPt + 14; // baseline offset

  for (const rawLine of buffer) {
    // Page break tag
    if (rawLine.trim() === '\\P') {
      doc.addPage();
      y = topPt + 14;
      continue;
    }

    const text = stripTags(rawLine);

    if (y + lineHt > bottomLimit) {
      doc.addPage();
      y = topPt + 14;
    }

    if (text.length > 0) {
      doc.text(text, leftPt, y);
    }
    y += lineHt;
  }

  const outName = filename ? filename.replace(/\.sfw$/, '.pdf') : 'document.pdf';
  doc.save(outName);
}
