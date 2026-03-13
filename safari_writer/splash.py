"""Terminal splash screens for Safari Writer."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from importlib import resources
import math
import os
from pathlib import Path
import shutil
import sys
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from PIL import Image

__all__ = [
    "DEFAULT_SPLASH_STYLE",
    "SPLASH_DURATION_SECONDS",
    "main",
    "maybe_show_splash",
    "resolve_splash_style",
    "run_splash",
    "should_show_splash",
]

RESET = "\033[0m"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
CLEAR = "\033[2J"
HOME = "\033[H"


def rgb(r: int, g: int, b: int) -> str:
    return f"\033[38;2;{r};{g};{b}m"


def bg_rgb(r: int, g: int, b: int) -> str:
    return f"\033[48;2;{r};{g};{b}m"


PALETTE = {
    "gold": (255, 210, 90),
    "amber": (255, 170, 55),
    "orange": (255, 120, 45),
    "crimson": (210, 55, 65),
    "plum": (120, 55, 120),
    "violet": (150, 100, 220),
    "sky": (100, 190, 255),
    "mint": (100, 255, 200),
    "leaf": (60, 190, 90),
    "sand": (245, 225, 170),
    "white": (245, 245, 245),
    "shadow": (20, 12, 18),
}

SUBTITLE = "FIELD NOTES • STORY ENGINE • VINTAGE EDITION"
SPLASH_DURATION_SECONDS = 5.0
DEFAULT_SPLASH_STYLE = "logo"
_VALID_SPLASH_STYLES = frozenset({"logo", "fancy", "off"})

ASCII_TITLE = [
    r"  ███████╗ █████╗ ███████╗ █████╗ ██████╗ ██╗",
    r"  ██╔════╝██╔══██╗██╔════╝██╔══██╗██╔══██╗██║",
    r"  ███████╗███████║█████╗  ███████║██████╔╝██║",
    r"  ╚════██║██╔══██║██╔══╝  ██╔══██║██╔══██╗██║",
    r"  ███████║██║  ██║██║     ██║  ██║██║  ██║██║",
    r"  ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝",
    r" ",
    r"  ██╗    ██╗██████╗ ██╗████████╗███████╗██████╗     ",
    r"  ██║    ██║██╔══██╗██║╚══██╔══╝██╔════╝██╔══██╗    ",
    r"  ██║ █╗ ██║██████╔╝██║   ██║   █████╗  ██████╔╝    ",
    r"  ██║███╗██║██╔══██╗██║   ██║   ██╔══╝  ██╔══██╗    ",
    r"  ╚███╔███╔╝██║  ██║██║   ██║   ███████╗██║  ██║    ",
    r"   ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝    ",
]

ANIMALS = ["🦁", "🦓", "🦒", "🦜"]
USE_EMOJI = sys.stdout.isatty()


def terminal_size() -> tuple[int, int]:
    size = shutil.get_terminal_size(fallback=(100, 32))
    return size.columns, size.lines


def move(x: int, y: int) -> str:
    return f"\033[{y};{x}H"


def center_x(text: str, width: int) -> int:
    return max(1, (width - len(text)) // 2 + 1)


def resolve_splash_style(style: object | None) -> str:
    """Normalize splash style values stored in settings."""

    if style is False:
        return "off"
    if style is True or style is None:
        return DEFAULT_SPLASH_STYLE
    if isinstance(style, str):
        normalized = style.strip().lower()
        aliases = {
            "0": "off",
            "disable": "off",
            "disabled": "off",
            "false": "off",
            "none": "off",
        }
        normalized = aliases.get(normalized, normalized)
        if normalized in _VALID_SPLASH_STYLES:
            return normalized
    return DEFAULT_SPLASH_STYLE


@contextmanager
def _logo_resource_path() -> Iterator[Path]:
    resource = resources.files("safari_writer").joinpath("safari_logo.png")
    with resources.as_file(resource) as logo_path:
        yield logo_path


def _image_to_ansi_lines(image: Image.Image) -> list[str]:
    img = image.convert("RGB")
    lines: list[str] = []
    for y in range(0, img.height, 2):
        parts: list[str] = []
        for x in range(img.width):
            r1, g1, b1 = _rgb_triplet(img, x, y)
            if y + 1 < img.height:
                r2, g2, b2 = _rgb_triplet(img, x, y + 1)
            else:
                r2, g2, b2 = 0, 0, 0
            parts.append(f"{rgb(r1, g1, b1)}{bg_rgb(r2, g2, b2)}▀")
        parts.append(RESET)
        lines.append("".join(parts))
    return lines


def _rgb_triplet(image: Image.Image, x: int, y: int) -> tuple[int, int, int]:
    pixel = image.getpixel((x, y))
    if not (
        isinstance(pixel, tuple)
        and len(pixel) >= 3
        and isinstance(pixel[0], int)
        and isinstance(pixel[1], int)
        and isinstance(pixel[2], int)
    ):
        raise TypeError("Expected RGB pixel data")
    return pixel[0], pixel[1], pixel[2]


def _render_logo() -> tuple[list[str], int]:
    from safari_view.render import RenderContext, RenderMode, create_pipeline

    width, height = terminal_size()
    context = RenderContext(
        target_width=max(16, width - 6),
        target_height=max(8, (height - 7) * 2),
        dithering=True,
    )
    with _logo_resource_path() as logo_path:
        transformed = create_pipeline().process(logo_path, RenderMode.MODE_800, context)
    return _image_to_ansi_lines(transformed), transformed.width


def _draw_logo_frame() -> None:
    width, height = terminal_size()
    logo_lines, logo_width = _render_logo()
    logo_height = len(logo_lines)
    status = "Safari Writer"
    footer = "Press any key to continue"
    start_y = max(2, (height - (logo_height + 2)) // 2)
    start_x = max(1, (width - logo_width) // 2 + 1)

    sys.stdout.write(HOME)
    for offset, line in enumerate(logo_lines):
        sys.stdout.write(move(start_x, start_y + offset) + line)

    status_y = min(height - 3, start_y + logo_height + 1)
    sys.stdout.write(
        move(center_x(status, width), status_y) + rgb(*PALETTE["sand"]) + status + RESET
    )
    sys.stdout.write(
        move(center_x(footer, width), height - 2)
        + rgb(*PALETTE["sky"])
        + footer
        + RESET
    )
    sys.stdout.flush()


def gradient_color(t: float) -> tuple[int, int, int]:
    stops = [
        (0.00, PALETTE["gold"]),
        (0.35, PALETTE["amber"]),
        (0.55, PALETTE["orange"]),
        (0.75, PALETTE["crimson"]),
        (1.00, PALETTE["violet"]),
    ]
    for i in range(len(stops) - 1):
        a_t, a = stops[i]
        b_t, b = stops[i + 1]
        if a_t <= t <= b_t:
            local = (t - a_t) / (b_t - a_t)
            red = int(a[0] + (b[0] - a[0]) * local)
            green = int(a[1] + (b[1] - a[1]) * local)
            blue = int(a[2] + (b[2] - a[2]) * local)
            return red, green, blue
    return stops[-1][1]


def colorize_line(line: str, frame: int, shimmer: bool = True) -> str:
    out = []
    chars = max(1, len(line) - 1)
    for i, ch in enumerate(line):
        t = i / chars
        r, g, b = gradient_color(t)
        if shimmer and ch != " ":
            wave = 0.10 * math.sin((i * 0.7) + frame * 0.22)
            r = min(255, max(0, int(r * (1.0 + wave))))
            g = min(255, max(0, int(g * (1.0 + wave))))
            b = min(255, max(0, int(b * (1.0 + wave))))
        out.append(f"{rgb(r, g, b)}{ch}")
    out.append(RESET)
    return "".join(out)


def draw_background(width: int, height: int, frame: int) -> str:
    lines = []
    for y in range(1, height + 1):
        row = []
        horizon = height * 0.42
        dist = abs(y - horizon) / max(1, height)
        base_r = int(20 + 120 * max(0, 1 - dist * 2.1))
        base_g = int(12 + 60 * max(0, 1 - dist * 2.0))
        base_b = int(26 + 150 * max(0, 1 - dist * 1.8))
        if y % 2 == 0:
            base_r = max(0, base_r - 6)
            base_g = max(0, base_g - 6)
            base_b = max(0, base_b - 6)
        for x in range(1, width + 1):
            glow = math.sin((x * 0.09) + frame * 0.13) * 10
            r = min(255, max(0, int(base_r + glow)))
            g = min(255, max(0, int(base_g + glow * 0.6)))
            b = min(255, max(0, int(base_b + glow * 1.2)))
            if y < height * 0.24 and (x + y * 7 + frame) % 97 == 0:
                row.append(bg_rgb(r, g, b) + rgb(245, 240, 220) + "·")
            else:
                row.append(bg_rgb(r, g, b) + " ")
        row.append(RESET)
        lines.append("".join(row))
    return "".join(move(1, y + 1) + line for y, line in enumerate(lines))


def palm_line(width: int) -> str:
    left = "  _\\/_      "
    center = "  .-^-._.-^-._.-^-._.  "
    right = "      _\\/__ "
    fill = "▁"
    interior = max(0, width - len(left) - len(center) - len(right))
    return (
        left
        + (fill * (interior // 2))
        + center
        + (fill * (interior - interior // 2))
        + right
    )


def zebra_stripes(text: str, frame: int) -> str:
    out = []
    for i, ch in enumerate(text):
        if ch == " ":
            out.append(ch)
            continue
        stripe = ((i + frame) // 2) % 2 == 0
        color = PALETTE["sand"] if stripe else PALETTE["white"]
        out.append(f"{rgb(*color)}{ch}")
    out.append(RESET)
    return "".join(out)


def _draw_fancy_frame(frame: int) -> None:
    width, height = terminal_size()
    min_w, min_h = 84, 28
    sys.stdout.write(HOME)
    sys.stdout.write(draw_background(width, height, frame))
    if width < min_w or height < min_h:
        msg = "Please enlarge the terminal for the full splash screen."
        sys.stdout.write(
            move(center_x(msg, width), max(2, height // 2))
            + rgb(*PALETTE["sand"])
            + msg
            + RESET
        )
        sys.stdout.flush()
        return

    title_y = max(3, height // 2 - 9)
    shadow_offset = 2
    for i, line in enumerate(ASCII_TITLE):
        shadow_x = center_x(line, width) + shadow_offset
        shadow_y = title_y + i + 1
        sys.stdout.write(
            move(shadow_x, shadow_y) + rgb(*PALETTE["shadow"]) + line + RESET
        )
    for i, line in enumerate(ASCII_TITLE):
        sys.stdout.write(
            move(center_x(line, width), title_y + i) + colorize_line(line, frame)
        )

    animal = ANIMALS[(frame // 10) % len(ANIMALS)] if USE_EMOJI else "◆"
    banner = f"{animal}  {SUBTITLE}  {animal}"
    banner_y = title_y + len(ASCII_TITLE) + 2
    sys.stdout.write(
        move(center_x(banner, width), banner_y) + zebra_stripes(banner, frame) + RESET
    )

    tagline = "An expedition-ready writing environment for the command line"
    tag_y = banner_y + 2
    sys.stdout.write(
        move(center_x(tagline, width), tag_y) + rgb(*PALETTE["mint"]) + tagline + RESET
    )

    horizon = palm_line(min(width - 4, 120))
    horizon_y = tag_y + 3
    sys.stdout.write(
        move(center_x(horizon, width), horizon_y)
        + rgb(*PALETTE["leaf"])
        + horizon
        + RESET
    )

    badge = " [ BOOT SEQUENCE: READY ] "
    badge_y = horizon_y + 2
    sys.stdout.write(
        move(center_x(badge, width), badge_y)
        + bg_rgb(*PALETTE["crimson"])
        + rgb(*PALETTE["sand"])
        + badge
        + RESET
    )

    dots = "." * ((frame % 4) + 1)
    status = f"Loading creative tools{dots:<4}"
    status_y = badge_y + 2
    sys.stdout.write(
        move(center_x(status, width), status_y) + rgb(*PALETTE["gold"]) + status + RESET
    )
    sys.stdout.flush()


def _is_tty(stream: object) -> bool:
    isatty = getattr(stream, "isatty", None)
    return bool(callable(isatty) and isatty())


def should_show_splash(
    *,
    no_splash: bool = False,
    style: object | None = None,
    environ: Mapping[str, str] | None = None,
    stdin: object | None = None,
    stdout: object | None = None,
) -> bool:
    """Return whether the splash should be shown in the current terminal."""

    if no_splash or resolve_splash_style(style) == "off":
        return False
    env = os.environ if environ is None else environ
    if "NO_COLOR" in env:
        return False
    input_stream = sys.stdin if stdin is None else stdin
    output_stream = sys.stdout if stdout is None else stdout
    return _is_tty(input_stream) and _is_tty(output_stream)


@contextmanager
def _keypress_listener() -> Iterator[Callable[[], bool]]:
    if os.name == "nt":
        windows_msvcrt: Any = __import__("msvcrt")

        def windows_key_pressed() -> bool:
            if not windows_msvcrt.kbhit():
                return False
            windows_msvcrt.getwch()
            return True

        yield windows_key_pressed
        return

    if not _is_tty(sys.stdin):
        yield lambda: False
        return

    try:
        select_module: Any = __import__("select")
        posix_termios: Any = __import__("termios")
        posix_tty: Any = __import__("tty")
        fd = sys.stdin.fileno()
        original_mode = posix_termios.tcgetattr(fd)
    except (AttributeError, OSError):
        yield lambda: False
        return

    try:
        posix_tty.setcbreak(fd)

        def posix_key_pressed() -> bool:
            ready, _, _ = select_module.select([sys.stdin], [], [], 0)
            if not ready:
                return False
            sys.stdin.read(1)
            return True

        yield posix_key_pressed
    finally:
        posix_termios.tcsetattr(fd, posix_termios.TCSADRAIN, original_mode)


def _draw_status_lines(frame: int) -> None:
    width, height = terminal_size()
    line1 = "Initializing field journal..."
    line2 = "Ink ribbon aligned. Lantern glow set. Ready to write."
    sys.stdout.write(
        move(center_x(line1, width), max(2, height - 6))
        + rgb(*PALETTE["amber"])
        + line1
        + RESET
    )
    sys.stdout.write(
        move(center_x(line2, width), max(3, height - 5))
        + rgb(*PALETTE["sand"])
        + line2
        + RESET
    )

    footer = "Press any key to continue"
    pulse = 0.65 + 0.35 * (math.sin(frame * 0.25) + 1) / 2
    c = tuple(int(v * pulse) for v in PALETTE["sky"])
    sys.stdout.write(
        move(center_x(footer, width), height - 2) + rgb(*c) + footer + RESET
    )
    sys.stdout.flush()


def _run_logo_splash(duration: float) -> None:
    deadline = time.monotonic() + max(0.0, duration)
    try:
        sys.stdout.write(HIDE_CURSOR + CLEAR + HOME)
        sys.stdout.flush()
        _draw_logo_frame()
        with _keypress_listener() as key_pressed:
            while True:
                if key_pressed() or time.monotonic() >= deadline:
                    break
                time.sleep(0.05)
    finally:
        sys.stdout.write(CLEAR + HOME + SHOW_CURSOR + RESET)
        sys.stdout.flush()


def _run_fancy_splash(duration: float) -> None:
    deadline = time.monotonic() + max(0.0, duration)
    try:
        sys.stdout.write(HIDE_CURSOR + CLEAR + HOME)
        sys.stdout.flush()
        frame = 0
        with _keypress_listener() as key_pressed:
            while True:
                _draw_fancy_frame(frame)
                _draw_status_lines(frame)
                if key_pressed() or time.monotonic() >= deadline:
                    break
                time.sleep(0.1)
                frame += 1
    finally:
        sys.stdout.write(CLEAR + HOME + SHOW_CURSOR + RESET)
        sys.stdout.flush()


def run_splash(
    duration: float = SPLASH_DURATION_SECONDS,
    *,
    style: object | None = None,
) -> None:
    """Render the configured splash until timeout or the first key press."""

    resolved_style = resolve_splash_style(style)
    if resolved_style == "off":
        return
    if resolved_style == "logo":
        _run_logo_splash(duration)
        return
    _run_fancy_splash(duration)


def maybe_show_splash(
    *,
    no_splash: bool = False,
    duration: float = SPLASH_DURATION_SECONDS,
    style: object | None = None,
    environ: Mapping[str, str] | None = None,
    stdin: object | None = None,
    stdout: object | None = None,
) -> bool:
    """Show the splash when the terminal can support it."""

    if not should_show_splash(
        no_splash=no_splash,
        style=style,
        environ=environ,
        stdin=stdin,
        stdout=stdout,
    ):
        return False
    run_splash(duration=duration, style=style)
    return True


def main() -> int:
    maybe_show_splash()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
