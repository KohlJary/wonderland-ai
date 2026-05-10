"""Textual app entry point — counter screen as the hello-world.

Extend with new screens via ``self.push_screen(MyScreen())`` and
new key bindings via ``BINDINGS = [Binding(key, action, label)]``.
"""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Button, Footer, Header, Static


class CounterScreen(Static):
    """A reactive counter — pressing the button increments. Used
    to demonstrate Textual's reactive + button-press flow."""

    DEFAULT_CSS = """
    CounterScreen {
        align: center middle;
        height: 1fr;
        padding: 2;
    }
    CounterScreen #counter-label {
        text-align: center;
        height: auto;
        margin-bottom: 1;
    }
    CounterScreen Button {
        min-width: 20;
    }
    """

    count: reactive[int] = reactive(0)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(self._format(), id="counter-label")
            yield Button("Click me", id="increment", variant="primary")

    def _format(self) -> str:
        return f"[b]Count:[/b] {self.count}"

    def watch_count(self, _old: int, _new: int) -> None:
        if self.is_mounted:
            self.query_one("#counter-label", Static).update(self._format())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "increment":
            self.count += 1


class HelloApp(App[None]):
    """Hello-world TUI — extend with new screens."""

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield CounterScreen()
        yield Footer()


def run() -> None:
    HelloApp().run()


if __name__ == "__main__":
    run()
