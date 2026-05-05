"""Tests for the White Rabbit — second character to come online."""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from wonderland import (
    AgentIdentity,
    AgentMemory,
    Context,
    Engagement,
    InMemoryCaucus,
    LLMClient,
    RabbitResponseParseError,
    SpeechAct,
    TicketRegistry,
    Utterance,
    UtteranceContent,
    WhiteRabbit,
    parse_rabbit_response,
    white_rabbit_rules,
)

# ---------- helpers ----------


def _u(
    *,
    thread_id: str = "t",
    speaker: str = "alice",
    addressed: list[str] | str = "caucus",
    act: SpeechAct = SpeechAct.STORY,
    body: str = "...",
) -> Utterance:
    return Utterance(
        thread_id=thread_id,
        speaker=AgentIdentity(name=speaker, constitution_version="0.1"),
        addressed_to=(
            "caucus"
            if addressed == "caucus"
            else [AgentIdentity(name=n, constitution_version="0.1") for n in addressed]
        ),
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


async def _rabbit(
    tmp_path: Path,
    *,
    llm: LLMClient | None = None,
    with_registry: bool = True,
) -> WhiteRabbit:
    bus = InMemoryCaucus()
    memory = AgentMemory.for_project(tmp_path, "white_rabbit")
    await memory.open()
    registry = TicketRegistry(tmp_path) if with_registry else None
    return WhiteRabbit(memory=memory, bus=bus, llm=llm, ticket_registry=registry)


# ---------- engagement rules ----------


def test_rules_always_engages_with_directive() -> None:
    rules = white_rabbit_rules()
    assert rules.categorize(_u(act=SpeechAct.DIRECTIVE)) is Engagement.ALWAYS


def test_rules_story_only_from_alice() -> None:
    rules = white_rabbit_rules()
    assert rules.categorize(_u(act=SpeechAct.STORY, speaker="alice")) is Engagement.ALWAYS
    assert rules.categorize(_u(act=SpeechAct.STORY, speaker="dodo")) is Engagement.ALMOST_NEVER


def test_rules_proposal_from_cat_is_always() -> None:
    """Cat proposals always have scheduling implications per §III."""
    rules = white_rabbit_rules()
    assert rules.categorize(_u(act=SpeechAct.PROPOSAL, speaker="cheshire_cat")) is Engagement.ALWAYS


def test_rules_proposal_from_other_agent_is_rare() -> None:
    rules = white_rabbit_rules()
    assert rules.categorize(_u(act=SpeechAct.PROPOSAL, speaker="dodo")) is Engagement.RARELY


def test_rules_concern_engages_when_scope_or_schedule_word_present() -> None:
    rules = white_rabbit_rules()
    schedule = _u(act=SpeechAct.CONCERN, body="the timeline is slipping")
    pure_arch = _u(act=SpeechAct.CONCERN, body="the seam between A and B is fragile")
    assert rules.categorize(schedule) is Engagement.ALWAYS
    assert rules.categorize(pure_arch) is Engagement.ALMOST_NEVER


def test_rules_implementation_from_tweedles_is_always() -> None:
    rules = white_rabbit_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.IMPLEMENTATION, speaker="tweedledee"))
        is Engagement.ALWAYS
    )
    assert (
        rules.categorize(_u(act=SpeechAct.IMPLEMENTATION, speaker="tweedledum"))
        is Engagement.ALWAYS
    )


def test_rules_implementation_from_non_tweedle_is_skipped() -> None:
    rules = white_rabbit_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.IMPLEMENTATION, speaker="dodo"))
        is Engagement.ALMOST_NEVER
    )


def test_rules_observation_engages_on_incident_words() -> None:
    rules = white_rabbit_rules()
    incident = _u(act=SpeechAct.OBSERVATION, body="P1 outage in production")
    routine = _u(act=SpeechAct.OBSERVATION, body="latency p95 is 45ms today")
    assert rules.categorize(incident) is Engagement.SELECTIVELY
    assert rules.categorize(routine) is Engagement.ALMOST_NEVER


def test_rules_question_about_schedule_engages() -> None:
    rules = white_rabbit_rules()
    schedule_q = _u(act=SpeechAct.QUESTION, body="by when can we ship this?")
    other_q = _u(act=SpeechAct.QUESTION, body="what color should the button be?")
    assert rules.categorize(schedule_q) is Engagement.SELECTIVELY
    assert rules.categorize(other_q) is Engagement.ALMOST_NEVER


def test_rules_deference_is_skipped() -> None:
    rules = white_rabbit_rules()
    assert rules.categorize(_u(act=SpeechAct.DEFERENCE)) is Engagement.ALMOST_NEVER


# ---------- parse_rabbit_response ----------


def test_parse_silence() -> None:
    response = parse_rabbit_response('{"decision": "silence"}')
    assert response.decision == "silence"
    assert response.tickets == []


def test_parse_silence_coerces_explicit_nulls() -> None:
    """Live Haiku 4.5 sometimes emits explicit nulls instead of omitting fields."""
    response = parse_rabbit_response(
        '{"decision": "silence", "body": null, "tickets": null}'
    )
    assert response.decision == "silence"
    assert response.body == ""
    assert response.tickets == []


