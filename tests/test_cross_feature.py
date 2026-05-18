"""Tests for cross-feature ticket consolidation (T-a5).

Verifies the detector finds duplicate clusters spanning multiple
features, picks the best home via parent-source overlap, and
auto-aborts the duplicates via ticket_lifecycle.
"""

from __future__ import annotations

from pathlib import Path

from wonderland.cross_feature import (
    ConsolidationDecision,
    consolidate_cross_feature_duplicates,
    find_cross_feature_duplicates,
)
from wonderland.ticket_lifecycle import (
    TicketState,
    get_state as get_ticket_state,
)


def _write_feature(
    project_root: Path, slug: str, sources: list[str],
    guid: str = "01ABCDEF",
) -> None:
    """Write a minimal feature markdown."""
    feat_dir = project_root / ".wonderland" / "features"
    feat_dir.mkdir(parents=True, exist_ok=True)
    body = (
        f"## Feature 001: {slug}\n\n"
        f"**GUID:** {guid}\n"
        f"**Sources:** {', '.join(sources)}\n"
        f"**Stack span:** backend\n\n"
        f"**Description:**\n\nx\n"
    )
    (feat_dir / f"feature-{guid}-{slug}.md").write_text(body, encoding="utf-8")


def _write_ticket(
    project_root: Path, slug: str, sources: list[str],
    guid: str = "01TICKEE",
) -> None:
    """Write a minimal ticket markdown with the Sources line."""
    tic_dir = project_root / ".wonderland" / "tickets"
    tic_dir.mkdir(parents=True, exist_ok=True)
    body = (
        f"## Ticket 001: {slug}\n\n"
        f"**GUID:** {guid}\n"
        f"**Sources:** {', '.join(sources)}\n"
        f"**Owner:** tweedledum\n"
        f"**Tier:** v1\n"
        f"**Stack span:** backend\n"
        f"**Estimate:** 0.5d\n\n"
        f"**Description:**\n\nx\n"
    )
    (tic_dir / f"ticket-{guid}-{slug}.md").write_text(body, encoding="utf-8")


# ---------- detection ----------


def test_no_duplicates_when_each_ticket_has_unique_upstream(
    tmp_path: Path,
) -> None:
    """Two features, each with one ticket whose upstream sources
    are distinct → no consolidation."""
    _write_feature(tmp_path, "feat-a", ["story-a1"], guid="01AAAAAA")
    _write_feature(tmp_path, "feat-b", ["story-b1"], guid="01BBBBBB")
    _write_ticket(tmp_path, "ticket-a", ["feat-a", "story-a1"], guid="01TKTAAA")
    _write_ticket(tmp_path, "ticket-b", ["feat-b", "story-b1"], guid="01TKTBBB")
    decisions = find_cross_feature_duplicates(tmp_path)
    assert decisions == []


def test_detects_cross_feature_duplicate(tmp_path: Path) -> None:
    """Two features each have a ticket sourcing the same upstream
    story → cluster detected."""
    _write_feature(tmp_path, "feat-persist", ["story-schema", "story-crud"], guid="01AAAAAA")
    _write_feature(tmp_path, "feat-test", ["story-fixtures"], guid="01BBBBBB")
    _write_ticket(
        tmp_path, "schema-under-persist",
        ["feat-persist", "story-schema"],
        guid="01TKTAAA",
    )
    _write_ticket(
        tmp_path, "schema-under-test",
        ["feat-test", "story-schema"],
        guid="01TKTBBB",
    )
    decisions = find_cross_feature_duplicates(tmp_path)
    assert len(decisions) == 1
    d = decisions[0]
    # feat-persist's sources include story-schema; feat-test's don't
    # → feat-persist's ticket wins
    assert d.kept_parent_feature == "feat-persist"
    assert d.kept_slug == "schema-under-persist"
    assert d.retracted_slugs == ("schema-under-test",)
    assert d.upstream_sources == frozenset({"story-schema"})


def test_tie_break_deterministic_on_slug(tmp_path: Path) -> None:
    """When two parent features score equally, the alphabetically
    first slug wins."""
    _write_feature(tmp_path, "feat-a", ["story-shared"], guid="01AAAAAA")
    _write_feature(tmp_path, "feat-b", ["story-shared"], guid="01BBBBBB")
    _write_ticket(
        tmp_path, "z-ticket-under-a",
        ["feat-a", "story-shared"],
        guid="01TKTZZZ",
    )
    _write_ticket(
        tmp_path, "a-ticket-under-b",
        ["feat-b", "story-shared"],
        guid="01TKTAAA",
    )
    decisions = find_cross_feature_duplicates(tmp_path)
    assert len(decisions) == 1
    # Both feature.sources match equally well; tie-break on slug:
    # "a-ticket-under-b" < "z-ticket-under-a"
    assert decisions[0].kept_slug == "a-ticket-under-b"


