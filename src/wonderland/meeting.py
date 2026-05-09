"""Phased meeting orchestrator — the engine for analysis 033 / P9.

Drives a meeting whose ``phases:`` list is non-empty by opening
priority windows in rotation, asking each cast member to act-or-pass,
and advancing phases on the three exit conditions (succession,
exhaustion, exit-condition artifact). Strictly opt-in — meetings
without ``phases:`` declared continue to use ``_convene_one``'s
legacy engagement-policy path in ``workflow.py``.

The orchestrator yields workflow-level events compatible with
``run_workflow``'s existing surface; ``LiveRunHandle`` translates the
new phase events into ``RunEvent`` shapes (T56) for the streaming UI.

Per the design decisions sketched in T58 review:
  1. Engagement bypass — orchestrator drives ``deliberate()`` directly
     rather than relying on each agent's engagement policy.
  2. Synthetic trigger — the window-open utterance carries the
     "act or pass" framing in its body; constitutions are not modified.
  3. Per-window timeout via ``asyncio.wait_for``, default 300s
     (matches ``Runner.DEFAULT_QUIESCENCE_SECONDS``).
  4. Both meeting_budget (dollars) and rotation budget apply;
     whichever fires first ends the phase.
  5. Snapshot persistence of phase events lands in T58c.
"""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from wonderland.turns import (
    PhaseDefinition,
    PhaseState,
    WindowAction,
    WindowOutcome,
)
from wonderland.utterance import (
    AgentIdentity,
    SpeechAct,
    Utterance,
    UtteranceContent,
)

if TYPE_CHECKING:
    from wonderland.runner import Runner
    from wonderland.workflow import Meeting, WorkflowCapture


# Default per-window deliberation timeout. Matches Runner's
# DEFAULT_QUIESCENCE_SECONDS — Tweedles writing 250-line files while
# iterating on red→green tests can legitimately take several minutes
# of tool loop. Shorter timeouts here would convert real work into
# spurious passes.
DEFAULT_WINDOW_TIMEOUT_SECONDS: float = 300.0


# ---------------------------------------------------------------------
# Workflow-level event dataclasses (translated to T56 RunEvents by
# LiveRunHandle).
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class PhaseStartEvent:
    """A phase opened inside a phased meeting."""

    thread_id: str
    phase: PhaseDefinition
    cast: tuple[str, ...]
    timestamp: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))


@dataclass(frozen=True)
class PhaseEndEvent:
    """A phase closed. ``reason`` is one of: succession, exhausted,
    exit_condition, aborted."""

    thread_id: str
    phase_name: str
    reason: str
    rotations_used: int
    total_windows: int
    passes_per_agent: dict[str, int]
    acts_per_agent: dict[str, int]
    timestamp: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))


@dataclass(frozen=True)
class PriorityWindowOpenEvent:
    """Priority just passed to ``agent_id`` for one window."""

    thread_id: str
    phase_name: str
    agent_id: str
    rotation_index: int
    window_index: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))


@dataclass(frozen=True)
class AgentActEvent:
    """The agent used their priority window to emit an utterance."""

    thread_id: str
    phase_name: str
    agent_id: str
    rotation_index: int
    utterance_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))


@dataclass(frozen=True)
class AgentPassEvent:
    """The agent declined their priority window."""

    thread_id: str
    phase_name: str
    agent_id: str
    rotation_index: int
    reason: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))


@dataclass(frozen=True)
class RotationCompleteEvent:
    """A full rotation around the cast just finished — boundary
    event for UI rendering."""

    thread_id: str
    phase_name: str
    rotation_index: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))


# ---------------------------------------------------------------------
# Phase-event persistence (T58d / analysis 034 F6)
# ---------------------------------------------------------------------
# Phased runs need their phase events on disk so post-run analysis can
# measure deliberations (the unit phases bound) rather than just LLM
# calls (what telemetry tracks). Without this, every phased run has
# the same measurement gap r35 had — we know a phase ended via
# `succession` vs `exhausted` etc., but only on the live wire.

PhaseEvent = (
    PhaseStartEvent
    | PhaseEndEvent
    | PriorityWindowOpenEvent
    | AgentActEvent
    | AgentPassEvent
    | RotationCompleteEvent
)

PhaseEventWriter = Callable[[PhaseEvent], Awaitable[None]]
"""Coroutine that persists a phase event somewhere (default: JSONL on
disk). Async so writers can use aiofiles or batched flushes if needed;
the default writer is synchronous-disguised-as-async (a bare file
write + flush per event)."""


