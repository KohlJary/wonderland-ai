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
    per_item: str | None = Field(
        default=None,
        description=(
            "If set, this meeting runs once per artifact of the named kind "
            "from prior meetings (e.g. ``per_item: feature``). The runner "
            "convenes the meeting N times, with iteration thread_ids of the "
            "form ``{meeting.id}-{item.slug}``. Seed bindings whose kinds "
            "include the per_item kind get sliced to just the current item; "
            "bindings whose ``from`` references another per_item meeting "
            "get sliced to the iteration thread that matches the current "
            "item's slug. Used to scope expensive meetings (e.g. M4/M5 in "
            "TDD-serial) to one feature at a time rather than fanning out "
            "across all features in a single shot."
        ),
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
    *,
    per_item_meetings: dict[str, str] | None = None,
    current_item_kind: str | None = None,
    current_item_slug: str | None = None,
) -> list[Utterance]:
    """Apply seed-binding rules to produce the seed utterance list for
    a meeting. Mirrors the hand-rolled filtering in T38 scripts.

    For each binding:
      1. Pick candidates:
         - ``from: any`` → all captured utterances.
         - ``from: <id>`` where the named meeting was per_item → all
           utterances whose thread_id starts with ``<id>-`` (across all
           iterations); if we're currently in a per_item iteration,
           additionally slice to the iteration thread_id matching the
           current item's slug when that thread has matching artifacts.
         - otherwise → utterances captured under that exact thread_id.
      2. Filter by ``kinds`` — keep utterances carrying at least one
         artifact of a matching kind.
      3. If we're currently in a per_item iteration AND the binding's
         ``kinds`` include the iteration kind, slice to artifacts whose
         payload slug matches the current item's slug. This is the rule
         that gives M4 iteration N just feature N's spec rather than all
         of them.
      4. Apply ``where`` — payload key→value match against the matching
         artifact's payload. If filter yields zero AND ``fallback: any``,
         drop the where clause.
      5. Apply ``limit`` — keep first N.

    Bindings are processed in order; the union of their results becomes
    the seed list, deduplicated by utterance id.

    ``per_item_meetings`` maps meeting_id → per_item kind for every
    meeting in the workflow that uses per_item. ``current_item_kind`` /
    ``current_item_slug`` describe the iteration the caller is currently
    inside (None when the meeting is not per_item).
    """
    per_item_meetings = per_item_meetings or {}
    out: list[Utterance] = []
    seen_ids: set[str] = set()
    for binding in bindings:
        if binding.from_meeting == "any":
            candidates = capture.utterances
        elif binding.from_meeting in per_item_meetings:
            # Source meeting was per_item — gather utterances from any
            # of its iteration threads (thread_ids prefixed with
            # ``<meeting_id>-``).
            prefix = f"{binding.from_meeting}-"
            candidates = [u for u in capture.utterances if u.thread_id.startswith(prefix)]
            # If we're currently in a per_item iteration, slice to the
            # paired iteration's thread_id when present. Falls through
            # to the full per_item-meeting candidate set if no exact
            # match (e.g., the paired iteration produced no artifacts).
            if current_item_slug is not None:
                paired_thread_id = f"{binding.from_meeting}-{current_item_slug}"
                paired = [u for u in candidates if u.thread_id == paired_thread_id]
                if paired:
                    candidates = paired
        else:
            candidates = capture.utterances_for(binding.from_meeting)

        kinded = [
            u
            for u in candidates
            if any(a.kind in binding.kinds for a in u.content.artifacts)
        ]

        # If we're inside a per_item iteration AND this binding pulls
        # the iteration kind, slice to the current item's payload slug.
        # Without this, M4 iteration N would see every feature in its
        # context, not just feature N.
        #
        # Two-step slice: (1) drop utterances whose iteration-kind
        # artifacts don't match the slug; (2) for the kept utterances,
        # rewrite their artifact list to keep only iteration-kind
        # artifacts matching the current slug (other kinds pass through
        # untouched). The rewrite step matters when one utterance
        # carries multiple iteration-kind artifacts (e.g., Rabbit ships
        # all six features in one M2.5 utterance) — without it the
        # iteration sees every feature in its context.
        if (
            current_item_kind is not None
            and current_item_slug is not None
            and current_item_kind in binding.kinds
        ):
            sliced: list[Utterance] = []
            for u in kinded:
                matching = [
                    a
                    for a in u.content.artifacts
                    if a.kind == current_item_kind
                    and a.payload.get("slug") == current_item_slug
                ]
                if not matching:
                    continue
                kept = [
                    a
                    for a in u.content.artifacts
                    if a.kind != current_item_kind
                    or a.payload.get("slug") == current_item_slug
                ]
                if len(kept) == len(u.content.artifacts):
                    sliced.append(u)
                else:
                    sliced.append(
                        u.model_copy(
                            update={
                                "content": u.content.model_copy(
                                    update={"artifacts": kept}
                                )
                            }
                        )
                    )
            kinded = sliced

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
    """Emitted by run_workflow before convening each meeting.

    For per_item meetings, one event fires per iteration. ``thread_id``
    is the actual bus thread the meeting convened on (``meeting.id``
    for non-per_item meetings; ``{meeting.id}-{item.slug}`` for
    iterations). ``iteration_index`` / ``iteration_total`` /
    ``iteration_label`` are populated for per_item iterations and None
    otherwise.
    """

    meeting: Meeting
    seeds: list[Utterance]
    thread_id: str | None = None
    iteration_index: int | None = None
    iteration_total: int | None = None
    iteration_label: str | None = None


