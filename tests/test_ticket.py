"""Tests for the Ticket writer + registry."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from wonderland import (
    TicketDependencies,
    TicketPayload,
    TicketRegistry,
    TicketStatus,
    TicketTier,
    render_ticket,
)

# ---------- TicketPayload validation ----------


def test_payload_requires_non_empty_title() -> None:
    with pytest.raises(ValidationError):
        TicketPayload(
            title="",
            owner="tweedledee",
            tier=TicketTier.V1,
            estimate="1d",
            description="x",
        )


def test_payload_requires_non_empty_owner() -> None:
    with pytest.raises(ValidationError):
        TicketPayload(
            title="t",
            owner="",
            tier=TicketTier.V1,
            estimate="1d",
            description="x",
        )


def test_payload_requires_estimate() -> None:
    """The Rabbit always estimates — non-negotiable per §I."""
    with pytest.raises(ValidationError):
        TicketPayload(
            title="t",
            owner="tweedledee",
            tier=TicketTier.V1,
            estimate="",
            description="x",
        )


def test_payload_requires_description() -> None:
    with pytest.raises(ValidationError):
        TicketPayload(
            title="t",
            owner="tweedledee",
            tier=TicketTier.V1,
            estimate="1d",
            description="",
        )


def test_payload_default_status_is_open() -> None:
    payload = TicketPayload(
        title="t",
        owner="tweedledee",
        tier=TicketTier.V1,
        estimate="1d",
        description="d",
    )
    assert payload.status is TicketStatus.OPEN


def test_payload_default_dependencies_are_empty() -> None:
    payload = TicketPayload(
        title="t",
        owner="tweedledee",
        tier=TicketTier.V1,
        estimate="1d",
        description="d",
    )
    assert payload.dependencies.blocks == []
    assert payload.dependencies.blocked_by == []
    assert payload.dependencies.soft == []


def test_payload_dependencies_can_be_specified() -> None:
    payload = TicketPayload(
        title="t",
        owner="tweedledee",
        tier=TicketTier.V1,
        estimate="1d",
        description="d",
        dependencies=TicketDependencies(blocked_by=["ticket-001-foo"], soft=["ticket-002-bar"]),
    )
    assert payload.dependencies.blocked_by == ["ticket-001-foo"]
    assert payload.dependencies.soft == ["ticket-002-bar"]


@pytest.mark.parametrize("tier", [TicketTier.V1, TicketTier.FAST_FOLLOW, TicketTier.POST_LAUNCH])
def test_payload_accepts_each_tier(tier: TicketTier) -> None:
    payload = TicketPayload(
        title="t",
        owner="tweedledee",
        tier=tier,
        estimate="1d",
        description="d",
    )
    assert payload.tier is tier


def test_payload_rejects_unknown_tier() -> None:
    with pytest.raises(ValidationError):
        TicketPayload(
            title="t",
            owner="tweedledee",
            tier="someday",  # type: ignore[arg-type]
            estimate="1d",
            description="d",
        )


@pytest.mark.parametrize(
    "bad_source",
    [
        "contract-note-003",
        "adr-001-stack-locked",
        "milestone-01-onboarding",
        "requirement-007-marcus",
        "retraction-x",
        "review-002",
        "ticket-001",
    ],
)
def test_payload_rejects_non_feature_source_prefix(bad_source: str) -> None:
    """T-m7 substrate guard: tickets descend from features (and
    optionally stories), not from contract-notes / ADRs / etc."""
    with pytest.raises(ValidationError):
        TicketPayload(
            title="t",
            owner="tweedledum",
            tier=TicketTier.V1,
            estimate="1d",
            description="d",
            sources=[bad_source],
        )


def test_payload_accepts_feature_and_story_sources() -> None:
    """Slugs that don't match a known non-feature prefix pass through —
    the validator can't tell a feature slug from a story slug without
    a registry lookup, so both are accepted by shape."""
    payload = TicketPayload(
        title="t",
        owner="tweedledum",
        tier=TicketTier.V1,
        estimate="1d",
        description="d",
        sources=["marcus-onboarding-flow", "story-007"],
    )
    assert payload.sources == ["marcus-onboarding-flow", "story-007"]


# ---------- render_ticket ----------


def test_render_ticket_includes_all_required_sections() -> None:
    payload = TicketPayload(
        title="Implement message translation pipeline",
        owner="tweedledum",
        tier=TicketTier.V1,
        estimate="1.5-3 days, 60% confident",
        description="Wire the translation provider into the message send path.",
        sources=["story-007", "proposal-002"],
        acceptance=["A→B message arrives translated", "translation latency p95 < 500ms"],
        risk="auth integration may bite — expand to 4d if so",
    )
    out = render_ticket(7, payload)

    assert "## Ticket 007: Implement message translation pipeline" in out
    assert "**Sources:** story-007, proposal-002" in out
    assert "**Owner:** tweedledum" in out
    assert "**Tier:** v1" in out
    assert "**Estimate:** 1.5-3 days, 60% confident" in out
    assert "**Status:** open" in out
    assert "**Dependencies:**" in out
    assert "- Blocks: —" in out
    assert "**Description:**" in out
    assert "Wire the translation provider" in out
    assert "**Acceptance:**" in out
    assert "- A→B message arrives translated" in out
    assert "**Risk:**" in out
    assert "auth integration may bite" in out


def test_render_ticket_omits_risk_section_when_empty() -> None:
    payload = TicketPayload(
        title="t",
        owner="tweedledee",
        tier=TicketTier.V1,
        estimate="1d",
        description="d",
    )
    out = render_ticket(1, payload)
    assert "**Risk:**" not in out


def test_render_ticket_renders_dependencies() -> None:
    payload = TicketPayload(
        title="t",
        owner="tweedledee",
        tier=TicketTier.V1,
        estimate="1d",
        description="d",
        dependencies=TicketDependencies(
            blocks=["ticket-002-foo"],
            blocked_by=["ticket-001-baseline"],
            soft=["ticket-003-style"],
        ),
    )
    out = render_ticket(5, payload)
    assert "- Blocks: ticket-002-foo" in out
    assert "- Blocked by: ticket-001-baseline" in out
    assert "- Soft: ticket-003-style" in out


def test_render_ticket_three_digit_padding() -> None:
    payload = TicketPayload(
        title="t",
        owner="tweedledee",
        tier=TicketTier.V1,
        estimate="1d",
        description="d",
    )
    out = render_ticket(2, payload)
    assert "## Ticket 002:" in out


def test_render_ticket_acceptance_placeholder_when_empty() -> None:
    payload = TicketPayload(
        title="t",
        owner="tweedledee",
        tier=TicketTier.V1,
        estimate="1d",
        description="d",
    )
    out = render_ticket(1, payload)
    assert "- (to be filled)" in out


# ---------- TicketRegistry — empty state ----------


def test_empty_registry_lists_no_tickets(tmp_path: Path) -> None:
    registry = TicketRegistry(tmp_path)
    assert registry.list_tickets() == []


def test_empty_registry_next_number_is_one(tmp_path: Path) -> None:
    registry = TicketRegistry(tmp_path)
    assert registry.next_number() == 1


def test_empty_registry_find_returns_none(tmp_path: Path) -> None:
    registry = TicketRegistry(tmp_path)
    assert registry.find_by_slug("anything") is None
    assert registry.find_by_number(1) is None


def test_path_is_under_dot_wonderland_tickets(tmp_path: Path) -> None:
    registry = TicketRegistry(tmp_path)
    assert registry.path == tmp_path / ".wonderland" / "tickets"


# ---------- TicketRegistry — write ----------


def test_write_creates_file_at_expected_path(tmp_path: Path) -> None:
    registry = TicketRegistry(tmp_path)
    record = registry.write(
        TicketPayload(
            title="Implement /health endpoint",
            owner="tweedledum",
            tier=TicketTier.V1,
            estimate="0.5d",
            description="Standard liveness endpoint for the Phoenix app.",
        )
    )
    assert record.number == 1
    assert record.slug == "implement-health-endpoint"
    assert record.title == "Implement /health endpoint"
    # T-g3: filename embeds short_guid for substrate identity.
    expected = (
        tmp_path
        / ".wonderland"
        / "tickets"
        / f"ticket-{record.guid[:8]}-implement-health-endpoint.md"
    )
    assert record.path == expected
    assert record.path.is_file()


def test_write_creates_parent_directory(tmp_path: Path) -> None:
    registry = TicketRegistry(tmp_path)
    payload = TicketPayload(
        title="t",
        owner="tweedledee",
        tier=TicketTier.V1,
        estimate="1d",
        description="d",
    )
    registry.write(payload)
    assert registry.path.is_dir()


def test_write_accepts_dict_payload(tmp_path: Path) -> None:
    registry = TicketRegistry(tmp_path)
    record = registry.write(
        {
            "title": "Wire constitution loader",
            "owner": "tweedledum",
            "tier": "v1",
            "estimate": "0.5d",
            "description": "Read constitutions/<name>.md, parse header, return Identity.",
        }
    )
    assert record.title == "Wire constitution loader"


def test_write_rejects_payload_without_estimate(tmp_path: Path) -> None:
    registry = TicketRegistry(tmp_path)
    with pytest.raises(ValidationError):
        registry.write(
            {
                "title": "t",
                "owner": "tweedledee",
                "tier": "v1",
                "estimate": "",
                "description": "d",
            }
        )


def test_write_auto_increments_number(tmp_path: Path) -> None:
    registry = TicketRegistry(tmp_path)
    a = registry.write(_simple("A"))
    b = registry.write(_simple("B"))
    c = registry.write(_simple("C"))
    assert (a.number, b.number, c.number) == (1, 2, 3)


def test_write_re_emit_same_slug_updates_in_place(tmp_path: Path) -> None:
    """P15 follow-up — update-by-slug semantics. Rabbit re-emitting
    the same ticket across M3 iterations now overwrites in place
    rather than creating ticket-001 + ticket-008 with similar
    content (discovery5 pilot)."""
    registry = TicketRegistry(tmp_path)
    first = registry.write(_simple("Ship the registration form"))
    second = registry.write(_simple("Ship the registration form"))
    assert first.number == second.number == 1
    assert first.path == second.path
    files = sorted(registry.path.glob("ticket-*.md"))
    assert len(files) == 1


def test_written_file_round_trips_through_render_ticket(tmp_path: Path) -> None:
    registry = TicketRegistry(tmp_path)
    payload = TicketPayload(
        title="Caucus event bus",
        owner="tweedledum",
        tier=TicketTier.V1,
        estimate="1.5d",
        description="Redis Streams-backed bus with InMemory stub.",
        acceptance=["publish/subscribe roundtrip", "fan-out to multiple subscribers"],
    )
    record = registry.write(payload)
    assert record.read() == render_ticket(1, payload)


# ---------- TicketRegistry — queries ----------


def test_list_tickets_in_number_order(tmp_path: Path) -> None:
    registry = TicketRegistry(tmp_path)
    for title in ("Third", "First", "Second"):
        registry.write(_simple(title))
    listing = registry.list_tickets()
    assert [r.number for r in listing] == [1, 2, 3]
    assert [r.title for r in listing] == ["Third", "First", "Second"]


def test_find_by_slug(tmp_path: Path) -> None:
    registry = TicketRegistry(tmp_path)
    registry.write(_simple("Wire bus subscribers"))
    found = registry.find_by_slug("wire-bus-subscribers")
    assert found is not None
    assert found.title == "Wire bus subscribers"


def test_find_by_number(tmp_path: Path) -> None:
    registry = TicketRegistry(tmp_path)
    registry.write(_simple("A"))
    registry.write(_simple("B"))
    found = registry.find_by_number(2)
    assert found is not None
    assert found.title == "B"


def test_registry_skips_non_ticket_files(tmp_path: Path) -> None:
    registry = TicketRegistry(tmp_path)
    registry.write(_simple("A"))
    (registry.path / "README.md").write_text("not a ticket")
    (registry.path / "ticket-malformed.md").write_text("also not")
    listing = registry.list_tickets()
    assert len(listing) == 1


def test_next_number_with_gaps_picks_max_plus_one(tmp_path: Path) -> None:
    registry = TicketRegistry(tmp_path)
    registry.path.mkdir(parents=True, exist_ok=True)
    for n in (1, 4, 9):
        path = registry.path / f"ticket-{n:03d}-stub.md"
        path.write_text(f"## Ticket {n:03d}: Stub\n", encoding="utf-8")
    assert registry.next_number() == 10


# ---------- delete_by_slug ----------


def test_delete_by_slug_removes_file(tmp_path: Path) -> None:
    """The dashboard's prune flow uses this to drop duplicate tickets
    Rabbit shipped during M3 revision passes (analysis 040 issue)."""
    registry = TicketRegistry(tmp_path)
    record = registry.write(_simple("To be deleted"))
    assert record.path.is_file()

    assert registry.delete_by_slug("to-be-deleted") is True
    assert not record.path.is_file()
    # Registry list reflects the deletion.
    assert registry.find_by_slug("to-be-deleted") is None


def test_delete_by_slug_returns_false_for_unknown_slug(tmp_path: Path) -> None:
    registry = TicketRegistry(tmp_path)
    registry.write(_simple("Existing ticket"))
    assert registry.delete_by_slug("never-existed") is False
    # Existing ticket survives.
    assert registry.find_by_slug("existing-ticket") is not None


def test_delete_by_slug_doesnt_repack_numbering(tmp_path: Path) -> None:
    """Numbering tolerates gaps — deleting ticket-002 leaves
    ticket-001 and ticket-003 in place; next_number() returns 4
    (max + 1), matching the on-disk source-of-truth contract."""
    registry = TicketRegistry(tmp_path)
    a = registry.write(_simple("A"))
    b = registry.write(_simple("B"))
    c = registry.write(_simple("C"))
    assert (a.number, b.number, c.number) == (1, 2, 3)

    registry.delete_by_slug("b")
    remaining = registry.list_tickets()
    assert [r.number for r in remaining] == [1, 3]
    assert registry.next_number() == 4


# ---------- TicketSource + test_coverage_required (tea-party skip) ----------


class TestReadTicketNeedsTestDesign:
    """Validation of the read_ticket_needs_test_design helper that
    backs the tea-party (M6) iteration filter. Source-based default
    + explicit override semantics."""

    def test_m3_decomposition_default_passes(self, tmp_path: Path) -> None:
        from wonderland.ticket import (
            TicketSource,
            read_ticket_needs_test_design,
        )

        reg = TicketRegistry(tmp_path)
        reg.write(
            TicketPayload(
                title="Fresh from M3",
                owner="tweedledee",
                tier=TicketTier.V1,
                estimate="1d",
                description="x",
                source=TicketSource.M3_DECOMPOSITION,
            )
        )
        assert read_ticket_needs_test_design(tmp_path, "fresh-from-m3") is True

    def test_review_synthesis_default_skips(self, tmp_path: Path) -> None:
        from wonderland.ticket import (
            TicketSource,
            read_ticket_needs_test_design,
        )

        reg = TicketRegistry(tmp_path)
        reg.write(
            TicketPayload(
                title="Fix the is_pending flag",
                owner="tweedledee",
                tier=TicketTier.V1,
                estimate="0.5d",
                description="x",
                source=TicketSource.REVIEW_SYNTHESIS,
            )
        )
        assert (
            read_ticket_needs_test_design(tmp_path, "fix-the-is-pending-flag")
            is False
        )

    def test_review_synthesis_with_override_passes(
        self, tmp_path: Path
    ) -> None:
        """Caterpillar can mark a finding test_coverage_required=True
        when the fix introduces uncovered behavior; the synthesized
        ticket then passes tea-party even though its source is
        review_synthesis."""
        from wonderland.ticket import (
            TicketSource,
            read_ticket_needs_test_design,
        )

        reg = TicketRegistry(tmp_path)
        reg.write(
            TicketPayload(
                title="Add JWT validation to auth",
                owner="tweedledum",
                tier=TicketTier.V1,
                estimate="2d",
                description="x",
                source=TicketSource.REVIEW_SYNTHESIS,
                test_coverage_required=True,
            )
        )
        assert (
            read_ticket_needs_test_design(
                tmp_path, "add-jwt-validation-to-auth"
            )
            is True
        )

    def test_m3_decomposition_with_skip_override_skips(
        self, tmp_path: Path
    ) -> None:
        """Operator can force-skip tea-party for a fresh ticket they
        consider already well-spec'd."""
        from wonderland.ticket import (
            TicketSource,
            read_ticket_needs_test_design,
        )

        reg = TicketRegistry(tmp_path)
        reg.write(
            TicketPayload(
                title="Rename column",
                owner="tweedledum",
                tier=TicketTier.V1,
                estimate="0.25d",
                description="x",
                source=TicketSource.M3_DECOMPOSITION,
                test_coverage_required=False,
            )
        )
        assert (
            read_ticket_needs_test_design(tmp_path, "rename-column") is False
        )

    def test_missing_ticket_defaults_to_pass(self, tmp_path: Path) -> None:
        """Missing-file / unparseable: default True (safer to over-
        include than silently skip)."""
        from wonderland.ticket import read_ticket_needs_test_design

        assert (
            read_ticket_needs_test_design(tmp_path, "nonexistent-slug") is True
        )


# ---------- helpers ----------


def _simple(title: str) -> TicketPayload:
    return TicketPayload(
        title=title,
        owner="tweedledee",
        tier=TicketTier.V1,
        estimate="1d",
        description="placeholder description",
    )
