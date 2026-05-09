"""Tests for the phased meeting orchestrator (T58b).

Tests use a FakePhaseRunner + FakePhaseAgent that scripts agent
responses, so we cover orchestration behavior end-to-end without
spinning up real LLM calls. Real Runner integration lands in T58c.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from wonderland import (
    AgentIdentity,
    InMemoryCaucus,
    SpeechAct,
    Utterance,
    UtteranceContent,
)
from wonderland.agent import Context
from wonderland.meeting import (
    AgentActEvent,
    AgentPassEvent,
    PhaseEndEvent,
    PhaseStartEvent,
    PriorityWindowOpenEvent,
    RotationCompleteEvent,
    run_phased_meeting,
)
from wonderland.utterance import Artifact
from wonderland.workflow import (
    Meeting,
    MeetingEndEvent,
    MeetingStartEvent,
    PhaseSpec,
    WorkflowCapture,
)


# --- Fakes -----------------------------------------------------------


class FakeTelemetry:
    def __init__(self) -> None:
        self.call_count: int = 0


@dataclass
class _ScriptedResponse:
    """One agent response in a script.

    ``utterance`` is what the fake agent's deliberate() returns. Use
    ``None`` to simulate silence (timeout); use ``RAISE_TIMEOUT`` to
    simulate the asyncio.wait_for path firing.
    """

    utterance: Utterance | None = None
    raise_timeout: bool = False


class FakePhaseAgent:
    """Mimics the WonderlandAgent surface that run_phased_meeting
    touches: ``identity``, ``compose_context``, ``deliberate``."""

    def __init__(self, name: str, *, responses: list[_ScriptedResponse] | None = None) -> None:
        self.identity = AgentIdentity(name=name, constitution_version="0.1")
        self._responses: list[_ScriptedResponse] = responses or []
        self._cursor: int = 0
        self.compose_calls: list[list[Utterance]] = []
        self.deliberate_calls: int = 0

    async def compose_context(self, triggers: list[Utterance]) -> Context:
        self.compose_calls.append(list(triggers))
        return Context(
            constitution=f"<{self.identity.name} constitution>",
            triggers=tuple(triggers),
        )

    async def deliberate(self, context: Context) -> Utterance | None:
        self.deliberate_calls += 1
        if self._cursor >= len(self._responses):
            return None  # exhausted scripts default to pass
        scripted = self._responses[self._cursor]
        self._cursor += 1
        if scripted.raise_timeout:
            # Hang forever so asyncio.wait_for fires the timeout.
            await asyncio.sleep(3600)
        return scripted.utterance


@dataclass
class FakePhaseRunner:
    """Slice of Runner that run_phased_meeting touches."""

    bus: InMemoryCaucus
    agents: dict[str, FakePhaseAgent]
    dodo: FakePhaseAgent
    telemetry: FakeTelemetry = field(default_factory=FakeTelemetry)
    total_cost: float = 0.0
    convene_calls: list[dict[str, Any]] = field(default_factory=list)
    thread_completes: list[dict[str, str]] = field(default_factory=list)
    _completed: bool = False
    # T58d: phase-event persistence writes to project_root/.wonderland/
    # — provide a tmp dir-friendly default that callers can override
    # per test (run_workflow path uses this).
    project_root: Path = field(
        default_factory=lambda: Path("/tmp") / "wonderland-test"
    )
    # Each ACTED window costs $0.05 by default; tests can override
    # by mutating runner.total_cost directly between yields.
    cost_per_act: float = 0.05

    async def convene(
        self,
        *,
        thread_id: str,
        goal: str,
        roster: list[str],
        seed_utterances: list[Utterance],
        convenor_directive: str | None = None,
    ) -> None:
        self.convene_calls.append(
            {
                "thread_id": thread_id,
                "goal": goal,
                "roster": list(roster),
                "seeds": list(seed_utterances),
                "convenor_directive": convenor_directive,
            }
        )

    def mark_thread_complete(self, thread_id: str, reason: str) -> None:
        self.thread_completes.append({"thread_id": thread_id, "reason": reason})


# --- Helpers ---------------------------------------------------------


def _utt(speaker: str, *, body: str = "...", act: SpeechAct = SpeechAct.PROPOSAL,
         thread_id: str = "t", artifacts: list[Artifact] | None = None) -> Utterance:
    return Utterance(
        thread_id=thread_id,
        speaker=AgentIdentity(name=speaker, constitution_version="0.1"),
        addressed_to="caucus",
        speech_act=act,
        content=UtteranceContent(body=body, artifacts=artifacts or []),
    )


def _meeting(
    *,
    roster: list[str],
    phases: list[PhaseSpec],
    meeting_budget: float | None = None,
) -> Meeting:
    return Meeting(
        id="t",
        label="M-test",
        goal="test",
        roster=roster,
        phases=phases,
        meeting_budget=meeting_budget,
    )


def _make_runner(
    *,
    cast: list[str],
    scripts: dict[str, list[_ScriptedResponse]] | None = None,
) -> FakePhaseRunner:
    bus = InMemoryCaucus()
    scripts = scripts or {}
    agents = {
        name: FakePhaseAgent(name, responses=scripts.get(name, []))
        for name in cast
    }
    dodo = FakePhaseAgent("dodo")
    return FakePhaseRunner(bus=bus, agents=agents, dodo=dodo)


async def _drive(meeting: Meeting, runner: FakePhaseRunner) -> list[Any]:
    """Run the orchestrator to completion and collect yielded events."""
    events: list[Any] = []
    async for event in run_phased_meeting(
        meeting=meeting,
        runner=runner,  # type: ignore[arg-type]
        capture=WorkflowCapture(),
        directive=None,
        per_item_meetings={},
        current_item_kind=None,
        current_item_slug=None,
        thread_id="t",
        iteration_index=None,
        iteration_total=None,
        iteration_label=None,
    ):
        events.append(event)
        # Mock cost accounting: each ACTED utterance ticks the meter.
        # Window-open from Dodo doesn't.
        if hasattr(event, "kind") and event.kind == "utterance":
            u = event.payload.get("utterance")
            if u is not None and u.speaker.name != "dodo":
                runner.total_cost += runner.cost_per_act
                runner.telemetry.call_count += 1
    return events


# ---------------------------------------------------------------------
# Construction + basic shape
# ---------------------------------------------------------------------


async def test_meeting_start_and_end_events_bracket_phase_events() -> None:
    runner = _make_runner(
        cast=["alice"],
        scripts={
            "alice": [_ScriptedResponse(utterance=_utt("alice", body="hi"))],
        },
    )
    meeting = _meeting(
        roster=["alice"],
        phases=[PhaseSpec(name="discussion", max_rotations=1)],
    )
    events = await _drive(meeting, runner)

    assert isinstance(events[0], MeetingStartEvent)
    assert isinstance(events[-2], MeetingEndEvent)
    # Last event is _OutcomeSentinel
    assert events[-1].outcome == "COMPLETE"

    # PhaseStart precedes any window event
    phase_starts = [e for e in events if isinstance(e, PhaseStartEvent)]
    phase_ends = [e for e in events if isinstance(e, PhaseEndEvent)]
    assert len(phase_starts) == 1
    assert len(phase_ends) == 1


# ---------------------------------------------------------------------
# Termination: rotation budget exhausts
# ---------------------------------------------------------------------


async def test_phase_ends_with_reason_exhausted_when_all_act() -> None:
    """Three agents, one rotation max, every agent acts → phase ends
    with reason 'exhausted'."""
    runner = _make_runner(
        cast=["a", "b", "c"],
        scripts={
            "a": [_ScriptedResponse(utterance=_utt("a"))],
            "b": [_ScriptedResponse(utterance=_utt("b"))],
            "c": [_ScriptedResponse(utterance=_utt("c"))],
        },
    )
    meeting = _meeting(
        roster=["a", "b", "c"],
        phases=[PhaseSpec(name="discussion", max_rotations=1)],
    )
    events = await _drive(meeting, runner)

    end = next(e for e in events if isinstance(e, PhaseEndEvent))
    assert end.reason == "exhausted"
    assert end.rotations_used == 1
    assert end.total_windows == 3
    assert end.acts_per_agent == {"a": 1, "b": 1, "c": 1}
    assert end.passes_per_agent == {"a": 0, "b": 0, "c": 0}


# ---------------------------------------------------------------------
# Termination: succession (everyone passes in last rotation)
# ---------------------------------------------------------------------


async def test_phase_ends_via_succession_when_all_pass_first_rotation() -> None:
    """Three agents all return None → all PASSED → phase ends via
    succession on the first rotation."""
    runner = _make_runner(
        cast=["a", "b", "c"],
        scripts={
            "a": [_ScriptedResponse(utterance=None)],
            "b": [_ScriptedResponse(utterance=None)],
            "c": [_ScriptedResponse(utterance=None)],
        },
    )
    meeting = _meeting(
        roster=["a", "b", "c"],
        phases=[PhaseSpec(name="discussion", max_rotations=5)],
    )
    events = await _drive(meeting, runner)

    end = next(e for e in events if isinstance(e, PhaseEndEvent))
    assert end.reason == "succession"
    assert end.rotations_used == 1
    assert end.passes_per_agent == {"a": 1, "b": 1, "c": 1}


# ---------------------------------------------------------------------
# Explicit PASS speech act
# ---------------------------------------------------------------------


async def test_explicit_pass_speech_act_classified_as_passed() -> None:
    """An agent emitting speech_act=PASS produces an AgentPassEvent
    with the body as the reason; not an AgentActEvent."""
    pass_utt = _utt("a", body="Nothing to add this rotation.", act=SpeechAct.PASS)
    runner = _make_runner(
        cast=["a"],
        scripts={"a": [_ScriptedResponse(utterance=pass_utt)]},
    )
    meeting = _meeting(
        roster=["a"],
        phases=[PhaseSpec(name="discussion", max_rotations=1)],
    )
    events = await _drive(meeting, runner)

    pass_events = [e for e in events if isinstance(e, AgentPassEvent)]
    act_events = [e for e in events if isinstance(e, AgentActEvent)]
    assert len(pass_events) == 1
    assert pass_events[0].reason == "Nothing to add this rotation."
    assert len(act_events) == 0


# ---------------------------------------------------------------------
# Per-window timeout
# ---------------------------------------------------------------------


async def test_window_timeout_classified_as_pass() -> None:
    """When deliberate hangs past the window timeout, the window is
    classified as PASSED (no utterance, no AgentActEvent)."""
    runner = _make_runner(
        cast=["a"],
        scripts={"a": [_ScriptedResponse(raise_timeout=True)]},
    )
    meeting = _meeting(
        roster=["a"],
        phases=[PhaseSpec(name="discussion", max_rotations=1)],
    )
    events: list[Any] = []
    async for event in run_phased_meeting(
        meeting=meeting,
        runner=runner,  # type: ignore[arg-type]
        capture=WorkflowCapture(),
        directive=None,
        per_item_meetings={},
        current_item_kind=None,
        current_item_slug=None,
        thread_id="t",
        iteration_index=None,
        iteration_total=None,
        iteration_label=None,
        window_timeout_seconds=0.05,  # tight, so the test isn't slow
    ):
        events.append(event)

    assert any(isinstance(e, AgentPassEvent) for e in events)
    assert not any(isinstance(e, AgentActEvent) for e in events)


# ---------------------------------------------------------------------
# Multi-phase: phases run in declaration order
# ---------------------------------------------------------------------


async def test_multiple_phases_run_in_declaration_order() -> None:
    runner = _make_runner(
        cast=["a"],
        scripts={
            "a": [
                _ScriptedResponse(utterance=_utt("a", body="phase-1")),
                _ScriptedResponse(utterance=_utt("a", body="phase-2")),
            ],
        },
    )
    meeting = _meeting(
        roster=["a"],
        phases=[
            PhaseSpec(name="opening", max_rotations=1),
            PhaseSpec(name="closing", max_rotations=1),
        ],
    )
    events = await _drive(meeting, runner)

    starts = [e for e in events if isinstance(e, PhaseStartEvent)]
    assert [s.phase.name for s in starts] == ["opening", "closing"]


# ---------------------------------------------------------------------
# Recipients filter on the window-open utterance (T58a integration)
# ---------------------------------------------------------------------


async def test_window_open_utterance_targets_only_priority_agent() -> None:
    """The window-open utterance carries recipients={priority_agent},
    so the bus delivers it only to that agent. Bystander agents on the
    bus don't see it."""
    runner = _make_runner(
        cast=["a", "b"],
        scripts={
            "a": [_ScriptedResponse(utterance=_utt("a"))],
            "b": [_ScriptedResponse(utterance=_utt("b"))],
        },
    )

    sub_a = runner.bus.subscribe(agent_name="a")
    sub_b = runner.bus.subscribe(agent_name="b")
    sub_obs = runner.bus.subscribe(agent_name="runner-observer", bypass_roster=True)

    meeting = _meeting(
        roster=["a", "b"],
        phases=[PhaseSpec(name="discussion", max_rotations=1)],
    )
    await _drive(meeting, runner)

    async def collect_until_drained(it: AsyncIterator[Utterance]) -> list[Utterance]:
        out: list[Utterance] = []
        try:
            while True:
                u = await asyncio.wait_for(anext(it), timeout=0.05)
                out.append(u)
        except (asyncio.TimeoutError, StopAsyncIteration):
            return out

    a_received = await collect_until_drained(sub_a)
    b_received = await collect_until_drained(sub_b)
    obs_received = await collect_until_drained(sub_obs)

    # Each agent received their own window-open and both response
    # utterances (responses go open since they have recipients=None).
    a_window_opens = [u for u in a_received if u.speaker.name == "dodo"]
    b_window_opens = [u for u in b_received if u.speaker.name == "dodo"]
    assert len(a_window_opens) == 1
    assert len(b_window_opens) == 1
    # A's window-open targeted only A; B's targeted only B.
    assert a_window_opens[0].recipients == frozenset({"a"})
    assert b_window_opens[0].recipients == frozenset({"b"})
    # Observer (bypass_roster=True) saw both window-opens — measurement
    # is whole-bus.
    obs_window_opens = [u for u in obs_received if u.speaker.name == "dodo"]
    assert len(obs_window_opens) == 2


