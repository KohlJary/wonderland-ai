"""Launch confirmation modal — guards the irreversible "spend money
on a real run" action with a deliberate Yes/No prompt.

Per the project_tui_lazygit_principle memory: modals are reserved
for cases where a single thing needs the full canvas, OR for
irreversible actions. Burning $3-5 per run qualifies.

Returns True via dismiss when the user confirms, False on decline,
None if dismissed via Escape (treated as decline).
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class LaunchConfirmationScreen(ModalScreen[bool]):
    """Confirmation prompt before kicking off a real Wonderland run.

    The summary inputs (directive, workflow, budget, project root)
    are passed in at construction; the modal renders them so the
    user has a clear view of what they're about to spend money on.
    """

    BINDINGS = [
        Binding("escape", "dismiss_no", "Cancel", show=True),
        Binding("y", "confirm", "Yes", show=True),
        Binding("n", "dismiss_no", "No", show=True),
        Binding("enter", "confirm", "Confirm", show=False),
    ]

    DEFAULT_CSS = """
    LaunchConfirmationScreen {
        align: center middle;
    }
    LaunchConfirmationScreen > #launch-confirm-container {
        width: 70;
        height: auto;
        background: $surface;
        border: round $accent;
        padding: 1 2;
    }
    LaunchConfirmationScreen #launch-confirm-title {
        color: $accent;
        height: auto;
        margin: 0 0 1 0;
    }
    LaunchConfirmationScreen #launch-confirm-detail {
        color: $foreground;
        height: auto;
        margin: 0 0 1 0;
    }
    LaunchConfirmationScreen #launch-confirm-warning {
        color: $warning;
        height: auto;
        margin: 0 0 1 0;
    }
    LaunchConfirmationScreen #launch-confirm-buttons {
        height: auto;
        align: center middle;
    }
    LaunchConfirmationScreen Button {
        margin: 0 1;
    }
    """

    def __init__(
        self,
        *,
        directive: str,
        workflow_name: str,
        budget: float,
        project_root: str,
    ) -> None:
        super().__init__()
        self._directive = directive
        self._workflow_name = workflow_name
        self._budget = budget
        self._project_root = project_root

    def compose(self) -> ComposeResult:
        with Vertical(id="launch-confirm-container"):
            yield Static(
                "[b]Confirm launch[/b]",
                id="launch-confirm-title",
            )
            preview = self._directive.strip().split("\n", 1)[0]
            if len(preview) > 80:
                preview = preview[:80] + "…"
            yield Static(
                f"[b]Directive:[/b] {preview}\n"
                f"[b]Workflow:[/b] {self._workflow_name}\n"
                f"[b]Project:[/b] {self._project_root}\n"
                f"[b]Budget cap:[/b] ~${self._budget:.2f} "
                f"[dim](soft — runs can exceed this by 10-20% before "
                f"the global cap escalates)[/dim]",
                id="launch-confirm-detail",
            )
            yield Static(
                "[b]This will burn API tokens.[/b] "
                "Press [b]y[/b] to confirm, [b]n[/b] or [b]esc[/b] to cancel.",
                id="launch-confirm-warning",
            )
            with Horizontal(id="launch-confirm-buttons"):
                yield Button("Yes (y)", id="launch-yes", variant="primary")
                yield Button("No (n)", id="launch-no")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "launch-yes":
            self.dismiss(True)
        else:
            self.dismiss(False)

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_dismiss_no(self) -> None:
        self.dismiss(False)


__all__ = ["LaunchConfirmationScreen"]
