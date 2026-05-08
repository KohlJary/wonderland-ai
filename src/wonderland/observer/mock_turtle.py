"""``MockTurtleHandle`` — replay a snapshot's event stream in
compressed clock time.

The Mock Turtle is the testbed for the live-watch UI: it speaks the
same ``RunHandle`` protocol as ``HistoricalRunHandle`` and (eventually)
``LiveRunHandle``, but inserts ``asyncio.sleep`` between events
based on their captured timestamp deltas, scaled by a configurable
speed factor. The result is a snapshot that "plays back" at clock
time you can iterate against, without any API spend.

Why a Mock Turtle:

  P8.4's live-watch screen needs an event stream that arrives over
  time so we can iterate on layout, navigation, cost-tickers, mid-
  meeting drill-downs, abort flows, and a dozen other UX questions
  that only surface when events aren't already in hand. Doing that
  iteration against a real run costs ~$3-5 per pass and ~25 minutes
  wall-clock. Doing it against the Mock Turtle costs nothing and
  takes seconds.

  The literary fit is on the nose for this character: he is *literally
  not-a-turtle* (mock turtle soup = veal pretending), and his chapter
  in the source material is melancholy retelling of his "education."
  An agent that re-narrates a captured run in compressed time so you
  can see how it went without paying for it again is exactly his vibe.

Usage:

    from wonderland.observer import MockTurtleHandle

    handle = MockTurtleHandle(snapshot_dir, speed=5.0, max_dwell_seconds=2.0)

    async for event in handle.stream_events():
        # Renders at 5x clock speed; quiet periods longer than 2s
        # of wall-clock collapse to 2s rather than dragging on.
        ...

The non-streaming methods (summary, meetings, utterances, artifacts,
per_agent_telemetry) just delegate to the wrapped HistoricalRunHandle
— they're snapshot-static and there's no value in re-implementing them.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterator
from datetime import datetime
from pathlib import Path

from wonderland.observer.events import RunEvent
from wonderland.observer.historical import HistoricalRunHandle
from wonderland.observer.interface import (
    AgentTelemetry,
    RunArtifact,
    RunHandle,
    RunMeeting,
    RunSummary,
)
from wonderland.utterance import Utterance


class MockTurtleHandle(RunHandle):
    """Replays a captured snapshot at compressed clock speed.

    Parameters
    ----------
    snapshot_dir:
        Path to the snapshot (same shape as ``HistoricalRunHandle``).
    speed:
        Clock-speed multiplier. ``1.0`` plays at original speed;
        ``5.0`` is 5× faster (wall-clock seconds per event-time
        second); ``float('inf')`` yields with no sleep at all (same
        as ``HistoricalRunHandle.stream_events()`` directly). Must
        be positive.
    max_dwell_seconds:
        Cap on the wall-clock sleep between any two events. Quiet
        periods longer than this collapse to ``max_dwell_seconds``
        regardless of how long they took in the source run. Default
        is 2.0s — long enough to feel like real waiting, short enough
        that M5's 5-minute deliberation-and-write loop doesn't stall
        a demo. Set to ``0.0`` to disable the cap (faithful timing
        scaled by speed).

    Notes
    -----
    The first event always fires immediately (no sleep before it).
    Subsequent events sleep ``min(delta / speed, max_dwell_seconds)``
    where ``delta`` is the source-time difference in seconds.
    """

    def __init__(
        self,
        snapshot_dir: Path | str,
        *,
        speed: float = 5.0,
        max_dwell_seconds: float = 2.0,
    ) -> None:
        if speed <= 0:
            raise ValueError(f"speed must be positive, got {speed}")
        if max_dwell_seconds < 0:
            raise ValueError(
                f"max_dwell_seconds must be non-negative, got {max_dwell_seconds}"
            )
        self.snapshot_dir = Path(snapshot_dir)
        self.speed = speed
        self.max_dwell_seconds = max_dwell_seconds
        self._historical = HistoricalRunHandle(self.snapshot_dir)

    # ------------------------------------------------------------------ #
    # Static methods — delegate to the wrapped handle.
    # ------------------------------------------------------------------ #

    def summary(self) -> RunSummary:
        return self._historical.summary()

    def meetings(self) -> list[RunMeeting]:
        return self._historical.meetings()

    def utterances(self, *, thread_id: str | None = None) -> Iterator[Utterance]:
        return self._historical.utterances(thread_id=thread_id)

    def per_agent_telemetry(self) -> list[AgentTelemetry]:
        return self._historical.per_agent_telemetry()

    def artifacts(self, *, kind: str | None = None) -> list[RunArtifact]:
        return self._historical.artifacts(kind=kind)

    # ------------------------------------------------------------------ #
    # The streaming method — the whole point of this class.
    # ------------------------------------------------------------------ #

    async def stream_events(self) -> AsyncIterator[RunEvent]:
        """Replay the wrapped snapshot's events with compressed-time
        sleeping between them.

        Algorithm:
          - First event: yield immediately.
          - Subsequent events: compute delta = event.timestamp -
            prev_event.timestamp (seconds). Sleep
            ``min(delta / speed, max_dwell_seconds)``. Then yield.

        The cap means a 6-minute deliberation pause (e.g. M5's
        write_file → run_tests → fix → repeat cycles) at speed=5x
        would otherwise be 72s of wall-clock; with the default
        max_dwell_seconds=2.0 it collapses to 2s.

        Negative deltas (events out of order in the source stream)
        are clamped to 0 — yield immediately.
        """
        prev_ts: datetime | None = None
        async for event in self._historical.stream_events():
            event_ts = event.timestamp  # type: ignore[attr-defined]
            if prev_ts is not None:
                delta_s = (event_ts - prev_ts).total_seconds()
                wait = min(max(delta_s, 0.0) / self.speed, self.max_dwell_seconds)
                if wait > 0:
                    await asyncio.sleep(wait)
            yield event
            prev_ts = event_ts


__all__ = ["MockTurtleHandle"]
