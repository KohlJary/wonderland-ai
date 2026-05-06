"""Contract Note writer + registry — the Tweedles' negotiation artifact.

Per the Tweedle Pair Protocol §II ("The Contract Is the Seam") and §IV
("Contract change request"), the Contract Note is how the Tweedles
explicitly negotiate changes to the contract that sits at the
frontend/backend seam. Without a Contract Note, contract changes drift
silently — analysis 007's Tweedle Dance showed exactly this failure
mode: the pair converged on substantive contract decisions in
utterance bodies but never transitioned to shipping because the
framework had no explicit "we have agreed; now ship" inflection point.

The Contract Note adds that inflection point as a versioned, on-disk
artifact. Each note carries the proposed change, both sides' impact
assessments, and a state in `proposed → counterpart_assessed → agreed`
(or `escalated` / `deferred`). When state reaches `agreed`, a
contract version is locked and subsequent ImplementationPayload
records can reference that locked version explicitly via their
`contract` field.

The grin equivalent here is **proposed_change**: a Contract Note that
doesn't name a specific proposed change is just a discussion. The
schema rejects empty proposals so the artifact stays load-bearing.

Storage at ``<project_root>/.wonderland/contract-notes/contract-note-NNN-slug.md``,
mirroring the other registries. Mutability is intentional: a single
note progresses through states as the pair negotiates, rather than
forcing each transition to be a new file. This keeps the per-contract
audit trail in one place where downstream consumers (the
Implementation registry, the Cat on escalation) can find it.
"""

from __future__ import annotations

import contextlib
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from wonderland.adr import slugify

CONTRACT_NOTES_DIRNAME = "contract-notes"
_FILENAME_PATTERN = re.compile(r"^contract-note-(\d+)-([a-z0-9-]+)\.md$")


class ContractNoteState(StrEnum):
    """Where a Contract Note sits in the negotiation workflow.

    - PROPOSED: initiator has published the note with their side's
      impact filled. Counterpart has not yet responded.
    - COUNTERPART_ASSESSED: counterpart has filled in their side's
      impact. Either side can now mark agreed or escalate.
    - AGREED: both sides accept. ``contract_version`` is locked and
      ImplementationPayload.contract should reference it.
    - ESCALATED: the pair could not agree; the Cat is being asked
      to rule on the architectural implication.
    - DEFERRED: the change is not happening in this iteration. The
      note stays on disk so the next negotiation can build on it.
    """

    PROPOSED = "proposed"
    COUNTERPART_ASSESSED = "counterpart_assessed"
    AGREED = "agreed"
    ESCALATED = "escalated"
    DEFERRED = "deferred"


