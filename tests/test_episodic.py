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
