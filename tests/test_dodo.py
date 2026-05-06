"""Tests for the Dodo — orchestrator, procedural-acts-only."""

from __future__ import annotations

import asyncio
import contextlib
from pathlib import Path

import pytest

from wonderland import (
    AgentIdentity,
    AgentMemory,
    Context,
    Dodo,
    Engagement,
    InMemoryCaucus,
    SpeechAct,
    Utterance,
    UtteranceContent,
    dodo_rules,
)

# ---------- helpers ----------


def _u(
    *,
    thread_id: str = "t",
    speaker: str = "white_rabbit",
    act: SpeechAct = SpeechAct.CONCERN,
    body: str = "...",
) -> Utterance:
    return Utterance(
        thread_id=thread_id,
        speaker=AgentIdentity(name=speaker, constitution_version="0.1"),
        addressed_to="caucus",
        speech_act=act,
        content=UtteranceContent(body=body),
    )


async def _dodo(tmp_path: Path) -> Dodo:
    bus = InMemoryCaucus()
    memory = AgentMemory.for_project(tmp_path, "dodo")
    await memory.open()
    return Dodo(memory=memory, bus=bus, llm=None)


# ---------- engagement rules ----------


def test_rules_engages_with_concern_carrying_conflict_words() -> None:
    rules = dodo_rules()
    conflict = _u(act=SpeechAct.CONCERN, body="we have a deadlock between A and B")
    routine = _u(act=SpeechAct.CONCERN, body="the button color looks wrong")
    assert rules.categorize(conflict) is Engagement.ALWAYS
    assert rules.categorize(routine) is Engagement.ALMOST_NEVER


def test_rules_always_engages_with_escalation() -> None:
    rules = dodo_rules()
    assert rules.categorize(_u(act=SpeechAct.ESCALATION)) is Engagement.ALWAYS


def test_rules_does_not_engage_with_directive() -> None:
    """Dodo issues directives (relays them); doesn't consume them.

    Listening for them on the bus would just produce echoes — and
    self-skip in WonderlandAgent.listen would catch his own anyway.
    """
    rules = dodo_rules()
    assert rules.categorize(_u(act=SpeechAct.DIRECTIVE)) is Engagement.ALMOST_NEVER


def test_rules_does_not_engage_with_deference() -> None:
    rules = dodo_rules()
    assert rules.categorize(_u(act=SpeechAct.DEFERENCE)) is Engagement.ALMOST_NEVER


def test_rules_does_not_engage_with_domain_content() -> None:
    """The Dodo's most pernicious failure mode (§VIII) — engaging with
    architecture/scope/quality discussions. These should never engage."""
    rules = dodo_rules()
    proposals = _u(act=SpeechAct.PROPOSAL, body="use Redis Streams for the bus")
    tickets = _u(act=SpeechAct.TICKET, body="implement /translate endpoint")
    reviews = _u(act=SpeechAct.REVIEW, body="this code path needs error handling")
    rulings = _u(act=SpeechAct.RULING, body="data residency: EU only")
    for utterance in (proposals, tickets, reviews, rulings):
        assert rules.categorize(utterance) is Engagement.ALMOST_NEVER


# ---------- Dodo construction ----------


async def test_loads_constitution_from_disk(tmp_path: Path) -> None:
    dodo = await _dodo(tmp_path)
    assert dodo.identity.name == "dodo"
    assert "You are the Dodo" in dodo.identity.constitution_text


async def test_engagement_policy_is_wired(tmp_path: Path) -> None:
    dodo = await _dodo(tmp_path)
    conflict = _u(act=SpeechAct.CONCERN, body="we are deadlocked")
    routine = _u(act=SpeechAct.PROPOSAL)
    assert dodo.should_engage(conflict) is True
    assert dodo.should_engage(routine) is False


async def test_constructs_without_llm(tmp_path: Path) -> None:
    """Dodo's mechanical acts don't need an LLM."""
    dodo = await _dodo(tmp_path)
    assert dodo.llm is None


# ---------- relay_directive ----------


