"""
Terminal splash screen with a safari-writer / 1980s home-computing vibe.
No external dependencies required.

Features:
- Centered retro title art
- Animated scanlines / shimmer
- Warm sunset + jungle palette
- Animated status lines and prompt
- Works best in a truecolor terminal, but has ANSI fallbacks

Run:
    uv run python -m safari_writer.splash
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
import math
import os
import random
import shutil
import sys
import time
from typing import Any

if os.name == "nt":
    import msvcrt

__all__ = [
    "SPLASH_DURATION_SECONDS",
    "main",
    "maybe_show_splash",
    "run_splash",
    "should_show_splash",
]

# -----------------------------
# ANSI helpers
# -----------------------------

RESET = "\033[0m"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
CLEAR = "\033[2J"
HOME = "\033[H"


def rgb(r: int, g: int, b: int) -> str:
    return f"\033[38;2;{r};{g};{b}m"


def bg_rgb(r: int, g: int, b: int) -> str:
    return f"\033[48;2;{r};{g};{b}m"


def bold(text: str) -> str:
    return f"\033[1m{text}{RESET}"


def dim(text: str) -> str:
    return f"\033[2m{text}{RESET}"


# -----------------------------
# Theme
# -----------------------------

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
    "deep_leaf": (20, 100, 45),
    "sand": (245, 225, 170),
    "white": (245, 245, 245),
    "shadow": (20, 12, 18),
}

TITLE = "SAFARI WRITER"
SUBTITLE = "FIELD NOTES • STORY ENGINE • VINTAGE EDITION"
SPLASH_DURATION_SECONDS = 3.0


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


# -----------------------------
# Drawing
# -----------------------------

def terminal_size() -> tuple[int, int]:
    size = shutil.get_terminal_size(fallback=(100, 32))
    return size.columns, size.lines


def move(x: int, y: int) -> str:
    return f"\033[{y};{x}H"


def center_x(text: str, width: int) -> int:
    return max(1, (width - visual_len(text)) // 2 + 1)


def visual_len(text: str) -> int:
    # Rough length for ANSI-free strings.
    return len(text)


def gradient_color(t: float) -> tuple[int, int, int]:
    """
    Sunset gradient:
    gold -> orange -> crimson -> violet
    """
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

        if shimmer and ch not in (" ",):
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

        # Sky/jungle glow
        horizon = height * 0.42
        dist = abs(y - horizon) / max(1, height)

        base_r = int(20 + 120 * max(0, 1 - dist * 2.1))
        base_g = int(12 + 60 * max(0, 1 - dist * 2.0))
        base_b = int(26 + 150 * max(0, 1 - dist * 1.8))

        # Subtle scanlines
        if y % 2 == 0:
            base_r = max(0, base_r - 6)
            base_g = max(0, base_g - 6)
            base_b = max(0, base_b - 6)

        for x in range(1, width + 1):
            glow = math.sin((x * 0.09) + frame * 0.13) * 10
            r = min(255, max(0, int(base_r + glow)))
            g = min(255, max(0, int(base_g + glow * 0.6)))
            b = min(255, max(0, int(base_b + glow * 1.2)))

            # Sparse stars / sparkle near top
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
    return left + (fill * (interior // 2)) + center + (fill * (interior - interior // 2)) + right


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


def type_line(x: int, y: int, text: str, color: tuple[int, int, int], delay: float = 0.015) -> None:
    sys.stdout.write(move(x, y))
    sys.stdout.flush()
    for ch in text:
        sys.stdout.write(rgb(*color) + ch + RESET)
        sys.stdout.flush()
        time.sleep(delay)


def draw_frame(frame: int) -> None:
    width, height = terminal_size()
    min_w, min_h = 84, 28

    sys.stdout.write(HOME)
    sys.stdout.write(draw_background(width, height, frame))

    if width < min_w or height < min_h:
        msg = "Please enlarge the terminal for the full splash screen."
        x = center_x(msg, width)
        y = max(2, height // 2)
        sys.stdout.write(move(x, y) + rgb(*PALETTE["sand"]) + msg + RESET)
        sys.stdout.flush()
        return

    title_y = max(3, height // 2 - 9)
    shadow_offset = 2

    # Shadow
    for i, line in enumerate(ASCII_TITLE):
        shadow_x = center_x(line, width) + shadow_offset
        shadow_y = title_y + i + 1
        sys.stdout.write(move(shadow_x, shadow_y) + rgb(*PALETTE["shadow"]) + line + RESET)

    # Main title
    for i, line in enumerate(ASCII_TITLE):
        x = center_x(line, width)
        y = title_y + i
        sys.stdout.write(move(x, y) + colorize_line(line, frame))

    # Decorative animal banner
    animal = random.choice(ANIMALS) if USE_EMOJI else "◆"
    banner = f"{animal}  {SUBTITLE}  {animal}"
    banner_x = center_x(banner, width)
    banner_y = title_y + len(ASCII_TITLE) + 2
    sys.stdout.write(move(banner_x, banner_y) + zebra_stripes(banner, frame) + RESET)

    # Tagline
    tagline = "An expedition-ready writing environment for the command line"
    tag_x = center_x(tagline, width)
    tag_y = banner_y + 2
    sys.stdout.write(move(tag_x, tag_y) + rgb(*PALETTE["mint"]) + tagline + RESET)

    # Palm / horizon separator
    horizon = palm_line(min(width - 4, 120))
    horizon_x = center_x(horizon, width)
    horizon_y = tag_y + 3
    sys.stdout.write(move(horizon_x, horizon_y) + rgb(*PALETTE["leaf"]) + horizon + RESET)

    # Small retro badge
    badge = " [ BOOT SEQUENCE: READY ] "
    badge_x = center_x(badge, width)
    badge_y = horizon_y + 2
    sys.stdout.write(
        move(badge_x, badge_y)
        + bg_rgb(*PALETTE["crimson"])
        + rgb(*PALETTE["sand"])
        + badge
        + RESET
    )

    # Animated status dots
    dots = "." * ((frame % 4) + 1)
    status = f"Loading creative tools{dots:<4}"
    status_x = center_x(status, width)
    status_y = badge_y + 2
    sys.stdout.write(move(status_x, status_y) + rgb(*PALETTE["gold"]) + status + RESET)

    # Footer
    footer = "Press any key to continue"
    footer_x = center_x(footer, width)
    footer_y = height - 2
    pulse = 0.65 + 0.35 * (math.sin(frame * 0.25) + 1) / 2
    c = tuple(int(v * pulse) for v in PALETTE["sky"])
    sys.stdout.write(move(footer_x, footer_y) + rgb(*c) + footer + RESET)

    sys.stdout.flush()


# -----------------------------
# Main
# -----------------------------

def _is_tty(stream: object) -> bool:
    isatty = getattr(stream, "isatty", None)
    return bool(callable(isatty) and isatty())


def should_show_splash(
    *,
    no_splash: bool = False,
    environ: Mapping[str, str] | None = None,
    stdin: object | None = None,
    stdout: object | None = None,
) -> bool:
    """Return whether the splash should be shown in the current terminal."""

    if no_splash:
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
        def key_pressed() -> bool:
            if not msvcrt.kbhit():
                return False
            msvcrt.getwch()
            return True

        yield key_pressed
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

        def key_pressed() -> bool:
            ready, _, _ = select_module.select([sys.stdin], [], [], 0)
            if not ready:
                return False
            sys.stdin.read(1)
            return True

        yield key_pressed
    finally:
        posix_termios.tcsetattr(fd, posix_termios.TCSADRAIN, original_mode)


def _draw_status_lines(frame: int) -> None:
    width, height = terminal_size()
    line1 = "Initializing field journal..."
    line2 = "Ink ribbon aligned. Lantern glow set. Ready to write."
    x1 = center_x(line1, width)
    y1 = max(2, height - 6)
    x2 = center_x(line2, width)
    y2 = y1 + 1
    sys.stdout.write(move(x1, y1) + rgb(*PALETTE["amber"]) + line1 + RESET)
    sys.stdout.write(move(x2, y2) + rgb(*PALETTE["sand"]) + line2 + RESET)

    footer = "Press any key to continue"
    footer_x = center_x(footer, width)
    footer_y = height - 2
    pulse = 0.65 + 0.35 * (math.sin(frame * 0.25) + 1) / 2
    c = tuple(int(v * pulse) for v in PALETTE["sky"])
    sys.stdout.write(move(footer_x, footer_y) + rgb(*c) + footer + RESET)
    sys.stdout.flush()


def run_splash(duration: float = SPLASH_DURATION_SECONDS) -> None:
    """Render the splash screen until timeout or the first key press."""

    deadline = time.monotonic() + max(0.0, duration)

    try:
        sys.stdout.write(HIDE_CURSOR + CLEAR + HOME)
        sys.stdout.flush()

        frame = 0
        with _keypress_listener() as key_pressed:
            while True:
                draw_frame(frame)
                _draw_status_lines(frame)
                if key_pressed() or time.monotonic() >= deadline:
                    break
                time.sleep(0.08)
                frame += 1
    finally:
        sys.stdout.write(CLEAR + HOME + SHOW_CURSOR + RESET)
        sys.stdout.flush()


def maybe_show_splash(
    *,
    no_splash: bool = False,
    duration: float = SPLASH_DURATION_SECONDS,
    environ: Mapping[str, str] | None = None,
    stdin: object | None = None,
    stdout: object | None = None,
) -> bool:
    """Show the splash when the terminal can support it."""

    if not should_show_splash(
        no_splash=no_splash,
        environ=environ,
        stdin=stdin,
        stdout=stdout,
    ):
        return False
    run_splash(duration=duration)
    return True


def main() -> int:
    maybe_show_splash()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
