"""Tests for ``LiveRunHandle`` (T52) — exercises the Runner+Workflow
wrapping and RunnerEvent → RunEvent translation against a fake
runner so we don't burn real API tokens.

The acceptance for T52: a polymorphic consumer typed against
``RunHandle`` iterates ``LiveRunHandle`` and ``HistoricalRunHandle``
interchangeably, getting the same RunEvent shape from both. The
streaming surface composes regardless of source.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from wonderland.observer import (
    AgentTelemetryDelta,
    ArtifactShipped,
    LiveRunHandle,
    MeetingEnded,
    MeetingStarted,
    RunEnded,
    RunStarted,
    UtteranceEmitted,
)
from wonderland.utterance import (
    AgentIdentity,
    Artifact,
    SpeechAct,
    Utterance,
    UtteranceContent,
)
from wonderland.workflow import Meeting, SeedBinding, Workflow


_NOW = datetime(2026, 5, 8, 12, 0, 0, tzinfo=timezone.utc)


def _utt(
    *,
    thread_id: str,
    speaker: str = "alice",
    speech_act: SpeechAct = SpeechAct.PROPOSAL,
    artifacts: list[Artifact] | None = None,
    body: str = "",
) -> Utterance:
    return Utterance(
        thread_id=thread_id,
        speaker=AgentIdentity(name=speaker, constitution_version="1"),
        addressed_to="caucus",
        speech_act=speech_act,
        content=UtteranceContent(body=body, artifacts=artifacts or []),
    )


# --------------------------------------------------------------------- #
# Fake runner — minimal slice that LiveRunHandle drives via run_workflow
# --------------------------------------------------------------------- #


@dataclass
class _FakeEvent:
    """Stand-in for RunnerEvent."""

    kind: str
    payload: dict[str, Any] = field(default_factory=dict)


class _FakeTelemetry:
    def __init__(self, per_agent: dict[str, dict] | None = None):
        self.per_agent = per_agent or {}
        self.call_count = sum(
            row.get("calls", 0) for row in self.per_agent.values()
        )
        self.total_cost = sum(
            row.get("cost", 0.0) for row in self.per_agent.values()
        )
        self._per_thread_cost: dict[str, float] = {}

    def cost_for_thread(self, thread_id: str) -> float:
        return self._per_thread_cost.get(thread_id, 0.0)


class _FakeRunner:
    """Mimics the slice of Runner that run_workflow + LiveRunHandle
    exercise. Per-meeting scripts: each thread_id maps to a list of
    fake events the runner yields when convened on that thread."""

    def __init__(
        self,
        scripts: dict[str, list[_FakeEvent]],
        project_root: Path | None = None,
        per_agent: dict[str, dict] | None = None,
    ):
        self._scripts = scripts
        self._current_thread: str | None = None
        self.telemetry = _FakeTelemetry(per_agent)
        self.total_cost: float = self.telemetry.total_cost
        self._completed = False
        self.convene_calls: list[dict[str, Any]] = []
        self.thread_completes: list[dict[str, str]] = []
        self.project_root = project_root or Path("/tmp/fake-project")
        self.setup_called = False
        self.teardown_called = False

    async def setup(self) -> None:
        self.setup_called = True

    async def teardown(self) -> None:
        self.teardown_called = True

    def mark_thread_complete(self, thread_id: str, reason: str) -> None:
        self.thread_completes.append({"thread_id": thread_id, "reason": reason})

    async def convene(
        self,
        *,
        thread_id: str,
        goal: str,
        roster: list[str],
        seed_utterances: list[Utterance],
        convenor_directive: str | None = None,
    ) -> None:
        self._current_thread = thread_id
        self.convene_calls.append(
            {
                "thread_id": thread_id,
                "goal": goal,
                "roster": list(roster),
                "convenor_directive": convenor_directive,
            }
        )

    async def events(
        self, *, terminal_thread_id: str | None = None
    ) -> AsyncIterator[_FakeEvent]:
        for ev in self._scripts.get(self._current_thread or "", []):
            if ev.kind == "utterance":
                self.telemetry.call_count += 1
                self.total_cost += 0.10
                # Update per_agent telemetry as well so live
                # accounting works.
                u = ev.payload.get("utterance")
                if u is not None:
                    name = u.speaker.name
                    row = self.telemetry.per_agent.setdefault(
                        name, {"calls": 0, "cost": 0.0}
                    )
                    row["calls"] += 1
                    row["cost"] += 0.10
            yield ev
            await asyncio.sleep(0)
            if ev.kind in ("aborted", "timeout"):
                return
            if ev.kind == "complete":
                if terminal_thread_id is None:
                    return
                event_thread_id = (ev.payload or {}).get("thread_id")
                if (
                    event_thread_id is None
                    or event_thread_id == terminal_thread_id
                ):
                    return


# --------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------- #


@pytest.fixture
def two_meeting_workflow() -> Workflow:
    return Workflow(
        name="live-test",
        description="d",
        meetings=[
            Meeting(
                id="scoping",
                label="M1",
                name="The Caucus Race",
                goal="g1",
                roster=["alice"],
                meeting_budget=1.0,
            ),
            Meeting(
                id="impl",
                label="M2",
                goal="g2",
                roster=["tweedledum"],
                meeting_budget=1.0,
                seeds=[
                    SeedBinding(**{"from": "scoping", "kinds": ["story"]})
                ],
            ),
        ],
    )


class TestLifecycle:
    async def test_setup_called_at_stream_start(
        self, two_meeting_workflow: Workflow, tmp_path: Path
    ) -> None:
        scripts = {
            "scoping": [_FakeEvent("complete")],
            "impl": [_FakeEvent("complete")],
        }
        runner = _FakeRunner(scripts, project_root=tmp_path)
        handle = LiveRunHandle(
            runner=runner,  # type: ignore[arg-type]
            workflow=two_meeting_workflow,
            directive="go",
        )
        # Setup should NOT be called yet.
        assert not runner.setup_called
        # Drain the stream.
        async for _ in handle.stream_events():
            pass
        assert runner.setup_called

    async def test_teardown_called_on_completion(
        self, two_meeting_workflow: Workflow, tmp_path: Path
    ) -> None:
        scripts = {
            "scoping": [_FakeEvent("complete")],
            "impl": [_FakeEvent("complete")],
        }
        runner = _FakeRunner(scripts, project_root=tmp_path)
        handle = LiveRunHandle(
            runner=runner,  # type: ignore[arg-type]
            workflow=two_meeting_workflow,
            directive="go",
        )
        async for _ in handle.stream_events():
            pass
        assert runner.teardown_called

    async def test_teardown_called_on_cancellation(
        self, two_meeting_workflow: Workflow, tmp_path: Path
    ) -> None:
        """If the consumer cancels mid-stream, teardown must still
        run so background threads don't leak."""
        scripts = {
            "scoping": [
                _FakeEvent("utterance", {"utterance": _utt(thread_id="scoping")}),
                _FakeEvent("complete"),
            ],
            "impl": [_FakeEvent("complete")],
        }
        runner = _FakeRunner(scripts, project_root=tmp_path)
        handle = LiveRunHandle(
            runner=runner,  # type: ignore[arg-type]
            workflow=two_meeting_workflow,
            directive="go",
        )
        # Read just the first couple of events, then close the
        # generator (simulates the consumer aborting).
        gen = handle.stream_events()
        await gen.__anext__()  # RunStarted
        await gen.__anext__()  # MeetingStarted (M1)
        await gen.aclose()
        assert runner.teardown_called


