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
    metadata. See analysis 016 followup. run_tests added in analysis
    028 followup so M5 Tweedles can iterate red→green properly."""
    defs = Tools.tool_definitions()
    names = {d["name"] for d in defs}
    assert names == {
        "read_file",
        "write_file",
        "list_files",
        "grep",
        "git_status",
        "git_diff",
        "run_tests",
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


# ---------- run_tests ----------


def _seed_pytest_project(root: Path) -> None:
    """Drop a tiny pytest-runnable project at ``root``: one passing test,
    one failing test, plus a conftest the tests can use.
    """
    (root / "tests").mkdir()
    (root / "tests" / "__init__.py").write_text("")
    (root / "tests" / "test_pass.py").write_text(
        "def test_truthy():\n    assert True\n\n"
        "def test_addition():\n    assert 1 + 1 == 2\n"
    )
    (root / "tests" / "test_fail.py").write_text(
        "def test_falsy():\n    assert False, 'this is the failure message'\n"
    )


def test_run_tests_reports_pass_and_fail_counts(tmp_path: Path) -> None:
    _seed_pytest_project(tmp_path)
    tools = Tools(tmp_path)
    result = tools.run_tests()
    # The summary line should reflect both outcomes.
    assert "passed" in result
    assert "failed" in result
    assert "2 passed" in result
    assert "1 failed" in result


def test_run_tests_reports_failure_detail(tmp_path: Path) -> None:
    """The compact summary should name the failing test by id so the
    Tweedle can scope a follow-up run to it."""
    _seed_pytest_project(tmp_path)
    tools = Tools(tmp_path)
    result = tools.run_tests()
    assert "test_fail.py::test_falsy" in result


def test_run_tests_with_paths_runs_only_those(tmp_path: Path) -> None:
    """Scoping to a specific path is the load-bearing usage pattern —
    Tweedles iterate against the test file matching the feature they
    just shipped, not the full suite each time."""
    _seed_pytest_project(tmp_path)
    tools = Tools(tmp_path)
    result = tools.run_tests(paths=["tests/test_pass.py"])
    assert "2 passed" in result
    # The failing test in test_fail.py should NOT appear because we
    # didn't run it.
    assert "test_falsy" not in result


def test_run_tests_no_tests_collected(tmp_path: Path) -> None:
    """Empty project — pytest exit code 5. Result string explains."""
    (tmp_path / "tests").mkdir()  # exists but empty
    tools = Tools(tmp_path)
    result = tools.run_tests()
    assert "no tests" in result.lower()


def test_run_tests_rejects_path_escape(tmp_path: Path) -> None:
    """Sandbox check: paths outside project_root must be rejected."""
    _seed_pytest_project(tmp_path)
    tools = Tools(tmp_path)
    with pytest.raises(ToolError, match="escapes project root"):
        tools.run_tests(paths=["../outside/test_evil.py"])


def test_run_tests_truncates_oversized_output(tmp_path: Path) -> None:
    """A suite with hundreds of failures shouldn't dominate context.
    Result must stay under MAX_TEST_OUTPUT_BYTES."""
    from wonderland.tools import MAX_TEST_OUTPUT_BYTES

    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "__init__.py").write_text("")
    # Generate 200 failing tests with deliberately verbose assertion
    # messages — guarantees pytest output blows past the cap.
    failing_tests = "\n\n".join(
        f"def test_fail_{i}():\n"
        f"    assert False, "
        f"'failure message {i} ' + 'x' * 100"
        for i in range(200)
    )
    (tmp_path / "tests" / "test_many.py").write_text(failing_tests)
    tools = Tools(tmp_path)
    result = tools.run_tests()
    assert len(result.encode("utf-8")) <= MAX_TEST_OUTPUT_BYTES + 100  # tiny slop
    # Summary still readable.
    assert "200" in result and "failed" in result


def test_run_tests_via_execute_dispatch(tmp_path: Path) -> None:
    """The execute() dispatch path is what the Tweedle's tool-use loop
    actually calls — make sure the wiring works."""
    _seed_pytest_project(tmp_path)
    tools = Tools(tmp_path)
    result = tools.execute("run_tests", {"paths": ["tests/test_pass.py"]})
    assert "2 passed" in result


def test_run_tests_surfaces_collection_failure_prominently(tmp_path: Path) -> None:
    """When the import chain is broken, pytest can't collect ANY
    tests — every test signal is hidden until the import is fixed.
    The result must lead with this so the LLM doesn't try to interpret
    a (silently empty) summary line.

    Regression test for the skeleton-overwrite pattern documented in
    analyses 029 and 030: Tweedles removed HelloMessage from
    models.py but left messages.py importing it, breaking conftest's
    import chain and hiding all real test signal.
    """
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "__init__.py").write_text("")
    (tmp_path / "tests" / "conftest.py").write_text(
        "from src.broken_module import nonexistent\n"
    )
    (tmp_path / "tests" / "test_anything.py").write_text(
        "def test_should_be_invisible():\n    assert True\n"
    )
    tools = Tools(tmp_path)
    result = tools.run_tests()
    assert "BUILD FAILURE" in result, (
        f"collection failures must lead with BUILD FAILURE, got: {result!r}"
    )
    # Result should mention ImportError or ModuleNotFoundError.
    assert "Error" in result or "Module" in result


def test_run_tests_collection_error_names_offending_file(tmp_path: Path) -> None:
    """The result should point at the file whose import chain is
    broken so the LLM can navigate directly there with read_file."""
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "__init__.py").write_text("")
    (tmp_path / "tests" / "conftest.py").write_text(
        "import this_module_does_not_exist\n"
    )
    (tmp_path / "tests" / "test_a.py").write_text("def test_a():\n    pass\n")
    tools = Tools(tmp_path)
    result = tools.run_tests()
    assert "BUILD FAILURE" in result
    # Either the collection-error or the import-error path should
    # surface enough detail to navigate.
    assert "this_module_does_not_exist" in result or "conftest" in result


def test_run_tests_normal_failure_does_not_trigger_build_failure_path(
    tmp_path: Path,
) -> None:
    """A regular assert-failure test must not be misclassified as a
    build failure. The two surfaces are different signals and the
    LLM treats them differently."""
    _seed_pytest_project(tmp_path)
    tools = Tools(tmp_path)
    result = tools.run_tests()
    assert "BUILD FAILURE" not in result, (
        "test failures are different from build failures; don't conflate"
    )
    assert "failed" in result


def test_run_tests_with_timeout_passthrough(tmp_path: Path) -> None:
    """The timeout_seconds parameter from the tool input should reach
    the underlying subprocess.run call. We don't actually trigger a
    timeout (would slow the test suite); we just check the parameter
    is accepted without error."""
    _seed_pytest_project(tmp_path)
    tools = Tools(tmp_path)
    # Generous timeout — confirms the param flows through
    result = tools.execute(
        "run_tests",
        {"paths": ["tests/test_pass.py"], "timeout_seconds": 30.0},
    )
    assert "passed" in result
