"""Argparse-based CLI entrypoint for Safari Writer."""

from __future__ import annotations

import argparse
import json
import os
import sys
from importlib import metadata
from pathlib import Path

from safari_writer.cli_types import StartupRequest
from safari_writer.ansi_preview import extract_ansi_page, render_ansi_preview
from safari_writer.document_io import load_document_buffer, load_document_state
from safari_writer.format_codec import decode_sfw, encode_sfw, strip_controls
from safari_writer.mail_merge_db import (
    MailMergeDB,
    apply_mail_merge_to_buffer,
    inspect_mail_merge_db,
    load_mail_merge_db,
    save_mail_merge_db,
    validate_mail_merge_data,
)
from safari_writer.proofing import (
    check_word,
    extract_words,
    load_personal_dictionary,
    make_checker,
    suggest_words,
)
from safari_writer.splash import maybe_show_splash
from safari_writer.state import AppState, GlobalFormat

__all__ = ["build_parser", "build_startup_request", "main", "parse_args"]

TOP_LEVEL_COMMANDS = {"tui", "export", "proof", "format", "mail-merge"}


def _version_string() -> str:
    try:
        return metadata.version("safari-writer")
    except metadata.PackageNotFoundError:
        return "0.1.0"


def build_parser() -> argparse.ArgumentParser:
    """Build the root CLI parser."""

    parser = argparse.ArgumentParser(
        prog="safari-writer",
        description="Safari Writer text editor and utilities.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {_version_string()}",
    )
    parser.add_argument("--cwd", help="Resolve relative paths as if launched from PATH.")
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Default text encoding for headless file I/O.",
    )
    parser.add_argument(
        "--no-splash",
        action="store_true",
        help="Skip the startup splash screen for TUI launches.",
    )
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument("-q", "--quiet", action="store_true", help="Suppress status output.")
    verbosity.add_argument("-v", "--verbose", action="store_true", help="Emit extra status output.")

    subparsers = parser.add_subparsers(dest="command")

    tui_parser = subparsers.add_parser("tui", help="Launch the Textual interface at a specific destination.")
    tui_subparsers = tui_parser.add_subparsers(dest="tui_command", required=True)

    tui_menu = tui_subparsers.add_parser("menu", help="Open the main menu.")
    _add_tui_file_option(tui_menu)
    _add_tui_read_only_option(tui_menu)
    tui_menu.set_defaults(handler=_handle_tui_command)

    tui_edit = tui_subparsers.add_parser("edit", help="Open directly in the editor.")
    edit_source = tui_edit.add_mutually_exclusive_group()
    edit_source.add_argument("--file", help="Load a document before entering the editor.")
    edit_source.add_argument("--new", action="store_true", help="Open a blank document.")
    _add_tui_read_only_option(tui_edit)
    tui_edit.add_argument("--cursor-line", type=int, help="Initial 1-based cursor line.")
    tui_edit.add_argument("--cursor-column", type=int, help="Initial 1-based cursor column.")
    tui_edit.set_defaults(handler=_handle_tui_command)

    tui_proof = tui_subparsers.add_parser("proofreader", help="Open directly in the proofreader.")
    _add_tui_file_option(tui_proof)
    _add_tui_read_only_option(tui_proof)
    tui_proof.add_argument("--mode", choices=["highlight", "print", "correct", "search"])
    tui_proof.add_argument(
        "--personal-dict",
        action="append",
        default=[],
        help="Load a personal dictionary file before startup.",
    )
    tui_proof.set_defaults(handler=_handle_tui_command)

    tui_global = tui_subparsers.add_parser("global-format", help="Open directly in Global Format.")
    _add_tui_file_option(tui_global)
    _add_tui_read_only_option(tui_global)
    tui_global.set_defaults(handler=_handle_tui_command)

    tui_mail_merge = tui_subparsers.add_parser("mail-merge", help="Open directly in Mail Merge.")
    _add_tui_read_only_option(tui_mail_merge)
    tui_mail_merge.add_argument("--database", help="Load a mail-merge database before startup.")
    tui_mail_merge.add_argument(
        "--mode",
        choices=["menu", "enter", "update", "format", "subset"],
        default="menu",
    )
    tui_mail_merge.set_defaults(handler=_handle_tui_command)

    tui_print = tui_subparsers.add_parser("print", help="Open directly in print/export flow.")
    _add_tui_file_option(tui_print)
    _add_tui_read_only_option(tui_print)
    tui_print.add_argument("--target", choices=["ansi", "markdown", "postscript"])
    tui_print.set_defaults(handler=_handle_tui_command)

    tui_index_current = tui_subparsers.add_parser("index-current", help="Open the current-folder index.")
    tui_index_current.add_argument("--path", help="Directory to browse.")
    tui_index_current.set_defaults(handler=_handle_tui_command)

    tui_index_external = tui_subparsers.add_parser("index-external", help="Open the external-drive index.")
    tui_index_external.set_defaults(handler=_handle_tui_command)

    tui_safari_dos = tui_subparsers.add_parser("safari-dos", help="Open Safari DOS inside Safari Writer.")
    tui_safari_dos.add_argument("--path", help="Directory to browse.")
    tui_safari_dos.set_defaults(handler=_handle_tui_command)

    export_parser = subparsers.add_parser("export", help="Run headless export commands.")
    export_subparsers = export_parser.add_subparsers(dest="export_command", required=True)

    export_markdown = export_subparsers.add_parser("markdown", help="Export a document to Markdown.")
    _add_export_input(export_markdown)
    _add_output_flags(export_markdown, "Markdown")
    export_markdown.add_argument("--merge-db", help="Optional mail-merge database to apply.")
    export_markdown.set_defaults(handler=_handle_export_markdown)

    export_postscript = export_subparsers.add_parser("postscript", help="Export a document to PostScript.")
    _add_export_input(export_postscript)
    export_postscript.add_argument("-o", "--output", help="Destination .ps file.")
    export_postscript.add_argument("--merge-db", help="Optional mail-merge database to apply.")
    export_postscript.set_defaults(handler=_handle_export_postscript)

    export_ansi = export_subparsers.add_parser("ansi", help="Render ANSI preview output headlessly.")
    _add_export_input(export_ansi)
    export_ansi.add_argument("--page", type=int, help="Render a single 1-based page.")
    export_ansi.add_argument("--stdout", action="store_true", help="Write rendered ANSI to stdout.")
    export_ansi.set_defaults(handler=_handle_export_ansi)

    proof_parser = subparsers.add_parser("proof", help="Run headless proofing commands.")
    proof_subparsers = proof_parser.add_subparsers(dest="proof_command", required=True)

    proof_check = proof_subparsers.add_parser("check", help="Return whether a document contains spelling errors.")
    proof_check.add_argument("input", help="Source document.")
    proof_check.add_argument("--personal-dict", action="append", default=[])
    proof_check.set_defaults(handler=_handle_proof_check)

    proof_list = proof_subparsers.add_parser("list", help="List spelling issues.")
    proof_list.add_argument("input", help="Source document.")
    proof_list.add_argument("--personal-dict", action="append", default=[])
    proof_list.add_argument("--json", action="store_true", dest="as_json")
    proof_list.set_defaults(handler=_handle_proof_list)

    proof_suggest = proof_subparsers.add_parser("suggest", help="Suggest spellings for a word.")
    proof_suggest.add_argument("word")
    proof_suggest.set_defaults(handler=_handle_proof_suggest)

    format_parser = subparsers.add_parser("format", help="Use the .sfw format codec directly.")
    format_subparsers = format_parser.add_subparsers(dest="format_command", required=True)

    format_encode = format_subparsers.add_parser("encode", help="Encode plain text as .sfw.")
    format_encode.add_argument("input")
    format_encode.add_argument("-o", "--output")
    format_encode.set_defaults(handler=_handle_format_encode)

    format_decode = format_subparsers.add_parser("decode", help="Decode .sfw to control-character text.")
    format_decode.add_argument("input")
    format_decode.add_argument("-o", "--output")
    format_decode.set_defaults(handler=_handle_format_decode)

    format_strip = format_subparsers.add_parser("strip", help="Strip inline formatting control codes.")
    format_strip.add_argument("input")
    format_strip.add_argument("-o", "--output")
    format_strip.set_defaults(handler=_handle_format_strip)

    mail_merge_parser = subparsers.add_parser("mail-merge", help="Run headless mail-merge commands.")
    mail_merge_subparsers = mail_merge_parser.add_subparsers(dest="mail_merge_command", required=True)

    mail_merge_inspect = mail_merge_subparsers.add_parser("inspect", help="Inspect a mail-merge database.")
    mail_merge_inspect.add_argument("database")
    mail_merge_inspect.add_argument("--json", action="store_true", dest="as_json")
    mail_merge_inspect.set_defaults(handler=_handle_mail_merge_inspect)

    mail_merge_subset = mail_merge_subparsers.add_parser("subset", help="Apply a subset filter to a database.")
    mail_merge_subset.add_argument("database")
    mail_merge_subset.add_argument("--field", type=int, required=True)
    mail_merge_subset.add_argument("--low", required=True)
    mail_merge_subset.add_argument("--high", required=True)
    mail_merge_subset.add_argument("--json", action="store_true", dest="as_json")
    mail_merge_subset.set_defaults(handler=_handle_mail_merge_subset)

    mail_merge_append = mail_merge_subparsers.add_parser("append", help="Append one database to another.")
    mail_merge_append.add_argument("base_db")
    mail_merge_append.add_argument("other_db")
    mail_merge_append.add_argument("-o", "--output")
    mail_merge_append.set_defaults(handler=_handle_mail_merge_append)

    mail_merge_validate = mail_merge_subparsers.add_parser("validate", help="Validate mail-merge JSON.")
    mail_merge_validate.add_argument("database")
    mail_merge_validate.set_defaults(handler=_handle_mail_merge_validate)

    return parser


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments after applying shorthand normalization."""

    parser = build_parser()
    return parser.parse_args(_normalize_argv(argv))


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return an exit code."""

    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        args = parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return code if isinstance(code, int) else 0

    original_cwd = Path.cwd()
    try:
        _apply_cwd(args)
        handler = getattr(args, "handler", None)
        if handler is None:
            return _run_default_tui(args)
        return int(handler(args))
    except FileNotFoundError as exc:
        _emit_error(str(exc))
        return 2
    except NotADirectoryError as exc:
        _emit_error(str(exc))
        return 2
    except ValueError as exc:
        _emit_error(str(exc))
        return 2
    except OSError as exc:
        _emit_error(str(exc))
        return 2
    finally:
        os.chdir(original_cwd)


