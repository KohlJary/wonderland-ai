"""Project skeleton loader / applier — the missing piece that
analysis 037 named as load-bearing.

A skeleton is a working hello-world tree (pyproject, src/, tests/,
conftest.py, .gitignore, README) that the Wonderland team extends
rather than inventing from scratch. Pre-laying the structure
communicates "production code goes in src/, tests go in tests/"
*structurally* — without the convenor directives having to
re-explain the convention every iteration.

Per analysis 037 F1+F7: every TUI run since r33 has been against
bare project roots, and the deliverable shape progressively
collapsed (r38's reductio: production logic in tests/conftest.py
because there was no canonical src/ to write to). Skeleton
restoration is the durable fix; this module is the loader the
NewRunScreen picker (T71) and any CLI/programmatic caller will
consume.

API mirrors ``wonderland.directive`` and ``wonderland.workflow``:

  - ``skeletons_dir()`` — directory holding bundled skeletons
  - ``list_skeletons()`` — enumerate available skeletons
  - ``load_skeleton(name)`` — load one by name (with metadata)
  - ``apply_skeleton(skeleton, project_root)`` — copy files into
    a project root (rejects non-empty roots by default)
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

# The bundled skeleton directory sits alongside ``closet/workflows/``
# and ``closet/directives/``. Same loader pattern: bundled here +
# per-project overrides at ``<project_root>/.wonderland/skeletons/``
# (when that's wired in T71+).


class PostApplyStep(BaseModel):
    """One command to run after the skeleton's files are laid down.

    Currently informational — the picker surfaces these as a
    'Setup commands (run after apply)' block for the operator to
    copy-paste. Future work (roadmap 3a22d99e) adds an auto-install
    runner that executes these as subprocesses. Per the
    multi-language-ready design: each skeleton declares its own
    install procedure as data, the applier doesn't hardcode
    pip-vs-npm-vs-cargo logic.
    """

    description: str = Field(
        description="Human-readable label, e.g. 'Install Python deps'."
    )
    command: str = Field(
        description="Shell command to run, e.g. 'pip install -e .[dev]'."
    )
    cwd: str = Field(
        default=".",
        description=(
            "Working directory relative to project root. Defaults "
            "to '.' (project root itself). Used for monorepos where "
            "frontend deps live under frontend/ etc."
        ),
    )


class SkeletonManifest(BaseModel):
    """Optional metadata next to a skeleton's files. Declares the
    language stack (informational) + post-apply commands the
    operator (or future auto-runner) should execute to make the
    skeleton runnable.

    A skeleton without a manifest is treated as empty-manifest:
    no post-apply steps, no language tag. Backward-compatible with
    skeletons that predate T73.
    """

    language: str | None = Field(
        default=None,
        description=(
            "Language stack tag for picker filtering / display. "
            "Examples: 'python', 'javascript', 'rust'. Optional. "
            "Superseded by ``stack.language`` for runtime-shape use; "
            "kept for back-compat + picker filtering."
        ),
    )
    stack: dict[str, str] | None = Field(
        default=None,
        description=(
            "Project stack shape — runtime / language / "
            "ui_framework / storage / test_framework. When set, "
            "``apply_skeleton`` writes a ``.wonderland/project.yaml`` "
            "from these fields so the substrate's project_context "
            "loader sees the stack at run time. Optional but "
            "strongly recommended for skeletons on a fixed runtime "
            "(tui / web / cli) — without it, agents have to guess "
            "the runtime from the directive alone, which is the "
            "M5-Tweedle-drift failure mode named in analysis 040. "
            "See ``ProjectStack`` for the field set."
        ),
    )
    entry_point: str | None = Field(
        default=None,
        description=(
            "Path to the file the runtime enters at. Written into "
            "project.yaml if set. Helps M8 review check the "
            "App.tsx-orphan failure mode (component built but "
            "never imported into the entry point)."
        ),
    )
    post_apply: list[PostApplyStep] = Field(
        default_factory=list,
        description=(
            "Ordered list of commands to run after the skeleton's "
            "files are laid down. Currently surfaced via the "
            "picker as copy-paste instructions; auto-runner is "
            "deferred (roadmap 3a22d99e)."
        ),
    )


@dataclass(frozen=True)
class Skeleton:
    """A project skeleton — a working hello-world tree the team
    extends. ``files`` lists relative paths from the skeleton root
    that will be copied into a target project root. ``description``
    is the human-readable picker label."""

    name: str
    description: str
    root: Path
    files: tuple[str, ...] = field(default_factory=tuple)
    manifest: SkeletonManifest = field(default_factory=SkeletonManifest)

    def top_level_dirs(self) -> tuple[str, ...]:
        """Top-level directory names the skeleton lays down. Used
        in the picker preview ('skeleton ships: src/, tests/, ...').
        Computed from ``files`` rather than re-walking ``root``."""
        seen: set[str] = set()
        out: list[str] = []
        for f in self.files:
            head = f.split("/", 1)[0] if "/" in f else None
            if head and head not in seen:
                seen.add(head)
                out.append(head)
        return tuple(sorted(out))


def skeletons_dir() -> Path:
    """Directory holding bundled skeletons (parallel to
    ``workflows_dir()``)."""
    import wonderland

    return Path(wonderland.__file__).parent / "closet" / "skeletons"


def _scan_skeleton_files(root: Path) -> tuple[str, ...]:
    """Walk a skeleton directory; return relative paths of every
    file that should be laid down on apply. The skeleton's own
    .gitignore IS included; manifest.yaml is excluded (it's
    metadata for the loader, not a file the operator's project
    needs)."""
    if not root.is_dir():
        return ()
    out: list[str] = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        # Filter hidden directories (e.g., .git, .venv) but keep
        # hidden files at the top level (.gitignore, .env.example).
        parts = rel.parts
        if any(part.startswith(".") and part not in {".gitignore", ".env.example"}
               for part in parts[:-1]):
            continue
        # manifest.yaml is metadata for the skeleton loader — it
        # shouldn't be copied into the user's project.
        if rel.as_posix() == "manifest.yaml":
            continue
        out.append(rel.as_posix())
    return tuple(out)


def _load_manifest(root: Path) -> SkeletonManifest:
    """Read the skeleton's manifest.yaml if present; return an
    empty manifest otherwise. Empty-manifest behavior preserves
    backward compat with skeletons that predate T73."""
    path = root / "manifest.yaml"
    if not path.is_file():
        return SkeletonManifest()
    try:
        with path.open() as f:
            data = yaml.safe_load(f) or {}
    except (OSError, yaml.YAMLError):
        return SkeletonManifest()
    return SkeletonManifest.model_validate(data)


def _read_skeleton_description(root: Path) -> str:
    """Pull the description from the skeleton's README's first
    non-heading paragraph. Falls back to the skeleton's directory
    name if no README exists."""
    readme = root / "README.md"
    if not readme.is_file():
        return root.name
    try:
        text = readme.read_text(encoding="utf-8")
    except OSError:
        return root.name
    # First non-heading, non-empty line/paragraph.
    paragraph: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            if paragraph:
                break
            continue
        if stripped.startswith("#"):
            if paragraph:
                break
            continue
        paragraph.append(stripped)
    if not paragraph:
        return root.name
    desc = " ".join(paragraph)
    # Trim — picker cells need to be readable.
    if len(desc) > 200:
        desc = desc[:197] + "..."
    return desc


def list_skeletons() -> list[Skeleton]:
    """Names + metadata for every bundled skeleton, sorted by name."""
    base = skeletons_dir()
    if not base.is_dir():
        return []
    out: list[Skeleton] = []
    for entry in sorted(base.iterdir()):
        if not entry.is_dir():
            continue
        files = _scan_skeleton_files(entry)
        if not files:
            continue
        out.append(
            Skeleton(
                name=entry.name,
                description=_read_skeleton_description(entry),
                root=entry,
                files=files,
                manifest=_load_manifest(entry),
            )
        )
    return out


def load_skeleton(name: str) -> Skeleton:
    """Load one bundled skeleton by name. Raises FileNotFoundError
    with the available list if the name is unknown."""
    skeletons = list_skeletons()
    for s in skeletons:
        if s.name == name:
            return s
    available = sorted(s.name for s in skeletons)
    raise FileNotFoundError(
        f"skeleton not found: {name!r}. Bundled skeletons: {available}"
    )


def apply_skeleton(
    skeleton: Skeleton,
    project_root: Path,
    *,
    overwrite: bool = False,
) -> list[Path]:
    """Lay the skeleton's file tree into ``project_root``. Returns
    the list of paths written.

    By default refuses to overwrite existing files (a non-empty
    project root is treated as user content not to clobber). Pass
    ``overwrite=True`` for re-application or testing.

    The project root is created if missing. Parent directories of
    each skeleton file are created as needed.
    """
    project_root.mkdir(parents=True, exist_ok=True)

    # Pre-flight: detect collisions if not overwriting.
    if not overwrite:
        existing = [
            project_root / rel
            for rel in skeleton.files
            if (project_root / rel).exists()
        ]
        if existing:
            preview = ", ".join(p.name for p in existing[:5])
            extra = f" (and {len(existing) - 5} more)" if len(existing) > 5 else ""
            raise FileExistsError(
                f"skeleton {skeleton.name!r} would overwrite existing "
                f"files in {project_root}: {preview}{extra}. "
                "Pass overwrite=True to force, or pick an empty root."
            )

    written: list[Path] = []
    for rel in skeleton.files:
        src = skeleton.root / rel
        dst = project_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        written.append(dst)

    # Write project context memory from manifest.stack so the
    # substrate's seed-fallback loader sees the runtime shape at
    # run time. Skipped when the manifest doesn't declare a stack
    # — leaves the project to operate from directive-only
    # grounding (legacy behavior).
    project_yaml = _write_project_context_from_manifest(
        skeleton, project_root, overwrite=overwrite
    )
    if project_yaml is not None:
        written.append(project_yaml)

    return written


def write_project_context_from_skeleton(
    skeleton: Skeleton,
    project_root: Path,
    *,
    overwrite: bool = False,
) -> Path | None:
    """Translate the skeleton's manifest.stack into a
    ``.wonderland/project.yaml`` so the team's seed loader can
    surface the runtime shape during architecture + contract
    meetings.

    Public counterpart to ``apply_skeleton``'s file-laying path:
    callable on its own for retrofit (non-bare roots that already
    have skeleton files but lack project_context — typical for
    projects created before context memory landed, or for adopt-
    existing-codebase flows where the operator picked the
    skeleton that matches an existing tree).

    Returns the written path, or None when the manifest didn't
    declare a stack OR when a project.yaml already exists and
    ``overwrite`` is False (don't clobber operator-edited
    context).
    """
    stack_data = skeleton.manifest.stack
    if not stack_data or "runtime" not in stack_data:
        return None

    from wonderland.project_context import (
        ProjectContext,
        ProjectStack,
        project_context_path,
        save_project_context,
    )

    target = project_context_path(project_root)
    if target.exists() and not overwrite:
        return None

    stack = ProjectStack(
        runtime=stack_data["runtime"],
        language=stack_data.get("language") or skeleton.manifest.language,
        ui_framework=stack_data.get("ui_framework"),
        storage=stack_data.get("storage"),
        test_framework=stack_data.get("test_framework"),
    )
    context = ProjectContext(
        name=project_root.name,
        stack=stack,
        entry_point=skeleton.manifest.entry_point,
    )
    return save_project_context(context, project_root)


# Internal alias kept so apply_skeleton's call site doesn't move.
_write_project_context_from_manifest = write_project_context_from_skeleton


def is_bare_project_root(project_root: Path) -> bool:
    """True if the project root is bare enough to apply a skeleton
    safely. Allows .git/, .gitignore, README.md (typical
    just-`git init`'d directory) but rejects roots with src/,
    tests/, or any other content the skeleton would clobber."""
    if not project_root.is_dir():
        return True  # missing dir = bare; will be created on apply
    allowed = {".git", ".gitignore", "README.md", ".DS_Store"}
    for entry in project_root.iterdir():
        if entry.name not in allowed:
            return False
    return True


__all__ = [
    "PostApplyStep",
    "Skeleton",
    "SkeletonManifest",
    "apply_skeleton",
    "is_bare_project_root",
    "list_skeletons",
    "load_skeleton",
    "skeletons_dir",
    "write_project_context_from_skeleton",
]