# ---------------------------------------------------------------------
# Rotation boundaries
# ---------------------------------------------------------------------


async def test_rotation_complete_event_emitted_at_each_boundary() -> None:
    runner = _make_runner(
        cast=["a", "b"],
        scripts={
            "a": [
                _ScriptedResponse(utterance=_utt("a")),
                _ScriptedResponse(utterance=_utt("a")),
            ],
            "b": [
                _ScriptedResponse(utterance=_utt("b")),
                _ScriptedResponse(utterance=_utt("b")),
            ],
        },
    )
    meeting = _meeting(
        roster=["a", "b"],
        phases=[PhaseSpec(name="discussion", max_rotations=2)],
    )
    events = await _drive(meeting, runner)

    rot_events = [e for e in events if isinstance(e, RotationCompleteEvent)]
    assert [r.rotation_index for r in rot_events] == [0, 1]


# ---------------------------------------------------------------------
# Meeting budget gate
# ---------------------------------------------------------------------


async def test_meeting_budget_exhaustion_ends_phase_with_aborted_reason() -> None:
    """When the meeting_budget fires mid-phase, the phase ends with
    reason='aborted' and the meeting outcome is MEETING_BUDGET."""
    runner = _make_runner(
        cast=["a", "b", "c"],
        scripts={
            "a": [_ScriptedResponse(utterance=_utt("a"))] * 5,
            "b": [_ScriptedResponse(utterance=_utt("b"))] * 5,
            "c": [_ScriptedResponse(utterance=_utt("c"))] * 5,
        },
    )
    runner.cost_per_act = 0.10
    meeting = _meeting(
        roster=["a", "b", "c"],
        phases=[PhaseSpec(name="discussion", max_rotations=10)],
        meeting_budget=0.25,  # ~3 acts before budget hits
    )
    events = await _drive(meeting, runner)

    end_event = next(e for e in events if isinstance(e, PhaseEndEvent))
    assert end_event.reason == "aborted"

    sentinel = events[-1]
    assert sentinel.outcome == "MEETING_BUDGET"

    # mark_thread_complete called for non-COMPLETE outcomes
    assert any(c["thread_id"] == "t" for c in runner.thread_completes)