class ContractNotePayload(BaseModel):
    """Structured payload a Tweedle attaches to a contract_note utterance.

    Field discipline reflects the Pair Protocol §IV workflow:

    - **proposed_change**: the grin equivalent. Required, non-empty.
      A Contract Note without a specific proposed change is just
      discussion — the schema rejects empty proposals with the §II
      message.
    - **current_shape**: the contract as it stands today (version,
      schema, envelope shape, whatever). Lets the reader tell what
      is changing.
    - **source**: who or what surfaced the need for this change
      (a story, a ticket, a bug-at-the-seam, a user observation).
      Required-by-validator — anonymous "we should change X" notes
      drift into bikeshedding.
    - **frontend_impact / backend_impact**: each side's assessment
      of what the change means for their layer. The proposer fills
      in their side; the counterpart fills in theirs. Both fields
      are optional at the schema level so the note can land in
      ``state=proposed`` with one filled.
    - **contract_version**: locked when state transitions to AGREED.
      Empty until then.
    - **resolution**: how the negotiation concluded — what got
      agreed, what got escalated, what got deferred and why.
      Populated when state moves to a terminal state.
    """

    title: str = Field(min_length=1)
    proposed_change: str = ""
    """What's being proposed. The grin equivalent — required-by-validator.
    A Contract Note without a specific proposed change is just discussion."""
    current_shape: str = ""
    """The contract as it stands today. Required-by-validator so the
    reader can tell what is changing."""
    source: str = ""
    """Who or what surfaced the need for this change. Required-by-validator
    — anonymous proposals drift into bikeshedding."""
    frontend_impact: str = ""
    """Tweedledee's assessment of what this change means for the frontend
    layer. Empty when the proposer is the backend Tweedle and the frontend
    has not yet responded."""
    backend_impact: str = ""
    """Tweedledum's assessment of what this change means for the backend
    layer. Empty when the proposer is the frontend Tweedle and the
    backend has not yet responded."""
    state: ContractNoteState = ContractNoteState.PROPOSED
    contract_version: str = ""
    """Locked when state transitions to AGREED. Empty until then. The
    string format is the pair's choice (e.g., 'message-envelope v3',
    'OpenAPI rev 2026-05-05', 'GraphQL schema 2.1.0')."""
    resolution: str = ""
    """How the negotiation concluded. Populated when state moves to a
    terminal state (AGREED / ESCALATED / DEFERRED)."""

    @field_validator("proposed_change")
    @classmethod
    def _proposed_change_required(cls, v: str) -> str:
        if not v.strip():
            raise ValueError(
                "proposed_change must be non-empty — a Contract Note without "
                "a specific proposed change is just discussion. Per the "
                "Tweedle Pair Protocol §II, the contract is the seam; if "
                "you don't have a concrete change to propose, raise a "
                "concern instead."
            )
        return v

    @field_validator("current_shape")
    @classmethod
    def _current_shape_required(cls, v: str) -> str:
        if not v.strip():
            raise ValueError(
                "current_shape must be non-empty — name the contract as it "
                "stands today (envelope version, schema rev, RPC shape, "
                "etc.) so the reader can tell what is changing."
            )
        return v

    @field_validator("source")
    @classmethod
    def _source_required(cls, v: str) -> str:
        if not v.strip():
            raise ValueError(
                "source must be non-empty — name the story, ticket, bug, "
                "or observation that surfaced this. Anonymous 'we should "
                "change X' notes drift into bikeshedding."
            )
        return v


@dataclass(frozen=True)
class ContractNoteRecord:
    number: int
    slug: str
    title: str
    state: ContractNoteState
    contract_version: str
    path: Path

    def read(self) -> str:
        return self.path.read_text(encoding="utf-8")


def render_contract_note(number: int, payload: ContractNotePayload) -> str:
    """Render a ContractNotePayload as the markdown that lands on disk.

    Format mirrors the per-Tweedle §V layout: header carries the
    discriminating fields (state, contract_version) for fast scanning;
    body has Current Shape / Proposed Change / Source / Frontend Impact
    / Backend Impact / Resolution sections.
    """
    lines: list[str] = [
        f"## Contract Note {number:03d}: {payload.title}",
        "",
        f"**State:** {payload.state.value}",
        f"**Contract Version:** {payload.contract_version or '(unlocked)'}",
        "",
        "**Current Shape:**",
        "",
        payload.current_shape.rstrip(),
        "",
        "**Proposed Change:**",
        "",
        payload.proposed_change.rstrip(),
        "",
        f"**Source:** {payload.source}",
        "",
    ]
    if payload.frontend_impact.strip():
        lines.extend(
            [
                "**Frontend Impact (Tweedledee):**",
                "",
                payload.frontend_impact.rstrip(),
                "",
            ]
        )
    else:
        lines.extend(
            [
                "**Frontend Impact (Tweedledee):** _pending_",
                "",
            ]
        )
    if payload.backend_impact.strip():
        lines.extend(
            [
                "**Backend Impact (Tweedledum):**",
                "",
                payload.backend_impact.rstrip(),
                "",
            ]
        )
    else:
        lines.extend(
            [
                "**Backend Impact (Tweedledum):** _pending_",
                "",
            ]
        )
    if payload.resolution.strip():
        lines.extend(
            [
                "**Resolution:**",
                "",
                payload.resolution.rstrip(),
                "",
            ]
        )
    return "\n".join(lines)


