"""ThreadMonitor — the Dodo's eyes for structured noticing.

Per dodo.md §VI / WONDERLAND_SPEC §6. The Dodo distinguishes
**quiescence** (productive silence; the team has said what it has to
say) from **stuckness** (waiting silence; an open expectation hasn't
been picked up). Both look like "no activity," but the right Dodo
response is opposite — quiet for quiescence, nudge for stuck.

The ThreadMonitor watches the bus and tracks per-thread state. It
emits ``ThreadStateChange`` events as threads transition. The Dodo
(or any other consumer) iterates ``transitions()`` and reacts.

Detection model — first cut:

- **RUNNING → QUIESCENT**: no activity for ``quiescence_seconds`` AND
  no open expectations on the thread.
- **RUNNING → STUCK**: no activity for ``quiescence_seconds`` AND at
  least one open expectation.
- **any → COMPLETE**: an ``acknowledgment`` utterance with ``"complete"``
  in its body. (The Dodo issues these via ``acknowledge``; this lets
  the monitor close the thread when the orchestrator says so.)

An "open expectation" is a ``question``, ``concern``, ``proposal``, or
``deference`` that hasn't been engaged. Engagement heuristic for the
first cut: any subsequent utterance from a *different speaker* on the
same thread closes all open expectations from prior speakers. Loose,
but it captures the common case (Rabbit asks question, Cat answers,
question is closed). Refinement is a P5+ concern when the full cast
exposes the false-positive rate.

Deadlock (nudge-threshold-exceeded) is deferred to the conflict flow
(T19/T20). The monitor exposes ``record_nudge(thread_id)`` so the Dodo
can register them; transitions to ``DEADLOCKED`` will land alongside
escalation.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from wonderland.utterance import SpeechAct, Utterance

if TYPE_CHECKING:
    from wonderland.caucus import Caucus


_EXPECTATION_ACTS: frozenset[SpeechAct] = frozenset(
    {
        SpeechAct.QUESTION,
        SpeechAct.CONCERN,
        SpeechAct.PROPOSAL,
        SpeechAct.DEFERENCE,
    }
)


class ThreadState(StrEnum):
    RUNNING = "running"
    QUIESCENT = "quiescent"
    STUCK = "stuck"
    DEADLOCKED = "deadlocked"
    COMPLETE = "complete"
    ABANDONED = "abandoned"


@dataclass(frozen=True)
class ThreadStateChange:
    thread_id: str
    from_state: ThreadState
    to_state: ThreadState
    at: datetime
    reason: str = ""


@dataclass
class ThreadInfo:
    thread_id: str
    state: ThreadState = ThreadState.RUNNING
    last_activity: datetime = field(default_factory=lambda: datetime.now(UTC))
    utterance_count: int = 0
    open_expectations: dict[str, Utterance] = field(default_factory=dict)
    nudge_count: int = 0


class ThreadMonitor:
    """Watches the bus; emits thread-state transitions for orchestration to react to.

    Use as start/stop, with ``transitions()`` as the consumer iterator:

        monitor = ThreadMonitor(bus, quiescence_seconds=30.0)
        await monitor.start()
        try:
            async for change in monitor.transitions():
                if change.to_state is ThreadState.QUIESCENT:
                    ...
        finally:
            await monitor.stop()
    """

    def __init__(
        self,
        bus: Caucus,
        *,
        quiescence_seconds: float = 30.0,
        check_interval: float = 1.0,
        deadlock_after_nudges: int = 2,
        agent_name: str = "thread_monitor",
    ) -> None:
        self._bus = bus
        self._quiescence_seconds = quiescence_seconds
        self._check_interval = check_interval
        self._deadlock_after_nudges = deadlock_after_nudges
        self._agent_name = agent_name

        self._threads: dict[str, ThreadInfo] = {}
        # Subscribe synchronously per the WonderlandAgent fix from T14 — bus
        # publishes between construction and iteration must not be lost.
        self._iterator: AsyncIterator[Utterance] = self._bus.subscribe(agent_name)
        self._transitions: asyncio.Queue[ThreadStateChange] = asyncio.Queue()
        self._consume_task: asyncio.Task[None] | None = None
        self._timer_task: asyncio.Task[None] | None = None

    # ------------------------------------------------------------------ #
    # Inspection
    # ------------------------------------------------------------------ #

    def thread_state(self, thread_id: str) -> ThreadState:
        info = self._threads.get(thread_id)
        return info.state if info else ThreadState.RUNNING

    def thread_info(self, thread_id: str) -> ThreadInfo | None:
        return self._threads.get(thread_id)

    def known_threads(self) -> list[str]:
        return sorted(self._threads.keys())

    def record_nudge(self, thread_id: str) -> None:
        """Register that the Dodo (or anyone) issued a nudge against a thread.

        When ``nudge_count`` reaches ``deadlock_after_nudges`` and the
        thread is still STUCK, the next state check transitions to
        DEADLOCKED.
        """
        info = self._threads.setdefault(thread_id, ThreadInfo(thread_id=thread_id))
        info.nudge_count += 1

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    async def start(self) -> None:
        self._consume_task = asyncio.create_task(
            self._consume_loop(), name="thread-monitor-consume"
        )
        self._timer_task = asyncio.create_task(self._timer_loop(), name="thread-monitor-timer")

    async def stop(self) -> None:
        for task in (self._consume_task, self._timer_task):
            if task is not None and not task.done():
                task.cancel()
        for task in (self._consume_task, self._timer_task):
            if task is not None:
                with contextlib.suppress(asyncio.CancelledError):
                    await task
        self._consume_task = None
        self._timer_task = None
        with contextlib.suppress(Exception):
            await self._iterator.aclose()  # type: ignore[attr-defined]

    async def transitions(self) -> AsyncIterator[ThreadStateChange]:
        """Yield state changes as they happen. Caller iterates until cancelled."""
        while True:
            change = await self._transitions.get()
            yield change

    # ------------------------------------------------------------------ #
    # Internal loops
    # ------------------------------------------------------------------ #

    async def _consume_loop(self) -> None:
        async for utterance in self._iterator:
            self._record(utterance)
            change = self._check_completion(utterance)
            if change is not None:
                await self._transitions.put(change)

    async def _timer_loop(self) -> None:
        while True:
            await asyncio.sleep(self._check_interval)
            now = datetime.now(UTC)
            for info in list(self._threads.values()):
                change = self._check_state_after_silence(info, now)
                if change is not None:
                    await self._transitions.put(change)

    # ------------------------------------------------------------------ #
    # State machine
    # ------------------------------------------------------------------ #

    def _record(self, u: Utterance) -> None:
        info = self._threads.setdefault(u.thread_id, ThreadInfo(thread_id=u.thread_id))
        info.last_activity = u.timestamp
        info.utterance_count += 1

        # Engagement heuristic: any utterance from a different speaker than
        # an open expectation closes that expectation.
        for expect_id, expect in list(info.open_expectations.items()):
            if expect.id == u.id:
                continue
            if expect.speaker.name != u.speaker.name:
                del info.open_expectations[expect_id]

        # If this utterance itself raises an expectation, track it.
        if u.speech_act in _EXPECTATION_ACTS:
            info.open_expectations[u.id] = u

        # Any new activity on a previously-non-running thread should reset
        # state to RUNNING — the team came back. This avoids a quiescent
        # thread staying quiescent forever once someone speaks again.
        if info.state in (ThreadState.QUIESCENT, ThreadState.STUCK):
            previous = info.state
            info.state = ThreadState.RUNNING
            # Note: we don't emit a transition for this — the next silence
            # check will re-evaluate. Future enhancement: emit RUNNING
            # transitions if a consumer cares.
            _ = previous

    def _check_completion(self, u: Utterance) -> ThreadStateChange | None:
        if u.speech_act is not SpeechAct.ACKNOWLEDGMENT:
            return None
        if "complete" not in u.content.body.lower():
            return None
        info = self._threads.get(u.thread_id)
        if info is None or info.state is ThreadState.COMPLETE:
            return None
        return self._transition(info, ThreadState.COMPLETE, "acknowledgment of completion")

    def _check_state_after_silence(
        self, info: ThreadInfo, now: datetime
    ) -> ThreadStateChange | None:
        if info.state in (ThreadState.COMPLETE, ThreadState.ABANDONED):
            return None
        elapsed = (now - info.last_activity).total_seconds()
        if elapsed < self._quiescence_seconds:
            return None

        if info.open_expectations:
            # Stuck — and possibly deadlocked if nudge threshold exceeded.
            if info.state is ThreadState.STUCK and info.nudge_count >= self._deadlock_after_nudges:
                return self._transition(
                    info,
                    ThreadState.DEADLOCKED,
                    f"{info.nudge_count} nudges, still {len(info.open_expectations)} open",
                )
            if info.state is not ThreadState.STUCK:
                return self._transition(
                    info,
                    ThreadState.STUCK,
                    f"{len(info.open_expectations)} open expectation(s); silent {elapsed:.1f}s",
                )
            return None

        if info.state is not ThreadState.QUIESCENT:
            return self._transition(
                info,
                ThreadState.QUIESCENT,
                f"no open expectations; silent {elapsed:.1f}s",
            )
        return None

    def _transition(
        self, info: ThreadInfo, to_state: ThreadState, reason: str
    ) -> ThreadStateChange:
        from_state = info.state
        info.state = to_state
        return ThreadStateChange(
            thread_id=info.thread_id,
            from_state=from_state,
            to_state=to_state,
            at=datetime.now(UTC),
            reason=reason,
        )


__all__ = [
    "ThreadInfo",
    "ThreadMonitor",
    "ThreadState",
    "ThreadStateChange",
]
