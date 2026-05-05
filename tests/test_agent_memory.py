"""Tests for AgentMemory — the SAM composite."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from wonderland import (
    AgentIdentity,
    AgentMemory,
    SpeechAct,
    Utterance,
    UtteranceContent,
)


def _utterance(*, body: str = "...", speaker: str = "white_rabbit") -> Utterance:
    return Utterance(
        thread_id="t",
        speaker=AgentIdentity(name=speaker, constitution_version="0.1"),
        addressed_to="caucus",
        speech_act=SpeechAct.PROPOSAL,
        content=UtteranceContent(body=body),
        timestamp=datetime.now(UTC),
    )


# ---------- construction ----------


async def test_for_project_assembles_three_stores(tmp_path: Path) -> None:
    memory = AgentMemory.for_project(tmp_path, "cheshire_cat")
    base = tmp_path / ".wonderland" / "memory" / "cheshire_cat"
    assert memory.episodic.path == base / "episodic.sqlite"
    assert memory.semantic.path == base / "semantic"
    assert memory.relational.path == base / "relational"


async def test_agent_name_is_exposed(tmp_path: Path) -> None:
    memory = AgentMemory.for_project(tmp_path, "white_rabbit")
    assert memory.agent_name == "white_rabbit"


# ---------- lifecycle ----------


async def test_open_and_close(tmp_path: Path) -> None:
    memory = AgentMemory.for_project(tmp_path, "cheshire_cat")
    await memory.open()
    await memory.record(_utterance(body="hi"))
    assert await memory.count() == 1
    await memory.close()


async def test_async_context_manager(tmp_path: Path) -> None:
    async with AgentMemory.for_project(tmp_path, "cheshire_cat") as memory:
        await memory.record(_utterance(body="hi"))
        assert await memory.count() == 1
    # After exit, the SQLite connection is closed
    with pytest.raises(RuntimeError, match="not open"):
        await memory.count()


# ---------- episodic delegations ----------


async def test_record_and_query_by_thread(tmp_path: Path) -> None:
    async with AgentMemory.for_project(tmp_path, "cheshire_cat") as memory:
        u = _utterance(body="message on thread t")
        await memory.record(u)
        history = await memory.query_by_thread("t")
        assert len(history) == 1
        assert history[0].content.body == "message on thread t"


async def test_query_by_speaker(tmp_path: Path) -> None:
    async with AgentMemory.for_project(tmp_path, "cheshire_cat") as memory:
        await memory.record(_utterance(speaker="white_rabbit"))
        await memory.record(_utterance(speaker="alice"))
        rabbit_history = await memory.query_by_speaker("white_rabbit")
        assert len(rabbit_history) == 1


async def test_query_by_other_agent_alias(tmp_path: Path) -> None:
    async with AgentMemory.for_project(tmp_path, "cheshire_cat") as memory:
        await memory.record(_utterance(speaker="white_rabbit"))
        a = await memory.query_by_speaker("white_rabbit")
        b = await memory.query_by_other_agent("white_rabbit")
        assert a == b


async def test_count_starts_at_zero(tmp_path: Path) -> None:
    async with AgentMemory.for_project(tmp_path, "cheshire_cat") as memory:
        assert await memory.count() == 0


# ---------- semantic + relational accessed via attributes ----------


async def test_semantic_store_writes_persist(tmp_path: Path) -> None:
    async with AgentMemory.for_project(tmp_path, "cheshire_cat") as memory:
        memory.semantic.write("architecture", "Use Redis Streams.")
    # After close, content survives — file-backed
    fresh = AgentMemory.for_project(tmp_path, "cheshire_cat")
    assert "Use Redis Streams" in fresh.semantic.read("architecture")


async def test_relational_store_writes_persist(tmp_path: Path) -> None:
    async with AgentMemory.for_project(tmp_path, "cheshire_cat") as memory:
        memory.relational.write("white_rabbit", "asks me for estimates I don't give")
    fresh = AgentMemory.for_project(tmp_path, "cheshire_cat")
    assert "estimates" in fresh.relational.read("white_rabbit")


async def test_semantic_and_relational_isolated_per_agent(tmp_path: Path) -> None:
    async with (
        AgentMemory.for_project(tmp_path, "cheshire_cat") as cat,
        AgentMemory.for_project(tmp_path, "white_rabbit") as rabbit,
    ):
        cat.semantic.write("note", "cat-note")
        rabbit.semantic.write("note", "rabbit-note")
        cat.relational.write("alice", "cat's-alice")
        rabbit.relational.write("alice", "rabbit's-alice")

        assert cat.semantic.read("note") == "cat-note"
        assert rabbit.semantic.read("note") == "rabbit-note"
        assert cat.relational.read("alice") == "cat's-alice"
        assert rabbit.relational.read("alice") == "rabbit's-alice"