@dataclass
class MeetingEndEvent:
    """Emitted by run_workflow after each meeting terminates. The
    outcome is one of: COMPLETE, MEETING_BUDGET, GLOBAL_BUDGET, TIMEOUT,
    ABORTED. Same iteration fields as MeetingStartEvent for per_item
    meetings."""

    meeting: Meeting
    outcome: str
    elapsed_s: float
    calls_delta: int
    cost_delta: float
    artifact_kinds: dict[str, int]
    thread_id: str | None = None
    iteration_index: int | None = None
    iteration_total: int | None = None
    iteration_label: str | None = None


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

    Per_item meetings (e.g., M4/M5 in tdd-serial) are convened once per
    matching artifact found in the capture. Each iteration emits its own
    MeetingStart/MeetingEnd events with iteration metadata populated.
    """
    capture = WorkflowCapture()

    # Map of meeting_id → per_item kind for every per_item meeting.
    # Used by resolve_seeds to know when to look across iteration
    # threads vs a single thread_id.
    per_item_meetings: dict[str, str] = {
        m.id: m.per_item for m in workflow.meetings if m.per_item is not None
    }

    for meeting in workflow.meetings:
        is_entry = meeting is workflow.entry_meeting

        if meeting.per_item is None:
            outcome = "RUNNING"
            async for event in _convene_one(
                meeting=meeting,
                runner=runner,
                capture=capture,
                directive=directive if is_entry else None,
                per_item_meetings=per_item_meetings,
                current_item_kind=None,
                current_item_slug=None,
                thread_id=meeting.id,
                iteration_index=None,
                iteration_total=None,
                iteration_label=None,
            ):
                if isinstance(event, _OutcomeSentinel):
                    outcome = event.outcome
                    continue
                yield event
            if outcome == "GLOBAL_BUDGET":
                return
            continue

        # Per_item meeting — find every artifact of the iteration kind
        # already captured, dedupe by slug, convene once per item.
        items: list[dict[str, Any]] = []
        seen_slugs: set[str] = set()
        for u in capture.utterances:
            for a in u.content.artifacts:
                if a.kind != meeting.per_item:
                    continue
                slug = a.payload.get("slug")
                if not slug or slug in seen_slugs:
                    continue
                seen_slugs.add(slug)
                items.append(a.payload)

        if not items:
            # Nothing to iterate over — emit a synthetic skip so the
            # consumer sees the meeting was acknowledged. Fail-loud
            # rather than silently eating the meeting.
            yield MeetingStartEvent(
                meeting=meeting,
                seeds=[],
                thread_id=meeting.id,
                iteration_index=0,
                iteration_total=0,
                iteration_label="(no items)",
            )
            yield MeetingEndEvent(
                meeting=meeting,
                outcome="COMPLETE",
                elapsed_s=0.0,
                calls_delta=0,
                cost_delta=0.0,
                artifact_kinds={},
                thread_id=meeting.id,
                iteration_index=0,
                iteration_total=0,
                iteration_label="(no items)",
            )
            continue

        for idx, item in enumerate(items):
            slug = item["slug"]
            iteration_thread_id = f"{meeting.id}-{slug}"
            label = item.get("title") or slug
            outcome = "RUNNING"
            async for event in _convene_one(
                meeting=meeting,
                runner=runner,
                capture=capture,
                directive=None,  # per_item meetings can't be entry
                per_item_meetings=per_item_meetings,
                current_item_kind=meeting.per_item,
                current_item_slug=slug,
                thread_id=iteration_thread_id,
                iteration_index=idx + 1,
                iteration_total=len(items),
                iteration_label=label,
            ):
                if isinstance(event, _OutcomeSentinel):
                    outcome = event.outcome
                    continue
                yield event
            if outcome == "GLOBAL_BUDGET":
                return


@dataclass
class _OutcomeSentinel:
    """Internal sentinel: ``_convene_one`` yields this as its final
    event so ``run_workflow`` can read the meeting's outcome without
    having to peek at MeetingEndEvent attributes. Filtered out before
    events reach the caller."""

    outcome: str


async def _convene_one(
    *,
    meeting: Meeting,
    runner: Runner,
    capture: WorkflowCapture,
    directive: str | None,
    per_item_meetings: dict[str, str],
    current_item_kind: str | None,
    current_item_slug: str | None,
    thread_id: str,
    iteration_index: int | None,
    iteration_total: int | None,
    iteration_label: str | None,
) -> AsyncIterator[Any]:
    """Convene a single meeting (or one per_item iteration) and drain
    its events. Async iterator; yields MeetingStartEvent, then runner
    events as they fire, then MeetingEndEvent, then a final
    _OutcomeSentinel so the caller knows the final outcome.

    Pulled out of run_workflow so the per_item and plain-meeting paths
    share the convene + event-loop logic without duplication.
    """
    seeds = resolve_seeds(
        meeting.seeds,
        capture,
        per_item_meetings=per_item_meetings,
        current_item_kind=current_item_kind,
        current_item_slug=current_item_slug,
    )

    convenor_directive = directive if directive is not None else meeting.convenor_directive

    # Surface the meeting label, name, and iteration metadata to the
    # team. Iteration label puts the current feature's title into the
    # context window so the agents anchor on it.
    if iteration_label is not None and iteration_total:
        if meeting.name:
            header = (
                f"**{meeting.label} — {meeting.name}** "
                f"(iteration {iteration_index}/{iteration_total}: {iteration_label})"
            )
        else:
            header = (
                f"**{meeting.label}** "
                f"(iteration {iteration_index}/{iteration_total}: {iteration_label})"
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

    # Reset per-thread completion tracking so the runner can fire
    # complete again for this new thread.
    runner._completed = False

    await runner.convene(
        thread_id=thread_id,
        goal=meeting.goal,
        roster=meeting.roster,
        seed_utterances=seeds,
        convenor_directive=convenor_directive,
    )

    outcome = "RUNNING"
    # terminal_thread_id ensures complete events from prior meetings
    # don't end this iteration's loop. See analysis 030.
    async for event in runner.events(terminal_thread_id=thread_id):
        if event.kind == "utterance":
            capture.observe(event.payload["utterance"])

        yield event

        if event.kind == "budget_exceeded":
            outcome = "GLOBAL_BUDGET"
            break

        if meeting.meeting_budget is not None:
            spent = runner.total_cost - cost_before
            if spent >= meeting.meeting_budget:
                outcome = "MEETING_BUDGET"
                break

        if event.kind == "complete":
            event_thread_id = (event.payload or {}).get("thread_id")
            if event_thread_id is not None and event_thread_id != thread_id:
                continue
            outcome = "COMPLETE"
            break

        if event.kind in ("timeout", "aborted"):
            outcome = event.kind.upper()
            break

    if outcome in ("MEETING_BUDGET", "TIMEOUT", "ABORTED"):
        runner.mark_thread_complete(thread_id, f"meeting ended via {outcome}")

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
