"""Project — first-class abstraction for an operator's working venue.

Pre-P11, "project" was implicit: a path the operator typed into
NewRunScreen, with run history scattered across `runs/` directories
under the wonderland-ai checkout. Operators came back to a path and
re-typed everything (workflow, budget, directive presets) each time.

P11 promotes Project to a registered entity with its own metadata,
defaults, and a stable identity that the TUI orients around. Runs can
still be launched without a project (back-compat for ad-hoc work) —
Project is *additive*, not a precondition.

Persistence is a single registry file at ``~/.wonderland/projects.json``
(simple migration story, no per-project dotfiles to manage). The file
is created lazily on first ``register_project()`` call; missing-file
state is treated as "no projects yet" rather than an error.

API mirrors ``wonderland.skeleton`` and ``wonderland.workflow``:

  - ``projects_registry_path()`` — resolved path to the JSON registry
  - ``list_projects(include_archived=False)`` — enumerate
  - ``load_project(name)`` — fetch one by name (raises if missing)
  - ``save_project(p)`` — persist updates to an existing project
  - ``register_project(p)`` — add a new project (rejects duplicate names)
  - ``archive_project(name)`` — soft-delete (run history stays)
  - ``unarchive_project(name)`` — undo archive
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------- #
# Project lifecycle phase — P15 T-m8 UX work
#
# An operator opening the dashboard should immediately see WHERE the
# project sits in the discovery → planning → design → implementation
# flow, and what the recommended next workflow is. ``derive_project_phase``
# reads ``.wonderland/`` directly and computes the phase from disk
# state — no separate state file to keep in sync, no agent involvement.
# ---------------------------------------------------------------------- #


class ProjectPhase(StrEnum):
    DISCOVERY = "discovery"
    """No requirements captured yet — operator should run the discovery
    workflow first to interview the team about personas, constraints,
    scope, and success criteria."""

    PLANNING = "planning"
    """Requirements exist, but no milestones — operator should run
    milestone-plan to organize the requirements into a 3-7 milestone
    sequence."""

    DESIGN = "design"
    """Milestones planned. At least one milestone hasn't yet been
    designed (no features sourcing its consumed requirements'
    stories). Operator should run tdd-design with --milestone <slug>
    for the next undesigned milestone."""

    IMPLEMENTATION = "implementation"
    """All planned milestones have features. Operator should queue
    features + run tdd-implement to ship them."""

    COMPLETE = "complete"
    """Every feature in every milestone has been verified. Project
    is shipped — operator may add follow-on milestones or call it
    done."""


@dataclass(frozen=True)
class ProjectPhaseSnapshot:
    """Derived view of where the project sits in the flow. The
    dashboard renders ``label`` + ``next_action_hint``; downstream
    automation may dispatch on ``phase``."""

    phase: ProjectPhase
    label: str
    """One-line headline, e.g. ``DESIGN (M1 of 4 milestones)``."""
    next_action_hint: str
    """Operator-facing recommendation: which workflow to run next +
    optionally the --milestone slug to scope it."""
    requirements_count: int
    milestones_count: int
    designed_milestones_count: int
    features_count: int


def derive_project_phase(project_root: Path) -> ProjectPhaseSnapshot:
    """Read ``project_root/.wonderland/`` and return a phase snapshot.

    Heuristics — keep the phase derivation purely structural so the
    dashboard never gets stuck waiting on a state file an agent
    forgot to write:

      - DISCOVERY: zero requirement files
      - PLANNING: requirements exist, zero milestones
      - DESIGN: any milestone has zero features sourcing stories
        that realize its consumed requirements; recommend the
        lowest-ordered such milestone
      - IMPLEMENTATION: every milestone has at least one feature; no
        special completion check (lifecycle states drive what's
        next inside implementation)
      - COMPLETE: every feature is in ``verified`` (read from
        feature-states.jsonl)

    Falls back to DISCOVERY when ``project_root`` doesn't have a
    ``.wonderland/`` dir at all.
    """
    wland = project_root / ".wonderland"
    req_dir = wland / "requirements"
    milestone_dir = wland / "milestones"
    story_dir = wland / "stories"
    feature_dir = wland / "features"

    def _count(d: Path, pattern: str) -> int:
        if not d.is_dir():
            return 0
        return sum(1 for _ in d.glob(pattern))

    req_count = _count(req_dir, "requirement-*.md")
    milestone_count = _count(milestone_dir, "milestone-*.md")
    feature_count = _count(feature_dir, "feature-*.md")

    if req_count == 0:
        return ProjectPhaseSnapshot(
            phase=ProjectPhase.DISCOVERY,
            label="DISCOVERY — no requirements yet",
            next_action_hint=(
                "Run the ``discovery`` workflow to interview the "
                "team about personas, constraints, and scope."
            ),
            requirements_count=0,
            milestones_count=0,
            designed_milestones_count=0,
            features_count=0,
        )

    if milestone_count == 0:
        return ProjectPhaseSnapshot(
            phase=ProjectPhase.PLANNING,
            label=(
                f"PLANNING — {req_count} requirements captured, "
                "no milestones yet"
            ),
            next_action_hint=(
                "Run the ``milestone-plan`` workflow to organize "
                "the requirements into a 3-7 milestone sequence."
            ),
            requirements_count=req_count,
            milestones_count=0,
            designed_milestones_count=0,
            features_count=feature_count,
        )

    # Per-milestone realization check — find the lowest-ordered
    # milestone whose consumes_requirements aren't all realized by
    # features. If every milestone is designed, fall through to
    # implementation/complete checks.
    next_undesigned_slug, next_undesigned_label, designed_count = (
        _find_next_undesigned_milestone(project_root)
    )
    if next_undesigned_slug is not None:
        label = (
            f"DESIGN — {next_undesigned_label} "
            f"({designed_count} of {milestone_count} designed)"
        )
        hint = (
            f"Run ``tdd-design --milestone "
            f"{next_undesigned_slug}`` to compose features "
            f"realizing this milestone's requirements."
        )
        return ProjectPhaseSnapshot(
            phase=ProjectPhase.DESIGN,
            label=label,
            next_action_hint=hint,
            requirements_count=req_count,
            milestones_count=milestone_count,
            designed_milestones_count=designed_count,
            features_count=feature_count,
        )

    # All milestones designed. Check if all features are verified.
    all_verified = _all_features_verified(project_root)
    if all_verified and feature_count > 0:
        return ProjectPhaseSnapshot(
            phase=ProjectPhase.COMPLETE,
            label=(
                f"COMPLETE — all {feature_count} features verified "
                f"across {milestone_count} milestones"
            ),
            next_action_hint=(
                "Project is shipped. Add a follow-on milestone via "
                "``milestone-plan`` or call it done."
            ),
            requirements_count=req_count,
            milestones_count=milestone_count,
            designed_milestones_count=milestone_count,
            features_count=feature_count,
        )

    return ProjectPhaseSnapshot(
        phase=ProjectPhase.IMPLEMENTATION,
        label=(
            f"IMPLEMENTATION — {feature_count} features designed "
            f"across {milestone_count} milestones"
        ),
        next_action_hint=(
            "Queue features in the dashboard, then run "
            "``tdd-implement`` to ship the work."
        ),
        requirements_count=req_count,
        milestones_count=milestone_count,
        designed_milestones_count=milestone_count,
        features_count=feature_count,
    )


def _find_next_undesigned_milestone(
    project_root: Path,
) -> tuple[str | None, str, int]:
    """Walk milestones in order, find the first that isn't realized
    (i.e., has consumes_requirements with no story→feature chain).

    Reuses ``wonderland.coverage`` rather than reimplementing the
    chain walk. Returns ``(slug, label, designed_count)`` where
    slug is None when every milestone is designed.
    """
    try:
        from wonderland.coverage import (
            run_coverage_check,
        )
    except Exception:  # noqa: BLE001
        return None, "", 0

    milestone_dir = project_root / ".wonderland" / "milestones"
    if not milestone_dir.is_dir():
        return None, "", 0

    # Read each milestone's slug + order from disk; visit in order.
    import re

    entries: list[tuple[int, str, str]] = []
    for path in milestone_dir.glob("milestone-*.md"):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        slug_m = re.search(
            r"^\*\*Slug:\*\*\s*(\S+)", text, re.MULTILINE
        )
        order_m = re.search(
            r"^\*\*Order:\*\*\s*(\d+)", text, re.MULTILINE
        )
        title_m = re.match(r"##\s*(.+?)$", text, re.MULTILINE)
        if not slug_m:
            continue
        slug = slug_m.group(1).strip()
        order = int(order_m.group(1)) if order_m else 999
        title = title_m.group(1).strip() if title_m else slug
        entries.append((order, slug, title))

    entries.sort()
    designed = 0
    for _order, slug, title in entries:
        gap = run_coverage_check(
            "milestone_realization",
            project_root,
            milestone_slug=slug,
        )
        if gap is None:
            designed += 1
            continue
        # First undesigned wins.
        return slug, title, designed

    return None, "", designed


def _all_features_verified(project_root: Path) -> bool:
    """Read feature-states.jsonl + check every feature's last state
    is ``verified``. When the file's missing, treat as 'not yet
    complete' (zero verified features can't be COMPLETE)."""
    states_path = project_root / ".wonderland" / "feature-states.jsonl"
    if not states_path.is_file():
        return False
    try:
        text = states_path.read_text(encoding="utf-8")
    except OSError:
        return False

    last_state: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            evt = json.loads(line)
        except json.JSONDecodeError:
            continue
        slug = evt.get("feature_slug")
        to_state = evt.get("to_state")
        if slug and to_state:
            last_state[slug] = to_state

    if not last_state:
        return False
    return all(s == "verified" for s in last_state.values())


def projects_registry_path() -> Path:
    """Path to the global projects registry file. Honors WONDERLAND_HOME
    if set (testing convenience), otherwise lands at ``~/.wonderland/``.
    """
    import os

    home_override = os.environ.get("WONDERLAND_HOME")
    base = Path(home_override) if home_override else Path.home() / ".wonderland"
    return base / "projects.json"


class NotificationPrefs(BaseModel):
    """Per-project notification preferences. Future bug 24e8ce94
    (auto-sentinel notifications) will read these to decide whether
    to fire OS-level notifications when a question is pending."""

    # OS-level notification (notify-send / equivalent) when the team
    # asks the operator a question or when a run hits an escalation.
    os_notification: bool = True
    # Audible chime on the same triggers. Off by default to avoid
    # surprising users; opt-in for noisy demo rigs.
    audible_chime: bool = False
    # Terminal bell character (\a) — zero-dependency fallback that
    # works in any terminal that has bell-on-active configured.
    terminal_bell: bool = True


class Project(BaseModel):
    """A registered Wonderland project — name, root, defaults, history.

    Created via ``register_project()``; mutated via ``save_project()``;
    fetched via ``load_project(name)``. Names are unique within the
    registry; root_path values *should* be unique but the registry
    doesn't hard-enforce that (an operator may have aliased two
    project names to the same root for staging vs. production
    purposes — uncommon but valid)."""

    name: str = Field(
        min_length=1,
        description="Stable, human-readable identifier. Unique in the registry.",
    )
    root_path: Path = Field(
        description=(
            "Absolute path to the project's working tree. Stored as "
            "``Path``; serialized as a string in the JSON registry."
        ),
    )
    last_workflow: str | None = Field(
        default=None,
        description=(
            "Workflow name (e.g. 'tdd-serial-phased') most recently "
            "launched against this project. NewRunScreen prefills the "
            "Select with this — purely a usability hint. The operator "
            "can pick any workflow per run; switching workflows is "
            "expected (TDD for features, smoke for sanity checks, "
            "etc.). Auto-updates after each successful run; not a "
            "constraint, not 'the project's workflow.'"
        ),
    )
    default_skeleton: str | None = Field(
        default=None,
        description=(
            "Skeleton name (e.g. 'fullstack-fastapi-react') applied "
            "at project creation. Stored for record only — re-applying "
            "isn't part of normal operation."
        ),
    )
    default_budget: float = Field(
        default=5.00,
        gt=0,
        description="Default per-run dollar budget; NewRunScreen prefills this.",
    )
    notification_prefs: NotificationPrefs = Field(
        default_factory=NotificationPrefs,
        description="Per-project notification preferences (bug 24e8ce94).",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp of registration.",
    )
    last_run_id: str | None = Field(
        default=None,
        description=(
            "run_id of the most recent run launched against this "
            "project. None until the first run completes."
        ),
    )
    prime_directive: str | None = Field(
        default=None,
        description=(
            "Operator-blessed canonical directive for the project. "
            "Used by NewRunScreen's preset table as a 'Prime' "
            "starting point so design passes on long-running projects "
            "stay oriented across N>1 runs. Auto-populated from the "
            "first non-empty directive launched against the project; "
            "subsequent updates currently require editing the registry "
            "(in-TUI editor lands in a follow-on)."
        ),
    )
    archived: bool = Field(
        default=False,
        description=(
            "Soft-delete flag. Archived projects don't show in the "
            "default library view but their run history stays "
            "accessible via the Archived tab."
        ),
    )

    @field_validator("root_path")
    @classmethod
    def _absolute_path(cls, v: Path) -> Path:
        """Normalize root_path to absolute. Doesn't require the path
        to *exist* — projects can be registered against paths that
        will be created at apply-skeleton time."""
        return v.expanduser().resolve()


def _read_registry() -> dict:
    """Load the registry file, returning ``{"projects": []}`` if absent
    or empty. Raises on malformed JSON so the caller doesn't silently
    operate on a partial registry."""
    path = projects_registry_path()
    if not path.is_file():
        return {"projects": []}
    text = path.read_text()
    if not text.strip():
        return {"projects": []}
    data = json.loads(text)
    if not isinstance(data, dict) or "projects" not in data:
        raise ValueError(
            f"projects registry at {path} is malformed: expected "
            f"a top-level dict with a 'projects' key"
        )
    return data


def _write_registry(data: dict) -> None:
    """Atomic write to the registry file. Creates the parent directory
    if missing. Uses a tmp+rename pattern so a crash mid-write doesn't
    corrupt the registry."""
    path = projects_registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str))
    tmp.replace(path)


def list_projects(*, include_archived: bool = False) -> list[Project]:
    """Enumerate registered projects. By default filters out archived
    ones; pass ``include_archived=True`` for the full list (the
    Archived tab in T75's library uses this)."""
    data = _read_registry()
    projects = [Project.model_validate(p) for p in data.get("projects", [])]
    if not include_archived:
        projects = [p for p in projects if not p.archived]
    projects.sort(key=lambda p: p.name)
    return projects


def load_project(name: str) -> Project:
    """Fetch a project by name. Raises ``KeyError`` if no project
    with that name is registered."""
    for p in list_projects(include_archived=True):
        if p.name == name:
            return p
    raise KeyError(
        f"no project named {name!r}; "
        f"registered: {[p.name for p in list_projects(include_archived=True)]}"
    )


def save_project(project: Project) -> None:
    """Persist updates to an existing project. Raises ``KeyError`` if
    no project with this name exists — use ``register_project`` to
    add new ones."""
    data = _read_registry()
    projects = data.get("projects", [])
    for i, p_data in enumerate(projects):
        if p_data.get("name") == project.name:
            projects[i] = json.loads(project.model_dump_json())
            data["projects"] = projects
            _write_registry(data)
            return
    raise KeyError(
        f"no project named {project.name!r} to save; "
        f"call register_project() instead"
    )


def register_project(project: Project) -> None:
    """Add a new project to the registry. Raises ``ValueError`` if
    a project with the same name already exists (regardless of
    archived state)."""
    data = _read_registry()
    projects = data.get("projects", [])
    existing_names = {p.get("name") for p in projects}
    if project.name in existing_names:
        raise ValueError(
            f"project named {project.name!r} already registered; "
            f"use save_project() to update or pick a different name"
        )
    projects.append(json.loads(project.model_dump_json()))
    data["projects"] = projects
    _write_registry(data)


def archive_project(name: str) -> None:
    """Soft-delete a project. Run history stays accessible via the
    Archived tab in the project library; the project no longer
    appears in the default ``list_projects()`` view."""
    project = load_project(name)
    if project.archived:
        return  # idempotent
    project.archived = True
    save_project(project)


def unarchive_project(name: str) -> None:
    """Reverse ``archive_project()``. Idempotent — safe to call on
    already-active projects."""
    project = load_project(name)
    if not project.archived:
        return
    project.archived = False
    save_project(project)


# --------------------------------------------------------------------- #
# Per-project run history (P11 T80)
# --------------------------------------------------------------------- #


@dataclass(frozen=True)
class RunRecord:
    """Lightweight summary of a single run, parsed from a telemetry
    JSON file. Cheaper than HistoricalRunHandle — no log parsing,
    no SQLite connection, no caches. ProjectDashboardScreen's Runs
    tab uses this for the list view; per-run detail still fans out
    to richer accessors when the operator drills in.
    """

    run_id: str
    telemetry_path: Path
    total_cost: float
    total_calls: int
    elapsed_seconds: float | None
    outcome: str | None
    model: str | None
    budget_dollars: float | None
    budget_exceeded: bool

    @property
    def started_at(self) -> datetime | None:
        """Parse the run_id (format YYYYMMDDTHHMMSS) into a UTC
        datetime. Returns None if the run_id doesn't match the
        expected format (e.g. legacy snapshots with arbitrary names)."""
        try:
            return datetime.strptime(self.run_id, "%Y%m%dT%H%M%S").replace(
                tzinfo=UTC
            )
        except (ValueError, TypeError):
            return None


def list_project_runs(project: Project) -> list[RunRecord]:
    """Enumerate runs for a project by scanning ``<root>/.wonderland/
    telemetry/run-*.json``. Sorted by started_at descending (newest
    first) — the dashboard's natural reading order.

    Best-effort: malformed telemetry files are skipped silently
    (they shouldn't normally exist, but a partial write during a
    crashed run could leave one). The list is empty when the project
    hasn't run anything yet."""
    telemetry_dir = project.root_path / ".wonderland" / "telemetry"
    if not telemetry_dir.is_dir():
        return []
    records: list[RunRecord] = []
    for path in telemetry_dir.glob("run-*.json"):
        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        run_id = data.get("run_id")
        if not isinstance(run_id, str):
            continue
        records.append(RunRecord(
            run_id=run_id,
            telemetry_path=path,
            total_cost=float(data.get("total_cost", 0.0)),
            total_calls=int(data.get("total_calls", 0)),
            elapsed_seconds=(
                float(data["elapsed_seconds"])
                if isinstance(data.get("elapsed_seconds"), (int, float))
                else None
            ),
            outcome=data.get("outcome"),
            model=data.get("model"),
            budget_dollars=(
                float(data["budget_dollars"])
                if isinstance(data.get("budget_dollars"), (int, float))
                else None
            ),
            budget_exceeded=bool(data.get("budget_exceeded", False)),
        ))
    # Newest first. RunRecord.started_at parses the run_id; runs with
    # unparseable ids sink to the bottom (None comparison handled via
    # an empty-string fallback for sort stability).
    records.sort(
        key=lambda r: r.started_at or datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )
    return records


__all__ = [
    "NotificationPrefs",
    "Project",
    "RunRecord",
    "archive_project",
    "list_project_runs",
    "list_projects",
    "load_project",
    "projects_registry_path",
    "register_project",
    "save_project",
    "unarchive_project",
]