class ContractNoteRegistry:
    """Read/write registry over ``<project_root>/.wonderland/contract-notes/``.

    Same shape as the other registries plus a mutating ``update`` method.
    Mutability is intentional: a single note progresses through states
    as the pair negotiates, rather than forcing each transition to be
    a new file. This keeps the per-contract audit trail in one place.
    """

    def __init__(self, project_root: Path) -> None:
        self._root = project_root / ".wonderland" / CONTRACT_NOTES_DIRNAME

    @property
    def path(self) -> Path:
        return self._root

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #

    def list_contract_notes(self) -> list[ContractNoteRecord]:
        if not self._root.is_dir():
            return []
        records: list[ContractNoteRecord] = []
        for entry in self._root.iterdir():
            if not entry.is_file():
                continue
            record = self._record_from_path(entry)
            if record is not None:
                records.append(record)
        records.sort(key=lambda r: r.number)
        return records

    def next_number(self) -> int:
        existing = self.list_contract_notes()
        if not existing:
            return 1
        return max(r.number for r in existing) + 1

    def find_by_slug(self, slug: str) -> ContractNoteRecord | None:
        for record in self.list_contract_notes():
            if record.slug == slug:
                return record
        return None

    def find_by_number(self, number: int) -> ContractNoteRecord | None:
        for record in self.list_contract_notes():
            if record.number == number:
                return record
        return None

    def read_payload(self, slug: str) -> ContractNotePayload | None:
        """Reconstruct the full payload from disk for a given slug.

        Used by ``update`` to round-trip and by callers that want the
        full negotiation context, not just the header. Returns None if
        the slug doesn't exist.
        """
        record = self.find_by_slug(slug)
        if record is None:
            return None
        return _parse_payload(record.path, record.title)

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #

    def write(self, payload: ContractNotePayload | dict) -> ContractNoteRecord:
        validated = (
            payload
            if isinstance(payload, ContractNotePayload)
            else ContractNotePayload.model_validate(payload)
        )

        number = self.next_number()
        slug = slugify(validated.title)
        filename = f"contract-note-{number:03d}-{slug}.md"
        full_path = self._root / filename

        self._root.mkdir(parents=True, exist_ok=True)
        full_path.write_text(render_contract_note(number, validated), encoding="utf-8")

        return ContractNoteRecord(
            number=number,
            slug=slug,
            title=validated.title,
            state=validated.state,
            contract_version=validated.contract_version,
            path=full_path,
        )

    def update(
        self,
        slug: str,
        *,
        frontend_impact: str | None = None,
        backend_impact: str | None = None,
        state: ContractNoteState | None = None,
        contract_version: str | None = None,
        resolution: str | None = None,
    ) -> ContractNoteRecord:
        """Mutate an existing Contract Note in place.

        Used to fill in the counterpart's impact, transition state, and
        lock a contract version when the negotiation reaches AGREED.
        Raises KeyError if the slug doesn't exist; raises ValueError if
        the resulting payload is invalid (e.g., the proposed_change
        somehow got cleared).
        """
        existing = self.read_payload(slug)
        if existing is None:
            raise KeyError(f"No Contract Note with slug {slug!r}")

        updated = existing.model_copy(
            update={
                k: v
                for k, v in {
                    "frontend_impact": frontend_impact,
                    "backend_impact": backend_impact,
                    "state": state,
                    "contract_version": contract_version,
                    "resolution": resolution,
                }.items()
                if v is not None
            }
        )

        record = self.find_by_slug(slug)
        assert record is not None  # we just read it via read_payload
        record.path.write_text(render_contract_note(record.number, updated), encoding="utf-8")

        return ContractNoteRecord(
            number=record.number,
            slug=record.slug,
            title=updated.title,
            state=updated.state,
            contract_version=updated.contract_version,
            path=record.path,
        )

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    @staticmethod
    def _record_from_path(path: Path) -> ContractNoteRecord | None:
        match = _FILENAME_PATTERN.match(path.name)
        if not match:
            return None
        number = int(match.group(1))
        slug = match.group(2)
        title, state, contract_version = ContractNoteRegistry._read_header(
            path, fallback_title=slug
        )
        return ContractNoteRecord(
            number=number,
            slug=slug,
            title=title,
            state=state,
            contract_version=contract_version,
            path=path,
        )

    @staticmethod
    def _read_header(path: Path, *, fallback_title: str) -> tuple[str, ContractNoteState, str]:
        title = fallback_title
        state = ContractNoteState.PROPOSED
        contract_version = ""
        try:
            with path.open(encoding="utf-8") as f:
                lines = [f.readline() for _ in range(6)]
        except OSError:
            return title, state, contract_version

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("## Contract Note") and ":" in stripped:
                title = stripped.split(":", 1)[1].strip() or fallback_title
            if stripped.startswith("**State:**"):
                value = stripped.removeprefix("**State:**").strip()
                with contextlib.suppress(ValueError):
                    state = ContractNoteState(value)
            if stripped.startswith("**Contract Version:**"):
                value = stripped.removeprefix("**Contract Version:**").strip()
                contract_version = "" if value == "(unlocked)" else value
        return title, state, contract_version


