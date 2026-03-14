"""Splash-screen behavior tests."""

from __future__ import annotations

from importlib import resources

from safari_writer.splash import (DEFAULT_SPLASH_STYLE,
                                  SPLASH_DURATION_SECONDS, maybe_show_splash,
                                  resolve_splash_style, should_show_splash)


class FakeStream:
    def __init__(self, is_tty: bool) -> None:
        self._is_tty = is_tty

    def isatty(self) -> bool:
        return self._is_tty


def test_should_show_splash_skips_when_no_color_is_set():
    assert not should_show_splash(
        stdin=FakeStream(True),
        stdout=FakeStream(True),
        environ={"NO_COLOR": "1"},
    )


def test_should_show_splash_skips_when_style_is_off():
    assert not should_show_splash(
        style="off",
        stdin=FakeStream(True),
        stdout=FakeStream(True),
        environ={},
    )


def test_resolve_splash_style_defaults_to_logo():
    assert resolve_splash_style(None) == DEFAULT_SPLASH_STYLE
    assert resolve_splash_style("logo") == "logo"
    assert resolve_splash_style("fancy") == "fancy"
    assert resolve_splash_style("disabled") == "off"
    assert resolve_splash_style("bogus") == DEFAULT_SPLASH_STYLE


def test_maybe_show_splash_runs_when_terminal_supports_it(monkeypatch):
    called: list[tuple[float, object | None]] = []

    monkeypatch.setattr(
        "safari_writer.splash.run_splash",
        lambda duration=SPLASH_DURATION_SECONDS, style=None: called.append(
            (duration, style)
        ),
    )

    shown = maybe_show_splash(
        duration=1.5,
        style="fancy",
        stdin=FakeStream(True),
        stdout=FakeStream(True),
        environ={},
    )

    assert shown is True
    assert called == [(1.5, "fancy")]


def test_logo_resource_is_available():
    assert resources.files("safari_writer").joinpath("safari_logo.png").is_file()
