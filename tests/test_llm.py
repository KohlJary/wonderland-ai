"""Tests for the Anthropic LLM wrapper."""

from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from wonderland import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    CachedBlock,
    LLMClient,
    TokenUsage,
)

# ---------- helpers ----------


def _mock_response(
    text: str = "hi",
    *,
    input_tokens: int = 10,
    output_tokens: int = 5,
    cache_creation: int = 0,
    cache_read: int = 0,
    stop_reason: str = "end_turn",
) -> SimpleNamespace:
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=text)],
        stop_reason=stop_reason,
        usage=SimpleNamespace(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_creation_input_tokens=cache_creation,
            cache_read_input_tokens=cache_read,
        ),
    )


def _mock_anthropic_client(response: SimpleNamespace | None = None) -> MagicMock:
    client = MagicMock()
    client.messages = MagicMock()
    client.messages.create = AsyncMock(return_value=response or _mock_response())
    return client


# ---------- defaults ----------


async def test_default_model_is_haiku_4_5() -> None:
    mock = _mock_anthropic_client()
    llm = LLMClient(client=mock)
    assert llm.model == DEFAULT_MODEL
    assert DEFAULT_MODEL == "claude-haiku-4-5-20251001"

    await llm.complete(system=["x"], messages=[{"role": "user", "content": "hi"}])
    kwargs = mock.messages.create.call_args.kwargs
    assert kwargs["model"] == "claude-haiku-4-5-20251001"


async def test_model_override() -> None:
    mock = _mock_anthropic_client()
    llm = LLMClient(client=mock, model="claude-sonnet-4-6")
    await llm.complete(system=["x"], messages=[{"role": "user", "content": "hi"}])
    assert mock.messages.create.call_args.kwargs["model"] == "claude-sonnet-4-6"


async def test_default_max_tokens() -> None:
    mock = _mock_anthropic_client()
    llm = LLMClient(client=mock)
    await llm.complete(system=["x"], messages=[{"role": "user", "content": "hi"}])
    assert mock.messages.create.call_args.kwargs["max_tokens"] == DEFAULT_MAX_TOKENS


async def test_max_tokens_override() -> None:
    mock = _mock_anthropic_client()
    llm = LLMClient(client=mock)
    await llm.complete(
        system=["x"],
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=500,
    )
    assert mock.messages.create.call_args.kwargs["max_tokens"] == 500


# ---------- cache breakpoints ----------


async def test_cached_block_gets_cache_control_marker() -> None:
    mock = _mock_anthropic_client()
    llm = LLMClient(client=mock)
    await llm.complete(
        system=[CachedBlock("constitution"), "trigger"],
        messages=[{"role": "user", "content": "hi"}],
    )
    system_blocks = mock.messages.create.call_args.kwargs["system"]
    assert system_blocks == [
        {
            "type": "text",
            "text": "constitution",
            "cache_control": {"type": "ephemeral"},
        },
        {"type": "text", "text": "trigger"},
    ]


async def test_multiple_cache_breakpoints() -> None:
    """Constitution + relationships both become cached prefixes."""
    mock = _mock_anthropic_client()
    llm = LLMClient(client=mock)
    await llm.complete(
        system=[
            CachedBlock("constitution"),
            CachedBlock("relationships"),
            "current thread",
        ],
        messages=[{"role": "user", "content": "trigger"}],
    )
    system_blocks = mock.messages.create.call_args.kwargs["system"]
    assert len(system_blocks) == 3
    assert system_blocks[0]["cache_control"] == {"type": "ephemeral"}
    assert system_blocks[1]["cache_control"] == {"type": "ephemeral"}
    assert "cache_control" not in system_blocks[2]


async def test_plain_string_system_has_no_cache_marker() -> None:
    mock = _mock_anthropic_client()
    llm = LLMClient(client=mock)
    await llm.complete(
        system=["just a plain prompt"],
        messages=[{"role": "user", "content": "hi"}],
    )
    system_blocks = mock.messages.create.call_args.kwargs["system"]
    assert system_blocks == [{"type": "text", "text": "just a plain prompt"}]


# ---------- result extraction ----------


async def test_complete_returns_extracted_text() -> None:
    mock = _mock_anthropic_client(_mock_response(text="extracted body"))
    llm = LLMClient(client=mock)
    result = await llm.complete(
        system=["x"],
        messages=[{"role": "user", "content": "hi"}],
    )
    assert result.text == "extracted body"


