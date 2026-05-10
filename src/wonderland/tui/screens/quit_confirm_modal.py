"""QuitConfirmModal — confirms exiting the Wonderland TUI.

Lightweight guard against accidental quit. The TUI is bound to ``q``
which is also a common navigation key in some operator muscle memory;
without a confirmation step, a stray keystroke can drop the operator
out mid-session and lose their place. Especially relevant when a live
run is in progress — though abort/pause is wired separately, just
exiting the TUI shouldn't stop the run, but it also shouldn't happen
on a fingerslip.

Dismisses with True (quit), False / None (stay).
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Static


class QuitConfirmModal(ModalScreen[bool | None]):
    """Modal confirming the operator wants to exit the TUI.

    Returns True if the operator confirmed the quit; None / False
    otherwise (stay in the app).
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
        Binding("enter", "confirm", "Confirm", show=True),
        Binding("q", "confirm", "Confirm", show=False),
        # n / y are common modal-dismissal shortcuts; surface them
        # here too. y triggers confirm, n triggers cancel.
        Binding("y", "confirm", "Yes", show=False),
        Binding("n", "cancel", "No", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical(id="quit-modal-root"):
            yield Static(
                "[b yellow]Quit Wonderland?[/b yellow]",
                id="quit-modal-header",
            )
            yield Static(
                "[dim]Any in-flight runs will continue in the "
                "background until you abort them. Live-watch state "
                "and unsaved dashboard cursor positions will be "
                "lost. Re-launch with [b]wonderland-tui[/b] to "
                "resume.[/dim]",
                id="quit-modal-body",
            )
            with Horizontal(id="quit-modal-actions"):
                yield Button(
                    "Quit",
                    id="quit-modal-confirm",
                    variant="error",
                )
                yield Button(
                    "Cancel",
                    id="quit-modal-cancel",
                    variant="primary",
                )
        yield Footer()

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit-modal-confirm":
            self.action_confirm()
        elif event.button.id == "quit-modal-cancel":
            self.action_cancel()


__all__ = ["QuitConfirmModal"]
