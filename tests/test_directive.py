"""Tests for ``wonderland.directive`` — schema, loader, save round-trip
for the bundled + per-project directive presets (T50)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from wonderland.directive import (
    DirectivePreset,
    directives_dir,
    list_directives,
    list_project_directives,
    load_directive,
    load_project_directive,
    project_directives_dir,
    save_directive,
)


# ---------------------------------------------------------------------
# Schema basics
# ---------------------------------------------------------------------


class TestSchema:
    def test_minimal_preset(self):
        p = DirectivePreset(name="x", title="X", body="do X")
        assert p.name == "x"
        assert p.title == "X"
        assert p.body == "do X"
        assert p.description == ""
        assert p.suggested_workflow is None
        assert p.suggested_skeleton is None
        assert p.tags == []

    def test_full_preset(self):
        p = DirectivePreset(
            name="pomodoro",
            title="Pomodoro timer",
            description="A focus session app",
            body="Build a Pomodoro timer.",
            suggested_workflow="tdd-serial",
            suggested_skeleton="fullstack-fastapi-react",
            tags=["greenfield", "feature-rich"],
        )
        assert p.suggested_workflow == "tdd-serial"
        assert "greenfield" in p.tags

    def test_name_is_required(self):
        with pytest.raises(ValidationError):
            DirectivePreset(title="X", body="do X")  # type: ignore[call-arg]

    def test_body_is_required(self):
        with pytest.raises(ValidationError):
            DirectivePreset(name="x", title="X")  # type: ignore[call-arg]


# ---------------------------------------------------------------------
# Bundled preset discovery + loading
# ---------------------------------------------------------------------


class TestBundledPresets:
    def test_directives_dir_resolves(self):
        d = directives_dir()
        assert d.is_dir(), f"bundled directives dir missing: {d}"

    def test_list_includes_canonical_presets(self):
        names = list_directives()
        # The canonical bundled set should at least include these.
        for required in ("pomodoro", "hello-endpoint", "ping"):
            assert required in names, f"missing bundled preset: {required}"

    def test_load_pomodoro_matches_analyses_directive(self):
        p = load_directive("pomodoro")
        assert p.name == "pomodoro"
        # The body text is the canonical directive analyses 029-032
        # used for the substrate-convergence work.
        assert "Pomodoro" in p.body
        assert "focus sessions" in p.body
        assert p.suggested_workflow == "tdd-serial"

    def test_load_by_name_strips_yaml_suffix(self):
        # 'pomodoro' should resolve the same as 'pomodoro.yaml'
        # via the path branch of the loader.
        by_name = load_directive("pomodoro")
        by_path = load_directive(directives_dir() / "pomodoro.yaml")
        assert by_name == by_path

    def test_load_missing_raises_with_available_list(self):
        with pytest.raises(FileNotFoundError) as excinfo:
            load_directive("nonexistent-zzz")
        # Available bundled list should appear in the error message
        # for legibility.
        msg = str(excinfo.value)
        assert "Bundled:" in msg
        assert "pomodoro" in msg


# ---------------------------------------------------------------------
# Per-project preset discovery + saving
# ---------------------------------------------------------------------


class TestProjectPresets:
    def test_list_handles_missing_dir(self, tmp_path: Path):
        # Fresh project root, no .wonderland/directives — should
        # return [] without raising.
        assert list_project_directives(tmp_path) == []

    def test_save_creates_directory(self, tmp_path: Path):
        # The .wonderland/directives/ subdir doesn't exist yet; save
        # creates it.
        assert not project_directives_dir(tmp_path).exists()
        preset = DirectivePreset(
            name="custom-thing",
            title="Custom thing",
            body="Build a custom thing.",
        )
        path = save_directive(preset, tmp_path)
        assert path.is_file()
        assert project_directives_dir(tmp_path).is_dir()

    def test_save_round_trips(self, tmp_path: Path):
        original = DirectivePreset(
            name="round-trip-test",
            title="Round-trip test",
            description="Verify save/load preserves all fields.",
            body="Build a round-trip test\nwith multiple lines.\n",
            suggested_workflow="tdd-serial",
            suggested_skeleton="fullstack-fastapi-react",
            tags=["test"],
        )
        save_directive(original, tmp_path)
        loaded = load_project_directive("round-trip-test", tmp_path)
        assert loaded.name == original.name
        assert loaded.title == original.title
        assert loaded.description == original.description
        assert loaded.body.rstrip() == original.body.rstrip()
        assert loaded.suggested_workflow == original.suggested_workflow
        assert loaded.suggested_skeleton == original.suggested_skeleton
        assert loaded.tags == original.tags

    def test_list_picks_up_saved_presets(self, tmp_path: Path):
        save_directive(
            DirectivePreset(name="alpha", title="A", body="x"), tmp_path
        )
        save_directive(
            DirectivePreset(name="beta", title="B", body="y"), tmp_path
        )
        names = list_project_directives(tmp_path)
        assert names == ["alpha", "beta"]

    def test_load_project_missing_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            load_project_directive("nonexistent", tmp_path)

    def test_saved_yaml_is_human_readable(self, tmp_path: Path):
        # The saved YAML should preserve field order and use literal
        # block style for multi-line body — humans should be able to
        # edit these files by hand.
        preset = DirectivePreset(
            name="readable",
            title="Readable",
            body="line one\nline two\n",
        )
        path = save_directive(preset, tmp_path)
        text = path.read_text()
        # name comes before body (preserves field order)
        assert text.index("name:") < text.index("body:")
        # body's trailing newline preserved as a single trailing \n
        with path.open() as f:
            data = yaml.safe_load(f)
        assert data["body"] == "line one\nline two\n"


# ---------------------------------------------------------------------
# Sanity check on bundled YAML files
# ---------------------------------------------------------------------


class TestAllBundledLoad:
    """Every bundled preset should load cleanly through the schema."""

    def test_every_bundled_preset_is_valid(self):
        for name in list_directives():
            p = load_directive(name)
            assert p.name == name
            assert p.title  # non-empty
            assert p.body  # non-empty

    def test_suggested_workflow_when_set_resolves(self):
        # If a preset names a suggested_workflow, that workflow
        # should actually exist in closet/workflows/.
        from wonderland.workflow import list_workflows

        workflows = set(list_workflows())
        for name in list_directives():
            p = load_directive(name)
            if p.suggested_workflow is not None:
                assert p.suggested_workflow in workflows, (
                    f"{name} suggests workflow '{p.suggested_workflow}' "
                    f"which doesn't exist; available: {workflows}"
                )
