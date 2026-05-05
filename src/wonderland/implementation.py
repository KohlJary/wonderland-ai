"""Implementation writer + registry — the Tweedles' artifact.

Per WONDERLAND_SPEC §9 / tweedledee.md §V / tweedledum.md §V /
tweedle_pair_protocol.md §II. The Tweedles ship code; the
Implementation artifact is the meta-record of what each shipment
contains: which ticket it implements, what contract version it
honors, what side of the seam it sits on, and the side-specific
details the other Tweedle (and the Caterpillar, the Hatter, the
Dormouse) need to reason about the change.

The grin equivalent here is **contract**: per the Pair Protocol §II,
"implicit contracts are bugs in the making." Every implementation
must reference the contract version it honors. The schema rejects
empty contracts with the §II message — an implementation that
doesn't name the seam it's matching is exactly the shape of the
failure mode this field exists to prevent.

A single payload type covers both Tweedles. The ``side`` enum
discriminates frontend vs backend; side-specific fields
(ui_states_implemented + client_state for frontend; invariants +
schema_changes + failure_modes for backend) are optional and
populated per side. This keeps the on-disk artifact stream uniform
while letting each Tweedle's voice show through the populated
fields.

Storage at ``<project_root>/.wonderland/implementations/implementation-NNN-slug.md``,
mirroring the other registries.
"""

from __future__ import annotations

import contextlib
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from wonderland.adr import slugify

IMPLEMENTATIONS_DIRNAME = "implementations"
_FILENAME_PATTERN = re.compile(r"^implementation-(\d+)-([a-z0-9-]+)\.md$")


class ImplementationSide(StrEnum):
    """Which side of the seam this implementation lives on."""

    FRONTEND = "frontend"
    BACKEND = "backend"


class ImplementationPayload(BaseModel):
    """Structured payload a Tweedle attaches to an implementation utterance.

    Validation enforces the pair's discipline:

    - title, ticket_reference, approach_summary: all required and
      non-empty. An implementation must trace to a Rabbit ticket and
      describe what the code actually does. ("I'll handle the realtime
      piece" is not a Tweedle artifact; "wired the message list to the
      WebSocket subscription with a virtual scroll" is.)
    - side: required enum. The discriminator that lets downstream
      consumers (Caterpillar, Hatter, Dormouse) know which fields to
      look for.
    - **contract**: required, non-empty. The grin equivalent — per the
      Pair Protocol §II, implicit contracts are bugs in the making.
      The schema rejects empty-contract implementations with the §II
      message.
    - Side-specific fields (ui_states_implemented + client_state for
      frontend; invariants_enforced + schema_changes +
      failure_modes_handled for backend) are optional. The agent
      protocol guides each Tweedle to populate the fields appropriate
      to their side.
    """

    title: str = Field(min_length=1)
    side: ImplementationSide
    ticket_reference: str = ""
    """The Rabbit ticket slug or number this implementation serves.
    Required-by-validator below."""
    approach_summary: str = ""
    """What the code actually does, in concrete terms. Required-by-validator."""
    contract: str = ""
    """The contract version + shape this implementation honors. The
    grin equivalent — required-by-validator. Per Pair Protocol §II,
    implicit contracts are bugs in the making."""
    files_touched: list[str] = Field(default_factory=list)
    """Paths and brief descriptions of what changed."""
    open_questions_for_pair: list[str] = Field(default_factory=list)
    """Specific questions the other Tweedle should answer before this
    implementation is complete. Surfaced inline so the contract
    negotiation stays explicit."""
    ready_for_review: bool = False
    """Whether the Caterpillar should engage. False means the Tweedle
    is still iterating; True is the explicit review-gate per
    tweedledee.md §VI / tweedledum.md §VI."""
    known_limitations: list[str] = Field(default_factory=list)
    """Things this implementation does not yet handle, with severity
    where helpful."""
    # ----- frontend-specific -----
    ui_states_implemented: list[str] = Field(default_factory=list)
    """Per tweedledee.md §V — named UI states the implementation
    handles (loading / empty / error / offline / stale / etc.)."""
    client_state: str = ""
    """What state lives on the client, why, and how it reconciles
    with canonical server state. Per tweedledee.md §I client state
    is "a small kingdom you are responsible for"."""
    # ----- backend-specific -----
    invariants_enforced: list[str] = Field(default_factory=list)
    """Per tweedledum.md §V — invariants this implementation enforces,
    each named with how (DB constraint, validation, transactional
    boundary, etc.)."""
    schema_changes: str = ""
    """Migrations introduced, with backward-compatibility notes."""
    failure_modes_handled: list[str] = Field(default_factory=list)
    """Per tweedledum.md §V — failure modes addressed, each with the
    handling behavior (retry, dead-letter, propagate, fallback)."""

    @field_validator("ticket_reference")
    @classmethod
    def _ticket_ref_required(cls, v: str) -> str:
        if not v.strip():
            raise ValueError(
                "ticket_reference must be non-empty — implementations must "
                "trace to a Rabbit ticket. If the work isn't ticketed, ask "
                "the Rabbit to ticket it before shipping."
            )
        return v

    @field_validator("approach_summary")
    @classmethod
    def _approach_required(cls, v: str) -> str:
        if not v.strip():
            raise ValueError(
                "approach_summary must be non-empty — describe what the "
                "code actually does. 'I'll handle the realtime piece' is "
                "vague enough that the other Tweedle can't reason about "
                "the contract."
            )
        return v

    @field_validator("contract")
    @classmethod
    def _contract_required(cls, v: str) -> str:
        if not v.strip():
            raise ValueError(
                "contract must be non-empty — implementations without an "
                "explicit contract reference are 'implicit contracts, "
                "bugs in the making' per the Tweedle Pair Protocol §II. "
                "Cite the OpenAPI revision, schema version, message "
                "envelope version, or whatever shape the agreement takes."
            )
        return v


