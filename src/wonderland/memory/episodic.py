"""Episodic memory — every utterance an agent observed or produced, in order.

Per WONDERLAND_SPEC §8 / D-004. Storage is a per-agent SQLite database at
``<project_root>/.wonderland/memory/<agent_name>/episodic.sqlite``. The
agent owns its store; no cross-agent reads through this layer — that's
what the Caucus is for.

The schema keeps the full Utterance as JSON (so replay is lossless) and
extracts a small number of indexed columns (thread_id, speaker_name,
speech_act, branch_id) so the agent's typical queries stay cheap. Schema
versioning lives in a sidecar table; migrations check the recorded
version and step forward.

**Branching (schema v2, T-a2):** Each utterance is tagged with a
``branch_id`` so memory can be scoped by milestone-design pass,
per-feature implementation pass, or project-level. ``"project"`` is
the special root branch — receives consolidated summaries on
milestone close. Other branches use structured names like
``design:m1-data-layer`` or ``impl:m1-data-layer:feat:foo``. The
active branch is a task-local ``ContextVar`` so concurrent pipeline-
parallel runs each see their own branch without cross-contamination.
Reads accept an optional ``branches=[...]`` filter; default ``None``
returns all branches (operator/dashboard view) while agent-time
queries pass an inheritance chain (typically ``["project",
<own-branch>]``).
"""

from __future__ import annotations

from pathlib import Path
from types import TracebackType
from typing import Self

import aiosqlite

from wonderland.utterance import Utterance

SCHEMA_VERSION = 2

# Default branch tag — receives operator-driven utterances, system
# events, and milestone-close consolidation summaries. Agent reads
# in a scoped context include this as the project-level root.
PROJECT_BRANCH = "project"

# Archive prefix — applied to a branch's utterances when consolidated.
# Still on disk for forensics + paper-trail, but excluded from
# default agent reads (would re-introduce the wedge-bleed pattern).
ARCHIVED_PREFIX = "archived:"


# Originally implemented as a ContextVar per the WONDERLAND_SPEC §8
# "task-local" framing, but that broke across the Runner's actual
# task topology. ContextVar values are captured at ``create_task``
# time — Runner.start() spawns agent tasks BEFORE run_workflow sets
# the active branch, so each agent task carries a snapshot of the
# default ``PROJECT_BRANCH`` for its entire lifetime. Later
# ``set_active_branch_id`` calls in run_workflow update only the
# workflow task's contextvar; agents' ``memory.record(utterance)``
# calls still read PROJECT_BRANCH from their stale snapshot, so
# every utterance lands on ``branch_id='project'``. The branching
# infrastructure existed on disk (schema v2 column, inheritance
# chain) but did nothing because nothing ever got tagged with a
# non-default branch — diagnosed on obol's M3 design where
# 1,179/1,179 of caterpillar's utterances were on 'project',
# letting M2 deliberation leak into M3 recall.
#
# Fix: workflow-scoped module-level string. asyncio is single-
# threaded per event loop; concurrent runners in the same process
# wasn't a real use case and the ContextVar semantics were
# preventing the load-bearing case (Runner-shared workflow branch)
# from working. Pipeline parallelism within a single workflow
# shares the branch correctly because pipelines belong to one
# milestone scope.
_active_branch: str = PROJECT_BRANCH


def get_active_branch_id() -> str:
    """Return the active branch tag for the current workflow run.

    Defaults to ``PROJECT_BRANCH`` when no branch is set — that's the
    right semantic for operator-driven flows + system events that
    happen outside a workflow scope.
    """
    return _active_branch


def set_active_branch_id(branch_id: str) -> str:
    """Set the active branch for the current process. Returns the
    PRIOR branch_id as the token; pass that token to
    ``reset_active_branch_id`` to restore.

    Use a try/finally pattern to keep scopes clean::

        token = set_active_branch_id("design:m1-foo")
        try:
            ...
        finally:
            reset_active_branch_id(token)
    """
    global _active_branch
    prior = _active_branch
    _active_branch = branch_id
    return prior


def reset_active_branch_id(token: object) -> None:
    """Restore the active branch to its prior value via the token
    returned by ``set_active_branch_id`` (the token IS the prior
    branch_id string after the ContextVar → global migration)."""
    global _active_branch
    if not isinstance(token, str):
        # Tolerate stale ContextVar.Token-shaped callers during
        # migration; reset to default rather than crashing.
        _active_branch = PROJECT_BRANCH
        return
    _active_branch = token


def inheritance_chain(branch_id: str | None = None) -> list[str]:
    """Compute the inheritance chain for an active branch — the list
    of branches an agent at this branch can legitimately read from.

    Provisional semantics (T-a2 design Q1: NO design-to-impl
    inheritance):

      - For any branch: returns ``[PROJECT_BRANCH, branch_id]`` —
        the agent sees project-level summaries + its own branch's
        deliberation.
      - For ``PROJECT_BRANCH`` (no scope active): returns just
        ``[PROJECT_BRANCH]``.

    Specifically does NOT include design branches in an impl
    branch's chain. The contract artifacts on disk (features,
    tickets, contract notes, ADRs) are the design-to-impl bridge;
    if something only lives in design memory, it wasn't load-
    bearing enough to survive. This semantic surfaces design-impl
    gaps as substrate-level bugs rather than masking them via
    memory inheritance.
    """
    if branch_id is None:
        branch_id = get_active_branch_id()
    if branch_id == PROJECT_BRANCH:
        return [PROJECT_BRANCH]
    return [PROJECT_BRANCH, branch_id]


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

