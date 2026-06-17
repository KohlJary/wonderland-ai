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
    reattribute_orphaned_tickets,
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


# ---------- T-ab63 pass 2 — title-similarity clustering ----------


def _write_ticket_titled(
    project_root: Path, slug: str, title: str, sources: list[str],
    guid: str,
) -> None:
    """Like _write_ticket but separates title text from slug. Needed
    for title-similarity tests where conceptually-equivalent tickets
    have distinct slugs but overlapping title tokens."""
    tic_dir = project_root / ".wonderland" / "tickets"
    tic_dir.mkdir(parents=True, exist_ok=True)
    body = (
        f"## Ticket 001: {title}\n\n"
        f"**GUID:** {guid}\n"
        f"**Sources:** {', '.join(sources)}\n"
        f"**Owner:** tweedledum\n"
        f"**Tier:** v1\n"
        f"**Stack span:** backend\n"
        f"**Estimate:** 0.5d\n\n"
        f"**Description:**\n\nx\n"
    )
    (tic_dir / f"ticket-{guid}-{slug}.md").write_text(body, encoding="utf-8")


def test_t_ab63p2_title_similarity_catches_ldr_final_pattern(
    tmp_path: Path,
) -> None:
    """T-ab63 pass 2: title-token Jaccard catches near-duplicates that
    EXACT upstream-source clustering misses. Mirrors ldr-final M1
    design's 5 schema tickets across 5 different features: each
    decomposed from different upstream stories (so exact-source
    clusters miss them), but their titles share 'sqlite + schema +
    migration + users + partner_profile + tables' token overlap.
    """
    _write_feature(tmp_path, "feat-a", ["story-aa"], guid="01AAAAAA")
    _write_feature(tmp_path, "feat-b", ["story-bb"], guid="01BBBBBB")
    _write_feature(tmp_path, "feat-c", ["story-cc"], guid="01CCCCCC")

    # Three tickets, three different features, three different
    # upstream stories — but all about "SQLite schema migration for
    # users and partner_profile tables". Title-Jaccard ≥ 0.6.
    _write_ticket_titled(
        tmp_path, "schema-1",
        "SQLite schema migration for users and partner_profile tables",
        ["feat-a", "story-aa"], guid="01TKT001",
    )
    _write_ticket_titled(
        tmp_path, "schema-2",
        "SQLite schema and migration: users + partner_profile",
        ["feat-b", "story-bb"], guid="01TKT002",
    )
    _write_ticket_titled(
        tmp_path, "schema-3",
        "Migration for users and partner_profile SQLite schema",
        ["feat-c", "story-cc"], guid="01TKT003",
    )

    decisions = find_cross_feature_duplicates(tmp_path)
    # Should detect one cluster covering all 3 schema tickets
    assert len(decisions) == 1
    decision = decisions[0]
    all_slugs = {decision.kept_slug, *decision.retracted_slugs}
    assert all_slugs == {"schema-1", "schema-2", "schema-3"}
    # The retracted set should be 2 of the 3
    assert len(decision.retracted_slugs) == 2


def test_t_ab63p2_title_similarity_respects_threshold(
    tmp_path: Path,
) -> None:
    """Pass 2 doesn't cluster tickets with weak title overlap. E.g.,
    'test signup' and 'test signin' share only 'test' but should
    stay separate (they're testing different things)."""
    _write_feature(tmp_path, "feat-a", ["story-aa"], guid="01AAAAAA")
    _write_feature(tmp_path, "feat-b", ["story-bb"], guid="01BBBBBB")
    _write_ticket_titled(
        tmp_path, "signup-test", "Test signup endpoint behavior",
        ["feat-a", "story-aa"], guid="01TKT001",
    )
    _write_ticket_titled(
        tmp_path, "signin-test", "Test signin endpoint behavior",
        ["feat-b", "story-bb"], guid="01TKT002",
    )
    decisions = find_cross_feature_duplicates(tmp_path)
    # Two tickets share 'test endpoint behavior' but differ on
    # 'signup' vs 'signin' — Jaccard should be ~0.5, below threshold
    # of 0.6. Stay distinct.
    assert decisions == []


