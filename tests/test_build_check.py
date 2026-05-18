"""Tests for the verify-kind Meeting + build_check hook (P16 T-v2).

A verify-kind meeting bypasses the agent-convening path entirely.
The substrate fires a registered verification check, emits a
BuildCheckEvent wrapped in MeetingStart/End events, and on failure
synthesizes a SystemReview + routes via the existing blocking-
review path so follow-up tickets land on disk.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from wonderland import (
    FeaturePayload,
    FeatureRegistry,
    StackSpan,
    TicketTier,
)
from wonderland.feature_lifecycle import FeatureState, transition
from wonderland.review import ReviewRegistry
from wonderland.ticket import TicketRegistry
from wonderland.verification import (
    VerificationFinding,
    VerificationResult,
    register_check,
)
from wonderland.workflow import (
    BuildCheckEvent,
    Meeting,
    MeetingEndEvent,
    MeetingStartEvent,
    _pick_feature_for_build_check_attribution,
    _run_verify_meeting,
    _synthesize_build_check_review,
)


# ---------- Meeting.kind + build_check validation ----------


def test_regular_meeting_defaults_to_kind_regular() -> None:
    m = Meeting(
        id="m1", label="M1", goal="g",
        roster=["alice"],
    )
    assert m.kind == "regular"
    assert m.build_check is None


def test_verify_meeting_requires_build_check() -> None:
    """kind='verify' without build_check is incoherent — the meeting
    has nothing to do. Validator must catch it."""
    with pytest.raises(ValueError, match="build_check"):
        Meeting(id="m9", label="M9", goal="g", kind="verify")


def test_verify_meeting_rejects_non_empty_roster() -> None:
    """Verify meetings don't convene agents — a roster would be
    misleading. Validator enforces emptiness."""
    with pytest.raises(ValueError, match="empty roster"):
        Meeting(
            id="m9", label="M9", goal="g", kind="verify",
            build_check="pytest_collects",
            roster=["caterpillar"],
        )


def test_verify_meeting_rejects_phases() -> None:
    """Verify meetings are one-shot checks, not rotations. No
    phases allowed."""
    from wonderland.workflow import PhaseSpec

    with pytest.raises(ValueError, match="no phases"):
        Meeting(
            id="m9", label="M9", goal="g", kind="verify",
            build_check="pytest_collects",
            phases=[PhaseSpec(name="p", max_rotations=1)],
        )


def test_regular_meeting_rejects_build_check() -> None:
    """A regular meeting with build_check is incoherent — the
    substrate wouldn't know what to do with it. Force the operator
    to pick a kind explicitly."""
    with pytest.raises(ValueError, match="kind='verify'"):
        Meeting(
            id="m1", label="M1", goal="g", kind="regular",
            roster=["alice"], build_check="pytest_collects",
        )


def test_regular_meeting_requires_roster() -> None:
    """The roster default became `[]` to support verify meetings,
    but regular meetings still need a non-empty roster. Validator
    re-enforces."""
    with pytest.raises(ValueError, match="non-empty roster"):
        Meeting(id="m1", label="M1", goal="g")


def test_verify_meeting_accepts_minimal_config() -> None:
    """The happy path: kind='verify' + build_check named + no
    roster + no phases → valid. Single-string build_check is
    normalized to a one-element list by the validator (so the
    runtime has a single shape to handle)."""
    m = Meeting(
        id="m9", label="M9", goal="g",
        kind="verify", build_check="pytest_collects",
    )
    assert m.kind == "verify"
    assert m.build_check == ["pytest_collects"]
    assert m.roster == []
    assert m.phases == []


def test_verify_meeting_accepts_list_of_checks() -> None:
    """Multiple checks can run in one verify meeting — each is
    invoked independently; findings union into one review."""
    m = Meeting(
        id="m9", label="M9", goal="g",
        kind="verify", build_check=["pytest_collects", "npm_build"],
    )
    assert m.build_check == ["pytest_collects", "npm_build"]


# ---------- _pick_feature_for_build_check_attribution ----------


def _make_feature(registry: FeatureRegistry, *, title: str) -> str:
    record = registry.write(
        FeaturePayload(
            title=title, description="d",
            stack_span=StackSpan.BACKEND,
            tier=TicketTier.V1, sources=["s"],
        )
    )
    return record.slug


def test_pick_returns_none_when_no_features(tmp_path: Path) -> None:
    assert _pick_feature_for_build_check_attribution(tmp_path) is None


def test_pick_returns_only_feature_when_one_exists(tmp_path: Path) -> None:
    reg = FeatureRegistry(tmp_path)
    slug = _make_feature(reg, title="solo")
    assert _pick_feature_for_build_check_attribution(tmp_path) == slug


def _drive_to(project_root: Path, slug: str, *path: FeatureState) -> None:
    """Walk the feature through the lifecycle states in order. The
    legal-transitions graph requires hopping via proposed → designed →
    queued → in_progress → ready_for_review; callers pass whichever
    subset they need (in valid order) and this helper applies them."""
    from wonderland.feature_lifecycle import back_fill_state, get_state
    # First transition must be from (initial); use back_fill_state
    # to seed PROPOSED if no record exists yet.
    if get_state(project_root, slug) is None:
        back_fill_state(project_root, slug, FeatureState.PROPOSED, notes="seed")
    for state in path:
        transition(project_root, slug, state, by="t", notes="seed")


def test_pick_prefers_ready_for_review_over_queued(tmp_path: Path) -> None:
    """Features in ready_for_review state are the most-recently-
    touched in the implementation pipeline. The hook attaches
    follow-up tickets there so the next run picks them up."""
    reg = FeatureRegistry(tmp_path)
    queued = _make_feature(reg, title="queued-one")
    ready = _make_feature(reg, title="ready-one")
    _drive_to(
        tmp_path, queued,
        FeatureState.IN_DESIGN, FeatureState.DESIGNED, FeatureState.QUEUED,
    )
    _drive_to(
        tmp_path, ready,
        FeatureState.IN_DESIGN, FeatureState.DESIGNED,
        FeatureState.QUEUED, FeatureState.IN_PROGRESS,
        FeatureState.READY_FOR_REVIEW,
    )
    assert _pick_feature_for_build_check_attribution(tmp_path) == ready


def test_pick_falls_back_to_any_feature_when_no_active_state(
    tmp_path: Path,
) -> None:
    reg = FeatureRegistry(tmp_path)
    first = _make_feature(reg, title="first")
    second = _make_feature(reg, title="second")
    # Both remain PENDING (default).
    picked = _pick_feature_for_build_check_attribution(tmp_path)
    assert picked == second
    assert first != second


# ---------- _synthesize_build_check_review ----------


def test_synthesize_review_writes_disk_artifact(tmp_path: Path) -> None:
    findings = (
        VerificationFinding(
            title="Pytest collection failed",
            location="src/api/sessions.py:14",
            concern="FastAPI dep resolution fails",
            request="Add Depends(get_db) to the route signature",
        ),
    )
    slug = _synthesize_build_check_review(
        project_root=tmp_path,
        check_name="pytest_collects",
        findings=findings,
        feature_slug="user-sessions",
    )
    assert slug is not None
    reg = ReviewRegistry(tmp_path)
    record = reg.find_by_slug(slug)
    assert record is not None
    body = record.read()
    assert "request-changes" in body
    assert "Pytest collection failed" in body
    assert "sessions.py:14" in body


def test_synthesize_review_handles_missing_location(tmp_path: Path) -> None:
    """Some collection errors don't carry a file:line — review still
    needs to satisfy ReviewPayload's non-empty target_files."""
    findings = (
        VerificationFinding(
            title="Pytest collection failed",
            location="", concern="...", request="...",
        ),
    )
    slug = _synthesize_build_check_review(
        project_root=tmp_path,
        check_name="pytest_collects",
        findings=findings,
        feature_slug="any-feature",
    )
    assert slug is not None
    body = ReviewRegistry(tmp_path).find_by_slug(slug).read()
    assert "verification" in body.lower()