def _add_tui_file_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--file", help="Load a document before entering the TUI destination.")


def _add_tui_read_only_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--read-only", action="store_true", help="Open in read-only mode when supported.")


def _add_export_input(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("input", help="Source document.")


def _add_output_flags(parser: argparse.ArgumentParser, label: str) -> None:
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("-o", "--output", help=f"Destination {label} file.")
    output_group.add_argument("--stdout", action="store_true", help=f"Write {label} to stdout.")


def _normalize_argv(argv: list[str]) -> list[str]:
    normalized: list[str] = []
    index = 0
    while index < len(argv):
        token = argv[index]
        normalized.append(token)
        if token in {"--cwd", "--encoding"}:
            index += 1
            if index < len(argv):
                normalized.append(argv[index])
        elif not token.startswith("-"):
            break
        index += 1

    if not argv:
        return []
    first_non_option_index = len(normalized) - 1 if normalized else 0
    if first_non_option_index >= len(argv):
        return argv
    first_non_option = argv[first_non_option_index]
    remaining = argv[first_non_option_index:]
    if first_non_option in TOP_LEVEL_COMMANDS:
        return argv
    if first_non_option.startswith("-"):
        return argv
    if len(remaining) == 1:
        return argv[:first_non_option_index] + ["tui", "edit", "--file", first_non_option]
    return argv


def _apply_cwd(args: argparse.Namespace) -> None:
    if not getattr(args, "cwd", None):
        return
    target = Path(args.cwd)
    if not target.exists():
        raise FileNotFoundError(f"Working directory not found: {target}")
    if not target.is_dir():
        raise NotADirectoryError(f"Working directory is not a directory: {target}")
    os.chdir(target)


def _run_default_tui(args: argparse.Namespace) -> int:
    state = AppState()
    request = StartupRequest(destination="menu")
    _show_tui_splash(args)
    return _launch_tui(state, request, args)


def build_startup_request(args: argparse.Namespace) -> StartupRequest:
    """Build a StartupRequest from parsed TUI args."""

    command = args.tui_command
    if command == "menu":
        return StartupRequest(
            destination="menu",
            document_path=Path(args.file).resolve() if args.file else None,
            read_only=getattr(args, "read_only", False),
        )
    if command == "edit":
        document_path = Path(args.file).resolve() if getattr(args, "file", None) else None
        return StartupRequest(
            destination="edit",
            document_path=document_path,
            cursor_line=args.cursor_line,
            cursor_column=args.cursor_column,
            read_only=args.read_only,
        )
    if command == "proofreader":
        return StartupRequest(
            destination="proofreader",
            document_path=Path(args.file).resolve() if args.file else None,
            proofreader_mode=args.mode,
            read_only=args.read_only,
            personal_dict_paths=tuple(Path(path).resolve() for path in args.personal_dict),
        )
    if command == "global-format":
        return StartupRequest(
            destination="global_format",
            document_path=Path(args.file).resolve() if args.file else None,
            read_only=args.read_only,
        )
    if command == "mail-merge":
        return StartupRequest(
            destination="mail_merge",
            mail_merge_database_path=Path(args.database).resolve() if args.database else None,
            mail_merge_mode=args.mode,
            read_only=args.read_only,
        )
    if command == "print":
        return StartupRequest(
            destination="print",
            document_path=Path(args.file).resolve() if args.file else None,
            print_target=args.target,
            read_only=args.read_only,
        )
    if command == "index-current":
        return StartupRequest(
            destination="index_current",
            index_path=Path(args.path).resolve() if args.path else Path.cwd(),
        )
    if command == "index-external":
        return StartupRequest(destination="index_external")
    if command == "safari-dos":
        return StartupRequest(
            destination="safari_dos",
            safari_dos_path=Path(args.path).resolve() if args.path else Path.cwd(),
        )
    raise ValueError(f"Unsupported TUI destination: {command}")


def _handle_tui_command(args: argparse.Namespace) -> int:
    state = AppState()
    request = build_startup_request(args)

    if request.document_path:
        state = load_document_state(request.document_path, encoding=args.encoding)
    if request.mail_merge_database_path:
        state.mail_merge_db = load_mail_merge_db(
            request.mail_merge_database_path,
            encoding=args.encoding,
        )
    if request.destination == "index_current" and request.index_path and not request.index_path.is_dir():
        raise NotADirectoryError(f"Index path is not a directory: {request.index_path}")
    if request.destination == "safari_dos" and request.safari_dos_path and not request.safari_dos_path.is_dir():
        raise NotADirectoryError(f"Safari DOS path is not a directory: {request.safari_dos_path}")
    for path in request.personal_dict_paths:
        if not path.exists():
            raise FileNotFoundError(f"Personal dictionary not found: {path}")

    _show_tui_splash(args)
    return _launch_tui(state, request, args)


def _show_tui_splash(args: argparse.Namespace) -> None:
    maybe_show_splash(no_splash=getattr(args, "no_splash", False))


def _launch_tui(state: AppState, request: StartupRequest, args: argparse.Namespace) -> int:
    from safari_writer.app import SafariWriterApp

    if request.destination == "edit" and not request.document_path and not getattr(args, "new", False):
        request = StartupRequest(
            destination="edit",
            cursor_line=request.cursor_line,
            cursor_column=request.cursor_column,
            read_only=request.read_only,
        )
    app = SafariWriterApp(state=state, startup_request=request)
    app.run()
    return 0


def _handle_export_markdown(args: argparse.Namespace) -> int:
    from safari_writer.export_md import export_markdown

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve() if args.output else input_path.with_suffix(".md")
    buffer = load_document_buffer(input_path, encoding=args.encoding)
    buffer = _load_merge_applied_buffer(buffer, args.merge_db, args.encoding)
    rendered = export_markdown(buffer, GlobalFormat())
    if args.stdout:
        _emit(rendered.rstrip("\n"))
    else:
        output_path.write_text(rendered, encoding="utf-8")
        _emit_status(args, f"Exported Markdown to {output_path}")
    return 0


def _handle_export_postscript(args: argparse.Namespace) -> int:
    from safari_writer.export_ps import export_postscript

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve() if args.output else input_path.with_suffix(".ps")
    buffer = load_document_buffer(input_path, encoding=args.encoding)
    buffer = _load_merge_applied_buffer(buffer, args.merge_db, args.encoding)
    rendered = export_postscript(buffer, GlobalFormat())
    output_path.write_text(rendered, encoding="utf-8")
    _emit_status(args, f"Exported PostScript to {output_path}")
    return 0


def _handle_export_ansi(args: argparse.Namespace) -> int:
    input_path = Path(args.input).resolve()
    buffer = load_document_buffer(input_path, encoding=args.encoding)
    rendered = render_ansi_preview(buffer, GlobalFormat())
    if args.page is not None:
        rendered = extract_ansi_page(rendered, args.page)
    _emit("\n".join(rendered).rstrip())
    return 0


def _handle_proof_check(args: argparse.Namespace) -> int:
    errors = _collect_spelling_errors(
        Path(args.input).resolve(),
        args.encoding,
        args.personal_dict,
    )
    if not args.quiet:
        if errors:
            _emit(f"{len(errors)} spelling error(s) found in {args.input}")
        else:
            _emit(f"No spelling errors found in {args.input}")
    return 1 if errors else 0


def _handle_proof_list(args: argparse.Namespace) -> int:
    errors = _collect_spelling_errors(
        Path(args.input).resolve(),
        args.encoding,
        args.personal_dict,
    )
    payload = [
        {"line": row + 1, "column": column + 1, "token": token}
        for row, column, token in errors
    ]
    if args.as_json:
        _emit(json.dumps(payload, indent=2))
    else:
        for issue in payload:
            _emit(f"Line {issue['line']}, column {issue['column']}: {issue['token']}")
    return 0


def _handle_proof_suggest(args: argparse.Namespace) -> int:
    checker = make_checker()
    for word in suggest_words(args.word, checker):
        _emit(word)
    return 0


def _handle_format_encode(args: argparse.Namespace) -> int:
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve() if args.output else input_path.with_suffix(".sfw")
    text = input_path.read_text(encoding=args.encoding, errors="replace")
    buffer = text.split("\n") if text else [""]
    output_path.write_text(encode_sfw(buffer), encoding="utf-8")
    _emit_status(args, f"Encoded {input_path} to {output_path}")
    return 0


def _handle_format_decode(args: argparse.Namespace) -> int:
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve() if args.output else input_path.with_suffix(".decoded.txt")
    text = input_path.read_text(encoding=args.encoding, errors="replace")
    output_path.write_text("\n".join(decode_sfw(text)), encoding="utf-8")
    _emit_status(args, f"Decoded {input_path} to {output_path}")
    return 0


def _handle_format_strip(args: argparse.Namespace) -> int:
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve() if args.output else input_path.with_suffix(".txt")
    buffer = load_document_buffer(input_path, encoding=args.encoding)
    output_path.write_text("\n".join(strip_controls(buffer)), encoding="utf-8")
    _emit_status(args, f"Stripped formatting from {input_path} to {output_path}")
    return 0


def _handle_mail_merge_inspect(args: argparse.Namespace) -> int:
    db = load_mail_merge_db(Path(args.database).resolve(), encoding=args.encoding)
    payload = inspect_mail_merge_db(db)
    if args.as_json:
        _emit(json.dumps(payload, indent=2))
    else:
        _emit(f"Filename: {payload['filename']}")
        _emit(f"Fields: {payload['field_count']}")
        _emit(f"Records: {payload['record_count']}")
        _emit(f"Records free: {payload['records_free']}")
        for field in payload["fields"]:
            _emit(f"  {field['index']:>2}. {field['name']} ({field['max_len']})")
    return 0


def _handle_mail_merge_subset(args: argparse.Namespace) -> int:
    db = load_mail_merge_db(Path(args.database).resolve(), encoding=args.encoding)
    if args.field < 1 or args.field > len(db.fields):
        raise ValueError(f"Field must be between 1 and {len(db.fields)}")
    indexes = db.apply_subset(args.field - 1, args.low, args.high)
    payload = {
        "field": args.field,
        "low": args.low,
        "high": args.high,
        "matching_indexes": [index + 1 for index in indexes],
        "records": [db.records[index] for index in indexes],
    }
    if args.as_json:
        _emit(json.dumps(payload, indent=2))
    else:
        _emit(f"{len(indexes)} record(s) matched")
        for index in indexes:
            preview = " | ".join(value for value in db.records[index][:3] if value)
            _emit(f"  Record {index + 1}: {preview}")
    return 0


def _handle_mail_merge_append(args: argparse.Namespace) -> int:
    base_path = Path(args.base_db).resolve()
    other_path = Path(args.other_db).resolve()
    output_path = Path(args.output).resolve() if args.output else base_path.with_name(f"{base_path.stem}.merged.json")
    base_db = load_mail_merge_db(base_path, encoding=args.encoding)
    other_db = load_mail_merge_db(other_path, encoding=args.encoding)
    if not base_db.schema_matches(other_db):
        raise ValueError("Cannot append databases with different schemas")
    merged = MailMergeDB(
        fields=[field for field in base_db.fields],
        records=[list(record) for record in base_db.records],
        filename=str(output_path),
    )
    available = max(0, merged.records_free)
    merged.records.extend([list(record) for record in other_db.records[:available]])
    save_mail_merge_db(merged, output_path, encoding=args.encoding)
    _emit_status(args, f"Wrote merged database to {output_path}")
    return 0


def _handle_mail_merge_validate(args: argparse.Namespace) -> int:
    database_path = Path(args.database).resolve()
    try:
        data = json.loads(database_path.read_text(encoding=args.encoding))
    except json.JSONDecodeError as exc:
        _emit_error(f"{database_path}: {exc}")
        return 2
    errors = validate_mail_merge_data(data)
    if errors:
        for error in errors:
            _emit(error)
        return 1
    _emit_status(args, f"{database_path} is valid")
    return 0


def _collect_spelling_errors(
    input_path: Path,
    encoding: str,
    personal_dict_paths: list[str],
) -> list[tuple[int, int, str]]:
    buffer = load_document_buffer(input_path, encoding=encoding)
    checker = make_checker()
    personal_words: set[str] = set()
    for dictionary_path in personal_dict_paths:
        personal_words.update(load_personal_dictionary(Path(dictionary_path).resolve(), encoding=encoding))
    return [
        (row, column, token)
        for row, column, token in extract_words(buffer)
        if not check_word(token, checker, set(), personal_words)
    ]


def _load_merge_applied_buffer(buffer: list[str], merge_db_path: str | None, encoding: str) -> list[str]:
    if not merge_db_path:
        return buffer
    db = load_mail_merge_db(Path(merge_db_path).resolve(), encoding=encoding)
    return apply_mail_merge_to_buffer(buffer, db)


def _emit_status(args: argparse.Namespace, message: str) -> None:
    if not args.quiet:
        _emit(message)


def _emit(message: str) -> None:
    print(message)


def _emit_error(message: str) -> None:
    print(message, file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