def test_t_ab63p2_title_similarity_requires_distinct_parents(
    tmp_path: Path,
) -> None:
    """Two near-duplicate tickets under the SAME feature don't trigger
    Pass 2 (that's M3.5 within-feature consolidation territory).
    Pass 2 is cross-feature only by design."""
    _write_feature(tmp_path, "feat-a", ["story-aa"], guid="01AAAAAA")
    _write_ticket_titled(
        tmp_path, "schema-a1",
        "SQLite schema migration for users table",
        ["feat-a", "story-aa"], guid="01TKT001",
    )
    _write_ticket_titled(
        tmp_path, "schema-a2",
        "SQLite schema migration users table setup",
        ["feat-a", "story-aa"], guid="01TKT002",
    )
    decisions = find_cross_feature_duplicates(tmp_path)
    # Same parent feature → not a Pass 2 cluster
    assert decisions == []


def test_t_ab63p2_pass1_consolidated_tickets_excluded_from_pass2(
    tmp_path: Path,
) -> None:
    """A ticket already clustered by Pass 1 (exact upstream-source
    match) shouldn't be re-clustered by Pass 2. Avoids double-jeopardy
    in the decision list."""
    _write_feature(tmp_path, "feat-a", ["story-x"], guid="01AAAAAA")
    _write_feature(tmp_path, "feat-b", ["story-x"], guid="01BBBBBB")
    # Two tickets with IDENTICAL upstream sources — Pass 1 catches
    _write_ticket_titled(
        tmp_path, "schema-1",
        "SQLite schema migration users partner_profile",
        ["feat-a", "story-x"], guid="01TKT001",
    )
    _write_ticket_titled(
        tmp_path, "schema-2",
        "SQLite schema migration users partner_profile",
        ["feat-b", "story-x"], guid="01TKT002",
    )
    decisions = find_cross_feature_duplicates(tmp_path)
    assert len(decisions) == 1
    # Both tickets in one cluster
    all_slugs = {decisions[0].kept_slug, *decisions[0].retracted_slugs}
    assert all_slugs == {"schema-1", "schema-2"}


# ---------- T-ab78: orphaned-ticket re-attribution ----------


def _write_feature_milestoned(
    project_root: Path, slug: str, milestone: str | None, guid: str,
) -> None:
    """Feature markdown carrying a milestone field (for active-scope
    re-attribution tests)."""
    feat_dir = project_root / ".wonderland" / "features"
    feat_dir.mkdir(parents=True, exist_ok=True)
    body = (
        f"## Feature 001: {slug}\n\n"
        f"**GUID:** {guid}\n"
        f"**Slug:** {slug}\n"
        f"**Milestone:** {milestone or '—'}\n"
        f"**Sources:** story-x\n"
        f"**Stack span:** backend\n\n"
        f"**Description:**\n\nx\n"
    )
    (feat_dir / f"feature-{guid}-{slug}.md").write_text(body, encoding="utf-8")


def test_reattributes_milestone_orphaned_ticket(tmp_path: Path) -> None:
    """A ticket citing only the milestone (no feature) gets re-homed to
    the feature whose title best matches — the M2 failure mode."""
    _write_feature(tmp_path, "partner-profile-schema-and-post-partner-endpoint",
                   ["story-x"], guid="01AAAAAA")
    _write_feature(tmp_path, "server-side-geocoding-and-timezone-resolver",
                   ["story-x"], guid="01BBBBBB")
    # Orphan: cites the milestone slug, not a feature.
    _write_ticket_titled(
        tmp_path, "partner-schema-write-endpoint-stub",
        "Partner profile schema + write endpoint stub",
        ["m2-partner-profile-storage", "story-x"], guid="01TKT001",
    )
    reattached = reattribute_orphaned_tickets(tmp_path)
    assert len(reattached) == 1
    slug, feature, score = reattached[0]
    assert slug == "partner-schema-write-endpoint-stub"
    assert feature == "partner-profile-schema-and-post-partner-endpoint"
    # On-disk sources now lead with the feature.
    text = (tmp_path / ".wonderland" / "tickets"
            / "ticket-01TKT001-partner-schema-write-endpoint-stub.md").read_text()
    assert "**Sources:** partner-profile-schema-and-post-partner-endpoint" in text


