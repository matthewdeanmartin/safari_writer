export const DEMO_SFW_CONTENT = `\\H:Safari Writer Web Demo
\\F:Page @P
\\E\\BSafari Writer Web\\b
\\EVersion 0.1.0
\\E\\Ua browser-based word processor\\u

Welcome to \\BSafari Writer\\b, a faithful recreation of the
classic \\BAtariWriter 80\\b word processor from 1985. This
version runs entirely in your browser — no server, no
signup, no downloads required.

\\BFormatting Features\\b

Safari Writer supports inline formatting tags that let you
style text the way the original did:

  \\BBold text\\b is toggled with \\BCtrl+B\\b.
  \\UUnderlined text\\u is toggled with \\BCtrl+U\\b.
  \\GElongated text\\g is toggled with \\BCtrl+G\\b.

You can also control line alignment:

\\E\\BThis line is centered\\b (Ctrl+E)

\\R\\BThis line is flush right\\b (Ctrl+R)

\\MThis paragraph is indented with the indent tag (Ctrl+M).
It adds a visual marker at the start of the line.

\\BNavigation\\b

  Arrow keys       Move cursor
  Ctrl+Left/Right  Jump by word
  Home / End       Start / end of line
  Ctrl+Home/End    Start / end of document
  Page Up / Down   Scroll by page

\\BEditing\\b

  Insert           Toggle insert / type-over mode
  Ctrl+Z           Undo (up to 50 levels)
  Ctrl+X           Cut selection
  Ctrl+C           Copy selection
  Ctrl+V           Paste
  Shift+Delete     Delete to end of line
  Tab              Jump to next tab stop
  Ctrl+T           Set/clear tab stop at cursor
  Ctrl+Shift+T     Clear all tab stops

\\P
\\E\\BPage Two — Search, Export & More\\b

\\BSearch & Replace\\b

  Ctrl+F           Find text
  F3               Find next occurrence
  Alt+H            Set replacement string
  Alt+N            Replace current and find next
  Alt+R            Global replace (all occurrences)

\\BBlock Operations\\b

Select text with Shift+Arrow keys, then:
  Ctrl+X           Cut to clipboard
  Ctrl+C           Copy to clipboard
  Ctrl+V           Paste from clipboard
  Alt+W            Word count
  Alt+A            Alphabetize selected lines

\\BFile Storage\\b

Your documents are saved in your browser's local storage.
Use \\BCtrl+S\\b to save at any time. Press \\B1\\b or \\B2\\b
from the main menu to browse your saved files.

\\BExport Options\\b

From the \\BPrint/Export\\b screen (press \\BP\\b from the main
menu or \\BCtrl+P\\b from the editor) you can export as:
  - \\BANSI Preview\\b — paginated view in the terminal
  - \\BPlain Text\\b (.txt) — tags stripped
  - \\BMarkdown\\b (.md) — tags converted to Markdown
  - \\BPDF\\b (.pdf) — generated via jsPDF
  - \\BPostScript\\b (.ps) — hand-rolled PS output

\\BGlobal Format\\b

Press \\BG\\b from the main menu to configure document-wide
settings: margins, line spacing, justification, page
length, paragraph indent, font style, and more.

\\BProofreader\\b

Press \\BV\\b from the main menu to spellcheck your document.
Choose \\BHighlight\\b to see all errors at once, or
\\BCorrect\\b to step through them one by one with
suggestions and replacement options.

\\R— End of Demo —
`;
