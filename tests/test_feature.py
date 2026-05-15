"""Tests for the Feature writer + registry — Rabbit's M2.5 grouping artifact."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from wonderland import (
    FeaturePayload,
    FeatureRegistry,
    StackSpan,
    TicketTier,
    render_feature,
)


# ---------- FeaturePayload validation ----------


def test_payload_requires_non_empty_title() -> None:
    with pytest.raises(ValidationError):
        FeaturePayload(
            title="",
            description="x",
            tickets=["t1"],
            stack_span=StackSpan.FRONTEND,
            tier=TicketTier.V1,
            sources=["s"],
        )


def test_payload_requires_non_empty_description() -> None:
    with pytest.raises(ValidationError):
        FeaturePayload(
            title="t",
            description="",
            tickets=["t1"],
            stack_span=StackSpan.FRONTEND,
            tier=TicketTier.V1,
            sources=["s"],
        )


def test_payload_accepts_empty_tickets_at_m2_ship_time() -> None:
    """Post-T88 workflow: M2 ships features BEFORE M3 decomposes
    them into tickets, so feature.tickets is empty when Rabbit
    first emits the feature. The ticket→feature link is recorded
    on the ticket side (ticket.sources). Old constraint
    ``min_length=1`` is dropped because it fought the intended
    flow — Rabbit was emitting concerns about the schema instead
    of shipping features.
    """
    payload = FeaturePayload(
        title="empty-at-ship-time",
        description="M3 will populate tickets later",
        tickets=[],  # empty at M2 ship time — M3 fills via reverse-index
        stack_span=StackSpan.FRONTEND,
        tier=TicketTier.V1,
        sources=["seeded-story"],
    )
    assert payload.tickets == []


def test_payload_validates_stack_span_enum() -> None:
    with pytest.raises(ValidationError):
        FeaturePayload(
            title="t",
            description="x",
            tickets=["t1"],
            stack_span="middleware",  # type: ignore[arg-type]
            tier=TicketTier.V1,
        )


def test_payload_validates_tier_enum() -> None:
    with pytest.raises(ValidationError):
        FeaturePayload(
            title="t",
            description="x",
            tickets=["t1"],
            stack_span=StackSpan.FRONTEND,
            tier="someday",  # type: ignore[arg-type]
        )


def test_payload_optional_fields_default_empty() -> None:
    payload = FeaturePayload(
        title="t",
        description="x",
        tickets=["t1"],
        stack_span=StackSpan.FRONTEND,
        tier=TicketTier.V1,
        sources=["s"],
    )
    # ``personas`` remains optional; ``sources`` is required (T-m8b
    # follow-up — features without sources are unmoored claims that
    # break the milestone-realization coverage walk).
    assert payload.personas == []
    assert payload.sources == ["s"]


def test_payload_rejects_empty_sources() -> None:
    """T-m8b follow-up — every feature must cite at least one story
    slug. The discovery2 pilot produced a feature with empty
    Sources line that broke the coverage walk; validator catches
    it at parse time so White Rabbit's retry loop fixes it."""
    with pytest.raises(ValidationError):
        FeaturePayload(
            title="t",
            description="x",
            tickets=["t1"],
            stack_span=StackSpan.FRONTEND,
            tier=TicketTier.V1,
            sources=[],
        )


def test_payload_kind_defaults_to_capability() -> None:
    """Pre-kind features didn't carry the field; default keeps old
    payloads valid and assigns the right semantic meaning (user-
    facing). Foundations have to be opted into explicitly."""
    payload = FeaturePayload(
        title="t",
        description="x",
        stack_span=StackSpan.FRONTEND,
        tier=TicketTier.V1,
        sources=["s"],
    )
    from wonderland.feature import FeatureKind

    assert payload.kind == FeatureKind.CAPABILITY


def test_payload_accepts_foundation_kind() -> None:
    """Caterpillar's plumbing stories compose into foundation
    features — same lifecycle, different framing. Validates the
    payload accepts the foundation discriminator and renders it
    in the markdown."""
    from wonderland.feature import FeatureKind

    payload = FeaturePayload(
        title="Mock financial data for development",
        description="Developers seed mock account + transaction data on app startup so the dashboard renders without hitting Plaid.",
        kind=FeatureKind.FOUNDATION,
        personas=["Maya the developer"],
        stack_span=StackSpan.BACKEND,
        tier=TicketTier.V1,
        sources=["mock-financial-data-for-dashboard-development"],
    )
    out = render_feature(1, payload)
    assert "**Kind:** foundation" in out
    assert payload.kind == FeatureKind.FOUNDATION


def test_render_feature_includes_kind_for_capability() -> None:
    """Capability is the default; render still emits the Kind line
    so the dashboard's parser doesn't have to special-case its
    absence."""
    payload = FeaturePayload(
        title="t",
        description="x",
        stack_span=StackSpan.FRONTEND,
        tier=TicketTier.V1,
        sources=["s"],
    )
    out = render_feature(1, payload)
    assert "**Kind:** capability" in out


