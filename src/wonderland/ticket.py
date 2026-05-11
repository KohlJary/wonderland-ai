"""Ticket writer + registry — the White Rabbit's pocket-watch marks.

Per WONDERLAND_SPEC §9 / white_rabbit.md §V. The Rabbit decomposes
stories and proposals into tickets — concrete work units with explicit
scope, dependencies, and estimates. The estimate is always present and
always honest; the burndown stays trustworthy or it stops being useful.

Storage: ``<project_root>/.wonderland/tickets/ticket-NNN-slug.md``,
3-digit zero-padded numbering for filesystem sortability. Same
single-source-of-truth approach as ``ADRRegistry`` — no separate
counter file; ``next_number()`` derives from scanning existing tickets.

Validation is **looser than ADRs.** ADRs enforce the grin (the
Tradeoffs section is non-optional) because the Cat doesn't bless
something without naming costs. Tickets enforce the *Rabbit's*
discipline: title, owner, tier, estimate, and description are all
required; the rest can be empty but is represented in the schema so
the Rabbit knows what's missing if he tries to omit it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

from wonderland.adr import slugify

TICKETS_DIRNAME = "tickets"
_FILENAME_PATTERN = re.compile(r"^ticket-(\d+)-([a-z0-9-]+)\.md$")


class TicketStackSpan(StrEnum):
    """Which side of the stack the ticket's work touches.

    Mirrors ``feature.StackSpan`` — kept as a separate enum here
    so the ticket module doesn't take on a hard dep on the feature
    module and so the two can drift independently if needed (we
    don't expect them to). Used by the M7 roster filter to decide
    which Tweedles to invite for the iteration.
    """

    FRONTEND = "frontend"
    BACKEND = "backend"
    FULL_STACK = "full-stack"


class TicketTier(StrEnum):
    V1 = "v1"
    FAST_FOLLOW = "fast-follow"
    POST_LAUNCH = "post-launch"


class TicketStatus(StrEnum):
    OPEN = "open"
    IN_FLIGHT = "in_flight"
    BLOCKED = "blocked"
    DONE = "done"
    DROPPED = "dropped"


class TicketDependencies(BaseModel):
    """Three flavors of dependency, per Rabbit §V."""

    blocks: list[str] = Field(default_factory=list)
    blocked_by: list[str] = Field(default_factory=list)
    soft: list[str] = Field(default_factory=list)


class TicketPayload(BaseModel):
    """Structured payload the Rabbit attaches to a ticket-issuing utterance."""

    title: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    tier: TicketTier
    estimate: str = Field(min_length=1)
    description: str = Field(min_length=1)
    sources: list[str] = Field(default_factory=list)
    dependencies: TicketDependencies = Field(default_factory=TicketDependencies)
    acceptance: list[str] = Field(default_factory=list)
    risk: str = ""
    status: TicketStatus = TicketStatus.OPEN
    # Which side of the stack the ticket touches. Same enum values
    # as ``feature.StackSpan``; aliased here so the ticket schema
    # is self-contained (and to avoid an import cycle). Used by
    # the M7 roster filter to skip the Tweedle whose layer this
    # ticket doesn't touch — frontend tickets only need
    # Tweedledee in the M7 roster, backend tickets only need
    # Tweedledum, full-stack tickets need both. Default is
    # ``full-stack`` so older tickets (and any tickets where
    # M3.5 / M5 didn't make a determination) keep the original
    # full-roster behavior.
    stack_span: "TicketStackSpan" = Field(
        default_factory=lambda: TicketStackSpan.FULL_STACK,
    )


@dataclass(frozen=True)
class TicketRecord:
    number: int
    slug: str
    title: str
    path: Path

    def read(self) -> str:
        return self.path.read_text(encoding="utf-8")


def render_ticket(number: int, payload: TicketPayload) -> str:
    """Render a ticket payload as the markdown that lands on disk.

    The on-disk format mirrors white_rabbit.md §V exactly so a human
    reading the file sees what the Rabbit's constitution says a ticket
    should look like.
    """
    lines: list[str] = [
        f"## Ticket {number:03d}: {payload.title}",
        "",
        f"**Sources:** {_join_or_dash(payload.sources)}",
        f"**Owner:** {payload.owner}",
        f"**Tier:** {payload.tier.value}",
        f"**Stack span:** {payload.stack_span.value}",
        f"**Estimate:** {payload.estimate}",
        f"**Status:** {payload.status.value}",
        "",
        "**Dependencies:**",
        f"- Blocks: {_join_or_dash(payload.dependencies.blocks)}",
        f"- Blocked by: {_join_or_dash(payload.dependencies.blocked_by)}",
        f"- Soft: {_join_or_dash(payload.dependencies.soft)}",
        "",
        "**Description:**",
        "",
        payload.description.rstrip(),
        "",
        "**Acceptance:**",
    ]
    if payload.acceptance:
        lines.extend(f"- {item}" for item in payload.acceptance)
    else:
        lines.append("- (to be filled)")
    lines.append("")
    if payload.risk.strip():
        lines.append("**Risk:**")
        lines.append("")
        lines.append(payload.risk.rstrip())
        lines.append("")
    return "\n".join(lines)


def _join_or_dash(items: list[str]) -> str:
    return ", ".join(items) if items else "—"


def read_ticket_stack_span(
    project_root: Path, slug: str
) -> TicketStackSpan:
    """Read the ``**Stack span:**`` line from a ticket's on-disk
    markdown. Returns ``FULL_STACK`` for tickets where the line is
    missing or unrecognised — safe default that preserves the
    full-roster behaviour for older tickets that predate the
    schema field.

    Cheap (single file read + regex); called once per ticket
    iteration in ``_collect_per_item_items`` so the substrate
    can attach the value to the item payload before the roster
    filter kicks in.
    """
    record = TicketRegistry(project_root).find_by_slug(slug)
    if record is None:
        return TicketStackSpan.FULL_STACK
    try:
        text = record.path.read_text(encoding="utf-8")
    except OSError:
        return TicketStackSpan.FULL_STACK
    match = _STACK_SPAN_RE.search(text)
    if match is None:
        return TicketStackSpan.FULL_STACK
    raw = match.group(1).strip().lower()
    try:
        return TicketStackSpan(raw)
    except ValueError:
        return TicketStackSpan.FULL_STACK


_STACK_SPAN_RE = re.compile(
    r"^\s*\*\*Stack span:\*\*\s*(\S+)\s*$",
    re.MULTILINE,
)


class TicketRegistry:
    """Read/write registry over ``<project_root>/.wonderland/tickets/``.

    Same shape as ``ADRRegistry``: numbering derives from scanning
    existing files, so manual deletions don't corrupt the sequence and
    a stray non-ticket file in the directory doesn't crash queries.
    """

    def __init__(self, project_root: Path) -> None:
        self._root = project_root / ".wonderland" / TICKETS_DIRNAME

    @property
    def path(self) -> Path:
        return self._root

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #

    def list_tickets(self) -> list[TicketRecord]:
        if not self._root.is_dir():
            return []
        records: list[TicketRecord] = []
        for entry in self._root.iterdir():
            if not entry.is_file():
                continue
            record = self._record_from_path(entry)
            if record is not None:
                records.append(record)
        records.sort(key=lambda r: r.number)
        return records

    def next_number(self) -> int:
        existing = self.list_tickets()
        if not existing:
            return 1
        return max(r.number for r in existing) + 1

    def find_by_slug(self, slug: str) -> TicketRecord | None:
        for record in self.list_tickets():
            if record.slug == slug:
                return record
        return None

    def find_by_number(self, number: int) -> TicketRecord | None:
        for record in self.list_tickets():
            if record.number == number:
                return record
        return None

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #

    def write(self, payload: TicketPayload | dict) -> TicketRecord:
        validated = (
            payload if isinstance(payload, TicketPayload) else TicketPayload.model_validate(payload)
        )

        number = self.next_number()
        slug = slugify(validated.title)
        filename = f"ticket-{number:03d}-{slug}.md"
        full_path = self._root / filename

        self._root.mkdir(parents=True, exist_ok=True)
        full_path.write_text(render_ticket(number, validated), encoding="utf-8")

        return TicketRecord(
            number=number,
            slug=slug,
            title=validated.title,
            path=full_path,
        )

    def delete_by_slug(self, slug: str) -> bool:
        """Remove a ticket file from disk by slug. Returns True if a
        matching ticket was found and deleted, False otherwise.

        Numbering deliberately doesn't repack — list_tickets walks the
        filename pattern and tolerates gaps. Used by the dashboard's
        ticket-prune flow when an operator wants to drop duplicates
        Rabbit shipped during M3 revision passes (see analysis 040
        + roadmap 171b36e1).
        """
        record = self.find_by_slug(slug)
        if record is None:
            return False
        try:
            record.path.unlink()
        except OSError:
            return False
        return True

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    @staticmethod
    def _record_from_path(path: Path) -> TicketRecord | None:
        match = _FILENAME_PATTERN.match(path.name)
        if not match:
            return None
        number = int(match.group(1))
        slug = match.group(2)
        title = TicketRegistry._title_from_file(path, fallback=slug)
        return TicketRecord(number=number, slug=slug, title=title, path=path)

    @staticmethod
    def _title_from_file(path: Path, *, fallback: str) -> str:
        try:
            with path.open(encoding="utf-8") as f:
                first_line = f.readline().strip()
        except OSError:
            return fallback
        if not first_line.startswith("## Ticket") or ":" not in first_line:
            return fallback
        return first_line.split(":", 1)[1].strip() or fallback
