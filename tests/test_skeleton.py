"""Tests for the skeleton loader / applier (T70 / P8.6).

Covers the bundled-skeleton loader API + the apply path that
NewRunScreen's picker (T71) will consume.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from wonderland.skeleton import (
    Skeleton,
    apply_skeleton,
    is_bare_project_root,
    list_skeletons,
    load_skeleton,
    skeletons_dir,
)


# --- Bundled-skeleton inventory ---


def test_skeletons_dir_resolves() -> None:
    """The runtime resolver should land on a directory that has at
    least one bundled skeleton subdirectory."""
    d = skeletons_dir()
    assert d.is_dir(), f"skeletons dir missing: {d}"


def test_list_skeletons_returns_entries() -> None:
    skeletons = list_skeletons()
    assert len(skeletons) > 0
    for s in skeletons:
        assert isinstance(s, Skeleton)
        assert s.name
        assert s.description
        assert s.root.is_dir()
        assert len(s.files) > 0


def test_list_includes_known_skeletons() -> None:
    """The five bundled skeletons should all surface."""
    names = {s.name for s in list_skeletons()}
    expected = {
        "fullstack-fastapi-react",
        "python-cli",
        "python-fastapi",
        "python-tui",
        "react-vite",
    }
    missing = expected - names
    assert not missing, f"missing bundled skeletons: {missing}"


def test_load_skeleton_returns_named_entry() -> None:
    s = load_skeleton("python-cli")
    assert s.name == "python-cli"
    assert any("src/cli.py" in f for f in s.files)


def test_load_missing_skeleton_raises_with_available_list() -> None:
    with pytest.raises(FileNotFoundError) as excinfo:
        load_skeleton("nonexistent-skeleton")
    msg = str(excinfo.value)
    assert "Bundled skeletons:" in msg


def test_skeletons_have_descriptions() -> None:
    """Every bundled skeleton has a description picked up from its
    README — the picker (T71) needs human-readable labels."""
    for s in list_skeletons():
        # Description should be substantive (> 20 chars), not just
        # the directory name.
        assert len(s.description) > 20, (
            f"{s.name}: description too short ({s.description!r})"
        )


def test_skeleton_top_level_dirs_are_useful() -> None:
    """Every bundled skeleton ships at least one top-level
    directory (src/, tests/, frontend/, etc.) so the picker
    preview can show structure."""
    for s in list_skeletons():
        assert len(s.top_level_dirs()) > 0, (
            f"{s.name}: no top-level dirs (only files at root?)"
        )


# --- Apply path ---


def test_apply_skeleton_to_empty_dir(tmp_path: Path) -> None:
    s = load_skeleton("python-cli")
    written = apply_skeleton(s, tmp_path)
    assert len(written) > 0
    # Spot-check expected files
    assert (tmp_path / "pyproject.toml").is_file()
    assert (tmp_path / "src/cli.py").is_file()
    assert (tmp_path / "tests/test_cli.py").is_file()
    assert (tmp_path / ".gitignore").is_file()


def test_apply_skeleton_creates_missing_root(tmp_path: Path) -> None:
    """Applying to a path that doesn't exist yet should create it."""
    target = tmp_path / "fresh-project"
    assert not target.exists()
    s = load_skeleton("python-cli")
    apply_skeleton(s, target)
    assert target.is_dir()
    assert (target / "pyproject.toml").is_file()


def test_apply_skeleton_refuses_to_overwrite(tmp_path: Path) -> None:
    """Default behavior: if any skeleton file would overwrite an
    existing file, raise FileExistsError."""
    s = load_skeleton("python-cli")
    apply_skeleton(s, tmp_path)
    # Now try again — should fail
    with pytest.raises(FileExistsError, match="overwrite"):
        apply_skeleton(s, tmp_path)


def test_apply_skeleton_overwrite_force(tmp_path: Path) -> None:
    """overwrite=True bypasses the collision check."""
    s = load_skeleton("python-cli")
    apply_skeleton(s, tmp_path)
    # Modify one file
    (tmp_path / "src/cli.py").write_text("# modified")
    # Re-apply with overwrite — should succeed and restore
    apply_skeleton(s, tmp_path, overwrite=True)
    content = (tmp_path / "src/cli.py").read_text()
    assert content != "# modified"


# --- Bare-root detection ---


def test_is_bare_project_root_for_truly_empty(tmp_path: Path) -> None:
    assert is_bare_project_root(tmp_path)


def test_is_bare_project_root_with_only_git_files(tmp_path: Path) -> None:
    """A `git init`'d directory with .git/ + .gitignore + README is
    still considered bare — no production content yet."""
    (tmp_path / ".git").mkdir()
    (tmp_path / ".gitignore").write_text("__pycache__\n")
    (tmp_path / "README.md").write_text("# project")
    assert is_bare_project_root(tmp_path)


def test_is_bare_project_root_rejects_with_src(tmp_path: Path) -> None:
    """A project root with src/ is no longer bare; applying a
    skeleton would risk clobbering."""
    (tmp_path / "src").mkdir()
    assert not is_bare_project_root(tmp_path)


def test_is_bare_project_root_rejects_with_tests(tmp_path: Path) -> None:
    (tmp_path / "tests").mkdir()
    assert not is_bare_project_root(tmp_path)


def test_is_bare_project_root_rejects_arbitrary_content(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("print('hi')")
    assert not is_bare_project_root(tmp_path)


def test_is_bare_project_root_for_missing_dir(tmp_path: Path) -> None:
    """A path that doesn't exist yet is bare (will be created on
    apply)."""
    assert is_bare_project_root(tmp_path / "missing")
