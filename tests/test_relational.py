"""Tests for RelationalStore — per-other-agent notes."""

from __future__ import annotations

from pathlib import Path

from wonderland import RelationalStore


def test_path_is_under_dot_wonderland_memory(tmp_path: Path) -> None:
    store = RelationalStore(tmp_path, "cheshire_cat")
    expected = tmp_path / ".wonderland" / "memory" / "cheshire_cat" / "relational"
    assert store.path == expected


def test_read_missing_returns_empty(tmp_path: Path) -> None:
    store = RelationalStore(tmp_path, "cheshire_cat")
    assert store.read("white_rabbit") == ""


def test_write_then_read_roundtrip(tmp_path: Path) -> None:
    store = RelationalStore(tmp_path, "cheshire_cat")
    store.write("white_rabbit", "Asks for estimates I shouldn't be giving.")
    assert "estimates" in store.read("white_rabbit")


def test_write_creates_parent_directory(tmp_path: Path) -> None:
    store = RelationalStore(tmp_path, "cheshire_cat")
    store.write("white_rabbit", "note")
    assert store.path.is_dir()


def test_other_name_used_as_filename_directly(tmp_path: Path) -> None:
    """Agent names are already canonical snake_case; no slugification."""
    store = RelationalStore(tmp_path, "cheshire_cat")
    store.write("white_rabbit", "note")
    files = sorted(store.path.glob("*.md"))
    assert files[0].name == "white_rabbit.md"


def test_write_replaces_existing_note(tmp_path: Path) -> None:
    store = RelationalStore(tmp_path, "cheshire_cat")
    store.write("white_rabbit", "first")
    store.write("white_rabbit", "second")
    assert store.read("white_rabbit") == "second"


def test_list_others_returns_names_alphabetically(tmp_path: Path) -> None:
    store = RelationalStore(tmp_path, "cheshire_cat")
    store.write("white_rabbit", "...")
    store.write("alice", "...")
    store.write("mad_hatter", "...")
    assert store.list_others() == ["alice", "mad_hatter", "white_rabbit"]


def test_list_others_empty_when_no_writes(tmp_path: Path) -> None:
    store = RelationalStore(tmp_path, "cheshire_cat")
    assert store.list_others() == []


def test_for_speakers_returns_formatted_block(tmp_path: Path) -> None:
    store = RelationalStore(tmp_path, "cheshire_cat")
    store.write("white_rabbit", "tries to push estimates onto me; gentle redirect")
    store.write("alice", "her naive questions often surface load-bearing assumptions")
    block = store.for_speakers(["alice", "white_rabbit"])
    assert "## Relational notes" in block
    assert "### alice" in block
    assert "### white_rabbit" in block
    assert "naive questions" in block
    assert "gentle redirect" in block


def test_for_speakers_skips_empty_notes(tmp_path: Path) -> None:
    store = RelationalStore(tmp_path, "cheshire_cat")
    store.write("white_rabbit", "real notes")
    # no notes for alice
    block = store.for_speakers(["alice", "white_rabbit"])
    assert "alice" not in block
    assert "white_rabbit" in block


def test_for_speakers_empty_when_no_notes(tmp_path: Path) -> None:
    store = RelationalStore(tmp_path, "cheshire_cat")
    block = store.for_speakers(["white_rabbit", "alice"])
    assert block == ""


def test_for_speakers_preserves_input_order(tmp_path: Path) -> None:
    store = RelationalStore(tmp_path, "cheshire_cat")
    store.write("zebra", "z note")
    store.write("alpha", "a note")
    block = store.for_speakers(["zebra", "alpha"])
    z_pos = block.index("zebra")
    a_pos = block.index("alpha")
    assert z_pos < a_pos


def test_separate_agents_have_separate_notes(tmp_path: Path) -> None:
    cat = RelationalStore(tmp_path, "cheshire_cat")
    rabbit = RelationalStore(tmp_path, "white_rabbit")
    cat.write("alice", "cat's view of alice")
    rabbit.write("alice", "rabbit's view of alice")
    assert cat.read("alice") == "cat's view of alice"
    assert rabbit.read("alice") == "rabbit's view of alice"
