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
        )


def test_payload_requires_non_empty_description() -> None:
    with pytest.raises(ValidationError):
        FeaturePayload(
            title="t",
            description="",
            tickets=["t1"],
            stack_span=StackSpan.FRONTEND,
            tier=TicketTier.V1,
        )


def test_payload_requires_at_least_one_ticket() -> None:
    """A feature with zero tickets isn't a feature, it's a wish."""
    with pytest.raises(ValidationError):
        FeaturePayload(
            title="empty feature",
            description="this should fail",
            tickets=[],
            stack_span=StackSpan.FRONTEND,
            tier=TicketTier.V1,
        )


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
    )
    assert payload.personas == []
    assert payload.sources == []


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


def test_render_feature_uses_dash_for_empty_optionals() -> None:
    payload = FeaturePayload(
        title="t",
        description="x",
        tickets=["t1"],
        stack_span=StackSpan.BACKEND,
        tier=TicketTier.FAST_FOLLOW,
    )
    out = render_feature(1, payload)
    assert "**Sources:** —" in out
    assert "**Personas:** —" in out


# ---------- FeatureRegistry ----------


def _payload(title: str = "f", tickets: list[str] | None = None) -> FeaturePayload:
    return FeaturePayload(
        title=title,
        description="d",
        tickets=tickets or ["t1"],
        stack_span=StackSpan.FRONTEND,
        tier=TicketTier.V1,
    )


def test_registry_writes_to_features_dir(tmp_path: Path) -> None:
    reg = FeatureRegistry(tmp_path)
    record = reg.write(_payload())
    assert record.path.parent == tmp_path / ".wonderland" / "features"
    assert record.path.is_file()
    assert record.number == 1
    assert record.path.name.startswith("feature-001-")


def test_registry_numbers_increment(tmp_path: Path) -> None:
    reg = FeatureRegistry(tmp_path)
    a = reg.write(_payload(title="alpha"))
    b = reg.write(_payload(title="beta"))
    c = reg.write(_payload(title="gamma"))
    assert (a.number, b.number, c.number) == (1, 2, 3)


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
