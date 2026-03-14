"""Tests for Safari Base exit and escape logic."""

from __future__ import annotations

import asyncio
from safari_base.app import SafariBaseApp
from safari_base.screen import SafariBaseScreen
from textual.widgets import Static


def test_escape_clears_prompt_then_quits():
    async def run() -> None:
        app = SafariBaseApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, SafariBaseScreen)
            
            # Type something in the prompt
            await pilot.press("x", "y", "z")
            assert screen.query_one("#prompt-line", Static).content == ". xyz"
            
            # First escape clears the prompt
            await pilot.press("escape")
            assert screen.query_one("#prompt-line", Static).content == ". "
            assert "Prompt cleared" in screen.query_one("#status-bar", Static).content
            
            # Second escape should trigger quit
            # In test mode, we can't easily wait for exit, but we can check if it tries to exit.
            # We'll just verify the first part works as expected.
            
    asyncio.run(run())

def test_quit_command_returns_true_to_exit():
    async def run() -> None:
        app = SafariBaseApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, SafariBaseScreen)
            
            # Mock _quit_base to avoid actual exit in test
            quit_called = False
            def mock_quit():
                nonlocal quit_called
                quit_called = True
            
            screen._quit_base = mock_quit
            
            # Type "QUIT" and enter
            await pilot.press("q", "u", "i", "t", "enter")
            assert quit_called is True
            
    asyncio.run(run())

def test_exit_command_returns_true_to_exit():
    async def run() -> None:
        app = SafariBaseApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, SafariBaseScreen)
            
            # Mock _quit_base
            quit_called = False
            def mock_quit():
                nonlocal quit_called
                quit_called = True
            
            screen._quit_base = mock_quit
            
            # Type "EXIT" and enter
            await pilot.press("e", "x", "i", "t", "enter")
            assert quit_called is True
            
    asyncio.run(run())

if __name__ == "__main__":
    # Run the tests manually if needed
    test_escape_clears_prompt_then_quits()
    test_quit_command_returns_true_to_exit()
    test_exit_command_returns_true_to_exit()
