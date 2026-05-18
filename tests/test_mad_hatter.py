"""Tests for the Mad Hatter — QA / Testing."""

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
    HatterResponseParseError,
    InMemoryCaucus,
    LLMClient,
    MadHatter,
    SpeechAct,
    TestScenarioRegistry,
    Utterance,
    UtteranceContent,
    mad_hatter_rules,
    parse_hatter_response,
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


async def _hatter(
    tmp_path: Path,
    *,
    llm: LLMClient | None = None,
    with_registry: bool = True,
) -> MadHatter:
    bus = InMemoryCaucus()
    memory = AgentMemory.for_project(tmp_path, "mad_hatter")
    await memory.open()
    registry = TestScenarioRegistry(tmp_path) if with_registry else None
    return MadHatter(memory=memory, bus=bus, llm=llm, test_scenario_registry=registry)


def _scenario_dict(**overrides) -> dict:
    base = {
        "title": "User pastes 40,000 emoji into a one-line message field",
        "severity": "silent-wrongness",
        "setup": "Composer that advertises 280-char limit but does no client enforcement.",
        "trigger": "User pastes huge emoji block and presses send.",
        "expected": "Message rejected with a clear error before it leaves the device.",
        "concern": "Emoji are sliced byte-wise, not grapheme-wise; recipient renders garbage.",
        "property": "",
        "implies": [],
    }
    return base | overrides


# ---------- engagement rules ----------


def test_rules_always_engages_with_directive() -> None:
    rules = mad_hatter_rules()
    assert rules.categorize(_u(act=SpeechAct.DIRECTIVE)) is Engagement.ALWAYS


def test_rules_story_engages_regardless_of_author() -> None:
    """Caterpillar joined Alice as a story author at M1 (plumbing
    stories — commit 61172d3); Hatter's story engagement no longer
    hardcodes speaker_is('alice'). The §IV "does not issue stories"
    discipline is preserved by the listen-loop's self-skip
    (agents don't engage with their own emissions); the engagement
    rule just decides whose stories he reads to derive scenarios
    from, and that's anyone shipping stories."""
    rules = mad_hatter_rules()
    assert rules.categorize(_u(act=SpeechAct.STORY, speaker="alice", body="x")) is Engagement.ALWAYS
    assert (
        rules.categorize(_u(act=SpeechAct.STORY, speaker="caterpillar", body="x"))
        is Engagement.ALWAYS
    )
    assert rules.categorize(_u(act=SpeechAct.STORY, speaker="dodo", body="x")) is Engagement.ALWAYS


def test_rules_proposal_from_cat_is_always() -> None:
    rules = mad_hatter_rules()
    assert rules.categorize(_u(act=SpeechAct.PROPOSAL, speaker="cheshire_cat")) is Engagement.ALWAYS


def test_rules_proposal_from_other_is_almost_never() -> None:
    rules = mad_hatter_rules()
    assert rules.categorize(_u(act=SpeechAct.PROPOSAL, speaker="dodo")) is Engagement.ALMOST_NEVER


def test_rules_implementation_from_tweedle_is_always() -> None:
    rules = mad_hatter_rules()
    for tweedle in ("tweedledee", "tweedledum"):
        assert (
            rules.categorize(_u(act=SpeechAct.IMPLEMENTATION, speaker=tweedle)) is Engagement.ALWAYS
        )


def test_rules_implementation_from_other_is_almost_never() -> None:
    rules = mad_hatter_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.IMPLEMENTATION, speaker="dodo"))
        is Engagement.ALMOST_NEVER
    )


def test_rules_concern_from_anyone_is_always() -> None:
    """Per §III: 'somebody noticed something; you want to know what.'"""
    rules = mad_hatter_rules()
    for speaker in ("alice", "cheshire_cat", "white_rabbit", "dormouse"):
        assert rules.categorize(_u(act=SpeechAct.CONCERN, speaker=speaker)) is Engagement.ALWAYS


