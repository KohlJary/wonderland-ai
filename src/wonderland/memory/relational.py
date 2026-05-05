"""Relational memory — per-other-agent notes.

Per WONDERLAND_SPEC §8. Each character keeps notes about every other
character they've worked with. The Caterpillar's notes on Tweedledee
are different from his notes on Tweedledum; both belong only to the
Caterpillar — they're not shared.

Storage: one markdown file per other agent, at
``<project_root>/.wonderland/memory/<agent>/relational/<other_name>.md``.
The other-agent name is treated as already canonical (snake_case
agent names from constitutions); no slugification, so a round-trip
between ``write(name, ...)`` and ``read(name)`` is exact.

These notes are what make ``compose_context`` capable of producing the
relationships layer. ``for_speakers`` formats the relevant notes as a
markdown block ready to drop into a CachedBlock prefix.
"""

from __future__ import annotations

from pathlib import Path

RELATIONAL_DIRNAME = "relational"


class RelationalStore:
    """Per-agent markdown-backed store of notes about other agents."""

    def __init__(self, project_root: Path, agent_name: str) -> None:
        self._root = project_root / ".wonderland" / "memory" / agent_name / RELATIONAL_DIRNAME
        self._agent_name = agent_name

    @property
    def path(self) -> Path:
        return self._root

    @property
    def agent_name(self) -> str:
        return self._agent_name

    def read(self, other_name: str) -> str:
        path = self._note_path(other_name)
        if not path.is_file():
            return ""
        return path.read_text(encoding="utf-8")

    def write(self, other_name: str, content: str) -> None:
        path = self._note_path(other_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def list_others(self) -> list[str]:
        if not self._root.is_dir():
            return []
        return sorted(p.stem for p in self._root.glob("*.md"))

    def for_speakers(self, names: list[str] | tuple[str, ...]) -> str:
        """Format the relational notes for the given speakers as a markdown block.

        Returns an empty string when none of the speakers have notes —
        callers can drop the result straight into a Context layer
        without conditional logic.
        """
        sections: list[str] = []
        for name in names:
            content = self.read(name).strip()
            if content:
                sections.append(f"### {name}\n\n{content}")
        if not sections:
            return ""
        return "## Relational notes\n\n" + "\n\n".join(sections)

    def _note_path(self, other_name: str) -> Path:
        return self._root / f"{other_name}.md"
