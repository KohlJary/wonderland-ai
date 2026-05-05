"""Per-agent memory layers — the SAM-equivalent.

Per WONDERLAND_SPEC §8. Each agent owns its memory; cross-agent
observations flow through the Caucus, not through shared storage.
Three layers:

- ``episodic`` — every utterance the agent produced or observed-and-
  engaged-with, queryable by thread/speaker. SQLite-backed for
  indexing; the source of truth is the JSON payload of each row.
- ``semantic`` — distilled beliefs about the codebase, the domain,
  and the work. Markdown-backed; one file per topic.
- ``relational`` — per-other-agent notes. Markdown-backed; one file
  per other agent.

``AgentMemory`` is the composite — wraps all three stores and exposes
the convenience methods that an agent's runtime uses
(``record``/``query_by_*`` delegate to episodic; ``semantic`` and
``relational`` are accessed as attributes for the higher layers).
"""

from __future__ import annotations

from pathlib import Path
from types import TracebackType
from typing import Self

from wonderland.memory.episodic import EpisodicStore
from wonderland.memory.relational import RelationalStore
from wonderland.memory.semantic import SemanticStore
from wonderland.utterance import Utterance


class AgentMemory:
    """Per-agent SAM composite — episodic + semantic + relational.

    Construct via ``AgentMemory.for_project(project_root, agent_name)``
    for the standard layout. Use as an async context manager so the
    underlying SQLite connection in EpisodicStore is opened/closed
    cleanly:

        async with AgentMemory.for_project(root, "cheshire_cat") as memory:
            await memory.record(utterance)
            history = await memory.query_by_thread(thread_id)
            notes_about_rabbit = memory.relational.read("white_rabbit")

    The four common episodic operations are exposed as direct methods so
    consumers don't have to chain through ``.episodic`` for the hot path.
    Semantic and relational stay attribute-accessed because their APIs
    are richer and the call sites for them tend to be specific.
    """

    def __init__(
        self,
        episodic: EpisodicStore,
        semantic: SemanticStore,
        relational: RelationalStore,
    ) -> None:
        self.episodic = episodic
        self.semantic = semantic
        self.relational = relational

    @classmethod
    def for_project(cls, project_root: Path, agent_name: str) -> Self:
        return cls(
            episodic=EpisodicStore(project_root, agent_name),
            semantic=SemanticStore(project_root, agent_name),
            relational=RelationalStore(project_root, agent_name),
        )

    @property
    def agent_name(self) -> str:
        return self.episodic.agent_name

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    async def open(self) -> None:
        await self.episodic.open()
        # Semantic and relational are file-based; no open/close needed.

    async def close(self) -> None:
        await self.episodic.close()

    async def __aenter__(self) -> Self:
        await self.open()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.close()

    # ------------------------------------------------------------------ #
    # Episodic delegations — the hot path
    # ------------------------------------------------------------------ #

    async def record(self, utterance: Utterance) -> None:
        await self.episodic.record(utterance)

    async def query_by_thread(self, thread_id: str, *, limit: int | None = None) -> list[Utterance]:
        return await self.episodic.query_by_thread(thread_id, limit=limit)

    async def query_by_speaker(self, name: str, *, limit: int | None = None) -> list[Utterance]:
        return await self.episodic.query_by_speaker(name, limit=limit)

    async def query_by_other_agent(self, name: str, *, limit: int | None = None) -> list[Utterance]:
        return await self.episodic.query_by_other_agent(name, limit=limit)

    async def count(self) -> int:
        return await self.episodic.count()


__all__ = [
    "AgentMemory",
    "EpisodicStore",
    "RelationalStore",
    "SemanticStore",
]
