"""Tests for the Caterpillar — Senior Engineer / Code Review."""

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
    Caterpillar,
    CaterpillarResponseParseError,
    Context,
    Engagement,
    InMemoryCaucus,
    LLMClient,
    ReviewRegistry,
    SpeechAct,
    Utterance,
    UtteranceContent,
    caterpillar_rules,
    parse_caterpillar_response,
)

# ---------- helpers ----------


def _u(
    *,
    thread_id: str = "t",
    speaker: str = "tweedledee",
    addressed: list[str] | str = "caucus",
    act: SpeechAct = SpeechAct.IMPLEMENTATION,
    body: str = "implemented the refund handler at handlers/payments.py",
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


async def _caterpillar(
    tmp_path: Path,
    *,
    llm: LLMClient | None = None,
    with_registry: bool = False,
) -> Caterpillar:
    bus = InMemoryCaucus()
    memory = AgentMemory.for_project(tmp_path, "caterpillar")
    await memory.open()
    registry = ReviewRegistry(tmp_path) if with_registry else None
    return Caterpillar(memory=memory, bus=bus, llm=llm, review_registry=registry)


def _finding_dict(**overrides) -> dict:
    base = {
        "severity": "change-required",
        "title": "validate_input also writes to the database",
        "location": "handlers/payments.py:42",
        "quote": "if not _ok(req):\n    log_attempt(req)\n    return False",
        "read": "Despite the name, this function logs to the database in the rejection path.",
        "concern": (
            "Future callers will rely on the validation-only contract the name implies "
            "and be surprised by the side effect."
        ),
        "request": "Rename to validate_and_log_input or split out the logging call.",
    }
    return base | overrides


def _review_dict(**overrides) -> dict:
    base = {
        "title": "Payment refund handler",
        "target_files": ["src/payments/refund.py"],
        "verdict": "request-changes",
        "findings": [_finding_dict()],
        "approvals": [],
        "cross_domain_references": [],
    }
    return base | overrides


# ---------- engagement rules ----------


def test_rules_implementation_from_tweedle_is_always() -> None:
    rules = caterpillar_rules()
    for tweedle in ("tweedledee", "tweedledum"):
        assert (
            rules.categorize(_u(act=SpeechAct.IMPLEMENTATION, speaker=tweedle)) is Engagement.ALWAYS
        )


def test_rules_implementation_from_other_is_almost_never() -> None:
    rules = caterpillar_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.IMPLEMENTATION, speaker="dodo"))
        is Engagement.ALMOST_NEVER
    )


def test_rules_review_only_when_addressed_to_caterpillar() -> None:
    rules = caterpillar_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.REVIEW, addressed=["caterpillar"])) is Engagement.ALWAYS
    )
    assert rules.categorize(_u(act=SpeechAct.REVIEW, addressed="caucus")) is Engagement.ALMOST_NEVER


def test_rules_concern_with_quality_words_is_always() -> None:
    rules = caterpillar_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.CONCERN, body="this affects test coverage and naming"))
        is Engagement.ALWAYS
    )


def test_rules_concern_without_quality_words_is_almost_never() -> None:
    rules = caterpillar_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.CONCERN, body="we should ship before the deadline"))
        is Engagement.ALMOST_NEVER
    )


def test_rules_test_scenario_from_hatter_is_always() -> None:
    rules = caterpillar_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.TEST_SCENARIO, speaker="mad_hatter")) is Engagement.ALWAYS
    )


def test_rules_test_scenario_from_other_is_almost_never() -> None:
    rules = caterpillar_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.TEST_SCENARIO, speaker="dodo")) is Engagement.ALMOST_NEVER
    )


def test_rules_question_only_when_addressed_to_caterpillar() -> None:
    rules = caterpillar_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.QUESTION, addressed=["caterpillar"])) is Engagement.ALWAYS
    )
    assert (
        rules.categorize(_u(act=SpeechAct.QUESTION, addressed="caucus")) is Engagement.ALMOST_NEVER
    )


def test_rules_proposal_from_cat_is_selective() -> None:
    rules = caterpillar_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.PROPOSAL, speaker="cheshire_cat"))
        is Engagement.SELECTIVELY
    )


