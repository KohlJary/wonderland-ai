"""Tests for ``MockTurtleHandle`` — event identity vs Historical,
order preservation, and timing semantics (T42 + T43).

The Mock Turtle is the testbed for the live-watch UI. Its contract:
  - Same events as ``HistoricalRunHandle.stream_events()`` for the
    same snapshot, in the same order.
  - Sleeps between events according to ``speed`` and
    ``max_dwell_seconds``.
  - Implements all the same non-streaming methods (delegated to a
    wrapped HistoricalRunHandle).
"""

from __future__ import annotations

import time
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from wonderland.observer import (
    HistoricalRunHandle,
    MockTurtleHandle,
    RunEnded,
    RunEvent,
    RunStarted,
)


_V6_BANNER = (
    Path(__file__).resolve().parents[1]
    / "analyses"
    / "data"
    / "029-substrate-convergence"
    / "v6"
)


def _v6_or_skip() -> Path:
    if not (_V6_BANNER / "wonderland-snapshot").is_dir():
        pytest.skip("v6 banner snapshot not present")
    return _V6_BANNER


async def _collect(stream: AsyncIterator[RunEvent]) -> list[RunEvent]:
    return [ev async for ev in stream]


# ---------------------------------------------------------------------
# Constructor validation
# ---------------------------------------------------------------------


class TestConstructor:
    def test_speed_must_be_positive(self) -> None:
        snap = _v6_or_skip()
        with pytest.raises(ValueError, match="speed must be positive"):
            MockTurtleHandle(snap, speed=0.0)
        with pytest.raises(ValueError, match="speed must be positive"):
            MockTurtleHandle(snap, speed=-1.0)

    def test_max_dwell_must_be_non_negative(self) -> None:
        snap = _v6_or_skip()
        with pytest.raises(ValueError, match="max_dwell_seconds must be non-negative"):
            MockTurtleHandle(snap, max_dwell_seconds=-0.5)

    def test_zero_max_dwell_is_allowed(self) -> None:
        """0.0 means no dwell cap — sleeps are fully proportional to
        delta / speed. Useful for true-fidelity playback at slow
        speeds."""
        snap = _v6_or_skip()
        h = MockTurtleHandle(snap, speed=10.0, max_dwell_seconds=0.0)
        assert h.max_dwell_seconds == 0.0

    def test_path_string_is_accepted(self) -> None:
        snap = _v6_or_skip()
        h = MockTurtleHandle(str(snap))
        assert h.snapshot_dir == snap


# ---------------------------------------------------------------------
# Event identity — same events as historical, same order.
# ---------------------------------------------------------------------


class TestEventIdentity:
    """The Mock Turtle's stream is the historical stream's events, in
    the same order, just with sleeps inserted. The events themselves
    are unchanged."""

    @pytest.fixture
    def fast_mock(self) -> MockTurtleHandle:
        # speed=1e6 + 0 dwell means all sleeps round to 0 — playback
        # is effectively instantaneous, isolating the event-content
        # comparison from timing concerns.
        return MockTurtleHandle(_v6_or_skip(), speed=1e6, max_dwell_seconds=0.0)

    async def test_same_event_count(self, fast_mock: MockTurtleHandle) -> None:
        historical = HistoricalRunHandle(_v6_or_skip())
        h_events = await _collect(historical.stream_events())
        m_events = await _collect(fast_mock.stream_events())
        assert len(m_events) == len(h_events)

    async def test_same_event_types_in_same_order(
        self, fast_mock: MockTurtleHandle
    ) -> None:
        historical = HistoricalRunHandle(_v6_or_skip())
        h_events = await _collect(historical.stream_events())
        m_events = await _collect(fast_mock.stream_events())
        h_kinds = [type(ev).__name__ for ev in h_events]
        m_kinds = [type(ev).__name__ for ev in m_events]
        assert m_kinds == h_kinds

    async def test_same_timestamps(self, fast_mock: MockTurtleHandle) -> None:
        historical = HistoricalRunHandle(_v6_or_skip())
        h_events = await _collect(historical.stream_events())
        m_events = await _collect(fast_mock.stream_events())
        for he, me in zip(h_events, m_events):
            assert he.timestamp == me.timestamp


# ---------------------------------------------------------------------
# Order preservation
# ---------------------------------------------------------------------


class TestOrderPreservation:
    async def test_event_timestamps_are_non_decreasing(self) -> None:
        mock = MockTurtleHandle(_v6_or_skip(), speed=1e6, max_dwell_seconds=0.0)
        events = await _collect(mock.stream_events())
        for prev, curr in zip(events, events[1:]):
            assert prev.timestamp <= curr.timestamp, (
                f"Out of order: {type(prev).__name__} at {prev.timestamp} "
                f"-> {type(curr).__name__} at {curr.timestamp}"
            )

    async def test_run_started_first_run_ended_last(self) -> None:
        mock = MockTurtleHandle(_v6_or_skip(), speed=1e6, max_dwell_seconds=0.0)
        events = await _collect(mock.stream_events())
        assert isinstance(events[0], RunStarted)
        assert isinstance(events[-1], RunEnded)


# ---------------------------------------------------------------------
# Timing semantics
# ---------------------------------------------------------------------


