"""Tests for the INVITE speech act + roster mutation in WonderlandAgent.speak.

Per Block 2c: any agent can publish an INVITE addressed to specific
other agents. The framework adds the invitees to the thread's roster
*before* publish, so the bus delivers the invite to them and they're
included in all subsequent thread utterances.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from wonderland.agent import WonderlandAgent
from wonderland.caucus import InMemoryCaucus
from wonderland.identity import ConstitutionHeader, Identity
from wonderland.memory import AgentMemory
from wonderland.roster import ThreadRoster
from wonderland.utterance import (
    PROCEDURAL_ACTS,
    SUBSTANTIVE_ACTS,
    AgentIdentity,
    SpeechAct,
    Utterance,
    UtteranceContent,
    is_procedural,
)


def _identity(name: str) -> Identity:
    return Identity(
        name=name,
        header=ConstitutionHeader(
            display_name=name.capitalize(),
            role="test",
            lineage="test",
            version="0.1",
            license="test",
        ),
        constitution_text="",
    )


# ---------- speech-act registration ----------


def test_invite_is_a_procedural_speech_act() -> None:
    assert SpeechAct.INVITE in PROCEDURAL_ACTS
    assert SpeechAct.INVITE not in SUBSTANTIVE_ACTS
    assert is_procedural(SpeechAct.INVITE)


# ---------- _apply_invite_if_any ----------


async def test_invite_adds_addressed_agents_to_thread_roster(tmp_path: Path) -> None:
    """An INVITE with addressed_to=[X, Y] adds X and Y to the registered
    thread's roster."""
    roster = ThreadRoster()
    roster.register("scoping", members={"alice", "dodo"}, goal="g")
    bus = InMemoryCaucus(roster=roster)
    memory = AgentMemory.for_project(tmp_path, "alice")
    await memory.open()
    agent = WonderlandAgent(identity=_identity("alice"), memory=memory, bus=bus)
    agent.set_roster(roster)

    invite = Utterance(
        thread_id="scoping",
        speaker=AgentIdentity(name="alice", constitution_version="0.1"),
        addressed_to=[
            AgentIdentity(name="cheshire_cat", constitution_version="0.1"),
            AgentIdentity(name="caterpillar", constitution_version="0.1"),
        ],
        speech_act=SpeechAct.INVITE,
        content=UtteranceContent(body="Cat, Caterpillar — please join"),
    )

    agent._apply_invite_if_any(invite)

    members = roster.members("scoping")
    assert "cheshire_cat" in members
    assert "caterpillar" in members
    assert "alice" in members  # original member preserved
    assert "dodo" in members
    await memory.close()


async def test_invite_no_op_when_thread_is_open(tmp_path: Path) -> None:
    """Open threads include everyone already; INVITE shouldn't add anything."""
    roster = ThreadRoster()
    bus = InMemoryCaucus(roster=roster)
    memory = AgentMemory.for_project(tmp_path, "alice")
    await memory.open()
    agent = WonderlandAgent(identity=_identity("alice"), memory=memory, bus=bus)
    agent.set_roster(roster)

    invite = Utterance(
        thread_id="open-thread",
        speaker=AgentIdentity(name="alice", constitution_version="0.1"),
        addressed_to=[AgentIdentity(name="cheshire_cat", constitution_version="0.1")],
        speech_act=SpeechAct.INVITE,
        content=UtteranceContent(body="..."),
    )

    # No raise; just a no-op.
    agent._apply_invite_if_any(invite)
    assert roster.is_open("open-thread")
    await memory.close()


async def test_invite_no_op_when_no_roster_wired(tmp_path: Path) -> None:
    """Direct construction without set_roster: INVITE publishes normally
    but doesn't mutate any roster (there isn't one)."""
    bus = InMemoryCaucus()
    memory = AgentMemory.for_project(tmp_path, "alice")
    await memory.open()
    agent = WonderlandAgent(identity=_identity("alice"), memory=memory, bus=bus)
    # Note: agent._roster is None by default.

    invite = Utterance(
        thread_id="t",
        speaker=AgentIdentity(name="alice", constitution_version="0.1"),
        addressed_to=[AgentIdentity(name="cheshire_cat", constitution_version="0.1")],
        speech_act=SpeechAct.INVITE,
        content=UtteranceContent(body="..."),
    )

    # No raise.
    agent._apply_invite_if_any(invite)
    await memory.close()


