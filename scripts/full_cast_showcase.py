"""Full-cast showcase — all 10 agents on one bus, autonomous, on a real directive.

Where ``health_endpoint_showcase.py`` ran four agents on a trivial
operational change, this runs the entire cast (Cat, Rabbit, Alice,
Dodo, Hatter, Caterpillar, Queen, Dormouse, Tweedledee, Tweedledum)
on the translation-chat scenario the voices sweep used in isolation.

The scenario was chosen for two reasons. First, it has surface in
every domain — user need (Alice), architecture (Cat), sequence
(Rabbit), test scenarios (Hatter), code review (Caterpillar),
security/compliance (Queen, GDPR keyword present), production
(Dormouse), implementation (Tweedles). Second, it provides clean
continuity with analysis 005 — the same root scenario, with the
agents now able to interact rather than only respond in isolation.

The synthetic-consensus guard runs alongside the team. When agents
from distinct constitutional domains converge on the same answer,
the guard surfaces the pattern. The hypothesis: real disagreement
should keep the guard quiet most of the time. If it fires, the
alert is informative either way.

Usage:
    uv run python scripts/full_cast_showcase.py
    uv run python scripts/full_cast_showcase.py --project-root ./showcase-output
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

from wonderland import (
    ADRRegistry,
    AgentMemory,
    Alice,
    Caterpillar,
    CheshireCat,
    ConsensusAlert,
    Dodo,
    Dormouse,
    EscalationRegistry,
    ImplementationRegistry,
    InMemoryCaucus,
    LLMClient,
    MadHatter,
    ObservationRegistry,
    QueenOfHearts,
    ReviewRegistry,
    RulingRegistry,
    StoryRegistry,
    SyntheticConsensusGuard,
    TestScenarioRegistry,
    ThreadMonitor,
    ThreadState,
    TicketRegistry,
    TokenUsage,
    Tweedledee,
    Tweedledum,
    Utterance,
    WhiteRabbit,
)

DEFAULT_DIRECTIVE = (
    "Build a translation-integrated chat application MVP. Two users in "
    "different language groups exchanging short messages with near-real-"
    "time translation. EU consumer scope (GDPR applies). Target: "
    "shippable v1 in three weeks. Initial scope: text-only messages, "
    "two-language pairs at launch (English ↔ German, English ↔ Japanese), "
    "no message edit, no message delete, basic auth. Looking for the team "
    "to scope, decompose, and identify the ship-blocking decisions."
)

DEFAULT_TIMEOUT_S = 600.0
DEFAULT_QUIESCENCE_S = 30.0


# --------------------------------------------------------------------- #
# Pretty printers
# --------------------------------------------------------------------- #


def section(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def print_utterance(u: Utterance, *, elapsed: float) -> None:
    print(f"\n[t={elapsed:6.2f}s]  {u.speaker.name} — {u.speech_act.value}")
    body = u.content.body.strip()
    if body:
        for line in body.splitlines():
            print(f"   {line}")
    if u.content.artifacts:
        print(f"   artifacts ({len(u.content.artifacts)}):")
        for artifact in u.content.artifacts:
            payload = artifact.payload
            title = payload.get("title", payload.get("decision_required", "?"))
            severity = payload.get("severity", payload.get("verdict", ""))
            extra = f"  [{severity}]" if severity else ""
            print(f"     - {artifact.kind}: {title}{extra}")


def print_artifact_files(project_root: Path) -> None:
    section("Artifacts on disk")
    artifact_dirs = [
        ("stories", "Alice"),
        ("architecture", "Cat (ADRs)"),
        ("tickets", "Rabbit"),
        ("test-scenarios", "Hatter"),
        ("reviews", "Caterpillar"),
        ("rulings", "Queen"),
        ("observations", "Dormouse"),
        ("implementations", "Tweedles"),
        ("escalations", "Dodo"),
    ]
    for dirname, owner in artifact_dirs:
        subdir = project_root / ".wonderland" / dirname
        if not subdir.is_dir():
            continue
        files = sorted(p for p in subdir.iterdir() if p.is_file() and p.suffix == ".md")
        if files:
            print(f"\n  {owner} → {dirname}/ ({len(files)}):")
            for path in files:
                print(f"    - {path.relative_to(project_root)}")


# --------------------------------------------------------------------- #
# Showcase
# --------------------------------------------------------------------- #


async def run_showcase(
    directive: str,
    project_root: Path,
    *,
    timeout: float,
    quiescence_seconds: float,
) -> int:
    print("=" * 72)
    print("Wonderland — Full-Cast Showcase (10 agents, end-to-end)")
    print("=" * 72)
    print(f"Project root: {project_root}")
    print(f"Quiescence threshold: {quiescence_seconds:.1f}s of bus-silence with no open expectations")
    print(f"Hard timeout: {timeout:.0f}s")

    usage: dict[str, list[TokenUsage]] = defaultdict(list)

    def usage_cb(name: str):
        def _cb(u: TokenUsage) -> None:
            usage[name].append(u)
        return _cb

    bus = InMemoryCaucus()

    # Open per-agent memory in parallel
    agent_names = (
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
    )
    memories = {name: AgentMemory.for_project(project_root, name) for name in agent_names}
    for mem in memories.values():
        await mem.open()

    # Construct each agent with its registry. Per-agent LLMClient so per-agent
    # token attribution is clean.
    alice = Alice(
        memory=memories["alice"],
        bus=bus,
        llm=LLMClient(on_token_usage=usage_cb("alice")),
        story_registry=StoryRegistry(project_root),
    )
    cat = CheshireCat(
        memory=memories["cheshire_cat"],
        bus=bus,
        llm=LLMClient(on_token_usage=usage_cb("cheshire_cat")),
        adr_registry=ADRRegistry(project_root),
    )
    rabbit = WhiteRabbit(
        memory=memories["white_rabbit"],
        bus=bus,
        llm=LLMClient(on_token_usage=usage_cb("white_rabbit")),
        ticket_registry=TicketRegistry(project_root),
    )
    dodo = Dodo(
        memory=memories["dodo"],
        bus=bus,
        llm=LLMClient(on_token_usage=usage_cb("dodo")),
        escalation_registry=EscalationRegistry(project_root),
    )
    hatter = MadHatter(
        memory=memories["mad_hatter"],
        bus=bus,
        llm=LLMClient(on_token_usage=usage_cb("mad_hatter")),
        test_scenario_registry=TestScenarioRegistry(project_root),
    )
    caterpillar = Caterpillar(
        memory=memories["caterpillar"],
        bus=bus,
        llm=LLMClient(on_token_usage=usage_cb("caterpillar")),
        review_registry=ReviewRegistry(project_root),
    )
    queen = QueenOfHearts(
        memory=memories["queen_of_hearts"],
        bus=bus,
        llm=LLMClient(on_token_usage=usage_cb("queen_of_hearts")),
        ruling_registry=RulingRegistry(project_root),
    )
    dormouse = Dormouse(
        memory=memories["dormouse"],
        bus=bus,
        llm=LLMClient(on_token_usage=usage_cb("dormouse")),
        observation_registry=ObservationRegistry(project_root),
    )
    dee = Tweedledee(
        memory=memories["tweedledee"],
        bus=bus,
        llm=LLMClient(on_token_usage=usage_cb("tweedledee")),
        implementation_registry=ImplementationRegistry(project_root),
    )
    dum = Tweedledum(
        memory=memories["tweedledum"],
        bus=bus,
        llm=LLMClient(on_token_usage=usage_cb("tweedledum")),
        implementation_registry=ImplementationRegistry(project_root),
    )

    agents = [alice, cat, rabbit, dodo, hatter, caterpillar, queen, dormouse, dee, dum]

    # Subscribe observers BEFORE the directive lands — synchronous registration
    # is a virtue for any consumer that should not miss events.
    monitor = ThreadMonitor(bus, quiescence_seconds=quiescence_seconds)
    await monitor.start()

    consensus_guard = SyntheticConsensusGuard(
        bus,
        min_agents=3,
        similarity_threshold=0.5,
        window_size=20,
        shingle_size=2,
    )
    await consensus_guard.start()

    observer = bus.subscribe(agent_name="showcase-printer")

    start = time.monotonic()
    thread_id = "translation-chat-mvp"
    completion_event = asyncio.Event()
    consensus_alerts: list[ConsensusAlert] = []
    state_log: list[str] = []

    section("Directive")
    print(directive)
    section("Dance")

    async def printer() -> None:
        async for u in observer:
            print_utterance(u, elapsed=time.monotonic() - start)
            sys.stdout.flush()

    async def state_watcher() -> None:
        async for change in monitor.transitions():
            elapsed = time.monotonic() - start
            line = (
                f"\n[t={elapsed:6.2f}s]  thread_monitor — "
                f"{change.from_state.value} → {change.to_state.value}  ({change.reason})"
            )
            print(line)
            sys.stdout.flush()
            state_log.append(line.strip())

            if change.to_state is ThreadState.QUIESCENT:
                await dodo.acknowledge(
                    change.thread_id,
                    state="complete",
                    body=(
                        f"Thread {change.thread_id} → complete. The team has gone "
                        "quiet with no open expectations; the directive is settled."
                    ),
                )
            elif change.to_state in (ThreadState.STUCK, ThreadState.DEADLOCKED):
                print(
                    f"   (showcase note: thread is {change.to_state.value}; "
                    "a real team would resolve via Dodo nudge → conflict ladder.)"
                )
            elif change.to_state is ThreadState.COMPLETE:
                completion_event.set()

    async def consensus_watcher() -> None:
        async for alert in consensus_guard.alerts():
            elapsed = time.monotonic() - start
            print(
                f"\n[t={elapsed:6.2f}s]  consensus_guard — "
                f"{alert.speech_act.value} convergence across "
                f"{', '.join(alert.agents)} ({alert.average_pairwise_similarity:.2f})"
            )
            sys.stdout.flush()
            consensus_alerts.append(alert)

    printer_task = asyncio.create_task(printer(), name="showcase-printer")
    watcher_task = asyncio.create_task(state_watcher(), name="showcase-state-watcher")
    consensus_task = asyncio.create_task(consensus_watcher(), name="showcase-consensus")
    agent_tasks = [
        asyncio.create_task(agent.run(), name=f"{agent.identity.name}-run") for agent in agents
    ]

    exit_code = 0
    try:
        await dodo.relay_directive(directive, thread_id=thread_id)
        try:
            await asyncio.wait_for(completion_event.wait(), timeout=timeout)
        except TimeoutError:
            print(
                f"\nTIMEOUT: thread did not reach COMPLETE within {timeout:.0f}s.",
                file=sys.stderr,
            )
            print(
                f"  Last observed state: {monitor.thread_state(thread_id).value}",
                file=sys.stderr,
            )
            exit_code = 1
    finally:
        elapsed_total = time.monotonic() - start

        print_artifact_files(project_root)

        section("Consensus alerts")
        if consensus_alerts:
            for alert in consensus_alerts:
                print(
                    f"\n  {alert.speech_act.value} convergence  [avg sim "
                    f"{alert.average_pairwise_similarity:.2f}]"
                )
                print(f"    agents:  {', '.join(alert.agents)}")
                print(f"    domains: {', '.join(alert.domains)}")
                print(f"    reason:  {alert.reason}")
        else:
            print(
                "\n  (none — the team produced disagreement, not synthetic consensus.)"
            )

        section("Token usage (per agent, summed across calls)")
        total_in = 0
        total_out = 0
        for name in agent_names:
            calls = usage[name]
            if not calls:
                print(f"  {name:18s}: (no LLM calls)")
                continue
            ti = sum(u.input_tokens for u in calls)
            to = sum(u.output_tokens for u in calls)
            tcw = sum(u.cache_creation_input_tokens for u in calls)
            tcr = sum(u.cache_read_input_tokens for u in calls)
            total_in += ti
            total_out += to
            print(
                f"  {name:18s}: calls={len(calls):2d}  "
                f"in={ti:6d}  out={to:5d}  cache_w={tcw:5d}  cache_r={tcr:5d}"
            )
        print(f"\n  {'TOTAL':18s}: in={total_in:6d}  out={total_out:5d}")

        section("Timing + outcome")
        print(f"  end-to-end: {elapsed_total:.2f}s")
        if completion_event.is_set():
            print("  outcome:    COMPLETE (Dodo acknowledged on quiescence)")
        else:
            print(f"  outcome:    {monitor.thread_state(thread_id).value} (timed out)")

        section("Thread state log")
        for line in state_log:
            print(f"  {line}")

        # Teardown
        for agent in agents:
            await agent.stop()
        await monitor.stop()
        await consensus_guard.stop()
        for task in (*agent_tasks, watcher_task, consensus_task, printer_task):
            task.cancel()
        for task in (*agent_tasks, watcher_task, consensus_task, printer_task):
            with contextlib.suppress(asyncio.CancelledError):
                await task
        for mem in memories.values():
            await mem.close()

    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the full-cast showcase.")
    parser.add_argument("--directive", default=DEFAULT_DIRECTIVE)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Where to write .wonderland/ artifacts. Default: a fresh tempdir.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_S,
        help=f"Hard cap on the run, in seconds (default {DEFAULT_TIMEOUT_S:.0f}).",
    )
    parser.add_argument(
        "--quiescence-seconds",
        type=float,
        default=DEFAULT_QUIESCENCE_S,
        help=(
            f"Bus-silence required before the ThreadMonitor calls quiescence "
            f"(default {DEFAULT_QUIESCENCE_S:.1f})."
        ),
    )
    args = parser.parse_args()

    if args.project_root is None:
        with tempfile.TemporaryDirectory(prefix="wonderland-full-cast-") as tmp:
            return asyncio.run(
                run_showcase(
                    args.directive,
                    Path(tmp),
                    timeout=args.timeout,
                    quiescence_seconds=args.quiescence_seconds,
                )
            )
    args.project_root.mkdir(parents=True, exist_ok=True)
    return asyncio.run(
        run_showcase(
            args.directive,
            args.project_root,
            timeout=args.timeout,
            quiescence_seconds=args.quiescence_seconds,
        )
    )


if __name__ == "__main__":
    sys.exit(main())
