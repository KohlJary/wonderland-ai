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

from wonderland.agent import AgentState
from wonderland.utterance import SpeechAct, Utterance

if TYPE_CHECKING:
    from wonderland.caucus import Caucus
    from wonderland.roster import ThreadRoster


_EXPECTATION_ACTS: frozenset[SpeechAct] = frozenset(
    {
        SpeechAct.QUESTION,
        SpeechAct.CONCERN,
        SpeechAct.PROPOSAL,
        SpeechAct.DEFERENCE,
    }
)

# T-ab66: open expectations (question/concern/proposal/deference)
# that sit unengaged for this long get auto-closed at quiescence-
# check time. LDR-rerun v5 stuck-phase analysis: 4-parallel decompose
# had one thread whose lone agent asked a question their counterpart
# never engaged. The open expectation kept the thread out of
# QUIESCENT (gate at line 316) and out of fast turn-based STUCK
# (gate at line 314 needs all_members_idle, which is False while the
# asked agent is still in AWAITING_RESPONSE). The fallback wall-clock
# safety net then fired twice (once per nudge cycle), eating ~580s
# wall time. Pruning stale expectations lets turn-based quiescence
# proceed naturally — the asked-but-not-answered question is treated
# as silently rejected, the thread proceeds, the run completes
# cleanly. Logged on prune so the audit trail shows what happened.
_EXPECTATION_STALE_SECONDS: float = 60.0


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
    # Count of utterances from roster members other than the convenor,
    # excluding seeds replayed from prior meetings. The IDLE-keyed
    # quiescence check requires this to be > 0 — a thread that just
    # opened can't be "quiescent" before any member has had a chance
    # to engage. Without this gate, a member transitioning to IDLE
    # from a different thread (e.g. finishing M4's last call right as
    # M5 convenes) would instantly quiesce M5 before its agents read
    # the directive. See analysis 027.
    member_engagements: int = 0


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
        roster: ThreadRoster | None = None,
        quiescence_seconds: float = 300.0,
        check_interval: float = 1.0,
        deadlock_after_nudges: int = 2,
        expectation_stale_seconds: float = _EXPECTATION_STALE_SECONDS,
        agent_name: str = "thread_monitor",
    ) -> None:
        self._bus = bus
        self._roster = roster
        # Wall-clock quiescence is now a SAFETY NET, not the primary
        # detector. Default raised to 300s to catch hung LLM calls
        # without triggering on normal-but-slow tool loops. Turn-based
        # detection (via record_agent_state) fires the moment all
        # members go IDLE — much faster and correct by construction.
        # When roster is None (no agent-state plumbing), wall-clock
        # remains the only mechanism — back-compat preserved.
        self._quiescence_seconds = quiescence_seconds
        self._check_interval = check_interval
        self._deadlock_after_nudges = deadlock_after_nudges
        self._expectation_stale_seconds = expectation_stale_seconds
        self._agent_name = agent_name

        self._threads: dict[str, ThreadInfo] = {}
        # Per-agent activity state for turn-based quiescence (see
        # analysis 022). Updated via record_agent_state, which the
        # Runner wires into each agent's state-change handler.
        self._agent_states: dict[str, AgentState] = {}
        # Threads currently awaiting external input (operator answer
        # to a QUESTION-to-operator utterance, T69). While paused,
        # neither turn-based nor wall-clock quiescence fires for the
        # thread — the team is intentionally silent waiting for the
        # human to respond, not productively-finished. The runner's
        # user-question watcher manages the pause set.
        self._quiescence_paused_threads: set[str] = set()
        # Subscribe synchronously per the WonderlandAgent fix from T14 — bus
        # publishes between construction and iteration must not be lost.
        # ThreadMonitor needs to see every utterance regardless of
        # per-thread roster (it tracks state across all live threads).
        self._iterator: AsyncIterator[Utterance] = self._bus.subscribe(
            agent_name, bypass_roster=True
        )
        self._transitions: asyncio.Queue[ThreadStateChange] = asyncio.Queue()
        self._consume_task: asyncio.Task[None] | None = None
        self._timer_task: asyncio.Task[None] | None = None

    # ------------------------------------------------------------------ #
    # Inspection
    # ------------------------------------------------------------------ #

    def pause_for_external_input(self, thread_id: str) -> None:
        """Suppress quiescence for ``thread_id`` while it's awaiting
        external input (T69 — operator answer to a QUESTION-to-
        operator utterance). Both turn-based and wall-clock paths
        gate on the pause flag; agent-state transitions still record
        normally so resume picks up the right post-resume baseline.
        Idempotent."""
        self._quiescence_paused_threads.add(thread_id)

    def resume_for_external_input(self, thread_id: str) -> None:
        """End the pause for ``thread_id`` after external input
        landed. Quiescence detection re-enables on the next state
        change or wall-clock check. Idempotent."""
        self._quiescence_paused_threads.discard(thread_id)

    def is_paused_for_external_input(self, thread_id: str) -> bool:
        """For tests / inspection: True if quiescence is currently
        suppressed for this thread."""
        return thread_id in self._quiescence_paused_threads

    def thread_state(self, thread_id: str) -> ThreadState:
        info = self._threads.get(thread_id)
        return info.state if info else ThreadState.RUNNING

    def thread_info(self, thread_id: str) -> ThreadInfo | None:
        return self._threads.get(thread_id)

    def known_threads(self) -> list[str]:
        return sorted(self._threads.keys())

    def mark_complete(self, thread_id: str, reason: str) -> None:
        """Force-transition a thread to COMPLETE.

        Used by run_workflow when a meeting exits via MEETING_BUDGET (or
        any non-COMPLETE terminal outcome) so the late-publish guard
        suppresses any in-flight deliberations whose calls land after
        the meeting closed. Without this, a slow agent's response would
        post into a still-RUNNING thread that no one is reading, and
        get miscounted against the next meeting.

        No-op if the thread is unknown or already COMPLETE.
        """
        info = self._threads.get(thread_id)
        if info is None or info.state is ThreadState.COMPLETE:
            return
        change = self._transition(info, ThreadState.COMPLETE, reason)
        self._transitions.put_nowait(change)

    def record_nudge(self, thread_id: str) -> None:
        """Register that the Dodo (or anyone) issued a nudge against a thread.

        When ``nudge_count`` reaches ``deadlock_after_nudges`` and the
        thread is still STUCK, the next state check transitions to
        DEADLOCKED.
        """
        info = self._threads.setdefault(thread_id, ThreadInfo(thread_id=thread_id))
        info.nudge_count += 1

    def record_agent_state(
        self,
        agent_name: str,
        new_state: AgentState,
    ) -> None:
        """Update an agent's activity state and re-check quiescence on
        threads where they are a member.

        The Runner installs this as the state-change handler on every
        agent. When an agent transitions to IDLE, every thread they
        belong to may become quiescent — we check by asking the roster
        for membership and inspecting all members' states.

        No-op when no roster was wired (back-compat: ThreadMonitor falls
        back to wall-clock-only detection).
        """
        previous = self._agent_states.get(agent_name, AgentState.IDLE)
        if new_state is previous:
            return
        self._agent_states[agent_name] = new_state
        if self._roster is None:
            return
        # Only IDLE transitions can OPEN the door to quiescence.
        # Non-IDLE transitions guarantee the thread is non-quiescent,
        # but the existing _record() path already keeps state RUNNING
        # whenever a member produced an utterance, so we don't need to
        # actively unwind here.
        if new_state is not AgentState.IDLE:
            return
        for thread_id in self._roster.threads():
            if agent_name not in self._roster.members(thread_id):
                continue
            change = self._check_state_after_idle_transition(thread_id)
            if change is not None:
                self._transitions.put_nowait(change)

    def _prune_stale_expectations(
        self, info: ThreadInfo, now: datetime
    ) -> None:
        """T-ab66: drop open_expectations older than the stale threshold.

        Open expectations gate both QUIESCENT and STUCK transitions.
        When a question/concern sits unengaged longer than
        ``_EXPECTATION_STALE_SECONDS``, treat it as silently rejected
        and remove it from tracking so the thread can proceed via the
        normal quiescence path. Without this, agents who ask questions
        the roster doesn't engage with leave the meeting stuck on
        wall-clock timeouts (LDR-rerun v5: ~580s per stuck thread).

        Mutates info.open_expectations in place. Logs each pruned
        expectation to stderr so the audit trail surfaces the silent
        rejection.
        """
        if not info.open_expectations:
            return
        stale_ids = []
        for expect_id, expect in info.open_expectations.items():
            age = (now - expect.timestamp).total_seconds()
            if age >= self._expectation_stale_seconds:
                stale_ids.append((expect_id, expect, age))
        if not stale_ids:
            return
        import sys
        for expect_id, expect, age in stale_ids:
            sys.stderr.write(
                f"[expectation-stale-prune] thread={info.thread_id!r} "
                f"speech_act={expect.speech_act.value!r} "
                f"speaker={expect.speaker.name!r} "
                f"age={age:.1f}s — treating as silently rejected\n"
            )
            del info.open_expectations[expect_id]

    def _all_members_idle(self, thread_id: str) -> bool:
        """True iff every member of the thread's roster is IDLE.

        An unknown agent (no recorded state) is treated as IDLE — they
        either haven't started (still waiting for a turn) or never
        engaged with this thread.
        """
        if self._roster is None:
            return False
        members = self._roster.members(thread_id)
        if not members:
            return False
        for member in members:
            state = self._agent_states.get(member, AgentState.IDLE)
            if state is not AgentState.IDLE:
                return False
        return True

    def _check_state_after_idle_transition(
        self, thread_id: str
    ) -> ThreadStateChange | None:
        """Quiescence check fired by an agent going IDLE. Returns a
        transition if the thread should change state, else None.

        Mirrors the wall-clock _check_state_after_silence logic but
        keyed on agent state rather than elapsed time. STUCK still
        gates on open expectations (per the spec); the only difference
        is *when* we check (immediately on idle, not after N seconds).
        """
        # T69: while a thread is awaiting external input (operator
        # answer to a QUESTION-to-operator), all-members-IDLE is
        # *expected* — the human is the next mover. Don't fire
        # quiescence and don't transition the thread.
        if thread_id in self._quiescence_paused_threads:
            return None
        info = self._threads.get(thread_id)
        if info is None or info.state in (
            ThreadState.COMPLETE,
            ThreadState.ABANDONED,
        ):
            return None
        # A freshly-convened thread has utterance_count=1 (the
        # convenor's directive) but no member engagements yet. If a
        # roster member transitions to IDLE in this window — typically
        # because they just finished a turn on a *different* thread —
        # the quiescence check would otherwise see all-members-idle
        # and instantly transition the new thread to QUIESCENT before
        # any agent has had a chance to read the directive. Wall-clock
        # quiescence (_check_state_after_silence) remains the safety
        # net for threads that genuinely never engage.
        if info.member_engagements == 0:
            return None
        if not self._all_members_idle(thread_id):
            return None
        # T-ab66: prune expectations that have aged past the stale
        # threshold so a stuck-on-unanswered-question thread can
        # proceed to QUIESCENT instead of waiting wall-clock.
        self._prune_stale_expectations(info, datetime.now(UTC))
        if info.open_expectations:
            if (
                info.state is ThreadState.STUCK
                and info.nudge_count >= self._deadlock_after_nudges
            ):
                return self._transition(
                    info,
                    ThreadState.DEADLOCKED,
                    f"{info.nudge_count} nudges, still {len(info.open_expectations)} open",
                )
            if info.state is not ThreadState.STUCK:
                return self._transition(
                    info,
                    ThreadState.STUCK,
                    f"{len(info.open_expectations)} open expectation(s); all members idle",
                )
            return None
        if info.state is not ThreadState.QUIESCENT:
            return self._transition(
                info,
                ThreadState.QUIESCENT,
                "no open expectations; all members idle",
            )
        return None

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

        # Track member engagement so the IDLE-keyed quiescence check can
        # tell "team finished" from "team hasn't started." A new thread
        # gets the convenor's directive (utterance_count=1) but no real
        # member work yet. We count an utterance as engagement when its
        # speaker is on the thread's roster, isn't the convenor, and
        # isn't a seed replayed from a prior meeting.
        if (
            self._roster is not None
            and not u.is_seed
            and self._roster.is_member(u.thread_id, u.speaker.name)
            and u.speaker.name != self._roster.convenor(u.thread_id)
        ):
            info.member_engagements += 1

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
        # T69: don't fire wall-clock quiescence on threads waiting
        # for operator input. Operators may take minutes to read
        # the question and decide; the silence is intentional, not
        # pathological.
        if info.thread_id in self._quiescence_paused_threads:
            return None
        elapsed = (now - info.last_activity).total_seconds()
        if elapsed < self._quiescence_seconds:
            return None

        # T-ab66: prune expectations that have aged past the stale
        # threshold so a stuck-on-unanswered-question thread can
        # transition to QUIESCENT via the no-expectations path below.
        self._prune_stale_expectations(info, now)
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
        # T-ab66 instrumentation: log thread-state transitions to stderr
        # so post-run analysis can identify which quiescence path fired
        # (turn-based "all members idle" vs wall-clock "silent {N}s").
        # The reason text already distinguishes them; this just surfaces
        # them where they're greppable from run logs. ThreadStateChange
        # events aren't persisted to events.jsonl, so without this
        # surface there's no way to tell which path drove a phase exit.
        import sys
        sys.stderr.write(
            f"[thread-state] thread={info.thread_id!r} "
            f"{from_state.value} → {to_state.value}  "
            f"reason={reason!r}\n"
        )
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
