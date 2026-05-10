"""ProjectLibraryScreen — the TUI's new home (P11 T75).

Replaces SnapshotLibraryScreen as the landing screen. Operators land
on a list of registered projects with per-project metadata + last-run
summary; runs without a project context still work (back-compat) via
the 'r' key which pushes NewRunScreen with no Project attached.

Lazygit-shape per project_tui_lazygit_principle: project list left,
metadata + recent-run summary right. The right pane updates on row
highlight (selection-driven population).

P11 chunk T74→T75→T78 wires:
  - enter: open NewRunScreen with the highlighted project's defaults
    pre-filled (T78 reads the project context)
  - n: hint to use ``wonderland project add`` from CLI (T76 ships
    the proper TUI form later)
  - e: hint to use ``wonderland project edit`` (T77 ships TUI form)
  - a: archive selected project
  - r: 'run without project' — push NewRunScreen with no context
  - L: open the cross-project Snapshot Library (for browsing all runs
    regardless of project association — useful while transitioning)
  - S: settings, A: analyses, c: cast, q: quit (top-level concerns)
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Static

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
    """Lists registered projects; selecting one launches the run flow
    with the project's defaults pre-filled."""

    BINDINGS = [
        Binding("enter", "open_selected", "Open dashboard", show=True),
        # 'd' kept as an explicit alias — most operators will use
        # Enter, but the keybind reads cleanly in the footer hint and
        # supports vim-style "press d to dive into details" muscle
        # memory.
        Binding("d", "open_selected", "Dashboard", show=False),
        # Legacy muscle memory: 'n' opens NewRunScreen (no project
        # context, same as pre-P11). 'N' (uppercase) opens the new
        # project form. The compromise keeps every test that pressed
        # 'n' on the home screen working without modification.
        Binding("n", "run_without_project", "New run", show=True),
        Binding("N", "new_project", "New project", show=True),
        Binding("e", "edit_project", "Edit", show=True),
        Binding("x", "archive_selected", "Archive", show=True),
        Binding("u", "unarchive_selected", "Unarchive", show=True),
        # 'h' for history — 'L' is reserved by WonderlandApp for vim
        # bottom-jump (priority=True). 'h' is free at app level
        # (lowercase isn't bound; only 'H' is taken).
        Binding("h", "open_library", "All runs", show=True),
        # Lowercase 'a' on the old SnapshotLibrary opened the analyses
        # screen; preserve that muscle memory here too.
        Binding("a", "open_analyses", "Analyses", show=True),
        Binding("c", "open_cast", "Cast", show=True),
        Binding("S", "open_settings", "Settings", show=True),
        Binding("R", "refresh", "Refresh", show=True),
        Binding("ctrl+a", "toggle_archived", "Show archived", show=True),
        # Vim nav (j/k/g/G/H/L) is provided by WonderlandApp.
    ]

    # Action menu rows — each entry is (action_id, label, description).
    # Highlighting a row populates the detail pane with the description;
    # pressing Enter on a row dispatches to action_<action_id>().
    # Project-context actions live in the bottom button row, not here —
    # this menu is for things you can do regardless of selection.
    _ACTION_ROWS: tuple[tuple[str, str, str], ...] = (
        (
            "run_without_project",
            "▶ New run",
            "Launch a one-off run without a project context. Same flow "
            "as before P11 — operator types path / picks workflow / "
            "etc. manually. Use this for ad-hoc work or when you "
            "don't want to register a project yet.",
        ),
        (
            "open_analyses",
            "📖 Analyses",
            "Browse the field-notes corpus — analyses 001..N tracking "
            "what each Wonderland run revealed about the substrate, "
            "the directives, and the agents. The project's running "
            "lab notebook.",
        ),
        (
            "open_cast",
            "👤 The Cast",
            "Browse the ten Wonderland agents — Alice, the Cheshire "
            "Cat, the White Rabbit, the Dodo, the Mad Hatter, the "
            "Caterpillar, the Queen of Hearts, the Dormouse, "
            "Tweedledee + Tweedledum. Each card shows the character's "
            "constitution + characteristic failure mode (§VIII).",
        ),
        (
            "open_library",
            "📁 All runs",
            "Cross-project run browser — every snapshot under the "
            "wonderland-ai checkout's runs/ + analyses/data/ trees. "
            "Pre-P11 this was the TUI's home; now it's a sub-screen "
            "for cases where you want to compare runs across "
            "projects.",
        ),
        (
            "open_settings",
            "⚙ Settings",
            "Edit user-level settings — Anthropic API key + default "
            "model. Stored in ~/.config/wonderland/config.json (or "
            "the env var path). Project-level overrides land in T77.",
        ),
        (
            "refresh",
            "↻ Refresh",
            "Re-read the projects registry from disk. Use after "
            "registering a project from the CLI in another terminal.",
        ),
        (
            "toggle_archived",
            "⊘ Show archived",
            "Toggle archived projects in the list. Archived projects "
            "still have their full run history; they just don't "
            "clutter the active view.",
        ),
    )

    def __init__(self) -> None:
        super().__init__()
        self._projects: list[Project] = []
        self._show_archived = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical():
            yield Static("[b]Wonderland · Projects[/b]", id="home-title")
            # Three-column row: project list (with project-context
            # buttons stacked under it), action menu, detail pane.
            # The project buttons sit directly under the projects
            # list — visually grouping the affordance with the data
            # it acts on. Detail pane updates based on which table is
            # highlighted (project rows → project metadata; action
            # rows → action description).
            with Horizontal(id="project-library-row"):
                with Vertical(id="project-list-pane"):
                    yield Static(
                        "[b]Projects[/b]",
                        id="project-list-label",
                    )
                    yield DataTable(
                        id="project-table",
                        cursor_type="row",
                    )
                    # Big stacked buttons under the project list —
                    # full-column-width, visually prominent so they
                    # read as the primary call-to-action for whatever
                    # is selected above. Open-dashboard is the
                    # entrypoint for "act on this project"; run
                    # launches happen from inside the dashboard.
                    with Vertical(id="project-list-buttons"):
                        yield Button(
                            "▶ Open dashboard",
                            id="open-button",
                            variant="primary",
                        )
                        yield Button(
                            "＋ New project",
                            id="new-project-button",
                        )
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
                with Vertical(id="project-detail-pane"):
                    yield Static(
                        "[b]Detail[/b]",
                        id="project-detail-label",
                    )
                    with VerticalScroll(id="project-detail-scroll"):
                        yield Static(
                            "[dim](no project selected)[/dim]",
                            id="project-detail",
                        )
        yield Footer()

    def on_mount(self) -> None:
        self._populate_actions()
        self._populate()

    # ------------------------------------------------------------------ #
    # Population
    # ------------------------------------------------------------------ #

    def _populate(self) -> None:
        table = self.query_one("#project-table", DataTable)
        table.clear(columns=True)
        table.add_columns(
            "Name", "Path", "Workflow", "Last run", "Status"
        )
        self._projects = list_projects(include_archived=self._show_archived)
        if not self._projects:
            self._render_empty_state()
            self._focus_action_table()
            return
        for p in self._projects:
            status = "[dim]archived[/dim]" if p.archived else "[green]active[/green]"
            table.add_row(
                p.name,
                str(p.root_path),
                p.last_workflow or "—",
                _fmt_relative(p.created_at if p.last_run_id is None else p.created_at),
                status,
            )
        table.cursor_coordinate = (0, 0)
        self._render_detail(self._projects[0])
        # Default focus is the actions menu (per project-library UX
        # decision): the operator can immediately read what's
        # available, then Tab to the project list when they want to
        # pick one.
        self._focus_action_table()

    def _focus_action_table(self) -> None:
        """Move keyboard focus to the actions menu — the default
        landing point for the screen. Pulled out so both populated
        and empty-state branches share the call site."""
        try:
            self.query_one("#action-table", DataTable).focus()
        except Exception:  # noqa: BLE001
            # Action table may not exist yet during early mount;
            # populate is occasionally called from places where
            # the action-table widget isn't realized.
            pass

    def _render_empty_state(self) -> None:
        """First-time state — no projects yet. Detail pane explains
        how to register one. The actions menu (middle pane) and the
        '＋ New project' button at the bottom both lead the operator
        into NewProjectScreen."""
        detail = self.query_one("#project-detail", Static)
        detail.update(
            "[b yellow]No projects registered yet.[/b yellow]\n\n"
            "Get started:\n\n"
            "  [b]1.[/b] Click [b]＋ New project[/b] at the bottom\n"
            "      (or press [b]N[/b]) to open the registration form.\n\n"
            "  [b]2.[/b] Fill in name + path (and optionally pick a\n"
            "      starter workflow + skeleton). Press [b]ctrl+s[/b] to\n"
            "      create.\n\n"
            "  [b]3.[/b] Press [b]Enter[/b] on the new row to launch a run\n"
            "      with the project's defaults.\n\n"
            "[dim]Alternative: run [b]wonderland project add NAME PATH[/b] "
            "from a shell, then refresh (R or the [italic]↻ Refresh[/italic] "
            "action).[/dim]\n\n"
            "[dim]Browse the actions menu in the middle column — "
            "highlighting an action shows its description here.[/dim]"
        )

    def _render_detail(self, project: Project) -> None:
        detail = self.query_one("#project-detail", Static)
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
        ])
        lines.extend([
            "",
            "[dim]Press [b]Enter[/b] to launch a new run with this "
            "project's defaults.[/dim]",
        ])
        detail.update("\n".join(lines))

    # ------------------------------------------------------------------ #
    # Selection-driven population
    # ------------------------------------------------------------------ #

    def _populate_actions(self) -> None:
        """Fill the action menu with the static row set defined on
        the class. Run once at on_mount; the action set doesn't change
        during the screen's lifetime."""
        table = self.query_one("#action-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Action")
        for _, label, _desc in self._ACTION_ROWS:
            table.add_row(label)

    def on_data_table_row_highlighted(
        self, event: DataTable.RowHighlighted
    ) -> None:
        """Selection-driven detail pane: project rows render metadata;
        action rows render the action's description."""
        if event.data_table.id == "project-table":
            row = event.cursor_row
            if row is None or row < 0 or row >= len(self._projects):
                return
            self._render_detail(self._projects[row])
        elif event.data_table.id == "action-table":
            row = event.cursor_row
            if row is None or row < 0 or row >= len(self._ACTION_ROWS):
                return
            self._render_action_description(row)

    def _render_action_description(self, row_idx: int) -> None:
        """Show the highlighted action's description in the detail
        pane. Operator can read what an action does before pressing
        Enter on it — the pattern most lazygit-shaped TUIs use for
        their command palettes.

        Empty-state suppression: when no projects are registered, the
        detail pane shows the first-time guidance permanently — action
        hovers don't overwrite it. The operator's first job is to
        create a project; once they have one, action descriptions
        become available.
        """
        if not self._projects:
            return
        action_id, label, description = self._ACTION_ROWS[row_idx]
        detail = self.query_one("#project-detail", Static)
        detail.update(
            f"[b]{label}[/b]\n\n"
            f"{description}\n\n"
            "[dim]Press Enter (or click the row) to run this action.[/dim]"
        )

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #

    def action_refresh(self) -> None:
        self._populate()

    def action_toggle_archived(self) -> None:
        self._show_archived = not self._show_archived
        self.notify(
            f"Archived projects: {'shown' if self._show_archived else 'hidden'}",
            timeout=2,
        )
        self._populate()

    def _selected_project(self) -> Project | None:
        table = self.query_one("#project-table", DataTable)
        row = table.cursor_row
        if row is None or row < 0 or row >= len(self._projects):
            return None
        return self._projects[row]

    def action_open_selected(self) -> None:
        """Open the dashboard for the selected project. From the
        dashboard's actions pane the operator can launch a new run,
        edit defaults, etc. — the library is for *picking* a project,
        the dashboard is for *acting on* one."""
        project = self._selected_project()
        if project is None:
            self.notify(
                "No project selected — register one with "
                "`wonderland project add` first.",
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
        """Back-compat path — push NewRunScreen with no project
        context. Operator types path / picks workflow / etc. manually,
        same as before P11."""
        from wonderland.tui.screens.new_run import NewRunScreen

        self.app.push_screen(NewRunScreen())

    def action_new_project(self) -> None:
        """Push the NewProjectScreen registration form (T76). On
        successful registration: refresh the library so the new
        project appears immediately."""
        from wonderland.tui.screens.new_project import NewProjectScreen

        self.app.push_screen(NewProjectScreen(), self._on_new_project_done)

    def _on_new_project_done(self, project: Project | None) -> None:
        """Callback for NewProjectScreen.dismiss — None means cancel,
        a Project means the operator created one. Either way: refresh
        the table so the new project is visible (and selected if
        we got one back)."""
        self._populate()
        if project is None:
            return
        # Move the cursor to the newly registered project so the
        # detail pane shows it. list is alphabetically sorted, so
        # find the row by name.
        for i, p in enumerate(self._projects):
            if p.name == project.name:
                table = self.query_one("#project-table", DataTable)
                table.cursor_coordinate = (i, 0)
                break

    def action_edit_project(self) -> None:
        """Push the EditProjectScreen for the currently-selected
        project (T77). On save: refresh the library so the updated
        defaults render immediately."""
        project = self._selected_project()
        if project is None:
            self.notify("No project selected.", severity="warning")
            return
        from wonderland.tui.screens.edit_project import EditProjectScreen

        self.app.push_screen(
            EditProjectScreen(project), self._on_edit_project_done
        )

    def _on_edit_project_done(self, project: Project | None) -> None:
        """Callback for EditProjectScreen.dismiss. Either way, refresh
        the table so any updates render. Re-cursors onto the same
        project by name to preserve focus."""
        prior_name = project.name if project is not None else None
        self._populate()
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
        self._populate()

    def action_unarchive_selected(self) -> None:
        project = self._selected_project()
        if project is None or not project.archived:
            return
        unarchive_project(project.name)
        self.notify(f"Unarchived: {project.name}", timeout=3)
        self._populate()

    def action_open_library(self) -> None:
        """All-runs view — pushes the existing SnapshotLibraryScreen
        for cross-project run browsing."""
        from pathlib import Path as _P  # local import to avoid TC clash
        from wonderland.tui.screens.snapshot_library import SnapshotLibraryScreen

        # Snapshot library walks the wonderland-ai checkout's runs/
        # and analyses/data/ trees. Reuse the app's snapshot_root
        # (set by WonderlandApp.__init__).
        root = getattr(self.app, "snapshot_root", _P.cwd())
        self.app.push_screen(SnapshotLibraryScreen(root))

    def action_open_analyses(self) -> None:
        from wonderland.tui.screens.analyses import AnalysesScreen

        self.app.push_screen(AnalysesScreen())

    def action_open_cast(self) -> None:
        from wonderland.tui.screens.cast import CastBrowserScreen

        self.app.push_screen(CastBrowserScreen())

    def action_open_settings(self) -> None:
        from wonderland.tui.screens.settings import SettingsScreen

        self.app.push_screen(SettingsScreen())

    # ------------------------------------------------------------------ #
    # Button routing
    # ------------------------------------------------------------------ #

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "open-button":
            self.action_open_selected()
        elif event.button.id == "new-project-button":
            self.action_new_project()

    def on_data_table_row_selected(
        self, event: DataTable.RowSelected
    ) -> None:
        """Enter on a project row → open run; enter on an action row
        → dispatch that action by name."""
        if event.data_table.id == "project-table":
            self.action_open_selected()
        elif event.data_table.id == "action-table":
            row = event.cursor_row
            if row is None or row < 0 or row >= len(self._ACTION_ROWS):
                return
            action_id, _label, _desc = self._ACTION_ROWS[row]
            handler = getattr(self, f"action_{action_id}", None)
            if handler is not None:
                handler()


__all__ = ["ProjectLibraryScreen"]
