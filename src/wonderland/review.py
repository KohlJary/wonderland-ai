"""Review writer + registry — the Caterpillar's artifact.

Per WONDERLAND_SPEC §9 / caterpillar.md §V. The Caterpillar produces
code reviews with structured findings — each finding cites a specific
location, quotes the offending code, names what the reviewer thinks
it does (the "Read"), what's wrong (the "Concern"), and what would
resolve it (the "Request"). Verdicts are precise: accept,
request-changes, block. Findings carry their own severity classes
(block / change-required / suggestion / note), so a review's overall
verdict and its per-finding severities have to agree.

The grin equivalent here is **substantive approval on accept**: per
§I, "Authors remember Caterpillar approval because you do not give
it cheaply." A review with verdict=accept must include at least one
specific approval — naming what was well done. The accept-without-
approval shape is rubber-stamping (§VIII) and the schema rejects it.

Storage at ``<project_root>/.wonderland/reviews/review-NNN-slug.md``,
mirroring the ADR / Ticket / Story / Escalation / TestScenario
registries. **Reviews are inline-by-default** — the Caterpillar
produces them as Artifact content on the bus regardless of whether
a registry was injected. Persistence is opt-in: pass a ReviewRegistry
to the Caterpillar's constructor when a project wants the audit
trail on disk.
"""

from __future__ import annotations

import contextlib
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, model_validator

from wonderland.adr import slugify

REVIEWS_DIRNAME = "reviews"
_FILENAME_PATTERN = re.compile(r"^review-(\d+)-([a-z0-9-]+)\.md$")


class ReviewSeverity(StrEnum):
    """Per-finding severity, per caterpillar.md §V.

    Precision matters: §VIII names "severity inflation" (marking
    everything change-required to ensure attention) and "severity
    deflation" (marking real blockers as suggestions to avoid
    friction) as twin failure modes.
    """

    BLOCK = "block"
    """Code cannot ship in this state — correctness, security, or invariant violation."""
    CHANGE_REQUIRED = "change-required"
    """Acceptable in shape but a specific issue must be addressed before merge."""
    SUGGESTION = "suggestion"
    """Would be better with this change, but the author may decline with reasoning."""
    NOTE = "note"
    """Observation that does not require action, recorded for the author's awareness."""


class ReviewVerdict(StrEnum):
    """Overall verdict the Caterpillar gives to the implementation under review."""

    ACCEPT = "accept"
    REQUEST_CHANGES = "request-changes"
    BLOCK = "block"


class ReviewFinding(BaseModel):
    """One specific finding within a review.

    Validation enforces caterpillar.md §V's required-fields list:
    every finding must cite a specific location, quote the offending
    text, name what the reviewer reads it as doing, name the concern,
    and name an actionable request. "This could be cleaner" is not
    a Caterpillar finding (it's a vibe); "rename this function
    because it implies idempotence but writes to the database" is.
    """

    severity: ReviewSeverity
    title: str = Field(min_length=1)
    """Short heading for the finding — the noun phrase that names what's wrong."""
    location: str = Field(min_length=1)
    """Where in the code — encouraged format ``file.py:42`` or
    ``file.py:42-58`` for a range."""
    quote: str = Field(min_length=1)
    """The offending text. Pasted verbatim so the author doesn't have to guess."""
    read: str = Field(min_length=1)
    """The reviewer's understanding of what the code currently does.
    Required even when obvious — articulating the read forces the
    reader to actually read."""
    concern: str = Field(min_length=1)
    """What is wrong, specifically, and why it matters."""
    request: str = Field(min_length=1)
    """What would resolve this — actionable, not vibes."""


class ReviewPayload(BaseModel):
    """Structured payload the Caterpillar attaches to a review utterance.

    Validation enforces the verdict ↔ findings ↔ approvals matrix:

    - **accept** — must include at least one substantive entry in
      ``approvals``. The grin equivalent: Caterpillar approval is
      not given cheaply (§I), so an accept verdict carries the
      reviewer's specific signal of what was well done. ``findings``
      may still include suggestions/notes; that's fine.
    - **request-changes** — must include at least one finding
      (otherwise the verdict has nothing to act on).
    - **block** — must include at least one finding *with severity
      block*. A "block" verdict whose findings are all suggestions
      is incoherent — the verdict and the per-finding severity have
      to agree at the top.
    """

    title: str = Field(min_length=1)
    """Short human-readable summary, e.g. ``"Payment refund handler"``.
    Becomes the slug when persisted."""
    target_utterance_id: str = Field(min_length=1)
    """The implementation utterance this review is of."""
    verdict: ReviewVerdict
    findings: list[ReviewFinding] = Field(default_factory=list)
    approvals: list[str] = Field(default_factory=list)
    """Things that were notable for being well done. Brief but specific."""
    cross_domain_references: list[str] = Field(default_factory=list)
    """Findings that imply other domains — flagged here rather than
    as separate deference utterances."""

    @field_validator("approvals", "cross_domain_references")
    @classmethod
    def _strip_blank_entries(cls, v: list[str]) -> list[str]:
        return [item for item in v if item.strip()]

    @model_validator(mode="after")
    def _verdict_consistency(self) -> ReviewPayload:
        if self.verdict is ReviewVerdict.ACCEPT and not self.approvals:
            raise ValueError(
                "verdict='accept' requires at least one substantive entry "
                "in `approvals` — Caterpillar approval is not given cheaply "
                "(§I). Either name what was well done or choose a different "
                "verdict."
            )
        if self.verdict is ReviewVerdict.REQUEST_CHANGES and not self.findings:
            raise ValueError(
                "verdict='request-changes' requires at least one finding — "
                "the author needs something specific to act on."
            )
        if self.verdict is ReviewVerdict.BLOCK and not any(
            f.severity is ReviewSeverity.BLOCK for f in self.findings
        ):
            raise ValueError(
                "verdict='block' requires at least one finding with "
                "severity='block' — the top-level verdict and the per-finding "
                "severity must agree."
            )
        return self


