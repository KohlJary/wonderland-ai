"""Tests for the Dodo — orchestrator, procedural-acts-only."""

from __future__ import annotations

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