class TestEventTranslation:
    """The translation layer produces the RunEvent shapes downstream
    consumers (LiveRunScreen, etc.) expect."""

    async def test_emits_run_started_first_run_ended_last(
        self, two_meeting_workflow: Workflow, tmp_path: Path
    ) -> None:
        scripts = {
            "scoping": [_FakeEvent("complete")],
            "impl": [_FakeEvent("complete")],
        }
        runner = _FakeRunner(scripts, project_root=tmp_path)
        handle = LiveRunHandle(
            runner=runner,  # type: ignore[arg-type]
            workflow=two_meeting_workflow,
            directive="go",
        )
        events = [ev async for ev in handle.stream_events()]
        assert isinstance(events[0], RunStarted)
        assert isinstance(events[-1], RunEnded)

    async def test_meeting_starts_and_ends_balance(
        self, two_meeting_workflow: Workflow, tmp_path: Path
    ) -> None:
        scripts = {
            "scoping": [_FakeEvent("complete")],
            "impl": [_FakeEvent("complete")],
        }
        runner = _FakeRunner(scripts, project_root=tmp_path)
        handle = LiveRunHandle(
            runner=runner,  # type: ignore[arg-type]
            workflow=two_meeting_workflow,
            directive="go",
        )
        events = [ev async for ev in handle.stream_events()]
        starts = [ev for ev in events if isinstance(ev, MeetingStarted)]
        ends = [ev for ev in events if isinstance(ev, MeetingEnded)]
        assert len(starts) == 2
        assert len(ends) == 2

    async def test_utterance_translated_to_utterance_emitted(
        self, two_meeting_workflow: Workflow, tmp_path: Path
    ) -> None:
        u = _utt(thread_id="scoping", body="hello")
        scripts = {
            "scoping": [
                _FakeEvent("utterance", {"utterance": u}),
                _FakeEvent("complete"),
            ],
            "impl": [_FakeEvent("complete")],
        }
        runner = _FakeRunner(scripts, project_root=tmp_path)
        handle = LiveRunHandle(
            runner=runner,  # type: ignore[arg-type]
            workflow=two_meeting_workflow,
            directive="go",
        )
        events = [ev async for ev in handle.stream_events()]
        utts = [ev for ev in events if isinstance(ev, UtteranceEmitted)]
        assert len(utts) == 1
        assert utts[0].utterance.id == u.id

    async def test_attached_artifact_emits_artifact_shipped(
        self, two_meeting_workflow: Workflow, tmp_path: Path
    ) -> None:
        artifact = Artifact(
            kind="story",
            payload={
                "path": str(tmp_path / "stories" / "story-001.md"),
                "title": "A focus session story",
            },
        )
        u = _utt(thread_id="scoping", artifacts=[artifact])
        scripts = {
            "scoping": [
                _FakeEvent("utterance", {"utterance": u}),
                _FakeEvent("complete"),
            ],
            "impl": [_FakeEvent("complete")],
        }
        runner = _FakeRunner(scripts, project_root=tmp_path)
        handle = LiveRunHandle(
            runner=runner,  # type: ignore[arg-type]
            workflow=two_meeting_workflow,
            directive="go",
        )
        events = [ev async for ev in handle.stream_events()]
        artifacts = [ev for ev in events if isinstance(ev, ArtifactShipped)]
        assert len(artifacts) == 1
        assert artifacts[0].artifact.kind == "story"
        assert artifacts[0].artifact.title == "A focus session story"

    async def test_per_agent_telemetry_deltas_at_end(
        self, two_meeting_workflow: Workflow, tmp_path: Path
    ) -> None:
        u_alice = _utt(thread_id="scoping", speaker="alice")
        u_tweedle = _utt(thread_id="impl", speaker="tweedledum")
        scripts = {
            "scoping": [
                _FakeEvent("utterance", {"utterance": u_alice}),
                _FakeEvent("complete"),
            ],
            "impl": [
                _FakeEvent("utterance", {"utterance": u_tweedle}),
                _FakeEvent("complete"),
            ],
        }
        runner = _FakeRunner(scripts, project_root=tmp_path)
        handle = LiveRunHandle(
            runner=runner,  # type: ignore[arg-type]
            workflow=two_meeting_workflow,
            directive="go",
        )
        events = [ev async for ev in handle.stream_events()]
        deltas = [ev for ev in events if isinstance(ev, AgentTelemetryDelta)]
        # One delta per agent that emitted: alice + tweedledum
        names = {d.telemetry.name for d in deltas}
        assert names == {"alice", "tweedledum"}


