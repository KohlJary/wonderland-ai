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
from pydantic import BaseModel, ConfigDict, Field, model_validator

from wonderland.turns import PhaseDefinition

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
    consumed_by: str | None = Field(
        default=None,
        description=(
            "Drop matched utterances whose slug already appears in some "
            "downstream artifact's ``sources:`` list. Used to scope "
            "M2 composition to *uncomposed* stories on cross-run "
            "design passes — once a story has a feature sourcing it, "
            "M2 has no business renegotiating it. Generic over any "
            "(consumed-kind, consumer-kind) pair: stories→features, "
            "features→adrs, etc. None = no consumption filter "
            "(default; legacy seed behavior)."
        ),
    )


class PhaseSpec(BaseModel):
    """Workflow-side declaration of a phase within a meeting.

    Per analysis 033 — phases are sub-units of a meeting; each has
    its own priority rotation and rotation budget. A meeting opts
    into phase-based engine semantics by declaring at least one
    phase here. Meetings with no ``phases:`` declaration run on the
    legacy engagement-policy path (backward compatibility).

    The schema is intentionally minimal — runtime behavior lives
    elsewhere (engine in T58, opt-in workflow YAMLs in T59).
    """

    name: str = Field(
        min_length=1,
        description=(
            "Phase name, unique within the meeting (e.g. 'red-tests', "
            "'settle')."
        ),
    )
    max_rotations: int = Field(
        default=3,
        ge=1,
        description=(
            "Upper bound on full priority rotations within this phase. "
            "Engine-side measurement primitive — never surfaced in "
            "agent context (per the analysis 030 F1 anchoring lesson)."
        ),
    )
    exit_condition_artifact: str | None = Field(
        default=None,
        description=(
            "If set, the phase ends when an artifact of this kind "
            "ships (e.g. ``contract``), even with rotations remaining. "
            "Lets a phase be 'until X is shipped' rather than "
            "'for N rotations.' Validated as a string only — the "
            "runtime checks the kind name against shipped artifacts "
            "directly, no central artifact registry to validate "
            "against."
        ),
    )
    team_groupings: list[list[str]] = Field(
        default_factory=list,
        description=(
            "Two-Headed Giant team partition (analysis 034 F2 / "
            "P9.5). Empty list = one-agent-per-team (each agent "
            "gets their own serial priority window, the original "
            "P9 behavior). Non-empty = explicit teams; agents in "
            "the same team deliberate concurrently within one team "
            "window. Validated against the meeting's roster at the "
            "Meeting level: every cast member must appear in "
            "exactly one team, no overlap, no orphans."
        ),
    )

    @model_validator(mode="after")
    def _validate_team_groupings_no_overlap(self) -> "PhaseSpec":
        """Phase-local check: no agent appears in more than one team
        within this phase. Cast-coverage validation runs at the
        Meeting level."""
        if not self.team_groupings:
            return self
        seen: set[str] = set()
        for team in self.team_groupings:
            if not team:
                raise ValueError(
                    f"phase {self.name!r}: team_groupings cannot "
                    "contain empty teams"
                )
            for member in team:
                if member in seen:
                    raise ValueError(
                        f"phase {self.name!r}: agent {member!r} "
                        "appears in multiple teams"
                    )
                seen.add(member)
        return self

    def to_phase_definition(self) -> PhaseDefinition:
        """Convert the workflow-side spec into the engine-side data
        primitive (``wonderland.turns.PhaseDefinition``)."""
        return PhaseDefinition(
            name=self.name,
            max_rotations=self.max_rotations,
            exit_condition_artifact=self.exit_condition_artifact,
            team_groupings=tuple(tuple(team) for team in self.team_groupings),
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
    phases: list[PhaseSpec] = Field(
        default_factory=list,
        description=(
            "Optional declaration of MtG-style phases inside this "
            "meeting (per analysis 033). Each phase has its own "
            "priority rotation + rotation budget. When present, the "
            "engine runs the meeting as: for each phase, rotate "
            "priority through cast, agents act-or-pass, advance when "
            "all-pass-in-succession or rotation-budget exhausts or "
            "exit-condition artifact ships. When absent (the default), "
            "the meeting runs on the legacy engagement-policy path — "
            "phase semantics are strictly opt-in."
        ),
    )

    # --- Feature lifecycle integration (P12 T86 + T87) ---

    iterate_only_in_states: list[str] | None = Field(
        default=None,
        description=(
            "T86 input filter for per_item meetings. When set, only "
            "iterate over items whose feature lifecycle state is in "
            "the named set. Used by tdd-implement's M5 to scope "
            "iterations to features in 'queued' state. Values match "
            "FeatureState enum members (proposed, in_design, "
            "designed, queued, in_progress, ready_for_review, "
            "verified, rejected). None means no filter — iterate "
            "over every candidate item (legacy behavior)."
        ),
    )
    transition_emitted_to: str | None = Field(
        default=None,
        description=(
            "T87 output transition for meetings that EMIT features "
            "(M2.5). After the meeting completes, every feature "
            "artifact emitted gets transitioned to this state via "
            "feature_lifecycle.transition(). Idempotent — features "
            "already in a non-allowed state are skipped silently. "
            "Used by M2.5 to mark fresh emissions as 'proposed'."
        ),
    )
    transition_iteration_to: str | None = Field(
        default=None,
        description=(
            "T87 output transition for per_item meetings that "
            "OPERATE ON existing features (M3, M4, M5, M6). After "
            "each iteration completes successfully, the iteration's "
            "feature transitions to this state. Idempotent. Used "
            "by M4 to mark features as 'designed' when scenarios "
            "ship; by M6 to mark as 'ready_for_review' when reviews "
            "approve."
        ),
    )
    parallel: bool = Field(
        default=False,
        description=(
            "T93: when True, per_item iterations run concurrently "
            "via asyncio.gather + stream-merge instead of sequentially "
            "via a for-loop. Used by tdd-design's M3 + M5 where "
            "iterations are structurally independent (decomposition "
            "and contract-negotiation per feature don't share state). "
            "Default False preserves the safe sequential behavior; "
            "opt-in per workflow YAML for meetings whose iterations "
            "have no cross-iteration coupling. Implementation-phase "
            "meetings (M6/M7) should NOT use this — tickets in the "
            "same feature can race on src/ files."
        ),
    )

    @model_validator(mode="after")
    def _validate_phase_names_unique(self) -> "Meeting":
        if not self.phases:
            return self
        names = [p.name for p in self.phases]
        if len(names) != len(set(names)):
            dupes = sorted({n for n in names if names.count(n) > 1})
            raise ValueError(
                f"meeting {self.id!r} has duplicate phase names: {dupes}"
            )
        return self

    @model_validator(mode="after")
    def _validate_team_groupings_cover_roster(self) -> "Meeting":
        """For each phase that declares team_groupings, every cast
        member (= meeting roster) must appear in exactly one team —
        no orphans, no extras. Phases without team_groupings (empty
        list) skip this check; they get one-agent-per-team at
        runtime."""
        if not self.phases:
            return self
        roster_set = set(self.roster)
        for phase in self.phases:
            if not phase.team_groupings:
                continue
            covered: set[str] = set()
            for team in phase.team_groupings:
                covered.update(team)
            orphans = roster_set - covered
            extras = covered - roster_set
            if orphans:
                raise ValueError(
                    f"meeting {self.id!r} phase {phase.name!r}: "
                    f"team_groupings missing cast members: {sorted(orphans)}"
                )
            if extras:
                raise ValueError(
                    f"meeting {self.id!r} phase {phase.name!r}: "
                    f"team_groupings reference non-cast members: "
                    f"{sorted(extras)}"
                )
        return self


class WorkflowDefaults(BaseModel):
    """Runtime defaults the workflow recommends. Caller may override."""

    budget_dollars: float | None = None
    timeout_seconds: float | None = None
    quiescence_seconds: float | None = None
    # Override for the LLM model id used by every agent in this
    # workflow. None → Runner's DEFAULT_MODEL applies. Lets a "-dev"
    # variant of a workflow swap to a cheaper model without touching
    # any code (analysis 038, P10 cost work). String is passed
    # straight through to the Anthropic API so any valid model id
    # works (e.g. ``claude-haiku-3-5-20241022``).
    model: str | None = None


class Pipeline(BaseModel):
    """Run a workflow's meetings as per-item lanes that flow concurrently.

    The pipeline shape inverts the dispatch model: instead of "for each
    meeting, iterate items" (stage-style — wait for all M1 to finish
    before any M2 starts), it's "for each item (lane), iterate meetings"
    (pipeline-style — lane A can be in M2 while lane B is still in M1).

    Used by tdd-implement: each queued feature gets a lane that runs
    Hatter→Implementation→Trial as its own dependency chain. One feature
    finishing its tea-party early can start its implementation while
    other features are still writing tests.

    Within a lane:
    - meetings whose ``per_item`` matches the pipeline's ``per_item``
      run once for the lane's outer item (e.g. M8 ``per_item: feature``
      runs once per feature lane).
    - meetings whose ``per_item`` is a sub-kind (e.g. M6/M7
      ``per_item: ticket`` within a feature lane) iterate over the
      sub-items belonging to this lane's outer item — only feature-A's
      tickets get processed in feature-A's lane.
    - meetings without ``per_item`` are ambiguous in pipeline mode and
      get treated as the outer kind (run once per lane).

    Cross-lane isolation is enforced via thread_id namespacing
    (``pipe.{outer_slug}.{meeting_id}-{sub_slug}``) and a
    ``lane_thread_prefix`` filter on seed resolution: lane A's M2
    seeing M1 output sees only lane A's M1, not lane B's.
    """

    per_item: str = Field(
        description=(
            "Lane iteration kind — typically 'feature'. The workflow "
            "spawns one lane per matching outer item."
        ),
    )
    parallel: bool = Field(
        default=True,
        description=(
            "When true, lanes run via asyncio.gather (concurrent). "
            "When false, lanes run sequentially. The whole reason for "
            "the pipeline shape is the parallel case; the sequential "
            "fallback exists for debugging + tests."
        ),
    )
    iterate_only_in_states: list[str] | None = Field(
        default=None,
        description=(
            "Lifecycle-state filter on outer items, mirroring "
            "``Meeting.iterate_only_in_states``. None → run a lane "
            "for every outer item the bus + disk fallback surface."
        ),
    )


class Workflow(BaseModel):
    """A complete workflow — name, description, ordered meetings."""

    name: str
    description: str
    version: int = 1
    defaults: WorkflowDefaults = Field(default_factory=WorkflowDefaults)
    meetings: list[Meeting]
    pipeline: Pipeline | None = Field(
        default=None,
        description=(
            "If set, the workflow runs in pipeline mode: meetings "
            "execute as per-item lanes rather than stage-by-stage. "
            "See Pipeline docstring for semantics."
        ),
    )

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

    Supports a top-level ``extends:`` field that names a parent
    workflow (bundled name or path). The child inherits the parent's
    meetings + defaults; any field the child sets overrides the
    parent. Used by ``-dev`` variants that swap only ``defaults.model``
    while keeping the parent's meeting shape verbatim.
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

    extends = data.pop("extends", None) if isinstance(data, dict) else None
    if extends is not None:
        parent = load_workflow(extends)
        parent_data = parent.model_dump()
        # Shallow defaults merge: parent keys + child keys, child wins.
        # Anything else (meetings, name, description, version) is a
        # straight top-level override — child wins if present, else
        # parent's value carries through.
        child_defaults = data.get("defaults") or {}
        parent_defaults = parent_data.get("defaults") or {}
        merged_defaults = {**parent_defaults, **child_defaults}
        merged = {**parent_data, **data}
        merged["defaults"] = merged_defaults
        data = merged

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
    project_root: Path | None = None,
    lane_thread_prefix: str | None = None,
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
            # of its iteration threads. Pipeline mode prefixes thread
            # ids with ``pipe.{lane_slug}.``; sequential mode uses the
            # plain ``{meeting_id}-{slug}`` form. The endswith match
            # covers both.
            prefix = f"{binding.from_meeting}-"
            candidates = [
                u for u in capture.utterances
                if u.thread_id.startswith(prefix)
                or f".{binding.from_meeting}-" in u.thread_id
            ]
            # If we're currently in a per_item iteration, slice to the
            # paired iteration's thread_id when present. Falls through
            # to the full per_item-meeting candidate set if no exact
            # match (e.g., the paired iteration produced no artifacts).
            if current_item_slug is not None:
                paired_suffix = f"{binding.from_meeting}-{current_item_slug}"
                paired = [
                    u for u in candidates
                    if u.thread_id == paired_suffix
                    or u.thread_id.endswith(f".{paired_suffix}")
                ]
                if paired:
                    candidates = paired
        else:
            candidates = capture.utterances_for(binding.from_meeting)

        # Pipeline lane scoping: drop utterances from OTHER lanes so
        # lane A's M8 doesn't seed from lane B's M6 output. Threads
        # without a ``pipe.`` prefix (e.g., the entry meeting's
        # directive on "main", or sequential-mode meetings) are
        # always allowed through — they're either cross-cutting or
        # not in any lane.
        if lane_thread_prefix is not None:
            candidates = [
                u for u in candidates
                if not u.thread_id.startswith("pipe.")
                or u.thread_id.startswith(lane_thread_prefix)
            ]

        kinded = [
            u
            for u in candidates
            if any(a.kind in binding.kinds for a in u.content.artifacts)
        ]

        # Cross-run continuity (analysis 039): when the bus has nothing
        # for this binding's kind filter but the project has the
        # artifacts on disk from a prior run, fall back to disk. This
        # closes the gap that bit r41-obol's M2.5 — Alice + Rabbit
        # didn't re-emit existing stories/tickets, so the bus was
        # empty for them, so M2.5 saw zero seeds, so White Rabbit
        # had nothing to compose features from.
        #
        # Bus content always wins when present (current run's
        # emissions are authoritative). Disk fallback only fires when
        # the bus query for this binding came back empty.
        if not kinded and project_root is not None:
            from wonderland.seeds_fallback import disk_seeds_for_kinds

            kinded = disk_seeds_for_kinds(
                project_root,
                list(binding.kinds),
                thread_id=binding.from_meeting,
            )

        # Consumption filter (binding.consumed_by): drop utterances
        # whose slug already appears in some downstream artifact's
        # ``Sources:`` line. Used to scope M2 composition to
        # *uncomposed* stories on cross-run design passes — once a
        # story has a feature sourcing it, M2 has no business
        # renegotiating it. Generic over (consumed-kind,
        # consumer-kind) pairs.
        if binding.consumed_by is not None:
            consumed = _consumed_source_slugs(
                project_root, binding.consumed_by
            )
            if consumed:
                kinded = [
                    u
                    for u in kinded
                    if not any(
                        a.payload.get("slug") in consumed
                        for a in u.content.artifacts
                        if a.kind in binding.kinds
                    )
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



def _collect_per_item_items(
    *,
    item_kind: str,
    state_filter: list[str] | None,
    capture: WorkflowCapture,
    runner: Runner,
    lane_outer_kind: str | None = None,
    lane_outer_slug: str | None = None,
) -> list[dict[str, Any]]:
    """Collect items for a per_item iteration: bus → disk fallback →
    state filter → optional lane scoping.

    Extracted from run_workflow's per_item branch so the pipeline
    runtime can reuse it. ``lane_outer_kind`` / ``lane_outer_slug``
    add a "this lane's children only" filter — e.g. when a lane is
    keyed on a feature and the meeting iterates over tickets, the
    lane keeps only tickets whose parent feature matches the lane's
    feature slug.
    """
    items: list[dict[str, Any]] = []
    seen_slugs: set[str] = set()

    for u in capture.utterances:
        for a in u.content.artifacts:
            if a.kind != item_kind:
                continue
            slug = a.payload.get("slug")
            if not slug or slug in seen_slugs:
                continue
            seen_slugs.add(slug)
            items.append(a.payload)

    project_root = getattr(runner, "project_root", None)
    if not items and project_root is not None:
        from wonderland.seeds_fallback import disk_seeds_for_kinds

        synthetic = disk_seeds_for_kinds(
            project_root,
            [item_kind],
            thread_id=item_kind,
        )
        for u in synthetic:
            for a in u.content.artifacts:
                if a.kind != item_kind:
                    continue
                slug = a.payload.get("slug")
                if not slug or slug in seen_slugs:
                    continue
                seen_slugs.add(slug)
                items.append(a.payload)

    # State filter mirroring the legacy meeting.iterate_only_in_states
    # path. Kept here so a synthetic Pipeline-derived collection picks
    # up the same lifecycle gating.
    if state_filter is not None and project_root is not None:
        from wonderland.feature_lifecycle import FeatureState, get_state

        allowed = {FeatureState(s) for s in state_filter}
        filtered: list[dict[str, Any]] = []

        if item_kind == "ticket":
            ticket_to_feature = _ticket_to_feature_map(project_root)
            for item in items:
                feature_slug = ticket_to_feature.get(item["slug"])
                if feature_slug is None:
                    continue
                state = get_state(project_root, feature_slug)
                if state is not None and state in allowed:
                    filtered.append(item)
        else:
            for item in items:
                state = get_state(project_root, item["slug"])
                if state is not None and state in allowed:
                    filtered.append(item)
        items = filtered

    # Lane scoping: keep only items belonging to this lane's outer
    # item. ``feature/ticket`` is the canonical case (lane keyed on
    # feature, sub-meeting iterates over tickets). Other lane shapes
    # fall through unscoped — the substrate doesn't know how to
    # match them and the operator can add support if it ever matters.
    if (
        lane_outer_slug is not None
        and lane_outer_kind == "feature"
        and item_kind == "ticket"
        and project_root is not None
    ):
        ticket_to_feature = _ticket_to_feature_map(project_root)
        items = [
            it for it in items
            if ticket_to_feature.get(it["slug"]) == lane_outer_slug
        ]
    elif (
        lane_outer_slug is not None
        and lane_outer_kind is not None
        and item_kind == lane_outer_kind
    ):
        # Lane's outer kind matches the meeting's iteration kind —
        # the meeting runs once for THIS lane's outer item.
        items = [it for it in items if it.get("slug") == lane_outer_slug]

    return items


async def _run_pipelined_workflow(
    workflow: Workflow,
    runner: Runner,
    directive: str,
) -> AsyncIterator[Any]:
    """Pipeline-mode entry: spawn one lane per outer item, run lanes
    concurrently (or serially when ``pipeline.parallel: false``), each
    lane runs all of ``workflow.meetings`` in declaration order.

    Pipeline shape inverts the dispatch: instead of waiting for all of
    M1 across every feature before any M2 starts, lane A can be in M2
    while lane B is still in M1. Built for tdd-implement's per-feature
    Hatter→Implementation→Trial flow.
    """
    pipeline = workflow.pipeline
    assert pipeline is not None  # caller guards
    capture = WorkflowCapture()

    per_item_meetings: dict[str, str] = {
        m.id: m.per_item for m in workflow.meetings if m.per_item is not None
    }

    outer_items = _collect_per_item_items(
        item_kind=pipeline.per_item,
        state_filter=pipeline.iterate_only_in_states,
        capture=capture,
        runner=runner,
    )

    if not outer_items:
        # Nothing to pipeline — synthesize a skip per meeting so the
        # consumer sees the workflow was acknowledged. Mirrors the
        # empty-items path in run_workflow's per_item branch.
        for meeting in workflow.meetings:
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
        return

    def _make_lane(idx: int, outer_item: dict[str, Any]):
        outer_slug = outer_item["slug"]
        lane_thread_prefix = f"pipe.{outer_slug}."
        lane_label = outer_item.get("title") or outer_slug

        async def _gen():
            async for event in _run_lane(
                workflow=workflow,
                runner=runner,
                capture=capture,
                per_item_meetings=per_item_meetings,
                outer_kind=pipeline.per_item,
                outer_slug=outer_slug,
                outer_label=lane_label,
                lane_index=idx + 1,
                lane_total=len(outer_items),
                lane_thread_prefix=lane_thread_prefix,
                # Only the very first lane's first meeting is the
                # "entry" — receives the operator's directive. Other
                # lanes pick up the directive from the bus / disk.
                directive=directive if idx == 0 else None,
            ):
                yield event

        return _gen()

    iterators = [_make_lane(idx, item) for idx, item in enumerate(outer_items)]

    if pipeline.parallel:
        global_budget_hit = False
        async for event in _merge_async_iterators(iterators):
            if isinstance(event, _OutcomeSentinel):
                if event.outcome == "GLOBAL_BUDGET":
                    global_budget_hit = True
                continue
            yield event
        if global_budget_hit:
            return
    else:
        for it in iterators:
            global_budget_hit = False
            async for event in it:
                if isinstance(event, _OutcomeSentinel):
                    if event.outcome == "GLOBAL_BUDGET":
                        global_budget_hit = True
                    continue
                yield event
            if global_budget_hit:
                return


async def _run_lane(
    *,
    workflow: Workflow,
    runner: Runner,
    capture: WorkflowCapture,
    per_item_meetings: dict[str, str],
    outer_kind: str,
    outer_slug: str,
    outer_label: str,
    lane_index: int,
    lane_total: int,
    lane_thread_prefix: str,
    directive: str | None,
) -> AsyncIterator[Any]:
    """One lane of a pipelined workflow — runs every meeting in
    declaration order, scoped to a single outer item.

    Per-meeting dispatch:
    - ``per_item: <outer_kind>`` (e.g., per_item: feature in a feature
      lane): runs once for THIS lane's outer item.
    - ``per_item: <sub-kind>`` (e.g., per_item: ticket within a
      feature lane): iterates over the sub-items belonging to this
      lane's outer item.
    - ``per_item: None``: runs once for the lane (treated as the
      outer kind). Rare; included for consistency.

    Thread ids are namespaced with ``lane_thread_prefix`` so
    ``resolve_seeds`` can scope cross-meeting bindings to this lane
    only.
    """
    is_first_meeting = True
    for meeting in workflow.meetings:
        meeting_directive = directive if is_first_meeting else None
        is_first_meeting = False

        # Resolve the meeting's iteration shape for this lane.
        if meeting.per_item is None or meeting.per_item == outer_kind:
            # Single iteration for this lane's outer item.
            iteration_slug = outer_slug
            iteration_label = outer_label
            thread_id = f"{lane_thread_prefix}{meeting.id}-{outer_slug}"
            outcome = "RUNNING"
            async for event in _run_one_meeting(
                meeting=meeting,
                runner=runner,
                capture=capture,
                directive=meeting_directive,
                per_item_meetings=per_item_meetings,
                current_item_kind=outer_kind,
                current_item_slug=iteration_slug,
                thread_id=thread_id,
                iteration_index=lane_index,
                iteration_total=lane_total,
                iteration_label=iteration_label,
                lane_thread_prefix=lane_thread_prefix,
            ):
                if isinstance(event, _OutcomeSentinel):
                    outcome = event.outcome
                    yield event
                    continue
                yield event
            if outcome == "GLOBAL_BUDGET":
                return
            continue

        # Sub-kind iteration scoped to this lane (e.g., tickets-of-
        # feature-X). Collect lane-scoped items, then iterate
        # sequentially within the lane (lanes are the parallelism
        # boundary; within a lane, ticket-level work is sequential
        # to avoid src/ races and keep per-ticket TDD discipline).
        #
        # ``state_filter=None`` here on purpose: the pipeline's outer
        # filter already gated WHICH features get a lane; per-meeting
        # state filters within a lane would just fight the per-
        # iteration transitions (M6 fires queued → in_progress; M7's
        # legacy [queued] filter would then reject that same feature).
        # In pipeline mode the lane is the gate.
        sub_items = _collect_per_item_items(
            item_kind=meeting.per_item,
            state_filter=None,
            capture=capture,
            runner=runner,
            lane_outer_kind=outer_kind,
            lane_outer_slug=outer_slug,
        )

        if not sub_items:
            # Lane has no children for this meeting — synthetic skip
            # so the consumer still sees the meeting acknowledged in
            # this lane's stream.
            thread_id = f"{lane_thread_prefix}{meeting.id}"
            yield MeetingStartEvent(
                meeting=meeting,
                seeds=[],
                thread_id=thread_id,
                iteration_index=0,
                iteration_total=0,
                iteration_label=f"{outer_label} (no items)",
            )
            yield MeetingEndEvent(
                meeting=meeting,
                outcome="COMPLETE",
                elapsed_s=0.0,
                calls_delta=0,
                cost_delta=0.0,
                artifact_kinds={},
                thread_id=thread_id,
                iteration_index=0,
                iteration_total=0,
                iteration_label=f"{outer_label} (no items)",
            )
            continue

        for sub_idx, sub_item in enumerate(sub_items):
            sub_slug = sub_item["slug"]
            sub_label = sub_item.get("title") or sub_slug
            thread_id = f"{lane_thread_prefix}{meeting.id}-{sub_slug}"
            outcome = "RUNNING"
            async for event in _run_one_meeting(
                meeting=meeting,
                runner=runner,
                capture=capture,
                directive=None,  # sub-meetings never receive directive
                per_item_meetings=per_item_meetings,
                current_item_kind=meeting.per_item,
                current_item_slug=sub_slug,
                thread_id=thread_id,
                iteration_index=sub_idx + 1,
                iteration_total=len(sub_items),
                iteration_label=f"{outer_label} / {sub_label}",
                lane_thread_prefix=lane_thread_prefix,
            ):
                if isinstance(event, _OutcomeSentinel):
                    outcome = event.outcome
                    yield event
                    continue
                yield event
            if outcome == "GLOBAL_BUDGET":
                return


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
    if workflow.pipeline is not None:
        async for event in _run_pipelined_workflow(workflow, runner, directive):
            yield event
        return

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
            async for event in _run_one_meeting(
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

        # Cross-run / cross-workflow fallback: when the bus is empty
        # for this meeting's per_item kind but the project has matching
        # artifacts on disk (typical for tdd-implement, which is the
        # entry meeting of its own workflow and has no upstream
        # in-this-run material), pull them from disk via the same
        # seed-fallback mechanism that resolve_seeds uses. Without
        # this, the per_item iteration finds zero items, hits the
        # synthetic-skip path, and the meeting completes empty —
        # exactly what tdd-implement was doing before this fix.
        project_root = getattr(runner, "project_root", None)
        if not items and project_root is not None:
            from wonderland.seeds_fallback import disk_seeds_for_kinds

            synthetic = disk_seeds_for_kinds(
                project_root,
                [meeting.per_item],
                thread_id=meeting.id,
            )
            for u in synthetic:
                for a in u.content.artifacts:
                    if a.kind != meeting.per_item:
                        continue
                    slug = a.payload.get("slug")
                    if not slug or slug in seen_slugs:
                        continue
                    seen_slugs.add(slug)
                    items.append(a.payload)

        # T86 input filter: when iterate_only_in_states is set on the
        # meeting, drop items whose feature lifecycle state isn't in
        # the allowed set. Lets tdd-implement's M7 scope to tickets
        # whose parent feature is in 'queued' state. Skipped if
        # project_root unavailable (e.g. FakeRunner test fixtures) —
        # back-compat preserved.
        #
        # Two semantics depending on per_item kind:
        #   - per_item: feature → check the item's own lifecycle state
        #   - per_item: ticket  → look up which feature this ticket
        #     belongs to (via FeaturePayload.tickets), check that
        #     feature's state. Tickets don't have their own lifecycle
        #     in v1; the parent feature's state gates them. Per
        #     T88-note: feature is the human-meaningful unit, ticket
        #     is the iteration atom.
        if (
            meeting.iterate_only_in_states is not None
            and getattr(runner, "project_root", None) is not None
        ):
            from wonderland.feature_lifecycle import (
                FeatureState,
                get_state,
            )

            allowed = {
                FeatureState(s) for s in meeting.iterate_only_in_states
            }
            filtered: list[dict[str, Any]] = []

            if meeting.per_item == "ticket":
                # Reverse-index tickets to parent features so we can
                # gate ticket iterations by the parent feature's
                # lifecycle state. Shared helper with the T87
                # transition logic — same lookup, two consumers.
                ticket_to_feature = _ticket_to_feature_map(
                    runner.project_root
                )
                for item in items:
                    ticket_slug = item["slug"]
                    feature_slug = ticket_to_feature.get(ticket_slug)
                    if feature_slug is None:
                        # Orphan ticket (no parent feature) — drop
                        # under the strict interpretation. Filtering's
                        # job is to surface only work the operator
                        # explicitly queued.
                        continue
                    state = get_state(
                        runner.project_root, feature_slug
                    )
                    if state is not None and state in allowed:
                        filtered.append(item)
            else:
                # per_item: feature (or any other kind we treat
                # directly): the item's own slug IS the feature slug.
                for item in items:
                    slug = item["slug"]
                    state = get_state(runner.project_root, slug)
                    if state is not None and state in allowed:
                        filtered.append(item)

            items = filtered

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

        if meeting.parallel:
            # T93: parallel iteration — fan out via asyncio.gather
            # + stream-merge so iterations run concurrently and the
            # operator sees real-time progress across the fan-out.
            # Safe for meetings with structurally independent
            # iterations (M3 decomposition + M5 contracts in the
            # split workflow); NOT safe for ticket-level meetings
            # (M6/M7) where iterations might race on src/ files.
            #
            # Disk-write safety: registries (TicketRegistry,
            # FeatureRegistry, etc.) read-then-write next_number
            # synchronously. Since asyncio is single-threaded and
            # registry.write() has no awaits, two concurrent tasks
            # naturally serialize during the write — no explicit
            # lock needed.

            def _make_iter(idx: int, item: dict[str, Any]):
                slug = item["slug"]
                iteration_thread_id = f"{meeting.id}-{slug}"
                label = item.get("title") or slug

                async def _gen():
                    async for event in _run_one_meeting(
                        meeting=meeting,
                        runner=runner,
                        capture=capture,
                        directive=None,
                        per_item_meetings=per_item_meetings,
                        current_item_kind=meeting.per_item,
                        current_item_slug=slug,
                        thread_id=iteration_thread_id,
                        iteration_index=idx + 1,
                        iteration_total=len(items),
                        iteration_label=label,
                    ):
                        yield event

                return _gen()

            iterators = [_make_iter(idx, item) for idx, item in enumerate(items)]
            global_budget_hit = False
            async for event in _merge_async_iterators(iterators):
                if isinstance(event, _OutcomeSentinel):
                    if event.outcome == "GLOBAL_BUDGET":
                        global_budget_hit = True
                    continue
                yield event
            if global_budget_hit:
                return
        else:
            # Sequential iteration — original safe default.
            for idx, item in enumerate(items):
                slug = item["slug"]
                iteration_thread_id = f"{meeting.id}-{slug}"
                label = item.get("title") or slug
                outcome = "RUNNING"
                async for event in _run_one_meeting(
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


async def _merge_async_iterators(
    iterators: list,
):
    """Merge multiple async iterators into a single stream — yields
    events as they fire from any iterator. Per-iterator order is
    preserved; events from different iterators interleave naturally.

    Used by the T93 parallel per_item branch: each iteration is an
    async generator yielding RunnerEvent / MeetingStartEvent / etc.
    The merge lets the operator see real-time progress across all
    parallel iterations rather than waiting for the entire fan-out
    to complete.

    Implementation: one feeder task per iterator, all push events
    onto a shared asyncio.Queue. A sentinel marks each iterator's
    completion; we yield until every sentinel has come back.
    """
    import asyncio

    if not iterators:
        return
    queue: asyncio.Queue = asyncio.Queue()
    sentinel = object()

    async def _feeder(it):
        try:
            async for event in it:
                await queue.put(event)
        except Exception as exc:  # noqa: BLE001
            await queue.put(("__feeder_error__", exc))
        finally:
            await queue.put(sentinel)

    tasks = [asyncio.create_task(_feeder(it)) for it in iterators]
    n_remaining = len(iterators)
    try:
        while n_remaining > 0:
            event = await queue.get()
            if event is sentinel:
                n_remaining -= 1
                continue
            if (
                isinstance(event, tuple)
                and len(event) == 2
                and event[0] == "__feeder_error__"
            ):
                # An iteration raised; surface the exception so the
                # caller can decide what to do. Other iterations
                # keep going via their own feeder tasks.
                raise event[1]
            yield event
    finally:
        # Best-effort cleanup if the consumer broke out early.
        for task in tasks:
            if not task.done():
                task.cancel()


def _ticket_to_feature_map(project_root: Path) -> dict[str, str]:
    """Build a reverse index: ticket_slug → parent_feature_slug.

    Source-of-truth: each ticket's ``Sources:`` field. M3 (the
    per_item: feature decomposition meeting) emits tickets whose
    sources field includes the iteration's feature slug — the
    ticket's own record carries the parent reference. We walk the
    ticket registry, parse each ticket's Sources line, and match
    source slugs against the feature registry to find the parent.

    Why ticket-side not feature-side (changed from earlier): the
    feature payload's ``tickets:`` list is fragile — Rabbit emits
    it at M2 time before M3 has produced any tickets, so the slugs
    listed there don't always match the actual tickets that get
    decomposed in M3. The ticket-side reference is naturally
    one-directional and tracks reality. Feature.tickets stays
    informational; a wrong list there doesn't break iteration.

    Best-effort: returns empty map on any error so the caller can
    gracefully fall through to no-filter / no-transition behavior.
    """
    import re

    out: dict[str, str] = {}
    try:
        from wonderland.feature import FeatureRegistry
        from wonderland.ticket import TicketRegistry

        feature_slugs = {
            f.slug for f in FeatureRegistry(project_root).list_features()
        }
        if not feature_slugs:
            return {}

        sources_re = re.compile(
            r"^\s*\*\*Sources?:\*\*\s*(.+?)$",
            re.MULTILINE,
        )

        for ticket_record in TicketRegistry(project_root).list_tickets():
            try:
                text = ticket_record.path.read_text(encoding="utf-8")
            except OSError:
                continue
            match = sources_re.search(text)
            if not match:
                continue
            # Comma-separated slug list. Strip whitespace, ignore
            # empty entries (e.g., the literal "—" placeholder when
            # sources was empty at write time).
            sources_line = match.group(1).strip()
            if sources_line in ("", "—", "-"):
                continue
            for source in (s.strip() for s in sources_line.split(",")):
                if source and source in feature_slugs:
                    # First feature-shaped source wins. M3 directive
                    # requires the parent feature to be the first
                    # entry; this matches that contract.
                    out[ticket_record.slug] = source
                    break
    except Exception:  # noqa: BLE001 — best-effort
        return {}
    return out


def _consumed_source_slugs(
    project_root: Path | None, consumer_kind: str
) -> set[str]:
    """Scan ``project_root/.wonderland/<consumer-dir>/`` for files of
    ``consumer_kind`` and return every slug that appears in any of
    their ``Sources:`` lines.

    Used by ``SeedBinding.consumed_by`` to scope a seed binding to
    only artifacts that haven't yet been consumed by a downstream
    kind. Canonical case: M2 composition's ``from: scoping kinds:
    [story], consumed_by: feature`` — drops stories that already
    have a feature sourcing them, so cross-run design passes don't
    renegotiate stories the prior pass already composed.

    Best-effort: returns empty set on any error or when the
    consumer-kind directory doesn't exist (no files = nothing
    consumed yet, so all source artifacts pass through).

    Generic over (consumer_kind, source-of-consumed). The Sources
    line in markdown carries arbitrary slugs; this helper just
    accumulates them.
    """
    import re

    if project_root is None:
        return set()

    # Map consumer_kind → on-disk directory + filename pattern.
    # Mirrors the structure used by registries elsewhere; if a kind
    # we don't know about lands here, treat as no consumption.
    kind_dirs = {
        "feature": "features",
        "ticket": "tickets",
        "adr": "architecture",
        "ruling": "rulings",
        "contract_note": "contract-notes",
        "test_scenario": "test-scenarios",
        "implementation": "implementations",
        "review": "reviews",
        "story": "stories",
        "observation": "observations",
    }
    dirname = kind_dirs.get(consumer_kind)
    if dirname is None:
        return set()

    base = project_root / ".wonderland" / dirname
    if not base.is_dir():
        return set()

    sources_re = re.compile(
        r"^\s*\*\*Sources?:\*\*\s*(.+?)$",
        re.MULTILINE,
    )

    consumed: set[str] = set()
    for path in base.glob("*.md"):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        match = sources_re.search(text)
        if not match:
            continue
        sources_line = match.group(1).strip()
        if sources_line in ("", "—", "-"):
            continue
        for source in (s.strip() for s in sources_line.split(",")):
            if source:
                consumed.add(source)
    return consumed


def _apply_post_meeting_transitions(
    *,
    meeting: Meeting,
    runner: Runner,
    new_utterances: list[Utterance],
    current_item_slug: str | None,
) -> None:
    """T87 output transitions — fire feature lifecycle transitions
    after a meeting completes successfully.

    Two semantics, both opt-in via Meeting fields:

    - ``transition_emitted_to``: meetings that EMIT features (M2.5).
      Every feature artifact in this meeting's emissions transitions
      to the named state. Idempotent — IllegalTransition errors
      (e.g. feature already in a non-allowed state) get caught and
      logged-as-skip rather than failing the meeting.

    - ``transition_iteration_to``: per_item meetings that operate
      ON existing features (M3, M4, M5, M6). The iteration's
      feature_slug (from ``current_item_slug``) transitions to the
      named state. Fires once per iteration that completed — the
      caller already gates on outcome=='COMPLETE' so failed
      iterations don't transition.

    Skipped silently if project_root is unavailable (FakeRunner
    test fixtures, etc.) so the transition layer never breaks the
    meeting flow.
    """
    project_root = getattr(runner, "project_root", None)
    if project_root is None:
        return

    from wonderland.feature_lifecycle import (
        FeatureState,
        IllegalTransitionError,
        transition,
    )

    actor = "system"  # transitions fired by workflow are system-level

    # transition_emitted_to: fire for every feature artifact emitted
    # in this meeting. M2.5's natural use case.
    if meeting.transition_emitted_to:
        try:
            target = FeatureState(meeting.transition_emitted_to)
        except ValueError:
            target = None
        if target is not None:
            seen: set[str] = set()
            for u in new_utterances:
                for a in u.content.artifacts:
                    if a.kind != "feature":
                        continue
                    slug = a.payload.get("slug")
                    if not slug or slug in seen:
                        continue
                    seen.add(slug)
                    try:
                        transition(
                            project_root,
                            slug,
                            target,
                            by=actor,
                            notes=(
                                f"Auto-transition from meeting "
                                f"{meeting.id!r} on COMPLETE"
                            ),
                        )
                    except IllegalTransitionError:
                        # Already in a non-allowed state — idempotent
                        # behavior. Re-running the workflow on a
                        # project that's already past this point
                        # shouldn't fail.
                        pass

    # transition_iteration_to: fire once for the iteration's feature.
    # Two semantics depending on per_item kind (T88 split workflow
    # support):
    #   - per_item: feature → current_item_slug IS the feature slug;
    #     transition directly.
    #   - per_item: ticket  → current_item_slug is a ticket slug; look
    #     up which feature the ticket belongs to, transition that
    #     feature. Lets tdd-implement's M6 (per_item: ticket) move
    #     the parent feature → in_progress on first ticket; subsequent
    #     tickets find the feature already in_progress so the
    #     idempotent illegal-transition swallow no-ops them.
    if meeting.transition_iteration_to and current_item_slug:
        try:
            target = FeatureState(meeting.transition_iteration_to)
        except ValueError:
            target = None
        if target is not None:
            if meeting.per_item == "ticket":
                lookup = _ticket_to_feature_map(project_root)
                feature_slug = lookup.get(current_item_slug)
            else:
                feature_slug = current_item_slug
            if feature_slug:
                try:
                    transition(
                        project_root,
                        feature_slug,
                        target,
                        by=actor,
                        notes=(
                            f"Auto-transition from iteration of "
                            f"{meeting.id!r} on COMPLETE"
                        ),
                    )
                except IllegalTransitionError:
                    pass


async def _run_one_meeting(
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
    lane_thread_prefix: str | None = None,
) -> AsyncIterator[Any]:
    """Dispatch a single meeting (or per_item iteration) onto either
    the legacy engagement-policy path (``_convene_one``) or the
    phased orchestrator (``meeting.run_phased_meeting``) based on
    whether ``meeting.phases`` is non-empty.

    Phase semantics are strictly opt-in (analysis 033 / P9 T57):
    workflows without a ``phases:`` declaration retain the original
    parallel-multicast behavior unchanged.
    """
    if meeting.phases:
        # Local import to avoid the meeting ↔ workflow circular at
        # module-load time (meeting.py imports MeetingStartEvent /
        # MeetingEndEvent / resolve_seeds from workflow).
        from wonderland.meeting import (
            jsonl_phase_event_writer,
            run_phased_meeting,
        )

        # Phase-event persistence (T58d / analysis 034 F6). Writes
        # one JSON line per phase event to
        # ``<project_root>/.wonderland/phase-events.jsonl`` for
        # post-run analysis (deliberation counts, phase-end reasons,
        # per-agent §VIII shapes). Multiple meetings share the same
        # file and append in run order — readers can group by
        # thread_id when needed.
        phase_writer = jsonl_phase_event_writer(
            runner.project_root / ".wonderland" / "phase-events.jsonl"
        )

        async for event in run_phased_meeting(
            meeting=meeting,
            runner=runner,
            capture=capture,
            directive=directive,
            per_item_meetings=per_item_meetings,
            current_item_kind=current_item_kind,
            current_item_slug=current_item_slug,
            thread_id=thread_id,
            iteration_index=iteration_index,
            iteration_total=iteration_total,
            iteration_label=iteration_label,
            phase_event_writer=phase_writer,
            lane_thread_prefix=lane_thread_prefix,
        ):
            yield event
        return

    async for event in _convene_one(
        meeting=meeting,
        runner=runner,
        capture=capture,
        directive=directive,
        per_item_meetings=per_item_meetings,
        current_item_kind=current_item_kind,
        current_item_slug=current_item_slug,
        thread_id=thread_id,
        iteration_index=iteration_index,
        iteration_total=iteration_total,
        iteration_label=iteration_label,
        lane_thread_prefix=lane_thread_prefix,
    ):
        yield event


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
    lane_thread_prefix: str | None = None,
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
        # FakeRunner test fixtures don't always expose project_root —
        # back-compat for the existing test surface, which doesn't
        # need disk fallback.
        project_root=getattr(runner, "project_root", None),
        lane_thread_prefix=lane_thread_prefix,
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

    calls_before = runner.telemetry.call_count
    artifact_count_before = len(capture.utterances)
    meeting_start = time.monotonic()

    # Per-thread cost attribution for parallel meetings — see
    # meeting.run_phased_meeting for the full rationale. Setting the
    # contextvar here covers the legacy non-phased path's
    # orchestrator-driven calls as well.
    from wonderland.telemetry import (
        reset_current_thread_id,
        set_current_thread_id,
    )

    telemetry_token = set_current_thread_id(thread_id)
    try:
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
                spent = runner.telemetry.cost_for_thread(thread_id)
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
    finally:
        reset_current_thread_id(telemetry_token)

    if outcome in ("MEETING_BUDGET", "TIMEOUT", "ABORTED"):
        runner.mark_thread_complete(thread_id, f"meeting ended via {outcome}")

    elapsed = time.monotonic() - meeting_start
    calls_delta = runner.telemetry.call_count - calls_before
    cost_delta = runner.telemetry.cost_for_thread(thread_id)
    new_utterances = capture.utterances[artifact_count_before:]
    kinds_count: dict[str, int] = {}
    for u in new_utterances:
        for a in u.content.artifacts:
            kinds_count[a.kind] = kinds_count.get(a.kind, 0) + 1

    # T87 output transitions — fire on successful completion only.
    # Failed meetings (BUDGET / TIMEOUT / ABORTED) leave feature state
    # untouched so the operator can see what shipped vs. didn't.
    if outcome == "COMPLETE":
        _apply_post_meeting_transitions(
            meeting=meeting,
            runner=runner,
            new_utterances=new_utterances,
            current_item_slug=current_item_slug,
        )

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
