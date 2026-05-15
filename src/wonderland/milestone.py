"""Milestone substrate — sequential ordering layer above features.

Per ``project_interviews_milestones_thesis.md``: Interviews capture
operator intent once as requirement artifacts; Milestones organize
those requirements into a multi-run trajectory. tdd-design runs
scoped to a milestone produce features that ship together; the
operator iterates milestone-by-milestone instead of regenerating
the trajectory framing per run.

A Milestone groups requirements into an ordered, named slice with
a definition of done. Status is *derived* from features-that-belong-
to-this-milestone (proposed if nothing queued; in_progress if any
feature is in flight; done if every feature is verified; deferred
if the milestone YAML / markdown says so). No separate lifecycle
log in v1 — the implicit-status approach is the gameplan-approved
shape until it hits a real limit.

Storage at ``<project_root>/.wonderland/milestones/`` mirrors the
other registry patterns but with one key divergence: the registry
*updates by slug*, not append-only. Re-running ``milestone-plan``
after a follow-up discovery should amend the existing plan (extend
a milestone with new requirements, or append a new milestone at
the end) without losing operator-edited content. Same-slug writes
overwrite; new-slug writes append.

Filename shape: ``<NN>-<slug>.md`` where ``NN`` is the milestone's
``order`` (zero-padded). Order is part of the filename so the
sorted directory listing reads as the operator-facing milestone
sequence without an extra index file.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, model_validator

from wonderland.adr import slugify
from wonderland.interview import Confidence

MILESTONES_DIRNAME = "milestones"
_FILENAME_PATTERN = re.compile(
    r"^milestone-(\d+)-([a-z0-9-]+)\.md$"
)


class MilestoneStatus(StrEnum):
    """Lifecycle states a milestone can occupy. v1 derives these
    from features-belonging-to-milestone rather than tracking a
    separate state log — see ``MilestoneRegistry.derive_status`` for
    the derivation logic.

    - ``proposed``: no features have been queued or designed against
      this milestone yet. Default state.
    - ``in_progress``: at least one feature scoped to this
      milestone is in_progress / queued / ready_for_review.
    - ``done``: every feature scoped to this milestone has reached
      a verified terminal state.
    - ``deferred``: milestone is in the plan but explicitly punted
      out of the current cycle (operator-driven; lives in the
      milestone's YAML body).
    """

    PROPOSED = "proposed"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    DEFERRED = "deferred"


class MilestonePayload(BaseModel):
    """Structured payload an agent attaches to a ``milestone``
    utterance during the planning meeting.

    The trio (Rabbit, Cat, Alice) each ships milestones from their
    lens; the substrate writes each via ``MilestoneRegistry.write``,
    which dedups by slug. Same slug = update; new slug = append.
    """

    slug: str = Field(
        min_length=1,
        pattern=r"^[a-z0-9][a-z0-9-]*$",
        description=(
            "Stable identifier — used as the registry key for "
            "update-by-slug semantics. Lowercase letters / digits / "
            "hyphens; no leading hyphen. Pick something short and "
            "meaningful (``foundation``, ``logging-loop``, "
            "``gamification``, ``cloud-mode``); avoid prefixing "
            "with numbers (the order field handles sequencing)."
        ),
    )
    name: str = Field(
        min_length=1,
        description=(
            "Human-readable milestone name (e.g. ``Foundation: "
            "local data layer + profile shell``). Shown in the "
            "dashboard's milestones pane."
        ),
    )
    order: int = Field(
        ge=1,
        description=(
            "1-indexed position in the milestone sequence. Drives "
            "the filename + the dashboard's ordering. Conflicts "
            "(two milestones with the same order) are tolerated — "
            "the registry breaks ties by slug, but agents should "
            "coordinate to keep order unique."
        ),
    )
    goal: str = Field(
        min_length=1,
        description=(
            "One- to three-sentence statement of what this "
            "milestone accomplishes. Becomes part of M1's "
            "convenor_directive when tdd-design runs scoped to "
            "this milestone."
        ),
    )
    done_when: list[str] = Field(
        default_factory=list,
        description=(
            "Observable conditions of done — concrete enough that "
            "the operator (and downstream meetings) can check "
            "them. Each item is one sentence. e.g. 'App launches "
            "on a fresh machine and creates a profile.'"
        ),
    )
    consumes_requirements: list[str] = Field(
        default_factory=list,
        description=(
            "Requirement slugs scoped to this milestone. tdd-design "
            "--milestone <slug> filters M1+ seeds to just these. "
            "Same requirement can belong to multiple milestones if "
            "it's load-bearing for each (e.g., the data-layer "
            "requirement seeds both Foundation and Logging-Loop)."
        ),
    )
    deferred: bool = Field(
        default=False,
        description=(
            "Operator-driven flag marking this milestone as "
            "explicitly deferred. The status derivation reads "
            "this; deferred milestones don't get auto-promoted to "
            "in_progress when features land against them."
        ),
    )
    confidence: Confidence = Field(
        default=Confidence.OPERATOR_STATED,
        description=(
            "Provenance — operator_stated when the operator "
            "approved this milestone, interviewer_inferred when an "
            "agent proposed it without operator confirmation. "
            "Cross-run planning passes can re-confirm by setting "
            "operator_stated."
        ),
    )

    @model_validator(mode="after")
    def _consumes_requirements_unique(self) -> "MilestonePayload":
        """Same requirement slug appearing twice in a single
        milestone is almost certainly a bug — fail fast at construct
        time rather than letting M1 see duplicates downstream."""
        seen: set[str] = set()
        dupes: list[str] = []
        for slug in self.consumes_requirements:
            if slug in seen:
                dupes.append(slug)
            seen.add(slug)
        if dupes:
            raise ValueError(
                f"milestone {self.slug!r}: duplicate requirement "
                f"slugs in consumes_requirements: {dupes}"
            )
        return self


@dataclass(frozen=True)
class MilestoneRecord:
    slug: str
    order: int
    name: str
    deferred: bool
    confidence: Confidence
    path: Path

    def read(self) -> str:
        return self.path.read_text(encoding="utf-8")


def render_milestone(payload: MilestonePayload) -> str:
    """Render a MilestonePayload as the markdown that lands on disk.

    Format mirrors the requirement / ADR / story registries: title
    heading, bold field labels, body sections. ``consumes_requirements``
    renders as a bulleted list; ``done_when`` ditto.
    """
    lines: list[str] = [
        f"## Milestone {payload.order:02d}: {payload.name}",
        "",
        f"**Slug:** {payload.slug}",
        f"**Order:** {payload.order}",
        f"**Deferred:** {'true' if payload.deferred else 'false'}",
        f"**Confidence:** {payload.confidence.value}",
        "",
        "**Goal:**",
        "",
        payload.goal.rstrip(),
        "",
    ]
    if payload.done_when:
        lines.extend(
            [
                "**Done when:**",
                "",
            ]
        )
        lines.extend(f"- {item}" for item in payload.done_when)
        lines.append("")
    if payload.consumes_requirements:
        lines.extend(
            [
                "**Consumes requirements:**",
                "",
            ]
        )
        lines.extend(
            f"- {slug}" for slug in payload.consumes_requirements
        )
        lines.append("")
    return "\n".join(lines)


class MilestoneRegistry:
    """Read/write registry over ``<project_root>/.wonderland/milestones/``.

    Key divergence from the other registries: **updates by slug, not
    append-only**. Re-running ``milestone-plan`` after a follow-up
    discovery should amend the existing plan without duplicating
    milestones — same slug means overwrite the file in place.

    Filename: ``milestone-NN-slug.md`` where NN is the order
    (zero-padded). Order can change between writes; the registry
    renames the file when ``order`` shifts so the sorted directory
    listing stays consistent with the operator-facing sequence.
    """

    def __init__(self, project_root: Path) -> None:
        self._root = project_root / ".wonderland" / MILESTONES_DIRNAME

    @property
    def path(self) -> Path:
        return self._root

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #

    def list_milestones(self) -> list[MilestoneRecord]:
        """All milestones on disk, sorted by order then slug. Order
        is the operator-facing sequence; slug breaks ties (rare —
        agents should coordinate to keep order unique)."""
        if not self._root.is_dir():
            return []
        records: list[MilestoneRecord] = []
        for entry in self._root.iterdir():
            if not entry.is_file():
                continue
            record = self._record_from_path(entry)
            if record is not None:
                records.append(record)
        records.sort(key=lambda r: (r.order, r.slug))
        return records

    def find_by_slug(self, slug: str) -> MilestoneRecord | None:
        for record in self.list_milestones():
            if record.slug == slug:
                return record
        return None

    def find_by_order(self, order: int) -> MilestoneRecord | None:
        for record in self.list_milestones():
            if record.order == order:
                return record
        return None

    def next_order(self) -> int:
        """Smallest unused order number. Used by agents to append a
        new milestone at the end without colliding with existing
        ones; new plans typically start fresh from 1."""
        existing = self.list_milestones()
        if not existing:
            return 1
        return max(r.order for r in existing) + 1

    # ------------------------------------------------------------------ #
    # Writes (update-by-slug)
    # ------------------------------------------------------------------ #

    def write(
        self, payload: MilestonePayload | dict
    ) -> MilestoneRecord:
        """Create or update a milestone by slug. Existing milestone
        with the same slug → overwrite (filename may change if
        ``order`` shifted). New slug → append."""
        validated = (
            payload
            if isinstance(payload, MilestonePayload)
            else MilestonePayload.model_validate(payload)
        )

        # Existing milestone with this slug? Replace it.
        existing = self.find_by_slug(validated.slug)
        if existing is not None and existing.path.is_file():
            # Remove the old file if the order changed (filename
            # follows order, so we'd otherwise leave a stale copy).
            new_path = self._path_for(
                validated.order, validated.slug
            )
            if existing.path != new_path:
                try:
                    existing.path.unlink()
                except OSError:
                    pass
            target = new_path
        else:
            target = self._path_for(validated.order, validated.slug)

        self._root.mkdir(parents=True, exist_ok=True)
        target.write_text(
            render_milestone(validated), encoding="utf-8"
        )

        return MilestoneRecord(
            slug=validated.slug,
            order=validated.order,
            name=validated.name,
            deferred=validated.deferred,
            confidence=validated.confidence,
            path=target,
        )

    def delete_by_slug(self, slug: str) -> bool:
        """Remove a milestone file. Returns True if found and
        deleted, False otherwise. Used by operator pruning + by
        the planning loop when an agent proposes consolidating
        two milestones into one."""
        record = self.find_by_slug(slug)
        if record is None:
            return False
        try:
            record.path.unlink()
        except OSError:
            return False
        return True

    # ------------------------------------------------------------------ #
    # Derived status
    # ------------------------------------------------------------------ #

    @staticmethod
    def derive_status(
        *,
        deferred: bool,
        feature_states: list[str],
    ) -> MilestoneStatus:
        """Roll feature states up to a milestone status.

        Inputs: the milestone's ``deferred`` flag + the lifecycle
        states of the features that consume this milestone's
        requirements (resolved by the dashboard via
        ``MilestoneRegistry.features_for``).

        Rules:
          - deferred → DEFERRED (operator-driven; status doesn't
            move regardless of feature state)
          - no features → PROPOSED (nothing's been designed yet)
          - any feature is verified-or-better AND not all features
            are verified → IN_PROGRESS (at least one feature in
            flight, work isn't complete)
          - any feature is queued / in_progress / ready_for_review
            / designed → IN_PROGRESS
          - all features are verified → DONE
          - otherwise (e.g., all features are still proposed) →
            PROPOSED
        """
        if deferred:
            return MilestoneStatus.DEFERRED
        if not feature_states:
            return MilestoneStatus.PROPOSED

        all_verified = all(s == "verified" for s in feature_states)
        if all_verified:
            return MilestoneStatus.DONE

        any_in_flight = any(
            s
            in (
                "designed",
                "queued",
                "in_progress",
                "ready_for_review",
                "verified",
            )
            for s in feature_states
        )
        if any_in_flight:
            return MilestoneStatus.IN_PROGRESS

        return MilestoneStatus.PROPOSED

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _path_for(self, order: int, slug: str) -> Path:
        return self._root / f"milestone-{order:02d}-{slug}.md"

    @staticmethod
    def _record_from_path(path: Path) -> MilestoneRecord | None:
        match = _FILENAME_PATTERN.match(path.name)
        if not match:
            return None
        order = int(match.group(1))
        slug = match.group(2)
        name, deferred, confidence = (
            MilestoneRegistry._fields_from_file(
                path, fallback_name=slug
            )
        )
        return MilestoneRecord(
            slug=slug,
            order=order,
            name=name,
            deferred=deferred,
            confidence=confidence,
            path=path,
        )

    @staticmethod
    def _fields_from_file(
        path: Path, *, fallback_name: str
    ) -> tuple[str, bool, Confidence]:
        """Parse the first several lines for name + deferred +
        confidence. Tolerates operator hand-edits — same shape as
        the requirement registry's parser."""
        name = fallback_name
        deferred = False
        confidence = Confidence.OPERATOR_STATED
        try:
            with path.open(encoding="utf-8") as f:
                lines = [f.readline() for _ in range(10)]
        except OSError:
            return name, deferred, confidence
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("## Milestone"):
                if ":" in stripped:
                    name = stripped.split(":", 1)[1].strip() or name
            elif stripped.startswith("**Deferred:**"):
                raw = stripped.removeprefix("**Deferred:**").strip().lower()
                deferred = raw == "true"
            elif stripped.startswith("**Confidence:**"):
                raw = stripped.removeprefix("**Confidence:**").strip()
                try:
                    confidence = Confidence(raw)
                except ValueError:
                    pass
        return name, deferred, confidence


__all__ = [
    "MILESTONES_DIRNAME",
    "Milestone",
    "MilestonePayload",
    "MilestoneRecord",
    "MilestoneRegistry",
    "MilestoneStatus",
    "render_milestone",
]


# Backwards-friendly alias so code importing ``Milestone`` from the
# top-level wonderland namespace finds the payload model directly
# (mirrors how ``Story`` / ``Ticket`` are exposed without a
# ``-Payload`` suffix in many call sites).
Milestone = MilestonePayload
