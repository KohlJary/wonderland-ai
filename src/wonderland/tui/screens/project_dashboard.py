"""ProjectDashboardScreen — per-project landing surface (P11 T79).

Shell + tab structure for the in-depth project view. Operators reach
this from ProjectLibraryScreen by selecting a project and pressing
the dashboard binding (currently bound to a separate key — Enter
still launches a new run, since that's the higher-frequency action).

Tabs:
  - Runs (T80): list of past runs with per-run detail
  - Artifacts (T83): browse .wonderland/ contents per run
  - Files (T81 — placeholder): DirectoryTree of project_root,
    coming in the next chunk
  - Metrics (T82 — placeholder): plotext graphs across runs,
    coming in the next chunk

Lazygit-shape inside each tab: list left, detail right.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    DirectoryTree,
    Footer,
    Header,
    Static,
    TabbedContent,
    TabPane,
    Tree,
)

from wonderland.feature_lifecycle import (
    FeatureState,
    get_state as get_feature_state,
)
from wonderland.project import (
    Project,
    RunRecord,
    list_project_runs,
)


def _fmt_duration(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    if seconds < 60:
        return f"{seconds:.0f}s"
    return f"{seconds / 60:.1f}m"


def _fmt_cost(cost: float) -> str:
    return f"${cost:.2f}"


def _fmt_outcome(outcome: str | None, budget_exceeded: bool) -> str:
    """Render outcome with a color hint. budget_exceeded=true tags
    the run with a yellow [budget!] suffix even when outcome=complete
    so the operator sees that the cap fired."""
    if outcome is None:
        return "[dim]?[/dim]"
    base = {
        "complete": f"[green]{outcome}[/green]",
        "aborted": f"[red]{outcome}[/red]",
        "timeout": f"[red]{outcome}[/red]",
    }.get(outcome, outcome)
    if budget_exceeded:
        return f"{base} [yellow][budget!][/yellow]"
    return base


_AGENT_KEYS = (
    "alice",
    "cheshire_cat",
    "white_rabbit",
    "dodo",
    "mad_hatter",
    "caterpillar",
    "queen_of_hearts",
    "dormouse",
    "tweedledee",
    "tweedledum",
)


# Directory names skipped by the Files tab — system, build, or cache
# state that operators don't need cluttering the tree. Matched against
# entry.name (basename), not full path.
_FILES_TAB_SKIP_DIRS: frozenset[str] = frozenset({
    ".git",
    ".wonderland",  # has its own Artifacts tab
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".tox",
    ".idea",
    ".vscode",
    "target",  # rust
    ".next",
    ".cache",
})

# Files larger than this get truncated in the content viewer; anything
# larger is best opened externally.
_FILE_VIEWER_MAX_BYTES: int = 200_000


class _FilteredDirectoryTree(DirectoryTree):
    """DirectoryTree that hides system/build/cache directories from
    the Files tab. The standard widget shows everything; for project
    browsing we want a clean view of the operator's actual code +
    artifacts. Keeps the .wonderland/ tree out (it has its own tab)."""

    def filter_paths(self, paths):  # type: ignore[override]
        return [
            p for p in paths
            if not (p.is_dir() and p.name in _FILES_TAB_SKIP_DIRS)
        ]


class _FeatureRow:
    """Lightweight container for a feature row in the dashboard list.
    Holds slug, title, current lifecycle state, kind (capability vs
    foundation), and the path to the feature's markdown file so the
    detail pane can render the dossier."""

    __slots__ = ("slug", "title", "state", "kind", "path")

    def __init__(
        self,
        slug: str,
        title: str,
        state: FeatureState | None,
        path: Path,
        kind: str = "capability",
    ) -> None:
        self.slug = slug
        self.title = title
        self.state = state
        self.kind = kind
        self.path = path


_STATE_BADGE: dict[FeatureState | None, str] = {
    None: "[dim]?[/dim]",
    FeatureState.PROPOSED: "[grey50]●[/grey50] proposed",
    FeatureState.IN_DESIGN: "[blue]●[/blue] in_design",
    FeatureState.DESIGNED: "[cyan]●[/cyan] designed",
    FeatureState.QUEUED: "[yellow]●[/yellow] queued",
    FeatureState.IN_PROGRESS: "[magenta]●[/magenta] in_progress",
    FeatureState.READY_FOR_REVIEW: "[green]◯[/green] ready_review",
    FeatureState.VERIFIED: "[bright_green]✓[/bright_green] verified",
    FeatureState.REJECTED: "[red]✗[/red] rejected",
}


# Filter chip definitions. None state means "all". FeatureState members
# filter to that specific state. Order chosen to match the operator's
# typical scan order: triage states first, then terminal states.
_FILTER_CHIPS: tuple[tuple[str, str, FeatureState | None], ...] = (
    ("filter-all", "all", None),
    ("filter-designed", "designed", FeatureState.DESIGNED),
    ("filter-queued", "queued", FeatureState.QUEUED),
    ("filter-rfr", "ready_review", FeatureState.READY_FOR_REVIEW),
    ("filter-in-progress", "in_progress", FeatureState.IN_PROGRESS),
    ("filter-verified", "verified", FeatureState.VERIFIED),
    ("filter-rejected", "rejected", FeatureState.REJECTED),
)


class ProjectDashboardScreen(Screen[None]):
    """Per-project landing surface — Features as primary content,
    drill-downs (Runs / Artifacts / Files / Metrics) as secondary
    tabs at the bottom.

    Reshape per the P12 architectural conversation: Features are the
    primary operator interaction surface ("what's the state of my
    features? which need my attention?"); investigation surfaces
    (run history, raw artifacts, code tree, metrics) are drill-downs
    the operator opens when "wait, why did the team make this contract
    decision?" comes up. Default focus lands on the features list."""

    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
        Binding("n", "new_run", "New run", show=True),
        Binding("R", "refresh", "Refresh", show=True),
        Binding("m", "toggle_mark", "Mark ticket", show=True),
        Binding("D", "prune_marked", "Delete marked", show=True),
        Binding("1", "show_runs", "Runs", show=False),
        Binding("2", "show_artifacts", "Artifacts", show=False),
        Binding("3", "show_files", "Files", show=False),
        Binding("4", "show_metrics", "Metrics", show=False),
    ]

    def __init__(self, project: Project) -> None:
        super().__init__()
        self.project = project
        self._runs: list[RunRecord] = []
        self._artifacts: list[tuple[str, Path]] = []
        self._features: list[_FeatureRow] = []
        self._filter: FeatureState | None = None
        # Marked-for-deletion ticket slugs. Operator presses ``m`` on
        # a ticket node in the features tree to toggle membership;
        # ``D`` opens the prune confirmation modal. Used to deduplicate
        # M3 output when Rabbit ships duplicate tickets across revision
        # passes (see analysis 040 + roadmap 171b36e1) — the
        # substrate-side dedup hasn't landed yet.
        self._marked_ticket_slugs: set[str] = set()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical(id="dashboard-root"):
            yield Static(
                f"[b]{self.project.name}[/b] · "
                f"[dim]{self.project.root_path}[/dim]",
                id="dashboard-header",
            )
            # Actions pane (T92) — all P12 actions always visible so
            # the operator's mental model of what's possible doesn't
            # depend on lifecycle state. The state-aware part is
            # PRIORITY: the highest-leverage action gets variant=
            # primary (visually emphasized); secondary actions stay
            # default. Buttons whose target state has zero features
            # get disabled (greyed out) but stay visible — operator
            # sees "Implement 0 queued" and understands they need to
            # queue something first.
            #
            # Priority order (T92):
            #   verify ready_for_review > implement queued >
            #   design (always available; promoted when nothing else
            #   is actionable)
            with Horizontal(id="dashboard-actions"):
                yield Button(
                    "▶ Design features",
                    id="action-design",
                    variant="primary",
                )
                yield Button(
                    "▶ Implement queued",
                    id="action-implement",
                )
                yield Button(
                    "▶ Verify ready",
                    id="action-verify-ready",
                )
                yield Button(
                    "Custom run",
                    id="action-custom-run",
                )

            # Features primary surface — left list (with state filter
            # chips), right detail (dossier + per-feature actions).
            # This is the operator's main attention surface in P12.
            with Horizontal(id="features-row"):
                with Vertical(id="features-list-pane"):
                    yield Static("[b]Features[/b]", id="features-list-label")
                    with Horizontal(id="features-filter-row"):
                        for chip_id, label, _state in _FILTER_CHIPS:
                            classes = "filter-chip"
                            if _state is None:
                                classes += " filter-active"
                            yield Button(
                                label, id=chip_id, classes=classes
                            )
                    # Tree (not DataTable): each feature is a parent
                    # node; its tickets nest underneath like a file
                    # tree. Operator can highlight a ticket and see
                    # the same dossier shape as for features. Default
                    # expanded so tickets are immediately visible —
                    # typical project sizes (3-6 features × 1-4
                    # tickets) fit fine.
                    yield Tree(
                        "Features",
                        id="features-tree",
                    )
                with Vertical(id="features-detail-pane"):
                    yield Static(
                        "[b]Feature detail[/b]",
                        id="features-detail-label",
                    )
                    with VerticalScroll(id="features-detail-scroll"):
                        yield Static(
                            "[dim](no feature selected)[/dim]",
                            id="features-detail",
                        )
                    with Horizontal(id="feature-actions-row"):
                        # Promote → Designed shows when the selected
                        # feature is in_design (M5 didn't fully fire,
                        # or operator un-promoted earlier). Replaces
                        # queue/un-queue in that view since those
                        # transitions aren't legal from in_design.
                        yield Button(
                            "Promote to Designed",
                            id="feature-action-promote-designed",
                            variant="primary",
                        )
                        yield Button(
                            "Queue", id="feature-action-queue"
                        )
                        yield Button(
                            "Un-queue", id="feature-action-unqueue"
                        )
                        # in_progress controls — escape hatches for
                        # features stuck mid-implementation. Mark Ready
                        # advances to ready_for_review (skip M8 and go
                        # straight to operator verify); Re-design
                        # aborts implementation and sends back to
                        # designed (operator wants to re-run design
                        # phase against new directive).
                        yield Button(
                            "Mark Ready",
                            id="feature-action-mark-ready",
                            variant="primary",
                        )
                        yield Button(
                            "Re-design",
                            id="feature-action-redesign",
                            variant="warning",
                        )
                        yield Button(
                            "Verify",
                            id="feature-action-verify",
                            variant="success",
                        )
                        yield Button(
                            "Reject",
                            id="feature-action-reject",
                            variant="error",
                        )

            # Drill-downs — investigation surfaces. Take less screen
            # real estate than the Features section; operator opens
            # them with 1/2/3/4 keybinds when investigating "why
            # did the team make this decision?" types of questions.
            yield Static(
                "[dim]Drill-downs · 1=Runs  2=Artifacts  "
                "3=Files  4=Metrics[/dim]",
                id="dashboard-drilldown-label",
            )
            with TabbedContent(id="dashboard-tabs"):
                with TabPane("Runs", id="tab-runs"):
                    yield from self._compose_runs_tab()
                with TabPane("Artifacts", id="tab-artifacts"):
                    yield from self._compose_artifacts_tab()
                with TabPane("Files", id="tab-files"):
                    yield from self._compose_files_tab()
                with TabPane("Metrics", id="tab-metrics"):
                    yield from self._compose_metrics_tab()
        yield Footer()

    # ------------------------------------------------------------------ #
    # Runs tab (T80)
    # ------------------------------------------------------------------ #

    def _compose_runs_tab(self) -> ComposeResult:
        with Horizontal(id="runs-tab-row"):
            with Vertical(id="runs-list-pane"):
                yield Static("[b]Runs[/b]", id="runs-list-label")
                yield DataTable(id="runs-table", cursor_type="row")
            with Vertical(id="runs-detail-pane"):
                yield Static("[b]Run detail[/b]", id="runs-detail-label")
                with VerticalScroll(id="runs-detail-scroll"):
                    yield Static(
                        "[dim](no run selected)[/dim]",
                        id="runs-detail",
                    )

    def _populate_runs(self) -> None:
        table = self.query_one("#runs-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Run", "Started", "Cost", "Calls", "Time", "Outcome")
        self._runs = list_project_runs(self.project)
        if not self._runs:
            self._render_runs_empty_state()
            return
        for record in self._runs:
            started = (
                record.started_at.strftime("%Y-%m-%d %H:%M")
                if record.started_at
                else "—"
            )
            table.add_row(
                record.run_id,
                started,
                _fmt_cost(record.total_cost),
                str(record.total_calls),
                _fmt_duration(record.elapsed_seconds),
                _fmt_outcome(record.outcome, record.budget_exceeded),
            )
        table.cursor_coordinate = (0, 0)
        self._render_run_detail(self._runs[0])

    def _render_runs_empty_state(self) -> None:
        detail = self.query_one("#runs-detail", Static)
        detail.update(
            "[b yellow]No runs yet for this project.[/b yellow]\n\n"
            "Press [b]escape[/b] to return to the project library, "
            "then press [b]Enter[/b] on the project (or click "
            "[b]▶ New run on selected project[/b]) to launch the "
            "first run.\n\n"
            "[dim]After at least one run completes, this tab will "
            "show the full history with cost / time / outcome per "
            "run.[/dim]"
        )

    def _render_run_detail(self, record: RunRecord) -> None:
        """Detail pane: per-agent cost breakdown + meta. Reads the
        telemetry JSON directly (cheap; one file). For richer per-run
        accessors (utterances, contract-notes, escalations) the
        Artifacts tab is the right place — this pane keeps to the
        top-level shape of the run."""
        detail = self.query_one("#runs-detail", Static)
        import json
        try:
            with record.telemetry_path.open(encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            detail.update(f"[red]Telemetry load failed: {exc}[/red]")
            return

        per_agent_raw = data.get("per_agent") or {}
        per_agent_pairs: list[tuple[str, int, float]] = []
        for name, agent_data in per_agent_raw.items():
            if not isinstance(agent_data, dict):
                continue
            per_agent_pairs.append((
                name,
                int(agent_data.get("calls", 0)),
                float(agent_data.get("cost", 0.0)),
            ))
        # Order: Wonderland canonical cast order, then any guests at
        # the bottom alphabetically.
        canonical_order = {n: i for i, n in enumerate(_AGENT_KEYS)}
        per_agent_pairs.sort(
            key=lambda t: (canonical_order.get(t[0], 999), t[0])
        )

        lines: list[str] = [
            f"[b]Run {record.run_id}[/b]",
            "",
        ]
        if record.started_at:
            lines.append(
                f"[b]Started:[/b] "
                f"{record.started_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )
        lines.extend([
            f"[b]Outcome:[/b] {_fmt_outcome(record.outcome, record.budget_exceeded)}",
            f"[b]Wall-clock:[/b] {_fmt_duration(record.elapsed_seconds)}",
            f"[b]Total cost:[/b] {_fmt_cost(record.total_cost)}"
            + (
                f" / {_fmt_cost(record.budget_dollars)} cap"
                if record.budget_dollars is not None
                else ""
            ),
            f"[b]Total calls:[/b] {record.total_calls}",
            f"[b]Model:[/b] {record.model or '[dim](unknown)[/dim]'}",
            "",
            "[b]Per-agent breakdown:[/b]",
        ])
        if not per_agent_pairs:
            lines.append("  [dim](no per-agent telemetry recorded)[/dim]")
        else:
            # Two-column layout: agent name + bar + numbers
            max_cost = max((cost for _, _, cost in per_agent_pairs), default=0.0)
            for name, calls, cost in per_agent_pairs:
                share = (cost / record.total_cost) if record.total_cost else 0
                bar_len = int(share * 20) if share > 0 else 0
                bar = "█" * bar_len + "·" * (20 - bar_len)
                pct = f"{share * 100:5.1f}%"
                lines.append(
                    f"  [b]{name:<16}[/b] {bar} "
                    f"{pct} · {_fmt_cost(cost)} · {calls:>4} calls"
                )
            del max_cost  # placeholder for future bar normalization

        lines.extend([
            "",
            f"[dim]Telemetry: {record.telemetry_path.name}[/dim]",
        ])
        detail.update("\n".join(lines))

    def on_data_table_row_highlighted(
        self, event: DataTable.RowHighlighted
    ) -> None:
        if event.data_table.id == "runs-table":
            row = event.cursor_row
            if row is None or row < 0 or row >= len(self._runs):
                return
            self._render_run_detail(self._runs[row])
        elif event.data_table.id == "artifacts-table":
            row = event.cursor_row
            if row is None or row < 0 or row >= len(self._artifacts):
                return
            self._render_artifact_content(self._artifacts[row])

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """Tree cursor moved → update the detail pane to match the
        highlighted node. Features render their dossier; tickets
        render the ticket markdown plus a header naming the parent
        feature so the operator keeps context."""
        if event.node.tree.id != "features-tree":
            return
        data = event.node.data
        if data is None:
            return
        if data.get("kind") == "feature":
            row = data["row"]
            self._render_feature_detail(row)
            self._refresh_per_feature_action_buttons(row)
        elif data.get("kind") == "ticket":
            self._render_ticket_detail(
                data["record"], data["feature_row"]
            )
            # Tickets don't have lifecycle state of their own; show
            # the parent feature's button shape so the operator's
            # next move is obvious.
            self._refresh_per_feature_action_buttons(data["feature_row"])

    def _refresh_per_feature_action_buttons(
        self, row: "_FeatureRow"
    ) -> None:
        """Show/hide the per-feature action buttons based on the
        selected feature's lifecycle state.

        State → visible buttons:
          - in_design → Promote to Designed
          - designed → Queue
          - queued → Un-queue
          - in_progress → Mark Ready, Re-design (escape hatches when
            M8 budget-aborted or operator wants to abandon impl)
          - ready_for_review → Verify, Reject
          - proposed / verified / rejected → none

        Promote-to-Designed is restricted to in_design because
        ``in_design → designed`` is the only direct path to
        designed in LEGAL_TRANSITIONS. (proposed → designed isn't
        legal; proposed must first go through in_design.)

        Buttons that don't apply are hidden via ``display = False``
        rather than disabled so the row stays uncluttered. The
        operator's next legal move is the only thing visible.
        """
        try:
            promote_btn = self.query_one(
                "#feature-action-promote-designed", Button
            )
            queue_btn = self.query_one("#feature-action-queue", Button)
            unqueue_btn = self.query_one(
                "#feature-action-unqueue", Button
            )
            mark_ready_btn = self.query_one(
                "#feature-action-mark-ready", Button
            )
            redesign_btn = self.query_one(
                "#feature-action-redesign", Button
            )
            verify_btn = self.query_one(
                "#feature-action-verify", Button
            )
            reject_btn = self.query_one(
                "#feature-action-reject", Button
            )
        except Exception:  # noqa: BLE001 — pre-mount race
            return

        state = row.state
        promote_btn.display = state == FeatureState.IN_DESIGN
        queue_btn.display = state == FeatureState.DESIGNED
        unqueue_btn.display = state == FeatureState.QUEUED
        mark_ready_btn.display = state == FeatureState.IN_PROGRESS
        redesign_btn.display = state == FeatureState.IN_PROGRESS
        verify_btn.display = state == FeatureState.READY_FOR_REVIEW
        reject_btn.display = state == FeatureState.READY_FOR_REVIEW

    # ------------------------------------------------------------------ #
    # Artifacts tab (T83)
    # ------------------------------------------------------------------ #

    # Folders inside .wonderland/ that hold operator-readable artifacts.
    # Anything else (memory/, telemetry/) is system state — out of
    # scope for this browser. Order matches typical workflow phase
    # output (features first, then contracts, then implementation,
    # then escalations + reviews).
    _ARTIFACT_DIRS: tuple[tuple[str, str], ...] = (
        ("features", "Features"),
        ("contract-notes", "Contracts"),
        ("test-scenarios", "Test scenarios"),
        ("stories", "Stories"),
        ("tickets", "Tickets"),
        ("architecture", "Architecture"),
        ("rulings", "Rulings"),
        ("observations", "Observations"),
        ("implementations", "Implementations"),
        ("escalations", "Escalations"),
    )

    def _compose_artifacts_tab(self) -> ComposeResult:
        with Horizontal(id="artifacts-tab-row"):
            with Vertical(id="artifacts-list-pane"):
                yield Static(
                    "[b]Artifacts[/b] [dim](.wonderland/ contents)[/dim]",
                    id="artifacts-list-label",
                )
                yield DataTable(id="artifacts-table", cursor_type="row")
            with Vertical(id="artifacts-detail-pane"):
                yield Static(
                    "[b]Artifact content[/b]",
                    id="artifacts-detail-label",
                )
                with VerticalScroll(id="artifacts-detail-scroll"):
                    yield Static(
                        "[dim](no artifact selected)[/dim]",
                        id="artifacts-detail",
                    )

    def _populate_artifacts(self) -> None:
        table = self.query_one("#artifacts-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Kind", "Name", "Modified")
        self._artifacts = self._discover_artifacts()
        if not self._artifacts:
            detail = self.query_one("#artifacts-detail", Static)
            detail.update(
                "[b yellow]No artifacts yet.[/b yellow]\n\n"
                "Once a run completes, the team's artifacts (features, "
                "contracts, test scenarios, escalations, etc.) will "
                "land in this project's [b].wonderland/[/b] directory "
                "and become browseable here.\n\n"
                "[dim]Memory + telemetry directories are excluded — "
                "this view is for human-readable artifacts only.[/dim]"
            )
            return
        for kind_label, path in self._artifacts:
            mtime = datetime.fromtimestamp(
                path.stat().st_mtime, tz=timezone.utc
            )
            table.add_row(
                kind_label,
                path.name,
                mtime.strftime("%Y-%m-%d %H:%M"),
            )
        table.cursor_coordinate = (0, 0)
        self._render_artifact_content(self._artifacts[0])

    def _discover_artifacts(self) -> list[tuple[str, Path]]:
        """Walk the documented .wonderland/ subdirs and collect any
        markdown/text files. Returns a flat list ordered by
        (directory-priority, mtime-desc) so most-recent-first within
        each kind."""
        wd = self.project.root_path / ".wonderland"
        out: list[tuple[str, Path]] = []
        if not wd.is_dir():
            return out
        for dirname, label in self._ARTIFACT_DIRS:
            subdir = wd / dirname
            if not subdir.is_dir():
                continue
            files = sorted(
                (p for p in subdir.iterdir() if p.is_file()),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            for path in files:
                out.append((label, path))
        return out

    def _render_artifact_content(self, entry: tuple[str, Path]) -> None:
        _label, path = entry
        detail = self.query_one("#artifacts-detail", Static)
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            detail.update(f"[red]Failed to read {path.name}: {exc}[/red]")
            return
        # Truncate at 50K chars to keep the render snappy on very
        # large escalations or ADRs. Operators with bigger artifacts
        # can open them externally.
        if len(text) > 50_000:
            text = (
                text[:50_000]
                + "\n\n[dim]…(truncated; "
                f"{len(text) - 50_000} more chars on disk; open externally)[/dim]"
            )
        detail.update(text)

    # ------------------------------------------------------------------ #
    # Metrics tab (T82)
    # ------------------------------------------------------------------ #

    def _compose_metrics_tab(self) -> ComposeResult:
        with VerticalScroll(id="metrics-scroll"):
            yield Static(
                "[dim](no runs yet — metrics need at least one "
                "completed run)[/dim]",
                id="metrics-content",
            )

    @staticmethod
    def _strip_ansi(text: str) -> str:
        """Strip ANSI escape sequences from plotext output. Textual's
        Rich-markup parser treats bracketed ANSI codes (e.g. ``[0m``)
        as markup tags and chokes on them. Plotext doesn't have a
        no-color flag we can flip globally, so we sanitize on the
        way out. Colors get dropped; chart shape survives."""
        import re

        ansi_re = re.compile(r"\x1b\[[0-9;]*m")
        return ansi_re.sub("", text)

    def _populate_metrics(self) -> None:
        """Render the metrics view: a stack of plotext-rendered
        ASCII charts, computed from the same RunRecord set the Runs
        tab uses. Plotext writes ANSI; we strip the color codes since
        Static renders via Rich and bracketed ANSI sequences trip the
        markup parser."""
        content = self.query_one("#metrics-content", Static)
        if not self._runs:
            content.update(
                "[b yellow]No runs yet — metrics will populate after the "
                "first run completes.[/b yellow]\n\n"
                "[dim]Tracked metrics: cumulative cost, per-agent cost "
                "share, wall-clock per run, tool-call distribution, "
                "outcome counts, cache-hit-rate trend.[/dim]"
            )
            return

        import plotext as plt
        import json as _json

        sections: list[str] = []

        # --- Headline summary ---
        n_runs = len(self._runs)
        total_spend = sum(r.total_cost for r in self._runs)
        total_calls = sum(r.total_calls for r in self._runs)
        outcomes = {}
        for r in self._runs:
            o = r.outcome or "unknown"
            outcomes[o] = outcomes.get(o, 0) + 1
        outcome_summary = ", ".join(
            f"{count} {name}" for name, count in sorted(outcomes.items())
        )
        sections.append(
            f"[b]Project totals[/b]\n"
            f"  Runs: {n_runs}    Spend: ${total_spend:.2f}    "
            f"Calls: {total_calls:,}    Outcomes: {outcome_summary}\n"
        )

        # --- Cost per run (chronological) ---
        sorted_runs = sorted(
            self._runs,
            key=lambda r: r.started_at or datetime.min.replace(tzinfo=timezone.utc),
        )
        cost_y = [r.total_cost for r in sorted_runs]
        budget_y = [r.budget_dollars or 0 for r in sorted_runs]
        # Plotext autodetects strings that look like dates and tries
        # to parse them — run_ids in YYYYMMDDTHHMMSS format trip the
        # parser. Use 1-indexed labels for the x-axis; legend below
        # ties index → run_id for the operator.
        x_indices = list(range(1, len(sorted_runs) + 1))
        plt.clear_figure()
        plt.theme("clear")
        plt.plot_size(width=72, height=12)
        plt.title("Cost per run (vs. budget cap)")
        plt.bar(x_indices, cost_y, marker="hd", label="cost")
        plt.plot(x_indices, budget_y, marker="braille", label="budget")
        plt.xlabel("run")
        plt.ylabel("$")
        cost_chart = self._strip_ansi(plt.build())
        run_legend = "  ".join(
            f"[dim]{i}[/dim]={r.run_id}"
            for i, r in zip(x_indices, sorted_runs, strict=True)
        )
        sections.append(
            f"[b]Cost per run[/b]\n{cost_chart}\n[dim]Legend:[/dim] {run_legend}"
        )

        # --- Wall-clock per run ---
        wallclock_minutes = [
            (r.elapsed_seconds or 0) / 60 for r in sorted_runs
        ]
        plt.clear_figure()
        plt.theme("clear")
        plt.plot_size(width=72, height=10)
        plt.title("Wall-clock per run (minutes)")
        plt.bar(x_indices, wallclock_minutes, marker="hd")
        plt.xlabel("run")
        plt.ylabel("minutes")
        sections.append("[b]Wall-clock[/b]\n" + self._strip_ansi(plt.build()))

        # --- Per-agent cost (averaged across runs) ---
        agent_totals: dict[str, float] = {}
        for record in self._runs:
            try:
                with record.telemetry_path.open(encoding="utf-8") as f:
                    data = _json.load(f)
            except (OSError, _json.JSONDecodeError):
                continue
            per_agent = data.get("per_agent") or {}
            for name, agent_data in per_agent.items():
                if not isinstance(agent_data, dict):
                    continue
                agent_totals[name] = (
                    agent_totals.get(name, 0.0)
                    + float(agent_data.get("cost", 0.0))
                )
        if agent_totals:
            # Order by canonical cast order so the chart reads
            # consistently across projects.
            ordered = sorted(
                agent_totals.items(),
                key=lambda kv: ({n: i for i, n in enumerate(_AGENT_KEYS)}.get(
                    kv[0], 999
                ), kv[0]),
            )
            agents = [name for name, _ in ordered]
            costs = [cost for _, cost in ordered]
            plt.clear_figure()
            plt.theme("clear")
            plt.plot_size(width=72, height=12)
            plt.title("Total cost by agent (across all runs)")
            plt.bar(agents, costs, marker="hd", orientation="horizontal")
            plt.xlabel("$")
            sections.append("[b]Per-agent cost[/b]\n" + self._strip_ansi(plt.build()))

        # --- Outcome distribution ---
        if outcomes:
            outcome_names = list(sorted(outcomes.keys()))
            outcome_counts = [outcomes[n] for n in outcome_names]
            plt.clear_figure()
            plt.theme("clear")
            plt.plot_size(width=60, height=8)
            plt.title("Run outcomes")
            plt.bar(outcome_names, outcome_counts, marker="hd")
            plt.xlabel("outcome")
            plt.ylabel("count")
            sections.append("[b]Outcomes[/b]\n" + self._strip_ansi(plt.build()))

        content.update("\n\n".join(sections))

    # ------------------------------------------------------------------ #
    # Files tab (T81)
    # ------------------------------------------------------------------ #

    def _compose_files_tab(self) -> ComposeResult:
        with Horizontal(id="files-tab-row"):
            with Vertical(id="files-tree-pane"):
                yield Static("[b]Project tree[/b]", id="files-tree-label")
                yield _FilteredDirectoryTree(
                    str(self.project.root_path), id="files-tree"
                )
            with Vertical(id="files-detail-pane"):
                yield Static(
                    "[b]File content[/b]",
                    id="files-detail-label",
                )
                with VerticalScroll(id="files-detail-scroll"):
                    yield Static(
                        "[dim](no file selected)[/dim]",
                        id="files-detail",
                    )

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """File picked in the Files tab — render its contents in the
        right pane. Skips reads that would be too big or non-textual."""
        path = event.path
        detail = self.query_one("#files-detail", Static)
        try:
            size = path.stat().st_size
        except OSError as exc:
            detail.update(f"[red]stat failed: {exc}[/red]")
            return
        if size > _FILE_VIEWER_MAX_BYTES:
            detail.update(
                f"[yellow]File too large to preview[/yellow] "
                f"({size:,} bytes; cap is {_FILE_VIEWER_MAX_BYTES:,}).\n\n"
                f"[dim]Open externally:[/dim]\n  $ $EDITOR {path}"
            )
            return
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            detail.update(f"[red]Read failed: {exc}[/red]")
            return
        # Heuristic: if the first 4KB has too many NUL/control bytes,
        # treat as binary and refuse to render the body.
        head = text[:4096]
        ctrl_chars = sum(
            1 for c in head if ord(c) < 32 and c not in ("\n", "\r", "\t")
        )
        if ctrl_chars > 32:
            detail.update(
                f"[yellow]Binary file — preview suppressed[/yellow] "
                f"({size:,} bytes).\n\n"
                f"[dim]Open externally:[/dim]\n  $ $EDITOR {path}"
            )
            return
        # Header summary so the operator knows where they are without
        # peering at the breadcrumb in the tree pane.
        try:
            rel = path.relative_to(self.project.root_path)
        except ValueError:
            rel = path
        header = f"[b]{rel}[/b] [dim]({size:,} bytes)[/dim]\n"
        detail.update(header + "\n" + text)

    # ------------------------------------------------------------------ #
    # Features primary surface
    # ------------------------------------------------------------------ #

    def _load_features(self) -> list[_FeatureRow]:
        """Read all features from the project's registry, attach
        their current lifecycle state. Best-effort — missing
        registry returns empty list.

        Back-fill: features that exist on disk but have no transition
        log entry (typically pre-T85 projects, but also any feature
        emitted before lifecycle wiring caught it) get recorded as
        ``designed`` via back_fill_state. Most accurate default for
        the typical case — features came out of M2.5 with contracts
        + scenarios, fully designed but not yet operator-touched.
        Operator can then queue / verify normally.
        """
        from wonderland.feature_lifecycle import back_fill_state

        try:
            from wonderland.feature import FeatureRegistry

            records = FeatureRegistry(self.project.root_path).list_features()
        except Exception:  # noqa: BLE001
            return []
        out: list[_FeatureRow] = []
        for rec in records:
            state = get_feature_state(self.project.root_path, rec.slug)
            if state is None:
                # Pre-T85 feature without lifecycle record. Back-fill
                # as designed — operator can queue / verify from there.
                try:
                    back_fill_state(
                        self.project.root_path,
                        rec.slug,
                        FeatureState.DESIGNED,
                        notes=(
                            "Back-filled from pre-T85 feature on disk "
                            "(no transition log)"
                        ),
                    )
                    state = FeatureState.DESIGNED
                except Exception:  # noqa: BLE001
                    # If back-fill fails for any reason, leave state
                    # as None and let the operator deal with it; the
                    # dashboard renders ?-badge for None.
                    pass
            # Parse `**Kind:** <kind>` from the markdown. Best-effort:
            # missing field → default to capability (matches the
            # FeaturePayload default + back-compat with pre-kind
            # features on disk).
            kind = "capability"
            try:
                body = rec.path.read_text(encoding="utf-8")
                for line in body.splitlines():
                    if line.startswith("**Kind:**"):
                        kind = line.split("**Kind:**", 1)[1].strip()
                        break
            except OSError:
                pass
            out.append(
                _FeatureRow(
                    slug=rec.slug,
                    title=rec.title,
                    state=state,
                    path=rec.path,
                    kind=kind,
                )
            )
        # Sort: active states first (designed/queued/in_progress/
        # ready_review), then proposed/in_design, then terminal
        # (verified/rejected). Within each tier, alphabetical by slug.
        priority = {
            FeatureState.READY_FOR_REVIEW: 0,
            FeatureState.QUEUED: 1,
            FeatureState.DESIGNED: 2,
            FeatureState.IN_PROGRESS: 3,
            FeatureState.IN_DESIGN: 4,
            FeatureState.PROPOSED: 5,
            FeatureState.VERIFIED: 6,
            FeatureState.REJECTED: 7,
            None: 8,
        }
        out.sort(key=lambda r: (priority.get(r.state, 99), r.slug))
        return out

    def _refresh_action_buttons(self) -> None:
        """T92: update the actions pane based on current feature
        lifecycle distribution. Counts features per state, sets
        button labels with counts, disables buttons whose target
        state has zero features, and assigns variant=primary to the
        highest-priority actionable button.

        Priority order: verify > implement > design. The design
        button is the always-on baseline (you can always make more
        features); it gets primary variant only when no other
        actions have features waiting."""
        counts: dict[FeatureState, int] = {state: 0 for state in FeatureState}
        for f in self._features:
            if f.state is not None:
                counts[f.state] = counts.get(f.state, 0) + 1

        try:
            design_btn = self.query_one("#action-design", Button)
            implement_btn = self.query_one("#action-implement", Button)
            verify_btn = self.query_one("#action-verify-ready", Button)
            custom_btn = self.query_one("#action-custom-run", Button)
        except Exception:  # noqa: BLE001 — pre-mount race; refresh fires later
            return

        n_queued = counts.get(FeatureState.QUEUED, 0)
        n_ready = counts.get(FeatureState.READY_FOR_REVIEW, 0)

        # Update labels with current counts.
        implement_btn.label = f"▶ Implement {n_queued} queued"
        verify_btn.label = f"▶ Verify {n_ready} ready"

        # Disable empty-target buttons. Textual's Button.disabled
        # greys out the button + blocks click events.
        implement_btn.disabled = n_queued == 0
        verify_btn.disabled = n_ready == 0

        # Primary variant assignment — exactly one button gets the
        # primary spotlight. Priority: verify > implement > design.
        # Custom-run never gets primary; it's the escape hatch.
        if n_ready > 0:
            primary_id = "action-verify-ready"
        elif n_queued > 0:
            primary_id = "action-implement"
        else:
            primary_id = "action-design"

        for btn in (design_btn, implement_btn, verify_btn, custom_btn):
            if btn.id == primary_id:
                btn.variant = "primary"
            else:
                btn.variant = "default"

    def _action_run_design(self) -> None:
        """Push NewRunScreen with project context + tdd-design pre-
        selected. Design runs are cheap (~$3); operator can iterate
        the design loop several times before committing
        implementation budget. Operator writes their own directive —
        design needs the operator's framing of what they want
        designed."""
        from wonderland.tui.screens.new_run import NewRunScreen

        self.app.push_screen(
            NewRunScreen(
                project=self.project,
                default_workflow="tdd-design",
            )
        )

    def _action_run_implement(self) -> None:
        """Push NewRunScreen with project context + tdd-implement
        pre-selected + a boilerplate directive. Operator can edit
        the directive (e.g. to add focus like 'prioritize the Plaid
        integration'), or just hit Go — the team works from seeded
        lifecycle artifacts (features, tickets, contracts on disk),
        so the directive text isn't load-bearing."""
        from wonderland.tui.screens.new_run import NewRunScreen

        n_queued = sum(
            1 for f in self._features if f.state == FeatureState.QUEUED
        )
        directive = (
            f"Implement the {n_queued} queued feature(s) per their "
            f"existing tickets and contracts. The team works from "
            f"seeded lifecycle artifacts; this directive is a "
            f"placeholder — edit to add focus if useful."
        )
        self.app.push_screen(
            NewRunScreen(
                project=self.project,
                default_workflow="tdd-implement",
                default_directive=directive,
            )
        )

    def _action_verify_first_ready(self) -> None:
        """Move cursor to the first ready_for_review feature and open
        the verify modal. Operator can verify or reject; on dismiss,
        action_refresh re-counts so the button updates if there are
        more rfr features queued."""
        # Find the first ready_for_review feature in display order
        # (which is sort-priority sorted, so rfr is near the top).
        target_row: _FeatureRow | None = None
        visible = [
            r for r in self._features
            if self._filter is None or r.state == self._filter
        ]
        for row in visible:
            if row.state == FeatureState.READY_FOR_REVIEW:
                target_row = row
                break
        if target_row is None:
            self.notify(
                "No ready_for_review features. State changed — "
                "refresh and try again.",
                severity="warning",
            )
            return
        try:
            tree = self.query_one("#features-tree", Tree)
            tree.focus()
            # Find the matching feature node and move cursor to it.
            for node in tree.root.children:
                if (
                    node.data is not None
                    and node.data.get("kind") == "feature"
                    and node.data["row"].slug == target_row.slug
                ):
                    tree.select_node(node)
                    break
        except Exception:  # noqa: BLE001
            pass
        # Open the verify modal directly — operator's intent at this
        # action is "verify the first ready feature."
        self._open_verify_modal("verify")

    def _action_custom_run(self) -> None:
        """Escape hatch — operator wants a workflow not in the typical
        design/implement loop (smoke, canonical, dev variants, etc.).
        Pushes NewRunScreen with project context but no hint."""
        from wonderland.tui.screens.new_run import NewRunScreen

        self.app.push_screen(NewRunScreen(project=self.project))

    def _populate_features(self) -> None:
        tree = self.query_one("#features-tree", Tree)
        tree.clear()
        tree.show_root = False  # the pane label "Features" is enough
        self._features = self._load_features()
        # T92: refresh the actions pane every time the features list
        # changes so button state (counts, primary variant, disabled
        # flags) tracks reality.
        self._refresh_action_buttons()
        visible = [
            r for r in self._features
            if self._filter is None or r.state == self._filter
        ]
        if not visible:
            self._render_features_empty_state()
            return

        # feature_slug → list[TicketRecord]. Built from each ticket's
        # Sources field (option-1 source-of-truth from the slug-
        # mismatch fix in analysis 040 vintage).
        feature_to_tickets = self._load_ticket_tree()

        for row in visible:
            badge = _STATE_BADGE.get(row.state, "[dim]?[/dim]")
            title = row.title[:60] + ("…" if len(row.title) > 60 else "")
            # Foundation features get a small inline tag so plumbing
            # work is visually distinct from user-facing capabilities
            # in the same Features tab. Capabilities render unadorned.
            kind_tag = (
                "  [magenta]\\[fdn][/magenta]"
                if row.kind == "foundation"
                else ""
            )
            label = (
                f"{badge}  [b]{title}[/b]{kind_tag}  "
                f"[dim]{row.slug}[/dim]"
            )
            node = tree.root.add(
                label,
                data={"kind": "feature", "row": row},
                expand=True,
            )
            for ticket in feature_to_tickets.get(row.slug, []):
                ticket_title = ticket.title[:55] + (
                    "…" if len(ticket.title) > 55 else ""
                )
                # Marked tickets render with a red ✗ prefix +
                # strikethrough so the operator can scan the tree
                # and see what's queued for deletion before
                # confirming. Unmarked uses the standard dim bullet.
                if ticket.slug in self._marked_ticket_slugs:
                    ticket_label = (
                        f"[red]✗[/red] [strike]{ticket_title}[/strike]  "
                        f"[dim]{ticket.slug}[/dim]"
                    )
                else:
                    ticket_label = (
                        f"[dim]·[/dim] {ticket_title}  "
                        f"[dim]{ticket.slug}[/dim]"
                    )
                node.add_leaf(
                    ticket_label,
                    data={
                        "kind": "ticket",
                        "record": ticket,
                        "feature_row": row,
                    },
                )

        # Land cursor on the first feature + render its detail so the
        # right pane isn't empty on initial mount.
        if tree.root.children:
            tree.cursor_line = 0
        self._render_feature_detail(visible[0])

    def _load_ticket_tree(self) -> dict[str, list]:
        """Map each feature slug → list of TicketRecord that name it
        as their parent (via the ticket's Sources field). Returns
        empty dict on any I/O / registry error so the tree can still
        render features as leaf-only nodes."""
        try:
            from wonderland.ticket import TicketRegistry
            from wonderland.workflow import _ticket_to_feature_map
        except Exception:  # noqa: BLE001
            return {}
        try:
            records = TicketRegistry(
                self.project.root_path
            ).list_tickets()
            ticket_to_feature = _ticket_to_feature_map(
                self.project.root_path
            )
        except Exception:  # noqa: BLE001
            return {}
        out: dict[str, list] = {}
        for rec in records:
            feature_slug = ticket_to_feature.get(rec.slug)
            if feature_slug is None:
                continue
            out.setdefault(feature_slug, []).append(rec)
        # Sort tickets within each feature by ticket number for a
        # stable, human-readable order.
        for feature_slug in out:
            out[feature_slug].sort(key=lambda r: r.number)
        return out

    def _render_features_empty_state(self) -> None:
        detail = self.query_one("#features-detail", Static)
        if not self._features:
            detail.update(
                "[b yellow]No features yet for this project.[/b yellow]\n\n"
                "Run [b]tdd-design[/b] (or [b]tdd-serial-phased[/b] for the "
                "all-in-one) and Rabbit will produce features in M2.\n\n"
                "[dim]After at least one design run completes, the features "
                "will surface here with state badges showing where each one "
                "is in the lifecycle.[/dim]"
            )
        else:
            filter_label = (
                self._filter.value if self._filter else "all"
            )
            detail.update(
                f"[dim]No features in state '[b]{filter_label}[/b]'. "
                f"({len(self._features)} total — try a different filter.)[/dim]"
            )

    def _render_feature_detail(self, row: _FeatureRow) -> None:
        detail = self.query_one("#features-detail", Static)
        try:
            body = row.path.read_text(encoding="utf-8")
        except OSError as exc:
            detail.update(f"[red]Read failed: {exc}[/red]")
            return
        badge = _STATE_BADGE.get(row.state, "[dim]?[/dim]")
        header = f"[b]{row.title}[/b]   {badge}\n[dim]{row.slug}[/dim]\n\n"
        detail.update(header + body)

    def _render_ticket_detail(
        self, record, feature_row: _FeatureRow
    ) -> None:
        """Render a ticket's markdown in the detail pane with a
        header naming the parent feature. Same shape as the feature
        detail render so the operator's eye doesn't have to retrain
        when moving between feature and ticket nodes."""
        detail = self.query_one("#features-detail", Static)
        try:
            body = record.path.read_text(encoding="utf-8")
        except OSError as exc:
            detail.update(f"[red]Read failed: {exc}[/red]")
            return
        badge = _STATE_BADGE.get(feature_row.state, "[dim]?[/dim]")
        header = (
            f"[b]Ticket — {record.title}[/b]\n"
            f"[dim]{record.slug}[/dim]\n"
            f"Parent feature: [dim]{feature_row.slug}[/dim]   {badge}\n\n"
        )
        detail.update(header + body)

    def _filter_state_for(self, button_id: str) -> FeatureState | None:
        for chip_id, _label, state in _FILTER_CHIPS:
            if chip_id == button_id:
                return state
        return None

    def _set_filter(self, state: FeatureState | None) -> None:
        self._filter = state
        # Update chip styling: 'filter-active' class on the chip that
        # matches the new filter, removed from others.
        active_id = next(
            (chip_id for chip_id, _l, s in _FILTER_CHIPS if s == state),
            "filter-all",
        )
        for chip_id, _label, _state in _FILTER_CHIPS:
            try:
                btn = self.query_one(f"#{chip_id}", Button)
            except Exception:  # noqa: BLE001
                continue
            if chip_id == active_id:
                btn.add_class("filter-active")
            else:
                btn.remove_class("filter-active")
        self._populate_features()

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def on_mount(self) -> None:
        self._populate_features()
        self._populate_runs()
        self._populate_artifacts()
        self._populate_metrics()
        # Land focus on the features tree — primary attention surface.
        try:
            self.query_one("#features-tree", Tree).focus()
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_new_run(self) -> None:
        """Launch a new run with this project's context — pushes
        NewRunScreen with project= prefilled. Reached from the
        dashboard's actions pane (button) and from the 'n' keybind.
        """
        from wonderland.tui.screens.new_run import NewRunScreen

        self.app.push_screen(NewRunScreen(project=self.project))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid is None:
            return
        # T92 actions pane — state-aware dispatch.
        if bid == "action-design":
            self._action_run_design()
        elif bid == "action-implement":
            self._action_run_implement()
        elif bid == "action-verify-ready":
            self._action_verify_first_ready()
        elif bid == "action-custom-run":
            self._action_custom_run()
        elif bid == "dashboard-new-run-button":
            # Legacy id from before T92 — keep handler so any test or
            # external trigger that still uses it works.
            self.action_new_run()
        elif bid.startswith("filter-"):
            # Filter chip — set the lifecycle-state filter and
            # re-populate the features list.
            state = self._filter_state_for(bid)
            self._set_filter(state)
        elif bid.startswith("feature-action-"):
            # Per-feature actions. T90 wires verify/reject to actually
            # transition state + capture notes; queue/un-queue work
            # via direct lifecycle.transition() since they don't need
            # operator notes. For now, queue/un-queue ship; verify
            # and reject notify "T90 wires this" so the buttons exist
            # but the verify-with-notes flow ships in its own task.
            self._handle_feature_action(bid)

    def _handle_feature_action(self, button_id: str) -> None:
        """Per-feature action button dispatch. Queue / Un-queue ship
        now (single-step transitions, no operator notes needed).
        Verify / Reject defer to T90 which adds the notes-modal."""
        from wonderland.feature_lifecycle import (
            IllegalTransitionError,
            transition,
        )

        row = self._currently_highlighted_feature()
        if row is None:
            self.notify("No feature selected.", severity="warning")
            return

        if button_id == "feature-action-promote-designed":
            try:
                transition(
                    self.project.root_path,
                    row.slug,
                    FeatureState.DESIGNED,
                    by="operator",
                    notes="Promoted from in_design via dashboard",
                )
                self.notify(
                    f"Promoted {row.slug} to designed — queue it next."
                )
                self.action_refresh()
            except IllegalTransitionError as exc:
                self.notify(
                    f"Can't promote: {exc}", severity="warning"
                )
        elif button_id == "feature-action-queue":
            try:
                transition(
                    self.project.root_path,
                    row.slug,
                    FeatureState.QUEUED,
                    by="operator",
                )
                self.notify(
                    f"Queued {row.slug} for next implementation run."
                )
                self.action_refresh()
            except IllegalTransitionError as exc:
                self.notify(f"Can't queue: {exc}", severity="warning")
        elif button_id == "feature-action-unqueue":
            try:
                transition(
                    self.project.root_path,
                    row.slug,
                    FeatureState.DESIGNED,
                    by="operator",
                    notes="Un-queued",
                )
                self.notify(f"Un-queued {row.slug}.")
                self.action_refresh()
            except IllegalTransitionError as exc:
                self.notify(f"Can't un-queue: {exc}", severity="warning")
        elif button_id == "feature-action-mark-ready":
            try:
                transition(
                    self.project.root_path,
                    row.slug,
                    FeatureState.READY_FOR_REVIEW,
                    by="operator",
                    notes=(
                        "Manually marked ready_for_review from "
                        "in_progress via dashboard "
                        "(M8 didn't auto-transition — likely "
                        "budget-aborted post-verdict)"
                    ),
                )
                self.notify(
                    f"Marked {row.slug} ready_for_review — "
                    f"verify or reject when ready."
                )
                self.action_refresh()
            except IllegalTransitionError as exc:
                self.notify(
                    f"Can't mark ready: {exc}", severity="warning"
                )
        elif button_id == "feature-action-redesign":
            try:
                transition(
                    self.project.root_path,
                    row.slug,
                    FeatureState.DESIGNED,
                    by="operator",
                    notes=(
                        "Aborted in_progress; sent back to designed "
                        "via dashboard (operator wants to re-run "
                        "design phase)"
                    ),
                )
                self.notify(
                    f"Sent {row.slug} back to designed — "
                    f"re-run tdd-design or queue again."
                )
                self.action_refresh()
            except IllegalTransitionError as exc:
                self.notify(
                    f"Can't re-design: {exc}", severity="warning"
                )
        elif button_id == "feature-action-verify":
            self._open_verify_modal("verify")
        elif button_id == "feature-action-reject":
            self._open_verify_modal("reject")

    def _open_verify_modal(self, mode: str) -> None:
        """Push the verify/reject modal for the highlighted feature.
        Guards: feature must be selected AND in ready_for_review
        state. Both branches surface a useful warning notify if the
        guards fail."""
        from wonderland.tui.screens.verify_modal import (
            VerifyRejectModal,
        )

        row = self._currently_highlighted_feature()
        if row is None:
            self.notify("No feature selected.", severity="warning")
            return
        if row.state != FeatureState.READY_FOR_REVIEW:
            current = row.state.value if row.state else "(no state)"
            self.notify(
                f"Can only {mode} features in 'ready_for_review' "
                f"state. {row.slug!r} is currently {current!r}.",
                severity="warning",
                timeout=6,
            )
            return
        self.app.push_screen(
            VerifyRejectModal(
                feature_slug=row.slug,
                feature_title=row.title,
                mode=mode,  # type: ignore[arg-type]
            ),
            self._on_verify_modal_done,
        )

    def _on_verify_modal_done(
        self, result: tuple[FeatureState, str] | None
    ) -> None:
        """Callback for the verify/reject modal. Dismiss returned
        either (target_state, notes) on submit or None on cancel."""
        if result is None:
            return
        from wonderland.feature_lifecycle import (
            IllegalTransitionError,
            transition,
        )

        target_state, notes = result
        # Highlighted row is what the modal acted on — re-resolve to
        # be safe (cursor might have moved between the modal push
        # and dismiss; rare but possible if the user navigated mid-
        # modal somehow).
        row = self._currently_highlighted_feature()
        if row is None:
            self.notify(
                "Lost feature reference; refresh and try again.",
                severity="error",
            )
            return
        try:
            transition(
                self.project.root_path,
                row.slug,
                target_state,
                by="operator",
                notes=notes if notes else None,
            )
        except IllegalTransitionError as exc:
            self.notify(f"Transition failed: {exc}", severity="error")
            return
        verb = "verified" if target_state == FeatureState.VERIFIED else "rejected"
        self.notify(f"{row.slug} {verb}.", timeout=4)
        self.action_refresh()

    def _currently_highlighted_feature(self) -> _FeatureRow | None:
        """Return the feature corresponding to the highlighted node
        in the features tree. When a ticket is highlighted, returns
        the parent feature — so action buttons (queue / verify /
        reject) operate on the feature even while the operator is
        scrolling around the ticket sub-tree."""
        try:
            tree = self.query_one("#features-tree", Tree)
        except Exception:  # noqa: BLE001
            return None
        node = tree.cursor_node
        if node is None or node.data is None:
            return None
        kind = node.data.get("kind")
        if kind == "feature":
            return node.data["row"]
        if kind == "ticket":
            return node.data["feature_row"]
        return None

    def action_refresh(self) -> None:
        self._populate_features()
        self._populate_runs()
        self._populate_artifacts()
        self._populate_metrics()

    def action_toggle_mark(self) -> None:
        """Toggle the highlighted ticket node's mark-for-deletion
        state. No-op when the cursor is on a feature node — only
        tickets are deletable from this UI (feature deletion would
        cascade through the lifecycle log + tickets, separate flow).
        """
        try:
            tree = self.query_one("#features-tree", Tree)
        except Exception:  # noqa: BLE001
            return
        node = tree.cursor_node
        if node is None or node.data is None:
            return
        if node.data.get("kind") != "ticket":
            self.notify(
                "Mark only applies to ticket nodes — move cursor "
                "to a ticket under a feature.",
                timeout=3,
            )
            return
        slug = node.data["record"].slug
        if slug in self._marked_ticket_slugs:
            self._marked_ticket_slugs.discard(slug)
            verb = "unmarked"
        else:
            self._marked_ticket_slugs.add(slug)
            verb = "marked for deletion"
        # Repaint the tree so the prefix changes immediately. Cheap
        # — features tree is small.
        self._populate_features()
        # Reposition cursor on the same ticket node so the operator
        # can keep marking siblings without losing their place.
        self._restore_tree_cursor_to_ticket(slug)
        self.notify(
            f"Ticket {slug} {verb}. {len(self._marked_ticket_slugs)} "
            f"total marked. Press D to delete.",
            timeout=2,
        )

    def action_prune_marked(self) -> None:
        """Open the prune-confirm modal listing marked tickets.
        On confirm, delete the files from disk, clear the mark set,
        refresh the tree."""
        if not self._marked_ticket_slugs:
            self.notify(
                "No tickets marked. Highlight a ticket node and "
                "press m to mark it for deletion.",
                timeout=4,
            )
            return
        # Build the (slug, title) list in tree-order so the modal's
        # list reads top-to-bottom matching what the operator sees.
        from wonderland.ticket import TicketRegistry

        try:
            records = TicketRegistry(self.project.root_path).list_tickets()
        except Exception:  # noqa: BLE001
            records = []
        marked_pairs: list[tuple[str, str]] = [
            (rec.slug, rec.title)
            for rec in records
            if rec.slug in self._marked_ticket_slugs
        ]

        from wonderland.tui.screens.ticket_prune_modal import TicketPruneModal

        def _on_close(confirmed: bool | None) -> None:
            if not confirmed:
                return
            self._execute_prune()

        self.app.push_screen(
            TicketPruneModal(marked_pairs), _on_close
        )

    def _execute_prune(self) -> None:
        """Delete the marked tickets from disk, clear the mark set,
        refresh the tree. Reports the success count."""
        from wonderland.ticket import TicketRegistry

        registry = TicketRegistry(self.project.root_path)
        deleted = 0
        failed: list[str] = []
        for slug in list(self._marked_ticket_slugs):
            if registry.delete_by_slug(slug):
                deleted += 1
            else:
                failed.append(slug)
        self._marked_ticket_slugs.clear()
        self._populate_features()
        if failed:
            self.notify(
                f"Deleted {deleted} ticket(s); {len(failed)} could "
                f"not be deleted ({', '.join(failed[:3])}...).",
                severity="warning",
                timeout=6,
            )
        else:
            self.notify(
                f"Deleted {deleted} ticket(s).", timeout=3
            )

    def _restore_tree_cursor_to_ticket(self, slug: str) -> None:
        """After a tree rebuild, walk the tree to find the ticket
        node whose data.record.slug matches and select it. Best-
        effort — no-op if not found (e.g., the ticket was deleted).
        """
        try:
            tree = self.query_one("#features-tree", Tree)
        except Exception:  # noqa: BLE001
            return
        for feature_node in tree.root.children:
            for child in feature_node.children:
                if (
                    child.data is not None
                    and child.data.get("kind") == "ticket"
                    and child.data["record"].slug == slug
                ):
                    tree.select_node(child)
                    return

    def action_show_runs(self) -> None:
        self.query_one("#dashboard-tabs", TabbedContent).active = "tab-runs"

    def action_show_artifacts(self) -> None:
        self.query_one("#dashboard-tabs", TabbedContent).active = (
            "tab-artifacts"
        )

    def action_show_files(self) -> None:
        self.query_one("#dashboard-tabs", TabbedContent).active = "tab-files"

    def action_show_metrics(self) -> None:
        self.query_one("#dashboard-tabs", TabbedContent).active = "tab-metrics"


__all__ = ["ProjectDashboardScreen"]
