"""InterviewModal — surfaces a discovery (P14) question batch to
the operator and collects their answers.

The substrate writes ``pending_interview.json`` under the run dir
when an interviewer agent is ready for operator input; the App's
interview poller picks that up and pushes this modal. Operator
fills the form (or free-responds, or skips the section), submits;
the App writes ``pending_interview_answers.json`` back; the
subprocess's bridge picks the answers up and feeds them to the
interviewer's next deliberation.

Per the project_tui_lazygit_principle memory: modals are reserved
for single-thing-needs-full-canvas interactions. A discovery
interview fits — the rest of the run is paused, the operator's
answers shape downstream design, and structured form input
deserves dedicated screen real estate. Free-response escapes on
every field mean the form never traps an operator with a more
nuanced answer than the structured widget allows.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Checkbox,
    Input,
    Label,
    RadioButton,
    RadioSet,
    Static,
    TextArea,
)


@dataclass(frozen=True)
class InterviewModalResult:
    """What InterviewModal returns via dismiss().

    ``batch_id`` round-trips back to the substrate so the bridge can
    disambiguate this answer set from any stale follow-up answers
    file. ``answers`` is a list of dicts shaped for direct serialization
    into ``pending_interview_answers.json``. ``section_skipped`` short-
    circuits the interviewer — the bridge returns immediately and the
    substrate emits InterviewEnded with outcome SKIPPED.
    """

    batch_id: str
    interview_id: str
    answers: list[dict[str, Any]]
    section_skipped: bool


class InterviewModal(ModalScreen[InterviewModalResult | None]):
    """Multi-question form modal. Constructed with the raw payload
    parsed from ``pending_interview.json``; dismisses with an
    ``InterviewModalResult`` on submit/skip-section, or ``None`` on
    Esc cancel (the substrate treats None as "operator dismissed
    without committing"; the bridge keeps waiting until timeout)."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
        Binding("ctrl+enter", "submit", "Submit", show=True),
    ]

    DEFAULT_CSS = """
    InterviewModal {
        align: center middle;
    }
    InterviewModal > #interview-container {
        width: 85%;
        max-width: 130;
        height: 90%;
        background: $surface;
        border: thick $accent;
        padding: 1 2;
    }
    InterviewModal #interview-title {
        color: $accent;
        text-style: bold;
        height: auto;
        margin: 0 0 1 0;
    }
    InterviewModal #interview-meta {
        color: $text;
        height: auto;
        margin: 0 0 1 0;
    }
    InterviewModal #interview-goal {
        color: $primary;
        height: auto;
        margin: 0 0 1 0;
        padding: 0 1;
        border: round $panel-darken-1;
    }
    InterviewModal #interview-questions-scroll {
        height: 1fr;
        margin: 0 0 1 0;
        border: round $panel;
        padding: 1 1;
    }
    InterviewModal .interview-question-block {
        height: auto;
        margin: 0 0 2 0;
        padding: 0 0 1 0;
        border-bottom: tall $panel-darken-2;
    }
    InterviewModal .interview-question-text {
        color: $foreground;
        text-style: bold;
        height: auto;
        margin: 0 0 1 0;
    }
    InterviewModal .interview-required-tag {
        color: $error;
    }
    InterviewModal .interview-free-text-input {
        height: 4;
        margin: 0 0 1 0;
    }
    InterviewModal .interview-options {
        height: auto;
        margin: 0 0 1 0;
    }
    InterviewModal .interview-followup-label {
        color: $primary-darken-1;
        height: auto;
        margin: 1 0 0 0;
    }
    InterviewModal .interview-followup-input {
        height: 3;
        margin: 0 0 1 0;
    }
    InterviewModal #interview-actions {
        height: auto;
        align: center middle;
    }
    InterviewModal #interview-actions Button {
        margin: 0 1;
        min-width: 16;
    }
    """

    def __init__(self, payload: dict[str, Any]) -> None:
        """Construct from the raw pending_interview.json payload.

        Expected shape:
          {
            "batch_id": str,
            "interview_id": str,
            "label": str,
            "name": str,
            "interviewer": str,
            "goal": str,
            "estimated_minutes": int,
            "questions": [
              {"id": str, "text": str, "kind": str,
               "required": bool, "options": list[str]},
              ...
            ]
          }
        """
        super().__init__()
        self._batch_id = str(payload.get("batch_id", ""))
        self._interview_id = str(payload.get("interview_id", ""))
        self._label = str(payload.get("label", ""))
        self._name = str(payload.get("name", ""))
        self._interviewer = str(payload.get("interviewer", ""))
        self._goal = str(payload.get("goal", ""))
        self._estimated_minutes = int(payload.get("estimated_minutes", 5))
        raw_questions = payload.get("questions") or []
        self._questions: list[dict[str, Any]] = [
            q for q in raw_questions if isinstance(q, dict)
        ]

    def compose(self) -> ComposeResult:
        with Vertical(id="interview-container"):
            yield Static(
                f"[b]{self._label} — {self._name}[/b]   "
                f"[dim]interviewer: {self._interviewer}[/dim]",
                id="interview-title",
            )
            yield Static(
                f"[dim]~{self._estimated_minutes} min · "
                f"{len(self._questions)} question"
                f"{'s' if len(self._questions) != 1 else ''}"
                "[/dim]",
                id="interview-meta",
            )
            if self._goal.strip():
                yield Static(
                    f"[b]Goal:[/b] {self._goal}",
                    id="interview-goal",
                )
            with VerticalScroll(id="interview-questions-scroll"):
                for question in self._questions:
                    yield from self._compose_question(question)
            with Horizontal(id="interview-actions"):
                yield Button(
                    "Submit",
                    id="interview-submit",
                    variant="primary",
                )
                yield Button(
                    "Skip section",
                    id="interview-skip-section",
                )
                yield Button(
                    "Cancel",
                    id="interview-cancel",
                )

    def _compose_question(self, q: dict[str, Any]) -> ComposeResult:
        """Yield the widgets for one question — the question text,
        the structured widget per kind, and the free-response escape
        box below. Each question's id namespaces the widget ids so
        action_submit can pull them back out reliably."""
        qid = q.get("id", "")
        text = q.get("text", "")
        kind = q.get("kind", "free_text")
        required = bool(q.get("required", False))
        options = q.get("options") or []
        required_tag = (
            " [red](required)[/red]" if required else ""
        )

        with Vertical(classes="interview-question-block"):
            yield Static(
                f"{text}{required_tag}",
                classes="interview-question-text",
            )

            if kind == "free_text":
                yield TextArea(
                    "",
                    id=f"q-{qid}-text",
                    classes="interview-free-text-input",
                )
            elif kind == "single_choice":
                with RadioSet(id=f"q-{qid}-radio", classes="interview-options"):
                    for opt in options:
                        yield RadioButton(opt)
            elif kind == "multi_choice":
                with Vertical(classes="interview-options"):
                    for idx, opt in enumerate(options):
                        yield Checkbox(opt, id=f"q-{qid}-check-{idx}")
            elif kind == "numeric":
                yield Input(
                    placeholder="(number)",
                    id=f"q-{qid}-numeric",
                    type="number",
                )
            else:
                # Unknown kind — fall back to free_text so the operator
                # can still answer rather than getting stuck.
                yield TextArea(
                    "",
                    id=f"q-{qid}-text",
                    classes="interview-free-text-input",
                )

            yield Label(
                "Free response (optional — elaborate beyond the form):",
                classes="interview-followup-label",
            )
            yield Input(
                placeholder="extra context, caveats, anything the form didn't capture",
                id=f"q-{qid}-free",
                classes="interview-followup-input",
            )

    # ------------------------------------------------------------------ #
    # Buttons + actions
    # ------------------------------------------------------------------ #

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "interview-submit":
            self.action_submit()
        elif bid == "interview-skip-section":
            self._dismiss_skip()
        elif bid == "interview-cancel":
            self.action_cancel()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_submit(self) -> None:
        answers = self._collect_answers()
        # Required-field check. If a required field has neither a
        # value nor free-response text, surface a notification and
        # stay on the modal.
        for i, ans in enumerate(answers):
            q = self._questions[i]
            if not q.get("required"):
                continue
            value = ans.get("value")
            value_filled = value not in (None, "", [])
            free_filled = bool(str(ans.get("free_response", "")).strip())
            if not (value_filled or free_filled):
                self.notify(
                    f"Required question missing: {q.get('text', '')[:60]!r}",
                    severity="warning",
                    timeout=6,
                )
                return
        self.dismiss(
            InterviewModalResult(
                batch_id=self._batch_id,
                interview_id=self._interview_id,
                answers=answers,
                section_skipped=False,
            )
        )

    def _dismiss_skip(self) -> None:
        """Skip-section: shipping an empty answers list with
        section_skipped=True. The substrate's _run_one_interview
        closes the interview without ever calling the interviewer."""
        self.dismiss(
            InterviewModalResult(
                batch_id=self._batch_id,
                interview_id=self._interview_id,
                answers=[],
                section_skipped=True,
            )
        )

    # ------------------------------------------------------------------ #
    # Answer extraction
    # ------------------------------------------------------------------ #

    def _collect_answers(self) -> list[dict[str, Any]]:
        """Walk each question's widgets and produce the answer dict
        shape the bridge expects. Free-response text is always
        captured alongside the structured value — the interviewer
        agent sees both halves."""
        out: list[dict[str, Any]] = []
        for q in self._questions:
            qid = q.get("id", "")
            kind = q.get("kind", "free_text")
            options = q.get("options") or []

            value: Any = None
            if kind == "free_text":
                try:
                    raw = self.query_one(f"#q-{qid}-text", TextArea).text
                except Exception:  # noqa: BLE001
                    raw = ""
                if raw.strip():
                    value = raw.strip()
            elif kind == "single_choice":
                try:
                    rs = self.query_one(f"#q-{qid}-radio", RadioSet)
                    pressed_idx = rs.pressed_index
                except Exception:  # noqa: BLE001
                    pressed_idx = -1
                if pressed_idx is not None and 0 <= pressed_idx < len(options):
                    value = options[pressed_idx]
            elif kind == "multi_choice":
                selected: list[str] = []
                for idx, opt in enumerate(options):
                    try:
                        cb = self.query_one(
                            f"#q-{qid}-check-{idx}", Checkbox
                        )
                    except Exception:  # noqa: BLE001
                        continue
                    if cb.value:
                        selected.append(opt)
                value = selected or None
            elif kind == "numeric":
                try:
                    raw = self.query_one(
                        f"#q-{qid}-numeric", Input
                    ).value.strip()
                except Exception:  # noqa: BLE001
                    raw = ""
                if raw:
                    try:
                        value = float(raw)
                    except ValueError:
                        value = None
            else:
                # Fallback path — treated as free_text.
                try:
                    raw = self.query_one(f"#q-{qid}-text", TextArea).text
                except Exception:  # noqa: BLE001
                    raw = ""
                if raw.strip():
                    value = raw.strip()

            try:
                free = self.query_one(f"#q-{qid}-free", Input).value.strip()
            except Exception:  # noqa: BLE001
                free = ""

            out.append(
                {
                    "question_id": qid,
                    "value": value,
                    "free_response": free,
                    "skipped": value is None and not free,
                }
            )
        return out


__all__ = ["InterviewModal", "InterviewModalResult"]
