"""Tests for phase + priority + rotation data primitives.

Per analysis 033 / T55. Covers the data model in isolation — no
engine wiring yet (T58). Tests verify construction invariants,
rotation arithmetic, the three completion conditions (succession,
exhaustion, exit-condition), and the per-agent counts that T60's
failure-mode detectors will piggyback on.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from wonderland.turns import (
    PhaseDefinition,
    PhaseState,
    WindowAction,
    WindowOutcome,
)


# --- PhaseDefinition ---


def test_phase_definition_constructs_with_defaults() -> None:
    p = PhaseDefinition(name="discussion")
    assert p.name == "discussion"
    assert p.max_rotations == 3
    assert p.exit_condition_artifact is None


def test_phase_definition_with_exit_condition() -> None:
    p = PhaseDefinition(
        name="negotiate",
        max_rotations=5,
        exit_condition_artifact="contract",
    )
    assert p.exit_condition_artifact == "contract"


def test_phase_definition_rejects_empty_name() -> None:
    with pytest.raises(ValueError, match="name"):
        PhaseDefinition(name="", max_rotations=3)


def test_phase_definition_rejects_zero_rotations() -> None:
    with pytest.raises(ValueError, match="max_rotations"):
        PhaseDefinition(name="discussion", max_rotations=0)


def test_phase_definition_is_frozen() -> None:
    p = PhaseDefinition(name="discussion")
    with pytest.raises(FrozenInstanceError):
        p.name = "other"  # type: ignore[misc]


# --- Two-Headed Giant team_groupings (T63 / P9.5) ---


def test_phase_definition_team_groupings_default_empty() -> None:
    p = PhaseDefinition(name="discussion")
    assert p.team_groupings == ()


def test_phase_definition_with_team_groupings() -> None:
    p = PhaseDefinition(
        name="clarify",
        team_groupings=(("alice", "hatter"), ("tweedledee", "tweedledum")),
    )
    assert len(p.team_groupings) == 2
    assert p.team_groupings[0] == ("alice", "hatter")


def test_phase_definition_team_overlap_rejected() -> None:
    with pytest.raises(ValueError, match="multiple teams"):
        PhaseDefinition(
            name="clarify",
            team_groupings=(("alice", "hatter"), ("alice", "tweedledee")),
        )


def test_phase_definition_empty_team_rejected() -> None:
    with pytest.raises(ValueError, match="empty teams"):
        PhaseDefinition(name="clarify", team_groupings=(("alice",), ()))


def test_next_team_default_is_single_agent_tuples() -> None:
    """When team_groupings is empty (the default), next_team
    returns single-member tuples — same shape as next_agent
    historically returned."""
    s = _state(cast=("a", "b", "c"))
    # Initial team = ("a",), single-member.
    assert s.next_team() == ("a",)
    assert s.next_agent() == "a"


def test_next_team_advances_through_teams() -> None:
    """With explicit team_groupings, next_team rotates through
    teams in declared order. Each team window resolves all its
    members before the next team's window opens."""
    s = PhaseState(
        definition=PhaseDefinition(
            name="clarify",
            max_rotations=2,
            team_groupings=(("alice", "hatter"), ("td", "tdm")),
        ),
        cast=("alice", "hatter", "td", "tdm"),
    )
    # Rotation 0, team 0
    assert s.next_team() == ("alice", "hatter")
    # Resolve both members of team 0
    s.outcomes.append(
        WindowOutcome(rotation_index=0, agent_id="alice", action=WindowAction.PASSED)
    )
    s.outcomes.append(
        WindowOutcome(rotation_index=0, agent_id="hatter", action=WindowAction.PASSED)
    )
    # Rotation 0, team 1
    assert s.next_team() == ("td", "tdm")
    # Resolve both
    s.outcomes.append(
        WindowOutcome(rotation_index=0, agent_id="td", action=WindowAction.PASSED)
    )
    s.outcomes.append(
        WindowOutcome(rotation_index=0, agent_id="tdm", action=WindowAction.PASSED)
    )
    # Rotation 0 complete; rotation 1, team 0 next
    assert s.current_rotation == 1
    # All-passed-in-succession (last len(cast)=4 windows all PASSED)
    assert s.is_complete()
    assert s.next_team() is None


