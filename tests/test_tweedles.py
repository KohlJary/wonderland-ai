"""Tests for the Tweedles — Tweedledee + Tweedledum, the implementation pair."""

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
    ContractNotePayload,
    ContractNoteRegistry,
    ContractNoteState,
    Engagement,
    ImplementationRegistry,
    ImplementationSide,
    InMemoryCaucus,
    LLMClient,
    SpeechAct,
    Tweedledee,
    Tweedledum,
    TweedleResponseParseError,
    Utterance,
    UtteranceContent,
    parse_tweedle_response,
    tweedledee_rules,
    tweedledum_rules,
)

# ---------- helpers ----------


def _u(
    *,
    thread_id: str = "t",
    speaker: str = "white_rabbit",
    addressed: list[str] | str = "caucus",
    act: SpeechAct = SpeechAct.TICKET,
    body: str = "ticket-014: wire the message subscription on the frontend",
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


async def _tweedledee(
    tmp_path: Path,
    *,
    llm: LLMClient | None = None,
    with_registry: bool = True,
    with_contract_notes: bool = True,
) -> Tweedledee:
    bus = InMemoryCaucus()
    memory = AgentMemory.for_project(tmp_path, "tweedledee")
    await memory.open()
    registry = ImplementationRegistry(tmp_path) if with_registry else None
    notes = ContractNoteRegistry(tmp_path) if with_contract_notes else None
    return Tweedledee(
        memory=memory,
        bus=bus,
        llm=llm,
        implementation_registry=registry,
        contract_note_registry=notes,
    )


async def _tweedledum(
    tmp_path: Path,
    *,
    llm: LLMClient | None = None,
    with_registry: bool = True,
    with_contract_notes: bool = True,
) -> Tweedledum:
    bus = InMemoryCaucus()
    memory = AgentMemory.for_project(tmp_path, "tweedledum")
    await memory.open()
    registry = ImplementationRegistry(tmp_path) if with_registry else None
    notes = ContractNoteRegistry(tmp_path) if with_contract_notes else None
    return Tweedledum(
        memory=memory,
        bus=bus,
        llm=llm,
        implementation_registry=registry,
        contract_note_registry=notes,
    )


def _frontend_impl_dict(**overrides) -> dict:
    base = {
        "title": "Translation message subscription",
        "side": "frontend",
        "ticket_reference": "ticket-014-translation-message-subscription",
        "approach_summary": "WebSocket subscription with virtual scroll and pending-translation queue.",
        "contract": "message-envelope v3 + message-translated event",
        "files_touched": ["src/chat/MessageList.tsx"],
        "open_questions_for_pair": [
            "Does message-translated arrive once per language?",
        ],
        "ready_for_review": True,
        "ui_states_implemented": ["loading", "empty", "error-recoverable", "stale"],
        "client_state": "Pending-translation queue keyed by message_id; 60s TTL.",
    }
    return base | overrides


def _backend_impl_dict(**overrides) -> dict:
    base = {
        "title": "Translation worker pipeline",
        "side": "backend",
        "ticket_reference": "ticket-015-translation-worker-pipeline",
        "approach_summary": "Worker pool persists jobs and emits message-translated events.",
        "contract": "message-envelope v3 + message-translated event",
        "files_touched": ["services/translation/worker.py"],
        "ready_for_review": True,
        "invariants_enforced": [
            "every translated message has exactly one source_lang (DB FK NOT NULL)",
        ],
        "schema_changes": "Migration 0042 adds translation_status enum + source_lang FK; backfilled.",
        "failure_modes_handled": [
            "worker crash mid-message: job re-enqueued via at-least-once delivery",
        ],
    }
    return base | overrides


# ---------- engagement rules: shared structure ----------


def test_dee_rules_ticket_from_rabbit_is_always() -> None:
    assert (
        tweedledee_rules().categorize(_u(act=SpeechAct.TICKET, speaker="white_rabbit"))
        is Engagement.ALWAYS
    )


def test_dum_rules_ticket_from_rabbit_is_always() -> None:
    assert (
        tweedledum_rules().categorize(_u(act=SpeechAct.TICKET, speaker="white_rabbit"))
        is Engagement.ALWAYS
    )


def test_dee_rules_proposal_from_cat_is_always() -> None:
    assert (
        tweedledee_rules().categorize(_u(act=SpeechAct.PROPOSAL, speaker="cheshire_cat"))
        is Engagement.ALWAYS
    )


def test_dum_rules_proposal_from_cat_is_always() -> None:
    assert (
        tweedledum_rules().categorize(_u(act=SpeechAct.PROPOSAL, speaker="cheshire_cat"))
        is Engagement.ALWAYS
    )


def test_dee_rules_story_from_alice_is_always() -> None:
    assert (
        tweedledee_rules().categorize(_u(act=SpeechAct.STORY, speaker="alice")) is Engagement.ALWAYS
    )


def test_dee_rules_test_scenario_from_hatter_is_always() -> None:
    assert (
        tweedledee_rules().categorize(_u(act=SpeechAct.TEST_SCENARIO, speaker="mad_hatter"))
        is Engagement.ALWAYS
    )


def test_dee_rules_review_from_caterpillar_is_always() -> None:
    assert (
        tweedledee_rules().categorize(_u(act=SpeechAct.REVIEW, speaker="caterpillar"))
        is Engagement.ALWAYS
    )


def test_dee_rules_question_only_when_addressed_to_dee() -> None:
    rules = tweedledee_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.QUESTION, addressed=["tweedledee"])) is Engagement.ALWAYS
    )
    assert (
        rules.categorize(_u(act=SpeechAct.QUESTION, addressed="caucus")) is Engagement.ALMOST_NEVER
    )


