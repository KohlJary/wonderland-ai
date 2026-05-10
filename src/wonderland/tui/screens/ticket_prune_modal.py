"""TicketPruneModal — confirmation UI for bulk ticket deletion from
the dashboard's features tree.

Use case: M3 ships duplicate tickets when Rabbit revises mid-meeting
(observed in May 10 obol post-T88 — same source-set, multiple
ticket batches with different slugs). Until the substrate-side
dedup lands (roadmap 171b36e1), the operator needs a fast manual
prune path so 40-ticket M3 outputs collapse to ~13 unique work atoms
before queueing.

UX shape: operator marks tickets for deletion via the dashboard's
features tree (`m` toggle on a ticket node), then `D` opens this
modal showing the count + list. Confirm deletes the files; cancel
keeps the marks for further triage.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Static


class TicketPruneModal(ModalScreen[bool]):
    """Modal confirming bulk-delete of tickets the operator marked.

    Dismisses with:
      - ``True``  if the operator confirms the deletion
      - ``False`` if the operator cancels (marks survive for later)
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
        Binding("enter", "confirm", "Confirm", show=True),
    ]

    DEFAULT_CSS = """
    TicketPruneModal {
        align: center middle;
    }

    TicketPruneModal > #ticket-prune-container {
        width: 80;
        max-height: 30;
        background: $panel;
        border: thick $error;
        padding: 1 2;
    }

    TicketPruneModal #ticket-prune-title {
        color: $error;
        text-style: bold;
        margin-bottom: 1;
    }

    TicketPruneModal #ticket-prune-summary {
        color: $foreground;
        margin-bottom: 1;
    }

    TicketPruneModal #ticket-prune-list-scroll {
        height: 1fr;
        border: round $panel-darken-1;
        padding: 0 1;
        margin-bottom: 1;
    }

    TicketPruneModal #ticket-prune-list {
        color: $foreground;
    }

    TicketPruneModal #ticket-prune-actions {
        height: auto;
        align: center middle;
    }

    TicketPruneModal #ticket-prune-actions Button {
        margin: 0 1;
    }
    """

    def __init__(self, marked: list[tuple[str, str]]) -> None:
        """``marked`` is a list of (ticket_slug, ticket_title) tuples
        — the operator's selection. Order is whatever the dashboard
        passes in (typically tree-order for stability)."""
        super().__init__()
        self._marked = marked

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="ticket-prune-container"):
            yield Static(
                f"Delete {len(self._marked)} ticket(s)?",
                id="ticket-prune-title",
            )
            yield Static(
                "[dim]This permanently removes the marked ticket files "
                "from disk. The action can't be undone from inside the "
                "TUI (operator can git-checkout to recover).[/dim]",
                id="ticket-prune-summary",
            )
            with VerticalScroll(id="ticket-prune-list-scroll"):
                yield Static(self._render_list(), id="ticket-prune-list")
            with Horizontal(id="ticket-prune-actions"):
                yield Button(
                    "Cancel", id="ticket-prune-cancel"
                )
                yield Button(
                    f"Delete {len(self._marked)}",
                    id="ticket-prune-confirm",
                    variant="error",
                )
        yield Footer()

    def _render_list(self) -> str:
        if not self._marked:
            return "[dim](no tickets marked)[/dim]"
        return "\n".join(
            f"  • [b]{title}[/b]   [dim]{slug}[/dim]"
            for slug, title in self._marked
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ticket-prune-cancel":
            self.dismiss(False)
        elif event.button.id == "ticket-prune-confirm":
            self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)

    def action_confirm(self) -> None:
        # Empty-marked guard: the dashboard pushes the modal only
        # when something is marked, but defensively dismiss as
        # cancel rather than commit nothing-to-do.
        if not self._marked:
            self.dismiss(False)
            return
        self.dismiss(True)