def test_next_team_handles_uneven_teams() -> None:
    """Teams of different sizes (e.g. solo + paired) advance
    correctly: 1 + 2 = 3 windows per rotation; the rotation
    boundary respects the team sizes."""
    s = PhaseState(
        definition=PhaseDefinition(
            name="m6-defend",
            max_rotations=2,
            team_groupings=(("caterpillar",), ("td", "tdm")),
        ),
        cast=("caterpillar", "td", "tdm"),
    )
    # First window: solo caterpillar team
    assert s.next_team() == ("caterpillar",)
    s.outcomes.append(
        WindowOutcome(
            rotation_index=0, agent_id="caterpillar", action=WindowAction.ACTED,
            utterance_id="u-1",
        )
    )
    # Second window: paired Tweedles team
    assert s.next_team() == ("td", "tdm")


# --- WindowOutcome ---


def test_window_outcome_acted_with_utterance() -> None:
    o = WindowOutcome(
        rotation_index=0,
        agent_id="hatter",
        action=WindowAction.ACTED,
        utterance_id="u-1",
    )
    assert o.action == WindowAction.ACTED
    assert o.utterance_id == "u-1"


def test_window_outcome_passed_no_utterance() -> None:
    o = WindowOutcome(
        rotation_index=0,
        agent_id="cheshire_cat",
        action=WindowAction.PASSED,
    )
    assert o.utterance_id is None


def test_window_outcome_passed_with_utterance_rejected() -> None:
    """A PASSED window cannot reference an utterance — the agent
    by definition didn't speak."""
    with pytest.raises(ValueError, match="utterance_id"):
        WindowOutcome(
            rotation_index=0,
            agent_id="cat",
            action=WindowAction.PASSED,
            utterance_id="u-1",
        )


# --- PhaseState basics ---


def _state(
    cast: tuple[str, ...] = ("alice", "hatter", "cat"),
    max_r: int = 3,
    exit_artifact: str | None = None,
) -> PhaseState:
    return PhaseState(
        definition=PhaseDefinition(
            name="discussion",
            max_rotations=max_r,
            exit_condition_artifact=exit_artifact,
        ),
        cast=cast,
    )


def _act(state: PhaseState, agent: str, *, rotation: int | None = None) -> None:
    """Append an ACTED outcome at the implied next rotation."""
    r = rotation if rotation is not None else state.current_rotation
    state.outcomes.append(
        WindowOutcome(
            rotation_index=r,
            agent_id=agent,
            action=WindowAction.ACTED,
            utterance_id=f"u-{len(state.outcomes)}",
        )
    )


def _pass(state: PhaseState, agent: str, *, rotation: int | None = None) -> None:
    r = rotation if rotation is not None else state.current_rotation
    state.outcomes.append(
        WindowOutcome(
            rotation_index=r,
            agent_id=agent,
            action=WindowAction.PASSED,
        )
    )


def test_phase_state_starts_empty() -> None:
    s = _state()
    assert s.windows_opened == 0
    assert s.current_rotation == 0
    assert not s.is_complete()
    assert not s.is_exhausted()
    assert not s.all_passed_in_succession()


def test_phase_state_rejects_empty_cast() -> None:
    with pytest.raises(ValueError, match="cast"):
        PhaseState(definition=PhaseDefinition(name="d"), cast=())


def test_phase_state_first_agent_is_first_in_cast() -> None:
    s = _state(cast=("alice", "hatter", "cat"))
    assert s.next_agent() == "alice"


# --- Rotation arithmetic ---


def test_phase_state_rotation_advances_after_full_pass() -> None:
    s = _state(cast=("a", "b", "c"))
    for agent in ("a", "b", "c"):
        _act(s, agent)
    assert s.current_rotation == 1
    assert s.next_agent() == "a"


def test_phase_state_next_agent_cycles() -> None:
    s = _state(cast=("a", "b", "c"))
    expected = ["a", "b", "c", "a", "b", "c", "a"]
    actual: list[str] = []
    for _ in expected:
        nxt = s.next_agent()
        assert nxt is not None
        actual.append(nxt)
        _act(s, nxt)
    assert actual == expected


# --- Termination: all_passed_in_succession ---


def test_all_passed_in_succession_first_rotation() -> None:
    s = _state(cast=("a", "b", "c"))
    for agent in ("a", "b", "c"):
        _pass(s, agent)
    assert s.all_passed_in_succession()
    assert s.is_complete()
    assert s.next_agent() is None


def test_all_passed_in_succession_requires_full_cast_size() -> None:
    s = _state(cast=("a", "b", "c"))
    _pass(s, "a")
    _pass(s, "b")
    # Only 2 of 3 cast-size, not yet "all passed"
    assert not s.all_passed_in_succession()