def test_rules_proposal_from_other_is_almost_never() -> None:
    rules = caterpillar_rules()
    assert rules.categorize(_u(act=SpeechAct.PROPOSAL, speaker="dodo")) is Engagement.ALMOST_NEVER


def test_rules_ticket_from_rabbit_is_selective() -> None:
    rules = caterpillar_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.TICKET, speaker="white_rabbit")) is Engagement.SELECTIVELY
    )


def test_rules_ruling_from_queen_is_selective() -> None:
    rules = caterpillar_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.RULING, speaker="queen_of_hearts"))
        is Engagement.SELECTIVELY
    )


def test_rules_observation_from_dormouse_is_selective() -> None:
    rules = caterpillar_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.OBSERVATION, speaker="dormouse"))
        is Engagement.SELECTIVELY
    )


def test_rules_deference_is_rare() -> None:
    rules = caterpillar_rules()
    assert rules.categorize(_u(act=SpeechAct.DEFERENCE)) is Engagement.RARELY


def test_rules_alice_stories_engage_always() -> None:
    """Caterpillar joined Alice on M1 (was Alice-only before): on
    each story Alice ships he engages and either reviews the shape
    (concern/question on missing confusion-flag, generic persona,
    overlap, etc.) OR ships a plumbing-side story of his own
    covering surfaces Alice's "inhabit users" frame doesn't reach
    (testing infra, observability, deployment). Replaces the
    earlier assertion that he didn't engage with stories at all
    — that was the legacy roster shape."""
    rules = caterpillar_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.STORY, speaker="alice"))
        is Engagement.ALWAYS
    )


def test_rules_stories_engage_regardless_of_author() -> None:
    """Updated from the legacy speaker_is('alice') restriction:
    stories trigger Caterpillar review regardless of author. He
    reviews story shape (confusion-flag present, persona specific,
    etc.) and may also ship a plumbing story of his own when the
    set is incomplete. Self-loops are prevented by the listen-loop's
    self-skip (Caterpillar doesn't engage with his own stories)."""
    rules = caterpillar_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.STORY, speaker="white_rabbit"))
        is Engagement.ALWAYS
    )
    # Self-engagement is still prevented at the listen-loop layer
    # (agent.py skips own-speaker utterances), so this rule
    # firing on caterpillar-as-speaker doesn't cause infinite
    # review of his own stories.
    assert (
        rules.categorize(_u(act=SpeechAct.STORY, speaker="caterpillar"))
        is Engagement.ALWAYS
    )


# ---------- parse_caterpillar_response ----------


def test_parse_silence() -> None:
    response = parse_caterpillar_response('{"decision": "silence"}')
    assert response.decision == "silence"
    assert response.reviews == []


def test_parse_silence_coerces_explicit_nulls() -> None:
    """Live Haiku 4.5 sometimes emits explicit nulls for omitted fields."""
    response = parse_caterpillar_response('{"decision": "silence", "body": null, "reviews": null}')
    assert response.decision == "silence"
    assert response.body == ""
    assert response.reviews == []


def test_parse_concern() -> None:
    text = (
        '```json\n{"decision": "concern", "body": "third reviewer-as-author drift this week"}\n```'
    )
    response = parse_caterpillar_response(text)
    assert response.decision == "concern"
    assert "drift" in response.body


def test_parse_question() -> None:
    text = '{"decision": "question", "body": "what is the invariant on retry?"}'
    response = parse_caterpillar_response(text)
    assert response.decision == "question"


def test_parse_review_with_one_review() -> None:
    payload = {
        "decision": "review",
        "body": "Reviewing the refund handler — one change-required, otherwise clean.",
        "reviews": [_review_dict()],
    }
    response = parse_caterpillar_response(f"```json\n{json.dumps(payload)}\n```")
    assert response.decision == "review"
    assert len(response.reviews) == 1
    assert response.reviews[0].verdict.value == "request-changes"


