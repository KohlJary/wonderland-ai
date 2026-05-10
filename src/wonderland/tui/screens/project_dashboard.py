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


class ProjectDashboardScreen(Screen[None]):
    """Per-project landing surface — tabs for runs / artifacts /
    files / metrics."""

    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
        Binding("n", "new_run", "New run", show=True),
        Binding("R", "refresh", "Refresh", show=True),
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

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical(id="dashboard-root"):
            yield Static(
                f"[b]{self.project.name}[/b] · "
                f"[dim]{self.project.root_path}[/dim]",
                id="dashboard-header",
            )
            # Actions pane — always visible regardless of which tab is
            # active. Starts with "New Run"; future operator-level
            # actions (Edit project, Archive, Open in shell, Run-
            # follow watcher) land in this row alongside.
            with Horizontal(id="dashboard-actions"):
                yield Button(
                    "▶ New Run",
                    id="dashboard-new-run-button",
                    variant="primary",
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
    # Lifecycle
    # ------------------------------------------------------------------ #

    def on_mount(self) -> None:
        self._populate_runs()
        self._populate_artifacts()
        self._populate_metrics()

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
        if event.button.id == "dashboard-new-run-button":
            self.action_new_run()

    def action_refresh(self) -> None:
        self._populate_runs()
        self._populate_artifacts()
        self._populate_metrics()

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