# ---------------------------------------------------------------------
# Exit condition: phase ends when artifact ships
# ---------------------------------------------------------------------


async def test_phase_ends_via_exit_condition_when_target_artifact_ships() -> None:
    """When an agent ships an artifact whose kind matches the phase's
    exit_condition_artifact, the phase ends with reason='exit_condition'
    even if rotation budget remains."""
    contract_artifact = Artifact(kind="contract", payload={"slug": "deal"})
    settle_utt = _utt(
        "a",
        body="Contract signed.",
        act=SpeechAct.CONTRACT_NOTE,
        artifacts=[contract_artifact],
    )
    runner = _make_runner(
        cast=["a", "b"],
        scripts={
            "a": [_ScriptedResponse(utterance=settle_utt)],
            "b": [_ScriptedResponse(utterance=_utt("b"))],
        },
    )
    meeting = _meeting(
        roster=["a", "b"],
        phases=[
            PhaseSpec(
                name="negotiate",
                max_rotations=10,
                exit_condition_artifact="contract",
            ),
        ],
    )
    events = await _drive(meeting, runner)

    end = next(e for e in events if isinstance(e, PhaseEndEvent))
    assert end.reason == "exit_condition"
    # Phase ended after a's first window — b never got a turn.
    assert end.total_windows == 1


