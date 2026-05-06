"""Tests for the Dormouse — SRE / Observability."""

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
    Dormouse,
    DormouseResponseParseError,
    Engagement,
    InMemoryCaucus,
    LLMClient,
    ObservationRegistry,
    SpeechAct,
    Utterance,
    UtteranceContent,
    dormouse_rules,
    parse_dormouse_response,
)

# ---------- helpers ----------


def _u(
    *,
    thread_id: str = "t",
    speaker: str = "tweedledum",
    addressed: list[str] | str = "caucus",
    act: SpeechAct = SpeechAct.IMPLEMENTATION,
    body: str = (
        "deployed the translation service v1.2 to prod-eu-west-1; metrics + logs "
        "are wired to the standard observability stack"
    ),
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


async def _dormouse(
    tmp_path: Path,
    *,
    llm: LLMClient | None = None,
    with_registry: bool = True,
) -> Dormouse:
    bus = InMemoryCaucus()
    memory = AgentMemory.for_project(tmp_path, "dormouse")
    await memory.open()
    registry = ObservationRegistry(tmp_path) if with_registry else None
    return Dormouse(memory=memory, bus=bus, llm=llm, observation_registry=registry)


def _observation_dict(**overrides) -> dict:
    base = {
        "title": "Translation service error rate spike",
        "type": "incident",
        "severity": "sev2",
        "time_window_start": "2026-05-05T14:23:00Z",
        "time_window_end": "2026-05-05T14:31:00Z",
        "symptom": "Error rate rose from 0.04% to 2.7% over 8 minutes; ~380 requests affected.",
        "affected_scope": "translation-service eu-west-1, message-translate endpoint",
        "evidence": [
            "https://grafana.internal/d/translation/overview",
            "trace ID 01HXYZABCDEFGH",
        ],
        "probable_domain": "backend",
        "routed_to": "tweedledum",
    }
    return base | overrides


# ---------- engagement rules ----------


def test_rules_implementation_from_tweedle_is_always() -> None:
    rules = dormouse_rules()
    for tweedle in ("tweedledee", "tweedledum"):
        assert (
            rules.categorize(_u(act=SpeechAct.IMPLEMENTATION, speaker=tweedle)) is Engagement.ALWAYS
        )


def test_rules_implementation_from_other_is_almost_never() -> None:
    rules = dormouse_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.IMPLEMENTATION, speaker="dodo"))
        is Engagement.ALMOST_NEVER
    )


def test_rules_ruling_from_queen_is_always() -> None:
    rules = dormouse_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.RULING, speaker="queen_of_hearts")) is Engagement.ALWAYS
    )


def test_rules_ruling_from_other_is_almost_never() -> None:
    rules = dormouse_rules()
    assert rules.categorize(_u(act=SpeechAct.RULING, speaker="dodo")) is Engagement.ALMOST_NEVER


def test_rules_concern_with_production_words_is_always() -> None:
    rules = dormouse_rules()
    assert (
        rules.categorize(
            _u(act=SpeechAct.CONCERN, body="error rate on prod is climbing — possible outage")
        )
        is Engagement.ALWAYS
    )


def test_rules_concern_without_production_words_is_almost_never() -> None:
    rules = dormouse_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.CONCERN, body="we should rename this variable"))
        is Engagement.ALMOST_NEVER
    )


def test_rules_question_only_when_addressed_to_dormouse() -> None:
    rules = dormouse_rules()
    assert rules.categorize(_u(act=SpeechAct.QUESTION, addressed=["dormouse"])) is Engagement.ALWAYS
    assert (
        rules.categorize(_u(act=SpeechAct.QUESTION, addressed="caucus")) is Engagement.ALMOST_NEVER
    )


def test_rules_proposal_from_cat_is_selective() -> None:
    rules = dormouse_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.PROPOSAL, speaker="cheshire_cat"))
        is Engagement.SELECTIVELY
    )


def test_rules_proposal_from_other_is_almost_never() -> None:
    rules = dormouse_rules()
    assert rules.categorize(_u(act=SpeechAct.PROPOSAL, speaker="dodo")) is Engagement.ALMOST_NEVER


