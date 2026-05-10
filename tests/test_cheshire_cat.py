"""Tests for the Cheshire Cat — the first character to come online."""

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
    ADRRegistry,
    AgentIdentity,
    AgentMemory,
    CatResponseParseError,
    CheshireCat,
    Context,
    Engagement,
    InMemoryCaucus,
    LLMClient,
    SpeechAct,
    Utterance,
    UtteranceContent,
    cheshire_cat_rules,
    parse_cat_response,
)

# ---------- helpers ----------


def _u(
    *,
    thread_id: str = "t",
    speaker: str = "white_rabbit",
    addressed: list[str] | str = "caucus",
    act: SpeechAct = SpeechAct.PROPOSAL,
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


async def _cat(
    tmp_path: Path,
    *,
    llm: LLMClient | None = None,
    with_registry: bool = True,
) -> CheshireCat:
    bus = InMemoryCaucus()
    memory = AgentMemory.for_project(tmp_path, "cheshire_cat")
    await memory.open()
    registry = ADRRegistry(tmp_path) if with_registry else None
    return CheshireCat(memory=memory, bus=bus, llm=llm, adr_registry=registry)


# ---------- engagement rules ----------


def test_cat_rules_always_engages_with_directive() -> None:
    rules = cheshire_cat_rules()
    assert rules.categorize(_u(act=SpeechAct.DIRECTIVE)) is Engagement.ALWAYS


def test_cat_rules_always_engages_with_proposal() -> None:
    rules = cheshire_cat_rules()
    assert rules.categorize(_u(act=SpeechAct.PROPOSAL)) is Engagement.ALWAYS


def test_cat_rules_question_only_when_addressed() -> None:
    rules = cheshire_cat_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.QUESTION, addressed=["cheshire_cat"]))
        is Engagement.ALWAYS
    )
    assert (
        rules.categorize(_u(act=SpeechAct.QUESTION, addressed="caucus")) is Engagement.ALMOST_NEVER
    )


def test_cat_rules_ticket_engages_when_implementation_smell() -> None:
    rules = cheshire_cat_rules()
    smelly = _u(
        act=SpeechAct.TICKET,
        body="Implement message translation with a synchronous call per message.",
    )
    benign = _u(act=SpeechAct.TICKET, body="Add a profile page.")
    assert rules.categorize(smelly) is Engagement.ALWAYS
    assert rules.categorize(benign) is Engagement.ALMOST_NEVER


def test_cat_rules_concern_engages_when_architectural_keyword_present() -> None:
    rules = cheshire_cat_rules()
    architectural = _u(act=SpeechAct.CONCERN, body="Worried about the seam between A and B.")
    not_architectural = _u(act=SpeechAct.CONCERN, body="The button color looks wrong.")
    assert rules.categorize(architectural) is Engagement.ALWAYS
    assert rules.categorize(not_architectural) is Engagement.ALMOST_NEVER


def test_cat_rules_story_engages_on_every_alice_story() -> None:
    """Cat wakes on every Alice story regardless of body keywords; the
    deliberate() step decides whether the cumulative picture warrants
    synthesizing an ADR. The previous keyword filter (real-time,
    multi-tenant, etc.) made Cat structurally deaf to user-shaped
    stories, leaving the architectural picture un-synthesized."""
    rules = cheshire_cat_rules()
    plain_alice = _u(
        act=SpeechAct.STORY,
        speaker="alice",
        body="Users want to set a profile photo.",
    )
    arch_alice = _u(
        act=SpeechAct.STORY,
        speaker="alice",
        body="Users need real-time updates.",
    )
    not_alice = _u(
        act=SpeechAct.STORY,
        speaker="white_rabbit",
        body="Users need real-time updates.",
    )
    assert rules.categorize(plain_alice) is Engagement.SELECTIVELY
    assert rules.categorize(arch_alice) is Engagement.SELECTIVELY
    assert rules.categorize(not_alice) is Engagement.ALMOST_NEVER


def test_cat_rules_implementation_engages_selectively() -> None:
    """Cat engages broadly with implementation; deliberate() chooses silence."""
    rules = cheshire_cat_rules()
    assert rules.categorize(_u(act=SpeechAct.IMPLEMENTATION)) is Engagement.SELECTIVELY


def test_cat_rules_observation_is_rare() -> None:
    rules = cheshire_cat_rules()
    assert rules.categorize(_u(act=SpeechAct.OBSERVATION)) is Engagement.RARELY


