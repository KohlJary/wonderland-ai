"""Streaming run events — the payload type ``RunHandle.stream_events()`` yields.

A ``RunEvent`` is one observation about a run, timestamped to when it
occurred. The base ``RunEvent`` class is abstract; concrete events
land as frozen dataclasses (``RunStarted``, ``MeetingStarted``,
``UtteranceEmitted``, ``ArtifactShipped``, ``AgentTelemetryDelta``,
``MeetingEnded``, ``RunEnded``).

Consumers iterate via:

    async for event in handle.stream_events():
        match event:
            case UtteranceEmitted(utterance=u):
                print(f"{u.speaker.name}: {u.content.body}")
            case MeetingStarted(meeting=m, iteration_label=label):
                print(f"Opening {m.label} ({label or m.name})")
            case ...

The streaming surface is what the live-watch UI subscribes to. The
inspector's existing non-streaming methods (``summary()``,
``meetings()``, ``utterances()``, ``artifacts()``) still exist and
remain authoritative for replay-time analysis — streaming is for the
"events as they arrive" UX, not a replacement for inspection.

Same shape used by:
  - ``HistoricalRunHandle.stream_events()`` — yields everything in
    one pass with no sleeping (the snapshot is finished; consumer
    just wants the chronology).
  - ``MockTurtleHandle.stream_events()`` — yields with compressed-
    time sleeping so a live-watch UI can be tested against real
    captured runs without API spend.
  - ``LiveRunHandle.stream_events()`` (P8.5) — subscribes to a
    running ``Runner`` and emits events as they happen.

UI code that subscribes here doesn't know which source it's getting,
which is the point.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Union

from wonderland.utterance import Utterance

from wonderland.observer.interface import (
    AgentTelemetry,
    RunArtifact,
    RunMeeting,
    RunSummary,
)


@dataclass(frozen=True)
class RunStarted:
    """Emitted once at the start of the stream — carries run-level
    metadata so consumers know what they're watching before any
    meeting events arrive.
    """

    timestamp: datetime
    summary: RunSummary


@dataclass(frozen=True)
class MeetingStarted:
    """A meeting or per_item iteration just opened.

    For non-iteration meetings, the iteration_* fields are None. For
    per_item iterations, they carry the index / total / human label
    (e.g., the feature title) so the UI can render
    ``M4 — The Mad Tea Party (iteration 2/5: Break Timer)``.
    """

    timestamp: datetime
    meeting: RunMeeting
    thread_id: str
    iteration_index: int | None = None
    iteration_total: int | None = None
    iteration_label: str | None = None


@dataclass(frozen=True)
class UtteranceEmitted:
    """An agent published a turn on the bus."""

    timestamp: datetime
    utterance: Utterance


@dataclass(frozen=True)
class ArtifactShipped:
    """A structured artifact (story, feature, contract_note, ticket,
    test_scenario, implementation, adr, review, ruling) landed on
    disk. Emitted alongside the carrying utterance — consumers that
    only want disk artifacts can filter to ArtifactShipped events;
    consumers that want the full bus context should still consume
    UtteranceEmitted and read .content.artifacts.
    """

    timestamp: datetime
    artifact: RunArtifact


@dataclass(frozen=True)
class AgentTelemetryDelta:
    """Periodic update on an agent's accumulated calls + cost.

    Doesn't replace utterance-level accounting; it's the running
    rollup the live-watch screen renders as a per-agent ticker. For
    historical replay, may emit once per agent at the end of the run
    rather than streaming continuously.
    """

    timestamp: datetime
    telemetry: AgentTelemetry


@dataclass(frozen=True)
class MeetingEnded:
    """A meeting (or per_item iteration) just closed. ``outcome`` is
    one of COMPLETE / MEETING_BUDGET / GLOBAL_BUDGET / TIMEOUT /
    ABORTED.

    Carries the same iteration_* fields as MeetingStarted so the UI
    can pair start/end events for per_item iterations.
    """

    timestamp: datetime
    meeting: RunMeeting
    thread_id: str
    outcome: str
    elapsed_seconds: float
    calls_delta: int
    cost_delta: float
    artifact_kinds: dict[str, int]
    iteration_index: int | None = None
    iteration_total: int | None = None
    iteration_label: str | None = None


@dataclass(frozen=True)
class RunEnded:
    """Emitted once when the stream is exhausted. Carries the final
    summary so consumers can render the closing totals without
    having to call summary() separately.

    The ``outcome`` mirrors RunSummary.outcome — COMPLETE if the run
    settled cleanly, otherwise the terminal failure mode the run
    exited via (GLOBAL_BUDGET / TIMEOUT / ABORTED).
    """

    timestamp: datetime
    summary: RunSummary


# Phase + priority + rotation events (P9 / analysis 033). These
# events surface meeting structure that the engine emits when a
# meeting declares phases. Older snapshots predate these events and
# simply don't include them — historical replay works either way.


@dataclass(frozen=True)
class PhaseStarted:
    """A new phase opened inside a meeting.

    Phases are workflow-declared sub-units of a meeting (e.g. M4's
    ``red → green → refactor``). Each phase has its own priority
    rotation and rotation budget. The engine emits ``PhaseStarted``
    when entering the phase, before any priority window opens.
    """

    timestamp: datetime
    meeting_thread_id: str
    phase_name: str
    max_rotations: int
    cast: tuple[str, ...]
    """Priority order for this phase. Tuple, not list, because the
    order is fixed for the duration of the phase."""
    exit_condition_artifact: str | None = None


@dataclass(frozen=True)
class PhaseEnded:
    """A phase closed.

    ``reason`` is one of: ``"succession"`` (every cast member passed
    in succession — natural end), ``"exhausted"`` (rotation budget
    spent), ``"exit_condition"`` (the workflow's exit-condition
    artifact shipped), or ``"aborted"`` (run-level abort). The
    per-agent count maps are the §VIII observability primitive — T60
    detectors read these to flag sprawl (never-passes) and
    withdrawal (always-passes-after-first) shapes.
    """

    timestamp: datetime
    meeting_thread_id: str
    phase_name: str
    reason: str
    rotations_used: int
    total_windows: int
    passes_per_agent: dict[str, int]
    acts_per_agent: dict[str, int]


@dataclass(frozen=True)
class PriorityWindowOpened:
    """Priority just passed to ``agent_id``. They will either act or
    pass before the window closes.

    ``window_index_in_phase`` is monotonic across the entire phase
    (0, 1, 2, ...) so consumers can render windows linearly.
    ``rotation_index`` is which rotation this window belongs to.
    """

    timestamp: datetime
    meeting_thread_id: str
    phase_name: str
    agent_id: str
    rotation_index: int
    window_index_in_phase: int


@dataclass(frozen=True)
class AgentActed:
    """An agent used their priority window to emit an utterance.

    Paired with ``UtteranceEmitted`` for the actual utterance
    payload — consumers that only care about phase structure can
    subscribe to ``AgentActed`` alone; consumers that need the
    utterance content read both. ``utterance_id`` cross-references
    them.
    """

    timestamp: datetime
    meeting_thread_id: str
    phase_name: str
    agent_id: str
    rotation_index: int
    utterance_id: str


@dataclass(frozen=True)
class AgentPassed:
    """An agent declined their priority window.

    Pass is a first-class action — distinct from "wasn't asked to
    speak." Counting passes per agent is what makes Cat withdrawal
    observable from outside the agent (analysis 033).
    """

    timestamp: datetime
    meeting_thread_id: str
    phase_name: str
    agent_id: str
    rotation_index: int
    reason: str | None = None
    """Optional human-readable explanation. Engine may leave None;
    agents that volunteer a reason via tool call can populate it."""


@dataclass(frozen=True)
class RotationCompleted:
    """A full rotation around the cast just finished.

    Boundary event — payload is intentionally minimal because the
    interesting per-rotation accounting can be derived from the
    AgentActed / AgentPassed stream. Useful as a render hint for the
    TUI ("draw a horizontal line between rotations").
    """

    timestamp: datetime
    meeting_thread_id: str
    phase_name: str
    rotation_index: int


# Sealed union type alias. New event kinds added to this module
# should also extend this union — that's the canonical surface
# RunHandle.stream_events() yields, and consumers' match/isinstance
# checks read against it.
RunEvent = Union[
    RunStarted,
    MeetingStarted,
    UtteranceEmitted,
    ArtifactShipped,
    AgentTelemetryDelta,
    MeetingEnded,
    RunEnded,
    PhaseStarted,
    PhaseEnded,
    PriorityWindowOpened,
    AgentActed,
    AgentPassed,
    RotationCompleted,
]


__all__ = [
    "AgentActed",
    "AgentPassed",
    "AgentTelemetryDelta",
    "ArtifactShipped",
    "MeetingEnded",
    "MeetingStarted",
    "PhaseEnded",
    "PhaseStarted",
    "PriorityWindowOpened",
    "RotationCompleted",
    "RunEnded",
    "RunEvent",
    "RunStarted",
    "UtteranceEmitted",
]
