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


# ---------- P18 guid round-trip ----------


def test_payload_auto_generates_guid_when_missing() -> None:
    """Every fresh payload gets a ULID via default_factory."""
    payload = _payload()
    assert payload.guid
    # ULIDs are 26 chars; smoke-check the shape.
    assert len(payload.guid) == 26


def test_payload_preserves_explicit_guid() -> None:
    """Caller-supplied guid is preserved (used when re-emitting
    to amend an existing artifact)."""
    payload = _payload(guid="01HAAAA000000000000000000A")
    assert payload.guid == "01HAAAA000000000000000000A"


def test_render_includes_guid_line() -> None:
    """Markdown body must include the GUID line so the parser can
    read it back."""
    payload = _payload()
    from wonderland import render_story

    out = render_story(7, payload)
    assert f"**GUID:** {payload.guid}" in out


def test_registry_round_trips_guid(tmp_path: Path) -> None:
    """write() → list_stories() preserves the guid: this is the
    load-bearing property — the substrate routes on guid, so the
    value on disk must match the value the agent emitted."""
    registry = StoryRegistry(tmp_path)
    payload = _payload()
    record = registry.write(payload)
    assert record.guid == payload.guid

    # Re-read via list_stories — guid must be preserved.
    all_records = registry.list_stories()
    assert len(all_records) == 1
    assert all_records[0].guid == payload.guid


def test_re_emit_same_slug_preserves_guid(tmp_path: Path) -> None:
    """The P18 amend-vs-create distinction: re-emitting with the
    same slug must preserve the original guid even if the caller's
    payload has a different guid. The registry's slug-based lookup
    is the back-compat path; guid stability is the win."""
    registry = StoryRegistry(tmp_path)
    first = registry.write(_payload(title="Alpha story"))
    second_payload = _payload(title="Alpha story", guid="01HBBBB000000000000000000B")
    second = registry.write(second_payload)
    # Same slug → registry preserves the original guid, ignoring the
    # second payload's fresh guid (treats as amendment).
    assert second.guid == first.guid
    assert second.guid != "01HBBBB000000000000000000B"


def test_guid_parsed_back_from_disk(tmp_path: Path) -> None:
    """Round-trip: write a story, read its file directly, confirm
    the GUID line is present and matches what list_stories returns."""
    registry = StoryRegistry(tmp_path)
    record = registry.write(_payload())
    raw = record.path.read_text()
    assert f"**GUID:** {record.guid}" in raw

    # Fresh registry instance — no in-memory state — still surfaces
    # the same guid via the markdown parser.
    fresh_registry = StoryRegistry(tmp_path)
    refound = fresh_registry.find_by_slug(record.slug)
    assert refound is not None
    assert refound.guid == record.guid


# ---------- T-g2 find_by_guid + update-by-guid ----------


def test_find_by_guid_returns_record(tmp_path: Path) -> None:
    """The primary identity lookup. find_by_guid resolves a known
    guid to its record; slug doesn't matter."""
    registry = StoryRegistry(tmp_path)
    record = registry.write(_payload(title="Original story"))

    found = registry.find_by_guid(record.guid)
    assert found is not None
    assert found.guid == record.guid
    assert found.slug == record.slug


def test_find_by_guid_returns_none_for_missing(tmp_path: Path) -> None:
    registry = StoryRegistry(tmp_path)
    registry.write(_payload())
    assert registry.find_by_guid("01HZZZ000000000000000000ZZ") is None


def test_find_by_guid_returns_none_for_empty_string(tmp_path: Path) -> None:
    """Empty guid is the back-compat signal — don't match every
    record with no guid; just return None so the caller falls
    through to slug-based lookup."""
    registry = StoryRegistry(tmp_path)
    registry.write(_payload())
    assert registry.find_by_guid("") is None


def test_re_emit_same_guid_different_slug_updates_in_place(
    tmp_path: Path,
) -> None:
    """The headline T-g2 win: agent re-emits with the same guid
    but a different title (so different slug). Registry recognizes
    the identity via guid + updates in place. validation4's
    triplicate-feature pattern becomes substrate-impossible."""
    registry = StoryRegistry(tmp_path)
    first = registry.write(_payload(title="Original title"))
    # Same guid, different title → must update in place
    second = registry.write(_payload(
        guid=first.guid,
        title="Revised title v2",
    ))
    assert second.number == first.number
    # Slug reflects the new title; identity stays the original guid
    assert second.guid == first.guid
    assert second.slug == "revised-title-v2"
    # Only one story on disk — the in-place update overwrote the
    # original (and renamed if we'd implemented filename guid embedding,
    # but T-g2 keeps the existing path so the file count stays at 1).
    assert len(registry.list_stories()) == 1


