"""Tests for ThreadRoster + bus integration."""

from __future__ import annotations

import asyncio

import pytest

from wonderland.caucus import InMemoryCaucus
from wonderland.roster import ThreadRoster
from wonderland.utterance import (
    AgentIdentity,
    SpeechAct,
    Utterance,
    UtteranceContent,
)


def _u(*, thread_id: str, speaker: str = "alice", body: str = "hi") -> Utterance:
    return Utterance(
        thread_id=thread_id,
        speaker=AgentIdentity(name=speaker, constitution_version="0.1"),
        addressed_to="caucus",
        speech_act=SpeechAct.STORY,
        content=UtteranceContent(body=body),
    )


# ---------- ThreadRoster ----------


def test_open_thread_lets_everyone_in() -> None:
    roster = ThreadRoster()
    assert roster.is_open("main")
    assert roster.is_member("main", "alice")
    assert roster.is_member("main", "any-agent")


def test_register_then_filter() -> None:
    roster = ThreadRoster()
    roster.register("scoping", members={"alice", "cheshire_cat", "dodo"}, goal="ADR")
    assert not roster.is_open("scoping")
    assert roster.is_member("scoping", "alice")
    assert roster.is_member("scoping", "dodo")
    assert not roster.is_member("scoping", "white_rabbit")
    assert not roster.is_member("scoping", "queen_of_hearts")


def test_register_idempotent_on_identical_input() -> None:
    roster = ThreadRoster()
    roster.register("t", members={"a", "b"}, goal="g")
    roster.register("t", members={"a", "b"}, goal="g")  # no-op


def test_register_raises_on_overwrite_with_different_members() -> None:
    roster = ThreadRoster()
    roster.register("t", members={"a", "b"})
    with pytest.raises(ValueError, match="refusing to overwrite"):
        roster.register("t", members={"a", "c"})


def test_add_member_buzz_in() -> None:
    roster = ThreadRoster()
    roster.register("scoping", members={"alice", "dodo"})
    roster.add_member("scoping", "queen_of_hearts")
    assert roster.is_member("scoping", "queen_of_hearts")


def test_add_member_to_open_thread_raises() -> None:
    roster = ThreadRoster()
    with pytest.raises(KeyError, match="open"):
        roster.add_member("not-registered", "alice")


def test_remove_member() -> None:
    roster = ThreadRoster()
    roster.register("t", members={"alice", "dodo"})
    roster.remove_member("t", "alice")
    assert not roster.is_member("t", "alice")
    assert roster.is_member("t", "dodo")


def test_remove_member_idempotent_when_not_present() -> None:
    roster = ThreadRoster()
    roster.register("t", members={"dodo"})
    roster.remove_member("t", "not-a-member")  # no-op
    assert roster.is_member("t", "dodo")


def test_members_returns_snapshot() -> None:
    roster = ThreadRoster()
    roster.register("t", members={"a", "b"})
    snap = roster.members("t")
    assert snap == frozenset({"a", "b"})


def test_goal_and_convenor_round_trip() -> None:
    roster = ThreadRoster()
    roster.register("t", members={"a"}, goal="ship the ADR", convenor="dodo")
    assert roster.goal("t") == "ship the ADR"
    assert roster.convenor("t") == "dodo"


def test_threads_lists_in_registration_order() -> None:
    roster = ThreadRoster()
    roster.register("first", members={"a"})
    roster.register("second", members={"b"})
    assert roster.threads() == ["first", "second"]


# ---------- InMemoryCaucus + roster integration ----------


async def _drain(it, n: int, timeout: float = 0.5) -> list:
    """Collect up to n items from an async iterator with a small timeout."""
    out = []
    try:
        async with asyncio.timeout(timeout):
            async for item in it:
                out.append(item)
                if len(out) >= n:
                    return out
    except TimeoutError:
        pass
    return out


async def test_bus_without_roster_delivers_to_all() -> None:
    bus = InMemoryCaucus()
    alice_iter = bus.subscribe("alice")
    rabbit_iter = bus.subscribe("white_rabbit")
    await bus.publish(_u(thread_id="main", speaker="cat"))

    alice_received = await _drain(alice_iter, 1)
    rabbit_received = await _drain(rabbit_iter, 1)
    assert len(alice_received) == 1
    assert len(rabbit_received) == 1


async def test_bus_with_roster_filters_to_members() -> None:
    roster = ThreadRoster()
    roster.register("scoping", members={"alice", "dodo"})
    bus = InMemoryCaucus(roster=roster)

    alice_iter = bus.subscribe("alice")
    rabbit_iter = bus.subscribe("white_rabbit")
    dodo_iter = bus.subscribe("dodo")

    await bus.publish(_u(thread_id="scoping", speaker="cheshire_cat"))

    alice_received = await _drain(alice_iter, 1)
    dodo_received = await _drain(dodo_iter, 1)
    rabbit_received = await _drain(rabbit_iter, 1)

    assert len(alice_received) == 1, "alice is in the roster"
    assert len(dodo_received) == 1, "dodo is in the roster"
    assert len(rabbit_received) == 0, "white_rabbit is not in the scoping roster"


async def test_bus_with_roster_open_thread_still_fans_out() -> None:
    """A registered roster gates only its registered threads. Threads
    nobody registered remain open — backward-compat for mixed usage."""
    roster = ThreadRoster()
    roster.register("scoping", members={"alice"})
    bus = InMemoryCaucus(roster=roster)

    rabbit_iter = bus.subscribe("white_rabbit")
    await bus.publish(_u(thread_id="other-thread", speaker="cheshire_cat"))

    received = await _drain(rabbit_iter, 1)
    assert len(received) == 1, "open thread should still deliver to non-roster subs"


async def test_bypass_roster_subscribers_see_everything() -> None:
    """Framework observers (ThreadMonitor, ConsensusGuard, runner-observer)
    bypass roster filtering so they can see all threads."""
    roster = ThreadRoster()
    roster.register("scoping", members={"alice"})
    bus = InMemoryCaucus(roster=roster)

    framework_iter = bus.subscribe("monitor", bypass_roster=True)
    await bus.publish(_u(thread_id="scoping", speaker="alice"))

    received = await _drain(framework_iter, 1)
    assert len(received) == 1, "bypass_roster subscriber should always see"


async def test_buzz_in_after_publish_does_not_backfill() -> None:
    """Roster changes apply to subsequent publishes only — buzzing in
    later doesn't deliver missed utterances. The receiver who joined
    late starts from the next message."""
    roster = ThreadRoster()
    roster.register("scoping", members={"alice"})
    bus = InMemoryCaucus(roster=roster)

    rabbit_iter = bus.subscribe("white_rabbit")
    await bus.publish(_u(thread_id="scoping", speaker="alice", body="missed me"))

    roster.add_member("scoping", "white_rabbit")
    await bus.publish(_u(thread_id="scoping", speaker="alice", body="now you see"))

    received = await _drain(rabbit_iter, 2)
    assert len(received) == 1
    assert received[0].content.body == "now you see"
