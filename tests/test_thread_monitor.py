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


# ---------- T69: pause for external input ----------


async def test_pause_for_external_input_suppresses_wall_clock_quiescence() -> None:
    """While a thread is paused (awaiting operator answer to a
    QUESTION-to-operator), wall-clock quiescence must not fire even
    though the thread has gone silent past quiescence_seconds."""
    bus = InMemoryCaucus()
    monitor = ThreadMonitor(bus, quiescence_seconds=0.1, check_interval=0.05)
    await monitor.start()

    await bus.publish(_u(act=SpeechAct.ACKNOWLEDGMENT, body="thread t → running"))
    monitor.pause_for_external_input("t")

    # Wait well past quiescence_seconds — without the pause, this
    # would have produced a QUIESCENT transition.
    await asyncio.sleep(0.3)

    # Verify pause held: no transition delivered yet.
    iterator = monitor.transitions()
    with contextlib.suppress(TimeoutError):
        change = await asyncio.wait_for(anext(iterator), timeout=0.1)
        # If we got here, the pause failed.
        raise AssertionError(
            f"quiescence fired despite pause: {change.to_state.value}"
        )

    # Resume — quiescence is now allowed; with continued silence,
    # the next wall-clock tick should fire it.
    monitor.resume_for_external_input("t")
    [change] = await _drain_until(monitor, count=1)
    assert change.to_state is ThreadState.QUIESCENT

    await monitor.stop()


async def test_pause_resume_is_idempotent() -> None:
    """Pausing or resuming the same thread twice is harmless."""
    bus = InMemoryCaucus()
    monitor = ThreadMonitor(bus)
    monitor.pause_for_external_input("t")
    monitor.pause_for_external_input("t")
    assert monitor.is_paused_for_external_input("t")
    monitor.resume_for_external_input("t")
    monitor.resume_for_external_input("t")
    assert not monitor.is_paused_for_external_input("t")


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


async def test_idle_keyed_quiescence_blocked_until_member_engages() -> None:
    """A freshly-convened thread must not quiesce just because its
    roster members are IDLE. Without this gate, a member finishing a
    turn on a different thread (going IDLE) would instantly quiesce
    any other thread they're in — including ones that just opened.

    Regression for the M5-immediate-quiescence pattern documented in
    analysis 027: M4 budget cap → M5 convene → M4's last agent goes
    IDLE → M5 transitions RUNNING → QUIESCENT → COMPLETE in 0s before
    any agent reads the M5 directive.
    """
    from wonderland.agent import AgentState
    from wonderland.roster import ThreadRoster

    bus = InMemoryCaucus()
    roster = ThreadRoster()
    roster.register(
        "implementation",
        members={"tweedledee", "tweedledum", "dodo"},
        goal="ship it",
        convenor="dodo",
    )
    monitor = ThreadMonitor(
        bus, roster=roster, quiescence_seconds=10.0, check_interval=10.0
    )
    await monitor.start()

    # Convenor publishes the directive. Thread now has utterance_count=1
    # but member_engagements=0 — no roster member has acted yet.
    await bus.publish(
        _u(thread_id="implementation", speaker="dodo", act=SpeechAct.DIRECTIVE)
    )
    await asyncio.sleep(0.05)

    # Simulate Tweedles being mid-turn on a different thread, then
    # going IDLE as that turn finishes. record_agent_state only fires
    # the quiescence check on a *transition* to IDLE, so we have to
    # flip them to AWAITING_RESPONSE first to make IDLE a real change.
    monitor.record_agent_state("tweedledum", AgentState.AWAITING_RESPONSE)
    monitor.record_agent_state("tweedledee", AgentState.AWAITING_RESPONSE)
    monitor.record_agent_state("tweedledum", AgentState.IDLE)
    monitor.record_agent_state("tweedledee", AgentState.IDLE)

    # Give the monitor a moment to process. Nothing should fire — the
    # implementation thread is RUNNING with zero member engagements.
    await asyncio.sleep(0.05)

    info = monitor.thread_info("implementation")
    assert info is not None
    assert info.state is ThreadState.RUNNING, (
        "thread must stay RUNNING when only the convenor has spoken — "
        "without member engagement, quiescence is premature"
    )
    assert info.member_engagements == 0

    await monitor.stop()


