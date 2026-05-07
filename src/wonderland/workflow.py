"""Workflow — meeting-chain templates as data on disk.

A workflow declares an ordered sequence of meetings: who's in the
room, what their convener tells them, how the meeting is seeded
from prior meetings' artifacts, and what budget cap it gets. The
canonical 5-meeting sequence (scoping → decomposition → contract
negotiation → implementation → review) lives at
``closet/workflows/canonical.yaml`` and is the baseline for
roadmap ``29497820`` (Dodo as dynamic meeting orchestrator).

Why data-on-disk rather than Python:

- Dodo's eventual job is to compose workflows on the fly. Composing
  a YAML doc is much cheaper than generating + ``exec``-ing Python.
- Different feature flows want different sequences (canonical for
  greenfield-on-skeleton, TDD with separated test-write/test-pass,
  spike workflows, hotfix workflows). Multiple named files instead
  of one big Python switch.
- Workflows can be inspected, diffed, and reviewed like any other
  artifact.

This module defines the schema (Pydantic models) + the loader
(``load_workflow``). Execution lives at ``Workflow.run`` (planned —
landing alongside the T38 refactor).
"""

from __future__ import annotations

import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from wonderland.runner import Runner
    from wonderland.utterance import Utterance


class SeedBinding(BaseModel):
    """How to seed a meeting from prior meetings' artifacts.

    Resolved at runtime by the Workflow runner: it looks at the named
    prior meeting's captured utterances, filters by ``kinds``, applies
    optional ``where`` payload-match, applies ``limit``, and falls back
    to the unfiltered set if ``fallback: any`` and the strict filter
    yielded nothing.

    Example:

        seeds:
          - from: contract-negotiation
            kinds: [contract_note]
            where: {state: agreed}
            fallback: any   # if no agreed contracts, send all proposed
    """

    model_config = ConfigDict(populate_by_name=True)

    from_meeting: str = Field(
        alias="from",
        description=(
            "Meeting id to draw seeds from. Use 'any' to draw from any "
            "prior meeting that produced matching artifacts."
        ),
    )
    kinds: list[str] = Field(description="Artifact kinds to filter by, e.g. ['adr', 'story'].")
    where: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Payload key→value match. Each artifact's payload must contain "
            "every key with the matching value to pass."
        ),
    )
    limit: int | None = Field(
        default=None,
        description="Take only the first N matching seeds. None = no limit.",
    )
    fallback: str | None = Field(
        default=None,
        description=(
            "Behavior when filtering yields zero seeds. 'any' = drop the "
            "where clause and send unfiltered matching-kind utterances. "
            "None = empty seed set is fine."
        ),
    )


class Meeting(BaseModel):
    """One meeting in a workflow."""

    id: str = Field(description="Stable thread_id for this meeting (e.g. 'scoping').")
    label: str = Field(description="Display label (e.g. 'M1').")
    name: str | None = Field(
        default=None,
        description=(
            "Optional book-event name (e.g. 'The Caucus Race'). The "
            "framework's character-shaped substrate makes pure numeric "
            "labels feel sterile; named meetings make the literary "
            "structure legible in logs and analyses. Numeric labels "
            "remain authoritative for sequencing."
        ),
    )
    goal: str = Field(description="One-line statement of what the meeting produces.")
    roster: list[str] = Field(
        description="Agent names invited. Dodo is added automatically by the runner."
    )
    convenor_directive: str = Field(
        default="",
        description=(
            "What Dodo says when convening. Empty for the entry (first) "
            "meeting — the runtime passes the user's directive through "
            "verbatim there."
        ),
    )
    meeting_budget: float | None = Field(
        default=None,
        description="Per-meeting $ cap. None = no per-meeting cap (global cap still applies).",
    )
    seeds: list[SeedBinding] = Field(
        default_factory=list,
        description="How to seed this meeting from prior meetings' artifacts.",
    )


class WorkflowDefaults(BaseModel):
    """Runtime defaults the workflow recommends. Caller may override."""

    budget_dollars: float | None = None
    timeout_seconds: float | None = None
    quiescence_seconds: float | None = None


class Workflow(BaseModel):
    """A complete workflow — name, description, ordered meetings."""

    name: str
    description: str
    version: int = 1
    defaults: WorkflowDefaults = Field(default_factory=WorkflowDefaults)
    meetings: list[Meeting]

    def meeting_by_id(self, meeting_id: str) -> Meeting | None:
        """Look up a meeting by id; None if not present."""
        for m in self.meetings:
            if m.id == meeting_id:
                return m
        return None

    @property
    def entry_meeting(self) -> Meeting:
        """The first meeting — receives the user's runtime directive."""
        if not self.meetings:
            raise ValueError(f"workflow {self.name!r} has no meetings")
        return self.meetings[0]


def workflows_dir() -> Path:
    """Directory holding the bundled workflow YAML files."""
    import wonderland

    return Path(wonderland.__file__).parent / "closet" / "workflows"


