"""Tests for the Queen of Hearts — Security / Compliance."""

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
    QueenOfHearts,
    QueenResponseParseError,
    RulingRegistry,
    SpeechAct,
    Utterance,
    UtteranceContent,
    parse_queen_response,
    queen_of_hearts_rules,
)

# ---------- helpers ----------


def _u(
    *,
    thread_id: str = "t",
    speaker: str = "cheshire_cat",
    addressed: list[str] | str = "caucus",
    act: SpeechAct = SpeechAct.PROPOSAL,
    body: str = "proposing OAuth2 with refresh tokens stored client-side",
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


async def _queen(
    tmp_path: Path,
    *,
    llm: LLMClient | None = None,
    with_registry: bool = True,
) -> QueenOfHearts:
    bus = InMemoryCaucus()
    memory = AgentMemory.for_project(tmp_path, "queen_of_hearts")
    await memory.open()
    registry = RulingRegistry(tmp_path) if with_registry else None
    return QueenOfHearts(memory=memory, bus=bus, llm=llm, ruling_registry=registry)


def _ruling_dict(**overrides) -> dict:
    base = {
        "title": "Refresh tokens stored client-side without HttpOnly",
        "severity": "high",
        "domain": "authentication",
        "source": "proposal from cheshire_cat",
        "citation": "OWASP A01:2021 Broken Access Control; CWE-1004 Sensitive Cookie Without 'HttpOnly' Flag",
        "finding": "Refresh tokens accessible to JavaScript are exfiltrable via XSS, surviving cookie-flag protections.",
        "required_remediation": "Move refresh tokens to HttpOnly cookies; document the SameSite + Secure posture.",
        "acceptance_criteria": [
            "refresh tokens not readable from document.cookie",
            "Set-Cookie carries HttpOnly + Secure + SameSite=Lax for the refresh token",
        ],
    }
    return base | overrides


# ---------- engagement rules ----------


def test_rules_proposal_from_cat_is_always() -> None:
    rules = queen_of_hearts_rules()
    assert rules.categorize(_u(act=SpeechAct.PROPOSAL, speaker="cheshire_cat")) is Engagement.ALWAYS


def test_rules_proposal_from_other_is_almost_never() -> None:
    rules = queen_of_hearts_rules()
    assert rules.categorize(_u(act=SpeechAct.PROPOSAL, speaker="dodo")) is Engagement.ALMOST_NEVER


def test_rules_implementation_from_tweedle_is_always() -> None:
    rules = queen_of_hearts_rules()
    for tweedle in ("tweedledee", "tweedledum"):
        assert (
            rules.categorize(_u(act=SpeechAct.IMPLEMENTATION, speaker=tweedle)) is Engagement.ALWAYS
        )


def test_rules_implementation_from_other_is_almost_never() -> None:
    rules = queen_of_hearts_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.IMPLEMENTATION, speaker="dodo"))
        is Engagement.ALMOST_NEVER
    )


def test_rules_concern_with_security_words_is_always() -> None:
    rules = queen_of_hearts_rules()
    assert (
        rules.categorize(
            _u(act=SpeechAct.CONCERN, speaker="alice", body="this exposes PII to the audit log")
        )
        is Engagement.ALWAYS
    )


def test_rules_concern_without_security_words_is_almost_never() -> None:
    rules = queen_of_hearts_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.CONCERN, body="we should ship before Friday"))
        is Engagement.ALMOST_NEVER
    )


def test_rules_test_scenario_from_hatter_is_always() -> None:
    rules = queen_of_hearts_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.TEST_SCENARIO, speaker="mad_hatter")) is Engagement.ALWAYS
    )


def test_rules_observation_with_incident_words_is_always() -> None:
    rules = queen_of_hearts_rules()
    assert (
        rules.categorize(
            _u(
                act=SpeechAct.OBSERVATION,
                speaker="dormouse",
                body="anomalous spike in failed auth attempts from one IP — possible reconnaissance",
            )
        )
        is Engagement.ALWAYS
    )


def test_rules_ticket_from_rabbit_is_always() -> None:
    rules = queen_of_hearts_rules()
    assert rules.categorize(_u(act=SpeechAct.TICKET, speaker="white_rabbit")) is Engagement.ALWAYS


def test_rules_question_only_when_addressed_to_queen() -> None:
    rules = queen_of_hearts_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.QUESTION, addressed=["queen_of_hearts"]))
        is Engagement.ALWAYS
    )
    assert (
        rules.categorize(_u(act=SpeechAct.QUESTION, addressed="caucus")) is Engagement.ALMOST_NEVER
    )