async def test_idle_keyed_quiescence_fires_after_member_engages() -> None:
    """Complementary pin: once a roster member engages, the IDLE-keyed
    quiescence check works as before. The gate from the prior test
    only blocks before-engagement, not after.
    """
    from wonderland.agent import AgentState
    from wonderland.roster import ThreadRoster

    bus = InMemoryCaucus()
    roster = ThreadRoster()
    roster.register(
        "t",
        members={"alice", "white_rabbit", "dodo"},
        goal="g",
        convenor="dodo",
    )
    monitor = ThreadMonitor(
        bus, roster=roster, quiescence_seconds=10.0, check_interval=10.0
    )
    await monitor.start()

    # Directive lands; no engagement yet.
    await bus.publish(_u(thread_id="t", speaker="dodo", act=SpeechAct.DIRECTIVE))
    # A roster member emits a non-expectation act — engagement registered.
    await bus.publish(
        _u(thread_id="t", speaker="alice", act=SpeechAct.ACKNOWLEDGMENT)
    )
    await asyncio.sleep(0.05)

    info = monitor.thread_info("t")
    assert info is not None
    assert info.member_engagements == 1

    # Now the team goes IDLE; quiescence should fire. Flip to
    # AWAITING_RESPONSE first so IDLE is a real transition.
    monitor.record_agent_state("white_rabbit", AgentState.AWAITING_RESPONSE)
    monitor.record_agent_state("alice", AgentState.AWAITING_RESPONSE)
    monitor.record_agent_state("white_rabbit", AgentState.IDLE)
    monitor.record_agent_state("alice", AgentState.IDLE)

    [change] = await _drain_until(monitor, count=1)
    assert change.thread_id == "t"
    assert change.to_state is ThreadState.QUIESCENT

    await monitor.stop()


async def test_seeds_do_not_count_as_engagement() -> None:
    """Seeds replayed from a prior meeting carry the original speaker's
    identity but is_seed=True. They populate context, they don't
    represent new work on the current thread, so they must not unlock
    the quiescence gate.
    """
    from wonderland.agent import AgentState
    from wonderland.roster import ThreadRoster

    bus = InMemoryCaucus()
    roster = ThreadRoster()
    roster.register(
        "t",
        members={"alice", "white_rabbit", "dodo"},
        goal="g",
        convenor="dodo",
    )
    monitor = ThreadMonitor(
        bus, roster=roster, quiescence_seconds=10.0, check_interval=10.0
    )
    await monitor.start()

    # Seed from a roster member — re-stamped from a prior meeting.
    seed = Utterance(
        thread_id="t",
        speaker=AgentIdentity(name="alice", constitution_version="0.1"),
        addressed_to="caucus",
        speech_act=SpeechAct.STORY,
        content=UtteranceContent(body="seeded story from prior meeting"),
        is_seed=True,
    )
    await bus.publish(seed)
    await asyncio.sleep(0.05)

    info = monitor.thread_info("t")
    assert info is not None
    assert info.member_engagements == 0, (
        "seeds carry the original speaker but represent prior-meeting "
        "context, not new engagement on the current thread"
    )

    # All members IDLE — should still not quiesce.
    monitor.record_agent_state("alice", AgentState.AWAITING_RESPONSE)
    monitor.record_agent_state("white_rabbit", AgentState.AWAITING_RESPONSE)
    monitor.record_agent_state("alice", AgentState.IDLE)
    monitor.record_agent_state("white_rabbit", AgentState.IDLE)
    await asyncio.sleep(0.05)
    assert info.state is ThreadState.RUNNING

    await monitor.stop()


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


# ---------- T-ab66 — stale-expectation pruning ----------


async def test_t_ab66_stale_question_pruned_unblocks_quiescent() -> None:
    """T-ab66: a question that sits open past
    ``expectation_stale_seconds`` gets auto-closed at quiescence-check
    time, letting the thread transition QUIESCENT via the no-open-
    expectations path rather than STUCK via the open-expectations
    path. LDR-rerun v5 receipt: ~580s wall-clock spent on threads
    where one agent's question never got engaged."""
    bus = InMemoryCaucus()
    monitor = ThreadMonitor(
        bus,
        quiescence_seconds=0.5,
        expectation_stale_seconds=0.1,
        check_interval=0.05,
    )
    await monitor.start()

    # Question opens an expectation; nobody answers.
    await bus.publish(_u(act=SpeechAct.QUESTION, body="by when?", speaker="white_rabbit"))

    # Wait long enough for the expectation to age past 0.1s. The next
    # wall-clock check at 0.5s will prune it and transition QUIESCENT.
    [change] = await _drain_until(monitor, count=1, timeout=2.0)
    assert change.to_state is ThreadState.QUIESCENT
    # The thread's open_expectations should now be empty (pruned).
    info = monitor.thread_info("t")
    assert info is not None
    assert info.open_expectations == {}

    await monitor.stop()


async def test_t_ab66_fresh_question_still_stuck() -> None:
    """T-ab66: a question that hasn't aged past the stale threshold
    still gates the thread to STUCK — pruning only applies to ages
    beyond ``expectation_stale_seconds``. Confirms the prune is age-
    bounded, not unconditional."""
    bus = InMemoryCaucus()
    monitor = ThreadMonitor(
        bus,
        quiescence_seconds=0.1,
        expectation_stale_seconds=10.0,  # never reaches before quiescence check
        check_interval=0.05,
    )
    await monitor.start()

    await bus.publish(_u(act=SpeechAct.QUESTION, body="by when?", speaker="white_rabbit"))

    [change] = await _drain_until(monitor, count=1)
    assert change.to_state is ThreadState.STUCK
    assert "open expectation" in change.reason

    await monitor.stop()
