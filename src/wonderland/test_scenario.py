"""Test Scenario writer + registry — the Mad Hatter's artifact.

Per WONDERLAND_SPEC §9 / mad_hatter.md §V. The Hatter generates
test scenarios — edge cases, adversarial inputs, race conditions —
each carrying a triaged severity class. **Severity is non-optional**:
mad_hatter.md §VIII names "untriaged severity" as a failure mode the
Hatter actively guards against, mirroring the Cat's grin and Alice's
confusion-flags. The "Concern" field is similarly required — the
Hatter's hypothesis about what *will* happen, surfaced so it can be
checked.

Storage at ``<project_root>/.wonderland/test-scenarios/scenario-NNN-slug.md``,
mirroring the ADR / Ticket / Story / Escalation registries.
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

TEST_SCENARIOS_DIRNAME = "test-scenarios"
# T-g3: filename's id-part is either an 8-char ULID prefix (new) or
# a 1-4 digit legacy number (pre-P18).
_FILENAME_PATTERN = re.compile(
    r"^scenario-(?P<id>[0-9A-HJKMNP-TV-Z]{8}|\d{1,4})-(?P<slug>[a-z0-9-]+)\.md$"
)
_GUID_PATTERN = re.compile(r"^\*\*GUID:\*\*\s*([0-9A-HJKMNP-TV-Z]{26})\s*$", re.MULTILINE)
_NUMBER_FROM_H2 = re.compile(r"^##\s*Scenario\s+(\d+)\s*:", re.MULTILINE)


class Severity(StrEnum):
    """The Hatter's severity vocabulary, per mad_hatter.md §II.

    Precise on purpose — mad_hatter.md §VIII calls out "severity
    inflation" (labeling degradation as breakage to get attention) as
    a failure mode that erodes the team's trust in the labels. Use
    underclaim-if-anything as the tiebreaker.
    """

    BREAKAGE = "breakage"
    """System stops working."""
    SILENT_WRONGNESS = "silent-wrongness"
    """System appears to work but produces wrong output. Most dangerous."""
    DEGRADATION = "degradation"
    """System works but worse than promised."""
    CURIOSITY = "curiosity"
    """Interesting but unlikely to bite."""
    DELIGHT = "delight"
    """I just want to know what happens."""


class TestScenarioPayload(BaseModel):
    """Structured payload the Hatter attaches to a test_scenario utterance.

    Validation enforces Hatter discipline:

    - title, setup, trigger, expected, concern: all required and
      non-empty. Skeleton scenarios are not artifacts; they're noise.
    - severity: required enum, no defaults. Untriaged severity is
      §VIII's named failure mode; the type system enforces what the
      constitution demands.
    - concern: required and non-empty. The grin equivalent — the
      Hatter's hypothesis about what *will* happen, surfaced so it
      can be checked. A scenario without a concern is a test, not
      a scenario.
    - property: optional. When the scenario is a witness to a
      general statement (property-based-testing posture per §I), the
      property field carries the general form.
    - implies: optional. Cross-domain implications — handoffs to
      other agents named inline rather than as separate deference
      utterances.
    """

    guid: str = Field(default_factory=new_artifact_guid)
    """P18 — stable TestScenario identity. Re-emit with same guid
    to amend; new guid creates new scenario."""

    title: str = Field(min_length=1)
    severity: Severity
    setup: str = Field(min_length=1)
    """The state of the world before the interesting moment. Be specific."""
    trigger: str = Field(min_length=1)
    """The action or event that pokes the system."""
    expected: str = Field(min_length=1)
    """What should happen if the system is correct."""
    concern: str = Field(min_length=1)
    """The Hatter's hypothesis about what *will* happen, and why.
    Required even when the Hatter feels confident — the value is in
    surfacing the hypothesis so it can be checked."""
    property: str = ""
    """Optional. The general statement this scenario is a witness to.
    Property-based form when possible."""
    implies: list[str] = Field(default_factory=list)
    """Optional. Cross-domain implications — e.g.
    'Implies architectural decision about edit-translation invalidation
    — flag for Cat.'"""

    @field_validator("concern")
    @classmethod
    def _concern_must_have_substance(cls, v: str) -> str:
        if not v.strip():
            raise ValueError(
                "concern must be non-empty — the hypothesis is the grin "
                "equivalent and the scenario is incomplete without it"
            )
        return v


# Opt out of pytest's auto-collection — the "Test" prefix collides with
# pytest's collection rules but these aren't test classes.
TestScenarioPayload.__test__ = False  # type: ignore[attr-defined]


@dataclass(frozen=True)
class TestScenarioRecord:
    number: int
    guid: str
    slug: str
    title: str
    severity: Severity
    path: Path

    def read(self) -> str:
        return self.path.read_text(encoding="utf-8")


TestScenarioRecord.__test__ = False  # type: ignore[attr-defined]


