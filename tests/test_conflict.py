"""Tests for the conflict-resolution data types."""

from __future__ import annotations

from wonderland import (
    DOMAIN_PRIMACY,
    Conflict,
    ConflictDomain,
    Dissent,
    Resolution,
    domain_owner,
)

# ---------- DOMAIN_PRIMACY ----------


def test_domain_primacy_covers_every_domain() -> None:
    """Every ConflictDomain must have an owner — leaving one out would
    silently produce KeyError at the worst possible time (escalation)."""
    for domain in ConflictDomain:
        assert domain in DOMAIN_PRIMACY


def test_domain_primacy_assigns_canonical_names() -> None:
    """Cross-check the spec §7 table against canonical agent names."""
    expected = {
        ConflictDomain.USER_NEED: "alice",
        ConflictDomain.ARCHITECTURE: "cheshire_cat",
        ConflictDomain.SEQUENCE: "white_rabbit",
        ConflictDomain.SEVERITY: "mad_hatter",
        ConflictDomain.CODE_QUALITY: "caterpillar",
        ConflictDomain.SECURITY: "queen_of_hearts",
        ConflictDomain.PRODUCTION: "dormouse",
    }
    assert expected == DOMAIN_PRIMACY


def test_domain_owner_lookup() -> None:
    assert domain_owner(ConflictDomain.ARCHITECTURE) == "cheshire_cat"
    assert domain_owner(ConflictDomain.USER_NEED) == "alice"


# ---------- Dissent ----------


def test_dissent_construction() -> None:
    d = Dissent(
        speaker="cheshire_cat",
        position="this couples the layers in a way that will hurt later",
        rationale="the seam is the schema; collapsing it costs us a future migration",
    )
    assert d.speaker == "cheshire_cat"
    assert "couples the layers" in d.position
    assert "seam is the schema" in d.rationale


def test_dissent_rationale_optional() -> None:
    d = Dissent(speaker="cheshire_cat", position="...")
    assert d.rationale == ""


# ---------- Conflict ----------


def test_conflict_construction() -> None:
    conflict = Conflict(
        thread_id="t",
        proposals=("01J0", "01J1"),
        proposal_bodies=(
            ("cheshire_cat", "use a queue"),
            ("white_rabbit", "this slips us past Thursday"),
        ),
        domain_hint=ConflictDomain.SEQUENCE,
    )
    assert conflict.thread_id == "t"
    assert len(conflict.proposals) == 2
    assert conflict.domain_hint is ConflictDomain.SEQUENCE


def test_conflict_domain_hint_optional() -> None:
    conflict = Conflict(thread_id="t", proposals=("01J0",))
    assert conflict.domain_hint is None


# ---------- Resolution ----------


def test_resolution_composed_shape() -> None:
    resolution = Resolution(
        thread_id="t",
        composed=True,
        composition_text="The Cat's queue + Rabbit's Thursday cut compose: queue with a 1-day budget.",
        rationale="the proposals address different axes",
    )
    assert resolution.is_composition is True
    assert resolution.needs_escalation is False


def test_resolution_not_composed_shape() -> None:
    resolution = Resolution(
        thread_id="t",
        composed=False,
        suggested_domain=ConflictDomain.ARCHITECTURE,
        suggested_owner="cheshire_cat",
        rationale="the disagreement is about whether to add a layer at all",
    )
    assert resolution.is_composition is False
    assert resolution.needs_escalation is True
    assert resolution.suggested_owner == "cheshire_cat"


def test_resolution_carries_dissents() -> None:
    resolution = Resolution(
        thread_id="t",
        composed=True,
        composition_text="...",
        dissents=(Dissent(speaker="white_rabbit", position="this slips Thursday"),),
    )
    assert len(resolution.dissents) == 1
    assert resolution.dissents[0].speaker == "white_rabbit"


def test_resolution_default_no_dissents() -> None:
    resolution = Resolution(thread_id="t", composed=True, composition_text="...")
    assert resolution.dissents == ()
