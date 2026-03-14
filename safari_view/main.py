"""Argparse CLI for SafariView."""

from __future__ import annotations

import argparse
import logging
import sys
from importlib import metadata
from pathlib import Path

from safari_view.render import RenderContext, RenderMode, create_pipeline
from safari_view.state import SafariViewLaunchConfig, SafariViewState
from safari_view.ui_terminal.textual_app import SafariViewApp
from safari_view.ui_tk.tk_app import SafariViewTkApp

__all__ = ["build_parser", "main", "parse_args"]

TOP_LEVEL_COMMANDS = {"tui", "tk", "open", "browse", "render", "modes"}
MODE_CHOICES = ("2600", "800", "st", "native")
DEFAULT_RENDER_WIDTH = 800
DEFAULT_RENDER_HEIGHT = 600


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


def _parse_render_mode(value: str) -> RenderMode:
    mapping = {
        "2600": RenderMode.MODE_2600,
        "800": RenderMode.MODE_800,
        "st": RenderMode.MODE_ST,
        "native": RenderMode.NATIVE,
    }
    return mapping[value]


def _add_bool_toggle(
    parser: argparse.ArgumentParser,
    name: str,
    *,
    default: bool,
    help_text: str,
) -> None:
    dest = name.replace("-", "_")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        f"--{name}",
        dest=dest,
        action="store_true",
        default=default,
        help=help_text,
    )
    group.add_argument(f"--no-{name}", dest=dest, action="store_false")


