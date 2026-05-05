"""Tests for WonderlandAgent — the base class for every character."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from wonderland import (
    AgentIdentity,
    AgentMemory,
    CachedBlock,
    Context,
    InMemoryCaucus,
    SpeechAct,
    Utterance,
    UtteranceContent,
    WonderlandAgent,
    format_transcript,
    format_utterance,
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
    memory = AgentMemory.for_project(tmp_path, "cheshire_cat")
    await memory.open()
    return WonderlandAgent(
        identity=identity or _make_identity(),
        memory=memory,
        bus=bus,
    )


# ---------- transcript helpers ----------


def test_format_utterance_includes_speaker_and_act() -> None:
    u = _utterance(speaker="cat", act=SpeechAct.PROPOSAL, body="...")
    out = format_utterance(u)
    assert "[cat — proposal]" in out
    assert "..." in out


def test_format_transcript_joins_with_blank_line() -> None:
    a = _utterance(speaker="A", body="first")
    b = _utterance(speaker="B", body="second")
    out = format_transcript([a, b])
    assert out == f"{format_utterance(a)}\n\n{format_utterance(b)}"


def test_format_transcript_empty() -> None:
    assert format_transcript([]) == ""


def test_format_transcript_preserves_order() -> None:
    """Caller is responsible for chronological order; transcript honors it."""
    a = _utterance(body="A")
    b = _utterance(body="B")
    c = _utterance(body="C")
    forward = format_transcript([a, b, c])
    reverse = format_transcript([c, b, a])
    assert forward.index("A") < forward.index("B") < forward.index("C")
    assert reverse.index("C") < reverse.index("B") < reverse.index("A")


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
    memory = AgentMemory.for_project(tmp_path, "cat")
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
    ctx = await agent.compose_context(triggers)
    assert ctx.constitution == agent.identity.constitution_text
    assert ctx.triggers == tuple(triggers)


async def test_compose_context_with_no_triggers_has_empty_thread(tmp_path: Path) -> None:
    agent = await _agent(tmp_path)
    ctx = await agent.compose_context([])
    assert ctx.current_thread == ""
    assert ctx.triggers == ()


async def test_compose_context_populates_current_thread_from_episodic_memory(
    tmp_path: Path,
) -> None:
    """Prior utterances on the same thread show up in the current_thread layer."""
    from datetime import UTC, datetime

    agent = await _agent(tmp_path)
    base = datetime(2026, 5, 4, 12, 0, 0, tzinfo=UTC)

    # Prior thread history (recorded as if we'd observed and engaged earlier)
    earlier = Utterance(
        thread_id="t",
        speaker=AgentIdentity(name="white_rabbit", constitution_version="0.1"),
        addressed_to="caucus",
        speech_act=SpeechAct.TICKET,
        content=UtteranceContent(body="ticket body"),
        timestamp=base.replace(second=0),
    )
    await agent.memory.record(earlier)

    # The trigger arrives now
    trigger = Utterance(
        thread_id="t",
        speaker=AgentIdentity(name="mad_hatter", constitution_version="0.1"),
        addressed_to="caucus",
        speech_act=SpeechAct.TEST_SCENARIO,
        content=UtteranceContent(body="trigger body"),
        timestamp=base.replace(second=10),
    )
    await agent.memory.record(trigger)

    ctx = await agent.compose_context([trigger])
    assert "ticket body" in ctx.current_thread
    assert "[white_rabbit — ticket]" in ctx.current_thread


async def test_compose_context_populates_relationships_from_relational_memory(
    tmp_path: Path,
) -> None:
    """When the trigger comes from an agent we have notes about, those notes
    show up in Context.relationships."""
    agent = await _agent(tmp_path)
    agent.memory.relational.write(
        "white_rabbit",
        "Asks me for estimates I shouldn't be giving. Gentle redirect each time.",
    )

    trigger = _utterance(thread_id="t", speaker="white_rabbit", body="by when?")
    ctx = await agent.compose_context([trigger])

    assert "white_rabbit" in ctx.relationships
    assert "estimates I shouldn't be giving" in ctx.relationships


async def test_compose_context_relationships_empty_when_no_notes(tmp_path: Path) -> None:
    """No relational notes for the trigger's speaker → relationships layer empty."""
    agent = await _agent(tmp_path)
    trigger = _utterance(thread_id="t", speaker="white_rabbit")
    ctx = await agent.compose_context([trigger])
    assert ctx.relationships == ""


async def test_compose_context_includes_relationships_for_thread_speakers(
    tmp_path: Path,
) -> None:
    """Relationships layer covers everyone in the thread, not just the trigger speaker."""
    agent = await _agent(tmp_path)
    agent.memory.relational.write("white_rabbit", "rabbit-notes")
    agent.memory.relational.write("alice", "alice-notes")

    earlier = _utterance(thread_id="t", speaker="alice", body="user story...")
    await agent.memory.record(earlier)

    trigger = _utterance(thread_id="t", speaker="white_rabbit", body="ticketing it now")
    ctx = await agent.compose_context([trigger])

    assert "rabbit-notes" in ctx.relationships
    assert "alice-notes" in ctx.relationships


async def test_compose_context_excludes_self_from_relationships(tmp_path: Path) -> None:
    """The agent doesn't keep relational notes about itself."""
    agent = await _agent(tmp_path)
    agent.memory.relational.write(agent.identity.name, "should not appear")
    trigger = _utterance(thread_id="t", speaker=agent.identity.name)
    ctx = await agent.compose_context([trigger])
    assert "should not appear" not in ctx.relationships


async def test_compose_context_excludes_triggers_from_thread_history(tmp_path: Path) -> None:
    """The trigger appears as the immediate stimulus — don't double it in the history."""
    agent = await _agent(tmp_path)
    trigger = _utterance(thread_id="t", body="trigger-only")
    await agent.memory.record(trigger)

    ctx = await agent.compose_context([trigger])
    assert "trigger-only" not in ctx.current_thread
    # But the trigger is still presented as the trigger
    _, messages = ctx.to_llm_request()
    assert "trigger-only" in messages[0]["content"]


async def test_compose_context_isolates_threads(tmp_path: Path) -> None:
    """Other threads' history doesn't leak into this thread's context."""
    agent = await _agent(tmp_path)
    other_thread = _utterance(thread_id="OTHER", body="other-thread-content")
    await agent.memory.record(other_thread)

    trigger = _utterance(thread_id="t", body="this-thread")
    ctx = await agent.compose_context([trigger])
    assert "other-thread-content" not in ctx.current_thread


async def test_compose_context_orders_history_chronologically(tmp_path: Path) -> None:
    from datetime import UTC, datetime

    agent = await _agent(tmp_path)
    base = datetime(2026, 5, 4, 12, 0, 0, tzinfo=UTC)
    for i in range(3):
        await agent.memory.record(
            Utterance(
                thread_id="t",
                speaker=AgentIdentity(name="rabbit", constitution_version="0.1"),
                addressed_to="caucus",
                speech_act=SpeechAct.TICKET,
                content=UtteranceContent(body=f"#{i}"),
                timestamp=base.replace(second=i),
            )
        )
    trigger = _utterance(thread_id="t", body="now")
    ctx = await agent.compose_context([trigger])
    # All three appear, in order
    idx0 = ctx.current_thread.index("#0")
    idx1 = ctx.current_thread.index("#1")
    idx2 = ctx.current_thread.index("#2")
    assert idx0 < idx1 < idx2


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
    memory = AgentMemory.for_project(tmp_path, "cheshire_cat")
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