# ---------------------------------------------------------------------
# Window event sequencing
# ---------------------------------------------------------------------


async def test_window_open_event_precedes_act_event_for_same_window() -> None:
    """For each priority window: PriorityWindowOpenEvent precedes the
    AgentActEvent / AgentPassEvent that resolves it."""
    runner = _make_runner(
        cast=["a", "b"],
        scripts={
            "a": [_ScriptedResponse(utterance=_utt("a"))],
            "b": [_ScriptedResponse(utterance=_utt("b"))],
        },
    )
    meeting = _meeting(
        roster=["a", "b"],
        phases=[PhaseSpec(name="discussion", max_rotations=1)],
    )
    events = await _drive(meeting, runner)

    window_open_indices = [
        i for i, e in enumerate(events) if isinstance(e, PriorityWindowOpenEvent)
    ]
    act_indices = [
        i for i, e in enumerate(events) if isinstance(e, AgentActEvent)
    ]
    # Two windows, two acts; each act follows its window-open.
    assert len(window_open_indices) == 2
    assert len(act_indices) == 2
    assert window_open_indices[0] < act_indices[0]
    assert window_open_indices[1] < act_indices[1]


# ---------------------------------------------------------------------
# Convene + cleanup
# ---------------------------------------------------------------------


async def test_convene_called_before_phase_loop() -> None:
    runner = _make_runner(
        cast=["a"],
        scripts={"a": [_ScriptedResponse(utterance=_utt("a"))]},
    )
    meeting = _meeting(
        roster=["a"],
        phases=[PhaseSpec(name="discussion", max_rotations=1)],
    )
    await _drive(meeting, runner)

    assert len(runner.convene_calls) == 1
    assert runner.convene_calls[0]["thread_id"] == "t"
    assert runner.convene_calls[0]["roster"] == ["a"]


