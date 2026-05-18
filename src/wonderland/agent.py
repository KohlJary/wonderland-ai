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

    async def compose_context(self, triggers: list[Utterance]) -> Context:
        """Build the layered context for this turn.

        Constitution comes from the identity (invariant, cached).
        Relationships are pulled from relational memory for the speakers
        we're seeing in this turn (cached if non-empty — slow-changing).
        Current-thread history is read from episodic memory and
        rendered as a chronological transcript (uncached — changes
        every turn). Triggers themselves are excluded from the
        transcript since they're presented separately as the immediate
        stimulus.
        """
        thread_text = ""
        relationships_text = ""
        engagement_state = ""
        if triggers:
            thread_id = triggers[0].thread_id
            history = await self.memory.query_by_thread(thread_id)
            trigger_ids = {t.id for t in triggers}
            history_excluding_triggers = [u for u in history if u.id not in trigger_ids]
            thread_text = format_transcript(history_excluding_triggers)

            speaker_names: set[str] = {t.speaker.name for t in triggers}
            for past in history_excluding_triggers:
                speaker_names.add(past.speaker.name)
            speaker_names.discard(self.identity.name)
            relationships_text = self.memory.relational.for_speakers(sorted(speaker_names))

            engagement_state = self._build_engagement_state(thread_id, history)

        return Context(
            constitution=self.identity.constitution_text,
            relationships=relationships_text,
            current_thread=thread_text,
            triggers=tuple(triggers),
            engagement_state=engagement_state,
        )

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
        max_tool_iterations: int = 20,
    ) -> str:
        """Tool-use loop. Calls the LLM with tools=[...]; if the response
        is a tool_use, executes the tools, appends results, calls again.
        Returns the final text response when the LLM stops requesting tools.

        ``max_tool_iterations`` caps the loop to prevent runaway tool use
        on a malformed prompt. Subclasses' protocols ask for a final
        JSON response; if the LLM iterates past the cap without producing
        one, this returns "" so the parser raises and the speak loop
        treats it as silence.

        Bumped from 10 → 20 in T38 Session 2 diagnostics: continuation-
        session Tweedles legitimately needed more reads (read existing
        models.py + messages.py + users.py + schemas.py + tests + git_diff
        to understand what already shipped) before designing the diff.
        At 10 iterations they'd exhaust on read_file calls and never
        emit the final JSON. Risk of feedback loops is low — the
        toolset (read/write/list/grep/git_status/git_diff) is local-
        only with no network / process-spawning paths.

        Side effect: ``self._last_write_file_paths`` is reset at entry
        and populated as ``write_file`` tool calls succeed. Subclasses
        can read it after parsing to coerce decisions when the LLM
        writes files but picks a non-implementation utterance.
        """
        assert self._tools is not None, "set_tools must have been called"
        assert self.llm is not None
        self._last_write_file_paths = []
        tool_defs = self._tools.tool_definitions()

        # Working copy of messages we'll extend with assistant + tool_result
        # turns. The caller's `messages` is preserved.
        loop_messages = list(messages)

        for _ in range(max_tool_iterations):
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
            for block in content_blocks:
                btype = getattr(block, "type", None)
                if btype == "text":
                    assistant_blocks.append({"type": "text", "text": block.text})
                elif btype == "tool_use":
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
                        tool_output = self._tools.execute(
                            block.name,
                            tool_input,
                            agent_id=self.identity.name,
                        )
                        if block.name == "write_file":
                            path = tool_input.get("path")
                            if isinstance(path, str):
                                self._last_write_file_paths.append(path)
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

            loop_messages.append({"role": "assistant", "content": assistant_blocks})
            loop_messages.append({"role": "user", "content": tool_results})

        return ""

    async def _parse_with_retry(
        self,
        parse_fn: Callable[[str], _T],
        response_text: str,
        *,
        system: list,  # type: ignore[type-arg]
        messages: list,  # type: ignore[type-arg]
        max_retries: int = 1,
    ) -> _T:
        """Parse ``response_text`` with ``parse_fn``. On
        ``ResponseParseError``, retry once by re-prompting the LLM with
        the malformed response + a hint to respond with valid JSON only.

        The retry is a plain ``llm.complete`` call — no tools — because
        the goal is to recover the *structured response*, not to do more
        work. The agent already finished its tool loop (if any); this is
        purely about formatting the conclusion.

        Returns the parsed model on success. Re-raises the parse error
        from the *final* attempt if all retries fail; the speak loop's
        existing exception handler then treats the turn as silence.

        Logs every retry attempt to stderr (success or failure) so the
        retry rate is observable from the run log.
        """
        assert self.llm is not None, "LLM must be wired to retry"
        last_exc: ResponseParseError | None = None
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
                if attempt >= max_retries:
                    raise
                import sys

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
