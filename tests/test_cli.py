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