async def test_relay_directive_publishes_directive_utterance(tmp_path: Path) -> None:
    dodo = await _dodo(tmp_path)
    observer = dodo.bus.subscribe(agent_name="observer")

    utterance = await dodo.relay_directive(
        body="Build a translation chat",
        thread_id="demo-thread",
    )

    assert utterance.speech_act is SpeechAct.DIRECTIVE
    assert utterance.speaker.name == "dodo"
    assert utterance.thread_id == "demo-thread"
    assert utterance.content.body == "Build a translation chat"

    # Observer sees it on the bus
    received = await anext(observer)
    assert received.id == utterance.id


async def test_relay_directive_records_in_memory(tmp_path: Path) -> None:
    dodo = await _dodo(tmp_path)
    await dodo.relay_directive(body="...", thread_id="t")
    assert await dodo.memory.count() == 1
    history = await dodo.memory.query_by_thread("t")
    assert history[0].speech_act is SpeechAct.DIRECTIVE


async def test_relay_directive_default_addressed_to_caucus(tmp_path: Path) -> None:
    dodo = await _dodo(tmp_path)
    utterance = await dodo.relay_directive(body="...", thread_id="t")
    assert utterance.addressed_to == "caucus"


# ---------- acknowledge ----------


async def test_acknowledge_publishes_acknowledgment(tmp_path: Path) -> None:
    dodo = await _dodo(tmp_path)
    observer = dodo.bus.subscribe(agent_name="observer")

    utterance = await dodo.acknowledge("demo-thread", state="complete")

    assert utterance.speech_act is SpeechAct.ACKNOWLEDGMENT
    assert utterance.speaker.name == "dodo"
    assert "complete" in utterance.content.body
    assert "demo-thread" in utterance.content.body

    received = await anext(observer)
    assert received.id == utterance.id


async def test_acknowledge_records_in_memory(tmp_path: Path) -> None:
    dodo = await _dodo(tmp_path)
    await dodo.acknowledge("t", state="quiescent")
    history = await dodo.memory.query_by_thread("t")
    assert history[0].speech_act is SpeechAct.ACKNOWLEDGMENT


async def test_acknowledge_accepts_custom_body(tmp_path: Path) -> None:
    dodo = await _dodo(tmp_path)
    custom = "Thread t complete: 4 tickets shipped, 1 ADR recorded, no escalations."
    utterance = await dodo.acknowledge("t", state="complete", body=custom)
    assert utterance.content.body == custom


@pytest.mark.parametrize(
    "state",
    ["running", "quiescent", "stuck", "deadlocked", "complete", "abandoned"],
)
async def test_acknowledge_accepts_each_documented_state(tmp_path: Path, state: str) -> None:
    dodo = await _dodo(tmp_path)
    utterance = await dodo.acknowledge("t", state=state)
    assert state in utterance.content.body


# ---------- deliberate is silent by default ----------


async def test_deliberate_returns_none_by_default(tmp_path: Path) -> None:
    """Per §VIII: performing orchestration is a failure mode the Dodo
    guards against. Per-utterance deliberation produces silence."""
    dodo = await _dodo(tmp_path)
    ctx = Context(constitution=dodo.identity.constitution_text, triggers=(_u(),))
    assert await dodo.deliberate(ctx) is None


async def test_deliberate_silent_even_on_engaged_concern(tmp_path: Path) -> None:
    """Dodo engages with conflict-bearing concerns to record + queue them,
    but the per-utterance deliberation is still silent in T17 — the
    state-machine actions live in T18+ (ThreadMonitor / conflict flow)."""
    dodo = await _dodo(tmp_path)
    conflict = _u(act=SpeechAct.CONCERN, body="we are stuck — deadlock between A and B")
    ctx = Context(constitution=dodo.identity.constitution_text, triggers=(conflict,))
    assert await dodo.deliberate(ctx) is None


# ---------- T33: nudge() — procedural reminder for STUCK threads ----------


async def test_nudge_publishes_nudge_utterance(tmp_path: Path) -> None:
    dodo = await _dodo(tmp_path)
    utterance = await dodo.nudge("t-stuck", reason="2 open expectation(s); silent 30.4s")
    assert utterance.speech_act is SpeechAct.NUDGE
    assert utterance.thread_id == "t-stuck"
    assert utterance.speaker.name == "dodo"
    assert "2 open expectation(s)" in utterance.content.body
    assert "stuck" in utterance.content.body.lower()


