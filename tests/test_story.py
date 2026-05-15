"""Tests for the Story writer + registry."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from wonderland import (
    StoryPayload,
    StoryRegistry,
    StoryTier,
    render_story,
)

# ---------- helpers ----------


def _payload(**overrides) -> StoryPayload:
    base = {
        "title": "Joiner sees translation as it arrives",
        "persona": "Maya, 31, polyglot moderator drowning in cross-language threads",
        "situation": "She joins a busy chat where members write in three languages.",
        "need": "As Maya, I want translations to appear as messages arrive, so that the conversation reads as one stream.",
        "acceptance": [
            "Maya sees a translated version of any message within 1s of its arrival",
            "translation source language is shown when ambiguous",
        ],
        "tier": StoryTier.CORE,
        "confusion_flags": [
            "what happens when translation provider is slow — fall back to original?",
        ],
    }
    return StoryPayload(**(base | overrides))


# ---------- StoryPayload validation ----------


def test_payload_requires_non_empty_title() -> None:
    with pytest.raises(ValidationError):
        _payload(title="")


def test_payload_requires_non_empty_persona() -> None:
    with pytest.raises(ValidationError):
        _payload(persona="")


def test_payload_requires_non_empty_situation() -> None:
    with pytest.raises(ValidationError):
        _payload(situation="")


def test_payload_requires_non_empty_need() -> None:
    with pytest.raises(ValidationError):
        _payload(need="")


def test_payload_rejects_empty_acceptance_list() -> None:
    """A story without observable acceptance can't actually be tested as shipped."""
    with pytest.raises(ValidationError):
        _payload(acceptance=[])


def test_payload_rejects_only_whitespace_acceptance() -> None:
    with pytest.raises(ValidationError):
        _payload(acceptance=["", "  "])


def test_payload_rejects_empty_confusion_flags() -> None:
    """The grin equivalent — required even when nothing felt wrong."""
    with pytest.raises(ValidationError):
        _payload(confusion_flags=[])


def test_payload_rejects_only_whitespace_confusion_flags() -> None:
    with pytest.raises(ValidationError, match="suspect"):
        _payload(confusion_flags=["", " "])


@pytest.mark.parametrize(
    "tier",
    [StoryTier.CORE, StoryTier.ENRICHMENT, StoryTier.FAST_FOLLOW],
)
def test_payload_accepts_each_tier(tier: StoryTier) -> None:
    payload = _payload(tier=tier)
    assert payload.tier is tier


def test_payload_rejects_unknown_tier() -> None:
    with pytest.raises(ValidationError):
        _payload(tier="someday")


# ---------- render_story ----------


def test_render_includes_all_required_sections() -> None:
    out = render_story(7, _payload())
    assert "## Story 007: Joiner sees translation as it arrives" in out
    assert "**Persona:** Maya, 31, polyglot moderator" in out
    assert "**Situation:**" in out
    assert "She joins a busy chat" in out
    assert "**Need:**" in out
    assert "As Maya, I want translations" in out
    assert "**Acceptance:**" in out
    assert "- Maya sees a translated version" in out
    assert "**Tier:** core" in out
    assert "**Confusion-flags:**" in out
    assert "- what happens when translation provider is slow" in out


def test_render_three_digit_padding() -> None:
    assert "Story 003:" in render_story(3, _payload())


# ---------- StoryRegistry — empty state ----------


def test_empty_registry_state(tmp_path: Path) -> None:
    registry = StoryRegistry(tmp_path)
    assert registry.list_stories() == []
    assert registry.next_number() == 1
    assert registry.find_by_slug("anything") is None
    assert registry.find_by_number(1) is None


def test_path_under_dot_wonderland_stories(tmp_path: Path) -> None:
    registry = StoryRegistry(tmp_path)
    assert registry.path == tmp_path / ".wonderland" / "stories"


# ---------- StoryRegistry — write ----------


def test_write_creates_file_at_expected_path(tmp_path: Path) -> None:
    registry = StoryRegistry(tmp_path)
    record = registry.write(_payload())
    assert record.number == 1
    assert record.slug == "joiner-sees-translation-as-it-arrives"
    assert record.path.is_file()


def test_write_creates_parent_directory(tmp_path: Path) -> None:
    registry = StoryRegistry(tmp_path)
    registry.write(_payload())
    assert registry.path.is_dir()


def test_write_re_emit_same_slug_updates_in_place(tmp_path: Path) -> None:
    """P15 follow-up — update-by-slug semantics. Alice re-emitting
    the same story across rotations now overwrites in place rather
    than creating story-002 + story-006 with identical slugs
    (discovery5 pilot behavior)."""
    registry = StoryRegistry(tmp_path)
    first = registry.write(_payload())
    second = registry.write(_payload())
    assert first.number == second.number == 1
    assert first.path == second.path
    files = sorted(registry.path.glob("story-*.md"))
    assert len(files) == 1


def test_write_accepts_dict_payload(tmp_path: Path) -> None:
    registry = StoryRegistry(tmp_path)
    record = registry.write(
        {
            "title": "Speaker hears their language echoed back",
            "persona": "Diego, 24, learning Mandarin",
            "situation": "Practicing in a multilingual study group.",
            "need": "As Diego, I want my Mandarin shown to native speakers, so that I get correction.",
            "acceptance": ["original message visible alongside translation"],
            "tier": "core",
            "confusion_flags": ["uncertain if 'native speakers' is identifiable"],
        }
    )
    assert record.title == "Speaker hears their language echoed back"


def test_write_rejects_payload_without_confusion_flags(tmp_path: Path) -> None:
    registry = StoryRegistry(tmp_path)
    with pytest.raises(ValidationError):
        registry.write(
            {
                "title": "t",
                "persona": "p",
                "situation": "s",
                "need": "n",
                "acceptance": ["a"],
                "tier": "core",
                "confusion_flags": [],
            }
        )


def test_write_auto_increments(tmp_path: Path) -> None:
    registry = StoryRegistry(tmp_path)
    a = registry.write(_payload(title="A"))
    b = registry.write(_payload(title="B"))
    assert (a.number, b.number) == (1, 2)


def test_written_file_round_trips_through_render(tmp_path: Path) -> None:
    registry = StoryRegistry(tmp_path)
    payload = _payload()
    record = registry.write(payload)
    assert record.read() == render_story(1, payload)


# ---------- StoryRegistry — queries ----------


def test_list_in_number_order(tmp_path: Path) -> None:
    registry = StoryRegistry(tmp_path)
    for title in ("Third", "First", "Second"):
        registry.write(_payload(title=title))
    listing = registry.list_stories()
    assert [r.number for r in listing] == [1, 2, 3]
    assert [r.title for r in listing] == ["Third", "First", "Second"]


def test_find_by_slug(tmp_path: Path) -> None:
    registry = StoryRegistry(tmp_path)
    registry.write(_payload(title="Maya joins"))
    found = registry.find_by_slug("maya-joins")
    assert found is not None


def test_skips_non_story_files(tmp_path: Path) -> None:
    registry = StoryRegistry(tmp_path)
    registry.write(_payload(title="A"))
    (registry.path / "README.md").write_text("not a story")
    (registry.path / "story-malformed.md").write_text("also not")
    assert len(registry.list_stories()) == 1
