"""Run a bundled workflow against the full Wonderland cast and print
events as they happen. Verifies the workflow loader + runner
integration end-to-end against real agents.

Usage:
    uv run python scripts/workflow_demo.py
        # Defaults: smoke workflow, "Build a /hello endpoint" directive,
        # /tmp/wonderland-workflow-demo project root.

    uv run python scripts/workflow_demo.py --workflow canonical \\
        --directive "Build a translation chat MVP."

    uv run python scripts/workflow_demo.py --list
        # Lists bundled workflows without running anything.

    uv run python scripts/workflow_demo.py --dry-run
        # Loads + pretty-prints the workflow structure, no LLM calls.

The script reads the Anthropic API key via the standard resolution
chain (ANTHROPIC_API_KEY env var, then ~/.config/wonderland/config.json).
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import shutil
import subprocess
import sys
import time
from pathlib import Path

from wonderland.runner import Runner
from wonderland.workflow import (
    MeetingEndEvent,
    MeetingStartEvent,
    Workflow,
    list_workflows,
    load_workflow,
    run_workflow,
)

DEFAULT_DIRECTIVE = (
    "Build a /hello endpoint that returns the current server time as JSON."
)


def section(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def print_workflow(wf: Workflow) -> None:
    """Pretty-print a workflow's structure. Used for --dry-run."""
    section(f"Workflow: {wf.name} (v{wf.version})")
    print(wf.description)
    print()
    if wf.defaults.budget_dollars:
        print(f"Default budget: ${wf.defaults.budget_dollars:.2f}")
    if wf.defaults.timeout_seconds:
        print(f"Default timeout: {wf.defaults.timeout_seconds:.0f}s")
    if wf.defaults.quiescence_seconds:
        print(f"Default quiescence fallback: {wf.defaults.quiescence_seconds:.0f}s")
    print()
    print(f"Meetings ({len(wf.meetings)}):")
    for m in wf.meetings:
        budget = f"${m.meeting_budget:.2f}" if m.meeting_budget else "no cap"
        print(f"  {m.label}: {m.id} ({budget})")
        print(f"      goal:    {m.goal}")
        print(f"      roster:  {sorted(m.roster)}")
        if m.seeds:
            for s in m.seeds:
                seed_desc = f"from {s.from_meeting} kinds={s.kinds}"
                if s.where:
                    seed_desc += f" where={s.where}"
                if s.limit is not None:
                    seed_desc += f" limit={s.limit}"
                if s.fallback:
                    seed_desc += f" fallback={s.fallback}"
                print(f"      seed:    {seed_desc}")
        if m is wf.entry_meeting:
            print("      directive: <runtime user input>")
        else:
            preview = m.convenor_directive.strip().split("\n", 1)[0][:80]
            print(f"      directive: {preview}…")


def render_event(event) -> str | None:
    """One-line render of a workflow / runner event."""
    if isinstance(event, MeetingStartEvent):
        m = event.meeting
        n_seeds = len(event.seeds)
        return (
            f"\n{'─' * 78}\n"
            f"  {m.label} START · {m.id} · roster={sorted(m.roster)} · seeds={n_seeds}\n"
            f"  goal: {m.goal}\n"
            f"{'─' * 78}"
        )
    if isinstance(event, MeetingEndEvent):
        m = event.meeting
        kinds = (
            ", ".join(f"{k}×{v}" for k, v in sorted(event.artifact_kinds.items()))
            or "no artifacts"
        )
        return (
            f"\n  {m.label} END · {event.outcome} · "
            f"{event.elapsed_s:.1f}s · {event.calls_delta} calls · "
            f"${event.cost_delta:.4f}\n"
            f"  artifacts: {kinds}"
        )
    # Otherwise, treat it as a RunnerEvent
    elapsed = getattr(event, "elapsed", 0.0)
    kind = getattr(event, "kind", "?")
    payload = getattr(event, "payload", {})
    if kind == "utterance":
        u = payload["utterance"]
        first_line = u.content.body.strip().split("\n", 1)[0] if u.content.body else "(no body)"
        snippet = first_line[:100] + ("…" if len(first_line) > 100 else "")
        addressed = (
            u.addressed_to
            if isinstance(u.addressed_to, str)
            else "[" + ",".join(a.name for a in u.addressed_to) + "]"
        )
        line = (
            f"  [t={elapsed:6.2f}s] {u.speaker.name:18s} "
            f"{u.speech_act.value:14s} →{addressed} {snippet}"
        )
        if u.content.artifacts:
            for art in u.content.artifacts:
                title = art.payload.get("title", "?")
                line += f"\n{'':<29s}↳ {art.kind}: {title}"
        return line
    if kind == "state":
        change = payload["change"]
        return f"  [t={elapsed:6.2f}s] <thread_monitor> {change.from_state.value} → {change.to_state.value}"
    if kind == "complete":
        return f"  [t={elapsed:6.2f}s] <complete>"
    if kind == "timeout":
        return f"  [t={elapsed:6.2f}s] <timeout>"
    if kind == "aborted":
        return f"  [t={elapsed:6.2f}s] <aborted>"
    if kind == "budget_exceeded":
        cost = payload.get("cost", 0)
        return f"  [t={elapsed:6.2f}s] <budget> EXCEEDED ${cost:.2f}"
    if kind == "budget_warning":
        cost = payload.get("cost", 0)
        budget = payload.get("budget", 0)
        return f"  [t={elapsed:6.2f}s] <budget> WARNING ${cost:.2f} / ${budget:.2f}"
    return None