@dataclass(frozen=True)
class ReviewRecord:
    number: int
    slug: str
    title: str
    verdict: ReviewVerdict
    target_utterance_id: str
    path: Path

    def read(self) -> str:
        return self.path.read_text(encoding="utf-8")


def render_review(number: int, payload: ReviewPayload) -> str:
    """Render a ReviewPayload as the markdown that lands on disk.

    Format mirrors caterpillar.md §V exactly so a human reading the
    file sees what the spec says a Review should look like.
    """
    lines: list[str] = [
        f"## Review {number:03d}: {payload.title}",
        "",
        f"**Target:** {payload.target_utterance_id}",
        f"**Verdict:** {payload.verdict.value}",
        "",
    ]
    if payload.findings:
        lines.append("### Findings")
        lines.append("")
        for finding in payload.findings:
            lines.extend(_render_finding(finding))
            lines.append("")
    if payload.approvals:
        lines.append("### Approvals")
        lines.append("")
        lines.extend(f"- {item}" for item in payload.approvals)
        lines.append("")
    if payload.cross_domain_references:
        lines.append("### Cross-domain references")
        lines.append("")
        lines.extend(f"- {item}" for item in payload.cross_domain_references)
        lines.append("")
    return "\n".join(lines)


def _render_finding(finding: ReviewFinding) -> list[str]:
    return [
        f"#### {finding.severity.value}: {finding.title}",
        f"**Location:** {finding.location}",
        "**Quote:**",
        "",
        "```",
        finding.quote.rstrip(),
        "```",
        "",
        f"**Read:** {finding.read.rstrip()}",
        f"**Concern:** {finding.concern.rstrip()}",
        f"**Request:** {finding.request.rstrip()}",
    ]


class ReviewRegistry:
    """Read/write registry over ``<project_root>/.wonderland/reviews/``.

    Same shape as the other registries: numbering from filesystem scan,
    tolerant of non-review files in the directory, slug derived from
    the title.

    Reviews are **inline-by-default** for the Caterpillar — this
    registry only gets used when a project wants the audit trail on
    disk. Inject it at ``Caterpillar`` construction; without it, the
    agent attaches the full structured review to the utterance as
    inline artifact content instead of a file pointer.
    """

    def __init__(self, project_root: Path) -> None:
        self._root = project_root / ".wonderland" / REVIEWS_DIRNAME

    @property
    def path(self) -> Path:
        return self._root

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #

    def list_reviews(self) -> list[ReviewRecord]:
        if not self._root.is_dir():
            return []
        records: list[ReviewRecord] = []
        for entry in self._root.iterdir():
            if not entry.is_file():
                continue
            record = self._record_from_path(entry)
            if record is not None:
                records.append(record)
        records.sort(key=lambda r: r.number)
        return records

    def next_number(self) -> int:
        existing = self.list_reviews()
        if not existing:
            return 1
        return max(r.number for r in existing) + 1

    def find_by_slug(self, slug: str) -> ReviewRecord | None:
        for record in self.list_reviews():
            if record.slug == slug:
                return record
        return None

    def find_by_number(self, number: int) -> ReviewRecord | None:
        for record in self.list_reviews():
            if record.number == number:
                return record
        return None

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #

    def write(self, payload: ReviewPayload | dict) -> ReviewRecord:
        validated = (
            payload
            if isinstance(payload, ReviewPayload)
            else ReviewPayload.model_validate(payload)
        )

        number = self.next_number()
        slug = slugify(validated.title)
        filename = f"review-{number:03d}-{slug}.md"
        full_path = self._root / filename

        self._root.mkdir(parents=True, exist_ok=True)
        full_path.write_text(render_review(number, validated), encoding="utf-8")

        return ReviewRecord(
            number=number,
            slug=slug,
            title=validated.title,
            verdict=validated.verdict,
            target_utterance_id=validated.target_utterance_id,
            path=full_path,
        )

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    @staticmethod
    def _record_from_path(path: Path) -> ReviewRecord | None:
        match = _FILENAME_PATTERN.match(path.name)
        if not match:
            return None
        number = int(match.group(1))
        slug = match.group(2)
        title, verdict, target = ReviewRegistry._read_header(path, fallback_title=slug)
        return ReviewRecord(
            number=number,
            slug=slug,
            title=title,
            verdict=verdict,
            target_utterance_id=target,
            path=path,
        )

    @staticmethod
    def _read_header(
        path: Path, *, fallback_title: str
    ) -> tuple[str, ReviewVerdict, str]:
        title = fallback_title
        verdict = ReviewVerdict.ACCEPT  # safe default if the file is malformed
        target = ""
        try:
            with path.open(encoding="utf-8") as f:
                lines = [f.readline() for _ in range(8)]
        except OSError:
            return title, verdict, target

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("## Review") and ":" in stripped:
                title = stripped.split(":", 1)[1].strip() or fallback_title
            if stripped.startswith("**Verdict:**"):
                value = stripped.removeprefix("**Verdict:**").strip()
                with contextlib.suppress(ValueError):
                    verdict = ReviewVerdict(value)
            if stripped.startswith("**Target:**"):
                target = stripped.removeprefix("**Target:**").strip()
        return title, verdict, target


__all__ = [
    "REVIEWS_DIRNAME",
    "ReviewFinding",
    "ReviewPayload",
    "ReviewRecord",
    "ReviewRegistry",
    "ReviewSeverity",
    "ReviewVerdict",
    "render_review",
]