def test_cat_rules_deference_is_skipped() -> None:
    rules = cheshire_cat_rules()
    assert rules.categorize(_u(act=SpeechAct.DEFERENCE)) is Engagement.ALMOST_NEVER


# ---------- parse_cat_response ----------


def test_parse_cat_response_extracts_fenced_json() -> None:
    # Per the post_init validator: decision='proposal' requires the adr
    # field. This test verifies the fence-extraction itself; the proposal
    # carries a minimal valid ADR.
    text = """The Cat considers the trigger.

```json
{
  "decision": "proposal",
  "body": "Use Redis.",
  "adr": {
    "title": "Use Redis",
    "context": "Need a bus.",
    "decision": "Use Redis.",
    "tradeoffs": ["familiar ops"]
  }
}
```

That is all."""
    response = parse_cat_response(text)
    assert response.decision == "proposal"
    assert response.body == "Use Redis."
    assert response.adr is not None


def test_parse_cat_response_accepts_unfenced_json() -> None:
    """Tolerate the LLM forgetting the fence."""
    text = '{"decision": "silence"}'
    response = parse_cat_response(text)
    assert response.decision == "silence"


def test_parse_cat_response_extracts_adr_payload() -> None:
    text = """```json
{
  "decision": "proposal",
  "body": "Use Redis Streams.",
  "adr": {
    "title": "Use Redis Streams for the Caucus",
    "context": "Need an event bus.",
    "decision": "Use Redis Streams.",
    "tradeoffs": ["familiar ops", "single-region default"]
  }
}
```"""
    response = parse_cat_response(text)
    assert response.decision == "proposal"
    assert response.adr is not None
    assert response.adr.title == "Use Redis Streams for the Caucus"
    assert len(response.adr.tradeoffs) == 2


def test_parse_cat_response_silence_omits_body() -> None:
    response = parse_cat_response('{"decision": "silence"}')
    assert response.decision == "silence"
    assert response.body == ""


def test_parse_cat_response_silence_coerces_explicit_nulls() -> None:
    """Live Haiku 4.5 sometimes emits explicit nulls instead of omitting fields."""
    response = parse_cat_response('{"decision": "silence", "body": null, "adr": null}')
    assert response.decision == "silence"
    assert response.body == ""
    assert response.adr is None


def test_parse_cat_response_raises_on_missing_json() -> None:
    with pytest.raises(CatResponseParseError):
        parse_cat_response("just plain text, no json")


def test_parse_cat_response_raises_on_invalid_json() -> None:
    with pytest.raises(CatResponseParseError):
        parse_cat_response("```json\n{not valid}\n```")


def test_parse_cat_response_raises_on_invalid_decision() -> None:
    with pytest.raises(CatResponseParseError):
        parse_cat_response('{"decision": "shout", "body": "wat"}')


def test_parse_cat_response_rejects_adr_without_tradeoffs() -> None:
    """The grin enforcement reaches all the way to the parser."""
    text = """```json
{
  "decision": "proposal",
  "body": "ship it",
  "adr": {"title": "t", "context": "c", "decision": "d", "tradeoffs": []}
}
```"""
    with pytest.raises(CatResponseParseError):
        parse_cat_response(text)


# ---------- CheshireCat construction ----------


async def test_cat_loads_constitution_from_disk(tmp_path: Path) -> None:
    cat = await _cat(tmp_path)
    assert cat.identity.name == "cheshire_cat"
    assert "Cheshire Cat" in cat.identity.header.display_name
    assert "You are the Cheshire Cat." in cat.identity.constitution_text


async def test_cat_engagement_policy_is_wired(tmp_path: Path) -> None:
    cat = await _cat(tmp_path)
    proposal = _u(act=SpeechAct.PROPOSAL)
    deference = _u(act=SpeechAct.DEFERENCE)
    assert cat.should_engage(proposal) is True
    assert cat.should_engage(deference) is False


async def test_cat_with_no_llm_is_silent(tmp_path: Path) -> None:
    """No LLM injected → deliberate falls back to silence."""
    cat = await _cat(tmp_path, llm=None)
    ctx = Context(constitution=cat.identity.constitution_text, triggers=(_u(),))
    assert await cat.deliberate(ctx) is None


# ---------- deliberate() ----------


