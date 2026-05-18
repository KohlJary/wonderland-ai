"""Convergence-failure detection — T-a3.

When the same finding-cluster recurs across N consecutive review
passes on the same feature, the substrate emits a ``spec_ambiguity``
signal and pauses the implementation loop pending operator
disambiguation. Stops cost-burn on convergence failures.

Mvp-demo M1 F1 surfaced the failure mode: same 2 findings (DELETE
shape + tag-validation error shape) recurred across 5 consecutive
review passes (~$11 burned) because Contract Note 001 + ADR-001
left the correct shape under-specified. The implementers oscillated
between valid interpretations; Caterpillar rejected whichever was
current; repeat. No substrate-level signal told the operator
"this isn't a code bug, it's a spec ambiguity."

Detection heuristic: compute a fingerprint per finding using
``(file_location_without_line_numbers, first_60_chars_of_concern)``.
If the same fingerprint appears in ≥N consecutive reviews for the
same feature (default N=3), flag as convergence failure. The flag
gets persisted to disk + surfaced to the operator.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from wonderland.artifact_guid import new_artifact_guid, short_guid

SPEC_AMBIGUITY_DIRNAME = "spec-ambiguity"
DEFAULT_WINDOW = 3


@dataclass(frozen=True)
class FindingFingerprint:
    """Comparable fingerprint of a review finding — strips line
    numbers from location so 'src/foo.py:147-184' and 'src/foo.py:189-195'
    compare equal (the finding is on the same file even if the line
    range shifted between implementation attempts)."""

    file_location: str
    concern_key: str

    def __str__(self) -> str:
        return f"{self.file_location}|{self.concern_key}"


def compute_finding_fingerprint(finding: dict) -> FindingFingerprint:
    """Build a stable fingerprint from a finding dict."""
    location = str(finding.get("location", "") or "")
    # Strip line-range suffix: "path:123-456" or "path:123,789" → "path"
    file_part = location.split(":", 1)[0].strip()
    concern = str(finding.get("concern", "") or "")
    # Normalize whitespace + lowercase, take first 60 chars
    concern_key = " ".join(concern.lower().split())[:60]
    return FindingFingerprint(
        file_location=file_part, concern_key=concern_key,
    )


# Parse fingerprint-relevant pieces out of an on-disk review markdown.
_FINDING_BLOCK_RE = re.compile(
    r"####\s+(?:block|change-required|suggestion|note):\s*.+?\n"
    r"\*\*Location:\*\*\s*([^\n]+).*?"
    r"\*\*Concern:\*\*\s*([^\n]+)",
    re.DOTALL,
)


def fingerprints_from_review_text(review_md: str) -> set[FindingFingerprint]:
    """Extract finding fingerprints from a review markdown file.

    Tolerates the substrate's render format (see review.py
    ``_render_finding``). Only blocking-class findings get fingerprinted
    — suggestions and notes don't drive the convergence loop because
    they don't synthesize follow-up tickets.
    """
    result: set[FindingFingerprint] = set()
    # Filter to ticketable severities only — the convergence loop is
    # specifically about findings that produce follow-up tickets.
    for match in re.finditer(
        r"####\s+(block|change-required):\s*([^\n]+)\n"
        r"\*\*Location:\*\*\s*([^\n]+).*?"
        r"\*\*Concern:\*\*\s*([^\n]+)",
        review_md,
        re.DOTALL,
    ):
        location = match.group(3).strip()
        concern = match.group(4).strip()
        result.add(compute_finding_fingerprint(
            {"location": location, "concern": concern}
        ))
    return result


def fingerprints_from_findings(findings: list[dict]) -> set[FindingFingerprint]:
    """Compute fingerprints from a fresh in-memory findings list
    (the one passed through ``_route_blocking_review``)."""
    result: set[FindingFingerprint] = set()
    for f in findings:
        sev = str(f.get("severity", "") or "")
        if sev not in ("block", "change-required"):
            continue
        result.add(compute_finding_fingerprint(f))
    return result


def _list_reviews_attributed_to_feature(
    project_root: Path, feature_slug: str,
) -> list[Path]:
    """Find every review markdown on disk that mentions this
    feature slug in its body (typically via the **Feature:**
    reference or **Files reviewed:** that includes the feature
    file path).

    Imperfect heuristic, but conservative — false positives
    (reviews attributed to a feature they don't actually concern)
    just mean we detect convergence slightly later. False
    negatives would be worse (missing the signal).

    Sorted by filename, which on the T-g3 short_guid convention
    is roughly chronological (ULIDs are time-sortable).
    """
    reviews_dir = project_root / ".wonderland" / "reviews"
    if not reviews_dir.is_dir():
        return []
    matches: list[Path] = []
    for path in sorted(reviews_dir.glob("review-*.md")):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if feature_slug in text:
            matches.append(path)
    return matches


@dataclass(frozen=True)
class ConvergenceFailure:
    """Result of convergence detection — names the recurring
    fingerprints + the contract artifacts the operator should
    review for ambiguity."""

    feature_slug: str
    window: int
    recurring_fingerprints: tuple[FindingFingerprint, ...]
    cited_contract_artifacts: tuple[str, ...]

    def summary(self) -> str:
        """Operator-facing summary string for the spec_ambiguity
        observation body."""
        fp_lines = "\n".join(
            f"  - ``{fp.file_location}`` — {fp.concern_key}..."
            for fp in self.recurring_fingerprints
        )
        contracts_lines = "\n".join(
            f"  - ``{c}``" for c in self.cited_contract_artifacts
        ) if self.cited_contract_artifacts else "  (none cited)"
        return (
            f"**Convergence failure: feature ``{self.feature_slug}`` "
            f"has circled {self.window}+ review passes with substantially "
            f"equivalent findings.**\n\n"
            f"Likely cause: spec ambiguity, not implementation bug. The "
            f"team has been oscillating between valid interpretations of "
            f"the contract; Caterpillar rejects whichever's current.\n\n"
            f"**Recurring findings:**\n{fp_lines}\n\n"
            f"**Cited contract artifacts (operator should review for "
            f"ambiguity):**\n{contracts_lines}\n\n"
            f"Implementation loop paused. Operator: disambiguate the "
            f"contract / ADR / spec artifact above, then re-queue the "
            f"feature to resume implementation."
        )


def detect_convergence_failure(
    project_root: Path,
    *,
    feature_slug: str,
    current_findings: list[dict],
    window: int = DEFAULT_WINDOW,
) -> ConvergenceFailure | None:
    """Check whether the current review's findings indicate convergence
    failure.

    A fingerprint is "recurring" when it appears in EVERY review in
    the comparison window (current + ``window-1`` prior reviews).
    Returns ``None`` when:
      - fewer than ``window-1`` prior reviews exist on disk for
        the feature (not enough history to judge);
      - the current review has no ticketable findings (oscillation
        requires findings on both sides);
      - no fingerprint appears in every window slot (each review
        is finding different things — that's progressive
        deepening, not oscillation).

    When detected, the returned object includes the recurring
    fingerprints + a best-effort extraction of any contract /
    ADR slugs cited in the recurring findings' concern text
    (operator should review those artifacts for ambiguity).
    """
    current_fps = fingerprints_from_findings(current_findings)
    if not current_fps:
        return None

    prior_reviews = _list_reviews_attributed_to_feature(
        project_root, feature_slug
    )
    # Need at least window-1 prior reviews (so current + prior = window)
    if len(prior_reviews) < window - 1:
        return None
    recent = prior_reviews[-(window - 1):]

    # Intersection across all recent + current
    recurring = set(current_fps)
    for path in recent:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return None
        prior_fps = fingerprints_from_review_text(text)
        recurring &= prior_fps
        if not recurring:
            return None

    if not recurring:
        return None

    # Best-effort: extract cited contract / ADR artifact slugs from
    # the recurring findings' concern text. Heuristic — looks for
    # patterns like "Contract Note 001", "ADR-001", or "adr-001-foo".
    cited: set[str] = set()
    for fp in recurring:
        # Re-find the concern text in the current findings for this fp
        for f in current_findings:
            if compute_finding_fingerprint(f) == fp:
                concern = str(f.get("concern", "") or "")
                for m in re.finditer(
                    r"(?:contract\s+note|adr)[-\s]?(\d+)",
                    concern, re.IGNORECASE,
                ):
                    cited.add(m.group(0))

    return ConvergenceFailure(
        feature_slug=feature_slug,
        window=window,
        recurring_fingerprints=tuple(sorted(
            recurring, key=lambda fp: (fp.file_location, fp.concern_key)
        )),
        cited_contract_artifacts=tuple(sorted(cited)),
    )


def record_spec_ambiguity(
    project_root: Path, failure: ConvergenceFailure,
) -> Path:
    """Persist the spec_ambiguity artifact to disk so the dashboard
    can surface it + the operator has a durable record."""
    out_dir = project_root / ".wonderland" / SPEC_AMBIGUITY_DIRNAME
    out_dir.mkdir(parents=True, exist_ok=True)
    guid = new_artifact_guid()
    body = (
        f"# Spec ambiguity: {failure.feature_slug}\n\n"
        f"**GUID:** {guid}\n"
        f"**Feature:** {failure.feature_slug}\n"
        f"**Detected at:** {datetime.now(timezone.utc).isoformat()}\n"
        f"**Window:** {failure.window} consecutive review passes\n\n"
        f"{failure.summary()}\n"
    )
    out_path = out_dir / (
        f"spec-ambiguity-{short_guid(guid)}-{failure.feature_slug}.md"
    )
    out_path.write_text(body, encoding="utf-8")
    return out_path


__all__ = [
    "FindingFingerprint",
    "ConvergenceFailure",
    "compute_finding_fingerprint",
    "fingerprints_from_review_text",
    "fingerprints_from_findings",
    "detect_convergence_failure",
    "record_spec_ambiguity",
    "DEFAULT_WINDOW",
    "SPEC_AMBIGUITY_DIRNAME",
]
