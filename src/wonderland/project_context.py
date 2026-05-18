"""Project context memory — authoritative project-level facts that
constrain how the team builds.

Distinct from per-run directives (operator's intent for *this* run)
and from the codex (Caterpillar's living build-state document — see
roadmap b50df6af). This is project-level ground truth, written once
by skeleton-apply (or operator, by hand), read-only to agents.

Motivating problem: r41/r42 obol's M4 ADR drift named in analysis
040. The directive-as-seed fix (commit ed082bd) gets the operator's
literal directive into Cat's M4 context — but the Tweedles in M5
still drift to HTTP-shaped contracts because their constitutional
roles ("frontend bias" / "backend bias") run through M5 even when
the runtime is a single-process TUI. Project context memory makes
the stack a fact the substrate can name and the team can't
unilaterally violate.

Shape:

  # .wonderland/project.yaml
  name: obol
  stack:
    runtime: tui
    language: python
    ui_framework: textual
    storage: sqlite
    test_framework: pytest
  entry_point: src/obol/__main__.py
  conventions: |
    Diff-based writes for incremental edits.
    Tests in tests/, code in src/.

The runtime field is the load-bearing one — it tells agents what
shape the program runs as (tui / web / cli / service / mobile). The
others are informational hints for downstream meetings. ``language``
+ ``runtime`` together are usually enough for the team to refuse
HTTP-boundary contracts in a TUI project.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class ProjectStack(BaseModel):
    """The runtime shape of the project.

    All fields except ``runtime`` are optional — they're hints for
    downstream meetings, not load-bearing facts. ``runtime`` is the
    one the substrate uses to refuse stack-incompatible contracts.
    """

    runtime: str = Field(
        description=(
            "How the program executes. Common values: 'tui' "
            "(terminal UI, single-process), 'web' (browser + "
            "backend service, client-server), 'cli' (single-process "
            "command-line), 'service' (long-running daemon, no UI), "
            "'mobile' (iOS/Android client). Freeform string so "
            "operators can name niche runtimes (tauri, electron, "
            "mcp-server, browser-extension, etc.)."
        ),
    )
    language: str | None = Field(
        default=None,
        description=(
            "Primary language. Common values: 'python', "
            "'typescript', 'rust', 'go', 'python+typescript' for "
            "fullstack. Hyphenated combinations are fine."
        ),
    )
    ui_framework: str | None = Field(
        default=None,
        description=(
            "UI framework where applicable. 'textual' for Python "
            "TUI, 'react' for web, 'clap' for Rust CLI parsers, "
            "etc. None for headless services."
        ),
    )
    storage: str | None = Field(
        default=None,
        description=(
            "Persistence layer. 'sqlite', 'postgres', 'filesystem', "
            "'in-memory', etc. None when no persistent storage."
        ),
    )
    test_framework: str | None = Field(
        default=None,
        description=(
            "Test runner. 'pytest', 'vitest', 'cargo test', "
            "'jest', etc."
        ),
    )


class ProjectContext(BaseModel):
    """Authoritative project-level facts the team consults at every
    meeting that makes architectural or contract-level decisions.

    Loaded into seed context via the ``project_context`` kind in
    seeds_fallback. M4 (architecture), M5 (contracts), and M8
    (review) are the natural consumers.
    """

    name: str = Field(
        description=(
            "Project name. Typically matches the directory name + "
            "the directive's ``name`` field."
        ),
    )
    stack: ProjectStack
    entry_point: str | None = Field(
        default=None,
        description=(
            "Path to the file/symbol the program enters at. "
            "'src/obol/__main__.py' for a Python TUI, "
            "'frontend/src/main.tsx' for a Vite+React app, etc. "
            "Helps M8 review check that components actually get "
            "wired into the running program (the App.tsx orphan "
            "from analysis 040 is the failure mode this guards "
            "against)."
        ),
    )
    prime_directive: str | None = Field(
        default=None,
        description=(
            "The operator's original directive text, preserved as "
            "ambient project context. Critical for minimal-directive "
            "projects (e.g. obol's two-sentence \"build me a TUI "
            "dashboard for managing personal finances. Think 'htop "
            "for money'\") where the directive's vibe carries the "
            "soul of what's being built but the per-meeting relayed "
            "directive only covers the meeting's immediate scope. "
            "Without this field, downstream meetings (M4 architecture, "
            "M5 contracts, M8 review) read stack + entry_point but "
            "lose the 'what feel are we going for' grounding. The "
            "Project registry's own prime_directive auto-populates "
            "at first-run; this field mirrors it into the per-meeting "
            "seed context."
        ),
    )
    conventions: str = Field(
        default="",
        description=(
            "Free-form prose carrying constraints the team should "
            "respect: file layout, write style, naming, etc. "
            "Surfaced verbatim into agent context."
        ),
    )


def project_context_path(project_root: Path) -> Path:
    """The canonical location for a project's context memory.
    File doesn't have to exist; ``load_project_context`` returns
    None if absent.
    """
    return project_root / ".wonderland" / "project.yaml"


def load_project_context(project_root: Path) -> ProjectContext | None:
    """Read ``project_root/.wonderland/project.yaml`` if present.

    Returns None when the file is missing — projects predating
    project-context-memory still work without it. Callers that
    require a context (e.g. seeds_fallback's loader) handle the
    None case by returning an empty seed list, leaving the team
    to operate from the directive alone.
    """
    path = project_context_path(project_root)
    if not path.is_file():
        return None
    with path.open() as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        return None
    return ProjectContext.model_validate(data)


def save_project_context(
    context: ProjectContext, project_root: Path
) -> Path:
    """Persist a context to ``.wonderland/project.yaml``. Creates
    the directory if missing. Returns the written path.

    Used by ``apply_skeleton`` at project init (skeleton's
    ``manifest.stack`` becomes the seed) and by future hand-edits
    via the TUI / CLI.
    """
    path = project_context_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = context.model_dump(exclude_none=True)
    # Drop empty conventions rather than serializing `conventions: ''`
    # — keeps the YAML clean for the common case where the skeleton
    # didn't ship convention prose.
    if "conventions" in data:
        if data["conventions"].strip():
            data["conventions"] = data["conventions"].rstrip() + "\n"
        else:
            del data["conventions"]
    # Same treatment for prime_directive — non-empty serializes with a
    # trailing newline (YAML block-scalar friendly); empty/whitespace-
    # only gets dropped. None case already handled by exclude_none above.
    if "prime_directive" in data:
        if data["prime_directive"].strip():
            data["prime_directive"] = data["prime_directive"].rstrip() + "\n"
        else:
            del data["prime_directive"]
    with path.open("w") as f:
        yaml.safe_dump(
            data,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )
    return path


def render_context_body(context: ProjectContext) -> str:
    """Format a ProjectContext as the body of a seed utterance.

    Agents read this prose, not the YAML envelope. Structured as a
    bulleted fact sheet so the team can scan-and-cite during
    architecture / contract decisions.

    Prime directive (when present) renders FIRST — it's the soul of
    the project and should be the first thing every meeting reads.
    Stack + entry_point come next as structural grounding. Conventions
    last as detail. This ordering matters for minimal-directive
    projects where the directive is what the substrate should be
    serving every meeting, not just discovery.
    """
    stack = context.stack
    lines: list[str] = [f"**Project:** {context.name}"]
    if context.prime_directive and context.prime_directive.strip():
        lines.extend(
            [
                "",
                "**Prime directive (operator's original ask):**",
                context.prime_directive.rstrip(),
            ]
        )
    lines.extend(
        [
            "",
            "**Stack:**",
            f"- Runtime: {stack.runtime}",
        ]
    )
    if stack.language:
        lines.append(f"- Language: {stack.language}")
    if stack.ui_framework:
        lines.append(f"- UI framework: {stack.ui_framework}")
    if stack.storage:
        lines.append(f"- Storage: {stack.storage}")
    if stack.test_framework:
        lines.append(f"- Test framework: {stack.test_framework}")
    if context.entry_point:
        lines.extend(["", f"**Entry point:** {context.entry_point}"])
    if context.conventions.strip():
        lines.extend(["", "**Conventions:**", context.conventions.rstrip()])
    return "\n".join(lines)


__all__ = [
    "ProjectContext",
    "ProjectStack",
    "load_project_context",
    "project_context_path",
    "render_context_body",
    "save_project_context",
]
