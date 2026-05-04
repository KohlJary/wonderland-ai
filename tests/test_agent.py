"""Tests for WonderlandAgent — the base class for every character."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from wonderland import (
    AgentIdentity,
    CachedBlock,
    Context,
    EpisodicStore,
    InMemoryCaucus,
    SpeechAct,
    Utterance,
    UtteranceContent,
    WonderlandAgent,
    load_constitution,
)
from wonderland.identity import (
    ConstitutionHeader,
    Identity,
)

# ---------- helpers ----------


def _make_identity(
    name: str = "cheshire_cat",
    interests: frozenset[SpeechAct] | None = None,
) -> Identity:
    return Identity(
        name=name,
        header=ConstitutionHeader(
            display_name=name,
            role="r",
            lineage="Wonderland v0.1",
            version="0.1",
            license="Hippocratic 3.0",
        ),
        constitution_text=f"You are {name}.",
        interests=interests if interests is not None else frozenset(SpeechAct),
    )


def _utterance(
    *,
    thread_id: str = "t",
    speaker: str = "white_rabbit",
    act: SpeechAct = SpeechAct.PROPOSAL,
    body: str = "...",
) -> Utterance:
    return Utterance(
        thread_id=thread_id,
        speaker=AgentIdentity(name=speaker, constitution_version="0.1"),
        addressed_to="caucus",
        speech_act=act,
        content=UtteranceContent(body=body),
    )


async def _agent(
    tmp_path: Path,
    *,
    identity: Identity | None = None,
) -> WonderlandAgent:
    bus = InMemoryCaucus()
    memory = EpisodicStore(tmp_path, "cheshire_cat")
    await memory.open()
    return WonderlandAgent(
        identity=identity or _make_identity(),
        memory=memory,
        bus=bus,
    )


# ---------- Context ----------


def test_context_to_llm_request_caches_constitution() -> None:
    ctx = Context(constitution="You are X.")
    system, messages = ctx.to_llm_request()
    assert system == [CachedBlock("You are X.")]
    assert messages == [{"role": "user", "content": "(no trigger)"}]


def test_context_to_llm_request_caches_relationships_when_present() -> None:
    ctx = Context(constitution="You are X.", relationships="Tweedles overengineer.")
    system, _ = ctx.to_llm_request()
    assert system == [
        CachedBlock("You are X."),
        CachedBlock("Tweedles overengineer."),
    ]


def test_context_to_llm_request_appends_uncached_thread() -> None:
    ctx = Context(
        constitution="You are X.",
        relationships="rels",
        current_thread="thread snapshot",
    )
    system, _ = ctx.to_llm_request()
    assert system[-1] == "thread snapshot"  # plain str, no cache marker
    assert isinstance(system[0], CachedBlock)
    assert isinstance(system[1], CachedBlock)


def test_context_to_llm_request_formats_triggers_into_user_message() -> None:
    u = _utterance(speaker="rabbit", act=SpeechAct.TICKET, body="implement X")
    ctx = Context(constitution="C", triggers=(u,))
    _, messages = ctx.to_llm_request()
    assert messages[0]["role"] == "user"
    assert "[rabbit — ticket]" in messages[0]["content"]
    assert "implement X" in messages[0]["content"]


def test_context_to_llm_request_joins_multiple_triggers() -> None:
    a = _utterance(body="A")
    b = _utterance(body="B")
    ctx = Context(constitution="C", triggers=(a, b))
    _, messages = ctx.to_llm_request()
    assert "A" in messages[0]["content"]
    assert "B" in messages[0]["content"]


# ---------- WonderlandAgent — base behavior ----------


async def test_constructor_wires_identity_memory_bus_llm(tmp_path: Path) -> None:
    bus = InMemoryCaucus()
    memory = EpisodicStore(tmp_path, "cat")
    await memory.open()
    identity = _make_identity()
    agent = WonderlandAgent(identity=identity, memory=memory, bus=bus, llm=None)
    assert agent.identity is identity
    assert agent.memory is memory
    assert agent.bus is bus
    assert agent.llm is None


async def test_should_engage_delegates_to_identity(tmp_path: Path) -> None:
    """Identity owns the policy; the agent just calls into it."""
    interests = frozenset({SpeechAct.PROPOSAL})
    identity = _make_identity(interests=interests)
    agent = await _agent(tmp_path, identity=identity)

    proposal = _utterance(act=SpeechAct.PROPOSAL)
    ticket = _utterance(act=SpeechAct.TICKET)
    assert agent.should_engage(proposal) is True
    assert agent.should_engage(ticket) is False


async def test_default_compose_context_contains_constitution(tmp_path: Path) -> None:
    agent = await _agent(tmp_path)
    triggers = [_utterance()]
    ctx = agent.compose_context(triggers)
    assert ctx.constitution == agent.identity.constitution_text
    assert ctx.triggers == tuple(triggers)


async def test_default_deliberate_returns_none(tmp_path: Path) -> None:
    """Silence is the default. Subclasses override to speak."""
    agent = await _agent(tmp_path)
    ctx = Context(constitution="C")
    assert await agent.deliberate(ctx) is None


# ---------- listen loop ----------


async def test_listen_records_and_queues_engaged_utterances(tmp_path: Path) -> None:
    interests = frozenset({SpeechAct.PROPOSAL})
    agent = await _agent(tmp_path, identity=_make_identity(interests=interests))
    listen_task = asyncio.create_task(agent.listen())

    await agent.bus.publish(_utterance(act=SpeechAct.PROPOSAL, body="seen"))

    queued = await asyncio.wait_for(agent.pending.get(), timeout=1.0)
    assert queued.content.body == "seen"
    assert await agent.memory.count() == 1

    listen_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await listen_task


async def test_listen_skips_utterances_outside_interests(tmp_path: Path) -> None:
    interests = frozenset({SpeechAct.PROPOSAL})
    agent = await _agent(tmp_path, identity=_make_identity(interests=interests))
    listen_task = asyncio.create_task(agent.listen())

    # Caucus filters by interests at the subscription layer, so a TICKET never
    # reaches this subscriber. Memory + queue stay empty.
    await agent.bus.publish(_utterance(act=SpeechAct.TICKET))
    await asyncio.sleep(0.05)
    assert agent.pending.empty()
    assert await agent.memory.count() == 0

    listen_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await listen_task


async def test_listen_does_not_record_when_engagement_policy_rejects(tmp_path: Path) -> None:
    """Even if the speech_act is in interests, a custom policy can refuse to engage."""

    def reject_all(_u: Utterance, _memory: object | None = None) -> bool:
        return False

    identity = Identity(
        name="cat",
        header=ConstitutionHeader(
            display_name="cat",
            role="r",
            lineage="Wonderland v0.1",
            version="0.1",
            license="L",
        ),
        constitution_text="",
        interests=frozenset(SpeechAct),
        engagement_policy=reject_all,
    )
    agent = await _agent(tmp_path, identity=identity)
    listen_task = asyncio.create_task(agent.listen())

    await agent.bus.publish(_utterance(act=SpeechAct.PROPOSAL))
    await asyncio.sleep(0.05)
    assert agent.pending.empty()
    assert await agent.memory.count() == 0

    listen_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await listen_task


# ---------- speak loop ----------


async def test_speak_publishes_when_deliberate_returns_utterance(tmp_path: Path) -> None:
    agent = await _agent(tmp_path)

    output = _utterance(speaker="cheshire_cat", act=SpeechAct.PROPOSAL, body="my reply")

    async def fixed_deliberate(_ctx: Context) -> Utterance:
        return output

    agent.deliberate = fixed_deliberate  # type: ignore[method-assign]

    # Subscribe to bus to confirm the agent published
    sub = agent.bus.subscribe(agent_name="observer")
    speak_task = asyncio.create_task(agent.speak())
    await agent.pending.put(_utterance(act=SpeechAct.QUESTION))

    received = await asyncio.wait_for(anext(sub), timeout=1.0)
    assert received.content.body == "my reply"
    assert await agent.memory.count() == 1  # the agent's own output recorded

    speak_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await speak_task


async def test_speak_silently_skips_when_deliberate_returns_none(tmp_path: Path) -> None:
    """Silence is a valid move."""
    agent = await _agent(tmp_path)
    sub = agent.bus.subscribe(agent_name="observer")

    speak_task = asyncio.create_task(agent.speak())
    await agent.pending.put(_utterance(act=SpeechAct.QUESTION))

    # Wait briefly to let the speak loop process; no publish should happen
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(anext(sub), timeout=0.1)
    assert await agent.memory.count() == 0

    speak_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await speak_task


# ---------- lifecycle ----------


async def test_run_starts_both_loops_and_stop_cancels_them(tmp_path: Path) -> None:
    agent = await _agent(tmp_path)
    run_task = asyncio.create_task(agent.run())
    await asyncio.sleep(0.05)  # let run() schedule its sub-tasks
    assert agent._listen_task is not None
    assert agent._speak_task is not None
    assert not agent._listen_task.done()
    assert not agent._speak_task.done()

    await agent.stop()
    assert agent._listen_task is None
    assert agent._speak_task is None

    run_task.cancel()
    with contextlib_suppress(asyncio.CancelledError):
        await run_task


# Tiny helper inline to avoid importing contextlib at top-level for one use
def contextlib_suppress(*excs: type[BaseException]):
    import contextlib as _contextlib

    return _contextlib.suppress(*excs)


# ---------- end-to-end with a real loaded constitution ----------


async def test_end_to_end_with_loaded_constitution(tmp_path: Path) -> None:
    """Wire identity-from-disk + memory + bus and observe one turn."""
    cat_identity = load_constitution("cheshire_cat")
    bus = InMemoryCaucus()
    memory = EpisodicStore(tmp_path, "cheshire_cat")
    await memory.open()

    class FixedReplyAgent(WonderlandAgent):
        async def deliberate(self, context: Context) -> Utterance | None:
            assert "Cheshire Cat" in context.constitution
            return Utterance(
                thread_id=context.triggers[0].thread_id,
                speaker=self.identity.as_agent_identity(),
                addressed_to="caucus",
                speech_act=SpeechAct.PROPOSAL,
                content=UtteranceContent(body="What would have to be true?"),
            )

    agent = FixedReplyAgent(identity=cat_identity, memory=memory, bus=bus)
    observer = bus.subscribe(agent_name="observer")
    run_task = asyncio.create_task(agent.run())

    await bus.publish(_utterance(act=SpeechAct.DIRECTIVE, body="build a thing"))

    cat_reply = await asyncio.wait_for(anext(observer), timeout=1.0)
    # The first utterance the observer sees might be the original directive
    # (caucus broadcasts to everyone). Skip until we see the cat's reply.
    while cat_reply.speaker.name != "cheshire_cat":
        cat_reply = await asyncio.wait_for(anext(observer), timeout=1.0)
    assert "What would have to be true?" in cat_reply.content.body

    await agent.stop()
    run_task.cancel()
    with contextlib_suppress(asyncio.CancelledError):
        await run_task
    await memory.close()
