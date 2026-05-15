"""Tests for the Milestone substrate — models, validation,
update-by-slug registry semantics, derived status."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from wonderland import (
    Confidence,
    Milestone,
    MilestonePayload,
    MilestoneRegistry,
    MilestoneStatus,
    render_milestone,
)


# --------------------------------------------------------------------- #
# Top-level alias
# --------------------------------------------------------------------- #


def test_milestone_alias_is_payload() -> None:
    """Top-level ``Milestone`` resolves to ``MilestonePayload`` —
    keeps call sites short like ``Story`` / ``Ticket`` do."""
    assert Milestone is MilestonePayload


# --------------------------------------------------------------------- #
# Payload validation
# --------------------------------------------------------------------- #


def _payload(**overrides) -> MilestonePayload:
    base = {
        "slug": "foundation",
        "name": "Foundation: data layer + profile shell",
        "order": 1,
        "goal": "Local SQLite schema, profile shell, app skeleton.",
        "done_when": [
            "App launches on a fresh machine",
            "Profile can be created and selected",
        ],
        "consumes_requirements": [
            "multi-user-local-profiles",
            "local-storage-sqlite",
        ],
    }
    return MilestonePayload(**(base | overrides))


def test_payload_minimal_construct() -> None:
    p = _payload()
    assert p.slug == "foundation"
    assert p.order == 1
    assert p.deferred is False
    assert p.confidence is Confidence.OPERATOR_STATED


def test_payload_rejects_empty_slug() -> None:
    with pytest.raises(ValidationError):
        _payload(slug="")


def test_payload_rejects_uppercase_slug() -> None:
    with pytest.raises(ValidationError):
        _payload(slug="Foundation")


def test_payload_rejects_leading_hyphen_slug() -> None:
    with pytest.raises(ValidationError):
        _payload(slug="-foundation")


def test_payload_rejects_order_zero() -> None:
    with pytest.raises(ValidationError):
        _payload(order=0)


def test_payload_rejects_empty_name() -> None:
    with pytest.raises(ValidationError):
        _payload(name="")


def test_payload_rejects_empty_goal() -> None:
    with pytest.raises(ValidationError):
        _payload(goal="")


def test_payload_rejects_duplicate_requirements() -> None:
    with pytest.raises(
        ValidationError, match="duplicate requirement"
    ):
        _payload(
            consumes_requirements=[
                "local-storage-sqlite",
                "multi-user-local-profiles",
                "local-storage-sqlite",
            ]
        )


def test_payload_accepts_deferred_flag() -> None:
    p = _payload(deferred=True)
    assert p.deferred is True


def test_payload_accepts_inferred_confidence() -> None:
    p = _payload(confidence=Confidence.INTERVIEWER_INFERRED)
    assert p.confidence is Confidence.INTERVIEWER_INFERRED


# --------------------------------------------------------------------- #
# render_milestone markdown
# --------------------------------------------------------------------- #


def test_render_includes_title_and_metadata() -> None:
    p = _payload()
    md = render_milestone(p)
    assert "## Milestone 01: Foundation: data layer + profile shell" in md
    assert "**Slug:** foundation" in md
    assert "**Order:** 1" in md
    assert "**Deferred:** false" in md
    assert "**Confidence:** operator_stated" in md


def test_render_includes_goal_done_when_and_requirements() -> None:
    p = _payload()
    md = render_milestone(p)
    assert "**Goal:**" in md
    assert "Local SQLite schema" in md
    assert "**Done when:**" in md
    assert "- App launches on a fresh machine" in md
    assert "**Consumes requirements:**" in md
    assert "- multi-user-local-profiles" in md


def test_render_marks_deferred_when_flag_set() -> None:
    p = _payload(deferred=True)
    md = render_milestone(p)
    assert "**Deferred:** true" in md


# --------------------------------------------------------------------- #
# Registry — append + update-by-slug
# --------------------------------------------------------------------- #


def test_registry_writes_numbered_file(tmp_path: Path) -> None:
    reg = MilestoneRegistry(tmp_path)
    record = reg.write(_payload())
    assert record.path.name == "milestone-01-foundation.md"
    assert record.path.exists()


def test_registry_append_increments_next_order(
    tmp_path: Path,
) -> None:
    reg = MilestoneRegistry(tmp_path)
    reg.write(_payload(slug="foundation", order=1))
    reg.write(_payload(slug="logging-loop", order=2, name="Logging loop"))
    assert reg.next_order() == 3


def test_registry_update_by_slug_overwrites_in_place(
    tmp_path: Path,
) -> None:
    """Re-writing the same slug should update the existing file,
    not create a second one — this is the cross-run continuity
    primitive."""
    reg = MilestoneRegistry(tmp_path)
    reg.write(_payload(slug="foundation", name="Original name"))
    reg.write(_payload(slug="foundation", name="Revised name"))

    records = reg.list_milestones()
    assert len(records) == 1
    assert records[0].name == "Revised name"


def test_registry_update_with_order_change_renames_file(
    tmp_path: Path,
) -> None:
    """When ``order`` shifts on an update, the old filename should
    be removed and the new one created. Without this, the
    sorted-listing-as-sequence invariant breaks."""
    reg = MilestoneRegistry(tmp_path)
    reg.write(_payload(slug="foundation", order=1))
    assert (tmp_path / ".wonderland" / "milestones" / "milestone-01-foundation.md").exists()
    reg.write(_payload(slug="foundation", order=3))
    files = sorted(p.name for p in reg.path.iterdir())
    assert files == ["milestone-03-foundation.md"]


def test_registry_find_by_slug(tmp_path: Path) -> None:
    reg = MilestoneRegistry(tmp_path)
    reg.write(_payload(slug="foundation"))
    reg.write(_payload(slug="logging-loop", order=2, name="Logging loop"))
    found = reg.find_by_slug("logging-loop")
    assert found is not None
    assert found.order == 2


def test_registry_find_by_order(tmp_path: Path) -> None:
    reg = MilestoneRegistry(tmp_path)
    reg.write(_payload(slug="foundation", order=1))
    reg.write(_payload(slug="logging-loop", order=2, name="Logging loop"))
    found = reg.find_by_order(2)
    assert found is not None
    assert found.slug == "logging-loop"


def test_registry_list_sorted_by_order_then_slug(
    tmp_path: Path,
) -> None:
    reg = MilestoneRegistry(tmp_path)
    # Insert out of order — registry should sort by order on read.
    reg.write(_payload(slug="logging-loop", order=2, name="Logging"))
    reg.write(_payload(slug="foundation", order=1))
    reg.write(_payload(slug="gamification", order=3, name="Gamification"))
    slugs = [r.slug for r in reg.list_milestones()]
    assert slugs == ["foundation", "logging-loop", "gamification"]


def test_registry_empty_when_directory_missing(
    tmp_path: Path,
) -> None:
    reg = MilestoneRegistry(tmp_path)
    assert reg.list_milestones() == []
    assert reg.next_order() == 1


def test_registry_delete_by_slug(tmp_path: Path) -> None:
    reg = MilestoneRegistry(tmp_path)
    reg.write(_payload(slug="foundation"))
    reg.write(_payload(slug="logging-loop", order=2, name="Logging"))
    assert reg.delete_by_slug("foundation") is True
    assert reg.find_by_slug("foundation") is None
    assert reg.find_by_slug("logging-loop") is not None


def test_registry_delete_missing_returns_false(
    tmp_path: Path,
) -> None:
    reg = MilestoneRegistry(tmp_path)
    assert reg.delete_by_slug("nope") is False


def test_registry_preserves_deferred_through_read(
    tmp_path: Path,
) -> None:
    """Round-trip: a deferred milestone written + read back keeps
    the flag. Parser tolerance — operator hand-edits should be
    safe too."""
    reg = MilestoneRegistry(tmp_path)
    reg.write(_payload(deferred=True))
    records = reg.list_milestones()
    assert len(records) == 1
    assert records[0].deferred is True


def test_registry_tolerates_unrelated_files(tmp_path: Path) -> None:
    """Files in the milestones dir that don't match the pattern
    should be ignored — same tolerance as the other registries."""
    reg = MilestoneRegistry(tmp_path)
    reg.write(_payload())
    (reg.path / "README.md").write_text("not a milestone\n")
    records = reg.list_milestones()
    assert len(records) == 1


# --------------------------------------------------------------------- #
# Derived status
# --------------------------------------------------------------------- #


def test_derive_status_proposed_when_no_features() -> None:
    s = MilestoneRegistry.derive_status(
        deferred=False, feature_states=[]
    )
    assert s is MilestoneStatus.PROPOSED


def test_derive_status_proposed_when_all_features_proposed() -> None:
    """Features in 'proposed' (the default feature state) don't move
    the milestone into in_progress — the milestone is still being
    designed, not built."""
    s = MilestoneRegistry.derive_status(
        deferred=False,
        feature_states=["proposed", "proposed"],
    )
    assert s is MilestoneStatus.PROPOSED


def test_derive_status_in_progress_when_any_feature_designed() -> None:
    s = MilestoneRegistry.derive_status(
        deferred=False,
        feature_states=["proposed", "designed"],
    )
    assert s is MilestoneStatus.IN_PROGRESS


def test_derive_status_in_progress_when_any_feature_queued() -> None:
    s = MilestoneRegistry.derive_status(
        deferred=False,
        feature_states=["queued", "proposed"],
    )
    assert s is MilestoneStatus.IN_PROGRESS


def test_derive_status_done_when_all_features_verified() -> None:
    s = MilestoneRegistry.derive_status(
        deferred=False,
        feature_states=["verified", "verified"],
    )
    assert s is MilestoneStatus.DONE


def test_derive_status_in_progress_when_mixed_verified_others() -> None:
    """Partially-shipped milestone — verified + in-flight features =
    in_progress, not done."""
    s = MilestoneRegistry.derive_status(
        deferred=False,
        feature_states=["verified", "in_progress"],
    )
    assert s is MilestoneStatus.IN_PROGRESS


def test_derive_status_deferred_overrides_everything() -> None:
    """Deferred is an operator-driven escape: even verified features
    can't move a deferred milestone into done."""
    s = MilestoneRegistry.derive_status(
        deferred=True,
        feature_states=["verified", "verified"],
    )
    assert s is MilestoneStatus.DEFERRED