def test_reattribution_skips_already_attributed(tmp_path: Path) -> None:
    """A ticket already citing a feature is left untouched."""
    _write_feature(tmp_path, "feat-a", ["story-x"], guid="01AAAAAA")
    _write_ticket_titled(
        tmp_path, "t1", "Some ticket title", ["feat-a", "story-x"],
        guid="01TKT001",
    )
    assert reattribute_orphaned_tickets(tmp_path) == []


def test_surface_dedup_catches_orphan_plus_parented_directly(
    tmp_path: Path,
) -> None:
    """Unification: a parented ticket + an orphan that build the same
    surface are caught by the surface pass DIRECTLY — orphans are included,
    no re-attribution needed first. (Was: orphan invisible until re-homed,
    then cross-feature Jaccard. The unified surface pass subsumes that.)"""
    _write_feature(tmp_path, "schema-feature-alpha", ["story-x"], guid="01AAAAAA")
    _write_ticket_titled(
        tmp_path, "schema-ticket-1",
        "Set up SQLite schema migration for users", ["schema-feature-alpha"],
        guid="01TKT001",
    )
    # Orphan with the same surface (be|act:schema).
    _write_ticket_titled(
        tmp_path, "schema-ticket-2",
        "SQLite schema migration", ["m2-some-milestone"],
        guid="01TKT002",
    )
    decisions = find_surface_duplicates(tmp_path)
    assert len(decisions) == 1
    assert {decisions[0].kept_slug, *decisions[0].retracted_slugs} == {
        "schema-ticket-1", "schema-ticket-2",
    }
    assert decisions[0].kept_slug == "schema-ticket-1"  # parented wins


def test_reattribution_scopes_to_active_milestone(tmp_path: Path) -> None:
    """An M2 orphan never re-homes to an M1 feature when active_slug is
    given — only active-milestone features are candidates."""
    _write_feature_milestoned(
        tmp_path, "auth-foundation-feature", "m1-auth-foundation", "01AAAAAA")
    _write_feature_milestoned(
        tmp_path, "partner-profile-storage-feature",
        "m2-partner-profile-storage", "01BBBBBB")
    # Orphan whose title happens to share tokens with BOTH, but belongs to M2.
    _write_ticket_titled(
        tmp_path, "partner-profile-write",
        "partner profile storage write path", ["m2-partner-profile-storage"],
        guid="01TKT001",
    )
    reattached = reattribute_orphaned_tickets(
        tmp_path, "m2-partner-profile-storage")
    assert len(reattached) == 1
    assert reattached[0][1] == "partner-profile-storage-feature"


# ---------- T-ab79: within-feature dedup (surface signatures) ----------

from wonderland.cross_feature import (  # noqa: E402
    _surface_signature,
    consolidate_surface_duplicates,
    consolidate_within_feature_duplicates,
    find_surface_duplicates,
    find_within_feature_duplicates,
)


def test_surface_signature_extraction() -> None:
    assert _surface_signature("Implement POST /auth/signup with validation") == "be|path:/auth/signup"
    assert _surface_signature("POST /auth/signup — account creation") == "be|path:/auth/signup"
    assert _surface_signature("POST /auth/signin verification") == "be|path:/auth/signin"
    assert _surface_signature("Frontend: Sign-up flow (email + password form)") == "fe|act:signup"
    assert _surface_signature("Implement frontend sign-in form") == "fe|act:signin"
    assert _surface_signature("Create SQLite schema for users") == "be|act:schema"
    # No derivable surface → None (never deduped)
    assert _surface_signature("Set up Vite proxy and CORS config") is None


def test_within_feature_dedup_clusters_same_surface(tmp_path: Path) -> None:
    """Two tickets under one feature building the same endpoint = dup."""
    _write_feature(tmp_path, "auth-feature", ["story-x"], guid="01AAAAAA")
    _write_ticket_titled(
        tmp_path, "signup-a", "Implement POST /auth/signup with validation",
        ["auth-feature"], guid="01TKT001",
    )
    _write_ticket_titled(
        tmp_path, "signup-b", "POST /auth/signup — account creation",
        ["auth-feature"], guid="01TKT002",
    )
    decisions = find_within_feature_duplicates(tmp_path)
    assert len(decisions) == 1
    assert {decisions[0].kept_slug, *decisions[0].retracted_slugs} == {"signup-a", "signup-b"}


