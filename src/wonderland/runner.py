"""Runner — the durable orchestration layer for Wonderland teams.

Where individual demo scripts hand-wired the bus + monitor + agents
+ printer for each scenario, the Runner consolidates that machinery
into a single class with a clean event protocol. Both the CLI
(stdin/stdout) and a future TUI (Textual) consume the same
``RunnerEvent`` stream — different presentation, same engine.

Per the T34 restructure after the polite-deadlock $8 surprise: the
Runner owns budget caps + token telemetry + interactive escalation
so cost runaway becomes a recoverable event (human prompt) rather
than a charge on the dashboard. Live re-runs of full-cast scenarios
are expensive ($5-10 each) and must be defended against; the
Runner is where that defense lives.

Usage from a presentation layer::

    runner = Runner.make_full_cast(project_root, budget_dollars=2.00)
    await runner.setup()
    try:
        await runner.publish_directive("Build a translation chat...")
        async for event in runner.events():
            render(event)
            if event.kind == "escalation_prompt":
                response = await get_user_input(event.payload["brief"])
                await runner.respond_to_escalation(
                    event.payload["prompt_id"], response
                )
            if event.kind in ("complete", "aborted", "timeout"):
                break
    finally:
        await runner.teardown()

The Runner emits structured ``RunnerEvent``\\s for every utterance,
state transition, consensus alert, budget warning, escalation prompt,
and lifecycle event. A presentation layer's only job is to render
those events and (when interactive) feed responses back via
``respond_to_escalation``.
"""

from __future__ import annotations

import asyncio
import contextlib
import time
import uuid
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from ulid import ULID

from wonderland.adr import ADRRegistry
from wonderland.agent import AgentState
from wonderland.agents import (
    Alice,
    Caterpillar,
    CheshireCat,
    Dodo,
    Dormouse,
    MadHatter,
    QueenOfHearts,
    Tweedledee,
    Tweedledum,
    WhiteRabbit,
)
from wonderland.caucus import Caucus, InMemoryCaucus
from wonderland.consensus import SyntheticConsensusGuard
from wonderland.contract_note import ContractNoteRegistry
from wonderland.escalation import EscalationBrief, EscalationRecord, EscalationRegistry
from wonderland.implementation import ImplementationRegistry
from wonderland.llm import LLMClient
from wonderland.memory import AgentMemory
from wonderland.observation import ObservationRegistry
from wonderland.review import ReviewRegistry
from wonderland.roster import ThreadRoster
from wonderland.ruling import RulingRegistry
from wonderland.story import StoryRegistry
from wonderland.telemetry import Telemetry
from wonderland.test_scenario import TestScenarioRegistry
from wonderland.thread_monitor import ThreadMonitor, ThreadState, ThreadStateChange
from wonderland.feature import FeatureRegistry
from wonderland.ticket import TicketRegistry
from wonderland.tools import Tools
from wonderland.utterance import SpeechAct, Utterance

# --------------------------------------------------------------------- #
# Event protocol
# --------------------------------------------------------------------- #


EventKind = Literal[
    "utterance",
    "state",
    "consensus_alert",
    "telemetry",
    "budget_warning",
    "budget_exceeded",
    "escalation_prompt",
    "complete",
    "aborted",
    "timeout",
]


def _ensure_git_repo(project_root: Path) -> None:
    """Initialize ``project_root`` as a git repo with an empty initial
    commit, idempotently. Reviewers (Caterpillar via git_diff) need an
    initial commit to diff working-tree changes against.

    Skip silently if git isn't installed — git_status / git_diff will
    fail per-call with a clear ToolError, but the rest of the framework
    still works. Skip silently if project_root is already a repo.
    """
    import subprocess

    git_dir = project_root / ".git"
    if git_dir.exists():
        return
    try:
        # Initialize as a fresh repo with an empty initial commit so
        # subsequent `git diff HEAD` has a baseline.
        subprocess.run(
            ["git", "init", "--initial-branch=main"],
            cwd=project_root,
            capture_output=True,
            check=True,
            timeout=10,
        )
        # .gitignore: keep .wonderland/ (registries, memory, telemetry)
        # out of the working-tree diff. Otherwise every meeting's
        # registry writes pollute git_status / git_diff and the
        # reviewer can't find the actual code among the noise. We only
        # write the file if it doesn't already exist so we don't
        # clobber a project's existing rules.
        gitignore = project_root / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text(
                "# Wonderland framework state — registries, episodic memory,\n"
                "# telemetry. Not part of the code under review.\n"
                ".wonderland/\n"
            )
        # Configure local identity so the empty commit doesn't fail on
        # systems without a global git config. Local-scope only; no
        # global config touched.
        subprocess.run(
            ["git", "config", "user.email", "wonderland@local"],
            cwd=project_root,
            capture_output=True,
            check=True,
            timeout=10,
        )
        subprocess.run(
            ["git", "config", "user.name", "Wonderland Runner"],
            cwd=project_root,
            capture_output=True,
            check=True,
            timeout=10,
        )
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "wonderland: empty initial commit"],
            cwd=project_root,
            capture_output=True,
            check=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        # Git not available, or init failed — proceed without it.
        # Tools.git_status / git_diff will surface the error per call.
        return


