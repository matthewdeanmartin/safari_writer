"""CLI tests for safari_slides."""

from __future__ import annotations

import importlib

import safari_slides
from safari_slides.main import main, parse_args


def test_public_exports_are_explicit() -> None:
    expected = {
        "Presentation",
        "SafariSlidesApp",
        "SafariSlidesState",
        "Slide",
        "build_parser",
        "build_slidemd_from_writer",
        "default_slide_export_name",
        "load_presentation",
        "main",
        "parse_args",
        "parse_slidemd",
        "slides_state_from_writer",
    }

    assert expected.issubset(set(safari_slides.__all__))


def test_parse_args_accepts_optional_input() -> None:
    args = parse_args(["talk.slides.md"])

    assert args.input == "talk.slides.md"


def test_main_returns_error_for_missing_deck(capsys) -> None:
    exit_code = main(["missing.slides.md"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Slide deck not found" in captured.err


def test_main_launches_app_when_input_exists(monkeypatch, tmp_path) -> None:
    deck = tmp_path / "deck.slides.md"
    deck.write_text("# Intro\n", encoding="utf-8")
    launched: list[str] = []
    main_module = importlib.import_module("safari_slides.main")

    class FakeApp:
        def __init__(self, source_path):
            launched.append(str(source_path))

        def run(self) -> None:
            launched.append("run")

    monkeypatch.setattr(main_module, "SafariSlidesApp", FakeApp)

    exit_code = main_module.main([str(deck)])

    assert exit_code == 0
    assert launched == [str(deck.resolve()), "run"]