async def test_nudge_records_in_memory(tmp_path: Path) -> None:
    dodo = await _dodo(tmp_path)
    await dodo.nudge("t-stuck", reason="silent 30s")
    history = await dodo.memory.query_by_thread("t-stuck")
    assert len(history) == 1
    assert history[0].speech_act is SpeechAct.NUDGE


async def test_nudge_accepts_custom_body(tmp_path: Path) -> None:
    dodo = await _dodo(tmp_path)
    custom = "Pair has been negotiating for 3 turns without an artifact."
    utterance = await dodo.nudge("t-1", body=custom)
    assert utterance.content.body == custom


async def test_nudge_default_addressed_to_caucus(tmp_path: Path) -> None:
    dodo = await _dodo(tmp_path)
    utterance = await dodo.nudge("t-1", reason="silent")
    assert utterance.addressed_to == "caucus"


# ---------- T33: watch_thread_states() — wires monitor → procedural acts ----------


async def test_watch_emits_nudge_on_running_to_stuck(tmp_path: Path) -> None:
    """The structural anti-deadlock fix: STUCK transition → Dodo nudge."""

    from wonderland import ThreadMonitor

    bus = InMemoryCaucus()
    memory = AgentMemory.for_project(tmp_path, "dodo")
    await memory.open()
    dodo = Dodo(memory=memory, bus=bus, llm=None)

    # Subscribe an observer BEFORE the dodo's nudge so we can assert.
    observer = bus.subscribe(agent_name="observer")

    monitor = ThreadMonitor(bus, quiescence_seconds=0.1, check_interval=0.05)
    await monitor.start()

    watcher = asyncio.create_task(dodo.watch_thread_states(monitor))

    # Publish a question to open an expectation; the silent timer will fire STUCK.
    question = _u(act=SpeechAct.QUESTION, body="who owns this?", speaker="white_rabbit")
    await bus.publish(question)

    # Wait for the Dodo's NUDGE to land
    received: list[Utterance] = []
    try:
        async with asyncio.timeout(2.0):
            async for u in observer:
                received.append(u)
                if u.speaker.name == "dodo" and u.speech_act is SpeechAct.NUDGE:
                    break
    finally:
        watcher.cancel()
        with contextlib.suppress(asyncio.CancelledError, BaseException):
            await watcher
        await monitor.stop()
        await memory.close()

    nudges = [u for u in received if u.speech_act is SpeechAct.NUDGE]
    assert len(nudges) >= 1
    assert nudges[0].speaker.name == "dodo"
    # Confirm record_nudge was called
    info = monitor.thread_info(question.thread_id)
    assert info is not None
    assert info.nudge_count >= 1


async def test_watch_emits_acknowledge_on_quiescent(tmp_path: Path) -> None:
    """QUIESCENT transition → Dodo acknowledges with state=complete.

    Consolidates the thread-closure logic that showcase scripts
    previously did ad-hoc — running the watcher means the script
    doesn't have to wire QUIESCENT → acknowledge itself.
    """

    from wonderland import ThreadMonitor

    bus = InMemoryCaucus()
    memory = AgentMemory.for_project(tmp_path, "dodo")
    await memory.open()
    dodo = Dodo(memory=memory, bus=bus, llm=None)
    observer = bus.subscribe(agent_name="observer")

    monitor = ThreadMonitor(bus, quiescence_seconds=0.1, check_interval=0.05)
    await monitor.start()

    watcher = asyncio.create_task(dodo.watch_thread_states(monitor))

    # An OBSERVATION (not in expectation acts) means no open expectations;
    # silence after will trigger QUIESCENT (not STUCK).
    obs = _u(act=SpeechAct.OBSERVATION, speaker="dormouse", body="metrics nominal")
    await bus.publish(obs)

    received: list[Utterance] = []
    try:
        async with asyncio.timeout(2.0):
            async for u in observer:
                received.append(u)
                if (
                    u.speaker.name == "dodo"
                    and u.speech_act is SpeechAct.ACKNOWLEDGMENT
                    and "complete" in u.content.body.lower()
                ):
                    break
    finally:
        watcher.cancel()
        with contextlib.suppress(asyncio.CancelledError, BaseException):
            await watcher
        await monitor.stop()
        await memory.close()

    acks = [
        u for u in received if u.speech_act is SpeechAct.ACKNOWLEDGMENT and u.speaker.name == "dodo"
    ]
    assert len(acks) >= 1
    assert "complete" in acks[0].content.body.lower()