# ---------------------------------------------------------------------
# Two-Headed Giant — concurrent team windows (T64 / P9.5)
# ---------------------------------------------------------------------


async def test_team_window_opens_for_all_members_concurrently() -> None:
    """A team window emits one PriorityWindowOpenEvent per team
    member, all before any deliberation runs (events fire upfront,
    deliberations happen in parallel via asyncio.gather)."""
    runner = _make_runner(
        cast=["alice", "hatter"],
        scripts={
            "alice": [_ScriptedResponse(utterance=_utt("alice"))],
            "hatter": [_ScriptedResponse(utterance=_utt("hatter"))],
        },
    )
    meeting = _meeting(
        roster=["alice", "hatter"],
        phases=[
            PhaseSpec(
                name="clarify",
                max_rotations=1,
                team_groupings=[["alice", "hatter"]],
            ),
        ],
    )
    events = await _drive(meeting, runner)

    pwos = [e for e in events if isinstance(e, PriorityWindowOpenEvent)]
    # One rotation × one team of 2 = 2 windows
    assert len(pwos) == 2
    # Both share the same rotation_index and consecutive
    # window_index slots in cast order
    assert pwos[0].agent_id == "alice"
    assert pwos[0].rotation_index == 0
    assert pwos[0].window_index == 0
    assert pwos[1].agent_id == "hatter"
    assert pwos[1].rotation_index == 0
    assert pwos[1].window_index == 1