def _parse_payload(path: Path, fallback_title: str) -> ContractNotePayload:
    """Reconstruct a ContractNotePayload from a rendered file on disk.

    Round-trips render_contract_note. Used by ContractNoteRegistry.update
    and by callers that need the full negotiation context.
    """
    text = path.read_text(encoding="utf-8")

    title = fallback_title
    state = ContractNoteState.PROPOSED
    contract_version = ""
    source = ""
    sections: dict[str, list[str]] = {}
    current_section: str | None = None

    section_headers = {
        "**Current Shape:**": "current_shape",
        "**Proposed Change:**": "proposed_change",
        "**Frontend Impact (Tweedledee):**": "frontend_impact",
        "**Backend Impact (Tweedledum):**": "backend_impact",
        "**Resolution:**": "resolution",
    }

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("## Contract Note") and ":" in stripped:
            title = stripped.split(":", 1)[1].strip() or fallback_title
            current_section = None
            continue
        if stripped.startswith("**State:**"):
            value = stripped.removeprefix("**State:**").strip()
            with contextlib.suppress(ValueError):
                state = ContractNoteState(value)
            current_section = None
            continue
        if stripped.startswith("**Contract Version:**"):
            value = stripped.removeprefix("**Contract Version:**").strip()
            contract_version = "" if value == "(unlocked)" else value
            current_section = None
            continue
        if stripped.startswith("**Source:**"):
            source = stripped.removeprefix("**Source:**").strip()
            current_section = None
            continue
        if stripped in section_headers:
            current_section = section_headers[stripped]
            sections.setdefault(current_section, [])
            continue
        # Inline "_pending_" markers are not section content.
        if stripped.endswith("_pending_") and stripped.startswith("**"):
            current_section = None
            continue
        if stripped.startswith("**") and stripped.endswith(":**"):
            # Some other bold header — close the current section.
            current_section = None
            continue
        if current_section is not None:
            sections.setdefault(current_section, []).append(raw_line)

    def _join(name: str) -> str:
        return "\n".join(sections.get(name, [])).strip()

    return ContractNotePayload(
        title=title,
        current_shape=_join("current_shape") or "(missing)",
        proposed_change=_join("proposed_change") or "(missing)",
        source=source or "(missing)",
        frontend_impact=_join("frontend_impact"),
        backend_impact=_join("backend_impact"),
        state=state,
        contract_version=contract_version,
        resolution=_join("resolution"),
    )


__all__ = [
    "CONTRACT_NOTES_DIRNAME",
    "ContractNotePayload",
    "ContractNoteRecord",
    "ContractNoteRegistry",
    "ContractNoteState",
    "render_contract_note",
]