def test_within_feature_signup_signin_not_merged(tmp_path: Path) -> None:
    """The false-positive guard: signup and signin are distinct surfaces
    even though their titles are ~50-100% lexically identical (the case
    that breaks title-Jaccard — frontend signup/signin flow titles are
    1.00 Jaccard)."""
    _write_feature(tmp_path, "auth-feature", ["story-x"], guid="01AAAAAA")
    _write_ticket_titled(
        tmp_path, "fe-signup", "Frontend: Sign-up flow (email + password form)",
        ["auth-feature"], guid="01TKT001",
    )
    _write_ticket_titled(
        tmp_path, "fe-signin", "Frontend: Sign-in flow (email + password form)",
        ["auth-feature"], guid="01TKT002",
    )
    assert find_within_feature_duplicates(tmp_path) == []


def test_within_feature_frontend_backend_same_action_not_merged(
    tmp_path: Path,
) -> None:
    """A frontend signup form and the backend signup endpoint are distinct
    deliverables — layer keeps them apart."""
    _write_feature(tmp_path, "auth-feature", ["story-x"], guid="01AAAAAA")
    _write_ticket_titled(
        tmp_path, "be-signup", "Implement POST /auth/signup endpoint",
        ["auth-feature"], guid="01TKT001",
    )
    _write_ticket_titled(
        tmp_path, "fe-signup", "Implement frontend sign-up form",
        ["auth-feature"], guid="01TKT002",
    )
    assert find_within_feature_duplicates(tmp_path) == []


def test_surface_dedup_catches_cross_feature_same_surface(tmp_path: Path) -> None:
    """Unification: same surface under DIFFERENT features IS a duplicate —
    grouping by surface signature alone catches it (the M1-fullstack leak
    where signup appeared under two features and cross-feature Jaccard
    missed it)."""
    _write_feature(tmp_path, "feat-a", ["story-x"], guid="01AAAAAA")
    _write_feature(tmp_path, "feat-b", ["story-x"], guid="01BBBBBB")
    _write_ticket_titled(
        tmp_path, "t-a", "POST /auth/signup endpoint", ["feat-a"], guid="01TKT001",
    )
    _write_ticket_titled(
        tmp_path, "t-b", "Implement POST /auth/signup with validation", ["feat-b"],
        guid="01TKT002",
    )
    decisions = find_surface_duplicates(tmp_path)
    assert len(decisions) == 1
    assert {decisions[0].kept_slug, *decisions[0].retracted_slugs} == {"t-a", "t-b"}


def test_surface_dedup_includes_orphans_and_prefers_parented(
    tmp_path: Path,
) -> None:
    """An orphaned ticket (cites a story slug, no feature) sharing a surface
    with a parented ticket is a duplicate; the PARENTED one wins so the
    survivor has a home."""
    _write_feature(tmp_path, "feat-a", ["story-x"], guid="01AAAAAA")
    _write_ticket_titled(
        tmp_path, "parented", "POST /auth/signup endpoint with validation",
        ["feat-a"], guid="01TKT001",
    )
    _write_ticket_titled(
        tmp_path, "orphan", "POST /auth/signup",
        ["some-story-slug"], guid="01TKT002",  # no feature in sources
    )
    decisions = find_surface_duplicates(tmp_path)
    assert len(decisions) == 1
    assert decisions[0].kept_slug == "parented"  # parented beats orphan
    assert decisions[0].retracted_slugs == ("orphan",)


def test_reattribution_uses_surface_owner(tmp_path: Path) -> None:
    """An orphan re-homes to the feature that already owns its surface,
    even when the feature SLUG (a verbose user-story phrase) barely
    token-overlaps the orphan's technical title."""
    _write_feature(
        tmp_path, "kohl-signs-up-with-email-and-password", ["story-x"],
        guid="01AAAAAA",
    )
    # Parented ticket establishes the surface owner.
    _write_ticket_titled(
        tmp_path, "owned-signup", "Implement POST /auth/signup endpoint",
        ["kohl-signs-up-with-email-and-password"], guid="01TKT001",
    )
    # Orphan with the same surface, title that won't Jaccard-match the slug.
    _write_ticket_titled(
        tmp_path, "orphan-signup", "POST /auth/signup",
        ["a-story-slug"], guid="01TKT002",
    )
    reattached = reattribute_orphaned_tickets(tmp_path)
    assert ("orphan-signup", "kohl-signs-up-with-email-and-password", 1.0) in reattached


