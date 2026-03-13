"""Argparse CLI entrypoint for Safari DOS."""

from __future__ import annotations

import argparse
from importlib import metadata
import logging
from pathlib import Path
import sys

from safari_dos.app import SafariDosApp
from safari_dos.services import (
    copy_paths,
    create_folder,
    discover_locations,
    duplicate_path,
    get_entry_info,
    get_preview_text,
    list_favorites,
    list_directory,
    list_recent_documents,
    list_recent_locations,
    move_paths,
    move_to_garbage,
    record_recent_document,
    rename_path,
    set_protected,
    toggle_favorite,
    unzip_path,
    zip_paths,
)
from safari_dos.state import SafariDosExitRequest, SafariDosLaunchConfig, SafariDosState

__all__ = ["build_parser", "main", "parse_args"]

TOP_LEVEL_COMMANDS = {
    "tui",
    "menu",
    "browse",
    "devices",
    "favorites",
    "garbage",
    "help",
    "pick-file",
    "pick-dir",
    "ls",
    "info",
    "preview",
    "favorite",
    "recent",
    "mkdir",
    "rename",
    "duplicate",
    "copy",
    "move",
    "trash",
    "protect",
    "unprotect",
    "zip",
    "unzip",
    "locations",
    "edit",
}
SORT_CHOICES = ("name", "date", "size", "type")
SCREEN_CHOICES = ("menu", "browser", "devices", "favorites", "garbage", "help")
PICKER_CHOICES = ("file", "directory")
PREVIEW_CHOICES = ("show", "hide", "fullscreen")


def _version_string() -> str:
    try:
        return metadata.version("safari-writer")
    except metadata.PackageNotFoundError:
        return "0.1.0"


def _configure_logging(debug: bool) -> None:
    if not debug:
        return
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def _add_show_hidden_flags(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--show-hidden",
        dest="show_hidden",
        action="store_true",
        default=False,
        help="Include hidden files in directory listings.",
    )
    group.add_argument(
        "--hide-hidden",
        dest="show_hidden",
        action="store_false",
    )


def _add_browser_startup_flags(parser: argparse.ArgumentParser) -> None:
    _add_show_hidden_flags(parser)
    parser.add_argument("--preview", choices=PREVIEW_CHOICES, default="show")
    parser.add_argument("--sort", choices=SORT_CHOICES, default="name")
    parser.add_argument(
        "--descending",
        action="store_true",
        help="Reverse file ordering within directories and files.",
    )
    parser.add_argument("--filter", default="", help="Initial name filter text.")
    parser.add_argument("--select", help="Select an item by name in the current folder.")
    parser.add_argument("--select-path", help="Select an item by path.")


