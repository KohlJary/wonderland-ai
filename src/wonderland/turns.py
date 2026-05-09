"""Phase + priority + rotation primitives for the meeting engine.

Per analysis 033 — data model for MtG-style turn structure inside a
meeting. Phases are workflow-declared sequences within a meeting; in
each phase, every cast member gets a priority window in rotation;
agents either act (one utterance) or pass; the phase advances when
all cast members pass in succession, when the rotation budget
exhausts, or when a workflow-declared exit-condition artifact ships.

This module is data-only — dataclasses, enums, pure-function state
queries. The engine wiring lives in workflow.py / runner.py and
consumes these types. Per the no-anchoring lesson (analysis 030 F1),
nothing here is surfaced into agent context; rotations are an
engine-side measurement primitive, not an agent-facing budget.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class WindowAction(str, Enum):
    """What an agent did with their priority window."""

    ACTED = "acted"
    PASSED = "passed"


@dataclass(frozen=True)
class PhaseDefinition:
    """A phase declared by the workflow.

    Phases are sub-units of a meeting. Engine-side counterpart to
    ``wonderland.workflow.PhaseSpec`` — same fields, but framework-
    free (frozen dataclass, not Pydantic), so the meeting engine
    can construct + manipulate phases without dragging the schema
    layer along.
    """

    name: str
    max_rotations: int = 3
    exit_condition_artifact: str | None = None
    """If set, the phase ends when an artifact of this kind ships.
    Lets a phase be 'until the contract is signed' rather than
    'for N rotations.'"""
    team_groupings: tuple[tuple[str, ...], ...] = ()
    """Two-Headed Giant team partition (analysis 034 F2 / P9.5).
    Empty tuple = one-agent-per-team (each agent gets their own
    serial priority window — the original P9 behavior). Non-empty =
    explicit teams; agents within the same team open their windows
    concurrently inside one team window, recovering the parallelism
    that constitutional pairs deserve. Frozen-tuple-of-tuples (not
    list-of-lists) so PhaseDefinition stays hashable."""

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("phase name cannot be empty")
        if self.max_rotations < 1:
            raise ValueError(
                f"max_rotations must be >= 1, got {self.max_rotations}"
            )
        # Basic team_groupings sanity. Cast-coverage validation
        # (every cast member in exactly one team) lives at the
        # workflow / Meeting level since PhaseDefinition doesn't
        # carry the cast.
        if self.team_groupings:
            seen: set[str] = set()
            for team in self.team_groupings:
                if not team:
                    raise ValueError(
                        "team_groupings cannot contain empty teams"
                    )
                for member in team:
                    if member in seen:
                        raise ValueError(
                            f"agent {member!r} appears in multiple "
                            f"teams in phase {self.name!r}"
                        )
                    seen.add(member)


@dataclass(frozen=True)
class WindowOutcome:
    """What happened in a single priority window.

    The window is identified by ``(rotation_index, agent_id)`` —
    at most one window per agent per rotation. ``utterance_id``
    is set when the agent acted, so the outcome can be cross-
    referenced against the utterance bus.
    """

    rotation_index: int
    agent_id: str
    action: WindowAction
    utterance_id: str | None = None

    def __post_init__(self) -> None:
        if (
            self.action == WindowAction.PASSED
            and self.utterance_id is not None
        ):
            raise ValueError(
                f"PASSED window cannot carry an utterance_id "
                f"(got {self.utterance_id!r})"
            )


@dataclass
class PhaseState:
    """Runtime state of a phase in flight.

    Carries the immutable ``definition`` + the immutable ``cast`` (the
    priority order) + the append-only ``outcomes`` history. Every
    derived property — current rotation, next agent, completion —
    computes from ``outcomes``, so the data model has a single source
    of truth.
    """

    definition: PhaseDefinition
    cast: tuple[str, ...]
    """Priority order for this phase. First agent in the tuple gets
    the first window of every rotation."""
    outcomes: list[WindowOutcome] = field(default_factory=list)
    """Append-only history of every window in this phase."""
    exit_condition_met: bool = False
    """Set by the engine when the phase's exit_condition_artifact
    ships. Phase-end logic reads it via is_complete()."""

    def __post_init__(self) -> None:
        if not self.cast:
            raise ValueError("phase cast cannot be empty")

    @property
    def windows_opened(self) -> int:
        return len(self.outcomes)

    @property
    def current_rotation(self) -> int:
        """Number of *completed* rotations. 0 before the first
        rotation finishes; equals ``max_rotations`` when the budget
        is fully spent. Cast non-emptiness is enforced in
        ``__post_init__`` so the divisor is always >= 1."""
        return len(self.outcomes) // len(self.cast)

    def all_passed_in_succession(self) -> bool:
        """True iff the last ``len(cast)`` windows are all PASSED.

        That's the natural phase-end condition: every cast member
        passed their most recent window without an act breaking the
        chain. Returns False until at least one full rotation of
        windows has opened.
        """
        n = len(self.cast)
        if len(self.outcomes) < n:
            return False
        return all(
            o.action == WindowAction.PASSED for o in self.outcomes[-n:]
        )

    def is_exhausted(self) -> bool:
        """True when the rotation budget is fully spent.

        Distinct from ``all_passed_in_succession`` — exhaustion is
        the forced phase-end, succession is the natural one.
        """
        return self.current_rotation >= self.definition.max_rotations

    def is_complete(self) -> bool:
        """The phase is done — by exit condition, by everyone passing
        in succession, or by rotation budget exhaustion."""
        return (
            self.exit_condition_met
            or self.all_passed_in_succession()
            or self.is_exhausted()
        )

    def next_agent(self) -> str | None:
        """The agent whose priority window comes next, or ``None`` if
        the phase is complete. Equivalent to ``next_team()[0]`` —
        kept for backward compatibility with single-agent rotation
        callers."""
        team = self.next_team()
        return team[0] if team else None

    def next_team(self) -> tuple[str, ...] | None:
        """The team whose window comes next, or ``None`` if the
        phase is complete. When ``team_groupings`` is empty (the
        default), each agent is their own team — this returns a
        single-member tuple matching ``next_agent()``'s historical
        behavior. When ``team_groupings`` is set (Two-Headed Giant
        / P9.5), the returned tuple has multiple members and the
        orchestrator opens windows for them concurrently."""
        if self.is_complete():
            return None
        teams = self._effective_teams()
        pos_in_rotation = len(self.outcomes) % len(self.cast)
        cumulative = 0
        for team in teams:
            cumulative += len(team)
            if pos_in_rotation < cumulative:
                return team
        # Defensive: cumulative coverage of cast guaranteed by
        # PhaseDefinition validation, so this is unreachable.
        return teams[0]

    def _effective_teams(self) -> tuple[tuple[str, ...], ...]:
        """Resolve the team partition for rotation logic. When
        ``team_groupings`` is empty (the default), each cast member
        is their own team — preserves the original P9 single-agent
        rotation. When set, return as-is."""
        if self.definition.team_groupings:
            return self.definition.team_groupings
        return tuple((agent,) for agent in self.cast)

    def passes_per_agent(self) -> dict[str, int]:
        """Count of PASSED outcomes per agent, across the phase.

        Used by T60's failure-mode detectors:
        - never-passes is sprawl shape (Hatter §VIII)
        - always-passes-after-first is withdrawal shape (Cat §VIII)
        """
        counts: dict[str, int] = dict.fromkeys(self.cast, 0)
        for o in self.outcomes:
            if o.action == WindowAction.PASSED:
                counts[o.agent_id] = counts.get(o.agent_id, 0) + 1
        return counts

    def acts_per_agent(self) -> dict[str, int]:
        """Count of ACTED outcomes per agent, across the phase."""
        counts: dict[str, int] = dict.fromkeys(self.cast, 0)
        for o in self.outcomes:
            if o.action == WindowAction.ACTED:
                counts[o.agent_id] = counts.get(o.agent_id, 0) + 1
        return counts


__all__ = [
    "PhaseDefinition",
    "PhaseState",
    "WindowAction",
    "WindowOutcome",
]
