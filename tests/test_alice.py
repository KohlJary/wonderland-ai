"""Tests for Alice — User / Product Owner."""

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
    Alice,
    AliceResponseParseError,
    Context,
    Engagement,
    InMemoryCaucus,
    LLMClient,
    SpeechAct,
    StoryRegistry,
    Utterance,
    UtteranceContent,
    alice_rules,
    parse_alice_response,
)

# ---------- helpers ----------


def _u(
    *,
    thread_id: str = "t",
    speaker: str = "dodo",
    addressed: list[str] | str = "caucus",
    act: SpeechAct = SpeechAct.DIRECTIVE,
    body: str = "build a translation chat app",
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


async def _alice(
    tmp_path: Path,
    *,
    llm: LLMClient | None = None,
    with_registry: bool = True,
) -> Alice:
    bus = InMemoryCaucus()
    memory = AgentMemory.for_project(tmp_path, "alice")
    await memory.open()
    registry = StoryRegistry(tmp_path) if with_registry else None
    return Alice(memory=memory, bus=bus, llm=llm, story_registry=registry)


def _story_dict(**overrides) -> dict:
    base = {
        "title": "Joiner sees translation",
        "persona": "Maya, 31, polyglot moderator",
        "situation": "She joins a busy multilingual chat.",
        "need": "As Maya, I want translations as they arrive, so that the chat reads as one stream.",
        "acceptance": ["translated message visible within 1s"],
        "tier": "core",
        "confusion_flags": ["what about translation provider failures"],
    }
    return base | overrides


# ---------- engagement rules ----------


def test_rules_always_engages_with_directive() -> None:
    rules = alice_rules()
    assert rules.categorize(_u(act=SpeechAct.DIRECTIVE)) is Engagement.ALWAYS


def test_rules_question_only_when_addressed_to_alice() -> None:
    rules = alice_rules()
    assert rules.categorize(_u(act=SpeechAct.QUESTION, addressed=["alice"])) is Engagement.ALWAYS
    assert (
        rules.categorize(_u(act=SpeechAct.QUESTION, addressed="caucus")) is Engagement.ALMOST_NEVER
    )


def test_rules_proposal_from_cat_is_always() -> None:
    rules = alice_rules()
    assert rules.categorize(_u(act=SpeechAct.PROPOSAL, speaker="cheshire_cat")) is Engagement.ALWAYS


def test_rules_proposal_from_other_is_rare() -> None:
    rules = alice_rules()
    assert rules.categorize(_u(act=SpeechAct.PROPOSAL, speaker="dodo")) is Engagement.RARELY


def test_rules_ticket_from_rabbit_is_always() -> None:
    rules = alice_rules()
    assert rules.categorize(_u(act=SpeechAct.TICKET, speaker="white_rabbit")) is Engagement.ALWAYS


def test_rules_test_scenario_from_hatter_is_always() -> None:
    """Per §III: Hatter's test_scenarios are 'a gift; engage with gratitude'."""
    rules = alice_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.TEST_SCENARIO, speaker="mad_hatter")) is Engagement.ALWAYS
    )


def test_rules_review_from_caterpillar_is_selective() -> None:
    rules = alice_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.REVIEW, speaker="caterpillar")) is Engagement.SELECTIVELY
    )


def test_rules_ruling_from_queen_is_selective() -> None:
    rules = alice_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.RULING, speaker="queen_of_hearts"))
        is Engagement.SELECTIVELY
    )


def test_rules_observation_from_dormouse_is_selective() -> None:
    rules = alice_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.OBSERVATION, speaker="dormouse"))
        is Engagement.SELECTIVELY
    )


def test_rules_deference_is_skipped() -> None:
    rules = alice_rules()
    assert rules.categorize(_u(act=SpeechAct.DEFERENCE)) is Engagement.ALMOST_NEVER


# ---------- parse_alice_response ----------


def test_parse_silence() -> None:
    response = parse_alice_response('{"decision": "silence"}')
    assert response.decision == "silence"
    assert response.stories == []


def test_parse_silence_coerces_explicit_nulls() -> None:
    """Live Haiku 4.5 sometimes emits explicit nulls instead of omitting fields."""
    response = parse_alice_response('{"decision": "silence", "body": null, "stories": null}')
    assert response.decision == "silence"
    assert response.body == ""
    assert response.stories == []


