"""Tests for content-level scope-leak detection + retraction (T-ab74).

Seeded with the six real ldr-final M1-design tickets that touched
cross-milestone surfaces: 3 genuine leaks (title names a foreign-milestone
surface = deliverable leak) and 3 legitimate references (foreign surface
appears only in the body as a guard/redirect target). The title-token gate
must flag 3 and clear 3.
"""

from __future__ import annotations

import re
from pathlib import Path

from wonderland.scope_leak import (
    ScopeLeakDecision,
    find_content_scope_leaks,
    retract_content_scope_leaks,
)
from wonderland.ticket_lifecycle import (
    TicketState,
    get_state as get_ticket_state,
    transition as ticket_transition,
)

# The ldr-final roster. m1-auth-foundation is the active milestone.
_ROSTER = [
    (1, "m1-auth-foundation", "Auth Foundation"),
    (2, "m2-partner-profile-storage", "Partner Profile Storage"),
    (3, "m3-time-card", "Time Card"),
    (4, "m4-weather-card", "Weather Card"),
    (5, "m5-news-card", "News Card"),
    (6, "m6-dashboard-integration-and-demo-readiness",
     "Dashboard Integration and Demo Readiness"),
]

# The six real ldr-final tickets touching cross-milestone surfaces.
# (title, expected_leak)
_LDR_TICKETS = [
    ("Implement session middleware and GET /auth/me endpoint", False),
    ("Frontend: call protected dashboard endpoint and handle 401 "
     "redirect to signin", True),
    ("Protect dashboard backend route behind auth middleware", True),
    ("Frontend dashboard page structure, API integration for protected "
     "route and 401 redirect", True),
    ("Frontend: sign up and sign in routes, forms, and backend "
     "integration", False),
    ("Backend signin endpoint, session middleware, signed cookies, "
     "and /api/me route", False),
]