def test_rules_test_scenario_from_hatter_is_selective() -> None:
    rules = dormouse_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.TEST_SCENARIO, speaker="mad_hatter"))
        is Engagement.SELECTIVELY
    )


def test_rules_ticket_from_rabbit_is_selective() -> None:
    rules = dormouse_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.TICKET, speaker="white_rabbit")) is Engagement.SELECTIVELY
    )


def test_rules_deference_is_rare() -> None:
    rules = dormouse_rules()
    assert rules.categorize(_u(act=SpeechAct.DEFERENCE)) is Engagement.RARELY


def test_rules_story_is_almost_never() -> None:
    """The Dormouse rarely interacts with stories — Alice's domain."""
    rules = dormouse_rules()
    assert rules.categorize(_u(act=SpeechAct.STORY, speaker="alice")) is Engagement.ALMOST_NEVER


def test_rules_directive_is_almost_never() -> None:
    """The Dormouse doesn't consume directives — Dodo's domain."""
    rules = dormouse_rules()
    assert rules.categorize(_u(act=SpeechAct.DIRECTIVE)) is Engagement.ALMOST_NEVER


# ---------- parse_dormouse_response ----------


def test_parse_silence() -> None:
    response = parse_dormouse_response('{"decision": "silence"}')
    assert response.decision == "silence"
    assert response.observations == []


def test_parse_silence_coerces_explicit_nulls() -> None:
    """Live Haiku 4.5 sometimes emits explicit nulls for omitted fields."""
    response = parse_dormouse_response(
        '{"decision": "silence", "body": null, "observations": null}'
    )
    assert response.decision == "silence"
    assert response.body == ""
    assert response.observations == []


def test_parse_concern() -> None:
    text = (
        '```json\n{"decision": "concern", '
        '"body": "no observability hook on the new translation worker — '
        "I can't diagnose if it fails\"}\n```"
    )
    response = parse_dormouse_response(text)
    assert response.decision == "concern"
    assert "observability hook" in response.body


def test_parse_question() -> None:
    text = (
        '{"decision": "question", '
        '"body": "is the new endpoint expected to be quiet during off-hours?"}'
    )
    response = parse_dormouse_response(text)
    assert response.decision == "question"


def test_parse_observation_with_one_observation() -> None:
    payload = {
        "decision": "observation",
        "body": "Sev2 incident — translation service error spike.",
        "observations": [_observation_dict()],
    }
    response = parse_dormouse_response(f"```json\n{json.dumps(payload)}\n```")
    assert response.decision == "observation"
    assert len(response.observations) == 1
    assert response.observations[0].severity.value == "sev2"


def test_parse_observation_with_multiple_observations() -> None:
    payload = {
        "decision": "observation",
        "body": "Two services landed; both observability sign-offs.",
        "observations": [
            _observation_dict(
                title="translation service post-deploy",
                type="post-deploy",
                severity="informational",
            ),
            _observation_dict(
                title="auth service post-deploy",
                type="post-deploy",
                severity="informational",
            ),
        ],
    }
    response = parse_dormouse_response(f"```json\n{json.dumps(payload)}\n```")
    assert len(response.observations) == 2


def test_parse_rejects_observation_decision_with_no_observations() -> None:
    with pytest.raises(DormouseResponseParseError):
        parse_dormouse_response('{"decision": "observation", "body": "...", "observations": []}')


def test_parse_rejects_observation_with_empty_evidence() -> None:
    """Schema validation propagates: observations without evidence are unverifiable."""
    payload = {
        "decision": "observation",
        "body": "...",
        "observations": [_observation_dict(evidence=[])],
    }
    with pytest.raises(DormouseResponseParseError):
        parse_dormouse_response(f"```json\n{json.dumps(payload)}\n```")


def test_parse_rejects_invalid_severity() -> None:
    payload = {
        "decision": "observation",
        "body": "...",
        "observations": [_observation_dict(severity="critical")],
    }
    with pytest.raises(DormouseResponseParseError):
        parse_dormouse_response(f"```json\n{json.dumps(payload)}\n```")


def test_parse_rejects_invalid_type() -> None:
    payload = {
        "decision": "observation",
        "body": "...",
        "observations": [_observation_dict(type="catastrophe")],
    }
    with pytest.raises(DormouseResponseParseError):
        parse_dormouse_response(f"```json\n{json.dumps(payload)}\n```")


