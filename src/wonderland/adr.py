"""ADR writer + registry — the Cheshire Cat's grin, persisted.

Per WONDERLAND_SPEC §9 / D-006 / cheshire_cat.md §V. Every architectural
decision the Cat blesses must be recorded as an ADR with explicit
tradeoffs. The Tradeoffs section is the grin; an ADR without it is
incomplete and the Cat will not bless it.

Storage: ``<project_root>/.wonderland/architecture/adr-NNN-slug.md``,
3-digit zero-padded numbering for filesystem sortability. The registry
auto-increments by scanning existing files — no separate counter file
to keep in sync.

The on-disk format mirrors cheshire_cat.md §V::

    # ADR-NNN: [Decision]

    ## Context
    [What problem is being decided. What forces are at play.]

    ## Decision
    [What was chosen.]

    ## Tradeoffs
    - [explicit tradeoffs as a bullet list]

    ## Status
    Proposed | Accepted | Superseded by ADR-MMM
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

ADR_DIRNAME = "architecture"
_FILENAME_PATTERN = re.compile(r"^adr-(\d+)-([a-z0-9-]+)\.md$")
_SLUG_NORMALIZE = re.compile(r"[^a-z0-9]+")


class ADRStatus(StrEnum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    SUPERSEDED = "superseded"


class ADRPayload(BaseModel):
    """The structured payload an ADR-producing artifact carries.

    Validation enforces the Cat's discipline: title, context, decision,
    and tradeoffs must all be present and non-empty. The grin is the
    tradeoffs list — explicitly required to have at least one
    substantive entry.
    """

    title: str = Field(min_length=1)
    context: str = Field(min_length=1)
    decision: str = Field(min_length=1)
    tradeoffs: list[str] = Field(min_length=1)
    status: ADRStatus = ADRStatus.PROPOSED
    superseded_by: int | None = None

    @field_validator("tradeoffs")
    @classmethod
    def _tradeoffs_must_have_substance(cls, v: list[str]) -> list[str]:
        if not any(item.strip() for item in v):
            raise ValueError(
                "tradeoffs must contain at least one non-empty entry — the grin is non-optional"
            )
        return v


@dataclass(frozen=True)
class ADRRecord:
    number: int
    slug: str
    title: str
    path: Path

    def read(self) -> str:
        return self.path.read_text(encoding="utf-8")


def slugify(text: str) -> str:
    """Convert text to a lowercase, dash-separated, ASCII-safe slug."""
    slug = _SLUG_NORMALIZE.sub("-", text.lower()).strip("-")
    return slug or "untitled"


def render_adr(number: int, payload: ADRPayload) -> str:
    """Render an ADRPayload as the markdown that will land on disk."""
    lines: list[str] = [
        f"# ADR-{number:03d}: {payload.title}",
        "",
        "## Context",
        "",
        payload.context.rstrip(),
        "",
        "## Decision",
        "",
        payload.decision.rstrip(),
        "",
        "## Tradeoffs",
        "",
    ]
    lines.extend(f"- {tradeoff}" for tradeoff in payload.tradeoffs)
    lines.append("")
    lines.append("## Status")
    lines.append("")
    if payload.status is ADRStatus.SUPERSEDED and payload.superseded_by is not None:
        lines.append(f"Superseded by ADR-{payload.superseded_by:03d}")
    else:
        lines.append(payload.status.value.capitalize())
    lines.append("")
    return "\n".join(lines)


class ADRRegistry:
    """Read/write registry over ``<project_root>/.wonderland/architecture/``.

    The registry is the single point of truth for ADR numbering — there
    is no separate counter file to drift from the directory contents.
    Numbers are derived by scanning existing files; the next number is
    one greater than the highest existing.
    """

    def __init__(self, project_root: Path) -> None:
        self._root = project_root / ".wonderland" / ADR_DIRNAME

    @property
    def path(self) -> Path:
        return self._root

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #

    def list_adrs(self) -> list[ADRRecord]:
        """Every ADR in the directory, sorted by number ascending."""
        if not self._root.is_dir():
            return []
        records: list[ADRRecord] = []
        for entry in self._root.iterdir():
            if not entry.is_file():
                continue
            record = self._record_from_path(entry)
            if record is not None:
                records.append(record)
        records.sort(key=lambda r: r.number)
        return records

    def next_number(self) -> int:
        existing = self.list_adrs()
        if not existing:
            return 1
        return max(r.number for r in existing) + 1

    def find_by_slug(self, slug: str) -> ADRRecord | None:
        for record in self.list_adrs():
            if record.slug == slug:
                return record
        return None

    def find_by_number(self, number: int) -> ADRRecord | None:
        for record in self.list_adrs():
            if record.number == number:
                return record
        return None

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #

    def write(self, payload: ADRPayload | dict) -> ADRRecord:
        """Persist `payload` as the next ADR. Returns the record written.

        Validation happens here: ``payload`` is parsed as ``ADRPayload``
        if a dict is passed; the Pydantic model enforces the discipline
        (non-empty title/context/decision/tradeoffs).
        """
        validated = (
            payload if isinstance(payload, ADRPayload) else ADRPayload.model_validate(payload)
        )

        number = self.next_number()
        slug = slugify(validated.title)
        filename = f"adr-{number:03d}-{slug}.md"
        full_path = self._root / filename

        self._root.mkdir(parents=True, exist_ok=True)
        full_path.write_text(render_adr(number, validated), encoding="utf-8")

        return ADRRecord(
            number=number,
            slug=slug,
            title=validated.title,
            path=full_path,
        )

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    @staticmethod
    def _record_from_path(path: Path) -> ADRRecord | None:
        match = _FILENAME_PATTERN.match(path.name)
        if not match:
            return None
        number = int(match.group(1))
        slug = match.group(2)
        title = ADRRegistry._title_from_file(path, fallback=slug)
        return ADRRecord(number=number, slug=slug, title=title, path=path)

    @staticmethod
    def _title_from_file(path: Path, *, fallback: str) -> str:
        """Read the H1 line and extract the title after the 'ADR-NNN: ' prefix.

        Falls back to the slug if the file is unreadable or malformed —
        the registry shouldn't fail just because someone hand-edited a
        file.
        """
        try:
            with path.open(encoding="utf-8") as f:
                first_line = f.readline().strip()
        except OSError:
            return fallback
        if not first_line.startswith("# ADR-") or ":" not in first_line:
            return fallback
        return first_line.split(":", 1)[1].strip() or fallback
