"""Tests for the file-primitive tools the Tweedles use to ship code."""

from __future__ import annotations

from pathlib import Path

import pytest

from wonderland.tools import (
    MAX_GREP_HITS,
    MAX_LIST_ENTRIES,
    MAX_READ_BYTES,
    ToolError,
    Tools,
)

# ---------- helpers ----------


def _seed(root: Path) -> None:
    """Seed a small project tree for read/list/grep tests."""
    (root / "src").mkdir()
    (root / "src" / "main.py").write_text("def hello():\n    return 'world'\n")
    (root / "src" / "utils.py").write_text("def helper():\n    return 42\n")
    (root / "src" / "sub").mkdir()
    (root / "src" / "sub" / "nested.py").write_text("x = 1\n")
    (root / "tests").mkdir()
    (root / "tests" / "test_main.py").write_text("def test_hello():\n    pass\n")


# ---------- write + read round-trip ----------


def test_write_then_read_round_trip(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    msg = tools.write_file("hello.py", "print('hi')\n")
    assert "wrote" in msg
    assert tools.read_file("hello.py") == "print('hi')\n"


def test_write_creates_parent_directories(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    tools.write_file("a/b/c/file.txt", "content")
    assert (tmp_path / "a" / "b" / "c" / "file.txt").is_file()


def test_write_overwrites_existing_file(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    tools.write_file("f.txt", "first")
    tools.write_file("f.txt", "second")
    assert tools.read_file("f.txt") == "second"


def test_write_to_directory_path_raises(tmp_path: Path) -> None:
    (tmp_path / "adir").mkdir()
    tools = Tools(tmp_path)
    with pytest.raises(ToolError, match="path is a directory"):
        tools.write_file("adir", "content")


def test_read_missing_file_raises(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    with pytest.raises(ToolError, match="file not found"):
        tools.read_file("nope.txt")


def test_read_directory_path_raises(tmp_path: Path) -> None:
    (tmp_path / "adir").mkdir()
    tools = Tools(tmp_path)
    with pytest.raises(ToolError, match="not a file"):
        tools.read_file("adir")


def test_read_truncates_oversized_file(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    big = "a" * (MAX_READ_BYTES + 100)
    (tmp_path / "big.txt").write_text(big)
    out = tools.read_file("big.txt")
    assert "[truncated:" in out
    # The visible portion should be exactly MAX_READ_BYTES of content.
    visible_content = out.split("\n\n[truncated:")[0]
    assert len(visible_content) == MAX_READ_BYTES


def test_read_binary_raises(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    (tmp_path / "binary.bin").write_bytes(b"\x80\x81\x82\x83")
    with pytest.raises(ToolError, match="not valid UTF-8"):
        tools.read_file("binary.bin")


# ---------- sandbox safety ----------


def test_relative_dot_dot_path_rejected(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    with pytest.raises(ToolError, match="escapes project root"):
        tools.read_file("../escape.txt")


def test_absolute_path_outside_root_rejected(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    # /etc is almost certainly not inside tmp_path.
    with pytest.raises(ToolError, match="escapes project root"):
        tools.read_file("/etc/passwd")


def test_absolute_path_inside_root_accepted(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    tools.write_file("ok.txt", "x")
    inside = str((tmp_path / "ok.txt").resolve())
    assert tools.read_file(inside) == "x"


def test_symlink_escape_rejected(tmp_path: Path) -> None:
    """A symlink in-tree pointing out of tree gets caught at resolve time."""
    outside = tmp_path.parent / "outside-target.txt"
    outside.write_text("secret")
    try:
        link = tmp_path / "link-out"
        link.symlink_to(outside)
        tools = Tools(tmp_path)
        with pytest.raises(ToolError, match="escapes project root"):
            tools.read_file("link-out")
    finally:
        outside.unlink(missing_ok=True)


# ---------- list_files ----------


def test_list_files_flat_directory(tmp_path: Path) -> None:
    _seed(tmp_path)
    tools = Tools(tmp_path)
    out = tools.list_files("src")
    assert "src/main.py" in out
    assert "src/utils.py" in out
    assert "src/sub" in out
    # Non-recursive: nested files don't appear.
    assert "nested.py" not in out


def test_list_files_with_glob_recurses(tmp_path: Path) -> None:
    _seed(tmp_path)
    tools = Tools(tmp_path)
    out = tools.list_files(".", pattern="*.py")
    assert "src/main.py" in out
    assert "src/utils.py" in out
    assert "src/sub/nested.py" in out
    assert "tests/test_main.py" in out


def test_list_files_empty_directory(tmp_path: Path) -> None:
    (tmp_path / "empty").mkdir()
    tools = Tools(tmp_path)
    assert tools.list_files("empty") == "(no entries)"


def test_list_files_missing_directory_raises(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    with pytest.raises(ToolError, match="directory not found"):
        tools.list_files("nope")


def test_list_files_truncates_at_cap(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    for i in range(MAX_LIST_ENTRIES + 50):
        (tmp_path / f"f{i:04d}.txt").write_text("x")
    out = tools.list_files(".")
    assert "[truncated:" in out
    # Visible entries should equal MAX_LIST_ENTRIES.
    lines = out.split("\n")
    visible = [line for line in lines if not line.startswith("[truncated")]
    assert len(visible) == MAX_LIST_ENTRIES


# ---------- grep ----------


def test_grep_finds_simple_match(tmp_path: Path) -> None:
    _seed(tmp_path)
    tools = Tools(tmp_path)
    out = tools.grep("hello", "src")
    assert "src/main.py:1:def hello():" in out


def test_grep_returns_marker_when_no_matches(tmp_path: Path) -> None:
    _seed(tmp_path)
    tools = Tools(tmp_path)
    out = tools.grep("nonexistent_thing", "src")
    assert "no matches" in out


def test_grep_ignore_case(tmp_path: Path) -> None:
    _seed(tmp_path)
    tools = Tools(tmp_path)
    out = tools.grep("HELLO", "src", ignore_case=True)
    assert "main.py" in out


def test_grep_invalid_regex_raises(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    with pytest.raises(ToolError, match="invalid regex"):
        tools.grep("[unclosed", ".")


def test_grep_skips_binary_files(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    (tmp_path / "code.py").write_text("greeting = 'hello'\n")
    (tmp_path / "data.bin").write_bytes(b"\x80\x81hello\x82")
    out = tools.grep("hello", ".")
    # Hits in code.py only; data.bin is skipped silently.
    assert "code.py" in out
    assert "data.bin" not in out


def test_grep_truncates_at_cap(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    # One file with > MAX_GREP_HITS matches.
    lines = "\n".join(f"hit_{i}" for i in range(MAX_GREP_HITS + 50))
    (tmp_path / "many.txt").write_text(lines)
    out = tools.grep("hit_", ".")
    assert "truncated at" in out


def test_grep_on_single_file(tmp_path: Path) -> None:
    _seed(tmp_path)
    tools = Tools(tmp_path)
    out = tools.grep("hello", "src/main.py")
    assert "src/main.py:1:" in out


# ---------- tool_definitions schema shape ----------


def test_tool_definitions_returns_full_set() -> None:
    """Working-tree-as-artifact: git_status + git_diff joined the
    set so reviewers can read what shipped without consulting parallel
    metadata. See analysis 016 followup."""
    defs = Tools.tool_definitions()
    names = {d["name"] for d in defs}
    assert names == {
        "read_file",
        "write_file",
        "list_files",
        "grep",
        "git_status",
        "git_diff",
    }


def test_tool_definitions_have_input_schemas() -> None:
    for d in Tools.tool_definitions():
        assert "name" in d
        assert "description" in d
        assert "input_schema" in d
        assert d["input_schema"]["type"] == "object"
        assert "properties" in d["input_schema"]


# ---------- execute dispatch ----------


def test_execute_routes_to_each_tool(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    assert "wrote" in tools.execute("write_file", {"path": "f.txt", "content": "hi"})
    assert tools.execute("read_file", {"path": "f.txt"}) == "hi"
    assert "f.txt" in tools.execute("list_files", {"directory": "."})
    assert "f.txt:1:hi" in tools.execute("grep", {"pattern": "hi"})


def test_execute_unknown_tool_raises(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    with pytest.raises(ToolError, match="unknown tool"):
        tools.execute("rm_rf", {"path": "/"})