# ---------- _run_verify_meeting (the substrate handler) ----------


class _FakeRunner:
    def __init__(self, project_root: Path | None) -> None:
        self.project_root = project_root


def _verify_meeting(name: str) -> Meeting:
    return Meeting(
        id="m9", label="M9", goal="run verification",
        kind="verify", build_check=name,
    )


@pytest.mark.asyncio
async def test_verify_meeting_short_circuits_when_no_project_root() -> None:
    """No project_root = no place to run pytest. Hook still emits
    start + end events (so the timeline shows the meeting fired)
    plus a skipped BuildCheckEvent."""
    runner = _FakeRunner(project_root=None)
    events = [e async for e in _run_verify_meeting(
        _verify_meeting("pytest_collects"), runner,
    )]
    # MeetingStart, BuildCheck (skipped), MeetingEnd
    assert isinstance(events[0], MeetingStartEvent)
    assert isinstance(events[-1], MeetingEndEvent)
    bc = next(e for e in events if isinstance(e, BuildCheckEvent))
    assert bc.skipped is True
    assert "project_root" in bc.skip_reason


@pytest.mark.asyncio
async def test_verify_meeting_short_circuits_when_check_unknown(
    tmp_path: Path,
) -> None:
    """Unknown check name (typo in YAML) emits a skipped event but
    still fires the start/end pair so the timeline shows it ran."""
    runner = _FakeRunner(project_root=tmp_path)
    events = [e async for e in _run_verify_meeting(
        _verify_meeting("not-a-real-check"), runner,
    )]
    bc = next(e for e in events if isinstance(e, BuildCheckEvent))
    assert bc.skipped is True
    assert "Unknown" in bc.skip_reason


