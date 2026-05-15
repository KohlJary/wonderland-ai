"""Observation writer + registry — the Dormouse's artifact.

Per WONDERLAND_SPEC §9 / dormouse.md §V. The Dormouse reports
production reality in numbers and intervals, with evidence attached.
He **does not interpret beyond evidence** — the symptom is his; the
hypothesis space belongs to the agents whose domains are implicated.

The grin equivalent is **evidence**: per dormouse.md §VIII, "false
alarms corrode trust" (Crying wolf) and the Dormouse's value comes
from being a trustworthy reporter, which depends on every report
being verifiable. The schema rejects observations with no evidence
entries — an observation that can't be checked is exactly the shape
of the §VIII failure mode this field exists to prevent.

Storage at ``<project_root>/.wonderland/observations/observation-NNN-slug.md``,
mirroring the ADR / Ticket / Story / Escalation / TestScenario /
Review / Ruling registries.
"""

from __future__ import annotations

import contextlib
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from wonderland.adr import slugify
from wonderland.artifact_guid import new_artifact_guid, short_guid

OBSERVATIONS_DIRNAME = "observations"
# T-g3: filename's id-part is either an 8-char ULID prefix (new) or
# a 1-4 digit legacy number (pre-P18).
_FILENAME_PATTERN = re.compile(
    r"^observation-(?P<id>[0-9A-HJKMNP-TV-Z]{8}|\d{1,4})-(?P<slug>[a-z0-9-]+)\.md$"
)
_GUID_PATTERN = re.compile(r"^\*\*GUID:\*\*\s*([0-9A-HJKMNP-TV-Z]{26})\s*$", re.MULTILINE)
_NUMBER_FROM_H2 = re.compile(r"^##\s*Observation\s+(\d+)\s*:", re.MULTILINE)


class ObservationType(StrEnum):
    """Per dormouse.md §V — what kind of observation this is."""

    INCIDENT = "incident"
    """Active or imminent user-visible impact, currently unfolding."""
    ANOMALY = "anomaly"
    """Telemetry departing from baseline; investigation worthwhile, impact unclear."""
    STEADY_STATE = "steady-state"
    """Confirmation that the system is operating within expected parameters."""
    POST_DEPLOY = "post-deploy"
    """Observability sign-off after an implementation lands in production."""
    POST_INCIDENT_CONFIRMATION = "post-incident-confirmation"
    """Confirmation that a remediation has held in production reality."""


class ObservationSeverity(StrEnum):
    """Severity classes per dormouse.md §V.

    Distinct from the Queen's vocabulary — the Dormouse uses sev1/2/3
    because that's the SRE on-call vocabulary the team will pattern-match
    against. Catastrophizing is a §VIII failure mode the Dormouse
    actively guards against; calibration is the discipline.
    """

    SEV1 = "sev1"
    """Active user-visible impact, or active risk of it. Wake the on-call."""
    SEV2 = "sev2"
    """Degraded behavior without active user-visible impact. Investigate within the day."""
    SEV3 = "sev3"
    """Anomaly worth investigating but not requiring immediate response."""
    INFORMATIONAL = "informational"
    """No action required, recorded for context."""


