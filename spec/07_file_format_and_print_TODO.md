# File Format and Print TODO

These items are described in `spec/07_file_format_and_print.md` but are still missing or only partially implemented.

## 1. Interactive form filling at print/export time

Spec intent:

- form blanks should support a print-time prompt/fill workflow

Current implementation:

- form blanks render as placeholders such as `[________]`
- there is no interactive "fill the blanks before export" workflow

Implementation references:

- `safari_writer/screens/print_screen.py`
- `safari_writer/export_md.py`
- `safari_writer/export_ps.py`

## 2. Chain-file execution during print/export

Spec intent:

- chain markers should pull additional file content into the print/export flow

Current implementation:

- ANSI preview shows a note such as `>>> Chain: ...`
- Markdown export preserves the chain as a comment marker
- there is no confirmed include-and-render chain expansion in the export path

Implementation references:

- `safari_writer/screens/print_screen.py`
- `safari_writer/export_md.py`
- `safari_writer/export_ps.py`
- `safari_writer/screens/editor.py`