@dataclass(frozen=True)
class ImplementationRecord:
    number: int
    slug: str
    title: str
    side: ImplementationSide
    ticket_reference: str
    contract: str
    ready_for_review: bool
    path: Path

    def read(self) -> str:
        return self.path.read_text(encoding="utf-8")


def render_implementation(number: int, payload: ImplementationPayload) -> str:
    """Render an ImplementationPayload as the markdown that lands on disk.

    Format closely follows tweedledee.md §V and tweedledum.md §V; the
    side-specific sections are emitted per side, so a frontend
    implementation's file shows UI States and Client State while a
    backend implementation's file shows Invariants and Schema Changes.
    """
    lines: list[str] = [
        f"## Implementation {number:03d}: {payload.title}",
        "",
        f"**Side:** {payload.side.value}",
        f"**Ticket:** {payload.ticket_reference}",
        f"**Contract:** {payload.contract}",
        f"**Ready for review:** {'yes' if payload.ready_for_review else 'no'}",
        "",
        "**Approach:**",
        "",
        payload.approach_summary.rstrip(),
        "",
    ]
    if payload.side is ImplementationSide.FRONTEND:
        if payload.ui_states_implemented:
            lines.append("**UI States Implemented:**")
            lines.extend(f"- {item}" for item in payload.ui_states_implemented)
            lines.append("")
        if payload.client_state.strip():
            lines.extend(
                [
                    "**Client State:**",
                    "",
                    payload.client_state.rstrip(),
                    "",
                ]
            )
    else:
        if payload.invariants_enforced:
            lines.append("**Invariants Enforced:**")
            lines.extend(f"- {item}" for item in payload.invariants_enforced)
            lines.append("")
        if payload.schema_changes.strip():
            lines.extend(
                [
                    "**Schema Changes:**",
                    "",
                    payload.schema_changes.rstrip(),
                    "",
                ]
            )
        if payload.failure_modes_handled:
            lines.append("**Failure Modes Handled:**")
            lines.extend(f"- {item}" for item in payload.failure_modes_handled)
            lines.append("")
    if payload.files_touched:
        lines.append("**Files:**")
        lines.extend(f"- {item}" for item in payload.files_touched)
        lines.append("")
    if payload.open_questions_for_pair:
        lines.append("**Open Questions for Pair:**")
        lines.extend(f"- {item}" for item in payload.open_questions_for_pair)
        lines.append("")
    if payload.known_limitations:
        lines.append("**Known Limitations:**")
        lines.extend(f"- {item}" for item in payload.known_limitations)
        lines.append("")
    return "\n".join(lines)


