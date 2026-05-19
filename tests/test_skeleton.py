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


# --- Manifest layer (T73) ---


def test_bundled_skeletons_have_manifests() -> None:
    """All five bundled skeletons ship a manifest.yaml. Backward
    compat: skeletons without a manifest get an empty default;
    we test that explicit manifests are loaded correctly."""
    for s in list_skeletons():
        # Every bundled skeleton declares at least a language.
        assert s.manifest.language is not None, (
            f"{s.name}: missing manifest.yaml or language tag"
        )


def test_python_cli_manifest_post_apply() -> None:
    s = load_skeleton("python-cli")
    assert s.manifest.language == "python"
    assert len(s.manifest.post_apply) == 1
    step = s.manifest.post_apply[0]
    assert "pip install" in step.command
    assert step.cwd == "."
    assert step.description


def test_fullstack_skeleton_has_multi_language_post_apply() -> None:
    """The fullstack skeleton spans Python backend + JS frontend;
    its post_apply lists both pip and npm steps with different
    cwd values."""
    s = load_skeleton("fullstack-fastapi-react")
    assert s.manifest.language == "python+javascript"
    cmds = [step.command for step in s.manifest.post_apply]
    assert any("pip install" in c for c in cmds)
    assert any("npm install" in c for c in cmds)
    cwds = {step.cwd for step in s.manifest.post_apply}
    assert "frontend" in cwds  # frontend deps install in frontend/


def test_skeleton_without_manifest_defaults_to_empty(tmp_path: Path) -> None:
    """A skeleton directory without manifest.yaml loads with the
    default empty manifest — backward compat for any future
    skeleton that doesn't need post-apply steps."""
    from wonderland.skeleton import (
        SkeletonManifest,
        _load_manifest,
    )

    # Directory exists but no manifest.yaml inside
    manifest = _load_manifest(tmp_path)
    assert isinstance(manifest, SkeletonManifest)
    assert manifest.language is None
    assert manifest.post_apply == []


def test_manifest_yaml_is_not_in_skeleton_files() -> None:
    """The manifest itself is metadata for the loader, not part
    of the user's project. apply_skeleton must NOT copy
    manifest.yaml into the operator's project root."""
    for s in list_skeletons():
        assert "manifest.yaml" not in s.files, (
            f"{s.name}: manifest.yaml leaked into files list"
        )


def test_apply_skeleton_does_not_copy_manifest(tmp_path: Path) -> None:
    """End-to-end check: the applied project root has no
    manifest.yaml even though the skeleton's source directory
    has one."""
    s = load_skeleton("python-cli")
    apply_skeleton(s, tmp_path)
    assert not (tmp_path / "manifest.yaml").exists()


# --- prime_directive carryover (closes the obol M3 vibe-loss gap) ---


def test_apply_skeleton_persists_prime_directive_to_project_context(
    tmp_path: Path,
) -> None:
    """When the operator passes a prime_directive at project-create
    time, it lands in ``.wonderland/project.yaml`` so every
    downstream meeting's ``project_context`` seed carries the
    operator's intent — not just discovery. Closes the gap where
    minimal-directive projects (obol's "htop for money") lost vibe
    at M4 / M5 / M8 because those meetings don't see the discovery
    directive directly."""
    from wonderland.project_context import load_project_context

    s = load_skeleton("python-cli")
    apply_skeleton(
        s, tmp_path,
        prime_directive="Build me a TUI dashboard for personal finances.",
    )

    ctx = load_project_context(tmp_path)
    assert ctx is not None
    # YAML round-trip preserves a trailing newline on block-scalar
    # outputs; the meaningful content is what matters.
    assert ctx.prime_directive is not None
    assert ctx.prime_directive.rstrip() == (
        "Build me a TUI dashboard for personal finances."
    )


def test_apply_skeleton_omits_prime_directive_when_none(
    tmp_path: Path,
) -> None:
    """Back-compat: callers that don't pass prime_directive get the
    legacy behavior — project.yaml has no prime_directive field."""
    from wonderland.project_context import load_project_context

    s = load_skeleton("python-cli")
    apply_skeleton(s, tmp_path)

    ctx = load_project_context(tmp_path)
    assert ctx is not None
    assert ctx.prime_directive is None


def test_apply_skeleton_treats_whitespace_prime_directive_as_none(
    tmp_path: Path,
) -> None:
    """Empty / whitespace prime_directive doesn't pollute the YAML."""
    from wonderland.project_context import load_project_context

    s = load_skeleton("python-cli")
    apply_skeleton(s, tmp_path, prime_directive="   \n  ")

    ctx = load_project_context(tmp_path)
    assert ctx is not None
    assert ctx.prime_directive is None


def test_write_project_context_from_skeleton_accepts_prime_directive(
    tmp_path: Path,
) -> None:
    """Same primitive callable on its own for retrofit (the non-bare
    root path the new-project TUI flow uses when the operator
    adopts an existing tree)."""
    from wonderland.project_context import load_project_context
    from wonderland.skeleton import write_project_context_from_skeleton

    s = load_skeleton("python-cli")
    written = write_project_context_from_skeleton(
        s, tmp_path,
        prime_directive="Track personal finances htop-style.",
    )
    assert written is not None

    ctx = load_project_context(tmp_path)
    assert ctx is not None
    assert ctx.prime_directive is not None
    assert ctx.prime_directive.rstrip() == (
        "Track personal finances htop-style."
    )
