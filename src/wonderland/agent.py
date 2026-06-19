"""WonderlandAgent — the base class every character subclasses.

Per WONDERLAND_SPEC §5. Wires the four primitives an agent needs to
exist on the bus: an Identity (who am I), an AgentMemory (the SAM
composite — episodic + semantic + relational), a Caucus (where do
utterances live), and an LLMClient (how do I deliberate).

Two async loops run concurrently when ``run()`` is called:

- ``listen()`` subscribes to the bus, records utterances the agent
  engages with, and queues them for processing.
- ``speak()`` pulls from the queue, composes context, deliberates, and
  if the deliberation produces an utterance, publishes it back to the
  bus and records it.

The default ``deliberate()`` returns ``None`` — silence is a valid
move and the base class respects that. Subclasses override
``deliberate()`` (and optionally ``compose_context()``) to give a
character its voice.

Memory recording happens in both loops because:
- ``listen()`` records what we engaged with (per spec §8: "every
  utterance the agent has produced or observed-and-engaged-with")
- ``speak()`` records our own output (the agent may not subscribe to
  its own speech_acts, so listen() wouldn't catch them)
EpisodicStore.record is idempotent on id, so the overlap is safe.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import re
from collections.abc import AsyncIterator, Callable, Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, TypeVar

from pydantic import BaseModel, Field, ValidationError

_T = TypeVar("_T")

from wonderland.llm import CachedBlock, Message, SystemPart
from wonderland.parsing import ResponseParseError
from wonderland.primer import FRAMEWORK_PRIMER
from wonderland.telemetry import reset_current_thread_id, set_current_thread_id
from wonderland.utterance import Artifact, SpeechAct, Utterance

if TYPE_CHECKING:
    from wonderland.caucus import Caucus
    from wonderland.identity import Identity
    from wonderland.llm import LLMClient
    from wonderland.memory import AgentMemory


class AgentState(StrEnum):
    """Per-agent activity state for turn-based quiescence detection.

    The ThreadMonitor reads these to decide whether a meeting can quiesce
    — a thread is quiescent iff every member is IDLE. This replaces the
    wall-clock model where bus silence stood in for agent inactivity
    (and missed slow tool loops + LLM calls in flight, see analysis 022).

    States:
    - IDLE: gather_triggers blocked, waiting for a turn signal. Truly silent.
    - AWAITING_RESPONSE: in deliberate() / LLM call in flight. No bus output yet.
    - IN_TOOL_LOOP: between LLM calls inside _complete_with_tools, executing tools.

    The wall-clock timer remains as a safety net for hung LLM calls
    (agent stuck in AWAITING_RESPONSE without state reset).
    """

    IDLE = "idle"
    AWAITING_RESPONSE = "awaiting_response"
    IN_TOOL_LOOP = "in_tool_loop"


@dataclass(frozen=True)
class Context:
    """The layered prompt skeleton an agent assembles each turn.

    Per WONDERLAND_SPEC §5. T7 establishes the shape; P2 fills the
    layers with content from semantic + relational memory and the
    current thread's history.
    """

    constitution: str
    relationships: str = ""
    current_thread: str = ""
    triggers: tuple[Utterance, ...] = field(default_factory=tuple)
    engagement_state: str = ""
    """Pre-trigger annotation: factual snapshot of what's been said and
    shipped on the current thread (own turns + own artifacts + team
    artifacts). Lets the agent's protocol's "by your Nth turn ship X"
    rules see deterministic data instead of inferring from the history
    transcript prose. Empty string when no thread context is available
    (no triggers, fresh agent)."""

    def to_llm_request(self) -> tuple[list[SystemPart], list[Message]]:
        """Convert this context into ``LLMClient.complete()`` arguments.

        Layered prompt structure (cached blocks create cache breakpoints;
        Anthropic supports up to 4 per request).

        - **Framework primer** — invariant per-call AND across agents.
          Cast list, speech-act vocabulary, engagement grades, artifact
          schemas, conflict-resolution table. Sent as a plain string
          (not CachedBlock) — still cached as part of any downstream
          breakpoint's prefix; just doesn't have its own breakpoint.
          Trades cross-agent framework-only cache for an additional
          breakpoint slot at ``current_thread`` (see below). Within
          single-agent loops (most of M7's cost) this trade is net
          positive; multi-agent meetings still cache the framework via
          the constitution-prefix.
        - **Constitution** — invariant per-agent (loaded once).
        - **Relationships** — slow-changing per-agent (the per-other-
          agent notes for the speakers in the current trigger set).
        - **Current thread** — per-emission history transcript.
          Cached as of context-compression Lever A: within a single
          Tweedle emission's tool-use loop (~27 LLM calls per emission
          in mvp-demo2 M7 telemetry), this transcript doesn't change
          across the round-trips. Caching shifts it from $1/MTok
          uncached input to $0.10/MTok cache read on every round-trip
          after the first. Expected M7 savings: ~20-40%.
        - **Triggers** — per-turn. In the user message, not the system
          blocks.
        """
        system: list[SystemPart] = [
            # Framework primer kept as a plain string so its breakpoint
            # slot can be reused by current_thread (the higher-leverage
            # cache). Framework is still in the cached prefix of every
            # downstream CachedBlock — see docstring.
            FRAMEWORK_PRIMER,
            CachedBlock(self.constitution),
        ]
        if self.relationships:
            system.append(CachedBlock(self.relationships))
        if self.current_thread:
            # CachedBlock since context-compression Lever A. The current_thread
            # transcript is stable across all tool-use round-trips within a
            # single agent emission; caching it captures the within-emission
            # reuse pattern that drives M7 cost.
            system.append(CachedBlock(self.current_thread))

        trigger_text = "\n\n".join(_format_utterance(u) for u in self.triggers)
        # Engagement state goes BEFORE the trigger in the user message
        # so the LLM reads it first. Factual data (counts), not
        # prescription — the protocol decides what to do with it.
        body_parts: list[str] = []
        if self.engagement_state:
            body_parts.append(self.engagement_state)
        body_parts.append(trigger_text or "(no trigger)")
        messages: list[Message] = [{"role": "user", "content": "\n\n".join(body_parts)}]
        return system, messages


def format_utterance(u: Utterance) -> str:
    """Render one utterance as a labeled text block for prompt inclusion.

    Includes a brief artifact appendix when artifacts are attached, so
    downstream readers can reference the canonical slug / number /
    state of an artifact a previous speaker landed. Without this,
    follow-up agents (e.g., a Tweedle responding to a sibling's
    Contract Note) have no way to learn the slug they need to
    reference, and the LLM either fabricates one or skips the
    response.
    """
    head = f"[{u.speaker.name} — {u.speech_act.value}]\n{u.content.body}"
    if not u.content.artifacts:
        return head
    bits: list[str] = []
    for artifact in u.content.artifacts:
        payload = artifact.payload
        slug = payload.get("slug", "")
        title = payload.get("title", "")
        state = payload.get("state", "")
        op = payload.get("operation", "")
        parts = [artifact.kind]
        if slug:
            parts.append(f"slug={slug}")
        if title:
            parts.append(f'"{title}"')
        if op:
            parts.append(f"operation={op}")
        if state:
            parts.append(f"state={state}")
        bits.append(" ".join(parts))
    return f"{head}\n\n(artifacts: {'; '.join(bits)})"


def format_transcript(utterances: Iterable[Utterance]) -> str:
    """Join an ordered sequence of utterances into a single transcript string.

    Empty input yields an empty string. Order is preserved as given —
    callers are expected to pass utterances chronologically.
    """
    return "\n\n".join(format_utterance(u) for u in utterances)


# Backwards-compatible private alias used in Context.to_llm_request.
_format_utterance = format_utterance


# --------------------------------------------------------------------- #
# T-ab24a Stage 1 — context-size diagnostic instrumentation.
#
# mvp-demo-rerun-A surfaced a memory-inflation failure mode: after N
# iterations on the same feature, the assembled context grew past
# Claude's 200K hard cap and every deliberation crashed with a
# BadRequestError. T-ab23 surfaced the crash; this helper surfaces
# *which* context layer is driving the growth so Stage 2 can target
# the right thing to truncate.
#
# Approximation: ~4 chars per token. Good enough for diagnostic
# breakdowns (we're looking for "thread_history is 170K" vs
# "triggers are 5K", not exact token math). Exact tokenization is
# available via anthropic.client but adds latency to every context
# build; not worth it for instrumentation.
# --------------------------------------------------------------------- #

_CONTEXT_SIZE_WARN_TOKENS = 100_000  # 50% of Claude's 200K cap
_CONTEXT_SIZE_INFO_TOKENS = 30_000  # Below this, silence

# T-ab24b Stage 2 — thread_history budget.
#
# Observed in mvp-demo-rerun-A: 657K chars of thread_history mapped
# to 203K real tokens (3.24 chars/token for our utterance content,
# which is markdown-with-code-heavy). Claude's hard cap is 200K
# real tokens. Reserve ~70K real tokens for system prompt + tools
# schema + constitution + triggers + headroom, budget the rest for
# thread_history.
#
# 130K real tokens × 3.24 chars/token ≈ 420K char budget. We budget
# in chars directly (rather than going through the approximation)
# so the constant has the calibration baked in — no double-
# conversion error.
_THREAD_HISTORY_BUDGET_CHARS = 420_000


def _approx_tokens(text: str) -> int:
    """Char-based token approximation (~4 chars/token for English text).

    Conservative — undercounts real tokens by ~1.2-1.3× for our
    utterance content (markdown + code). Good for diagnostic
    breakdowns; for budgeting use char-counts with calibrated
    constants instead (see ``_THREAD_HISTORY_BUDGET_CHARS``)."""
    return len(text) // 4


def _approx_utterance_chars(u: Utterance) -> int:
    """Approximate the rendered size of a single utterance.

    Used by ``_budget_thread_history`` to walk the history and pick
    which utterances fit in the budget. Matches ``format_utterance``
    shape closely enough for budgeting (slight over-count is fine;
    we err on the side of preserving headroom)."""
    body_len = len(u.content.body or "")
    artifact_len = sum(
        len(a.payload or "") if hasattr(a, "payload") and isinstance(a.payload, str)
        else 200  # rough estimate when artifact payload isn't a plain string
        for a in u.content.artifacts
    )
    # ~80 chars for the speaker/act header + framing
    return body_len + artifact_len + 80


# T-ab24c — first-K priming preserved across the truncation. Earliest
# utterances in a meeting establish the framing (directive, ticket,
# contract notes); they're load-bearing for an agent picking up the
# thread. We keep the first PRIMING_KEEP utterances by chronological
# position, then walk newest backward filling the remaining budget.
_PRIMING_KEEP = 10


def _budget_thread_history(
    history: list[Utterance],
    budget_chars: int = _THREAD_HISTORY_BUDGET_CHARS,
) -> tuple[list[Utterance], int]:
    """Truncate ``history`` to fit within ``budget_chars`` of
    rendered size. Keeps first-K + newest-K, drops the middle.

    Returns ``(kept_history, dropped_count)``. When the full history
    fits, returns it unchanged with ``dropped_count == 0``.

    Strategy when over budget:
      1. Keep the first ``_PRIMING_KEEP`` utterances — the meeting's
         opening framing (directive, ticket, early contracts).
         Preserves the agent's anchor for what the meeting is about.
      2. Walk the remaining tail newest → oldest, including each
         utterance until the remaining budget exhausts. Preserves
         active deliberation context.
      3. Drop the middle. The accumulated iteration noise from past
         attempts on the same thread is what grows linearly with
         re-runs; that's exactly what we want to shed.

    T-ab24b's first cut preserved all seed utterances on the theory
    that seeds were small framing artifacts. mvp-demo-rerun-A broke
    that assumption: Runner.convene re-publishes prior-thread
    history as seeds, so after enough iteration, 2165 of 2169
    utterances were seeds — the truncation dropped 4 non-seeds and
    kept everything else. T-ab24c treats seeds and non-seeds
    equivalently. The first-K + newest-K strategy preserves the
    same framing utterances (they're at the start of the thread)
    without needing to special-case seed-ness.

    Edge case: when the first-K itself exceeds budget, we keep the
    first-K anyway and drop everything after. Operator should
    investigate (likely an unusually huge ticket or seed payload);
    Stage 3 (LLM summarization) would compact the priming itself
    when needed.
    """
    total = sum(_approx_utterance_chars(u) for u in history)
    if total <= budget_chars:
        return history, 0

    # Priming = first K utterances (chronological). These carry the
    # meeting's opening framing regardless of seed-ness.
    priming = history[:_PRIMING_KEEP]
    tail = history[_PRIMING_KEEP:]
    priming_size = sum(_approx_utterance_chars(u) for u in priming)
    remaining = budget_chars - priming_size

    if remaining <= 0:
        # Priming alone exceeds budget — keep priming, drop the tail.
        # Operator-investigatable; Stage 3 would handle gracefully.
        return priming, len(tail)

    # Walk the tail newest → oldest, accumulating until budget exhausts.
    kept_tail: list[Utterance] = []
    running = 0
    for u in reversed(tail):
        size = _approx_utterance_chars(u)
        if running + size > remaining:
            break
        kept_tail.append(u)
        running += size
    kept_tail.reverse()

    dropped = len(tail) - len(kept_tail)
    return priming + kept_tail, dropped


def _truncation_banner(dropped_count: int) -> str:
    """One-line notice prepended to a truncated transcript so agents
    know they're seeing a partial thread. Stays small — banner cost
    shouldn't eat measurable budget."""
    return (
        f"[Context-budget notice: {dropped_count} earlier "
        f"utterance(s) in this thread were elided to fit the "
        f"model's context window. Seed utterances + most-recent "
        f"turns are preserved.]\n\n"
    )


# T-ab57: tool-result truncation. Tool results live in the
# deliberation's loop_messages list for the rest of that
# deliberation, so a single oversized result (e.g. 35K-byte grep,
# 65K git_diff) costs cache_write once + cache_read on every
# subsequent LLM call in the same tool loop. Capping at a
# reasonable budget prevents the long-tail outliers from amplifying
# across iterations. obol-260522-1 data: 52% of tweedle tool-result
# bytes were above 5K. The cap encourages the model to be more
# targeted on retries (e.g. grep with narrower pattern, read_file
# with line range) rather than dumping huge outputs into context.
_TOOL_RESULT_CAP_CHARS = 5_000


def _maybe_truncate_tool_result(content: str, tool_name: str) -> str:
    """Cap oversized tool results; preserve small ones verbatim.

    When the content exceeds ``_TOOL_RESULT_CAP_CHARS``, keep the
    head (most output formats put the most useful info first —
    e.g. grep matches, file content from line 1) and append a
    marker telling the model how many bytes were dropped + how to
    get them if needed.
    """
    if not isinstance(content, str):
        # Tool framework currently returns str; defensive against
        # future tool returning structured content.
        return content
    if len(content) <= _TOOL_RESULT_CAP_CHARS:
        return content
    truncated = len(content) - _TOOL_RESULT_CAP_CHARS
    head = content[:_TOOL_RESULT_CAP_CHARS - 200]
    marker = (
        f"\n\n[truncated {truncated:,} bytes for context budget. "
        f"If the truncated content is load-bearing, re-run "
        f"`{tool_name}` with narrower scope (e.g. line range, "
        f"more specific pattern, smaller directory).]"
    )
    return head + marker


def _log_context_size(
    agent_name: str,
    triggers: list[Utterance],
    ctx: "Context",
) -> None:
    """Log per-layer context size after assembly. WARN above 100K
    tokens (half the 200K cap) so operators see prompts approaching
    the wall before they crash; INFO above 30K for routine
    visibility. Silent under 30K — most prompts are fine."""
    import logging

    constitution_t = _approx_tokens(ctx.constitution)
    relationships_t = _approx_tokens(ctx.relationships)
    thread_history_t = _approx_tokens(ctx.current_thread)
    engagement_state_t = _approx_tokens(ctx.engagement_state)
    triggers_text = format_transcript(triggers) if triggers else ""
    triggers_t = _approx_tokens(triggers_text)
    total = (
        constitution_t
        + relationships_t
        + thread_history_t
        + engagement_state_t
        + triggers_t
    )

    if total < _CONTEXT_SIZE_INFO_TOKENS:
        return

    thread_id = triggers[0].thread_id if triggers else "(none)"
    logger = logging.getLogger("wonderland.context_size")
    level = (
        logging.WARNING
        if total >= _CONTEXT_SIZE_WARN_TOKENS
        else logging.INFO
    )
    logger.log(
        level,
        "context-size agent=%s thread=%s total~=%d "
        "constitution=%d relationships=%d thread_history=%d "
        "triggers=%d engagement_state=%d",
        agent_name,
        thread_id,
        total,
        constitution_t,
        relationships_t,
        thread_history_t,
        triggers_t,
        engagement_state_t,
    )


# --------------------------------------------------------------------- #
# Compaction — agent reflects on a thread between threads
# --------------------------------------------------------------------- #


@dataclass(frozen=True)
class CompactionContext:
    """Reflection prompt skeleton — what the agent sees when compacting.

    Constitution and protocol stay invariant per agent (cached). Existing
    semantic + relational memory are slow-changing (cached when present).
    The thread transcript is the new material — what we're reflecting on
    — and goes into the user message uncached.
    """

    constitution: str
    protocol: str
    existing_semantic: str = ""
    existing_relational: str = ""
    transcript: str = ""

    def to_llm_request(self) -> tuple[list[SystemPart], list[Message]]:
        system: list[SystemPart] = [
            CachedBlock(self.constitution),
            CachedBlock(self.protocol),
        ]
        if self.existing_semantic:
            system.append(
                CachedBlock(f"## Your current semantic memory\n\n{self.existing_semantic}")
            )
        if self.existing_relational:
            system.append(CachedBlock(self.existing_relational))

        user = (
            f"## Thread transcript to reflect on\n\n{self.transcript}"
            if self.transcript
            else "(no thread transcript provided)"
        )
        return system, [{"role": "user", "content": user}]


class CompactionResponse(BaseModel):
    """Structured JSON the agent returns from a compaction reflection.

    Each entry in ``semantic_updates`` REPLACES the topic file in full;
    each entry in ``relational_updates`` REPLACES the per-agent file in
    full. Empty dicts are valid — an uneventful thread or one outside
    the agent's domain produces no updates, and that's honest.
    """

    semantic_updates: dict[str, str] = Field(default_factory=dict)
    relational_updates: dict[str, str] = Field(default_factory=dict)


@dataclass(frozen=True)
class CompactionResult:
    """What changed during a compaction. Empty when nothing was updated."""

    thread_id: str = ""
    semantic_topics_updated: tuple[str, ...] = ()
    relational_agents_updated: tuple[str, ...] = ()

    @property
    def is_empty(self) -> bool:
        return not (self.semantic_topics_updated or self.relational_agents_updated)


class CompactionResponseParseError(ValueError):
    """The compaction LLM response did not parse into a valid CompactionResponse."""


_COMPACTION_JSON_BLOCK = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def parse_compaction_response(text: str) -> CompactionResponse:
    """Extract the fenced JSON block and validate it as CompactionResponse.

    Tolerates the LLM omitting the fence and emitting bare JSON.
    """
    match = _COMPACTION_JSON_BLOCK.search(text)
    if match is None:
        candidate = text.strip()
        if not (candidate.startswith("{") and candidate.endswith("}")):
            raise CompactionResponseParseError("no JSON block found in compaction response")
        raw = candidate
    else:
        raw = match.group(1)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CompactionResponseParseError(
            f"compaction response was not valid JSON: {exc}"
        ) from exc
    try:
        return CompactionResponse.model_validate(data)
    except ValidationError as exc:
        raise CompactionResponseParseError(
            f"compaction response failed schema validation: {exc}"
        ) from exc


_DEFAULT_COMPACTION_PROTOCOL = """\
You have just observed a thread to its conclusion. Reflect on it in your
own voice and produce updates to your semantic memory (distilled beliefs
about the codebase, the domain, the work) and your relational memory
(what you've observed about each other agent in the thread, in their
working with you).

Respond with exactly one fenced JSON block:

```
{
  "semantic_updates": {
    "topic-slug": "full updated content for this topic in markdown",
    "...": "..."
  },
  "relational_updates": {
    "other_agent_name": "full updated notes for this agent in markdown",
    "...": "..."
  }
}
```

Each entry REPLACES the existing file in full — include everything you
want to keep, not just additions or deltas. If you want to expand on
existing notes, paste the existing notes back (you'll see them in the
prompt) and add to them.

If the thread was uneventful in your domain or your view of an agent
hasn't changed, an empty compaction (`{}`) is correct and honest. Do
not invent reflections to fill space.

Speak in your own voice. Use slugs for topic keys (lowercase, dashes).
Use canonical agent names (snake_case) for relational keys.
"""


class WonderlandAgent:
    """Base class for every Wonderland character.

    Subclasses override ``deliberate()`` to give the character its voice.
    The default returns ``None`` (silence), which is correct for an
    agent that hasn't been told what to say.

    Subclasses can also override ``COMPACTION_PROTOCOL`` to flavor
    how the agent reflects on a thread between threads. The default
    asks for structured JSON updates to semantic + relational memory.
    """

    COMPACTION_PROTOCOL: str = _DEFAULT_COMPACTION_PROTOCOL

    def __init__(
        self,
        identity: Identity,
        memory: AgentMemory,
        bus: Caucus,
        llm: LLMClient | None = None,
    ) -> None:
        self.identity = identity
        self.memory = memory
        self.bus = bus
        self.llm = llm
        self.pending: asyncio.Queue[Utterance] = asyncio.Queue()
        # Hard budget gate. None = no cap (current default for direct
        # agent construction). Runner.setup wires this for every agent
        # so the speak loop refuses to spend once the team is over the
        # cap. Per analysis 011: a soft cap (which only emits a warning
        # event) failed during T36 — the team blew past $3 by 86%
        # because each agent had in-flight calls when the cap fired
        # and the auto-respond re-triggered everyone for another round.
        # The hard gate is enforced inside speak() so no LLM call
        # happens for an over-budget turn.
        self._budget_ok: Callable[[], bool] | None = None
        # Optional ThreadRoster reference for INVITE handling (Block 2c).
        # When set, the agent's speak() can mutate the roster on INVITE
        # publish so the named invitees join the meeting before the
        # invite reaches the bus. None = no roster wiring = INVITE
        # publishes through normally but doesn't change membership.
        self._roster = None  # type: ignore[var-annotated]
        # Optional Tools reference for tool-use deliberation. When set,
        # subclasses' deliberate() can call _complete_with_tools to run
        # the read/write/list/grep tool-use loop. Set via set_tools or
        # the subclass constructor. None = no tools = single-shot
        # complete() (the original behavior).
        self._tools = None  # type: ignore[var-annotated]
        # Optional callback for the late-publish stop-gap. When set, the
        # speak loop calls handler(utterance) before publish; if the
        # handler returns True, the utterance is suppressed (the target
        # thread closed before this deliberation finished). The Runner
        # installs this; agents constructed directly leave it None.
        self._late_publish_handler = None  # type: ignore[var-annotated]
        # Populated by _complete_with_tools each time write_file is
        # successfully called inside the tools loop. Subclasses inspect
        # it after parsing to coerce the bus utterance when the LLM
        # writes files but picks a non-implementation decision (the
        # working tree is the artifact, the bus utterance is the
        # team's record of what happened).
        self._last_write_file_paths: list[str] = []
        # Phase orchestrator gate (analysis 033 / P9 T58c). When True,
        # listen() records bus traffic to memory but does NOT enqueue
        # for deliberation — the orchestrator drives compose_context +
        # deliberate directly. False = autonomous engagement (the
        # original behavior).
        self._orchestrator_owned: bool = False
        # Turn-based quiescence support (analysis 022 follow-up). The
        # speak() loop and tool loop call _set_state to mark the agent's
        # current activity; the Runner installs a state-change handler
        # that funnels updates to the ThreadMonitor. Quiescence becomes
        # "all members IDLE" rather than "no bus events for N seconds".
        self._state: AgentState = AgentState.IDLE
        self._state_change_handler: (
            Callable[[str, AgentState, AgentState], None] | None
        ) = None
        # Register the bus subscription at construction time, *not* inside
        # listen()'s async body. Caucus implementations register the
        # subscriber queue synchronously when subscribe() is called; the
        # async iteration only consumes from it. Doing this in __init__
        # means publishes that happen between construction and the first
        # listen() iteration aren't lost.
        self._bus_iterator: AsyncIterator[Utterance] = self.bus.subscribe(
            self.identity.name,
            self.identity.interests,
        )
        self._listen_task: asyncio.Task[None] | None = None
        self._speak_task: asyncio.Task[None] | None = None

    # ------------------------------------------------------------------ #
    # Listen loop
    # ------------------------------------------------------------------ #

    def should_engage(self, u: Utterance) -> bool:
        return self.identity.should_engage(u, self.memory)

    async def listen(self) -> None:
        """Consume from the bus; record + queue what we engage with.

        The bus fans out to every subscriber including the agent itself,
        so the agent observes its own published utterances. Skip those —
        if an agent wants to reflect on something it said earlier, it
        queries episodic memory (where speak() already recorded it).
        Treating own utterances as fresh triggers would loop forever for
        any agent whose engagement rules accept its own speech_act.
        """
        async for utterance in self._bus_iterator:
            # Seeds first, before the self-speaker filter. Seeds need
            # to land in this agent's memory regardless of who emitted
            # them — including the case where the seed is attributed
            # to *this* agent (cross-run continuity via the disk
            # fallback in seeds_fallback.py: a synthetic ticket
            # attributed to white_rabbit becomes context for the
            # composition meeting where white_rabbit needs to read
            # her own prior tickets to compose features).
            #
            # Without this ordering, white_rabbit would skip her own
            # seeded tickets and protest "I can't see the tickets" —
            # the bug r42-obol surfaced. Engagement still short-
            # circuits via is_seed in EngagementRules.categorize, so
            # seeds don't queue for deliberate(); they just become
            # readable history.
            if utterance.is_seed:
                await self.memory.record(utterance)
                continue
            # Own non-seed utterances: already recorded via speak(),
            # skip to avoid double-recording + treating self-speech as
            # a fresh engagement trigger (which would loop forever).
            if utterance.speaker.name == self.identity.name:
                continue
            if self._orchestrator_owned:
                # Phased meetings (P9): the phase orchestrator drives
                # deliberation directly. Record bus traffic to memory
                # so compose_context sees it as thread history, but
                # don't enqueue — the orchestrator never reads the
                # pending queue, and unbounded queueing across
                # back-to-back phased meetings could leak.
                await self.memory.record(utterance)
                continue
            if self.should_engage(utterance):
                await self.memory.record(utterance)
                await self.pending.put(utterance)

    # ------------------------------------------------------------------ #
    # Speak loop
    # ------------------------------------------------------------------ #

    async def gather_triggers(self) -> list[Utterance]:
        """Collect the utterances to deliberate on next.

        Default: one trigger at a time. Subclasses can override to batch
        (the Hatter might want to see all test-implicating utterances
        from a thread before generating scenarios) or debounce.
        """
        return [await self.pending.get()]

    async def compose_context(
        self,
        triggers: list[Utterance],
        *,
        memory_scope: str = "all",
    ) -> Context:
        """Build the layered context for this turn.

        Constitution comes from the identity (invariant, cached).
        Relationships are pulled from relational memory for the speakers
        we're seeing in this turn (cached if non-empty — slow-changing).
        Current-thread history is read from episodic memory and
        rendered as a chronological transcript (uncached — changes
        every turn). Triggers themselves are excluded from the
        transcript since they're presented separately as the immediate
        stimulus.

        T-ab25a: ``memory_scope`` controls what slice of thread
        history the agent sees.
          - ``"all"`` (default): every utterance, including seeds
            re-published from prior threads. Original behavior.
          - ``"meeting_only"``: non-seed utterances only. Right for
            pure-execution phases (implement) where the accumulated
            iteration noise is contamination, not signal.
        Passed in by the meeting engine from the active phase's
        ``memory_scope`` field on ``PhaseDefinition``.
        """
        thread_text = ""
        relationships_text = ""
        engagement_state = ""
        if triggers:
            thread_id = triggers[0].thread_id
            # T-ab52: scope the recall query to the active branch's
            # inheritance chain (project + active branch). Without
            # this, query_by_thread defaults to ALL branches — so
            # T-ab8's per-milestone write isolation has no read-time
            # teeth: a query for thread_id='scoping' during M6 design
            # pulls in M1-M5's scoping utterances too (different
            # branches, same thread_id). obol-260522-1 measured 72
            # such cross-milestone utterances bleeding into M6's
            # recall before this fix landed. The inheritance_chain
            # for ``design:m6-...`` is ``[project, design:m6-...]``
            # — agent sees its own branch + project-level summaries
            # only, sibling milestone branches are filtered out.
            from wonderland.memory.episodic import inheritance_chain

            history = await self.memory.query_by_thread(
                thread_id, branches=inheritance_chain()
            )
            trigger_ids = {t.id for t in triggers}
            history_excluding_triggers = [u for u in history if u.id not in trigger_ids]

            # T-ab27: drop nudge utterances. Dodo's priority-window-
            # open nudges are ~280 chars of scaffolding ("your turn
            # to act…") with no semantic content the agent benefits
            # from re-reading. Filter at compose_context (not at
            # storage) so the audit trail is preserved — operators
            # debugging meeting flow can still see the nudge sequence
            # via direct SQLite query or future dashboard view.
            # Future-proofed by speech_act, not speaker, in case
            # other characters emit framing nudges later.
            history_excluding_triggers = [
                u for u in history_excluding_triggers
                if u.speech_act is not SpeechAct.NUDGE
            ]

            # T-ab25a: apply memory_scope filter. When meeting_only,
            # drop seed utterances (re-published prior-thread history).
            # The mvp-demo-rerun-A broken implement thread had 2165
            # seeds vs 4 non-seeds — meeting_only drops 99.8% of the
            # accumulated context for a pure-execution phase.
            if memory_scope == "meeting_only":
                history_excluding_triggers = [
                    u for u in history_excluding_triggers if not u.is_seed
                ]

            # T-ab24b: cap thread_history rendered size so iterative
            # re-runs on the same thread don't accumulate past the
            # model's context window. Preserves seeds + most-recent;
            # drops the middle.
            budgeted_history, dropped = _budget_thread_history(
                history_excluding_triggers,
            )
            thread_text = format_transcript(budgeted_history)
            if dropped > 0:
                thread_text = _truncation_banner(dropped) + thread_text
                import logging
                logging.getLogger("wonderland.context_size").info(
                    "thread_history truncated: agent=%s thread=%s "
                    "dropped=%d kept=%d (seeds + most-recent)",
                    self.identity.name,
                    thread_id,
                    dropped,
                    len(budgeted_history),
                )

            speaker_names: set[str] = {t.speaker.name for t in triggers}
            for past in history_excluding_triggers:
                speaker_names.add(past.speaker.name)
            speaker_names.discard(self.identity.name)
            relationships_text = self.memory.relational.for_speakers(sorted(speaker_names))

            engagement_state = self._build_engagement_state(thread_id, history)

        ctx = Context(
            constitution=self.identity.constitution_text,
            relationships=relationships_text,
            current_thread=thread_text,
            triggers=tuple(triggers),
            engagement_state=engagement_state,
        )
        _log_context_size(self.identity.name, triggers, ctx)
        return ctx

    def _build_engagement_state(
        self, thread_id: str, history: list[Utterance]
    ) -> str:
        """Compute factual counts for the engagement-state annotation.

        Reads the thread history (already queried by compose_context) and
        emits a concise summary the LLM can act on without re-deriving:
        - this agent's prior turn count + speech-act breakdown
        - this agent's artifacts shipped (count by kind)
        - team-wide artifacts shipped (count by kind, includes own)

        Format kept terse so it doesn't dominate the user message —
        the trigger and thread-history transcript still carry the
        narrative.
        """
        from collections import Counter

        own_name = self.identity.name
        # Fresh = utterances emitted in THIS thread; seeded = utterances
        # re-published by Runner.convene from a prior thread. Surface
        # them separately so the agent can tell "we already have these
        # contracts (seeded)" from "I've shipped this much in this
        # thread (fresh)" — without that split, an agent reading the
        # engagement state thinks seeded artifacts are their own
        # current-thread work.
        fresh = [u for u in history if not u.is_seed]
        seeded = [u for u in history if u.is_seed]

        own_turns = [u for u in fresh if u.speaker.name == own_name]
        own_acts = Counter(u.speech_act.value for u in own_turns)
        own_artifacts = Counter(
            a.kind for u in own_turns for a in u.content.artifacts
        )
        team_artifacts = Counter(
            a.kind for u in fresh for a in u.content.artifacts
        )
        seeded_artifacts = Counter(
            a.kind for u in seeded for a in u.content.artifacts
        )

        def _fmt_counter(c: Counter) -> str:
            if not c:
                return "none"
            return ", ".join(f"{k}×{v}" for k, v in sorted(c.items(), key=lambda kv: -kv[1]))

        lines = [f"[engagement state on thread {thread_id!r}]"]
        if own_turns:
            lines.append(
                f"your prior turns on this thread: {len(own_turns)} ({_fmt_counter(own_acts)})"
            )
        else:
            lines.append("your prior turns on this thread: 0")
        lines.append(f"your artifacts shipped on this thread: {_fmt_counter(own_artifacts)}")
        lines.append(f"team artifacts shipped on this thread: {_fmt_counter(team_artifacts)}")
        if seeded_artifacts:
            lines.append(
                f"context from prior threads (seeded): {_fmt_counter(seeded_artifacts)}"
            )
        lines.append("[end engagement state]")
        return "\n".join(lines)

    async def deliberate(self, context: Context) -> Utterance | None:
        """Decide what to say. Return ``None`` for silence.

        The base default is silence. Subclasses override to call
        ``self.llm.complete(...)`` with the assembled context and
        produce an Utterance.
        """
        return None

    def set_roster(self, roster) -> None:  # type: ignore[no-untyped-def]
        """Wire (or clear) a ThreadRoster reference. When set, an INVITE
        utterance the agent emits adds the named addressed_to agents to
        the thread's roster *before* publish, so the bus delivers the
        invite to the new members. None = no roster wiring.
        """
        self._roster = roster

    def set_tools(self, tools) -> None:  # type: ignore[no-untyped-def]
        """Wire (or clear) a Tools reference. When set, subclasses' deliberate()
        can call _complete_with_tools to run the read/write/list/grep
        tool-use loop. None = no tools = single-shot complete() (the
        original behavior).
        """
        self._tools = tools

    def set_state_change_handler(
        self,
        handler,  # type: ignore[no-untyped-def]
    ) -> None:
        """Wire (or clear) the agent-state change handler.

        ``handler(agent_name, from_state, to_state)`` is called by
        ``_set_state`` on every transition. The Runner installs this so
        the ThreadMonitor can detect quiescence based on actual agent
        activity rather than wall-clock bus silence.
        """
        self._state_change_handler = handler

    def _set_state(self, new_state: AgentState) -> None:
        """Update the agent's activity state and notify any handler.

        No-op if the state is unchanged (avoids handler spam from the
        tool loop re-entering AWAITING_RESPONSE on each iteration when
        already there). Handler exceptions are swallowed — a buggy
        monitor must not kill the speak loop.
        """
        if new_state is self._state:
            return
        old = self._state
        self._state = new_state
        if self._state_change_handler is not None:
            try:
                self._state_change_handler(self.identity.name, old, new_state)
            except Exception as exc:
                import sys

                print(
                    f"[{self.identity.name}] state-change handler raised "
                    f"{type(exc).__name__}: {exc} — ignoring",
                    file=sys.stderr,
                )

    def set_late_publish_handler(
        self,
        handler,  # type: ignore[no-untyped-def]
    ) -> None:
        """Wire (or clear) the late-publish handler.

        ``handler(utterance) -> bool`` is called by ``speak()`` right
        before publishing. If it returns ``True``, the utterance is
        suppressed (the framework treats it as a "late" deliberation
        whose target thread already closed) — speak() skips publish and
        memory.record. If ``False`` (default behavior when no handler
        is wired), publish proceeds normally.

        The Runner installs this so it can detect the slow-deliberation-
        crosses-meeting-boundaries pattern surfaced in T36 v17/v18 and
        roadmap 29497820. This is a stop-gap until the big Dodo
        meeting-orchestration rework lands.
        """
        self._late_publish_handler = handler

    @property
    def tools(self):  # type: ignore[no-untyped-def]
        return self._tools

    async def _complete_with_tools(
        self,
        system: list,  # type: ignore[type-arg]
        messages: list,  # type: ignore[type-arg]
        max_tool_iterations: int = 15,
        max_read_iterations: int = 30,
    ) -> str:
        """Tool-use loop. Calls the LLM with tools=[...]; if the response
        is a tool_use, executes the tools, appends results, calls again.
        Returns the final text response when the LLM stops requesting tools.

        SPLIT BUDGET. Reads are EXPLORATION, not progress — they shouldn't
        eat the budget the agent needs to BUILD. A single shared cap made an
        agent that read 20 files to understand a feature run out before it
        could write a line (the frontend Tweedle that read its way through
        the data-flow chain and shipped nothing; Caterpillar reading file
        after file as the project grew, then going silent). So there are two
        budgets:
          - ``max_read_iterations`` — read-only turns (read_file / list_files
            / grep / git_status / git_diff). Generous, because understanding
            a feature is allowed to be expensive. Bounded so accumulated read
            results (each kept in-context for later turns) don't blow the
            window, and so a read-runaway can't spin forever.
          - ``max_tool_iterations`` — productive turns (a turn that calls
            write_file or any non-read tool, i.e. real progress). The tight
            convergence budget.
        A turn whose tool calls are ALL reads advances only the read budget.
        The "stop exploring, commit now" nudge fires as EITHER budget runs
        low; on exhaustion of either, a final no-tools call forces the
        structured response rather than returning "".

        Side effect: ``self._last_write_file_paths`` is reset at entry
        and populated as ``write_file`` tool calls succeed. Subclasses
        can read it after parsing to coerce decisions when the LLM
        writes files but picks a non-implementation utterance.
        """
        _READ_ONLY_TOOLS = frozenset({
            "read_file", "list_files", "grep", "git_status", "git_diff",
        })
        assert self._tools is not None, "set_tools must have been called"
        assert self.llm is not None
        self._last_write_file_paths = []
        tool_defs = self._tools.tool_definitions()

        # Working copy of messages we'll extend with assistant + tool_result
        # turns. The caller's `messages` is preserved.
        loop_messages = list(messages)

        read_iters = 0
        productive_iters = 0
        # Per-loop read cache (Kohl's ring-buffer idea, keyed for
        # invalidate-on-write rather than evict-by-age). Re-reading the same
        # file while reasoning through a dependency chain is the dominant
        # source of read-budget waste; serving an identical read from the
        # cache costs nothing and DOESN'T spend a read turn, so the read
        # budget tracks UNIQUE surface area instead of total read calls —
        # exactly the axis that scales with project size at M8.
        read_cache: dict[str, str] = {}
        # Absolute backstop: a fully-cached read turn is free, so a model that
        # spins re-requesting the same file would never trip the read/write
        # caps. total_iters always bumps and bounds that pathology.
        total_iters = 0
        _hard_iter_cap = max_read_iterations + max_tool_iterations + 15
        while (
            productive_iters < max_tool_iterations
            and read_iters < max_read_iterations
            and total_iters < _hard_iter_cap
        ):
            total_iters += 1
            # Flip back to AWAITING_RESPONSE before each LLM call. On the
            # first iteration this is a no-op (speak() already set us
            # there); on subsequent iterations we're transitioning back
            # from IN_TOOL_LOOP. _set_state is no-op on no-change so the
            # diagnostic distinction is clean.
            self._set_state(AgentState.AWAITING_RESPONSE)
            result = await self.llm.complete(
                system=system,
                messages=loop_messages,
                tools=tool_defs,
            )
            stop_reason = result.stop_reason
            content_blocks = result.raw.content if result.raw is not None else []

            if stop_reason != "tool_use":
                return result.text

            # About to execute tools — mark state so the monitor sees
            # us as still active even though we're not making LLM calls.
            self._set_state(AgentState.IN_TOOL_LOOP)
            # Extract tool_use blocks; build tool_result blocks for each.
            assistant_blocks: list[dict] = []
            tool_results: list[dict] = []
            tool_names: set[str] = set()
            # Did this turn perform any REAL (non-cached) read? A turn whose
            # reads were all cache hits did no work → it shouldn't spend a
            # read turn (see classification below).
            any_real_read = False
            for block in content_blocks:
                btype = getattr(block, "type", None)
                if btype == "text":
                    assistant_blocks.append({"type": "text", "text": block.text})
                elif btype == "tool_use":
                    tool_names.add(block.name)
                    assistant_blocks.append(
                        {
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": dict(block.input) if block.input else {},
                        }
                    )
                    try:
                        tool_input = dict(block.input) if block.input else {}
                        is_read = block.name in _READ_ONLY_TOOLS
                        cache_sig = (
                            block.name
                            + ":"
                            + json.dumps(tool_input, sort_keys=True, default=str)
                            if is_read
                            else None
                        )
                        if cache_sig is not None and cache_sig in read_cache:
                            # Identical read already served this loop — free.
                            tool_output = read_cache[cache_sig]
                        else:
                            if is_read:
                                any_real_read = True
                            tool_output = self._tools.execute(
                                block.name,
                                tool_input,
                                agent_id=self.identity.name,
                            )
                            if block.name == "write_file":
                                path = tool_input.get("path")
                                if isinstance(path, str):
                                    self._last_write_file_paths.append(path)
                                    # Invalidate-on-write: drop any cached read
                                    # of this path, plus tree/content-level
                                    # reads (list_files/grep) a write can
                                    # change. Staleness here would serve the
                                    # pre-write file — actively harmful.
                                    for k in list(read_cache):
                                        if (
                                            path in k
                                            or k.startswith("list_files:")
                                            or k.startswith("grep:")
                                        ):
                                            read_cache.pop(k, None)
                            # T-ab57: cap tool result size to prevent within-
                            # deliberation context bloat. Each tool result
                            # stays in loop_messages for all subsequent LLM
                            # calls in this deliberation (~5-13 calls typical),
                            # so an untruncated 35K grep or 65K git_diff
                            # multiplies its cost across many cache_read
                            # cycles. obol-260522-1 cost analysis: 52% of
                            # tweedle tool-result bytes were above 5K
                            # (concentrated in grep + read_file + git_diff
                            # long tail).
                            tool_output = _maybe_truncate_tool_result(
                                tool_output, block.name
                            )
                            if cache_sig is not None:
                                read_cache[cache_sig] = tool_output
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": tool_output,
                            }
                        )
                    except Exception as exc:  # ToolError + anything else
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": f"error: {exc}",
                                "is_error": True,
                            }
                        )

            # Classify the turn: a turn whose tools are ALL reads is pure
            # exploration → spend the (generous) read budget. Any write /
            # check / mixed turn is progress → spend the (tight) convergence
            # budget.
            if tool_names and tool_names <= _READ_ONLY_TOOLS:
                # Fully-cached read turn (no real read) is free — don't spend
                # a read turn on content we already had.
                if any_real_read:
                    read_iters += 1
            else:
                productive_iters += 1

            loop_messages.append({"role": "assistant", "content": assistant_blocks})
            # Force convergence as EITHER budget runs low. An agent still
            # READING this deep — the frontend Tweedle working through the
            # data-flow dependency chain, or Caterpillar reading file after
            # file as the project grows — will otherwise exhaust the read
            # budget and return "" (silence) having committed nothing. This is
            # the mechanism behind BOTH the Tweedle that never builds and
            # Caterpillar's worsens-with-scope silence. Push it to commit
            # while it still has budget to do so.
            reads_left = max_read_iterations - read_iters
            writes_left = max_tool_iterations - productive_iters
            if reads_left <= 4 or writes_left <= 3:
                tool_results.append({
                    "type": "text",
                    "text": (
                        f"[substrate] Budget nearly spent (reads_left="
                        f"{reads_left}, write_turns_left={writes_left}). STOP "
                        f"exploring — make your write_file calls now (if any) "
                        f"and then emit your FINAL response JSON. Do not request "
                        f"more reads; commit with what you have."
                    ),
                })
            loop_messages.append({"role": "user", "content": tool_results})

        # Tool budget exhausted with no final non-tool response. Returning ""
        # here drops the whole turn as silence — the failure that silently
        # ships hollow frontends and auto-approves unreviewed features. Make
        # ONE last no-tools call so the model commits whatever it gathered
        # (any write_file calls it made already landed —
        # working-tree-as-artifact). Best-effort; "" only as the true last
        # resort.
        try:
            self._set_state(AgentState.AWAITING_RESPONSE)
            loop_messages.append({
                "role": "user",
                "content": (
                    "Tool budget exhausted. Stop calling tools and emit your "
                    "FINAL response now as the JSON your protocol requires, "
                    "based on everything you've done so far."
                ),
            })
            forced = await self.llm.complete(system=system, messages=loop_messages)
            return forced.text
        except Exception:  # noqa: BLE001 — never let recovery crash the loop
            return ""

    async def _parse_with_retry(
        self,
        parse_fn: Callable[[str], _T],
        response_text: str,
        *,
        system: list,  # type: ignore[type-arg]
        messages: list,  # type: ignore[type-arg]
        max_retries: int = 3,
    ) -> _T:
        """Parse ``response_text`` with ``parse_fn``. On
        ``ResponseParseError``, retry up to ``max_retries`` times by
        re-prompting the LLM with the malformed response + a hint to
        respond with valid JSON only.

        The retry is a plain ``llm.complete`` call — no tools — because
        the goal is to recover the *structured response*, not to do more
        work. The agent already finished its tool loop (if any); this is
        purely about formatting the conclusion.

        ``max_retries`` default is 3 (4 attempts). The dominant failure
        here is the model returning an EMPTY response (Haiku, len=0 chars),
        which is transient — a retry usually recovers — but with the old
        budget of 1 retry, two empties in a row silenced the agent. That
        compounds: Tweedledee had exactly 2 implement windows on a feature,
        both came back empty, and it passed both → the frontend was never
        built (it looked like the Tweedle "refused" to work, but it just
        ran out of attempts). Same path silences Caterpillar on M8 and the
        rate climbs with context size. Extra attempts only fire on the
        failure path, so the common (clean-parse) case pays nothing.

        Returns the parsed model on success. Re-raises the parse error
        from the *final* attempt if all retries fail; the speak loop's
        existing exception handler then treats the turn as silence.

        Logs every retry attempt to stderr (success or failure) so the
        retry rate is observable from the run log.
        """
        assert self.llm is not None, "LLM must be wired to retry"
        last_exc: ResponseParseError | None = None
        # An EMPTY response (len 0) on a large context is almost always
        # deterministic — re-prompting just returns empty again, at full
        # context cost. So cap CONSECUTIVE empties at 2 (the original + one
        # retry): a transient empty still recovers, but a deterministic one
        # doesn't burn the whole max_retries budget re-sending a huge prompt
        # for nothing (the bill the frontend Tweedle was running up).
        # Malformed-but-present responses reset the counter and keep the
        # full retry budget — those recover.
        consecutive_empty = 0
        for attempt in range(max_retries + 1):
            try:
                parsed = parse_fn(response_text)
                if attempt > 0:
                    import sys

                    print(
                        f"[{self.identity.name}] parse retry succeeded on attempt "
                        f"{attempt + 1}",
                        file=sys.stderr,
                    )
                return parsed
            except ResponseParseError as exc:
                last_exc = exc
                import sys

                consecutive_empty = (
                    consecutive_empty + 1
                    if not (response_text or "").strip()
                    else 0
                )
                if consecutive_empty >= 2:
                    print(
                        f"[{self.identity.name}] {consecutive_empty} consecutive "
                        f"EMPTY responses — bailing (deterministic; not "
                        f"re-sending the full context further)",
                        file=sys.stderr,
                    )
                    raise
                if attempt >= max_retries:
                    raise

                print(
                    f"[{self.identity.name}] parse error on attempt {attempt + 1}, "
                    f"retrying: {type(exc).__name__}: {exc}",
                    file=sys.stderr,
                )
                # Build retry messages: the prior conversation + the
                # malformed assistant turn + a user hint asking for clean
                # JSON. Empty assistant content is rejected by the API,
                # so substitute a placeholder when the LLM returned "".
                retry_messages = list(messages) + [
                    {
                        "role": "assistant",
                        "content": response_text or "(empty response)",
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Your previous response could not be parsed: {exc}\n\n"
                            "Please respond again with VALID JSON ONLY matching "
                            "your response schema. No prose outside the JSON. "
                            "No tool calls — just the JSON response."
                        ),
                    },
                ]
                result = await self.llm.complete(system=system, messages=retry_messages)
                response_text = result.text
                # If the retry hit the output cap, the response is
                # almost certainly truncated mid-JSON and parse will
                # fail again with a confusing "no JSON block found".
                # Log the actual cause so the failure mode is legible.
                if getattr(result, "stop_reason", None) == "max_tokens":
                    print(
                        f"[{self.identity.name}] retry response hit "
                        f"max_tokens cap (likely truncated mid-JSON) — "
                        f"raise DEFAULT_MAX_TOKENS or shorten the agent's "
                        f"response protocol if this recurs",
                        file=sys.stderr,
                    )
        # Unreachable: max_retries=N means N+1 attempts, last one re-raises.
        raise last_exc  # type: ignore[misc]  # pragma: no cover

    def set_budget_guard(self, guard: Callable[[], bool] | None) -> None:
        """Wire (or clear) the hard budget gate. ``guard()`` returns True
        when the agent is allowed to spend on a deliberate() call. Called
        before context composition so an over-budget turn pays nothing.

        The Runner installs this for every agent during setup. Direct
        agent construction (tests, demos) leaves it unset; with no
        guard, the cap behaves as before this change (no enforcement).
        """
        self._budget_ok = guard

    async def speak(self) -> None:
        """Pull triggers, deliberate, publish + record on output.

        ``deliberate()`` exceptions are caught and treated as silence rather
        than killing the speak loop. A malformed LLM response, a cancelled
        in-flight call, or any other transient deliberation failure should
        cost one turn, not the agent's entire participation in the thread.
        ``CancelledError`` is re-raised so ``stop()`` can shut down cleanly.
        """
        while True:
            triggers = await self.gather_triggers()
            # Hard budget gate. If the team is over the cap, drop this
            # turn before we incur any LLM cost. The trigger is already
            # consumed from `pending`, so the queue doesn't grow; we
            # just don't deliberate. The Runner emits the
            # `budget_exceeded` event once when the cap is first
            # crossed, so the user sees the cause; subsequent silenced
            # turns are intentional.
            if self._budget_ok is not None and not self._budget_ok():
                continue
            # Mark active before any LLM cost is incurred. The finally
            # block restores IDLE on every exit path (publish, silence,
            # exception, late-publish suppression) so the ThreadMonitor
            # reliably sees the agent become idle exactly once per turn.
            self._set_state(AgentState.AWAITING_RESPONSE)
            # Stamp the contextvar so any LLM call inside this turn
            # gets attributed to the originating meeting/iteration.
            # Critical for parallel meetings — without this, every
            # call lands against an empty thread_id and per-meeting
            # budget checks fall back to the broken global counter.
            turn_thread_id = triggers[0].thread_id if triggers else ""
            telemetry_token = set_current_thread_id(turn_thread_id)
            try:
                context = await self.compose_context(triggers)
                try:
                    utterance = await self.deliberate(context)
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    # Drop this turn, keep the loop alive for the next trigger.
                    # Logged via stderr so the failure is visible without
                    # forcing every consumer to wire a logger.
                    import sys

                    print(
                        f"[{self.identity.name}] deliberate() raised "
                        f"{type(exc).__name__}: {exc} — treating as silence",
                        file=sys.stderr,
                    )
                    continue
                if utterance is not None:
                    # Late-publish stop-gap (roadmap 29497820): if a slow
                    # deliberation finished after its target thread closed,
                    # suppress the utterance rather than silently publishing
                    # into a settled thread. Without this, T36 v17/v18 had
                    # contract_notes landing on already-closed threads —
                    # the bus accepted them but the meeting capture had
                    # moved on, so the work was lost from the team's view.
                    if self._late_publish_handler is not None and self._late_publish_handler(
                        utterance
                    ):
                        continue
                    # P15 T-m6 stage-leak guardrail. When the meeting
                    # declared allowed_decisions, strip artifacts whose
                    # source speech_act isn't on the list + delete the
                    # on-disk files those artifacts already wrote.
                    # Suppression event surfaces in the live-watch UI
                    # so the operator can see what was caught.
                    utterance = self._apply_allowed_decisions_filter(
                        utterance
                    )
                    # Block 2c: INVITE handling. When the agent emits an
                    # INVITE addressed to specific other agents, add those
                    # agents to the thread's roster *before* publishing,
                    # so the bus delivers the invite (and all subsequent
                    # thread utterances) to them. Without this, the
                    # invitees aren't in the roster yet, so the bus
                    # filters them out and they never see the invite.
                    self._apply_invite_if_any(utterance)
                    await self.bus.publish(utterance)
                    await self.memory.record(utterance)
            finally:
                reset_current_thread_id(telemetry_token)
                self._set_state(AgentState.IDLE)

    def _apply_allowed_decisions_filter(
        self, utterance: Utterance
    ) -> Utterance:
        """P15 T-m6 stage-leak guardrail. When the meeting on this
        utterance's thread declared ``allowed_decisions``, drop the
        artifacts whose source speech_act isn't on the list — and
        delete the on-disk files those artifacts point at (registries
        like RequirementRegistry, MilestoneRegistry, TicketRegistry,
        StoryRegistry, etc. write to disk BEFORE the agent's
        deliberate returns, so we can't prevent the write; we clean
        up after).

        The utterance ITSELF stays on the bus as a transcript record
        — only its artifacts get stripped. Downstream meetings filter
        on artifacts, so a stripped utterance acts as a no-op.

        Returns the utterance unchanged when no filter applies; a
        ``model_copy(update={"content": ...})`` with empty artifacts
        when the filter caught a stage-leak.
        """
        from wonderland.workflow import (
            get_active_disallowed_decisions,
            get_thread_allowed_decisions,
        )

        if not utterance.content.artifacts:
            return utterance

        # Two filter layers compose:
        #   1. Workflow-level kill-list: speech_acts that are
        #      NEVER valid in this workflow (e.g., milestone_plan
        #      during tdd-design). Stamped at run_workflow entry.
        #   2. Meeting-level positive filter: speech_acts allowed
        #      for THIS meeting only (e.g., milestone-plan's
        #      [milestone_plan, concern, deference, silence]).
        #
        # Either filter stripping the utterance's artifacts is
        # enough — both apply if both are set.
        disallowed = get_active_disallowed_decisions()
        speech_act_str = utterance.speech_act.value
        if speech_act_str in disallowed:
            reason = (
                f"workflow disallowed_decisions = "
                f"{sorted(disallowed)!r}; "
                f"speech_act={speech_act_str!r} is forbidden in "
                "this workflow"
            )
            for art in utterance.content.artifacts:
                self._delete_artifact_file(art)
                self._emit_suppressed_event(
                    utterance=utterance,
                    artifact_kind=art.kind,
                    reason=reason,
                )
            return utterance.model_copy(
                update={
                    "content": utterance.content.model_copy(
                        update={"artifacts": []}
                    )
                }
            )

        allowed = get_thread_allowed_decisions(utterance.thread_id)
        if allowed is None:
            return utterance
        if speech_act_str in allowed:
            return utterance

        # Stage-leak detected. Walk the artifacts, attempt to delete
        # each one's backing file (best-effort — if the artifact's
        # payload doesn't carry a path, or the file is already gone,
        # skip silently). The artifact kind + agent identity ride on
        # the ArtifactSuppressed observer event so the live-watch
        # surface can show what was caught.
        reason = (
            f"meeting allowed_decisions = {sorted(allowed)!r}; "
            f"speech_act={utterance.speech_act.value!r} not on the list"
        )
        for art in utterance.content.artifacts:
            self._delete_artifact_file(art)
            self._emit_suppressed_event(
                utterance=utterance,
                artifact_kind=art.kind,
                reason=reason,
            )
        return utterance.model_copy(
            update={
                "content": utterance.content.model_copy(
                    update={"artifacts": []}
                )
            }
        )

    def _delete_artifact_file(self, artifact: Artifact) -> None:
        """Best-effort delete of an artifact's on-disk file. Reads
        ``artifact.payload['path']`` when present. Silent on every
        failure path — this is cleanup, not the critical path."""
        # Milestone files are owned EXCLUSIVELY by the milestone-plan
        # snapshot (_apply_milestone_plan_snapshot — logged + guarded).
        # The decision-filter must never delete them: an agent
        # re-emitting the milestone_plan in a later meeting that
        # disallows it — the P21 diagram-stack meeting drawing the
        # milestones, or any tdd-design meeting where milestone_plan is
        # on the kill-list — is RE-AFFIRMING the committed plan, not
        # creating a stage-leak. Deleting the backing files here wipes
        # the whole plan as a side effect (wwu 2026-06-19: the
        # diagram-stack meeting silently deleted all milestones this
        # way — directly, so not even a milestone-unlink.log entry).
        # The artifact still gets stripped from the bus by the caller;
        # only the destructive on-disk delete is skipped.
        if artifact.kind == "milestone":
            return
        if not isinstance(artifact.payload, dict):
            return
        raw_path = artifact.payload.get("path")
        if not raw_path:
            return
        try:
            from pathlib import Path

            Path(str(raw_path)).unlink()
        except OSError:
            pass

    def _emit_suppressed_event(
        self,
        *,
        utterance: Utterance,
        artifact_kind: str,
        reason: str,
    ) -> None:
        """Surface an ArtifactSuppressed event to the runner's event
        bus so the live-watch UI can show the drop. Lazy import to
        avoid the observer ↔ agent circular at module-load time."""
        from datetime import datetime, timezone

        from wonderland.observer.events import ArtifactSuppressed

        # The runner installs a callback for ad-hoc events via
        # ``self._suppressed_artifact_handler``; when nothing's wired
        # the drop is silent (tests, unit-level constructions).
        handler = getattr(
            self, "_suppressed_artifact_handler", None
        )
        if handler is None:
            return
        try:
            handler(
                ArtifactSuppressed(
                    timestamp=datetime.now(tz=timezone.utc),
                    thread_id=utterance.thread_id,
                    speech_act=utterance.speech_act.value,
                    artifact_kind=artifact_kind,
                    agent=self.identity.name,
                    reason=reason,
                )
            )
        except Exception:  # noqa: BLE001 — observability is non-critical
            pass

    def _apply_invite_if_any(self, utterance: Utterance) -> None:
        """If ``utterance`` is an INVITE with addressed_to agents, add
        them to the roster (no-op if no roster wired or thread is open).
        """
        if utterance.speech_act is not SpeechAct.INVITE:
            return
        if self._roster is None:
            return
        if self._roster.is_open(utterance.thread_id):
            # Open threads include everyone already; nothing to add.
            return
        addressed = utterance.addressed_to
        if not isinstance(addressed, list):
            return
        for invitee in addressed:
            self._roster.add_member(utterance.thread_id, invitee.name)

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    async def run(self) -> None:
        """Run both loops concurrently until cancelled."""
        self._listen_task = asyncio.create_task(self.listen(), name=f"{self.identity.name}-listen")
        self._speak_task = asyncio.create_task(self.speak(), name=f"{self.identity.name}-speak")
        with contextlib.suppress(asyncio.CancelledError):
            await asyncio.gather(self._listen_task, self._speak_task)

    # ------------------------------------------------------------------ #
    # Compaction — reflect between threads
    # ------------------------------------------------------------------ #

    async def compose_compaction_context(self, thread_id: str) -> CompactionContext:
        """Build the reflection prompt skeleton for ``thread_id``.

        Pulls the full thread from episodic memory, the agent's existing
        semantic memory and relational notes for the speakers in the
        thread (other than self), and packages them with the agent's
        constitution and compaction protocol.
        """
        history = await self.memory.query_by_thread(thread_id)
        transcript = format_transcript(history)

        speaker_names = {u.speaker.name for u in history}
        speaker_names.discard(self.identity.name)
        existing_semantic = self.memory.semantic.as_text()
        existing_relational = self.memory.relational.for_speakers(sorted(speaker_names))

        return CompactionContext(
            constitution=self.identity.constitution_text,
            protocol=self.COMPACTION_PROTOCOL,
            existing_semantic=existing_semantic,
            existing_relational=existing_relational,
            transcript=transcript,
        )

    async def compact(self, thread_id: str) -> CompactionResult:
        """Reflect on a thread in-character; persist semantic + relational updates.

        Returns an empty ``CompactionResult`` when there's nothing to
        reflect on (no LLM injected, no thread history) or when the
        agent's own reflection produces no updates.
        """
        if self.llm is None:
            return CompactionResult(thread_id=thread_id)

        context = await self.compose_compaction_context(thread_id)
        if not context.transcript:
            return CompactionResult(thread_id=thread_id)

        system, messages = context.to_llm_request()
        result = await self.llm.complete(system=system, messages=messages)
        response = parse_compaction_response(result.text)

        semantic_updated: list[str] = []
        for topic, content in response.semantic_updates.items():
            self.memory.semantic.write(topic, content)
            semantic_updated.append(topic)

        relational_updated: list[str] = []
        for name, content in response.relational_updates.items():
            self.memory.relational.write(name, content)
            relational_updated.append(name)

        return CompactionResult(
            thread_id=thread_id,
            semantic_topics_updated=tuple(semantic_updated),
            relational_agents_updated=tuple(relational_updated),
        )

    # ------------------------------------------------------------------ #
    # Lifecycle (continued)
    # ------------------------------------------------------------------ #

    async def stop(self) -> None:
        """Cancel both loops, close the bus iterator, and wait to settle."""
        for task in (self._listen_task, self._speak_task):
            if task is not None and not task.done():
                task.cancel()
        for task in (self._listen_task, self._speak_task):
            if task is not None:
                with contextlib.suppress(asyncio.CancelledError):
                    await task
        self._listen_task = None
        self._speak_task = None
        with contextlib.suppress(Exception):
            await self._bus_iterator.aclose()  # type: ignore[attr-defined]