def test_dum_rules_question_only_when_addressed_to_dum() -> None:
    rules = tweedledum_rules()
    assert (
        rules.categorize(_u(act=SpeechAct.QUESTION, addressed=["tweedledum"])) is Engagement.ALWAYS
    )


# ---------- engagement rules: mirror-image sibling orientation ----------


def test_dee_engages_always_with_concern_from_dum() -> None:
    """Concerns from the sibling are the contract-negotiation surface."""
    assert (
        tweedledee_rules().categorize(_u(act=SpeechAct.CONCERN, speaker="tweedledum"))
        is Engagement.ALWAYS
    )


def test_dum_engages_always_with_concern_from_dee() -> None:
    assert (
        tweedledum_rules().categorize(_u(act=SpeechAct.CONCERN, speaker="tweedledee"))
        is Engagement.ALWAYS
    )


def test_dee_engages_rarely_with_dum_implementation() -> None:
    """Sibling implementation that doesn't touch the contract isn't his primary surface."""
    assert (
        tweedledee_rules().categorize(_u(act=SpeechAct.IMPLEMENTATION, speaker="tweedledum"))
        is Engagement.RARELY
    )


def test_dum_engages_rarely_with_dee_implementation() -> None:
    assert (
        tweedledum_rules().categorize(_u(act=SpeechAct.IMPLEMENTATION, speaker="tweedledee"))
        is Engagement.RARELY
    )


def test_implementation_from_non_sibling_is_almost_never() -> None:
    """The Tweedles don't echo same-typed utterances from non-sibling speakers."""
    assert (
        tweedledee_rules().categorize(_u(act=SpeechAct.IMPLEMENTATION, speaker="dodo"))
        is Engagement.ALMOST_NEVER
    )
    assert (
        tweedledum_rules().categorize(_u(act=SpeechAct.IMPLEMENTATION, speaker="dodo"))
        is Engagement.ALMOST_NEVER
    )


# ---------- engagement rules: SELECTIVELY ----------


def test_ruling_from_queen_is_selective_for_both() -> None:
    for rules in (tweedledee_rules(), tweedledum_rules()):
        assert (
            rules.categorize(_u(act=SpeechAct.RULING, speaker="queen_of_hearts"))
            is Engagement.SELECTIVELY
        )


def test_observation_from_dormouse_is_selective_for_both() -> None:
    for rules in (tweedledee_rules(), tweedledum_rules()):
        assert (
            rules.categorize(_u(act=SpeechAct.OBSERVATION, speaker="dormouse"))
            is Engagement.SELECTIVELY
        )


# ---------- engagement rules: ALMOST_NEVER guards ----------


def test_directive_engages_both() -> None:
    """The Tweedles engage on convenor directives. Without this, an
    implementation-only meeting (Tweedles + Dodo, no Cat or Alice on
    roster) sees a Dodo directive land on the bus and nobody listens —
    none of the Tweedles' other engagement triggers (tickets, sibling
    moves) have fired yet, so the meeting goes silent. The directive is
    what tells the pair what THIS meeting is for; ignoring it makes
    meeting-mode signals impossible."""
    for rules in (tweedledee_rules(), tweedledum_rules()):
        assert rules.categorize(_u(act=SpeechAct.DIRECTIVE)) is Engagement.ALWAYS


def test_review_from_non_caterpillar_is_almost_never_for_both() -> None:
    for rules in (tweedledee_rules(), tweedledum_rules()):
        assert rules.categorize(_u(act=SpeechAct.REVIEW, speaker="dodo")) is Engagement.ALMOST_NEVER


# ---------- parse_tweedle_response ----------


def test_parse_silence() -> None:
    response = parse_tweedle_response('{"decision": "silence"}')
    assert response.decision == "silence"
    assert response.implementations == []


def test_parse_recovers_from_narration_before_json() -> None:
    """The Tweedle (Haiku) sometimes narrates before producing the
    JSON, e.g.: 'Let me think about this...\\n\\n{"decision": ...}'.
    The parser scans for brace-balanced JSON substrings as a fallback
    when neither a fenced block nor a bare-JSON whole-text match is
    found. Without this fallback, the v10-v14 enchilada runs lost
    multiple Tweedle turns to 'no JSON block found' silences."""
    text = (
        "Reading the contract notes carefully. Tweedledum's envelope "
        "shape is workable. I'll ship the frontend types now.\n\n"
        '{"decision": "silence"}'
    )
    response = parse_tweedle_response(text)
    assert response.decision == "silence"