def test_consolidate_within_feature_aborts_retracted(tmp_path: Path) -> None:
    _write_feature(tmp_path, "auth-feature", ["story-x"], guid="01AAAAAA")
    _write_ticket_titled(
        tmp_path, "signup-keep", "Implement POST /auth/signup with full validation",
        ["auth-feature"], guid="01TKT001",
    )
    _write_ticket_titled(
        tmp_path, "signup-dup", "POST /auth/signup",
        ["auth-feature"], guid="01TKT002",
    )
    applied = consolidate_within_feature_duplicates(tmp_path)
    assert len(applied) == 1
    # Longest title wins (more specific)
    assert applied[0].kept_slug == "signup-keep"
    assert get_ticket_state(tmp_path, "signup-dup") == TicketState.ABORTED
    assert get_ticket_state(tmp_path, "signup-keep") is None  # untouched


def test_surface_dedup_skips_already_aborted(tmp_path: Path) -> None:
    """Regression: a ticket a PRIOR pass already aborted must not drag its
    live sibling down. Two same-surface tickets, one pre-aborted → the
    surface pass leaves the survivor alone (it must not re-cluster the dead
    one as winner and abort the live one — the schema-vanishes bug)."""
    from wonderland.ticket_lifecycle import back_fill_state, transition

    _write_feature(tmp_path, "feat-a", ["story-x"], guid="01AAAAAA")
    _write_ticket_titled(
        tmp_path, "schema-live", "Set up SQLite schema migration for users",
        ["feat-a"], guid="01TKT001",
    )
    _write_ticket_titled(
        tmp_path, "schema-dead", "SQLite schema migration",
        ["feat-a"], guid="01TKT002",
    )
    # Pre-abort schema-dead, as a prior pass would.
    back_fill_state(tmp_path, "schema-dead", TicketState.IN_PROGRESS)
    transition(tmp_path, "schema-dead", TicketState.ABORTED, by="prior-pass")

    decisions = find_surface_duplicates(tmp_path)
    assert decisions == []  # only one LIVE ticket on this surface → no dup
    consolidate_surface_duplicates(tmp_path)
    assert get_ticket_state(tmp_path, "schema-live") is None  # survivor untouched


def test_cross_feature_does_not_merge_different_surfaces_sharing_upstream(
    tmp_path: Path,
) -> None:
    """Regression (M1-verify): tickets that share an upstream story but
    build DIFFERENT surfaces are NOT duplicates. One story decomposes into
    many surfaces; Pass 1's exact-upstream clustering must not merge them.
    This is the bug that deleted 14 distinct tickets (incl. both frontend
    forms) keeping only session-middleware."""
    _write_feature(tmp_path, "feat-a", ["story-auth"], guid="01AAAAAA")
    _write_feature(tmp_path, "feat-b", ["story-auth"], guid="01BBBBBB")
    _write_ticket_titled(
        tmp_path, "signup-a", "POST /auth/signup endpoint",
        ["feat-a", "story-auth"], guid="01TKT001",
    )
    _write_ticket_titled(
        tmp_path, "signin-b", "POST /auth/signin endpoint",
        ["feat-b", "story-auth"], guid="01TKT002",
    )
    _write_ticket_titled(
        tmp_path, "me-a", "GET /auth/me endpoint",
        ["feat-a", "story-auth"], guid="01TKT003",
    )
    _write_ticket_titled(
        tmp_path, "schema-b", "Set up SQLite schema for users",
        ["feat-b", "story-auth"], guid="01TKT004",
    )
    decisions = find_cross_feature_duplicates(tmp_path)
    retracted = [s for d in decisions for s in d.retracted_slugs]
    assert retracted == []  # all distinct surfaces → nothing merged


