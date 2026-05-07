"""Anthropic SDK wrapper with prompt-cache breakpoints and usage telemetry.

Per WONDERLAND_SPEC §5 / D-005. Default model is Haiku 4.5
(``claude-haiku-4-5-20251001``) to keep development costs low; that
choice is reviewable once we have eval data on the agent loop.

The compose_context layer (T-future) builds a layered prompt that looks
like::

    [CONSTITUTION]      ← invariant per-agent → cache here
    [RELATIONSHIPS]     ← slow-changing → cache here
    [CURRENT THREAD]    ← episodic, fast-changing
    [TRIGGER]           ← per-turn

This module's job is to turn that into a request: ``CachedBlock`` items
in ``system`` get ``cache_control: ephemeral``, plain ``str`` items
don't. The Anthropic API caches every prefix up to the rightmost cached
block, so two cache breakpoints means the constitution-only prefix and
the constitution+relationships prefix are both cacheable.

A sync ``on_token_usage`` callback fires after every call so an external
budget tracker can see what each request cost — input tokens, output
tokens, cache creation, cache reads. Useful for the eval harness in P7.

API key resolution when no client is injected: ``ANTHROPIC_API_KEY``
environment variable, then ``<config_dir>/config.json`` (see
``wonderland.config``). The Anthropic SDK raises with a helpful message
if neither is set.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from wonderland.config import load_config

if TYPE_CHECKING:
    from anthropic import AsyncAnthropic


DEFAULT_MODEL = "claude-haiku-4-5-20251001"
# Output token cap. Bumped from 4096 → 16384 after analysis-pending
# Geocities run: Hatter's wide-directive responses (12+ test scenarios
# in one turn) hit the 4096 cap mid-JSON, producing truncated output
# that no parse strategy could recover from (closing `}` and ` ``` `
# never emitted). 16K gives chatty agents real room; cost-conscious
# agents emit fewer tokens and pay less. Per-meeting budget caps
# still bound runaway output spend.
DEFAULT_MAX_TOKENS = 16384


@dataclass(frozen=True)
class CachedBlock:
    """A system-message text block that should become a cache breakpoint.

    The Anthropic API will cache the prompt prefix up to and including
    this block's content. Use one ``CachedBlock`` per layer that should
    be a cacheable prefix (constitution, then relationships, etc.).
    """

    text: str


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0


@dataclass(frozen=True)
class CompletionResult:
    text: str
    stop_reason: str | None
    usage: TokenUsage
    raw: Any = field(repr=False)


SystemPart = str | CachedBlock
Message = dict[str, Any]
TokenUsageCallback = Callable[[TokenUsage], None]


def _api_key_from_config() -> str | None:
    """Read the Anthropic API key from the user config file, if present."""
    try:
        return load_config().anthropic.api_key
    except (OSError, ValueError):
        # Missing file is handled by load_config returning defaults; ValueError
        # covers JSONDecodeError. Either way, fall through to letting the
        # Anthropic SDK raise its own helpful "no key" error on first use.
        return None


def _build_system_blocks(parts: list[SystemPart]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for part in parts:
        if isinstance(part, CachedBlock):
            blocks.append(
                {
                    "type": "text",
                    "text": part.text,
                    "cache_control": {"type": "ephemeral"},
                }
            )
        else:
            blocks.append({"type": "text", "text": part})
    return blocks


def _extract_text(content: list[Any]) -> str:
    parts: list[str] = []
    for block in content:
        block_type = getattr(block, "type", None) or (
            block.get("type") if isinstance(block, dict) else None
        )
        if block_type != "text":
            continue
        text = getattr(block, "text", None)
        if text is None and isinstance(block, dict):
            text = block.get("text")
        if text:
            parts.append(text)
    return "".join(parts)


def _extract_usage(response: Any) -> TokenUsage:
    usage = getattr(response, "usage", None)
    if usage is None:
        return TokenUsage()

    def _g(name: str) -> int:
        value = getattr(usage, name, 0)
        return int(value) if value is not None else 0

    return TokenUsage(
        input_tokens=_g("input_tokens"),
        output_tokens=_g("output_tokens"),
        cache_creation_input_tokens=_g("cache_creation_input_tokens"),
        cache_read_input_tokens=_g("cache_read_input_tokens"),
    )


class LLMClient:
    """Thin Anthropic wrapper that owns model + caching + telemetry concerns.

    The underlying ``AsyncAnthropic`` client is injected for tests, or
    auto-constructed from the environment (``ANTHROPIC_API_KEY``) on
    first use.
    """

    def __init__(
        self,
        client: AsyncAnthropic | None = None,
        *,
        model: str = DEFAULT_MODEL,
        on_token_usage: TokenUsageCallback | None = None,
    ) -> None:
        self._client = client
        self._model = model
        self._on_token_usage = on_token_usage

    @property
    def model(self) -> str:
        return self._model

    @property
    def client(self) -> AsyncAnthropic:
        if self._client is None:
            from anthropic import AsyncAnthropic

            api_key = os.environ.get("ANTHROPIC_API_KEY") or _api_key_from_config()
            self._client = AsyncAnthropic(api_key=api_key) if api_key else AsyncAnthropic()
        return self._client

    async def complete(
        self,
        *,
        system: list[SystemPart],
        messages: list[Message],
        max_tokens: int = DEFAULT_MAX_TOKENS,
        **extra: Any,
    ) -> CompletionResult:
        system_blocks = _build_system_blocks(system)
        response = await self.client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system_blocks,
            messages=messages,
            **extra,
        )
        usage = _extract_usage(response)
        if self._on_token_usage is not None:
            self._on_token_usage(usage)
        return CompletionResult(
            text=_extract_text(response.content),
            stop_reason=getattr(response, "stop_reason", None),
            usage=usage,
            raw=response,
        )
