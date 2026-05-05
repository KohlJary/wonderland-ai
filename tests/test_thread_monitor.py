"""Tests for ThreadMonitor — quiescence + stuck + deadlock detection."""

from __future__ import annotations

import asyncio
import contextlib

import pytest

from wonderland import (
    AgentIdentity,
    InMemoryCaucus,
    SpeechAct,
    ThreadMonitor,
    ThreadState,
    Utterance,
    UtteranceContent,
)

# ---------- helpers ----------


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


async def _drain_until(monitor: ThreadMonitor, *, count: int, timeout: float = 2.0):
    """Collect `count` transitions or raise TimeoutError."""
    iterator = monitor.transitions()
    out = []
    for _ in range(count):
        change = await asyncio.wait_for(anext(iterator), timeout=timeout)
        out.append(change)
    return out


# ---------- inspection ----------


async def test_unknown_thread_state_is_running() -> None:
    bus = InMemoryCaucus()
    monitor = ThreadMonitor(bus)
    assert monitor.thread_state("nonexistent") is ThreadState.RUNNING
    assert monitor.thread_info("nonexistent") is None


async def test_known_threads_returned_after_activity() -> None:
    bus = InMemoryCaucus()
    monitor = ThreadMonitor(bus, quiescence_seconds=10.0)
    await monitor.start()
    await bus.publish(_u(thread_id="alpha"))
    await bus.publish(_u(thread_id="beta"))
    await asyncio.sleep(0.05)
    assert sorted(monitor.known_threads()) == ["alpha", "beta"]
    await monitor.stop()


# ---------- quiescence ----------


async def test_quiescence_fires_after_silence_with_no_open_expectations() -> None:
    bus = InMemoryCaucus()
    monitor = ThreadMonitor(bus, quiescence_seconds=0.1, check_interval=0.05)
    await monitor.start()

    # An acknowledgment doesn't create an open expectation.
    await bus.publish(_u(act=SpeechAct.ACKNOWLEDGMENT, body="thread t → running"))

    [change] = await _drain_until(monitor, count=1)
    assert change.thread_id == "t"
    assert change.from_state is ThreadState.RUNNING
    assert change.to_state is ThreadState.QUIESCENT
    assert "no open expectations" in change.reason

    await monitor.stop()


async def test_stuck_fires_when_open_expectation_with_silence() -> None:
    """A question with no cross-speaker engagement → stuck after silence."""
    bus = InMemoryCaucus()
    monitor = ThreadMonitor(bus, quiescence_seconds=0.1, check_interval=0.05)
    await monitor.start()

    # Question opens an expectation; nobody answers.
    await bus.publish(_u(act=SpeechAct.QUESTION, body="by when?", speaker="white_rabbit"))

    [change] = await _drain_until(monitor, count=1)
    assert change.to_state is ThreadState.STUCK
    assert "open expectation" in change.reason

    await monitor.stop()


async def test_cross_speaker_engagement_closes_open_expectation() -> None:
    """Question from Rabbit + non-expectation response from Cat → quiescent.

    The Cat's response must be a non-expectation act (reframe,
    acknowledgment, etc.) — a proposal would close the original
    question but immediately open a new expectation, leaving the
    thread STUCK rather than QUIESCENT.
    """
    bus = InMemoryCaucus()
    monitor = ThreadMonitor(bus, quiescence_seconds=0.1, check_interval=0.05)
    await monitor.start()

    await bus.publish(_u(act=SpeechAct.QUESTION, speaker="white_rabbit"))
    await bus.publish(_u(act=SpeechAct.REFRAME, speaker="cheshire_cat", body="ask instead: ..."))

    [change] = await _drain_until(monitor, count=1)
    assert change.to_state is ThreadState.QUIESCENT


async def test_cross_speaker_proposal_closes_question_but_opens_new_expectation() -> None:
    """Cat's proposal closes the Rabbit's question but opens its own expectation.

    Demonstrates the chained-expectation behavior — substantive
    multi-turn dance keeps the thread in expectation-bearing state
    until something settles.
    """
    bus = InMemoryCaucus()
    monitor = ThreadMonitor(bus, quiescence_seconds=0.1, check_interval=0.05)
    await monitor.start()

    await bus.publish(_u(act=SpeechAct.QUESTION, speaker="white_rabbit"))
    await bus.publish(_u(act=SpeechAct.PROPOSAL, speaker="cheshire_cat", body="here's the call"))

    [change] = await _drain_until(monitor, count=1)
    # The proposal opens a new expectation; thread is stuck waiting on engagement
    assert change.to_state is ThreadState.STUCK


async def test_same_speaker_does_not_close_own_expectation() -> None:
    """The Cat asking a question and the Cat speaking again doesn't resolve it."""
    bus = InMemoryCaucus()
    monitor = ThreadMonitor(bus, quiescence_seconds=0.1, check_interval=0.05)
    await monitor.start()

    await bus.publish(_u(act=SpeechAct.QUESTION, speaker="cheshire_cat"))
    await bus.publish(_u(act=SpeechAct.QUESTION, speaker="cheshire_cat", body="and another"))

    [change] = await _drain_until(monitor, count=1)
    assert change.to_state is ThreadState.STUCK


# ---------- completion ----------


async def test_completion_fires_on_acknowledgment_with_complete() -> None:
    bus = InMemoryCaucus()
    monitor = ThreadMonitor(bus, quiescence_seconds=10.0, check_interval=0.05)
    await monitor.start()

    await bus.publish(_u(speaker="dodo", act=SpeechAct.ACKNOWLEDGMENT, body="Thread t → complete."))

    [change] = await _drain_until(monitor, count=1)
    assert change.to_state is ThreadState.COMPLETE
    assert "acknowledgment" in change.reason

    await monitor.stop()


