"""Tests for the Dodo's compose-conflict-resolution path."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from wonderland import (
    AgentMemory,
    Conflict,
    ConflictDomain,
    ConflictResponse,
    ConflictResponseParseError,
    Dodo,
    InMemoryCaucus,
    LLMClient,
    Resolution,
    SpeechAct,
    parse_conflict_response,
)

# ---------- helpers ----------


def _conflict() -> Conflict:
    return Conflict(
        thread_id="t",
        proposals=("01JCAT", "01JRABBIT"),
        proposal_bodies=(
            ("cheshire_cat", "Queue translations and process them async."),
            ("white_rabbit", "Async slips Thursday's demo. Synchronous must ship v1."),
        ),
        domain_hint=ConflictDomain.SEQUENCE,
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


async def _dodo(tmp_path: Path, *, llm: LLMClient | None = None) -> Dodo:
    bus = InMemoryCaucus()
    memory = AgentMemory.for_project(tmp_path, "dodo")
    await memory.open()
    return Dodo(memory=memory, bus=bus, llm=llm)


# ---------- parse_conflict_response ----------


def test_parse_composed_response() -> None:
    text = """```json
{
  "composed": true,
  "composition": "Queue with a 1-day budget — Rabbit ships v1, Cat's async layer comes fast-follow.",
  "rationale": "the proposals address different axes (mechanism vs. timeline)"
}
```"""
    response = parse_conflict_response(text)
    assert response.composed is True
    assert "Queue with a 1-day budget" in response.composition
    assert "different axes" in response.rationale


def test_parse_non_composed_response() -> None:
    text = """```json
{
  "composed": false,
  "suggested_domain": "architecture",
  "rationale": "the disagreement is about whether to add an async layer at all",
  "dissents": [
    {"speaker": "cheshire_cat", "position": "queue is needed", "rationale": "translation latency varies"},
    {"speaker": "white_rabbit", "position": "synchronous fits Thursday", "rationale": "demo window is fixed"}
  ]
}
```"""
    response = parse_conflict_response(text)
    assert response.composed is False
    assert response.suggested_domain == "architecture"
    assert len(response.dissents) == 2


def test_parse_unfenced_json() -> None:
    response = parse_conflict_response('{"composed": true, "composition": "..."}')
    assert response.composed is True


def test_parse_conflict_coerces_explicit_nulls() -> None:
    """Live Haiku 4.5 sometimes emits nulls instead of omitting optional fields."""
    response = parse_conflict_response(
        '{"composed": true, "composition": "merged", "rationale": null, "dissents": null}'
    )
    assert response.composed is True
    assert response.composition == "merged"
    assert response.rationale == ""
    assert response.dissents == []


def test_parse_rejects_missing_json() -> None:
    with pytest.raises(ConflictResponseParseError):
        parse_conflict_response("just plain text")


def test_parse_rejects_invalid_decision_shape() -> None:
    with pytest.raises(ConflictResponseParseError):
        parse_conflict_response('{"composed": "maybe"}')


# ---------- compose_conflict_resolution: with mocked LLM ----------


async def test_compose_returns_composed_resolution(tmp_path: Path) -> None:
    payload = {
        "composed": True,
        "composition": "Queue with a 1-day budget; Rabbit ships v1, Cat's async lands fast-follow.",
        "rationale": "the proposals address different axes",
        "dissents": [],
    }
    dodo = await _dodo(tmp_path, llm=_mock_llm(f"```json\n{json.dumps(payload)}\n```"))

    resolution = await dodo.compose_conflict_resolution(_conflict())

    assert resolution.composed is True
    assert "Queue with a 1-day budget" in resolution.composition_text
    assert resolution.is_composition is True
    assert resolution.needs_escalation is False


async def test_compose_returns_non_composed_resolution(tmp_path: Path) -> None:
    payload = {
        "composed": False,
        "suggested_domain": "architecture",
        "rationale": "fundamental disagreement on layer count",
        "dissents": [
            {"speaker": "cheshire_cat", "position": "queue needed", "rationale": "..."},
            {"speaker": "white_rabbit", "position": "sync wins", "rationale": "..."},
        ],
    }
    dodo = await _dodo(tmp_path, llm=_mock_llm(f"```json\n{json.dumps(payload)}\n```"))

    resolution = await dodo.compose_conflict_resolution(_conflict())

    assert resolution.composed is False
    assert resolution.suggested_domain is ConflictDomain.ARCHITECTURE
    assert resolution.suggested_owner == "cheshire_cat"
    assert resolution.needs_escalation is True
    assert len(resolution.dissents) == 2


async def test_compose_falls_back_to_caller_hint_when_llm_picks_unknown_domain(
    tmp_path: Path,
) -> None:
    """If the LLM hallucinates a domain, fall back to the caller's hint."""
    payload = {
        "composed": False,
        "suggested_domain": "vibe",  # not a real ConflictDomain
        "rationale": "no",
    }
    dodo = await _dodo(tmp_path, llm=_mock_llm(f"```json\n{json.dumps(payload)}\n```"))

    resolution = await dodo.compose_conflict_resolution(_conflict())

    # Caller's hint was ConflictDomain.SEQUENCE → owner is white_rabbit
    assert resolution.suggested_domain is ConflictDomain.SEQUENCE
    assert resolution.suggested_owner == "white_rabbit"


