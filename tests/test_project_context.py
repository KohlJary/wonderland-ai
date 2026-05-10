"""Tests for project context memory — authoritative project-level
facts loaded into seed contexts via the project_context kind."""

from __future__ import annotations

from pathlib import Path

import pytest

from wonderland.project_context import (
    ProjectContext,
    ProjectStack,
    load_project_context,
    project_context_path,
    render_context_body,
    save_project_context,
)


def test_load_returns_none_when_file_missing(tmp_path: Path) -> None:
    """Greenfield projects without context memory return None —
    callers handle the absence (legacy directive-only grounding)."""
    assert load_project_context(tmp_path) is None


def test_save_load_roundtrip(tmp_path: Path) -> None:
    ctx = ProjectContext(
        name="obol",
        stack=ProjectStack(
            runtime="tui",
            language="python",
            ui_framework="textual",
            test_framework="pytest",
        ),
        entry_point="src/obol/__main__.py",
        conventions="Diff-based writes preferred.",
    )
    path = save_project_context(ctx, tmp_path)
    assert path == project_context_path(tmp_path)
    assert path.is_file()

    loaded = load_project_context(tmp_path)
    assert loaded is not None
    assert loaded.name == "obol"
    assert loaded.stack.runtime == "tui"
    assert loaded.stack.ui_framework == "textual"
    assert loaded.entry_point == "src/obol/__main__.py"
    assert "Diff-based writes" in loaded.conventions


def test_save_drops_empty_conventions(tmp_path: Path) -> None:
    """Common case: skeleton apply doesn't populate conventions
    prose. The serialized YAML should not carry an empty
    ``conventions: ''`` line — keeps the on-disk file clean."""
    ctx = ProjectContext(
        name="empty-conv",
        stack=ProjectStack(runtime="cli"),
    )
    path = save_project_context(ctx, tmp_path)
    text = path.read_text()
    assert "conventions:" not in text


def test_render_context_body_formats_stack_as_bullets() -> None:
    """The body that ends up in agent context is a bulleted fact
    sheet — not the YAML envelope. Agents should see facts, not
    syntax."""
    ctx = ProjectContext(
        name="obol",
        stack=ProjectStack(
            runtime="tui",
            language="python",
            ui_framework="textual",
        ),
        entry_point="src/obol/__main__.py",
    )
    body = render_context_body(ctx)
    # No YAML envelope.
    assert "stack:" not in body
    assert "name:" not in body
    # Markdown-rendered prose.
    assert "**Project:** obol" in body
    assert "Runtime: tui" in body
    assert "Language: python" in body
    assert "UI framework: textual" in body
    assert "Entry point:" in body


def test_render_skips_optional_stack_fields_when_unset() -> None:
    """Minimal stack (just runtime) renders without fake fields."""
    ctx = ProjectContext(name="x", stack=ProjectStack(runtime="cli"))
    body = render_context_body(ctx)
    assert "Runtime: cli" in body
    assert "Language:" not in body
    assert "UI framework:" not in body
    assert "Storage:" not in body


def test_runtime_is_required() -> None:
    """``runtime`` is the load-bearing field. Stack without it
    isn't a valid project context."""
    with pytest.raises(Exception):
        ProjectStack()  # type: ignore[call-arg]


# --- Integration with seeds_fallback ---


def test_seeds_fallback_returns_project_context_seed(tmp_path: Path) -> None:
    """``project_context`` is wired as a kind in seeds_fallback —
    M4 / M5 / M8 can request ``from: any kinds: [project_context]``
    and get the rendered body."""
    from wonderland.seeds_fallback import (
        disk_seeds_for_kinds,
        supported_disk_kinds,
    )

    assert "project_context" in supported_disk_kinds()

    save_project_context(
        ProjectContext(
            name="obol",
            stack=ProjectStack(runtime="tui", language="python"),
        ),
        tmp_path,
    )

    seeds = disk_seeds_for_kinds(
        tmp_path, ["project_context"], thread_id="architecture"
    )
    assert len(seeds) == 1
    body = seeds[0].content.body
    assert "Runtime: tui" in body
    assert "stack:" not in body  # YAML envelope must NOT leak


def test_seeds_fallback_empty_when_no_context(tmp_path: Path) -> None:
    """Project without context memory → empty seed list, not
    error. Lets legacy projects continue working unchanged."""
    from wonderland.seeds_fallback import disk_seeds_for_kinds

    seeds = disk_seeds_for_kinds(
        tmp_path, ["project_context"], thread_id="architecture"
    )
    assert seeds == []


# --- Integration with apply_skeleton ---


def test_apply_skeleton_writes_project_context_from_manifest(
    tmp_path: Path,
) -> None:
    """The python-tui skeleton's manifest carries
    ``stack: {runtime: tui, ...}``; ``apply_skeleton`` writes a
    matching ``.wonderland/project.yaml`` into the new project so
    the team's first run reads the runtime shape from context
    memory, not from the directive's prose alone."""
    from wonderland.skeleton import apply_skeleton, load_skeleton

    skeleton = load_skeleton("python-tui")
    project_root = tmp_path / "demo"
    apply_skeleton(skeleton, project_root)

    ctx = load_project_context(project_root)
    assert ctx is not None
    assert ctx.stack.runtime == "tui"
    assert ctx.stack.language == "python"
    assert ctx.stack.ui_framework == "textual"


