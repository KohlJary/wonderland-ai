"""Tests for SemanticStore — markdown-backed distilled beliefs."""

from __future__ import annotations

from pathlib import Path

from wonderland import SemanticStore


def test_path_is_under_dot_wonderland_memory(tmp_path: Path) -> None:
    store = SemanticStore(tmp_path, "cheshire_cat")
    expected = tmp_path / ".wonderland" / "memory" / "cheshire_cat" / "semantic"
    assert store.path == expected


def test_read_missing_topic_returns_empty(tmp_path: Path) -> None:
    store = SemanticStore(tmp_path, "cheshire_cat")
    assert store.read("anything") == ""


def test_write_then_read_roundtrip(tmp_path: Path) -> None:
    store = SemanticStore(tmp_path, "cheshire_cat")
    store.write("architecture", "## Bus is Redis Streams.\n\nCaucus pattern per spec §3.")
    content = store.read("architecture")
    assert "Bus is Redis Streams" in content


def test_write_creates_parent_directory(tmp_path: Path) -> None:
    store = SemanticStore(tmp_path, "cheshire_cat")
    store.write("conventions", "we slug titles for filenames")
    assert store.path.is_dir()


def test_topic_is_slugified_for_filename(tmp_path: Path) -> None:
    """Spaces and punctuation in topic names become slug-friendly."""
    store = SemanticStore(tmp_path, "cheshire_cat")
    store.write("System Conventions!", "content")
    files = sorted(store.path.glob("*.md"))
    assert len(files) == 1
    assert files[0].name == "system-conventions.md"


def test_write_replaces_existing_topic(tmp_path: Path) -> None:
    store = SemanticStore(tmp_path, "cheshire_cat")
    store.write("architecture", "first version")
    store.write("architecture", "second version")
    assert store.read("architecture") == "second version"


def test_list_topics_returns_stems_alphabetically(tmp_path: Path) -> None:
    store = SemanticStore(tmp_path, "cheshire_cat")
    store.write("zoo", "z")
    store.write("alpha", "a")
    store.write("middle", "m")
    assert store.list_topics() == ["alpha", "middle", "zoo"]


def test_list_topics_empty_when_no_writes(tmp_path: Path) -> None:
    store = SemanticStore(tmp_path, "cheshire_cat")
    assert store.list_topics() == []


def test_as_text_concatenates_all_topics(tmp_path: Path) -> None:
    store = SemanticStore(tmp_path, "cheshire_cat")
    store.write("architecture", "Use Redis Streams.")
    store.write("conventions", "ADR Tradeoffs are non-optional.")
    text = store.as_text()
    assert "### architecture" in text
    assert "Use Redis Streams." in text
    assert "### conventions" in text
    assert "ADR Tradeoffs are non-optional." in text


def test_as_text_skips_empty_topics(tmp_path: Path) -> None:
    store = SemanticStore(tmp_path, "cheshire_cat")
    store.write("architecture", "real content")
    store.write("placeholder", "   ")  # whitespace only
    text = store.as_text()
    assert "architecture" in text
    assert "placeholder" not in text


def test_as_text_empty_when_no_topics(tmp_path: Path) -> None:
    store = SemanticStore(tmp_path, "cheshire_cat")
    assert store.as_text() == ""


def test_separate_agents_have_separate_stores(tmp_path: Path) -> None:
    cat = SemanticStore(tmp_path, "cheshire_cat")
    rabbit = SemanticStore(tmp_path, "white_rabbit")
    cat.write("architecture", "cat-view")
    rabbit.write("architecture", "rabbit-view")
    assert cat.read("architecture") == "cat-view"
    assert rabbit.read("architecture") == "rabbit-view"
    assert cat.path != rabbit.path
