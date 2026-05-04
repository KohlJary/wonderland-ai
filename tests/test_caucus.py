"""Tests for the Caucus event bus.

InMemoryCaucus gets full coverage. RedisCaucus tests are gated behind the
``WONDERLAND_REDIS_URL`` environment variable so CI can run unit tests
without a Redis dependency.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import uuid
from collections.abc import AsyncIterator

import pytest

from wonderland import (
    AgentIdentity,
    Caucus,
    InMemoryCaucus,
    SpeechAct,
    Utterance,
    UtteranceContent,
)

# ---------- helpers ----------


def _speaker(name: str = "cheshire_cat") -> AgentIdentity:
    return AgentIdentity(name=name, constitution_version="0.1")


def _utterance(
    *,
    thread_id: str = "thread-1",
    act: SpeechAct = SpeechAct.PROPOSAL,
    body: str = "...",
    speaker: AgentIdentity | None = None,
) -> Utterance:
    return Utterance(
        thread_id=thread_id,
        speaker=speaker or _speaker(),
        addressed_to="caucus",
        speech_act=act,
        content=UtteranceContent(body=body),
    )


async def _collect(
    iterator: AsyncIterator[Utterance],
    n: int,
    *,
    timeout: float = 1.0,
) -> list[Utterance]:
    """Consume `n` items from an async iterator, with a per-call timeout."""
    out: list[Utterance] = []
    for _ in range(n):
        out.append(await asyncio.wait_for(anext(iterator), timeout=timeout))
    return out


# ---------- InMemoryCaucus ----------


async def test_publish_assigns_monotonic_ids() -> None:
    caucus = InMemoryCaucus()
    a = await caucus.publish(_utterance(body="a"))
    b = await caucus.publish(_utterance(body="b"))
    assert a != b


async def test_history_records_all_published() -> None:
    caucus = InMemoryCaucus()
    await caucus.publish(_utterance(body="one"))
    await caucus.publish(_utterance(body="two"))
    bodies = [u.content.body for u in caucus.history]
    assert bodies == ["one", "two"]


async def test_subscribe_yields_subsequent_publishes() -> None:
    caucus = InMemoryCaucus()
    sub = caucus.subscribe(agent_name="cat")
    await caucus.publish(_utterance(body="hello"))
    received = await _collect(sub, 1)
    assert received[0].content.body == "hello"


async def test_from_beginning_replays_history() -> None:
    caucus = InMemoryCaucus()
    await caucus.publish(_utterance(body="past-1"))
    await caucus.publish(_utterance(body="past-2"))
    sub = caucus.subscribe(agent_name="cat", from_beginning=True)
    received = await _collect(sub, 2)
    assert [u.content.body for u in received] == ["past-1", "past-2"]


async def test_default_subscribe_skips_history() -> None:
    caucus = InMemoryCaucus()
    await caucus.publish(_utterance(body="missed"))
    sub = caucus.subscribe(agent_name="cat")
    await caucus.publish(_utterance(body="seen"))
    received = await _collect(sub, 1)
    assert received[0].content.body == "seen"


async def test_fan_out_to_multiple_subscribers() -> None:
    caucus = InMemoryCaucus()
    cat = caucus.subscribe(agent_name="cat")
    rabbit = caucus.subscribe(agent_name="rabbit")
    await caucus.publish(_utterance(body="for both"))
    cat_msg = await asyncio.wait_for(anext(cat), timeout=1.0)
    rabbit_msg = await asyncio.wait_for(anext(rabbit), timeout=1.0)
    assert cat_msg.content.body == "for both"
    assert rabbit_msg.content.body == "for both"


async def test_interest_filter_drops_unrelated_acts() -> None:
    caucus = InMemoryCaucus()
    sub = caucus.subscribe(
        agent_name="cat",
        interests=frozenset({SpeechAct.PROPOSAL}),
    )
    await caucus.publish(_utterance(act=SpeechAct.TICKET, body="ignored"))
    await caucus.publish(_utterance(act=SpeechAct.PROPOSAL, body="seen"))
    msg = await asyncio.wait_for(anext(sub), timeout=1.0)
    assert msg.content.body == "seen"


async def test_thread_filter_isolates_thread() -> None:
    caucus = InMemoryCaucus()
    sub = caucus.subscribe(agent_name="cat", thread_id="thread-A")
    await caucus.publish(_utterance(thread_id="thread-B", body="other"))
    await caucus.publish(_utterance(thread_id="thread-A", body="mine"))
    msg = await asyncio.wait_for(anext(sub), timeout=1.0)
    assert msg.content.body == "mine"


async def test_subscriber_unregisters_on_close() -> None:
    caucus = InMemoryCaucus()
    sub = caucus.subscribe(agent_name="cat")
    await caucus.publish(_utterance(body="x"))
    await asyncio.wait_for(anext(sub), timeout=1.0)
    await sub.aclose()
    # After close the cat subscriber list should be empty
    assert "cat" not in caucus._subscribers


async def test_two_subscribers_under_same_agent_name_both_receive() -> None:
    """InMemory fans out to every queue, including duplicates under one name.

    (Redis consumer-group semantics are different — same-name consumers
    share a position there. The in-memory stub is a development aid; the
    distinction matters only when we test the real Redis path.)
    """
    caucus = InMemoryCaucus()
    a = caucus.subscribe(agent_name="cat")
    b = caucus.subscribe(agent_name="cat")
    await caucus.publish(_utterance(body="hi"))
    a_msg = await asyncio.wait_for(anext(a), timeout=1.0)
    b_msg = await asyncio.wait_for(anext(b), timeout=1.0)
    assert a_msg.content.body == "hi"
    assert b_msg.content.body == "hi"


def test_inmemory_satisfies_caucus_protocol() -> None:
    caucus: Caucus = InMemoryCaucus()
    assert hasattr(caucus, "publish")
    assert hasattr(caucus, "subscribe")


# ---------- RedisCaucus (opt-in) ----------


REDIS_URL = os.environ.get("WONDERLAND_REDIS_URL")
redis_required = pytest.mark.skipif(
    REDIS_URL is None,
    reason="set WONDERLAND_REDIS_URL=redis://localhost:6379 to run Redis tests",
)


@redis_required
async def test_redis_publish_and_subscribe_roundtrip() -> None:
    from redis.asyncio import from_url

    from wonderland import RedisCaucus

    client = from_url(REDIS_URL)  # type: ignore[arg-type]
    stream = f"wonderland:test:{uuid.uuid4().hex}"
    caucus = RedisCaucus(client, stream=stream)

    sub = caucus.subscribe(agent_name="cat", block_ms=500)

    async def deliver() -> None:
        await asyncio.sleep(0.1)  # give the consumer group time to be created
        await caucus.publish(_utterance(body="redis-hello"))

    deliver_task = asyncio.create_task(deliver())
    msg = await asyncio.wait_for(anext(sub), timeout=3.0)
    await deliver_task
    assert msg.content.body == "redis-hello"

    with contextlib.suppress(Exception):
        await client.delete(stream)
    await client.aclose()
