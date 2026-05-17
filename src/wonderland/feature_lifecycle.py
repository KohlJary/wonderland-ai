"""Feature lifecycle: state machine + persistence (P12 T85).

Promotes 'feature' from a one-shot M2.5 emission to a first-class
entity that persists across runs with operator-visible state. The
lifecycle is the foundation for splitting tdd-serial-phased into
composable design + implement + verify atoms (T88) and for the
operator's batch-and-verify UX (T89-T92).

State machine (transitions valid per LEGAL_TRANSITIONS below):

    [initial]
        ↓ (Rabbit emits feature in M2.5)
    proposed
        ↓ (M3 starts negotiating contracts)
    in_design
        ↓ (M4 finishes test scenarios; T87 auto-transition)
    designed ─────────┐
        ↓             │ (operator rejects at design review)
        ↓ (operator   ↓
        ↓  queues)    │
    queued       rejected
        ↓
    in_progress
        ↓ (M6 verdict approve + tests pass + impl complete)
    ready_for_review ─┐
        ↓             ↓
    verified     rejected
                       ↓ (terminal — operator restarts with new slug)

Storage: ``<project_root>/.wonderland/feature-states.jsonl``,
append-only state-transition log. Each line is one TransitionRecord.
The "current state" of a feature is the to_state of its most recent
transition. Reading the log gives the full history for audit + for
cross-run continuity (the disk-fallback seed mechanism shipped in
0.3.0 will eventually surface state-transition utterances so the
team's deliberation context includes "the operator rejected
feature-002 with note: 'Plaid auth handling is hand-waved'").

API:
  - ``transition(project_root, slug, to_state, by, notes=...)`` —
    appends a transition record after validating the transition is
    legal given the feature's current state. Raises
    ``IllegalTransitionError`` on invalid moves.
  - ``get_state(project_root, slug)`` — current state (or None if
    the feature has no transitions logged yet).
  - ``list_features_in_state(project_root, state)`` — slugs of
    features currently in the named state.
  - ``transitions_for(project_root, slug)`` — full history for one
    feature.
  - ``all_transitions(project_root)`` — full log (audit / debugging).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field


FEATURE_STATES_FILENAME = "feature-states.jsonl"


class FeatureState(StrEnum):
    """Lifecycle states a feature can occupy.

    The transitions between them are validated by ``LEGAL_TRANSITIONS``;
    illegal transitions raise. State semantics:

    - ``proposed``: Rabbit emitted the feature in M2.5 but no further
      work has happened.
    - ``in_design``: M3 contracts and/or M4 scenarios are being
      written for this feature.
    - ``designed``: contracts + test scenarios complete. Ready for
      operator review and possible implementation queueing.
    - ``queued``: operator has selected this feature for the next
      implementation run.
    - ``in_progress``: M5 is actively shipping implementations for
      this feature's tickets.
    - ``ready_for_review``: implementation complete, M6 reviewed +
      approved, tests pass. Awaits operator verification.
    - ``verified``: operator ran the feature, exercised UX, accepted.
    - ``rejected``: operator rejected at either the design-review or
      ready-for-review gate. Terminal — restart with a new slug if
      the underlying need still applies.
    """

    PROPOSED = "proposed"
    IN_DESIGN = "in_design"
    DESIGNED = "designed"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    READY_FOR_REVIEW = "ready_for_review"
    VERIFIED = "verified"
    REJECTED = "rejected"


# Legal forward transitions per state. None as a key means "no prior
# state" — the only valid initial transition is to ``proposed``.
#
# Worth noting: ``designed → queued`` and ``queued → designed`` are
# both legal so the operator can un-queue a feature they queued by
# mistake. ``rejected`` is terminal — the design-feedback channel
# (T90's notes) carries forward into next runs via cross-run
# continuity, but the rejected feature itself doesn't transition out.
LEGAL_TRANSITIONS: dict[FeatureState | None, frozenset[FeatureState]] = {
    None: frozenset({FeatureState.PROPOSED}),
    FeatureState.PROPOSED: frozenset({
        FeatureState.IN_DESIGN,
        FeatureState.REJECTED,  # operator can reject right at proposal
    }),
    FeatureState.IN_DESIGN: frozenset({
        FeatureState.DESIGNED,
        FeatureState.REJECTED,
    }),
    FeatureState.DESIGNED: frozenset({
        FeatureState.QUEUED,
        # Operator-driven: send back to design for re-decomposition.
        # Validation5 surfaced this need — features 4 + 5 had 0
        # tickets attributed (M3 slug drift left them undeployable)
        # and the only way to generate tickets was to rerun design
        # on those features. tdd-decompose.yaml workflow picks up
        # features in in_design and iterates M3 over them; after
        # decomposition M3 transitions them back to designed via
        # transition_iteration_to.
        FeatureState.IN_DESIGN,
        FeatureState.REJECTED,  # design-review rejection
    }),
    FeatureState.QUEUED: frozenset({
        FeatureState.IN_PROGRESS,
        FeatureState.DESIGNED,  # un-queue
    }),
    FeatureState.IN_PROGRESS: frozenset({
        FeatureState.READY_FOR_REVIEW,
        FeatureState.DESIGNED,  # operator escape hatch — abort impl, send back to design
        FeatureState.REJECTED,  # implementation aborted
    }),
    FeatureState.READY_FOR_REVIEW: frozenset({
        FeatureState.VERIFIED,
        FeatureState.REJECTED,
    }),
    FeatureState.VERIFIED: frozenset(),  # terminal
    FeatureState.REJECTED: frozenset(),  # terminal
}


class IllegalTransitionError(ValueError):
    """Raised when ``transition()`` is asked to move a feature into
    a state its current state doesn't permit. The error message
    includes the offending move + the legal options for context."""


class TransitionRecord(BaseModel):
    """One state-transition event in the append-only log."""

    feature_slug: str = Field(min_length=1)
    from_state: FeatureState | None = Field(
        default=None,
        description=(
            "The state the feature was in before this transition. "
            "None for the initial transition into ``proposed``."
        ),
    )
    to_state: FeatureState
    by: str = Field(
        min_length=1,
        description=(
            "Who initiated the transition: an agent name "
            "('white_rabbit', 'caterpillar', etc.), the literal "
            "string 'operator' for human actions, or 'system' for "
            "auto-transitions fired by T87/T91 rules."
        ),
    )
    at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    notes: str | None = Field(
        default=None,
        description=(
            "Optional context. Required for rejections (operators "
            "must say why); used for cross-run continuity in T90's "
            "verify/reject UI — notes get surfaced as state-change "
            "utterances on subsequent runs."
        ),
    )


def _registry_path(project_root: Path) -> Path:
    return project_root / ".wonderland" / FEATURE_STATES_FILENAME


def _append_record(project_root: Path, record: TransitionRecord) -> None:
    """Atomic-ish append: open in append mode and write one line.
    Append-only log → no need for tmp+rename pattern; concurrent
    appends on POSIX are safe at the line level for writes < 4KB
    (PIPE_BUF), and our records are well under that."""
    path = _registry_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = record.model_dump_json() + "\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(line)


def all_transitions(project_root: Path) -> list[TransitionRecord]:
    """Return every transition logged for this project, in append
    order. Empty list if the registry file doesn't exist or is
    empty. Malformed lines are skipped silently — partial writes
    during a crash shouldn't stop the rest of the log from
    loading."""
    path = _registry_path(project_root)
    if not path.is_file():
        return []
    records: list[TransitionRecord] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                records.append(TransitionRecord.model_validate(data))
            except (json.JSONDecodeError, ValueError):
                # Best-effort: skip malformed lines. Logging is the
                # caller's problem; the lifecycle layer doesn't have
                # a logger configured.
                continue
    return records


def transitions_for(
    project_root: Path, feature_slug: str
) -> list[TransitionRecord]:
    """Full history for one feature, in chronological order. Empty
    list if the feature has never transitioned."""
    return [
        r for r in all_transitions(project_root)
        if r.feature_slug == feature_slug
    ]


def _tickets_for_feature(
    project_root: Path, feature_slug: str
) -> list[str]:
    """Return the slugs of all tickets whose ``Sources:`` field
    names ``feature_slug`` as their parent. Returns [] when the
    map can't be built (no tickets on disk, registry error, etc.).

    Lazy-imports ``_ticket_to_feature_map`` from workflow.py so
    this module stays import-cheap and avoids a feature_lifecycle
    ↔ workflow cycle at module load."""
    try:
        from wonderland.workflow import _ticket_to_feature_map
    except Exception:  # noqa: BLE001
        return []
    try:
        mapping = _ticket_to_feature_map(project_root)
    except Exception:  # noqa: BLE001
        return []
    return [slug for slug, feat in mapping.items() if feat == feature_slug]


def _derive_post_ticket_state(
    project_root: Path, feature_slug: str
) -> FeatureState | None:
    """Roll the feature's tickets up into a derived feature state.

    Returns one of QUEUED / IN_PROGRESS / READY_FOR_REVIEW when
    the rollup is meaningful, or None when:
      - no tickets exist for this feature yet (M3 hasn't decomposed
        it, so feature stays in whatever pre-ticket state it's in)
      - tickets exist but none have an operator-touched state
        (all PENDING or no record yet — same "stay pre-ticket"
        semantics)

    Rollup rules (Jira-style epic-from-stories):

      - all tickets DONE → READY_FOR_REVIEW
      - any ticket IN_PROGRESS or ABORTED → IN_PROGRESS
        (mid-flight work or operator owes a retry call; the
        ABORTED-as-in_progress mapping deliberately surfaces
        retry-pending features in the same triage bucket as
        actively-running ones; the ⚠ ticket badge in the
        dashboard tree carries the "needs attention" detail.)
      - any ticket QUEUED (and none active) → QUEUED
      - everything else (mixed PENDING + some DONE) → IN_PROGRESS

    The substrate's per-ticket lifecycle is the source of truth;
    this function is read-only and computes from the latest tickets.
    """
    from wonderland.ticket_lifecycle import (
        TicketState,
        get_state as get_ticket_state,
    )

    tickets = _tickets_for_feature(project_root, feature_slug)
    if not tickets:
        return None
    states = [get_ticket_state(project_root, t) for t in tickets]

    # All untouched → no derivation, feature stays in its log state.
    if all(s in (None, TicketState.PENDING) for s in states):
        return None

    # All terminal-positive → ready for operator review.
    if all(s == TicketState.DONE for s in states):
        return FeatureState.READY_FOR_REVIEW

    # Any in-flight or retry-pending → in_progress umbrella.
    if any(
        s in (TicketState.IN_PROGRESS, TicketState.ABORTED)
        for s in states
    ):
        return FeatureState.IN_PROGRESS

    # Any queued, none active → queued.
    if any(s == TicketState.QUEUED for s in states):
        return FeatureState.QUEUED

    # Mixed PENDING + DONE with nothing queued / active. Reads as
    # "partial work shipped, more pending" — still in_progress.
    return FeatureState.IN_PROGRESS


def get_state(
    project_root: Path, feature_slug: str
) -> FeatureState | None:
    """Current state of a feature, layered over two sources:

      1. Operator terminals (VERIFIED / REJECTED) from the
         transition log — these win unconditionally. Verify/reject
         is final; the substrate doesn't auto-revert them when
         the operator later mutates ticket state.
      2. Ticket-derived rollup (QUEUED / IN_PROGRESS /
         READY_FOR_REVIEW) — see ``_derive_post_ticket_state``.
         This replaces the previous "read the most-recent log
         entry verbatim" path for post-design states. Legacy log
         entries for those states (queued, in_progress,
         ready_for_review written by older runs) are ignored when
         tickets are around — the tickets win.
      3. Pre-ticket states (PROPOSED / IN_DESIGN / DESIGNED) and
         the legacy-only edge case (post-ticket log entries with
         no tickets on disk): fall back to the most recent log
         entry.

    Returns None when no log entries exist and no tickets exist —
    same "feature exists on disk but hasn't entered the lifecycle"
    semantics as before.
    """
    history = transitions_for(project_root, feature_slug)
    if not history:
        return None

    # Operator terminals override everything.
    for record in reversed(history):
        if record.to_state in (
            FeatureState.VERIFIED, FeatureState.REJECTED
        ):
            return record.to_state

    derived = _derive_post_ticket_state(project_root, feature_slug)
    if derived is not None:
        return derived

    # No tickets (or all untouched) — last log entry wins.
    return history[-1].to_state


def list_features_in_state(
    project_root: Path, state: FeatureState
) -> list[str]:
    """Slugs of features currently in the given state. Walks the
    full log to compute current-state-per-feature, then filters.
    Returns slugs in alphabetical order."""
    current: dict[str, FeatureState] = {}
    for record in all_transitions(project_root):
        current[record.feature_slug] = record.to_state
    matches = [slug for slug, s in current.items() if s == state]
    matches.sort()
    return matches


def transition(
    project_root: Path,
    feature_slug: str,
    to_state: FeatureState,
    by: str,
    notes: str | None = None,
) -> TransitionRecord:
    """Append a state-transition record after validating the move
    is legal given the feature's current state.

    Raises ``IllegalTransitionError`` if the requested transition
    isn't in ``LEGAL_TRANSITIONS`` for the current state.
    Concurrency: append is atomic at the line level on POSIX; the
    state read happens before the append, so simultaneous writes
    could in principle race. In practice, lifecycle transitions
    are operator-driven or single-runner-driven; concurrent
    transitions on the same feature don't happen.
    """
    current = get_state(project_root, feature_slug)
    legal = LEGAL_TRANSITIONS.get(current, frozenset())
    if to_state not in legal:
        from_label = current.value if current else "(initial)"
        legal_labels = sorted(s.value for s in legal) or ["(none — terminal state)"]
        raise IllegalTransitionError(
            f"Illegal transition for feature {feature_slug!r}: "
            f"{from_label} → {to_state.value}. "
            f"Legal moves from {from_label}: {legal_labels}"
        )
    record = TransitionRecord(
        feature_slug=feature_slug,
        from_state=current,
        to_state=to_state,
        by=by,
        notes=notes,
    )
    _append_record(project_root, record)
    return record


def back_fill_state(
    project_root: Path,
    feature_slug: str,
    state: FeatureState,
    *,
    notes: str | None = None,
) -> TransitionRecord:
    """Record a state for a feature WITHOUT validating the transition.
    Used for migration: pre-T85 features that exist on disk but have
    no transition log get back-filled to a sensible state so they can
    enter the lifecycle. Bypasses ``LEGAL_TRANSITIONS`` validation.

    Refuses to back-fill features that ALREADY have a state record
    — back-fill is for migration only, not for retconning history.
    Returns the recorded TransitionRecord.

    Records the transition with ``by='system_backfill'`` so the
    audit log distinguishes back-filled state from legitimate
    operator/agent transitions.
    """
    if get_state(project_root, feature_slug) is not None:
        raise ValueError(
            f"feature {feature_slug!r} already has a recorded state; "
            f"back_fill_state is for migration only"
        )
    record = TransitionRecord(
        feature_slug=feature_slug,
        from_state=None,
        to_state=state,
        by="system_backfill",
        notes=notes
        or "Back-filled from pre-T85 feature registry",
    )
    _append_record(project_root, record)
    return record


__all__ = [
    "FEATURE_STATES_FILENAME",
    "FeatureState",
    "IllegalTransitionError",
    "LEGAL_TRANSITIONS",
    "TransitionRecord",
    "all_transitions",
    "back_fill_state",
    "get_state",
    "list_features_in_state",
    "transition",
    "transitions_for",
]