def test_parse_review_with_multiple_reviews() -> None:
    payload = {
        "decision": "review",
        "body": "Two implementations landed; reviewing both.",
        "reviews": [
            _review_dict(title="Refund handler"),
            _review_dict(
                title="Auth middleware",
                verdict="accept",
                findings=[],
                approvals=["the new exception type carries actionable context"],
            ),
        ],
    }
    response = parse_caterpillar_response(f"```json\n{json.dumps(payload)}\n```")
    assert len(response.reviews) == 2


def test_parse_rejects_review_decision_with_no_reviews() -> None:
    with pytest.raises(CaterpillarResponseParseError):
        parse_caterpillar_response('{"decision": "review", "body": "...", "reviews": []}')


def test_parse_rejects_story_decision_with_empty_stories() -> None:
    """validation2 pilot deadlock — agent declared decision='story'
    without populating the stories[] payload, repeatedly. Validator
    now requires the payload to actually exist when the decision
    says so."""
    with pytest.raises(CaterpillarResponseParseError):
        parse_caterpillar_response(
            '{"decision": "story", "body": "I will author foundation stories", "stories": []}'
        )


def test_parse_accepts_story_decision_with_payload() -> None:
    """Happy path: decision='story' with a real StoryPayload entry
    parses cleanly. Tests that the validator gate isn't accidentally
    rejecting valid story emissions."""
    payload = {
        "decision": "story",
        "stories": [{
            "title": "Maya the developer runs the dashboard with mock data",
            "persona": "Maya the developer onboarding to the codebase",
            "situation": "First time setup; no external API keys yet.",
            "need": "As Maya, I want to run the dashboard with OBOL_MOCK=1 so I can exercise UX without setting up Plaid.",
            "acceptance": [
                "OBOL_MOCK=1 yields seeded mock data on dashboard load",
                "real Plaid path bypassed cleanly under mock",
            ],
            "tier": "core",
            "confusion_flags": ["seed data scope undefined for sandbox vs production fixtures"],
        }],
    }
    response = parse_caterpillar_response(
        f"```json\n{json.dumps(payload)}\n```"
    )
    assert response.decision == "story"
    assert len(response.stories) == 1
    assert response.stories[0].persona.startswith("Maya")


def test_parse_rejects_accept_with_no_approvals() -> None:
    """Schema validation propagates: accept requires substantive approvals."""
    payload = {
        "decision": "review",
        "body": "...",
        "reviews": [
            _review_dict(verdict="accept", findings=[], approvals=[]),
        ],
    }
    with pytest.raises(CaterpillarResponseParseError):
        parse_caterpillar_response(f"```json\n{json.dumps(payload)}\n```")


def test_parse_rejects_invalid_decision() -> None:
    with pytest.raises(CaterpillarResponseParseError):
        parse_caterpillar_response('{"decision": "bless"}')


def test_parse_rejects_missing_json() -> None:
    with pytest.raises(CaterpillarResponseParseError):
        parse_caterpillar_response("just plain text")


# ---------- Caterpillar construction ----------


async def test_caterpillar_loads_constitution(tmp_path: Path) -> None:
    cat = await _caterpillar(tmp_path)
    assert cat.identity.name == "caterpillar"
    assert "Caterpillar" in cat.identity.constitution_text


async def test_caterpillar_engagement_policy_wired(tmp_path: Path) -> None:
    cat = await _caterpillar(tmp_path)
    impl = _u(act=SpeechAct.IMPLEMENTATION, speaker="tweedledee")
    foreign_proposal = _u(act=SpeechAct.PROPOSAL, speaker="dodo")
    assert cat.should_engage(impl) is True
    assert cat.should_engage(foreign_proposal) is False


async def test_caterpillar_with_no_llm_is_silent(tmp_path: Path) -> None:
    cat = await _caterpillar(tmp_path, llm=None)
    ctx = Context(constitution=cat.identity.constitution_text, triggers=(_u(),))
    assert await cat.deliberate(ctx) is None


# ---------- deliberate ----------


async def test_deliberate_returns_none_on_silence(tmp_path: Path) -> None:
    llm = _mock_llm('```json\n{"decision": "silence"}\n```')
    cat = await _caterpillar(tmp_path, llm=llm)
    ctx = Context(constitution=cat.identity.constitution_text, triggers=(_u(),))
    assert await cat.deliberate(ctx) is None