def build_parser() -> argparse.ArgumentParser:
    """Build the explicit Safari DOS parser."""
    parser = argparse.ArgumentParser(
        prog="safari-dos",
        description="Safari DOS file manager.",
        allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  safari-dos\n"
            "  safari-dos browse C:\\work --show-hidden --sort date --descending\n"
            "  safari-dos favorites\n"
            "  safari-dos pick-file C:\\docs --filter report\n"
            "  safari-dos ls C:\\docs --show-hidden --sort type\n"
            "  safari-dos copy C:\\backup C:\\docs\\memo.txt C:\\docs\\todo.txt\n"
            "  safari-dos zip C:\\backup\\docs.zip C:\\docs\\memo.txt C:\\docs\\todo.txt\n"
            "  safari-dos info C:\\docs\\memo.txt"
        ),
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {_version_string()}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    tui_parser = subparsers.add_parser("tui", help="Launch Safari DOS interactively.")
    tui_parser.add_argument("path", nargs="?", help="Optional starting directory.")
    tui_parser.add_argument("--screen", choices=SCREEN_CHOICES, default="menu")
    _add_browser_startup_flags(tui_parser)
    tui_parser.add_argument("--picker", choices=PICKER_CHOICES)
    tui_parser.add_argument(
        "--pending-filename",
        default="",
        help="Initial pending file name for directory picker flows.",
    )

    menu_parser = subparsers.add_parser("menu", help="Jump straight to the main menu.")
    menu_parser.add_argument("path", nargs="?", help="Optional starting directory.")

    browse_parser = subparsers.add_parser(
        "browse",
        help="Jump straight to the file browser.",
    )
    browse_parser.add_argument("path", help="Directory or file to browse.")
    _add_browser_startup_flags(browse_parser)

    devices_parser = subparsers.add_parser(
        "devices",
        help="Jump straight to the devices screen.",
    )
    devices_parser.add_argument("path", nargs="?", help="Optional context directory.")

    favorites_parser = subparsers.add_parser(
        "favorites",
        help="Jump straight to favorites and recent items.",
    )
    favorites_parser.add_argument("path", nargs="?", help="Optional context directory.")

    garbage_parser = subparsers.add_parser(
        "garbage",
        help="Jump straight to the garbage help screen.",
    )
    garbage_parser.add_argument("path", nargs="?", help="Optional context directory.")

    help_parser = subparsers.add_parser("help", help="Open the DOS help screen.")
    help_parser.add_argument("path", nargs="?", help="Optional context directory.")

    pick_file_parser = subparsers.add_parser(
        "pick-file",
        help="Open the file browser in file-picker mode.",
    )
    pick_file_parser.add_argument("path", help="Starting directory.")
    _add_browser_startup_flags(pick_file_parser)

    pick_dir_parser = subparsers.add_parser(
        "pick-dir",
        help="Open the file browser in directory-picker mode.",
    )
    pick_dir_parser.add_argument("path", help="Starting directory.")
    _add_browser_startup_flags(pick_dir_parser)

    ls_parser = subparsers.add_parser("ls", help="List directory contents.")
    ls_parser.add_argument("path", nargs="?", default=".", help="Directory to list.")
    _add_show_hidden_flags(ls_parser)
    ls_parser.add_argument("--sort", choices=SORT_CHOICES, default="name")
    ls_parser.add_argument("--descending", action="store_true")
    ls_parser.add_argument("--filter", default="")

    info_parser = subparsers.add_parser("info", help="Show detailed file information.")
    info_parser.add_argument("path")

    preview_parser = subparsers.add_parser("preview", help="Show a text preview.")
    preview_parser.add_argument("path")
    preview_parser.add_argument("--limit-lines", type=int, default=25)

    favorite_parser = subparsers.add_parser(
        "favorite",
        help="Manage favorite locations.",
    )
    favorite_subparsers = favorite_parser.add_subparsers(
        dest="favorite_command",
        required=True,
    )
    favorite_subparsers.add_parser("list", help="List favorites.")
    favorite_toggle = favorite_subparsers.add_parser(
        "toggle",
        help="Toggle a path in favorites.",
    )
    favorite_toggle.add_argument("path")

    recent_parser = subparsers.add_parser("recent", help="List recent items.")
    recent_subparsers = recent_parser.add_subparsers(dest="recent_command", required=True)
    recent_subparsers.add_parser("locations", help="List recent locations.")
    recent_subparsers.add_parser("documents", help="List recent documents.")

    mkdir_parser = subparsers.add_parser("mkdir", help="Create a directory.")
    mkdir_parser.add_argument("parent")
    mkdir_parser.add_argument("name")

    rename_parser = subparsers.add_parser("rename", help="Rename a path.")
    rename_parser.add_argument("source")
    rename_parser.add_argument("new_name")

    duplicate_parser = subparsers.add_parser(
        "duplicate",
        help="Duplicate a file or directory.",
    )
    duplicate_parser.add_argument("source")

    copy_parser = subparsers.add_parser("copy", help="Copy items into a directory.")
    copy_parser.add_argument("destination")
    copy_parser.add_argument("sources", nargs="+")

    move_parser = subparsers.add_parser("move", help="Move items into a directory.")
    move_parser.add_argument("destination")
    move_parser.add_argument("sources", nargs="+")

    trash_parser = subparsers.add_parser("trash", help="Send items to the OS trash.")
    trash_parser.add_argument("sources", nargs="+")

    protect_parser = subparsers.add_parser("protect", help="Mark a path read-only.")
    protect_parser.add_argument("path")

    unprotect_parser = subparsers.add_parser(
        "unprotect",
        help="Clear read-only protection on a path.",
    )
    unprotect_parser.add_argument("path")

    zip_parser = subparsers.add_parser("zip", help="Create a ZIP archive.")
    zip_parser.add_argument("archive")
    zip_parser.add_argument("sources", nargs="+")

    unzip_parser = subparsers.add_parser("unzip", help="Extract a ZIP archive.")
    unzip_parser.add_argument("archive")
    unzip_parser.add_argument("destination", nargs="?", default=".")

    subparsers.add_parser("locations", help="List discovered DOS device locations.")

    edit_parser = subparsers.add_parser(
        "edit",
        help="Open a file in Safari Writer directly.",
    )
    edit_parser.add_argument("file")
    return parser