def test_rules_story_engages_selectively_regardless_of_author() -> None:
    """Caterpillar joined Alice as a story author at M1 (plumbing
    stories — commit 61172d3). Queen's story engagement is
    selective regardless of who shipped — security review against
    plumbing stories is just as useful as against user stories
    (auth + secrets handling often surfaces in dev infra)."""
    rules = queen_of_hearts_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.STORY, speaker="alice"))
        is Engagement.SELECTIVELY
    )
    assert (
        rules.categorize(_u(act=SpeechAct.STORY, speaker="caterpillar"))
        is Engagement.SELECTIVELY
    )


def test_rules_review_from_caterpillar_is_selective() -> None:
    rules = queen_of_hearts_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.REVIEW, speaker="caterpillar")) is Engagement.SELECTIVELY
    )


def test_rules_directive_with_compliance_words_is_selective() -> None:
    rules = queen_of_hearts_rules()
    assert (
        rules.categorize(
            _u(
                act=SpeechAct.DIRECTIVE,
                speaker="dodo",
                body="build a chat application that handles GDPR-scoped EU consumer data",
            )
        )
        is Engagement.SELECTIVELY
    )


def test_rules_directive_without_compliance_words_is_almost_never() -> None:
    rules = queen_of_hearts_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.DIRECTIVE, body="add a /health endpoint"))
        is Engagement.ALMOST_NEVER
    )


def test_rules_deference_is_rare() -> None:
    rules = queen_of_hearts_rules()
    assert rules.categorize(_u(act=SpeechAct.DEFERENCE)) is Engagement.RARELY


# ---------- parse_queen_response ----------


def test_parse_silence() -> None:
    response = parse_queen_response('{"decision": "silence"}')
    assert response.decision == "silence"
    assert response.rulings == []


def test_parse_silence_coerces_explicit_nulls() -> None:
    """Live Haiku 4.5 sometimes emits explicit nulls for omitted fields."""
    response = parse_queen_response('{"decision": "silence", "body": null, "rulings": null}')
    assert response.decision == "silence"
    assert response.body == ""
    assert response.rulings == []


def test_parse_concern() -> None:
    text = (
        '```json\n{"decision": "concern", '
        '"body": "this proposal implies PII handling that needs threat-model review"}\n```'
    )
    response = parse_queen_response(text)
    assert response.decision == "concern"
    assert "PII" in response.body


def test_parse_question() -> None:
    text = (
        '{"decision": "question", "body": "what is the data residency requirement for EU users?"}'
    )
    response = parse_queen_response(text)
    assert response.decision == "question"


def test_parse_ruling_with_one_ruling() -> None:
    payload = {
        "decision": "ruling",
        "body": "One ruling on the refresh-token proposal.",
        "rulings": [_ruling_dict()],
    }
    response = parse_queen_response(f"```json\n{json.dumps(payload)}\n```")
    assert response.decision == "ruling"
    assert len(response.rulings) == 1
    assert response.rulings[0].severity.value == "high"


def test_parse_ruling_with_multiple_rulings() -> None:
    payload = {
        "decision": "ruling",
        "body": "Two distinct concerns surface from this proposal.",
        "rulings": [
            _ruling_dict(title="Token storage"),
            _ruling_dict(
                title="Audit trail gap",
                severity="medium",
                domain="logging-and-audit",
                citation="GDPR Art. 30 records of processing activities",
            ),
        ],
    }
    response = parse_queen_response(f"```json\n{json.dumps(payload)}\n```")
    assert len(response.rulings) == 2


def test_parse_coerces_empty_ruling_with_body_to_concern() -> None:
    """Live Haiku 4.5 sometimes emits decision='ruling' with rulings=[] and
    a substantive body — the LLM intended a ruling but didn't fill the
    structured payload. Rather than reject the whole response (and lose
    the body), coerce to decision='concern' so the body content survives.
    Same shape as Tweedle's decision-coercion validator."""
    response = parse_queen_response(
        '{"decision": "ruling", "body": "translation must enforce GDPR retention", "rulings": []}'
    )
    assert response.decision == "concern"
    assert "GDPR retention" in response.body


def test_parse_rejects_ruling_decision_with_no_rulings_and_empty_body() -> None:
    """If the body is also empty, there's nothing to coerce — schema rejects."""
    with pytest.raises(QueenResponseParseError):
        parse_queen_response('{"decision": "ruling", "body": "", "rulings": []}')