def render_test_scenario(number: int, payload: TestScenarioPayload) -> str:
    """Render a TestScenarioPayload as the markdown that lands on disk.

    Format mirrors mad_hatter.md §V exactly so a human reading the
    file sees what the spec says a Test Scenario should look like.
    """
    lines: list[str] = [
        f"## Scenario {number:03d}: {payload.title}",
        "",
        f"**GUID:** {payload.guid}",
        f"**Severity:** {payload.severity.value}",
        "",
        "**Setup:**",
        "",
        payload.setup.rstrip(),
        "",
        "**Trigger:**",
        "",
        payload.trigger.rstrip(),
        "",
        "**Expected:**",
        "",
        payload.expected.rstrip(),
        "",
        "**Concern:**",
        "",
        payload.concern.rstrip(),
        "",
    ]
    if payload.property.strip():
        lines.extend(
            [
                "**Property:**",
                "",
                payload.property.rstrip(),
                "",
            ]
        )
    if payload.implies:
        lines.append("**Implies:**")
        lines.extend(f"- {item}" for item in payload.implies)
        lines.append("")
    return "\n".join(lines)


class TestScenarioRegistry:
    """Read/write registry over ``<project_root>/.wonderland/test-scenarios/``.

    Same shape as the other registries: numbering from filesystem scan,
    tolerant of non-scenario files in the directory, slug derived from
    the title.
    """

    def __init__(self, project_root: Path) -> None:
        self._root = project_root / ".wonderland" / TEST_SCENARIOS_DIRNAME

    @property
    def path(self) -> Path:
        return self._root

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #

    def list_scenarios(self) -> list[TestScenarioRecord]:
        if not self._root.is_dir():
            return []
        records: list[TestScenarioRecord] = []
        for entry in self._root.iterdir():
            if not entry.is_file():
                continue
            record = self._record_from_path(entry)
            if record is not None:
                records.append(record)
        records.sort(key=lambda r: r.number)
        return records

    def next_number(self) -> int:
        existing = self.list_scenarios()
        if not existing:
            return 1
        return max(r.number for r in existing) + 1

    def find_by_guid(self, guid: str) -> TestScenarioRecord | None:
        """P18 T-g2 — primary identity lookup."""
        if not guid:
            return None
        for record in self.list_scenarios():
            if record.guid == guid:
                return record
        return None

    def find_by_slug(self, slug: str) -> TestScenarioRecord | None:
        for record in self.list_scenarios():
            if record.slug == slug:
                return record
        return None

    def find_by_number(self, number: int) -> TestScenarioRecord | None:
        for record in self.list_scenarios():
            if record.number == number:
                return record
        return None

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #

    def write(self, payload: TestScenarioPayload | dict) -> TestScenarioRecord:
        validated = (
            payload
            if isinstance(payload, TestScenarioPayload)
            else TestScenarioPayload.model_validate(payload)
        )

        slug = slugify(validated.title)
        # T-g2: guid-first lookup. Scenarios are typically discrete
        # events (each is its own probe), but update-by-guid is the
        # right semantic when the Hatter explicitly amends a prior
        # scenario by re-emitting its guid.
        existing = self.find_by_guid(validated.guid)
        if existing is not None:
            number = existing.number
            full_path = existing.path
        else:
            number = self.next_number()
            # T-g3: filename embeds short_guid for substrate identity.
            filename = f"scenario-{short_guid(validated.guid)}-{slug}.md"
            full_path = self._root / filename

        self._root.mkdir(parents=True, exist_ok=True)
        full_path.write_text(render_test_scenario(number, validated), encoding="utf-8")

        return TestScenarioRecord(
            number=number,
            guid=validated.guid,
            slug=slug,
            title=validated.title,
            severity=validated.severity,
            path=full_path,
        )

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    @staticmethod
    def _record_from_path(path: Path) -> TestScenarioRecord | None:
        match = _FILENAME_PATTERN.match(path.name)
        if not match:
            return None
        id_part = match.group("id")
        slug = match.group("slug")
        title, severity = TestScenarioRegistry._title_and_severity_from_file(
            path, fallback_title=slug
        )
        guid = TestScenarioRegistry._guid_from_file(path)
        number = TestScenarioRegistry._number_from_file(path, id_part)
        return TestScenarioRecord(
            number=number,
            guid=guid,
            slug=slug,
            title=title,
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
    def _title_and_severity_from_file(path: Path, *, fallback_title: str) -> tuple[str, Severity]:
        title = fallback_title
        severity = Severity.CURIOSITY  # safe default if the file is malformed
        try:
            with path.open(encoding="utf-8") as f:
                lines = [f.readline() for _ in range(8)]
        except OSError:
            return title, severity

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("## Scenario") and ":" in stripped:
                title = stripped.split(":", 1)[1].strip() or fallback_title
            if stripped.startswith("**Severity:**"):
                value = stripped.removeprefix("**Severity:**").strip()
                # Keep the default if the file's severity line was malformed
                # or used a value not in the current enum.
                with contextlib.suppress(ValueError):
                    severity = Severity(value)
        return title, severity


TestScenarioRegistry.__test__ = False  # type: ignore[attr-defined]


__all__ = [
    "TEST_SCENARIOS_DIRNAME",
    "Severity",
    "TestScenarioPayload",
    "TestScenarioRecord",
    "TestScenarioRegistry",
    "render_test_scenario",
]