_EVENT_KINDS: dict[str, type] = {
    "PhaseStartEvent": PhaseStartEvent,
    "PhaseEndEvent": PhaseEndEvent,
    "PriorityWindowOpenEvent": PriorityWindowOpenEvent,
    "AgentActEvent": AgentActEvent,
    "AgentPassEvent": AgentPassEvent,
    "RotationCompleteEvent": RotationCompleteEvent,
}


def serialize_phase_event(event: PhaseEvent) -> dict[str, Any]:
    """Convert a phase event to a JSON-friendly dict.

    Adds a ``_kind`` discriminator so the reader knows which event
    type to reconstruct. ``datetime`` fields serialize as ISO 8601.
    Nested dataclasses (PhaseDefinition inside PhaseStartEvent)
    serialize via ``dataclasses.asdict``. Tuples serialize as lists
    (JSON-native); the deserializer restores tuples for fields that
    require them.
    """
    payload = asdict(event)
    payload["_kind"] = type(event).__name__
    # asdict converts datetime as-is (not JSON-friendly); fix up.
    if isinstance(event.timestamp, datetime):
        payload["timestamp"] = event.timestamp.isoformat()
    return payload


def deserialize_phase_event(payload: dict[str, Any]) -> PhaseEvent:
    """Reconstruct a phase event from its on-disk dict form."""
    kind = payload.pop("_kind", None)
    if kind not in _EVENT_KINDS:
        raise ValueError(f"unknown phase-event kind: {kind!r}")
    cls = _EVENT_KINDS[kind]
    if isinstance(payload.get("timestamp"), str):
        payload["timestamp"] = datetime.fromisoformat(payload["timestamp"])
    if kind == "PhaseStartEvent":
        # ``phase`` is a nested dataclass; ``cast`` was a tuple
        # serialized as a list. ``team_groupings`` was a tuple-of-
        # tuples on the engine side; JSON gives us list-of-lists,
        # restore tuple shape so equality holds.
        phase_payload = dict(payload["phase"])
        if "team_groupings" in phase_payload:
            phase_payload["team_groupings"] = tuple(
                tuple(team) for team in phase_payload["team_groupings"]
            )
        payload["phase"] = PhaseDefinition(**phase_payload)
        payload["cast"] = tuple(payload["cast"])
    return cls(**payload)


def jsonl_phase_event_writer(path: Path) -> PhaseEventWriter:
    """Build a writer that appends one JSON line per phase event to
    ``path``. The parent directory is created if missing. Each call
    opens, appends, and flushes — small overhead per event but
    guarantees the line is on disk before the next event fires (so
    a crash mid-meeting still leaves a partial-but-readable log).
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    async def _write(event: PhaseEvent) -> None:
        line = json.dumps(serialize_phase_event(event)) + "\n"
        # Open-append-close per event for crash safety. Phased
        # meetings emit a few events per second at most, so the
        # syscall overhead is negligible.
        with path.open("a") as f:
            f.write(line)

    return _write


def read_phase_events(path: Path) -> list[PhaseEvent]:
    """Read a phase-events.jsonl file and return the events in
    write order. Returns an empty list if the file doesn't exist
    (older snapshots predate T58d)."""
    if not path.is_file():
        return []
    events: list[PhaseEvent] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            events.append(deserialize_phase_event(json.loads(line)))
    return events


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def _build_window_open_utterance(
    *,
    thread_id: str,
    phase_name: str,
    agent_id: str,
    dodo_identity: AgentIdentity,
    target_identity: AgentIdentity,
) -> Utterance:
    """Construct the window-open utterance from Dodo to the priority
    agent. Uses ``recipients={agent_id}`` so only the target sees it
    (T58a primitive). Body carries the synthetic "act or pass"
    framing — no constitution change required."""
    return Utterance(
        thread_id=thread_id,
        speaker=dodo_identity,
        addressed_to=[target_identity],
        speech_act=SpeechAct.NUDGE,
        content=UtteranceContent(
            body=(
                f"**Priority window — phase: {phase_name}.**\n\n"
                f"It is your turn to act. You may emit any speech act "
                f"that's load-bearing in this phase, or emit "
                f"`speech_act: pass` if you have nothing load-bearing "
                f"to add right now. Other cast members are listening "
                f"but cannot act in this window."
            ),
        ),
        recipients=frozenset({agent_id}),
    )


def _classify_response(response: Utterance | None) -> WindowAction:
    """Map an agent's deliberate() result to ACT or PASS."""
    if response is None:
        return WindowAction.PASSED
    if response.speech_act == SpeechAct.PASS:
        return WindowAction.PASSED
    return WindowAction.ACTED


