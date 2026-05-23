"""Tests for the milestone-framing prepend helpers (P15 + P16 T-v6).

These render the framing block that lands at the top of the
entry meeting's directive when ``run_workflow`` is invoked with a
milestone slug. Three things go into it:

  - Milestone name + goal + done_when
  - Seeded personas (anti-hallucination whitelist; P15)
  - Existing stories on disk (slug-stability guard; P16 T-v6)
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from wonderland import (
    RulingPayload,
    RulingRegistry,
    StoryPayload,
    StoryRegistry,
    StoryTier,
    TicketPayload,
    TicketRegistry,
)
from wonderland.ticket import TicketStackSpan, TicketTier
from wonderland.workflow import (
    _classify_milestone_shape,
    _format_existing_rulings_block,
    _format_existing_stories_block,
    _format_existing_tickets_block,
    _format_m1_lead_block,
    _format_seeded_personas_block,
    _MilestoneScope,
    _prepend_milestone_framing,
)


def _fake_runner(project_root: Path | None) -> SimpleNamespace:
    """Substitute for the real Runner — the framing helpers only
    read ``project_root``, so a duck-typed object is enough."""
    return SimpleNamespace(project_root=project_root)


def _scope(kind: str = "capability") -> _MilestoneScope:
    return _MilestoneScope(
        slug="m1-foundation",
        name="M1 — foundation",
        goal="Stand up the auth flow",
        done_when=("User can sign up", "User can log in"),
        consumes=frozenset({"user-signup", "user-login"}),
        kind=kind,
    )


# ---------- _format_existing_stories_block ----------


def test_existing_stories_block_empty_when_no_runner() -> None:
    assert _format_existing_stories_block(None) == ""


def test_existing_stories_block_empty_when_no_project_root() -> None:
    assert _format_existing_stories_block(_fake_runner(None)) == ""


def test_existing_stories_block_empty_when_no_stories_dir(
    tmp_path: Path,
) -> None:
    """A fresh project hasn't written any stories yet — the framing
    block should silently degrade to an empty string. Otherwise M1
    would see misleading "Stories already on disk:" with no entries."""
    runner = _fake_runner(tmp_path)
    assert _format_existing_stories_block(runner) == ""


def test_existing_stories_block_filters_by_active_milestone(
    tmp_path: Path,
) -> None:
    """T-ab34: when an active milestone scope is set, only list
    stories whose ``**Milestone:**`` field matches. obol-260522 M4
    surfaced this: Alice/Rabbit kept asking about M1-M2-M3 cross-
    milestone composition because this block listed every story in
    the project. Anti-duplicate framing has to stay scoped to what
    THIS run can actually duplicate."""
    import wonderland.workflow as wf

    reg = StoryRegistry(tmp_path)
    # Write a story for M4
    m4_record = reg.write(StoryPayload(
        title="Kohl reviews credit card payoff",
        persona="Kohl, AI researcher",
        situation="Month-end debt review.",
        need="As Kohl, I want to see my payoff progress.",
        acceptance=["payoff % visible"],
        tier=StoryTier.CORE,
        confusion_flags=["none"],
        milestone="m4-credit-card-debt-payoff-tracking",
    ))
    # Write a story for M3
    m3_record = reg.write(StoryPayload(
        title="Kohl sets a monthly budget",
        persona="Kohl, AI researcher",
        situation="Planning next month.",
        need="As Kohl, I want to set a budget.",
        acceptance=["budget saved"],
        tier=StoryTier.CORE,
        confusion_flags=["none"],
        milestone="m3-budgeting-and-monthly-summary",
    ))

    # With no active scope: both stories should appear
    out_no_scope = _format_existing_stories_block(_fake_runner(tmp_path))
    assert "Kohl reviews credit card payoff" in out_no_scope
    assert "Kohl sets a monthly budget" in out_no_scope
    assert "for this project" in out_no_scope

    # With M4 active scope: only M4 story should appear
    scope = _MilestoneScope(
        slug="m4-credit-card-debt-payoff-tracking",
        name="M4 — Credit Card Debt Payoff",
        goal="Track debt paydown",
        done_when=("Operator can mark debt",),
        consumes=frozenset(),
    )
    wf.set_active_milestone_scope(scope)
    try:
        out_m4_scope = _format_existing_stories_block(_fake_runner(tmp_path))
    finally:
        wf.set_active_milestone_scope(None)
    assert "Kohl reviews credit card payoff" in out_m4_scope
    assert "Kohl sets a monthly budget" not in out_m4_scope
    assert "for milestone ``m4-credit-card-debt-payoff-tracking``" in out_m4_scope


def test_existing_stories_block_lists_stories_with_slugs(
    tmp_path: Path,
) -> None:
    """The whole point of this block: when stories exist, render
    their slugs + titles + personas so M1 can spot near-duplicates
    BEFORE coining a fresh slug."""
    reg = StoryRegistry(tmp_path)
    reg.write(StoryPayload(
        title="User signs up with email",
        persona="Maya, 31, polyglot moderator",
        situation="She lands on the homepage and wants to claim a username.",
        need="As Maya, I want to sign up with email so that I can claim a homepage URL.",
        acceptance=["email + password validates", "redirect to dashboard"],
        tier=StoryTier.CORE,
        confusion_flags=["what if email is already in use?"],
    ))
    out = _format_existing_stories_block(_fake_runner(tmp_path))
    assert "Stories already on disk" in out
    assert "``user-signs-up-with-email``" in out
    assert "User signs up with email" in out
    # Persona snippet appears (truncated to one-line identifier).
    assert "Maya" in out


def test_existing_stories_block_lists_multiple_in_order(
    tmp_path: Path,
) -> None:
    reg = StoryRegistry(tmp_path)
    reg.write(StoryPayload(
        title="First story",
        persona="P1, dev",
        situation="S1.",
        need="As P1, I want X.",
        acceptance=["a1"],
        tier=StoryTier.CORE,
        confusion_flags=["c1"],
    ))
    reg.write(StoryPayload(
        title="Second story",
        persona="P2, user",
        situation="S2.",
        need="As P2, I want Y.",
        acceptance=["a2"],
        tier=StoryTier.CORE,
        confusion_flags=["c2"],
    ))
    out = _format_existing_stories_block(_fake_runner(tmp_path))
    # Both slugs should appear (story-001 + story-002).
    assert "``first-story``" in out
    assert "``second-story``" in out


# ---------- _prepend_milestone_framing integration ----------


def test_prepend_includes_existing_stories_block_when_present(
    tmp_path: Path,
) -> None:
    """End-to-end: the framing function pulls existing-stories
    into the directive prefix when a runner with stories on disk
    is supplied."""
    reg = StoryRegistry(tmp_path)
    reg.write(StoryPayload(
        title="Seed story",
        persona="P, dev",
        situation="S.",
        need="As P, I want X.",
        acceptance=["a"],
        tier=StoryTier.CORE,
        confusion_flags=["c"],
    ))
    runner = _fake_runner(tmp_path)
    result = _prepend_milestone_framing(
        directive="Original directive.",
        scope=_scope(),
        runner=runner,
    )
    assert "Stories already on disk" in result
    assert "``seed-story``" in result
    assert "Original directive." in result


def test_prepend_silently_skips_block_when_no_stories(
    tmp_path: Path,
) -> None:
    """Empty stories dir → no block in the framing (don't say "stories
    already on disk" when there aren't any — that's misleading)."""
    runner = _fake_runner(tmp_path)
    result = _prepend_milestone_framing(
        directive="Operator directive.",
        scope=_scope(),
        runner=runner,
    )
    assert "Stories already on disk" not in result
    # Other framing pieces still present (regression check).
    assert "M1 — foundation" in result
    assert "Operator directive." in result


def test_prepend_works_without_runner() -> None:
    """Callers can pass None for runner (pre-T-v6 contract). The
    framing falls back to "no existing context" cleanly — the
    operator's directive is still preserved."""
    result = _prepend_milestone_framing(
        directive="The work.",
        scope=_scope(),
        runner=None,
    )
    assert "Stories already on disk" not in result
    assert "Seeded personas" not in result  # no runner → no persona block
    assert "The work." in result


# ---------- _format_existing_tickets_block (validation2 follow-up) ----------


def _ticket_payload(title: str) -> TicketPayload:
    return TicketPayload(
        title=title,
        description="d",
        owner="tweedledee",
        tier=TicketTier.V1,
        stack_span=TicketStackSpan.BACKEND,
        estimate="1 day",
        acceptance=["a"],
        sources=["seed-feature"],
    )


def test_existing_tickets_block_empty_when_no_dir(tmp_path: Path) -> None:
    """No tickets directory yet — block silently degrades to empty."""
    assert _format_existing_tickets_block(_fake_runner(tmp_path)) == ""


def test_existing_tickets_block_lists_each_ticket(tmp_path: Path) -> None:
    """Mirror of the stories block: ``slug — title`` rows so Rabbit
    and Caterpillar can spot near-duplicates BEFORE re-emitting.
    The validation2 pilot had 21 tickets for 4 features because
    this block didn't exist — multiple schema-init + auth-endpoint
    near-duplicates all hashed differently."""
    reg = TicketRegistry(tmp_path)
    reg.write(_ticket_payload("Initialize SQLite schema for users + sessions"))
    reg.write(_ticket_payload("Authentication endpoints: register + login"))
    out = _format_existing_tickets_block(_fake_runner(tmp_path))
    assert "Tickets already on disk" in out
    assert "``initialize-sqlite-schema-for-users-sessions``" in out
    assert "``authentication-endpoints-register-login``" in out


# ---------- _format_existing_rulings_block ----------


def _ruling_payload(title: str) -> RulingPayload:
    from wonderland.ruling import RulingDomain, RulingSeverity

    return RulingPayload(
        title=title,
        severity=RulingSeverity.HIGH,
        domain=RulingDomain.CRYPTOGRAPHY,
        citation="OWASP Top 10 A02:2021 Cryptographic Failures",
        finding="...",
        required_remediation="...",
        acceptance_criteria=["a"],
    )


def test_existing_rulings_block_empty_when_no_dir(tmp_path: Path) -> None:
    assert _format_existing_rulings_block(_fake_runner(tmp_path)) == ""


def test_existing_rulings_block_lists_each_ruling(tmp_path: Path) -> None:
    """Queen of Hearts re-emitted near-duplicate rulings in
    validation2 (password hashing ruled twice, user isolation
    ruled twice, admin bootstrap audit ruled twice). The block
    lets her see what's already adjudicated."""
    reg = RulingRegistry(tmp_path)
    reg.write(_ruling_payload("Password storage must use bcrypt or argon2"))
    reg.write(_ruling_payload("User data isolation enforced at storage layer"))
    out = _format_existing_rulings_block(_fake_runner(tmp_path))
    assert "Rulings already on disk" in out
    assert "``password-storage-must-use-bcrypt-or-argon2``" in out
    assert "``user-data-isolation-enforced-at-storage-layer``" in out


def test_prepend_includes_tickets_and_rulings_when_present(
    tmp_path: Path,
) -> None:
    """End-to-end: tickets + rulings join stories in the framing
    prepend when they exist on disk."""
    TicketRegistry(tmp_path).write(_ticket_payload("Ticket X"))
    RulingRegistry(tmp_path).write(_ruling_payload("Ruling Y"))
    result = _prepend_milestone_framing(
        directive="Original directive.",
        scope=_scope(),
        runner=_fake_runner(tmp_path),
    )
    assert "Tickets already on disk" in result
    assert "``ticket-x``" in result
    assert "Rulings already on disk" in result
    assert "``ruling-y``" in result
    assert "Original directive." in result


# ---------- _classify_milestone_shape (validation2 deadlock fix) ----------


def _write_requirement(
    tmp_path: Path, slug: str, kind: str
) -> None:
    """Helper: drop a minimal requirement markdown on disk so the
    classifier can read its kind."""
    req_dir = tmp_path / ".wonderland" / "requirements"
    req_dir.mkdir(parents=True, exist_ok=True)
    (req_dir / f"requirement-001-{slug}.md").write_text(
        f"## Requirement 001: {slug}\n\n"
        f"**Slug:** {slug}\n"
        f"**Kind:** {kind}\n\n"
        f"Body.\n",
        encoding="utf-8",
    )


def test_classify_foundation_when_consumes_are_infrastructure(
    tmp_path: Path,
) -> None:
    """A milestone whose consumes are all constraint/integration/scope
    kinds is foundation-shape. validation2's M0 is the canonical
    example — auth + schema + sync + LLM provider abstraction.

    T-ab50: pass kind="" to exercise the heuristic path (explicit
    kind would short-circuit). Production paths set kind from the
    milestone file's **Kind:** line; tests targeting the heuristic
    specifically opt out via the empty-kind sentinel."""
    _write_requirement(tmp_path, "stack-react-sqlite", "constraint")
    scope = _MilestoneScope(
        slug="m0", name="M0 foundation",
        goal="Stand up auth + schema",
        done_when=("auth works", "schema isolates users"),
        consumes=frozenset({"stack-react-sqlite"}),
        kind="",
    )
    assert (
        _classify_milestone_shape(scope, _fake_runner(tmp_path))
        == "foundation"
    )


def test_classify_capability_when_consumes_include_situation(
    tmp_path: Path,
) -> None:
    """A milestone with at least one situation/persona consume is
    capability-shape — Alice's natural lane.

    T-ab50: kind="" opts into the heuristic path."""
    _write_requirement(tmp_path, "marcus-logs-session", "situation")
    scope = _MilestoneScope(
        slug="m1", name="M1 session log",
        goal="Marcus logs a workout",
        done_when=("logs persist",),
        consumes=frozenset({"marcus-logs-session"}),
        kind="",
    )
    assert (
        _classify_milestone_shape(scope, _fake_runner(tmp_path))
        == "capability"
    )


def test_classify_mixed_when_both_kinds_present(tmp_path: Path) -> None:
    """Mixed milestones (some situation, some constraint) default
    to Alice-led; Caterpillar still ships foundation stories per
    his constitution. No lead-assignment override needed.

    T-ab50: kind="" opts into the heuristic path."""
    _write_requirement(tmp_path, "marcus-logs-session", "situation")
    _write_requirement(tmp_path, "stack-react-sqlite", "constraint")
    scope = _MilestoneScope(
        slug="m2", name="M2 mixed",
        goal="Marcus + schema",
        done_when=("both work",),
        consumes=frozenset({"marcus-logs-session", "stack-react-sqlite"}),
        kind="",
    )
    assert (
        _classify_milestone_shape(scope, _fake_runner(tmp_path))
        == "mixed"
    )


def test_classify_returns_mixed_when_no_runner() -> None:
    """No runner = no project_root = can't classify. Mixed is the
    safe default (preserves Alice-led behavior for the runs where
    classification can't fire).

    T-ab50: kind="" opts into the heuristic path; without runner
    we fall through to the mixed default."""
    scope = _scope(kind="")
    assert _classify_milestone_shape(scope, None) == "mixed"


def test_t_ab50_explicit_kind_wins_over_heuristic(
    tmp_path: Path,
) -> None:
    """T-ab50: when the milestone's Kind: field is explicit
    (capability or foundation), it short-circuits the consumes-based
    heuristic. obol-260522-1 M6 surfaced the contradiction:
    kind=capability (operator's explicit choice for the upload flow)
    + consumes=[constraint requirements] → heuristic said foundation
    → "M1 LEAD: Caterpillar" framing → alice (only one in the room
    per T-ab6's kind-driven filter) read 'I'm not the lead' and
    passed. Both pieces of substrate logic must read the same
    source of truth — the explicit Kind field."""
    # Infra-only consumes; without T-ab50 heuristic would say foundation
    _write_requirement(tmp_path, "stack-react-sqlite", "constraint")

    # Explicit capability wins even though consumes look foundation-shape
    cap_scope = _MilestoneScope(
        slug="m6", name="M6 csv-and-ofx-import",
        goal="upload + parse + dedup",
        done_when=("upload works",),
        consumes=frozenset({"stack-react-sqlite"}),
        kind="capability",
    )
    assert (
        _classify_milestone_shape(cap_scope, _fake_runner(tmp_path))
        == "capability"
    )

    # Explicit foundation also wins (back-compat for the normal case)
    found_scope = _MilestoneScope(
        slug="m1", name="M1 data layer",
        goal="schema bootstrap",
        done_when=("tables exist",),
        consumes=frozenset({"stack-react-sqlite"}),
        kind="foundation",
    )
    assert (
        _classify_milestone_shape(found_scope, _fake_runner(tmp_path))
        == "foundation"
    )


# ---------- _format_m1_lead_block ----------


def test_m1_lead_block_empty_for_capability_shape(tmp_path: Path) -> None:
    """Capability-shape milestones use the default Alice-led flow;
    no explicit lead assignment needed."""
    _write_requirement(tmp_path, "marcus-logs-session", "situation")
    scope = _MilestoneScope(
        slug="m1", name="M1",
        goal="g", done_when=("d",),
        consumes=frozenset({"marcus-logs-session"}),
    )
    assert _format_m1_lead_block(scope, _fake_runner(tmp_path)) == ""


def test_m1_lead_block_names_caterpillar_for_foundation(
    tmp_path: Path,
) -> None:
    """Foundation-shape milestones get an explicit "Caterpillar
    leads, Alice silences" block at the top of the framing. This
    is the missing piece that broke validation2's M1 deadlock —
    constitution alone wasn't strong enough to make Caterpillar
    take the lane."""
    _write_requirement(tmp_path, "stack-react-sqlite", "constraint")
    # T-ab50: kind="" opts into the heuristic path for this test.
    scope = _MilestoneScope(
        slug="m0", name="M0",
        goal="g", done_when=("d",),
        consumes=frozenset({"stack-react-sqlite"}),
        kind="",
    )
    block = _format_m1_lead_block(scope, _fake_runner(tmp_path))
    assert "M1 LEAD: Caterpillar" in block
    assert "first move in M1 must be ``decision: story``" in block
    assert "default in M1 here is ``silence``" in block
    # Names the deadlock pattern this prevents so the agents
    # recognize the failure mode they're being steered away from.
    assert "deadlock" in block.lower()


def test_prepend_injects_lead_block_at_top_for_foundation(
    tmp_path: Path,
) -> None:
    """The lead block must appear BEFORE the milestone scope header
    so it's the first thing M1 agents read. Order matters: the
    constitutional guidance was being out-weighted by the agents'
    default scoping-question instinct."""
    _write_requirement(tmp_path, "stack-react-sqlite", "constraint")
    # T-ab50: kind="" opts into the heuristic path for this test.
    scope = _MilestoneScope(
        slug="m0", name="M0 foundation",
        goal="Stand up auth + schema",
        done_when=("auth works",),
        consumes=frozenset({"stack-react-sqlite"}),
        kind="",
    )
    result = _prepend_milestone_framing(
        directive="The work.",
        scope=scope,
        runner=_fake_runner(tmp_path),
    )
    lead_pos = result.find("M1 LEAD: Caterpillar")
    scope_pos = result.find("Milestone scope:")
    assert lead_pos >= 0, "lead block missing from framing"
    assert scope_pos >= 0, "scope header missing from framing"
    assert lead_pos < scope_pos, (
        "lead block must appear BEFORE scope header — order is "
        "load-bearing for agent attention"
    )
