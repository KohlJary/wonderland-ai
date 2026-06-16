"""Tests for the file-primitive tools the Tweedles use to ship code."""

from __future__ import annotations

from datetime import datetime, timezone
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


# ---------- line-range reads (obol-demo3 cost-reduction follow-up) ----------


def test_read_with_offset_and_limit_returns_numbered_slice(
    tmp_path: Path,
) -> None:
    """Range read returns just the requested window with 1-indexed
    line-number prefixes. The Tweedles can grep for a symbol and
    then read just its definition block, instead of re-reading
    full 200-line files 40+ times like obol-demo3 M7 telemetry
    showed."""
    tools = Tools(tmp_path)
    (tmp_path / "src.py").write_text(
        "line1\nline2\nline3\nline4\nline5\n"
    )
    out = tools.read_file("src.py", offset=2, limit=2)
    assert "    2\tline2" in out
    assert "    3\tline3" in out
    assert "line1" not in out
    assert "line4" not in out
    assert "[lines 2-3 of 5 in src.py]" in out


def test_read_offset_only_reads_from_offset_to_eof(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    (tmp_path / "src.py").write_text("a\nb\nc\nd\n")
    out = tools.read_file("src.py", offset=3)
    assert "    3\tc" in out
    assert "    4\td" in out
    assert "    1" not in out


def test_read_limit_only_reads_first_n_lines(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    (tmp_path / "src.py").write_text("a\nb\nc\nd\n")
    out = tools.read_file("src.py", limit=2)
    assert "    1\ta" in out
    assert "    2\tb" in out
    assert "    3" not in out
    assert "[lines 1-2 of 4" in out


def test_read_full_file_unchanged_when_no_range_params(
    tmp_path: Path,
) -> None:
    """Back-compat: callers that don't pass offset/limit get the
    legacy full-file output, no line-number prefixes."""
    tools = Tools(tmp_path)
    (tmp_path / "src.py").write_text("hello\nworld\n")
    out = tools.read_file("src.py")
    assert out == "hello\nworld\n"
    assert "[lines" not in out  # no range footer


def test_read_invalid_offset_raises(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    (tmp_path / "src.py").write_text("a\nb\n")
    with pytest.raises(ToolError, match="offset must be"):
        tools.read_file("src.py", offset=0)


def test_read_offset_past_eof_raises(tmp_path: Path) -> None:
    """Clear feedback when the agent tries to read past EOF, instead
    of silently returning empty."""
    tools = Tools(tmp_path)
    (tmp_path / "src.py").write_text("a\nb\n")
    with pytest.raises(ToolError, match="past EOF"):
        tools.read_file("src.py", offset=10)


def test_read_invalid_limit_raises(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    (tmp_path / "src.py").write_text("a\nb\n")
    with pytest.raises(ToolError, match="limit must be"):
        tools.read_file("src.py", limit=0)


def test_read_dispatch_via_execute_with_range(tmp_path: Path) -> None:
    """Execute() path forwards offset + limit correctly."""
    tools = Tools(tmp_path)
    (tmp_path / "src.py").write_text("a\nb\nc\nd\n")
    out = tools.execute(
        "read_file",
        {"path": "src.py", "offset": 2, "limit": 2},
    )
    assert "    2\tb" in out
    assert "    3\tc" in out
    assert "    1" not in out


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
    028 followup so M5 Tweedles can iterate red→green properly.
    str_replace + insert added in T67 (P10) for token-cheap iterative
    file authoring. verify_imports added in P16 T-v5 — Caterpillar's
    static-check tool for the bug class between code review and
    test collection. exec_smoke_probe added after the obol M2
    retrospective — for the runtime-only bug class (SQL CHECK
    constraints, schema drift, framework wiring) that even
    verify_imports can't catch because the code is syntactically
    fine; only running it surfaces the failure."""
    defs = Tools.tool_definitions()
    names = {d["name"] for d in defs}
    assert names == {
        "read_file",
        "write_file",
        "delete_file",
        "str_replace",
        "insert",
        "list_files",
        "grep",
        "git_status",
        "git_diff",
        "run_tests",
        "verify_imports",
        "exec_smoke_probe",
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


# ---------------------------------------------------------------------
# Tool-call observability (T66 / P10)
# ---------------------------------------------------------------------


def test_on_tool_call_callback_fires_per_dispatch(tmp_path: Path) -> None:
    """When ``on_tool_call`` is set, each successful execute()
    invocation produces a ToolCallEvent with timing + sizes."""
    from wonderland.tools import ToolCallEvent

    captured: list[ToolCallEvent] = []
    tools = Tools(tmp_path, on_tool_call=captured.append)

    (tmp_path / "hello.txt").write_text("hi there\n")
    out = tools.execute("read_file", {"path": "hello.txt"}, agent_id="alice")
    assert "hi there" in out

    assert len(captured) == 1
    event = captured[0]
    assert event.tool_name == "read_file"
    assert event.agent_id == "alice"
    assert event.error is None
    assert event.elapsed_ms >= 0.0
    assert event.result_bytes > 0
    # path is small enough to round-trip verbatim
    assert event.args_summary["path"] == "hello.txt"


def test_on_tool_call_summarizes_large_write_content(tmp_path: Path) -> None:
    """write_file's content arg can be many KB; the summary
    replaces it with a byte-count entry rather than echoing the
    whole blob into the JSONL log."""
    from wonderland.tools import ToolCallEvent

    captured: list[ToolCallEvent] = []
    tools = Tools(tmp_path, on_tool_call=captured.append)

    big_content = "x" * 8192
    tools.execute(
        "write_file",
        {"path": "big.txt", "content": big_content},
        agent_id="tweedledum",
    )

    event = captured[0]
    assert event.tool_name == "write_file"
    assert event.agent_id == "tweedledum"
    # content should be summarized, not echoed
    assert "content" not in event.args_summary
    assert event.args_summary["content_bytes"] == 8192
    # input_bytes captures the cost of resending the whole file
    assert event.input_bytes >= 8192


def test_on_tool_call_captures_errors(tmp_path: Path) -> None:
    """Tool errors propagate normally but the observer still
    records the attempt (with error message captured)."""
    from wonderland.tools import ToolCallEvent

    captured: list[ToolCallEvent] = []
    tools = Tools(tmp_path, on_tool_call=captured.append)

    with pytest.raises(ToolError):
        tools.execute("read_file", {"path": "missing.txt"}, agent_id="hatter")

    assert len(captured) == 1
    event = captured[0]
    assert event.tool_name == "read_file"
    assert event.error is not None
    assert "missing.txt" in event.error
    assert event.result_bytes == 0


def test_on_tool_call_writer_failure_does_not_break_dispatch(tmp_path: Path) -> None:
    """If the observer callback raises, the underlying tool result
    must still be returned to the caller — observability is
    best-effort and never masks the real work."""

    def broken_writer(_event):
        raise RuntimeError("observer is broken")

    tools = Tools(tmp_path, on_tool_call=broken_writer)
    (tmp_path / "x.txt").write_text("hello\n")
    # Read should succeed despite the writer raising
    result = tools.execute("read_file", {"path": "x.txt"})
    assert "hello" in result


def test_jsonl_tool_call_writer_round_trip(tmp_path: Path) -> None:
    """Writer + reader round-trip every event field."""
    from wonderland.tools import (
        ToolCallEvent,
        jsonl_tool_call_writer,
        read_tool_calls,
    )

    path = tmp_path / "tool-calls.jsonl"
    write = jsonl_tool_call_writer(path)
    now = datetime.now(tz=timezone.utc)

    events = [
        ToolCallEvent(
            timestamp=now,
            tool_name="write_file",
            agent_id="tweedledum",
            args_summary={"path": "src/api.py", "content_bytes": 4096},
            input_bytes=4128,
            elapsed_ms=12.5,
            result_bytes=42,
            error=None,
        ),
        ToolCallEvent(
            timestamp=now,
            tool_name="run_tests",
            agent_id="tweedledee",
            args_summary={"paths": ["tests/test_api.py"]},
            input_bytes=20,
            elapsed_ms=850.2,
            result_bytes=1024,
            error=None,
        ),
    ]
    for ev in events:
        write(ev)

    read_back = read_tool_calls(path)
    assert read_back == events


def test_read_tool_calls_missing_file_returns_empty(tmp_path: Path) -> None:
    from wonderland.tools import read_tool_calls

    assert read_tool_calls(tmp_path / "nonexistent.jsonl") == []


# ---------------------------------------------------------------------
# Diff-based write tools (T67 / P10)
# ---------------------------------------------------------------------


def test_str_replace_unique_match_applies_patch(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    p = tmp_path / "x.py"
    p.write_text("def foo():\n    return False\n")
    result = tools.str_replace("x.py", "return False", "return True")
    assert "str_replace applied" in result
    assert p.read_text() == "def foo():\n    return True\n"


def test_str_replace_zero_matches_raises(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    p = tmp_path / "x.py"
    p.write_text("def foo():\n    return True\n")
    with pytest.raises(ToolError, match="not found"):
        tools.str_replace("x.py", "return False", "return True")


def test_str_replace_multiple_matches_raises(tmp_path: Path) -> None:
    """Ambiguous matches must be rejected; the LLM has to include
    more context for the match to be unique."""
    tools = Tools(tmp_path)
    p = tmp_path / "x.py"
    p.write_text("a = 1\nb = 1\nc = 1\n")
    with pytest.raises(ToolError, match="matches 3 times"):
        tools.str_replace("x.py", "= 1", "= 2")


def test_str_replace_empty_old_rejected(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    p = tmp_path / "x.py"
    p.write_text("hello\n")
    with pytest.raises(ToolError, match="cannot be empty"):
        tools.str_replace("x.py", "", "world")


def test_str_replace_with_empty_new_deletes(tmp_path: Path) -> None:
    """Deletion via str_replace(old, '') — the deletion primitive."""
    tools = Tools(tmp_path)
    p = tmp_path / "x.py"
    p.write_text("def foo():\n    print('debug')\n    return 42\n")
    tools.str_replace("x.py", "    print('debug')\n", "")
    assert p.read_text() == "def foo():\n    return 42\n"


def test_str_replace_missing_file_raises(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    with pytest.raises(ToolError, match="not found"):
        tools.str_replace("nope.py", "old", "new")


def test_str_replace_via_execute_dispatch(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    p = tmp_path / "x.py"
    p.write_text("a = 1\n")
    result = tools.execute(
        "str_replace",
        {"path": "x.py", "old": "a = 1", "new": "a = 42"},
    )
    assert "applied" in result
    assert p.read_text() == "a = 42\n"


def test_delete_file_removes_file(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    p = tmp_path / "doomed.md"
    p.write_text("content")
    result = tools.delete_file("doomed.md")
    assert "deleted" in result
    assert not p.exists()


def test_delete_file_idempotent_on_missing(tmp_path: Path) -> None:
    """An agent calling delete_file on a path that doesn't exist
    shouldn't crash — returns 'not found' so the LLM gets useful
    feedback without the meeting flow erroring out."""
    tools = Tools(tmp_path)
    result = tools.delete_file("never-existed.md")
    assert "no file at" in result.lower() or "not found" in result.lower()


def test_delete_file_refuses_directory(tmp_path: Path) -> None:
    """Sandbox-level guard: deleting a directory could cascade-prune
    entire feature/ticket trees by accident. Force the agent to
    name individual files."""
    tools = Tools(tmp_path)
    (tmp_path / "subdir").mkdir()
    with pytest.raises(ToolError, match="directory"):
        tools.delete_file("subdir")


def test_delete_file_via_execute_dispatch(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    p = tmp_path / "x.md"
    p.write_text("doomed")
    result = tools.execute("delete_file", {"path": "x.md"})
    assert "deleted" in result
    assert not p.exists()


def test_delete_file_sandbox_blocks_escape(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    with pytest.raises(ToolError, match="escape"):
        tools.delete_file("../outside.md")


def test_insert_after_line_n(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    p = tmp_path / "x.py"
    p.write_text("import os\nimport sys\n")
    tools.insert("x.py", 2, "import json")
    assert p.read_text() == "import os\nimport sys\nimport json\n"


def test_insert_prepend_with_zero(tmp_path: Path) -> None:
    """line_number=0 prepends at the top of the file."""
    tools = Tools(tmp_path)
    p = tmp_path / "x.py"
    p.write_text("def foo():\n    pass\n")
    tools.insert("x.py", 0, "#!/usr/bin/env python")
    assert p.read_text() == "#!/usr/bin/env python\ndef foo():\n    pass\n"


def test_insert_adds_trailing_newline_if_missing(tmp_path: Path) -> None:
    """If the inserted content lacks a trailing newline, one is
    added so the next line stays on its own line."""
    tools = Tools(tmp_path)
    p = tmp_path / "x.py"
    p.write_text("a = 1\nb = 2\n")
    tools.insert("x.py", 1, "x = 99")  # no trailing \n
    assert p.read_text() == "a = 1\nx = 99\nb = 2\n"


def test_insert_out_of_bounds_raises(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    p = tmp_path / "x.py"
    p.write_text("a = 1\nb = 2\n")
    with pytest.raises(ToolError, match="out of bounds"):
        tools.insert("x.py", 99, "c = 3")
    with pytest.raises(ToolError, match="out of bounds"):
        tools.insert("x.py", -1, "c = 3")


def test_insert_via_execute_dispatch(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    p = tmp_path / "x.py"
    p.write_text("first\nlast\n")
    result = tools.execute(
        "insert",
        {"path": "x.py", "line_number": 1, "content": "middle"},
    )
    assert "applied" in result
    assert p.read_text() == "first\nmiddle\nlast\n"


def test_str_replace_event_carries_file_size_after_for_savings_analysis(
    tmp_path: Path,
) -> None:
    """The on_tool_call event for str_replace records
    file_size_after_bytes — the cost a hypothetical full write_file
    would have paid. Comparing against input_bytes gives the bytes
    saved by using the diff primitive (T67's headline metric)."""
    from wonderland.tools import ToolCallEvent

    captured: list[ToolCallEvent] = []
    tools = Tools(tmp_path, on_tool_call=captured.append)
    p = tmp_path / "x.py"
    # Big file so the savings show clearly
    p.write_text("\n".join(f"line_{i}" for i in range(200)) + "\n")
    tools.execute(
        "str_replace",
        {"path": "x.py", "old": "line_42", "new": "line_FORTY_TWO"},
        agent_id="tweedledum",
    )
    event = captured[0]
    assert event.tool_name == "str_replace"
    assert event.file_size_after_bytes is not None
    # Sanity: post-patch file is much bigger than the diff input
    assert event.file_size_after_bytes > event.input_bytes * 5, (
        "expected big savings vs full-write — diff payload is small "
        f"({event.input_bytes} bytes) vs the patched file "
        f"({event.file_size_after_bytes} bytes)"
    )


def test_insert_event_carries_file_size_after(tmp_path: Path) -> None:
    """Same observability for insert as for str_replace."""
    from wonderland.tools import ToolCallEvent

    captured: list[ToolCallEvent] = []
    tools = Tools(tmp_path, on_tool_call=captured.append)
    p = tmp_path / "x.py"
    p.write_text("a = 1\n")
    tools.execute(
        "insert",
        {"path": "x.py", "line_number": 1, "content": "b = 2"},
    )
    event = captured[0]
    assert event.tool_name == "insert"
    assert event.file_size_after_bytes == len(p.read_text().encode("utf-8"))


def test_write_file_event_has_no_file_size_after(tmp_path: Path) -> None:
    """write_file's input_bytes already captures the full file size,
    so file_size_after_bytes stays None — only diff ops (str_replace,
    insert) populate it."""
    from wonderland.tools import ToolCallEvent

    captured: list[ToolCallEvent] = []
    tools = Tools(tmp_path, on_tool_call=captured.append)
    tools.execute(
        "write_file",
        {"path": "x.py", "content": "hello\n"},
    )
    event = captured[0]
    assert event.tool_name == "write_file"
    assert event.file_size_after_bytes is None


def test_diff_tools_appear_in_tool_definitions() -> None:
    """The Anthropic tool-use schema must include str_replace + insert
    so the LLM can call them."""
    defs = Tools.tool_definitions()
    names = {d["name"] for d in defs}
    assert "str_replace" in names
    assert "insert" in names


def test_read_file_description_advertises_milestone_roster() -> None:
    """T-ab78 follow-up — read_file's description must point agents at
    the milestone roster for scope-ownership lookups. We locked down
    cross-milestone story/feature/ticket reads (T-ab35) to keep design
    passes on-task; this re-surfaces the boundary data (goal +
    done-when) as supplementary context so agents self-resolve
    'who owns surface X?' instead of escalating to the operator."""
    read_file_def = next(
        d for d in Tools.tool_definitions() if d["name"] == "read_file"
    )
    desc = read_file_def["description"].lower()
    assert ".wonderland/milestones/" in desc
    assert "done-when" in desc or "done when" in desc


# ---------- verify_imports (P16 T-v5) ----------


def test_verify_imports_in_tool_definitions() -> None:
    """Caterpillar can't call the tool unless it's registered in the
    Anthropic schema."""
    defs = Tools.tool_definitions()
    names = {d["name"] for d in defs}
    assert "verify_imports" in names


def test_verify_imports_passes_on_clean_file(tmp_path: Path) -> None:
    """A syntactically clean, fully-imported file should produce
    an OK return value with no diagnostics."""
    tools = Tools(tmp_path)
    tools.write_file(
        "clean.py",
        "import os\n\ndef greet():\n    return os.environ.get('USER', 'anon')\n",
    )
    out = tools.verify_imports("clean.py")
    assert out.startswith("OK:")


def test_verify_imports_catches_undefined_name(tmp_path: Path) -> None:
    """The canonical class of bug — referencing a name that isn't
    defined or imported. Ruff's F821 (undefined-name) catches this."""
    tools = Tools(tmp_path)
    tools.write_file(
        "bug.py",
        "def use_it():\n    return some_undefined_function(42)\n",
    )
    out = tools.verify_imports("bug.py")
    # Output should NOT start with OK + should name the undefined symbol.
    assert not out.startswith("OK:")
    assert "some_undefined_function" in out or "F821" in out


def test_verify_imports_catches_syntax_error(tmp_path: Path) -> None:
    """E9 family catches syntax / indentation errors that wouldn't
    even import."""
    tools = Tools(tmp_path)
    tools.write_file(
        "broken.py",
        "def foo(:\n    return 1\n",  # invalid syntax
    )
    out = tools.verify_imports("broken.py")
    assert not out.startswith("OK:")


def test_verify_imports_skips_frontend_files(tmp_path: Path) -> None:
    """Frontend files (.ts/.tsx/.js/.jsx) need full-project tsc
    context that a single-file static check can't provide. Return
    a skipped marker pointing at npm_build instead of erroring."""
    tools = Tools(tmp_path)
    tools.write_file(
        "App.tsx",
        "export default function App() { return null; }\n",
    )
    out = tools.verify_imports("App.tsx")
    assert "skipped" in out.lower()
    assert "npm_build" in out


def test_verify_imports_rejects_unknown_extensions(tmp_path: Path) -> None:
    """Markdown / config files are out of scope — the operator should
    get a clear ToolError rather than a meaningless ruff invocation."""
    tools = Tools(tmp_path)
    tools.write_file("notes.md", "# header\n")
    with pytest.raises(ToolError, match="only supports .py"):
        tools.verify_imports("notes.md")


def test_verify_imports_rejects_missing_file(tmp_path: Path) -> None:
    tools = Tools(tmp_path)
    with pytest.raises(ToolError, match="not found"):
        tools.verify_imports("does/not/exist.py")


def test_verify_imports_dispatch_via_execute(tmp_path: Path) -> None:
    """The execute() path needs the tool wired into the dispatch
    table; without that, the LLM's tool_use blocks become no-ops."""
    tools = Tools(tmp_path)
    tools.write_file("hi.py", "x = 1\n")
    out = tools.execute("verify_imports", {"path": "hi.py"})
    assert out.startswith("OK:")


# ====================================================================
# exec_smoke_probe — Caterpillar's M8 runtime probe for bugs that
# static review (and even verify_imports) reliably misses: SQL CHECK
# constraints SQLite rejects at INSERT, schema drift, framework
# wiring that 404s, async deadlocks. Tests below verify the
# happy-path output shape, the canonical failure-mode capture, and
# the safety rails (snippet size cap, timeout, dispatch).
# ====================================================================


def test_exec_smoke_probe_in_tool_definitions() -> None:
    """Caterpillar can't call the probe unless it's registered in
    the Anthropic schema."""
    defs = Tools.tool_definitions()
    names = {d["name"] for d in defs}
    assert "exec_smoke_probe" in names


def test_exec_smoke_probe_runs_clean_snippet(tmp_path: Path) -> None:
    """Happy path: a clean snippet runs to completion, exit_code=0,
    stdout captures print() output, stderr is empty."""
    tools = Tools(tmp_path)
    out = tools.exec_smoke_probe("print('hello'); print('world')")
    assert "exit_code=0" in out
    assert "hello" in out
    assert "world" in out
    assert "stderr: (empty)" in out


def test_exec_smoke_probe_captures_traceback_in_stderr(
    tmp_path: Path,
) -> None:
    """The canonical signal for a bug: snippet raises, exit_code is
    non-zero, traceback lands in stderr. This is the M2 SQLite CHECK
    constraint shape — INSERT fails, sqlite3.OperationalError gets
    raised, Cat sees the traceback and files the finding."""
    tools = Tools(tmp_path)
    out = tools.exec_smoke_probe("raise RuntimeError('boom')")
    assert "exit_code=1" in out
    assert "RuntimeError" in out
    assert "boom" in out


def test_exec_smoke_probe_runs_in_project_root(tmp_path: Path) -> None:
    """Snippets need to resolve package imports against the project
    root — without that, probing a freshly-added module is
    impossible."""
    tools = Tools(tmp_path)
    tools.write_file("probe_target.py", "def value():\n    return 42\n")
    out = tools.exec_smoke_probe(
        "import probe_target; print(probe_target.value())"
    )
    assert "exit_code=0" in out
    assert "42" in out


def test_exec_smoke_probe_rejects_empty_snippet(tmp_path: Path) -> None:
    """A blank probe is operator error — surface it as ToolError
    rather than burning a subprocess."""
    tools = Tools(tmp_path)
    with pytest.raises(ToolError, match="non-empty"):
        tools.exec_smoke_probe("")
    with pytest.raises(ToolError, match="non-empty"):
        tools.exec_smoke_probe("   \n   ")


def test_exec_smoke_probe_rejects_oversized_snippet(
    tmp_path: Path,
) -> None:
    """16 KiB is generous for a smoke probe. Anything larger is
    a test, not a probe — guide Cat to file it as a tests/ ticket
    via the error message."""
    tools = Tools(tmp_path)
    huge = "x = 1\n" * 5000  # ~30 KiB
    with pytest.raises(ToolError, match="exceeds"):
        tools.exec_smoke_probe(huge)


def test_exec_smoke_probe_enforces_timeout(tmp_path: Path) -> None:
    """A stuck probe must not block the review meeting's wall
    clock. The hard timeout surfaces as ToolError so Cat can decide
    whether to narrow the probe."""
    tools = Tools(tmp_path)
    with pytest.raises(ToolError, match="timed out"):
        tools.exec_smoke_probe(
            "import time; time.sleep(10)", timeout_seconds=0.5
        )


def test_exec_smoke_probe_truncates_oversized_output(
    tmp_path: Path,
) -> None:
    """Probes that print() large blobs would dominate the LLM
    context. The 4 KiB cap matches run_tests' approach."""
    tools = Tools(tmp_path)
    out = tools.exec_smoke_probe(
        "print('x' * 10000)"
    )
    assert "[truncated]" in out
    # Cap is 4 KiB; output stays bounded.
    assert len(out.encode("utf-8")) < 5 * 1024


def test_exec_smoke_probe_dispatch_via_execute(tmp_path: Path) -> None:
    """The execute() path needs the tool wired into the dispatch
    table; without that, the LLM's tool_use blocks become no-ops."""
    tools = Tools(tmp_path)
    out = tools.execute("exec_smoke_probe", {"snippet": "print('ok')"})
    assert "exit_code=0" in out
    assert "ok" in out


def test_exec_smoke_probe_dispatch_honors_timeout_override(
    tmp_path: Path,
) -> None:
    """Caterpillar can tighten the timeout via the dispatch path
    for probes that should complete instantly."""
    tools = Tools(tmp_path)
    with pytest.raises(ToolError, match="timed out"):
        tools.execute(
            "exec_smoke_probe",
            {"snippet": "import time; time.sleep(2)", "timeout_seconds": 0.3},
        )


# ---------- T-ab35 tool-level milestone scoping ----------


def test_t_ab35_no_scope_set_allows_cross_milestone_reads(
    tmp_path: Path,
) -> None:
    """Without an active milestone scope, read_file works as before
    on cross-milestone artifacts. The guard only fires when scope
    is explicitly set + meeting is scoping/composition."""
    # Write a story tagged to a different milestone
    story_dir = tmp_path / ".wonderland" / "stories"
    story_dir.mkdir(parents=True)
    story_path = story_dir / "story-X-other.md"
    story_path.write_text(
        "## Story 001: Other\n\n**Milestone:** m99-other-milestone\n\nBody.\n"
    )
    tools = Tools(tmp_path)
    # No scope, no meeting id → should read freely
    content = tools.read_file(".wonderland/stories/story-X-other.md")
    assert "Other" in content


def test_t_ab35_blocks_cross_milestone_story_in_scoping_phase(
    tmp_path: Path,
) -> None:
    """T-ab35: when active milestone is m4 and meeting is ``scoping``,
    reading an m3-tagged story raises ToolError citing the scope drift."""
    import wonderland.workflow as wf
    from wonderland.telemetry import (
        set_current_meeting_id,
        reset_current_meeting_id,
    )

    # Write a story tagged to m3 (sibling of active m4 scope)
    story_dir = tmp_path / ".wonderland" / "stories"
    story_dir.mkdir(parents=True)
    (story_dir / "story-X-m3-sibling.md").write_text(
        "## Story 001: M3 sibling\n\n"
        "**Milestone:** m3-other-milestone\n\nBody.\n"
    )

    scope = wf._MilestoneScope(
        slug="m4-active",
        name="M4",
        goal="g",
        done_when=("d",),
        consumes=frozenset(),
    )
    wf.set_active_milestone_scope(scope)
    meeting_token = set_current_meeting_id("scoping")
    try:
        tools = Tools(tmp_path)
        with pytest.raises(ToolError, match="cross-milestone"):
            tools.read_file(".wonderland/stories/story-X-m3-sibling.md")
    finally:
        wf.set_active_milestone_scope(None)
        reset_current_meeting_id(meeting_token)


def test_t_ab35_allows_active_milestone_story(tmp_path: Path) -> None:
    """A story tagged to the active milestone reads fine even during
    scoping. The guard is cross-milestone-specific."""
    import wonderland.workflow as wf
    from wonderland.telemetry import (
        set_current_meeting_id,
        reset_current_meeting_id,
    )

    story_dir = tmp_path / ".wonderland" / "stories"
    story_dir.mkdir(parents=True)
    (story_dir / "story-X-active.md").write_text(
        "## Story 001: Active scope\n\n**Milestone:** m4-active\n\nBody.\n"
    )

    scope = wf._MilestoneScope(
        slug="m4-active",
        name="M4",
        goal="g",
        done_when=("d",),
        consumes=frozenset(),
    )
    wf.set_active_milestone_scope(scope)
    meeting_token = set_current_meeting_id("scoping")
    try:
        tools = Tools(tmp_path)
        content = tools.read_file(".wonderland/stories/story-X-active.md")
        assert "Active scope" in content
    finally:
        wf.set_active_milestone_scope(None)
        reset_current_meeting_id(meeting_token)


def test_t_ab35_allows_cross_milestone_in_decomposition_phase(
    tmp_path: Path,
) -> None:
    """T-ab35 only guards scoping + composition. Later phases
    (decomposition, consolidation, architecture, contract-negotiation)
    iterate per-feature and self-scope via existing iteration
    filters — the guard doesn't apply there."""
    import wonderland.workflow as wf
    from wonderland.telemetry import (
        set_current_meeting_id,
        reset_current_meeting_id,
    )

    story_dir = tmp_path / ".wonderland" / "stories"
    story_dir.mkdir(parents=True)
    (story_dir / "story-X-m3-sibling.md").write_text(
        "## Story 001: M3 sibling\n\n"
        "**Milestone:** m3-other-milestone\n\nBody.\n"
    )

    scope = wf._MilestoneScope(
        slug="m4-active",
        name="M4",
        goal="g",
        done_when=("d",),
        consumes=frozenset(),
    )
    wf.set_active_milestone_scope(scope)
    meeting_token = set_current_meeting_id("decomposition")
    try:
        tools = Tools(tmp_path)
        # Cross-milestone read should succeed in decomposition phase
        content = tools.read_file(".wonderland/stories/story-X-m3-sibling.md")
        assert "M3 sibling" in content
    finally:
        wf.set_active_milestone_scope(None)
        reset_current_meeting_id(meeting_token)


def test_t_ab35_allows_cross_milestone_adr_read(tmp_path: Path) -> None:
    """ADRs (architecture/) remain readable cross-scope — legitimate
    foundation-context lookups. Only stories/features/tickets are
    guarded."""
    import wonderland.workflow as wf
    from wonderland.telemetry import (
        set_current_meeting_id,
        reset_current_meeting_id,
    )

    arch_dir = tmp_path / ".wonderland" / "architecture"
    arch_dir.mkdir(parents=True)
    (arch_dir / "adr-001-anything.md").write_text(
        "# ADR-001\n\nSome architectural decision.\n"
    )

    scope = wf._MilestoneScope(
        slug="m4-active",
        name="M4",
        goal="g",
        done_when=("d",),
        consumes=frozenset(),
    )
    wf.set_active_milestone_scope(scope)
    meeting_token = set_current_meeting_id("scoping")
    try:
        tools = Tools(tmp_path)
        # ADR read should always succeed regardless of milestone scope
        content = tools.read_file(".wonderland/architecture/adr-001-anything.md")
        assert "ADR-001" in content
    finally:
        wf.set_active_milestone_scope(None)
        reset_current_meeting_id(meeting_token)


def test_t_ab35_allows_unattributable_story(tmp_path: Path) -> None:
    """Stories without a Milestone: field stay readable (defensive
    back-compat, matches seeds_fallback's T-ab9 behavior)."""
    import wonderland.workflow as wf
    from wonderland.telemetry import (
        set_current_meeting_id,
        reset_current_meeting_id,
    )

    story_dir = tmp_path / ".wonderland" / "stories"
    story_dir.mkdir(parents=True)
    (story_dir / "story-X-legacy.md").write_text(
        "## Story 001: Legacy story\n\nBody, no milestone tag.\n"
    )

    scope = wf._MilestoneScope(
        slug="m4-active",
        name="M4",
        goal="g",
        done_when=("d",),
        consumes=frozenset(),
    )
    wf.set_active_milestone_scope(scope)
    meeting_token = set_current_meeting_id("scoping")
    try:
        tools = Tools(tmp_path)
        content = tools.read_file(".wonderland/stories/story-X-legacy.md")
        assert "Legacy story" in content
    finally:
        wf.set_active_milestone_scope(None)
        reset_current_meeting_id(meeting_token)


def test_t_ab46_list_files_hides_cross_milestone_stories(
    tmp_path: Path,
) -> None:
    """T-ab46: list_files on .wonderland/stories/ during scoping/
    composition with active scope should filter out sibling-milestone
    files. Filenames carry concept slugs; visibility of those alone
    biases agents toward 'already covered' reasoning."""
    import wonderland.workflow as wf
    from wonderland.telemetry import (
        set_current_meeting_id,
        reset_current_meeting_id,
    )

    story_dir = tmp_path / ".wonderland" / "stories"
    story_dir.mkdir(parents=True)
    (story_dir / "story-1-active.md").write_text(
        "## Story 001\n\n**Milestone:** m4-active\n"
    )
    (story_dir / "story-2-sibling.md").write_text(
        "## Story 002\n\n**Milestone:** m3-sibling\n"
    )
    (story_dir / "story-3-legacy.md").write_text(
        "## Story 003: no tag\n"  # legacy / unattributable
    )

    scope = wf._MilestoneScope(
        slug="m4-active",
        name="M4",
        goal="g",
        done_when=("d",),
        consumes=frozenset(),
    )
    wf.set_active_milestone_scope(scope)
    meeting_token = set_current_meeting_id("scoping")
    try:
        tools = Tools(tmp_path)
        result = tools.list_files(".wonderland/stories")
        # Active milestone's story: visible
        assert "story-1-active.md" in result
        # Sibling milestone's story: hidden
        assert "story-2-sibling.md" not in result
        # Unattributable (legacy): visible by defensive default
        assert "story-3-legacy.md" in result
    finally:
        wf.set_active_milestone_scope(None)
        reset_current_meeting_id(meeting_token)


def test_t_ab46_list_files_unfiltered_outside_scoping_phase(
    tmp_path: Path,
) -> None:
    """T-ab46: when meeting is decomposition / implement / verify
    (not scoping or composition), list_files returns everything.
    The filter is scoped to the load-bearing phases only — the
    per-feature iteration filters (T-ab17/19/20) handle scoping
    downstream."""
    import wonderland.workflow as wf
    from wonderland.telemetry import (
        set_current_meeting_id,
        reset_current_meeting_id,
    )

    story_dir = tmp_path / ".wonderland" / "stories"
    story_dir.mkdir(parents=True)
    (story_dir / "story-1-active.md").write_text(
        "## Story 001\n\n**Milestone:** m4-active\n"
    )
    (story_dir / "story-2-sibling.md").write_text(
        "## Story 002\n\n**Milestone:** m3-sibling\n"
    )

    scope = wf._MilestoneScope(
        slug="m4-active",
        name="M4",
        goal="g",
        done_when=("d",),
        consumes=frozenset(),
    )
    wf.set_active_milestone_scope(scope)
    meeting_token = set_current_meeting_id(
        "decomposition-some-feature"
    )
    try:
        tools = Tools(tmp_path)
        result = tools.list_files(".wonderland/stories")
        # Both visible: not scoping/composition phase, filter no-op
        assert "story-1-active.md" in result
        assert "story-2-sibling.md" in result
    finally:
        wf.set_active_milestone_scope(None)
        reset_current_meeting_id(meeting_token)


def test_t_ab46_list_files_unfiltered_outside_substrate_dirs(
    tmp_path: Path,
) -> None:
    """T-ab46: list_files on a source-tree directory (not under
    .wonderland/stories|features|tickets) returns everything —
    the filter only targets the artifact directories."""
    import wonderland.workflow as wf
    from wonderland.telemetry import (
        set_current_meeting_id,
        reset_current_meeting_id,
    )

    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("# a\n")
    (src / "b.py").write_text("# b\n")

    scope = wf._MilestoneScope(
        slug="m4-active",
        name="M4",
        goal="g",
        done_when=("d",),
        consumes=frozenset(),
    )
    wf.set_active_milestone_scope(scope)
    meeting_token = set_current_meeting_id("scoping")
    try:
        tools = Tools(tmp_path)
        result = tools.list_files("src")
        assert "src/a.py" in result
        assert "src/b.py" in result
    finally:
        wf.set_active_milestone_scope(None)
        reset_current_meeting_id(meeting_token)