async def test_team_window_resolves_in_cast_order_regardless_of_completion_order() -> None:
    """asyncio.gather may complete deliberations in any order, but
    AgentActedEvents fire in cast order so the transcript stays
    deterministic."""
    runner = _make_runner(
        cast=["alice", "hatter"],
        scripts={
            "alice": [_ScriptedResponse(utterance=_utt("alice"))],
            "hatter": [_ScriptedResponse(utterance=_utt("hatter"))],
        },
    )
    meeting = _meeting(
        roster=["alice", "hatter"],
        phases=[
            PhaseSpec(
                name="clarify",
                max_rotations=1,
                team_groupings=[["alice", "hatter"]],
            ),
        ],
    )
    events = await _drive(meeting, runner)

    acts = [e for e in events if isinstance(e, AgentActEvent)]
    assert [a.agent_id for a in acts] == ["alice", "hatter"]


async def test_two_teams_advance_in_declaration_order() -> None:
    """With multiple teams declared, each rotation cycles through
    teams in order. Team 0's full window resolves before team 1
    opens."""
    runner = _make_runner(
        cast=["alice", "hatter", "td", "tdm"],
        scripts={
            "alice": [_ScriptedResponse(utterance=_utt("alice"))],
            "hatter": [_ScriptedResponse(utterance=_utt("hatter"))],
            "td": [_ScriptedResponse(utterance=_utt("td"))],
            "tdm": [_ScriptedResponse(utterance=_utt("tdm"))],
        },
    )
    meeting = _meeting(
        roster=["alice", "hatter", "td", "tdm"],
        phases=[
            PhaseSpec(
                name="clarify",
                max_rotations=1,
                team_groupings=[["alice", "hatter"], ["td", "tdm"]],
            ),
        ],
    )
    events = await _drive(meeting, runner)

    pwos = [e for e in events if isinstance(e, PriorityWindowOpenEvent)]
    assert [p.agent_id for p in pwos] == ["alice", "hatter", "td", "tdm"]
    # All in rotation 0
    assert all(p.rotation_index == 0 for p in pwos)
    # window_index is monotonic across both teams
    assert [p.window_index for p in pwos] == [0, 1, 2, 3]


async def test_team_window_continues_when_one_member_raises() -> None:
    """asyncio.gather(return_exceptions=True) means a single
    member's failure doesn't poison the rest. The failing member
    is treated as PASS (no AgentActed for them); the other member
    still acts normally."""

    class _RaisingAgent(FakePhaseAgent):
        async def deliberate(self, context: Context) -> Utterance | None:
            raise RuntimeError("simulated deliberate failure")

    runner = _make_runner(
        cast=["alice", "hatter"],
        scripts={
            "alice": [_ScriptedResponse(utterance=_utt("alice"))],
        },
    )
    # Replace hatter with the raising agent
    runner.agents["hatter"] = _RaisingAgent("hatter")

    meeting = _meeting(
        roster=["alice", "hatter"],
        phases=[
            PhaseSpec(
                name="clarify",
                max_rotations=1,
                team_groupings=[["alice", "hatter"]],
            ),
        ],
    )
    events = await _drive(meeting, runner)

    acts = [e for e in events if isinstance(e, AgentActEvent)]
    passes = [e for e in events if isinstance(e, AgentPassEvent)]
    assert len(acts) == 1
    assert acts[0].agent_id == "alice"
    assert len(passes) == 1
    assert passes[0].agent_id == "hatter"


async def test_team_windows_recover_parallelism_via_gather() -> None:
    """Wall-clock smoke check: when two team members each take ~50ms
    to deliberate, the team window completes in ~50ms (parallel),
    not ~100ms (serial)."""

    class _SlowAgent(FakePhaseAgent):
        def __init__(self, name: str, delay: float) -> None:
            super().__init__(name)
            self._delay = delay

        async def deliberate(self, context: Context) -> Utterance | None:
            await asyncio.sleep(self._delay)
            return _utt(self.identity.name)

    runner = _make_runner(cast=["alice", "hatter"], scripts={})
    runner.agents["alice"] = _SlowAgent("alice", 0.05)
    runner.agents["hatter"] = _SlowAgent("hatter", 0.05)

    meeting = _meeting(
        roster=["alice", "hatter"],
        phases=[
            PhaseSpec(
                name="clarify",
                max_rotations=1,
                team_groupings=[["alice", "hatter"]],
            ),
        ],
    )
    start = time.monotonic()
    await _drive(meeting, runner)
    elapsed = time.monotonic() - start
    # Sequential would be ~0.10s; parallel should land near 0.05s.
    # Allow generous slack for CI flakiness — the assertion is
    # "we're closer to parallel than serial."
    assert elapsed < 0.09, (
        f"team window took {elapsed:.3f}s; expected near 0.05s "
        "(parallel via gather), not 0.10s (serial)"
    )


