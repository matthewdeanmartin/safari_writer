"""CLI tests for SafariView."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from safari_view.main import main, parse_args
from safari_view.render import RenderMode


def test_parse_args_supports_legacy_path_shorthand():
    args = parse_args(["gallery"])

    assert args.command == "tui"
    assert args.path == "gallery"
    assert args.mode == "800"
    assert args.browser == "show"


def test_parse_args_supports_open_command():
    args = parse_args(["open", "frog.png", "--mode", "st", "--no-dithering"])

    assert args.command == "open"
    assert args.image == "frog.png"
    assert args.mode == "st"
    assert args.dithering is False
    assert args.focus == "viewer"


def test_main_browse_launches_textual_frontend(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    class FakeApp:
        def __init__(self, state, launch_config) -> None:
            captured["state"] = state
            captured["launch_config"] = launch_config

        def run(self) -> None:
            captured["ran"] = True

    selected = tmp_path / "sample.png"
    selected.write_text("fake", encoding="utf-8")

    monkeypatch.setattr("safari_view.main.SafariViewApp", FakeApp)

    exit_code = main(
        [
            "browse",
            str(tmp_path),
            "--select",
            str(selected),
            "--browser",
            "hide",
            "--focus",
            "viewer",
            "--mode",
            "native",
            "--pixel-grid",
        ]
    )

    assert exit_code == 0
    state = captured["state"]
    launch = captured["launch_config"]
    assert state.current_path == tmp_path.resolve()
    assert state.render_mode is RenderMode.NATIVE
    assert state.pixel_grid is True
    assert launch.browser_visible is False
    assert launch.focus_target == "viewer"
    assert launch.selected_path == selected.resolve()
    assert captured["ran"] is True


def test_main_render_command_writes_output(tmp_path, capsys):
    source = tmp_path / "source.png"
    output = tmp_path / "rendered.png"
    Image.new("RGB", (20, 20), color="red").save(source)

    exit_code = main(
        [
            "render",
            str(source),
            "--mode",
            "2600",
            "--width",
            "64",
            "--height",
            "64",
            "--output",
            str(output),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert output.exists()
    assert str(output.resolve()) in captured.out


def test_main_tk_launches_tk_frontend(monkeypatch, tmp_path):
    captured: dict[str, object] = {}
    image_path = tmp_path / "sample.png"
    Image.new("RGB", (10, 10), color="blue").save(image_path)

    class FakeTkApp:
        def __init__(self, state) -> None:
            captured["state"] = state

        def run(self) -> None:
            captured["ran"] = True

    monkeypatch.setattr("safari_view.main.SafariViewTkApp", FakeTkApp)

    exit_code = main(["tk", "--image", str(image_path), "--mode", "st"])

    assert exit_code == 0
    state = captured["state"]
    assert state.current_image_path == image_path.resolve()
    assert state.current_path == image_path.parent.resolve()
    assert state.render_mode is RenderMode.MODE_ST
    assert captured["ran"] is True