def test_parse_concern() -> None:
    text = '```json\n{"decision": "concern", "body": "the work is drifting from Maya"}\n```'
    response = parse_alice_response(text)
    assert response.decision == "concern"
    assert "drifting" in response.body


def test_parse_story_with_one_story() -> None:
    payload = {
        "decision": "story",
        "body": "First persona: Maya, the moderator drowning in cross-language threads.",
        "stories": [_story_dict()],
    }
    response = parse_alice_response(f"```json\n{json.dumps(payload)}\n```")
    assert response.decision == "story"
    assert len(response.stories) == 1
    assert response.stories[0].title == "Joiner sees translation"


def test_parse_story_with_multiple_stories() -> None:
    payload = {
        "decision": "story",
        "body": "Two personas this directive surfaces.",
        "stories": [
            _story_dict(title="Maya joins", persona="Maya, moderator"),
            _story_dict(title="Diego learns", persona="Diego, language learner"),
        ],
    }
    response = parse_alice_response(f"```json\n{json.dumps(payload)}\n```")
    assert len(response.stories) == 2


def test_parse_rejects_story_decision_with_no_stories() -> None:
    """decision='story' but stories=[] is nonsense."""
    with pytest.raises(AliceResponseParseError):
        parse_alice_response('{"decision": "story", "body": "...", "stories": []}')


def test_parse_rejects_story_with_empty_confusion_flags() -> None:
    """Schema validation propagates from StoryPayload — stories without
    flags are suspect and rejected at parse time."""
    payload = {
        "decision": "story",
        "body": "...",
        "stories": [_story_dict(confusion_flags=[])],
    }
    with pytest.raises(AliceResponseParseError):
        parse_alice_response(f"```json\n{json.dumps(payload)}\n```")


def test_parse_rejects_invalid_decision() -> None:
    with pytest.raises(AliceResponseParseError):
        parse_alice_response('{"decision": "demand", "body": "wat"}')


def test_parse_rejects_missing_json() -> None:
    with pytest.raises(AliceResponseParseError):
        parse_alice_response("just text")


# ---------- Alice construction ----------


async def test_alice_loads_constitution(tmp_path: Path) -> None:
    alice = await _alice(tmp_path)
    assert alice.identity.name == "alice"
    assert "You are Alice" in alice.identity.constitution_text


async def test_alice_engagement_policy_wired(tmp_path: Path) -> None:
    alice = await _alice(tmp_path)
    directive = _u(act=SpeechAct.DIRECTIVE, body="...")
    deference = _u(act=SpeechAct.DEFERENCE, speaker="cheshire_cat")
    assert alice.should_engage(directive) is True
    assert alice.should_engage(deference) is False


async def test_alice_with_no_llm_is_silent(tmp_path: Path) -> None:
    alice = await _alice(tmp_path, llm=None)
    ctx = Context(constitution=alice.identity.constitution_text, triggers=(_u(),))
    assert await alice.deliberate(ctx) is None


# ---------- deliberate ----------


async def test_deliberate_returns_none_on_silence(tmp_path: Path) -> None:
    llm = _mock_llm('```json\n{"decision": "silence"}\n```')
    alice = await _alice(tmp_path, llm=llm)
    ctx = Context(constitution=alice.identity.constitution_text, triggers=(_u(),))
    assert await alice.deliberate(ctx) is None


async def test_deliberate_publishes_concern(tmp_path: Path) -> None:
    body = "the v1 cut drops Maya — she's the core experience"
    llm = _mock_llm(f"```json\n{json.dumps({'decision': 'concern', 'body': body})}\n```")
    alice = await _alice(tmp_path, llm=llm)
    trigger = _u(thread_id="t", body="cutting story 7")
    ctx = Context(constitution=alice.identity.constitution_text, triggers=(trigger,))

    utterance = await alice.deliberate(ctx)

    assert utterance is not None
    assert utterance.speech_act is SpeechAct.CONCERN
    assert utterance.content.body == body
    assert utterance.thread_id == "t"
    assert utterance.parent_id == trigger.id


