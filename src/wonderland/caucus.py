"""Caucus — the event bus through which all agents communicate.

Per WONDERLAND_SPEC §3 / D-003. Append-only, ordered, fan-out. Every
agent communication is published as an Utterance; subscribers receive
the stream of utterances filtered by their interests and (optionally) a
specific thread.

Two implementations land here:

- ``RedisCaucus`` — production. One stream per project, consumer groups
  per agent so each agent can keep its own position. Filtering by
  thread_id and interests happens client-side after deserialization;
  the bus stays generic and serializes the spec faithfully. Requires
  the optional ``redis`` extra (``pip install 'wonderland[redis]'``).
- ``InMemoryCaucus`` — pure-asyncio fan-out for unit tests. Same
  interface, no infrastructure required.

The protocol defines what an agent sees; the implementations differ
only in where the messages live.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Protocol

from pydantic import ValidationError

from wonderland.roster import ThreadRoster
from wonderland.utterance import SpeechAct, Utterance

try:
    import redis.exceptions as _redis_exc

    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False

if TYPE_CHECKING:
    from redis.asyncio import Redis


DEFAULT_STREAM = "wonderland:utterances"
_DATA_FIELD = "data"
_ALL_ACTS: frozenset[SpeechAct] = frozenset(SpeechAct)
_REDIS_INSTALL_HINT = (
    "RedisCaucus requires the redis package. Install with: "
    "pip install 'wonderland[redis]' (or `uv sync --extra redis`)."
)


class Caucus(Protocol):
    """The bus. Publishers add utterances; subscribers consume them."""

    async def publish(self, utterance: Utterance) -> str:
        """Append `utterance` to the bus. Returns the bus-assigned entry id."""
        ...

    def subscribe(
        self,
        agent_name: str,
        interests: frozenset[SpeechAct] = _ALL_ACTS,
        thread_id: str | None = None,
        *,
        from_beginning: bool = False,
        bypass_roster: bool = False,
    ) -> AsyncIterator[Utterance]:
        """Yield utterances matching `interests` (and optionally `thread_id`).

        `agent_name` identifies the subscriber so each agent can keep its
        own independent position in the stream — two agents subscribing
        with the same `agent_name` share a position.

        `bypass_roster=True` is for framework observers (ThreadMonitor,
        ConsensusGuard, the Runner's bus observer) that need to see
        every utterance regardless of per-thread roster filtering. Agent
        subscribers leave it False so the roster's per-thread membership
        check applies.
        """
        ...


# --------------------------------------------------------------------- #
# Redis implementation
# --------------------------------------------------------------------- #


def _coerce_str(value: str | bytes) -> str:
    return value.decode() if isinstance(value, bytes) else value


class RedisCaucus:
    """Caucus backed by Redis Streams.

    `client` is an `redis.asyncio.Redis` instance; the Caucus does not
    own its lifecycle. `stream` is the key under which utterances are
    appended — one stream per project namespace.
    """

    def __init__(self, client: Redis, *, stream: str = DEFAULT_STREAM) -> None:
        if not _REDIS_AVAILABLE:
            raise ImportError(_REDIS_INSTALL_HINT)
        self._client = client
        self._stream = stream

    async def publish(self, utterance: Utterance) -> str:
        entry_id = await self._client.xadd(
            self._stream,
            {_DATA_FIELD: utterance.model_dump_json()},
        )
        return _coerce_str(entry_id)

    async def _ensure_group(self, agent_name: str, *, from_beginning: bool) -> None:
        # ResponseError with a "BUSYGROUP" message means the group already
        # exists — the desired idempotent outcome.
        try:
            await self._client.xgroup_create(
                name=self._stream,
                groupname=agent_name,
                id="0" if from_beginning else "$",
                mkstream=True,
            )
        except _redis_exc.ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    async def subscribe(
        self,
        agent_name: str,
        interests: frozenset[SpeechAct] = _ALL_ACTS,
        thread_id: str | None = None,
        *,
        from_beginning: bool = False,
        bypass_roster: bool = False,
        block_ms: int = 5000,
        batch: int = 16,
    ) -> AsyncIterator[Utterance]:
        # bypass_roster is accepted for protocol parity but ignored
        # here — the Redis backend doesn't yet support roster-aware
        # delivery (server-side filtering would require a stream-per-
        # thread or per-agent topology). Revisit when distributed
        # rosters are needed.
        _ = bypass_roster
        await self._ensure_group(agent_name, from_beginning=from_beginning)
        consumer = agent_name

        while True:
            response = await self._client.xreadgroup(
                groupname=agent_name,
                consumername=consumer,
                streams={self._stream: ">"},
                count=batch,
                block=block_ms,
            )
            if not response:
                continue

            for _stream_name, entries in response:
                for entry_id, fields in entries:
                    utterance = self._decode_entry(fields)
                    # Always ack — even if we drop the message, we don't want
                    # it redelivered. Filtering is the subscriber's choice.
                    await self._client.xack(self._stream, agent_name, entry_id)
                    if utterance is None:
                        continue
                    if thread_id is not None and utterance.thread_id != thread_id:
                        continue
                    if utterance.speech_act not in interests:
                        continue
                    yield utterance

    @staticmethod
    def _decode_entry(fields: dict[bytes | str, bytes | str]) -> Utterance | None:
        raw = fields.get(_DATA_FIELD.encode()) or fields.get(_DATA_FIELD)
        if raw is None:
            return None
        try:
            return Utterance.model_validate_json(_coerce_str(raw))
        except ValidationError:
            return None


# --------------------------------------------------------------------- #
# In-memory implementation
# --------------------------------------------------------------------- #


class InMemoryCaucus:
    """Pure-asyncio fan-out Caucus for unit tests.

    Every subscriber gets its own queue; publish puts the utterance on
    every active queue. Filtering happens in the subscribe loop, mirroring
    the Redis implementation.

    Registration is synchronous: ``subscribe()`` adds the queue to the
    subscriber set before returning the async iterator, so a subscriber
    created before a ``publish()`` is guaranteed to receive that publish
    even if the iterator hasn't been advanced yet. Asyncio is
    single-threaded, so no lock is needed around the subscriber set as
    long as no ``await`` is interleaved between read and write.
    """

    def __init__(self, roster: ThreadRoster | None = None) -> None:
        self._history: list[Utterance] = []
        self._subscribers: dict[str, list[asyncio.Queue[Utterance]]] = {}
        # Names that bypass roster filtering on publish — framework
        # observers (ThreadMonitor, ConsensusGuard, Runner observer)
        # need every utterance regardless of per-thread roster.
        self._bypass_roster: set[str] = set()
        self._counter = 0
        # Optional ThreadRoster gates delivery per-thread. When None,
        # every utterance fans out to every subscriber (the original
        # behavior; what existing demos and tests depend on). When set,
        # only roster members of the utterance's thread receive it.
        # Open threads (threads the roster doesn't know about) still
        # fan out to everyone, so a partial roster setup doesn't break
        # untouched threads.
        self._roster = roster

    @property
    def history(self) -> list[Utterance]:
        return list(self._history)

    async def publish(self, utterance: Utterance) -> str:
        self._counter += 1
        entry_id = f"0-{self._counter}"
        self._history.append(utterance)
        for sub_name, queues in list(self._subscribers.items()):
            if (
                self._roster is not None
                and sub_name not in self._bypass_roster
                and not self._roster.is_member(utterance.thread_id, sub_name)
            ):
                continue
            for queue in queues:
                queue.put_nowait(utterance)
        return entry_id

    def subscribe(
        self,
        agent_name: str,
        interests: frozenset[SpeechAct] = _ALL_ACTS,
        thread_id: str | None = None,
        *,
        from_beginning: bool = False,
        bypass_roster: bool = False,
    ) -> AsyncIterator[Utterance]:
        queue: asyncio.Queue[Utterance] = asyncio.Queue()
        if from_beginning:
            for past in self._history:
                queue.put_nowait(past)
        self._subscribers.setdefault(agent_name, []).append(queue)
        if bypass_roster:
            self._bypass_roster.add(agent_name)
        return self._consume(queue, agent_name, interests, thread_id)

    async def _consume(
        self,
        queue: asyncio.Queue[Utterance],
        agent_name: str,
        interests: frozenset[SpeechAct],
        thread_id: str | None,
    ) -> AsyncIterator[Utterance]:
        try:
            while True:
                utterance = await queue.get()
                if thread_id is not None and utterance.thread_id != thread_id:
                    continue
                if utterance.speech_act not in interests:
                    continue
                yield utterance
        finally:
            with contextlib.suppress(ValueError, KeyError):
                self._subscribers[agent_name].remove(queue)
                if not self._subscribers[agent_name]:
                    del self._subscribers[agent_name]