async def test_deliberate_publishes_concern(tmp_path: Path) -> None:
    body = "third reviewer-as-author drift this week — class concern"
    llm = _mock_llm(f"```json\n{json.dumps({'decision': 'concern', 'body': body})}\n```")
    cat = await _caterpillar(tmp_path, llm=llm)
    trigger = _u(thread_id="t", body="implementation lands")
    ctx = Context(constitution=cat.identity.constitution_text, triggers=(trigger,))

    utterance = await cat.deliberate(ctx)

    assert utterance is not None
    assert utterance.speech_act is SpeechAct.CONCERN
    assert "reviewer-as-author" in utterance.content.body
    assert utterance.thread_id == "t"
    assert utterance.parent_id == trigger.id


async def test_deliberate_inlines_review_when_no_registry(tmp_path: Path) -> None:
    """Without a registry, the structured review rides on the bus inline."""
    payload = {
        "decision": "review",
        "body": "Reviewing the refund handler.",
        "reviews": [_review_dict()],
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    cat = await _caterpillar(tmp_path, llm=llm, with_registry=False)
    ctx = Context(constitution=cat.identity.constitution_text, triggers=(_u(),))

    utterance = await cat.deliberate(ctx)

    assert utterance is not None
    assert utterance.speech_act is SpeechAct.REVIEW
    assert len(utterance.content.artifacts) == 1
    artifact = utterance.content.artifacts[0]
    assert artifact.kind == "review"
    # Inline payload contains the full review structure, not just a pointer
    assert artifact.payload["verdict"] == "request-changes"
    assert "review" in artifact.payload
    assert artifact.payload["review"]["findings"][0]["severity"] == "change-required"
    # No file written
    assert not (tmp_path / ".wonderland" / "reviews").exists()


async def test_deliberate_persists_review_when_registry_present(tmp_path: Path) -> None:
    payload = {
        "decision": "review",
        "body": "Reviewing the refund handler.",
        "reviews": [_review_dict()],
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    cat = await _caterpillar(tmp_path, llm=llm, with_registry=True)
    ctx = Context(constitution=cat.identity.constitution_text, triggers=(_u(),))

    utterance = await cat.deliberate(ctx)

    assert utterance is not None
    assert utterance.speech_act is SpeechAct.REVIEW
    artifact = utterance.content.artifacts[0]
    assert artifact.kind == "review"
    # Persisted artifact carries a path pointer, not inline content
    assert "path" in artifact.payload
    assert artifact.payload["verdict"] == "request-changes"

    reviews_dir = tmp_path / ".wonderland" / "reviews"
    files = sorted(reviews_dir.glob("review-*.md"))
    assert len(files) == 1


async def test_persisted_review_artifact_carries_findings(tmp_path: Path) -> None:
    """P15 follow-up — even when the review is persisted to a
    registry (and the bus payload could in principle stay thin),
    the artifact's findings list must be inline so the post-
    meeting routing (``_route_blocking_review`` →
    ``_synthesize_followup_ticket_from_finding``) can iterate over
    them. The discovery5 pilot showed the bus payload omitting
    findings → zero synthesized tickets → reviews disappearing
    into the wind. This test pins findings inline going forward."""
    payload = {
        "decision": "review",
        "body": "Reviewing the refund handler.",
        "reviews": [_review_dict()],
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    cat = await _caterpillar(tmp_path, llm=llm, with_registry=True)
    ctx = Context(constitution=cat.identity.constitution_text, triggers=(_u(),))

    utterance = await cat.deliberate(ctx)
    assert utterance is not None
    artifact = utterance.content.artifacts[0]
    assert artifact.kind == "review"
    # Findings must travel with the artifact even when the file
    # is on disk — the auto-ticket synthesis reads from the bus
    # payload, not from disk.
    assert isinstance(artifact.payload.get("findings"), list)
    assert len(artifact.payload["findings"]) >= 1
    finding = artifact.payload["findings"][0]
    assert "severity" in finding
    assert "title" in finding
    assert "concern" in finding
    assert "request" in finding


async def test_deliberate_includes_protocol_in_system_prompt(tmp_path: Path) -> None:
    llm = _mock_llm('```json\n{"decision": "silence"}\n```')
    cat = await _caterpillar(tmp_path, llm=llm)
    ctx = Context(constitution="C", triggers=(_u(),))
    await cat.deliberate(ctx)

    create_kwargs = cat.llm.client.messages.create.call_args.kwargs
    system_blocks = create_kwargs["system"]
    # Position 0 is the framework primer (shared across all agents)
    assert "Wonderland — Framework Primer" in system_blocks[0]["text"]
    assert "cache_control" not in system_blocks[0]  # framework primer is plain string since context-compression Lever A (cache breakpoint reused for current_thread)
    # Position 1 is the per-agent constitution
    assert system_blocks[1]["text"] == "C"
    assert system_blocks[1]["cache_control"] == {"type": "ephemeral"}
    assert "fenced JSON block" in system_blocks[2]["text"]
    assert "approval is not given cheaply" in system_blocks[2]["text"]
    assert system_blocks[2]["cache_control"] == {"type": "ephemeral"}


# ---------- end-to-end (mocked LLM) ----------


async def test_end_to_end_implementation_produces_review(tmp_path: Path) -> None:
    payload = {
        "decision": "review",
        "body": "Reviewing the refund handler — one change-required.",
        "reviews": [_review_dict()],
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    cat = await _caterpillar(tmp_path, llm=llm, with_registry=True)
    observer = cat.bus.subscribe(agent_name="observer")

    run_task = asyncio.create_task(cat.run())
    await cat.bus.publish(
        _u(
            act=SpeechAct.IMPLEMENTATION,
            speaker="tweedledee",
            body="implemented the refund handler at handlers/payments.py",
        )
    )

    received = await asyncio.wait_for(anext(observer), timeout=2.0)
    while received.speaker.name != "caterpillar":
        received = await asyncio.wait_for(anext(observer), timeout=2.0)

    assert received.speech_act is SpeechAct.REVIEW
    assert len(received.content.artifacts) == 1

    reviews_dir = tmp_path / ".wonderland" / "reviews"
    assert len(list(reviews_dir.glob("review-*.md"))) == 1

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
async def test_live_caterpillar_smoke(tmp_path: Path) -> None:
    """Real Haiku 4.5 round-trip: implementation in, in-character Caterpillar move out."""
    cat = await _caterpillar(tmp_path, llm=LLMClient(), with_registry=True)
    observer = cat.bus.subscribe(agent_name="observer")
    run_task = asyncio.create_task(cat.run())

    try:
        await cat.bus.publish(
            _u(
                act=SpeechAct.IMPLEMENTATION,
                speaker="tweedledum",
                body=(
                    "Implemented the user-deletion endpoint at handlers/users.py. "
                    "It validates the session, fetches the user, and calls "
                    "delete_user(user_id). Tests cover the happy path. "
                    "```python\n"
                    "def delete_user_handler(request):\n"
                    "    session = request.session\n"
                    "    if not session:\n"
                    "        return 401\n"
                    "    user = User.get(session.user_id)\n"
                    "    delete_user(user.id)\n"
                    "    return 200\n"
                    "```"
                ),
            )
        )

        # The Caterpillar deliberates slowly on purpose (§I "moves slowly"),
        # and a structured Review with multiple findings is a longer LLM
        # round-trip than the other agents' artifacts.
        received = await asyncio.wait_for(anext(observer), timeout=120.0)
        while received.speaker.name != "caterpillar":
            received = await asyncio.wait_for(anext(observer), timeout=120.0)

        assert received.speech_act in {
            SpeechAct.REVIEW,
            SpeechAct.CONCERN,
            SpeechAct.QUESTION,
        }
        # Body may be empty when the speech act is REVIEW — the structured
        # review artifact is the message; additional prose is optional.
        # For non-review acts, body carries the substance.
        if received.speech_act is not SpeechAct.REVIEW:
            assert len(received.content.body) > 0

        if received.speech_act is SpeechAct.REVIEW:
            assert received.content.artifacts
            artifact = received.content.artifacts[0]
            assert artifact.payload["verdict"] in {"accept", "request-changes", "block"}
    finally:
        await cat.stop()
        run_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await run_task
        await cat.memory.close()
