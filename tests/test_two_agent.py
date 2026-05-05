"""Two-agent integration: Cat + Rabbit on the same bus.

This is P3's first observation point. With two voices live, we can verify
the substrate honors role boundaries the constitutions demand:

- Each agent produces its characteristic artifact (Cat → ADR, Rabbit → Ticket)
- The Rabbit records the Cat's proposals (always-engage per §III)
- The Cat skips routine Rabbit tickets — engagement is *asymmetric* by design

Mocked LLM tests handle the assertions; the live smoke (gated) lets us watch
the natural dance against Haiku 4.5 for the analyses transcript.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
from collections.abc import AsyncIterator
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from wonderland import (
    ADRRegistry,
    AgentIdentity,
    AgentMemory,
    CheshireCat,
    InMemoryCaucus,
    LLMClient,
    SpeechAct,
    TicketRegistry,
    Utterance,
    UtteranceContent,
    WhiteRabbit,
)

# ---------- helpers ----------


def _u(
    *,
    thread_id: str = "demo-thread",
    speaker: str = "dodo",
    act: SpeechAct = SpeechAct.DIRECTIVE,
    body: str = "...",
) -> Utterance:
    return Utterance(
        thread_id=thread_id,
        speaker=AgentIdentity(name=speaker, constitution_version="0.1"),
        addressed_to="caucus",
        speech_act=act,
        content=UtteranceContent(body=body),
    )


def _mock_llm(text: str) -> LLMClient:
    response = SimpleNamespace(
        content=[SimpleNamespace(type="text", text=text)],
        stop_reason="end_turn",
        usage=SimpleNamespace(
            input_tokens=10,
            output_tokens=5,
            cache_creation_input_tokens=0,
            cache_read_input_tokens=0,
        ),
    )
    client = MagicMock()
    client.messages = MagicMock()
    client.messages.create = AsyncMock(return_value=response)
    return LLMClient(client=client)


async def _setup_pair(
    tmp_path: Path,
    *,
    cat_response: str,
    rabbit_response: str,
) -> tuple[CheshireCat, WhiteRabbit, InMemoryCaucus]:
    bus = InMemoryCaucus()
    cat_memory = AgentMemory.for_project(tmp_path, "cheshire_cat")
    rabbit_memory = AgentMemory.for_project(tmp_path, "white_rabbit")
    await cat_memory.open()
    await rabbit_memory.open()

    cat = CheshireCat(
        memory=cat_memory,
        bus=bus,
        llm=_mock_llm(cat_response),
        adr_registry=ADRRegistry(tmp_path),
    )
    rabbit = WhiteRabbit(
        memory=rabbit_memory,
        bus=bus,
        llm=_mock_llm(rabbit_response),
        ticket_registry=TicketRegistry(tmp_path),
    )
    return cat, rabbit, bus


async def _collect_until(
    sub: AsyncIterator[Utterance],
    *,
    speakers: set[str],
    timeout_per_step: float = 2.0,
) -> dict[str, Utterance]:
    seen: dict[str, Utterance] = {}
    while set(seen.keys()) != speakers:
        u = await asyncio.wait_for(anext(sub), timeout=timeout_per_step)
        if u.speaker.name in speakers:
            seen.setdefault(u.speaker.name, u)
    return seen


async def _shutdown(*agents: CheshireCat | WhiteRabbit) -> None:
    for agent in agents:
        await agent.stop()
        await agent.memory.close()


# ---------- mocked: each agent produces its characteristic artifact ----------


async def test_directive_produces_cat_proposal_and_rabbit_tickets(tmp_path: Path) -> None:
    cat_response = json.dumps(
        {
            "decision": "proposal",
            "body": "Use a synchronous-first translation pipeline with explicit fallback.",
            "adr": {
                "title": "Synchronous-first translation",
                "context": "Two users; near-real-time message latency.",
                "decision": "Translate synchronously per outbound message; fall back to placeholder + retry on translation provider error.",
                "tradeoffs": [
                    "translation provider latency directly bounds message latency",
                    "no batching opportunities for cost savings",
                    "simpler delivery semantics",
                ],
            },
        }
    )
    rabbit_response = json.dumps(
        {
            "decision": "ticket",
            "body": "Decomposing the directive into v1 tickets.",
            "tickets": [
                {
                    "title": "Translation provider client",
                    "owner": "tweedledum",
                    "tier": "v1",
                    "estimate": "1-2 days, 60% confident",
                    "description": "Wrap the translation API; handle errors per Cat proposal.",
                    "sources": ["adr-001"],
                },
                {
                    "title": "Frontend send-message integration",
                    "owner": "tweedledee",
                    "tier": "v1",
                    "estimate": "0.5-1 day, 70% confident",
                    "description": "Call /translate before posting on the send action.",
                    "dependencies": {
                        "blocks": [],
                        "blocked_by": ["ticket-001-translation-provider-client"],
                        "soft": [],
                    },
                },
            ],
        }
    )

    cat, rabbit, bus = await _setup_pair(
        tmp_path,
        cat_response=f"```json\n{cat_response}\n```",
        rabbit_response=f"```json\n{rabbit_response}\n```",
    )
    observer = bus.subscribe(agent_name="observer")
    cat_task = asyncio.create_task(cat.run())
    rabbit_task = asyncio.create_task(rabbit.run())

    await bus.publish(_u(body="Build a translation-integrated chat application."))

    seen = await _collect_until(observer, speakers={"cheshire_cat", "white_rabbit"})

    cat_utterance = seen["cheshire_cat"]
    rabbit_utterance = seen["white_rabbit"]

    assert cat_utterance.speech_act is SpeechAct.PROPOSAL
    assert rabbit_utterance.speech_act is SpeechAct.TICKET

    # Each agent produced its characteristic artifact, and *only* its
    # characteristic artifact.
    cat_artifact_kinds = {a.kind for a in cat_utterance.content.artifacts}
    rabbit_artifact_kinds = {a.kind for a in rabbit_utterance.content.artifacts}
    assert cat_artifact_kinds == {"adr"}
    assert rabbit_artifact_kinds == {"ticket"}

    # Files on disk in their respective domains
    adr_files = list((tmp_path / ".wonderland" / "architecture").glob("adr-*.md"))
    ticket_files = list((tmp_path / ".wonderland" / "tickets").glob("ticket-*.md"))
    assert len(adr_files) == 1
    assert len(ticket_files) == 2

    await _shutdown(cat, rabbit)
    cat_task.cancel()
    rabbit_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await cat_task
    with contextlib.suppress(asyncio.CancelledError):
        await rabbit_task


# ---------- mocked: asymmetric engagement ----------


async def test_rabbit_records_cat_proposal_in_episodic_memory(tmp_path: Path) -> None:
    """Per Rabbit §III, proposals from the Cat are always-engage. Verify."""
    cat_response = json.dumps(
        {
            "decision": "proposal",
            "body": "Reframe — what does 'near-real-time' mean here?",
        }
    )
    # Rabbit silent — we only care that he sees and records the Cat's proposal.
    rabbit_response = json.dumps({"decision": "silence"})

    cat, rabbit, bus = await _setup_pair(
        tmp_path,
        cat_response=f"```json\n{cat_response}\n```",
        rabbit_response=f"```json\n{rabbit_response}\n```",
    )
    observer = bus.subscribe(agent_name="observer")
    cat_task = asyncio.create_task(cat.run())
    rabbit_task = asyncio.create_task(rabbit.run())

    await bus.publish(_u(body="Build a translation chat app."))

    # Wait until the Cat has spoken (which means the Rabbit has had a chance to
    # observe it — the bus is single-threaded and listen() is in the same loop).
    while True:
        u = await asyncio.wait_for(anext(observer), timeout=2.0)
        if u.speaker.name == "cheshire_cat":
            break

    # Give the Rabbit a tick to process the Cat's proposal
    await asyncio.sleep(0.05)

    rabbit_history = await rabbit.memory.query_by_speaker("cheshire_cat")
    assert len(rabbit_history) == 1
    assert rabbit_history[0].speech_act is SpeechAct.PROPOSAL

    await _shutdown(cat, rabbit)
    cat_task.cancel()
    rabbit_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await cat_task
    with contextlib.suppress(asyncio.CancelledError):
        await rabbit_task


async def test_cat_skips_routine_rabbit_ticket_in_episodic_memory(tmp_path: Path) -> None:
    """Per Cat §III: routine ticket decomposition is ALMOST_NEVER.

    A Rabbit ticket without an implementation hint that constrains
    architecture should not show up in the Cat's memory.
    """
    # The Cat is silent — we only care about what he records, not what he says.
    cat_response = json.dumps({"decision": "silence"})
    # The Rabbit issues a routine ticket — no architectural smell.
    rabbit_response = json.dumps(
        {
            "decision": "ticket",
            "body": "Routine v1 work.",
            "tickets": [
                {
                    "title": "Add a profile photo button",
                    "owner": "tweedledee",
                    "tier": "v1",
                    "estimate": "0.5d",
                    "description": "Wire the existing image upload to a profile button.",
                }
            ],
        }
    )

    cat, rabbit, bus = await _setup_pair(
        tmp_path,
        cat_response=f"```json\n{cat_response}\n```",
        rabbit_response=f"```json\n{rabbit_response}\n```",
    )
    observer = bus.subscribe(agent_name="observer")
    cat_task = asyncio.create_task(cat.run())
    rabbit_task = asyncio.create_task(rabbit.run())

    # The directive needs to be a story the Rabbit will engage with so he
    # produces the routine ticket. Use a story-from-Alice trigger.
    await bus.publish(
        _u(
            speaker="alice",
            act=SpeechAct.STORY,
            body="A user can upload a profile photo from settings.",
        )
    )

    # Wait until the Rabbit has spoken his ticket
    while True:
        u = await asyncio.wait_for(anext(observer), timeout=2.0)
        if u.speaker.name == "white_rabbit":
            break

    # Let the Cat's listen loop process the published Rabbit ticket
    await asyncio.sleep(0.05)

    # Cat's memory should NOT contain the Rabbit's routine ticket
    cat_history_from_rabbit = await cat.memory.query_by_speaker("white_rabbit")
    assert cat_history_from_rabbit == []

    await _shutdown(cat, rabbit)
    cat_task.cancel()
    rabbit_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await cat_task
    with contextlib.suppress(asyncio.CancelledError):
        await rabbit_task


async def test_cat_engages_with_rabbit_ticket_carrying_architectural_smell(
    tmp_path: Path,
) -> None:
    """Same speaker, same speech_act — different engagement based on body content.

    The Cat's heuristic looks at the utterance body for architectural smell.
    A Rabbit ticket whose body explicitly raises the synchronous-call concern
    crosses Cat's threshold. (Smell words buried only in artifact payloads
    won't trigger the heuristic — the LLM would see them through episodic
    memory if engagement happened, but the heuristic is the coarse filter
    before that.)
    """
    cat_response = json.dumps({"decision": "silence"})
    rabbit_response = json.dumps(
        {
            "decision": "ticket",
            "body": "Cat — this ticket assumes a synchronous call per message; "
            "want your read on the architectural shape before I commit.",
            "tickets": [
                {
                    "title": "Synchronous translation pipeline",
                    "owner": "tweedledum",
                    "tier": "v1",
                    "estimate": "1d",
                    "description": "Wire the translation API into the message send path.",
                }
            ],
        }
    )

    cat, rabbit, bus = await _setup_pair(
        tmp_path,
        cat_response=f"```json\n{cat_response}\n```",
        rabbit_response=f"```json\n{rabbit_response}\n```",
    )
    observer = bus.subscribe(agent_name="observer")
    cat_task = asyncio.create_task(cat.run())
    rabbit_task = asyncio.create_task(rabbit.run())

    await bus.publish(
        _u(speaker="alice", act=SpeechAct.STORY, body="user sends a message in Mandarin")
    )

    while True:
        u = await asyncio.wait_for(anext(observer), timeout=2.0)
        if u.speaker.name == "white_rabbit":
            break

    await asyncio.sleep(0.05)

    cat_history_from_rabbit = await cat.memory.query_by_speaker("white_rabbit")
    assert len(cat_history_from_rabbit) == 1
    assert cat_history_from_rabbit[0].speech_act is SpeechAct.TICKET

    await _shutdown(cat, rabbit)
    cat_task.cancel()
    rabbit_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await cat_task
    with contextlib.suppress(asyncio.CancelledError):
        await rabbit_task


# ---------- live smoke (opt-in) ----------


def _api_key_resolvable() -> bool:
    if os.environ.get("ANTHROPIC_API_KEY"):
        return True
    try:
        from wonderland.config import load_config

        return bool(load_config().anthropic.api_key)
    except Exception:
        return False


SMOKE_ENABLED = os.environ.get("WONDERLAND_LLM_SMOKE") == "1"
smoke_required = pytest.mark.skipif(
    not SMOKE_ENABLED or not _api_key_resolvable(),
    reason="set WONDERLAND_LLM_SMOKE=1 and provide an API key (env or config) to run live smoke",
)


@smoke_required
async def test_live_two_agent_dance(tmp_path: Path) -> None:
    """Cat + Rabbit live against Haiku 4.5. Observe role boundaries hold."""
    bus = InMemoryCaucus()
    cat_memory = AgentMemory.for_project(tmp_path, "cheshire_cat")
    rabbit_memory = AgentMemory.for_project(tmp_path, "white_rabbit")
    await cat_memory.open()
    await rabbit_memory.open()

    cat = CheshireCat(
        memory=cat_memory,
        bus=bus,
        llm=LLMClient(),
        adr_registry=ADRRegistry(tmp_path),
    )
    rabbit = WhiteRabbit(
        memory=rabbit_memory,
        bus=bus,
        llm=LLMClient(),
        ticket_registry=TicketRegistry(tmp_path),
    )
    observer = bus.subscribe(agent_name="observer")
    cat_task = asyncio.create_task(cat.run())
    rabbit_task = asyncio.create_task(rabbit.run())

    await bus.publish(
        _u(
            body=(
                "Build a translation-integrated chat application. Initial scope: "
                "two users in different language groups exchanging short messages "
                "with near-real-time translation."
            )
        )
    )

    seen: dict[str, Utterance] = {}
    deadline = asyncio.get_event_loop().time() + 30.0
    while {"cheshire_cat", "white_rabbit"} - set(seen.keys()):
        remaining = deadline - asyncio.get_event_loop().time()
        if remaining <= 0:
            break
        u = await asyncio.wait_for(anext(observer), timeout=remaining)
        if u.speaker.name in {"cheshire_cat", "white_rabbit"} and u.speaker.name not in seen:
            seen[u.speaker.name] = u

    assert "cheshire_cat" in seen, "Cat did not speak within 30s"
    assert "white_rabbit" in seen, "Rabbit did not speak within 30s"

    cat_utterance = seen["cheshire_cat"]
    rabbit_utterance = seen["white_rabbit"]

    # Cat's domain: architectural acts only
    assert cat_utterance.speech_act in {
        SpeechAct.PROPOSAL,
        SpeechAct.QUESTION,
        SpeechAct.REFRAME,
        SpeechAct.CONCERN,
        SpeechAct.DEFERENCE,
    }
    # Cat must not have produced a ticket artifact
    assert all(a.kind != "ticket" for a in cat_utterance.content.artifacts)

    # Rabbit's domain: scheduling acts only
    assert rabbit_utterance.speech_act in {
        SpeechAct.TICKET,
        SpeechAct.QUESTION,
        SpeechAct.CONCERN,
        SpeechAct.REFRAME,
        SpeechAct.DEFERENCE,
    }
    # Rabbit must not have produced an ADR artifact
    assert all(a.kind != "adr" for a in rabbit_utterance.content.artifacts)

    await _shutdown(cat, rabbit)
    cat_task.cancel()
    rabbit_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await cat_task
    with contextlib.suppress(asyncio.CancelledError):
        await rabbit_task