def _slugify(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s[:60]


def _write_milestone(
    project_root: Path, order: int, slug: str, name: str,
) -> None:
    ms_dir = project_root / ".wonderland" / "milestones"
    ms_dir.mkdir(parents=True, exist_ok=True)
    body = (
        f"## Milestone {order:02d}: {name}\n\n"
        f"**GUID:** 01MILESTN\n"
        f"**Slug:** {slug}\n"
        f"**Order:** {order}\n"
        f"**Kind:** capability\n"
        f"**Deferred:** false\n"
        f"**Confidence:** high\n\n"
        f"**Goal:**\n\nx\n"
    )
    # Filename id must be Crockford base32 (no I/L/O/U) to match the
    # milestone registry's filename pattern.
    (ms_dir / f"milestone-0MST00{order:02d}-{slug}.md").write_text(
        body, encoding="utf-8"
    )


_PARENT_FEATURE_SLUG = "auth-foundation-feature"


def _write_feature(
    project_root: Path, slug: str, milestone: str | None,
    guid: str = "0FEAT001",
) -> None:
    """Write a minimal feature markdown carrying a milestone field —
    the gate resolves ticket -> parent feature -> milestone and only
    examines tickets whose parent belongs to the active milestone."""
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


def _write_ticket(
    project_root: Path, title: str, *, number: int,
    parent: str = _PARENT_FEATURE_SLUG,
) -> str:
    """Write a minimal ticket markdown sourcing a parent feature; return
    its slug."""
    tic_dir = project_root / ".wonderland" / "tickets"
    tic_dir.mkdir(parents=True, exist_ok=True)
    slug = _slugify(title)
    guid = f"01TKT{number:03d}"
    body = (
        f"## Ticket {number:03d}: {title}\n\n"
        f"**GUID:** {guid}\n"
        f"**Sources:** {parent}, story-x\n"
        f"**Owner:** tweedledum\n"
        f"**Tier:** v1\n"
        f"**Stack span:** backend\n"
        f"**Estimate:** 0.5d\n\n"
        f"**Description:**\n\nx\n"
    )
    (tic_dir / f"ticket-{guid}-{slug}.md").write_text(body, encoding="utf-8")
    return slug


def _seed_roster(
    project_root: Path, *, parent_milestone: str | None = "m1-auth-foundation",
) -> None:
    """Seed the milestone roster + a parent feature tagged to the active
    milestone so tickets sourcing it are in-scope for the gate."""
    for order, slug, name in _ROSTER:
        _write_milestone(project_root, order, slug, name)
    _write_feature(project_root, _PARENT_FEATURE_SLUG, parent_milestone)


# ---------- detection ----------


def test_ldr_final_six_tickets_three_flag_three_clear(tmp_path: Path) -> None:
    """The canonical ldr-final fixture: 3 leaks flagged, 3 legit cleared."""
    _seed_roster(tmp_path)
    title_for_slug: dict[str, str] = {}
    for i, (title, _leak) in enumerate(_LDR_TICKETS, start=1):
        slug = _write_ticket(tmp_path, title, number=i)
        title_for_slug[slug] = title

    decisions = find_content_scope_leaks(tmp_path, "m1-auth-foundation")
    flagged_titles = {d.title for d in decisions}

    expected_leaks = {t for t, leak in _LDR_TICKETS if leak}
    expected_clean = {t for t, leak in _LDR_TICKETS if not leak}

    assert flagged_titles == expected_leaks
    assert not (flagged_titles & expected_clean)
    # Every leak is attributed to m6 (the dashboard owner).
    for d in decisions:
        assert "dashboard" in d.foreign_tokens
        assert "m6-dashboard-integration-and-demo-readiness" in d.foreign_milestones


def test_active_milestone_tokens_are_not_foreign(tmp_path: Path) -> None:
    """A ticket whose title names the ACTIVE milestone's surface (auth)
    is never flagged, even though 'auth' is a domain noun."""
    _seed_roster(tmp_path)
    _write_ticket(tmp_path, "Build the auth foundation signup endpoint", number=1)
    decisions = find_content_scope_leaks(tmp_path, "m1-auth-foundation")
    assert decisions == []


def test_no_active_scope_is_noop(tmp_path: Path) -> None:
    _seed_roster(tmp_path)
    _write_ticket(tmp_path, "Protect dashboard backend route", number=1)
    assert find_content_scope_leaks(tmp_path, "") == []


def test_single_milestone_roster_is_noop(tmp_path: Path) -> None:
    """Nothing to leak across when there's only one milestone."""
    _write_milestone(tmp_path, 1, "m1-auth-foundation", "Auth Foundation")
    _write_ticket(tmp_path, "Protect dashboard backend route", number=1)
    assert find_content_scope_leaks(tmp_path, "m1-auth-foundation") == []


def test_does_not_reach_into_other_milestones_tickets(tmp_path: Path) -> None:
    """T-ab76 regression: an M2 design run must NOT retract M1's auth
    tickets just because 'auth' is a foreign token under M2. The gate
    only examines tickets whose parent feature belongs to the ACTIVE
    milestone."""
    _seed_roster(tmp_path, parent_milestone="m1-auth-foundation")
    # An M1 auth ticket parented to the M1 feature.
    _write_ticket(tmp_path, "POST /auth/signup endpoint", number=1)
    # Active scope is now M2 — the M1 ticket is out of purview.
    decisions = find_content_scope_leaks(tmp_path, "m2-partner-profile-storage")
    assert decisions == []


def test_ticket_with_unresolvable_parent_milestone_is_skipped(
    tmp_path: Path,
) -> None:
    """Conservative: a ticket whose parent feature has no milestone field
    can't be positively attributed to the active scope, so it's never
    retracted."""
    _seed_roster(tmp_path, parent_milestone=None)  # feature.milestone unset
    _write_ticket(tmp_path, "Protect dashboard backend route", number=1)
    assert find_content_scope_leaks(tmp_path, "m1-auth-foundation") == []


def test_generic_scaffolding_tokens_do_not_flag(tmp_path: Path) -> None:
    """'integration' / 'storage' / 'time' are stopworded — a ticket whose
    only foreign-looking token is generic scaffolding is not flagged."""
    _seed_roster(tmp_path)
    _write_ticket(
        tmp_path, "Wire backend integration test storage harness", number=1
    )
    assert find_content_scope_leaks(tmp_path, "m1-auth-foundation") == []


# ---------- retraction ----------


def test_retracts_only_the_three_leaks(tmp_path: Path) -> None:
    _seed_roster(tmp_path)
    slug_leak: dict[str, bool] = {}
    for i, (title, leak) in enumerate(_LDR_TICKETS, start=1):
        slug = _write_ticket(tmp_path, title, number=i)
        slug_leak[slug] = leak

    applied = retract_content_scope_leaks(tmp_path, "m1-auth-foundation")
    assert len(applied) == 3

    for slug, leak in slug_leak.items():
        state = get_ticket_state(tmp_path, slug)
        if leak:
            assert state == TicketState.ABORTED, slug
        else:
            # Legit tickets are never touched — no transition log at all.
            assert state is None, slug


def test_aborted_leak_is_recoverable(tmp_path: Path) -> None:
    """ABORTED is on the canonical retry path — an operator can un-abort."""
    _seed_roster(tmp_path)
    slug = _write_ticket(
        tmp_path, "Protect dashboard backend route", number=1
    )
    retract_content_scope_leaks(tmp_path, "m1-auth-foundation")
    assert get_ticket_state(tmp_path, slug) == TicketState.ABORTED
    # Recoverable: ABORTED → QUEUED is legal.
    ticket_transition(
        tmp_path, slug, TicketState.QUEUED, by="operator",
        notes="un-abort",
    )
    assert get_ticket_state(tmp_path, slug) == TicketState.QUEUED


def test_retraction_is_idempotent(tmp_path: Path) -> None:
    """Re-running the sweep on an already-aborted leak is a no-op that
    still reports it as applied (already in the target state)."""
    _seed_roster(tmp_path)
    _write_ticket(tmp_path, "Protect dashboard backend route", number=1)
    first = retract_content_scope_leaks(tmp_path, "m1-auth-foundation")
    second = retract_content_scope_leaks(tmp_path, "m1-auth-foundation")
    assert len(first) == 1
    assert len(second) == 1


def test_decision_summary_is_descriptive() -> None:
    d = ScopeLeakDecision(
        ticket_slug="protect-dashboard",
        title="Protect dashboard backend route",
        foreign_tokens=frozenset({"dashboard"}),
        foreign_milestones=("m6-dashboard-integration-and-demo-readiness",),
    )
    s = d.summary()
    assert "dashboard" in s
    assert "m6-dashboard-integration-and-demo-readiness" in s
