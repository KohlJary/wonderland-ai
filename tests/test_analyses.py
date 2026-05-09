"""Tests for the analyses index module."""

from __future__ import annotations

import pytest

from wonderland.analyses import (
    AnalysisEntry,
    analyses_dir,
    list_analyses,
    load_analysis,
)


def test_analyses_dir_resolves() -> None:
    """The runtime resolver should land on a directory that exists
    + has at least some .md files."""
    d = analyses_dir()
    assert d.is_dir(), f"analyses dir missing: {d}"
    md_files = list(d.glob("*.md"))
    assert len(md_files) > 0, f"no .md files in {d}"


def test_list_analyses_returns_entries() -> None:
    entries = list_analyses()
    assert len(entries) > 0
    for e in entries:
        assert isinstance(e, AnalysisEntry)
        assert e.slug
        assert e.title
        assert e.path.is_file()


def test_list_analyses_sorted_by_number() -> None:
    """Entries with numeric prefixes sort ascending; the first few
    should be analyses 001, 002, 003 in order."""
    entries = list_analyses()
    if len(entries) < 3:
        pytest.skip("need at least 3 analyses")
    assert entries[0].number == 1
    assert entries[1].number == 2
    assert entries[2].number == 3


def test_list_includes_recent_banners() -> None:
    """The 030-032 cluster should be present — those are the
    substrate-convergence + tdd-serial banner analyses that the
    framework rests on."""
    entries = list_analyses()
    slugs = {e.slug for e in entries}
    assert "030-directive-bounds" in slugs
    assert "031-tdd-serial-v1" in slugs
    assert "032-tdd-serial-v3-banner" in slugs


def test_load_analysis_returns_markdown() -> None:
    content = load_analysis("032-tdd-serial-v3-banner")
    assert content.startswith("# ")
    # The 032 banner names the cost story
    assert "$4.7236" in content


def test_load_missing_raises_with_available_list() -> None:
    with pytest.raises(FileNotFoundError) as excinfo:
        load_analysis("999-nonexistent")
    msg = str(excinfo.value)
    assert "Available:" in msg


def test_titles_parsed_from_first_heading() -> None:
    """Every analysis has a ``# `` heading on its first non-blank
    line. The parser should pull it out (not just use the slug)."""
    entries = list_analyses()
    for e in entries:
        # Title shouldn't equal slug for files with proper headings
        # (which is all of them — the field-notes corpus is consistent).
        assert e.title != e.slug, (
            f"{e.slug}: title parser fell back to slug; check "
            f"the first ## line of {e.path}"
        )
