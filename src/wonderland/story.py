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

STORIES_DIRNAME = "stories"
_FILENAME_PATTERN = re.compile(r"^story-(\d+)-([a-z0-9-]+)\.md$")


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

    def find_by_number(self, number: int) -> StoryRecord | None:
        for record in self.list_stories():
            if record.number == number:
                return record
        return None

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #

    def write(self, payload: StoryPayload | dict) -> StoryRecord:
        validated = (
            payload if isinstance(payload, StoryPayload) else StoryPayload.model_validate(payload)
        )

        number = self.next_number()
        slug = slugify(validated.title)
        filename = f"story-{number:03d}-{slug}.md"
        full_path = self._root / filename

        self._root.mkdir(parents=True, exist_ok=True)
        full_path.write_text(render_story(number, validated), encoding="utf-8")

        return StoryRecord(
            number=number,
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
        number = int(match.group(1))
        slug = match.group(2)
        title = StoryRegistry._title_from_file(path, fallback=slug)
        return StoryRecord(number=number, slug=slug, title=title, path=path)

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