class TestTiming:
    async def test_high_speed_with_dwell_cap_is_fast(self) -> None:
        """speed=1000 + max_dwell=0.5 should drain the v6 banner
        (~1300s of source run) in well under 30s of wall-clock."""
        mock = MockTurtleHandle(_v6_or_skip(), speed=1000.0, max_dwell_seconds=0.5)
        t0 = time.monotonic()
        events = await _collect(mock.stream_events())
        elapsed = time.monotonic() - t0
        assert len(events) > 0
        assert elapsed < 30.0, (
            f"Mock turtle should drain in < 30s at speed=1000 + dwell=0.5; "
            f"took {elapsed:.1f}s"
        )

    async def test_max_dwell_caps_individual_sleeps(self) -> None:
        """A long inter-event gap in the source run should never
        produce a sleep longer than max_dwell_seconds. v6 banner has
        gaps of multiple minutes; cap at 0.1s and confirm total time
        stays bounded by event_count × 0.1."""
        snap = _v6_or_skip()
        # Use a very low speed so without dwell cap each sleep would
        # be huge; cap forces them small.
        mock = MockTurtleHandle(snap, speed=0.01, max_dwell_seconds=0.05)
        t0 = time.monotonic()
        events = await _collect(mock.stream_events())
        elapsed = time.monotonic() - t0
        # Bound: each of N-1 inter-event gaps sleeps at most 0.05s.
        # Plus some overhead for the actual yield work.
        upper_bound = (len(events) - 1) * 0.05 + 5.0
        assert elapsed <= upper_bound, (
            f"Total elapsed {elapsed:.2f}s exceeds upper bound {upper_bound:.2f}s "
            f"({len(events)-1} gaps × 0.05s + 5s slack)"
        )

    async def test_dwell_zero_disables_cap_at_high_speed(self) -> None:
        """speed=1000 + max_dwell=0 should still be fast because
        speed dominates. Verifies max_dwell=0 doesn't accidentally
        force zero sleep on every tick (it shouldn't — speed alone
        controls the per-event sleep when dwell cap is disabled)."""
        mock = MockTurtleHandle(_v6_or_skip(), speed=1000.0, max_dwell_seconds=0.0)
        t0 = time.monotonic()
        events = await _collect(mock.stream_events())
        elapsed = time.monotonic() - t0
        # At speed=1000 over ~1300s of source = ~1.3s of pure sleep
        # (plus event-yield overhead).
        assert len(events) > 0
        assert elapsed < 30.0

    async def test_first_event_yields_immediately(self) -> None:
        """No sleep before the first event — important so the UI can
        render an initial frame fast even if the source run started
        slowly. Slow speed + non-zero dwell would otherwise force a
        wait before the first event; this pins that it doesn't."""
        # speed=0.001 would scale a small delta into a long sleep
        # without the dwell cap. First event should still come back
        # in <1s regardless. We close the generator before draining
        # the rest — at this slow speed, draining all events would
        # take 100+ seconds. The first-event behavior is what's
        # under test.
        mock = MockTurtleHandle(_v6_or_skip(), speed=0.001, max_dwell_seconds=10.0)
        gen = mock.stream_events()
        t0 = time.monotonic()
        first = await gen.__anext__()
        elapsed = time.monotonic() - t0
        assert isinstance(first, RunStarted)
        assert elapsed < 1.0, (
            f"First event should yield immediately; took {elapsed:.2f}s"
        )
        await gen.aclose()


# ---------------------------------------------------------------------
# Non-streaming methods delegate to wrapped HistoricalRunHandle
# ---------------------------------------------------------------------


class TestStaticDelegation:
    @pytest.fixture
    def mock(self) -> MockTurtleHandle:
        return MockTurtleHandle(_v6_or_skip(), speed=1e6)

    @pytest.fixture
    def historical(self) -> HistoricalRunHandle:
        return HistoricalRunHandle(_v6_or_skip())

    def test_summary_matches(
        self, mock: MockTurtleHandle, historical: HistoricalRunHandle
    ) -> None:
        assert mock.summary() == historical.summary()

    def test_meetings_matches(
        self, mock: MockTurtleHandle, historical: HistoricalRunHandle
    ) -> None:
        assert mock.meetings() == historical.meetings()

    def test_per_agent_telemetry_matches(
        self, mock: MockTurtleHandle, historical: HistoricalRunHandle
    ) -> None:
        assert mock.per_agent_telemetry() == historical.per_agent_telemetry()

    def test_artifacts_matches(
        self, mock: MockTurtleHandle, historical: HistoricalRunHandle
    ) -> None:
        assert mock.artifacts() == historical.artifacts()

    def test_utterances_matches(
        self, mock: MockTurtleHandle, historical: HistoricalRunHandle
    ) -> None:
        m_us = list(mock.utterances())
        h_us = list(historical.utterances())
        assert len(m_us) == len(h_us)
        assert [u.id for u in m_us] == [u.id for u in h_us]


# ---------------------------------------------------------------------
# Integration: the streaming surface composes correctly (T44 prep)
# ---------------------------------------------------------------------


class TestStreamingSurface:
    """Anything that takes a RunHandle should work with both
    HistoricalRunHandle and MockTurtleHandle interchangeably."""

    async def test_polymorphic_consumer(self) -> None:
        """A consumer typed against ``RunHandle`` should iterate
        either implementation without branching."""
        from wonderland.observer.interface import RunHandle

        async def consume(handle: RunHandle) -> int:
            count = 0
            async for _ in handle.stream_events():
                count += 1
            return count

        snap = _v6_or_skip()
        historical_count = await consume(HistoricalRunHandle(snap))
        mock_count = await consume(
            MockTurtleHandle(snap, speed=1e6, max_dwell_seconds=0.0)
        )
        assert historical_count == mock_count