def _add_view_startup_flags(
    parser: argparse.ArgumentParser,
    *,
    default_browser: str,
    default_focus: str,
) -> None:
    parser.add_argument("path", nargs="?", help="Initial path or image to open.")
    parser.add_argument("--image", help="Open an image immediately on startup.")
    parser.add_argument("--mode", choices=MODE_CHOICES, default="800")
    _add_bool_toggle(
        parser,
        "dithering",
        default=True,
        help_text="Enable dithering during rendering.",
    )
    _add_bool_toggle(
        parser,
        "pixel-grid",
        default=False,
        help_text="Overlay a retro pixel grid when supported.",
    )
    parser.add_argument(
        "--browser",
        choices=("show", "hide"),
        default=default_browser,
        help="Whether the file browser pane starts visible.",
    )
    parser.add_argument(
        "--focus",
        choices=("browser", "viewer"),
        default=default_focus,
        help="Which pane should receive initial focus.",
    )
    parser.add_argument(
        "--select",
        help=(
            "Best-effort startup selection path. Files set the startup folder to "
            "their parent."
        ),
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the explicit SafariView parser."""
    parser = argparse.ArgumentParser(
        prog="safari-view",
        description="SafariView retro image viewer.",
        allow_abbrev=False,
        epilog=(
            "Examples:\n"
            "  safari-view tui .\n"
            "  safari-view open images\\frog.png --mode st --no-dithering\n"
            "  safari-view browse images --select images\\frog.png\n"
            "  safari-view tk --image images\\frog.png --mode native\n"
            "  safari-view render images\\frog.png --mode 2600 --width 160 "
            "--height 192 -o out\\frog-2600.png"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {_version_string()}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    tui_parser = subparsers.add_parser("tui", help="Launch the Textual frontend.")
    _add_view_startup_flags(tui_parser, default_browser="show", default_focus="browser")

    tk_parser = subparsers.add_parser("tk", help="Launch the Tk frontend.")
    tk_parser.add_argument("path", nargs="?", help="Initial path or image to open.")
    tk_parser.add_argument("--image", help="Open an image immediately on startup.")
    tk_parser.add_argument("--mode", choices=MODE_CHOICES, default="800")
    _add_bool_toggle(
        tk_parser,
        "dithering",
        default=True,
        help_text="Enable dithering during rendering.",
    )
    _add_bool_toggle(
        tk_parser,
        "pixel-grid",
        default=False,
        help_text="Overlay a retro pixel grid when supported.",
    )

    open_parser = subparsers.add_parser(
        "open",
        help="Open an image directly in the Textual frontend.",
    )
    open_parser.add_argument("image", help="Image file to open.")
    open_parser.add_argument("--mode", choices=MODE_CHOICES, default="800")
    _add_bool_toggle(
        open_parser,
        "dithering",
        default=True,
        help_text="Enable dithering during rendering.",
    )
    _add_bool_toggle(
        open_parser,
        "pixel-grid",
        default=False,
        help_text="Overlay a retro pixel grid when supported.",
    )
    open_parser.add_argument("--browser", choices=("show", "hide"), default="hide")
    open_parser.add_argument("--focus", choices=("browser", "viewer"), default="viewer")

    browse_parser = subparsers.add_parser(
        "browse",
        help="Start the Textual frontend focused on a directory.",
    )
    _add_view_startup_flags(
        browse_parser,
        default_browser="show",
        default_focus="browser",
    )

    render_parser = subparsers.add_parser(
        "render",
        help="Render an image through the retro pipeline and save it.",
    )
    render_parser.add_argument("image", help="Input image file.")
    render_parser.add_argument("--mode", choices=MODE_CHOICES, default="800")
    render_parser.add_argument("--width", type=int, default=DEFAULT_RENDER_WIDTH)
    render_parser.add_argument("--height", type=int, default=DEFAULT_RENDER_HEIGHT)
    _add_bool_toggle(
        render_parser,
        "dithering",
        default=True,
        help_text="Enable dithering during rendering.",
    )
    _add_bool_toggle(
        render_parser,
        "pixel-grid",
        default=False,
        help_text="Overlay a retro pixel grid when supported.",
    )
    render_parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Destination image path.",
    )

    subparsers.add_parser("modes", help="List supported render modes.")
    return parser


def _build_legacy_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="safari-view",
        description="SafariView retro image viewer.",
        allow_abbrev=False,
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {_version_string()}",
    )
    parser.add_argument("path", nargs="?", default=".", help="Initial path to browse.")
    return parser


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse SafariView CLI arguments with legacy shorthand support."""
    args_list = list(argv)
    pre_parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    pre_parser.add_argument("--debug", action="store_true")
    pre_parser.add_argument(
        "--version",
        action="version",
        version=f"safari-view {_version_string()}",
    )
    _, remaining = pre_parser.parse_known_args(args_list)
    if not remaining or (
        remaining[0] not in TOP_LEVEL_COMMANDS and not remaining[0].startswith("-")
    ):
        legacy = _build_legacy_parser().parse_args(args_list)
        return argparse.Namespace(
            debug=legacy.debug,
            command="tui",
            path=legacy.path,
            image=None,
            mode="800",
            dithering=True,
            pixel_grid=False,
            browser="show",
            focus="browser",
            select=None,
        )
    return build_parser().parse_args(args_list)


def _resolve_path(value: str | Path | None) -> Path | None:
    if value is None:
        return None
    return Path(value).resolve()


def _resolve_startup_paths(
    *,
    path_value: str | None,
    image_value: str | None,
    select_value: str | None,
) -> tuple[Path, Path | None, Path | None]:
    current_path = _resolve_path(path_value)
    image_path = _resolve_path(image_value)
    selected_path = _resolve_path(select_value)

    if image_path is None and current_path is not None and current_path.exists():
        if current_path.is_file():
            image_path = current_path
            current_path = current_path.parent

    if image_path is not None:
        if not image_path.exists():
            raise FileNotFoundError(f"Path not found: {image_path}")
        if not image_path.is_file():
            raise FileNotFoundError(f"Image path is not a file: {image_path}")

    if selected_path is not None:
        if not selected_path.exists():
            raise FileNotFoundError(f"Path not found: {selected_path}")
        if current_path is None:
            current_path = (
                selected_path.parent if selected_path.is_file() else selected_path
            )

    if current_path is None:
        current_path = (
            image_path.parent if image_path is not None else Path.cwd().resolve()
        )

    if not current_path.exists():
        raise FileNotFoundError(f"Path not found: {current_path}")
    if current_path.is_file():
        if image_path is None:
            image_path = current_path
        current_path = current_path.parent

    return current_path.resolve(), image_path, selected_path


def _build_view_state(
    *,
    path_value: str | None,
    image_value: str | None,
    mode_value: str,
    dithering: bool,
    pixel_grid: bool,
    browser: str = "show",
    focus: str = "browser",
    select_value: str | None = None,
) -> tuple[SafariViewState, SafariViewLaunchConfig]:
    current_path, image_path, selected_path = _resolve_startup_paths(
        path_value=path_value,
        image_value=image_value,
        select_value=select_value,
    )
    state = SafariViewState(
        current_path=current_path,
        current_image_path=image_path,
        render_mode=_parse_render_mode(mode_value),
        dithering=dithering,
        pixel_grid=pixel_grid,
    )
    launch_config = SafariViewLaunchConfig(
        browser_visible=browser != "hide",
        focus_target=focus,
        selected_path=selected_path,
    )
    return state, launch_config


def _launch_tui(args: argparse.Namespace) -> int:
    state, launch_config = _build_view_state(
        path_value=getattr(args, "path", None),
        image_value=getattr(args, "image", None),
        mode_value=args.mode,
        dithering=args.dithering,
        pixel_grid=args.pixel_grid,
        browser=getattr(args, "browser", "show"),
        focus=getattr(args, "focus", "browser"),
        select_value=getattr(args, "select", None),
    )
    SafariViewApp(state=state, launch_config=launch_config).run()
    return 0


def _launch_tk(args: argparse.Namespace) -> int:
    state, _ = _build_view_state(
        path_value=getattr(args, "path", None),
        image_value=getattr(args, "image", None),
        mode_value=args.mode,
        dithering=args.dithering,
        pixel_grid=args.pixel_grid,
    )
    SafariViewTkApp(state=state).run()
    return 0


def _run_render(args: argparse.Namespace) -> int:
    image_path = _resolve_path(args.image)
    output_path = _resolve_path(args.output)
    assert image_path is not None
    assert output_path is not None

    if not image_path.exists() or not image_path.is_file():
        raise FileNotFoundError(f"Image path not found: {image_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    context = RenderContext(
        target_width=args.width,
        target_height=args.height,
        dithering=args.dithering,
        pixel_grid=args.pixel_grid,
    )
    transformed = create_pipeline().process(
        image_path,
        _parse_render_mode(args.mode),
        context,
    )
    transformed.save(output_path)
    print(output_path)
    return 0


def _run_modes() -> int:
    for mode in MODE_CHOICES:
        print(mode)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the SafariView CLI."""
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    _configure_logging(getattr(args, "debug", False))

    if args.command in {"tui", "browse"}:
        return _launch_tui(args)
    if args.command == "open":
        return _launch_tui(
            argparse.Namespace(
                path=None,
                image=args.image,
                mode=args.mode,
                dithering=args.dithering,
                pixel_grid=args.pixel_grid,
                browser=args.browser,
                focus=args.focus,
                select=None,
            )
        )
    if args.command == "tk":
        return _launch_tk(args)
    if args.command == "render":
        return _run_render(args)
    if args.command == "modes":
        return _run_modes()
    raise ValueError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
