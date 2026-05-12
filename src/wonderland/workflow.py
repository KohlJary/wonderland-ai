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

import asyncio
import logging
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from wonderland.turns import PhaseDefinition

logger = logging.getLogger(__name__)

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


class RosterFilter(BaseModel):
    """Per-iteration roster narrowing for per_item meetings.

    When a meeting iterates over items (tickets, features, etc.)
    and the items carry a discriminating payload field (e.g.
    ``stack_span`` on tickets: ``frontend`` / ``backend`` /
    ``full-stack``), this lets the YAML declare a value → roster
    override. Iterations whose item payload's ``field`` value
    matches an entry in ``map`` use that narrowed roster; values
    not in the map fall through to the meeting's full roster.

    Buzz-in still works: agents not in the narrowed roster don't
    get priority windows but can still emit utterances when their
    constitution's §III engagement rules fire (e.g. Tweedledum
    speaks on a contract question even when only Tweedledee is in
    the M7 roster for a frontend ticket).

    Used by tdd-implement's M7 to skip a Tweedle for split-stack
    tickets — half the call volume for the dominant majority case
    where a ticket only touches one side of the seam.
    """

    field: str = Field(
        min_length=1,
        description=(
            "Item-payload field to read for the discriminator value "
            "(e.g. ``stack_span``)."
        ),
    )
    map: dict[str, list[str]] = Field(
        description=(
            "Field-value → narrowed roster mapping. Roster entries "
            "must be a subset of the meeting's full roster — the "
            "validator enforces this so a typo in the YAML doesn't "
            "silently swap in unrelated agents."
        ),
    )

    @field_validator("map")
    @classmethod
    def _map_not_empty(cls, v: dict[str, list[str]]) -> dict[str, list[str]]:
        if not v:
            raise ValueError(
                "RosterFilter.map cannot be empty — declare at least "
                "one value → roster entry, or omit per_item_roster_filter "
                "entirely."
            )
        return v


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
    gates_on_dependencies: bool = Field(
        default=False,
        description=(
            "When True (and the meeting runs inside an inner pipeline "
            "block on a per_item kind that has dependency relationships "
            "between items), this meeting waits for the same meeting "
            "to complete on each of the iteration item's upstream "
            "dependencies before starting. Used for ticket-level work "
            "in tdd-implement: M6 (Tea Party) runs all tickets in "
            "parallel because writing failing tests is independent, "
            "but M7 (Implementation) gates on dependencies so a "
            "ticket whose code depends on an upstream ticket's "
            "implementation doesn't start writing against half-built "
            "foundations. Dependencies come from the ticket's "
            "``Blocked by:`` markdown line (parsed when the items "
            "are collected). Cycles, missing deps, and cross-block "
            "deps log warnings and fall through (don't gate)."
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
    per_item_roster_filter: RosterFilter | None = Field(
        default=None,
        description=(
            "Narrow the roster per iteration based on an item-payload "
            "field. See ``RosterFilter``. Most useful for skipping "
            "irrelevant cast members on items that touch only part of "
            "the system — e.g. M7 (implementation) running just "
            "Tweedledee for a ``stack_span: frontend`` ticket."
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
    def _validate_roster_filter_subset(self) -> "Meeting":
        """Every agent named in a roster-filter mapping must be a
        member of the meeting's full roster. Catches typo'd or
        cross-meeting references before they cause a silent
        substrate failure at iteration time."""
        if self.per_item_roster_filter is None:
            return self
        if self.per_item is None:
            raise ValueError(
                f"meeting {self.id!r} declares per_item_roster_filter "
                f"but is not a per_item meeting"
            )
        roster_set = set(self.roster)
        for value, narrowed in self.per_item_roster_filter.map.items():
            extras = [a for a in narrowed if a not in roster_set]
            if extras:
                raise ValueError(
                    f"meeting {self.id!r}: per_item_roster_filter "
                    f"value {value!r} names agent(s) {extras} "
                    f"that aren't in the meeting's roster "
                    f"{sorted(roster_set)}"
                )
        return self

    def apply_roster_filter(
        self, item_payload: dict[str, Any]
    ) -> "Meeting":
        """Return a copy of this meeting with the roster (and any
        phase team_groupings that reference roster members) narrowed
        to whatever ``per_item_roster_filter`` resolves to for the
        given item. Returns self unchanged when:

          - ``per_item_roster_filter`` isn't set
          - the item's field value isn't in the filter's map
          - the narrowed roster matches the existing roster
            (no-op savings)

        Roster order is preserved (the original roster's relative
        order survives the filter; new orderings aren't introduced).
        ``team_groupings`` get the same filter applied — agents not
        in the narrowed roster are dropped; empty teams are dropped
        entirely.
        """
        rf = self.per_item_roster_filter
        if rf is None:
            return self
        field_value = item_payload.get(rf.field)
        if field_value is None or field_value not in rf.map:
            return self
        narrowed = set(rf.map[field_value])
        if narrowed == set(self.roster):
            return self
        new_roster = [a for a in self.roster if a in narrowed]
        # Filter team_groupings in every phase: drop non-roster
        # agents; drop empty teams.
        new_phases: list[PhaseSpec] = []
        for phase in self.phases:
            if not phase.team_groupings:
                new_phases.append(phase)
                continue
            new_teams = tuple(
                tuple(a for a in team if a in narrowed)
                for team in phase.team_groupings
            )
            new_teams = tuple(team for team in new_teams if team)
            new_phases.append(
                phase.model_copy(update={"team_groupings": new_teams})
            )
        return self.model_copy(
            update={"roster": new_roster, "phases": new_phases}
        )

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


class PipelineLevel(BaseModel):
    """One level of a (possibly multi-level) pipeline.

    Workflows can declare 1+ levels. Each level has its own iteration
    kind, parallel flag, and lifecycle filter. Meetings are matched to
    a level by their ``per_item`` field — meeting with
    ``per_item: feature`` runs at the feature-level; meeting with
    ``per_item: ticket`` runs at the ticket-level.

    Two-level example (tdd-implement):
      level 0: per_item=feature, parallel=false → features sequential
      level 1: per_item=ticket, parallel=true → tickets within each
        feature run in true pipeline (ticket A finishing M6 starts
        M7 while ticket B is still in M6)

    The flow within a feature lane: walk meetings in declaration
    order. Consecutive ticket-level meetings (M6, M7) get grouped
    into a block that runs as a per-ticket inner pipeline. Once the
    block finishes (all per-ticket inner lanes done), the lane
    continues with the next outer-level meeting (M8 review per
    feature). This is the recursive shape; works for arbitrary
    nesting if future workflows want it.
    """

    per_item: str = Field(
        description=(
            "Iteration kind for this level — e.g. 'feature' or 'ticket'."
        ),
    )
    parallel: bool = Field(
        default=True,
        description=(
            "When true, items at this level run concurrently. False "
            "means sequential iteration."
        ),
    )
    iterate_only_in_states: list[str] | None = Field(
        default=None,
        description=(
            "Lifecycle-state filter on items at this level, mirroring "
            "``Meeting.iterate_only_in_states``."
        ),
    )


class Pipeline(BaseModel):
    """Run a workflow's meetings as per-item lanes that flow concurrently.

    The pipeline shape inverts the dispatch model: instead of "for each
    meeting, iterate items" (stage-style — wait for all M1 to finish
    before any M2 starts), it's "for each item (lane), iterate meetings"
    (pipeline-style — lane A can be in M2 while lane B is still in M1).

    Two declaration shapes:

    1. **Single-level (legacy)** — top-level fields:

           pipeline:
             per_item: feature
             parallel: true
             iterate_only_in_states: [queued]

       Equivalent to ``levels: [{per_item: feature, parallel: true,
       iterate_only_in_states: [queued]}]``. Backward-compatible with
       workflows shipped before nested-level support.

    2. **Multi-level** — explicit ``levels`` list:

           pipeline:
             levels:
               - per_item: feature
                 parallel: false        # features sequential
                 iterate_only_in_states: [queued, in_progress]
               - per_item: ticket
                 parallel: true         # tickets within feature parallel

       Used by tdd-implement to flow each ticket through M6→M7 in
       parallel within a feature, with M8 (per_item: feature) running
       once after all per-ticket lanes finish.

    Within a lane (any level):
    - meetings whose ``per_item`` matches the lane's level run once
      for the lane's item (e.g. M8 ``per_item: feature`` runs once
      per feature lane).
    - meetings whose ``per_item`` matches an inner level kick off a
      nested per-item pipeline scoped to this lane's item.
    - meetings without ``per_item`` are treated as the outer kind
      (run once per lane).

    Cross-lane isolation is enforced via thread_id namespacing
    (``pipe.{outer_slug}.{meeting_id}-{sub_slug}``) and a
    ``lane_thread_prefix`` filter on seed resolution.
    """

    # Legacy single-level fields. Optional when ``levels`` is set.
    per_item: str | None = Field(
        default=None,
        description=(
            "Single-level shorthand: lane iteration kind. Mutually "
            "exclusive with ``levels`` — set one or the other."
        ),
    )
    parallel: bool = Field(
        default=True,
        description=(
            "Single-level shorthand: parallel flag. Ignored when "
            "``levels`` is set (each level has its own flag)."
        ),
    )
    iterate_only_in_states: list[str] | None = Field(
        default=None,
        description=(
            "Single-level shorthand: lifecycle-state filter. Ignored "
            "when ``levels`` is set."
        ),
    )

    # Multi-level declaration. Mutually exclusive with the single-level
    # shorthand fields above; the validator normalizes the legacy
    # form into a 1-element levels list so downstream code only sees
    # ``levels``.
    levels: list[PipelineLevel] | None = Field(
        default=None,
        description=(
            "Ordered list of pipeline levels (outer → inner). When "
            "set, supersedes the single-level shorthand fields."
        ),
    )

    def model_post_init(self, _context: Any) -> None:
        """Normalize legacy single-level form into a 1-element levels
        list. Downstream readers only access ``self.levels`` — they
        don't need to know about the legacy fields."""
        if self.levels is None:
            if self.per_item is None:
                raise ValueError(
                    "Pipeline requires either 'per_item' (legacy) or "
                    "'levels' (multi-level) to be set."
                )
            # Mutate; this only runs at construction.
            object.__setattr__(
                self,
                "levels",
                [
                    PipelineLevel(
                        per_item=self.per_item,
                        parallel=self.parallel,
                        iterate_only_in_states=self.iterate_only_in_states,
                    )
                ],
            )
        else:
            if self.per_item is not None:
                raise ValueError(
                    "Pipeline declares both 'per_item' (legacy) and "
                    "'levels' (multi-level). Set one or the other, "
                    "not both."
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
    category: str | None = Field(
        default=None,
        description=(
            "Higher-level grouping shown in the new-run-view workflow "
            "picker (post-26 redesign) as a dropdown header. Free-form "
            "string; normalized to lower case via ``normalized_category`` "
            "before comparison. Examples: 'design' (design-pass "
            "workflows like tdd-design), 'implementation' (tdd-implement), "
            "'legacy' (older tdd-serial-* kept for analysis reference). "
            "``None`` clusters under 'other'."
        ),
    )

    @property
    def normalized_category(self) -> str:
        """Case-insensitive category for grouping. Empty / None →
        ``"other"``. Mirrors ``DirectivePreset.normalized_category``."""
        if self.category is None:
            return "other"
        stripped = self.category.strip().lower()
        return stripped or "other"

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

        # Parent-feature scoping: when iterating tickets (the
        # tea-party / implementation / review meetings), don't dump
        # every feature + every contract_note into seed context.
        # Filter to the parent feature of this iteration's ticket.
        # This is what made Hatter sprawl — every M6 iteration was
        # getting the whole feature corpus.
        #
        # Feature artifacts: keep only those whose slug matches the
        # parent feature.
        # Contract_note utterances: keep only those whose thread_id
        # encodes the parent feature (M5 is per_item: feature so the
        # source thread_id is ``contract-negotiation-<feature>`` or
        # the pipeline equivalent). Disk-fallback notes don't carry
        # a feature in their synthesized thread_id; they pass through
        # — graceful degradation rather than silently filtering out
        # the cross-run case.
        if (
            current_item_kind == "ticket"
            and current_item_slug is not None
            and project_root is not None
            and (
                "feature" in binding.kinds
                or "contract_note" in binding.kinds
                or "review" in binding.kinds
            )
        ):
            try:
                ticket_to_feature = _ticket_to_feature_map(project_root)
            except Exception:  # noqa: BLE001
                ticket_to_feature = {}
            parent_feature_slug = ticket_to_feature.get(current_item_slug)
            if parent_feature_slug:
                feature_scoped: list[Utterance] = []
                for u in kinded:
                    artifacts = u.content.artifacts
                    has_feature = any(
                        a.kind == "feature" for a in artifacts
                    )
                    has_contract = any(
                        a.kind == "contract_note" for a in artifacts
                    )
                    has_review = any(
                        a.kind == "review" for a in artifacts
                    )
                    keep = True
                    new_artifacts = list(artifacts)
                    if has_feature:
                        # Drop feature artifacts whose slug isn't the
                        # parent. If after the drop no feature
                        # artifact remains AND the utterance carried
                        # no other relevant kind, skip the utterance.
                        new_artifacts = [
                            a for a in new_artifacts
                            if a.kind != "feature"
                            or a.payload.get("slug") == parent_feature_slug
                        ]
                        remaining_features = [
                            a for a in new_artifacts if a.kind == "feature"
                        ]
                        if not remaining_features and has_feature and not (
                            has_contract
                            or any(
                                a.kind in binding.kinds and a.kind != "feature"
                                for a in artifacts
                            )
                        ):
                            keep = False
                    if has_contract and keep:
                        # Filter by thread_id: contract_negotiation
                        # threads encode the feature slug. Disk-
                        # fallback notes (thread_id == bare meeting
                        # id without the feature suffix) pass through.
                        tid = u.thread_id
                        is_feature_specific = (
                            "contract-negotiation-" in tid
                        )
                        if is_feature_specific:
                            # Pattern matches both sequential
                            # (``contract-negotiation-<feature>``) and
                            # pipeline (``pipe.<…>.contract-negotiation-<feature>``).
                            keep = (
                                f"contract-negotiation-{parent_feature_slug}"
                                in tid
                            )
                    if has_review and keep:
                        # Reviews from M8 (per_item: feature) — the
                        # thread_id encodes the feature when emitted
                        # in a feature-scoped iteration. Same
                        # graceful-degradation as contract_notes for
                        # disk-fallback reviews (bare ``review``
                        # thread_id has no feature suffix).
                        tid = u.thread_id
                        is_feature_specific_review = "review-" in tid
                        if is_feature_specific_review:
                            keep = (
                                f"review-{parent_feature_slug}" in tid
                            )
                    if keep:
                        if new_artifacts == list(artifacts):
                            feature_scoped.append(u)
                        else:
                            feature_scoped.append(
                                u.model_copy(
                                    update={
                                        "content": u.content.model_copy(
                                            update={"artifacts": new_artifacts}
                                        )
                                    }
                                )
                            )
                kinded = feature_scoped

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
            # Explicit per-ticket queue marks override the feature-
            # state gate. The operator's intent in queueing a
            # specific ticket is "iterate this one even if the
            # parent feature isn't otherwise in scope" — typical
            # case: feature in_progress, one ticket aborted on
            # budget, operator re-queues that ticket. We need the
            # iteration to proceed even though in_progress may not
            # be the only allowed state.
            try:
                from wonderland.ticket_lifecycle import (
                    TicketState,
                    get_state as get_ticket_state,
                )
            except Exception:  # noqa: BLE001
                get_ticket_state = None
                TicketState = None  # type: ignore[assignment]

            ticket_to_feature = _ticket_to_feature_map(project_root)
            for item in items:
                # Explicit ticket-level queue override: skip the
                # feature-state gate entirely.
                if get_ticket_state is not None and TicketState is not None:
                    tstate = get_ticket_state(project_root, item["slug"])
                    if tstate in (
                        TicketState.QUEUED,
                        TicketState.IN_PROGRESS,
                    ):
                        filtered.append(item)
                        continue
                feature_slug = ticket_to_feature.get(item["slug"])
                if feature_slug is None:
                    continue
                state = get_state(project_root, feature_slug)
                if state is not None and state in allowed:
                    filtered.append(item)
        elif item_kind == "feature":
            # Mirror the per-ticket override one level up: when the
            # outer pipeline iterates features and a sub-meeting
            # iterates tickets, a feature with explicitly-queued
            # tickets should be included even if the feature's own
            # state isn't in ``allowed``. Otherwise queueing a
            # ticket on an in-progress / done feature has no effect
            # because the lane never spawns.
            try:
                from wonderland.ticket_lifecycle import (
                    TicketState,
                    get_state as get_ticket_state,
                )
            except Exception:  # noqa: BLE001
                get_ticket_state = None
                TicketState = None  # type: ignore[assignment]
            features_with_queued_tickets: set[str] = set()
            if get_ticket_state is not None and TicketState is not None:
                ticket_to_feature = _ticket_to_feature_map(project_root)
                for ticket_slug, feature_slug in ticket_to_feature.items():
                    tstate = get_ticket_state(project_root, ticket_slug)
                    if tstate in (
                        TicketState.QUEUED,
                        TicketState.IN_PROGRESS,
                    ):
                        features_with_queued_tickets.add(feature_slug)
            for item in items:
                slug = item["slug"]
                if slug in features_with_queued_tickets:
                    filtered.append(item)
                    continue
                state = get_state(project_root, slug)
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
        # Ticket-state filter (per-ticket queueing). When the
        # operator has explicitly queued at least one ticket
        # belonging to THIS lane's feature, scope the iteration to
        # just the queued + in_progress set. The
        # in_progress allowance covers a mid-run state where the
        # substrate has flipped the ticket to in_progress for the
        # first iteration; subsequent meetings in the same lane
        # should still see it. When no ticket is explicitly
        # queued, we fall through — every ticket of the feature
        # iterates, preserving the legacy behavior.
        try:
            from wonderland.ticket_lifecycle import (
                TicketState,
                get_state as get_ticket_state,
            )
        except Exception:  # noqa: BLE001
            get_ticket_state = None
            TicketState = None  # type: ignore[assignment]
        if get_ticket_state is not None and TicketState is not None:
            ticket_states: dict[str, Any] = {
                it["slug"]: get_ticket_state(project_root, it["slug"])
                for it in items
            }
            explicitly_queued = [
                slug for slug, state in ticket_states.items()
                if state in (TicketState.QUEUED, TicketState.IN_PROGRESS)
            ]
            if explicitly_queued:
                queued_set = set(explicitly_queued)
                items = [it for it in items if it["slug"] in queued_set]
    elif (
        lane_outer_slug is not None
        and lane_outer_kind is not None
        and item_kind == lane_outer_kind
    ):
        # Lane's outer kind matches the meeting's iteration kind —
        # the meeting runs once for THIS lane's outer item.
        items = [it for it in items if it.get("slug") == lane_outer_slug]

    # For ticket items, attach blocked_by dependencies parsed from
    # each ticket's markdown so downstream code (Meeting.gates_on_
    # dependencies) can use them for inner-block gating without
    # re-reading disk per lane.
    if item_kind == "ticket" and project_root is not None and items:
        blocked_by = _ticket_blocked_by_map(project_root)
        # Lazy import to avoid a workflow ↔ ticket cycle at module-
        # load. read_ticket_stack_span reads each ticket's markdown
        # once to surface the field — used by Meeting.apply_roster_
        # filter at convene time.
        from wonderland.ticket import read_ticket_stack_span

        for item in items:
            slug = item.get("slug")
            if slug:
                item["blocked_by"] = blocked_by.get(slug, [])
                item["stack_span"] = read_ticket_stack_span(
                    project_root, slug
                ).value

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
    assert pipeline.levels is not None  # validator guarantees
    capture = WorkflowCapture()

    per_item_meetings: dict[str, str] = {
        m.id: m.per_item for m in workflow.meetings if m.per_item is not None
    }

    # Outer level — levels[0]. Inner levels (if any) get dispatched
    # by _run_lane when it encounters a meeting whose per_item matches
    # an inner level's per_item.
    outer_level = pipeline.levels[0]
    outer_items = _collect_per_item_items(
        item_kind=outer_level.per_item,
        state_filter=outer_level.iterate_only_in_states,
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
                outer_kind=outer_level.per_item,
                outer_slug=outer_slug,
                outer_label=lane_label,
                lane_index=idx + 1,
                lane_total=len(outer_items),
                lane_thread_prefix=lane_thread_prefix,
                inner_levels=pipeline.levels[1:],
                outer_item=outer_item,
                # Only the very first lane's first meeting is the
                # "entry" — receives the operator's directive. Other
                # lanes pick up the directive from the bus / disk.
                directive=directive if idx == 0 else None,
            ):
                yield event

        return _gen()

    iterators = [_make_lane(idx, item) for idx, item in enumerate(outer_items)]

    if outer_level.parallel:
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
    inner_levels: list[PipelineLevel] | None = None,
    outer_item: dict[str, Any] | None = None,
) -> AsyncIterator[Any]:
    """One lane of a pipelined workflow — runs meetings in declaration
    order, scoped to a single outer item.

    Per-meeting dispatch:
    - ``per_item: <outer_kind>`` (e.g., per_item: feature in a feature
      lane): runs once for THIS lane's outer item.
    - ``per_item: <inner-level kind>`` (e.g., per_item: ticket inside
      a feature lane when inner_levels declares a ticket level):
      groups consecutive same-inner-level meetings into a block,
      then runs the block as a per-sub-item inner pipeline. Inner
      sub-items run in parallel if the inner level says so.
    - ``per_item: <unscoped sub-kind>`` (no matching inner level):
      legacy behavior — iterate sub-items sequentially within the
      lane, one meeting at a time. Preserves single-level pipeline
      semantics for back-compat.
    - ``per_item: None``: runs once for the lane (treated as outer).

    True per-sub-item pipelining requires ``inner_levels`` to declare
    that level. Without inner_levels, the block fall-through is
    sequential (same as the original single-level pipeline).

    Thread ids are namespaced with ``lane_thread_prefix`` so
    ``resolve_seeds`` can scope cross-meeting bindings to this lane
    only.
    """
    inner_levels = inner_levels or []
    inner_kinds = {lvl.per_item: lvl for lvl in inner_levels}

    meetings = workflow.meetings
    i = 0
    is_first_meeting = True
    while i < len(meetings):
        meeting = meetings[i]
        meeting_directive = directive if is_first_meeting else None
        is_first_meeting = False

        # Outer-level meeting: runs once for this lane's outer item.
        if meeting.per_item is None or meeting.per_item == outer_kind:
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
                item_payload=outer_item,
            ):
                if isinstance(event, _OutcomeSentinel):
                    outcome = event.outcome
                    yield event
                    continue
                yield event
            if outcome == "GLOBAL_BUDGET":
                return
            i += 1
            continue

        # Inner-level meeting: gather consecutive meetings at the
        # same inner level into a block. The block runs as a per-
        # sub-item pipeline — each sub-item gets a lane that flows
        # through the block in declaration order. Lanes run in
        # parallel if the inner level config says so.
        if meeting.per_item in inner_kinds:
            inner_level = inner_kinds[meeting.per_item]
            block: list[Meeting] = []
            while (
                i < len(meetings)
                and meetings[i].per_item == inner_level.per_item
            ):
                block.append(meetings[i])
                i += 1

            sub_items = _collect_per_item_items(
                item_kind=inner_level.per_item,
                state_filter=None,
                capture=capture,
                runner=runner,
                lane_outer_kind=outer_kind,
                lane_outer_slug=outer_slug,
            )

            outcome = "RUNNING"
            async for event in _run_inner_block(
                block=block,
                sub_items=sub_items,
                parallel=inner_level.parallel,
                runner=runner,
                capture=capture,
                per_item_meetings=per_item_meetings,
                outer_label=outer_label,
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

        # Legacy sub-kind (no matching inner level): iterate sub-items
        # sequentially within the lane, one meeting at a time. This is
        # the original single-level pipeline semantic — preserved
        # exactly so workflows that don't declare ``levels`` keep
        # their pre-multi-level behavior.
        #
        # ``state_filter=None`` here on purpose: the pipeline's outer
        # filter already gated WHICH features get a lane; per-meeting
        # state filters within a lane would just fight the per-
        # iteration transitions (M6 fires queued → in_progress; M7's
        # legacy [queued] filter would then reject that same feature).
        sub_items = _collect_per_item_items(
            item_kind=meeting.per_item,
            state_filter=None,
            capture=capture,
            runner=runner,
            lane_outer_kind=outer_kind,
            lane_outer_slug=outer_slug,
        )

        if not sub_items:
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
            i += 1
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
                directive=None,
                per_item_meetings=per_item_meetings,
                current_item_kind=meeting.per_item,
                current_item_slug=sub_slug,
                thread_id=thread_id,
                iteration_index=sub_idx + 1,
                iteration_total=len(sub_items),
                iteration_label=f"{outer_label} / {sub_label}",
                lane_thread_prefix=lane_thread_prefix,
                item_payload=sub_item,
            ):
                if isinstance(event, _OutcomeSentinel):
                    outcome = event.outcome
                    yield event
                    continue
                yield event
            if outcome == "GLOBAL_BUDGET":
                return
        i += 1


async def _run_inner_block(
    *,
    block: list[Meeting],
    sub_items: list[dict[str, Any]],
    parallel: bool,
    runner: Runner,
    capture: WorkflowCapture,
    per_item_meetings: dict[str, str],
    outer_label: str,
    lane_thread_prefix: str,
) -> AsyncIterator[Any]:
    """Run a block of inner-level meetings as a per-sub-item pipeline.

    Each sub-item gets its own lane that flows through every meeting
    in ``block`` in declaration order. Lanes run via
    ``_merge_async_iterators`` when ``parallel=True`` (true pipeline:
    sub-item A finishing M6 immediately advances to M7 while sub-item
    B is still in M6), or sequentially when ``parallel=False``.

    Thread ids inside the inner block are namespaced
    ``{lane_thread_prefix}{meeting.id}-{sub_slug}`` — the SAME
    namespace as the lane's outer-level meetings, so seed resolution
    via ``lane_thread_prefix`` continues to scope correctly. The
    inner pipeline doesn't introduce a new prefix; it stays within
    the outer lane's scope.
    """
    if not sub_items:
        # No items to iterate — synthesize end events for each meeting
        # in the block so the consumer sees the meetings acknowledged.
        for meeting in block:
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
        return

    # Dependency-gating setup. For each gated meeting, build a map
    # (sub_item_slug, meeting_id) → asyncio.Event. A lane sets its
    # event when the meeting completes; a downstream lane awaits its
    # upstream lanes' events before starting the gated meeting.
    #
    # Validation up-front: drop deps that don't refer to an item in
    # this block, and break self-references / cycles by stripping
    # offending edges. Edge cases log a warning and fall through
    # (lane runs without waiting on the dropped edge).
    item_slugs_in_block = {item["slug"] for item in sub_items}
    sub_item_deps: dict[str, list[str]] = {}
    for item in sub_items:
        slug = item["slug"]
        raw = item.get("blocked_by") or []
        # Drop self-references (cycle of 1) and out-of-block refs.
        clean = [d for d in raw if d != slug and d in item_slugs_in_block]
        if len(clean) != len(raw):
            dropped = set(raw) - set(clean)
            logger.info(
                "ticket %r blocked_by has %d unmappable deps "
                "(self-ref or out-of-block): %s",
                slug,
                len(dropped),
                ", ".join(sorted(dropped)),
            )
        sub_item_deps[slug] = clean

    # Cycle detection: drop edges that participate in a cycle (Tarjan-
    # lite — for each item, see if it's reachable from any of its
    # deps). On cycle, drop ALL deps from the cycle members. Cheap
    # and conservative: parallel execution is the safe fallback.
    def _has_cycle(start: str, visited: set[str]) -> bool:
        if start in visited:
            return True
        visited = visited | {start}
        return any(
            _has_cycle(d, visited) for d in sub_item_deps.get(start, [])
        )

    for slug in list(sub_item_deps.keys()):
        if _has_cycle(slug, set()):
            if sub_item_deps[slug]:
                logger.warning(
                    "ticket %r blocked_by participates in a cycle; "
                    "dropping all deps to keep the lane unblocked",
                    slug,
                )
            sub_item_deps[slug] = []

    # One Event per (sub_item_slug, meeting_id). Created up-front so
    # any lane can await any other lane's event regardless of start
    # order under _merge_async_iterators.
    completion_events: dict[tuple[str, str], asyncio.Event] = {}
    for item in sub_items:
        for meeting in block:
            completion_events[(item["slug"], meeting.id)] = asyncio.Event()

    def _make_inner_lane(idx: int, sub_item: dict[str, Any]):
        sub_slug = sub_item["slug"]
        sub_label = sub_item.get("title") or sub_slug
        deps = sub_item_deps.get(sub_slug, [])

        async def _gen():
            for meeting in block:
                # Gate: wait for upstream lanes' SAME meeting to
                # complete. Skip when meeting doesn't gate or this
                # ticket has no deps.
                if meeting.gates_on_dependencies and deps:
                    for dep_slug in deps:
                        ev = completion_events.get((dep_slug, meeting.id))
                        if ev is not None:
                            await ev.wait()

                thread_id = f"{lane_thread_prefix}{meeting.id}-{sub_slug}"
                outcome = "RUNNING"
                try:
                    async for event in _run_one_meeting(
                        meeting=meeting,
                        runner=runner,
                        capture=capture,
                        directive=None,
                        per_item_meetings=per_item_meetings,
                        current_item_kind=meeting.per_item,
                        current_item_slug=sub_slug,
                        thread_id=thread_id,
                        iteration_index=idx + 1,
                        iteration_total=len(sub_items),
                        iteration_label=f"{outer_label} / {sub_label}",
                        lane_thread_prefix=lane_thread_prefix,
                        item_payload=sub_item,
                    ):
                        if isinstance(event, _OutcomeSentinel):
                            outcome = event.outcome
                            yield event
                            continue
                        yield event
                finally:
                    # Always set the completion event so downstream
                    # waiters unblock — even on GLOBAL_BUDGET or
                    # exception. If we don't set on abort, dependent
                    # lanes hang forever waiting.
                    completion_events[(sub_slug, meeting.id)].set()

                if outcome == "GLOBAL_BUDGET":
                    return

        return _gen()

    inner_iterators = [
        _make_inner_lane(idx, item) for idx, item in enumerate(sub_items)
    ]

    if parallel:
        async for event in _merge_async_iterators(inner_iterators):
            yield event
    else:
        for it in inner_iterators:
            async for event in it:
                yield event


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
                        item_payload=item,
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
                    item_payload=item,
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
                if not source:
                    continue
                # Normalise three observed Sources formats:
                #   bare slug:           ``earn-xp-and-level-up-...``
                #   kind-colon prefix:   ``feature: earn-xp-and-level-up-...``
                #   kind-dash prefix:    ``feature-earn-xp-and-level-up-...``
                # Rabbit's directive asks for bare slugs, but the
                # other two leak through in practice. Without this
                # normalisation, ~half the tickets get silently
                # dropped from the parent map — they never reach
                # the per-item iteration and the operator wonders
                # why the imp run skipped them.
                if source in feature_slugs:
                    out[ticket_record.slug] = source
                    break
                # ``<kind>: <slug>`` — strip the colon-prefix.
                if ":" in source:
                    _, _, rest = source.partition(":")
                    rest = rest.strip()
                    if rest in feature_slugs:
                        out[ticket_record.slug] = rest
                        break
                # ``feature-<slug>`` — strip the dash-prefix when
                # the result matches a registered feature. Guard:
                # don't strip if the bare slug happens to also
                # start with ``feature-`` for legitimate reasons
                # (we already checked that case above).
                if source.startswith("feature-"):
                    alt = source[len("feature-"):]
                    if alt in feature_slugs:
                        out[ticket_record.slug] = alt
                        break
    except Exception:  # noqa: BLE001 — best-effort
        return {}
    return out


def _ticket_blocked_by_map(project_root: Path) -> dict[str, list[str]]:
    """Build an index: ticket_slug → list of slugs it's blocked by.

    Source-of-truth: each ticket's ``- Blocked by: ...`` line in the
    Dependencies section of its markdown. Rabbit emits this during M3
    decomposition. Format examples:

        - Blocked by: —
        - Blocked by: schema-init, csv-parser

    The ``—`` placeholder (or ``-`` ASCII variant, or empty) means no
    upstream dependencies.

    Used by ``Meeting.gates_on_dependencies`` to determine which
    upstream tickets a per-ticket lane should wait for before starting
    its gated meeting (typically M7 — implementation that depends on
    upstream tickets' implementations).

    Best-effort: missing files / parse failures map to empty deps so
    the gate falls through (lane runs normally without waiting).
    """
    import re

    out: dict[str, list[str]] = {}
    try:
        from wonderland.ticket import TicketRegistry

        # Match the dash-prefixed "Blocked by:" line inside the
        # Dependencies block. Be lenient about whitespace; the slug
        # list comes after the colon. Capture the rest of the line.
        blocked_by_re = re.compile(
            r"^\s*-\s*Blocked\s+by:\s*(.+?)$",
            re.IGNORECASE | re.MULTILINE,
        )

        for ticket_record in TicketRegistry(project_root).list_tickets():
            try:
                text = ticket_record.path.read_text(encoding="utf-8")
            except OSError:
                continue
            match = blocked_by_re.search(text)
            if not match:
                out[ticket_record.slug] = []
                continue
            line = match.group(1).strip()
            if line in ("", "—", "-", "none", "None"):
                out[ticket_record.slug] = []
                continue
            deps = [s.strip() for s in line.split(",") if s.strip()]
            # Drop the literal placeholders just in case they appear
            # mid-list (defensive — Rabbit's prose has been
            # well-behaved here but a future agent might not be).
            deps = [d for d in deps if d not in ("—", "-", "none", "None")]
            out[ticket_record.slug] = deps
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


def _apply_emission_transition_for_utterance(
    *,
    meeting: Meeting,
    runner: Runner,
    utterance: Utterance,
) -> None:
    """Per-utterance transition_emitted_to. Fires immediately when
    a feature artifact lands on the bus, not post-MeetingEnd.

    Closes the race between feature.md being persisted to disk
    (synchronous inside the agent's decide-loop) and the lifecycle
    state record being written. The dashboard's auto-refresh
    subscribes to bus events and re-reads features on every emission;
    without an inline transition, it sees a feature.md without a
    state record and back-fills DESIGNED (project_dashboard.py:858),
    which then prevents the legitimate transition_emitted_to:
    proposed from succeeding (DESIGNED → PROPOSED is illegal).

    Symptom in obol's May 10 mock-data design pass: features 008-013
    all landed at ``designed`` state instead of ``proposed``, so M3's
    ``iterate_only_in_states: [proposed]`` filtered them all out and
    M3 hit the synthetic-skip path (zero items).

    Skipped silently when project_root is unavailable (FakeRunner)
    so the transition layer never breaks meeting flow.
    """
    project_root = getattr(runner, "project_root", None)
    if project_root is None or not meeting.transition_emitted_to:
        return

    from wonderland.feature_lifecycle import (
        FeatureState,
        IllegalTransitionError,
        transition,
    )

    try:
        target = FeatureState(meeting.transition_emitted_to)
    except ValueError:
        return

    for a in utterance.content.artifacts:
        if a.kind != "feature":
            continue
        slug = a.payload.get("slug")
        if not slug:
            continue
        try:
            transition(
                project_root,
                slug,
                target,
                by="system",
                notes=(
                    f"Auto-transition from meeting "
                    f"{meeting.id!r} on emission"
                ),
            )
        except IllegalTransitionError:
            # Already in a non-allowed state — idempotent behavior.
            # Re-running the workflow on a project past this point
            # shouldn't fail.
            pass


def _find_blocking_review(
    new_utterances: list[Utterance], feature_slug: str
) -> dict | None:
    """Scan utterances emitted during this iteration for a review
    artifact whose verdict is request-changes or block. Returns the
    artifact's full payload dict (slug, findings, target_files, etc.)
    when found, else None.

    Used by ``_apply_post_meeting_transitions`` to route around the
    normal feature → ready_for_review transition when Caterpillar
    flags issues — instead, the substrate synthesizes follow-up
    tickets from the review's findings and the original iteration's
    tickets transition to DONE.
    """
    del feature_slug  # Reserved for future scoping; one feature
    # per M8 iteration today so the iteration's utterances are
    # already correctly scoped.
    for u in new_utterances:
        for a in u.content.artifacts:
            if a.kind != "review":
                continue
            verdict = a.payload.get("verdict")
            if verdict in ("request-changes", "block"):
                return dict(a.payload)
    return None


def _find_accept_review(
    new_utterances: list[Utterance],
) -> str | None:
    """Mirror of ``_find_blocking_review`` for accept verdicts.
    Returns the review slug when a review with verdict=accept ships
    in this iteration; else None."""
    for u in new_utterances:
        for a in u.content.artifacts:
            if a.kind != "review":
                continue
            if a.payload.get("verdict") == "accept":
                slug = a.payload.get("slug")
                if isinstance(slug, str) and slug:
                    return slug
                title = a.payload.get("title")
                if isinstance(title, str):
                    return title
                return "(unknown review)"
    return None


def _complete_tickets_on_accept_review(
    project_root: Path,
    *,
    feature_slug: str,
    review_slug: str,
    actor: str,
    meeting_id: str,
) -> None:
    """Mark every IN_PROGRESS ticket of ``feature_slug`` as DONE.
    With the derived-feature-state work, the feature's
    ready_for_review rollup depends on all-tickets-DONE; this is
    the success-path counterpart to the request-changes
    abort path.

    Tickets in other states (PENDING / DONE / ABORTED / QUEUED) are
    left alone — DONE is for "we just iterated this and Caterpillar
    approved", not for retroactively marking everything in the
    feature."""
    from wonderland.ticket_lifecycle import (
        IllegalTransitionError as TicketIllegal,
        TicketState,
        get_state as get_ticket_state,
        transition as ticket_transition,
    )

    notes = (
        f"Auto-complete from {meeting_id!r} on accept verdict "
        f"({review_slug!r})."
    )
    ticket_to_feature = _ticket_to_feature_map(project_root)
    feature_tickets = [
        slug for slug, feat in ticket_to_feature.items()
        if feat == feature_slug
    ]
    for ticket_slug in feature_tickets:
        state = get_ticket_state(project_root, ticket_slug)
        if state != TicketState.IN_PROGRESS:
            continue
        try:
            ticket_transition(
                project_root,
                ticket_slug,
                TicketState.DONE,
                by=actor,
                notes=notes,
            )
        except TicketIllegal:
            continue


# Finding severities that justify synthesizing a follow-up
# ticket. ``block`` and ``change-required`` map to "do this work
# before merging"; ``suggestion`` and ``note`` stay informational
# in the review artifact and don't spawn new iterations.
_TICKETABLE_FINDING_SEVERITIES: frozenset[str] = frozenset(
    {"block", "change-required"}
)


def _stack_span_for_finding_location(
    location: str,
) -> "TicketStackSpan":
    """Heuristic: map a finding's ``file:line`` location to a
    stack_span. Frontend paths land Tweedledee's follow-up,
    backend paths land Tweedledum's; mixed / unrecognised stays
    full-stack. Operator can re-label on the dashboard if the
    heuristic guesses wrong."""
    from wonderland.ticket import TicketStackSpan

    if not isinstance(location, str):
        return TicketStackSpan.FULL_STACK
    lower = location.lower()
    frontend_markers = (
        "/frontend/", "frontend/src/", "/src/components/",
        "/src/pages/", "/src/app.tsx", ".tsx", ".jsx", ".css",
    )
    backend_markers = (
        "/backend/", "/src/backend/", "/api/", "/models.py",
        "/main.py", "/migrations/", ".sql",
    )
    is_fe = any(m in lower for m in frontend_markers)
    is_be = any(m in lower for m in backend_markers)
    if is_fe and not is_be:
        return TicketStackSpan.FRONTEND
    if is_be and not is_fe:
        return TicketStackSpan.BACKEND
    return TicketStackSpan.FULL_STACK


def _synthesize_followup_ticket_from_finding(
    finding: dict,
    *,
    parent_feature_slug: str,
    review_slug: str,
) -> "TicketPayload | None":
    """Convert a single ``ReviewFinding`` dict into a TicketPayload.
    Returns None when the severity isn't ticket-worthy.

    Field mapping:
      - title ← finding.title (Caterpillar's noun-phrase heading)
      - description ← finding.concern + finding.request
        (concern names what's wrong; request names what would
        resolve it)
      - sources ← [parent_feature_slug, review_slug] so the
        ticket markdown's Sources line links back to its
        provenance
      - stack_span ← derived from finding.location
      - owner ← derived from stack_span
      - tier ← V1 (these are merge-blockers; high priority)
      - estimate ← "tbd — operator should refine" placeholder
    """
    from wonderland.ticket import (
        TicketPayload,
        TicketStackSpan,
        TicketTier,
    )

    severity = finding.get("severity")
    if (
        not isinstance(severity, str)
        or severity not in _TICKETABLE_FINDING_SEVERITIES
    ):
        return None
    title = finding.get("title")
    concern = finding.get("concern")
    request = finding.get("request")
    if not all(isinstance(v, str) and v.strip() for v in (
        title, concern, request,
    )):
        # Skip malformed findings — schema should prevent this
        # but defensive against partial reads.
        return None
    location = finding.get("location", "")
    stack_span = _stack_span_for_finding_location(
        location if isinstance(location, str) else ""
    )
    owner = {
        TicketStackSpan.FRONTEND: "tweedledee",
        TicketStackSpan.BACKEND: "tweedledum",
        TicketStackSpan.FULL_STACK: "tweedledee",  # arbitrary default
    }[stack_span]
    description = (
        f"From review ``{review_slug}`` ({severity}):\n\n"
        f"**Concern:** {concern.strip()}\n\n"
        f"**Request:** {request.strip()}\n\n"
        f"**Location:** ``{location}``"
    )
    return TicketPayload(
        title=title.strip(),
        owner=owner,
        tier=TicketTier.V1,
        stack_span=stack_span,
        estimate="tbd — operator should refine",
        description=description,
        sources=[parent_feature_slug, review_slug],
        acceptance=[request.strip()],
    )


def _route_blocking_review(
    project_root: Path,
    *,
    feature_slug: str,
    review_payload: dict,
    actor: str,
    meeting_id: str,
) -> None:
    """Request-changes path:

      1. Mark the iteration's IN_PROGRESS tickets as DONE — their
         implementation work shipped and Caterpillar's findings
         are coherence gaps to address in follow-up work, not
         "the original tickets failed entirely".
      2. Convert ticket-worthy findings (severity ``block`` /
         ``change-required``) into new TicketPayloads; write them
         to disk via TicketRegistry; transition them to QUEUED
         via ticket_lifecycle so the next imp run iterates only
         the follow-ups.
      3. Lower-severity findings (suggestion / note) stay
         informational in the review artifact — no new tickets,
         no operator burden.

    The feature itself doesn't need an explicit transition: with
    derived feature state, the rollup picks up the new QUEUED
    tickets and lands on ``queued`` (or ``in_progress`` once the
    operator launches the retry imp run).
    """
    from wonderland.ticket import TicketRegistry
    from wonderland.ticket_lifecycle import (
        IllegalTransitionError as TicketIllegal,
        TicketState,
        back_fill_state,
        get_state as get_ticket_state,
        transition as ticket_transition,
    )

    review_slug = (
        review_payload.get("slug")
        or review_payload.get("title")
        or "(unknown review)"
    )

    # Step 1: mark in-flight tickets DONE.
    ticket_to_feature = _ticket_to_feature_map(project_root)
    feature_tickets = [
        slug for slug, feat in ticket_to_feature.items()
        if feat == feature_slug
    ]
    done_notes = (
        f"Auto-complete from {meeting_id!r} on request-changes "
        f"verdict ({review_slug!r}); follow-up tickets synthesized "
        f"from review findings."
    )
    for ticket_slug in feature_tickets:
        state = get_ticket_state(project_root, ticket_slug)
        if state is None:
            try:
                back_fill_state(
                    project_root,
                    ticket_slug,
                    TicketState.IN_PROGRESS,
                    notes=(
                        "Back-filled to in_progress before "
                        "request-changes done-marking"
                    ),
                )
                state = TicketState.IN_PROGRESS
            except Exception:  # noqa: BLE001
                continue
        if state != TicketState.IN_PROGRESS:
            continue
        try:
            ticket_transition(
                project_root,
                ticket_slug,
                TicketState.DONE,
                by=actor,
                notes=done_notes,
            )
        except TicketIllegal:
            continue

    # Step 2: synthesize follow-up tickets from findings.
    findings = review_payload.get("findings")
    if not isinstance(findings, list):
        return
    registry = TicketRegistry(project_root)
    queue_notes = (
        f"Synthesized from review ``{review_slug}`` finding; "
        f"queued for next imp run."
    )
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        payload = _synthesize_followup_ticket_from_finding(
            finding,
            parent_feature_slug=feature_slug,
            review_slug=str(review_slug),
        )
        if payload is None:
            continue
        try:
            record = registry.write(payload)
        except Exception:  # noqa: BLE001 — registry write
            # could fail on disk pressure / duplicate slug; skip
            # this finding's follow-up rather than break the
            # meeting flow.
            continue
        # Transition the new ticket to QUEUED so it's picked up
        # on the next imp run. Back-fill PENDING first since
        # fresh tickets have no lifecycle record yet.
        try:
            back_fill_state(
                project_root,
                record.slug,
                TicketState.PENDING,
                notes=queue_notes,
            )
            ticket_transition(
                project_root,
                record.slug,
                TicketState.QUEUED,
                by=actor,
                notes=queue_notes,
            )
        except TicketIllegal:
            continue
        except Exception:  # noqa: BLE001
            continue


def _apply_post_meeting_transitions(
    *,
    meeting: Meeting,
    runner: Runner,
    new_utterances: list[Utterance],
    current_item_slug: str | None,
) -> None:
    """T87 output transitions — fire feature lifecycle transitions
    after a meeting completes successfully.

    Handles ``transition_iteration_to`` for per_item meetings that
    operate ON existing features (M3, M4, M5, M6). The iteration's
    feature_slug (from ``current_item_slug``) transitions to the
    named state. Fires once per iteration that completed — the
    caller gates on outcome=='COMPLETE' so failed iterations don't
    transition.

    ``transition_emitted_to`` is handled per-utterance (see
    ``_apply_emission_transition_for_utterance``) to close the
    dashboard-backfill race; not duplicated here.

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

    # transition_iteration_to: fire once for the iteration's
    # target. Two semantics depending on per_item kind:
    #
    #   - per_item: feature → target the FEATURE state (M3, M5 in
    #     tdd-design; both pre-ticket phases). Transition fires on
    #     ``current_item_slug`` via feature_lifecycle.
    #
    #   - per_item: ticket  → target the TICKET state via
    #     ticket_lifecycle. Tdd-implement's M6 fires this to flip
    #     the queued ticket → in_progress on iteration end;
    #     ticket_lifecycle.LEGAL_TRANSITIONS gates which moves are
    #     legal so a re-iteration of an in-flight ticket no-ops.
    #
    # The blocking/accept review routing below still applies AT THE
    # FEATURE LEVEL (M8 only — it's the meeting that emits reviews).
    if meeting.transition_iteration_to and current_item_slug:
        # Per-ticket transition path: route through ticket_lifecycle.
        # Don't fall through to feature_lifecycle when the meeting's
        # iteration unit is a ticket — under derived-feature-state
        # the feature transition becomes a duplicate side channel
        # anyway.
        if meeting.per_item == "ticket":
            from wonderland.ticket_lifecycle import (
                IllegalTransitionError as _TicketIllegal,
                TicketState,
                back_fill_state as ticket_back_fill,
                get_state as get_ticket_state,
                transition as ticket_transition,
            )

            try:
                ticket_target = TicketState(
                    meeting.transition_iteration_to
                )
            except ValueError:
                ticket_target = None
            if ticket_target is not None:
                state = get_ticket_state(project_root, current_item_slug)
                if state is None:
                    # No record yet — back-fill PENDING so the
                    # forward transition is legal.
                    try:
                        ticket_back_fill(
                            project_root,
                            current_item_slug,
                            TicketState.PENDING,
                            notes=(
                                "Back-filled before iteration "
                                f"transition from {meeting.id!r}"
                            ),
                        )
                    except Exception:  # noqa: BLE001
                        pass
                try:
                    ticket_transition(
                        project_root,
                        current_item_slug,
                        ticket_target,
                        by=actor,
                        notes=(
                            f"Auto-transition from iteration of "
                            f"{meeting.id!r} on COMPLETE"
                        ),
                    )
                except _TicketIllegal:
                    pass
            return

        # Per-feature transition path (M3, M5 in tdd-design).
        try:
            target = FeatureState(meeting.transition_iteration_to)
        except ValueError:
            target = None
        if target is not None and current_item_slug:
            try:
                transition(
                    project_root,
                    current_item_slug,
                    target,
                    by=actor,
                    notes=(
                        f"Auto-transition from iteration of "
                        f"{meeting.id!r} on COMPLETE"
                    ),
                )
            except IllegalTransitionError:
                pass

    # Review-verdict routing. Runs independently of
    # ``transition_iteration_to`` so M8 can drop its now-redundant
    # ``transition_iteration_to: ready_for_review`` (derivation
    # handles the feature rollup once tickets are DONE). Fires when
    # the meeting emitted a review artifact, regardless of per_item
    # kind — practically that's only M8 (per_item: feature) today
    # but the wiring doesn't care.
    if current_item_slug and meeting.per_item == "feature":
        feature_slug = current_item_slug
        blocking_review = _find_blocking_review(
            new_utterances, feature_slug
        )
        if blocking_review is not None:
            _route_blocking_review(
                project_root,
                feature_slug=feature_slug,
                review_payload=blocking_review,
                actor=actor,
                meeting_id=meeting.id,
            )
            return
        accept_review = _find_accept_review(new_utterances)
        if accept_review is not None:
            _complete_tickets_on_accept_review(
                project_root,
                feature_slug=feature_slug,
                review_slug=accept_review,
                actor=actor,
                meeting_id=meeting.id,
            )


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
    item_payload: dict[str, Any] | None = None,
) -> AsyncIterator[Any]:
    """Dispatch a single meeting (or per_item iteration) onto either
    the legacy engagement-policy path (``_convene_one``) or the
    phased orchestrator (``meeting.run_phased_meeting``) based on
    whether ``meeting.phases`` is non-empty.

    Phase semantics are strictly opt-in (analysis 033 / P9 T57):
    workflows without a ``phases:`` declaration retain the original
    parallel-multicast behavior unchanged.

    ``item_payload`` carries the per_item iteration's full payload
    dict (slug, title, stack_span, blocked_by, etc.) so this
    function can apply ``meeting.per_item_roster_filter`` before
    dispatching. Callers without a per_item context pass None.
    """
    # Apply the per-iteration roster filter, if any. Narrows the
    # roster + team_groupings for this iteration only; original
    # ``meeting`` object remains unchanged.
    if item_payload is not None:
        meeting = meeting.apply_roster_filter(item_payload)
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

        # Capture index before the phased orchestrator runs so we can
        # slice out new_utterances for transition_iteration_to gating.
        # Mirrors _convene_one's bookkeeping (which uses the same
        # artifact_count_before / new_utterances pattern).
        phased_artifact_count_before = len(capture.utterances)

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
            # Per-utterance transition_emitted_to fires on the phased
            # path too. The phased orchestrator yields RunnerEvent with
            # kind="utterance" for each agent emission (meeting.py
            # line ~628), same shape as the convene-one path. Without
            # this hook, M2's transition_emitted_to: proposed never
            # fires for phased meetings, leaving features at no-state
            # → dashboard back-fills DESIGNED on auto-refresh →
            # M3's iterate_only_in_states: [proposed] filters them
            # all out → M3 hits "(no items)" skip.
            if (
                hasattr(event, "kind")
                and event.kind == "utterance"
                and event.payload is not None
            ):
                emitted = event.payload.get("utterance")
                if emitted is not None:
                    _apply_emission_transition_for_utterance(
                        meeting=meeting,
                        runner=runner,
                        utterance=emitted,
                    )

            # transition_iteration_to fires on phased COMPLETE just
            # like the convene-one path. Without this, M3's
            # transition_iteration_to: in_design never fires for
            # phased meetings, leaving M3-decomposed features stuck
            # at proposed → M5's iterate_only_in_states: [in_design]
            # filters them all out → M5 hits "(no items)" skip.
            # Same dispatch-asymmetry shape that bit transition_emitted_to.
            if (
                isinstance(event, MeetingEndEvent)
                and event.outcome == "COMPLETE"
            ):
                phased_new_utterances = (
                    capture.utterances[phased_artifact_count_before:]
                )
                _apply_post_meeting_transitions(
                    meeting=meeting,
                    runner=runner,
                    new_utterances=phased_new_utterances,
                    current_item_slug=current_item_slug,
                )

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
                emitted = event.payload["utterance"]
                capture.observe(emitted)
                # transition_emitted_to fires per-utterance, not post-
                # MeetingEnd, to close the dashboard-backfill race
                # (project_dashboard.py:858 backfills DESIGNED on
                # auto-refresh if there's no lifecycle record yet).
                _apply_emission_transition_for_utterance(
                    meeting=meeting,
                    runner=runner,
                    utterance=emitted,
                )

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
    # calls_delta uses calls_for_thread (per-thread) instead of the
    # global call_count delta, otherwise pipeline-mode parallel lanes
    # contaminate each other's counts: when ticket-A's M7 finishes,
    # call_count - calls_before includes calls that tickets B and C
    # made concurrently during ticket-A's window, inflating the
    # reported call count by 3-4× (the live-watch's "454 calls" rows
    # on meetings that actually made ~80 LLM calls). Pairs cleanly
    # with cost_delta which already used the per-thread accumulator.
    calls_delta = runner.telemetry.calls_for_thread(thread_id)
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
