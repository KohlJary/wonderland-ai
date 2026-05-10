"""Tests for the Project model + registry persistence (T74 / P11).

Uses ``WONDERLAND_HOME`` env var to redirect persistence into
``tmp_path`` so each test gets a clean registry without touching the
operator's real ``~/.wonderland/``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from wonderland.project import (
    NotificationPrefs,
    Project,
    archive_project,
    list_projects,
    load_project,
    projects_registry_path,
    register_project,
    save_project,
    unarchive_project,
)


@pytest.fixture(autouse=True)
def _isolated_registry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect the global registry into ``tmp_path/.wonderland/`` for
    every test in this module. Autouse so individual tests don't have
    to remember to declare it."""
    monkeypatch.setenv("WONDERLAND_HOME", str(tmp_path / ".wonderland"))
    return tmp_path


# --- Model construction ---


class TestProjectModel:
    def test_minimal_construction(self, tmp_path: Path) -> None:
        p = Project(name="alpha", root_path=tmp_path)
        assert p.name == "alpha"
        assert p.root_path == tmp_path.resolve()
        assert p.default_budget == 5.00
        assert p.archived is False
        assert p.last_run_id is None

    def test_root_path_normalized_to_absolute(self) -> None:
        """Relative paths get resolved to absolute on construction."""
        p = Project(name="alpha", root_path=Path("./relative-thing"))
        assert p.root_path.is_absolute()

    def test_root_path_expands_user(self) -> None:
        p = Project(name="alpha", root_path=Path("~/foo"))
        assert "~" not in str(p.root_path)
        assert p.root_path.is_absolute()

    def test_name_must_be_non_empty(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError):
            Project(name="", root_path=tmp_path)

    def test_budget_must_be_positive(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError):
            Project(name="alpha", root_path=tmp_path, default_budget=0.0)
        with pytest.raises(ValueError):
            Project(name="alpha", root_path=tmp_path, default_budget=-1.0)

    def test_notification_prefs_defaults(self, tmp_path: Path) -> None:
        p = Project(name="alpha", root_path=tmp_path)
        assert p.notification_prefs.os_notification is True
        assert p.notification_prefs.audible_chime is False
        assert p.notification_prefs.terminal_bell is True

    def test_notification_prefs_override(self, tmp_path: Path) -> None:
        prefs = NotificationPrefs(
            os_notification=False,
            audible_chime=True,
            terminal_bell=False,
        )
        p = Project(name="alpha", root_path=tmp_path, notification_prefs=prefs)
        assert p.notification_prefs.os_notification is False
        assert p.notification_prefs.audible_chime is True


# --- Registry path resolution ---