async def test_deliberate_returns_none_on_silence(tmp_path: Path) -> None:
    llm = _mock_llm('```json\n{"decision": "silence"}\n```')
    cat = await _cat(tmp_path, llm=llm)
    ctx = Context(constitution=cat.identity.constitution_text, triggers=(_u(),))
    assert await cat.deliberate(ctx) is None


async def test_deliberate_produces_proposal_utterance(tmp_path: Path) -> None:
    # Per the post_init validator: a proposal must include an ADR.
    body = "What would have to be true for the choice to matter?"
    payload = {
        "decision": "proposal",
        "body": body,
        "adr": {
            "title": "Pick X over Y",
            "context": "X and Y are interchangeable in v1.",
            "decision": "Pick X.",
            "tradeoffs": ["familiar ops"],
        },
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    cat = await _cat(tmp_path, llm=llm)
    trigger = _u(thread_id="t", body="we should use X or Y")
    ctx = Context(constitution=cat.identity.constitution_text, triggers=(trigger,))

    utterance = await cat.deliberate(ctx)

    assert utterance is not None
    assert utterance.speech_act is SpeechAct.PROPOSAL
    assert utterance.content.body == body
    assert utterance.speaker.name == "cheshire_cat"
    assert utterance.thread_id == "t"
    assert utterance.parent_id == trigger.id


async def test_deliberate_writes_adr_when_payload_present(tmp_path: Path) -> None:
    payload = {
        "decision": "proposal",
        "body": "Use Redis Streams.",
        "adr": {
            "title": "Use Redis Streams for the Caucus",
            "context": "Need an event bus.",
            "decision": "Use Redis Streams.",
            "tradeoffs": ["familiar ops", "single-region default"],
        },
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    cat = await _cat(tmp_path, llm=llm)
    ctx = Context(constitution=cat.identity.constitution_text, triggers=(_u(),))

    utterance = await cat.deliberate(ctx)

    assert utterance is not None
    assert len(utterance.content.artifacts) == 1
    artifact = utterance.content.artifacts[0]
    assert artifact.kind == "adr"
    assert artifact.payload["number"] == 1
    assert artifact.payload["slug"] == "use-redis-streams-for-the-caucus"

    # File is on disk
    written_path = Path(artifact.payload["path"])
    assert written_path.is_file()
    contents = written_path.read_text(encoding="utf-8")
    assert "ADR-001" in contents
    assert "## Tradeoffs" in contents
    assert "familiar ops" in contents


async def test_deliberate_question_to_operator_routes_to_operator_with_question_act(
    tmp_path: Path,
) -> None:
    """When Cat picks ``decision: "question_to_operator"``, the
    emitted utterance must have ``speech_act=QUESTION`` AND
    ``addressed_to`` containing the operator identity — that's the
    shape the runner's user-question watcher matches against
    (``is_question_to_operator``). Without this, the question gets
    broadcast to caucus and the operator never sees it.

    Regression guard for the bug where every agent hardcoded
    ``addressed_to="caucus"`` so the operator-question pipeline was
    structurally bricked despite the runner-side machinery being in
    place.
    """
    from wonderland.utterance import (
        OPERATOR_NAME,
        is_question_to_operator,
    )

    payload = {
        "decision": "question_to_operator",
        "body": (
            "The directive says 'TUI' but the team's contracts are "
            "drifting toward HTTP boundaries — should the runtime "
            "be a single-process TUI or do we need a backend service?"
        ),
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    cat = await _cat(tmp_path, llm=llm)
    trigger = _u(thread_id="architecture", body="ADR drift")
    ctx = Context(constitution=cat.identity.constitution_text, triggers=(trigger,))

    utterance = await cat.deliberate(ctx)

    assert utterance is not None
    # speech_act = QUESTION (not "question_to_operator" — that's
    # the schema decision name; the bus-level type is QUESTION).
    assert utterance.speech_act is SpeechAct.QUESTION
    # addressed_to is a list (not "caucus") containing operator.
    assert isinstance(utterance.addressed_to, list)
    assert any(
        aid.name == OPERATOR_NAME for aid in utterance.addressed_to
    )
    # The runner's filter recognizes this as an operator-question.
    assert is_question_to_operator(utterance)
    # Body is preserved verbatim.
    assert "TUI" in utterance.content.body
    # In-team question routing not affected — caucus addressing
    # only kicks in when decision != question_to_operator.


async def test_deliberate_skips_adr_when_no_registry(tmp_path: Path) -> None:
    """If no ADR registry was supplied, the proposal still ships — without artifact."""
    payload = {
        "decision": "proposal",
        "body": "...",
        "adr": {
            "title": "T",
            "context": "C",
            "decision": "D",
            "tradeoffs": ["t"],
        },
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    cat = await _cat(tmp_path, llm=llm, with_registry=False)
    ctx = Context(constitution=cat.identity.constitution_text, triggers=(_u(),))

    utterance = await cat.deliberate(ctx)

    assert utterance is not None
    assert utterance.content.artifacts == []


async def test_deliberate_includes_protocol_in_system_prompt(tmp_path: Path) -> None:
    """The Cat's output protocol is appended after the constitution."""
    llm = _mock_llm('```json\n{"decision": "silence"}\n```')
    cat = await _cat(tmp_path, llm=llm)
    ctx = Context(constitution="C", triggers=(_u(),))
    await cat.deliberate(ctx)

    # Inspect what the LLM was called with via the underlying mock
    create_kwargs = cat.llm.client.messages.create.call_args.kwargs
    system_blocks = create_kwargs["system"]
    # Constitution first, protocol second, both cached
    # Position 0 is the framework primer (shared across all agents)
    assert "Wonderland — Framework Primer" in system_blocks[0]["text"]
    assert system_blocks[0]["cache_control"] == {"type": "ephemeral"}
    # Position 1 is the per-agent constitution
    assert system_blocks[1]["text"] == "C"
    assert system_blocks[1]["cache_control"] == {"type": "ephemeral"}
    assert "fenced JSON block" in system_blocks[2]["text"]
    assert system_blocks[2]["cache_control"] == {"type": "ephemeral"}


# ---------- end-to-end (mocked LLM) ----------


async def test_end_to_end_directive_produces_proposal_with_adr(tmp_path: Path) -> None:
    """Publish a directive, run the Cat, observe a proposal + ADR file."""
    payload = {
        "decision": "proposal",
        "body": "What would have to be true for X to be the right call?",
        "adr": {
            "title": "Use Redis Streams for the Caucus",
            "context": "We need a durable, ordered event bus for agent communication.",
            "decision": "Use Redis Streams as the Caucus implementation.",
            "tradeoffs": [
                "familiar operational profile",
                "single-region default; cross-region replication is non-trivial",
                "stream growth requires explicit retention policy",
            ],
        },
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    cat = await _cat(tmp_path, llm=llm)
    observer = cat.bus.subscribe(agent_name="observer")

    run_task = asyncio.create_task(cat.run())
    await cat.bus.publish(_u(act=SpeechAct.DIRECTIVE, body="build a translation chat app"))

    # Skip echoes of the original directive on the observer subscription
    received = await asyncio.wait_for(anext(observer), timeout=2.0)
    while received.speaker.name != "cheshire_cat":
        received = await asyncio.wait_for(anext(observer), timeout=2.0)

    assert received.speech_act is SpeechAct.PROPOSAL
    assert "What would have to be true" in received.content.body
    assert len(received.content.artifacts) == 1
    assert received.content.artifacts[0].kind == "adr"

    # ADR file appears at .wonderland/architecture/adr-001-*.md
    adr_dir = tmp_path / ".wonderland" / "architecture"
    adr_files = list(adr_dir.glob("adr-001-*.md"))
    assert len(adr_files) == 1
    assert "use-redis-streams-for-the-caucus" in adr_files[0].name

    # Cat recorded the proposal in episodic memory
    cat_history = await cat.memory.query_by_speaker("cheshire_cat")
    assert len(cat_history) == 1
    assert cat_history[0].content.body == received.content.body

    await cat.stop()
    run_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await run_task
    await cat.memory.close()


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
async def test_live_cat_smoke(tmp_path: Path) -> None:
    """Real Haiku 4.5 round-trip: directive in, in-character proposal out."""
    cat = await _cat(tmp_path, llm=LLMClient())
    observer = cat.bus.subscribe(agent_name="observer")
    run_task = asyncio.create_task(cat.run())

    await cat.bus.publish(
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
    while received.speaker.name != "cheshire_cat":
        received = await asyncio.wait_for(anext(observer), timeout=30.0)

    # The Cat must have spoken something substantive in his own voice
    assert received.speech_act in {
        SpeechAct.PROPOSAL,
        SpeechAct.QUESTION,
        SpeechAct.REFRAME,
        SpeechAct.CONCERN,
    }
    assert len(received.content.body) > 20

    await cat.stop()
    run_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await run_task
    await cat.memory.close()