@dataclass(frozen=True)
class RunnerEvent:
    """A single event the Runner emits for the presentation layer to render.

    ``kind`` discriminates the payload shape. The presentation layer
    decides how to render each kind — the Runner produces structured
    data, never strings of prose.
    """

    kind: EventKind
    elapsed: float
    payload: dict[str, Any] = field(default_factory=dict)


# --------------------------------------------------------------------- #
# Runner
# --------------------------------------------------------------------- #


@dataclass
class _PendingEscalation:
    """A live escalation awaiting a human response."""

    prompt_id: str
    brief: EscalationBrief
    record: EscalationRecord
    response_future: asyncio.Future[str]


class Runner:
    """Drives a Wonderland team for a directive run.

    Owns: bus, ThreadMonitor, all agents, SyntheticConsensusGuard,
    Telemetry, BudgetCap. Drives: a directive through the team to
    completion, escalation, or abort. Exposes: an async event stream.
    """

    DEFAULT_BUDGET_DOLLARS: float = 1.00
    # Wall-clock fallback for hung LLM calls. Turn-based quiescence
    # (analysis 022 follow-up) fires the moment all members go IDLE,
    # so this only matters when state tracking misses something —
    # network-hung deliberate(), agent crashed mid-state-transition.
    # 300s is generous enough to outlast any normal tool loop while
    # still bounding pathological cases.
    DEFAULT_QUIESCENCE_SECONDS: float = 300.0
    # Wall-clock global timeout — None by default. Wonderland is turn-
    # based; agents take turns, deliberate, ship work or go silent.
    # Runaway-loop protection is GLOBAL_BUDGET's job (each turn costs
    # money, the cap fires before any wall clock would meaningfully
    # protect anything). Wall-clock-as-safety-net lives at the
    # ThreadMonitor layer (network-hung deliberation, agent crash mid-
    # state-transition) — see ThreadMonitor's quiescence_seconds.
    # Per the project_no_wall_clock_in_turn_based memory and analysis
    # 029's M5-RUNNING-outcome bug: applying clock semantics at the
    # runner layer is a category error and was actively causing
    # downstream meeting starvation. Removed as a default; users who
    # want a wall-clock cap can pass timeout_seconds=N explicitly.
    DEFAULT_TIMEOUT_SECONDS: float | None = None
    BUDGET_WARNING_FRACTION: float = 0.80
    BUDGET_CHECK_INTERVAL_SECONDS: float = 1.0

    def __init__(
        self,
        bus: Caucus,
        agents: dict[str, Any],  # name → WonderlandAgent
        dodo: Dodo,
        *,
        project_root: Path,
        budget_dollars: float | None = DEFAULT_BUDGET_DOLLARS,
        quiescence_seconds: float = DEFAULT_QUIESCENCE_SECONDS,
        timeout_seconds: float | None = DEFAULT_TIMEOUT_SECONDS,
        telemetry: Telemetry | None = None,
        run_id: str | None = None,
        roster: ThreadRoster | None = None,
    ) -> None:
        self.bus = bus
        self.agents = agents  # includes dodo
        self.dodo = dodo
        self.project_root = project_root
        self.budget_dollars = budget_dollars
        self.quiescence_seconds = quiescence_seconds
        self.timeout_seconds = timeout_seconds
        self.telemetry = telemetry or Telemetry()
        self.run_id = run_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
        # The roster gates per-thread delivery at the bus. None = open
        # bus (every agent sees every thread, the original behavior).
        # When set, threads can be registered with subset rosters; the
        # runner-observer subscription is always added so the Runner
        # itself sees everything for telemetry / event emission.
        self.roster = roster

        # Pass the roster so the monitor can do turn-based quiescence
        # detection (analysis 022 follow-up). When all members of a thread
        # are IDLE, the monitor transitions immediately rather than waiting
        # for the wall-clock timer. The wall-clock cap is now a safety net
        # for hung LLM calls — see ThreadMonitor.__init__ for details.
        self._monitor = ThreadMonitor(
            bus,
            roster=roster,
            quiescence_seconds=quiescence_seconds,
        )
        # Lost-utterance registry: utterances whose deliberation
        # outlived their target thread. Populated by
        # _handle_late_publish via the late-publish handler wired into
        # every agent at setup. Inspectable via lost_utterances().
        # Stop-gap until roadmap 29497820 (big Dodo orchestration
        # rework) supersedes this.
        self._lost_utterances: list[Utterance] = []
        self._consensus_guard = SyntheticConsensusGuard(
            bus,
            min_agents=3,
            similarity_threshold=0.5,
            window_size=20,
            shingle_size=2,
        )
        # The runner-observer must see every utterance regardless of
        # roster filtering; bypass_roster=True opts it out of per-thread
        # gating so events still emit for scoped meetings.
        self._observer = bus.subscribe(agent_name="runner-observer", bypass_roster=True)

        self._event_queue: asyncio.Queue[RunnerEvent] = asyncio.Queue()
        self._pending_escalations: dict[str, _PendingEscalation] = {}
        self._budget_warned = False
        self._budget_exceeded = False
        self._aborted = False
        self._completed = False
        self._start_monotonic: float | None = None

        # Pause/resume primitive. The event is "set" (signaled) by
        # default — meeting dispatch awaits it before opening each
        # rotation, but the await returns immediately while set.
        # ``pause()`` clears the event; ``resume()`` sets it. While
        # paused, in-flight LLM calls finish (we don't cancel them
        # mid-deliberation), but no new rotations open. Cheapest
        # coarse pause that doesn't risk corrupting an emission.
        self._paused = asyncio.Event()
        self._paused.set()

        self._observer_task: asyncio.Task[None] | None = None
        self._state_task: asyncio.Task[None] | None = None
        self._consensus_task: asyncio.Task[None] | None = None
        self._budget_task: asyncio.Task[None] | None = None
        self._timeout_task: asyncio.Task[None] | None = None
        self._user_question_task: asyncio.Task[None] | None = None
        self._agent_tasks: list[asyncio.Task[None]] = []

        # User-question affordance (T69 / P10 / roadmap 9aae11bc).
        # Agents emit QUESTION-to-operator utterances when they need
        # a decision the team can't resolve internally. The watcher
        # task observes the bus, calls the registered handler, and
        # publishes the operator's answer as a normal OBSERVATION.
        # ``_user_question_handler`` is async (str -> str). When None,
        # questions are answered with a "no operator available"
        # sentinel so headless runs degrade gracefully.
        self._user_question_handler: (
            Callable[[Utterance], Any] | None
        ) = None
        # Registry tracking question_id → answer (cached) and
        # question_id → Future (pending) so callers can await an
        # answer without racing the watcher's publish.
        self._answered_questions: dict[str, Utterance] = {}
        self._pending_question_futures: dict[
            str, asyncio.Future[Utterance]
        ] = {}

    # ------------------------------------------------------------------ #
    # Factory: full-cast scenario
    # ------------------------------------------------------------------ #

    @classmethod
    async def make_full_cast(
        cls,
        project_root: Path,
        *,
        llm_factory: Callable[[str, Telemetry], LLMClient] | None = None,
        budget_dollars: float | None = DEFAULT_BUDGET_DOLLARS,
        quiescence_seconds: float = DEFAULT_QUIESCENCE_SECONDS,
        timeout_seconds: float | None = DEFAULT_TIMEOUT_SECONDS,
        telemetry: Telemetry | None = None,
        run_id: str | None = None,
        model: str | None = None,
    ) -> Runner:
        """Construct a Runner with all 10 agents wired against shared registries.

        ``llm_factory(name, telemetry) → LLMClient`` is the per-agent
        LLM constructor; the default builds a real LLMClient with
        telemetry's ``record_for(name)`` callback. Tests override with
        a mock factory.

        ``model`` overrides the LLM model id every agent uses. Only
        applies when ``llm_factory`` is None (the default factory path);
        callers passing a custom factory are responsible for selecting
        the model themselves. None → ``DEFAULT_MODEL`` from llm.py.

        The bus is wired with a fresh ``ThreadRoster``. By default no
        threads are registered, so the bus behaves as before (every
        agent sees every utterance). Callers that want a scoped meeting
        pass ``recipients=[...]`` to ``publish_directive``, which
        registers the thread before relaying.
        """
        roster = ThreadRoster()
        bus = InMemoryCaucus(roster=roster)
        telemetry = telemetry or Telemetry()

        if llm_factory is None:

            def _default_factory(name: str, tel: Telemetry) -> LLMClient:
                kwargs: dict[str, Any] = {
                    "on_token_usage": tel.record_for(name),
                }
                if model is not None:
                    kwargs["model"] = model
                return LLMClient(**kwargs)

            llm_factory = _default_factory

        memories: dict[str, AgentMemory] = {}
        for name in (
            "alice",
            "cheshire_cat",
            "white_rabbit",
            "dodo",
            "mad_hatter",
            "caterpillar",
            "queen_of_hearts",
            "dormouse",
            "tweedledee",
            "tweedledum",
        ):
            mem = AgentMemory.for_project(project_root, name)
            await mem.open()
            memories[name] = mem

        impl_registry = ImplementationRegistry(project_root)
        contract_note_registry = ContractNoteRegistry(project_root)
        # Tools sandboxed to project_root. Initially wired only to the
        # Tweedles (analysis 015); now expanded to Cat / Caterpillar /
        # Hatter so they can read existing code (Cat to ground
        # architecture, Caterpillar to actually look at code under
        # review, Hatter to write real test files alongside scenarios).
        # All four share the same Tools instance — same sandbox, no
        # duplicate path-resolution state. The on_tool_call writer
        # captures every invocation as a JSONL event for post-run
        # cost attribution (P10 / T66). Goes to the same .wonderland/
        # directory as phase events.
        from wonderland.tools import jsonl_tool_call_writer

        tool_call_writer = jsonl_tool_call_writer(
            project_root / ".wonderland" / "tool-calls.jsonl"
        )
        shared_tools = Tools(project_root, on_tool_call=tool_call_writer)
        # Initialize project_root as a git repo with an empty initial
        # commit so the working tree IS the implementation artifact:
        # Tweedles ship code; Caterpillar reviews via git_diff against
        # HEAD. Without an initial commit, diff has nothing to compare
        # against and the reviewer can't see what shipped vs what
        # already existed. Idempotent: skip if already a repo.
        _ensure_git_repo(project_root)

        agents: dict[str, Any] = {
            "alice": Alice(
                memory=memories["alice"],
                bus=bus,
                llm=llm_factory("alice", telemetry),
                story_registry=StoryRegistry(project_root),
                test_scenario_registry=TestScenarioRegistry(project_root),
            ),
            "cheshire_cat": CheshireCat(
                memory=memories["cheshire_cat"],
                bus=bus,
                llm=llm_factory("cheshire_cat", telemetry),
                adr_registry=ADRRegistry(project_root),
                tools=shared_tools,
            ),
            "white_rabbit": WhiteRabbit(
                memory=memories["white_rabbit"],
                bus=bus,
                llm=llm_factory("white_rabbit", telemetry),
                ticket_registry=TicketRegistry(project_root),
                feature_registry=FeatureRegistry(project_root),
                tools=shared_tools,
            ),
            "mad_hatter": MadHatter(
                memory=memories["mad_hatter"],
                bus=bus,
                llm=llm_factory("mad_hatter", telemetry),
                test_scenario_registry=TestScenarioRegistry(project_root),
                tools=shared_tools,
            ),
            "caterpillar": Caterpillar(
                memory=memories["caterpillar"],
                bus=bus,
                llm=llm_factory("caterpillar", telemetry),
                review_registry=ReviewRegistry(project_root),
                story_registry=StoryRegistry(project_root),
                tools=shared_tools,
            ),
            "queen_of_hearts": QueenOfHearts(
                memory=memories["queen_of_hearts"],
                bus=bus,
                llm=llm_factory("queen_of_hearts", telemetry),
                ruling_registry=RulingRegistry(project_root),
            ),
            "dormouse": Dormouse(
                memory=memories["dormouse"],
                bus=bus,
                llm=llm_factory("dormouse", telemetry),
                observation_registry=ObservationRegistry(project_root),
            ),
            "tweedledee": Tweedledee(
                memory=memories["tweedledee"],
                bus=bus,
                llm=llm_factory("tweedledee", telemetry),
                implementation_registry=impl_registry,
                contract_note_registry=contract_note_registry,
                tools=shared_tools,
            ),
            "tweedledum": Tweedledum(
                memory=memories["tweedledum"],
                bus=bus,
                llm=llm_factory("tweedledum", telemetry),
                implementation_registry=impl_registry,
                contract_note_registry=contract_note_registry,
                tools=shared_tools,
            ),
        }
        dodo = Dodo(
            memory=memories["dodo"],
            bus=bus,
            llm=llm_factory("dodo", telemetry),
            escalation_registry=EscalationRegistry(project_root),
        )
        agents["dodo"] = dodo

        return cls(
            bus=bus,
            agents=agents,
            dodo=dodo,
            project_root=project_root,
            budget_dollars=budget_dollars,
            quiescence_seconds=quiescence_seconds,
            timeout_seconds=timeout_seconds,
            telemetry=telemetry,
            run_id=run_id,
            roster=roster,
        )

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    async def setup(self) -> None:
        """Start the bus consumers + agent loops + monitor + guard."""
        self._start_monotonic = time.monotonic()
        await self._monitor.start()
        await self._consensus_guard.start()

        # Wire the hard budget gate into every agent before their loops
        # start. Each agent's speak() consults the gate before
        # deliberating; if the team is over the cap, no LLM call fires.
        # When budget_dollars is None the gate stays open (no cap).
        if self.budget_dollars is not None:
            cap = self.budget_dollars

            def _budget_ok() -> bool:
                return self.telemetry.total_cost < cap

            for agent in self.agents.values():
                agent.set_budget_guard(_budget_ok)

        # Wire the roster into every agent so INVITE utterances can
        # mutate roster membership in-flight (Block 2c). When self.roster
        # is None, set_roster(None) is a no-op and INVITE publishes
        # without changing the roster.
        for agent in self.agents.values():
            agent.set_roster(self.roster)

        # Late-publish stop-gap (roadmap 29497820): when a slow
        # deliberation completes after its trigger's thread already
        # transitioned to COMPLETE, suppress publish + record the
        # utterance for inspection. Without this, the bus accepted
        # late utterances and meeting capture silently lost them.
        # Replaced when the big Dodo orchestration rework lands.
        for agent in self.agents.values():
            agent.set_late_publish_handler(self._handle_late_publish)
        # Turn-based quiescence (analysis 022 follow-up): each agent
        # reports activity transitions to the ThreadMonitor so quiescence
        # detection fires the moment all members go IDLE rather than
        # after a wall-clock window. The wall-clock cap remains as a
        # hung-LLM-call safety net.
        for agent in self.agents.values():
            agent.set_state_change_handler(self._on_agent_state_change)

        self._observer_task = asyncio.create_task(self._consume_bus(), name="runner-bus-observer")
        self._state_task = asyncio.create_task(self._consume_states(), name="runner-state-watcher")
        self._consensus_task = asyncio.create_task(
            self._consume_consensus(), name="runner-consensus-watcher"
        )
        if self.budget_dollars is not None:
            self._budget_task = asyncio.create_task(
                self._check_budget(), name="runner-budget-checker"
            )
        # Wall-clock timeout — opt-in only. See DEFAULT_TIMEOUT_SECONDS
        # for the rationale (turn-based system, GLOBAL_BUDGET handles
        # runaway loops, applying clock semantics at this layer is a
        # category error that caused real bugs in analysis 029).
        if self.timeout_seconds is not None:
            self._timeout_task = asyncio.create_task(
                self._enforce_timeout(), name="runner-timeout"
            )
        # User-question watcher (T69) — observes the bus for
        # QUESTION-to-operator utterances and routes them through
        # the registered handler. Always started; if no handler
        # is registered, questions get the "no operator available"
        # sentinel answer.
        self._user_question_task = asyncio.create_task(
            self._watch_user_questions(),
            name="runner-user-question-watcher",
        )
        for name, agent in self.agents.items():
            self._agent_tasks.append(asyncio.create_task(agent.run(), name=f"{name}-run"))

    def _on_agent_state_change(
        self,
        agent_name: str,
        from_state: AgentState,
        to_state: AgentState,
    ) -> None:
        """Forward an agent's activity transition to the ThreadMonitor.

        Wired as ``set_state_change_handler`` on every agent during
        setup. The monitor uses this to detect quiescence the moment
        all members of a thread go IDLE — replacing the wall-clock
        bus-silence model that closed meetings mid-tool-loop (analysis
        022).

        from_state is unused (the monitor doesn't care about the prior
        state, only the new one) but kept in the signature for symmetry
        with other state-change consumers we might add later.
        """
        del from_state  # quiet linter; kept in signature for symmetry
        self._monitor.record_agent_state(agent_name, to_state)

    def _handle_late_publish(self, utterance: Utterance) -> bool:
        """Late-publish stop-gap. Called by an agent's speak() before
        it publishes a freshly-deliberated utterance. Returns True if
        the utterance should be suppressed because its target thread
        already transitioned to COMPLETE — which means a slow
        deliberation outlived its meeting.

        Returning True suppresses both the bus publish and the agent's
        memory.record(). The utterance is appended to
        ``self._lost_utterances`` for inspection.

        See roadmap 29497820 for the full Dodo orchestration rework
        that supersedes this.
        """
        thread_id = utterance.thread_id
        if not thread_id:
            return False
        state = self._monitor.thread_state(thread_id)
        if state is not ThreadState.COMPLETE:
            return False
        self._lost_utterances.append(utterance)
        import sys

        snippet = (utterance.content.body or "").strip().split("\n", 1)[0][:120]
        print(
            f"[late-publish] {utterance.speaker.name} → thread {thread_id!r} "
            f"(already COMPLETE) — suppressing {utterance.speech_act.value}: "
            f"{snippet!r}",
            file=sys.stderr,
        )
        return True

    def lost_utterances(self) -> list[Utterance]:
        """Utterances suppressed by the late-publish stop-gap. Empty
        when every deliberation finished within its meeting's
        boundaries. Non-empty signals the slow-deliberation pattern
        roadmap 29497820 documents."""
        return list(self._lost_utterances)

    def mark_thread_complete(self, thread_id: str, reason: str) -> None:
        """Force-mark a thread COMPLETE in the monitor.

        Called by run_workflow when a meeting exits via a non-COMPLETE
        terminal outcome (MEETING_BUDGET today). Without this, an
        in-flight deliberation whose LLM call returns after the meeting
        closed would publish into a thread the monitor still considers
        RUNNING — bypassing the late-publish guard and landing on an
        abandoned thread.
        """
        self._monitor.mark_complete(thread_id, reason)

    async def teardown(self) -> None:
        """Stop everything and write the per-run telemetry record."""
        for agent in self.agents.values():
            await agent.stop()
        await self._monitor.stop()
        await self._consensus_guard.stop()

        for task in (
            self._observer_task,
            self._state_task,
            self._consensus_task,
            self._budget_task,
            self._timeout_task,
            *self._agent_tasks,
        ):
            if task is not None and not task.done():
                task.cancel()
        for task in (
            self._observer_task,
            self._state_task,
            self._consensus_task,
            self._budget_task,
            self._timeout_task,
            *self._agent_tasks,
        ):
            if task is not None:
                with contextlib.suppress(asyncio.CancelledError):
                    await task

        # Resolve any pending escalations so their futures don't leak.
        for pending in self._pending_escalations.values():
            if not pending.response_future.done():
                pending.response_future.cancel()

        for mem in (a.memory for a in self.agents.values()):
            await mem.close()

        # Write the run record with summary metadata.
        outcome = "complete" if self._completed else "aborted" if self._aborted else "timeout"
        elapsed = self._elapsed()
        self.telemetry.write_run_record(
            self.project_root,
            self.run_id,
            extra={
                "outcome": outcome,
                "elapsed_seconds": round(elapsed, 2),
                "budget_dollars": self.budget_dollars,
                "budget_exceeded": self._budget_exceeded,
            },
        )

    # ------------------------------------------------------------------ #
    # Driving the run
    # ------------------------------------------------------------------ #

    async def publish_directive(
        self,
        directive: str,
        *,
        thread_id: str = "main",
        recipients: list[str] | tuple[str, ...] | set[str] | None = None,
        goal: str = "",
    ) -> Utterance:
        """Relay a directive from the Dodo to start the team's work.

        ``recipients`` registers a scoped meeting for ``thread_id``: only
        the named agents will see utterances on this thread. The Dodo is
        always added to the roster so it can orchestrate (nudge,
        escalate, acknowledge). Pass ``None`` (default) to leave the
        thread open — every agent sees it, the original behavior.

        ``goal`` is a short string describing what the meeting is for.
        Stored on the roster so future tooling (and future humans
        reading transcripts) can tell what each thread was convened to
        decide.
        """
        if recipients is not None and self.roster is not None:
            members = set(recipients)
            members.add(self.dodo.identity.name)
            self.roster.register(
                thread_id, members=members, goal=goal, convenor=self.dodo.identity.name
            )
        return await self.dodo.relay_directive(directive, thread_id=thread_id)

    async def convene(
        self,
        *,
        thread_id: str,
        goal: str,
        roster: list[str] | tuple[str, ...] | set[str],
        seed_utterances: list[Utterance] | tuple[Utterance, ...] = (),
        convenor_directive: str | None = None,
    ) -> list[Utterance]:
        """Open a follow-up meeting with prior-meeting context as opening seeds.

        Per analysis 014: the natural cross-meeting composition pattern is
        artifact A from meeting 1 driving artifact B in meeting 2. The
        Tweedles' engagement rules ``almost_never`` engage with bare
        directives — they wait for upstream artifacts (Cat proposals,
        Alice stories, Rabbit tickets). So a follow-up meeting needs the
        prior meeting's relevant artifacts *on the bus* as utterances
        from their original speakers. That's what this method does.

        Caller constructs the seed Utterance objects (preserving the
        original speaker, speech act, body, and artifacts). This method:

        1. Registers ``thread_id`` with ``roster`` (Dodo auto-added so
           it can orchestrate the new meeting).
        2. Re-stamps each seed's ``thread_id`` to the new meeting and
           publishes it. The bus's roster filtering routes them only to
           members; non-members never see them. Each agent's listen loop
           still skips its own utterances, so the original speaker
           (e.g., the Cat re-publishing her own ADR) doesn't engage with
           her own seed.
        3. Optionally publishes a Dodo directive as the convenor's
           framing — the meeting goal in the team's voice.

        Returns the list of seed utterances that were published (with
        re-stamped thread_id and fresh ids), so the caller can correlate
        if needed.
        """
        if self.roster is None:
            raise RuntimeError(
                "convene() requires the Runner to have a ThreadRoster. "
                "Use Runner.make_full_cast (which wires one) or pass "
                "roster=ThreadRoster() at construction."
            )

        members = set(roster)
        members.add(self.dodo.identity.name)
        self.roster.register(
            thread_id, members=members, goal=goal, convenor=self.dodo.identity.name
        )

        published: list[Utterance] = []
        for seed in seed_utterances:
            # Re-stamp to the new thread; preserve speaker/act/content/artifacts.
            # Pydantic's model_copy with update= mutates the frozen model
            # cleanly. We also strip parent_id since it would point at a
            # message in the prior thread (now meaningless), and bump
            # the timestamp to "now" so the thread_monitor's quiescence
            # check measures from the moment the seed lands on the bus
            # — not from when the original utterance was first created
            # in the prior meeting (which can be minutes ago, causing
            # the thread to immediately be marked silent-for-too-long
            # and quiesce within seconds).
            restamped = seed.model_copy(
                update={
                    "id": str(ULID()),
                    "thread_id": thread_id,
                    "parent_id": None,
                    "timestamp": datetime.now(UTC),
                    "is_seed": True,
                }
            )
            await self.bus.publish(restamped)
            published.append(restamped)

        if convenor_directive is not None:
            directive_utterance = await self.dodo.relay_directive(
                convenor_directive, thread_id=thread_id
            )
            published.append(directive_utterance)

        return published

    async def events(
        self,
        *,
        terminal_thread_id: str | None = None,
    ) -> AsyncIterator[RunnerEvent]:
        """Yield Runner events until completion, abort, or timeout.

        ``terminal_thread_id``: when set, only auto-return on
        ``complete`` events matching that thread. Stale complete
        events from other threads (e.g. M(N-1)'s mark_thread_complete
        firing during M(N)'s events loop) are yielded but don't end
        iteration. Required for the workflow's per-meeting events
        loop — otherwise a leaked complete from a prior meeting ends
        the new meeting before any agent deliberates (analysis 030's
        M5-RUNNING-outcome bug).

        Default ``None``: any complete ends iteration. Backward-
        compatible with the CLI and test_runner callers that drive
        single-thread runs and expect the original behavior.
        """
        while True:
            event = await self._event_queue.get()
            yield event
            if event.kind in ("aborted", "timeout"):
                return
            if event.kind == "complete":
                if terminal_thread_id is None:
                    # No filter: any complete ends iteration (legacy
                    # contract for single-thread callers).
                    return
                event_thread_id = (event.payload or {}).get("thread_id")
                if event_thread_id is None or event_thread_id == terminal_thread_id:
                    return
                # Stale complete from a different thread — keep going.

    async def respond_to_escalation(self, prompt_id: str, response: str) -> None:
        """Feed a human response into a pending escalation prompt.

        The response gets relayed by the Dodo as a follow-up directive
        ("Human resolution: <response>") so the team sees it as the
        team-leader speaking. Per the spec's escalation flow, this is
        what the framework calls "the human's call" — surfacing a
        provisional decision the team can adopt and adjust.
        """
        pending = self._pending_escalations.pop(prompt_id, None)
        if pending is None:
            raise ValueError(f"No pending escalation with id {prompt_id}")
        pending.response_future.set_result(response)

    def abort(self, reason: str = "user requested") -> None:
        """Mark the run as aborted; teardown happens in the finally block."""
        if self._aborted:
            return
        self._aborted = True
        # Wake any pause-waiters so cancellation propagates cleanly.
        # Otherwise an aborted-while-paused run would block in the
        # ``await self._paused.wait()`` call inside the meeting
        # dispatcher and never reach the abort handling below.
        self._paused.set()
        self._event_queue.put_nowait(
            RunnerEvent(
                kind="aborted",
                elapsed=self._elapsed(),
                payload={"reason": reason},
            )
        )

    def pause(self) -> None:
        """Pause the run. New rotations don't open until resume();
        in-flight LLM calls finish naturally (they're not cancelled
        mid-deliberation — that would risk corrupting partial
        emissions). Idempotent on re-pause."""
        self._paused.clear()

    def resume(self) -> None:
        """Resume from pause. Idempotent on re-resume."""
        self._paused.set()

    @property
    def is_paused(self) -> bool:
        """True iff pause() has been called and resume() hasn't yet
        followed. UI consumers read this to render Pause vs Resume
        labels on the same button."""
        return not self._paused.is_set()

    # ------------------------------------------------------------------ #
    # Internal consumers
    # ------------------------------------------------------------------ #

    async def _consume_bus(self) -> None:
        async for u in self._observer:
            await self._event_queue.put(
                RunnerEvent(
                    kind="utterance",
                    elapsed=self._elapsed(),
                    payload={"utterance": u},
                )
            )

    # ------------------------------------------------------------------ #
    # User-question affordance (T69)
    # ------------------------------------------------------------------ #

    def set_user_question_handler(
        self,
        handler: Callable[[Utterance], Any] | None,
    ) -> None:
        """Register an async handler for user questions. The handler
        receives the QUESTION-to-operator utterance and returns the
        user's reply text (str) or returns/raises something that the
        watcher will treat as 'no answer' (sentinel reply published).

        For TUI runs, the handler shows a modal and awaits user
        input. For headless runs, leave None — the watcher publishes
        a 'no operator available' sentinel so the team proceeds with
        their best judgment.
        """
        self._user_question_handler = handler

    async def _watch_user_questions(self) -> None:
        """Background task: subscribe to bus, detect QUESTION-to-
        operator, invoke handler, publish OBSERVATION-from-operator.

        Runs for the lifetime of the runner. Each detected question
        is processed sequentially — multiple questions queue rather
        than fan out, so the operator sees them one at a time.
        """
        from wonderland.utterance import (
            UtteranceContent,
            is_question_to_operator,
            operator_identity,
        )

        sub = self.bus.subscribe(
            agent_name="user-question-watcher", bypass_roster=True
        )
        async for u in sub:
            if not is_question_to_operator(u):
                continue
            # Suspend quiescence detection on this thread while
            # we wait for the operator. Without this, the asker's
            # post-publish IDLE transition would trigger turn-
            # based quiescence (or the 300s wall-clock fallback
            # would fire while the operator reads the question).
            self._monitor.pause_for_external_input(u.thread_id)
            try:
                if self._user_question_handler is None:
                    answer_text = (
                        "(no operator available; proceed with your "
                        "best judgment based on existing context)"
                    )
                else:
                    answer_text = await self._user_question_handler(u)
                    if not isinstance(answer_text, str) or not answer_text:
                        answer_text = (
                            "(operator skipped; proceed with your "
                            "best judgment)"
                        )
            except Exception as exc:  # noqa: BLE001
                # Handler failure should not deadlock the meeting.
                # Publish a sentinel and log; agents can still
                # proceed.
                answer_text = (
                    f"(operator handler error: {type(exc).__name__}; "
                    "proceed with your best judgment)"
                )
            finally:
                # Always resume quiescence — even on handler error
                # — so the meeting doesn't get stuck paused.
                self._monitor.resume_for_external_input(u.thread_id)

            answer_utt = Utterance(
                thread_id=u.thread_id,
                speaker=operator_identity(),
                addressed_to=[u.speaker],
                speech_act=SpeechAct.OBSERVATION,
                content=UtteranceContent(body=answer_text),
                parent_id=u.id,
            )
            await self.bus.publish(answer_utt)
            self._answered_questions[u.id] = answer_utt
            future = self._pending_question_futures.pop(u.id, None)
            if future is not None and not future.done():
                future.set_result(answer_utt)

    async def wait_for_question_answer(
        self,
        question_id: str,
        timeout: float = 600.0,
    ) -> Utterance:
        """Block until the operator's OBSERVATION reply for a given
        QUESTION-to-operator utterance lands on the bus. Returns
        immediately if the answer has already been published.

        Phased meetings call this after an agent's window resolved
        with a question utterance — guarantees the next agent's
        compose_context sees the operator's reply rather than
        racing the watcher's publish."""
        if question_id in self._answered_questions:
            return self._answered_questions[question_id]
        future = self._pending_question_futures.setdefault(
            question_id, asyncio.Future()
        )
        return await asyncio.wait_for(future, timeout=timeout)

    async def _consume_states(self) -> None:
        async for change in self._monitor.transitions():
            await self._event_queue.put(
                RunnerEvent(
                    kind="state",
                    elapsed=self._elapsed(),
                    payload={"change": change},
                )
            )
            await self._react_to_state(change)

    async def _react_to_state(self, change: ThreadStateChange) -> None:
        """Dispatch the structural anti-deadlock behavior the Dodo owns (T33)."""
        if change.to_state is ThreadState.STUCK:
            self._monitor.record_nudge(change.thread_id)
            await self.dodo.nudge(change.thread_id, reason=change.reason)
        elif change.to_state is ThreadState.DEADLOCKED:
            await self._escalate_via_runner(change.thread_id, reason=change.reason)
        elif change.to_state is ThreadState.QUIESCENT:
            await self.dodo.acknowledge(
                change.thread_id,
                state="complete",
                body=(
                    f"Thread {change.thread_id} → complete. The team has gone "
                    "quiet with no open expectations; the directive is settled."
                ),
            )
        elif change.to_state is ThreadState.COMPLETE:
            self._completed = True
            await self._event_queue.put(
                RunnerEvent(
                    kind="complete",
                    elapsed=self._elapsed(),
                    payload={"thread_id": change.thread_id},
                )
            )

    async def _consume_consensus(self) -> None:
        async for alert in self._consensus_guard.alerts():
            await self._event_queue.put(
                RunnerEvent(
                    kind="consensus_alert",
                    elapsed=self._elapsed(),
                    payload={"alert": alert},
                )
            )

    async def _check_budget(self) -> None:
        """Periodically check the running cost; warn / escalate when needed."""
        assert self.budget_dollars is not None
        warning_threshold = self.budget_dollars * self.BUDGET_WARNING_FRACTION
        while True:
            await asyncio.sleep(self.BUDGET_CHECK_INTERVAL_SECONDS)
            cost = self.telemetry.total_cost
            if cost >= self.budget_dollars and not self._budget_exceeded:
                self._budget_exceeded = True
                await self._event_queue.put(
                    RunnerEvent(
                        kind="budget_exceeded",
                        elapsed=self._elapsed(),
                        payload={
                            "cost": cost,
                            "budget": self.budget_dollars,
                        },
                    )
                )
                # Trigger an escalation so the human can decide:
                # continue (raise budget), abort, or change scope.
                await self._escalate_via_runner(
                    "main",
                    reason=(f"budget exceeded: ${cost:.2f} > ${self.budget_dollars:.2f}"),
                )
            elif cost >= warning_threshold and not self._budget_warned:
                self._budget_warned = True
                await self._event_queue.put(
                    RunnerEvent(
                        kind="budget_warning",
                        elapsed=self._elapsed(),
                        payload={
                            "cost": cost,
                            "budget": self.budget_dollars,
                            "fraction": cost / self.budget_dollars,
                        },
                    )
                )

    async def _enforce_timeout(self) -> None:
        # Only scheduled when timeout_seconds is not None — see setup().
        # Belt-and-suspenders: bail if it somehow gets called with None.
        timeout = self.timeout_seconds
        if timeout is None:
            return
        await asyncio.sleep(timeout)
        if self._completed or self._aborted:
            return
        await self._event_queue.put(
            RunnerEvent(
                kind="timeout",
                elapsed=self._elapsed(),
                payload={"timeout_seconds": timeout},
            )
        )

    # ------------------------------------------------------------------ #
    # Interactive escalation
    # ------------------------------------------------------------------ #

    async def _escalate_via_runner(self, thread_id: str, *, reason: str) -> None:
        """Use the Dodo's escalate_deadlock with the Runner's interactive channel.

        The channel emits an ``escalation_prompt`` event and waits for
        ``respond_to_escalation()``. When the response arrives, the
        channel relays it as a Dodo directive so the team sees the
        human's call and resumes work.
        """
        if self.dodo.escalation_registry is None:
            # No registry — fall back to logged acknowledge (the showcase
            # script's existing fallback path).
            await self.dodo.acknowledge(
                thread_id,
                state="deadlocked",
                body=(
                    f"Thread {thread_id} → deadlocked ({reason}); no escalation "
                    "registry to record the brief."
                ),
            )
            return

        await self.dodo.escalate_deadlock(
            thread_id,
            reason=reason,
            channel=self._interactive_channel,
        )

    async def _interactive_channel(self, brief: EscalationBrief, record: EscalationRecord) -> None:
        """The escalation channel that drives human-in-the-loop.

        Emits an ``escalation_prompt`` event, awaits the human's
        response via ``respond_to_escalation()``, then relays the
        response as a Dodo follow-up directive so the team sees it and
        resumes work.
        """
        prompt_id = str(uuid.uuid4())
        future: asyncio.Future[str] = asyncio.get_event_loop().create_future()
        pending = _PendingEscalation(
            prompt_id=prompt_id, brief=brief, record=record, response_future=future
        )
        self._pending_escalations[prompt_id] = pending

        await self._event_queue.put(
            RunnerEvent(
                kind="escalation_prompt",
                elapsed=self._elapsed(),
                payload={
                    "prompt_id": prompt_id,
                    "brief": brief,
                    "record_path": str(record.path),
                },
            )
        )

        try:
            response = await future
        except asyncio.CancelledError:
            # Runner is being torn down. Re-raise so the cancellation
            # propagates up the call chain — catching and returning
            # silently here would suppress cancellation and the budget
            # task would never finish, deadlocking teardown.
            raise

        # Relay the human response as a Dodo directive so the team
        # sees it as the team-leader speaking and resumes work.
        await self.dodo.relay_directive(
            body=f"Human resolution: {response}",
            thread_id=brief.thread_id,
        )

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _elapsed(self) -> float:
        if self._start_monotonic is None:
            return 0.0
        return time.monotonic() - self._start_monotonic

    @property
    def total_cost(self) -> float:
        return self.telemetry.total_cost


__all__ = [
    "EventKind",
    "Runner",
    "RunnerEvent",
]