class TestRegistryPath:
    def test_registry_path_under_wonderland_home(
        self, tmp_path: Path
    ) -> None:
        path = projects_registry_path()
        assert path.parent == tmp_path / ".wonderland"
        assert path.name == "projects.json"

    def test_registry_path_falls_back_to_home(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("WONDERLAND_HOME", raising=False)
        path = projects_registry_path()
        assert path.parent == Path.home() / ".wonderland"


# --- list_projects ---


class TestListProjects:
    def test_empty_when_no_registry_file(self) -> None:
        """Missing registry file is treated as 'no projects' rather
        than an error."""
        assert list_projects() == []

    def test_lists_in_alphabetical_order(self, tmp_path: Path) -> None:
        register_project(Project(name="charlie", root_path=tmp_path / "c"))
        register_project(Project(name="alpha", root_path=tmp_path / "a"))
        register_project(Project(name="bravo", root_path=tmp_path / "b"))
        names = [p.name for p in list_projects()]
        assert names == ["alpha", "bravo", "charlie"]

    def test_archived_excluded_by_default(self, tmp_path: Path) -> None:
        register_project(Project(name="active", root_path=tmp_path / "a"))
        register_project(Project(name="dead", root_path=tmp_path / "d"))
        archive_project("dead")
        names = [p.name for p in list_projects()]
        assert names == ["active"]

    def test_archived_included_when_requested(self, tmp_path: Path) -> None:
        register_project(Project(name="active", root_path=tmp_path / "a"))
        register_project(Project(name="dead", root_path=tmp_path / "d"))
        archive_project("dead")
        names = [p.name for p in list_projects(include_archived=True)]
        assert sorted(names) == ["active", "dead"]


# --- register_project ---


class TestRegisterProject:
    def test_registers_new_project(self, tmp_path: Path) -> None:
        p = Project(name="alpha", root_path=tmp_path / "alpha")
        register_project(p)
        loaded = load_project("alpha")
        assert loaded.name == "alpha"
        assert loaded.root_path == (tmp_path / "alpha").resolve()

    def test_creates_registry_file_lazily(self, tmp_path: Path) -> None:
        path = projects_registry_path()
        assert not path.exists()
        register_project(Project(name="alpha", root_path=tmp_path))
        assert path.is_file()

    def test_rejects_duplicate_name(self, tmp_path: Path) -> None:
        register_project(Project(name="alpha", root_path=tmp_path / "a"))
        with pytest.raises(ValueError, match="already registered"):
            register_project(Project(name="alpha", root_path=tmp_path / "b"))

    def test_rejects_duplicate_even_when_archived(self, tmp_path: Path) -> None:
        """Archived projects still occupy their name slot — operator
        must unarchive (or pick a new name) before reusing."""
        register_project(Project(name="alpha", root_path=tmp_path / "a"))
        archive_project("alpha")
        with pytest.raises(ValueError, match="already registered"):
            register_project(Project(name="alpha", root_path=tmp_path / "b"))

    def test_persists_across_reloads(self, tmp_path: Path) -> None:
        """Registry survives the in-process load cycle — write, then
        re-read should round-trip cleanly."""
        original = Project(
            name="alpha",
            root_path=tmp_path / "alpha",
            last_workflow="tdd-serial-phased",
            default_skeleton="python-cli",
            default_budget=7.50,
        )
        register_project(original)
        loaded = load_project("alpha")
        assert loaded.last_workflow == "tdd-serial-phased"
        assert loaded.default_skeleton == "python-cli"
        assert loaded.default_budget == 7.50


# --- load_project ---


class TestLoadProject:
    def test_loads_by_name(self, tmp_path: Path) -> None:
        register_project(Project(name="alpha", root_path=tmp_path))
        p = load_project("alpha")
        assert p.name == "alpha"

    def test_loads_archived_too(self, tmp_path: Path) -> None:
        """load_project finds archived projects — useful for the
        Archived tab in T75."""
        register_project(Project(name="alpha", root_path=tmp_path))
        archive_project("alpha")
        p = load_project("alpha")
        assert p.archived is True

    def test_raises_on_missing(self) -> None:
        with pytest.raises(KeyError, match="no project named"):
            load_project("nonexistent")

    def test_error_lists_available_names(self, tmp_path: Path) -> None:
        register_project(Project(name="alpha", root_path=tmp_path))
        with pytest.raises(KeyError) as excinfo:
            load_project("nonexistent")
        assert "alpha" in str(excinfo.value)


# --- save_project ---


class TestSaveProject:
    def test_persists_mutations(self, tmp_path: Path) -> None:
        register_project(Project(name="alpha", root_path=tmp_path))
        p = load_project("alpha")
        p.last_workflow = "tdd-serial-phased"
        p.last_run_id = "20260509T230353"
        save_project(p)

        reloaded = load_project("alpha")
        assert reloaded.last_workflow == "tdd-serial-phased"
        assert reloaded.last_run_id == "20260509T230353"

    def test_raises_on_unknown_name(self, tmp_path: Path) -> None:
        unregistered = Project(name="ghost", root_path=tmp_path)
        with pytest.raises(KeyError, match="no project named .*ghost"):
            save_project(unregistered)


# --- archive / unarchive ---


class TestArchive:
    def test_archive_marks_project_archived(self, tmp_path: Path) -> None:
        register_project(Project(name="alpha", root_path=tmp_path))
        archive_project("alpha")
        assert load_project("alpha").archived is True

    def test_archive_is_idempotent(self, tmp_path: Path) -> None:
        register_project(Project(name="alpha", root_path=tmp_path))
        archive_project("alpha")
        archive_project("alpha")  # no-op, no error
        assert load_project("alpha").archived is True

    def test_unarchive_reverses(self, tmp_path: Path) -> None:
        register_project(Project(name="alpha", root_path=tmp_path))
        archive_project("alpha")
        unarchive_project("alpha")
        assert load_project("alpha").archived is False

    def test_unarchive_idempotent_on_active(self, tmp_path: Path) -> None:
        register_project(Project(name="alpha", root_path=tmp_path))
        unarchive_project("alpha")  # no-op
        assert load_project("alpha").archived is False


# --- Atomic write ---


class TestAtomicWrite:
    def test_no_partial_writes_visible(self, tmp_path: Path) -> None:
        """Mid-write crash recovery — the tmp+rename pattern means
        the registry file is either pre-write or post-write, never
        partially written. We can't easily simulate a crash here, but
        we can confirm no .json.tmp leftovers persist after a normal
        write."""
        register_project(Project(name="alpha", root_path=tmp_path))
        registry_dir = projects_registry_path().parent
        leftovers = list(registry_dir.glob("*.tmp"))
        assert leftovers == []


# --- Malformed registry ---


class TestMalformedRegistry:
    def test_missing_projects_key_raises(self, tmp_path: Path) -> None:
        path = projects_registry_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"unrelated": "data"}')
        with pytest.raises(ValueError, match="malformed"):
            list_projects()

    def test_invalid_json_raises(self, tmp_path: Path) -> None:
        path = projects_registry_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("not json at all {{{")
        import json

        with pytest.raises(json.JSONDecodeError):
            list_projects()

    def test_empty_file_treated_as_no_projects(self, tmp_path: Path) -> None:
        """Empty registry file is benign — same as no file at all."""
        path = projects_registry_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("")
        assert list_projects() == []