def test_parse_rejects_ruling_with_empty_citation() -> None:
    """Schema validation propagates: rulings without citation are opinions."""
    payload = {
        "decision": "ruling",
        "body": "...",
        "rulings": [_ruling_dict(citation="")],
    }
    with pytest.raises(QueenResponseParseError):
        parse_queen_response(f"```json\n{json.dumps(payload)}\n```")


def test_parse_rejects_invalid_severity() -> None:
    payload = {
        "decision": "ruling",
        "body": "...",
        "rulings": [_ruling_dict(severity="catastrophic")],
    }
    with pytest.raises(QueenResponseParseError):
        parse_queen_response(f"```json\n{json.dumps(payload)}\n```")


def test_parse_rejects_invalid_domain() -> None:
    payload = {
        "decision": "ruling",
        "body": "...",
        "rulings": [_ruling_dict(domain="vibes")],
    }
    with pytest.raises(QueenResponseParseError):
        parse_queen_response(f"```json\n{json.dumps(payload)}\n```")


def test_parse_rejects_invalid_decision() -> None:
    with pytest.raises(QueenResponseParseError):
        parse_queen_response('{"decision": "behead"}')


def test_parse_rejects_missing_json() -> None:
    with pytest.raises(QueenResponseParseError):
        parse_queen_response("just plain text, no json")


# ---------- QueenOfHearts construction ----------


async def test_queen_loads_constitution(tmp_path: Path) -> None:
    queen = await _queen(tmp_path)
    assert queen.identity.name == "queen_of_hearts"
    assert "Queen of Hearts" in queen.identity.constitution_text


async def test_queen_engagement_policy_wired(tmp_path: Path) -> None:
    queen = await _queen(tmp_path)
    cat_proposal = _u(act=SpeechAct.PROPOSAL, speaker="cheshire_cat")
    foreign_proposal = _u(act=SpeechAct.PROPOSAL, speaker="dodo")
    assert queen.should_engage(cat_proposal) is True
    assert queen.should_engage(foreign_proposal) is False


async def test_queen_with_no_llm_is_silent(tmp_path: Path) -> None:
    queen = await _queen(tmp_path, llm=None)
    ctx = Context(constitution=queen.identity.constitution_text, triggers=(_u(),))
    assert await queen.deliberate(ctx) is None


# ---------- deliberate ----------


async def test_deliberate_returns_none_on_silence(tmp_path: Path) -> None:
    llm = _mock_llm('```json\n{"decision": "silence"}\n```')
    queen = await _queen(tmp_path, llm=llm)
    ctx = Context(constitution=queen.identity.constitution_text, triggers=(_u(),))
    assert await queen.deliberate(ctx) is None


async def test_deliberate_publishes_concern(tmp_path: Path) -> None:
    body = "this proposal needs a threat model before I can rule"
    llm = _mock_llm(f"```json\n{json.dumps({'decision': 'concern', 'body': body})}\n```")
    queen = await _queen(tmp_path, llm=llm)
    trigger = _u(thread_id="t", body="proposal lands")
    ctx = Context(constitution=queen.identity.constitution_text, triggers=(trigger,))

    utterance = await queen.deliberate(ctx)

    assert utterance is not None
    assert utterance.speech_act is SpeechAct.CONCERN
    assert "threat model" in utterance.content.body
    assert utterance.thread_id == "t"
    assert utterance.parent_id == trigger.id


