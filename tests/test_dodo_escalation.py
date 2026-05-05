"""Tests for Dodo.escalate — the human-in-the-loop handoff."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from wonderland import (
    AgentMemory,
    BriefProseResponse,
    BriefResponseParseError,
    Conflict,
    ConflictDomain,
    Dodo,
    EscalationBrief,
    EscalationRecord,
    EscalationRegistry,
    InMemoryCaucus,
    LLMClient,
    Resolution,
    SpeechAct,
    parse_brief_response,
)

# ---------- helpers ----------


def _conflict() -> Conflict:
    return Conflict(
        thread_id="demo-thread",
        proposals=("01JCAT", "01JRABBIT"),
        proposal_bodies=(
            ("cheshire_cat", "Async layer with explicit fallback."),
            ("white_rabbit", "Synchronous v1; ship Thursday."),
        ),
        domain_hint=ConflictDomain.ARCHITECTURE,
    )


def _non_composing_resolution() -> Resolution:
    return Resolution(
        thread_id="demo-thread",
        composed=False,
        suggested_domain=ConflictDomain.ARCHITECTURE,
        suggested_owner="cheshire_cat",
        rationale="the proposals contradict on the synchronous-vs-async axis",
    )


def _composing_resolution() -> Resolution:
    return Resolution(
        thread_id="t",
        composed=True,
        composition_text="...",
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


async def _dodo(
    tmp_path: Path,
    *,
    llm: LLMClient | None = None,
    with_registry: bool = True,
) -> Dodo:
    bus = InMemoryCaucus()
    memory = AgentMemory.for_project(tmp_path, "dodo")
    await memory.open()
    registry = EscalationRegistry(tmp_path) if with_registry else None
    return Dodo(memory=memory, bus=bus, llm=llm, escalation_registry=registry)


# ---------- parse_brief_response ----------


def test_parse_fenced_brief_response() -> None:
    text = """```json
{
  "decision_required": "Should we ship synchronous v1 by Thursday at the cost of an async rework later?",
  "stakes": "Sync ships 2 days faster; rework adds a week.",
  "background": "Translation chat directive; Alice blocked."
}
```"""
    response = parse_brief_response(text)
    assert "Thursday" in response.decision_required
    assert "Sync ships" in response.stakes


def test_parse_unfenced_brief_response() -> None:
    response = parse_brief_response('{"decision_required": "X?"}')
    assert response.decision_required == "X?"


def test_parse_brief_coerces_explicit_nulls() -> None:
    """Live Haiku 4.5 sometimes emits nulls for omitted optional prose fields."""
    response = parse_brief_response(
        '{"decision_required": "Pick A or B?", "stakes": null, "background": null}'
    )
    assert response.decision_required == "Pick A or B?"
    assert response.stakes == ""
    assert response.background == ""


def test_parse_rejects_missing_decision() -> None:
    with pytest.raises(BriefResponseParseError):
        parse_brief_response('{"stakes": "x"}')


def test_parse_rejects_missing_json() -> None:
    with pytest.raises(BriefResponseParseError):
        parse_brief_response("just text")


# ---------- escalate: guards ----------


async def test_escalate_rejects_composing_resolution(tmp_path: Path) -> None:
    """Symmetric with publish_composition's non-composing guard."""
    dodo = await _dodo(tmp_path)
    with pytest.raises(ValueError, match="non-composing"):
        await dodo.escalate(
            conflict=_conflict(),
            resolution=_composing_resolution(),
        )


async def test_escalate_requires_registry(tmp_path: Path) -> None:
    """Without a registry the brief would be lost — fail loudly."""
    dodo = await _dodo(tmp_path, with_registry=False)
    with pytest.raises(RuntimeError, match="escalation_registry"):
        await dodo.escalate(
            conflict=_conflict(),
            resolution=_non_composing_resolution(),
        )


# ---------- escalate: fallback (no LLM) ----------


async def test_escalate_with_no_llm_uses_fallback(tmp_path: Path) -> None:
    dodo = await _dodo(tmp_path, llm=None)
    record = await dodo.escalate(
        conflict=_conflict(),
        resolution=_non_composing_resolution(),
        thread_summary="Translation chat thread; both agents weighed in.",
    )

    assert record.number == 1
    assert record.path.is_file()
    contents = record.read()
    assert "demo-thread" in contents
    assert "cheshire_cat" in contents
    assert "white_rabbit" in contents
    assert "Translation chat thread" in contents


# ---------- escalate: with mocked LLM ----------


