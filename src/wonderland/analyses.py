"""Analyses index — runtime access to the project's field-notes
collection.

The analyses are the project's load-bearing thinking: each one
walks through what a specific run revealed (substrate bugs found,
directive iterations validated, hypotheses falsified, banner
results). They're what makes 'why is this framework the way it
is' answerable without a 30-minute conversation.

Bundled with the package at ``closet/analyses/`` so a fresh ``pip
install`` user can browse the corpus from inside the TUI without
needing the source checkout. Falls back to ``<repo>/analyses/`` for
developers running from a checkout (gives them edits-without-
rebuild).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def _bundled_analyses_dir() -> Path:
    """Bundled-with-the-package analyses dir."""
    import wonderland

    return Path(wonderland.__file__).parent / "closet" / "analyses"


def _checkout_analyses_dir() -> Path | None:
    """If running from a source checkout, the repo's authoritative
    ``analyses/`` directory. Returns None when not in a checkout."""
    import wonderland

    pkg_root = Path(wonderland.__file__).resolve().parent
    # Walk up from src/wonderland/ to find the repo root with an
    # analyses/ directory next to src/.
    candidate = pkg_root.parent.parent / "analyses"
    if candidate.is_dir() and any(candidate.glob("*.md")):
        return candidate
    return None


def analyses_dir() -> Path:
    """Resolve the analyses directory at runtime.

    Prefers the source-checkout location when available (so
    developers see edits without rebuilding the wheel). Falls back
    to the bundled package data for installed users.
    """
    checkout = _checkout_analyses_dir()
    if checkout is not None:
        return checkout
    return _bundled_analyses_dir()


@dataclass(frozen=True)
class AnalysisEntry:
    """One analysis file's metadata."""

    slug: str  # the filename stem, e.g. '032-tdd-serial-v3-banner'
    number: int  # the leading numeric prefix, parsed for sorting
    title: str  # parsed from the first ``# `` heading; falls back to slug
    path: Path  # absolute path to the .md file


def _parse_first_heading(path: Path) -> str:
    """Pull the first ``# `` heading out of an analysis file. Falls
    back to the file stem if no heading line is present in the
    first few lines (analyses always have one, but be robust).
    """
    try:
        with path.open(encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                if i > 20:
                    break
                stripped = line.strip()
                if stripped.startswith("# "):
                    return stripped[2:].strip()
    except OSError:
        pass
    return path.stem


def list_analyses() -> list[AnalysisEntry]:
    """Return all analyses, sorted by number ascending. Empty list
    if the analyses directory doesn't exist or has no .md files."""
    d = analyses_dir()
    if not d.is_dir():
        return []
    out: list[AnalysisEntry] = []
    for path in sorted(d.glob("*.md")):
        slug = path.stem
        # Numeric prefix: '032-foo-bar' → 32. Files without a numeric
        # prefix sort last (number = 9999 sentinel).
        try:
            number = int(slug.split("-", 1)[0])
        except (ValueError, IndexError):
            number = 9999
        title = _parse_first_heading(path)
        out.append(AnalysisEntry(slug=slug, number=number, title=title, path=path))
    out.sort(key=lambda e: (e.number, e.slug))
    return out


def load_analysis(slug: str) -> str:
    """Read the markdown content of one analysis by slug.

    ``slug`` is the filename stem (e.g. ``'032-tdd-serial-v3-banner'``).
    Raises ``FileNotFoundError`` if not present.
    """
    d = analyses_dir()
    path = d / f"{slug}.md"
    if not path.is_file():
        raise FileNotFoundError(
            f"analysis not found: {path}. Available: "
            f"{[e.slug for e in list_analyses()]}"
        )
    return path.read_text(encoding="utf-8", errors="replace")


__all__ = [
    "AnalysisEntry",
    "analyses_dir",
    "list_analyses",
    "load_analysis",
]
