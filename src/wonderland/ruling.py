"""Ruling writer + registry — the Queen of Hearts' artifact.

Per WONDERLAND_SPEC §9 / queen_of_hearts.md §V. The Queen issues
**rulings** — determinations on security and compliance, not opinions.
Each ruling carries a severity (critical / high / medium / low /
informational), a domain (authentication, secret-handling, etc.), a
specific finding, required remediation, and observable acceptance
criteria.

The grin equivalent is **citation**: per queen_of_hearts.md §VIII,
"rulings without citation are not rulings, they are opinions." The
schema rejects empty-citation rulings as a structural guard against
the Caprice failure mode the constitution actively names. Every
ruling must reference a specific threat, compliance requirement, or
known vulnerability class.

Storage at ``<project_root>/.wonderland/rulings/ruling-NNN-slug.md``,
mirroring the ADR / Ticket / Story / Escalation / TestScenario /
Review registries.
"""

from __future__ import annotations

import contextlib
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from wonderland.adr import slugify

RULINGS_DIRNAME = "rulings"
_FILENAME_PATTERN = re.compile(r"^ruling-(\d+)-([a-z0-9-]+)\.md$")


class RulingSeverity(StrEnum):
    """Severity classes per queen_of_hearts.md §V.

    Precise on purpose — §VIII names "severity inflation" (labeling
    everything critical to ensure attention) and severity deflation
    (shipping incidents) as twin failure modes. Accuracy is the
    discipline.
    """

    CRITICAL = "critical"
    """Ship-blocking. Active or imminent harm. No negotiation on remediation."""
    HIGH = "high"
    """Must be remediated before next release. Significant harm if exploited."""
    MEDIUM = "medium"
    """Must be remediated within a defined window. Real but bounded risk."""
    LOW = "low"
    """Should be remediated. Compounding risk; left unfixed indefinitely, becomes high."""
    INFORMATIONAL = "informational"
    """No immediate action required, but recorded for future reference."""


class RulingDomain(StrEnum):
    """Domain classes per queen_of_hearts.md §V.

    The specific compliance framework (GDPR, HIPAA, SOC 2, etc.)
    when relevant goes into ``compliance_implications`` rather than
    proliferating per-framework enum values.
    """

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    SECRET_HANDLING = "secret-handling"
    DATA_HANDLING = "data-handling"
    INPUT_VALIDATION = "input-validation"
    LOGGING_AND_AUDIT = "logging-and-audit"
    DEPENDENCIES = "dependencies"
    NETWORK = "network"
    CRYPTOGRAPHY = "cryptography"
    PRIVACY = "privacy"
    COMPLIANCE = "compliance"
    """Generic; the specific framework goes in ``compliance_implications``."""


class RulingPayload(BaseModel):
    """Structured payload the Queen attaches to a ruling utterance.

    Validation enforces the Queen's discipline:

    - title, finding, required_remediation: all required and non-empty.
      A ruling with no specific finding is not yet a ruling.
    - severity, domain: required enums. Untriaged severity is the
      §VIII failure mode this enforces structurally.
    - **citation**: required, non-empty. The grin equivalent — per
      §VIII, "rulings without citation are not rulings, they are
      opinions." The schema rejects opinion-shaped rulings before
      they can hit the bus.
    - acceptance_criteria: at least one observable, testable
      condition. Without it, "remediation complete" is unfalsifiable.
    - source, residual_risk, compliance_implications,
      audit_reference: optional context fields.
    """

    title: str = Field(min_length=1)
    severity: RulingSeverity
    domain: RulingDomain
    source: str = ""
    """What triggered this ruling — proposal / implementation /
    observation / scenario / etc."""
    citation: str = ""
    """The threat model, compliance requirement, or vulnerability
    class this ruling references. Specific. Named. Referenceable.
    The grin equivalent: §VIII names "Caprice" (rulings without
    citation) as the failure mode this field exists to prevent.
    Validated below — empty/whitespace rejected with the §VIII message."""
    finding: str = Field(min_length=1)
    """What is wrong, what would happen if shipped as-is, who is
    harmed and how."""
    required_remediation: str = Field(min_length=1)
    """What must be true for this to be acceptable. Specific enough
    that the Tweedles know what they're aiming for; agnostic enough
    that they retain authority over implementation choices."""
    acceptance_criteria: list[str] = Field(min_length=1)
    """How the Queen will know the remediation is complete.
    Observable. Testable."""
    residual_risk: str = ""
    """What remains after remediation, with reasoning for why it is
    acceptable."""
    compliance_implications: str = ""
    """If this ruling stems from or affects a compliance framework
    (GDPR, HIPAA, SOC 2, etc.), name the framework, the specific
    requirement, and the relationship."""
    audit_reference: str = ""
    """The audit-trail entry this ruling will produce. The system's
    defense is partly the existence of this record."""

    @field_validator("citation")
    @classmethod
    def _citation_must_have_substance(cls, v: str) -> str:
        if not v.strip():
            raise ValueError(
                "citation must be non-empty — rulings without citation are "
                "opinions (§VIII: Caprice). Cite the specific threat, "
                "compliance requirement, or known vulnerability class."
            )
        return v

    @field_validator("acceptance_criteria")
    @classmethod
    def _acceptance_must_have_substance(cls, v: list[str]) -> list[str]:
        if not any(item.strip() for item in v):
            raise ValueError(
                "acceptance_criteria must contain at least one observable, "
                "testable condition — without it, 'remediation complete' is "
                "unfalsifiable."
            )
        return v


