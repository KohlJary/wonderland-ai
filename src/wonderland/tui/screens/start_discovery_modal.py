"""StartDiscoveryModal — post-project-creation prompt to jump into discovery.

Pushed at the end of ``NewProjectScreen.action_submit`` once the
project is registered. The discovery workflow is the natural first
move on a fresh project (P15 T-m8 UX: the flow is discovery →
milestone-plan → tdd-design → tdd-implement), so the modal
recommends Yes by default and offers a Later button for operators
who want to set up the project shape before talking to the team.

Dismisses with True (launch discovery), False / None (stay).
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Static


class StartDiscoveryModal(ModalScreen[bool | None]):
    """Modal asking whether to jump into the discovery workflow
    immediately after creating a project.

    Returns True when the operator confirms; False / None otherwise.
    """

    BINDINGS = [
        Binding("escape", "later", "Later", show=True),
        Binding("enter", "start", "Start discovery", show=True),
        Binding("y", "start", "Yes", show=False),
        Binding("n", "later", "Later", show=False),
    ]

    def __init__(self, project_name: str) -> None:
        super().__init__()
        self._project_name = project_name

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical(id="start-discovery-modal-root"):
            yield Static(
                f"[b]Project {self._project_name!r} created.[/b]",
                id="start-discovery-modal-header",
            )
            yield Static(
                "[dim]The discovery workflow interviews the team "
                "about personas, technical constraints, and v1 "
                "scope — about 12 minutes of operator attention. "
                "It captures requirements that every later workflow "
                "(milestone-plan, tdd-design, tdd-implement) seeds "
                "from, so running it first means you're not "
                "re-explaining the project on every run.\n\n"
                "Recommended: Yes. You can edit the prime directive "
                "afterward based on what discovery surfaces.[/dim]",
                id="start-discovery-modal-body",
            )
            with Horizontal(id="start-discovery-modal-actions"):
                yield Button(
                    "Yes, start discovery (recommended)",
                    id="start-discovery-modal-confirm",
                    variant="primary",
                )
                yield Button(
                    "Later",
                    id="start-discovery-modal-later",
                )
        yield Footer()

    def action_start(self) -> None:
        self.dismiss(True)

    def action_later(self) -> None:
        self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start-discovery-modal-confirm":
            self.action_start()
        elif event.button.id == "start-discovery-modal-later":
            self.action_later()


__all__ = ["StartDiscoveryModal"]