async def test_complete_concatenates_multiple_text_blocks() -> None:
    response = SimpleNamespace(
        content=[
            SimpleNamespace(type="text", text="part 1 "),
            SimpleNamespace(type="text", text="part 2"),
        ],
        stop_reason="end_turn",
        usage=SimpleNamespace(
            input_tokens=0,
            output_tokens=0,
            cache_creation_input_tokens=0,
            cache_read_input_tokens=0,
        ),
    )
    llm = LLMClient(client=_mock_anthropic_client(response))
    result = await llm.complete(
        system=["x"],
        messages=[{"role": "user", "content": "hi"}],
    )
    assert result.text == "part 1 part 2"


async def test_complete_skips_non_text_content_blocks() -> None:
    response = SimpleNamespace(
        content=[
            SimpleNamespace(type="text", text="text-1"),
            SimpleNamespace(type="tool_use", id="abc"),
            SimpleNamespace(type="text", text="text-2"),
        ],
        stop_reason="end_turn",
        usage=SimpleNamespace(
            input_tokens=0,
            output_tokens=0,
            cache_creation_input_tokens=0,
            cache_read_input_tokens=0,
        ),
    )
    llm = LLMClient(client=_mock_anthropic_client(response))
    result = await llm.complete(
        system=["x"],
        messages=[{"role": "user", "content": "hi"}],
    )
    assert result.text == "text-1text-2"


async def test_complete_carries_stop_reason_and_raw_response() -> None:
    response = _mock_response(stop_reason="max_tokens")
    llm = LLMClient(client=_mock_anthropic_client(response))
    result = await llm.complete(
        system=["x"],
        messages=[{"role": "user", "content": "hi"}],
    )
    assert result.stop_reason == "max_tokens"
    assert result.raw is response


# ---------- usage telemetry ----------


async def test_usage_extracted_from_response() -> None:
    response = _mock_response(
        input_tokens=120,
        output_tokens=40,
        cache_creation=1000,
        cache_read=500,
    )
    llm = LLMClient(client=_mock_anthropic_client(response))
    result = await llm.complete(
        system=["x"],
        messages=[{"role": "user", "content": "hi"}],
    )
    assert result.usage == TokenUsage(
        input_tokens=120,
        output_tokens=40,
        cache_creation_input_tokens=1000,
        cache_read_input_tokens=500,
    )


async def test_on_token_usage_callback_fires_after_each_call() -> None:
    captured: list[TokenUsage] = []

    def hook(usage: TokenUsage) -> None:
        captured.append(usage)

    mock = _mock_anthropic_client(_mock_response(input_tokens=7, output_tokens=3))
    llm = LLMClient(client=mock, on_token_usage=hook)
    await llm.complete(system=["x"], messages=[{"role": "user", "content": "hi"}])
    await llm.complete(system=["x"], messages=[{"role": "user", "content": "hi"}])

    assert len(captured) == 2
    assert all(u.input_tokens == 7 and u.output_tokens == 3 for u in captured)


async def test_callback_skipped_when_not_provided() -> None:
    mock = _mock_anthropic_client()
    llm = LLMClient(client=mock)  # no callback
    result = await llm.complete(
        system=["x"],
        messages=[{"role": "user", "content": "hi"}],
    )
    # No callback to invoke; usage still parsed normally
    assert result.usage.input_tokens == 10


async def test_missing_cache_fields_default_to_zero() -> None:
    response = SimpleNamespace(
        content=[SimpleNamespace(type="text", text="ok")],
        stop_reason="end_turn",
        usage=SimpleNamespace(input_tokens=10, output_tokens=5),  # no cache_* fields
    )
    llm = LLMClient(client=_mock_anthropic_client(response))
    result = await llm.complete(
        system=["x"],
        messages=[{"role": "user", "content": "hi"}],
    )
    assert result.usage.cache_creation_input_tokens == 0
    assert result.usage.cache_read_input_tokens == 0


# ---------- live smoke test (opt-in) ----------


SMOKE_ENABLED = os.environ.get("WONDERLAND_LLM_SMOKE") == "1"
smoke_required = pytest.mark.skipif(
    not SMOKE_ENABLED or not os.environ.get("ANTHROPIC_API_KEY"),
    reason="set WONDERLAND_LLM_SMOKE=1 and ANTHROPIC_API_KEY to run live smoke test",
)


@smoke_required
async def test_live_haiku_smoke() -> None:
    """Tiny live call to confirm the Haiku 4.5 path works end-to-end."""
    llm = LLMClient()
    result = await llm.complete(
        system=[CachedBlock("Reply with exactly the word 'pong' and nothing else.")],
        messages=[{"role": "user", "content": "ping"}],
        max_tokens=20,
    )
    assert "pong" in result.text.lower()
    assert result.usage.input_tokens > 0
