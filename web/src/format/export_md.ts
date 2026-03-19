export function exportMarkdown(buffer: string[]): string {
  const output: string[] = [];

  for (const rawLine of buffer) {
    let line = rawLine;

    // Page break
    if (line.trim() === '\\P') {
      output.push('---');
      continue;
    }

    // Header/Footer as HTML comments
    if (line.startsWith('\\H:')) {
      output.push(`<!-- header: ${line.substring(3)} -->`);
      continue;
    }
    if (line.startsWith('\\F:')) {
      output.push(`<!-- footer: ${line.substring(3)} -->`);
      continue;
    }

    // Check for line-level formatting before inline processing
    let prefix = '';
    let suffix = '';
    if (line.startsWith('\\E')) {
      prefix = '<div align="center">';
      suffix = '</div>';
      line = line.substring(2);
    } else if (line.startsWith('\\R')) {
      prefix = '<div align="right">';
      suffix = '</div>';
      line = line.substring(2);
    } else if (line.startsWith('\\M')) {
      prefix = '    '; // 4-space indent
      line = line.substring(2);
    }

    // Inline formatting
    line = line.replace(/\\B/g, '**');
    line = line.replace(/\\b/g, '**');
    line = line.replace(/\\U/g, '_');
    line = line.replace(/\\u/g, '_');
    line = line.replace(/\\G/g, '**');
    line = line.replace(/\\g/g, '**');
    line = line.replace(/\\\[/g, '<sup>');
    line = line.replace(/\\]/g, '</sup>');
    line = line.replace(/\\C/g, '');
    line = line.replace(/\\_/g, '');

    output.push(prefix + line + suffix);
  }

  return output.join('\n');
}