def load_workflow(name_or_path: str | Path) -> Workflow:
    """Load a workflow by name or path.

    - ``load_workflow("canonical")`` — looks for
      ``closet/workflows/canonical.yaml`` next to the wonderland
      package.
    - ``load_workflow(Path("/abs/path/to/my.yaml"))`` — loads from
      an absolute path. Useful for tests + project-local workflow
      overrides.
    """
    if isinstance(name_or_path, Path):
        path = name_or_path
    elif "/" in name_or_path or name_or_path.endswith(".yaml"):
        path = Path(name_or_path)
    else:
        path = workflows_dir() / f"{name_or_path}.yaml"

    if not path.is_file():
        available = sorted(p.stem for p in workflows_dir().glob("*.yaml"))
        raise FileNotFoundError(
            f"workflow not found: {path}. Bundled workflows: {available}"
        )
    with path.open() as f:
        data = yaml.safe_load(f)
    return Workflow.model_validate(data)


def list_workflows() -> list[str]:
    """Names of bundled workflows (without the .yaml extension)."""
    return sorted(p.stem for p in workflows_dir().glob("*.yaml"))


# ---------------------------------------------------------------------------
# Execution — runs a workflow against a Runner
# ---------------------------------------------------------------------------


@dataclass
class WorkflowCapture:
    """Accumulates substantive utterances across meetings so prior-meeting
    artifacts can seed follow-up meetings.

    Mirrors the ad-hoc Capture pattern from the T38 scripts but adds
    per-meeting indexing — seed bindings can ask for utterances from a
    *specific* prior meeting (the from: field), not just any prior turn.
    """

    utterances: list[Utterance] = field(default_factory=list)

    def observe(self, u: Utterance) -> None:
        # Only keep utterances that carried artifacts (the substantive ones).
        # The seed needs to carry the artifact; we don't need every concern.
        if u.content.artifacts:
            self.utterances.append(u)

    def utterances_for(self, meeting_id: str) -> list[Utterance]:
        """Captured utterances whose thread_id matches the meeting id.

        Per the canonical convention, meeting.id IS the thread_id used
        when convening — so this is a direct filter, no extra mapping
        needed.
        """
        return [u for u in self.utterances if u.thread_id == meeting_id]


def resolve_seeds(
    bindings: list[SeedBinding],
    capture: WorkflowCapture,
) -> list[Utterance]:
    """Apply seed-binding rules to produce the seed utterance list for
    a meeting. Mirrors the hand-rolled filtering in T38 scripts.

    For each binding:
      1. Pick candidates: utterances from the named prior meeting, OR
         all captured utterances when ``from: any``.
      2. Filter by ``kinds`` — keep utterances carrying at least one
         artifact of a matching kind.
      3. Apply ``where`` — payload key→value match against the matching
         artifact's payload. If filter yields zero AND ``fallback: any``,
         drop the where clause.
      4. Apply ``limit`` — keep first N.

    Bindings are processed in order; the union of their results becomes
    the seed list, deduplicated by utterance id.
    """
    out: list[Utterance] = []
    seen_ids: set[str] = set()
    for binding in bindings:
        if binding.from_meeting == "any":
            candidates = capture.utterances
        else:
            candidates = capture.utterances_for(binding.from_meeting)

        kinded = [
            u
            for u in candidates
            if any(a.kind in binding.kinds for a in u.content.artifacts)
        ]

        if binding.where:
            filtered = [
                u
                for u in kinded
                if any(
                    a.kind in binding.kinds
                    and all(a.payload.get(k) == v for k, v in binding.where.items())
                    for a in u.content.artifacts
                )
            ]
            if not filtered and binding.fallback == "any":
                filtered = kinded
        else:
            filtered = kinded

        if binding.limit is not None:
            filtered = filtered[: binding.limit]

        for u in filtered:
            if u.id not in seen_ids:
                seen_ids.add(u.id)
                out.append(u)

    return out


@dataclass
class MeetingStartEvent:
    """Emitted by run_workflow before convening each meeting."""

    meeting: Meeting
    seeds: list[Utterance]


@dataclass
class MeetingEndEvent:
    """Emitted by run_workflow after each meeting terminates. The
    outcome is one of: COMPLETE, MEETING_BUDGET, GLOBAL_BUDGET, TIMEOUT,
    ABORTED."""

    meeting: Meeting
    outcome: str
    elapsed_s: float
    calls_delta: int
    cost_delta: float
    artifact_kinds: dict[str, int]


# Type alias for the union of events the workflow runner yields.
# The full union (including RunnerEvent from runner.py) is documented
# but we keep the runtime annotation as `Any` to avoid the runner
# import dependency at module load time.



