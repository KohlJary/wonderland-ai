"""Tweedle dance — Dee + Dum on a contract that has to be negotiated.

The full-cast race (analysis 006) showed the Tweedles surfacing
frontend-backend coupling concerns to *the team*. This demo isolates
just the pair (with the Cat as architectural arbiter only if they
escalate) and gives them a directive whose contract has genuine
ambiguity at the seam — message editing.

Why message editing: per the Pair Protocol §II "implicit contracts
are bugs in the making", and the message-edit feature has at least
three contract-shape questions neither Tweedle can resolve alone:

- **Message-id stability**: does an edit produce a new id, or
  preserve the original?
- **Translation invalidation**: when the source is edited, what
  happens to translations the recipient has already seen?
- **Pair-protocol ambiguity**: who owns the question of "what does
  the recipient observe at the moment of an edit" — is that a
  frontend display contract or a backend event-shape contract?

The hypothesis: the pair should produce Contract Notes (concerns or
implementations with explicit contract refs), iterate on each
other's positions, and either converge (publish implementations
that compose) or escalate to the Cat. Per the Pair Protocol §VII,
escalation is appropriate when the disagreement is genuinely
architectural — not as a way to avoid arguing.

Usage:
    uv run python scripts/tweedle_dance_demo.py
    uv run python scripts/tweedle_dance_demo.py --project-root ./dance-output
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
    AgentIdentity,
    AgentMemory,
    CheshireCat,
    Dodo,
    EscalationRegistry,
    ImplementationRegistry,
    InMemoryCaucus,
    LLMClient,
    SpeechAct,
    ThreadMonitor,
    ThreadState,
    TokenUsage,
    Tweedledee,
    Tweedledum,
    Utterance,
    UtteranceContent,
)

DEFAULT_TICKET = """\
Ticket-021: Add message editing to the translation chat.

Users should be able to edit messages they've sent. The pair (Tweedledee +
Tweedledum) needs to converge on a contract for this. Specifically, the
following questions are at the seam and must be answered together:

1. **Message-id stability**: when a user edits a message, does the message
   keep its original ID (the edit is in-place, with a revision counter), or
   does the edit create a new message that supersedes the original (each
   revision has its own ID)?

2. **Translation invalidation**: when the source message is edited, what
   happens to translations the recipient has already seen? Are they
   invalidated and re-fetched, marked as stale and shown alongside the new
   translation, or replaced silently?

3. **Real-time event shape**: when an edit occurs, what does the recipient's
   client see? A `message-edited` event with the new content? A
   `message-translated` event with a different message_id? Both?

Acceptance criteria:
- Both Tweedles publish implementations whose contracts agree on the
  same answers to (1), (2), and (3).
- The implementation utterances reference the same contract version.
- If the pair cannot agree, they explicitly escalate to the Cat.

