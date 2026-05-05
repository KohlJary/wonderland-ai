"""Escalation data + registry — when the Dodo hands a conflict to the human.

Per WONDERLAND_SPEC §7 / dodo.md §V. When multi-agent proposals don't
compose, the Dodo emits an Escalation Brief: a structured handoff
that makes the human's job tractable. The Brief names the specific
decision required (not "what should we do" but "should X happen,
given Y and Z?"), shows each agent's position with reasoning,
suggests the resolution that aligns with the primary-domain agent
(per ``DOMAIN_PRIMACY``), and surfaces the stakes.

Storage at ``<project_root>/.wonderland/escalations/escalation-NNN-<slug>.md``,
mirroring the ADR and Ticket registries. Same single-source-of-truth
approach: numbering derives from filesystem scan, not a counter.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field

from wonderland.adr import slugify

ESCALATIONS_DIRNAME = "escalations"
_FILENAME_PATTERN = re.compile(r"^escalation-(\d+)-([a-z0-9-]+)\.md$")


class AgentProposalSchema(BaseModel):
    """One agent's position as it appears in an Escalation Brief."""

    speaker: str
    position: str
    rationale: str = ""
    domain: str | None = None
    """The agent's domain — informational, useful for the human reading the
    brief to know which lens each agent was looking through."""


class EscalationBrief(BaseModel):
    """The structured handoff per dodo.md §V.

    The LLM-drafted fields (``decision_required``, ``stakes``,
    ``background``) carry the prose; the other fields are derived from
    the Conflict + Resolution that produced the escalation.
    """

    thread_id: str
    decision_required: str = Field(min_length=1)
    agent_proposals: list[AgentProposalSchema] = Field(min_length=2)
    suggested_resolution: str = Field(min_length=1)
    suggested_owner: str | None = None
    suggested_domain: str | None = None
    stakes: str = ""
    background: str = ""


@dataclass(frozen=True)
class EscalationRecord:
    number: int
    slug: str
    title: str
    path: Path

    def read(self) -> str:
        return self.path.read_text(encoding="utf-8")


def render_escalation(number: int, brief: EscalationBrief) -> str:
    """Render an EscalationBrief as the markdown that lands on disk.

    Format mirrors dodo.md §V exactly so a human reading the file sees
    what the spec says an Escalation Brief should look like.
    """
    lines: list[str] = [
        f"## Escalation {number:03d}: {brief.thread_id}",
        "",
        "**Decision Required:**",
        "",
        brief.decision_required.rstrip(),
        "",
        "**Agent Proposals:**",
    ]
    for proposal in brief.agent_proposals:
        domain_suffix = f" ({proposal.domain})" if proposal.domain else ""
        lines.append(f"- **{proposal.speaker}**{domain_suffix}: {proposal.position.rstrip()}")
        if proposal.rationale.strip():
            for rationale_line in proposal.rationale.splitlines():
                lines.append(f"  {rationale_line}")
    lines.append("")
    lines.append("**Suggested Resolution:**")
    lines.append("")
    lines.append(brief.suggested_resolution.rstrip())
    if brief.suggested_owner or brief.suggested_domain:
        owner = brief.suggested_owner or "—"
        domain = brief.suggested_domain or "—"
        lines.append("")
        lines.append(f"*Domain primacy:* `{domain}` → `{owner}`")
    if brief.stakes.strip():
        lines.append("")
        lines.append("**Stakes:**")
        lines.append("")
        lines.append(brief.stakes.rstrip())
    if brief.background.strip():
        lines.append("")
        lines.append("**Background:**")
        lines.append("")
        lines.append(brief.background.rstrip())
    lines.append("")
    return "\n".join(lines)


class EscalationRegistry:
    """Read/write registry over ``<project_root>/.wonderland/escalations/``.

    Same shape as ``ADRRegistry`` / ``TicketRegistry``: numbering from
    filesystem scan, tolerant of non-escalation files in the directory,
    slug derived from the thread_id (or first-line of decision_required
    if thread_id isn't slug-friendly).
    """

    def __init__(self, project_root: Path) -> None:
        self._root = project_root / ".wonderland" / ESCALATIONS_DIRNAME

    @property
    def path(self) -> Path:
        return self._root

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #

    def list_escalations(self) -> list[EscalationRecord]:
        if not self._root.is_dir():
            return []
        records: list[EscalationRecord] = []
        for entry in self._root.iterdir():
            if not entry.is_file():
                continue
            record = self._record_from_path(entry)
            if record is not None:
                records.append(record)
        records.sort(key=lambda r: r.number)
        return records

    def next_number(self) -> int:
        existing = self.list_escalations()
        if not existing:
            return 1
        return max(r.number for r in existing) + 1

    def find_by_slug(self, slug: str) -> EscalationRecord | None:
        for record in self.list_escalations():
            if record.slug == slug:
                return record
        return None

    def find_by_number(self, number: int) -> EscalationRecord | None:
        for record in self.list_escalations():
            if record.number == number:
                return record
        return None

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #

    def write(self, brief: EscalationBrief | dict) -> EscalationRecord:
        validated = (
            brief if isinstance(brief, EscalationBrief) else EscalationBrief.model_validate(brief)
        )

        number = self.next_number()
        slug = self._slug_for(validated)
        filename = f"escalation-{number:03d}-{slug}.md"
        full_path = self._root / filename

        self._root.mkdir(parents=True, exist_ok=True)
        full_path.write_text(render_escalation(number, validated), encoding="utf-8")

        return EscalationRecord(
            number=number,
            slug=slug,
            title=validated.thread_id,
            path=full_path,
        )

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    @staticmethod
    def _slug_for(brief: EscalationBrief) -> str:
        return slugify(brief.thread_id)

    @staticmethod
    def _record_from_path(path: Path) -> EscalationRecord | None:
        match = _FILENAME_PATTERN.match(path.name)
        if not match:
            return None
        number = int(match.group(1))
        slug = match.group(2)
        title = EscalationRegistry._title_from_file(path, fallback=slug)
        return EscalationRecord(number=number, slug=slug, title=title, path=path)

    @staticmethod
    def _title_from_file(path: Path, *, fallback: str) -> str:
        try:
            with path.open(encoding="utf-8") as f:
                first_line = f.readline().strip()
        except OSError:
            return fallback
        if not first_line.startswith("## Escalation") or ":" not in first_line:
            return fallback
        return first_line.split(":", 1)[1].strip() or fallback


__all__ = [
    "AgentProposalSchema",
    "EscalationBrief",
    "EscalationRecord",
    "EscalationRegistry",
    "render_escalation",
]
