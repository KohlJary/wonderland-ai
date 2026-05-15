"""Story writer + registry — Alice's inhabited-persona artifacts.

Per WONDERLAND_SPEC §9 / alice.md §V. Alice generates user stories
from inhabited personas — specific people with specific needs, not
"the user" in the abstract. Each story carries a tier (core /
enrichment / fast-follow) so the Rabbit can scope, plus a
**confusion-flags** field that mirrors the Cat's grin: the thing
Alice is required to surface even when she can't fully articulate
it. Stories without confusion-flags are suspect.

Storage at ``<project_root>/.wonderland/stories/story-NNN-slug.md``,
mirroring the ADR / Ticket / Escalation registries.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from wonderland.adr import slugify
from wonderland.artifact_guid import new_artifact_guid, short_guid

STORIES_DIRNAME = "stories"
# T-g3: filename's id-part is either an 8-char ULID prefix (new) or
# a 1-4 digit legacy number (pre-P18). The regex captures both
# shapes so the registry can read mixed-vintage directories without
# a migration step.
_FILENAME_PATTERN = re.compile(
    r"^story-(?P<id>[0-9A-HJKMNP-TV-Z]{8}|\d{1,4})-(?P<slug>[a-z0-9-]+)\.md$"
)
_GUID_PATTERN = re.compile(r"^\*\*GUID:\*\*\s*([0-9A-HJKMNP-TV-Z]{26})\s*$", re.MULTILINE)
_NUMBER_FROM_H2 = re.compile(r"^##\s*Story\s+(\d+)\s*:", re.MULTILINE)


class StoryTier(StrEnum):
    CORE = "core"
    ENRICHMENT = "enrichment"
    FAST_FOLLOW = "fast-follow"


class StoryPayload(BaseModel):
    """Structured payload Alice attaches to a story-issuing utterance.

    Validation enforces Alice's discipline:

    - title, persona, situation, need: all required and non-empty.
      Alice doesn't write skeletons.
    - acceptance: at least one observable condition. A story without
      observable acceptance criteria can't actually be tested as
      shipped.
    - confusion_flags: at least one substantive entry. The grin
      equivalent — Alice is required to surface what felt wrong even
      when she can't fully articulate it. Stories without flags are
      suspect (per §V).
    """

    guid: str = Field(default_factory=new_artifact_guid)
    """P18 — stable artifact identity. ULID generated at creation
    and preserved across re-emissions (Alice re-emits with the
    same guid to amend an existing story; coining a new guid
    creates a new story). The substrate routes on guid; slug is
    cosmetic. Cross-references (feature.sources, ticket sources,
    milestone.consumes_requirements) cite guid; phantom guids
    are caught immediately rather than drifting silently."""

    title: str = Field(min_length=1)
    persona: str = Field(min_length=1)
    """A specific person, grounded in detail, not "the user"."""
    situation: str = Field(min_length=1)
    """What is happening in their life when they encounter the system."""
    need: str = Field(min_length=1)
    """As [persona], I want [outcome], so that [purpose]."""
    acceptance: list[str] = Field(min_length=1)
    """Observable, testable conditions of done."""
    tier: StoryTier
    confusion_flags: list[str] = Field(min_length=1)
    """Things that felt wrong to Alice as she wrote this, even if
    she can't fully articulate why. The grin equivalent — required
    even when the answer is honestly 'nothing felt wrong here'."""
    realizes_requirements: list[str] = Field(default_factory=list)
    """P15 T-m8b — slug list of ``requirement`` artifacts this story
    realizes. The substrate's milestone_realization coverage check
    walks ``milestone.consumes_requirements`` → stories with that
    slug in ``realizes_requirements`` → features sourcing those
    stories, and flags any requirement with no chain. Empty list is
    permitted (Alice can ship a story she can't trace to a specific
    requirement — typically a story responding to operator
    directive context rather than a discovery artifact) but
    discouraged when the run is milestone-scoped: an empty list in
    a scoped run means the coverage check has nothing to anchor
    against. Slugs are the requirement filename's slug component,
    same shape as ``milestone.consumes_requirements``."""

    @field_validator("confusion_flags")
    @classmethod
    def _confusion_flags_must_have_substance(cls, v: list[str]) -> list[str]:
        if not any(item.strip() for item in v):
            raise ValueError(
                "confusion_flags must contain at least one non-empty entry — "
                "stories without flags are suspect (either you weren't paying "
                "attention, or the story is too easy to be interesting)"
            )
        return v

    @field_validator("acceptance")
    @classmethod
    def _acceptance_must_have_substance(cls, v: list[str]) -> list[str]:
        if not any(item.strip() for item in v):
            raise ValueError("acceptance must contain at least one non-empty condition")
        return v


@dataclass(frozen=True)
class StoryRecord:
    number: int
    guid: str
    slug: str
    title: str
    path: Path

    def read(self) -> str:
        return self.path.read_text(encoding="utf-8")


def render_story(number: int, payload: StoryPayload) -> str:
    """Render a StoryPayload as the markdown that lands on disk.

    Format mirrors alice.md §V exactly so a human reading the file
    sees what the spec says a Story should look like.
    """
    lines: list[str] = [
        f"## Story {number:03d}: {payload.title}",
        "",
        f"**GUID:** {payload.guid}",
        "",
        f"**Persona:** {payload.persona.rstrip()}",
        "",
        "**Situation:**",
        "",
        payload.situation.rstrip(),
        "",
        "**Need:**",
        "",
        payload.need.rstrip(),
        "",
        "**Acceptance:**",
    ]
    lines.extend(f"- {item}" for item in payload.acceptance)
    lines.append("")
    lines.append(f"**Tier:** {payload.tier.value}")
    lines.append("")
    lines.append("**Confusion-flags:**")
    lines.extend(f"- {flag}" for flag in payload.confusion_flags)
    lines.append("")
    # P15 T-m8b — realizes_requirements section. Always render the
    # header (empty list renders "- —" sentinel) so coverage parsers
    # can distinguish "Alice ships a story with no realizations" from
    # "old-format story without the field". When the list is empty,
    # downstream coverage flags the milestone's requirements as
    # potentially unrealized.
    lines.append("**Realizes requirements:**")
    if payload.realizes_requirements:
        lines.extend(f"- {slug}" for slug in payload.realizes_requirements)
    else:
        lines.append("- —")
    lines.append("")
    return "\n".join(lines)


class StoryRegistry:
    """Read/write registry over ``<project_root>/.wonderland/stories/``.

    Same shape as the other registries: numbering from filesystem
    scan, tolerant of non-story files in the directory, slug derived
    from the title.
    """

    def __init__(self, project_root: Path) -> None:
        self._root = project_root / ".wonderland" / STORIES_DIRNAME

    @property
    def path(self) -> Path:
        return self._root

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #

    def list_stories(self) -> list[StoryRecord]:
        if not self._root.is_dir():
            return []
        records: list[StoryRecord] = []
        for entry in self._root.iterdir():
            if not entry.is_file():
                continue
            record = self._record_from_path(entry)
            if record is not None:
                records.append(record)
        records.sort(key=lambda r: r.number)
        return records

    def next_number(self) -> int:
        existing = self.list_stories()
        if not existing:
            return 1
        return max(r.number for r in existing) + 1

    def find_by_slug(self, slug: str) -> StoryRecord | None:
        for record in self.list_stories():
            if record.slug == slug:
                return record
        return None

    def find_by_guid(self, guid: str) -> StoryRecord | None:
        """P18 — look up a story by its stable artifact guid. Primary
        lookup path; slug-based lookup is the back-compat fallback
        for re-emissions that don't thread the guid through. Returns
        None when no record matches (caller should treat as
        "create fresh artifact" signal)."""
        if not guid:
            return None
        for record in self.list_stories():
            if record.guid == guid:
                return record
        return None

    def find_by_number(self, number: int) -> StoryRecord | None:
        for record in self.list_stories():
            if record.number == number:
                return record
        return None

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #

    def write(self, payload: StoryPayload | dict) -> StoryRecord:
        """Create or update a story by slug. Existing story with the
        same slug → overwrite in place (preserves the original
        number); new slug → append with the next available number.

        P15 follow-up: previously, StoryRegistry always allocated a
        new number on every write, which meant Alice re-emitting the
        same story across rotations produced ``story-002`` and
        ``story-006`` with identical slugs (discovery5 pilot:
        8 files for 4 conceptual stories). MilestoneRegistry has had
        update-by-slug semantics since T-m1; this aligns the rest of
        the registries with that shape.
        """
        validated = (
            payload if isinstance(payload, StoryPayload) else StoryPayload.model_validate(payload)
        )

        slug = slugify(validated.title)
        # T-g2: identity-by-guid. Look up by guid first; fall back
        # to slug for back-compat with re-emissions that haven't
        # learned to thread the guid through (pre-T-g6 agents +
        # legacy bus payloads). Once T-g6 ships, the slug fallback
        # becomes vestigial — agents cite guid directly and the
        # registry no longer needs to guess.
        existing = self.find_by_guid(validated.guid)
        if existing is None:
            existing = self.find_by_slug(slug)

        if existing is not None:
            number = existing.number
            full_path = existing.path
        else:
            number = self.next_number()
            # T-g3: filename embeds short_guid for identity disambig.
            # Number remains in the H2 header for display, but the
            # filename no longer encodes substrate identity.
            filename = f"story-{short_guid(validated.guid)}-{slug}.md"
            full_path = self._root / filename

        # Preserve existing artifact's guid on slug-fallback match
        # so re-emissions don't generate fresh identity. (When the
        # primary guid-lookup matched, validated.guid IS existing.guid
        # already; this assignment is a no-op there.)
        if existing is not None and existing.guid:
            validated = validated.model_copy(update={"guid": existing.guid})

        self._root.mkdir(parents=True, exist_ok=True)
        full_path.write_text(render_story(number, validated), encoding="utf-8")

        return StoryRecord(
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
    def _record_from_path(path: Path) -> StoryRecord | None:
        match = _FILENAME_PATTERN.match(path.name)
        if not match:
            return None
        id_part = match.group("id")
        slug = match.group("slug")
        title = StoryRegistry._title_from_file(path, fallback=slug)
        guid = StoryRegistry._guid_from_file(path)
        number = StoryRegistry._number_from_file(path, id_part)
        return StoryRecord(
            number=number, guid=guid, slug=slug, title=title, path=path,
        )

    @staticmethod
    def _number_from_file(path: Path, id_part: str) -> int:
        """Resolve the display number for a story file.

        Legacy filenames carried the number in the id slot
        (``story-003-foo.md``); the new T-g3 shape carries the
        short_guid there and keeps the number only in the H2 header.
        For mixed-vintage directories, prefer the filename when it's
        numeric (avoids re-reading file contents for the common
        case) and fall back to parsing the H2 header for new-shape
        files. Numbers are display-only post-T-g3 — guid is the
        substrate identity."""
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
        """Extract the **GUID:** line value from the markdown. Returns
        a fresh ULID when the file predates the P18 guid-everywhere
        rollout — operator can re-emit through the registry to
        persist a stable guid; back-compat path doesn't write
        through on read."""
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return new_artifact_guid()
        m = _GUID_PATTERN.search(text)
        if m:
            return m.group(1)
        return new_artifact_guid()

    @staticmethod
    def _title_from_file(path: Path, *, fallback: str) -> str:
        try:
            with path.open(encoding="utf-8") as f:
                first_line = f.readline().strip()
        except OSError:
            return fallback
        if not first_line.startswith("## Story") or ":" not in first_line:
            return fallback
        return first_line.split(":", 1)[1].strip() or fallback


__all__ = [
    "StoryPayload",
    "StoryRecord",
    "StoryRegistry",
    "StoryTier",
    "render_story",
]
