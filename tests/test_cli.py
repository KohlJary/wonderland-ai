"""Tests for the wonderland init CLI."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from wonderland.cli import (
    README_BODY,
    README_FILENAME,
    SKELETON_DIRS,
    WONDERLAND_DIRNAME,
    InitResult,
    build_parser,
    format_init_result,
    init_skeleton,
    main,
)

# ---------- pure layer: init_skeleton ----------


def test_init_creates_full_layout_in_fresh_dir(tmp_path: Path) -> None:
    result = init_skeleton(tmp_path)

    wonderland = tmp_path / WONDERLAND_DIRNAME
    assert wonderland.is_dir()
    for name in SKELETON_DIRS:
        assert (wonderland / name).is_dir(), f"missing {name}/"
    assert (wonderland / README_FILENAME).is_file()
    assert result.did_anything


def test_init_writes_readme_with_documented_layout(tmp_path: Path) -> None:
    init_skeleton(tmp_path)
    text = (tmp_path / WONDERLAND_DIRNAME / README_FILENAME).read_text(encoding="utf-8")
    # Each subdir is mentioned, so the README is a real map of what's there.
    for name in SKELETON_DIRS:
        assert name in text, f"README does not mention {name}"


def test_init_is_idempotent(tmp_path: Path) -> None:
    first = init_skeleton(tmp_path)
    second = init_skeleton(tmp_path)
    assert first.did_anything is True
    # Second pass: nothing new to create, but everything's accounted for.
    assert second.created == ()
    assert WONDERLAND_DIRNAME + "/" in second.already_present


def test_init_fills_in_missing_subdirs_only(tmp_path: Path) -> None:
    wonderland = tmp_path / WONDERLAND_DIRNAME
    wonderland.mkdir()
    (wonderland / "tickets").mkdir()  # one already exists
    (wonderland / "stories" / "story-001-old.md").parent.mkdir()  # another with a file in it

    result = init_skeleton(tmp_path)

    # The two pre-existing dirs are reported as already-present, the rest as created.
    created = set(result.created)
    already = set(result.already_present)
    assert f"{WONDERLAND_DIRNAME}/tickets/" in already
    assert f"{WONDERLAND_DIRNAME}/stories/" in already
    assert f"{WONDERLAND_DIRNAME}/architecture/" in created
    assert f"{WONDERLAND_DIRNAME}/escalations/" in created
    assert f"{WONDERLAND_DIRNAME}/memory/" in created


def test_init_preserves_user_edited_readme(tmp_path: Path) -> None:
    wonderland = tmp_path / WONDERLAND_DIRNAME
    wonderland.mkdir()
    edited = "this is the user's notes; do not overwrite"
    (wonderland / README_FILENAME).write_text(edited, encoding="utf-8")

    init_skeleton(tmp_path)

    assert (wonderland / README_FILENAME).read_text(encoding="utf-8") == edited


def test_init_preserves_existing_artifacts(tmp_path: Path) -> None:
    wonderland = tmp_path / WONDERLAND_DIRNAME
    (wonderland / "stories").mkdir(parents=True)
    keeper = wonderland / "stories" / "story-001-keep-me.md"
    keeper.write_text("payload", encoding="utf-8")

    init_skeleton(tmp_path)

    assert keeper.is_file()
    assert keeper.read_text(encoding="utf-8") == "payload"


def test_init_raises_for_missing_root(tmp_path: Path) -> None:
    target = tmp_path / "nope"
    with pytest.raises(FileNotFoundError):
        init_skeleton(target)


def test_init_raises_when_root_is_a_file(tmp_path: Path) -> None:
    f = tmp_path / "afile"
    f.write_text("x")
    with pytest.raises(NotADirectoryError):
        init_skeleton(f)


def test_init_layout_matches_what_registries_expect(tmp_path: Path) -> None:
    """Smoke test: each registry's expected dir is part of SKELETON_DIRS."""
    from wonderland.adr import ADR_DIRNAME
    from wonderland.escalation import ESCALATIONS_DIRNAME
    from wonderland.implementation import IMPLEMENTATIONS_DIRNAME
    from wonderland.observation import OBSERVATIONS_DIRNAME
    from wonderland.ruling import RULINGS_DIRNAME
    from wonderland.story import STORIES_DIRNAME
    from wonderland.test_scenario import TEST_SCENARIOS_DIRNAME
    from wonderland.ticket import TICKETS_DIRNAME

    init_skeleton(tmp_path)
    wonderland = tmp_path / WONDERLAND_DIRNAME
    for dirname in (
        ADR_DIRNAME,
        TICKETS_DIRNAME,
        STORIES_DIRNAME,
        TEST_SCENARIOS_DIRNAME,
        RULINGS_DIRNAME,
        OBSERVATIONS_DIRNAME,
        IMPLEMENTATIONS_DIRNAME,
        ESCALATIONS_DIRNAME,
    ):
        assert (wonderland / dirname).is_dir(), f"registry expects {dirname}/"
    assert (wonderland / "memory").is_dir(), "AgentMemory expects memory/<agent>/ to live here"