@pytest.mark.asyncio
async def test_verify_meeting_emits_ok_event_on_success(
    tmp_path: Path,
) -> None:
    def passing(_root: Path) -> VerificationResult:
        return VerificationResult(check_name="fake_ok", ok=True)
    register_check("fake_ok", passing)

    runner = _FakeRunner(project_root=tmp_path)
    try:
        events = [e async for e in _run_verify_meeting(
            _verify_meeting("fake_ok"), runner,
        )]
    finally:
        from wonderland.verification import _CHECK_REGISTRY
        _CHECK_REGISTRY.pop("fake_ok", None)

    bc = next(e for e in events if isinstance(e, BuildCheckEvent))
    assert bc.ok is True
    assert bc.skipped is False
    assert bc.review_slug is None
    end = next(e for e in events if isinstance(e, MeetingEndEvent))
    assert end.outcome == "COMPLETE"
    # No reviews persisted.
    assert ReviewRegistry(tmp_path).list_reviews() == []


@pytest.mark.asyncio
async def test_verify_meeting_emits_skipped_event(tmp_path: Path) -> None:
    def skipper(_root: Path) -> VerificationResult:
        return VerificationResult(
            check_name="fake_skip", ok=False,
            skipped=True, skip_reason="no test setup",
        )
    register_check("fake_skip", skipper)

    runner = _FakeRunner(project_root=tmp_path)
    try:
        events = [e async for e in _run_verify_meeting(
            _verify_meeting("fake_skip"), runner,
        )]
    finally:
        from wonderland.verification import _CHECK_REGISTRY
        _CHECK_REGISTRY.pop("fake_skip", None)

    bc = next(e for e in events if isinstance(e, BuildCheckEvent))
    assert bc.skipped is True
    end = next(e for e in events if isinstance(e, MeetingEndEvent))
    # Skipped = no findings to act on; outcome still COMPLETE (the
    # check itself didn't fail; we just don't have test infra).
    assert end.outcome == "COMPLETE"


@pytest.mark.asyncio
async def test_verify_meeting_synthesizes_review_and_tickets(
    tmp_path: Path,
) -> None:
    """Full flow: check fails, hook writes review, picks feature,
    calls _route_blocking_review which synthesizes follow-up tickets
    on disk."""
    reg = FeatureRegistry(tmp_path)
    record = reg.write(FeaturePayload(
        title="alpha feature", description="d",
        stack_span=StackSpan.BACKEND, tier=TicketTier.V1, sources=["s"],
    ))
    _drive_to(
        tmp_path, record.slug,
        FeatureState.IN_DESIGN, FeatureState.DESIGNED,
        FeatureState.QUEUED, FeatureState.IN_PROGRESS,
        FeatureState.READY_FOR_REVIEW,
    )

    def failer(_root: Path) -> VerificationResult:
        return VerificationResult(
            check_name="fake_fail", ok=False, skipped=False,
            findings=(
                VerificationFinding(
                    title="Pytest collection failed",
                    location="src/api/sessions.py:14",
                    concern="FastAPI fails to resolve Depends",
                    request="Add Depends(get_db) to get_current_user",
                    severity="block",
                ),
            ),
        )
    register_check("fake_fail", failer)

    runner = _FakeRunner(project_root=tmp_path)
    try:
        events = [e async for e in _run_verify_meeting(
            _verify_meeting("fake_fail"), runner,
        )]
    finally:
        from wonderland.verification import _CHECK_REGISTRY
        _CHECK_REGISTRY.pop("fake_fail", None)

    # Multi-check semantics: the per-check BuildCheckEvent carries
    # the check's own outcome (no review_slug yet). A second
    # BuildCheckEvent fires after all checks complete carrying the
    # synthesized review_slug. Grab both.
    build_events = [e for e in events if isinstance(e, BuildCheckEvent)]
    per_check = build_events[0]
    final = build_events[-1]
    assert per_check.ok is False
    assert per_check.skipped is False
    assert per_check.findings_count == 1
    assert final.review_slug is not None
    end = next(e for e in events if isinstance(e, MeetingEndEvent))
    assert end.outcome == "REQUEST_CHANGES"

    review_record = ReviewRegistry(tmp_path).find_by_slug(final.review_slug)
    assert review_record is not None
    tickets = TicketRegistry(tmp_path).list_tickets()
    assert len(tickets) == 1
    ticket = tickets[0]
    assert "Pytest collection failed" in ticket.title
    body = ticket.read()
    assert final.review_slug in body