def test_parse_rejects_invalid_decision() -> None:
    with pytest.raises(DormouseResponseParseError):
        parse_dormouse_response('{"decision": "diagnose"}')


def test_parse_rejects_missing_json() -> None:
    with pytest.raises(DormouseResponseParseError):
        parse_dormouse_response("just plain text, no json")


# ---------- Dormouse construction ----------


async def test_dormouse_loads_constitution(tmp_path: Path) -> None:
    dormouse = await _dormouse(tmp_path)
    assert dormouse.identity.name == "dormouse"
    assert "Dormouse" in dormouse.identity.constitution_text


async def test_dormouse_engagement_policy_wired(tmp_path: Path) -> None:
    dormouse = await _dormouse(tmp_path)
    impl = _u(act=SpeechAct.IMPLEMENTATION, speaker="tweedledum")
    foreign_proposal = _u(act=SpeechAct.PROPOSAL, speaker="dodo")
    assert dormouse.should_engage(impl) is True
    assert dormouse.should_engage(foreign_proposal) is False


async def test_dormouse_with_no_llm_is_silent(tmp_path: Path) -> None:
    dormouse = await _dormouse(tmp_path, llm=None)
    ctx = Context(constitution=dormouse.identity.constitution_text, triggers=(_u(),))
    assert await dormouse.deliberate(ctx) is None


# ---------- deliberate ----------


async def test_deliberate_returns_none_on_silence(tmp_path: Path) -> None:
    llm = _mock_llm('```json\n{"decision": "silence"}\n```')
    dormouse = await _dormouse(tmp_path, llm=llm)
    ctx = Context(constitution=dormouse.identity.constitution_text, triggers=(_u(),))
    assert await dormouse.deliberate(ctx) is None


async def test_deliberate_publishes_concern(tmp_path: Path) -> None:
    body = "no observability hook on the new translation worker — observability gap"
    llm = _mock_llm(f"```json\n{json.dumps({'decision': 'concern', 'body': body})}\n```")
    dormouse = await _dormouse(tmp_path, llm=llm)
    trigger = _u(thread_id="t", body="implementation lands without metrics")
    ctx = Context(constitution=dormouse.identity.constitution_text, triggers=(trigger,))

    utterance = await dormouse.deliberate(ctx)

    assert utterance is not None
    assert utterance.speech_act is SpeechAct.CONCERN
    assert "observability gap" in utterance.content.body
    assert utterance.thread_id == "t"
    assert utterance.parent_id == trigger.id