# ---------- format_init_result ----------


def test_format_includes_path_and_created(tmp_path: Path) -> None:
    result = init_skeleton(tmp_path)
    text = format_init_result(result)
    assert str(tmp_path) in text
    assert "Created:" in text
    for entry in result.created:
        assert entry in text


def test_format_skipped_when_idempotent(tmp_path: Path) -> None:
    init_skeleton(tmp_path)
    second = init_skeleton(tmp_path)
    text = format_init_result(second)
    assert "already initialized" in text
    assert "Already present:" in text
    assert "Created:" not in text  # nothing new


def test_init_result_is_immutable(tmp_path: Path) -> None:
    result = init_skeleton(tmp_path)
    with pytest.raises(FrozenInstanceError):
        result.created = ()  # type: ignore[misc]


# ---------- main / argparse glue ----------


def test_main_init_returns_zero_in_fresh_dir(tmp_path: Path) -> None:
    rc = main(["init", str(tmp_path)])
    assert rc == 0
    assert (tmp_path / WONDERLAND_DIRNAME).is_dir()


def test_main_init_no_path_uses_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    rc = main(["init"])
    assert rc == 0
    assert (tmp_path / WONDERLAND_DIRNAME).is_dir()


def test_main_init_errors_on_missing_path(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = main(["init", str(tmp_path / "nope")])
    assert rc == 1
    assert "does not exist" in capsys.readouterr().err


def test_main_init_errors_when_path_is_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    f = tmp_path / "f"
    f.write_text("x")
    rc = main(["init", str(f)])
    assert rc == 1
    assert "is not a directory" in capsys.readouterr().err


def test_main_requires_a_subcommand(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([])
    # argparse exits 2 on missing required arg
    assert exc_info.value.code == 2
    err = capsys.readouterr().err
    assert "required" in err or "command" in err


def test_parser_lists_init_subcommand() -> None:
    parser = build_parser()
    # Smoke: parser parses `init` and the dispatch func is wired.
    namespace = parser.parse_args(["init", "/tmp"])
    assert hasattr(namespace, "func")
    assert namespace.path == "/tmp"


def test_main_init_prints_summary(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    main(["init", str(tmp_path)])
    out = capsys.readouterr().out
    assert "Initialized" in out
    assert WONDERLAND_DIRNAME in out


# ---------- README content sanity ----------


def test_readme_body_is_non_empty_markdown() -> None:
    assert README_BODY.startswith("#")
    assert "memory" in README_BODY
    assert "What to commit" in README_BODY


# ---------- InitResult shape ----------


def test_init_result_contains_resolved_paths(tmp_path: Path) -> None:
    result = init_skeleton(tmp_path)
    assert isinstance(result, InitResult)
    assert result.project_root == tmp_path
    assert result.wonderland_dir == tmp_path / WONDERLAND_DIRNAME


# ---------- `wonderland run` subcommand ----------
#
# These exercise the argparse glue, the escalation-mode dispatch, and a
# smoke test of _run_async end-to-end with a silent LLM that hits the
# timeout path. The Runner itself has its own tests; here we only verify
# the CLI dispatches into it correctly.


def test_parser_run_has_required_directive_arg() -> None:
    parser = build_parser()
    namespace = parser.parse_args(["run", "build a thing"])
    assert namespace.directive == "build a thing"
    assert namespace.budget == 1.00
    assert namespace.timeout == 600.0
    assert namespace.on_escalation == "prompt"
    assert namespace.auto_respond is None
    assert hasattr(namespace, "func")


def test_parser_run_accepts_overrides() -> None:
    parser = build_parser()
    namespace = parser.parse_args(
        [
            "run",
            "directive",
            "--budget",
            "5.0",
            "--timeout",
            "30",
            "--quiescence-seconds",
            "10",
            "--on-escalation",
            "auto",
            "--auto-respond",
            "go with B",
        ]
    )
    assert namespace.budget == 5.0
    assert namespace.timeout == 30.0
    assert namespace.quiescence_seconds == 10.0
    assert namespace.on_escalation == "auto"
    assert namespace.auto_respond == "go with B"


def test_parser_run_rejects_invalid_on_escalation() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["run", "x", "--on-escalation", "wrong"])


# --- _handle_escalation dispatch -------------------------------------- #


async def test_handle_escalation_abort_mode_aborts_runner() -> None:
    """--on-escalation=abort must call runner.abort and not block."""
    import argparse
    from unittest.mock import AsyncMock, MagicMock

    from wonderland.cli import _handle_escalation
    from wonderland.runner import RunnerEvent

    runner = MagicMock()
    runner.abort = MagicMock()
    runner.respond_to_escalation = AsyncMock()
    runner.total_cost = 0.42

    brief = MagicMock()
    brief.thread_id = "main"
    brief.decision_required = "?"
    brief.agent_proposals = []
    brief.suggested_resolution = ""
    brief.stakes = ""

    event = RunnerEvent(
        kind="escalation_prompt",
        elapsed=1.0,
        payload={
            "prompt_id": "p1",
            "brief": brief,
            "record_path": "/tmp/x",
        },
    )
    args = argparse.Namespace(on_escalation="abort", auto_respond=None)

    await _handle_escalation(event, runner, args)

    runner.abort.assert_called_once()
    runner.respond_to_escalation.assert_not_called()


async def test_handle_escalation_auto_mode_uses_auto_respond() -> None:
    import argparse
    from unittest.mock import AsyncMock, MagicMock

    from wonderland.cli import _handle_escalation
    from wonderland.runner import RunnerEvent

    runner = MagicMock()
    runner.abort = MagicMock()
    runner.respond_to_escalation = AsyncMock()
    runner.total_cost = 0.0

    brief = MagicMock()
    brief.thread_id = "main"
    brief.decision_required = "?"
    brief.agent_proposals = []
    brief.suggested_resolution = ""
    brief.stakes = ""

    event = RunnerEvent(
        kind="escalation_prompt",
        elapsed=1.0,
        payload={
            "prompt_id": "p1",
            "brief": brief,
            "record_path": "/tmp/x",
        },
    )
    args = argparse.Namespace(on_escalation="auto", auto_respond="approved")

    await _handle_escalation(event, runner, args)

    runner.respond_to_escalation.assert_awaited_once_with("p1", "approved")
    runner.abort.assert_not_called()


async def test_handle_escalation_prompt_without_tty_aborts() -> None:
    """When stdin isn't a tty and prompt mode is active, abort rather than hang."""
    import argparse
    import sys
    from unittest.mock import AsyncMock, MagicMock, patch

    from wonderland.cli import _handle_escalation
    from wonderland.runner import RunnerEvent

    runner = MagicMock()
    runner.abort = MagicMock()
    runner.respond_to_escalation = AsyncMock()
    runner.total_cost = 0.0

    brief = MagicMock()
    brief.thread_id = "main"
    brief.decision_required = "?"
    brief.agent_proposals = []
    brief.suggested_resolution = ""
    brief.stakes = ""

    event = RunnerEvent(
        kind="escalation_prompt",
        elapsed=1.0,
        payload={"prompt_id": "p1", "brief": brief, "record_path": "/tmp/x"},
    )
    args = argparse.Namespace(on_escalation="prompt", auto_respond=None)

    # Force stdin.isatty() to return False.
    with patch.object(sys.stdin, "isatty", return_value=False):
        await _handle_escalation(event, runner, args)

    runner.abort.assert_called_once()
    runner.respond_to_escalation.assert_not_called()


# --- _handle_event rendering ----------------------------------------- #


async def test_handle_event_utterance_prints_speaker_and_speech_act(
    capsys: pytest.CaptureFixture[str],
) -> None:
    import argparse
    from unittest.mock import MagicMock

    from wonderland.cli import _handle_event
    from wonderland.runner import RunnerEvent
    from wonderland.utterance import SpeechAct

    utterance = MagicMock()
    utterance.speaker.name = "alice"
    utterance.speech_act = SpeechAct.DIRECTIVE
    utterance.content.body = "build it"
    utterance.content.artifacts = []

    event = RunnerEvent(kind="utterance", elapsed=2.5, payload={"utterance": utterance})
    args = argparse.Namespace(on_escalation="abort", auto_respond=None)

    await _handle_event(event, MagicMock(), args)
    out = capsys.readouterr().out
    assert "alice" in out
    assert "directive" in out
    assert "build it" in out


async def test_handle_event_timeout_prints_to_stderr(
    capsys: pytest.CaptureFixture[str],
) -> None:
    import argparse
    from unittest.mock import MagicMock

    from wonderland.cli import _handle_event
    from wonderland.runner import RunnerEvent

    event = RunnerEvent(
        kind="timeout",
        elapsed=600.0,
        payload={"timeout_seconds": 600.0},
    )
    args = argparse.Namespace(on_escalation="abort", auto_respond=None)

    await _handle_event(event, MagicMock(), args)
    captured = capsys.readouterr()
    assert "timeout" in captured.err.lower() or "exceeded" in captured.err


# --- _run_async smoke test ------------------------------------------- #


async def test_run_async_errors_when_project_root_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import argparse

    from wonderland.cli import _run_async

    args = argparse.Namespace(
        directive="x",
        project_root=tmp_path / "nope",
        budget=1.0,
        quiescence_seconds=30.0,
        timeout=1.0,
        on_escalation="abort",
        auto_respond=None,
    )
    rc = await _run_async(args)
    assert rc == 1
    assert "does not exist" in capsys.readouterr().err


async def test_run_async_smoke_hits_timeout_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """End-to-end: silent LLM, very short timeout → exit code 1, telemetry written."""
    import argparse
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, MagicMock

    from wonderland import LLMClient
    from wonderland.cli import _run_async
    from wonderland.runner import Runner

    def silent_llm() -> LLMClient:
        response = SimpleNamespace(
            content=[SimpleNamespace(type="text", text='```json\n{"decision": "silence"}\n```')],
            stop_reason="end_turn",
            usage=SimpleNamespace(
                input_tokens=10,
                output_tokens=5,
                cache_creation_input_tokens=0,
                cache_read_input_tokens=0,
            ),
        )
        client = MagicMock()
        client.messages = MagicMock()
        client.messages.create = AsyncMock(return_value=response)
        return LLMClient(client=client)

    real_make_full_cast = Runner.make_full_cast

    async def patched_make_full_cast(project_root, **kwargs):  # type: ignore[no-untyped-def]
        kwargs.setdefault("llm_factory", lambda name, tel: silent_llm())
        return await real_make_full_cast(project_root, **kwargs)

    monkeypatch.setattr(Runner, "make_full_cast", patched_make_full_cast)

    args = argparse.Namespace(
        directive="silent test",
        project_root=tmp_path,
        budget=10.0,
        quiescence_seconds=30.0,
        timeout=0.5,
        on_escalation="abort",
        auto_respond=None,
        model=None,
    )
    rc = await _run_async(args)
    assert rc == 1  # timeout
    # Telemetry record written
    records = list((tmp_path / ".wonderland" / "telemetry").glob("run-*.json"))
    assert len(records) == 1


# ---------- `wonderland project` CLI (P11 T75) ----------


def test_project_add_creates_registry_entry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`wonderland project add NAME PATH` registers a project."""
    from wonderland.cli import main
    from wonderland.project import list_projects

    monkeypatch.setenv("WONDERLAND_HOME", str(tmp_path / ".wonderland"))
    rc = main([
        "project", "add", "alpha", str(tmp_path / "alpha-root"),
        "--workflow", "smoke",
        "--budget", "3.50",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Registered" in out
    assert "alpha" in out

    projects = list_projects()
    assert len(projects) == 1
    assert projects[0].name == "alpha"
    assert projects[0].last_workflow == "smoke"
    assert projects[0].default_budget == 3.50


def test_project_add_rejects_duplicate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from wonderland.cli import main

    monkeypatch.setenv("WONDERLAND_HOME", str(tmp_path / ".wonderland"))
    rc1 = main(["project", "add", "alpha", str(tmp_path)])
    assert rc1 == 0
    rc2 = main(["project", "add", "alpha", str(tmp_path)])
    assert rc2 == 1
    err = capsys.readouterr().err
    assert "already registered" in err


def test_project_list_empty_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from wonderland.cli import main

    monkeypatch.setenv("WONDERLAND_HOME", str(tmp_path / ".wonderland"))
    rc = main(["project", "list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "(no projects registered)" in out
    assert "wonderland project add" in out


def test_project_list_shows_registered(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from wonderland.cli import main

    monkeypatch.setenv("WONDERLAND_HOME", str(tmp_path / ".wonderland"))
    main(["project", "add", "alpha", str(tmp_path / "a"), "--budget", "1.00"])
    main(["project", "add", "bravo", str(tmp_path / "b"), "--budget", "2.50"])
    capsys.readouterr()  # discard prior output

    rc = main(["project", "list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "bravo" in out
    assert "$1.00" in out
    assert "$2.50" in out


def test_project_edit_updates_workflow(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from wonderland.cli import main
    from wonderland.project import load_project

    monkeypatch.setenv("WONDERLAND_HOME", str(tmp_path / ".wonderland"))
    main(["project", "add", "alpha", str(tmp_path / "a")])
    capsys.readouterr()

    rc = main(["project", "edit", "alpha", "--workflow", "tdd-serial-phased"])
    assert rc == 0
    p = load_project("alpha")
    assert p.last_workflow == "tdd-serial-phased"


def test_project_archive_and_unarchive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from wonderland.cli import main
    from wonderland.project import load_project

    monkeypatch.setenv("WONDERLAND_HOME", str(tmp_path / ".wonderland"))
    main(["project", "add", "alpha", str(tmp_path / "a")])
    capsys.readouterr()

    main(["project", "archive", "alpha"])
    assert load_project("alpha").archived is True

    main(["project", "unarchive", "alpha"])
    assert load_project("alpha").archived is False