class ImplementationRegistry:
    """Read/write registry over ``<project_root>/.wonderland/implementations/``.

    Same shape as the other registries: numbering from filesystem scan,
    tolerant of non-implementation files in the directory, slug derived
    from the title. Both Tweedles write to the same registry; the
    ``side`` field on each record discriminates frontend vs backend.
    """

    def __init__(self, project_root: Path) -> None:
        self._root = project_root / ".wonderland" / IMPLEMENTATIONS_DIRNAME

    @property
    def path(self) -> Path:
        return self._root

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #

    def list_implementations(self) -> list[ImplementationRecord]:
        if not self._root.is_dir():
            return []
        records: list[ImplementationRecord] = []
        for entry in self._root.iterdir():
            if not entry.is_file():
                continue
            record = self._record_from_path(entry)
            if record is not None:
                records.append(record)
        records.sort(key=lambda r: r.number)
        return records

    def next_number(self) -> int:
        existing = self.list_implementations()
        if not existing:
            return 1
        return max(r.number for r in existing) + 1

    def find_by_slug(self, slug: str) -> ImplementationRecord | None:
        for record in self.list_implementations():
            if record.slug == slug:
                return record
        return None

    def find_by_number(self, number: int) -> ImplementationRecord | None:
        for record in self.list_implementations():
            if record.number == number:
                return record
        return None

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #

    def write(self, payload: ImplementationPayload | dict) -> ImplementationRecord:
        validated = (
            payload
            if isinstance(payload, ImplementationPayload)
            else ImplementationPayload.model_validate(payload)
        )

        number = self.next_number()
        slug = slugify(validated.title)
        filename = f"implementation-{number:03d}-{slug}.md"
        full_path = self._root / filename

        self._root.mkdir(parents=True, exist_ok=True)
        full_path.write_text(render_implementation(number, validated), encoding="utf-8")

        return ImplementationRecord(
            number=number,
            slug=slug,
            title=validated.title,
            side=validated.side,
            ticket_reference=validated.ticket_reference,
            contract=validated.contract,
            ready_for_review=validated.ready_for_review,
            path=full_path,
        )

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    @staticmethod
    def _record_from_path(path: Path) -> ImplementationRecord | None:
        match = _FILENAME_PATTERN.match(path.name)
        if not match:
            return None
        number = int(match.group(1))
        slug = match.group(2)
        title, side, ticket, contract, ready = ImplementationRegistry._read_header(
            path, fallback_title=slug
        )
        return ImplementationRecord(
            number=number,
            slug=slug,
            title=title,
            side=side,
            ticket_reference=ticket,
            contract=contract,
            ready_for_review=ready,
            path=path,
        )

    @staticmethod
    def _read_header(
        path: Path, *, fallback_title: str
    ) -> tuple[str, ImplementationSide, str, str, bool]:
        title = fallback_title
        side = ImplementationSide.BACKEND  # safe default
        ticket = ""
        contract = ""
        ready = False
        try:
            with path.open(encoding="utf-8") as f:
                lines = [f.readline() for _ in range(8)]
        except OSError:
            return title, side, ticket, contract, ready

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("## Implementation") and ":" in stripped:
                title = stripped.split(":", 1)[1].strip() or fallback_title
            if stripped.startswith("**Side:**"):
                value = stripped.removeprefix("**Side:**").strip()
                with contextlib.suppress(ValueError):
                    side = ImplementationSide(value)
            if stripped.startswith("**Ticket:**"):
                ticket = stripped.removeprefix("**Ticket:**").strip()
            if stripped.startswith("**Contract:**"):
                contract = stripped.removeprefix("**Contract:**").strip()
            if stripped.startswith("**Ready for review:**"):
                value = stripped.removeprefix("**Ready for review:**").strip().lower()
                ready = value == "yes"
        return title, side, ticket, contract, ready


__all__ = [
    "IMPLEMENTATIONS_DIRNAME",
    "ImplementationPayload",
    "ImplementationRecord",
    "ImplementationRegistry",
    "ImplementationSide",
    "render_implementation",
]