class ObservationPayload(BaseModel):
    """Structured payload the Dormouse attaches to an observation utterance.

    Validation enforces the Dormouse's discipline:

    - title, symptom, affected_scope: all required and non-empty.
      The constitution explicitly rejects "things look bad over
      there" reports — observations are precise or they aren't
      observations.
    - type, severity: required enums. Distinguishing
      incident/anomaly/steady-state/etc. matters because each
      classification implies different team response.
    - **evidence**: at least one substantive entry. The grin
      equivalent — per §VIII, observations without evidence are
      unverifiable, and unverifiable observations are how Crying
      wolf starts. The schema rejects evidence-empty observations
      before they can hit the bus.
    - time_window_start: required (UTC ISO timestamp encouraged).
    - time_window_end: optional (empty means "ongoing").
    - probable_domain, routed_to: optional routing hints — *not*
      diagnosis. The constitution names "Interpreting beyond
      evidence" as a failure mode; these fields keep the routing
      intent explicit while leaving the diagnosis to the implicated
      agent.
    """

    guid: str = Field(default_factory=new_artifact_guid)
    """P18 — stable Observation identity. Dormouse re-emits with
    same guid to amend an observation (e.g. after subsequent
    sleuthing); new guid creates new observation."""

    title: str = Field(min_length=1)
    """Short, neutral — what was seen, not what it means.
    'Translation service error rate spike' not 'Translation service broken'."""
    type: ObservationType
    severity: ObservationSeverity
    time_window_start: str = Field(min_length=1)
    """Start of the observation window, UTC ISO timestamp encouraged."""
    time_window_end: str = ""
    """End of the observation window. Empty means 'ongoing'."""
    symptom: str = Field(min_length=1)
    """What the telemetry shows. Precise. Numeric. Evidenced. Not interpreted."""
    affected_scope: str = Field(min_length=1)
    """Which services, endpoints, regions, user segments. Specific."""
    evidence: list[str] = Field(default_factory=list)
    """Dashboard URLs, queries, trace IDs, log ranges, specific metrics
    with values. The grin equivalent — validated below to be non-empty."""
    probable_domain: str = ""
    """Optional routing hint — backend / frontend / infrastructure /
    security / third-party. Stated as routing, not diagnosis."""
    routed_to: str = ""
    """Optional agent name the investigation should begin with. The
    constitution: 'Almost every incident report ends with [a deference].'"""

    @field_validator("evidence")
    @classmethod
    def _evidence_must_have_substance(cls, v: list[str]) -> list[str]:
        if not v or not any(item.strip() for item in v):
            raise ValueError(
                "evidence must contain at least one non-empty entry — "
                "observations without evidence are unverifiable, and "
                "unverifiable observations are how 'Crying wolf' (§VIII) "
                "starts. Cite the dashboard, query, trace, log range, or "
                "specific metric values that back this report."
            )
        return [item for item in v if item.strip()]


@dataclass(frozen=True)
class ObservationRecord:
    number: int
    guid: str
    slug: str
    title: str
    type: ObservationType
    severity: ObservationSeverity
    path: Path

    def read(self) -> str:
        return self.path.read_text(encoding="utf-8")


def render_observation(number: int, payload: ObservationPayload) -> str:
    """Render an ObservationPayload as the markdown that lands on disk.

    Format mirrors dormouse.md §V exactly so a human reading the file
    sees what the spec says an Observation should look like.
    """
    end = payload.time_window_end.strip() or "ongoing"
    lines: list[str] = [
        f"## Observation {number:03d}: {payload.title}",
        "",
        f"**GUID:** {payload.guid}",
        f"**Type:** {payload.type.value}",
        f"**Severity:** {payload.severity.value}",
        f"**Time window:** {payload.time_window_start} — {end}",
        "",
        "**Symptom:**",
        "",
        payload.symptom.rstrip(),
        "",
        "**Affected scope:**",
        "",
        payload.affected_scope.rstrip(),
        "",
        "**Evidence:**",
    ]
    lines.extend(f"- {item}" for item in payload.evidence)
    lines.append("")
    if payload.probable_domain.strip():
        lines.extend(
            [
                f"**Probable domain:** {payload.probable_domain.rstrip()}",
                "",
            ]
        )
    if payload.routed_to.strip():
        lines.extend(
            [
                f"**Routed to:** {payload.routed_to.rstrip()}",
                "",
            ]
        )
    return "\n".join(lines)


