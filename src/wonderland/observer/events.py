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
]


__all__ = [
    "AgentTelemetryDelta",
    "ArtifactShipped",
    "MeetingEnded",
    "MeetingStarted",
    "RunEnded",
    "RunEvent",
    "RunStarted",
    "UtteranceEmitted",
]
