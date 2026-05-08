"""Tests for the streaming event types defined in
``wonderland.observer.events`` (T40).

These cover the contract:
  - All event types are constructable as frozen dataclasses.
  - The ``RunEvent`` union resolves to the expected concrete types.
  - The public ``wonderland.observer`` package re-exports them.
  - The abstract ``stream_events`` method is present on
    ``HistoricalRunHandle`` (stubbed for T40; T41 implements it).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import get_args

import pytest

from wonderland.observer import (
    AgentTelemetry,
    AgentTelemetryDelta,
    ArtifactShipped,
    HistoricalRunHandle,
    MeetingEnded,
    MeetingStarted,
    RunArtifact,
    RunEnded,
    RunEvent,
    RunHandle,
    RunMeeting,
    RunStarted,
    RunSummary,
    UtteranceEmitted,
)
from wonderland.utterance import (
    AgentIdentity,
    SpeechAct,
    Utterance,
    UtteranceContent,
)


_NOW = datetime(2026, 5, 8, 12, 0, 0, tzinfo=timezone.utc)


def _summary() -> RunSummary:
    return RunSummary(
        run_id="test-run",
        workflow_name="tdd-serial",
        directive="Build a thing.",
        project_root=Path("/tmp/test-project"),
        started_at=_NOW,
        ended_at=None,
        total_cost=0.0,
        total_calls=0,
        outcome=None,
    )


def _meeting(label: str = "M1") -> RunMeeting:
    return RunMeeting(
        id="scoping",
        label=label,
        name="The Caucus Race",
        started_at=_NOW,
        ended_at=None,
        outcome=None,
        elapsed_seconds=None,
        calls=0,
        cost=0.0,
    )


def _utterance() -> Utterance:
    return Utterance(
        thread_id="scoping",
        speaker=AgentIdentity(name="alice", constitution_version="1"),
        addressed_to="caucus",
        speech_act=SpeechAct.PROPOSAL,
        content=UtteranceContent(body="hello", artifacts=[]),
    )


# ---------------------------------------------------------------------
# Event-type construction
# ---------------------------------------------------------------------


class TestEventConstruction:
    def test_run_started(self) -> None:
        ev = RunStarted(timestamp=_NOW, summary=_summary())
        assert ev.timestamp == _NOW
        assert ev.summary.workflow_name == "tdd-serial"

    def test_meeting_started_without_iteration(self) -> None:
        ev = MeetingStarted(
            timestamp=_NOW,
            meeting=_meeting(),
            thread_id="scoping",
        )
        assert ev.iteration_index is None
        assert ev.iteration_total is None
        assert ev.iteration_label is None

    def test_meeting_started_with_iteration(self) -> None:
        ev = MeetingStarted(
            timestamp=_NOW,
            meeting=_meeting("M4"),
            thread_id="test-scenarios-focus-session",
            iteration_index=1,
            iteration_total=3,
            iteration_label="Focus session",
        )
        assert ev.iteration_index == 1
        assert ev.iteration_total == 3
        assert ev.iteration_label == "Focus session"

    def test_utterance_emitted(self) -> None:
        ev = UtteranceEmitted(timestamp=_NOW, utterance=_utterance())
        assert ev.utterance.speaker.name == "alice"

    def test_artifact_shipped(self) -> None:
        a = RunArtifact(
            kind="story",
            path=Path("/tmp/.wonderland/stories/story-001.md"),
            title="A focus session",
            created_at=_NOW,
        )
        ev = ArtifactShipped(timestamp=_NOW, artifact=a)
        assert ev.artifact.kind == "story"

    def test_agent_telemetry_delta(self) -> None:
        ev = AgentTelemetryDelta(
            timestamp=_NOW,
            telemetry=AgentTelemetry(name="alice", calls=3, cost=0.05),
        )
        assert ev.telemetry.name == "alice"

    def test_meeting_ended(self) -> None:
        ev = MeetingEnded(
            timestamp=_NOW,
            meeting=_meeting(),
            thread_id="scoping",
            outcome="COMPLETE",
            elapsed_seconds=20.4,
            calls_delta=2,
            cost_delta=0.0328,
            artifact_kinds={"story": 6, "adr": 1},
        )
        assert ev.outcome == "COMPLETE"
        assert ev.artifact_kinds["story"] == 6

    def test_run_ended(self) -> None:
        s = _summary()
        ev = RunEnded(timestamp=_NOW, summary=s)
        assert ev.summary is s


# ---------------------------------------------------------------------
# Frozen-ness
# ---------------------------------------------------------------------


class TestFrozen:
    def test_run_started_is_frozen(self) -> None:
        ev = RunStarted(timestamp=_NOW, summary=_summary())
        with pytest.raises(Exception):  # FrozenInstanceError on dataclass.replace would also be fine
            ev.timestamp = datetime.now(tz=timezone.utc)  # type: ignore[misc]

    def test_meeting_started_is_frozen(self) -> None:
        ev = MeetingStarted(
            timestamp=_NOW,
            meeting=_meeting(),
            thread_id="scoping",
        )
        with pytest.raises(Exception):
            ev.thread_id = "other"  # type: ignore[misc]


# ---------------------------------------------------------------------
# RunEvent union
# ---------------------------------------------------------------------


class TestRunEventUnion:
    def test_union_includes_all_concrete_event_types(self) -> None:
        members = set(get_args(RunEvent))
        assert members == {
            RunStarted,
            MeetingStarted,
            UtteranceEmitted,
            ArtifactShipped,
            AgentTelemetryDelta,
            MeetingEnded,
            RunEnded,
        }

    def test_union_members_are_frozen_dataclasses(self) -> None:
        # All event types should be frozen so callers can stash them
        # in sets, use them as dict keys (via id), and rely on no
        # post-construction mutation.
        for cls in get_args(RunEvent):
            assert getattr(cls, "__dataclass_params__").frozen, (
                f"{cls.__name__} should be frozen=True"
            )


# ---------------------------------------------------------------------
# RunHandle abstract surface
# ---------------------------------------------------------------------


class TestRunHandleAbstract:
    def test_run_handle_declares_stream_events(self) -> None:
        # RunHandle is the contract; stream_events is part of the
        # abstract surface starting in T40.
        assert hasattr(RunHandle, "stream_events")

    async def test_historical_stream_events_yields_events(self) -> None:
        """T41 implementation: yield-everything-now over the snapshot."""
        analyses_data = Path(__file__).resolve().parents[1] / "analyses" / "data"
        snapshots = list(analyses_data.rglob("run.log"))
        snapshot_dir = next(
            (p.parent for p in snapshots if (p.parent / "wonderland-snapshot").is_dir()),
            None,
        )
        if snapshot_dir is None:
            pytest.skip("no snapshot fixture available")

        handle = HistoricalRunHandle(snapshot_dir)
        events = [ev async for ev in handle.stream_events()]
        # At minimum: RunStarted + at least one MeetingStarted/Ended
        # pair + at least one UtteranceEmitted + RunEnded.
        assert any(isinstance(ev, RunStarted) for ev in events)
        assert any(isinstance(ev, RunEnded) for ev in events)
        assert any(isinstance(ev, MeetingStarted) for ev in events)
        assert any(isinstance(ev, MeetingEnded) for ev in events)
        assert any(isinstance(ev, UtteranceEmitted) for ev in events)


# ---------------------------------------------------------------------
# T41 — stream_events behavior on HistoricalRunHandle
# ---------------------------------------------------------------------


_V6_BANNER = (
    Path(__file__).resolve().parents[1]
    / "analyses"
    / "data"
    / "029-substrate-convergence"
    / "v6"
)


async def _collect_v6_events() -> list[RunEvent]:
    if not (_V6_BANNER / "wonderland-snapshot").is_dir():
        pytest.skip("v6 banner snapshot not present")
    handle = HistoricalRunHandle(_V6_BANNER)
    return [ev async for ev in handle.stream_events()]


class TestStreamEventsOrdering:
    """The stream is a chronologically-ordered narrative of the run."""

    async def test_run_started_first_run_ended_last(self) -> None:
        events = await _collect_v6_events()
        assert isinstance(events[0], RunStarted)
        assert isinstance(events[-1], RunEnded)

    async def test_meeting_starts_and_ends_are_balanced(self) -> None:
        events = await _collect_v6_events()
        starts = sum(1 for ev in events if isinstance(ev, MeetingStarted))
        ends = sum(1 for ev in events if isinstance(ev, MeetingEnded))
        # Every MeetingStarted should be matched by exactly one
        # MeetingEnded (the stream pairs them).
        assert starts == ends
        assert starts > 0

    async def test_meeting_starts_are_ordered_by_timestamp(self) -> None:
        events = await _collect_v6_events()
        meeting_starts = [
            ev.timestamp for ev in events if isinstance(ev, MeetingStarted)
        ]
        assert meeting_starts == sorted(meeting_starts)

    async def test_utterances_appear_between_meeting_bookends(self) -> None:
        """No UtteranceEmitted should fire before the first MeetingStarted
        or after the last MeetingEnded."""
        events = await _collect_v6_events()
        first_start_idx = next(
            i for i, ev in enumerate(events) if isinstance(ev, MeetingStarted)
        )
        last_end_idx = max(
            i for i, ev in enumerate(events) if isinstance(ev, MeetingEnded)
        )
        for i, ev in enumerate(events):
            if isinstance(ev, UtteranceEmitted):
                assert first_start_idx <= i <= last_end_idx, (
                    f"utterance at index {i} outside meeting bookends "
                    f"[{first_start_idx}, {last_end_idx}]"
                )


class TestStreamEventsMeetings:
    """Meeting metadata in the stream."""

    async def test_v6_yields_seven_meetings(self) -> None:
        """v6 banner ran tdd workflow, 7 meetings: M1, M2, M2.5, M3,
        M4, M5, M6 (parallel-fan-out, no per_item iterations)."""
        events = await _collect_v6_events()
        starts = [ev for ev in events if isinstance(ev, MeetingStarted)]
        assert len(starts) == 7

    async def test_meeting_thread_ids_match_meetings_method(self) -> None:
        """The stream's MeetingStarted thread_ids should match the
        IDs returned by meetings() (modulo per_item iteration handling
        which is filed as a separate fix)."""
        if not (_V6_BANNER / "wonderland-snapshot").is_dir():
            pytest.skip("v6 banner snapshot not present")
        handle = HistoricalRunHandle(_V6_BANNER)
        events = [ev async for ev in handle.stream_events()]
        stream_ids = [
            ev.thread_id for ev in events if isinstance(ev, MeetingStarted)
        ]
        meetings_ids = [m.id for m in handle.meetings()]
        # Stream and meetings() should agree on the thread IDs they
        # surface — for v6 (no per_item) this is one-to-one.
        assert set(stream_ids) == set(meetings_ids)


class TestStreamEventsArtifacts:
    """ArtifactShipped fires for utterance-attached artifacts that
    resolve to an on-disk RunArtifact."""

    async def test_artifact_shipped_count_matches_resolvable_attachments(
        self,
    ) -> None:
        if not (_V6_BANNER / "wonderland-snapshot").is_dir():
            pytest.skip("v6 banner snapshot not present")
        handle = HistoricalRunHandle(_V6_BANNER)
        # Compute expected count: walk utterances, for each attached
        # artifact, check whether it resolves to a disk RunArtifact.
        artifacts_by_basename = {a.path.name: a for a in handle.artifacts()}
        expected = 0
        for u in handle.utterances():
            for a in u.content.artifacts or []:
                payload = a.payload if isinstance(a.payload, dict) else {}
                raw_path = payload.get("path")
                if raw_path and Path(raw_path).name in artifacts_by_basename:
                    expected += 1
        events = [ev async for ev in handle.stream_events()]
        actual = sum(1 for ev in events if isinstance(ev, ArtifactShipped))
        assert actual == expected
        # And it's non-zero — v6 banner shipped artifacts.
        assert actual > 0

    async def test_artifact_shipped_immediately_follows_carrying_utterance(
        self,
    ) -> None:
        """An ArtifactShipped event should never appear at the start of
        the stream; it always follows the UtteranceEmitted that carried
        it. So index(ArtifactShipped) > 0 and the most recent
        UtteranceEmitted is at the same timestamp."""
        events = await _collect_v6_events()
        most_recent_utterance_ts = None
        for ev in events:
            if isinstance(ev, UtteranceEmitted):
                most_recent_utterance_ts = ev.timestamp
            elif isinstance(ev, ArtifactShipped):
                assert most_recent_utterance_ts == ev.timestamp


class TestStreamEventsTelemetry:
    async def test_one_telemetry_delta_per_agent(self) -> None:
        events = await _collect_v6_events()
        deltas = [ev for ev in events if isinstance(ev, AgentTelemetryDelta)]
        names = [d.telemetry.name for d in deltas]
        # No duplicates — one final delta per agent.
        assert len(names) == len(set(names))
        # Non-empty — v6 had multiple agents working.
        assert len(deltas) > 0


class TestStreamEventsPerItemSnapshot:
    """v3 snapshot was tdd-serial with per_item iterations — the
    stream should reflect each iteration thread as its own meeting
    even though meetings() currently dedups by label (filed as
    7a5ff815)."""

    async def test_v3_yields_more_than_seven_meetings(self) -> None:
        v3 = (
            Path(__file__).resolve().parents[1]
            / "analyses"
            / "data"
            / "032-tdd-serial-v3"
        )
        if not (v3 / "wonderland-snapshot").is_dir():
            pytest.skip("v3 snapshot not present")
        handle = HistoricalRunHandle(v3)
        events = [ev async for ev in handle.stream_events()]
        starts = [ev for ev in events if isinstance(ev, MeetingStarted)]
        # v3 had M1, M2, M2.5, M3, M4×3, M5×3, M6 = 11 distinct
        # meeting threads (each per_item iteration is its own thread
        # in the SQLite). The stream detects transitions via thread_id
        # changes so should surface all 11.
        assert len(starts) == 11

    async def test_v3_per_item_iterations_have_distinct_thread_ids(
        self,
    ) -> None:
        v3 = (
            Path(__file__).resolve().parents[1]
            / "analyses"
            / "data"
            / "032-tdd-serial-v3"
        )
        if not (v3 / "wonderland-snapshot").is_dir():
            pytest.skip("v3 snapshot not present")
        handle = HistoricalRunHandle(v3)
        events = [ev async for ev in handle.stream_events()]
        starts = [ev for ev in events if isinstance(ev, MeetingStarted)]
        thread_ids = [s.thread_id for s in starts]
        # M4 iterations: test-scenarios-{slug} × 3 distinct slugs
        m4_iterations = [t for t in thread_ids if t.startswith("test-scenarios")]
        assert len(m4_iterations) == 3
        assert len(set(m4_iterations)) == 3
        # M5 iterations: implementation-{slug} × 3 distinct slugs
        m5_iterations = [t for t in thread_ids if t.startswith("implementation")]
        assert len(m5_iterations) == 3
        assert len(set(m5_iterations)) == 3
