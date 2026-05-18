"""Tests for convergence-failure detection (T-a3).

Verifies the detector correctly identifies oscillation patterns
(same fingerprint recurring across consecutive review passes)
vs. progressive deepening (different findings each pass).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from wonderland.convergence import (
    DEFAULT_WINDOW,
    SPEC_AMBIGUITY_DIRNAME,
    FindingFingerprint,
    compute_finding_fingerprint,
    detect_convergence_failure,
    fingerprints_from_findings,
    fingerprints_from_review_text,
    record_spec_ambiguity,
)


def _write_review(
    project_root: Path,
    slug: str,
    findings: list[dict],
    *,
    feature_slug: str,
    sortable_id: str = "01KRWA00",
) -> Path:
    """Write a minimal review markdown shaped like the substrate's
    render. ``sortable_id`` controls filename ordering."""
    reviews_dir = project_root / ".wonderland" / "reviews"
    reviews_dir.mkdir(parents=True, exist_ok=True)
    findings_md = ""
    for f in findings:
        findings_md += (
            f"#### {f['severity']}: {f.get('title', 'untitled')}\n"
            f"**Location:** {f['location']}\n\n"
            f"**Quote:**\n\n```\n{f.get('quote', 'x')}\n```\n\n"
            f"**Read:** {f.get('read', 'x')}\n"
            f"**Concern:** {f['concern']}\n"
            f"**Request:** {f.get('request', 'x')}\n\n"
        )
    body = (
        f"## Review 001: {slug}\n\n"
        f"**Feature:** {feature_slug}\n"  # so the heuristic finds it
        f"**Files reviewed:** src/x.py\n\n"
        f"### Findings\n\n{findings_md}"
    )
    path = reviews_dir / f"review-{sortable_id}-{slug}.md"
    path.write_text(body, encoding="utf-8")
    return path


# ---------- fingerprint computation ----------


def test_fingerprint_strips_line_numbers() -> None:
    f1 = compute_finding_fingerprint({
        "location": "src/foo.py:123-456",
        "concern": "Foo bar baz",
    })
    f2 = compute_finding_fingerprint({
        "location": "src/foo.py:200-300",
        "concern": "Foo bar baz",
    })
    assert f1 == f2  # Same file, same concern → same fingerprint


def test_fingerprint_normalizes_concern_whitespace_case() -> None:
    f1 = compute_finding_fingerprint({
        "location": "src/foo.py",
        "concern": "Foo  BAR\n\tbaz",
    })
    f2 = compute_finding_fingerprint({
        "location": "src/foo.py",
        "concern": "foo bar baz",
    })
    assert f1 == f2


def test_fingerprints_from_findings_only_blocks_change_required() -> None:
    findings = [
        {"severity": "block", "location": "a.py", "concern": "c1"},
        {"severity": "change-required", "location": "b.py", "concern": "c2"},
        {"severity": "suggestion", "location": "c.py", "concern": "c3"},
        {"severity": "note", "location": "d.py", "concern": "c4"},
    ]
    fps = fingerprints_from_findings(findings)
    assert len(fps) == 2
    locations = {fp.file_location for fp in fps}
    assert locations == {"a.py", "b.py"}


# ---------- parsing from review markdown ----------


def test_fingerprints_from_review_text(tmp_path: Path) -> None:
    path = _write_review(tmp_path, "my-review", [
        {
            "severity": "change-required",
            "location": "src/foo.py:10-20",
            "concern": "Tag filter does full table scan",
        },
        {
            "severity": "suggestion",  # should be excluded
            "location": "src/foo.py:30",
            "concern": "Minor nit",
        },
    ], feature_slug="my-feature")
    text = path.read_text()
    fps = fingerprints_from_review_text(text)
    assert len(fps) == 1
    fp = next(iter(fps))
    assert fp.file_location == "src/foo.py"
    assert "tag filter does full table scan" in fp.concern_key


# ---------- detection ----------


def test_no_detection_with_insufficient_history(tmp_path: Path) -> None:
    """Window=3 default: need at least 2 prior reviews for detection."""
    _write_review(tmp_path, "r1", [
        {"severity": "block", "location": "x.py:1", "concern": "same"},
    ], feature_slug="feat-x", sortable_id="01KRWA00")
    # Only 1 prior review on disk + 1 current = not enough
    result = detect_convergence_failure(
        tmp_path,
        feature_slug="feat-x",
        current_findings=[
            {"severity": "block", "location": "x.py:2", "concern": "same"},
        ],
    )
    assert result is None


def test_detects_recurring_finding_across_three_reviews(
    tmp_path: Path,
) -> None:
    """The mvp-demo F1 pattern: same finding (location + concern) in
    every consecutive review."""
    for i, sortable in enumerate(["01KRWA00", "01KRWA01"]):
        _write_review(
            tmp_path, f"r{i}",
            [{
                "severity": "block",
                "location": f"src/foo.py:{100 + i * 50}-{150 + i * 50}",
                "concern": "DELETE endpoint contradicts offline-first requirement",
            }],
            feature_slug="feat-x",
            sortable_id=sortable,
        )
    # Current review has same finding shape — should trip detection
    result = detect_convergence_failure(
        tmp_path,
        feature_slug="feat-x",
        current_findings=[{
            "severity": "block",
            "location": "src/foo.py:200-300",
            "concern": "DELETE endpoint contradicts offline-first requirement",
        }],
    )
    assert result is not None
    assert result.feature_slug == "feat-x"
    assert result.window == DEFAULT_WINDOW
    assert len(result.recurring_fingerprints) == 1
    fp = result.recurring_fingerprints[0]
    assert fp.file_location == "src/foo.py"


def test_progressive_deepening_does_not_trip_detection(
    tmp_path: Path,
) -> None:
    """F2 mvp-demo pattern: each review surfaces a DIFFERENT finding
    (cosmetic → architectural → environmental). Should NOT detect
    convergence failure."""
    findings_per_review = [
        [{
            "severity": "change-required",
            "location": "src/foo.py:5",
            "concern": "Unused import",
        }],
        [{
            "severity": "change-required",
            "location": "src/bar.py:20",
            "concern": "Tag normalization logic duplicated",
        }],
    ]
    for i, (sortable, findings) in enumerate(zip(
        ["01KRWA00", "01KRWA01"], findings_per_review,
    )):
        _write_review(
            tmp_path, f"r{i}", findings,
            feature_slug="feat-y",
            sortable_id=sortable,
        )
    # Current review has a DIFFERENT finding (deeper layer)
    result = detect_convergence_failure(
        tmp_path,
        feature_slug="feat-y",
        current_findings=[{
            "severity": "block",
            "location": "tests/conftest.py:11",
            "concern": "Test environment missing dependencies",
        }],
    )
    assert result is None


def test_detection_ignores_reviews_not_attributed_to_feature(
    tmp_path: Path,
) -> None:
    """Reviews for OTHER features shouldn't pollute the detection
    for this feature."""
    # 2 prior reviews on a DIFFERENT feature (would falsely trip
    # detection if we didn't filter by feature_slug)
    for i, sortable in enumerate(["01KRWA00", "01KRWA01"]):
        _write_review(
            tmp_path, f"r{i}",
            [{
                "severity": "block",
                "location": "src/foo.py:10",
                "concern": "Same recurring issue",
            }],
            feature_slug="feat-other",
            sortable_id=sortable,
        )
    # Current review for feat-x has overlapping fingerprint but the
    # prior reviews don't mention feat-x → no detection
    result = detect_convergence_failure(
        tmp_path,
        feature_slug="feat-x",
        current_findings=[{
            "severity": "block",
            "location": "src/foo.py:10",
            "concern": "Same recurring issue",
        }],
    )
    assert result is None


def test_detection_extracts_cited_contract_artifacts(
    tmp_path: Path,
) -> None:
    """When the recurring finding's concern cites a contract note
    or ADR, the failure object should include it for operator
    attention."""
    for sortable in ["01KRWA00", "01KRWA01"]:
        _write_review(
            tmp_path, f"r-{sortable}",
            [{
                "severity": "block",
                "location": "src/foo.py:10",
                "concern": (
                    "DELETE endpoint returns 409, but Contract Note 001 "
                    "says it should return 204 idempotent. ADR-001 "
                    "concurs."
                ),
            }],
            feature_slug="feat-x",
            sortable_id=sortable,
        )
    result = detect_convergence_failure(
        tmp_path,
        feature_slug="feat-x",
        current_findings=[{
            "severity": "block",
            "location": "src/foo.py:50",
            "concern": (
                "DELETE endpoint returns 409, but Contract Note 001 "
                "says it should return 204 idempotent. ADR-001 "
                "concurs."
            ),
        }],
    )
    assert result is not None
    cited = list(result.cited_contract_artifacts)
    # Should pick up both citations (normalized)
    assert any("contract note" in c.lower() and "001" in c for c in cited)
    assert any("adr" in c.lower() and "001" in c for c in cited)


def test_record_spec_ambiguity_writes_to_disk(tmp_path: Path) -> None:
    """The failure artifact gets persisted for operator + dashboard
    consumption."""
    from wonderland.convergence import ConvergenceFailure
    failure = ConvergenceFailure(
        feature_slug="feat-x",
        window=3,
        recurring_fingerprints=(
            FindingFingerprint(file_location="src/foo.py", concern_key="x"),
        ),
        cited_contract_artifacts=("Contract Note 001",),
    )
    out_path = record_spec_ambiguity(tmp_path, failure)
    assert out_path.exists()
    assert out_path.parent.name == SPEC_AMBIGUITY_DIRNAME
    body = out_path.read_text()
    assert "feat-x" in body
    assert "Contract Note 001" in body
    assert "Convergence failure" in body