async def test_deliberate_writes_observations_through_registry(tmp_path: Path) -> None:
    payload = {
        "decision": "observation",
        "body": "Sev2 incident on the translation service.",
        "observations": [_observation_dict()],
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    dormouse = await _dormouse(tmp_path, llm=llm)
    ctx = Context(constitution=dormouse.identity.constitution_text, triggers=(_u(),))

    utterance = await dormouse.deliberate(ctx)

    assert utterance is not None
    assert utterance.speech_act is SpeechAct.OBSERVATION
    assert len(utterance.content.artifacts) == 1
    artifact = utterance.content.artifacts[0]
    assert artifact.payload["severity"] == "sev2"
    assert artifact.payload["type"] == "incident"

    obs_dir = tmp_path / ".wonderland" / "observations"
    files = sorted(obs_dir.glob("observation-*.md"))
    assert len(files) == 1


async def test_deliberate_drops_observations_when_no_registry(tmp_path: Path) -> None:
    payload = {
        "decision": "observation",
        "body": "...",
        "observations": [_observation_dict()],
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    dormouse = await _dormouse(tmp_path, llm=llm, with_registry=False)
    ctx = Context(constitution=dormouse.identity.constitution_text, triggers=(_u(),))

    utterance = await dormouse.deliberate(ctx)

    assert utterance is not None
    assert utterance.speech_act is SpeechAct.OBSERVATION
    assert utterance.content.artifacts == []


async def test_deliberate_includes_protocol_in_system_prompt(tmp_path: Path) -> None:
    llm = _mock_llm('```json\n{"decision": "silence"}\n```')
    dormouse = await _dormouse(tmp_path, llm=llm)
    ctx = Context(constitution="C", triggers=(_u(),))
    await dormouse.deliberate(ctx)

    create_kwargs = dormouse.llm.client.messages.create.call_args.kwargs
    system_blocks = create_kwargs["system"]
    # Position 0 is the framework primer (shared across all agents)
    assert "Wonderland — Framework Primer" in system_blocks[0]["text"]
    assert system_blocks[0]["cache_control"] == {"type": "ephemeral"}
    # Position 1 is the per-agent constitution
    assert system_blocks[1]["text"] == "C"
    assert system_blocks[1]["cache_control"] == {"type": "ephemeral"}
    assert "fenced JSON block" in system_blocks[2]["text"]
    assert "Evidence is non-negotiable" in system_blocks[2]["text"]
    assert system_blocks[2]["cache_control"] == {"type": "ephemeral"}


# ---------- end-to-end (mocked LLM) ----------


async def test_end_to_end_implementation_produces_observation(tmp_path: Path) -> None:
    payload = {
        "decision": "observation",
        "body": "Post-deploy sign-off for the translation service.",
        "observations": [
            _observation_dict(
                title="translation service post-deploy",
                type="post-deploy",
                severity="informational",
            )
        ],
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    dormouse = await _dormouse(tmp_path, llm=llm)
    observer = dormouse.bus.subscribe(agent_name="observer")

    run_task = asyncio.create_task(dormouse.run())
    try:
        await dormouse.bus.publish(
            _u(
                act=SpeechAct.IMPLEMENTATION,
                speaker="tweedledum",
                body="deployed translation service v1.2 to prod with observability hooks",
            )
        )

        received = await asyncio.wait_for(anext(observer), timeout=2.0)
        while received.speaker.name != "dormouse":
            received = await asyncio.wait_for(anext(observer), timeout=2.0)

        assert received.speech_act is SpeechAct.OBSERVATION
        assert len(received.content.artifacts) == 1

        obs_dir = tmp_path / ".wonderland" / "observations"
        assert len(list(obs_dir.glob("observation-*.md"))) == 1
    finally:
        await dormouse.stop()
        run_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await run_task
        await dormouse.memory.close()


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
async def test_live_dormouse_smoke(tmp_path: Path) -> None:
    """Real Haiku 4.5 round-trip: implementation in, in-character Dormouse move out."""
    dormouse = await _dormouse(tmp_path, llm=LLMClient())
    observer = dormouse.bus.subscribe(agent_name="observer")
    run_task = asyncio.create_task(dormouse.run())

    try:
        await dormouse.bus.publish(
            _u(
                act=SpeechAct.IMPLEMENTATION,
                speaker="tweedledum",
                body=(
                    "Deployed translation-service v1.2 to prod-eu-west-1 at 14:00 UTC. "
                    "Standard metrics wired: request_count, error_rate, latency_p50/p95/p99, "
                    "queue_depth. Logs go to centralized stack with structured fields "
                    "(app, level, request_id, span_id). Dashboard at "
                    "https://grafana.internal/d/translation/overview. Alert thresholds "
                    "inherited from translation-service v1.1. Looking for post-deploy "
                    "sign-off — anything looks off?"
                ),
            )
        )

        received = await asyncio.wait_for(anext(observer), timeout=120.0)
        while received.speaker.name != "dormouse":
            received = await asyncio.wait_for(anext(observer), timeout=120.0)

        assert received.speech_act in {
            SpeechAct.OBSERVATION,
            SpeechAct.CONCERN,
            SpeechAct.QUESTION,
        }

        if received.speech_act is SpeechAct.OBSERVATION:
            # Each observation carries verifiable evidence — the §VIII guard.
            assert received.content.artifacts
            for artifact in received.content.artifacts:
                assert artifact.payload["severity"] in {
                    "sev1",
                    "sev2",
                    "sev3",
                    "informational",
                }
                assert artifact.payload["type"] in {
                    "incident",
                    "anomaly",
                    "steady-state",
                    "post-deploy",
                    "post-incident-confirmation",
                }
        else:
            assert len(received.content.body) > 0
    finally:
        await dormouse.stop()
        run_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await run_task
        await dormouse.memory.close()