async def run_workflow(
    workflow: Workflow,
    runner: Runner,
    directive: str,
) -> AsyncIterator[Any]:
    """Drive a workflow against a started Runner. Async generator
    yielding MeetingStartEvent / MeetingEndEvent / RunnerEvent.

    Caller is responsible for runner setup and teardown:

        runner = await Runner.make_full_cast(project_root, ...)
        await runner.setup()
        try:
            workflow = load_workflow("canonical")
            async for event in run_workflow(workflow, runner, DIRECTIVE):
                # render event, accumulate stats, etc.
                ...
        finally:
            await runner.teardown()

    Stops on global-budget exhaustion. Per-meeting budget exhaustion ends
    the meeting and emits MeetingEndEvent(outcome='MEETING_BUDGET') but
    the workflow continues to the next meeting (the caller may also
    short-circuit if it sees the global budget tightening).
    """
    capture = WorkflowCapture()

    for meeting in workflow.meetings:
        seeds = resolve_seeds(meeting.seeds, capture)
        is_entry = meeting is workflow.entry_meeting
        convenor_directive = directive if is_entry else meeting.convenor_directive

        # Surface the meeting name to the team. The character-shaped
        # substrate principle says the literary parallel should be
        # load-bearing, not ornamental — but it can't shape agent
        # deliberation if agents can't see it. The Dodo-relayed
        # directive is the team's first utterance on every thread, so
        # prefixing it with the meeting label and (optional) book-event
        # name puts the framing in the team's context window.
        if meeting.name:
            convenor_directive = (
                f"**{meeting.label} — {meeting.name}.**\n\n{convenor_directive}"
            )
        else:
            convenor_directive = f"**{meeting.label}.**\n\n{convenor_directive}"

        cost_before = runner.total_cost
        calls_before = runner.telemetry.call_count
        artifact_count_before = len(capture.utterances)
        meeting_start = time.monotonic()

        yield MeetingStartEvent(meeting=meeting, seeds=seeds)

        # Reset per-thread completion tracking so the runner can fire
        # complete again for this new thread.
        runner._completed = False

        await runner.convene(
            thread_id=meeting.id,
            goal=meeting.goal,
            roster=meeting.roster,
            seed_utterances=seeds,
            convenor_directive=convenor_directive,
        )

        outcome = "RUNNING"
        # Pass meeting.id as terminal_thread_id so events() only auto-
        # returns on a `complete` event for *this* meeting. Stale
        # completes from prior meetings (e.g. M(N-1)'s
        # mark_thread_complete) are yielded for capture but don't end
        # the loop. Without this, a leaked complete event ends M(N)'s
        # events loop before any agent deliberates — see analysis 030.
        async for event in runner.events(terminal_thread_id=meeting.id):
            if event.kind == "utterance":
                capture.observe(event.payload["utterance"])

            yield event

            if event.kind == "budget_exceeded":
                outcome = "GLOBAL_BUDGET"
                break

            # Per-meeting budget cap — soft, but ends the meeting early.
            if meeting.meeting_budget is not None:
                spent = runner.total_cost - cost_before
                if spent >= meeting.meeting_budget:
                    outcome = "MEETING_BUDGET"
                    break

            if event.kind == "complete":
                # `complete` events carry a thread_id in their payload;
                # only end this meeting if the event is for *this*
                # meeting's thread. Without this filter, a leftover
                # COMPLETE event from a prior meeting (e.g., emitted by
                # mark_thread_complete on the prior meeting's
                # MEETING_BUDGET exit) leaks into this meeting's events
                # loop and ends it before any agent has had a chance to
                # deliberate. This was the actual root cause of the
                # 0-calls / 0-cost M5 pattern in analyses 026 and 027 —
                # not the quiescence-on-startup race the prior fix
                # targeted (which was real but downstream of this).
                event_thread_id = (event.payload or {}).get("thread_id")
                if event_thread_id is not None and event_thread_id != meeting.id:
                    continue
                outcome = "COMPLETE"
                break

            if event.kind in ("timeout", "aborted"):
                # Global runner events — no thread_id, end the workflow
                # regardless of which meeting is currently running.
                outcome = event.kind.upper()
                break

        # If the meeting exited via a non-COMPLETE terminal outcome, the
        # convenor never sent the acknowledgment that would transition
        # the thread to COMPLETE. Force the transition so any agent
        # whose deliberate() is still in flight gets its late publish
        # suppressed by the runner's late-publish guard rather than
        # landing on an abandoned thread.
        if outcome in ("MEETING_BUDGET", "TIMEOUT", "ABORTED"):
            runner.mark_thread_complete(meeting.id, f"meeting ended via {outcome}")

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
        )

        if outcome == "GLOBAL_BUDGET":
            return


__all__ = [
    "Meeting",
    "MeetingEndEvent",
    "MeetingStartEvent",
    "SeedBinding",
    "Workflow",
    "WorkflowCapture",
    "WorkflowDefaults",
    "list_workflows",
    "load_workflow",
    "resolve_seeds",
    "run_workflow",
    "workflows_dir",
]