_MIGRATE_V1_TO_V2 = """
ALTER TABLE utterances ADD COLUMN branch_id TEXT NOT NULL DEFAULT 'project';
CREATE INDEX IF NOT EXISTS idx_branch ON utterances (branch_id, timestamp);
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

        # v1 → v2: add branch_id column + index. Existing rows default
        # to PROJECT_BRANCH. Idempotent — checks for column presence
        # rather than re-running ALTER TABLE (SQLite would fail on
        # duplicate column).
        if current < 2:
            async with self._conn.execute(
                "PRAGMA table_info(utterances)"
            ) as cursor:
                columns = await cursor.fetchall()
            column_names = {row[1] for row in columns}
            if "branch_id" not in column_names:
                await self._conn.executescript(_MIGRATE_V1_TO_V2)

        if current < SCHEMA_VERSION:
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

        Tags the utterance with the active branch (``get_active_branch_id()``)
        so future scoped reads can filter cleanly. The default branch is
        ``PROJECT_BRANCH`` — applies when no design/impl scope is active
        (operator-driven flows, system events).

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
                 speech_act, timestamp, payload, branch_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                get_active_branch_id(),
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
        branches: list[str] | None = None,
    ) -> list[Utterance]:
        """All utterances in `thread_id`, oldest first.

        ``branches`` filters reads to the named branch ids. Default
        ``None`` returns all branches (operator/dashboard view).
        Agent-time queries should pass an inheritance chain
        (typically ``inheritance_chain()`` for the active branch).
        """
        return await self._query(
            "WHERE thread_id = ?",
            (thread_id,),
            limit=limit,
            branches=branches,
        )

    async def query_by_speaker(
        self,
        name: str,
        *,
        limit: int | None = None,
        branches: list[str] | None = None,
    ) -> list[Utterance]:
        """All utterances spoken by the agent with canonical `name`, oldest first.

        Works for the agent's own past output and for tracking another agent's
        history. Use `query_by_other_agent` when the calling site is asking
        explicitly about a different agent — same query, clearer intent.

        ``branches`` filters as in ``query_by_thread``.
        """
        return await self._query(
            "WHERE speaker_name = ?",
            (name,),
            limit=limit,
            branches=branches,
        )

    async def query_by_other_agent(
        self,
        name: str,
        *,
        limit: int | None = None,
        branches: list[str] | None = None,
    ) -> list[Utterance]:
        """Utterances I observed *from* another agent named `name`."""
        return await self.query_by_speaker(
            name, limit=limit, branches=branches,
        )

    async def count(self) -> int:
        conn = self._require_open()
        async with conn.execute("SELECT COUNT(*) FROM utterances") as cursor:
            row = await cursor.fetchone()
        return int(row[0]) if row is not None else 0

    # ------------------------------------------------------------------ #
    # Consolidation (T-a2 chunk C)
    # ------------------------------------------------------------------ #

    async def archive_branch(self, branch_id: str) -> int:
        """Archive a branch — rewrite branch_id from ``<X>`` to
        ``archived:<X>`` for every utterance on the branch.

        Fired by ``consolidate_milestone`` after the project-level
        summary utterance has been recorded. Archived utterances
        stay on disk for forensics / paper-trail but are excluded
        from default agent reads (which pass an inheritance_chain
        of [PROJECT_BRANCH, own_branch] — archived:X isn't in any
        chain).

        Returns the number of rows rewritten. Idempotent — calling
        on an already-archived branch is a no-op.
        """
        if branch_id.startswith(ARCHIVED_PREFIX):
            return 0
        conn = self._require_open()
        archived_id = f"{ARCHIVED_PREFIX}{branch_id}"
        cursor = await conn.execute(
            "UPDATE utterances SET branch_id = ? WHERE branch_id = ?",
            (archived_id, branch_id),
        )
        await conn.commit()
        return cursor.rowcount

    async def record_at_branch(
        self, utterance: Utterance, branch_id: str,
    ) -> None:
        """Persist ``utterance`` tagged with an explicit ``branch_id``,
        bypassing the contextvar. Used by consolidation to write
        project-level summary utterances without setting the
        active branch context.
        """
        conn = self._require_open()
        await conn.execute(
            """
            INSERT OR IGNORE INTO utterances
                (id, thread_id, parent_id, speaker_name, speaker_version,
                 speech_act, timestamp, payload, branch_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                branch_id,
            ),
        )
        await conn.commit()

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    async def _query(
        self,
        where_clause: str,
        params: tuple[object, ...],
        *,
        limit: int | None,
        branches: list[str] | None = None,
    ) -> list[Utterance]:
        conn = self._require_open()
        if branches is not None and branches:
            placeholders = ",".join("?" * len(branches))
            where_clause = (
                f"{where_clause} AND branch_id IN ({placeholders})"
            )
            params = (*params, *branches)
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
