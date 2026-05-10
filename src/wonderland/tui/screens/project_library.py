"""ProjectLibraryScreen — the TUI's home (P11+).

Action-driven layout. Lazygit-shape per project_tui_lazygit_principle:
focus + selection drives filtering across panes.

Two columns:
  - LEFT: action menu (the primary surface — what can I do here?)
  - RIGHT: contextual detail pane that shows different content
    based on which action is highlighted

The "Open project" action is special: highlighting it surfaces the
project list in the detail pane (preview state); pressing Enter on
"Open project" moves focus into the project list; pressing Enter on
a project opens its dashboard. Per-project actions (archive, edit,
unarchive) are bound at the screen level — they fire on the
highlighted project when the project table is focused.

Other actions (New project, New run, Settings, Analyses, etc.) are
self-contained: highlight to read the description, Enter to dispatch.
The detail pane shows the description text instead of the project
table.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static

from wonderland.project import (
    Project,
    archive_project,
    list_projects,
    unarchive_project,
)


def _fmt_relative(dt: datetime | None) -> str:
    if dt is None:
        return "never"
    now = datetime.now(timezone.utc)
    delta = now - dt.astimezone(timezone.utc)
    seconds = delta.total_seconds()
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{int(seconds / 60)}m ago"
    if seconds < 86400:
        return f"{int(seconds / 3600)}h ago"
    days = int(seconds / 86400)
    return f"{days}d ago" if days < 30 else dt.strftime("%Y-%m-%d")


class ProjectLibraryScreen(Screen[None]):
    """Action-driven home screen.

    Selection-driven detail pane: action highlighted → detail
    pane content updates. ``open_project`` action surfaces the
    project list; other actions show description text.
    """

    BINDINGS = [
        # Enter / d on the action table dispatches the action; on the
        # project table opens the dashboard.
        Binding("enter", "activate", "Activate", show=True),
        Binding("d", "activate", "", show=False),
        # Per-project actions — only meaningful when the project
        # table is focused. e/x/u still work everywhere as a
        # convenience, but the description hint matches the project
        # context.
        Binding("e", "edit_project", "Edit project", show=False),
        Binding("x", "archive_selected", "Archive", show=False),
        Binding("u", "unarchive_selected", "Unarchive", show=False),
        # Top-level shortcuts that bypass the action menu — keep
        # operator muscle memory working.
        Binding("n", "run_without_project", "New run", show=True),
        Binding("N", "new_project", "New project", show=True),
        Binding("h", "open_library", "All runs", show=False),
        Binding("a", "open_analyses", "Analyses", show=False),
        Binding("c", "open_cast", "Cast", show=False),
        Binding("S", "open_settings", "Settings", show=True),
        Binding("R", "refresh", "Refresh", show=False),
        Binding("ctrl+a", "toggle_archived", "Archived", show=False),
        # Vim nav (j/k/g/G/H/L) is provided by WonderlandApp.
    ]

    # Action menu rows — (action_id, label, description). Order is
    # discoverability-driven: open project first (most common), then
    # creation actions, then settings, then meta-browsing.
    _ACTION_ROWS: tuple[tuple[str, str, str], ...] = (
        (
            "open_project",
            "▶ Open project",
            "Pick a registered project and dive into its dashboard. "
            "From the dashboard you can review features, queue work, "
            "and launch implementation runs.",
        ),
        (
            "new_project",
            "＋ New project",
            "Register a new project — name, root path, optional "
            "starter workflow + skeleton. Once registered, the "
            "project shows up under Open project and the dashboard "
            "is one step away.",
        ),
        (
            "run_without_project",
            "▶ New run (no project)",
            "Launch a one-off run without a project context. Useful "
            "for ad-hoc work or trying out a sample directive before "
            "committing to registering a project.",
        ),
        (
            "open_settings",
            "⚙ Settings",
            "Edit user-level settings — Anthropic API key, default "
            "model, welcome-screen toggle. Stored in "
            "~/.config/wonderland/config.json.",
        ),
        (
            "open_library",
            "📁 All runs",
            "Cross-project run browser — every snapshot under the "
            "wonderland-ai checkout's runs/ and analyses/data/ "
            "trees. Useful for comparing runs across projects.",
        ),
        (
            "open_analyses",
            "📖 Analyses",
            "Browse the field-notes corpus — analyses 001..N "
            "tracking what each Wonderland run revealed about the "
            "substrate, the directives, and the agents.",
        ),
        (
            "open_release_notes",
            "📋 Release notes",
            "What shipped in each version. Newest first; "
            "markdown-rendered inline.",
        ),
        (
            "open_cast",
            "👤 The Cast",
            "Browse the ten Wonderland agents. Each card shows the "
            "character's constitution + characteristic failure mode "
            "(§VIII).",
        ),
        (
            "refresh",
            "↻ Refresh",
            "Re-read the projects registry from disk. Use after "
            "registering a project from the CLI in another terminal.",
        ),
        (
            "toggle_archived",
            "⊘ Show / hide archived projects",
            "Toggle archived projects in the Open project list. "
            "Archived projects keep their full run history; this "
            "just controls whether they appear by default.",
        ),
    )

    def __init__(self) -> None:
        super().__init__()
        self._projects: list[Project] = []
        self._show_archived = False
        # Track which detail-pane mode is active so we know whether
        # to show the project list or the action description text.
        self._detail_mode: str = "action_description"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical():
            yield Static(
                "[b]Wonderland · Home[/b]",
                id="home-title",
            )
            with Horizontal(id="home-row"):
                with Vertical(id="action-menu-pane"):
                    yield Static(
                        "[b]Actions[/b]",
                        id="action-menu-label",
                    )
                    yield DataTable(
                        id="action-table",
                        cursor_type="row",
                        show_header=False,
                    )
                with Vertical(id="detail-pane"):
                    yield Static(
                        "[b]Detail[/b]",
                        id="detail-label",
                    )
                    # The detail pane has two stacked content
                    # widgets: the action-description text (default)
                    # and the project list (shown when "Open
                    # project" is highlighted). Visibility toggles
                    # via display=True/False.
                    with VerticalScroll(id="detail-scroll"):
                        yield Static(
                            "",
                            id="detail-text",
                        )
                        yield DataTable(
                            id="project-table",
                            cursor_type="row",
                        )
                        yield Static(
                            "",
                            id="project-detail",
                        )
        yield Footer()

    def on_mount(self) -> None:
        self._populate_actions()
        self._refresh_projects()
        # Default: actions menu focused, "Open project" highlighted,
        # detail pane shows the project list preview. Operator can
        # immediately see what they have.
        self._render_for_action_row(0)
        self._focus_action_table()

    # ------------------------------------------------------------------ #
    # Population
    # ------------------------------------------------------------------ #

    def _populate_actions(self) -> None:
        """Fill the action menu. Static across the screen's lifetime."""
        table = self.query_one("#action-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Action")
        for _, label, _desc in self._ACTION_ROWS:
            table.add_row(label)
        table.cursor_coordinate = (0, 0)

    def _refresh_projects(self) -> None:
        """Re-read the projects registry. Called on mount + after
        actions that change the registry (add / archive / refresh)."""
        table = self.query_one("#project-table", DataTable)
        table.clear(columns=True)
        table.add_columns(
            "Name", "Path", "Workflow", "Last run", "Status"
        )
        self._projects = list_projects(include_archived=self._show_archived)
        for p in self._projects:
            status = (
                "[dim]archived[/dim]"
                if p.archived
                else "[green]active[/green]"
            )
            table.add_row(
                p.name,
                str(p.root_path),
                p.last_workflow or "—",
                _fmt_relative(p.created_at),
                status,
            )
        if self._projects:
            table.cursor_coordinate = (0, 0)

    # ------------------------------------------------------------------ #
    # Detail pane content driver
    # ------------------------------------------------------------------ #

    def _render_for_action_row(self, row_idx: int) -> None:
        """Update the detail pane based on which action is
        highlighted. ``open_project`` shows the project list +
        per-project metadata; everything else shows the action's
        description text."""
        if row_idx < 0 or row_idx >= len(self._ACTION_ROWS):
            return
        action_id, label, description = self._ACTION_ROWS[row_idx]

        if action_id == "open_project":
            self._show_project_list_in_detail()
        else:
            self._show_action_description(label, description)

    def _show_action_description(self, label: str, description: str) -> None:
        """Detail pane shows the highlighted action's description.
        Hides the project table since that's only relevant under
        Open project."""
        self._detail_mode = "action_description"
        self.query_one("#detail-label", Static).update("[b]Detail[/b]")
        text = self.query_one("#detail-text", Static)
        text.update(
            f"[b]{label}[/b]\n\n"
            f"{description}\n\n"
            "[dim]Press Enter (or click the row) to run this action.[/dim]"
        )
        text.display = True
        self.query_one("#project-table", DataTable).display = False
        self.query_one("#project-detail", Static).display = False

    def _show_project_list_in_detail(self) -> None:
        """Detail pane shows the project list. Below the table, a
        small Static surfaces the highlighted project's metadata.
        Operator presses Enter on Open project to focus the table,
        then Enter on a project row to open the dashboard."""
        self._detail_mode = "project_list"
        self.query_one("#detail-label", Static).update(
            "[b]Open project[/b]  "
            "[dim](Enter focuses the list)[/dim]"
        )
        text = self.query_one("#detail-text", Static)
        if not self._projects:
            text.update(
                "[b yellow]No projects registered yet.[/b yellow]\n\n"
                "[dim]Press [b]N[/b] (uppercase) or pick "
                "[b]＋ New project[/b] from the actions menu to "
                "register one. Or run [b]wonderland project add NAME "
                "PATH[/b] from a shell, then [b]R[/b] to refresh."
                "[/dim]"
            )
            text.display = True
            self.query_one("#project-table", DataTable).display = False
            self.query_one("#project-detail", Static).display = False
            return
        text.update(
            "[dim]These are your registered projects. Press Enter "
            "on this row to focus the list, then Enter on a project "
            "to open its dashboard.[/dim]"
        )
        text.display = True
        self.query_one("#project-table", DataTable).display = True
        detail = self.query_one("#project-detail", Static)
        detail.display = True
        # Render metadata for the currently-highlighted project.
        table = self.query_one("#project-table", DataTable)
        row = table.cursor_row if table.cursor_row is not None else 0
        if 0 <= row < len(self._projects):
            self._render_project_detail(self._projects[row])

    def _render_project_detail(self, project: Project) -> None:
        """Per-project metadata displayed below the project table
        when Open project is the active mode."""
        lines = [
            f"[b]{project.name}[/b]",
            "",
            f"[b]Path:[/b] {project.root_path}",
            f"[b]Created:[/b] {project.created_at.strftime('%Y-%m-%d %H:%M UTC')}",
            f"[b]Last workflow:[/b] {project.last_workflow or '[dim](none yet)[/dim]'}",
            f"[b]Skeleton:[/b] {project.default_skeleton or '[dim](none)[/dim]'}",
            f"[b]Default budget:[/b] ${project.default_budget:.2f}",
        ]
        if project.last_run_id:
            lines.append(f"[b]Last run:[/b] {project.last_run_id}")
        else:
            lines.append("[b]Last run:[/b] [dim](none yet)[/dim]")
        if project.archived:
            lines.extend([
                "",
                "[b yellow]Archived[/b yellow] — press [b]u[/b] to unarchive.",
            ])
        prefs = project.notification_prefs
        lines.extend([
            "",
            "[b]Notifications:[/b]",
            f"  · OS: {'on' if prefs.os_notification else 'off'}",
            f"  · Audible chime: {'on' if prefs.audible_chime else 'off'}",
            f"  · Terminal bell: {'on' if prefs.terminal_bell else 'off'}",
            "",
            "[dim]Press Enter to open the dashboard for this project. "
            "[b]e[/b] edit · [b]x[/b] archive · [b]u[/b] unarchive[/dim]",
        ])
        self.query_one("#project-detail", Static).update("\n".join(lines))

    # ------------------------------------------------------------------ #
    # Selection wiring
    # ------------------------------------------------------------------ #

    def on_data_table_row_highlighted(
        self, event: DataTable.RowHighlighted
    ) -> None:
        """Action highlighted → swap detail pane.
        Project highlighted (only relevant in open_project mode) →
        update per-project metadata."""
        tid = event.data_table.id
        if tid == "action-table":
            row = event.cursor_row
            if row is not None and 0 <= row < len(self._ACTION_ROWS):
                self._render_for_action_row(row)
        elif tid == "project-table":
            row = event.cursor_row
            if row is not None and 0 <= row < len(self._projects):
                self._render_project_detail(self._projects[row])

    def on_data_table_row_selected(
        self, event: DataTable.RowSelected
    ) -> None:
        """Enter on action row dispatches the action; on project
        row opens the dashboard."""
        tid = event.data_table.id
        if tid == "action-table":
            row = event.cursor_row
            if row is None or not (0 <= row < len(self._ACTION_ROWS)):
                return
            action_id, _label, _desc = self._ACTION_ROWS[row]
            if action_id == "open_project":
                # Focus the project table for picking — Enter again
                # opens the highlighted project.
                self._focus_project_table()
                return
            handler = getattr(self, f"action_{action_id}", None)
            if handler is not None:
                handler()
        elif tid == "project-table":
            self.action_open_selected()

    def _focus_action_table(self) -> None:
        try:
            self.query_one("#action-table", DataTable).focus()
        except Exception:  # noqa: BLE001
            pass

    def _focus_project_table(self) -> None:
        try:
            self.query_one("#project-table", DataTable).focus()
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #

    def action_activate(self) -> None:
        """Generic Enter — dispatch to whichever table is focused.
        DataTable's default row-selected handler covers this; this
        action exists so the Enter binding is visible in the footer."""
        focused = self.focused
        if isinstance(focused, DataTable):
            focused.action_select_cursor()

    def action_refresh(self) -> None:
        self._refresh_projects()
        # Re-render whichever mode is active so the new state lands.
        if self._detail_mode == "project_list":
            self._show_project_list_in_detail()

    def action_toggle_archived(self) -> None:
        self._show_archived = not self._show_archived
        self.notify(
            f"Archived projects: {'shown' if self._show_archived else 'hidden'}",
            timeout=2,
        )
        self._refresh_projects()
        if self._detail_mode == "project_list":
            self._show_project_list_in_detail()

    def _selected_project(self) -> Project | None:
        try:
            table = self.query_one("#project-table", DataTable)
        except Exception:  # noqa: BLE001
            return None
        row = table.cursor_row
        if row is None or row < 0 or row >= len(self._projects):
            return None
        return self._projects[row]

    def action_open_selected(self) -> None:
        """Open the dashboard for the selected project."""
        project = self._selected_project()
        if project is None:
            self.notify(
                "No project selected — register one with "
                "`wonderland project add` or pick ＋ New project.",
                severity="warning",
            )
            return
        if project.archived:
            self.notify(
                "Selected project is archived — unarchive it first (u).",
                severity="warning",
            )
            return
        from wonderland.tui.screens.project_dashboard import (
            ProjectDashboardScreen,
        )

        self.app.push_screen(ProjectDashboardScreen(project))

    def action_run_without_project(self) -> None:
        from wonderland.tui.screens.new_run import NewRunScreen

        self.app.push_screen(NewRunScreen())

    def action_new_project(self) -> None:
        from wonderland.tui.screens.new_project import NewProjectScreen

        self.app.push_screen(NewProjectScreen(), self._on_new_project_done)

    def _on_new_project_done(self, project: Project | None) -> None:
        self._refresh_projects()
        if project is None:
            return
        # Move to "Open project" action so the new project is visible.
        action_table = self.query_one("#action-table", DataTable)
        action_table.cursor_coordinate = (0, 0)
        self._render_for_action_row(0)
        # Cursor onto the new project in the project table.
        for i, p in enumerate(self._projects):
            if p.name == project.name:
                table = self.query_one("#project-table", DataTable)
                table.cursor_coordinate = (i, 0)
                break

    def action_edit_project(self) -> None:
        project = self._selected_project()
        if project is None:
            self.notify(
                "No project selected — focus the project list first.",
                severity="warning",
            )
            return
        from wonderland.tui.screens.edit_project import EditProjectScreen

        self.app.push_screen(
            EditProjectScreen(project), self._on_edit_project_done
        )

    def _on_edit_project_done(self, project: Project | None) -> None:
        prior_name = project.name if project is not None else None
        self._refresh_projects()
        if prior_name is None:
            return
        for i, p in enumerate(self._projects):
            if p.name == prior_name:
                table = self.query_one("#project-table", DataTable)
                table.cursor_coordinate = (i, 0)
                break

    def action_archive_selected(self) -> None:
        project = self._selected_project()
        if project is None or project.archived:
            return
        archive_project(project.name)
        self.notify(f"Archived: {project.name}", timeout=3)
        self._refresh_projects()
        if self._detail_mode == "project_list":
            self._show_project_list_in_detail()

    def action_unarchive_selected(self) -> None:
        project = self._selected_project()
        if project is None or not project.archived:
            return
        unarchive_project(project.name)
        self.notify(f"Unarchived: {project.name}", timeout=3)
        self._refresh_projects()
        if self._detail_mode == "project_list":
            self._show_project_list_in_detail()

    def action_open_library(self) -> None:
        from pathlib import Path as _P
        from wonderland.tui.screens.snapshot_library import SnapshotLibraryScreen

        root = getattr(self.app, "snapshot_root", _P.cwd())
        self.app.push_screen(SnapshotLibraryScreen(root))

    def action_open_analyses(self) -> None:
        from wonderland.tui.screens.analyses import AnalysesScreen

        self.app.push_screen(AnalysesScreen())

    def action_open_release_notes(self) -> None:
        from wonderland.tui.screens.release_notes import (
            ReleaseNotesScreen,
        )

        self.app.push_screen(ReleaseNotesScreen())

    def action_open_cast(self) -> None:
        from wonderland.tui.screens.cast import CastBrowserScreen

        self.app.push_screen(CastBrowserScreen())

    def action_open_settings(self) -> None:
        from wonderland.tui.screens.settings import SettingsScreen

        self.app.push_screen(SettingsScreen())

    def action_open_project(self) -> None:
        """Operator-typed shortcut for landing on the Open project
        action without going through the action table. Highlights
        the action and focuses the project table directly."""
        action_table = self.query_one("#action-table", DataTable)
        action_table.cursor_coordinate = (0, 0)
        self._render_for_action_row(0)
        if self._projects:
            self._focus_project_table()


__all__ = ["ProjectLibraryScreen"]
