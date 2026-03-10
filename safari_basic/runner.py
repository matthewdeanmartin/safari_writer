"""MacroRunner — load a .BAS file, inject context, run, return output."""

from __future__ import annotations

import io
from pathlib import Path
from typing import TYPE_CHECKING

from safari_basic.interpreter import SafariBasic, BasicError
if TYPE_CHECKING:
    from safari_basic.context import MacroContext

__all__ = ["MacroRunner", "run_macro"]

# Maximum lines from the document we pre-inject as individual variables.
_MAX_DOC_LINES = 200


def run_macro(
    path: Path,
    context: MacroContext,
) -> tuple[str, str]:
    """Load and run a .BAS macro file against *context*.

    Returns ``(output, error)`` where *error* is an empty string on success.
    The caller should insert *output* into the document / create a Fed draft.
    """
    try:
        code = path.read_text(encoding="utf-8")
    except OSError as exc:
        return "", f"Cannot read macro: {exc}"

    # Capture PRINT output
    buf = io.StringIO()
    interp = SafariBasic(out_stream=buf)

    # Load program lines
    interp.reset()
    for raw in code.splitlines():
        interp.add_program_line(raw.strip())

    # Inject context variables after reset so they aren't cleared
    variables = context.build_variable_map()
    for name, value in variables.items():
        try:
            interp.inject_variable(name, value)  # type: ignore[arg-type]
        except Exception:
            pass  # skip variables the interpreter can't handle

    # Pre-inject document lines as DOC1$ … DOC200$
    doc_lines = context.document_lines[:_MAX_DOC_LINES]
    for i in range(1, _MAX_DOC_LINES + 1):
        line = doc_lines[i - 1] if i <= len(doc_lines) else ""
        try:
            interp.inject_variable(f"DOC{i}$", line)
        except Exception:
            pass

    # Pre-inject selected lines as SEL1$ … SELN$
    for i, line in enumerate(context.selected_lines(), start=1):
        try:
            interp.inject_variable(f"SEL{i}$", line)
        except Exception:
            pass

    try:
        interp.run_program()
    except BasicError as exc:
        return "", f"MACRO ERROR: {exc}"
    except Exception as exc:  # noqa: BLE001
        return "", f"MACRO ERROR: {exc}"

    output = buf.getvalue()
    # Strip trailing newline so caller controls final line spacing
    if output.endswith("\n"):
        output = output[:-1]
    context.output_lines = output.splitlines()
    return output, ""


class MacroRunner:
    """Stateless helper — thin wrapper around ``run_macro``."""

    @staticmethod
    def build_context(
        document_lines: list[str],
        cursor_row: int,
        cursor_col: int,
        selection_start: tuple[int, int] | None = None,
        selection_end: tuple[int, int] | None = None,
        clipboard: str = "",
        current_post: object | None = None,
    ) -> MacroContext:
        from safari_basic.context import MacroContext
        return MacroContext(
            document_lines=list(document_lines),
            cursor_row=cursor_row,
            cursor_col=cursor_col,
            selection_start=selection_start,
            selection_end=selection_end,
            clipboard=clipboard,
            current_post=current_post,
        )

    @staticmethod
    def run(path: Path, context: MacroContext) -> tuple[str, str]:
        return run_macro(path, context)
