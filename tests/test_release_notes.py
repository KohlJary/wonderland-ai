"""Tests for ``wonderland.release_notes`` — the loader behind the
ReleaseNotesScreen."""

from __future__ import annotations

from pathlib import Path

from wonderland.release_notes import (
    ReleaseNote,
    list_release_notes,
)


def test_list_release_notes_returns_existing_files() -> None:
    """The 0.4.0 file ships in this branch — discovery should
    find it. Validates the path-resolution heuristic still lands
    on the repo's ``release-notes/`` dir."""
    entries = list_release_notes()
    assert entries, "expected at least one release notes file"
    assert any(e.version == "0.4.0" for e in entries)
    for e in entries:
        assert e.path.is_file()


def test_release_note_version_key_orders_correctly() -> None:
    """0.10.0 sorts after 0.9.0 (numeric ordering, not lex)."""
    a = ReleaseNote(version="0.9.0", path=Path("/x/0.9.0.md"))
    b = ReleaseNote(version="0.10.0", path=Path("/x/0.10.0.md"))
    assert a.version_key < b.version_key


def test_pre_release_version_key_handles_suffix() -> None:
    """0.4.0-rc1 sorts together with 0.4.0 — the suffix is
    stripped for ordering purposes."""
    rc = ReleaseNote(version="0.4.0-rc1", path=Path("/x/0.4.0-rc1.md"))
    ga = ReleaseNote(version="0.4.0", path=Path("/x/0.4.0.md"))
    assert rc.version_key == ga.version_key