async def test_non_invite_utterances_dont_mutate_roster(tmp_path: Path) -> None:
    """Other speech acts don't trigger roster mutation."""
    roster = ThreadRoster()
    roster.register("scoping", members={"alice", "dodo"}, goal="g")
    bus = InMemoryCaucus(roster=roster)
    memory = AgentMemory.for_project(tmp_path, "alice")
    await memory.open()
    agent = WonderlandAgent(identity=_identity("alice"), memory=memory, bus=bus)
    agent.set_roster(roster)

    not_an_invite = Utterance(
        thread_id="scoping",
        speaker=AgentIdentity(name="alice", constitution_version="0.1"),
        addressed_to=[AgentIdentity(name="cheshire_cat", constitution_version="0.1")],
        speech_act=SpeechAct.QUESTION,
        content=UtteranceContent(body="Cat — quick question"),
    )

    agent._apply_invite_if_any(not_an_invite)
    members = roster.members("scoping")
    assert "cheshire_cat" not in members
    await memory.close()


# ---------- end-to-end: invitee receives the invite via the bus ----------


async def _drain(it, n: int, timeout: float = 0.5) -> list:
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


async def test_inviting_agent_pre_mutates_roster_so_bus_delivers_invite(
    tmp_path: Path,
) -> None:
    """End-to-end: agent A publishes INVITE addressed to B on a thread B
    isn't in. A's speak() updates the roster *before* publish, so the
    bus delivers the invite to B even though B wasn't a member when A
    issued the invite."""
    roster = ThreadRoster()
    roster.register("scoping", members={"alice", "dodo"}, goal="g")
    bus = InMemoryCaucus(roster=roster)

    # Subscribe a "B" listener to the bus to verify delivery.
    b_iter = bus.subscribe("cheshire_cat")
    received: list[Utterance] = []

    async def _consume() -> None:
        async for u in b_iter:
            received.append(u)

    consume_task = asyncio.create_task(_consume())

    # Set up agent A.
    memory = AgentMemory.for_project(tmp_path, "alice")
    await memory.open()
    agent = WonderlandAgent(identity=_identity("alice"), memory=memory, bus=bus)
    agent.set_roster(roster)

    invite = Utterance(
        thread_id="scoping",
        speaker=AgentIdentity(name="alice", constitution_version="0.1"),
        addressed_to=[AgentIdentity(name="cheshire_cat", constitution_version="0.1")],
        speech_act=SpeechAct.INVITE,
        content=UtteranceContent(body="Cat — please join, here's the context..."),
    )

    # Simulate the publish flow that happens in speak().
    agent._apply_invite_if_any(invite)
    await bus.publish(invite)
    await asyncio.sleep(0.05)  # let the consumer drain

    consume_task.cancel()
    import contextlib as _contextlib

    with _contextlib.suppress(asyncio.CancelledError):
        await consume_task
    await memory.close()

    # B (cheshire_cat) should have received the invite.
    assert any(
        u.speech_act is SpeechAct.INVITE and u.content.body.startswith("Cat — please join")
        for u in received
    ), f"cheshire_cat did not receive the invite; got {received!r}"


async def test_invite_without_pre_mutate_filters_out_invitee(tmp_path: Path) -> None:
    """Negative control: if we don't pre-mutate the roster, the bus
    filters out the invitee. This is the bug Block 2c exists to fix —
    confirms the roster filter is what's gating delivery."""
    roster = ThreadRoster()
    roster.register("scoping", members={"alice", "dodo"}, goal="g")
    bus = InMemoryCaucus(roster=roster)

    b_iter = bus.subscribe("cheshire_cat")
    received: list[Utterance] = []

    async def _consume() -> None:
        async for u in b_iter:
            received.append(u)

    consume_task = asyncio.create_task(_consume())

    invite = Utterance(
        thread_id="scoping",
        speaker=AgentIdentity(name="alice", constitution_version="0.1"),
        addressed_to=[AgentIdentity(name="cheshire_cat", constitution_version="0.1")],
        speech_act=SpeechAct.INVITE,
        content=UtteranceContent(body="..."),
    )
    # Skip the pre-mutate step intentionally.
    await bus.publish(invite)
    await asyncio.sleep(0.05)

    consume_task.cancel()
    import contextlib as _contextlib

    with _contextlib.suppress(asyncio.CancelledError):
        await consume_task

    assert received == [], (
        "without the pre-mutate, cheshire_cat shouldn't see the invite "
        "(they're not in the roster) — got delivery anyway"
    )
