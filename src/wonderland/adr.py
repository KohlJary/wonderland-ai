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

from wonderland.artifact_guid import new_artifact_guid, short_guid

ADR_DIRNAME = "architecture"
# T-g3: filename's id-part is either an 8-char ULID prefix (new) or
# a 1-4 digit legacy number (pre-P18).
_FILENAME_PATTERN = re.compile(
    r"^adr-(?P<id>[0-9A-HJKMNP-TV-Z]{8}|\d{1,4})-(?P<slug>[a-z0-9-]+)\.md$"
)
_GUID_PATTERN = re.compile(r"^\*\*GUID:\*\*\s*([0-9A-HJKMNP-TV-Z]{26})\s*$", re.MULTILINE)
# ADR uses ``# ADR-NNN: Title`` (single hash, dash separator).
_NUMBER_FROM_H1 = re.compile(r"^#\s*ADR-(\d+)\s*:", re.MULTILINE)
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

    guid: str = Field(default_factory=new_artifact_guid)
    """P18 — stable ADR identity. Re-emit with same guid to amend
    (e.g. Cat updates a decision); coining a new guid creates a new
    ADR. ``superseded_by`` should also migrate to guid-based
    references in T-g4."""

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
    guid: str
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
        f"**GUID:** {payload.guid}",
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

    def find_by_guid(self, guid: str) -> ADRRecord | None:
        """P18 T-g2 — primary identity lookup."""
        if not guid:
            return None
        for record in self.list_adrs():
            if record.guid == guid:
                return record
        return None

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

        slug = slugify(validated.title)
        # T-g2: guid-first lookup; slug fallback for back-compat.
        existing = self.find_by_guid(validated.guid)
        if existing is None:
            existing = self.find_by_slug(slug)

        if existing is not None:
            number = existing.number
            full_path = existing.path
        else:
            number = self.next_number()
            # T-g3: filename embeds short_guid for substrate identity.
            filename = f"adr-{short_guid(validated.guid)}-{slug}.md"
            full_path = self._root / filename

        # Preserve existing artifact's guid on slug-fallback match.
        if existing is not None and existing.guid:
            validated = validated.model_copy(update={"guid": existing.guid})

        self._root.mkdir(parents=True, exist_ok=True)
        full_path.write_text(render_adr(number, validated), encoding="utf-8")

        return ADRRecord(
            number=number,
            guid=validated.guid,
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
        id_part = match.group("id")
        slug = match.group("slug")
        title = ADRRegistry._title_from_file(path, fallback=slug)
        guid = ADRRegistry._guid_from_file(path)
        number = ADRRegistry._number_from_file(path, id_part)
        return ADRRecord(
            number=number, guid=guid, slug=slug, title=title, path=path,
        )

    @staticmethod
    def _number_from_file(path: Path, id_part: str) -> int:
        """T-g3 — legacy filenames carried number in the id slot;
        new-shape files keep it only in the H1 header."""
        if id_part.isdigit():
            return int(id_part)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return 0
        m = _NUMBER_FROM_H1.search(text)
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