def test_rules_question_only_when_addressed_to_hatter() -> None:
    rules = mad_hatter_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.QUESTION, addressed=["mad_hatter"])) is Engagement.ALWAYS
    )
    assert (
        rules.categorize(_u(act=SpeechAct.QUESTION, addressed="caucus")) is Engagement.ALMOST_NEVER
    )


def test_rules_ticket_from_rabbit_is_selective() -> None:
    rules = mad_hatter_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.TICKET, speaker="white_rabbit")) is Engagement.SELECTIVELY
    )


def test_rules_review_from_caterpillar_is_selective() -> None:
    rules = mad_hatter_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.REVIEW, speaker="caterpillar")) is Engagement.SELECTIVELY
    )


def test_rules_ruling_from_queen_is_selective() -> None:
    rules = mad_hatter_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.RULING, speaker="queen_of_hearts"))
        is Engagement.SELECTIVELY
    )


def test_rules_observation_from_dormouse_is_selective() -> None:
    rules = mad_hatter_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.OBSERVATION, speaker="dormouse"))
        is Engagement.SELECTIVELY
    )


def test_rules_deference_is_rare() -> None:
    rules = mad_hatter_rules()
    assert rules.categorize(_u(act=SpeechAct.DEFERENCE)) is Engagement.RARELY


# ---------- parse_hatter_response ----------


def test_parse_silence() -> None:
    response = parse_hatter_response('{"decision": "silence"}')
    assert response.decision == "silence"
    assert response.scenarios == []


def test_parse_silence_coerces_explicit_nulls() -> None:
    """Live Haiku 4.5 sometimes emits explicit nulls for omitted fields."""
    response = parse_hatter_response('{"decision": "silence", "body": null, "scenarios": null}')
    assert response.decision == "silence"
    assert response.body == ""
    assert response.scenarios == []


def test_parse_concern() -> None:
    text = '```json\n{"decision": "concern", "body": "third retry-path bug this month"}\n```'
    response = parse_hatter_response(text)
    assert response.decision == "concern"
    assert "retry-path" in response.body


def test_parse_observation() -> None:
    text = '{"decision": "observation", "body": "pattern across threads: i18n boundary"}'
    response = parse_hatter_response(text)
    assert response.decision == "observation"


def test_parse_test_scenario_with_one_scenario() -> None:
    payload = {
        "decision": "test_scenario",
        "body": "Edge case worth surfacing.",
        "scenarios": [_scenario_dict()],
    }
    response = parse_hatter_response(f"```json\n{json.dumps(payload)}\n```")
    assert response.decision == "test_scenario"
    assert len(response.scenarios) == 1
    assert response.scenarios[0].severity.value == "silent-wrongness"


def test_parse_test_scenario_with_multiple_scenarios() -> None:
    payload = {
        "decision": "test_scenario",
        "body": "Two edges around this feature.",
        "scenarios": [
            _scenario_dict(title="emoji overflow"),
            _scenario_dict(title="leap-second clock skew", severity="degradation"),
        ],
    }
    response = parse_hatter_response(f"```json\n{json.dumps(payload)}\n```")
    assert len(response.scenarios) == 2


def test_parse_rejects_test_scenario_decision_with_no_scenarios() -> None:
    with pytest.raises(HatterResponseParseError):
        parse_hatter_response('{"decision": "test_scenario", "body": "...", "scenarios": []}')


def test_parse_rejects_scenario_with_empty_concern() -> None:
    """Schema validation propagates from TestScenarioPayload — concerns
    are the grin equivalent and required."""
    payload = {
        "decision": "test_scenario",
        "body": "...",
        "scenarios": [_scenario_dict(concern="")],
    }
    with pytest.raises(HatterResponseParseError):
        parse_hatter_response(f"```json\n{json.dumps(payload)}\n```")


def test_parse_rejects_invalid_severity() -> None:
    payload = {
        "decision": "test_scenario",
        "body": "...",
        "scenarios": [_scenario_dict(severity="critical")],
    }
    with pytest.raises(HatterResponseParseError):
        parse_hatter_response(f"```json\n{json.dumps(payload)}\n```")