def test_apply_skeleton_writes_web_context_for_fullstack(
    tmp_path: Path,
) -> None:
    """fullstack-fastapi-react ships a web stack — runtime: web,
    not 'tui'. The whole point of project context memory is that
    different skeletons surface different runtimes."""
    from wonderland.skeleton import apply_skeleton, load_skeleton

    skeleton = load_skeleton("fullstack-fastapi-react")
    project_root = tmp_path / "demo"
    apply_skeleton(skeleton, project_root)

    ctx = load_project_context(project_root)
    assert ctx is not None
    assert ctx.stack.runtime == "web"


def test_retrofit_writes_project_context_on_non_bare_root(
    tmp_path: Path,
) -> None:
    """``write_project_context_from_skeleton`` is callable on its
    own, separate from ``apply_skeleton``'s file-laying path. This
    is the retrofit door: an existing tree with skeleton files
    already in place can still get its project_context written
    from the manifest without clobbering anything.

    Closes the gap where wiping ``.wonderland/`` but keeping
    ``src/`` / ``pyproject.toml`` / ``tests/`` (typical mid-
    development re-init) left projects without project_context
    because ``is_bare_project_root`` was False and
    ``apply_skeleton`` was skipped entirely."""
    from wonderland.skeleton import (
        load_skeleton,
        write_project_context_from_skeleton,
    )

    project_root = tmp_path / "demo"
    project_root.mkdir()
    # Simulate a non-bare root — already has skeleton files.
    (project_root / "src").mkdir()
    (project_root / "src" / "app.py").write_text("# existing\n")
    (project_root / "pyproject.toml").write_text("[project]\nname='demo'\n")

    skeleton = load_skeleton("python-tui")
    result = write_project_context_from_skeleton(skeleton, project_root)

    assert result is not None
    assert result == project_context_path(project_root)
    ctx = load_project_context(project_root)
    assert ctx is not None
    assert ctx.stack.runtime == "tui"
    # And critically: existing files weren't touched.
    assert (project_root / "src" / "app.py").read_text() == "# existing\n"


def test_retrofit_skips_when_project_yaml_exists(tmp_path: Path) -> None:
    """Operator-edited ``project.yaml`` survives retrofit by
    default — don't clobber operator content. Pass
    ``overwrite=True`` to force."""
    from wonderland.skeleton import (
        load_skeleton,
        write_project_context_from_skeleton,
    )

    project_root = tmp_path / "demo"
    project_root.mkdir()
    # Operator already has a context with non-default stack.
    save_project_context(
        ProjectContext(
            name="demo",
            stack=ProjectStack(runtime="custom-runtime"),
        ),
        project_root,
    )

    skeleton = load_skeleton("python-tui")
    result = write_project_context_from_skeleton(skeleton, project_root)

    # Skipped — operator content preserved.
    assert result is None
    ctx = load_project_context(project_root)
    assert ctx is not None
    assert ctx.stack.runtime == "custom-runtime"  # not "tui"


def test_retrofit_overwrite_replaces_existing(tmp_path: Path) -> None:
    """``overwrite=True`` lets operator opt in to replacing
    existing context (e.g. when re-keying a project's stack
    after a rewrite)."""
    from wonderland.skeleton import (
        load_skeleton,
        write_project_context_from_skeleton,
    )

    project_root = tmp_path / "demo"
    project_root.mkdir()
    save_project_context(
        ProjectContext(
            name="demo",
            stack=ProjectStack(runtime="placeholder"),
        ),
        project_root,
    )

    skeleton = load_skeleton("python-tui")
    write_project_context_from_skeleton(
        skeleton, project_root, overwrite=True
    )

    ctx = load_project_context(project_root)
    assert ctx is not None
    assert ctx.stack.runtime == "tui"


def test_retrofit_skips_when_skeleton_has_no_stack(tmp_path: Path) -> None:
    """Skeleton without stack metadata → retrofit returns None,
    same back-compat as ``apply_skeleton``."""
    from wonderland.skeleton import (
        Skeleton,
        SkeletonManifest,
        write_project_context_from_skeleton,
    )

    sk_root = tmp_path / "skeleton-no-stack"
    sk_root.mkdir()
    skeleton = Skeleton(
        name="no-stack",
        description="d",
        root=sk_root,
        files=(),
        manifest=SkeletonManifest(language="python"),
    )

    project_root = tmp_path / "demo"
    project_root.mkdir()
    result = write_project_context_from_skeleton(skeleton, project_root)
    assert result is None
    assert not project_context_path(project_root).is_file()


def test_apply_skeleton_skips_when_no_stack_in_manifest(
    tmp_path: Path,
) -> None:
    """Skeletons without a ``stack:`` block in their manifest
    don't write project.yaml — back-compat for predates-context-
    memory templates that haven't been updated yet."""
    from wonderland.skeleton import (
        Skeleton,
        SkeletonManifest,
        apply_skeleton,
    )

    # Build a minimal skeleton with one file and no stack metadata.
    sk_root = tmp_path / "no-stack-skeleton"
    sk_root.mkdir()
    (sk_root / "hello.txt").write_text("hi")

    skeleton = Skeleton(
        name="no-stack",
        description="legacy skeleton without stack metadata",
        root=sk_root,
        files=("hello.txt",),
        manifest=SkeletonManifest(language="python"),  # no stack
    )

    project_root = tmp_path / "demo"
    apply_skeleton(skeleton, project_root)

    # No project.yaml written — manifest didn't carry stack.
    assert not project_context_path(project_root).is_file()
    # But the skeleton's actual files DID get copied.
    assert (project_root / "hello.txt").is_file()