def test_intra_feature_duplicates_ignored(tmp_path: Path) -> None:
    """Two tickets in the SAME feature with the same upstream:
    M3.5 handles that. M3.75 only fires on cross-feature dupes."""
    _write_feature(tmp_path, "feat-a", ["story-x"], guid="01AAAAAA")
    _write_ticket(
        tmp_path, "ticket-1",
        ["feat-a", "story-x"],
        guid="01TKT111",
    )
    _write_ticket(
        tmp_path, "ticket-2",
        ["feat-a", "story-x"],
        guid="01TKT222",
    )
    decisions = find_cross_feature_duplicates(tmp_path)
    assert decisions == []  # Same parent feature → not cross-feature


def test_orphan_ticket_without_parent_feature_ignored(
    tmp_path: Path,
) -> None:
    """A ticket whose sources don't include any feature slug is
    orphan → skipped."""
    _write_feature(tmp_path, "feat-a", ["story-x"], guid="01AAAAAA")
    _write_ticket(
        tmp_path, "orphan-ticket",
        ["story-x"],  # No feature slug in sources
        guid="01TKT111",
    )
    decisions = find_cross_feature_duplicates(tmp_path)
    assert decisions == []


def test_handles_guid_slug_source_form(tmp_path: Path) -> None:
    """T-g5 form: sources may be 'guid:slug'. Detector strips the
    guid prefix before clustering."""
    _write_feature(tmp_path, "feat-a", ["story-schema"], guid="01AAAAAA")
    _write_feature(tmp_path, "feat-b", ["story-schema"], guid="01BBBBBB")
    _write_ticket(
        tmp_path, "ticket-under-a",
        ["01AAAA:feat-a", "01STORYY:story-schema"],
        guid="01TKTAAA",
    )
    _write_ticket(
        tmp_path, "ticket-under-b",
        ["01BBBB:feat-b", "01STORYY:story-schema"],
        guid="01TKTBBB",
    )
    decisions = find_cross_feature_duplicates(tmp_path)
    assert len(decisions) == 1
    # Cluster's upstream sources are the cleaned slugs
    assert "story-schema" in decisions[0].upstream_sources


# ---------- apply (end-to-end) ----------


def test_consolidate_aborts_retracted_tickets(tmp_path: Path) -> None:
    """consolidate_cross_feature_duplicates transitions retracted
    tickets to ABORTED in the lifecycle log; keeps the winner
    untouched."""
    _write_feature(tmp_path, "feat-persist", ["story-schema"], guid="01AAAAAA")
    _write_feature(tmp_path, "feat-test", [], guid="01BBBBBB")
    _write_ticket(
        tmp_path, "schema-under-persist",
        ["feat-persist", "story-schema"],
        guid="01TKTAAA",
    )
    _write_ticket(
        tmp_path, "schema-under-test",
        ["feat-test", "story-schema"],
        guid="01TKTBBB",
    )

    applied = consolidate_cross_feature_duplicates(tmp_path)
    assert len(applied) == 1
    decision = applied[0]
    assert decision.kept_slug == "schema-under-persist"

    # Winner's lifecycle untouched (no record exists yet)
    assert get_ticket_state(tmp_path, "schema-under-persist") is None

    # Loser is ABORTED
    assert get_ticket_state(tmp_path, "schema-under-test") == TicketState.ABORTED

    # Both files still exist on disk (forensics)
    tickets_dir = tmp_path / ".wonderland" / "tickets"
    assert (tickets_dir / "ticket-01TKTAAA-schema-under-persist.md").exists()
    assert (tickets_dir / "ticket-01TKTBBB-schema-under-test.md").exists()


def test_consolidate_idempotent_on_already_aborted(tmp_path: Path) -> None:
    """Re-running consolidation on already-aborted tickets: no
    error, decisions list reflects already-applied state."""
    _write_feature(tmp_path, "feat-a", ["story-x"], guid="01AAAAAA")
    _write_feature(tmp_path, "feat-b", [], guid="01BBBBBB")
    _write_ticket(
        tmp_path, "t-a", ["feat-a", "story-x"], guid="01TKTAAA",
    )
    _write_ticket(
        tmp_path, "t-b", ["feat-b", "story-x"], guid="01TKTBBB",
    )
    first = consolidate_cross_feature_duplicates(tmp_path)
    assert len(first) == 1
    second = consolidate_cross_feature_duplicates(tmp_path)
    # Second call sees already-aborted tickets; still reports the
    # decision but no actual changes
    assert len(second) == 1
    assert get_ticket_state(tmp_path, "t-b") == TicketState.ABORTED


def test_no_features_no_decisions(tmp_path: Path) -> None:
    """Project with no features → no decisions, no errors."""
    decisions = find_cross_feature_duplicates(tmp_path)
    assert decisions == []
    applied = consolidate_cross_feature_duplicates(tmp_path)
    assert applied == []
