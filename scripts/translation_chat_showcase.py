"""Translation Chat MVP — full-cast showcase via the Runner (P6.T36).

Where ``full_cast_showcase.py`` hand-wired the bus + monitor + guard +
agents + per-event printer, this runs the same directive through the
T34 Runner so we get budget caps, telemetry, structured event stream,
and interactive escalation for free. Functionally equivalent demo;
much smaller wrapper.

Why this matters: the prior full-cast race (analysis 006) cost ~$8 and
timed out at 90s without the team converging — the polite-deadlock
pattern in full bloom. Since then T33 wired the Dodo's nudge ladder,
T34 added budget caps, T34 follow-on trimmed the framework primer
(analysis 009), and T35 added the Contract Note artifact (analysis
010). This showcase tests whether the combined fixes let the team
actually progress on a substantive directive within bounded cost.

Per the user's framing: this is *also* the scoping run for tool
integration. The Tweedles can write `implementation` artifacts but
can't actually emit code to disk. We let the run play out and watch
for the specific places where the team wants to ship something it
can't, so the eventual tool design is informed by evidence rather
than speculation.

Usage:
    uv run python scripts/translation_chat_showcase.py
    uv run python scripts/translation_chat_showcase.py --project-root ./out
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

from wonderland.runner import Runner, RunnerEvent

DEFAULT_DIRECTIVE = (
    "Build a translation-integrated chat application MVP. Two users in "
    "different language groups exchanging short messages with near-real-"
    "time translation. EU consumer scope (GDPR applies). Target: "
    "shippable v1 in three weeks. Initial scope: text-only messages, "
    "two-language pairs at launch (English ↔ German, English ↔ Japanese), "
    "no message edit, no message delete, basic auth. Looking for the team "
    "to scope, decompose, and identify the ship-blocking decisions."
)

DEFAULT_TIMEOUT_S = 300.0
DEFAULT_QUIESCENCE_S = 30.0
DEFAULT_BUDGET = 3.00


def _format_event(event: RunnerEvent) -> str | None:
    """Return a human-readable line for an event, or None to skip."""
    elapsed = event.elapsed
    kind = event.kind
    if kind == "utterance":
        u = event.payload["utterance"]
        first_line = u.content.body.strip().split("\n", 1)[0]
        snippet = first_line[:140] + ("…" if len(first_line) > 140 else "")
        line = f"[t={elapsed:6.2f}s] {u.speaker.name:18s} {u.speech_act.value:14s} {snippet}"
        if u.content.artifacts:
            for artifact in u.content.artifacts:
                title = artifact.payload.get("title", "?")
                meta_bits = []
                for key in ("severity", "verdict", "side", "state", "operation"):
                    val = artifact.payload.get(key)
                    if val:
                        meta_bits.append(f"{key}={val}")
                meta = f" [{', '.join(meta_bits)}]" if meta_bits else ""
                line += f"\n{'':<29s}↳ {artifact.kind}: {title}{meta}"
        return line
    if kind == "state":
        change = event.payload["change"]
        return (
            f"[t={elapsed:6.2f}s] {'<thread_monitor>':<18s} "
            f"{change.from_state.value} → {change.to_state.value}  "
            f"({change.reason})"
        )
    if kind == "consensus_alert":
        alert = event.payload["alert"]
        return (
            f"[t={elapsed:6.2f}s] {'<consensus_guard>':<18s} "
            f"convergence: {', '.join(alert.agents)} "
            f"(sim {alert.average_pairwise_similarity:.2f})"
        )
    if kind == "budget_warning":
        cost = event.payload["cost"]
        budget = event.payload["budget"]
        fraction = event.payload["fraction"]
        return (
            f"[t={elapsed:6.2f}s] {'<budget>':<18s} "
            f"WARNING: ${cost:.2f} / ${budget:.2f} ({fraction:.0%} used)"
        )
    if kind == "budget_exceeded":
        cost = event.payload["cost"]
        budget = event.payload["budget"]
        return (
            f"[t={elapsed:6.2f}s] {'<budget>':<18s} "
            f"EXCEEDED: ${cost:.2f} > ${budget:.2f}; escalating"
        )
    if kind == "escalation_prompt":
        brief = event.payload["brief"]
        return f"[t={elapsed:6.2f}s] {'<escalation>':<18s} PROMPT: {brief.decision_required[:100]}"
    if kind == "complete":
        return f"[t={elapsed:6.2f}s] {'<complete>':<18s} thread settled cleanly"
    if kind == "aborted":
        reason = event.payload.get("reason", "?")
        return f"[t={elapsed:6.2f}s] {'<aborted>':<18s} {reason}"
    if kind == "timeout":
        sec = event.payload["timeout_seconds"]
        return f"[t={elapsed:6.2f}s] {'<timeout>':<18s} {sec:.0f}s exceeded"
    return None


async def _run(
    directive: str,
    project_root: Path,
    *,
    timeout: float,
    quiescence_seconds: float,
    budget: float,
    auto_respond: str,
    recipients: list[str] | None,
    goal: str,
) -> int:
    print("=" * 78)
    print("Wonderland — Translation Chat MVP showcase (T36, full cast via Runner)")
    print("=" * 78)
    print(f"Project root: {project_root}")
    print(f"Budget cap:   ${budget:.2f}")
    print(f"Timeout:      {timeout:.0f}s")
    if recipients is None:
        print("Roster:       open (every agent listens)")
    else:
        print(f"Roster:       {', '.join(recipients)} (+ dodo, auto-added)")
        print(f"Goal:         {goal}")
    print(f"Directive:    {directive}")
    print()
    print("--- Dance ---")

    runner = await Runner.make_full_cast(
        project_root,
        budget_dollars=budget,
        quiescence_seconds=quiescence_seconds,
        timeout_seconds=timeout,
    )

    event_counts: dict[str, int] = defaultdict(int)
    speech_act_counts: dict[str, int] = defaultdict(int)
    artifact_counts: dict[str, int] = defaultdict(int)
    exit_code = 0
    start = time.monotonic()

    try:
        await runner.setup()
        await runner.publish_directive(
            directive,
            recipients=recipients,
            goal=goal,
        )
        async for event in runner.events():
            event_counts[event.kind] += 1
            if event.kind == "utterance":
                u = event.payload["utterance"]
                speech_act_counts[u.speech_act.value] += 1
                for artifact in u.content.artifacts:
                    artifact_counts[artifact.kind] += 1
            line = _format_event(event)
            if line is not None:
                print(line)
                sys.stdout.flush()

            if event.kind == "escalation_prompt":
                # Auto-respond so the run is non-interactive.
                print(f"   ↪ auto-responding: {auto_respond}")
                await runner.respond_to_escalation(event.payload["prompt_id"], auto_respond)
            if event.kind == "complete":
                break
            if event.kind == "aborted":
                exit_code = 130
                break
            if event.kind == "timeout":
                exit_code = 1
                break
    except KeyboardInterrupt:
        runner.abort(reason="keyboard interrupt")
        exit_code = 130
    finally:
        elapsed_total = time.monotonic() - start
        await runner.teardown()

        print()
        print("--- Summary ---")
        print(f"Elapsed:        {elapsed_total:.1f}s")
        print(f"Total cost:     ${runner.total_cost:.4f}  (cap ${budget:.2f})")
        print(f"LLM calls:      {runner.telemetry.call_count}")
        print(f"Telemetry path: .wonderland/telemetry/run-{runner.run_id}.json")
        print()
        print("Speech acts:")
        for act, count in sorted(speech_act_counts.items(), key=lambda kv: -kv[1]):
            print(f"  {act:18s} {count}")
        print()
        print("Artifacts on disk:")
        for kind, count in sorted(artifact_counts.items(), key=lambda kv: -kv[1]):
            print(f"  {kind:18s} {count}")
        print()
        print("Per-agent token usage:")
        for agent, row in sorted(
            runner.telemetry.per_agent_summary().items(),
            key=lambda kv: -float(kv[1]["cost"]),
        ):
            print(
                f"  {agent:18s} calls={int(row['calls']):3d} "
                f"in={int(row['input_tokens']):7d} "
                f"out={int(row['output_tokens']):6d} "
                f"cache_r={int(row['cache_read_input_tokens']):7d} "
                f"cost=${float(row['cost']):.4f}"
            )

    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Translation Chat MVP showcase (T36).")
    parser.add_argument("--directive", default=DEFAULT_DIRECTIVE)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Where to write .wonderland/ artifacts. Default: a fresh tempdir.",
    )
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S)
    parser.add_argument("--quiescence-seconds", type=float, default=DEFAULT_QUIESCENCE_S)
    parser.add_argument("--budget", type=float, default=DEFAULT_BUDGET)
    parser.add_argument(
        "--auto-respond",
        type=str,
        default=(
            "Ship the simplest version that compiles for v1. Defer scope where "
            "the trade-off is reasonable; surface anything load-bearing as an "
            "open ticket for the next iteration."
        ),
    )
    parser.add_argument(
        "--roster",
        type=str,
        default="alice,cheshire_cat,queen_of_hearts",
        help=(
            "Comma-separated agent names that participate in the kickoff "
            "meeting (the Dodo is always added). Pass `--roster open` to run "
            "with the original full-cast no-roster behavior for direct "
            "comparison to analysis 011."
        ),
    )
    parser.add_argument(
        "--goal",
        type=str,
        default="produce an ADR for the translation message envelope",
        help="Meeting goal stored on the roster (no enforcement; for the record).",
    )
    args = parser.parse_args()

    if args.roster == "open":
        recipients = None
    else:
        recipients = [name.strip() for name in args.roster.split(",") if name.strip()]

    async def _go(root: Path) -> int:
        return await _run(
            args.directive,
            root,
            timeout=args.timeout,
            quiescence_seconds=args.quiescence_seconds,
            budget=args.budget,
            auto_respond=args.auto_respond,
            recipients=recipients,
            goal=args.goal,
        )

    if args.project_root is None:
        with tempfile.TemporaryDirectory(prefix="wonderland-translation-chat-") as tmp:
            return asyncio.run(_go(Path(tmp)))
    args.project_root.mkdir(parents=True, exist_ok=True)
    return asyncio.run(_go(args.project_root))


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        sys.exit(main())