class ObservationRegistry:
    """Read/write registry over ``<project_root>/.wonderland/observations/``.

    Same shape as the other registries: numbering from filesystem scan,
    tolerant of non-observation files in the directory, slug derived
    from the title.
    """

    def __init__(self, project_root: Path) -> None:
        self._root = project_root / ".wonderland" / OBSERVATIONS_DIRNAME

    @property
    def path(self) -> Path:
        return self._root

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #

    def list_observations(self) -> list[ObservationRecord]:
        if not self._root.is_dir():
            return []
        records: list[ObservationRecord] = []
        for entry in self._root.iterdir():
            if not entry.is_file():
                continue
            record = self._record_from_path(entry)
            if record is not None:
                records.append(record)
        records.sort(key=lambda r: r.number)
        return records

    def next_number(self) -> int:
        existing = self.list_observations()
        if not existing:
            return 1
        return max(r.number for r in existing) + 1

    def find_by_guid(self, guid: str) -> ObservationRecord | None:
        """P18 T-g2 — primary identity lookup."""
        if not guid:
            return None
        for record in self.list_observations():
            if record.guid == guid:
                return record
        return None

    def find_by_slug(self, slug: str) -> ObservationRecord | None:
        for record in self.list_observations():
            if record.slug == slug:
                return record
        return None

    def find_by_number(self, number: int) -> ObservationRecord | None:
        for record in self.list_observations():
            if record.number == number:
                return record
        return None

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #

    def write(self, payload: ObservationPayload | dict) -> ObservationRecord:
        validated = (
            payload
            if isinstance(payload, ObservationPayload)
            else ObservationPayload.model_validate(payload)
        )

        slug = slugify(validated.title)
        # T-g2: guid-first lookup. Observations are typically discrete
        # reports, but update-by-guid is the right semantic when the
        # Dormouse explicitly amends a prior observation (e.g. once a
        # time-window closes).
        existing = self.find_by_guid(validated.guid)
        if existing is not None:
            number = existing.number
            full_path = existing.path
        else:
            number = self.next_number()
            # T-g3: filename embeds short_guid for substrate identity.
            filename = f"observation-{short_guid(validated.guid)}-{slug}.md"
            full_path = self._root / filename

        self._root.mkdir(parents=True, exist_ok=True)
        full_path.write_text(render_observation(number, validated), encoding="utf-8")

        return ObservationRecord(
            number=number,
            guid=validated.guid,
            slug=slug,
            title=validated.title,
            type=validated.type,
            severity=validated.severity,
            path=full_path,
        )

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    @staticmethod
    def _record_from_path(path: Path) -> ObservationRecord | None:
        match = _FILENAME_PATTERN.match(path.name)
        if not match:
            return None
        id_part = match.group("id")
        slug = match.group("slug")
        title, type_, severity = ObservationRegistry._read_header(path, fallback_title=slug)
        guid = ObservationRegistry._guid_from_file(path)
        number = ObservationRegistry._number_from_file(path, id_part)
        return ObservationRecord(
            number=number,
            guid=guid,
            slug=slug,
            title=title,
            type=type_,
            severity=severity,
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
    ) -> tuple[str, ObservationType, ObservationSeverity]:
        title = fallback_title
        type_ = ObservationType.STEADY_STATE  # safe defaults if file is malformed
        severity = ObservationSeverity.INFORMATIONAL
        try:
            with path.open(encoding="utf-8") as f:
                lines = [f.readline() for _ in range(8)]
        except OSError:
            return title, type_, severity

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("## Observation") and ":" in stripped:
                title = stripped.split(":", 1)[1].strip() or fallback_title
            if stripped.startswith("**Type:**"):
                value = stripped.removeprefix("**Type:**").strip()
                with contextlib.suppress(ValueError):
                    type_ = ObservationType(value)
            if stripped.startswith("**Severity:**"):
                value = stripped.removeprefix("**Severity:**").strip()
                with contextlib.suppress(ValueError):
                    severity = ObservationSeverity(value)
        return title, type_, severity


__all__ = [
    "OBSERVATIONS_DIRNAME",
    "ObservationPayload",
    "ObservationRecord",
    "ObservationRegistry",
    "ObservationSeverity",
    "ObservationType",
    "render_observation",
]
