"""ProjectDashboardScreen — per-project landing surface (P11 T79).

Shell for the in-depth project view. Operators reach this from
ProjectLibraryScreen by selecting a project and pressing the
dashboard binding (currently bound to a separate key — Enter
still launches a new run, since that's the higher-frequency action).

Layout:
  - Top: actions row (design / implement / verify / custom)
  - Middle: a content row split into two columns —
      * Runs column (left): list of runs (top) + run detail (below).
        Always visible so background runs can surface here without
        the operator hunting through a tab. Tees up P? where runs
        become background processes the operator can leave running
        across screens.
      * Features column (right): the operator's main attention
        surface — feature tree + dossier detail + per-feature
        action buttons.
  - Bottom: drill-down tabs (Artifacts / Files / Metrics) for
    investigation surfaces.

Lazygit-shape inside each split: list-then-detail; selection on
the left drives content on the right (or below, for the runs
column).
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


# Ticket-state badges rendered as tree-node prefixes. None /
# TicketState.PENDING render as the bare bullet ([dim]·) so the
# default no-record case stays visually quiet and only opinionated
# states (queued / in_progress / done / aborted) stand out.
_TICKET_STATE_BADGE: dict[object, str] = {
    None: "[dim]·[/dim]",
    # Lazy import inside the module avoids a top-level ImportError
    # when ticket_lifecycle hasn't been loaded yet (tests / pyright).
}


def _ticket_state_for(project_root, ticket_slug):
    """Wrap ``ticket_lifecycle.get_state`` with a try/except so
    pre-mount / missing-registry callers degrade to None cleanly."""
    try:
        from wonderland.ticket_lifecycle import get_state

        return get_state(project_root, ticket_slug)
    except Exception:  # noqa: BLE001
        return None


def _populate_ticket_badge_map() -> None:
    """Populate the ticket-state badge lookup. Called lazily so the
    enum-typed keys are only constructed if ticket_lifecycle is
    importable — preserves the dashboard's pre-substrate test
    surface."""
    try:
        from wonderland.ticket_lifecycle import TicketState
    except Exception:  # noqa: BLE001
        return
    _TICKET_STATE_BADGE.setdefault(
        TicketState.PENDING, "[dim]·[/dim]"
    )
    _TICKET_STATE_BADGE.setdefault(
        TicketState.QUEUED, "[yellow]▶[/yellow]"
    )
    _TICKET_STATE_BADGE.setdefault(
        TicketState.IN_PROGRESS, "[magenta]⟳[/magenta]"
    )
    _TICKET_STATE_BADGE.setdefault(
        TicketState.DONE, "[bright_green]✓[/bright_green]"
    )
    _TICKET_STATE_BADGE.setdefault(
        TicketState.ABORTED, "[red]⚠[/red]"
    )


_populate_ticket_badge_map()


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
        # Drill-down keybinds — Runs has its own column now (always
        # visible), so the tab keybinds only cover the remaining
        # investigation surfaces.
        Binding("1", "show_artifacts", "Artifacts", show=False),
        Binding("2", "show_files", "Files", show=False),
        Binding("3", "show_metrics", "Metrics", show=False),
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
        # P15 T-m5 — currently-selected milestone in the milestones
        # tree, or None when no milestone is selected (show all
        # features). When set, the features pane filters to features
        # whose sources cite a story realizing one of this
        # milestone's consumes_requirements (via T-m8b chain).
        self._selected_milestone_slug: str | None = None
        # Cached set of feature slugs that "belong to" the active
        # milestone via the realization chain. Recomputed when
        # milestone selection changes; None means "no scope active —
        # show all features".
        self._milestone_feature_scope: set[str] | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical(id="dashboard-root"):
            yield Static(
                f"[b]{self.project.name}[/b] · "
                f"[dim]{self.project.root_path}[/dim]",
                id="dashboard-header",
            )
            # P15 T-m8 UX — lifecycle phase + next-action hint.
            # Derived from disk every refresh so the operator
            # immediately sees what the project needs next without
            # interpreting feature-table state. The Static is
            # filled in by _refresh_phase_badge so unit tests +
            # later mounts can re-derive without re-composing.
            yield Static(
                "",
                id="dashboard-phase",
            )
            # Actions pane (T92) — quick-launch surface always
            # visible. Contextual CTAs inside the panes (T-m5) layer
            # on top: those guide phase-specific next-step actions
            # (discovery / milestone-plan / design); these stay for
            # ad-hoc operator-driven launches.
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

            # Top row: Milestones tree (left) + Features (right).
            # P15 T-m5: milestones become the primary navigation
            # surface; selecting a milestone filters the features
            # pane to features whose stories realize that
            # milestone's consumes_requirements. Empty-state CTAs
            # inside each pane drive the operator through the flow
            # (discovery → milestone-plan → tdd-design → tdd-implement).
            with Horizontal(id="top-row"):
                # Milestones pane: tree + empty-state CTA. The tree
                # shows one node per milestone (collapsible to its
                # consumes_requirements). When no requirements exist,
                # the pane shows a big "Run discovery" button instead.
                # When requirements exist but no milestones, "Run
                # milestone-plan". When milestones exist but
                # decomposable requirements are unassigned, a smaller
                # "Some requirements unplanned" hint sits above the
                # tree.
                # Milestones row: list (left) + detail (right) —
                # mirrors the Features row structure so the operator's
                # eye doesn't have to retrain when moving between
                # them. List = tree of milestones + collapsible
                # requirements + phase-aware CTA. Detail = highlighted
                # milestone's body, with the "Design this milestone"
                # button anchored at the bottom of the detail pane
                # so the read order is select → review → act.
                with Horizontal(id="milestones-row"):
                    with Vertical(id="milestones-list-pane"):
                        yield Static(
                            "[b]Milestones[/b]",
                            id="milestones-label",
                        )
                        yield Static(
                            "",
                            id="milestones-orphan-hint",
                        )
                        yield Tree(
                            "Milestones",
                            id="milestones-tree",
                        )
                        # Empty-state CTA — populated by
                        # _refresh_milestones_cta when no
                        # requirements or no milestones exist.
                        # Hidden otherwise.
                        yield Button(
                            "",
                            id="milestones-empty-cta",
                            variant="primary",
                        )
                    with Vertical(id="milestones-detail-pane"):
                        yield Static(
                            "[b]Milestone detail[/b]",
                            id="milestones-detail-label",
                        )
                        with VerticalScroll(
                            id="milestones-detail-scroll"
                        ):
                            yield Static(
                                "[dim](no milestone selected)[/dim]",
                                id="milestones-detail",
                            )
                        # P15 T-m5 — Design CTA at the bottom of
                        # the milestone detail pane. Hidden by
                        # default; surfaced by
                        # _refresh_milestone_design_cta when the
                        # highlighted milestone has zero realizing
                        # features. Click launches tdd-design
                        # --milestone <slug>.
                        yield Button(
                            "",
                            id="milestone-design-cta",
                            variant="primary",
                        )
                # Features primary surface — left list (with state
                # filter chips), right detail (dossier + per-feature
                # actions). The list narrows to the selected
                # milestone's features when one is picked in the
                # Milestones tree.
                with Horizontal(id="features-row"):
                    with Vertical(id="features-list-pane"):
                        yield Static(
                            "[b]Features[/b]", id="features-list-label"
                        )
                        with Horizontal(id="features-filter-row"):
                            for chip_id, label, _state in _FILTER_CHIPS:
                                classes = "filter-chip"
                                if _state is None:
                                    classes += " filter-active"
                                yield Button(
                                    label, id=chip_id, classes=classes
                                )
                        # Tree (not DataTable): each feature is a
                        # parent node; its tickets nest underneath
                        # like a file tree. Operator can highlight a
                        # ticket and see the same dossier shape as
                        # for features. Default expanded so tickets
                        # are immediately visible — typical project
                        # sizes (3-6 features × 1-4 tickets) fit fine.
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
                            # Promote → Designed shows when the
                            # selected feature is in_design (M5 didn't
                            # fully fire, or operator un-promoted
                            # earlier). Replaces queue/un-queue in
                            # that view since those transitions
                            # aren't legal from in_design.
                            yield Button(
                                "Promote to Designed",
                                id="feature-action-promote-designed",
                                variant="primary",
                            )
                            yield Button(
                                "Queue", id="feature-action-queue"
                            )
                            yield Button(
                                "Un-queue",
                                id="feature-action-unqueue",
                            )
                            # designed → in_design transition for the
                            # tdd-decompose workflow. Use case: feature
                            # got designed but its ticket set is wrong
                            # (zero tickets attributed, over-pruned in
                            # M3.5, or operator inspects and wants a
                            # redo). This button transitions the
                            # feature back to in_design; the operator
                            # then runs tdd-decompose, which iterates
                            # M3+M3.5 over features in in_design and
                            # transitions them back to designed with
                            # fresh tickets.
                            yield Button(
                                "Decompose tickets",
                                id="feature-action-decompose",
                                variant="warning",
                            )
                            # in_progress controls — escape hatches
                            # for features stuck mid-implementation.
                            # Mark Ready advances to ready_for_review
                            # (skip M8 and go straight to operator
                            # verify); Re-design aborts implementation
                            # and sends back to designed (operator
                            # wants to re-run design phase against new
                            # directive).
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
                            # Per-ticket queue controls — only
                            # visible when a ticket node is
                            # highlighted in the tree. The operator
                            # uses these to re-queue a single ticket
                            # after an iteration aborts on budget,
                            # without re-running the whole feature.
                            yield Button(
                                "Queue ticket",
                                id="ticket-action-queue",
                                variant="primary",
                            )
                            yield Button(
                                "Un-queue ticket",
                                id="ticket-action-unqueue",
                            )
                            yield Button(
                                "Mark done",
                                id="ticket-action-mark-done",
                                variant="success",
                            )

            # Bottom row: Runs list + detail. Sits below the
            # Milestones/Features row so the operator's primary
            # navigation surface is up top + run history is the
            # reference layer below. Always visible — preparation
            # for background runs the operator can leave going
            # while navigating other views.
            with Horizontal(id="runs-row"):
                with Vertical(id="runs-list-pane"):
                    yield Static(
                        "[b]Runs[/b]", id="runs-list-label"
                    )
                    yield DataTable(
                        id="runs-table", cursor_type="row"
                    )
                with Vertical(id="runs-detail-pane"):
                    yield Static(
                        "[b]Run detail[/b]", id="runs-detail-label"
                    )
                    with VerticalScroll(id="runs-detail-scroll"):
                        yield Static(
                            "[dim](no run selected)[/dim]",
                            id="runs-detail",
                        )

            # Drill-downs — investigation surfaces. Take less screen
            # real estate than the Features section; operator opens
            # them with 1/2/3 keybinds when investigating "why did
            # the team make this decision?" types of questions. Runs
            # is no longer a tab — it has its own always-visible
            # row above.
            yield Static(
                "[dim]Drill-downs · 1=Artifacts  2=Files  "
                "3=Metrics[/dim]",
                id="dashboard-drilldown-label",
            )
            with TabbedContent(id="dashboard-tabs"):
                with TabPane("Artifacts", id="tab-artifacts"):
                    yield from self._compose_artifacts_tab()
                with TabPane("Files", id="tab-files"):
                    yield from self._compose_files_tab()
                with TabPane("Metrics", id="tab-metrics"):
                    yield from self._compose_metrics_tab()
        yield Footer()

    # ------------------------------------------------------------------ #
    # Runs column (T80; reshaped P14 — runs is its own always-visible
    # column to the left of features rather than a drill-down tab,
    # in preparation for background runs the operator can leave
    # going across screen pushes/pops).
    # ------------------------------------------------------------------ #

    def _populate_runs(self) -> None:
        # Slim 3-column shape (Started / Cost / Outcome) tuned for
        # the narrow runs column. The full per-run breakdown — calls,
        # wall-clock, model, per-agent — lives in the detail pane
        # below the table; the table itself is for fast scanning of
        # recent activity. run_id is encoded in the Started timestamp
        # (YYYYMMDDTHHMMSS format), so showing both would be redundant.
        #
        # If there's an active background run not yet on disk
        # (telemetry only writes after meetings end), it gets a
        # synthetic top row so the operator can reattach via Enter.
        table = self.query_one("#runs-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Started", "Cost", "Outcome")
        self._runs = list_project_runs(self.project)

        # Slice B: active-run row. If the App is driving an in-flight
        # run, render it with a [live] badge ahead of historical
        # rows. Stored in self._active_row_present so on_data_table_
        # row_selected can branch to the reattach path instead of
        # constructing a HistoricalRunHandle.
        active = getattr(self.app, "_active_run", None)
        self._active_row_present = (
            active is not None and not active.is_terminal
        )
        if self._active_row_present:
            started_label = (
                active.started_at.strftime("%m-%d %H:%M")
                if active.started_at
                else "—"
            )
            table.add_row(
                started_label,
                "[dim]—[/dim]",
                "[bright_yellow]▶ live[/bright_yellow]",
            )

        if not self._runs and not self._active_row_present:
            self._render_runs_empty_state()
            return
        for record in self._runs:
            started = (
                record.started_at.strftime("%m-%d %H:%M")
                if record.started_at
                else "—"
            )
            table.add_row(
                started,
                _fmt_cost(record.total_cost),
                _fmt_outcome(record.outcome, record.budget_exceeded),
            )
        table.cursor_coordinate = (0, 0)
        if self._active_row_present:
            self._render_active_run_detail()
        elif self._runs:
            self._render_run_detail(self._runs[0])

    def _render_active_run_detail(self) -> None:
        """Detail-pane render for the synthetic active-run row.
        Brief — the rich detail is on LiveRunScreen which the
        operator opens via Enter."""
        detail = self.query_one("#runs-detail", Static)
        active = self.app._active_run  # type: ignore[attr-defined]
        if active is None:
            detail.update("[dim]No active run.[/dim]")
            return
        detail.update(
            f"[b bright_yellow]▶ Live run {active.run_id}[/b bright_yellow]\n"
            f"[dim]Started:[/dim] "
            f"{active.started_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            f"[dim]Status:[/dim] {active.status}\n"
            f"[dim]Buffered events:[/dim] {len(active.buffer)}\n\n"
            f"Press [b]Enter[/b] to attach to the live watch screen."
        )

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
            if row is None or row < 0:
                return
            # Synthetic active-row at index 0 when present.
            if self._active_row_present and row == 0:
                self._render_active_run_detail()
                return
            historical_idx = (
                row - 1 if self._active_row_present else row
            )
            if historical_idx >= len(self._runs):
                return
            self._render_run_detail(self._runs[historical_idx])
        elif event.data_table.id == "artifacts-table":
            row = event.cursor_row
            if row is None or row < 0 or row >= len(self._artifacts):
                return
            self._render_artifact_content(self._artifacts[row])

    def on_data_table_row_selected(
        self, event: DataTable.RowSelected
    ) -> None:
        """Enter on the runs table:
          - synthetic active-run row → reattach via LiveRunScreen
            with run_id, subscribing to the App's in-flight task.
          - historical row → open via HistoricalRunHandle
            (post-mortem replay).

        Both paths go through LiveRunScreen — same UI for the
        operator regardless of whether the run is live or finished.
        """
        if event.data_table.id != "runs-table":
            return
        row = event.cursor_row
        if row is None or row < 0:
            return
        if self._active_row_present and row == 0:
            self._reattach_to_active_run()
            return
        historical_idx = row - 1 if self._active_row_present else row
        if historical_idx >= len(self._runs):
            return
        record = self._runs[historical_idx]
        self._open_run_in_live_screen(record)

    def _discover_workflow_for_run(
        self, record: RunRecord
    ) -> str | None:
        """Best-effort lookup of the workflow used for ``record``.

        Sources, in priority order:
          1. ``.wonderland/runs/<run_id>/status.json`` — the
             background-run subprocess writes ``"workflow": "..."``
             when launching, so this is authoritative for any run
             produced by the detached path.
          2. The project's ``last_workflow`` — set by
             ``NewRunScreen._launch_run`` when the run kicks off.
             Drifts when the operator launches another run after
             the one being viewed, so it's only a fallback.

        Returns None when neither source resolves — HistoricalRun-
        Handle then falls through to the structural-extraction
        path for thread_ids and uses a generic ``Meeting``
        placeholder for unrecognised threads.
        """
        import json

        run_dir = (
            self.project.root_path
            / ".wonderland"
            / "runs"
            / record.run_id
        )
        status_path = run_dir / "status.json"
        if status_path.is_file():
            try:
                data = json.loads(
                    status_path.read_text(encoding="utf-8")
                )
                if isinstance(data, dict):
                    workflow = data.get("workflow")
                    if isinstance(workflow, str) and workflow:
                        return workflow
            except (OSError, json.JSONDecodeError):
                pass
        return self.project.last_workflow

    def _reattach_to_active_run(self) -> None:
        """Push LiveRunScreen targeting the App's in-flight run.
        The screen subscribes to the active run's event buffer
        + tail; the consumer task lives on the App and survives
        screen pops."""
        from wonderland.tui.screens.live_run import LiveRunScreen

        active = self.app._active_run  # type: ignore[attr-defined]
        if active is None:
            self.notify(
                "No active run to attach to (it may have just "
                "completed). Refresh and try again.",
                severity="warning",
            )
            return
        self.app.push_screen(LiveRunScreen(run_id=active.run_id))

    def _open_run_in_live_screen(self, record: RunRecord) -> None:
        """Push LiveRunScreen wrapping a HistoricalRunHandle scoped
        to the selected run's run_id + time-window.

        The project's ``.wonderland/`` is cumulative across runs —
        Dodo's episodic memory stacks utterances from every run, the
        artifact directories accumulate, etc. To make a finished-run
        replay show only THAT run's events, we pass run_id +
        (started_at, started_at + elapsed_seconds + slop) to
        HistoricalRunHandle, which:

          - reads ``telemetry/run-<run_id>.json`` (not the latest
            file)
          - filters utterances to the time window when iterating
            Dodo's SQLite

        Background-run reattach (P? roadmap) will use a different
        RunHandle implementation (the live one) but flow through the
        same ``LiveRunScreen(handle=...)`` path.
        """
        from datetime import timedelta

        from wonderland.observer.historical import HistoricalRunHandle
        from wonderland.tui.screens.live_run import LiveRunScreen

        wonderland_dir = self.project.root_path
        time_window: tuple[datetime, datetime] | None = None
        if record.started_at is not None:
            # End slop: utterances written near run completion can
            # land a few seconds after the elapsed_seconds value
            # (telemetry flush latency, the meeting-end MEETING_END
            # marker). Add 30s to catch the trailing cluster.
            elapsed = record.elapsed_seconds or 0.0
            end = record.started_at + timedelta(seconds=elapsed + 30)
            time_window = (record.started_at, end)
        # Derive the workflow name from the run's status.json (the
        # background-run subprocess writes it there) or fall back
        # to the project's last_workflow. With this, HistoricalRun-
        # Handle's meeting lookup gets populated from the static
        # workflow definition — pipeline thread_ids then resolve
        # to ``M<N> — <name>`` instead of the synthetic ``Meeting``
        # placeholder.
        workflow_name = self._discover_workflow_for_run(record)
        try:
            handle = HistoricalRunHandle(
                wonderland_dir,
                run_id=record.run_id,
                time_window=time_window,
                workflow_name=workflow_name,
            )
        except FileNotFoundError as exc:
            self.notify(
                f"Can't open run — no .wonderland/ at "
                f"{wonderland_dir}: {exc}",
                severity="warning",
                timeout=6,
            )
            return
        self.app.push_screen(LiveRunScreen(handle=handle))

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """Tree cursor moved → update the detail pane to match the
        highlighted node. Features render their dossier; tickets
        render the ticket markdown plus a header naming the parent
        feature so the operator keeps context. Milestone nodes
        filter the features pane to the selected milestone's
        realization chain."""
        # P15 T-m5 — milestone-tree highlight dispatch. Two
        # selectable kinds:
        #   - milestone: select it (filters features pane via
        #     realization chain) + render its body in the detail
        #     pane.
        #   - requirement: render the requirement's body in the
        #     detail pane WITHOUT changing milestone scope. Lets
        #     the operator drill into a requirement without losing
        #     the milestone filter on the features pane.
        # The cross-cutting parent node is informational only —
        # no-op on highlight.
        if event.node.tree.id == "milestones-tree":
            data = event.node.data
            if data is None:
                return
            kind = data.get("kind")
            if kind == "milestone":
                self._select_milestone(data.get("slug"))
            elif kind == "requirement":
                self._render_requirement_detail(data.get("slug"))
            return
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
            # Tickets have their own lifecycle layer now — show
            # the per-ticket queue controls instead of the
            # feature's button shape.
            self._refresh_per_ticket_action_buttons(
                data["record"].slug
            )

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
        btns = self._action_buttons()
        if btns is None:
            return
        state = row.state
        btns["promote"].display = state == FeatureState.IN_DESIGN
        btns["queue"].display = state == FeatureState.DESIGNED
        btns["unqueue"].display = state == FeatureState.QUEUED
        btns["mark_ready"].display = state == FeatureState.IN_PROGRESS
        btns["redesign"].display = state == FeatureState.IN_PROGRESS
        # Decompose-tickets: visible on designed features. Transitions
        # the feature back to in_design so tdd-decompose's M3+M3.5
        # iteration filter (in_design) picks it up. Useful when the
        # original design pass shipped a feature with 0 tickets (slug
        # drift) or an unsatisfying ticket set.
        btns["decompose"].display = state == FeatureState.DESIGNED
        btns["verify"].display = state == FeatureState.READY_FOR_REVIEW
        btns["reject"].display = state == FeatureState.READY_FOR_REVIEW
        # Hide per-ticket buttons when a feature is highlighted.
        btns["ticket_queue"].display = False
        btns["ticket_unqueue"].display = False

    def _action_buttons(self) -> dict[str, Button] | None:
        """Resolve every action button once for an action-refresh
        pass. Returns None on pre-mount races so callers can bail
        cleanly."""
        try:
            return {
                "promote": self.query_one(
                    "#feature-action-promote-designed", Button
                ),
                "queue": self.query_one(
                    "#feature-action-queue", Button
                ),
                "unqueue": self.query_one(
                    "#feature-action-unqueue", Button
                ),
                "mark_ready": self.query_one(
                    "#feature-action-mark-ready", Button
                ),
                "redesign": self.query_one(
                    "#feature-action-redesign", Button
                ),
                "decompose": self.query_one(
                    "#feature-action-decompose", Button
                ),
                "verify": self.query_one(
                    "#feature-action-verify", Button
                ),
                "reject": self.query_one(
                    "#feature-action-reject", Button
                ),
                "ticket_queue": self.query_one(
                    "#ticket-action-queue", Button
                ),
                "ticket_unqueue": self.query_one(
                    "#ticket-action-unqueue", Button
                ),
                "ticket_mark_done": self.query_one(
                    "#ticket-action-mark-done", Button
                ),
            }
        except Exception:  # noqa: BLE001 — pre-mount race
            return None

    def _refresh_per_ticket_action_buttons(
        self, ticket_slug: str
    ) -> None:
        """When a ticket node is highlighted, show the ticket-level
        queue controls based on the ticket's current lifecycle
        state. Hides every per-feature button so the action row
        doesn't get confusing (one selection → one set of legal
        moves).

        State → visible buttons:
          - pending / aborted / done → Queue ticket
          - queued → Un-queue ticket
          - in_progress → Mark done (operator override when M8's
            accept-routing didn't fire — e.g. the run was killed
            mid-meeting or the operator manually wants to close
            the ticket without another review pass)
          - None (no record yet) → Queue ticket (back-fill on press)
        """
        from wonderland.ticket_lifecycle import (
            TicketState,
            get_state as get_ticket_state,
        )

        btns = self._action_buttons()
        if btns is None:
            return
        for name in (
            "promote",
            "queue",
            "unqueue",
            "mark_ready",
            "redesign",
            "decompose",
            "verify",
            "reject",
        ):
            btns[name].display = False
        state = get_ticket_state(self.project.root_path, ticket_slug)
        can_queue = state in (
            None,
            TicketState.PENDING,
            TicketState.ABORTED,
            TicketState.DONE,
            # IN_PROGRESS → QUEUED is the "un-abort a stuck iteration"
            # path in the state machine (ticket_lifecycle.LEGAL_TRANSITIONS).
            # validation5 surfaced this gap: synthesized follow-up tickets
            # got stuck in_progress when an implementation pass didn't
            # close cleanly, and the UI offered no way to re-queue them
            # short of marking done. Operator should be able to put the
            # ticket back on the queue without having to lie about its
            # state.
            TicketState.IN_PROGRESS,
        )
        can_unqueue = state == TicketState.QUEUED
        can_mark_done = state == TicketState.IN_PROGRESS
        btns["ticket_queue"].display = can_queue
        btns["ticket_unqueue"].display = can_unqueue
        btns["ticket_mark_done"].display = can_mark_done

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

        # Feature state is derived from tickets now (post-chunk-A):
        # a feature shows as QUEUED iff any of its tickets is queued.
        # So we can go back to the simple "count queued features"
        # — no dual count needed.
        n_queued = counts.get(FeatureState.QUEUED, 0)
        n_ready = counts.get(FeatureState.READY_FOR_REVIEW, 0)
        implement_btn.label = f"▶ Implement {n_queued} queued"
        verify_btn.label = f"▶ Verify {n_ready} ready"
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

        # Feature state is derived from tickets, so QUEUED features
        # are exactly the set with at least one queued ticket.
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

    # ------------------------------------------------------------------ #
    # Milestones tree (P15 T-m5)
    # ------------------------------------------------------------------ #

    def _populate_milestones(self) -> None:
        """Build the milestones tree from disk: one parent node per
        milestone (ordered by Order field), children = each
        consumes_requirement slug. Adds a synthetic "Cross-cutting"
        node at the bottom listing requirements whose kind is
        exempt from milestone assignment (persona / situation /
        out_of_scope / deal_breaker) — those inform every milestone
        but don't belong to any one. Refreshes the empty-state CTA +
        the orphan-requirements hint."""
        try:
            tree = self.query_one("#milestones-tree", Tree)
        except Exception:  # noqa: BLE001 — pre-mount
            return
        tree.clear()
        tree.show_root = False

        milestones = self._load_milestones()
        feature_counts = self._compute_per_milestone_feature_counts(
            milestones
        )
        for entry in milestones:
            req_count = len(entry["consumes"])
            feat_count = feature_counts.get(entry["slug"], 0)
            label = (
                f"[b]{entry['title']}[/b]  "
                f"[dim]{req_count} reqs · {feat_count} features[/dim]"
            )
            node = tree.root.add(
                label,
                data={
                    "kind": "milestone",
                    "slug": entry["slug"],
                    "title": entry["title"],
                },
                expand=False,
            )
            for req_slug in entry["consumes"]:
                node.add_leaf(
                    f"[dim]·[/dim]  {req_slug}",
                    data={"kind": "requirement", "slug": req_slug},
                )

        # Cross-cutting requirements — persona/situation/etc. kinds
        # that are exempt from milestone assignment (they inform
        # every milestone). Surface them as their own collapsible
        # node so the operator sees the full corpus accounted for
        # rather than wondering why N total requirements maps to
        # fewer milestone-assigned reqs. Skipped when there's no
        # requirements/ dir at all.
        cross_cutting = self._load_cross_cutting_requirements()
        if cross_cutting:
            cc_node = tree.root.add(
                f"[dim]Cross-cutting[/dim]  "
                f"[dim]{len(cross_cutting)} reqs · (context, no "
                f"milestone)[/dim]",
                data={"kind": "cross_cutting"},
                expand=False,
            )
            for req in cross_cutting:
                cc_node.add_leaf(
                    f"[dim]·[/dim]  [{req['kind']}] {req['slug']}",
                    data={
                        "kind": "requirement",
                        "slug": req["slug"],
                    },
                )

        self._refresh_milestones_cta(milestones)

    def _load_cross_cutting_requirements(self) -> list[dict]:
        """Read every requirement file + return a list of dicts for
        those whose kind is in the non-decomposable exempt set
        (persona / situation / out_of_scope / deal_breaker). These
        are cross-cutting context — they apply to every milestone
        but don't belong to any one. Sorted by kind then slug for
        stable display."""
        import re

        from wonderland.coverage import (
            _NON_DECOMPOSABLE_REQUIREMENT_KINDS,
            _parse_requirement_kind,
        )

        req_dir = (
            self.project.root_path / ".wonderland" / "requirements"
        )
        if not req_dir.is_dir():
            return []
        out: list[dict] = []
        # T-g3: filename id-part is short_guid (new) or legacy number.
        filename_re = re.compile(
            r"requirement-(?P<id>[0-9A-HJKMNP-TV-Z]{8}|\d{1,4})-(?P<slug>.+)\.md"
        )
        for path in req_dir.glob("requirement-*.md"):
            m = filename_re.match(path.name)
            if not m:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            kind = _parse_requirement_kind(text)
            if kind is None:
                continue
            if kind not in _NON_DECOMPOSABLE_REQUIREMENT_KINDS:
                continue
            id_part = m.group("id")
            out.append(
                {
                    "slug": m.group("slug"),
                    "kind": kind,
                    "number": int(id_part) if id_part.isdigit() else 0,
                }
            )
        out.sort(key=lambda r: (r["kind"], r["slug"]))
        return out

    def _load_milestones(self) -> list[dict]:
        """Read every milestone file + return a list of dicts with
        ``slug``, ``title``, ``order``, ``consumes`` in canonical
        order. Empty list when no milestones exist."""
        import re

        milestone_dir = (
            self.project.root_path / ".wonderland" / "milestones"
        )
        if not milestone_dir.is_dir():
            return []
        from wonderland.coverage import _parse_milestone_consumes

        entries: list[dict] = []
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
            entries.append(
                {
                    "slug": slug_m.group(1).strip(),
                    "title": (
                        title_m.group(1).strip() if title_m else slug_m.group(1)
                    ),
                    "order": int(order_m.group(1)) if order_m else 999,
                    "consumes": _parse_milestone_consumes(text),
                }
            )
        entries.sort(key=lambda e: (e["order"], e["slug"]))
        return entries

    def _compute_per_milestone_feature_counts(
        self, milestones: list[dict]
    ) -> dict[str, int]:
        """For each milestone, count features whose sources cite a
        story realizing any of its consumes_requirements. Uses the
        same chain walk as the T-m8b coverage check."""
        counts: dict[str, int] = {}
        if not milestones:
            return counts
        for entry in milestones:
            scope = self._milestone_to_feature_slugs(entry["slug"])
            counts[entry["slug"]] = len(scope)
        return counts

    def _milestone_to_feature_slugs(self, milestone_slug: str) -> set[str]:
        """Walk milestone.consumes_requirements → stories realizing
        each → features sourcing those stories. Returns the set of
        feature slugs whose PRIMARY milestone is this one.

        Primary milestone = the earliest-ordered milestone whose
        chain contains the feature. Features incidentally appearing
        in multiple milestones' raw chains (because an over-broad
        requirement like ``v1-ships-when-all-core-capabilities-work-
        end-to-end`` is consumed by both M2 and M4, and any backend
        feature realizes it) are attributed only to their earliest
        milestone — the foundation owns them, not every later
        milestone that shares an acceptance criterion.

        Mvp-demo M2 surfaced the failure mode: M1's CRUD endpoint
        feature appeared under M1 AND M2 AND M4 because three
        milestones consumed an over-broad acceptance requirement
        the feature happened to realize."""
        primary_map = self._compute_primary_milestone_per_feature()
        return {
            feat for feat, primary in primary_map.items()
            if primary == milestone_slug
        }

    def _compute_primary_milestone_per_feature(
        self,
    ) -> dict[str, str]:
        """Compute feature_slug → primary_milestone_slug map.

        Primary = the milestone whose chain (consumes_requirements
        → realizing stories → feature sources) has the STRONGEST
        OVERLAP with the feature's source set. Strongest = highest
        count of overlapping story slugs. Ties break on smallest
        order (foundation wins ties), then on slug (deterministic).

        Why strongest-overlap instead of earliest-match: over-broad
        acceptance requirements (e.g., ``v1-ships-when-all-core-
        capabilities-work-end-to-end``) get consumed by multiple
        milestones, and any feature realizing that requirement
        ends up matching multiple chains. The right attribution
        is to the milestone whose other narrower requirements the
        feature also realizes — that's where the *bulk* of its
        sourcing lives. Mvp-demo M2 surfaced both failure modes:
        the localStorage feature was incorrectly attributed to M1
        under earliest-wins (1 incidental story realizes M1), even
        though all 3 of its sources realize M2's narrower
        localStorage requirement.

        Features whose chain matches no milestone get no entry
        (orphan features, not shown under any milestone scope).
        """
        import re
        from wonderland.coverage import (
            _parse_milestone_consumes,
            _parse_story_realizes,
            _parse_feature_sources,
            _parse_feature_milestone,
        )

        project_root = self.project.root_path
        milestone_dir = project_root / ".wonderland" / "milestones"
        if not milestone_dir.is_dir():
            return {}

        # Build (slug, order) for all milestones, sorted by order then slug.
        milestone_meta: list[tuple[str, int, list[str]]] = []
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
            if not slug_m or not order_m:
                continue
            mslug = slug_m.group(1).strip()
            morder = int(order_m.group(1))
            consumes = _parse_milestone_consumes(text)
            milestone_meta.append((mslug, morder, consumes))
        milestone_meta.sort(key=lambda x: (x[1], x[0]))

        if not milestone_meta:
            return {}

        # Build req_slug → set[story_slug].
        story_root = project_root / ".wonderland" / "stories"
        story_filename_re = re.compile(
            r"story-(?:[0-9A-HJKMNP-TV-Z]{8}|\d{1,4})-(.+)\.md"
        )
        req_to_stories: dict[str, set[str]] = {}
        if story_root.is_dir():
            for p in story_root.glob("story-*.md"):
                m = story_filename_re.match(p.name)
                if not m:
                    continue
                story_slug = m.group(1)
                try:
                    text = p.read_text(encoding="utf-8")
                except OSError:
                    continue
                for r in _parse_story_realizes(text):
                    req_to_stories.setdefault(r, set()).add(story_slug)

        # For each milestone (in order), compute its story scope.
        milestone_story_scope: dict[str, set[str]] = {}
        for mslug, _morder, consumes in milestone_meta:
            scope: set[str] = set()
            for r in consumes:
                scope.update(req_to_stories.get(r, set()))
            milestone_story_scope[mslug] = scope

        # For each feature, attribute to the milestone with the
        # strongest overlap (most matching source stories). Ties
        # break on the milestone's order (foundation wins ties),
        # then on slug (deterministic).
        order_by_slug = {ms: order for ms, order, _ in milestone_meta}
        feature_root = project_root / ".wonderland" / "features"
        feature_filename_re = re.compile(
            r"feature-(?:[0-9A-HJKMNP-TV-Z]{8}|\d{1,4})-(.+)\.md"
        )
        primary: dict[str, str] = {}
        known_milestone_slugs = {ms for ms, _, _ in milestone_meta}
        if feature_root.is_dir():
            for p in feature_root.glob("feature-*.md"):
                m = feature_filename_re.match(p.name)
                if not m:
                    continue
                fslug = m.group(1)
                try:
                    text = p.read_text(encoding="utf-8")
                except OSError:
                    continue
                # T-ab5: explicit milestone field is authoritative
                # when present and resolvable. Strip guid prefix
                # (slug-only form is what milestone_meta holds).
                # Jaccard fallback below only runs for legacy
                # features shipped before T-ab5.
                explicit = _parse_feature_milestone(text)
                if explicit:
                    slug_only = (
                        explicit.split(":", 1)[1] if ":" in explicit else explicit
                    )
                    if slug_only in known_milestone_slugs:
                        primary[fslug] = slug_only
                        continue
                # T-g5 source resolution: sources may be plain slugs
                # OR guid:slug-prefixed forms. Strip the optional
                # guid prefix so comparison against story slugs works.
                # Mvp-demo regression: M3's markdown-preview feature
                # was orphaned because its sources used the new
                # guid:slug form but milestone_story_scope contains
                # plain slugs.
                raw_sources = _parse_feature_sources(text)
                sources: set[str] = set()
                for src in raw_sources:
                    if ":" in src:
                        # guid:slug — keep just the slug portion
                        sources.add(src.split(":", 1)[1])
                    else:
                        sources.add(src)
                if not sources:
                    continue
                # Score each milestone by overlap count.
                best: tuple[int, int, str] | None = None
                for mslug, morder, _consumes in milestone_meta:
                    overlap = len(sources & milestone_story_scope[mslug])
                    if overlap == 0:
                        continue
                    # Sort key: (-overlap, order, slug) — higher
                    # overlap first, then lower order, then slug
                    # alphabetical. We negate overlap because we
                    # want the LARGEST overlap to win in min().
                    key = (-overlap, morder, mslug)
                    if best is None or key < best:
                        best = key
                        best_ms = mslug
                if best is not None:
                    primary[fslug] = best_ms
        # Suppress the noqa-friendly name-mangling complaint on
        # ``best_ms`` — it's only referenced inside the if-block
        # gated on ``best is not None``, so it's always defined
        # when read.
        _ = order_by_slug  # currently unused; reserved for callers
        return primary

    def _refresh_milestones_cta(
        self, milestones: list[dict]
    ) -> None:
        """Drive the empty-state CTA button + orphan-requirements
        hint based on derived project phase. The button text + id-
        based dispatch (handled in on_button_pressed via
        ``milestones-empty-cta``) routes to the right NewRunScreen
        pre-fill (discovery / milestone-plan / nothing)."""
        try:
            from wonderland.project import (
                ProjectPhase,
                derive_project_phase,
            )
            from wonderland.coverage import (
                compute_orphan_requirements,
            )

            cta = self.query_one("#milestones-empty-cta", Button)
            tree = self.query_one("#milestones-tree", Tree)
            hint = self.query_one(
                "#milestones-orphan-hint", Static
            )
        except Exception:  # noqa: BLE001 — pre-mount
            return

        snap = derive_project_phase(self.project.root_path)

        # Default: tree visible, CTA + hint hidden.
        tree.display = True
        cta.display = False
        hint.update("")
        hint.display = False

        if snap.phase is ProjectPhase.DISCOVERY:
            tree.display = False
            cta.display = True
            cta.label = "▶ Run discovery to capture requirements"
            self._cta_action = "discovery"
            return
        if snap.phase is ProjectPhase.PLANNING:
            tree.display = False
            cta.display = True
            cta.label = (
                f"▶ Run milestone-plan "
                f"({snap.requirements_count} requirements ready)"
            )
            self._cta_action = "milestone-plan"
            return

        # Milestones exist — but check for orphan decomposable
        # requirements + surface the hint above the tree.
        gap = compute_orphan_requirements(self.project.root_path)
        if gap is not None:
            count = len(gap.items)
            hint.update(
                f"[yellow]⚠ {count} requirement(s) unassigned to "
                f"any milestone — consider re-running "
                f"milestone-plan.[/yellow]"
            )
            hint.display = True
        self._cta_action = None

    def _select_milestone(self, slug: str | None) -> None:
        """Set the active milestone scope + refresh the detail pane
        + features pane. Idempotent re-selection of the same slug
        clears the scope (toggle). When ``slug`` is None or
        unknown, scope is cleared and features pane shows
        everything."""
        if not slug or slug == self._selected_milestone_slug:
            self._selected_milestone_slug = None
            self._milestone_feature_scope = None
        else:
            self._selected_milestone_slug = slug
            self._milestone_feature_scope = (
                self._milestone_to_feature_slugs(slug)
            )
        self._refresh_milestone_detail()
        self._populate_features()

    def _refresh_milestone_detail(self) -> None:
        """Update the milestone detail pane + Design CTA button to
        match the currently-selected milestone. When no milestone
        is selected, the pane shows a hint + the CTA is hidden.
        When a milestone has zero realizing features, the CTA
        offers to launch tdd-design --milestone <slug>."""
        try:
            detail = self.query_one("#milestones-detail", Static)
            cta = self.query_one("#milestone-design-cta", Button)
        except Exception:  # noqa: BLE001 — pre-mount
            return
        slug = self._selected_milestone_slug
        if slug is None:
            detail.update("[dim](no milestone selected)[/dim]")
            cta.display = False
            cta.label = ""
            return
        # Read the milestone's body from disk for the detail pane.
        body = self._read_milestone_body(slug)
        if body is None:
            detail.update(
                f"[red]Milestone ``{slug}`` not found on disk.[/red]"
            )
            cta.display = False
            return
        scope_count = (
            len(self._milestone_feature_scope)
            if self._milestone_feature_scope is not None
            else 0
        )
        header = (
            f"[b]{slug}[/b]   "
            f"[dim]{scope_count} realizing feature(s)[/dim]\n\n"
        )
        detail.update(header + body)
        # Design CTA visible when this milestone has zero features
        # realizing its requirements (the operator's next-step
        # action). Hidden otherwise — the milestone is already
        # designed; further work happens via the Features pane.
        if scope_count == 0:
            cta.display = True
            cta.label = f"▶ Design milestone: {slug}"
        else:
            cta.display = False
            cta.label = ""

    def _read_milestone_body(self, slug: str) -> str | None:
        """Look up a milestone's full markdown body by slug. Returns
        None when the milestone isn't found on disk."""
        import re

        milestone_dir = (
            self.project.root_path / ".wonderland" / "milestones"
        )
        if not milestone_dir.is_dir():
            return None
        for path in milestone_dir.glob("milestone-*.md"):
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            slug_m = re.search(
                r"^\*\*Slug:\*\*\s*(\S+)", text, re.MULTILINE
            )
            if slug_m and slug_m.group(1).strip() == slug:
                return text
        return None

    def _render_requirement_detail(self, req_slug: str | None) -> None:
        """Render a requirement's markdown body in the milestone
        detail pane. Triggered when the operator highlights a
        requirement leaf in the milestones tree (under a milestone
        parent OR under the cross-cutting node). The milestone
        scope on the features pane is preserved — drilling into a
        requirement is informational, not navigational. The Design
        CTA hides since it's milestone-shaped, not requirement-
        shaped."""
        import re

        try:
            detail = self.query_one("#milestones-detail", Static)
            cta = self.query_one("#milestone-design-cta", Button)
        except Exception:  # noqa: BLE001 — pre-mount
            return
        if not req_slug:
            return
        req_dir = (
            self.project.root_path / ".wonderland" / "requirements"
        )
        if not req_dir.is_dir():
            detail.update(
                f"[red]No requirements directory — can't render "
                f"``{req_slug}``.[/red]"
            )
            cta.display = False
            return
        # Filename pattern: requirement-NNN-<slug>.md
        target = None
        for path in req_dir.glob(f"requirement-*-{req_slug}.md"):
            target = path
            break
        if target is None:
            # Fallback: scan + match by slug field in case the
            # filename doesn't include the slug exactly.
            for path in req_dir.glob("requirement-*.md"):
                try:
                    text = path.read_text(encoding="utf-8")
                except OSError:
                    continue
                slug_m = re.search(
                    r"^\*\*Slug:\*\*\s*(\S+)", text, re.MULTILINE
                )
                if slug_m and slug_m.group(1).strip() == req_slug:
                    target = path
                    break
        if target is None:
            detail.update(
                f"[yellow]Requirement ``{req_slug}`` not found on "
                f"disk.[/yellow]"
            )
            cta.display = False
            return
        try:
            body = target.read_text(encoding="utf-8")
        except OSError as exc:
            detail.update(f"[red]Read failed: {exc}[/red]")
            cta.display = False
            return
        header = f"[b]Requirement[/b] · [dim]{req_slug}[/dim]\n\n"
        detail.update(header + body)
        # CTA is milestone-shaped — hide when drilled into a
        # requirement. Reappears when the operator highlights a
        # milestone again.
        cta.display = False

    def _populate_features(self) -> None:
        tree = self.query_one("#features-tree", Tree)
        tree.clear()
        tree.show_root = False  # the pane label "Features" is enough
        self._features = self._load_features()
        # T92: refresh the actions pane every time the features list
        # changes so button state (counts, primary variant, disabled
        # flags) tracks reality.
        self._refresh_action_buttons()
        # P15 T-m5 — apply both filters: lifecycle state (chips) AND
        # active milestone scope (from milestones-tree selection).
        # Both must accept the feature for it to show. Scope filter
        # is a no-op when no milestone is selected.
        visible = [
            r for r in self._features
            if (self._filter is None or r.state == self._filter)
            and (
                self._milestone_feature_scope is None
                or r.slug in self._milestone_feature_scope
            )
        ]
        if not visible:
            self._render_features_empty_state()
            return

        # feature_slug → list[TicketRecord]. Built from each ticket's
        # Sources field (option-1 source-of-truth from the slug-
        # mismatch fix in analysis 040 vintage).
        feature_to_tickets = self._load_ticket_tree()

        # Pre-compute the ticket state map + blocked-by lookups so
        # rendering is O(tickets) disk reads instead of
        # O(tickets × deps). State map folds all_transitions once;
        # blocked_by needs one read per ticket (could be cached too,
        # but read counts are bounded by tree visibility).
        state_map = self._current_ticket_state_map()
        blocked_set = self._compute_blocked_tickets(
            feature_to_tickets, state_map
        )

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
                # Lifecycle state badge in the prefix. Marked-for-
                # deletion (the prune flow) wins over state since
                # it's a stronger operator signal. Otherwise we
                # show one of: ▶ queued / ⟳ in_progress / ✓ done /
                # ⚠ aborted / · pending (the bare bullet for the
                # default no-record-yet case).
                ticket_state = _ticket_state_for(
                    self.project.root_path, ticket.slug
                )
                if ticket.slug in self._marked_ticket_slugs:
                    ticket_label = (
                        f"[red]✗[/red] [strike]{ticket_title}[/strike]  "
                        f"[dim]{ticket.slug}[/dim]"
                    )
                else:
                    badge_prefix = _TICKET_STATE_BADGE.get(
                        ticket_state, "[dim]·[/dim]"
                    )
                    # Blocked badge — small lock prefix when this
                    # ticket has unsatisfied blocked_by deps still
                    # in the pipeline. Shows up alongside the state
                    # badge so operator sees the gate at a glance.
                    blocked_marker = (
                        " [red]🔒[/red]"
                        if ticket.slug in blocked_set
                        else ""
                    )
                    ticket_label = (
                        f"{badge_prefix}{blocked_marker} {ticket_title}  "
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
        # stable, human-readable order, then collapse duplicates
        # (same case-insensitive title under the same feature) to the
        # highest-numbered copy — that's the "latest" revision Rabbit
        # produced when M3 revised mid-meeting. Operator can still see
        # all copies via `wonderland list_tickets` on disk; this is a
        # UI-only filter to keep the tree readable.
        for feature_slug in out:
            ordered = sorted(out[feature_slug], key=lambda r: r.number)
            by_title: dict[str, object] = {}
            for rec in ordered:
                by_title[rec.title.strip().lower()] = rec
            out[feature_slug] = sorted(
                by_title.values(), key=lambda r: r.number  # type: ignore[arg-type]
            )
        return out

    def _render_features_empty_state(self) -> None:
        detail = self.query_one("#features-detail", Static)
        # P15 T-m5 — when a milestone is selected + has zero
        # features, surface a big CTA in the detail pane that
        # launches tdd-design pre-scoped to the milestone. This is
        # the design-time entry point: operator picks a milestone,
        # sees "no features yet", clicks the CTA, and lands on
        # NewRunScreen with the right workflow + --milestone slug.
        if self._selected_milestone_slug is not None:
            detail.update(
                f"[b yellow]Milestone "
                f"``{self._selected_milestone_slug}`` has no features "
                f"designed yet.[/b yellow]\n\n"
                f"[dim]Use the [b]Design milestone[/b] button at the "
                f"bottom of the Milestone detail pane on the left to "
                f"launch a tdd-design run scoped to this milestone — "
                f"Rabbit will compose features realizing its consumed "
                f"requirements.[/dim]"
            )
            return
        if not self._features:
            detail.update(
                "[b yellow]No features yet for this project.[/b yellow]\n\n"
                "Run [b]tdd-design[/b] and Rabbit will produce features "
                "in M2.\n\n"
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
        self._populate_milestones()
        self._populate_features()
        self._populate_runs()
        self._populate_artifacts()
        self._populate_metrics()
        self._refresh_phase_badge()
        self._refresh_milestone_detail()
        # Land focus on the milestones tree — primary navigation
        # surface in the T-m5 layout (drives which features the
        # right pane shows). Fall back to features-tree if milestones
        # aren't mounted yet (race during first render).
        try:
            self.query_one("#milestones-tree", Tree).focus()
        except Exception:  # noqa: BLE001
            try:
                self.query_one("#features-tree", Tree).focus()
            except Exception:  # noqa: BLE001
                pass

    def on_screen_resume(self) -> None:
        # Re-populate when the dashboard becomes the top screen again
        # (e.g. operator just exited a live-run view). Feature state and
        # the runs list both depend on disk state mutated by the run we
        # just left, so without this the user has to manually click a
        # filter chip or refresh to see updates.
        self._populate_milestones()
        self._populate_features()
        self._populate_runs()
        self._populate_artifacts()
        self._populate_metrics()
        self._refresh_phase_badge()
        self._refresh_milestone_detail()

    def _refresh_phase_badge(self) -> None:
        """P15 T-m8 UX — re-derive the project's lifecycle phase
        from disk + update the dashboard-phase Static. Silent on
        any read error; an empty badge is acceptable degradation."""
        try:
            from wonderland.project import derive_project_phase

            snapshot = derive_project_phase(self.project.root_path)
            badge = self.query_one("#dashboard-phase", Static)
            badge.update(
                f"[b]Phase:[/b] {snapshot.label}  ·  "
                f"[dim]{snapshot.next_action_hint}[/dim]"
            )
        except Exception:  # noqa: BLE001 — non-critical
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

    def _launch_workflow(
        self, workflow_name: str, *, milestone: str | None
    ) -> None:
        """P15 T-m5 — push NewRunScreen pre-filled with the named
        workflow + optional --milestone scope. Used by the
        milestones-pane CTA + the features-pane design CTA.
        Operator still confirms the launch on NewRunScreen; this
        just teleports them there with the right defaults.

        124b5858: for design-shaped workflows with a milestone scope,
        also prefill a synthesized directive from the milestone's
        goal + done_when. Mirrors the impl-prefill pattern so the
        operator sees what's being sent to the agents + can edit
        before submit. Same synthesizer as the runtime fallback in
        run_workflow — single source of truth.
        """
        from wonderland.tui.screens.new_run import NewRunScreen

        default_directive: str | None = None
        if (
            milestone is not None
            and workflow_name in ("tdd-design", "tdd-decompose")
        ):
            try:
                from wonderland.workflow import (
                    _synthesize_milestone_directive,
                    _resolve_milestone_scope,
                )
                # _resolve_milestone_scope wants a runner-like object;
                # build a thin stand-in with just project_root attr.
                import types
                runner_proxy = types.SimpleNamespace(
                    project_root=self.project.root_path
                )
                scope = _resolve_milestone_scope(runner_proxy, milestone)
                if scope is not None:
                    default_directive = _synthesize_milestone_directive(
                        scope, runner_proxy
                    )
            except Exception:  # noqa: BLE001 — prefill is best-effort
                default_directive = None

        kwargs: dict = {
            "project": self.project,
            "default_workflow": workflow_name,
            "default_milestone": milestone,
        }
        if default_directive is not None:
            kwargs["default_directive"] = default_directive

        self.app.push_screen(NewRunScreen(**kwargs))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid is None:
            return
        # P15 T-m5 — milestones-pane empty-state CTA dispatch.
        # ``_cta_action`` is set by _refresh_milestones_cta based on
        # the project's phase: discovery → launch discovery,
        # planning → launch milestone-plan.
        if bid == "milestones-empty-cta":
            action = getattr(self, "_cta_action", None)
            if action == "discovery":
                self._launch_workflow("discovery", milestone=None)
            elif action == "milestone-plan":
                self._launch_workflow(
                    "milestone-plan", milestone=None
                )
            return
        # P15 T-m5 — milestone-detail Design CTA. Visible only when
        # a milestone is selected + has zero realizing features.
        if bid == "milestone-design-cta":
            slug = self._selected_milestone_slug
            if slug:
                self._launch_workflow("tdd-design", milestone=slug)
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
        elif bid.startswith("ticket-action-"):
            self._handle_ticket_action(bid)

    def _handle_ticket_action(self, button_id: str) -> None:
        """Per-ticket action dispatch. Queue / Un-queue / Mark-done
        transitions the ticket through ``ticket_lifecycle`` so the
        workflow's per_item filter scopes correctly and the
        feature-state rollup picks up the change. Mark-done is the
        operator override for an in-progress ticket that didn't
        get auto-completed by an M8 accept verdict (e.g. the run
        died mid-meeting, or the operator wants to close out a
        ticket without another review pass)."""
        from wonderland.ticket_lifecycle import (
            IllegalTransitionError as TicketIllegalTransition,
            TicketState,
            back_fill_state as ticket_back_fill,
            get_state as get_ticket_state,
            transition as ticket_transition,
        )

        record = self._currently_highlighted_ticket()
        if record is None:
            self.notify(
                "No ticket selected.", severity="warning"
            )
            return
        slug = record.slug
        if button_id == "ticket-action-queue":
            target = TicketState.QUEUED
            verb = "queued for next implementation run"
        elif button_id == "ticket-action-mark-done":
            target = TicketState.DONE
            verb = "marked done"
        else:
            target = TicketState.PENDING
            verb = "un-queued"

        # Dependency gate — only applies when queueing. Unsatisfied
        # blocked_by deps surface as a notification naming the
        # offending slugs so the operator knows which tickets need
        # to land first instead of failing silently. "Satisfied" =
        # state ∈ {IN_PROGRESS, DONE} per the user's spec ("done or
        # ready for review"). PENDING / QUEUED / ABORTED / None all
        # count as still-blocking.
        if target == TicketState.QUEUED:
            unsatisfied = self._unsatisfied_blocked_by(slug)
            if unsatisfied:
                slug_list = ", ".join(unsatisfied)
                self.notify(
                    f"Can't queue {slug!r} — blocked by: {slug_list}. "
                    "Land or run those first.",
                    severity="warning",
                    timeout=8,
                )
                return

        current = get_ticket_state(self.project.root_path, slug)
        try:
            if current is None:
                # First time this ticket enters the lifecycle —
                # back-fill its initial state before the transition.
                # Skip back-fill if the operator's first action is
                # to queue: back-fill to PENDING then transition,
                # so the audit log captures both steps.
                ticket_back_fill(
                    self.project.root_path,
                    slug,
                    TicketState.PENDING,
                    notes="initial state on first dashboard action",
                )
                current = TicketState.PENDING
            if target == current:
                self.notify(
                    f"Ticket {slug!r} already in state "
                    f"{current.value}.",
                    timeout=3,
                )
                return
            ticket_transition(
                self.project.root_path,
                slug,
                target,
                by="operator",
            )
            self.notify(
                f"Ticket {slug!r} {verb}.", timeout=3
            )
            self._refresh_per_ticket_action_buttons(slug)
            # Re-render the features tree so the new state badge
            # appears on the ticket node.
            self._populate_features()
            self._restore_tree_cursor_to_ticket(slug)
        except TicketIllegalTransition as exc:
            self.notify(
                f"Can't {verb.split(' ', 1)[0]} ticket: {exc}",
                severity="warning",
                timeout=6,
            )

    def _currently_highlighted_ticket(self):
        """Return the ticket record under the tree cursor, or None
        when the cursor is on a feature node / outside the tree."""
        try:
            tree = self.query_one("#features-tree", Tree)
        except Exception:  # noqa: BLE001
            return None
        node = tree.cursor_node
        if node is None or node.data is None:
            return None
        if node.data.get("kind") != "ticket":
            return None
        return node.data["record"]

    def _current_ticket_state_map(self) -> dict[str, object]:
        """Fold the ticket-states.jsonl into {slug: TicketState} once.
        Cheap-O(N) over the log, used by _populate_features and the
        blocked-by computation so we don't re-read the log per ticket.
        Returns an empty dict if the log can't be read at all."""
        try:
            from wonderland.ticket_lifecycle import all_transitions

            current: dict[str, object] = {}
            for record in all_transitions(self.project.root_path):
                current[record.ticket_slug] = record.to_state
            return current
        except Exception:  # noqa: BLE001
            return {}

    def _compute_blocked_tickets(
        self,
        feature_to_tickets: dict[str, list],
        state_map: dict[str, object],
    ) -> set[str]:
        """Set of ticket slugs whose blocked_by deps aren't all in
        a satisfying state. Satisfied = state ∈ {IN_PROGRESS, DONE}.
        Pure read pass — one ticket-file read per ticket to parse
        the Blocked-by line; deps then looked up in ``state_map``
        without further disk I/O.
        """
        from wonderland.ticket import read_ticket_blocked_by

        try:
            from wonderland.ticket_lifecycle import TicketState
        except Exception:  # noqa: BLE001
            return set()

        satisfying = {TicketState.IN_PROGRESS, TicketState.DONE}
        blocked: set[str] = set()
        # Build a set of all known ticket slugs from the tree so we
        # silently skip dep references that aren't real tickets.
        known_slugs = {
            tk.slug
            for tickets in feature_to_tickets.values()
            for tk in tickets
        }
        for tickets in feature_to_tickets.values():
            for ticket in tickets:
                deps = read_ticket_blocked_by(
                    self.project.root_path, ticket.slug
                )
                if not deps:
                    continue
                for dep in deps:
                    if dep not in known_slugs:
                        continue
                    if state_map.get(dep) not in satisfying:
                        blocked.add(ticket.slug)
                        break
        return blocked

    def _unsatisfied_blocked_by(self, ticket_slug: str) -> list[str]:
        """Return the slugs of blocked_by deps that haven't reached
        a satisfying state. Satisfied = ticket_lifecycle state ∈
        {IN_PROGRESS, DONE}. PENDING / QUEUED / ABORTED / no-record
        all count as still-blocking. Missing dep tickets (slug
        doesn't resolve to a file on disk) are skipped silently —
        Rabbit sometimes invents soft references that aren't real
        ticket slugs and we'd rather not block on those.
        """
        from wonderland.ticket import (
            TicketRegistry,
            read_ticket_blocked_by,
        )
        from wonderland.ticket_lifecycle import (
            TicketState,
            get_state as get_ticket_state,
        )

        deps = read_ticket_blocked_by(self.project.root_path, ticket_slug)
        if not deps:
            return []
        registry = TicketRegistry(self.project.root_path)
        unsatisfied: list[str] = []
        for dep in deps:
            if registry.find_by_slug(dep) is None:
                continue  # not a real ticket slug; skip
            state = get_ticket_state(self.project.root_path, dep)
            if state not in (TicketState.IN_PROGRESS, TicketState.DONE):
                unsatisfied.append(dep)
        return unsatisfied

    def _handle_feature_action(self, button_id: str) -> None:
        """Per-feature action dispatch. Most actions are now bulk
        operations over the feature's tickets — feature state
        derives from the ticket rollup (chunks A + B), so writing
        feature-level lifecycle entries directly would be ignored.
        Verify / Reject stay at feature level (operator terminals).
        Promote-to-Designed still operates on the feature lifecycle
        because designed is a pre-ticket state.
        """
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
            n, skipped = self._bulk_ticket_op(
                row.slug,
                target_state="queued",
                eligible_states=("pending", None),
                notes=f"Bulk queue via {row.slug!r} feature action",
            )
            if n:
                self.notify(
                    f"Queued {n} ticket(s) on {row.slug} for next "
                    f"implementation run."
                )
            elif skipped:
                self.notify(
                    f"No pending tickets to queue on {row.slug}.",
                    severity="warning",
                )
            self.action_refresh()
        elif button_id == "feature-action-unqueue":
            n, skipped = self._bulk_ticket_op(
                row.slug,
                target_state="pending",
                eligible_states=("queued",),
                notes=f"Bulk un-queue via {row.slug!r} feature action",
            )
            if n:
                self.notify(
                    f"Un-queued {n} ticket(s) on {row.slug}."
                )
            else:
                self.notify(
                    f"No queued tickets to un-queue on {row.slug}.",
                    severity="warning",
                )
            self.action_refresh()
        elif button_id == "feature-action-mark-ready":
            n, skipped = self._bulk_ticket_op(
                row.slug,
                target_state="done",
                eligible_states=("queued", "in_progress", "pending"),
                notes=(
                    f"Bulk mark-done via {row.slug!r} feature action "
                    "(operator override; review skipped)"
                ),
            )
            if n:
                msg = (
                    f"Marked {n} ticket(s) on {row.slug} done — "
                    f"feature now ready for review."
                )
                if skipped:
                    msg += (
                        f" ({skipped} aborted ticket(s) skipped — "
                        f"re-queue them to retry through review.)"
                    )
                self.notify(msg)
            elif skipped:
                self.notify(
                    f"All non-done tickets on {row.slug} are "
                    f"aborted — re-queue to retry.",
                    severity="warning",
                )
            self.action_refresh()
        elif button_id == "feature-action-redesign":
            n, _ = self._bulk_ticket_op(
                row.slug,
                target_state="pending",
                eligible_states=(
                    "queued", "in_progress", "done", "aborted"
                ),
                notes=(
                    f"Bulk re-design via {row.slug!r}: operator "
                    "reverted tickets to pending"
                ),
            )
            self.notify(
                f"Reverted {n} ticket(s) on {row.slug} to pending — "
                f"re-run tdd-design or queue again."
            )
            self.action_refresh()
        elif button_id == "feature-action-decompose":
            # designed → in_design transition for tdd-decompose.
            # No ticket-state side effects (the existing tickets
            # stay on disk; the operator either runs tdd-decompose
            # to re-decompose, or manually retracts old tickets
            # first if they want a clean slate). M3.5's consolidation
            # in tdd-decompose handles merging/retracting redundant
            # tickets cleanly.
            from wonderland.feature_lifecycle import (
                FeatureState as _FState,
                IllegalTransitionError as _FIllegal,
                transition as _ftransition,
            )

            try:
                _ftransition(
                    self.project.root_path,
                    row.slug,
                    _FState.IN_DESIGN,
                    by="operator",
                    notes=(
                        f"Sent back to design for re-decomposition "
                        f"via dashboard. Operator next runs "
                        f"tdd-decompose to regenerate tickets."
                    ),
                )
                self.notify(
                    f"{row.slug}: designed → in_design. Run "
                    f"tdd-decompose to regenerate tickets.",
                )
            except _FIllegal as exc:
                self.notify(
                    f"Cannot send {row.slug} back to design: {exc}",
                    severity="error",
                )
            self.action_refresh()
        elif button_id == "feature-action-verify":
            self._open_verify_modal("verify")
        elif button_id == "feature-action-reject":
            self._open_verify_modal("reject")

    def _bulk_ticket_op(
        self,
        feature_slug: str,
        *,
        target_state: str,
        eligible_states: tuple[str | None, ...],
        notes: str,
    ) -> tuple[int, int]:
        """Bulk-transition every ticket of ``feature_slug`` whose
        current state matches one of ``eligible_states`` to
        ``target_state`` via the ticket-lifecycle chain helper.

        Returns ``(moved, skipped)`` — moved = tickets that
        transitioned, skipped = tickets that exist but didn't
        match any eligible state (kept for the caller to surface
        in the notification text, e.g. "N aborted tickets skipped").

        ``eligible_states`` uses string forms (``"pending"``,
        ``"queued"``, etc.) plus ``None`` for "no record yet" so
        the dashboard can write the eligibility filter without
        importing TicketState. Same for ``target_state``.
        """
        from wonderland.ticket_lifecycle import (
            IllegalTransitionError as _TicketIllegal,
            TicketState,
            chain_transition,
            get_state as get_ticket_state,
        )
        from wonderland.workflow import _ticket_to_feature_map

        try:
            target_enum = TicketState(target_state)
        except ValueError:
            return 0, 0

        eligible_enums: set[TicketState | None] = set()
        for s in eligible_states:
            if s is None:
                eligible_enums.add(None)
                continue
            try:
                eligible_enums.add(TicketState(s))
            except ValueError:
                continue

        try:
            mapping = _ticket_to_feature_map(self.project.root_path)
        except Exception:  # noqa: BLE001
            return 0, 0
        tickets = [
            slug for slug, feat in mapping.items()
            if feat == feature_slug
        ]
        moved = 0
        skipped = 0
        for slug in tickets:
            try:
                current = get_ticket_state(
                    self.project.root_path, slug
                )
            except Exception:  # noqa: BLE001
                continue
            if current not in eligible_enums:
                skipped += 1
                continue
            try:
                chain_transition(
                    self.project.root_path,
                    slug,
                    target_enum,
                    by="operator",
                    notes=notes,
                )
                moved += 1
            except _TicketIllegal:
                skipped += 1
        return moved, skipped

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

        # T-a2 chunk C: if this verify closed out a milestone (every
        # primary-attributed feature now in VERIFIED state), fire
        # episodic-memory consolidation: archive the milestone's
        # design + impl branches across all per-agent stores, write
        # a project-level summary utterance attributed to Mock
        # Turtle. Subsequent design passes' inheritance chains see
        # the summary but not the per-milestone deliberation noise.
        if target_state == FeatureState.VERIFIED:
            self._maybe_consolidate_milestone_for_feature(row.slug)

        self.action_refresh()

    def _maybe_consolidate_milestone_for_feature(
        self, verified_feature_slug: str,
    ) -> None:
        """Check whether ``verified_feature_slug`` closes its
        milestone (every primary-attributed feature now VERIFIED).
        If so, fire ``consolidate_milestone`` synchronously via a
        new asyncio loop (the dashboard runs in textual's event
        loop; the consolidation is a quick I/O bound op so blocking
        is fine).

        Operator gets a notify on success showing per-agent archive
        counts. Errors are swallowed + notified — consolidation is
        best-effort and shouldn't block the verify flow.
        """
        import asyncio
        from wonderland.feature_lifecycle import (
            FeatureState,
            get_state as get_feature_state,
        )
        from wonderland.memory.consolidation import consolidate_milestone

        try:
            primary_map = self._compute_primary_milestone_per_feature()
        except Exception:  # noqa: BLE001
            return

        milestone_slug = primary_map.get(verified_feature_slug)
        if milestone_slug is None:
            # Feature isn't attributed to a milestone — nothing to
            # consolidate.
            return

        # Find every feature in this milestone; check states.
        sibling_features = [
            f for f, m in primary_map.items() if m == milestone_slug
        ]
        all_verified = True
        for f in sibling_features:
            state = get_feature_state(self.project.root_path, f)
            if state != FeatureState.VERIFIED:
                all_verified = False
                break
        if not all_verified:
            # Milestone not yet fully closed.
            return

        # Look up milestone name (best-effort, for the summary body).
        milestone_name: str | None = None
        try:
            import re
            for path in (
                self.project.root_path / ".wonderland" / "milestones"
            ).glob("milestone-*.md"):
                text = path.read_text(encoding="utf-8")
                slug_m = re.search(
                    r"^\*\*Slug:\*\*\s*(\S+)", text, re.MULTILINE
                )
                if slug_m and slug_m.group(1).strip() == milestone_slug:
                    header_m = re.match(
                        r"^##\s*Milestone\s+\d+:\s*(.+?)$",
                        text, re.MULTILINE,
                    )
                    if header_m:
                        milestone_name = header_m.group(1).strip()
                    break
        except Exception:  # noqa: BLE001
            pass

        # Fire consolidation. asyncio.run() ok here — dashboard is
        # synchronous outside event handlers, and the consolidation
        # call is short.
        try:
            results = asyncio.run(consolidate_milestone(
                self.project.root_path,
                milestone_slug=milestone_slug,
                milestone_name=milestone_name,
                feature_slugs=sorted(sibling_features),
            ))
        except Exception as exc:  # noqa: BLE001
            self.notify(
                f"Memory consolidation failed for {milestone_slug}: "
                f"{exc}", severity="warning", timeout=6,
            )
            return

        total = sum(results.values())
        self.notify(
            f"Milestone {milestone_slug} closed. Memory branches "
            f"archived ({total} utterances across "
            f"{len(results)} agents); project-level summary "
            f"recorded.",
            timeout=8,
        )

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

    def action_show_artifacts(self) -> None:
        self.query_one("#dashboard-tabs", TabbedContent).active = (
            "tab-artifacts"
        )

    def action_show_files(self) -> None:
        self.query_one("#dashboard-tabs", TabbedContent).active = "tab-files"

    def action_show_metrics(self) -> None:
        self.query_one("#dashboard-tabs", TabbedContent).active = "tab-metrics"


__all__ = ["ProjectDashboardScreen"]
