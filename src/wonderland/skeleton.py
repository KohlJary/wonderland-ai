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

# The bundled skeleton directory sits alongside ``closet/workflows/``
# and ``closet/directives/``. Same loader pattern: bundled here +
# per-project overrides at ``<project_root>/.wonderland/skeletons/``
# (when that's wired in T71+).


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
    file (excluding hidden directories like .git that shouldn't be
    laid down). The skeleton's own .gitignore IS included — it's
    part of the scaffolding."""
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
        out.append(rel.as_posix())
    return tuple(out)


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
    return written


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
    "Skeleton",
    "apply_skeleton",
    "is_bare_project_root",
    "list_skeletons",
    "load_skeleton",
    "skeletons_dir",
]