def test_parse_rejects_invalid_decision() -> None:
    with pytest.raises(HatterResponseParseError):
        parse_hatter_response('{"decision": "pontification"}')


def test_parse_rejects_missing_json() -> None:
    with pytest.raises(HatterResponseParseError):
        parse_hatter_response("just plain text")


# ---------- MadHatter construction ----------


async def test_hatter_loads_constitution(tmp_path: Path) -> None:
    hatter = await _hatter(tmp_path)
    assert hatter.identity.name == "mad_hatter"
    assert "Mad Hatter" in hatter.identity.constitution_text


async def test_hatter_engagement_policy_wired(tmp_path: Path) -> None:
    hatter = await _hatter(tmp_path)
    directive = _u(act=SpeechAct.DIRECTIVE, body="...")
    foreign_proposal = _u(act=SpeechAct.PROPOSAL, speaker="dodo")
    assert hatter.should_engage(directive) is True
    assert hatter.should_engage(foreign_proposal) is False


async def test_hatter_with_no_llm_is_silent(tmp_path: Path) -> None:
    hatter = await _hatter(tmp_path, llm=None)
    ctx = Context(constitution=hatter.identity.constitution_text, triggers=(_u(),))
    assert await hatter.deliberate(ctx) is None


# ---------- deliberate ----------


async def test_deliberate_returns_none_on_silence(tmp_path: Path) -> None:
    llm = _mock_llm('```json\n{"decision": "silence"}\n```')
    hatter = await _hatter(tmp_path, llm=llm)
    ctx = Context(constitution=hatter.identity.constitution_text, triggers=(_u(),))
    assert await hatter.deliberate(ctx) is None


async def test_deliberate_publishes_concern(tmp_path: Path) -> None:
    body = "this is the third retry-path bug this month — class concern"
    llm = _mock_llm(f"```json\n{json.dumps({'decision': 'concern', 'body': body})}\n```")
    hatter = await _hatter(tmp_path, llm=llm)
    trigger = _u(thread_id="t", body="ticket lands")
    ctx = Context(constitution=hatter.identity.constitution_text, triggers=(trigger,))

    utterance = await hatter.deliberate(ctx)

    assert utterance is not None
    assert utterance.speech_act is SpeechAct.CONCERN
    assert "retry-path" in utterance.content.body
    assert utterance.thread_id == "t"
    assert utterance.parent_id == trigger.id


