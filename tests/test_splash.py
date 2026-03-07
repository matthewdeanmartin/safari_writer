"""Splash-screen behavior tests."""

from __future__ import annotations

from safari_writer.splash import SPLASH_DURATION_SECONDS, maybe_show_splash, should_show_splash


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


def test_maybe_show_splash_runs_when_terminal_supports_it(monkeypatch):
    called: list[float] = []

    monkeypatch.setattr(
        "safari_writer.splash.run_splash",
        lambda duration=SPLASH_DURATION_SECONDS: called.append(duration),
    )

    shown = maybe_show_splash(
        duration=1.5,
        stdin=FakeStream(True),
        stdout=FakeStream(True),
        environ={},
    )

    assert shown is True
    assert called == [1.5]
