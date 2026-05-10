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
        width: 80%;
        max-width: 110;
        height: auto;
        max-height: 90%;
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
        max-height: 24;
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
    AskUserModal #ask-user-options-label {
        margin-bottom: 0;
        color: $text;
    }
    /* Suggested-answer buttons are stacked vertically (one per row)
     * and full-width so long option text wraps cleanly instead of
     * truncating at the modal border. ``height: auto`` lets each
     * button grow to fit multi-line labels. */
    AskUserModal #ask-user-options {
        height: auto;
        max-height: 30;
        margin-bottom: 1;
    }
    AskUserModal #ask-user-options Button {
        margin: 0 0 1 0;
        width: 1fr;
        height: auto;
        min-height: 3;
        text-align: left;
    }
    """

    def __init__(
        self,
        *,
        asking_agent: str,
        question: str,
        options: list[str] | None = None,
        auto_dismiss_after: float | None = None,
    ) -> None:
        """Construct the modal.

        ``options`` (operator-question follow-up): when the asking
        agent supplies suggested answers, render each one as a
        clickable button above the free-text input. Click submits
        that option verbatim as the operator's reply; the operator
        can still type a custom answer if none of the options fit.
        Empty/None list = original free-text-only experience.

        ``auto_dismiss_after`` (T69 follow-up): if set to a positive
        number of seconds, the modal self-dismisses with None
        (sentinel reply) after that interval if the operator
        hasn't submitted an answer. ``None`` (default) waits
        indefinitely. The LiveRunScreen's auto-sentinel toggle
        passes the configured timeout through here.
        """
        super().__init__()
        self._asking_agent = asking_agent
        self._question = question
        self._options = list(options or [])
        self._auto_dismiss_after = auto_dismiss_after

    def compose(self) -> ComposeResult:
        with Vertical(id="ask-user-container"):
            yield Static(
                f"[b]A question from {self._asking_agent}[/b]",
                id="ask-user-title",
            )
            with VerticalScroll(id="ask-user-question-scroll"):
                yield Static(self._question, id="ask-user-question")
            if self._options:
                # Suggested-answer buttons row. Click submits that
                # option verbatim as the operator's reply.
                yield Static(
                    "[b]Suggested answers[/b] "
                    "[dim](click to submit verbatim, or type a "
                    "custom answer below)[/dim]",
                    id="ask-user-options-label",
                )
                # Vertical stack so each suggested answer gets its
                # own full-width row. Multi-line option text wraps
                # naturally instead of truncating at the modal width.
                with Vertical(id="ask-user-options"):
                    for idx, option in enumerate(self._options):
                        yield Button(
                            option,
                            id=f"ask-user-option-{idx}",
                            classes="ask-user-option",
                        )
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
        # Schedule the auto-dismiss timer if configured. Textual's
        # set_timer auto-cancels when the screen unmounts, so a
        # manual submit/skip before the timer fires cleans up
        # naturally. We don't try to surface a visible countdown —
        # the operator's experience is "modal appeared, type or
        # let it go"; the precise remaining seconds aren't
        # actionable.
        if (
            self._auto_dismiss_after is not None
            and self._auto_dismiss_after > 0
        ):
            self.set_timer(self._auto_dismiss_after, self._auto_dismiss)

    def _auto_dismiss(self) -> None:
        """Timer callback: dismiss with sentinel reply if the modal
        is still mounted (i.e., operator didn't submit/skip in
        time)."""
        # Defensive: only dismiss if we're still the active screen
        # — Textual's timer might fire shortly after a manual
        # dismiss already removed us. is_mounted checks for that.
        if self.is_mounted:
            self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ask-user-submit":
            self.action_submit()
        elif event.button.id == "ask-user-skip":
            self.action_skip()
        elif event.button.id and event.button.id.startswith("ask-user-option-"):
            # A suggested-answer button: submit that option verbatim.
            try:
                idx = int(event.button.id.split("-")[-1])
            except ValueError:
                return
            if 0 <= idx < len(self._options):
                self.dismiss(self._options[idx])

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