def test_all_passed_in_succession_resets_after_act() -> None:
    """If anyone ACTED in the last len(cast) windows, the chain is
    broken even if the surrounding windows are passes."""
    s = _state(cast=("a", "b", "c"))
    _pass(s, "a")
    _act(s, "b")
    _pass(s, "c")
    assert not s.all_passed_in_succession()


def test_all_passed_succession_succeeds_after_intervening_rotation() -> None:
    """Earlier acts don't poison later succession — the check is
    last-N-windows, not entire-history."""
    s = _state(cast=("a", "b", "c"))
    # Rotation 0: someone acts — chain broken.
    _pass(s, "a")
    _act(s, "b")
    _pass(s, "c")
    # Rotation 1: everyone passes — last 3 are all PASSED now.
    _pass(s, "a")
    _pass(s, "b")
    _pass(s, "c")
    assert s.all_passed_in_succession()
    assert s.is_complete()


# --- Termination: rotation budget exhaustion ---


def test_is_exhausted_at_max_rotations() -> None:
    s = _state(cast=("a", "b", "c"), max_r=2)
    for r in (0, 1):
        for agent in ("a", "b", "c"):
            _act(s, agent, rotation=r)
    assert s.current_rotation == 2
    assert s.is_exhausted()
    assert s.is_complete()
    assert s.next_agent() is None


def test_is_not_exhausted_mid_rotation() -> None:
    """Mid-rotation, exhaustion shouldn't fire — only when a full
    rotation completes does the budget tick."""
    s = _state(cast=("a", "b", "c"), max_r=3)
    _act(s, "a", rotation=0)
    _act(s, "b", rotation=0)
    # Two of three windows in rotation 0 — no full rotations done yet
    assert s.current_rotation == 0
    assert not s.is_exhausted()


# --- Termination: workflow exit condition ---


def test_exit_condition_met_completes_phase() -> None:
    s = _state(cast=("a", "b", "c"), exit_artifact="contract")
    _act(s, "a")
    s.exit_condition_met = True
    assert s.is_complete()
    assert s.next_agent() is None


def test_exit_condition_overrides_remaining_budget() -> None:
    """A shipped exit-condition artifact ends the phase even with
    rotation budget left over."""
    s = _state(cast=("a", "b", "c"), max_r=10, exit_artifact="contract")
    _act(s, "a")
    s.exit_condition_met = True
    assert s.is_complete()
    # Budget wasn't actually consumed
    assert s.current_rotation == 0


# --- Per-agent counts (T60 substrate) ---


def test_passes_per_agent_counts_sprawl_and_withdrawal_shapes() -> None:
    """Hatter never passes (sprawl shape); Cat always passes after
    his first window (withdrawal shape) — the two §VIII shapes T60
    will detect."""
    s = _state(cast=("hatter", "cat", "alice"))
    # Rotation 0: Hatter acts, Cat acts, Alice acts (everyone engaged)
    _act(s, "hatter")
    _act(s, "cat")
    _act(s, "alice")
    # Rotation 1: Hatter still acts, Cat passes, Alice acts
    _act(s, "hatter")
    _pass(s, "cat")
    _act(s, "alice")
    # Rotation 2: Hatter still acts, Cat passes, Alice passes
    _act(s, "hatter")
    _pass(s, "cat")
    _pass(s, "alice")

    passes = s.passes_per_agent()
    acts = s.acts_per_agent()
    assert passes == {"hatter": 0, "cat": 2, "alice": 1}
    assert acts == {"hatter": 3, "cat": 1, "alice": 2}


def test_passes_per_agent_initializes_unseen_agents_to_zero() -> None:
    """Cast members who never get a window still appear in the
    map with 0 — keeps downstream code simple."""
    s = _state(cast=("a", "b", "c"))
    _act(s, "a")
    counts = s.passes_per_agent()
    assert counts == {"a": 0, "b": 0, "c": 0}


# --- Interaction: completion shadows next_agent ---


def test_next_agent_returns_none_when_succession_ends_phase() -> None:
    s = _state(cast=("a", "b", "c"))
    _pass(s, "a")
    _pass(s, "b")
    _pass(s, "c")
    assert s.next_agent() is None


def test_next_agent_returns_none_when_exhausted() -> None:
    s = _state(cast=("a", "b"), max_r=1)
    _act(s, "a")
    _act(s, "b")
    assert s.is_exhausted()
    assert s.next_agent() is None