async def test_deliberate_writes_stories_through_registry(tmp_path: Path) -> None:
    payload = {
        "decision": "story",
        "body": "Personas this directive surfaces.",
        "stories": [
            _story_dict(title="Maya joins multilingual chat"),
            _story_dict(title="Diego practices Mandarin", persona="Diego, 24"),
        ],
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    alice = await _alice(tmp_path, llm=llm)
    ctx = Context(constitution=alice.identity.constitution_text, triggers=(_u(),))

    utterance = await alice.deliberate(ctx)

    assert utterance is not None
    assert utterance.speech_act is SpeechAct.STORY
    assert len(utterance.content.artifacts) == 2

    stories_dir = tmp_path / ".wonderland" / "stories"
    files = sorted(stories_dir.glob("story-*.md"))
    assert len(files) == 2


async def test_deliberate_drops_stories_when_no_registry(tmp_path: Path) -> None:
    payload = {
        "decision": "story",
        "body": "...",
        "stories": [_story_dict()],
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    alice = await _alice(tmp_path, llm=llm, with_registry=False)
    ctx = Context(constitution=alice.identity.constitution_text, triggers=(_u(),))

    utterance = await alice.deliberate(ctx)

    assert utterance is not None
    assert utterance.speech_act is SpeechAct.STORY
    assert utterance.content.artifacts == []


async def test_deliberate_includes_protocol_in_system_prompt(tmp_path: Path) -> None:
    llm = _mock_llm('```json\n{"decision": "silence"}\n```')
    alice = await _alice(tmp_path, llm=llm)
    ctx = Context(constitution="C", triggers=(_u(),))
    await alice.deliberate(ctx)

    create_kwargs = alice.llm.client.messages.create.call_args.kwargs
    system_blocks = create_kwargs["system"]
    # Position 0 is the framework primer (shared across all agents)
    assert "Wonderland — Framework Primer" in system_blocks[0]["text"]
    assert "cache_control" not in system_blocks[0]  # framework primer is plain string since context-compression Lever A (cache breakpoint reused for current_thread)
    # Position 1 is the per-agent constitution
    assert system_blocks[1]["text"] == "C"
    assert system_blocks[1]["cache_control"] == {"type": "ephemeral"}
    assert "fenced JSON block" in system_blocks[2]["text"]
    assert system_blocks[2]["cache_control"] == {"type": "ephemeral"}


# ---------- end-to-end (mocked LLM) ----------


async def test_end_to_end_directive_produces_stories(tmp_path: Path) -> None:
    payload = {
        "decision": "story",
        "body": "Two personas this surfaces.",
        "stories": [_story_dict(title="Maya joins"), _story_dict(title="Diego learns")],
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    alice = await _alice(tmp_path, llm=llm)
    observer = alice.bus.subscribe(agent_name="observer")

    run_task = asyncio.create_task(alice.run())
    await alice.bus.publish(_u(act=SpeechAct.DIRECTIVE, body="build something"))

    received = await asyncio.wait_for(anext(observer), timeout=2.0)
    while received.speaker.name != "alice":
        received = await asyncio.wait_for(anext(observer), timeout=2.0)

    assert received.speech_act is SpeechAct.STORY
    assert len(received.content.artifacts) == 2

    stories_dir = tmp_path / ".wonderland" / "stories"
    assert len(list(stories_dir.glob("story-*.md"))) == 2

    await alice.stop()
    run_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await run_task
    await alice.memory.close()


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
async def test_live_alice_smoke(tmp_path: Path) -> None:
    """Real Haiku 4.5 round-trip: directive in, in-character Alice move out."""
    alice = await _alice(tmp_path, llm=LLMClient())
    observer = alice.bus.subscribe(agent_name="observer")
    run_task = asyncio.create_task(alice.run())

    await alice.bus.publish(
        _u(
            act=SpeechAct.DIRECTIVE,
            body=(
                "Build a translation-integrated chat application. Initial scope: "
                "two users in different language groups exchanging short messages "
                "with near-real-time translation."
            ),
        )
    )

    received = await asyncio.wait_for(anext(observer), timeout=30.0)
    while received.speaker.name != "alice":
        received = await asyncio.wait_for(anext(observer), timeout=30.0)

    assert received.speech_act in {
        SpeechAct.STORY,
        SpeechAct.QUESTION,
        SpeechAct.CONCERN,
        SpeechAct.REFRAME,
    }
    assert len(received.content.body) > 20

    await alice.stop()
    run_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await run_task
    await alice.memory.close()