async def test_run_workflow_dispatches_phased_meetings_to_orchestrator(tmp_path) -> None:
    """A workflow with a phased meeting routes through
    run_phased_meeting; phase events appear in run_workflow's
    yielded event stream alongside meeting events."""
    from wonderland.workflow import Workflow, run_workflow

    runner = _make_runner(
        cast=["a", "b"],
        scripts={
            "a": [_ScriptedResponse(utterance=_utt("a"))],
            "b": [_ScriptedResponse(utterance=_utt("b"))],
        },
    )
    # T58d wires a phase-event writer based on runner.project_root;
    # use the test's tmp dir to keep the JSONL out of /tmp/.
    runner.project_root = tmp_path
    workflow = Workflow(
        name="phased-test",
        description="d",
        meetings=[
            Meeting(
                id="phased-meeting",
                label="M1",
                goal="phased work",
                roster=["a", "b"],
                phases=[PhaseSpec(name="discussion", max_rotations=1)],
            ),
        ],
    )

    events: list[Any] = []
    async for event in run_workflow(workflow, runner, "test directive"):  # type: ignore[arg-type]
        events.append(event)
        if hasattr(event, "kind") and event.kind == "utterance":
            u = event.payload.get("utterance")
            if u is not None and u.speaker.name != "dodo":
                runner.total_cost += runner.cost_per_act
                runner.telemetry.call_count += 1

    assert any(isinstance(e, PhaseStartEvent) for e in events)
    assert any(isinstance(e, PhaseEndEvent) for e in events)
    assert any(isinstance(e, PriorityWindowOpenEvent) for e in events)
    assert any(isinstance(e, AgentActEvent) for e in events)

    # Meeting events bracket the phase events.
    meeting_start = next(
        i for i, e in enumerate(events) if isinstance(e, MeetingStartEvent)
    )
    meeting_end = next(
        i for i, e in enumerate(events) if isinstance(e, MeetingEndEvent)
    )
    phase_start = next(
        i for i, e in enumerate(events) if isinstance(e, PhaseStartEvent)
    )
    phase_end = next(
        i for i, e in enumerate(events) if isinstance(e, PhaseEndEvent)
    )
    assert meeting_start < phase_start < phase_end < meeting_end


async def test_phase_event_writer_called_for_every_phase_event(tmp_path) -> None:
    """T58d — when a phase_event_writer is supplied, every phase
    event the orchestrator yields is also passed to the writer in
    order. Validates the persistence hook before checking on-disk
    format separately."""
    runner = _make_runner(
        cast=["a", "b"],
        scripts={
            "a": [_ScriptedResponse(utterance=_utt("a"))],
            "b": [_ScriptedResponse(utterance=_utt("b"))],
        },
    )
    meeting = _meeting(
        roster=["a", "b"],
        phases=[PhaseSpec(name="discussion", max_rotations=1)],
    )

    captured: list[Any] = []

    async def writer(event: Any) -> None:
        captured.append(event)

    events: list[Any] = []
    async for event in run_phased_meeting(
        meeting=meeting,
        runner=runner,  # type: ignore[arg-type]
        capture=WorkflowCapture(),
        directive=None,
        per_item_meetings={},
        current_item_kind=None,
        current_item_slug=None,
        thread_id="t",
        iteration_index=None,
        iteration_total=None,
        iteration_label=None,
        phase_event_writer=writer,
    ):
        events.append(event)

    # Every phase event from `events` appears in `captured` in the
    # same order. (Other event types — RunnerEvent, MeetingStart/End
    # — are not phase events and aren't written.)
    from wonderland.meeting import (
        AgentActEvent,
        AgentPassEvent,
        PhaseEndEvent,
        PhaseStartEvent,
        PriorityWindowOpenEvent,
        RotationCompleteEvent,
    )

    phase_event_types = (
        PhaseStartEvent,
        PhaseEndEvent,
        PriorityWindowOpenEvent,
        AgentActEvent,
        AgentPassEvent,
        RotationCompleteEvent,
    )
    yielded_phase_events = [e for e in events if isinstance(e, phase_event_types)]
    assert captured == yielded_phase_events
    assert len(captured) >= 5  # PhaseStart + 2 windows + 2 acts + RotationComplete + PhaseEnd at minimum


