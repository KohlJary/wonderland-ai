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

from wonderland.artifact_guid import new_artifact_guid, short_guid

REVIEWS_DIRNAME = "reviews"
# T-g3: filename's id-part is either an 8-char ULID prefix (new) or
# a 1-4 digit legacy number (pre-P18).
_FILENAME_PATTERN = re.compile(
    r"^review-(?P<id>[0-9A-HJKMNP-TV-Z]{8}|\d{1,4})-(?P<slug>[a-z0-9-]+)\.md$"
)
_GUID_PATTERN = re.compile(r"^\*\*GUID:\*\*\s*([0-9A-HJKMNP-TV-Z]{26})\s*$", re.MULTILINE)
_NUMBER_FROM_H2 = re.compile(r"^##\s*Review\s+(\d+)\s*:", re.MULTILINE)


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


class FindingKind(StrEnum):
    """Whether a finding describes a bug (behavior is wrong) or
    meta-feedback (behavior is correct; something about the
    code's expression could be better).

    The substrate uses this to gate ticket synthesis:
    ``bug``-kind findings spawn follow-up implementation tickets
    via ``_synthesize_followup_ticket_from_finding``; other kinds
    record in the review artifact but do NOT spawn tickets, on
    the theory that nobody should re-run M7 to "make the test
    clearer" when the test already passes.

    This is **orthogonal to severity**: a finding can be
    ``change-required`` severity (operator should pay attention)
    AND ``meta`` kind (advisory, no re-implementation needed).
    The two axes answer different questions:

    - severity → "how concerned should the author be?"
    - kind → "should the substrate spawn implementation work?"

    Analysis 033 §5.1 identified the recursive test-quality cycle
    that motivated this primitive: Caterpillar surfacing findings
    like "assertions lack clarity" or "test allows multiple
    conflicting interpretations" got synthesized as follow-up
    tickets, the Tweedles re-implemented the tests, Caterpillar
    reviewed again. 5+ such cycles × $2-4 each per pilot. The
    findings were legitimate review feedback but they were
    meta-feedback, not bugs — implementation tickets were the
    wrong shape of work to spawn from them.
    """

    BUG = "bug"
    """Implementation defect — behavior is wrong. Spawns a
    follow-up implementation ticket when severity is
    ``block`` or ``change-required``. Default."""
    META = "meta"
    """Meta-feedback about how the code expresses its intent —
    behavior is correct but clarity / structure / naming /
    test-assertion-quality could be better. Recorded in the
    review artifact for author awareness; does NOT spawn an
    implementation ticket regardless of severity. The recursive
    test-quality cycle's natural home."""
    CONVENTION = "convention"
    """Codebase convention / style observation. Author may
    address in next touch or accept with reasoning. Does NOT
    spawn an implementation ticket — convention drift is
    handled via Convention Notes (caterpillar.md §V), not
    re-implementation work."""
    NIT = "nit"
    """Minor cosmetic. Recorded for author awareness; never
    spawns an implementation ticket. If you're tempted to file
    many of these in one review, you may be drifting into
    bikeshedding (§VIII)."""


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
    kind: FindingKind = FindingKind.BUG
    """Whether this finding describes a bug (behavior is wrong) or
    meta-feedback / convention / nit (behavior is correct;
    expression could be better). Default ``bug`` preserves the
    pre-existing behavior — findings that don't set this field
    are treated as ticketable bug reports, same as before this
    primitive was added.

    Set explicitly to ``meta`` / ``convention`` / ``nit`` when
    the finding is feedback to the author about clarity /
    structure / style rather than an implementation defect. The
    substrate uses this to gate ticket synthesis — only
    ``bug``-kind findings spawn follow-up implementation tickets.

    Orthogonal to severity. A ``change-required``-severity
    ``meta``-kind finding tells the author "this matters, please
    address it" but tells the substrate "don't re-run M7 to
    fix it; the author addresses meta in their next touch."

    Motivation (analysis 033 §5.1): the recursive test-quality
    cycle that the Tweedles spent ~$12-15 of M7 on in mvp-demo2
    was driven by findings that were meta-feedback but got
    treated as bugs. Adding this field lets Caterpillar mark
    them honestly without losing the feedback signal."""

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
    test_coverage_required: bool = False
    """Whether the synthesized follow-up ticket (if this finding gets
    routed through ``_synthesize_followup_ticket_from_finding``) needs
    a fresh test-scenario design pass before implementation. Defaults
    to False — most findings restore code-correctness for paths whose
    existing tests already cover the surface area, so adversarial
    scenario design (tea-party / M6) adds little. Set True when the
    fix introduces a behavior that no existing test covers and the
    Mad Hatter's edge-case discipline would surface scenarios the
    Tweedles wouldn't think of on their own. Caterpillar's judgment;
    default-false keeps cost low on the common case."""


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

    guid: str = Field(default_factory=new_artifact_guid)
    """P18 — stable Review identity. Caterpillar re-emits with same
    guid to update an existing review (e.g. after seeing the
    author's fix); coining a new guid creates a new review."""

    title: str = Field(min_length=1)
    """Short human-readable summary, e.g. ``"Payment refund handler"``.
    Becomes the slug when persisted."""
    target_files: list[str] = Field(min_length=1)
    """The files this review covers (paths relative to project root).

    Working-tree-as-implementation-artifact (analysis 016 followup +
    analysis 018): the reviewer reads ``git_status`` / ``git_diff`` to
    find what shipped, then names the files this review is about. The
    review can cover one file or several; ``findings`` use file:line
    locations that should be a subset of ``target_files``."""
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
    guid: str
    slug: str
    title: str
    verdict: ReviewVerdict
    target_files: tuple[str, ...]
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
        f"**GUID:** {payload.guid}",
        f"**Files reviewed:** {', '.join(payload.target_files)}",
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
    lines = [
        f"#### {finding.severity.value}: {finding.title}",
    ]
    # Surface kind only when it's not the default (bug). Most
    # findings will be bugs and rendering "kind: bug" on every
    # one is noise; rendering "kind: meta" stands out where it
    # matters.
    if finding.kind is not FindingKind.BUG:
        lines.append(f"**Kind:** {finding.kind.value}")
    lines.extend([
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
    ])
    return lines


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

    def find_by_guid(self, guid: str) -> ReviewRecord | None:
        """P18 T-g2 — primary identity lookup."""
        if not guid:
            return None
        for record in self.list_reviews():
            if record.guid == guid:
                return record
        return None

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
            payload if isinstance(payload, ReviewPayload) else ReviewPayload.model_validate(payload)
        )

        slug = slugify(validated.title)
        # T-g2: guid-first lookup. Review doesn't have update-by-slug
        # (each review is a discrete event by default), but
        # update-by-guid is the right semantic when Caterpillar
        # explicitly amends a prior review by re-emitting its guid.
        existing = self.find_by_guid(validated.guid)
        if existing is not None:
            number = existing.number
            full_path = existing.path
        else:
            number = self.next_number()
            # T-g3: filename embeds short_guid for substrate identity.
            filename = f"review-{short_guid(validated.guid)}-{slug}.md"
            full_path = self._root / filename

        self._root.mkdir(parents=True, exist_ok=True)
        full_path.write_text(render_review(number, validated), encoding="utf-8")

        return ReviewRecord(
            number=number,
            guid=validated.guid,
            slug=slug,
            title=validated.title,
            verdict=validated.verdict,
            target_files=tuple(validated.target_files),
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
        id_part = match.group("id")
        slug = match.group("slug")
        title, verdict, target_files = ReviewRegistry._read_header(
            path, fallback_title=slug
        )
        guid = ReviewRegistry._guid_from_file(path)
        number = ReviewRegistry._number_from_file(path, id_part)
        return ReviewRecord(
            number=number,
            guid=guid,
            slug=slug,
            title=title,
            verdict=verdict,
            target_files=target_files,
            path=path,
        )

    @staticmethod
    def _number_from_file(path: Path, id_part: str) -> int:
        """T-g3 — legacy filenames carried number in the id slot;
        new-shape files keep it only in the H2 header."""
        if id_part.isdigit():
            return int(id_part)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return 0
        m = _NUMBER_FROM_H2.search(text)
        return int(m.group(1)) if m else 0

    @staticmethod
    def _guid_from_file(path: Path) -> str:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return new_artifact_guid()
        m = _GUID_PATTERN.search(text)
        return m.group(1) if m else new_artifact_guid()

    @staticmethod
    def _read_header(
        path: Path, *, fallback_title: str
    ) -> tuple[str, ReviewVerdict, tuple[str, ...]]:
        title = fallback_title
        verdict = ReviewVerdict.ACCEPT  # safe default if the file is malformed
        target_files: tuple[str, ...] = ()
        try:
            with path.open(encoding="utf-8") as f:
                lines = [f.readline() for _ in range(8)]
        except OSError:
            return title, verdict, target_files

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("## Review") and ":" in stripped:
                title = stripped.split(":", 1)[1].strip() or fallback_title
            if stripped.startswith("**Verdict:**"):
                value = stripped.removeprefix("**Verdict:**").strip()
                with contextlib.suppress(ValueError):
                    verdict = ReviewVerdict(value)
            if stripped.startswith("**Files reviewed:**"):
                raw = stripped.removeprefix("**Files reviewed:**").strip()
                if raw:
                    target_files = tuple(
                        item.strip() for item in raw.split(",") if item.strip()
                    )
        return title, verdict, target_files


__all__ = [
    "FindingKind",
    "REVIEWS_DIRNAME",
    "ReviewFinding",
    "ReviewPayload",
    "ReviewRecord",
    "ReviewRegistry",
    "ReviewSeverity",
    "ReviewVerdict",
    "render_review",
]
