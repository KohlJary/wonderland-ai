"""Wonderland CLI — `wonderland <subcommand>`.

Currently exposes a single subcommand:

    wonderland init [path]   Create the .wonderland/ skeleton in a project.

The skeleton mirrors what the registries and per-agent memory layers
expect at runtime: ``architecture/`` for ADRs (Cat), ``tickets/`` for
tickets (Rabbit), ``stories/`` for stories (Alice), ``escalations/``
for human-review briefs (Dodo), and ``memory/`` for per-agent
episodic SQLite + semantic + relational notes (subdirs land lazily
as each agent first opens its memory).

Stdlib only (argparse) so installing wonderland adds no CLI deps.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

WONDERLAND_DIRNAME = ".wonderland"

# Directories the artifact registries write into. memory/ is the per-agent
# root; subdirs (memory/<agent>/) land lazily as each agent first opens
# its memory, so we don't pre-create them here.
SKELETON_DIRS: tuple[str, ...] = (
    "architecture",
    "tickets",
    "stories",
    "test-scenarios",
    "rulings",
    "observations",
    "implementations",
    "contract-notes",
    "escalations",
    "memory",
)

README_FILENAME = "README.md"

README_BODY = """\
# .wonderland/

Per-project state for a Wonderland-managed project. Created by
`wonderland init`. The runtime reads from and writes to this directory;
agents persist their characteristic artifacts here, and per-agent memory
lives under `memory/`.

## Layout

- `architecture/` — ADRs the Cheshire Cat writes (`adr-NNN-slug.md`).
- `tickets/` — Tickets the White Rabbit writes (`ticket-NNN-slug.md`).
- `stories/` — User stories Alice writes (`story-NNN-slug.md`).
- `test-scenarios/` — Test scenarios the Mad Hatter writes
  (`scenario-NNN-slug.md`), each with a triaged severity.
- `rulings/` — Security and compliance rulings the Queen of Hearts
  writes (`ruling-NNN-slug.md`), each with a citation.
- `observations/` — Production-reality reports the Dormouse writes
  (`observation-NNN-slug.md`), each with verifiable evidence.
- `implementations/` — Implementation artifacts the Tweedles ship
  (`implementation-NNN-slug.md`), each with a contract reference.
- `contract-notes/` — Contract Notes the Tweedles negotiate
  (`contract-note-NNN-slug.md`), each progressing through
  proposed → counterpart_assessed → agreed (or escalated/deferred).
- `escalations/` — Briefs the Dodo writes when conflicts need a human.
- `memory/` — Per-agent episodic (SQLite) + semantic (markdown) +
  relational (markdown) notes. Subdirectories under `memory/<agent>/`
  appear lazily as each agent first opens its memory.

## What to commit