def test_parse_concern() -> None:
    text = '```json\n{"decision": "concern", "body": "scope is sliding"}\n```'
    response = parse_rabbit_response(text)
    assert response.decision == "concern"
    assert response.body == "scope is sliding"


def test_parse_ticket_decision_with_one_ticket() -> None:
    payload = {
        "decision": "ticket",
        "body": "Decomposing the directive into v1 work.",
        "tickets": [
            {
                "title": "Wire translation provider",
                "owner": "tweedledum",
                "tier": "v1",
                "estimate": "1-2 days, 65% confident",
                "description": "Add a single translation call per outbound message.",
            }
        ],
    }
    response = parse_rabbit_response(f"```json\n{json.dumps(payload)}\n```")
    assert response.decision == "ticket"
    assert len(response.tickets) == 1
    assert response.tickets[0].title == "Wire translation provider"


def test_parse_ticket_decision_with_multiple_tickets() -> None:
    payload = {
        "decision": "ticket",
        "body": "v1 cut.",
        "tickets": [
            {
                "title": "Backend translation route",
                "owner": "tweedledum",
                "tier": "v1",
                "estimate": "1d",
                "description": "POST /translate.",
            },
            {
                "title": "Frontend send-message flow",
                "owner": "tweedledee",
                "tier": "v1",
                "estimate": "1d",
                "description": "Wire the existing send button to call /translate before posting.",
            },
        ],
    }
    response = parse_rabbit_response(f"```json\n{json.dumps(payload)}\n```")
    assert len(response.tickets) == 2


def test_parse_rejects_ticket_decision_with_no_tickets() -> None:
    """decision=='ticket' but tickets=[] is nonsense."""
    with pytest.raises(RabbitResponseParseError):
        parse_rabbit_response('{"decision": "ticket", "body": "...", "tickets": []}')


def test_parse_rejects_invalid_decision() -> None:
    with pytest.raises(RabbitResponseParseError):
        parse_rabbit_response('{"decision": "cut", "body": "..."}')


def test_parse_rejects_missing_json() -> None:
    with pytest.raises(RabbitResponseParseError):
        parse_rabbit_response("just text")


# ---------- WhiteRabbit construction ----------


async def test_rabbit_loads_constitution(tmp_path: Path) -> None:
    rabbit = await _rabbit(tmp_path)
    assert rabbit.identity.name == "white_rabbit"
    assert "You are the White Rabbit" in rabbit.identity.constitution_text


async def test_rabbit_engagement_policy_wired(tmp_path: Path) -> None:
    rabbit = await _rabbit(tmp_path)
    directive = _u(act=SpeechAct.DIRECTIVE, speaker="dodo", body="build a thing")
    deference = _u(act=SpeechAct.DEFERENCE, speaker="alice")
    assert rabbit.should_engage(directive) is True
    assert rabbit.should_engage(deference) is False


async def test_rabbit_with_no_llm_is_silent(tmp_path: Path) -> None:
    rabbit = await _rabbit(tmp_path, llm=None)
    ctx = Context(constitution=rabbit.identity.constitution_text, triggers=(_u(),))
    assert await rabbit.deliberate(ctx) is None


# ---------- deliberate() ----------


async def test_deliberate_returns_none_on_silence(tmp_path: Path) -> None:
    llm = _mock_llm('```json\n{"decision": "silence"}\n```')
    rabbit = await _rabbit(tmp_path, llm=llm)
    ctx = Context(constitution=rabbit.identity.constitution_text, triggers=(_u(),))
    assert await rabbit.deliberate(ctx) is None


async def test_deliberate_publishes_concern(tmp_path: Path) -> None:
    body = "scope is sliding — story 7 needs a fast-follow cut"
    llm = _mock_llm(f"```json\n{json.dumps({'decision': 'concern', 'body': body})}\n```")
    rabbit = await _rabbit(tmp_path, llm=llm)
    trigger = _u(thread_id="t", body="we're behind")
    ctx = Context(constitution=rabbit.identity.constitution_text, triggers=(trigger,))

    utterance = await rabbit.deliberate(ctx)

    assert utterance is not None
    assert utterance.speech_act is SpeechAct.CONCERN
    assert utterance.content.body == body
    assert utterance.thread_id == "t"
    assert utterance.parent_id == trigger.id