async def test_watch_acknowledges_deadlocked_when_no_escalation_registry(
    tmp_path: Path,
) -> None:
    """Without an escalation registry, DEADLOCKED falls back to a logged
    acknowledgment rather than raising RuntimeError. Keeps the watcher
    usable in lightweight setups."""

    from wonderland import ThreadMonitor, ThreadState
    from wonderland.thread_monitor import ThreadStateChange

    bus = InMemoryCaucus()
    memory = AgentMemory.for_project(tmp_path, "dodo")
    await memory.open()
    dodo = Dodo(memory=memory, bus=bus, llm=None, escalation_registry=None)

    observer = bus.subscribe(agent_name="observer")
    monitor = ThreadMonitor(bus, quiescence_seconds=10.0)

    # Inject a DEADLOCKED transition directly into the queue.
    from datetime import UTC, datetime

    change = ThreadStateChange(
        thread_id="t-deadlocked",
        from_state=ThreadState.STUCK,
        to_state=ThreadState.DEADLOCKED,
        at=datetime.now(UTC),
        reason="3 nudges, still 2 open",
    )
    await monitor._transitions.put(change)

    watcher = asyncio.create_task(dodo.watch_thread_states(monitor))

    received: list[Utterance] = []
    try:
        async with asyncio.timeout(2.0):
            async for u in observer:
                received.append(u)
                if u.speaker.name == "dodo" and u.speech_act is SpeechAct.ACKNOWLEDGMENT:
                    break
    finally:
        watcher.cancel()
        with contextlib.suppress(asyncio.CancelledError, BaseException):
            await watcher
        await memory.close()

    acks = [u for u in received if u.speech_act is SpeechAct.ACKNOWLEDGMENT]
    assert len(acks) == 1
    assert "deadlocked" in acks[0].content.body.lower()


# ---------- T33: escalate_deadlock() — templated brief for polite-deadlock ----------


async def test_escalate_deadlock_writes_brief_to_registry(tmp_path: Path) -> None:
    from wonderland import EscalationRegistry

    bus = InMemoryCaucus()
    memory = AgentMemory.for_project(tmp_path, "dodo")
    await memory.open()
    registry = EscalationRegistry(tmp_path)
    dodo = Dodo(memory=memory, bus=bus, llm=None, escalation_registry=registry)

    record = await dodo.escalate_deadlock(
        "t-stuck",
        reason="3 nudges, still 4 open expectations",
        thread_summary="The team has produced 80 utterances, 79% concerns, 0 implementations.",
        channel=lambda brief, record: None,  # silent channel
    )

    assert record.path.is_file()
    content = record.read()
    assert "polite" not in content.lower() or "stuck" in content.lower()
    assert "deadlock" in content.lower() or "stuck" in content.lower()


async def test_escalate_deadlock_publishes_escalation_utterance(tmp_path: Path) -> None:
    from wonderland import EscalationRegistry

    bus = InMemoryCaucus()
    memory = AgentMemory.for_project(tmp_path, "dodo")
    await memory.open()
    registry = EscalationRegistry(tmp_path)
    dodo = Dodo(memory=memory, bus=bus, llm=None, escalation_registry=registry)
    observer = bus.subscribe(agent_name="observer")

    await dodo.escalate_deadlock(
        "t-stuck",
        reason="silent 90s",
        channel=lambda brief, record: None,
    )

    received = [u async for u in _take_n(observer, 1)]
    assert received[0].speech_act is SpeechAct.ESCALATION
    assert received[0].speaker.name == "dodo"


async def test_escalate_deadlock_requires_registry(tmp_path: Path) -> None:
    bus = InMemoryCaucus()
    memory = AgentMemory.for_project(tmp_path, "dodo")
    await memory.open()
    dodo = Dodo(memory=memory, bus=bus, llm=None, escalation_registry=None)

    with pytest.raises(RuntimeError, match="escalation_registry"):
        await dodo.escalate_deadlock("t", reason="x")


# helper for grabbing a finite number of utterances from an iterator
async def _take_n(it, n: int):
    count = 0
    async for u in it:
        yield u
        count += 1
        if count >= n:
            break