def _build_legacy_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="safari-dos",
        description="Safari DOS file manager.",
        allow_abbrev=False,
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {_version_string()}",
    )
    parser.add_argument("path", nargs="?", help="Optional starting directory.")
    return parser


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments with legacy shorthand support."""
    args_list = list(argv)
    pre_parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    pre_parser.add_argument("--debug", action="store_true")
    pre_parser.add_argument(
        "--version",
        action="version",
        version=f"safari-dos {_version_string()}",
    )
    _, remaining = pre_parser.parse_known_args(args_list)
    if not remaining or (
        remaining[0] not in TOP_LEVEL_COMMANDS and not remaining[0].startswith("-")
    ):
        legacy = _build_legacy_parser().parse_args(args_list)
        return argparse.Namespace(debug=legacy.debug, command="menu", path=legacy.path)
    return build_parser().parse_args(args_list)


def _resolve_path(value: str | Path | None) -> Path | None:
    if value is None:
        return None
    return Path(value).resolve()


def _resolve_existing_path(value: str | Path) -> Path:
    path = Path(value).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Path not found: {path}")
    return path


def _resolve_existing_directory(value: str | Path | None) -> Path:
    directory = Path.cwd().resolve() if value is None else Path(value).resolve()
    if directory.is_file():
        raise NotADirectoryError(f"Not a directory: {directory}")
    if not directory.exists():
        raise FileNotFoundError(f"Path not found: {directory}")
    return directory


def _resolve_selection(
    current_path: Path,
    *,
    select_name: str | None,
    select_path: str | None,
) -> Path | None:
    if select_path:
        selection = Path(select_path)
        if not selection.is_absolute():
            selection = current_path / selection
        return _resolve_existing_path(selection)
    if select_name:
        return _resolve_existing_path(current_path / select_name)
    return None


def _build_state_for_interactive(
    args: argparse.Namespace,
    *,
    initial_screen: str,
    picker_mode: str | None = None,
) -> tuple[SafariDosState, SafariDosLaunchConfig]:
    raw_path = _resolve_path(getattr(args, "path", None))
    selected_path: Path | None = None
    if raw_path is not None and raw_path.exists() and raw_path.is_file():
        selected_path = raw_path
        current_path = raw_path.parent
    else:
        current_path = _resolve_existing_directory(raw_path)

    selected_override = _resolve_selection(
        current_path,
        select_name=getattr(args, "select", None),
        select_path=getattr(args, "select_path", None),
    )
    if selected_override is not None:
        selected_path = selected_override

    show_hidden = getattr(args, "show_hidden", False)
    preview = getattr(args, "preview", "show")
    state = SafariDosState(
        current_path=current_path,
        show_hidden=show_hidden,
        show_preview=preview != "hide",
        fullscreen_preview=preview == "fullscreen",
        sort_field=getattr(args, "sort", "name"),
        ascending=not getattr(args, "descending", False),
        filter_text=getattr(args, "filter", ""),
        favorites=list_favorites(),
        recent_locations=list_recent_locations(),
        recent_documents=list_recent_documents(),
        pending_filename=getattr(args, "pending_filename", ""),
    )
    launch_config = SafariDosLaunchConfig(
        initial_screen=initial_screen,
        picker_mode=picker_mode,
        selected_path=selected_path,
    )
    return state, launch_config


def _launch_app(state: SafariDosState, launch_config: SafariDosLaunchConfig) -> int:
    app = SafariDosApp(state=state, launch_config=launch_config)
    result = app.run()
    if isinstance(result, SafariDosExitRequest) and result.action == "open-in-writer":
        from safari_writer.main import main as safari_writer_main

        if result.document_path is None:
            return 0
        return safari_writer_main(["tui", "edit", "--file", str(result.document_path)])
    return 0


def _print_directory_entries(entries: list) -> None:
    for entry in entries:
        size = "---" if entry.size_bytes is None else str(entry.size_bytes)
        flags = "".join(
            [
                "P" if entry.protected else "-",
                "H" if entry.hidden else "-",
                "L" if entry.is_link else "-",
            ]
        )
        print(
            f"{entry.name}\t{entry.kind}\t{size}\t"
            f"{entry.modified_at.isoformat(timespec='seconds')}\t{flags}"
        )


def main(argv: list[str] | None = None) -> int:
    """Launch Safari DOS or run a filesystem command."""
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    _configure_logging(getattr(args, "debug", False))

    if args.command == "menu":
        state, launch = _build_state_for_interactive(args, initial_screen="menu")
        return _launch_app(state, launch)
    if args.command == "tui":
        state, launch = _build_state_for_interactive(
            args,
            initial_screen=args.screen,
            picker_mode=args.picker,
        )
        return _launch_app(state, launch)
    if args.command == "browse":
        state, launch = _build_state_for_interactive(args, initial_screen="browser")
        return _launch_app(state, launch)
    if args.command == "devices":
        state, launch = _build_state_for_interactive(args, initial_screen="devices")
        return _launch_app(state, launch)
    if args.command == "favorites":
        state, launch = _build_state_for_interactive(args, initial_screen="favorites")
        return _launch_app(state, launch)
    if args.command == "garbage":
        state, launch = _build_state_for_interactive(args, initial_screen="garbage")
        return _launch_app(state, launch)
    if args.command == "help":
        state, launch = _build_state_for_interactive(args, initial_screen="help")
        return _launch_app(state, launch)
    if args.command == "pick-file":
        state, launch = _build_state_for_interactive(
            args,
            initial_screen="browser",
            picker_mode="file",
        )
        return _launch_app(state, launch)
    if args.command == "pick-dir":
        state, launch = _build_state_for_interactive(
            args,
            initial_screen="browser",
            picker_mode="directory",
        )
        return _launch_app(state, launch)

    if args.command == "ls":
        entries = list_directory(
            _resolve_existing_directory(args.path),
            show_hidden=args.show_hidden,
            filter_text=args.filter,
            sort_field=args.sort,
            ascending=not args.descending,
        )
        _print_directory_entries(entries)
        return 0
    if args.command == "info":
        print(get_entry_info(_resolve_existing_path(args.path)))
        return 0
    if args.command == "preview":
        print(
            get_preview_text(
                _resolve_existing_path(args.path),
                limit_lines=args.limit_lines,
            )
        )
        return 0
    if args.command == "favorite":
        if args.favorite_command == "list":
            for path in list_favorites():
                print(path)
            return 0
        path = _resolve_existing_path(args.path)
        added = toggle_favorite(path)
        print("added" if added else "removed")
        print(path)
        return 0
    if args.command == "recent":
        items = (
            list_recent_locations()
            if args.recent_command == "locations"
            else list_recent_documents()
        )
        for path in items:
            print(path)
        return 0
    if args.command == "mkdir":
        created = create_folder(_resolve_existing_directory(args.parent), args.name)
        print(created)
        return 0
    if args.command == "rename":
        renamed = rename_path(_resolve_existing_path(args.source), args.new_name)
        print(renamed)
        return 0
    if args.command == "duplicate":
        duplicated = duplicate_path(_resolve_existing_path(args.source))
        print(duplicated)
        return 0
    if args.command == "copy":
        copied = copy_paths(
            [_resolve_existing_path(source) for source in args.sources],
            _resolve_existing_directory(args.destination),
        )
        for path in copied:
            print(path)
        return 0
    if args.command == "move":
        moved = move_paths(
            [_resolve_existing_path(source) for source in args.sources],
            _resolve_existing_directory(args.destination),
        )
        for path in moved:
            print(path)
        return 0
    if args.command == "trash":
        for source in args.sources:
            entry = move_to_garbage(_resolve_existing_path(source))
            print(entry.original_path)
        return 0
    if args.command == "protect":
        path = _resolve_existing_path(args.path)
        set_protected(path, True)
        print(path)
        return 0
    if args.command == "unprotect":
        path = _resolve_existing_path(args.path)
        set_protected(path, False)
        print(path)
        return 0
    if args.command == "zip":
        archive = zip_paths(
            [_resolve_existing_path(source) for source in args.sources],
            Path(args.archive).resolve(),
        )
        print(archive)
        return 0
    if args.command == "unzip":
        unzip_path(
            _resolve_existing_path(args.archive),
            _resolve_existing_directory(args.destination),
        )
        print(_resolve_existing_directory(args.destination))
        return 0
    if args.command == "locations":
        for location in discover_locations(Path.cwd()):
            print(f"{location.token}\t{location.label}\t{location.path}")
        return 0
    if args.command == "edit":
        file_path = _resolve_existing_path(args.file)
        if file_path.is_dir():
            raise IsADirectoryError(f"Not a file: {file_path}")
        record_recent_document(file_path)
        from safari_writer.main import main as safari_writer_main

        return safari_writer_main(["tui", "edit", "--file", str(file_path)])
    raise ValueError(f"Unsupported command: {args.command}")
