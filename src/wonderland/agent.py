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
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, ValidationError

from wonderland.llm import CachedBlock, Message, SystemPart
from wonderland.utterance import Utterance

if TYPE_CHECKING:
    from wonderland.caucus import Caucus
    from wonderland.identity import Identity
    from wonderland.llm import LLMClient
    from wonderland.memory import AgentMemory


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

    def to_llm_request(self) -> tuple[list[SystemPart], list[Message]]:
        """Convert this context into ``LLMClient.complete()`` arguments.

        Constitution and relationships become cached system prefixes (the
        invariant + slow-changing layers). Current thread and triggers go
        into the uncached tail. Triggers are joined into a single user
        message — when the trigger set is multiple utterances the agent
        sees them as a batched stimulus.
        """
        system: list[SystemPart] = [CachedBlock(self.constitution)]
        if self.relationships:
            system.append(CachedBlock(self.relationships))
        if self.current_thread:
            system.append(self.current_thread)

        trigger_text = "\n\n".join(_format_utterance(u) for u in self.triggers)
        messages: list[Message] = [{"role": "user", "content": trigger_text or "(no trigger)"}]
        return system, messages


def format_utterance(u: Utterance) -> str:
    """Render one utterance as a labeled text block for prompt inclusion."""
    return f"[{u.speaker.name} — {u.speech_act.value}]\n{u.content.body}"


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
            if utterance.speaker.name == self.identity.name:
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

        return Context(
            constitution=self.identity.constitution_text,
            relationships=relationships_text,
            current_thread=thread_text,
            triggers=tuple(triggers),
        )

    async def deliberate(self, context: Context) -> Utterance | None:
        """Decide what to say. Return ``None`` for silence.

        The base default is silence. Subclasses override to call
        ``self.llm.complete(...)`` with the assembled context and
        produce an Utterance.
        """
        return None

    async def speak(self) -> None:
        """Pull triggers, deliberate, publish + record on output."""
        while True:
            triggers = await self.gather_triggers()
            context = await self.compose_context(triggers)
            utterance = await self.deliberate(context)
            if utterance is not None:
                await self.bus.publish(utterance)
                await self.memory.record(utterance)

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
