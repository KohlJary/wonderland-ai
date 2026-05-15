"""Feature writer + registry — Rabbit's grouping artifact for M2.5.

Per the M2/M3 gap surfaced in analysis 026/027 and roadmap d1f4f2ec:
M3 contract-negotiation seeds from a single ticket and Tweedles
generalize from there, which produces the inconsistent-frontend-vs-
backend pattern observed across runs. Features are tickets *grouped*
into user-facing units that span the stack coherently, so M3 can
negotiate seams against a feature instead of one ticket at a time.

Storage: ``<project_root>/.wonderland/features/feature-NNN-slug.md``,
3-digit zero-padded numbering. Same single-source-of-truth approach
as TicketRegistry — no separate counter file; ``next_number()``
derives from scanning existing features.

Validation is deliberately looser than tickets. Tickets pin scope,
estimate, and dependencies because the Rabbit's discipline says they
must; features are organizational — title, description, and at least
one constituent ticket are required, the rest is free-form. The
discipline lives at the ticket layer; features carry the user-facing
framing on top.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

from wonderland.adr import slugify
from wonderland.ticket import TicketTier

FEATURES_DIRNAME = "features"
_FILENAME_PATTERN = re.compile(r"^feature-(\d+)-([a-z0-9-]+)\.md$")


class StackSpan(StrEnum):
    """Which side of the stack a feature touches.

    Knowing this up front lets M3's contract negotiation pre-flight
    the right seams: full-stack features need both Tweedles aligned
    on the contract; backend-only or frontend-only features can be
    handled on one side. The pattern Tweedles missed in prior runs
    was full-stack work that they negotiated as if it were one-sided.
    """

    FRONTEND = "frontend"
    BACKEND = "backend"
    FULL_STACK = "full-stack"


class FeatureKind(StrEnum):
    """Whether the feature is a user-facing capability or foundational
    plumbing.

    Capabilities are user-meaningful — Alice's persona-driven stories
    compose into them. Foundations are developer-meaningful —
    Caterpillar's plumbing stories (mock data, observability,
    environment config, build tooling) compose into them. Same
    lifecycle, same decomposition into tickets, same dashboard view —
    the discriminator just tells agents what kind of work this is so
    M2 doesn't get hung up on "is mock-data setup really a feature?"
    semantic debates.

    Default is CAPABILITY for back-compat: features shipped before
    this field existed are user-facing capabilities by definition,
    and the default keeps existing payloads valid without a kind:
    field.
    """

    CAPABILITY = "capability"
    FOUNDATION = "foundation"


class FeaturePayload(BaseModel):
    """Structured payload Rabbit attaches to a feature-issuing utterance."""

    title: str = Field(min_length=1)
    description: str = Field(
        min_length=1,
        description="What user-facing thing this feature delivers, in plain language.",
    )
    kind: FeatureKind = Field(
        default=FeatureKind.CAPABILITY,
        description=(
            "capability (default) for user-facing features; "
            "foundation for plumbing/developer-experience work like "
            "mock data, observability, env config, build tooling. "
            "Functionally identical lifecycle; the kind drives "
            "context-appropriate framing so M2 doesn't argue "
            "semantics for stories whose persona is a developer."
        ),
    )
    tickets: list[str] = Field(
        default_factory=list,
        description=(
            "Slugs of constituent tickets this feature aggregates. "
            "Informational only — the source-of-truth for "
            "ticket→feature membership is each ticket's "
            "``Sources:`` field, written by M3 (Rabbit's "
            "decomposition meeting). When M2 ships a feature, "
            "this list is typically empty; M3 populates it later "
            "when tickets get decomposed (via the reverse-index "
            "in ``_ticket_to_feature_map``). Pre-T88 workflows "
            "where tickets came before features used this as the "
            "primary link, hence the field stays for back-compat "
            "even though it's no longer load-bearing."
        ),
    )
    personas: list[str] = Field(
        default_factory=list,
        description="Persona names from M1 stories that this feature serves.",
    )
    stack_span: StackSpan
    tier: TicketTier
    sources: list[str] = Field(
        ...,
        min_length=1,
        description=(
            "Story slugs whose intent this feature realizes. "
            "REQUIRED and non-empty — a feature without source "
            "stories is an unmoored claim; M3 decomposition needs "
            "the story chain to know what the feature was supposed "
            "to deliver and the T-m8b coverage check walks "
            "milestone.consumes_requirements → stories realizing "
            "those → features sourcing those stories. An empty "
            "sources list breaks that walk + leaves the feature "
            "orphaned in lifecycle queries."
        ),
    )


@dataclass(frozen=True)
class FeatureRecord:
    number: int
    slug: str
    title: str
    path: Path

    def read(self) -> str:
        return self.path.read_text(encoding="utf-8")


def render_feature(number: int, payload: FeaturePayload) -> str:
    """Render a feature payload as the markdown that lands on disk."""
    lines: list[str] = [
        f"## Feature {number:03d}: {payload.title}",
        "",
        f"**Kind:** {payload.kind.value}",
        f"**Sources:** {_join_or_dash(payload.sources)}",
        f"**Personas:** {_join_or_dash(payload.personas)}",
        f"**Stack span:** {payload.stack_span.value}",
        f"**Tier:** {payload.tier.value}",
        "",
        "**Description:**",
        "",
        payload.description.rstrip(),
        "",
        "**Constituent tickets:**",
    ]
    if payload.tickets:
        lines.extend(f"- {ticket}" for ticket in payload.tickets)
    else:
        # Empty tickets is normal at M2 ship time — M3 hasn't run
        # yet. Surface a "to be decomposed" placeholder so the file
        # is human-readable instead of "this should not happen,"
        # which used to be true under the pre-T88 workflow but
        # isn't anymore.
        lines.append("- *(to be decomposed in M3)*")
    lines.append("")
    return "\n".join(lines)


def _join_or_dash(items: list[str]) -> str:
    return ", ".join(items) if items else "—"


class FeatureRegistry:
    """Read/write registry over ``<project_root>/.wonderland/features/``.

    Same shape as TicketRegistry: numbering derives from scanning
    existing files; no separate counter to keep in sync.
    """

    def __init__(self, project_root: Path) -> None:
        self._root = project_root / ".wonderland" / FEATURES_DIRNAME

    @property
    def path(self) -> Path:
        return self._root

    def list_features(self) -> list[FeatureRecord]:
        if not self._root.is_dir():
            return []
        records: list[FeatureRecord] = []
        for entry in self._root.iterdir():
            if not entry.is_file():
                continue
            record = self._record_from_path(entry)
            if record is not None:
                records.append(record)
        records.sort(key=lambda r: r.number)
        return records

    def next_number(self) -> int:
        existing = self.list_features()
        if not existing:
            return 1
        return max(r.number for r in existing) + 1

    def find_by_slug(self, slug: str) -> FeatureRecord | None:
        for record in self.list_features():
            if record.slug == slug:
                return record
        return None

    def find_by_number(self, number: int) -> FeatureRecord | None:
        for record in self.list_features():
            if record.number == number:
                return record
        return None

    def write(self, payload: FeaturePayload | dict) -> FeatureRecord:
        """Create or update a feature by slug — update-by-slug
        semantics mirror MilestoneRegistry. Re-emit with the same
        slug overwrites in place (preserves number); new slug
        appends with the next available number. P15 follow-up
        aligning the design-time registries with the planning
        registry's dedup shape."""
        validated = (
            payload
            if isinstance(payload, FeaturePayload)
            else FeaturePayload.model_validate(payload)
        )

        slug = slugify(validated.title)
        existing = self.find_by_slug(slug)
        if existing is not None:
            number = existing.number
            full_path = existing.path
        else:
            number = self.next_number()
            filename = f"feature-{number:03d}-{slug}.md"
            full_path = self._root / filename

        self._root.mkdir(parents=True, exist_ok=True)
        full_path.write_text(render_feature(number, validated), encoding="utf-8")

        return FeatureRecord(
            number=number,
            slug=slug,
            title=validated.title,
            path=full_path,
        )

    @staticmethod
    def _record_from_path(path: Path) -> FeatureRecord | None:
        match = _FILENAME_PATTERN.match(path.name)
        if not match:
            return None
        number = int(match.group(1))
        slug = match.group(2)
        title = FeatureRegistry._title_from_file(path, fallback=slug)
        return FeatureRecord(number=number, slug=slug, title=title, path=path)

    @staticmethod
    def _title_from_file(path: Path, *, fallback: str) -> str:
        try:
            with path.open(encoding="utf-8") as f:
                first_line = f.readline().strip()
        except OSError:
            return fallback
        if not first_line.startswith("## Feature") or ":" not in first_line:
            return fallback
        return first_line.split(":", 1)[1].strip() or fallback


__all__ = [
    "FEATURES_DIRNAME",
    "FeaturePayload",
    "FeatureRecord",
    "FeatureRegistry",
    "StackSpan",
    "render_feature",
]
