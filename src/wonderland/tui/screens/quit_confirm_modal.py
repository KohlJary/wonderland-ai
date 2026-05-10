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
            # Slice B: surface in-flight runs. Quitting kills them
            # — until detached background processes land, the
            # consumer task lives on the App's event loop and dies
            # with the app. The operator should know what they're
            # tearing down before they confirm.
            active = getattr(self.app, "_active_run", None)
            if active is not None and not active.is_terminal:
                body_text = (
                    f"[b red]A run is in flight: "
                    f"{active.run_id}[/b red]\n"
                    f"[dim]Quitting will abort it — the consumer "
                    f"task lives in this app's event loop. "
                    f"Telemetry written so far is preserved on "
                    f"disk; mid-meeting state is lost. Press Cancel "
                    f"and abort it explicitly from the live-watch "
                    f"screen if you'd rather a clean shutdown.[/dim]"
                )
            else:
                body_text = (
                    "[dim]Live-watch state and unsaved dashboard "
                    "cursor positions will be lost. Re-launch with "
                    "[b]wonderland-tui[/b] to resume browsing.[/dim]"
                )
            yield Static(body_text, id="quit-modal-body")
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