# --- Per-project run history (T80) ---


class TestListProjectRuns:
    def test_empty_when_no_telemetry_dir(self, tmp_path: Path) -> None:
        from wonderland.project import list_project_runs

        register_project(Project(name="alpha", root_path=tmp_path / "alpha"))
        # No .wonderland/telemetry/ exists yet.
        records = list_project_runs(load_project("alpha"))
        assert records == []

    def test_lists_run_records_from_telemetry_files(
        self, tmp_path: Path
    ) -> None:
        import json
        from wonderland.project import list_project_runs

        root = tmp_path / "alpha"
        root.mkdir()
        register_project(Project(name="alpha", root_path=root))

        telemetry_dir = root / ".wonderland" / "telemetry"
        telemetry_dir.mkdir(parents=True)
        (telemetry_dir / "run-20260509T120000.json").write_text(json.dumps({
            "run_id": "20260509T120000",
            "total_cost": 1.50,
            "total_calls": 42,
            "elapsed_seconds": 120.0,
            "outcome": "complete",
            "model": "claude-haiku-4-5-20251001",
            "budget_dollars": 5.00,
            "budget_exceeded": False,
        }))
        (telemetry_dir / "run-20260510T080000.json").write_text(json.dumps({
            "run_id": "20260510T080000",
            "total_cost": 5.00,
            "total_calls": 100,
            "elapsed_seconds": 600.0,
            "outcome": "complete",
            "model": "claude-haiku-4-5-20251001",
            "budget_dollars": 5.00,
            "budget_exceeded": True,
        }))

        records = list_project_runs(load_project("alpha"))
        assert len(records) == 2
        # Newest first.
        assert records[0].run_id == "20260510T080000"
        assert records[1].run_id == "20260509T120000"
        assert records[0].budget_exceeded is True
        assert records[1].total_cost == 1.50

    def test_skips_malformed_telemetry(self, tmp_path: Path) -> None:
        from wonderland.project import list_project_runs

        root = tmp_path / "alpha"
        root.mkdir()
        register_project(Project(name="alpha", root_path=root))
        telemetry_dir = root / ".wonderland" / "telemetry"
        telemetry_dir.mkdir(parents=True)
        # Garbage JSON
        (telemetry_dir / "run-bad.json").write_text("not json {{")
        # Missing run_id
        (telemetry_dir / "run-noid.json").write_text('{"total_cost": 1.0}')
        # Valid one
        import json
        (telemetry_dir / "run-20260509T120000.json").write_text(json.dumps({
            "run_id": "20260509T120000",
            "total_cost": 1.0,
            "total_calls": 1,
        }))

        records = list_project_runs(load_project("alpha"))
        assert len(records) == 1
        assert records[0].run_id == "20260509T120000"

    def test_run_record_started_at_parses_run_id(
        self, tmp_path: Path
    ) -> None:
        from wonderland.project import RunRecord

        record = RunRecord(
            run_id="20260509T120530",
            telemetry_path=tmp_path / "x.json",
            total_cost=0,
            total_calls=0,
            elapsed_seconds=None,
            outcome=None,
            model=None,
            budget_dollars=None,
            budget_exceeded=False,
        )
        assert record.started_at is not None
        assert record.started_at.year == 2026
        assert record.started_at.month == 5
        assert record.started_at.hour == 12

    def test_run_record_started_at_handles_unparseable(
        self, tmp_path: Path
    ) -> None:
        from wonderland.project import RunRecord

        record = RunRecord(
            run_id="legacy-snapshot-name",
            telemetry_path=tmp_path / "x.json",
            total_cost=0,
            total_calls=0,
            elapsed_seconds=None,
            outcome=None,
            model=None,
            budget_dollars=None,
            budget_exceeded=False,
        )
        assert record.started_at is None