@pytest.mark.asyncio
async def test_verify_does_not_auto_complete_existing_feature_tickets(
    tmp_path: Path,
) -> None:
    """Mvp-demo regression: when build_check (verify) fires after
    M8 in the same run, M8 has already routed the iteration's
    request-changes review and synthesized follow-up tickets in
    QUEUED state. Build_check then calls _route_blocking_review
    for its own pytest failure — and the auto-complete sweep
    used to grab those freshly-queued M8 follow-ups and mark
    them DONE within seconds of creation, before any pass worked
    them.

    Fix: build_check passes auto_complete_in_flight_tickets=False
    so its routing only synthesizes the pytest follow-up ticket.
    The M8 follow-ups stay QUEUED.
    """
    from wonderland.ticket import TicketPayload, TicketSource
    from wonderland.ticket_lifecycle import (
        TicketState,
        back_fill_state,
        get_state as get_ticket_state,
        transition as ticket_transition,
    )

    reg = FeatureRegistry(tmp_path)
    record = reg.write(FeaturePayload(
        title="alpha feature", description="d",
        stack_span=StackSpan.BACKEND, tier=TicketTier.V1, sources=["s"],
    ))
    _drive_to(
        tmp_path, record.slug,
        FeatureState.IN_DESIGN, FeatureState.DESIGNED,
        FeatureState.QUEUED, FeatureState.IN_PROGRESS,
        FeatureState.READY_FOR_REVIEW,
    )

    # Simulate M8's freshly-synthesized follow-up: review-source
    # ticket attributed to this feature, in QUEUED state.
    treg = TicketRegistry(tmp_path)
    follow_up = treg.write(TicketPayload(
        title="M8 follow-up — fix delete idempotence",
        owner="tweedledum",
        tier=TicketTier.V1,
        stack_span=StackSpan.BACKEND,
        estimate="tbd",
        description="From M8 review finding",
        sources=[record.slug, "m8-review-slug"],
        acceptance=["fix it"],
        source=TicketSource.REVIEW_SYNTHESIS,
    ))
    back_fill_state(
        tmp_path, follow_up.slug,
        TicketState.PENDING, notes="m8 synth",
    )
    ticket_transition(
        tmp_path, follow_up.slug,
        TicketState.QUEUED, by="m8", notes="m8 queue",
    )

    def failer(_root: Path) -> VerificationResult:
        return VerificationResult(
            check_name="fake_fail", ok=False, skipped=False,
            findings=(
                VerificationFinding(
                    title="pytest failed",
                    location="tests/test_x.py",
                    concern="x", request="y",
                    severity="block",
                ),
            ),
        )
    register_check("fake_fail", failer)

    runner = _FakeRunner(project_root=tmp_path)
    try:
        async for _e in _run_verify_meeting(
            _verify_meeting("fake_fail"), runner,
        ):
            pass
    finally:
        from wonderland.verification import _CHECK_REGISTRY
        _CHECK_REGISTRY.pop("fake_fail", None)

    # M8 follow-up should STILL be queued — verify must not have
    # auto-completed it as a ghost completion.
    assert get_ticket_state(tmp_path, follow_up.slug) == TicketState.QUEUED
    # Verify's own follow-up DID get synthesized.
    tickets = TicketRegistry(tmp_path).list_tickets()
    titles = [t.title for t in tickets]
    assert any("pytest failed" in t for t in titles)


@pytest.mark.asyncio
async def test_verify_meeting_emits_event_when_no_feature_to_attach(
    tmp_path: Path,
) -> None:
    """When the check fails but there's no feature to attach the
    review to (e.g. verify ran against a project with no features),
    still emit the BuildCheckEvent (informational) but skip
    synthesis. The signal isn't lost."""
    def failer(_root: Path) -> VerificationResult:
        return VerificationResult(
            check_name="fake_fail_no_feature", ok=False, skipped=False,
            findings=(
                VerificationFinding(
                    title="Build broken", concern="c", request="r",
                ),
            ),
        )
    register_check("fake_fail_no_feature", failer)

    runner = _FakeRunner(project_root=tmp_path)
    try:
        events = [e async for e in _run_verify_meeting(
            _verify_meeting("fake_fail_no_feature"), runner,
        )]
    finally:
        from wonderland.verification import _CHECK_REGISTRY
        _CHECK_REGISTRY.pop("fake_fail_no_feature", None)

    bc = next(e for e in events if isinstance(e, BuildCheckEvent))
    assert bc.findings_count == 1
    assert bc.review_slug is None
    assert TicketRegistry(tmp_path).list_tickets() == []
    end = next(e for e in events if isinstance(e, MeetingEndEvent))
    # Without a feature to attach to, no review on disk, no tickets.
    # Outcome reflects the check's failure regardless.
    assert end.outcome == "REQUEST_CHANGES"