def test_cross_feature_still_merges_same_surface_sharing_upstream(
    tmp_path: Path,
) -> None:
    """The guard doesn't break legit dedup: two SAME-surface tickets under
    different features sharing an upstream story still merge."""
    _write_feature(tmp_path, "feat-a", ["story-auth"], guid="01AAAAAA")
    _write_feature(tmp_path, "feat-b", ["story-auth"], guid="01BBBBBB")
    _write_ticket_titled(
        tmp_path, "signup-a", "POST /auth/signup endpoint",
        ["feat-a", "story-auth"], guid="01TKT001",
    )
    _write_ticket_titled(
        tmp_path, "signup-b", "Implement POST /auth/signup with validation",
        ["feat-b", "story-auth"], guid="01TKT002",
    )
    decisions = find_cross_feature_duplicates(tmp_path)
    retracted = [s for d in decisions for s in d.retracted_slugs]
    assert len(retracted) == 1  # the two signups merge


def test_reattribution_refuses_unowned_surface(tmp_path: Path) -> None:
    """An orphan whose surface no in-scope feature owns must NOT be
    reattached, even when title-Jaccard would clear the threshold. T-ab78
    follow-up: the M3 run leaked an M4 news-card ticket into the M3 weather
    feature because 'News card: frontend rendering...' ≈ 'Weather card:
    frontend rendering...' on tokens. The surface (newscard vs weathercard)
    tells them apart; the gate refuses the cross-surface match."""
    _write_feature(tmp_path, "weather-card-cached-data", ["story-w"], guid="01AAAAAA")
    # Weather feature owns the weathercard surface (a parented ticket).
    _write_ticket_titled(
        tmp_path, "weather-owned",
        "Frontend: render the weather card component",
        ["weather-card-cached-data"], guid="01TKT001",
    )
    # Orphan weather ticket — same surface → reattaches.
    _write_ticket_titled(
        tmp_path, "weather-orphan",
        "Weather card: frontend rendering from cached API response",
        ["m3-some-milestone"], guid="01TKT002",
    )
    # Orphan NEWS ticket — different surface, no owner → must NOT reattach.
    _write_ticket_titled(
        tmp_path, "news-orphan",
        "News card: frontend rendering from cached API response",
        ["m3-some-milestone"], guid="01TKT003",
    )
    homed = {slug for slug, _, _ in reattribute_orphaned_tickets(tmp_path)}
    assert "weather-orphan" in homed
    assert "news-orphan" not in homed


def test_surface_dedup_keeps_distinct_responsibilities_same_path(
    tmp_path: Path,
) -> None:
    """Same-path tickets with DIFFERENT responsibilities (serve HTML vs serve
    data vs wire middleware) are not duplicates — they must all survive.
    ldr-ophanic M2: the /dashboard data endpoint got culled as a 'dup' of the
    HTML-serving endpoint, stranding the time card with no data to render."""
    _write_feature(tmp_path, "dash-feat", ["story-x"], guid="01AAAAAA")
    _write_ticket_titled(
        tmp_path, "serve-html",
        "GET /dashboard serves the React SPA index.html shell",
        ["dash-feat"], guid="01TKT001")
    _write_ticket_titled(
        tmp_path, "serve-data",
        "GET /dashboard returns partner profile data and session validation",
        ["dash-feat"], guid="01TKT002")
    _write_ticket_titled(
        tmp_path, "middleware",
        "Wire session middleware to protect the /dashboard route",
        ["dash-feat"], guid="01TKT003")
    assert find_surface_duplicates(tmp_path) == []


def test_surface_dedup_still_merges_same_responsibility(tmp_path: Path) -> None:
    """Control: genuine reworded duplicates on the same path still merge."""
    _write_feature(tmp_path, "auth-feat", ["story-x"], guid="01AAAAAA")
    _write_ticket_titled(
        tmp_path, "signup-a",
        "Implement POST /auth/signup endpoint with email validation",
        ["auth-feat"], guid="01TKT001")
    _write_ticket_titled(
        tmp_path, "signup-b",
        "POST /auth/signup endpoint with email and password validation",
        ["auth-feat"], guid="01TKT002")
    decs = find_surface_duplicates(tmp_path)
    assert len(decs) == 1
    assert {decs[0].kept_slug, *decs[0].retracted_slugs} == {"signup-a", "signup-b"}
