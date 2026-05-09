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
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass
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


@dataclass(frozen=True)
class PriorityWindowOpenEvent:
    """Priority just passed to ``agent_id`` for one window."""

    thread_id: str
    phase_name: str
    agent_id: str
    rotation_index: int
    window_index: int


@dataclass(frozen=True)
class AgentActEvent:
    """The agent used their priority window to emit an utterance."""

    thread_id: str
    phase_name: str
    agent_id: str
    rotation_index: int
    utterance_id: str


@dataclass(frozen=True)
class AgentPassEvent:
    """The agent declined their priority window."""

    thread_id: str
    phase_name: str
    agent_id: str
    rotation_index: int
    reason: str | None = None


@dataclass(frozen=True)
class RotationCompleteEvent:
    """A full rotation around the cast just finished — boundary
    event for UI rendering."""

    thread_id: str
    phase_name: str
    rotation_index: int


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

            yield PhaseStartEvent(
                thread_id=thread_id,
                phase=phase_def,
                cast=cast,
            )

            meeting_budget_hit = False

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

                next_agent_id = state.next_agent()
                # is_complete() returned False, so next_agent is set.
                assert next_agent_id is not None
                window_idx = state.windows_opened
                rotation_idx = state.current_rotation

                yield PriorityWindowOpenEvent(
                    thread_id=thread_id,
                    phase_name=phase_def.name,
                    agent_id=next_agent_id,
                    rotation_index=rotation_idx,
                    window_index=window_idx,
                )

                target_agent = runner.agents[next_agent_id]
                # ``runner.dodo.identity`` and ``agent.identity`` are
                # ``Identity`` objects (the heavyweight constitution-
                # carrying form). Utterance speakers/recipients use
                # the lightweight ``AgentIdentity`` (name +
                # constitution_version) — the conversion lives on
                # Identity.
                dodo_aid = (
                    runner.dodo.identity.as_agent_identity()
                    if hasattr(runner.dodo.identity, "as_agent_identity")
                    else runner.dodo.identity
                )
                target_aid = (
                    target_agent.identity.as_agent_identity()
                    if hasattr(target_agent.identity, "as_agent_identity")
                    else target_agent.identity
                )
                window_open = _build_window_open_utterance(
                    thread_id=thread_id,
                    phase_name=phase_def.name,
                    agent_id=next_agent_id,
                    dodo_identity=dodo_aid,
                    target_identity=target_aid,
                )
                await runner.bus.publish(window_open)
                yield RunnerEvent(
                    kind="utterance",
                    elapsed=time.monotonic() - meeting_start,
                    payload={"utterance": window_open},
                )

                # Drive deliberation directly.
                response: Utterance | None
                try:
                    context = await target_agent.compose_context(
                        [window_open]
                    )
                    response = await asyncio.wait_for(
                        target_agent.deliberate(context),
                        timeout=window_timeout_seconds,
                    )
                except (asyncio.TimeoutError, TimeoutError):
                    response = None

                action = _classify_response(response)

                if action == WindowAction.ACTED:
                    assert response is not None
                    await runner.bus.publish(response)
                    capture.observe(response)
                    state.outcomes.append(
                        WindowOutcome(
                            rotation_index=rotation_idx,
                            agent_id=next_agent_id,
                            action=WindowAction.ACTED,
                            utterance_id=response.id,
                        )
                    )
                    yield RunnerEvent(
                        kind="utterance",
                        elapsed=time.monotonic() - meeting_start,
                        payload={"utterance": response},
                    )
                    yield AgentActEvent(
                        thread_id=thread_id,
                        phase_name=phase_def.name,
                        agent_id=next_agent_id,
                        rotation_index=rotation_idx,
                        utterance_id=response.id,
                    )
                else:
                    pass_reason: str | None = None
                    if response is not None:
                        # Agent emitted PASS explicitly — publish it
                        # so the meeting record carries the rationale.
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
                            agent_id=next_agent_id,
                            action=WindowAction.PASSED,
                        )
                    )
                    yield AgentPassEvent(
                        thread_id=thread_id,
                        phase_name=phase_def.name,
                        agent_id=next_agent_id,
                        rotation_index=rotation_idx,
                        reason=pass_reason,
                    )

                _check_exit_condition(
                    state=state,
                    capture=capture,
                    artifact_count_before=artifact_count_before,
                )

                # Rotation boundary — emit RotationCompleteEvent at
                # the end of every full pass (regardless of how the
                # rotation concluded).
                if (window_idx + 1) % len(cast) == 0:
                    yield RotationCompleteEvent(
                        thread_id=thread_id,
                        phase_name=phase_def.name,
                        rotation_index=rotation_idx,
                    )

            yield PhaseEndEvent(
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
    "PhaseStartEvent",
    "PriorityWindowOpenEvent",
    "RotationCompleteEvent",
    "run_phased_meeting",
]
