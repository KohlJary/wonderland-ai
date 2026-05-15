"""Tests for the ADR writer + registry."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from wonderland import (
    ADRPayload,
    ADRRegistry,
    ADRStatus,
    render_adr,
    slugify,
)

# ---------- ADRPayload validation ----------


def test_payload_requires_non_empty_title() -> None:
    with pytest.raises(ValidationError):
        ADRPayload(title="", context="x", decision="x", tradeoffs=["t"])


def test_payload_requires_non_empty_context() -> None:
    with pytest.raises(ValidationError):
        ADRPayload(title="t", context="", decision="x", tradeoffs=["t"])


def test_payload_requires_non_empty_decision() -> None:
    with pytest.raises(ValidationError):
        ADRPayload(title="t", context="x", decision="", tradeoffs=["t"])


def test_payload_rejects_empty_tradeoffs_list() -> None:
    """The grin is non-optional."""
    with pytest.raises(ValidationError):
        ADRPayload(title="t", context="x", decision="y", tradeoffs=[])


def test_payload_rejects_only_whitespace_tradeoffs() -> None:
    """A list of empty strings still has no grin."""
    with pytest.raises(ValidationError, match="grin is non-optional"):
        ADRPayload(title="t", context="x", decision="y", tradeoffs=["", "  "])


def test_payload_default_status_is_proposed() -> None:
    payload = ADRPayload(title="t", context="x", decision="y", tradeoffs=["a"])
    assert payload.status is ADRStatus.PROPOSED


def test_payload_supersedes_with_link() -> None:
    payload = ADRPayload(
        title="t",
        context="x",
        decision="y",
        tradeoffs=["a"],
        status=ADRStatus.SUPERSEDED,
        superseded_by=7,
    )
    assert payload.status is ADRStatus.SUPERSEDED
    assert payload.superseded_by == 7


# ---------- slugify ----------


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Use Redis Streams for the Caucus", "use-redis-streams-for-the-caucus"),
        ("Hello, World!", "hello-world"),
        ("multi   space", "multi-space"),
        ("--leading-and-trailing--", "leading-and-trailing"),
        ("CamelCase", "camelcase"),
        ("v1.2.3-rc.1", "v1-2-3-rc-1"),
    ],
)
def test_slugify(text: str, expected: str) -> None:
    assert slugify(text) == expected


def test_slugify_empty_falls_back_to_untitled() -> None:
    assert slugify("") == "untitled"
    assert slugify("!!!") == "untitled"


# ---------- render_adr ----------


def test_render_adr_includes_all_sections() -> None:
    payload = ADRPayload(
        title="Use Redis Streams",
        context="Need an event bus.",
        decision="Use Redis Streams.",
        tradeoffs=["familiar ops", "single-region default"],
    )
    out = render_adr(1, payload)
    assert "# ADR-001: Use Redis Streams" in out
    assert "## Context" in out
    assert "## Decision" in out
    assert "## Tradeoffs" in out
    assert "## Status" in out
    assert "- familiar ops" in out
    assert "- single-region default" in out
    assert "Proposed" in out


def test_render_adr_renders_superseded_with_link() -> None:
    payload = ADRPayload(
        title="Old idea",
        context="x",
        decision="y",
        tradeoffs=["a"],
        status=ADRStatus.SUPERSEDED,
        superseded_by=42,
    )
    out = render_adr(7, payload)
    assert "Superseded by ADR-042" in out


def test_render_adr_three_digit_padding() -> None:
    payload = ADRPayload(title="t", context="x", decision="y", tradeoffs=["a"])
    out = render_adr(3, payload)
    assert "ADR-003:" in out


# ---------- ADRRegistry — empty state ----------


def test_empty_registry_lists_no_adrs(tmp_path: Path) -> None:
    registry = ADRRegistry(tmp_path)
    assert registry.list_adrs() == []


def test_empty_registry_next_number_is_one(tmp_path: Path) -> None:
    registry = ADRRegistry(tmp_path)
    assert registry.next_number() == 1


def test_empty_registry_find_returns_none(tmp_path: Path) -> None:
    registry = ADRRegistry(tmp_path)
    assert registry.find_by_slug("anything") is None
    assert registry.find_by_number(1) is None


def test_path_is_under_dot_wonderland(tmp_path: Path) -> None:
    registry = ADRRegistry(tmp_path)
    assert registry.path == tmp_path / ".wonderland" / "architecture"


# ---------- ADRRegistry — write ----------


def test_write_creates_file_at_expected_path(tmp_path: Path) -> None:
    registry = ADRRegistry(tmp_path)
    record = registry.write(
        ADRPayload(
            title="Use Redis Streams",
            context="bus needed",
            decision="redis it is",
            tradeoffs=["familiar ops"],
        )
    )
    assert record.number == 1
    assert record.slug == "use-redis-streams"
    assert record.title == "Use Redis Streams"
    # T-g3: filename embeds short_guid for substrate identity.
    assert (
        record.path
        == tmp_path
        / ".wonderland"
        / "architecture"
        / f"adr-{record.guid[:8]}-use-redis-streams.md"
    )
    assert record.path.is_file()


def test_write_creates_parent_directory(tmp_path: Path) -> None:
    registry = ADRRegistry(tmp_path)
    payload = ADRPayload(title="t", context="x", decision="y", tradeoffs=["a"])
    registry.write(payload)
    assert registry.path.is_dir()


def test_write_accepts_dict_payload(tmp_path: Path) -> None:
    registry = ADRRegistry(tmp_path)
    record = registry.write(
        {
            "title": "Cache the Constitution",
            "context": "Constitution is invariant.",
            "decision": "Mark it cached.",
            "tradeoffs": ["misses on rotation"],
        }
    )
    assert record.title == "Cache the Constitution"


def test_write_rejects_payload_with_empty_tradeoffs(tmp_path: Path) -> None:
    registry = ADRRegistry(tmp_path)
    with pytest.raises(ValidationError):
        registry.write({"title": "t", "context": "x", "decision": "y", "tradeoffs": []})


def test_write_auto_increments_number(tmp_path: Path) -> None:
    registry = ADRRegistry(tmp_path)
    a = registry.write(ADRPayload(title="A", context="c", decision="d", tradeoffs=["t"]))
    b = registry.write(ADRPayload(title="B", context="c", decision="d", tradeoffs=["t"]))
    c = registry.write(ADRPayload(title="C", context="c", decision="d", tradeoffs=["t"]))
    assert a.number == 1
    assert b.number == 2
    assert c.number == 3


def test_written_file_round_trips_through_render_adr(tmp_path: Path) -> None:
    """The file on disk is exactly what render_adr produces."""
    registry = ADRRegistry(tmp_path)
    payload = ADRPayload(
        title="Bicameral SpeechAct",
        context="Substantive vs procedural split.",
        decision="One enum, two frozensets.",
        tradeoffs=[
            "directive carve-out makes type-level split wrong",
            "subscribers must reason about category at call site",
        ],
    )
    record = registry.write(payload)
    assert record.read() == render_adr(1, payload)


# ---------- ADRRegistry — query after writes ----------


def test_list_adrs_returns_records_in_number_order(tmp_path: Path) -> None:
    registry = ADRRegistry(tmp_path)
    for title in ("Third", "First", "Second"):
        registry.write(ADRPayload(title=title, context="c", decision="d", tradeoffs=["t"]))
    listing = registry.list_adrs()
    assert [r.number for r in listing] == [1, 2, 3]
    # Title order matches write order, not alphabetical
    assert [r.title for r in listing] == ["Third", "First", "Second"]


def test_next_number_after_writes(tmp_path: Path) -> None:
    registry = ADRRegistry(tmp_path)
    registry.write(ADRPayload(title="A", context="c", decision="d", tradeoffs=["t"]))
    registry.write(ADRPayload(title="B", context="c", decision="d", tradeoffs=["t"]))
    assert registry.next_number() == 3


def test_find_by_slug_returns_match(tmp_path: Path) -> None:
    registry = ADRRegistry(tmp_path)
    registry.write(ADRPayload(title="Use Redis", context="c", decision="d", tradeoffs=["t"]))
    found = registry.find_by_slug("use-redis")
    assert found is not None
    assert found.title == "Use Redis"


def test_find_by_number_returns_match(tmp_path: Path) -> None:
    registry = ADRRegistry(tmp_path)
    registry.write(ADRPayload(title="A", context="c", decision="d", tradeoffs=["t"]))
    registry.write(ADRPayload(title="B", context="c", decision="d", tradeoffs=["t"]))
    found = registry.find_by_number(2)
    assert found is not None
    assert found.title == "B"


def test_registry_survives_unknown_files_in_directory(tmp_path: Path) -> None:
    """Files that don't match adr-NNN-slug.md are ignored, not errored."""
    registry = ADRRegistry(tmp_path)
    registry.write(ADRPayload(title="A", context="c", decision="d", tradeoffs=["t"]))
    # Drop a stray file
    (registry.path / "README.md").write_text("not an adr", encoding="utf-8")
    (registry.path / "adr-malformed.md").write_text("also not", encoding="utf-8")
    listing = registry.list_adrs()
    assert len(listing) == 1
    assert listing[0].slug == "a"


def test_next_number_picks_max_plus_one_with_gaps(tmp_path: Path) -> None:
    """If someone hand-deletes an intermediate ADR, next_number is still max+1."""
    registry = ADRRegistry(tmp_path)
    registry.path.mkdir(parents=True, exist_ok=True)
    # Manually create files numbered 1, 5, 7 (simulating a deletion history)
    for n in (1, 5, 7):
        path = registry.path / f"adr-{n:03d}-stub.md"
        path.write_text(f"# ADR-{n:03d}: Stub\n", encoding="utf-8")
    assert registry.next_number() == 8


def test_record_read_returns_file_content(tmp_path: Path) -> None:
    registry = ADRRegistry(tmp_path)
    record = registry.write(ADRPayload(title="Read me", context="c", decision="d", tradeoffs=["t"]))
    content = record.read()
    assert "# ADR-001: Read me" in content
