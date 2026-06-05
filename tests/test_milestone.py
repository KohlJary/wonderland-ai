"""Tests for the Milestone substrate — models, validation,
update-by-slug registry semantics, derived status."""

from __future__ import annotations

import re
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
    # T-g3: filename embeds short_guid for substrate identity.
    assert record.path.name == f"milestone-{record.guid[:8]}-foundation.md"
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


def test_registry_update_with_order_change_does_not_rename_file(
    tmp_path: Path,
) -> None:
    """T-g3: filename embeds short_guid, not order. Reordering
    updates the on-disk order in the H2 header without changing
    the filename — guid is identity, order is display."""
    reg = MilestoneRegistry(tmp_path)
    initial = reg.write(_payload(slug="foundation", order=1))
    assert initial.path.exists()
    updated = reg.write(
        _payload(slug="foundation", order=3, guid=initial.guid),
    )
    # Same file (guid-stable identity), order has shifted in record.
    assert updated.path == initial.path
    assert updated.order == 3
    files = sorted(p.name for p in reg.path.iterdir())
    assert files == [f"milestone-{initial.guid[:8]}-foundation.md"]


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


# --------------------------------------------------------------------- #
# T-ab65 — title-based foundation kind enforcement (check 3)
# --------------------------------------------------------------------- #


def _write_axis_requirement(req_dir: Path, slug: str, axis: str) -> None:
    """Helper: drop a requirement file with the specified Axis line
    so the kind-consistency validator's req_root gate activates.

    Filename id slot is 8 chars per T-g3's Crockford-style pattern
    (``[0-9A-HJKMNP-TV-Z]{8}``)."""
    req_dir.mkdir(parents=True, exist_ok=True)
    # Crockford base32 excludes I, L, O, U — derive an 8-char id from
    # the slug with safe-character substitution.
    alphabet = set("0123456789ABCDEFGHJKMNPQRSTVWXYZ")
    raw = (slug.upper() + "ABCDEFGH")[:8]
    safe_id = "".join(c if c in alphabet else "X" for c in raw)
    (req_dir / f"requirement-{safe_id}-{slug}.md").write_text(
        f"""## Requirement 001: {slug}

**GUID:** {safe_id}00000000000000000HW
**Slug:** {slug}
**Kind:** constraint
**Axis:** {axis}
**Confidence:** operator_stated

**Body:**

Test requirement for the validator gate.
""",
        encoding="utf-8",
    )


def _setup_project_with_reqs(
    tmp_path: Path, reqs: list[tuple[str, str]]
) -> Path:
    """Sets up ``.wonderland/requirements/`` with one or more
    axis-tagged requirements so the kind-validator's req_root gate
    activates. ``reqs`` is a list of (slug, axis) pairs. Returns
    ``tmp_path`` — caller passes it to ``MilestoneRegistry`` which
    adds ``.wonderland/milestones`` internally."""
    req_dir = tmp_path / ".wonderland" / "requirements"
    for slug, axis in reqs:
        _write_axis_requirement(req_dir, slug, axis)
    return tmp_path


# T-ab65 is autopromote-mode: capability-kind milestones whose
# title starts with "Foundation:" OR whose slug contains "foundation"
# get silently promoted to kind=foundation. LDR-rerun v2 showed
# reject-mode let agents adapt around the check by avoiding the
# title pattern; autopromote ratifies the agent's literal-word
# signal instead of forcing them to learn the routing-meta-language.


def _read_kind_on_disk(record_path: Path) -> str:
    """Read the persisted Kind field from a milestone file (matches
    the substrate's parser by reading the **Kind:** line)."""
    text = record_path.read_text(encoding="utf-8")
    m = re.search(r"^\*\*Kind:\*\*\s*(\S+)", text, re.MULTILINE)
    return m.group(1).strip().lower() if m else ""


def test_t_ab65_autopromotes_foundation_titled_capability_kind(
    tmp_path: Path,
) -> None:
    """T-ab65: a milestone whose name starts with 'Foundation:'
    auto-promotes to kind=foundation, even if the agent tagged
    capability. Mirrors LDR-rerun M1 case — capability-axis cite
    alongside foundation-axis ones lets check 2 stay quiet; check
    3 ratifies the title signal."""
    root = _setup_project_with_reqs(
        tmp_path,
        [("stack-constraint", "foundation"), ("v1-ship-criteria", "capability")],
    )
    reg = MilestoneRegistry(root)
    record = reg.write(
        _payload(
            slug="m1-auth",
            name="Foundation: Email+password auth, sessions",
            consumes_requirements=["stack-constraint", "v1-ship-criteria"],
        )
    )
    assert record.kind.value == "foundation"
    assert _read_kind_on_disk(record.path) == "foundation"


