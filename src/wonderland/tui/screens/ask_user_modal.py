"""Ask-user modal — surfaces a QUESTION-to-operator utterance to the
operator and collects their reply (T69 / P10).

When an agent's deliberation produces a QUESTION addressed to the
operator identity, the runner's user-question watcher routes the
question through the registered handler. For TUI runs, the handler
pushes this modal; the operator types a reply (or skips); the modal
returns the reply text which the watcher then publishes as an
OBSERVATION-from-operator on the bus.

Per the project_tui_lazygit_principle memory: modals are reserved
for cases where a single thing needs the full canvas, or for
attention-pulling interactions. A pending agent question fits both —
the rest of the meeting is paused until the operator answers, and
the question deserves the operator's full focus.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static


class AskUserModal(ModalScreen[str | None]):
    """Modal that surfaces an agent's question to the operator.

    Constructed with the question text and the asking agent's name;
    submits the operator's free-text reply via ``dismiss(reply)``,
    or ``dismiss(None)`` on skip / escape (the runner's watcher
    treats None as a sentinel reply directing the team to proceed
    with their best judgment).
    """

    BINDINGS = [
        Binding("escape", "skip", "Skip", show=True),
        Binding("ctrl+enter", "submit", "Submit", show=True),
    ]

    DEFAULT_CSS = """
    AskUserModal {
        align: center middle;
    }
    AskUserModal > #ask-user-container {
        width: 80;
        height: auto;
        background: $surface;
        border: round $accent;
        padding: 1 2;
    }
    AskUserModal #ask-user-title {
        color: $accent;
        height: auto;
        margin: 0 0 1 0;
    }
    AskUserModal #ask-user-question-scroll {
        height: auto;
        max-height: 12;
        margin: 0 0 1 0;
        border: round $panel;
        padding: 0 1;
    }
    AskUserModal #ask-user-question {
        color: $foreground;
        height: auto;
    }
    AskUserModal #ask-user-input-label {
        color: $primary;
        height: auto;
        margin: 1 0 0 0;
    }
    AskUserModal #ask-user-input {
        margin: 0 0 1 0;
    }
    AskUserModal #ask-user-actions {
        height: auto;
        align: center middle;
    }
    AskUserModal #ask-user-actions Button {
        margin: 0 1;
        min-width: 14;
    }
    """

    def __init__(self, *, asking_agent: str, question: str) -> None:
        super().__init__()
        self._asking_agent = asking_agent
        self._question = question

    def compose(self) -> ComposeResult:
        with Vertical(id="ask-user-container"):
            yield Static(
                f"[b]A question from {self._asking_agent}[/b]",
                id="ask-user-title",
            )
            with VerticalScroll(id="ask-user-question-scroll"):
                yield Static(self._question, id="ask-user-question")
            yield Static(
                "[b]Your answer[/b] "
                "[dim](free text — the team will see it as "
                "an observation from 'operator')[/dim]",
                id="ask-user-input-label",
            )
            yield Input(
                placeholder="Type your answer; Ctrl+Enter to submit, Esc to skip",
                id="ask-user-input",
            )
            with Horizontal(id="ask-user-actions"):
                yield Button("Submit", id="ask-user-submit", variant="primary")
                yield Button("Skip", id="ask-user-skip")

    def on_mount(self) -> None:
        self.query_one("#ask-user-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ask-user-submit":
            self.action_submit()
        elif event.button.id == "ask-user-skip":
            self.action_skip()

    def on_input_submitted(self, _event: Input.Submitted) -> None:
        # Pressing Enter in the input also submits.
        self.action_submit()

    def action_submit(self) -> None:
        text = self.query_one("#ask-user-input", Input).value.strip()
        if not text:
            # Empty submit treated as skip — operator pressed Enter
            # without typing.
            self.dismiss(None)
            return
        self.dismiss(text)

    def action_skip(self) -> None:
        self.dismiss(None)


__all__ = ["AskUserModal"]