async def test_deliberate_writes_scenarios_through_registry(tmp_path: Path) -> None:
    payload = {
        "decision": "test_scenario",
        "body": "Two edges around this directive.",
        "scenarios": [
            _scenario_dict(title="emoji overflow at composer"),
            _scenario_dict(title="leap-second clock skew on deploy", severity="degradation"),
        ],
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    hatter = await _hatter(tmp_path, llm=llm)
    ctx = Context(constitution=hatter.identity.constitution_text, triggers=(_u(),))

    utterance = await hatter.deliberate(ctx)

    assert utterance is not None
    assert utterance.speech_act is SpeechAct.TEST_SCENARIO
    assert len(utterance.content.artifacts) == 2
    # Severity surfaces in the artifact payload so downstream consumers can
    # filter without re-reading the file.
    severities = {a.payload["severity"] for a in utterance.content.artifacts}
    assert severities == {"silent-wrongness", "degradation"}

    scenarios_dir = tmp_path / ".wonderland" / "test-scenarios"
    files = sorted(scenarios_dir.glob("scenario-*.md"))
    assert len(files) == 2


async def test_deliberate_drops_scenarios_when_no_registry(tmp_path: Path) -> None:
    payload = {
        "decision": "test_scenario",
        "body": "...",
        "scenarios": [_scenario_dict()],
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    hatter = await _hatter(tmp_path, llm=llm, with_registry=False)
    ctx = Context(constitution=hatter.identity.constitution_text, triggers=(_u(),))

    utterance = await hatter.deliberate(ctx)

    assert utterance is not None
    assert utterance.speech_act is SpeechAct.TEST_SCENARIO
    assert utterance.content.artifacts == []


async def test_deliberate_includes_protocol_in_system_prompt(tmp_path: Path) -> None:
    llm = _mock_llm('```json\n{"decision": "silence"}\n```')
    hatter = await _hatter(tmp_path, llm=llm)
    ctx = Context(constitution="C", triggers=(_u(),))
    await hatter.deliberate(ctx)

    create_kwargs = hatter.llm.client.messages.create.call_args.kwargs
    system_blocks = create_kwargs["system"]
    # Position 0 is the framework primer (shared across all agents)
    assert "Wonderland — Framework Primer" in system_blocks[0]["text"]
    assert "cache_control" not in system_blocks[0]  # framework primer is plain string since context-compression Lever A (cache breakpoint reused for current_thread)
    # Position 1 is the per-agent constitution
    assert system_blocks[1]["text"] == "C"
    assert system_blocks[1]["cache_control"] == {"type": "ephemeral"}
    assert "fenced JSON block" in system_blocks[2]["text"]
    assert "severity" in system_blocks[2]["text"].lower()
    assert system_blocks[2]["cache_control"] == {"type": "ephemeral"}


# ---------- end-to-end (mocked LLM) ----------


async def test_end_to_end_directive_produces_scenarios(tmp_path: Path) -> None:
    payload = {
        "decision": "test_scenario",
        "body": "Edges this directive surfaces.",
        "scenarios": [
            _scenario_dict(title="emoji overflow"),
            _scenario_dict(title="silent-truncation at the encoding boundary"),
        ],
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    hatter = await _hatter(tmp_path, llm=llm)
    observer = hatter.bus.subscribe(agent_name="observer")

    run_task = asyncio.create_task(hatter.run())
    await hatter.bus.publish(_u(act=SpeechAct.DIRECTIVE, body="build something"))

    received = await asyncio.wait_for(anext(observer), timeout=2.0)
    while received.speaker.name != "mad_hatter":
        received = await asyncio.wait_for(anext(observer), timeout=2.0)

    assert received.speech_act is SpeechAct.TEST_SCENARIO
    assert len(received.content.artifacts) == 2

    scenarios_dir = tmp_path / ".wonderland" / "test-scenarios"
    assert len(list(scenarios_dir.glob("scenario-*.md"))) == 2

    await hatter.stop()
    run_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await run_task
    await hatter.memory.close()


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
async def test_live_hatter_smoke(tmp_path: Path) -> None:
    """Real Haiku 4.5 round-trip: directive in, in-character Hatter move out."""
    hatter = await _hatter(tmp_path, llm=LLMClient())
    observer = hatter.bus.subscribe(agent_name="observer")
    run_task = asyncio.create_task(hatter.run())

    await hatter.bus.publish(
        _u(
            act=SpeechAct.DIRECTIVE,
            body=(
                "Build a translation-integrated chat application. Initial scope: "
                "two users in different language groups exchanging short messages "
                "with near-real-time translation."
            ),
        )
    )

    received = await asyncio.wait_for(anext(observer), timeout=60.0)
    while received.speaker.name != "mad_hatter":
        received = await asyncio.wait_for(anext(observer), timeout=60.0)

    assert received.speech_act in {
        SpeechAct.TEST_SCENARIO,
        SpeechAct.CONCERN,
        SpeechAct.QUESTION,
    }
    assert len(received.content.body) > 0

    if received.speech_act is SpeechAct.TEST_SCENARIO:
        # Each scenario carries a triaged severity — the §VIII guard.
        assert received.content.artifacts
        for artifact in received.content.artifacts:
            assert artifact.payload["severity"] in {
                "breakage",
                "silent-wrongness",
                "degradation",
                "curiosity",
                "delight",
            }

    await hatter.stop()
    run_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await run_task
    await hatter.memory.close()