def test_parse_recovers_from_json_with_trailing_narration() -> None:
    """LLM also sometimes appends commentary after the JSON. The
    brace-balanced scan finds the object regardless of what surrounds
    it."""
    text = (
        '{"decision": "concern", "body": "the contract is underspecified"}\n\n'
        "Hopefully Tweedledee responds with the missing detail."
    )
    response = parse_tweedle_response(text)
    assert response.decision == "concern"
    assert "underspecified" in response.body


def test_parse_picks_first_valid_json_object() -> None:
    """If multiple JSON-shaped substrings are present (e.g., the LLM
    quoted a prior contract note in its narration), the first one that
    validates against TweedleResponse wins. Quoted JSON snippets that
    don't match the schema get skipped."""
    text = (
        'Earlier I saw {"shape": "irrelevant"} on the bus, but my actual move:\n'
        '{"decision": "silence"}'
    )
    response = parse_tweedle_response(text)
    assert response.decision == "silence"


def test_parse_coerces_acknowledgment_to_deference() -> None:
    """Haiku 4.5 occasionally emits decision='acknowledgment' (saw it in
    v8 enchilada M3 transcript). The decision validator maps it to
    'deference' rather than rejecting the whole response — the LLM's
    intent is 'I'm aligned with what my sibling said,' which is what
    deference means in the Tweedle schema."""
    response = parse_tweedle_response('{"decision": "acknowledgment"}')
    assert response.decision == "deference"


def test_parse_coerces_review_to_concern() -> None:
    """Saw in v14 M5: a Tweedle in a 'review' thread reached for
    decision='review' (the Caterpillar's act). Maps to 'concern'
    so the body content survives as a finding-shaped utterance
    rather than being lost to schema rejection."""
    response = parse_tweedle_response(
        '{"decision": "review", "body": "the consent gating is incomplete"}'
    )
    assert response.decision == "concern"
    assert "consent gating" in response.body


def test_parse_silence_coerces_explicit_nulls() -> None:
    """Live Haiku 4.5 sometimes emits explicit nulls for omitted fields."""
    response = parse_tweedle_response(
        '{"decision": "silence", "body": null, "implementations": null}'
    )
    assert response.decision == "silence"
    assert response.body == ""
    assert response.implementations == []


def test_parse_concern() -> None:
    text = (
        '```json\n{"decision": "concern", '
        '"body": "the proposed contract change breaks the offline queue"}\n```'
    )
    response = parse_tweedle_response(text)
    assert response.decision == "concern"
    assert "offline queue" in response.body


def test_parse_question() -> None:
    text = '{"decision": "question", "body": "what is the message-id behavior across edits?"}'
    response = parse_tweedle_response(text)
    assert response.decision == "question"


def test_parse_implementation_with_one_frontend_impl() -> None:
    payload = {
        "decision": "implementation",
        "body": "Frontend impl shipped; ready for review.",
        "implementations": [_frontend_impl_dict()],
    }
    response = parse_tweedle_response(f"```json\n{json.dumps(payload)}\n```")
    assert response.decision == "implementation"
    assert len(response.implementations) == 1
    assert response.implementations[0].side is ImplementationSide.FRONTEND


def test_parse_implementation_with_one_backend_impl() -> None:
    payload = {
        "decision": "implementation",
        "body": "Backend impl shipped.",
        "implementations": [_backend_impl_dict()],
    }
    response = parse_tweedle_response(f"```json\n{json.dumps(payload)}\n```")
    assert response.implementations[0].side is ImplementationSide.BACKEND


def test_parse_implementation_with_multiple_implementations() -> None:
    payload = {
        "decision": "implementation",
        "body": "Two pieces landed together.",
        "implementations": [
            _frontend_impl_dict(title="Subscription"),
            _frontend_impl_dict(title="Indicator"),
        ],
    }
    response = parse_tweedle_response(f"```json\n{json.dumps(payload)}\n```")
    assert len(response.implementations) == 2


def test_parse_rejects_implementation_decision_with_no_implementations() -> None:
    with pytest.raises(TweedleResponseParseError):
        parse_tweedle_response(
            '{"decision": "implementation", "body": "...", "implementations": []}'
        )


def test_parse_rejects_implementation_with_empty_contract() -> None:
    """Schema validation propagates: implicit contracts are bugs in the making."""
    payload = {
        "decision": "implementation",
        "body": "...",
        "implementations": [_frontend_impl_dict(contract="")],
    }
    with pytest.raises(TweedleResponseParseError):
        parse_tweedle_response(f"```json\n{json.dumps(payload)}\n```")


def test_parse_rejects_implementation_with_empty_ticket() -> None:
    payload = {
        "decision": "implementation",
        "body": "...",
        "implementations": [_frontend_impl_dict(ticket_reference="")],
    }
    with pytest.raises(TweedleResponseParseError):
        parse_tweedle_response(f"```json\n{json.dumps(payload)}\n```")


def test_parse_rejects_invalid_decision() -> None:
    with pytest.raises(TweedleResponseParseError):
        parse_tweedle_response('{"decision": "ship"}')