# ---------- render_feature ----------


def test_render_feature_includes_all_required_sections() -> None:
    payload = FeaturePayload(
        title="Sign up and claim a homepage",
        description="A new user lands on the page, picks a username, sets a password, and gets a homepage URL they can share.",
        tickets=["user-registration", "homepage-url-reservation", "share-link-display"],
        personas=["Jordan the musician", "Maya the activist"],
        stack_span=StackSpan.FULL_STACK,
        tier=TicketTier.V1,
        sources=["sign-up-and-claim-a-username"],
    )
    out = render_feature(7, payload)
    assert "## Feature 007: Sign up and claim a homepage" in out
    assert "**Sources:** sign-up-and-claim-a-username" in out
    assert "**Personas:** Jordan the musician, Maya the activist" in out
    assert "**Stack span:** full-stack" in out
    assert "**Tier:** v1" in out
    assert "user-registration" in out
    assert "homepage-url-reservation" in out
    assert "share-link-display" in out


def test_render_feature_uses_dash_for_empty_personas() -> None:
    """Personas remains optional + renders as dash when empty;
    sources is now required (T-m8b) so it always has a value."""
    payload = FeaturePayload(
        title="t",
        description="x",
        tickets=["t1"],
        stack_span=StackSpan.BACKEND,
        tier=TicketTier.FAST_FOLLOW,
        sources=["a-story"],
    )
    out = render_feature(1, payload)
    assert "**Sources:** a-story" in out
    assert "**Personas:** —" in out


# ---------- FeatureRegistry ----------


def _payload(title: str = "f", tickets: list[str] | None = None) -> FeaturePayload:
    return FeaturePayload(
        title=title,
        description="d",
        tickets=tickets or ["t1"],
        stack_span=StackSpan.FRONTEND,
        tier=TicketTier.V1,
        sources=["seed-story"],
    )


def test_registry_writes_to_features_dir(tmp_path: Path) -> None:
    reg = FeatureRegistry(tmp_path)
    record = reg.write(_payload())
    assert record.path.parent == tmp_path / ".wonderland" / "features"
    assert record.path.is_file()
    assert record.number == 1
    # T-g3: filename embeds short_guid (first 8 chars of ULID),
    # not the legacy zero-padded number. Number lives in the H2
    # header for display.
    assert record.path.name.startswith(f"feature-{record.guid[:8]}-")
    assert record.path.name.endswith(".md")


def test_registry_numbers_increment(tmp_path: Path) -> None:
    reg = FeatureRegistry(tmp_path)
    a = reg.write(_payload(title="alpha"))
    b = reg.write(_payload(title="beta"))
    c = reg.write(_payload(title="gamma"))
    assert (a.number, b.number, c.number) == (1, 2, 3)


def test_registry_re_emit_same_slug_updates_in_place(tmp_path: Path) -> None:
    """P15 follow-up — update-by-slug semantics. Re-emitting a
    feature with the same slug overwrites in place; the second
    write preserves the original number and path. Previously, the
    registry always allocated a new number, producing duplicate
    files for identical slugs (discovery5 pilot)."""
    reg = FeatureRegistry(tmp_path)
    first = reg.write(_payload(title="alpha"))
    second = reg.write(_payload(title="alpha"))
    assert first.number == second.number == 1
    assert first.path == second.path
    # Only one file on disk.
    files = sorted(reg.path.glob("feature-*.md"))
    assert len(files) == 1


def test_registry_next_number_derives_from_disk(tmp_path: Path) -> None:
    """Same single-source-of-truth as TicketRegistry — no separate counter file."""
    reg = FeatureRegistry(tmp_path)
    reg.write(_payload(title="alpha"))
    reg.write(_payload(title="beta"))
    # Construct a fresh registry to confirm it doesn't rely on instance state.
    reg2 = FeatureRegistry(tmp_path)
    assert reg2.next_number() == 3


def test_registry_find_by_slug_and_number(tmp_path: Path) -> None:
    reg = FeatureRegistry(tmp_path)
    record = reg.write(_payload(title="Sign up and claim"))
    assert reg.find_by_slug("sign-up-and-claim") is not None
    assert reg.find_by_number(record.number) is not None
    assert reg.find_by_slug("nonexistent") is None
    assert reg.find_by_number(99) is None


def test_registry_skips_non_matching_files(tmp_path: Path) -> None:
    """Stray files in features/ shouldn't crash list_features."""
    reg = FeatureRegistry(tmp_path)
    reg.write(_payload(title="real"))
    # Drop a non-feature file in the features dir.
    (tmp_path / ".wonderland" / "features" / "README.md").write_text("noise", encoding="utf-8")
    records = reg.list_features()
    assert len(records) == 1
    assert records[0].slug == "real"


def test_registry_empty_dir_returns_empty_list(tmp_path: Path) -> None:
    reg = FeatureRegistry(tmp_path)
    assert reg.list_features() == []
    assert reg.next_number() == 1