A reasonable default is to commit everything except `memory/`. The
artifacts (ADRs, tickets, stories, escalations) are an audit trail of
the team's decisions and worth versioning. Per-agent memory is local
state; commit it only if you want compactions to persist across
machines.
"""


@dataclass(frozen=True)
class InitResult:
    """What ``init_skeleton`` did, for the CLI to print and tests to assert against."""

    project_root: Path
    wonderland_dir: Path
    created: tuple[str, ...] = field(default_factory=tuple)
    already_present: tuple[str, ...] = field(default_factory=tuple)

    @property
    def did_anything(self) -> bool:
        return bool(self.created)


# --------------------------------------------------------------------- #
# Pure layer — no argparse, no print
# --------------------------------------------------------------------- #


def init_skeleton(project_root: Path) -> InitResult:
    """Create or fill in the ``.wonderland/`` skeleton at ``project_root``.

    Idempotent: re-running is safe. Files that exist (including a
    user-edited README) are left alone — only missing directories and
    a missing README are created.

    Raises ``FileNotFoundError`` if ``project_root`` doesn't exist;
    ``NotADirectoryError`` if it's a file, not a directory.
    """
    if not project_root.exists():
        raise FileNotFoundError(project_root)
    if not project_root.is_dir():
        raise NotADirectoryError(project_root)

    wonderland = project_root / WONDERLAND_DIRNAME
    created: list[str] = []
    already: list[str] = []

    if not wonderland.exists():
        wonderland.mkdir()
        created.append(WONDERLAND_DIRNAME + "/")
    else:
        already.append(WONDERLAND_DIRNAME + "/")

    for name in SKELETON_DIRS:
        path = wonderland / name
        rel = f"{WONDERLAND_DIRNAME}/{name}/"
        if path.exists():
            already.append(rel)
        else:
            path.mkdir()
            created.append(rel)

    readme = wonderland / README_FILENAME
    rel_readme = f"{WONDERLAND_DIRNAME}/{README_FILENAME}"
    if readme.exists():
        already.append(rel_readme)
    else:
        readme.write_text(README_BODY, encoding="utf-8")
        created.append(rel_readme)

    return InitResult(
        project_root=project_root,
        wonderland_dir=wonderland,
        created=tuple(created),
        already_present=tuple(already),
    )


def format_init_result(result: InitResult) -> str:
    """Human-readable summary of an InitResult, for the CLI to print."""
    lines: list[str] = []
    if result.did_anything:
        lines.append(f"Initialized .wonderland/ in {result.project_root}")
    else:
        lines.append(f".wonderland/ already initialized in {result.project_root}")

    if result.created:
        lines.append("  Created:")
        for entry in result.created:
            lines.append(f"    {entry}")
    if result.already_present:
        lines.append("  Already present:")
        for entry in result.already_present:
            lines.append(f"    {entry}")
    return "\n".join(lines)


# --------------------------------------------------------------------- #
# argparse layer
# --------------------------------------------------------------------- #


def cmd_init(args: argparse.Namespace) -> int:
    project_root = Path(args.path).resolve()
    try:
        result = init_skeleton(project_root)
    except FileNotFoundError:
        print(f"error: {project_root} does not exist", file=sys.stderr)
        return 1
    except NotADirectoryError:
        print(f"error: {project_root} is not a directory", file=sys.stderr)
        return 1
    print(format_init_result(result))
    return 0


# --------------------------------------------------------------------- #
# `wonderland run` — drive a directive through the full cast
# --------------------------------------------------------------------- #


def cmd_run(args: argparse.Namespace) -> int:
    """Drive a directive through the full Wonderland cast."""
    import asyncio

    return asyncio.run(_run_async(args))


async def _run_async(args: argparse.Namespace) -> int:
    # Imported lazily so `wonderland init` doesn't pay the import cost.
    from wonderland.runner import Runner

    project_root = Path(args.project_root).resolve()
    if not project_root.exists():
        print(f"error: {project_root} does not exist", file=sys.stderr)
        return 1

    runner = await Runner.make_full_cast(
        project_root,
        budget_dollars=args.budget,
        quiescence_seconds=args.quiescence_seconds,
        timeout_seconds=args.timeout,
        model=args.model,
    )

    print("=" * 72)
    print(f"Wonderland — run {runner.run_id}")
    print("=" * 72)
    print(f"Project root:  {project_root}")
    print(f"Budget:        ${args.budget:.2f}" if args.budget else "Budget:        (none)")
    print(f"Timeout:       {args.timeout:.0f}s")
    print(f"On escalation: {args.on_escalation}")
    print()
    print(f"Directive: {args.directive}")
    print()
    print("--- Dance ---")

    exit_code = 0
    try:
        await runner.setup()
        await runner.publish_directive(args.directive)
        async for event in runner.events():
            await _handle_event(event, runner, args)
            if event.kind == "complete":
                break
            if event.kind == "aborted":
                exit_code = 130  # SIGINT-style
                break
            if event.kind == "timeout":
                exit_code = 1
                break
    except KeyboardInterrupt:
        runner.abort(reason="keyboard interrupt")
        exit_code = 130
    finally:
        await runner.teardown()
        print()
        print("--- Summary ---")
        print(f"Total cost: ${runner.total_cost:.4f}")
        print(f"Total calls: {runner.telemetry.call_count}")
        print(f"Telemetry: .wonderland/telemetry/run-{runner.run_id}.json")

    return exit_code


async def _handle_event(event, runner, args) -> None:
    """Print the event to stdout; handle escalation prompts interactively."""
    elapsed = event.elapsed
    if event.kind == "utterance":
        u = event.payload["utterance"]
        body_first_line = u.content.body.strip().split("\n", 1)[0]
        snippet = body_first_line[:120] + ("…" if len(body_first_line) > 120 else "")
        print(f"[t={elapsed:6.2f}s] {u.speaker.name:18s} {u.speech_act.value:14s} {snippet}")
        if u.content.artifacts:
            for artifact in u.content.artifacts:
                title = artifact.payload.get("title", "?")
                severity = artifact.payload.get("severity", artifact.payload.get("verdict", ""))
                extra = f" [{severity}]" if severity else ""
                print(f"{'':<29s}↳ {artifact.kind}: {title}{extra}")
    elif event.kind == "state":
        change = event.payload["change"]
        print(
            f"[t={elapsed:6.2f}s] {'<thread_monitor>':<18s} "
            f"{change.from_state.value} → {change.to_state.value}  "
            f"({change.reason})"
        )
    elif event.kind == "consensus_alert":
        alert = event.payload["alert"]
        print(
            f"[t={elapsed:6.2f}s] {'<consensus_guard>':<18s} "
            f"convergence: {', '.join(alert.agents)} "
            f"(sim {alert.average_pairwise_similarity:.2f})"
        )
    elif event.kind == "budget_warning":
        cost = event.payload["cost"]
        budget = event.payload["budget"]
        fraction = event.payload["fraction"]
        print(
            f"[t={elapsed:6.2f}s] {'<budget>':<18s} "
            f"WARNING: ${cost:.2f} / ${budget:.2f} ({fraction:.0%} used)",
            file=sys.stderr,
        )
    elif event.kind == "budget_exceeded":
        cost = event.payload["cost"]
        budget = event.payload["budget"]
        print(
            f"[t={elapsed:6.2f}s] {'<budget>':<18s} "
            f"EXCEEDED: ${cost:.2f} > ${budget:.2f}; escalating",
            file=sys.stderr,
        )
    elif event.kind == "escalation_prompt":
        await _handle_escalation(event, runner, args)
    elif event.kind == "complete":
        print(f"[t={elapsed:6.2f}s] <complete>          thread settled cleanly")
    elif event.kind == "aborted":
        print(
            f"[t={elapsed:6.2f}s] <aborted>           {event.payload.get('reason', '?')}",
            file=sys.stderr,
        )
    elif event.kind == "timeout":
        print(
            f"[t={elapsed:6.2f}s] <timeout>           "
            f"{event.payload['timeout_seconds']:.0f}s exceeded",
            file=sys.stderr,
        )
    sys.stdout.flush()


async def _handle_escalation(event, runner, args) -> None:
    brief = event.payload["brief"]
    prompt_id = event.payload["prompt_id"]

    print()
    print("═" * 72, file=sys.stderr)
    print("ESCALATION", file=sys.stderr)
    print("═" * 72, file=sys.stderr)
    print(f"Thread: {brief.thread_id}", file=sys.stderr)
    print(f"Cost so far: ${runner.total_cost:.4f}", file=sys.stderr)
    print(file=sys.stderr)
    print(f"Decision required: {brief.decision_required}", file=sys.stderr)
    print(file=sys.stderr)
    if brief.agent_proposals:
        print("Agent positions:", file=sys.stderr)
        for prop in brief.agent_proposals:
            print(f"  • {prop.speaker}: {prop.position}", file=sys.stderr)
        print(file=sys.stderr)
    if brief.suggested_resolution:
        print(f"Suggested resolution: {brief.suggested_resolution}", file=sys.stderr)
        print(file=sys.stderr)
    if brief.stakes:
        print(f"Stakes: {brief.stakes}", file=sys.stderr)
        print(file=sys.stderr)
    print(f"Brief written to: {event.payload['record_path']}", file=sys.stderr)
    print(file=sys.stderr)

    if args.on_escalation == "abort":
        print("--on-escalation=abort; stopping run.", file=sys.stderr)
        runner.abort(reason="escalation triggered, --on-escalation=abort")
        return

    if args.on_escalation == "auto" and args.auto_respond:
        print(f"Auto-responding: {args.auto_respond}", file=sys.stderr)
        await runner.respond_to_escalation(prompt_id, args.auto_respond)
        return

    # Interactive mode — prompt via stdin.
    if not sys.stdin.isatty():
        print(
            "stdin is not a tty and --on-escalation=prompt was used; aborting. "
            "Set --on-escalation=abort or --auto-respond=<text> for non-interactive runs.",
            file=sys.stderr,
        )
        runner.abort(reason="non-interactive escalation without --auto-respond")
        return

    print("Your input (or 'abort' to stop): ", end="", file=sys.stderr, flush=True)
    response = sys.stdin.readline().strip()
    if response.lower() == "abort":
        runner.abort(reason="user aborted at escalation prompt")
        return
    await runner.respond_to_escalation(prompt_id, response)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wonderland",
        description=(
            "Wonderland — an identity-native multi-agent development system. "
            "Initialize a project to host a Wonderland team's per-project state."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="<command>")

    init_parser = subparsers.add_parser(
        "init",
        help="Create the .wonderland/ skeleton in a project directory.",
        description=(
            "Create (or fill in) the .wonderland/ directory layout the runtime "
            "expects. Idempotent — re-running is safe; existing files are not "
            "overwritten."
        ),
    )
    init_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Project root to initialize (default: current directory).",
    )
    init_parser.set_defaults(func=cmd_init)

    run_parser = subparsers.add_parser(
        "run",
        help="Drive a directive through the full Wonderland cast.",
        description=(
            "Spin up the full 10-agent cast against the supplied project root, "
            "publish the directive, and stream the dance to stdout. Interactive "
            "by default — when the team escalates (deadlocked or budget-exceeded), "
            "you'll be prompted on stderr to provide a resolution. For "
            "non-interactive runs, use --on-escalation=abort or "
            "--auto-respond=<text>."
        ),
    )
    run_parser.add_argument("directive", help="The directive to drive through the team.")
    run_parser.add_argument(
        "--project-root",
        type=Path,
        default=".",
        help="Project root with a .wonderland/ skeleton (default: current dir).",
    )
    run_parser.add_argument(
        "--budget",
        type=float,
        default=1.00,
        help="Dollar cap for the run; escalates when exceeded (default: $1.00).",
    )
    run_parser.add_argument(
        "--quiescence-seconds",
        type=float,
        default=30.0,
        help="Bus-silence with no open expectations to declare quiescent (default: 30s).",
    )
    run_parser.add_argument(
        "--timeout",
        type=float,
        default=600.0,
        help="Hard timeout for the run, in seconds (default: 600).",
    )
    run_parser.add_argument(
        "--on-escalation",
        choices=("prompt", "abort", "auto"),
        default="prompt",
        help=(
            "What to do when the team escalates: 'prompt' for interactive (default), "
            "'abort' to stop, 'auto' to use --auto-respond."
        ),
    )
    run_parser.add_argument(
        "--auto-respond",
        type=str,
        default=None,
        help="Text to use as the escalation response when --on-escalation=auto.",
    )
    run_parser.add_argument(
        "--model",
        type=str,
        default=None,
        help=(
            "Override the LLM model id every agent uses (e.g. "
            "'claude-haiku-3-5-20241022' for cheaper development "
            "runs). None → Runner's DEFAULT_MODEL applies."
        ),
    )
    run_parser.set_defaults(func=cmd_run)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())


__all__ = [
    "README_BODY",
    "README_FILENAME",
    "SKELETON_DIRS",
    "WONDERLAND_DIRNAME",
    "InitResult",
    "build_parser",
    "cmd_init",
    "cmd_run",
    "format_init_result",
    "init_skeleton",
    "main",
]