def test_parse_rejects_missing_json() -> None:
    with pytest.raises(TweedleResponseParseError):
        parse_tweedle_response("just plain text")


# ---------- Tweedledee construction ----------


async def test_dee_loads_constitution_and_pair_protocol(tmp_path: Path) -> None:
    dee = await _tweedledee(tmp_path)
    assert dee.identity.name == "tweedledee"
    text = dee.identity.constitution_text
    # Both the Tweedledee constitution and the pair protocol live in the
    # cached prefix — concatenated so the LLM sees both as part of identity.
    assert "Tweedledee" in text
    assert "Tweedle Pair Protocol" in text
    assert "The Argument Is the Work" in text


async def test_dum_loads_constitution_and_pair_protocol(tmp_path: Path) -> None:
    dum = await _tweedledum(tmp_path)
    assert dum.identity.name == "tweedledum"
    text = dum.identity.constitution_text
    assert "Tweedledum" in text
    assert "Tweedle Pair Protocol" in text


async def test_dee_engagement_policy_wired(tmp_path: Path) -> None:
    dee = await _tweedledee(tmp_path)
    ticket = _u(act=SpeechAct.TICKET, speaker="white_rabbit")
    foreign_review = _u(act=SpeechAct.REVIEW, speaker="dodo")
    assert dee.should_engage(ticket) is True
    assert dee.should_engage(foreign_review) is False


async def test_dum_engagement_policy_wired(tmp_path: Path) -> None:
    dum = await _tweedledum(tmp_path)
    ticket = _u(act=SpeechAct.TICKET, speaker="white_rabbit")
    foreign_review = _u(act=SpeechAct.REVIEW, speaker="dodo")
    assert dum.should_engage(ticket) is True
    assert dum.should_engage(foreign_review) is False


async def test_dee_with_no_llm_is_silent(tmp_path: Path) -> None:
    dee = await _tweedledee(tmp_path, llm=None)
    ctx = Context(constitution=dee.identity.constitution_text, triggers=(_u(),))
    assert await dee.deliberate(ctx) is None


# ---------- deliberate ----------


async def test_dee_deliberate_returns_none_on_silence(tmp_path: Path) -> None:
    llm = _mock_llm('```json\n{"decision": "silence"}\n```')
    dee = await _tweedledee(tmp_path, llm=llm)
    ctx = Context(constitution=dee.identity.constitution_text, triggers=(_u(),))
    assert await dee.deliberate(ctx) is None


async def test_dee_deliberate_publishes_concern(tmp_path: Path) -> None:
    body = "the proposed contract change breaks the offline queue"
    llm = _mock_llm(f"```json\n{json.dumps({'decision': 'concern', 'body': body})}\n```")
    dee = await _tweedledee(tmp_path, llm=llm)
    trigger = _u(thread_id="t", body="contract change incoming")
    ctx = Context(constitution=dee.identity.constitution_text, triggers=(trigger,))

    utterance = await dee.deliberate(ctx)

    assert utterance is not None
    assert utterance.speech_act is SpeechAct.CONCERN
    assert "offline queue" in utterance.content.body
    assert utterance.thread_id == "t"
    assert utterance.parent_id == trigger.id


