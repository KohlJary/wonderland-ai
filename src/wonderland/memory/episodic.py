"""Episodic memory — every utterance an agent observed or produced, in order.

Per WONDERLAND_SPEC §8 / D-004. Storage is a per-agent SQLite database at
``<project_root>/.wonderland/memory/<agent_name>/episodic.sqlite``. The
agent owns its store; no cross-agent reads through this layer — that's
what the Caucus is for.

The schema keeps the full Utterance as JSON (so replay is lossless) and
extracts a small number of indexed columns (thread_id, speaker_name,
speech_act) so the agent's typical queries stay cheap. Schema versioning
lives in a sidecar table; future migrations check the recorded version
and step forward.
"""

from __future__ import annotations

from pathlib import Path
from types import TracebackType
from typing import Self

import aiosqlite

from wonderland.utterance import Utterance

SCHEMA_VERSION = 1

_SCHEMA_V1 = """
CREATE TABLE IF NOT EXISTS utterances (
    id              TEXT PRIMARY KEY,
    thread_id       TEXT NOT NULL,
    parent_id       TEXT,
    speaker_name    TEXT NOT NULL,
    speaker_version TEXT NOT NULL,
    speech_act      TEXT NOT NULL,
    timestamp       TEXT NOT NULL,
    payload         TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_thread     ON utterances (thread_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_speaker    ON utterances (speaker_name, timestamp);
CREATE INDEX IF NOT EXISTS idx_speech_act ON utterances (speech_act, timestamp);

CREATE TABLE IF NOT EXISTS schema_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


class EpisodicStore:
    """Per-agent SQLite-backed log of observed and produced utterances.

    Use as an async context manager:

        async with EpisodicStore(project_root, "cheshire_cat") as memory:
            await memory.record(utterance)
            history = await memory.query_by_thread(thread_id)

    Or open and close explicitly:

        memory = EpisodicStore(project_root, "cheshire_cat")
        await memory.open()
        ...
        await memory.close()
    """

    def __init__(self, project_root: Path, agent_name: str) -> None:
        self._agent_name = agent_name
        self._path = project_root / ".wonderland" / "memory" / agent_name / "episodic.sqlite"
        self._conn: aiosqlite.Connection | None = None

    @property
    def path(self) -> Path:
        return self._path

    @property
    def agent_name(self) -> str:
        return self._agent_name

    async def open(self) -> None:
        if self._conn is not None:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self._path)
        # Foreign keys aren't used yet but enabling them now is cheap and avoids
        # a future migration if we ever add them.
        await self._conn.execute("PRAGMA foreign_keys = ON")
        await self._migrate()

    async def close(self) -> None:
        if self._conn is None:
            return
        await self._conn.close()
        self._conn = None

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
    # Schema
    # ------------------------------------------------------------------ #

    async def _migrate(self) -> None:
        assert self._conn is not None
        await self._conn.executescript(_SCHEMA_V1)
        async with self._conn.execute(
            "SELECT value FROM schema_meta WHERE key = 'version'"
        ) as cursor:
            row = await cursor.fetchone()

        current = int(row[0]) if row is not None else 0
        if current < SCHEMA_VERSION:
            # No upgrades to apply yet — v1 is the only schema. When we add
            # v2, branch on `current` and apply the deltas in order.
            await self._conn.execute(
                "INSERT OR REPLACE INTO schema_meta (key, value) VALUES ('version', ?)",
                (str(SCHEMA_VERSION),),
            )
            await self._conn.commit()

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #

    async def record(self, utterance: Utterance) -> None:
        """Persist `utterance`. Idempotent on id — silently ignores duplicates.

        Idempotency matters because the bus may redeliver an utterance under
        certain failure modes (e.g., consumer group reconnect). Recording is
        a write-everything-I-see behavior, and re-recording the same id is
        not a bug worth raising.
        """
        conn = self._require_open()
        await conn.execute(
            """
            INSERT OR IGNORE INTO utterances
                (id, thread_id, parent_id, speaker_name, speaker_version,
                 speech_act, timestamp, payload)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                utterance.id,
                utterance.thread_id,
                utterance.parent_id,
                utterance.speaker.name,
                utterance.speaker.constitution_version,
                utterance.speech_act.value,
                utterance.timestamp.isoformat(),
                utterance.model_dump_json(),
            ),
        )
        await conn.commit()

    # ------------------------------------------------------------------ #
    # Reads
    # ------------------------------------------------------------------ #

    async def query_by_thread(
        self,
        thread_id: str,
        *,
        limit: int | None = None,
    ) -> list[Utterance]:
        """All utterances in `thread_id`, oldest first."""
        return await self._query(
            "WHERE thread_id = ?",
            (thread_id,),
            limit=limit,
        )

    async def query_by_speaker(
        self,
        name: str,
        *,
        limit: int | None = None,
    ) -> list[Utterance]:
        """All utterances spoken by the agent with canonical `name`, oldest first.

        Works for the agent's own past output and for tracking another agent's
        history. Use `query_by_other_agent` when the calling site is asking
        explicitly about a different agent — same query, clearer intent.
        """
        return await self._query(
            "WHERE speaker_name = ?",
            (name,),
            limit=limit,
        )

    async def query_by_other_agent(
        self,
        name: str,
        *,
        limit: int | None = None,
    ) -> list[Utterance]:
        """Utterances I observed *from* another agent named `name`."""
        return await self.query_by_speaker(name, limit=limit)

    async def count(self) -> int:
        conn = self._require_open()
        async with conn.execute("SELECT COUNT(*) FROM utterances") as cursor:
            row = await cursor.fetchone()
        return int(row[0]) if row is not None else 0

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    async def _query(
        self,
        where_clause: str,
        params: tuple[object, ...],
        *,
        limit: int | None,
    ) -> list[Utterance]:
        conn = self._require_open()
        sql = f"SELECT payload FROM utterances {where_clause} ORDER BY timestamp ASC"
        if limit is not None:
            sql += f" LIMIT {int(limit)}"
        async with conn.execute(sql, params) as cursor:
            rows = await cursor.fetchall()
        return [Utterance.model_validate_json(row[0]) for row in rows]

    def _require_open(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("EpisodicStore not open — call .open() or use async with")
        return self._conn