async def test_escalate_with_llm_uses_drafted_prose(tmp_path: Path) -> None:
    payload = {
        "decision_required": "Ship synchronous v1 Thursday and accept async rework, or delay?",
        "stakes": "Demo window vs technical debt.",
        "background": "Translation chat directive; thread reached architectural impasse.",
    }
    dodo = await _dodo(tmp_path, llm=_mock_llm(f"```json\n{json.dumps(payload)}\n```"))

    record = await dodo.escalate(
        conflict=_conflict(),
        resolution=_non_composing_resolution(),
        thread_summary="Both agents proposed; no composition.",
    )

    contents = record.read()
    assert "Ship synchronous v1 Thursday" in contents
    assert "Demo window vs technical debt." in contents
    assert "Translation chat directive" in contents


async def test_escalate_publishes_escalation_utterance(tmp_path: Path) -> None:
    payload = {
        "decision_required": "Ship sync or delay?",
        "stakes": "...",
        "background": "...",
    }
    dodo = await _dodo(tmp_path, llm=_mock_llm(f"```json\n{json.dumps(payload)}\n```"))
    observer = dodo.bus.subscribe(agent_name="observer")

    record = await dodo.escalate(
        conflict=_conflict(),
        resolution=_non_composing_resolution(),
    )

    received = await anext(observer)
    assert received.speech_act is SpeechAct.ESCALATION
    assert received.speaker.name == "dodo"
    assert "Ship sync or delay?" in received.content.body
    assert len(received.content.artifacts) == 1
    artifact = received.content.artifacts[0]
    assert artifact.kind == "escalation"
    assert artifact.payload["number"] == record.number
    assert artifact.payload["suggested_owner"] == "cheshire_cat"


async def test_escalate_records_in_memory(tmp_path: Path) -> None:
    payload = {"decision_required": "?", "stakes": "...", "background": "..."}
    dodo = await _dodo(tmp_path, llm=_mock_llm(f"```json\n{json.dumps(payload)}\n```"))
    await dodo.escalate(
        conflict=_conflict(),
        resolution=_non_composing_resolution(),
    )
    history = await dodo.memory.query_by_thread("demo-thread")
    assert any(u.speech_act is SpeechAct.ESCALATION for u in history)


# ---------- escalate: channel emission ----------


async def test_escalate_invokes_sync_channel(tmp_path: Path) -> None:
    payload = {"decision_required": "?", "stakes": "...", "background": "..."}
    dodo = await _dodo(tmp_path, llm=_mock_llm(f"```json\n{json.dumps(payload)}\n```"))

    invocations: list[tuple[EscalationBrief, EscalationRecord]] = []

    def channel(brief: EscalationBrief, record: EscalationRecord) -> None:
        invocations.append((brief, record))

    record = await dodo.escalate(
        conflict=_conflict(),
        resolution=_non_composing_resolution(),
        channel=channel,
    )

    assert len(invocations) == 1
    brief, called_record = invocations[0]
    assert called_record.number == record.number
    assert isinstance(brief, EscalationBrief)


async def test_escalate_awaits_async_channel(tmp_path: Path) -> None:
    payload = {"decision_required": "?", "stakes": "...", "background": "..."}
    dodo = await _dodo(tmp_path, llm=_mock_llm(f"```json\n{json.dumps(payload)}\n```"))

    invocations: list[str] = []

    async def channel(brief: EscalationBrief, record: EscalationRecord) -> None:
        invocations.append(record.slug)

    await dodo.escalate(
        conflict=_conflict(),
        resolution=_non_composing_resolution(),
        channel=channel,
    )

    assert invocations == ["demo-thread"]


async def test_escalate_default_channel_is_stderr(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = {"decision_required": "Decide X?", "stakes": "...", "background": "..."}
    dodo = await _dodo(tmp_path, llm=_mock_llm(f"```json\n{json.dumps(payload)}\n```"))

    await dodo.escalate(
        conflict=_conflict(),
        resolution=_non_composing_resolution(),
    )

    captured = capsys.readouterr()
    assert "ESCALATION" in captured.err
    assert "Decide X?" in captured.err


# ---------- defaulting suggested_resolution ----------


async def test_brief_suggested_resolution_picks_primary_domain_proposal(
    tmp_path: Path,
) -> None:
    """When suggested_owner matches one of the proposers, the Brief leans
    toward that agent's position."""
    payload = {"decision_required": "?", "stakes": "...", "background": "..."}
    dodo = await _dodo(tmp_path, llm=_mock_llm(f"```json\n{json.dumps(payload)}\n```"))
    record = await dodo.escalate(
        conflict=_conflict(),
        resolution=_non_composing_resolution(),
    )
    contents = record.read()
    assert "Lean toward cheshire_cat" in contents
    assert "Async layer" in contents


# ---------- BriefProseResponse model ----------


def test_brief_prose_response_defaults() -> None:
    response = BriefProseResponse(decision_required="?")
    assert response.stakes == ""
    assert response.background == ""
