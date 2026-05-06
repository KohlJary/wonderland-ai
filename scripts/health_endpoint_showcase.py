"""Showcase 1 — Dodo + Alice + Cat + Rabbit, end-to-end on a tiny directive.

Per WONDERLAND_SPEC §10 and dodo.md §VI: the system runs to "done"
because the team goes quiet, not because anyone said "we're done".
The Dodo relays a directive, three domain agents engage per their
constitutions, the ThreadMonitor notices when the bus goes silent
with no open expectations, and the Dodo records the close as an
acknowledgment of completion.

Usage:
    uv run python scripts/health_endpoint_showcase.py
    uv run python scripts/health_endpoint_showcase.py --directive "..."
    uv run python scripts/health_endpoint_showcase.py --project-root ./showcase-output

The transcript is printed inline as it arrives so a reader can
follow the dance in real time. Final summary lists artifacts written
under .wonderland/ plus per-agent token usage.
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
    CheshireCat,
    Dodo,
    EscalationRegistry,
    InMemoryCaucus,
    LLMClient,
    StoryRegistry,
    ThreadMonitor,
    ThreadState,
    TicketRegistry,
    TokenUsage,
    Utterance,
    WhiteRabbit,
)

DEFAULT_DIRECTIVE = (
    "Add a GET /health endpoint to our Phoenix web app. It will be polled "
    "every 5 seconds by our Kubernetes liveness probe — no other consumers "
    "in v1, no auth, no dependency checks. Return HTTP 200 with the JSON "
    'body {"status":"ok"} whenever the app is up. Ship as the next '
    "deploy."
)
DEFAULT_TIMEOUT_S = 180.0
DEFAULT_QUIESCENCE_S = 15.0


# --------------------------------------------------------------------- #
# Pretty printers
# --------------------------------------------------------------------- #


def section(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def print_utterance(u: Utterance, *, elapsed: float) -> None:
    print(f"\n[t={elapsed:5.2f}s]  {u.speaker.name} — {u.speech_act.value}")
    body = u.content.body.strip()
    if body:
        for line in body.splitlines():
            print(f"   {line}")
    if u.content.artifacts:
        print(f"   artifacts ({len(u.content.artifacts)}):")
        for artifact in u.content.artifacts:
            title = artifact.payload.get("title") or artifact.payload.get("decision_required", "?")
            print(f"     - {artifact.kind}: {title}")


def print_artifact_file(path: Path) -> None:
    if not path.is_file():
        return
    print()
    print(f"--- {path.parent.name}/{path.name} ---")
    print(path.read_text(encoding="utf-8"), end="")


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
    print("Wonderland — Showcase 1: /health endpoint, end-to-end")
    print("=" * 72)
    print(f"Project root: {project_root}")
    print(f"Quiescence threshold: {quiescence_seconds:.1f}s of silence with no open expectations")

    # Per-agent token usage — one LLMClient per agent so the callback can attribute.
    usage: dict[str, list[TokenUsage]] = defaultdict(list)

    def usage_cb(name: str):
        def _cb(u: TokenUsage) -> None:
            usage[name].append(u)

        return _cb

    bus = InMemoryCaucus()

    alice_memory = AgentMemory.for_project(project_root, "alice")
    cat_memory = AgentMemory.for_project(project_root, "cheshire_cat")
    rabbit_memory = AgentMemory.for_project(project_root, "white_rabbit")
    dodo_memory = AgentMemory.for_project(project_root, "dodo")
    for mem in (alice_memory, cat_memory, rabbit_memory, dodo_memory):
        await mem.open()

    alice = Alice(
        memory=alice_memory,
        bus=bus,
        llm=LLMClient(on_token_usage=usage_cb("alice")),
        story_registry=StoryRegistry(project_root),
    )
    cat = CheshireCat(
        memory=cat_memory,
        bus=bus,
        llm=LLMClient(on_token_usage=usage_cb("cheshire_cat")),
        adr_registry=ADRRegistry(project_root),
    )
    rabbit = WhiteRabbit(
        memory=rabbit_memory,
        bus=bus,
        llm=LLMClient(on_token_usage=usage_cb("white_rabbit")),
        ticket_registry=TicketRegistry(project_root),
    )
    dodo = Dodo(
        memory=dodo_memory,
        bus=bus,
        llm=LLMClient(on_token_usage=usage_cb("dodo")),
        escalation_registry=EscalationRegistry(project_root),
    )

    # ThreadMonitor must subscribe before the directive lands so it sees every
    # utterance from t=0. Same lesson as T14 — synchronous registration is a
    # virtue for any consumer that should not miss events.
    monitor = ThreadMonitor(bus, quiescence_seconds=quiescence_seconds)
    await monitor.start()

    observer = bus.subscribe(agent_name="showcase-printer")

    start = time.monotonic()
    thread_id = "health-thread"

    section("Directive")
    print(directive)
    section("Dance")

    completion_event = asyncio.Event()
    final_state: dict[str, ThreadState | None] = {"state": None}

    async def printer() -> None:
        async for u in observer:
            print_utterance(u, elapsed=time.monotonic() - start)
            sys.stdout.flush()

    async def state_watcher() -> None:
        async for change in monitor.transitions():
            elapsed = time.monotonic() - start
            print(
                f"\n[t={elapsed:5.2f}s]  thread_monitor — "
                f"{change.from_state.value} → {change.to_state.value}  ({change.reason})"
            )
            sys.stdout.flush()

            # Happy path: when the team goes quiet with nothing pending, the
            # Dodo records completion. That published acknowledgment will
            # itself trigger the COMPLETE transition on its way past.
            if change.to_state is ThreadState.QUIESCENT:
                await dodo.acknowledge(
                    change.thread_id,
                    state="complete",
                    body=(
                        f"Thread {change.thread_id} → complete. The team has gone quiet "
                        "with no open expectations; the directive is settled."
                    ),
                )
            elif change.to_state in (ThreadState.STUCK, ThreadState.DEADLOCKED):
                # Showcase 1 doesn't exercise the conflict ladder; surface the
                # problem and let the timeout catch us if we can't recover.
                print(
                    f"   (showcase note: thread is {change.to_state.value}; "
                    "the conflict ladder would normally engage here.)"
                )
            elif change.to_state is ThreadState.COMPLETE:
                final_state["state"] = ThreadState.COMPLETE
                completion_event.set()

    printer_task = asyncio.create_task(printer(), name="showcase-printer")
    watcher_task = asyncio.create_task(state_watcher(), name="showcase-state-watcher")
    agent_tasks = [
        asyncio.create_task(alice.run(), name="alice-run"),
        asyncio.create_task(cat.run(), name="cat-run"),
        asyncio.create_task(rabbit.run(), name="rabbit-run"),
        asyncio.create_task(dodo.run(), name="dodo-run"),
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
        # Summary first while everything's still in scope, then teardown.
        elapsed_total = time.monotonic() - start

        section("Artifacts on disk")
        for kind, subdir in [
            ("stories", project_root / ".wonderland" / "stories"),
            ("architecture (ADRs)", project_root / ".wonderland" / "architecture"),
            ("tickets", project_root / ".wonderland" / "tickets"),
            ("escalations", project_root / ".wonderland" / "escalations"),
        ]:
            if subdir.is_dir():
                files = sorted(p for p in subdir.iterdir() if p.is_file() and p.suffix == ".md")
                if files:
                    print(f"\n  {kind} ({len(files)}):")
                    for path in files:
                        print(f"    - {path.relative_to(project_root)}")
                    for path in files:
                        print_artifact_file(path)

        section("Token usage (per agent, summed across calls)")
        for name in ("alice", "cheshire_cat", "white_rabbit", "dodo"):
            calls = usage[name]
            if not calls:
                print(f"  {name:14s}: (no LLM calls)")
                continue
            total_in = sum(u.input_tokens for u in calls)
            total_out = sum(u.output_tokens for u in calls)
            total_cache_w = sum(u.cache_creation_input_tokens for u in calls)
            total_cache_r = sum(u.cache_read_input_tokens for u in calls)
            print(
                f"  {name:14s}: calls={len(calls):2d}  "
                f"in={total_in:5d}  out={total_out:5d}  "
                f"cache_w={total_cache_w:5d}  cache_r={total_cache_r:5d}"
            )

        section("Timing")
        print(f"  end-to-end: {elapsed_total:.2f}s")
        if final_state["state"] is ThreadState.COMPLETE:
            print("  outcome:    COMPLETE (Dodo acknowledged on quiescence)")
        else:
            print(f"  outcome:    {monitor.thread_state(thread_id).value} (timed out)")

        # Teardown — stop agents, monitor, watcher, printer.
        for agent in (alice, cat, rabbit, dodo):
            await agent.stop()
        await monitor.stop()
        for task in (*agent_tasks, watcher_task, printer_task):
            task.cancel()
        for task in (*agent_tasks, watcher_task, printer_task):
            with contextlib.suppress(asyncio.CancelledError):
                await task
        for mem in (alice_memory, cat_memory, rabbit_memory, dodo_memory):
            await mem.close()

    return exit_code


# --------------------------------------------------------------------- #
# Entrypoint
# --------------------------------------------------------------------- #


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Wonderland Showcase 1 (/health).")
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
        with tempfile.TemporaryDirectory(prefix="wonderland-showcase-") as tmp:
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
