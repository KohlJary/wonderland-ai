"""Semantic memory — distilled beliefs the agent has accumulated.

Per WONDERLAND_SPEC §8. Semantic memory holds the agent's distilled
beliefs about the codebase, the domain, and the work — content the
agent owns and updates between threads (compaction in T16 is the
update trigger).

Storage is plain markdown, one file per topic, at
``<project_root>/.wonderland/memory/<agent>/semantic/<topic>.md``. No
SQLite: semantic content is naturally human-readable, benefits more
from being grep-able and editable by hand than from being indexed,
and there's no query pattern that needs more than "read the topic by
name" or "list what's in here." If/when that changes, the storage can
grow an index without the API needing to.
"""

from __future__ import annotations

from pathlib import Path

from wonderland.adr import slugify

SEMANTIC_DIRNAME = "semantic"


class SemanticStore:
    """Per-agent markdown-backed store of distilled beliefs."""

    def __init__(self, project_root: Path, agent_name: str) -> None:
        self._root = project_root / ".wonderland" / "memory" / agent_name / SEMANTIC_DIRNAME
        self._agent_name = agent_name

    @property
    def path(self) -> Path:
        return self._root

    @property
    def agent_name(self) -> str:
        return self._agent_name

    def read(self, topic: str) -> str:
        """Return the topic's content, or empty string if missing."""
        path = self._topic_path(topic)
        if not path.is_file():
            return ""
        return path.read_text(encoding="utf-8")

    def write(self, topic: str, content: str) -> None:
        """Replace the topic's content with `content`."""
        path = self._topic_path(topic)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def list_topics(self) -> list[str]:
        """Return the slugged topic names currently on disk, sorted."""
        if not self._root.is_dir():
            return []
        return sorted(p.stem for p in self._root.glob("*.md"))

    def as_text(self) -> str:
        """All non-empty topics concatenated as a readable block.

        Used by ``compose_context`` (and any agent that wants to fold
        semantic memory into the cached prompt prefix). Each topic
        becomes a level-3 section keyed by its slug.
        """
        sections: list[str] = []
        for topic in self.list_topics():
            content = self.read(topic).strip()
            if content:
                sections.append(f"### {topic}\n\n{content}")
        return "\n\n".join(sections)

    def _topic_path(self, topic: str) -> Path:
        return self._root / f"{slugify(topic)}.md"