def test_t_ab65_autopromotes_when_slug_contains_foundation(
    tmp_path: Path,
) -> None:
    """LDR-rerun v2 case: agents moved "Foundation" out of title
    prefix (renamed to "Auth + Session Foundation") but the slug
    stayed ``m1-auth-session-foundation``. Slug check catches this
    loophole — substrate identifiers don't use 'foundation' for any
    reason other than the routing keyword."""
    root = _setup_project_with_reqs(
        tmp_path,
        [("stack-constraint", "foundation"), ("v1-ship-criteria", "capability")],
    )
    reg = MilestoneRegistry(root)
    record = reg.write(
        _payload(
            slug="m1-auth-session-foundation",
            name="Auth + Session Foundation",
            consumes_requirements=["stack-constraint", "v1-ship-criteria"],
        )
    )
    assert record.kind.value == "foundation"
    assert _read_kind_on_disk(record.path) == "foundation"


def test_t_ab65_accepts_foundation_titled_foundation_kind(
    tmp_path: Path,
) -> None:
    """Title + kind agree on foundation — no promotion needed, no
    change. (Drop the capability-axis cite since foundation-kind
    milestones can't consume it per check 1.)"""
    from wonderland.milestone import MilestoneKind

    root = _setup_project_with_reqs(
        tmp_path, [("stack-constraint", "foundation")]
    )
    reg = MilestoneRegistry(root)
    record = reg.write(
        _payload(
            slug="m1-auth",
            name="Foundation: Email+password auth, sessions",
            kind=MilestoneKind.FOUNDATION,
            consumes_requirements=["stack-constraint"],
        )
    )
    assert record.kind.value == "foundation"


def test_t_ab65_accepts_non_foundation_titled_capability_kind(
    tmp_path: Path,
) -> None:
    """Capability-titled, capability-slugged, capability-kind —
    nothing changes."""
    root = _setup_project_with_reqs(
        tmp_path, [("kohl-signin", "capability")]
    )
    reg = MilestoneRegistry(root)
    record = reg.write(
        _payload(
            slug="m1-signin",
            name="Sign-up and sign-in user flow",
            consumes_requirements=["kohl-signin"],
        )
    )
    assert record.kind.value == "capability"


def test_t_ab65_case_insensitive_title_match(tmp_path: Path) -> None:
    """Title regex is case-insensitive — ``foundation:`` or
    ``FOUNDATION:`` both trigger autopromote."""
    root = _setup_project_with_reqs(
        tmp_path,
        [("stack", "foundation"), ("ship-criteria", "capability")],
    )
    reg = MilestoneRegistry(root)
    record = reg.write(
        _payload(
            slug="m1",
            name="foundation: lowercase variant",
            consumes_requirements=["stack", "ship-criteria"],
        )
    )
    assert record.kind.value == "foundation"


def test_t_ab65_no_promote_when_neither_signal(tmp_path: Path) -> None:
    """No 'foundation' in slug, no 'Foundation:' in title — nothing
    autopromotes. Tests that the autopromote is genuinely scoped
    to the signal patterns."""
    root = _setup_project_with_reqs(
        tmp_path, [("kohl-signin", "capability")]
    )
    reg = MilestoneRegistry(root)
    record = reg.write(
        _payload(
            slug="m1-signin-flow",
            name="Sign-up and sign-in flow",
            consumes_requirements=["kohl-signin"],
        )
    )
    assert record.kind.value == "capability"


def test_t_ab65_no_promote_on_mid_title_foundation(
    tmp_path: Path,
) -> None:
    """The title regex anchors to start — 'Foundation' appearing
    mid-string without colon prefix doesn't trigger. (Captures the
    metaphorical-use case: 'Build a foundation-shaped feature' is
    legitimately capability work.)"""
    root = _setup_project_with_reqs(
        tmp_path, [("kohl-signin", "capability")]
    )
    reg = MilestoneRegistry(root)
    record = reg.write(
        _payload(
            slug="m1-feature",
            name="Sign-up feature on the foundation layer",
            consumes_requirements=["kohl-signin"],
        )
    )
    assert record.kind.value == "capability"