async def test_compose_handles_missing_domain_and_no_hint(tmp_path: Path) -> None:
    """Non-composed with no LLM domain and no caller hint → no suggested owner."""
    payload = {"composed": False, "rationale": "unclear"}
    dodo = await _dodo(tmp_path, llm=_mock_llm(f"```json\n{json.dumps(payload)}\n```"))
    conflict_no_hint = Conflict(
        thread_id="t",
        proposals=("01J0", "01J1"),
        proposal_bodies=(("a", "x"), ("b", "y")),
        domain_hint=None,
    )

    resolution = await dodo.compose_conflict_resolution(conflict_no_hint)

    assert resolution.composed is False
    assert resolution.suggested_domain is None
    assert resolution.suggested_owner is None


async def test_compose_with_no_llm_returns_fallback(tmp_path: Path) -> None:
    """Without an LLM, return a non-composing Resolution carrying the
    caller's domain hint — the escalation flow takes over from there."""
    dodo = await _dodo(tmp_path, llm=None)

    resolution = await dodo.compose_conflict_resolution(_conflict())

    assert resolution.composed is False
    assert resolution.needs_escalation is True
    assert resolution.suggested_domain is ConflictDomain.SEQUENCE
    assert resolution.suggested_owner == "white_rabbit"


# ---------- publish_composition ----------


async def test_publish_composition_publishes_composition_utterance(tmp_path: Path) -> None:
    dodo = await _dodo(tmp_path)
    observer = dodo.bus.subscribe(agent_name="observer")

    resolution = Resolution(
        thread_id="t",
        composed=True,
        composition_text="Queue with budget; Rabbit ships v1.",
        rationale="composes",
    )
    utterance = await dodo.publish_composition(resolution)

    assert utterance.speech_act is SpeechAct.COMPOSITION
    assert utterance.speaker.name == "dodo"
    assert "Queue with budget" in utterance.content.body

    received = await anext(observer)
    assert received.id == utterance.id


async def test_publish_composition_attaches_resolution_artifact(tmp_path: Path) -> None:
    from wonderland import Dissent

    dodo = await _dodo(tmp_path)
    resolution = Resolution(
        thread_id="t",
        composed=True,
        composition_text="...",
        dissents=(Dissent(speaker="white_rabbit", position="slips Thursday"),),
    )
    utterance = await dodo.publish_composition(resolution)

    assert len(utterance.content.artifacts) == 1
    artifact = utterance.content.artifacts[0]
    assert artifact.kind == "resolution"
    assert artifact.payload["composed"] is True
    assert len(artifact.payload["dissents"]) == 1
    assert artifact.payload["dissents"][0]["speaker"] == "white_rabbit"


async def test_publish_composition_records_in_memory(tmp_path: Path) -> None:
    dodo = await _dodo(tmp_path)
    resolution = Resolution(thread_id="t", composed=True, composition_text="...")
    await dodo.publish_composition(resolution)
    history = await dodo.memory.query_by_thread("t")
    assert any(u.speech_act is SpeechAct.COMPOSITION for u in history)


async def test_publish_composition_rejects_non_composing_resolution(tmp_path: Path) -> None:
    """Composing a non-composition is the §VIII failure mode this method exists
    to enforce against."""
    dodo = await _dodo(tmp_path)
    resolution = Resolution(
        thread_id="t",
        composed=False,
        suggested_domain=ConflictDomain.ARCHITECTURE,
    )
    with pytest.raises(ValueError, match="composed Resolution"):
        await dodo.publish_composition(resolution)


# ---------- ConflictResponse model ----------


def test_response_default_dissents_empty() -> None:
    response = ConflictResponse(composed=True, composition="...")
    assert response.dissents == []
