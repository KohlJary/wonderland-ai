"""WonderlandAgent — the base class every character subclasses.

Per WONDERLAND_SPEC §5. Wires the four primitives an agent needs to
exist on the bus: an Identity (who am I), an EpisodicStore (what have
I observed/produced), a Caucus (where do utterances live), and an
LLMClient (how do I deliberate).

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
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from wonderland.llm import CachedBlock, Message, SystemPart
from wonderland.utterance import Utterance

if TYPE_CHECKING:
    from wonderland.caucus import Caucus
    from wonderland.identity import Identity
    from wonderland.llm import LLMClient
    from wonderland.memory import EpisodicStore


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


def _format_utterance(u: Utterance) -> str:
    return f"[{u.speaker.name} — {u.speech_act.value}]\n{u.content.body}"


class WonderlandAgent:
    """Base class for every Wonderland character.

    Subclasses override ``deliberate()`` to give the character its voice.
    The default returns ``None`` (silence), which is correct for an
    agent that hasn't been told what to say.
    """

    def __init__(
        self,
        identity: Identity,
        memory: EpisodicStore,
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
        """Consume from the bus; record + queue what we engage with."""
        async for utterance in self._bus_iterator:
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

    def compose_context(self, triggers: list[Utterance]) -> Context:
        """Build the layered context for this turn.

        Default: constitution-only. P2 fills in relationships from
        relational memory, current_thread from episodic memory.
        """
        return Context(
            constitution=self.identity.constitution_text,
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
            context = self.compose_context(triggers)
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
