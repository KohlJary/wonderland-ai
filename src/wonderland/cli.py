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
    "format_init_result",
    "init_skeleton",
    "main",
]
