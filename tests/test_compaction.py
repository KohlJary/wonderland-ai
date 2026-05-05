"""Tests for compaction-as-agent-behavior — agent reflects between threads."""

from __future__ import annotations

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
    CheshireCat,
    CompactionContext,
    CompactionResponse,
    CompactionResponseParseError,
    CompactionResult,
    InMemoryCaucus,
    LLMClient,
    SpeechAct,
    Utterance,
    UtteranceContent,
    WonderlandAgent,
    parse_compaction_response,
)
from wonderland.identity import ConstitutionHeader, Identity

# ---------- helpers ----------


def _make_identity(name: str = "cheshire_cat") -> Identity:
    return Identity(
        name=name,
        header=ConstitutionHeader(
            display_name=name,
            role="r",
            lineage="Wonderland v0.1",
            version="0.1",
            license="L",
        ),
        constitution_text=f"You are {name}.",
        interests=frozenset(SpeechAct),
    )


def _u(
    *,
    thread_id: str = "t",
    speaker: str = "white_rabbit",
    act: SpeechAct = SpeechAct.PROPOSAL,
    body: str = "...",
) -> Utterance:
    return Utterance(
        thread_id=thread_id,
        speaker=AgentIdentity(name=speaker, constitution_version="0.1"),
        addressed_to="caucus",
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


async def _agent(
    tmp_path: Path,
    *,
    llm: LLMClient | None = None,
    name: str = "cheshire_cat",
) -> WonderlandAgent:
    bus = InMemoryCaucus()
    memory = AgentMemory.for_project(tmp_path, name)
    await memory.open()
    return WonderlandAgent(
        identity=_make_identity(name),
        memory=memory,
        bus=bus,
        llm=llm,
    )


# ---------- CompactionResponse + parser ----------


def test_response_defaults_to_empty_dicts() -> None:
    response = CompactionResponse()
    assert response.semantic_updates == {}
    assert response.relational_updates == {}


def test_parse_fenced_json() -> None:
    text = """```json
{
  "semantic_updates": {"architecture": "Use Redis Streams."},
  "relational_updates": {"white_rabbit": "asks for estimates I shouldn't give"}
}
```"""
    response = parse_compaction_response(text)
    assert response.semantic_updates == {"architecture": "Use Redis Streams."}
    assert response.relational_updates == {"white_rabbit": "asks for estimates I shouldn't give"}


def test_parse_unfenced_json() -> None:
    response = parse_compaction_response('{"semantic_updates": {"x": "y"}}')
    assert response.semantic_updates == {"x": "y"}


def test_parse_empty_json_is_valid() -> None:
    """An empty compaction is correct and honest."""
    response = parse_compaction_response("{}")
    assert response.semantic_updates == {}
    assert response.relational_updates == {}


def test_parse_rejects_missing_json() -> None:
    with pytest.raises(CompactionResponseParseError):
        parse_compaction_response("just plain text, no json")


def test_parse_rejects_invalid_json() -> None:
    with pytest.raises(CompactionResponseParseError):
        parse_compaction_response("```json\n{not valid}\n```")


# ---------- CompactionResult ----------


def test_result_is_empty_when_no_updates() -> None:
    assert CompactionResult().is_empty
    assert CompactionResult(thread_id="t").is_empty


def test_result_not_empty_when_semantic_updated() -> None:
    assert not CompactionResult(semantic_topics_updated=("architecture",)).is_empty


def test_result_not_empty_when_relational_updated() -> None:
    assert not CompactionResult(relational_agents_updated=("white_rabbit",)).is_empty


# ---------- compose_compaction_context ----------


async def test_compose_compaction_context_builds_transcript_and_relational(
    tmp_path: Path,
) -> None:
    agent = await _agent(tmp_path)
    agent.memory.relational.write("white_rabbit", "tries to push me on estimates")
    agent.memory.semantic.write("architecture", "Use Redis Streams.")

    await agent.memory.record(_u(thread_id="t", body="rabbit said this"))

    context = await agent.compose_compaction_context("t")
    assert "rabbit said this" in context.transcript
    assert "tries to push me on estimates" in context.existing_relational
    assert "Use Redis Streams" in context.existing_semantic
    assert agent.identity.constitution_text in context.constitution


async def test_compose_compaction_context_excludes_self_from_relational(
    tmp_path: Path,
) -> None:
    agent = await _agent(tmp_path)
    agent.memory.relational.write(agent.identity.name, "shouldn't show up")
    await agent.memory.record(_u(speaker=agent.identity.name, body="my own utterance"))

    context = await agent.compose_compaction_context("t")
    assert "shouldn't show up" not in context.existing_relational


async def test_compose_compaction_context_empty_when_no_thread(tmp_path: Path) -> None:
    agent = await _agent(tmp_path)
    context = await agent.compose_compaction_context("nonexistent")
    assert context.transcript == ""


# ---------- CompactionContext.to_llm_request ----------


def test_to_llm_request_caches_constitution_and_protocol() -> None:
    context = CompactionContext(
        constitution="You are X.",
        protocol="Reflect.",
        transcript="things happened",
    )
    system, _ = context.to_llm_request()
    assert system[0].text == "You are X."
    assert system[1].text == "Reflect."


def test_to_llm_request_appends_existing_memory_blocks() -> None:
    context = CompactionContext(
        constitution="C",
        protocol="P",
        existing_semantic="sem",
        existing_relational="rel",
        transcript="t",
    )
    system, _ = context.to_llm_request()
    assert len(system) == 4  # constitution, protocol, semantic, relational


def test_to_llm_request_skips_empty_memory_blocks() -> None:
    context = CompactionContext(constitution="C", protocol="P", transcript="t")
    system, _ = context.to_llm_request()
    assert len(system) == 2


def test_to_llm_request_transcript_in_user_message() -> None:
    context = CompactionContext(constitution="C", protocol="P", transcript="thread happened")
    _, messages = context.to_llm_request()
    assert "thread happened" in messages[0]["content"]


# ---------- compact() ----------


async def test_compact_with_no_llm_returns_empty_result(tmp_path: Path) -> None:
    agent = await _agent(tmp_path, llm=None)
    await agent.memory.record(_u(thread_id="t"))
    result = await agent.compact("t")
    assert result.is_empty
    assert result.thread_id == "t"


async def test_compact_with_no_thread_history_returns_empty_result(tmp_path: Path) -> None:
    agent = await _agent(tmp_path, llm=_mock_llm("{}"))
    result = await agent.compact("nonexistent")
    assert result.is_empty
    # LLM was not called — short-circuit before composing prompt
    create_calls = agent.llm.client.messages.create.call_count
    assert create_calls == 0


async def test_compact_writes_semantic_updates(tmp_path: Path) -> None:
    payload = {
        "semantic_updates": {
            "architecture": "Use Redis Streams. ADR-001.",
            "conventions": "ADR Tradeoffs section is non-optional.",
        }
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    agent = await _agent(tmp_path, llm=llm)
    await agent.memory.record(_u(thread_id="t", body="..."))

    result = await agent.compact("t")

    assert sorted(result.semantic_topics_updated) == ["architecture", "conventions"]
    assert "Use Redis Streams" in agent.memory.semantic.read("architecture")
    assert "Tradeoffs" in agent.memory.semantic.read("conventions")


async def test_compact_writes_relational_updates(tmp_path: Path) -> None:
    payload = {
        "relational_updates": {
            "white_rabbit": "Asks me for estimates; gentle redirect each time.",
        }
    }
    llm = _mock_llm(f"```json\n{json.dumps(payload)}\n```")
    agent = await _agent(tmp_path, llm=llm)
    await agent.memory.record(_u(thread_id="t"))

    result = await agent.compact("t")

    assert result.relational_agents_updated == ("white_rabbit",)
    assert "estimates" in agent.memory.relational.read("white_rabbit")


async def test_compact_replace_in_full(tmp_path: Path) -> None:
    """Each update replaces the file in full; the agent must include
    everything it wants to keep, not just deltas."""
    agent_first = await _agent(
        tmp_path, llm=_mock_llm('```json\n{"semantic_updates": {"x": "first version"}}\n```')
    )
    await agent_first.memory.record(_u(thread_id="t1"))
    await agent_first.compact("t1")
    assert agent_first.memory.semantic.read("x") == "first version"

    # Second compaction returns just "second version" — replaces, doesn't append
    agent_second_llm = _mock_llm('```json\n{"semantic_updates": {"x": "second version"}}\n```')
    agent_first.llm = agent_second_llm
    await agent_first.memory.record(_u(thread_id="t2"))
    await agent_first.compact("t2")
    assert agent_first.memory.semantic.read("x") == "second version"


async def test_compact_empty_response_is_valid(tmp_path: Path) -> None:
    """An empty compaction is correct and honest."""
    agent = await _agent(tmp_path, llm=_mock_llm("{}"))
    await agent.memory.record(_u(thread_id="t"))
    result = await agent.compact("t")
    assert result.is_empty
    assert result.thread_id == "t"


async def test_compact_uses_class_protocol(tmp_path: Path) -> None:
    """Subclass-overridden COMPACTION_PROTOCOL flows into the prompt."""

    class HatterStyle(WonderlandAgent):
        COMPACTION_PROTOCOL = "Reflect nonlinearly. Make associative leaps."

    bus = InMemoryCaucus()
    memory = AgentMemory.for_project(tmp_path, "mad_hatter")
    await memory.open()
    llm = _mock_llm("{}")
    agent = HatterStyle(identity=_make_identity("mad_hatter"), memory=memory, bus=bus, llm=llm)
    await agent.memory.record(_u(thread_id="t"))

    await agent.compact("t")

    create_kwargs = agent.llm.client.messages.create.call_args.kwargs
    system_blocks = create_kwargs["system"]
    # Constitution at index 0, custom protocol at index 1
    assert "associative leaps" in system_blocks[1]["text"]


async def test_compact_includes_existing_semantic_in_prompt(tmp_path: Path) -> None:
    """Existing semantic memory is shown to the LLM so it can update-in-full."""
    agent = await _agent(tmp_path, llm=_mock_llm("{}"))
    agent.memory.semantic.write("architecture", "Use Redis Streams.")
    await agent.memory.record(_u(thread_id="t"))

    await agent.compact("t")

    create_kwargs = agent.llm.client.messages.create.call_args.kwargs
    system_blocks = create_kwargs["system"]
    semantic_block = next((b for b in system_blocks if "Use Redis Streams" in b["text"]), None)
    assert semantic_block is not None


# ---------- with the Cheshire Cat subclass ----------


async def test_cat_inherits_default_compaction_protocol(tmp_path: Path) -> None:
    bus = InMemoryCaucus()
    memory = AgentMemory.for_project(tmp_path, "cheshire_cat")
    await memory.open()
    cat = CheshireCat(memory=memory, bus=bus, llm=_mock_llm("{}"))
    await cat.memory.record(_u(thread_id="t"))

    result = await cat.compact("t")
    assert result.is_empty  # no updates from the mocked empty LLM


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
async def test_live_cat_compacts_a_thread(tmp_path: Path) -> None:
    """Real Haiku 4.5 reflection: Cat reads a small thread and produces updates."""
    bus = InMemoryCaucus()
    memory = AgentMemory.for_project(tmp_path, "cheshire_cat")
    await memory.open()
    cat = CheshireCat(memory=memory, bus=bus, llm=LLMClient())

    rabbit = AgentIdentity(name="white_rabbit", constitution_version="0.1")
    dodo = AgentIdentity(name="dodo", constitution_version="0.2")

    # A small thread to reflect on
    await memory.record(
        Utterance(
            thread_id="t",
            speaker=dodo,
            addressed_to="caucus",
            speech_act=SpeechAct.DIRECTIVE,
            content=UtteranceContent(
                body="Build a translation chat. Synchronous-first, falls back on translation errors."
            ),
        )
    )
    await memory.record(
        Utterance(
            thread_id="t",
            speaker=rabbit,
            addressed_to="caucus",
            speech_act=SpeechAct.QUESTION,
            content=UtteranceContent(
                body="Cat, by when can we expect the architectural call so I can ticket?"
            ),
        )
    )

    result = await cat.compact("t")

    # The Cat should produce at least one update — either a semantic note
    # about synchronous-first architecture, or a relational note about the
    # Rabbit asking for estimates. An empty result would also be honest
    # ("nothing changed for me here"), so don't assert strict non-emptiness.
    # Do assert the call completed without raising.
    assert result.thread_id == "t"

    with contextlib.suppress(Exception):
        await memory.close()
