"""AbortConfirmModal — confirms aborting a live run.

Abort is destructive: the run ends, no resume path. Operator can
re-launch but the prior run's lifecycle transitions stop where they
were. Telemetry is preserved by the safety-net flush in observer/
live's finally block, so the abort is recoverable in the analysis
sense (you can read what cost what), just not in the workflow sense.

Dismisses with True (confirm abort), False / None (stay running).
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Static


class AbortConfirmModal(ModalScreen[bool | None]):
    """Confirms operator wants to abort the currently-running run.

    Returns True if the operator confirmed; None / False otherwise.
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
        Binding("enter", "confirm", "Confirm", show=True),
        Binding("y", "confirm", "Yes", show=False),
        Binding("n", "cancel", "No", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical(id="abort-modal-root"):
            yield Static(
                "[b yellow]Abort the run?[/b yellow]",
                id="abort-modal-header",
            )
            yield Static(
                "[dim]The run will stop after the current LLM call "
                "finishes. Telemetry is preserved (you'll get a "
                "partial digest at .wonderland/digests/), and any "
                "lifecycle transitions that fired before abort stay "
                "in place. To resume, you'll need to launch a new "
                "run — there's no in-place resume.[/dim]",
                id="abort-modal-body",
            )
            with Horizontal(id="abort-modal-actions"):
                yield Button(
                    "Abort",
                    id="abort-modal-confirm",
                    variant="error",
                )
                yield Button(
                    "Keep running",
                    id="abort-modal-cancel",
                    variant="primary",
                )
        yield Footer()

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "abort-modal-confirm":
            self.action_confirm()
        elif event.button.id == "abort-modal-cancel":
            self.action_cancel()


__all__ = ["AbortConfirmModal"]