async def run_live(workflow: Workflow, directive: str, project_root: Path) -> int:
    """Set up the full cast, run the workflow, print events, summarize."""
    section(f"Running workflow {workflow.name!r} live")
    print(f"Project root: {project_root}")
    print(f"Directive:    {directive}")

    runner = await Runner.make_full_cast(
        project_root,
        budget_dollars=workflow.defaults.budget_dollars or 1.00,
        timeout_seconds=workflow.defaults.timeout_seconds or 300.0,
        quiescence_seconds=workflow.defaults.quiescence_seconds or 300.0,
    )
    print(
        f"Runner:       budget=${runner.budget_dollars:.2f} cap, "
        f"timeout={runner.timeout_seconds:.0f}s, "
        f"quiescence_fallback={runner.quiescence_seconds:.0f}s"
    )

    start = time.monotonic()
    try:
        await runner.setup()
        async for event in run_workflow(workflow, runner, directive):
            line = render_event(event)
            if line:
                print(line)
                sys.stdout.flush()
    finally:
        elapsed = time.monotonic() - start
        await runner.teardown()

        section("Summary")
        print(f"Total elapsed:  {elapsed:.1f}s")
        print(f"Total cost:     ${runner.total_cost:.4f}  (cap ${runner.budget_dollars:.2f})")
        print(f"Total LLM calls: {runner.telemetry.call_count}")
        print()
        print("Per-agent:")
        for agent, row in sorted(
            runner.telemetry.per_agent_summary().items(),
            key=lambda kv: -float(kv[1]["cost"]),
        ):
            print(
                f"  {agent:18s} calls={int(row['calls']):3d} "
                f"cost=${float(row['cost']):.4f}"
            )
        print()
        print("Artifacts on disk:")
        for subdir in sorted((project_root / ".wonderland").iterdir()):
            if not subdir.is_dir() or subdir.name in ("memory", "telemetry"):
                continue
            files = sorted(subdir.glob("*.md"))
            if files:
                print(f"  {subdir.name}/ ({len(files)} files)")
                for f in files:
                    print(f"    {f.name}")

    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description=(__doc__ or "").split("\n\n")[0],
    )
    p.add_argument(
        "--workflow",
        default="smoke",
        help="Bundled workflow name (default: smoke). Use --list to see options.",
    )
    p.add_argument("--directive", default=DEFAULT_DIRECTIVE, help="User directive.")
    p.add_argument(
        "--project-root",
        type=Path,
        default=Path("/tmp/wonderland-workflow-demo"),
        help="Project root for the demo run.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Load + pretty-print the workflow without running it.",
    )
    p.add_argument(
        "--list",
        action="store_true",
        help="List bundled workflows and exit.",
    )
    p.add_argument(
        "--clean",
        action="store_true",
        help="Wipe the project root before running (no carry-over from prior runs).",
    )
    args = p.parse_args()

    if args.list:
        names = list_workflows()
        section("Bundled workflows")
        for name in names:
            wf = load_workflow(name)
            print(f"  {name:14s} — {wf.description.strip().splitlines()[0]}")
        return 0

    workflow = load_workflow(args.workflow)

    if args.dry_run:
        print_workflow(workflow)
        return 0

    if args.clean and args.project_root.exists():
        print(f"Cleaning {args.project_root}…")
        shutil.rmtree(args.project_root)
    args.project_root.mkdir(parents=True, exist_ok=True)
    # Initialize git so the runner's _ensure_git_repo path is happy
    if not (args.project_root / ".git").exists():
        subprocess.run(
            ["git", "init", "--initial-branch=main"],
            cwd=args.project_root,
            capture_output=True,
            check=True,
            timeout=10,
        )

    with contextlib.suppress(KeyboardInterrupt):
        return asyncio.run(run_live(workflow, args.directive, args.project_root))
    return 130  # SIGINT


if __name__ == "__main__":
    raise SystemExit(main())
