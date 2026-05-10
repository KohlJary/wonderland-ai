"""EmptyDirectiveConfirmModal — confirms launching a run with no
directive text.

Wonderland's typical run flow expects a directive — Alice's stories
and Cat's ADRs derive from "what does the operator want?" But for
workflows like tdd-implement, the team works from seeded lifecycle
artifacts (features, tickets, contracts already on disk from a prior
design run) — the directive is the lifecycle, not text the operator
types.

This modal makes the empty-directive launch explicit rather than
silent. Operator says yes-or-no; if yes, NewRunScreen's action_go
proceeds with empty directive and the team works from seeds.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Static


class EmptyDirectiveConfirmModal(ModalScreen[bool | None]):
    """Confirms operator wants to launch with no directive.
    Dismisses with True (proceed), False (no), or None (escape)."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
        Binding("enter", "confirm", "Confirm", show=True),
    ]

    def __init__(self, *, workflow_name: str | None = None) -> None:
        super().__init__()
        self.workflow_name = workflow_name

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical(id="empty-dir-modal-root"):
            yield Static(
                "[b yellow]No directive entered.[/b yellow]",
                id="empty-dir-modal-header",
            )
            yield Static(
                self._body_text(),
                id="empty-dir-modal-body",
            )
            with Horizontal(id="empty-dir-modal-actions"):
                yield Button(
                    "▶ Launch without directive",
                    id="empty-dir-modal-confirm",
                    variant="primary",
                )
                yield Button(
                    "Cancel — write directive",
                    id="empty-dir-modal-cancel",
                )
        yield Footer()

    def _body_text(self) -> str:
        is_implement = (
            self.workflow_name == "tdd-implement"
        )
        if is_implement:
            return (
                "[dim]The [b]tdd-implement[/b] workflow operates on "
                "lifecycle artifacts (features, tickets, contracts) "
                "already on disk for this project. A directive is "
                "not strictly required — the team will work from "
                "seeds.[/dim]\n\n"
                "Confirm launching without a directive?"
            )
        return (
            "[dim]The team will read whatever lifecycle artifacts "
            "(features, tickets, contracts, ADRs) exist on disk for "
            "this project, but won't have a fresh directive to "
            "anchor on. This is expected for workflows like "
            "tdd-implement; for fresh-design workflows, you "
            "probably want a directive.[/dim]\n\n"
            "Confirm launching without a directive?"
        )

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "empty-dir-modal-confirm":
            self.action_confirm()
        elif event.button.id == "empty-dir-modal-cancel":
            self.action_cancel()


__all__ = ["EmptyDirectiveConfirmModal"]