@dataclass(frozen=True)
class RulingRecord:
    number: int
    slug: str
    title: str
    severity: RulingSeverity
    domain: RulingDomain
    path: Path

    def read(self) -> str:
        return self.path.read_text(encoding="utf-8")


def render_ruling(number: int, payload: RulingPayload) -> str:
    """Render a RulingPayload as the markdown that lands on disk.

    Format mirrors queen_of_hearts.md §V exactly so a human reading
    the file sees what the spec says a Ruling should look like.
    """
    lines: list[str] = [
        f"## Ruling {number:03d}: {payload.title}",
        "",
        f"**Severity:** {payload.severity.value}",
        f"**Domain:** {payload.domain.value}",
    ]
    if payload.source.strip():
        lines.append(f"**Source:** {payload.source.rstrip()}")
    lines.extend(
        [
            "",
            "**Citation:**",
            "",
            payload.citation.rstrip(),
            "",
            "**Finding:**",
            "",
            payload.finding.rstrip(),
            "",
            "**Required Remediation:**",
            "",
            payload.required_remediation.rstrip(),
            "",
            "**Acceptance Criteria:**",
        ]
    )
    lines.extend(f"- {item}" for item in payload.acceptance_criteria)
    lines.append("")
    if payload.residual_risk.strip():
        lines.extend(
            [
                "**Residual Risk:**",
                "",
                payload.residual_risk.rstrip(),
                "",
            ]
        )
    if payload.compliance_implications.strip():
        lines.extend(
            [
                "**Compliance Implications:**",
                "",
                payload.compliance_implications.rstrip(),
                "",
            ]
        )
    if payload.audit_reference.strip():
        lines.extend(
            [
                "**Audit Reference:**",
                "",
                payload.audit_reference.rstrip(),
                "",
            ]
        )
    return "\n".join(lines)


class RulingRegistry:
    """Read/write registry over ``<project_root>/.wonderland/rulings/``.

    Same shape as the other registries: numbering from filesystem scan,
    tolerant of non-ruling files in the directory, slug derived from
    the title.
    """

    def __init__(self, project_root: Path) -> None:
        self._root = project_root / ".wonderland" / RULINGS_DIRNAME

    @property
    def path(self) -> Path:
        return self._root

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #

    def list_rulings(self) -> list[RulingRecord]:
        if not self._root.is_dir():
            return []
        records: list[RulingRecord] = []
        for entry in self._root.iterdir():
            if not entry.is_file():
                continue
            record = self._record_from_path(entry)
            if record is not None:
                records.append(record)
        records.sort(key=lambda r: r.number)
        return records

    def next_number(self) -> int:
        existing = self.list_rulings()
        if not existing:
            return 1
        return max(r.number for r in existing) + 1

    def find_by_slug(self, slug: str) -> RulingRecord | None:
        for record in self.list_rulings():
            if record.slug == slug:
                return record
        return None

    def find_by_number(self, number: int) -> RulingRecord | None:
        for record in self.list_rulings():
            if record.number == number:
                return record
        return None

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #

    def write(self, payload: RulingPayload | dict) -> RulingRecord:
        validated = (
            payload
            if isinstance(payload, RulingPayload)
            else RulingPayload.model_validate(payload)
        )

        number = self.next_number()
        slug = slugify(validated.title)
        filename = f"ruling-{number:03d}-{slug}.md"
        full_path = self._root / filename

        self._root.mkdir(parents=True, exist_ok=True)
        full_path.write_text(render_ruling(number, validated), encoding="utf-8")

        return RulingRecord(
            number=number,
            slug=slug,
            title=validated.title,
            severity=validated.severity,
            domain=validated.domain,
            path=full_path,
        )

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    @staticmethod
    def _record_from_path(path: Path) -> RulingRecord | None:
        match = _FILENAME_PATTERN.match(path.name)
        if not match:
            return None
        number = int(match.group(1))
        slug = match.group(2)
        title, severity, domain = RulingRegistry._read_header(path, fallback_title=slug)
        return RulingRecord(
            number=number,
            slug=slug,
            title=title,
            severity=severity,
            domain=domain,
            path=path,
        )

    @staticmethod
    def _read_header(
        path: Path, *, fallback_title: str
    ) -> tuple[str, RulingSeverity, RulingDomain]:
        title = fallback_title
        severity = RulingSeverity.INFORMATIONAL  # safe default if the file is malformed
        domain = RulingDomain.COMPLIANCE
        try:
            with path.open(encoding="utf-8") as f:
                lines = [f.readline() for _ in range(8)]
        except OSError:
            return title, severity, domain

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("## Ruling") and ":" in stripped:
                title = stripped.split(":", 1)[1].strip() or fallback_title
            if stripped.startswith("**Severity:**"):
                value = stripped.removeprefix("**Severity:**").strip()
                with contextlib.suppress(ValueError):
                    severity = RulingSeverity(value)
            if stripped.startswith("**Domain:**"):
                value = stripped.removeprefix("**Domain:**").strip()
                with contextlib.suppress(ValueError):
                    domain = RulingDomain(value)
        return title, severity, domain


__all__ = [
    "RULINGS_DIRNAME",
    "RulingDomain",
    "RulingPayload",
    "RulingRecord",
    "RulingRegistry",
    "RulingSeverity",
    "render_ruling",
]