def test_new_guid_creates_new_artifact(tmp_path: Path) -> None:
    """Fresh guid + same title → new file, not update. The amend-
    vs-create distinction lives at the guid layer; coining a new
    guid is the explicit 'this is different' signal."""
    registry = StoryRegistry(tmp_path)
    first = registry.write(_payload(title="Story A"))
    second_payload = _payload(title="Story A")
    # second_payload's auto-generated guid is fresh; not first.guid
    assert second_payload.guid != first.guid

    # Without slug fallback, this would create a 2nd file. WITH
    # the slug fallback (back-compat path), the registry detects
    # the same slug and updates the original — using slug-as-
    # back-compat-identity. Behavior preserves the pre-P18
    # invariant: identical slug means same artifact unless guid
    # explicitly says otherwise. The slug fallback is what makes
    # this back-compat safe.
    second = registry.write(second_payload)
    assert second.number == first.number  # same file, slug match
    assert second.guid == first.guid  # back-compat preserves guid


# ---------- T-ab48 — active-scope milestone validation ----------


def test_t_ab48_rejects_story_attributed_to_sibling_milestone(
    tmp_path: Path,
) -> None:
    """obol-260522-1 M6 design: alice wrote 3 stories attributed
    to m5-kohl-debt-paydown-tracking during a run scoped to m6-csv-
    and-ofx-import. The substrate accepted whatever milestone alice
    declared, polluting M5's story pool with stories produced during
    M6 and leaving M6 with zero stories of its own.

    With T-ab48, StoryRegistry.write rejects writes whose milestone
    field doesn't match the active scope."""
    import wonderland.workflow as wf

    scope = wf._MilestoneScope(
        slug="m6-csv-and-ofx-import",
        name="M6",
        goal="g",
        done_when=("d",),
        consumes=frozenset(),
    )
    wf.set_active_milestone_scope(scope)
    try:
        registry = StoryRegistry(tmp_path)
        # Alice tries to write an M5-attributed story during M6 scope
        with pytest.raises(ValueError, match="milestone attribution mismatch"):
            registry.write(_payload(milestone="m5-kohl-debt-paydown-tracking"))
    finally:
        wf.set_active_milestone_scope(None)


def test_t_ab48_allows_matching_milestone(tmp_path: Path) -> None:
    """When alice's story milestone matches the active scope, write
    succeeds normally. Also handles the ``<guid>:<slug>`` form."""
    import wonderland.workflow as wf

    scope = wf._MilestoneScope(
        slug="m6-csv-and-ofx-import",
        name="M6",
        goal="g",
        done_when=("d",),
        consumes=frozenset(),
    )
    wf.set_active_milestone_scope(scope)
    try:
        registry = StoryRegistry(tmp_path)
        # Plain slug
        registry.write(_payload(
            title="M6 plain", milestone="m6-csv-and-ofx-import",
        ))
        # Guid-prefixed form
        registry.write(_payload(
            title="M6 prefixed",
            milestone="01ABCDEFGHJK4NSY5Y3FG9Z58Z:m6-csv-and-ofx-import",
        ))
    finally:
        wf.set_active_milestone_scope(None)


def test_t_ab48_allows_unscoped_writes(tmp_path: Path) -> None:
    """When no active scope is set (test fixtures, legacy backfill
    paths, scripts), the validator is skipped — pre-T-ab48 behavior
    holds. Also allows writes that omit the milestone field entirely
    (legacy stories without T-ab7 attribution)."""
    registry = StoryRegistry(tmp_path)
    # No scope; declared milestone of any value is allowed
    registry.write(_payload(title="A", milestone="m99-anything"))
    # Even with a scope set, an omitted milestone passes (operator can
    # backfill later — same defensive default seeds_fallback uses).
    import wonderland.workflow as wf
    scope = wf._MilestoneScope(
        slug="m6-active",
        name="M6",
        goal="g",
        done_when=("d",),
        consumes=frozenset(),
    )
    wf.set_active_milestone_scope(scope)
    try:
        registry.write(_payload(title="B no milestone", milestone=None))
    finally:
        wf.set_active_milestone_scope(None)