async def test_dee_writes_frontend_implementation_through_registry(
    tmp_path: Path,
) -> None:
    payload = {
        "decision": "implementation",
        "body": "Frontend impl shipped; ready for review.",
        "implementations": [_frontend_impl_dict()],
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    dee = await _tweedledee(tmp_path, llm=llm)
    ctx = Context(constitution=dee.identity.constitution_text, triggers=(_u(),))

    utterance = await dee.deliberate(ctx)

    assert utterance is not None
    assert utterance.speech_act is SpeechAct.IMPLEMENTATION
    assert len(utterance.content.artifacts) == 1
    artifact = utterance.content.artifacts[0]
    assert artifact.payload["side"] == "frontend"
    assert artifact.payload["ready_for_review"] is True
    assert "contract" in artifact.payload

    impl_dir = tmp_path / ".wonderland" / "implementations"
    files = sorted(impl_dir.glob("implementation-*.md"))
    assert len(files) == 1


async def test_dum_writes_backend_implementation_through_registry(
    tmp_path: Path,
) -> None:
    payload = {
        "decision": "implementation",
        "body": "Backend impl shipped; ready for review.",
        "implementations": [_backend_impl_dict()],
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    dum = await _tweedledum(tmp_path, llm=llm)
    ctx = Context(constitution=dum.identity.constitution_text, triggers=(_u(),))

    utterance = await dum.deliberate(ctx)

    assert utterance is not None
    assert utterance.speech_act is SpeechAct.IMPLEMENTATION
    artifact = utterance.content.artifacts[0]
    assert artifact.payload["side"] == "backend"


# ---------- contract_note action ----------


async def test_dee_proposes_contract_note(tmp_path: Path) -> None:
    """A contract_note=propose action writes a new note via the registry."""
    payload = {
        "decision": "contract_note",
        "body": "Proposing the new envelope shape with translation_status",
        "contract_notes": [
            {
                "operation": "propose",
                "title": "Translation envelope",
                "current_shape": "envelope v2 (text + sender_id)",
                "proposed_change": "add translation_status enum + source_lang FK",
                "source": "story-003-multilingual-chat",
                "frontend_impact": "badge per message; locale toggle in header",
            }
        ],
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    dee = await _tweedledee(tmp_path, llm=llm)
    ctx = Context(constitution=dee.identity.constitution_text, triggers=(_u(),))

    utterance = await dee.deliberate(ctx)

    assert utterance is not None
    assert utterance.speech_act is SpeechAct.CONTRACT_NOTE
    assert len(utterance.content.artifacts) == 1
    artifact = utterance.content.artifacts[0]
    assert artifact.kind == "contract_note"
    assert artifact.payload["operation"] == "propose"
    assert artifact.payload["state"] == "proposed"
    assert artifact.payload["slug"] == "translation-envelope"

    # Verify it landed on disk in the registry's directory.
    notes = ContractNoteRegistry(tmp_path).list_contract_notes()
    assert len(notes) == 1
    assert notes[0].state is ContractNoteState.PROPOSED


async def test_dum_responds_to_existing_contract_note(tmp_path: Path) -> None:
    """A contract_note=respond action mutates an existing note in place."""
    # Seed the registry with a note already in state=proposed.
    seed_registry = ContractNoteRegistry(tmp_path)
    seed = seed_registry.write(
        ContractNotePayload(
            title="Translation envelope",
            current_shape="envelope v2",
            proposed_change="add translation_status enum",
            source="story-003-multilingual-chat",
            frontend_impact="badge per message",
        )
    )

    payload = {
        "decision": "contract_note",
        "body": "Backend impact: new columns + migration",
        "contract_notes": [
            {
                "operation": "respond",
                "slug": seed.slug,
                "backend_impact": "new translation_status column; migration; index on source_lang",
            }
        ],
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    dum = await _tweedledum(tmp_path, llm=llm)
    ctx = Context(constitution=dum.identity.constitution_text, triggers=(_u(),))

    utterance = await dum.deliberate(ctx)

    assert utterance is not None
    assert utterance.speech_act is SpeechAct.CONTRACT_NOTE
    assert utterance.content.artifacts[0].payload["state"] == "counterpart_assessed"

    # Round-trip from disk: both impacts present, state advanced.
    after = ContractNoteRegistry(tmp_path).read_payload(seed.slug)
    assert after is not None
    assert after.state is ContractNoteState.COUNTERPART_ASSESSED
    assert after.frontend_impact == "badge per message"
    assert "new translation_status column" in after.backend_impact


async def test_either_tweedle_can_mark_agreed(tmp_path: Path) -> None:
    """mark_agreed locks the contract version on the existing note."""
    seed_registry = ContractNoteRegistry(tmp_path)
    seed = seed_registry.write(
        ContractNotePayload(
            title="Translation envelope",
            current_shape="envelope v2",
            proposed_change="add translation_status enum",
            source="story-003-multilingual-chat",
            frontend_impact="badge per message",
            backend_impact="new column + migration",
            state=ContractNoteState.COUNTERPART_ASSESSED,
        )
    )

    payload = {
        "decision": "contract_note",
        "body": "Both sides accept; locking v3.",
        "contract_notes": [
            {
                "operation": "mark_agreed",
                "slug": seed.slug,
                "contract_version": "envelope v3",
                "resolution": "Both sides accept; ship under v3",
            }
        ],
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    dee = await _tweedledee(tmp_path, llm=llm)
    ctx = Context(constitution=dee.identity.constitution_text, triggers=(_u(),))

    utterance = await dee.deliberate(ctx)

    assert utterance is not None
    artifact = utterance.content.artifacts[0]
    assert artifact.payload["state"] == "agreed"
    assert artifact.payload["contract_version"] == "envelope v3"


async def test_contract_note_action_validates_required_fields() -> None:
    """The TweedleContractNoteAction validators trip on missing required fields."""
    # propose without title
    bad_propose = {
        "decision": "contract_note",
        "body": "...",
        "contract_notes": [
            {
                "operation": "propose",
                "current_shape": "envelope v2",
                "proposed_change": "add field",
                "source": "story",
                "frontend_impact": "x",
            }
        ],
    }
    with pytest.raises(TweedleResponseParseError):
        parse_tweedle_response(f"```json\n{json.dumps(bad_propose)}\n```")

    # respond without slug
    bad_respond = {
        "decision": "contract_note",
        "body": "...",
        "contract_notes": [
            {
                "operation": "respond",
                "backend_impact": "new column",
            }
        ],
    }
    with pytest.raises(TweedleResponseParseError):
        parse_tweedle_response(f"```json\n{json.dumps(bad_respond)}\n```")

    # mark_agreed without contract_version
    bad_mark = {
        "decision": "contract_note",
        "body": "...",
        "contract_notes": [
            {
                "operation": "mark_agreed",
                "slug": "some-note",
                "resolution": "x",
            }
        ],
    }
    with pytest.raises(TweedleResponseParseError):
        parse_tweedle_response(f"```json\n{json.dumps(bad_mark)}\n```")


async def test_contract_note_decision_requires_action_list() -> None:
    """decision='contract_note' with empty contract_notes is rejected."""
    bad = {"decision": "contract_note", "body": "...", "contract_notes": []}
    with pytest.raises(TweedleResponseParseError):
        parse_tweedle_response(f"```json\n{json.dumps(bad)}\n```")


async def test_deliberate_drops_contract_notes_when_no_registry(tmp_path: Path) -> None:
    """When no registry is configured the artifact is dropped silently
    and the utterance still publishes (mirrors the implementation path)."""
    payload = {
        "decision": "contract_note",
        "body": "Proposing the envelope change",
        "contract_notes": [
            {
                "operation": "propose",
                "title": "Translation envelope",
                "current_shape": "envelope v2",
                "proposed_change": "add translation_status",
                "source": "story-003",
                "frontend_impact": "badge",
            }
        ],
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    dee = await _tweedledee(tmp_path, llm=llm, with_contract_notes=False)
    ctx = Context(constitution=dee.identity.constitution_text, triggers=(_u(),))

    utterance = await dee.deliberate(ctx)

    assert utterance is not None
    assert utterance.speech_act is SpeechAct.CONTRACT_NOTE
    assert utterance.content.artifacts == []


# ---------- tool-use loop ----------


def _mock_tool_use_llm(turns: list) -> LLMClient:
    """Mock LLM that returns a sequence of pre-canned responses.

    Each entry in ``turns`` is either:
    - A string (becomes a single text block with stop_reason='end_turn')
    - A dict with ``content`` (list of text/tool_use blocks) and
      ``stop_reason``

    The mock cycles through the list with each call to messages.create.
    """
    call_count = 0

    def _build_response(turn) -> SimpleNamespace:
        if isinstance(turn, str):
            content = [SimpleNamespace(type="text", text=turn)]
            stop_reason = "end_turn"
        else:
            content = []
            for block in turn["content"]:
                if block["type"] == "text":
                    content.append(SimpleNamespace(type="text", text=block["text"]))
                elif block["type"] == "tool_use":
                    content.append(
                        SimpleNamespace(
                            type="tool_use",
                            id=block["id"],
                            name=block["name"],
                            input=block["input"],
                        )
                    )
            stop_reason = turn.get("stop_reason", "tool_use")
        return SimpleNamespace(
            content=content,
            stop_reason=stop_reason,
            usage=SimpleNamespace(
                input_tokens=10,
                output_tokens=5,
                cache_creation_input_tokens=0,
                cache_read_input_tokens=0,
            ),
        )

    async def _create(**kwargs):
        nonlocal call_count
        if call_count >= len(turns):
            raise AssertionError(
                f"mock_tool_use_llm exhausted (configured {len(turns)} turns, "
                f"got {call_count + 1} calls)"
            )
        response = _build_response(turns[call_count])
        call_count += 1
        return response

    client = MagicMock()
    client.messages = MagicMock()
    client.messages.create = _create
    return LLMClient(client=client)


async def test_deliberate_with_tools_runs_tool_use_loop(tmp_path: Path) -> None:
    """When tools are wired, deliberate runs the tool-use loop:
    LLM emits tool_use → tools execute → results fed back → LLM emits
    final JSON response → response parsed normally."""
    from wonderland.tools import Tools

    final_payload = {
        "decision": "implementation",
        "body": "Shipped main.py based on what list_files revealed.",
        "implementations": [_frontend_impl_dict(files_touched=["main.py"])],
    }
    final_text = f"```json\n{json.dumps(final_payload)}\n```"

    llm = _mock_tool_use_llm(
        turns=[
            # Turn 1: LLM asks to list files
            {
                "content": [
                    {"type": "text", "text": "Let me see what's there."},
                    {
                        "type": "tool_use",
                        "id": "tool_1",
                        "name": "list_files",
                        "input": {"directory": "."},
                    },
                ],
                "stop_reason": "tool_use",
            },
            # Turn 2: LLM emits final JSON
            final_text,
        ]
    )

    tools = Tools(tmp_path)
    dee = await _tweedledee(tmp_path, llm=llm)
    dee._tools = tools  # inject; Runner does this via constructor wiring
    ctx = Context(constitution=dee.identity.constitution_text, triggers=(_u(),))

    utterance = await dee.deliberate(ctx)

    assert utterance is not None
    assert utterance.speech_act is SpeechAct.IMPLEMENTATION
    assert "Shipped main.py" in utterance.content.body


async def test_deliberate_with_tools_executes_write_file(tmp_path: Path) -> None:
    """tool_use(write_file) actually creates the file on disk."""
    from wonderland.tools import Tools

    final_payload = {
        "decision": "implementation",
        "body": "Wrote handler.py.",
        "implementations": [_frontend_impl_dict(files_touched=["handler.py"])],
    }
    final_text = f"```json\n{json.dumps(final_payload)}\n```"

    llm = _mock_tool_use_llm(
        turns=[
            {
                "content": [
                    {
                        "type": "tool_use",
                        "id": "t1",
                        "name": "write_file",
                        "input": {
                            "path": "src/handler.py",
                            "content": "def handle(): return 'ok'\n",
                        },
                    },
                ],
                "stop_reason": "tool_use",
            },
            final_text,
        ]
    )

    tools = Tools(tmp_path)
    dee = await _tweedledee(tmp_path, llm=llm)
    dee._tools = tools
    ctx = Context(constitution=dee.identity.constitution_text, triggers=(_u(),))

    await dee.deliberate(ctx)

    written = tmp_path / "src" / "handler.py"
    assert written.is_file()
    assert "def handle()" in written.read_text()


async def test_deliberate_with_tools_passes_tool_error_back_to_llm(tmp_path: Path) -> None:
    """When a tool raises ToolError, the loop returns is_error=True so
    the LLM can see the failure and recover."""
    from wonderland.tools import Tools

    final_payload = {
        "decision": "concern",
        "body": "Sandbox blocked my read attempt; defer this for now.",
    }
    final_text = f"```json\n{json.dumps(final_payload)}\n```"

    llm = _mock_tool_use_llm(
        turns=[
            {
                "content": [
                    {
                        "type": "tool_use",
                        "id": "t1",
                        "name": "read_file",
                        "input": {"path": "../escape.txt"},  # rejected
                    },
                ],
                "stop_reason": "tool_use",
            },
            final_text,
        ]
    )

    tools = Tools(tmp_path)
    dee = await _tweedledee(tmp_path, llm=llm)
    dee._tools = tools
    ctx = Context(constitution=dee.identity.constitution_text, triggers=(_u(),))

    utterance = await dee.deliberate(ctx)

    assert utterance is not None
    assert utterance.speech_act is SpeechAct.CONCERN
    assert "defer" in utterance.content.body.lower()


async def test_deliberate_without_tools_uses_single_shot_path(tmp_path: Path) -> None:
    """Backward compat: no tools wired → original single-shot completion
    path. (This is what every existing test relies on.)"""
    payload = {"decision": "silence"}
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    dee = await _tweedledee(tmp_path, llm=llm)
    assert dee._tools is None
    ctx = Context(constitution=dee.identity.constitution_text, triggers=(_u(),))

    utterance = await dee.deliberate(ctx)

    assert utterance is None  # silence


async def test_with_tools_protocol_includes_tools_section() -> None:
    """The tool-aware output protocol mentions the tool calls so the
    LLM knows it has them."""
    from wonderland.agents.tweedles import _OUTPUT_PROTOCOL_FRONTEND_WITH_TOOLS

    assert "Tools available" in _OUTPUT_PROTOCOL_FRONTEND_WITH_TOOLS
    assert "write_file" in _OUTPUT_PROTOCOL_FRONTEND_WITH_TOOLS
    assert "grep" in _OUTPUT_PROTOCOL_FRONTEND_WITH_TOOLS


async def test_no_tools_protocol_omits_tools_section() -> None:
    """The base output protocol stays clean when tools aren't wired."""
    from wonderland.agents.tweedles import _OUTPUT_PROTOCOL_FRONTEND

    assert "Tools available" not in _OUTPUT_PROTOCOL_FRONTEND


# ---------- existing implementation tests continue ----------


async def test_deliberate_drops_implementations_when_no_registry(tmp_path: Path) -> None:
    payload = {
        "decision": "implementation",
        "body": "...",
        "implementations": [_frontend_impl_dict()],
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    dee = await _tweedledee(tmp_path, llm=llm, with_registry=False)
    ctx = Context(constitution=dee.identity.constitution_text, triggers=(_u(),))

    utterance = await dee.deliberate(ctx)

    assert utterance is not None
    assert utterance.speech_act is SpeechAct.IMPLEMENTATION
    assert utterance.content.artifacts == []


async def test_dee_includes_protocol_with_frontend_guidance_in_system_prompt(
    tmp_path: Path,
) -> None:
    llm = _mock_llm('```json\n{"decision": "silence"}\n```')
    dee = await _tweedledee(tmp_path, llm=llm)
    ctx = Context(constitution="C", triggers=(_u(),))
    await dee.deliberate(ctx)

    create_kwargs = dee.llm.client.messages.create.call_args.kwargs
    system_blocks = create_kwargs["system"]
    # Position 0 is the framework primer (shared across all agents)
    assert "Wonderland — Framework Primer" in system_blocks[0]["text"]
    assert "cache_control" not in system_blocks[0]  # framework primer is plain string since context-compression Lever A (cache breakpoint reused for current_thread)
    # Position 1 is the per-agent constitution
    assert system_blocks[1]["text"] == "C"
    assert system_blocks[1]["cache_control"] == {"type": "ephemeral"}
    protocol = system_blocks[2]["text"]
    assert "fenced JSON block" in protocol
    assert "Contract is non-negotiable" in protocol
    assert "frontend Tweedle" in protocol
    assert "tweedledum" in protocol  # negotiates with the right sibling


async def test_dum_includes_protocol_with_backend_guidance_in_system_prompt(
    tmp_path: Path,
) -> None:
    llm = _mock_llm('```json\n{"decision": "silence"}\n```')
    dum = await _tweedledum(tmp_path, llm=llm)
    ctx = Context(constitution="C", triggers=(_u(),))
    await dum.deliberate(ctx)

    create_kwargs = dum.llm.client.messages.create.call_args.kwargs
    system_blocks = create_kwargs["system"]
    protocol = system_blocks[2]["text"]
    assert "backend Tweedle" in protocol
    assert "tweedledee" in protocol


# ---------- end-to-end (mocked LLM) ----------


async def test_end_to_end_dee_ticket_produces_implementation(tmp_path: Path) -> None:
    payload = {
        "decision": "implementation",
        "body": "Frontend impl shipped.",
        "implementations": [_frontend_impl_dict()],
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    dee = await _tweedledee(tmp_path, llm=llm)
    observer = dee.bus.subscribe(agent_name="observer")

    run_task = asyncio.create_task(dee.run())
    try:
        await dee.bus.publish(
            _u(
                act=SpeechAct.TICKET,
                speaker="white_rabbit",
                body="ticket-014: wire the message subscription",
            )
        )

        received = await asyncio.wait_for(anext(observer), timeout=2.0)
        while received.speaker.name != "tweedledee":
            received = await asyncio.wait_for(anext(observer), timeout=2.0)

        assert received.speech_act is SpeechAct.IMPLEMENTATION
        assert len(received.content.artifacts) == 1
        assert received.content.artifacts[0].payload["side"] == "frontend"

        impl_dir = tmp_path / ".wonderland" / "implementations"
        assert len(list(impl_dir.glob("implementation-*.md"))) == 1
    finally:
        await dee.stop()
        run_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await run_task
        await dee.memory.close()


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
async def test_live_dee_smoke(tmp_path: Path) -> None:
    """Real Haiku 4.5 round-trip: ticket in, in-character Tweedledee move out."""
    dee = await _tweedledee(tmp_path, llm=LLMClient())
    observer = dee.bus.subscribe(agent_name="observer")
    run_task = asyncio.create_task(dee.run())

    try:
        await dee.bus.publish(
            _u(
                act=SpeechAct.TICKET,
                speaker="white_rabbit",
                body=(
                    "ticket-014: Wire the translation message list to the new WebSocket "
                    "subscription. Contract: message-envelope v3 with translation_status "
                    "enum. UI states needed: loading, empty, error-recoverable (websocket "
                    "disconnect), stale (subscription >30s old). Estimate: 1 day. Owner: "
                    "tweedledee."
                ),
            )
        )

        received = await asyncio.wait_for(anext(observer), timeout=120.0)
        while received.speaker.name != "tweedledee":
            received = await asyncio.wait_for(anext(observer), timeout=120.0)

        assert received.speech_act in {
            SpeechAct.IMPLEMENTATION,
            SpeechAct.CONCERN,
            SpeechAct.QUESTION,
        }

        if received.speech_act is SpeechAct.IMPLEMENTATION:
            assert received.content.artifacts
            artifact = received.content.artifacts[0]
            assert artifact.payload["side"] == "frontend"
            # Contract is non-negotiable per the Pair Protocol §II
            assert artifact.payload["contract"]
        else:
            assert len(received.content.body) > 0
    finally:
        await dee.stop()
        run_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await run_task
        await dee.memory.close()


@smoke_required
async def test_live_dum_smoke(tmp_path: Path) -> None:
    """Real Haiku 4.5 round-trip: ticket in, in-character Tweedledum move out."""
    dum = await _tweedledum(tmp_path, llm=LLMClient())
    observer = dum.bus.subscribe(agent_name="observer")
    run_task = asyncio.create_task(dum.run())

    try:
        await dum.bus.publish(
            _u(
                act=SpeechAct.TICKET,
                speaker="white_rabbit",
                body=(
                    "ticket-015: Implement the translation worker pipeline. Contract: "
                    "message-envelope v3 with translation_status enum + source_lang FK. "
                    "Persist jobs durably; emit message-translated on completion or "
                    "message-translation-failed on dead-letter. Invariants: every "
                    "translated message has exactly one source_lang. Estimate: 2 days. "
                    "Owner: tweedledum."
                ),
            )
        )

        received = await asyncio.wait_for(anext(observer), timeout=120.0)
        while received.speaker.name != "tweedledum":
            received = await asyncio.wait_for(anext(observer), timeout=120.0)

        assert received.speech_act in {
            SpeechAct.IMPLEMENTATION,
            SpeechAct.CONCERN,
            SpeechAct.QUESTION,
        }

        if received.speech_act is SpeechAct.IMPLEMENTATION:
            assert received.content.artifacts
            artifact = received.content.artifacts[0]
            assert artifact.payload["side"] == "backend"
            assert artifact.payload["contract"]
        else:
            assert len(received.content.body) > 0
    finally:
        await dum.stop()
        run_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await run_task
        await dum.memory.close()
