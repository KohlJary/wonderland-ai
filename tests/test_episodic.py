"""Tests for EpisodicStore — per-agent SQLite-backed utterance log."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

import pytest

from wonderland import (
    AffectVector,
    AgentIdentity,
    Artifact,
    EpisodicStore,
    SpeechAct,
    Stance,
    Utterance,
    UtteranceContent,
)

# ---------- helpers ----------


def _utterance(
    *,
    thread_id: str = "t",
    speaker_name: str = "cheshire_cat",
    speaker_version: str = "0.1",
    act: SpeechAct = SpeechAct.PROPOSAL,
    body: str = "...",
    timestamp: datetime | None = None,
    parent_id: str | None = None,
) -> Utterance:
    return Utterance(
        thread_id=thread_id,
        parent_id=parent_id,
        speaker=AgentIdentity(name=speaker_name, constitution_version=speaker_version),
        addressed_to="caucus",
        speech_act=act,
        content=UtteranceContent(body=body),
        timestamp=timestamp or datetime.now(UTC),
    )


# ---------- lifecycle ----------


async def test_open_creates_directory_and_database(tmp_path: Path) -> None:
    store = EpisodicStore(tmp_path, "cheshire_cat")
    assert not store.path.exists()
    await store.open()
    assert store.path.exists()
    assert store.path.parent.is_dir()
    await store.close()


async def test_async_context_manager_opens_and_closes(tmp_path: Path) -> None:
    async with EpisodicStore(tmp_path, "cheshire_cat") as store:
        await store.record(_utterance(body="hi"))
        assert await store.count() == 1
    # After close, queries fail loudly rather than silently mis-reporting
    with pytest.raises(RuntimeError, match="not open"):
        await store.count()


async def test_open_is_idempotent(tmp_path: Path) -> None:
    store = EpisodicStore(tmp_path, "cheshire_cat")
    await store.open()
    await store.open()  # should not raise
    await store.close()


async def test_reopen_persists_existing_data(tmp_path: Path) -> None:
    a = EpisodicStore(tmp_path, "cheshire_cat")
    await a.open()
    await a.record(_utterance(body="persisted"))
    await a.close()

    b = EpisodicStore(tmp_path, "cheshire_cat")
    await b.open()
    history = await b.query_by_thread("t")
    assert len(history) == 1
    assert history[0].content.body == "persisted"
    await b.close()


async def test_path_includes_project_root_and_agent_name(tmp_path: Path) -> None:
    store = EpisodicStore(tmp_path, "cheshire_cat")
    expected = tmp_path / ".wonderland" / "memory" / "cheshire_cat" / "episodic.sqlite"
    assert store.path == expected


async def test_separate_agents_have_separate_stores(tmp_path: Path) -> None:
    async with (
        EpisodicStore(tmp_path, "cheshire_cat") as cat,
        EpisodicStore(tmp_path, "white_rabbit") as rabbit,
    ):
        await cat.record(_utterance(speaker_name="cheshire_cat", body="cat-said"))
        await rabbit.record(_utterance(speaker_name="white_rabbit", body="rabbit-said"))
        assert await cat.count() == 1
        assert await rabbit.count() == 1
        assert cat.path != rabbit.path


# ---------- record ----------


async def test_record_stores_full_utterance(tmp_path: Path) -> None:
    async with EpisodicStore(tmp_path, "cheshire_cat") as store:
        original = Utterance(
            thread_id="t",
            speaker=AgentIdentity(name="cheshire_cat", constitution_version="0.1"),
            addressed_to=[AgentIdentity(name="white_rabbit", constitution_version="0.1")],
            speech_act=SpeechAct.REFRAME,
            content=UtteranceContent(
                body="what would have to be true?",
                artifacts=[Artifact(kind="adr", payload={"n": 1})],
            ),
            confidence=0.7,
            stance=Stance.IN_CHARACTER,
            affect=AffectVector(arousal=0.3, extras={"oblique": 0.5}),
        )
        await store.record(original)
        history = await store.query_by_thread("t")
        assert history[0] == original


async def test_record_is_idempotent_on_id(tmp_path: Path) -> None:
    """Same utterance recorded twice → only one row, no error."""
    async with EpisodicStore(tmp_path, "cheshire_cat") as store:
        u = _utterance(body="once")
        await store.record(u)
        await store.record(u)
        assert await store.count() == 1


async def test_count_starts_at_zero(tmp_path: Path) -> None:
    async with EpisodicStore(tmp_path, "cheshire_cat") as store:
        assert await store.count() == 0


async def test_record_before_open_raises(tmp_path: Path) -> None:
    store = EpisodicStore(tmp_path, "cheshire_cat")
    with pytest.raises(RuntimeError, match="not open"):
        await store.record(_utterance())


# ---------- queries ----------


async def test_query_by_thread_returns_oldest_first(tmp_path: Path) -> None:
    base = datetime(2026, 5, 4, 12, 0, 0, tzinfo=UTC)
    async with EpisodicStore(tmp_path, "cheshire_cat") as store:
        for i in range(3):
            ts = base.replace(second=i)
            await store.record(_utterance(timestamp=ts, body=f"#{i}"))
        history = await store.query_by_thread("t")
        bodies = [u.content.body for u in history]
        assert bodies == ["#0", "#1", "#2"]


async def test_query_by_thread_isolates_threads(tmp_path: Path) -> None:
    async with EpisodicStore(tmp_path, "cheshire_cat") as store:
        await store.record(_utterance(thread_id="A", body="A1"))
        await store.record(_utterance(thread_id="B", body="B1"))
        await store.record(_utterance(thread_id="A", body="A2"))
        a_history = await store.query_by_thread("A")
        b_history = await store.query_by_thread("B")
        assert [u.content.body for u in a_history] == ["A1", "A2"]
        assert [u.content.body for u in b_history] == ["B1"]


async def test_query_by_speaker_filters_to_that_speaker(tmp_path: Path) -> None:
    async with EpisodicStore(tmp_path, "cheshire_cat") as store:
        await store.record(_utterance(speaker_name="cheshire_cat", body="cat"))
        await store.record(_utterance(speaker_name="white_rabbit", body="rabbit"))
        await store.record(_utterance(speaker_name="cheshire_cat", body="cat-2"))
        cat_history = await store.query_by_speaker("cheshire_cat")
        assert [u.content.body for u in cat_history] == ["cat", "cat-2"]


async def test_query_by_other_agent_is_alias_of_by_speaker(tmp_path: Path) -> None:
    async with EpisodicStore(tmp_path, "cheshire_cat") as store:
        await store.record(_utterance(speaker_name="white_rabbit", body="rabbit"))
        a = await store.query_by_speaker("white_rabbit")
        b = await store.query_by_other_agent("white_rabbit")
        assert a == b


async def test_query_returns_empty_when_no_match(tmp_path: Path) -> None:
    async with EpisodicStore(tmp_path, "cheshire_cat") as store:
        assert await store.query_by_thread("nonexistent") == []
        assert await store.query_by_speaker("nonexistent") == []


async def test_query_respects_limit(tmp_path: Path) -> None:
    base = datetime(2026, 5, 4, 12, 0, 0, tzinfo=UTC)
    async with EpisodicStore(tmp_path, "cheshire_cat") as store:
        for i in range(5):
            await store.record(_utterance(timestamp=base.replace(second=i), body=str(i)))
        history = await store.query_by_thread("t", limit=2)
        assert [u.content.body for u in history] == ["0", "1"]


# ---------- schema ----------


async def test_schema_meta_records_version(tmp_path: Path) -> None:
    async with EpisodicStore(tmp_path, "cheshire_cat") as store:
        conn = store._require_open()
        async with conn.execute("SELECT value FROM schema_meta WHERE key = 'version'") as cursor:
            row = await cursor.fetchone()
        assert row is not None
        assert int(row[0]) >= 1


async def test_concurrent_records_serialize_safely(tmp_path: Path) -> None:
    """Aiosqlite serializes concurrent writes — every record makes it in."""
    async with EpisodicStore(tmp_path, "cheshire_cat") as store:
        await asyncio.gather(*(store.record(_utterance(body=str(i))) for i in range(20)))
        assert await store.count() == 20


# ---------- branching (T-a2) ----------


async def test_default_branch_is_project(tmp_path: Path) -> None:
    """Without any branch set, utterances default to PROJECT_BRANCH."""
    from wonderland.memory.episodic import PROJECT_BRANCH, get_active_branch_id

    assert get_active_branch_id() == PROJECT_BRANCH
    async with EpisodicStore(tmp_path, "cheshire_cat") as store:
        await store.record(_utterance(body="hi"))
        # Query with explicit branch filter — should find it under project.
        history = await store.query_by_thread("t", branches=[PROJECT_BRANCH])
        assert len(history) == 1


async def test_record_tags_active_branch(tmp_path: Path) -> None:
    """When a branch is active, recorded utterances get tagged with it.
    Default-no-filter reads still see them; project-only filter does not."""
    from wonderland.memory.episodic import (
        PROJECT_BRANCH,
        set_active_branch_id,
        reset_active_branch_id,
    )

    async with EpisodicStore(tmp_path, "cheshire_cat") as store:
        await store.record(_utterance(body="project-level"))
        token = set_active_branch_id("design:m1-foo")
        try:
            await store.record(_utterance(body="branch-tagged"))
        finally:
            reset_active_branch_id(token)

        all_rows = await store.query_by_thread("t")
        assert len(all_rows) == 2

        project_only = await store.query_by_thread(
            "t", branches=[PROJECT_BRANCH]
        )
        assert [u.content.body for u in project_only] == ["project-level"]

        branch_only = await store.query_by_thread(
            "t", branches=["design:m1-foo"]
        )
        assert [u.content.body for u in branch_only] == ["branch-tagged"]


async def test_inheritance_chain_default_semantics() -> None:
    """Project branch chain is just project. Other branches inherit project."""
    from wonderland.memory.episodic import (
        PROJECT_BRANCH,
        inheritance_chain,
    )

    assert inheritance_chain(PROJECT_BRANCH) == [PROJECT_BRANCH]
    assert inheritance_chain("design:m2-foo") == [PROJECT_BRANCH, "design:m2-foo"]
    assert inheritance_chain("impl:m2-foo:feat:bar") == [
        PROJECT_BRANCH, "impl:m2-foo:feat:bar",
    ]


async def test_inheritance_chain_reads_scoped_correctly(tmp_path: Path) -> None:
    """An agent on design:m3 with inheritance_chain reads project + m3,
    NOT m1 or m2 design branches (the wedge-bleed-prevention semantic)."""
    from wonderland.memory.episodic import (
        inheritance_chain,
        set_active_branch_id,
        reset_active_branch_id,
    )

    async with EpisodicStore(tmp_path, "cheshire_cat") as store:
        # Write to project (operator / system)
        await store.record(_utterance(body="project-summary"))
        # Write to m1 design
        token = set_active_branch_id("design:m1-foo")
        try:
            await store.record(_utterance(body="m1-deliberation"))
        finally:
            reset_active_branch_id(token)
        # Write to m2 design (the wedge — must not bleed to m3)
        token = set_active_branch_id("design:m2-bar")
        try:
            await store.record(_utterance(body="m2-wedge-noise"))
        finally:
            reset_active_branch_id(token)
        # Write to m3 design
        token = set_active_branch_id("design:m3-baz")
        try:
            await store.record(_utterance(body="m3-own-work"))
        finally:
            reset_active_branch_id(token)

        # Agent on m3 reading via inheritance chain
        m3_view = await store.query_by_thread(
            "t", branches=inheritance_chain("design:m3-baz")
        )
        bodies = [u.content.body for u in m3_view]
        # Sees project + m3, NOT m1 or m2
        assert "project-summary" in bodies
        assert "m3-own-work" in bodies
        assert "m1-deliberation" not in bodies
        assert "m2-wedge-noise" not in bodies


async def test_contextvar_isolation_between_tasks(tmp_path: Path) -> None:
    """ContextVar gives task-local semantics — concurrent tasks each see
    their own active branch. Critical for pipeline-parallel impl runs."""
    from wonderland.memory.episodic import (
        get_active_branch_id,
        set_active_branch_id,
    )

    captured: dict[str, str] = {}

    async def worker(branch: str) -> None:
        set_active_branch_id(branch)
        await asyncio.sleep(0.01)  # give other tasks a chance to interleave
        captured[branch] = get_active_branch_id()

    await asyncio.gather(
        worker("design:m1"),
        worker("design:m2"),
        worker("impl:m3:feat:x"),
    )

    assert captured == {
        "design:m1": "design:m1",
        "design:m2": "design:m2",
        "impl:m3:feat:x": "impl:m3:feat:x",
    }


async def test_legacy_v1_data_migrates_to_project_branch(tmp_path: Path) -> None:
    """A v1 SQLite database (no branch_id column) should migrate cleanly:
    existing rows default to PROJECT_BRANCH, schema_meta bumps to v2."""
    import aiosqlite
    from wonderland.memory.episodic import PROJECT_BRANCH, SCHEMA_VERSION

    # Hand-create a v1-shaped database
    db_path = tmp_path / ".wonderland" / "memory" / "alice" / "episodic.sqlite"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(db_path) as conn:
        await conn.executescript("""
            CREATE TABLE utterances (
                id TEXT PRIMARY KEY,
                thread_id TEXT NOT NULL,
                parent_id TEXT,
                speaker_name TEXT NOT NULL,
                speaker_version TEXT NOT NULL,
                speech_act TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE TABLE schema_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            INSERT INTO schema_meta VALUES ('version', '1');
            INSERT INTO utterances VALUES (
                'legacy-id', 't', NULL, 'alice', '0.1', 'proposal',
                '2026-05-01T00:00:00+00:00', '{}'
            );
        """)
        await conn.commit()

    # Open via the new EpisodicStore — should migrate cleanly
    async with EpisodicStore(tmp_path, "alice") as store:
        # Schema version bumped to 2
        conn = store._require_open()
        async with conn.execute(
            "SELECT value FROM schema_meta WHERE key = 'version'"
        ) as cursor:
            row = await cursor.fetchone()
        assert row is not None
        assert int(row[0]) == SCHEMA_VERSION

        # Legacy row got branch_id = 'project' default
        async with conn.execute(
            "SELECT branch_id FROM utterances WHERE id = ?", ("legacy-id",)
        ) as cursor:
            row = await cursor.fetchone()
        assert row is not None
        assert row[0] == PROJECT_BRANCH
