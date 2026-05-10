"""Smoke tests for the TUI hello-world. Verifies the app mounts +
the counter increments when the button is pressed."""

from __future__ import annotations

from textual.widgets import Button, Static

from src.app import HelloApp


async def test_app_mounts() -> None:
    app = HelloApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        # Counter screen renders the initial Count: 0 label.
        label = app.query_one("#counter-label", Static)
        assert "Count:" in str(label.renderable)


async def test_counter_increments_on_button_press() -> None:
    app = HelloApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        button = app.query_one("#increment", Button)
        button.press()
        await pilot.pause()
        label = app.query_one("#counter-label", Static)
        assert "Count:[/b] 1" in str(label.renderable)