async def test_deliberate_writes_rulings_through_registry(tmp_path: Path) -> None:
    payload = {
        "decision": "ruling",
        "body": "Two distinct concerns.",
        "rulings": [
            _ruling_dict(title="Token storage"),
            _ruling_dict(
                title="Audit trail gap",
                severity="medium",
                domain="logging-and-audit",
                citation="GDPR Art. 30 records of processing activities",
            ),
        ],
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    queen = await _queen(tmp_path, llm=llm)
    ctx = Context(constitution=queen.identity.constitution_text, triggers=(_u(),))

    utterance = await queen.deliberate(ctx)

    assert utterance is not None
    assert utterance.speech_act is SpeechAct.RULING
    assert len(utterance.content.artifacts) == 2
    severities = {a.payload["severity"] for a in utterance.content.artifacts}
    domains = {a.payload["domain"] for a in utterance.content.artifacts}
    assert severities == {"high", "medium"}
    assert domains == {"authentication", "logging-and-audit"}

    rulings_dir = tmp_path / ".wonderland" / "rulings"
    files = sorted(rulings_dir.glob("ruling-*.md"))
    assert len(files) == 2


async def test_deliberate_drops_rulings_when_no_registry(tmp_path: Path) -> None:
    payload = {
        "decision": "ruling",
        "body": "...",
        "rulings": [_ruling_dict()],
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    queen = await _queen(tmp_path, llm=llm, with_registry=False)
    ctx = Context(constitution=queen.identity.constitution_text, triggers=(_u(),))

    utterance = await queen.deliberate(ctx)

    assert utterance is not None
    assert utterance.speech_act is SpeechAct.RULING
    assert utterance.content.artifacts == []


async def test_deliberate_includes_protocol_in_system_prompt(tmp_path: Path) -> None:
    llm = _mock_llm('```json\n{"decision": "silence"}\n```')
    queen = await _queen(tmp_path, llm=llm)
    ctx = Context(constitution="C", triggers=(_u(),))
    await queen.deliberate(ctx)

    create_kwargs = queen.llm.client.messages.create.call_args.kwargs
    system_blocks = create_kwargs["system"]
    # Position 0 is the framework primer (shared across all agents)
    assert "Wonderland — Framework Primer" in system_blocks[0]["text"]
    assert "cache_control" not in system_blocks[0]  # framework primer is plain string since context-compression Lever A (cache breakpoint reused for current_thread)
    # Position 1 is the per-agent constitution
    assert system_blocks[1]["text"] == "C"
    assert system_blocks[1]["cache_control"] == {"type": "ephemeral"}
    assert "fenced JSON block" in system_blocks[2]["text"]
    assert "Citation is non-negotiable" in system_blocks[2]["text"]
    assert system_blocks[2]["cache_control"] == {"type": "ephemeral"}


# ---------- end-to-end (mocked LLM) ----------


async def test_end_to_end_proposal_produces_ruling(tmp_path: Path) -> None:
    payload = {
        "decision": "ruling",
        "body": "Ruling on the refresh-token proposal.",
        "rulings": [_ruling_dict()],
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    queen = await _queen(tmp_path, llm=llm)
    observer = queen.bus.subscribe(agent_name="observer")

    run_task = asyncio.create_task(queen.run())
    try:
        await queen.bus.publish(
            _u(
                act=SpeechAct.PROPOSAL,
                speaker="cheshire_cat",
                body="proposing OAuth2 with refresh tokens stored client-side",
            )
        )

        received = await asyncio.wait_for(anext(observer), timeout=2.0)
        while received.speaker.name != "queen_of_hearts":
            received = await asyncio.wait_for(anext(observer), timeout=2.0)

        assert received.speech_act is SpeechAct.RULING
        assert len(received.content.artifacts) == 1

        rulings_dir = tmp_path / ".wonderland" / "rulings"
        assert len(list(rulings_dir.glob("ruling-*.md"))) == 1
    finally:
        await queen.stop()
        run_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await run_task
        await queen.memory.close()


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
async def test_live_queen_smoke(tmp_path: Path) -> None:
    """Real Haiku 4.5 round-trip: proposal in, in-character Queen move out."""
    queen = await _queen(tmp_path, llm=LLMClient())
    observer = queen.bus.subscribe(agent_name="observer")
    run_task = asyncio.create_task(queen.run())

    try:
        await queen.bus.publish(
            _u(
                act=SpeechAct.PROPOSAL,
                speaker="cheshire_cat",
                body=(
                    "Proposing OAuth2 with refresh tokens stored in localStorage on the "
                    "client. The refresh token will be sent in an Authorization header on "
                    "every API request alongside a short-lived access token. We'll log all "
                    "auth events including the full request payload at debug level for "
                    "observability."
                ),
            )
        )

        received = await asyncio.wait_for(anext(observer), timeout=120.0)
        while received.speaker.name != "queen_of_hearts":
            received = await asyncio.wait_for(anext(observer), timeout=120.0)

        assert received.speech_act in {
            SpeechAct.RULING,
            SpeechAct.CONCERN,
            SpeechAct.QUESTION,
        }

        if received.speech_act is SpeechAct.RULING:
            # Each ruling carries citation, severity, and domain — the §VIII guards.
            assert received.content.artifacts
            for artifact in received.content.artifacts:
                assert artifact.payload["severity"] in {
                    "critical",
                    "high",
                    "medium",
                    "low",
                    "informational",
                }
                assert artifact.payload["domain"]
        else:
            # Body carries the substance for non-ruling acts.
            assert len(received.content.body) > 0
    finally:
        await queen.stop()
        run_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await run_task
        await queen.memory.close()
