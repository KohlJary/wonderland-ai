"""Tests for the Review writer + registry."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from wonderland import (
    FindingKind,
    ReviewFinding,
    ReviewPayload,
    ReviewRegistry,
    ReviewSeverity,
    ReviewVerdict,
    render_review,
)

# ---------- helpers ----------


def _finding(**overrides) -> ReviewFinding:
    base = {
        "severity": ReviewSeverity.CHANGE_REQUIRED,
        "title": "validate_input also writes to the database",
        "location": "handlers/payments.py:42",
        "quote": "if not _ok(req):\n    log_attempt(req)\n    return False",
        "read": (
            "Despite the name, this function logs an attempt to the database in the rejection path."
        ),
        "concern": (
            "Future callers will rely on the validation-only contract the name "
            "implies and be surprised by the side effect on retry."
        ),
        "request": (
            "Rename to validate_and_log_input or split the logging into a "
            "separate step the caller invokes explicitly."
        ),
    }
    return ReviewFinding(**(base | overrides))


def _payload(**overrides) -> ReviewPayload:
    base = {
        "title": "Payment refund handler",
        "target_files": ["src/payments/refund.py"],
        "verdict": ReviewVerdict.REQUEST_CHANGES,
        "findings": [_finding()],
        "approvals": [],
        "cross_domain_references": [],
    }
    return ReviewPayload(**(base | overrides))


# ---------- ReviewFinding validation ----------


@pytest.mark.parametrize(
    "field",
    ["title", "location", "quote", "read", "concern", "request"],
)
def test_finding_requires_non_empty_field(field: str) -> None:
    with pytest.raises(ValidationError):
        _finding(**{field: ""})


@pytest.mark.parametrize("severity", list(ReviewSeverity))
def test_finding_accepts_each_severity(severity: ReviewSeverity) -> None:
    finding = _finding(severity=severity)
    assert finding.severity is severity


def test_finding_rejects_unknown_severity() -> None:
    with pytest.raises(ValidationError):
        _finding(severity="critical")  # type: ignore[arg-type]


# ---------- ReviewPayload validation: structural ----------


def test_payload_requires_non_empty_title() -> None:
    with pytest.raises(ValidationError):
        _payload(title="")


def test_payload_requires_at_least_one_target_file() -> None:
    """Working-tree-as-implementation-artifact: a review must name at
    least one file it covers. Empty target_files is incoherent — what
    did you review?"""
    with pytest.raises(ValidationError):
        _payload(target_files=[])


def test_payload_rejects_unknown_verdict() -> None:
    with pytest.raises(ValidationError):
        _payload(verdict="lgtm")  # type: ignore[arg-type]


def test_payload_strips_whitespace_only_approvals() -> None:
    payload = _payload(
        verdict=ReviewVerdict.ACCEPT,
        approvals=["good naming throughout", "  ", ""],
    )
    assert payload.approvals == ["good naming throughout"]


def test_payload_strips_whitespace_only_cross_domain_refs() -> None:
    payload = _payload(cross_domain_references=["flag for Cat", "", "   "])
    assert payload.cross_domain_references == ["flag for Cat"]


# ---------- ReviewPayload validation: verdict ↔ findings ↔ approvals ----------


def test_accept_requires_at_least_one_approval() -> None:
    """The grin equivalent — Caterpillar approval is not given cheaply."""
    with pytest.raises(ValidationError, match="approval is not given cheaply"):
        _payload(verdict=ReviewVerdict.ACCEPT, findings=[], approvals=[])


def test_accept_with_approvals_is_valid_even_without_findings() -> None:
    payload = _payload(
        verdict=ReviewVerdict.ACCEPT,
        findings=[],
        approvals=["error path on line 47 propagates with context the caller can use"],
    )
    assert payload.verdict is ReviewVerdict.ACCEPT


def test_accept_may_carry_low_severity_findings() -> None:
    payload = _payload(
        verdict=ReviewVerdict.ACCEPT,
        findings=[_finding(severity=ReviewSeverity.NOTE)],
        approvals=["clean separation between the two handlers"],
    )
    assert payload.findings[0].severity is ReviewSeverity.NOTE


def test_request_changes_requires_at_least_one_finding() -> None:
    with pytest.raises(ValidationError, match="something specific to act on"):
        _payload(verdict=ReviewVerdict.REQUEST_CHANGES, findings=[], approvals=[])


def test_block_verdict_requires_a_block_severity_finding() -> None:
    """A 'block' verdict whose findings are all suggestions is incoherent."""
    with pytest.raises(ValidationError, match="severity must agree"):
        _payload(
            verdict=ReviewVerdict.BLOCK,
            findings=[_finding(severity=ReviewSeverity.SUGGESTION)],
        )


def test_block_verdict_with_block_finding_is_valid() -> None:
    payload = _payload(
        verdict=ReviewVerdict.BLOCK,
        findings=[
            _finding(severity=ReviewSeverity.BLOCK, title="auth bypass on retry"),
            _finding(severity=ReviewSeverity.SUGGESTION),
        ],
    )
    assert payload.verdict is ReviewVerdict.BLOCK


# ---------- render_review ----------


def test_render_includes_required_sections() -> None:
    out = render_review(7, _payload())
    assert "## Review 007: Payment refund handler" in out
    assert "**Files reviewed:** src/payments/refund.py" in out
    assert "**Verdict:** request-changes" in out
    assert "### Findings" in out
    assert "#### change-required: validate_input also writes to the database" in out
    assert "**Location:** handlers/payments.py:42" in out
    assert "**Quote:**" in out
    assert "if not _ok(req):" in out
    assert "**Read:**" in out
    assert "**Concern:**" in out
    assert "**Request:**" in out


def test_render_includes_approvals_when_present() -> None:
    out = render_review(
        1,
        _payload(
            verdict=ReviewVerdict.ACCEPT,
            findings=[],
            approvals=["clean error path", "tests cover both branches"],
        ),
    )
    assert "### Approvals" in out
    assert "- clean error path" in out
    assert "- tests cover both branches" in out


def test_render_omits_approvals_when_empty() -> None:
    out = render_review(1, _payload())  # request-changes default; no approvals
    assert "### Approvals" not in out


def test_render_includes_cross_domain_refs_when_present() -> None:
    out = render_review(
        1,
        _payload(
            cross_domain_references=[
                "implies architectural question about retry semantics — Cat",
            ],
        ),
    )
    assert "### Cross-domain references" in out
    assert "- implies architectural question" in out


def test_render_omits_cross_domain_refs_when_empty() -> None:
    out = render_review(1, _payload())
    assert "### Cross-domain references" not in out


def test_render_three_digit_padding() -> None:
    assert "Review 003:" in render_review(3, _payload())


# ---------- FindingKind (meta-vs-bug primitive) ----------


def test_finding_kind_defaults_to_bug() -> None:
    """Default kind preserves pre-existing behavior — findings emitted
    without an explicit kind are treated as bug reports, same as
    before the primitive was added."""
    f = _finding()
    assert f.kind is FindingKind.BUG


@pytest.mark.parametrize("kind", list(FindingKind))
def test_finding_accepts_each_kind(kind: FindingKind) -> None:
    f = _finding(kind=kind)
    assert f.kind is kind


def test_finding_rejects_unknown_kind() -> None:
    with pytest.raises(ValidationError):
        _finding(kind="opinion")  # type: ignore[arg-type]


def test_render_omits_kind_when_bug_default() -> None:
    """Bug is the default and the most common — rendering it on every
    finding is noise. Surfacing the kind only when non-bug is the
    rule that keeps reviews readable."""
    out = render_review(1, _payload())  # default kind=bug on all findings
    assert "**Kind:**" not in out


def test_render_surfaces_kind_when_non_default() -> None:
    out = render_review(
        1,
        _payload(
            findings=[
                _finding(kind=FindingKind.META),
            ],
        ),
    )
    assert "**Kind:** meta" in out


@pytest.mark.parametrize(
    "kind",
    [FindingKind.META, FindingKind.CONVENTION, FindingKind.NIT],
)
def test_render_surfaces_each_non_bug_kind(kind: FindingKind) -> None:
    out = render_review(1, _payload(findings=[_finding(kind=kind)]))
    assert f"**Kind:** {kind.value}" in out


# ---------- Synthesis gate: kind-based ticket spawning ----------


def test_synthesis_skips_meta_kind_findings() -> None:
    """The load-bearing primitive: meta-kind findings record in the
    review artifact but DO NOT spawn implementation tickets,
    regardless of severity. This is the substrate gate that closes
    the recursive test-quality cycle analysis 033 §5.1 documented."""
    from wonderland.workflow import _synthesize_followup_ticket_from_finding

    finding = _finding(
        severity=ReviewSeverity.CHANGE_REQUIRED,
        kind=FindingKind.META,
    ).model_dump(mode="json")
    result = _synthesize_followup_ticket_from_finding(
        finding,
        parent_feature_slug="some-feature",
        review_slug="some-review",
    )
    assert result is None, (
        "meta-kind finding should not spawn a ticket — that's the whole point"
    )


def test_synthesis_skips_convention_kind_findings() -> None:
    from wonderland.workflow import _synthesize_followup_ticket_from_finding

    finding = _finding(
        severity=ReviewSeverity.CHANGE_REQUIRED,
        kind=FindingKind.CONVENTION,
    ).model_dump(mode="json")
    result = _synthesize_followup_ticket_from_finding(
        finding,
        parent_feature_slug="some-feature",
        review_slug="some-review",
    )
    assert result is None


def test_synthesis_skips_nit_kind_findings() -> None:
    from wonderland.workflow import _synthesize_followup_ticket_from_finding

    finding = _finding(
        severity=ReviewSeverity.CHANGE_REQUIRED,
        kind=FindingKind.NIT,
    ).model_dump(mode="json")
    result = _synthesize_followup_ticket_from_finding(
        finding,
        parent_feature_slug="some-feature",
        review_slug="some-review",
    )
    assert result is None


def test_synthesis_spawns_bug_kind_findings() -> None:
    """Default behavior preserved: bug-kind findings at ticketable
    severity DO spawn implementation tickets."""
    from wonderland.workflow import _synthesize_followup_ticket_from_finding

    finding = _finding(
        severity=ReviewSeverity.CHANGE_REQUIRED,
        kind=FindingKind.BUG,
    ).model_dump(mode="json")
    result = _synthesize_followup_ticket_from_finding(
        finding,
        parent_feature_slug="some-feature",
        review_slug="some-review",
    )
    assert result is not None
    assert result.title == "validate_input also writes to the database"


def test_synthesis_treats_missing_kind_as_bug_backcompat() -> None:
    """Findings emitted before this primitive shipped don't include
    a kind field; the synthesis path must treat them as bug-kind so
    pre-existing behavior is preserved."""
    from wonderland.workflow import _synthesize_followup_ticket_from_finding

    finding = _finding(severity=ReviewSeverity.CHANGE_REQUIRED).model_dump(mode="json")
    # Simulate a pre-primitive finding by deleting the kind field
    finding.pop("kind", None)
    result = _synthesize_followup_ticket_from_finding(
        finding,
        parent_feature_slug="some-feature",
        review_slug="some-review",
    )
    assert result is not None, (
        "missing kind should default to bug for back-compat"
    )


# ---------- ReviewRegistry — empty state ----------


def test_empty_registry_state(tmp_path: Path) -> None:
    registry = ReviewRegistry(tmp_path)
    assert registry.list_reviews() == []
    assert registry.next_number() == 1
    assert registry.find_by_slug("anything") is None
    assert registry.find_by_number(1) is None


def test_path_under_dot_wonderland_reviews(tmp_path: Path) -> None:
    registry = ReviewRegistry(tmp_path)
    assert registry.path == tmp_path / ".wonderland" / "reviews"


# ---------- ReviewRegistry — write ----------


def test_write_creates_file_at_expected_path(tmp_path: Path) -> None:
    registry = ReviewRegistry(tmp_path)
    record = registry.write(_payload())
    assert record.number == 1
    assert record.slug == "payment-refund-handler"
    assert record.path.is_file()
    assert record.verdict is ReviewVerdict.REQUEST_CHANGES
    assert record.target_files == ("src/payments/refund.py",)


def test_write_creates_parent_directory(tmp_path: Path) -> None:
    registry = ReviewRegistry(tmp_path)
    registry.write(_payload())
    assert registry.path.is_dir()


def test_write_accepts_dict_payload(tmp_path: Path) -> None:
    registry = ReviewRegistry(tmp_path)
    record = registry.write(
        {
            "title": "Auth middleware refactor",
            "target_files": ["src/auth/middleware.py"],
            "verdict": "accept",
            "findings": [],
            "approvals": ["the new exception type carries actionable context"],
            "cross_domain_references": [],
        }
    )
    assert record.verdict is ReviewVerdict.ACCEPT


def test_write_rejects_payload_with_invalid_verdict_consistency(tmp_path: Path) -> None:
    registry = ReviewRegistry(tmp_path)
    with pytest.raises(ValidationError):
        registry.write(
            {
                "title": "X",
                "target_files": ["src/x.py"],
                "verdict": "accept",
                "findings": [],
                "approvals": [],  # missing — should fail
            }
        )


def test_write_auto_increments(tmp_path: Path) -> None:
    registry = ReviewRegistry(tmp_path)
    a = registry.write(_payload(title="A"))
    b = registry.write(_payload(title="B"))
    assert (a.number, b.number) == (1, 2)


def test_written_file_round_trips_through_render(tmp_path: Path) -> None:
    registry = ReviewRegistry(tmp_path)
    payload = _payload()
    record = registry.write(payload)
    assert record.read() == render_review(1, payload)


# ---------- ReviewRegistry — queries ----------


def test_list_in_number_order(tmp_path: Path) -> None:
    registry = ReviewRegistry(tmp_path)
    for title in ("Third", "First", "Second"):
        registry.write(_payload(title=title))
    listing = registry.list_reviews()
    assert [r.number for r in listing] == [1, 2, 3]
    assert [r.title for r in listing] == ["Third", "First", "Second"]


def test_find_by_slug(tmp_path: Path) -> None:
    registry = ReviewRegistry(tmp_path)
    registry.write(_payload(title="Auth middleware"))
    found = registry.find_by_slug("auth-middleware")
    assert found is not None
    assert found.verdict is ReviewVerdict.REQUEST_CHANGES


def test_find_by_number(tmp_path: Path) -> None:
    registry = ReviewRegistry(tmp_path)
    registry.write(_payload(title="A"))
    registry.write(_payload(title="B"))
    found = registry.find_by_number(2)
    assert found is not None
    assert found.title == "B"


def test_recovers_verdict_and_target_from_disk(tmp_path: Path) -> None:
    registry = ReviewRegistry(tmp_path)
    registry.write(
        _payload(
            title="Acceptable change",
            verdict=ReviewVerdict.ACCEPT,
            findings=[],
            approvals=["substantive note about the new error handling"],
            target_files=["src/auth/handlers.py", "src/auth/types.py"],
        )
    )
    fresh = ReviewRegistry(tmp_path)
    listing = fresh.list_reviews()
    assert listing[0].verdict is ReviewVerdict.ACCEPT
    assert listing[0].target_files == ("src/auth/handlers.py", "src/auth/types.py")


def test_skips_non_review_files(tmp_path: Path) -> None:
    registry = ReviewRegistry(tmp_path)
    registry.write(_payload(title="A"))
    (registry.path / "README.md").write_text("not a review")
    (registry.path / "review-malformed.md").write_text("also not")
    assert len(registry.list_reviews()) == 1