Owner: tweedledee + tweedledum (paired).
Tier: v1.
Estimate: 3 days, 60% confident (the contract negotiation is the risk).
"""

DEFAULT_TIMEOUT_S = 240.0
DEFAULT_QUIESCENCE_S = 30.0


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
            title = payload.get("title", "?")
            extra_bits = []
            if "side" in payload:
                extra_bits.append(payload["side"])
            if payload.get("contract"):
                extra_bits.append(f"contract={payload['contract'][:60]}")
            extra = f"  [{', '.join(extra_bits)}]" if extra_bits else ""
            print(f"     - {artifact.kind}: {title}{extra}")


async def run_dance(
    ticket_body: str,
    project_root: Path,
    *,
    timeout: float,
    quiescence_seconds: float,
) -> int:
    print("=" * 72)
    print("Wonderland — Tweedle Dance (Dee + Dum, Cat on standby)")
    print("=" * 72)
    print(f"Project root: {project_root}")
    print(f"Quiescence threshold: {quiescence_seconds:.1f}s")

    usage: dict[str, list[TokenUsage]] = defaultdict(list)

    def usage_cb(name: str):
        def _cb(u: TokenUsage) -> None:
            usage[name].append(u)
        return _cb

    bus = InMemoryCaucus()

    dee_memory = AgentMemory.for_project(project_root, "tweedledee")
    dum_memory = AgentMemory.for_project(project_root, "tweedledum")
    cat_memory = AgentMemory.for_project(project_root, "cheshire_cat")
    dodo_memory = AgentMemory.for_project(project_root, "dodo")
    for mem in (dee_memory, dum_memory, cat_memory, dodo_memory):
        await mem.open()

    impl_registry = ImplementationRegistry(project_root)

    dee = Tweedledee(
        memory=dee_memory,
        bus=bus,
        llm=LLMClient(on_token_usage=usage_cb("tweedledee")),
        implementation_registry=impl_registry,
    )
    dum = Tweedledum(
        memory=dum_memory,
        bus=bus,
        llm=LLMClient(on_token_usage=usage_cb("tweedledum")),
        implementation_registry=impl_registry,
    )
    cat = CheshireCat(
        memory=cat_memory,
        bus=bus,
        llm=LLMClient(on_token_usage=usage_cb("cheshire_cat")),
        adr_registry=ADRRegistry(project_root),
    )
    dodo = Dodo(
        memory=dodo_memory,
        bus=bus,
        llm=LLMClient(on_token_usage=usage_cb("dodo")),
        escalation_registry=EscalationRegistry(project_root),
    )

    monitor = ThreadMonitor(bus, quiescence_seconds=quiescence_seconds)
    await monitor.start()

    observer = bus.subscribe(agent_name="dance-printer")

    start = time.monotonic()
    thread_id = "tweedle-dance"
    completion_event = asyncio.Event()
    state_log: list[str] = []

    section("Ticket (synthesized as if from the Rabbit)")
    print(ticket_body)
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
                f"{change.from_state.value} → {change.to_state.value}  "
                f"({change.reason})"
            )
            print(line)
            sys.stdout.flush()
            state_log.append(line.strip())

            if change.to_state is ThreadState.QUIESCENT:
                await dodo.acknowledge(
                    change.thread_id,
                    state="complete",
                    body=(
                        f"Thread {change.thread_id} → complete. The pair has "
                        "converged or escalated; the dance is settled."
                    ),
                )
            elif change.to_state is ThreadState.COMPLETE:
                completion_event.set()

    printer_task = asyncio.create_task(printer())
    watcher_task = asyncio.create_task(state_watcher())
    agents = [dee, dum, cat, dodo]
    agent_tasks = [
        asyncio.create_task(agent.run(), name=f"{agent.identity.name}-run")
        for agent in agents
    ]

    exit_code = 0
    try:
        # Synthesized Rabbit-shaped ticket — Tweedles ALWAYS engage with
        # tickets from the Rabbit per their §III rules.
        primer = Utterance(
            thread_id=thread_id,
            speaker=AgentIdentity(name="white_rabbit", constitution_version="0.2"),
            addressed_to="caucus",
            speech_act=SpeechAct.TICKET,
            content=UtteranceContent(body=ticket_body),
        )
        await bus.publish(primer)

        try:
            await asyncio.wait_for(completion_event.wait(), timeout=timeout)
        except TimeoutError:
            print(
                f"\nTIMEOUT: dance did not reach COMPLETE within {timeout:.0f}s.",
                file=sys.stderr,
            )
            exit_code = 1
    finally:
        elapsed_total = time.monotonic() - start

        section("Implementations on disk")
        impl_dir = project_root / ".wonderland" / "implementations"
        if impl_dir.is_dir():
            files = sorted(p for p in impl_dir.iterdir() if p.suffix == ".md")
            for path in files:
                print(f"  - {path.name}")

        section("Token usage (per agent)")
        total_in = 0
        total_out = 0
        for name in ("tweedledee", "tweedledum", "cheshire_cat", "dodo"):
            calls = usage[name]
            if not calls:
                print(f"  {name:14s}: (no LLM calls)")
                continue
            ti = sum(u.input_tokens for u in calls)
            to = sum(u.output_tokens for u in calls)
            tcr = sum(u.cache_read_input_tokens for u in calls)
            total_in += ti
            total_out += to
            print(
                f"  {name:14s}: calls={len(calls):2d}  "
                f"in={ti:6d}  out={to:5d}  cache_r={tcr:5d}"
            )
        print(f"\n  {'TOTAL':14s}: in={total_in:6d}  out={total_out:5d}")

        section("Outcome")
        print(f"  end-to-end: {elapsed_total:.2f}s")
        if completion_event.is_set():
            print("  outcome:    COMPLETE (Dodo acknowledged on quiescence)")
        else:
            print(f"  outcome:    {monitor.thread_state(thread_id).value} (timed out)")

        if state_log:
            section("Thread state log")
            for line in state_log:
                print(f"  {line}")

        for agent in agents:
            await agent.stop()
        await monitor.stop()
        for task in (*agent_tasks, watcher_task, printer_task):
            task.cancel()
        for task in (*agent_tasks, watcher_task, printer_task):
            with contextlib.suppress(asyncio.CancelledError):
                await task
        for mem in (dee_memory, dum_memory, cat_memory, dodo_memory):
            await mem.close()

    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Tweedle dance demo.")
    parser.add_argument("--ticket", default=DEFAULT_TICKET)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Where to write .wonderland/ artifacts. Default: a fresh tempdir.",
    )
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S)
    parser.add_argument("--quiescence-seconds", type=float, default=DEFAULT_QUIESCENCE_S)
    args = parser.parse_args()

    if args.project_root is None:
        with tempfile.TemporaryDirectory(prefix="wonderland-tweedle-dance-") as tmp:
            return asyncio.run(
                run_dance(
                    args.ticket,
                    Path(tmp),
                    timeout=args.timeout,
                    quiescence_seconds=args.quiescence_seconds,
                )
            )
    args.project_root.mkdir(parents=True, exist_ok=True)
    return asyncio.run(
        run_dance(
            args.ticket,
            args.project_root,
            timeout=args.timeout,
            quiescence_seconds=args.quiescence_seconds,
        )
    )


if __name__ == "__main__":
    sys.exit(main())