def _phase_end_reason(
    *,
    state: PhaseState,
    meeting_budget_hit: bool,
) -> str:
    """Determine why a phase ended. Order matters: budget overrides
    natural completion conditions; exit_condition overrides budget
    exhaustion; succession overrides rotation exhaustion."""
    if meeting_budget_hit:
        return "aborted"
    if state.exit_condition_met:
        return "exit_condition"
    if state.all_passed_in_succession():
        return "succession"
    if state.is_exhausted():
        return "exhausted"
    return "aborted"  # defensive — shouldn't reach


def _check_exit_condition(
    *,
    state: PhaseState,
    capture: "WorkflowCapture",
    artifact_count_before: int,
) -> None:
    """Scan utterances captured so far this meeting for an artifact
    of the phase's exit_condition_artifact kind. Mutates
    ``state.exit_condition_met`` in place when found."""
    if not state.definition.exit_condition_artifact:
        return
    if state.exit_condition_met:
        return
    target_kind = state.definition.exit_condition_artifact
    for u in capture.utterances[artifact_count_before:]:
        for a in u.content.artifacts:
            if a.kind == target_kind:
                state.exit_condition_met = True
                return


# ---------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------


async def run_phased_meeting(
    *,
    meeting: "Meeting",
    runner: "Runner",
    capture: "WorkflowCapture",
    directive: str | None,
    per_item_meetings: dict[str, str],
    current_item_kind: str | None,
    current_item_slug: str | None,
    thread_id: str,
    iteration_index: int | None,
    iteration_total: int | None,
    iteration_label: str | None,
    window_timeout_seconds: float = DEFAULT_WINDOW_TIMEOUT_SECONDS,
    phase_event_writer: PhaseEventWriter | None = None,
) -> AsyncIterator[Any]:
    """Drive one phased meeting end-to-end.

    Drop-in replacement for ``_convene_one`` when ``meeting.phases``
    is non-empty. Yields the same workflow-event surface plus phase
    events; ``run_workflow`` filters out the trailing
    ``_OutcomeSentinel`` per its existing convention.
    """
    # Local imports to avoid the workflow ↔ meeting circular at
    # module-load time (workflow.py also imports run_phased_meeting).
    from wonderland.runner import RunnerEvent
    from wonderland.workflow import (
        MeetingEndEvent,
        MeetingStartEvent,
        _OutcomeSentinel,
        resolve_seeds,
    )

    seeds = resolve_seeds(
        meeting.seeds,
        capture,
        per_item_meetings=per_item_meetings,
        current_item_kind=current_item_kind,
        current_item_slug=current_item_slug,
    )

    convenor_directive = (
        directive if directive is not None else meeting.convenor_directive
    )
    if iteration_label is not None and iteration_total:
        if meeting.name:
            header = (
                f"**{meeting.label} — {meeting.name}** "
                f"(iteration {iteration_index}/{iteration_total}: "
                f"{iteration_label})"
            )
        else:
            header = (
                f"**{meeting.label}** "
                f"(iteration {iteration_index}/{iteration_total}: "
                f"{iteration_label})"
            )
    elif meeting.name:
        header = f"**{meeting.label} — {meeting.name}.**"
    else:
        header = f"**{meeting.label}.**"
    convenor_directive = f"{header}\n\n{convenor_directive}"

    cost_before = runner.total_cost
    calls_before = runner.telemetry.call_count
    artifact_count_before = len(capture.utterances)
    meeting_start = time.monotonic()

    yield MeetingStartEvent(
        meeting=meeting,
        seeds=seeds,
        thread_id=thread_id,
        iteration_index=iteration_index,
        iteration_total=iteration_total,
        iteration_label=iteration_label,
    )

    # Suspend each cast member's autonomous deliberation. The
    # orchestrator drives all deliberate() calls in this meeting;
    # background listen() loops still record bus traffic to memory
    # so the agents see context but don't auto-respond. The
    # ``_orchestrator_owned`` attribute is the gate; agents that
    # don't have it (e.g. test fakes) are no-ops.
    for agent_name in meeting.roster:
        agent = runner.agents.get(agent_name)
        if agent is not None:
            setattr(agent, "_orchestrator_owned", True)

    runner._completed = False

    await runner.convene(
        thread_id=thread_id,
        goal=meeting.goal,
        roster=meeting.roster,
        seed_utterances=seeds,
        convenor_directive=convenor_directive,
    )

    outcome = "RUNNING"

    try:
        for phase_spec in meeting.phases:
            phase_def = phase_spec.to_phase_definition()
            cast = tuple(meeting.roster)
            state = PhaseState(definition=phase_def, cast=cast)

            phase_start = PhaseStartEvent(
                thread_id=thread_id,
                phase=phase_def,
                cast=cast,
            )
            if phase_event_writer is not None:
                await phase_event_writer(phase_start)
            yield phase_start

            meeting_budget_hit = False

            # Local helper: Identity → AgentIdentity coercion. Real
            # agents store ``Identity`` (constitution-carrying); test
            # fakes hand back ``AgentIdentity`` directly. The
            # ``as_agent_identity`` method exists on the former.
            def _aid(identity: Any) -> Any:
                if hasattr(identity, "as_agent_identity"):
                    return identity.as_agent_identity()
                return identity

            dodo_aid = _aid(runner.dodo.identity)

            # Per-window deliberation helper. Wraps the per-agent
            # compose_context + deliberate + timeout pattern so the
            # team window can run all members concurrently via
            # asyncio.gather.
            async def _deliberate_window(
                agent_id: str, window_open: Utterance
            ) -> Utterance | None:
                target = runner.agents[agent_id]
                try:
                    context = await target.compose_context([window_open])
                    return await asyncio.wait_for(
                        target.deliberate(context),
                        timeout=window_timeout_seconds,
                    )
                except (asyncio.TimeoutError, TimeoutError):
                    return None

            while not state.is_complete():
                # Meeting budget gate (Decision 4).
                if meeting.meeting_budget is not None:
                    if (
                        runner.total_cost - cost_before
                        >= meeting.meeting_budget
                    ):
                        outcome = "MEETING_BUDGET"
                        meeting_budget_hit = True
                        break

                team = state.next_team()
                # is_complete() returned False, so next_team is set.
                assert team is not None
                rotation_idx = state.current_rotation
                base_window_idx = state.windows_opened

                # ---- Open the team window ----
                # Publish window-open utterances + emit
                # PriorityWindowOpenEvents for each team member
                # before any deliberation runs. Deliberation then
                # happens concurrently for all members of the team.
                # In single-agent teams (the default when
                # team_groupings is empty), this collapses to the
                # original P9 behavior.
                window_opens: list[Utterance] = []
                for team_offset, agent_id in enumerate(team):
                    window_idx = base_window_idx + team_offset
                    pwo_evt = PriorityWindowOpenEvent(
                        thread_id=thread_id,
                        phase_name=phase_def.name,
                        agent_id=agent_id,
                        rotation_index=rotation_idx,
                        window_index=window_idx,
                    )
                    if phase_event_writer is not None:
                        await phase_event_writer(pwo_evt)
                    yield pwo_evt

                    target_aid = _aid(runner.agents[agent_id].identity)
                    window_open = _build_window_open_utterance(
                        thread_id=thread_id,
                        phase_name=phase_def.name,
                        agent_id=agent_id,
                        dodo_identity=dodo_aid,
                        target_identity=target_aid,
                    )
                    await runner.bus.publish(window_open)
                    window_opens.append(window_open)
                    yield RunnerEvent(
                        kind="utterance",
                        elapsed=time.monotonic() - meeting_start,
                        payload={"utterance": window_open},
                    )

                # ---- Concurrent team deliberation ----
                # asyncio.gather lets all team members deliberate at
                # once. Wall-clock for the team window =
                # max(member_deliberations) + small serialization
                # overhead for the per-member publish + event emit
                # below. This is the Two-Headed Giant
                # parallelism-recovery (analysis 034 F2 / P9.5).
                # return_exceptions=True so a single member's
                # failure doesn't poison the rest of the team.
                results = await asyncio.gather(
                    *[
                        _deliberate_window(agent_id, window_opens[i])
                        for i, agent_id in enumerate(team)
                    ],
                    return_exceptions=True,
                )

                # ---- Resolve windows in cast order ----
                # Even though deliberations completed in arbitrary
                # order via gather, we publish + emit in cast order
                # so the bus transcript and event stream are
                # deterministic regardless of LLM call timing.
                for team_offset, (agent_id, raw_response) in enumerate(
                    zip(team, results)
                ):
                    response: Utterance | None
                    if isinstance(raw_response, BaseException):
                        # Treat raised exceptions as PASS — the
                        # window slot is consumed, and the §VIII
                        # observability still counts a window even
                        # when the agent's deliberation crashed.
                        response = None
                    else:
                        response = raw_response

                    action = _classify_response(response)

                    if action == WindowAction.ACTED:
                        assert response is not None
                        await runner.bus.publish(response)
                        capture.observe(response)
                        state.outcomes.append(
                            WindowOutcome(
                                rotation_index=rotation_idx,
                                agent_id=agent_id,
                                action=WindowAction.ACTED,
                                utterance_id=response.id,
                            )
                        )
                        yield RunnerEvent(
                            kind="utterance",
                            elapsed=time.monotonic() - meeting_start,
                            payload={"utterance": response},
                        )
                        act_evt = AgentActEvent(
                            thread_id=thread_id,
                            phase_name=phase_def.name,
                            agent_id=agent_id,
                            rotation_index=rotation_idx,
                            utterance_id=response.id,
                        )
                        if phase_event_writer is not None:
                            await phase_event_writer(act_evt)
                        yield act_evt
                    else:
                        pass_reason: str | None = None
                        if response is not None:
                            await runner.bus.publish(response)
                            capture.observe(response)
                            pass_reason = response.content.body or None
                            yield RunnerEvent(
                                kind="utterance",
                                elapsed=time.monotonic() - meeting_start,
                                payload={"utterance": response},
                            )
                        state.outcomes.append(
                            WindowOutcome(
                                rotation_index=rotation_idx,
                                agent_id=agent_id,
                                action=WindowAction.PASSED,
                            )
                        )
                        pass_evt = AgentPassEvent(
                            thread_id=thread_id,
                            phase_name=phase_def.name,
                            agent_id=agent_id,
                            rotation_index=rotation_idx,
                            reason=pass_reason,
                        )
                        if phase_event_writer is not None:
                            await phase_event_writer(pass_evt)
                        yield pass_evt

                # Exit condition checked once per team window — any
                # member's act could have shipped the artifact.
                _check_exit_condition(
                    state=state,
                    capture=capture,
                    artifact_count_before=artifact_count_before,
                )

                # Rotation boundary — fires when all teams in this
                # rotation have had a window. windows_opened modulo
                # cast size catches this regardless of team shape
                # (sum of team sizes per rotation = len(cast)).
                if state.windows_opened % len(cast) == 0:
                    rot_evt = RotationCompleteEvent(
                        thread_id=thread_id,
                        phase_name=phase_def.name,
                        rotation_index=rotation_idx,
                    )
                    if phase_event_writer is not None:
                        await phase_event_writer(rot_evt)
                    yield rot_evt

            phase_end = PhaseEndEvent(
                thread_id=thread_id,
                phase_name=phase_def.name,
                reason=_phase_end_reason(
                    state=state,
                    meeting_budget_hit=meeting_budget_hit,
                ),
                rotations_used=state.current_rotation,
                total_windows=state.windows_opened,
                passes_per_agent=state.passes_per_agent(),
                acts_per_agent=state.acts_per_agent(),
            )
            if phase_event_writer is not None:
                await phase_event_writer(phase_end)
            yield phase_end

            if meeting_budget_hit:
                break

        if outcome == "RUNNING":
            outcome = "COMPLETE"
    finally:
        for agent_name in meeting.roster:
            agent = runner.agents.get(agent_name)
            if agent is not None:
                setattr(agent, "_orchestrator_owned", False)

    if outcome in ("MEETING_BUDGET", "TIMEOUT", "ABORTED"):
        runner.mark_thread_complete(
            thread_id, f"meeting ended via {outcome}"
        )

    elapsed = time.monotonic() - meeting_start
    calls_delta = runner.telemetry.call_count - calls_before
    cost_delta = runner.total_cost - cost_before
    new_utterances = capture.utterances[artifact_count_before:]
    kinds_count: dict[str, int] = {}
    for u in new_utterances:
        for a in u.content.artifacts:
            kinds_count[a.kind] = kinds_count.get(a.kind, 0) + 1

    yield MeetingEndEvent(
        meeting=meeting,
        outcome=outcome,
        elapsed_s=elapsed,
        calls_delta=calls_delta,
        cost_delta=cost_delta,
        artifact_kinds=kinds_count,
        thread_id=thread_id,
        iteration_index=iteration_index,
        iteration_total=iteration_total,
        iteration_label=iteration_label,
    )

    yield _OutcomeSentinel(outcome=outcome)


__all__ = [
    "AgentActEvent",
    "AgentPassEvent",
    "DEFAULT_WINDOW_TIMEOUT_SECONDS",
    "PhaseEndEvent",
    "PhaseEvent",
    "PhaseEventWriter",
    "PhaseStartEvent",
    "PriorityWindowOpenEvent",
    "RotationCompleteEvent",
    "deserialize_phase_event",
    "jsonl_phase_event_writer",
    "read_phase_events",
    "run_phased_meeting",
    "serialize_phase_event",
]
