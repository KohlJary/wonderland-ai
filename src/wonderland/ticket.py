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