async def test_completion_does_not_double_emit() -> None:
    bus = InMemoryCaucus()
    monitor = ThreadMonitor(bus, quiescence_seconds=10.0, check_interval=0.05)
    await monitor.start()

    await bus.publish(_u(speaker="dodo", act=SpeechAct.ACKNOWLEDGMENT, body="t → complete"))
    await bus.publish(
        _u(speaker="dodo", act=SpeechAct.ACKNOWLEDGMENT, body="another complete note")
    )

    [first] = await _drain_until(monitor, count=1)
    assert first.to_state is ThreadState.COMPLETE

    # No second transition arrives within a short window
    iterator = monitor.transitions()
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(anext(iterator), timeout=0.2)

    await monitor.stop()


# ---------- deadlock ----------


async def test_deadlock_after_nudge_threshold() -> None:
    """STUCK → DEADLOCKED when nudge_count meets threshold."""
    bus = InMemoryCaucus()
    monitor = ThreadMonitor(
        bus,
        quiescence_seconds=0.1,
        check_interval=0.05,
        deadlock_after_nudges=2,
    )
    await monitor.start()

    # First open expectation → stuck
    await bus.publish(_u(act=SpeechAct.QUESTION))
    [first] = await _drain_until(monitor, count=1)
    assert first.to_state is ThreadState.STUCK

    # Two nudges registered, still no engagement → deadlocked on next check
    monitor.record_nudge("t")
    monitor.record_nudge("t")

    [second] = await _drain_until(monitor, count=1)
    assert second.from_state is ThreadState.STUCK
    assert second.to_state is ThreadState.DEADLOCKED

    await monitor.stop()


# ---------- multi-thread isolation ----------


async def test_threads_tracked_independently() -> None:
    bus = InMemoryCaucus()
    monitor = ThreadMonitor(bus, quiescence_seconds=0.1, check_interval=0.05)
    await monitor.start()

    await bus.publish(_u(thread_id="alpha", act=SpeechAct.ACKNOWLEDGMENT, body="..."))
    await bus.publish(_u(thread_id="beta", act=SpeechAct.QUESTION, body="?"))

    seen: dict[str, ThreadState] = {}
    iterator = monitor.transitions()
    while {"alpha", "beta"} - set(seen.keys()):
        change = await asyncio.wait_for(anext(iterator), timeout=2.0)
        seen[change.thread_id] = change.to_state

    assert seen["alpha"] is ThreadState.QUIESCENT
    assert seen["beta"] is ThreadState.STUCK

    await monitor.stop()


# ---------- activity revives non-running threads ----------


async def test_new_activity_revives_quiescent_thread() -> None:
    """A QUIESCENT thread that gets new activity should re-evaluate, not stay stuck."""
    bus = InMemoryCaucus()
    monitor = ThreadMonitor(bus, quiescence_seconds=0.1, check_interval=0.05)
    await monitor.start()

    await bus.publish(_u(act=SpeechAct.ACKNOWLEDGMENT, body="..."))
    [first] = await _drain_until(monitor, count=1)
    assert first.to_state is ThreadState.QUIESCENT

    # New utterance arrives — thread reverts to RUNNING (silently, no emit yet)
    # and the next silence check should re-emit QUIESCENT.
    await bus.publish(_u(act=SpeechAct.ACKNOWLEDGMENT, body="..."))
    [second] = await _drain_until(monitor, count=1)
    assert second.from_state is ThreadState.RUNNING
    assert second.to_state is ThreadState.QUIESCENT

    await monitor.stop()


# ---------- lifecycle ----------


async def test_stop_cancels_background_tasks() -> None:
    bus = InMemoryCaucus()
    monitor = ThreadMonitor(bus, quiescence_seconds=10.0)
    await monitor.start()
    assert monitor._consume_task is not None
    assert monitor._timer_task is not None
    await monitor.stop()
    assert monitor._consume_task is None
    assert monitor._timer_task is None


async def test_stop_is_safe_when_never_started() -> None:
    bus = InMemoryCaucus()
    monitor = ThreadMonitor(bus)
    # Should not raise
    await monitor.stop()


# ---------- integration: monitor + Dodo.relay/acknowledge ----------


async def test_monitor_observes_dodo_relay_and_ack(tmp_path) -> None:
    """End-to-end: Dodo relays directive, ack completion, monitor sees both."""
    from pathlib import Path

    from wonderland import AgentMemory, Dodo

    _ = Path  # quiet unused import

    bus = InMemoryCaucus()
    memory = AgentMemory.for_project(tmp_path, "dodo")
    await memory.open()

    dodo = Dodo(memory=memory, bus=bus, llm=None)
    monitor = ThreadMonitor(bus, quiescence_seconds=0.1, check_interval=0.05)
    await monitor.start()

    await dodo.relay_directive(body="Build a thing.", thread_id="t")
    await dodo.acknowledge("t", state="complete")

    # We should see at least one transition — completion, possibly preceded by
    # quiescence depending on timing. Drain until we get COMPLETE.
    iterator = monitor.transitions()
    final: ThreadState | None = None
    for _ in range(3):
        with contextlib.suppress(TimeoutError):
            change = await asyncio.wait_for(anext(iterator), timeout=0.5)
            if change.to_state is ThreadState.COMPLETE:
                final = change.to_state
                break
    assert final is ThreadState.COMPLETE

    await monitor.stop()
    await memory.close()