async def test_deliberate_writes_tickets_through_registry(tmp_path: Path) -> None:
    payload = {
        "decision": "ticket",
        "body": "Decomposing the directive.",
        "tickets": [
            {
                "title": "Backend translation endpoint",
                "owner": "tweedledum",
                "tier": "v1",
                "estimate": "1d",
                "description": "POST /translate.",
            },
            {
                "title": "Frontend wiring",
                "owner": "tweedledee",
                "tier": "v1",
                "estimate": "0.5d",
                "description": "Call /translate before posting.",
            },
        ],
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    rabbit = await _rabbit(tmp_path, llm=llm)
    ctx = Context(constitution=rabbit.identity.constitution_text, triggers=(_u(),))

    utterance = await rabbit.deliberate(ctx)

    assert utterance is not None
    assert utterance.speech_act is SpeechAct.TICKET
    assert len(utterance.content.artifacts) == 2

    # Both files on disk
    tickets_dir = tmp_path / ".wonderland" / "tickets"
    files = sorted(tickets_dir.glob("ticket-*.md"))
    assert len(files) == 2
    titles = [f.read_text(encoding="utf-8").splitlines()[0] for f in files]
    assert any("Backend translation endpoint" in t for t in titles)
    assert any("Frontend wiring" in t for t in titles)


async def test_deliberate_drops_tickets_when_no_registry(tmp_path: Path) -> None:
    payload = {
        "decision": "ticket",
        "body": "...",
        "tickets": [
            {
                "title": "T",
                "owner": "tweedledee",
                "tier": "v1",
                "estimate": "1d",
                "description": "d",
            }
        ],
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    rabbit = await _rabbit(tmp_path, llm=llm, with_registry=False)
    ctx = Context(constitution=rabbit.identity.constitution_text, triggers=(_u(),))

    utterance = await rabbit.deliberate(ctx)

    assert utterance is not None
    assert utterance.speech_act is SpeechAct.TICKET
    assert utterance.content.artifacts == []  # no registry → no artifacts


async def test_deliberate_includes_protocol_in_system_prompt(tmp_path: Path) -> None:
    llm = _mock_llm('```json\n{"decision": "silence"}\n```')
    rabbit = await _rabbit(tmp_path, llm=llm)
    ctx = Context(constitution="C", triggers=(_u(),))
    await rabbit.deliberate(ctx)

    create_kwargs = rabbit.llm.client.messages.create.call_args.kwargs
    system_blocks = create_kwargs["system"]
    assert system_blocks[0]["text"] == "C"
    assert system_blocks[0]["cache_control"] == {"type": "ephemeral"}
    assert "fenced JSON block" in system_blocks[1]["text"]
    assert system_blocks[1]["cache_control"] == {"type": "ephemeral"}


# ---------- end-to-end (mocked LLM) ----------


async def test_end_to_end_directive_produces_tickets(tmp_path: Path) -> None:
    payload = {
        "decision": "ticket",
        "body": "Decomposing into v1 tickets.",
        "tickets": [
            {
                "title": "Translation service contract",
                "owner": "tweedledum",
                "tier": "v1",
                "estimate": "1d",
                "description": "Define the request/response shape for the translate endpoint.",
                "acceptance": ["spec posted to repo", "frontend can mock against it"],
            },
            {
                "title": "Frontend integration",
                "owner": "tweedledee",
                "tier": "v1",
                "estimate": "1d",
                "description": "Send button calls translate then posts.",
                "dependencies": {
                    "blocks": [],
                    "blocked_by": ["ticket-001-translation-service-contract"],
                    "soft": [],
                },
            },
        ],
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    rabbit = await _rabbit(tmp_path, llm=llm)
    observer = rabbit.bus.subscribe(agent_name="observer")

    run_task = asyncio.create_task(rabbit.run())
    await rabbit.bus.publish(
        _u(act=SpeechAct.DIRECTIVE, speaker="dodo", body="build a translation chat app")
    )

    received = await asyncio.wait_for(anext(observer), timeout=2.0)
    while received.speaker.name != "white_rabbit":
        received = await asyncio.wait_for(anext(observer), timeout=2.0)

    assert received.speech_act is SpeechAct.TICKET
    assert len(received.content.artifacts) == 2

    tickets_dir = tmp_path / ".wonderland" / "tickets"
    assert len(list(tickets_dir.glob("ticket-*.md"))) == 2

    await rabbit.stop()
    run_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await run_task
    await rabbit.memory.close()


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
async def test_live_rabbit_smoke(tmp_path: Path) -> None:
    """Real Haiku 4.5 round-trip: directive in, in-character Rabbit move out."""
    rabbit = await _rabbit(tmp_path, llm=LLMClient())
    observer = rabbit.bus.subscribe(agent_name="observer")
    run_task = asyncio.create_task(rabbit.run())

    await rabbit.bus.publish(
        _u(
            act=SpeechAct.DIRECTIVE,
            speaker="dodo",
            body=(
                "Build a translation-integrated chat application. Initial scope: "
                "two users in different language groups exchanging short messages "
                "with near-real-time translation."
            ),
        )
    )

    received = await asyncio.wait_for(anext(observer), timeout=30.0)
    while received.speaker.name != "white_rabbit":
        received = await asyncio.wait_for(anext(observer), timeout=30.0)

    assert received.speech_act in {
        SpeechAct.TICKET,
        SpeechAct.CONCERN,
        SpeechAct.QUESTION,
        SpeechAct.REFRAME,
    }
    assert len(received.content.body) > 20

    await rabbit.stop()
    run_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await run_task
    await rabbit.memory.close()
