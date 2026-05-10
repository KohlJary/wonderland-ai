"""Discover + load release-notes markdown files.

Release notes live at the repo root in ``release-notes/<version>.md``
— one file per release. They get committed alongside the code that
ships in that release; the in-app viewer surfaces them so an
operator can confirm what shipped without leaving the TUI.

Path resolution mirrors the snapshot-root trick in ``tui/app.py``:
walk up from this module's installed location to find the repo
root (``parents[2]`` from ``src/wonderland/release_notes.py`` →
``wonderland-ai/``). For editable installs this lands on the actual
checkout; for pip-installed wheels there's no ``release-notes/``
directory and the loader degrades to "no notes found" cleanly.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


_VERSION_FILE_RE = re.compile(r"^(\d+\.\d+\.\d+(?:[-+].+)?)\.md$")


@dataclass(frozen=True)
class ReleaseNote:
    """One release-notes markdown file on disk.

    ``version`` is the filename stem (e.g. ``"0.4.0"``); ``path`` is
    the absolute path to the file. Sorting on ``version_key`` orders
    notes newest-first using a tuple of integers (so 0.10.0 lands
    after 0.9.0 instead of lex-sorting before it).
    """

    version: str
    path: Path

    @property
    def version_key(self) -> tuple[int, ...]:
        """Tuple key for ordering. Strips any pre-release / build
        suffix (``0.4.0-rc1`` → ``(0, 4, 0)``) so the dominant
        sort is on the major.minor.patch numbers — pre-releases
        and the corresponding GA sort together which is the
        operator's expected behavior."""
        head = self.version.split("-", 1)[0].split("+", 1)[0]
        try:
            return tuple(int(p) for p in head.split("."))
        except ValueError:
            return (0,)


def _release_notes_dir() -> Path:
    """Locate the ``release-notes/`` directory at the repo root."""
    return Path(__file__).resolve().parents[2] / "release-notes"


def list_release_notes() -> list[ReleaseNote]:
    """Return all release-notes markdown files, newest first.

    Filename pattern: ``<semver>.md`` (e.g. ``0.4.0.md``,
    ``1.2.3-rc1.md``). Files that don't match are skipped silently
    — repo-root junk shouldn't crash the in-app viewer.
    """
    notes_dir = _release_notes_dir()
    if not notes_dir.is_dir():
        return []
    out: list[ReleaseNote] = []
    for path in notes_dir.iterdir():
        if not path.is_file():
            continue
        match = _VERSION_FILE_RE.match(path.name)
        if match is None:
            continue
        out.append(ReleaseNote(version=match.group(1), path=path))
    out.sort(key=lambda n: n.version_key, reverse=True)
    return out


def load_release_note(version: str) -> str:
    """Read the markdown body for ``version``. Raises FileNotFound
    if the version file isn't present — caller should match against
    ``list_release_notes`` to know the file exists before calling."""
    path = _release_notes_dir() / f"{version}.md"
    return path.read_text(encoding="utf-8")


__all__ = [
    "ReleaseNote",
    "list_release_notes",
    "load_release_note",
]
