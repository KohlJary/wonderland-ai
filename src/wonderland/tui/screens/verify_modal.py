"""VerifyRejectModal — operator's human-gate UI for the feature
lifecycle (P12 T90).

When a feature reaches ``ready_for_review`` (M6 verdict approve +
all tickets implemented + tests pass), the substrate's reality check
caps out at "tests pass according to my own scenarios." The operator
verification step is what closes that loop — the human runs the
feature, exercises its UX, and decides whether the team's deliverable
matches the operator's actual intent.

This modal is the moment that decision happens. Operator picks one
of three branches:

  - **Verified**: feature works as intended. Notes optional but
    recommended (positive feedback on what worked feeds Alice and
    Caterpillar's next-iteration context).
  - **Rejected**: feature doesn't meet expectations. Notes required —
    the operator must say *why* so the team has feedback to act on.
    Rejection notes flow into next-run deliberation context via the
    state-transition log (and eventually bus-emitted utterances when
    that follow-up lands).
  - **Cancel**: take no action; come back later.

The modal is reached from the dashboard's per-feature Verify/Reject
buttons (T89 left those as stubs). Only features in
``ready_for_review`` state can land here; the dashboard guards the
button paths so other states can't open this modal.
"""

from __future__ import annotations

from typing import Literal

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Static, TextArea

from wonderland.feature_lifecycle import FeatureState


VerifyMode = Literal["verify", "reject"]


class VerifyRejectModal(ModalScreen[tuple[FeatureState, str] | None]):
    """Modal that captures the operator's verify-or-reject decision +
    notes. Dismisses with:
      - ``(FeatureState.VERIFIED, notes)`` if verified
      - ``(FeatureState.REJECTED, notes)`` if rejected
      - ``None`` if cancelled

    Notes is always a string (possibly empty for verify; non-empty
    for reject — the modal enforces this before allowing submit).
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
        Binding("ctrl+s", "submit", "Confirm", show=True),
    ]

    def __init__(
        self,
        *,
        feature_slug: str,
        feature_title: str,
        mode: VerifyMode,
    ) -> None:
        super().__init__()
        self.feature_slug = feature_slug
        self.feature_title = feature_title
        self.mode = mode

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical(id="verify-modal-root"):
            yield Static(
                self._header_text(),
                id="verify-modal-header",
            )
            yield Static(
                f"[b]{self.feature_title}[/b]\n"
                f"[dim]{self.feature_slug}[/dim]",
                id="verify-modal-feature",
            )
            yield Static(
                self._guidance_text(),
                id="verify-modal-guidance",
            )
            with VerticalScroll(id="verify-modal-notes-scroll"):
                yield TextArea(
                    "",
                    id="verify-modal-notes",
                    language=None,
                )
            with Horizontal(id="verify-modal-actions"):
                yield Button(
                    self._confirm_label(),
                    id="verify-modal-confirm",
                    variant=self._confirm_variant(),
                )
                yield Button(
                    "Cancel (esc)",
                    id="verify-modal-cancel",
                )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#verify-modal-notes", TextArea).focus()

    # ------------------------------------------------------------------ #
    # Mode-dependent text
    # ------------------------------------------------------------------ #

    def _header_text(self) -> str:
        if self.mode == "verify":
            return "[b green]Verify feature[/b green]"
        return "[b red]Reject feature[/b red]"

    def _guidance_text(self) -> str:
        if self.mode == "verify":
            return (
                "[b]Notes (optional):[/b] What worked? Positive "
                "feedback on the deliverable will surface in the "
                "team's next-run context — Alice + Caterpillar see "
                "what the operator considered well-shipped."
            )
        return (
            "[b yellow]Notes (required):[/b yellow] Why are you "
            "rejecting this feature? Be specific — the team will "
            "see these notes on the next run and use them as "
            "feedback for re-design or re-implementation."
        )

    def _confirm_label(self) -> str:
        if self.mode == "verify":
            return "✓ Confirm verified (ctrl+s)"
        return "✗ Confirm rejected (ctrl+s)"

    def _confirm_variant(self) -> str:
        # Textual's Button accepts 'success' / 'error' / 'warning' /
        # 'primary' / 'default'. Verify gets success-green; reject
        # gets error-red.
        return "success" if self.mode == "verify" else "error"

    # ------------------------------------------------------------------ #
    # Submit / cancel
    # ------------------------------------------------------------------ #

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_submit(self) -> None:
        notes = self.query_one("#verify-modal-notes", TextArea).text.strip()
        if self.mode == "reject" and not notes:
            self.notify(
                "Rejection requires notes — please explain why so "
                "the team has feedback to act on.",
                severity="warning",
                timeout=5,
            )
            self.query_one("#verify-modal-notes", TextArea).focus()
            return
        target_state = (
            FeatureState.VERIFIED
            if self.mode == "verify"
            else FeatureState.REJECTED
        )
        self.dismiss((target_state, notes))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "verify-modal-confirm":
            self.action_submit()
        elif event.button.id == "verify-modal-cancel":
            self.action_cancel()


__all__ = ["VerifyMode", "VerifyRejectModal"]