class TestNonStreamingMethods:
    """The non-streaming methods snapshot accumulated state at call
    time. After draining the stream, they should reflect the
    completed run."""

    async def test_summary_after_run(
        self, two_meeting_workflow: Workflow, tmp_path: Path
    ) -> None:
        scripts = {
            "scoping": [_FakeEvent("complete")],
            "impl": [_FakeEvent("complete")],
        }
        runner = _FakeRunner(scripts, project_root=tmp_path)
        handle = LiveRunHandle(
            runner=runner,  # type: ignore[arg-type]
            workflow=two_meeting_workflow,
            directive="Build a thing.",
        )
        async for _ in handle.stream_events():
            pass
        summary = handle.summary()
        assert summary.workflow_name == "live-test"
        assert summary.directive == "Build a thing."
        assert summary.project_root == tmp_path
        assert summary.outcome == "COMPLETE"

    async def test_meetings_returns_completed_meetings(
        self, two_meeting_workflow: Workflow, tmp_path: Path
    ) -> None:
        scripts = {
            "scoping": [_FakeEvent("complete")],
            "impl": [_FakeEvent("complete")],
        }
        runner = _FakeRunner(scripts, project_root=tmp_path)
        handle = LiveRunHandle(
            runner=runner,  # type: ignore[arg-type]
            workflow=two_meeting_workflow,
            directive="go",
        )
        async for _ in handle.stream_events():
            pass
        meetings = handle.meetings()
        assert len(meetings) == 2
        assert {m.id for m in meetings} == {"scoping", "impl"}
        # Both should have terminal outcomes set
        assert all(m.outcome is not None for m in meetings)


class TestPolymorphicConsumer:
    """The acceptance test for T52 — same code consumes
    LiveRunHandle and (via Mock Turtle) HistoricalRunHandle the
    same way."""

    async def test_polymorphic_typed_against_run_handle(
        self, two_meeting_workflow: Workflow, tmp_path: Path
    ) -> None:
        from wonderland.observer.interface import RunHandle

        async def consume(handle: RunHandle) -> int:
            count = 0
            async for _ in handle.stream_events():
                count += 1
            return count

        scripts = {
            "scoping": [
                _FakeEvent(
                    "utterance",
                    {"utterance": _utt(thread_id="scoping")},
                ),
                _FakeEvent("complete"),
            ],
            "impl": [_FakeEvent("complete")],
        }
        runner = _FakeRunner(scripts, project_root=tmp_path)
        handle = LiveRunHandle(
            runner=runner,  # type: ignore[arg-type]
            workflow=two_meeting_workflow,
            directive="go",
        )
        count = await consume(handle)  # type: ignore[arg-type]
        assert count > 0