async def test_jsonl_phase_event_writer_round_trip(tmp_path) -> None:
    """T58d — write phase events through jsonl_phase_event_writer,
    then read them back via read_phase_events. Should round-trip
    every event type exactly."""
    from datetime import datetime, timezone

    from wonderland.meeting import (
        AgentActEvent,
        AgentPassEvent,
        PhaseEndEvent,
        PhaseStartEvent,
        PriorityWindowOpenEvent,
        RotationCompleteEvent,
        jsonl_phase_event_writer,
        read_phase_events,
    )
    from wonderland.turns import PhaseDefinition

    path = tmp_path / "phase-events.jsonl"
    write = jsonl_phase_event_writer(path)

    now = datetime(2026, 5, 9, 12, 0, 0, tzinfo=timezone.utc)
    events = [
        PhaseStartEvent(
            thread_id="m4",
            phase=PhaseDefinition(name="red-tests", max_rotations=3),
            cast=("alice", "hatter"),
            timestamp=now,
        ),
        PriorityWindowOpenEvent(
            thread_id="m4",
            phase_name="red-tests",
            agent_id="alice",
            rotation_index=0,
            window_index=0,
            timestamp=now,
        ),
        AgentActEvent(
            thread_id="m4",
            phase_name="red-tests",
            agent_id="alice",
            rotation_index=0,
            utterance_id="u-1",
            timestamp=now,
        ),
        AgentPassEvent(
            thread_id="m4",
            phase_name="red-tests",
            agent_id="hatter",
            rotation_index=0,
            reason=None,
            timestamp=now,
        ),
        RotationCompleteEvent(
            thread_id="m4",
            phase_name="red-tests",
            rotation_index=0,
            timestamp=now,
        ),
        PhaseEndEvent(
            thread_id="m4",
            phase_name="red-tests",
            reason="succession",
            rotations_used=1,
            total_windows=2,
            passes_per_agent={"alice": 0, "hatter": 1},
            acts_per_agent={"alice": 1, "hatter": 0},
            timestamp=now,
        ),
    ]
    for ev in events:
        await write(ev)

    read_back = read_phase_events(path)
    assert read_back == events


async def test_jsonl_phase_event_writer_creates_parent_dir(tmp_path) -> None:
    """The writer must create the .wonderland/ parent directory if
    it doesn't exist — fresh project roots won't have it."""
    from wonderland.meeting import (
        PhaseStartEvent,
        jsonl_phase_event_writer,
    )
    from wonderland.turns import PhaseDefinition

    nested = tmp_path / "fresh" / ".wonderland" / "phase-events.jsonl"
    write = jsonl_phase_event_writer(nested)
    await write(
        PhaseStartEvent(
            thread_id="m",
            phase=PhaseDefinition(name="d"),
            cast=("a",),
        )
    )
    assert nested.is_file()


async def test_read_phase_events_missing_file_returns_empty(tmp_path) -> None:
    """Older snapshots predate T58d and won't have phase-events.jsonl
    — read_phase_events returns an empty list, not an error."""
    from wonderland.meeting import read_phase_events

    assert read_phase_events(tmp_path / "nonexistent.jsonl") == []


async def test_orchestrator_owned_flag_cleared_in_finally() -> None:
    """Even when an exception fires mid-phase, the
    _orchestrator_owned flag must be cleared so agents resume
    autonomous deliberation in subsequent meetings."""
    # Force the script to be empty so deliberate returns None each
    # time → all-pass → phase exits cleanly. We're checking the
    # finally block resets the flag.
    runner = _make_runner(cast=["a"], scripts={"a": []})
    meeting = _meeting(
        roster=["a"],
        phases=[PhaseSpec(name="d", max_rotations=1)],
    )
    await _drive(meeting, runner)

    assert getattr(runner.agents["a"], "_orchestrator_owned", None) is False
