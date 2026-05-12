"""NewRunScreen — compose and launch a run.

Three regions:
  - **Preset picker** (left): DataTable of bundled + per-project
    directive presets. Selecting one populates the directive composer
    and pre-selects the suggested workflow.
  - **Directive composer** (right): TextArea for the actual directive
    text. Preset picks are starting points; user can edit freely.
  - **Configuration** (bottom): workflow picker, project-root input,
    budget input. Pre-filled from the selected preset's hints.

Per the project_tui_lazygit_principle memory: multi-pane, focusable
Tab cycle, no modals except for the launch confirmation (because
burning $3-5 should require deliberate consent).

T51 ships layout + state-only. T53 wires the Go button.
"""

from __future__ import annotations

from pathlib import Path

import os

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    Checkbox,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
    TextArea,
)

from wonderland.config import load_config
from wonderland.directive import (
    DirectivePreset,
    list_directives,
    list_project_directives,
    load_directive,
    load_project_directive,
    save_directive,
)
from wonderland.project import Project, save_project
from wonderland.skeleton import is_bare_project_root
from wonderland.tui.screens.launch_confirmation import LaunchConfirmationScreen
from wonderland.tui.screens.settings import SettingsScreen
from wonderland.tui.screens.skeleton_picker import SkeletonPickerScreen
from wonderland.workflow import Workflow, list_workflows, load_workflow


# Sentinel name for the "blank directive" pseudo-row at the top of
# the preset table — selecting it clears the composer + description
# so the user starts fresh.
_BLANK_PRESET = "__blank__"
_PRIME_PRESET = "__prime__"


class NewRunScreen(Screen[None]):
    """Compose a directive + workflow + project, launch a run.

    T51 scope: layout, preset selection populates the composer,
    workflow picker exposes bundled options, project + budget inputs
    accept text. The Go button is a stub until T53 wires the launch.
    """

    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
        Binding("g", "go", "Go", show=True),
        Binding("s", "save_as_preset", "Save preset", show=True),
        # Vim nav (j/k/g/G/H/L) is provided by WonderlandApp.
    ]

    # Form field order — Enter advances through these in sequence
    # (single-field widgets advance on plain Enter; TextAreas need
    # Tab since they consume Enter as a newline by default).
    # Last entry is the Go button; advancing past the name input
    # focuses Go so the user can press Enter to confirm-and-launch.
    _FORM_ORDER: tuple[str, ...] = (
        "preset-table",
        "directive-composer",
        "description-composer",
        "save-checkbox",
        "save-name-input",
        "workflow-table",
        "project-input",
        "budget-input",
        "go-button",
    )

    def __init__(
        self,
        project_root: Path | None = None,
        *,
        project: Project | None = None,
        default_workflow: str | None = None,
        default_directive: str | None = None,
    ) -> None:
        super().__init__()
        # P11: when a Project is supplied, prefill defaults from it
        # (workflow, budget, project_root). The operator can still
        # override per-run; their edits don't mutate the project's
        # stored defaults. When project is None, fall back to legacy
        # behavior (project_root=cwd or supplied path).
        self.project: Project | None = project
        if project is not None:
            self.project_root = project.root_path
        else:
            # Legacy path — project_root only, no project context.
            # Default is cwd for users running wonderland-tui from
            # inside the project they want to operate on.
            self.project_root = project_root or Path.cwd()
        # T92 path: dashboard's Implement/Design buttons pass these
        # so operator lands on NewRunScreen with workflow + directive
        # pre-filled. Operator can still edit either before launching.
        # default_workflow overrides the project's last_workflow if
        # both are set; explicit-from-action-button > project default.
        self._default_workflow = default_workflow
        self._default_directive = default_directive
        # Cache of (display_name, preset) tuples in display order so
        # row index → preset is a constant-time lookup.
        self._presets: list[tuple[str, DirectivePreset]] = []
        # Same shape for the workflow picker — parallel list of
        # (name, workflow) tuples. None payload = separator row.
        self._workflows: list[tuple[str, Workflow | None]] = []
        # Currently-selected workflow name; replaces the legacy
        # Select widget. None until the user picks a row OR a
        # default lands via on_mount.
        self._selected_workflow_name: str | None = None
        # Per-meeting enable/disable state for the currently-
        # selected workflow. Map of meeting_id → enabled bool;
        # rebuilt on workflow selection. Pre-filled True for all
        # meetings. Wiring to actually skip disabled meetings on
        # launch lands in a follow-on — the UI surface is here as
        # the foundation for the broader run-config knob set.
        self._meeting_enabled: dict[str, bool] = {}
        # Track whether the operator has explicitly OK'd launching
        # without a directive (via the empty-directive confirmation
        # modal). Lets the team work from seeds alone (features /
        # tickets / contracts on disk) for workflows like
        # tdd-implement where the lifecycle artifacts are the
        # directive.
        self._empty_directive_confirmed: bool = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical():
            if self.project is not None:
                yield Static(
                    f"[b]New run[/b] · project [accent]{self.project.name}[/accent] "
                    "· pick a preset or write fresh",
                    id="new-run-header",
                )
            else:
                yield Static(
                    "[b]New run[/b] · pick a preset or write fresh "
                    "[dim](no project context)[/dim]",
                    id="new-run-header",
                )

            # ── Row 1: directives ───────────────────────────────
            # Three-pane row mirroring the workflow row below.
            # Left: preset picker. Middle: directive composer.
            # Right: directive description (the saved-preset summary)
            # plus the save-as-preset controls tucked underneath
            # since they belong to the directive shape.
            with Horizontal(id="directive-row"):
                with Vertical(id="preset-pane"):
                    yield Static("[b]Directives[/b]", id="preset-label")
                    yield DataTable(
                        id="preset-table",
                        cursor_type="row",
                    )
                with Vertical(id="composer-pane"):
                    yield Static("[b]Directive[/b]", id="composer-label")
                    yield TextArea(
                        "",
                        id="directive-composer",
                        language=None,  # plain text
                    )
                with Vertical(id="directive-summary-pane"):
                    yield Static(
                        "[b]Description[/b] "
                        "[dim](optional — used if saved as preset)[/dim]",
                        id="description-label",
                    )
                    yield TextArea(
                        "",
                        id="description-composer",
                        language=None,
                    )
                    yield Static(
                        "[b]Save as preset[/b]",
                        id="save-section-label",
                    )
                    yield Checkbox(
                        "Save current directive",
                        value=False,
                        id="save-checkbox",
                    )
                    yield Input(
                        placeholder="my-directive-name",
                        id="save-name-input",
                    )

            # ── Row 2: workflows ────────────────────────────────
            # Same three-pane shape: picker, meetings list with
            # enable/disable checkboxes, workflow summary.
            with Horizontal(id="workflow-row"):
                with Vertical(id="workflow-pane"):
                    yield Static(
                        "[b]Workflows[/b]", id="workflow-label"
                    )
                    yield DataTable(
                        id="workflow-table",
                        cursor_type="row",
                    )
                with Vertical(id="workflow-meetings-pane"):
                    yield Static(
                        "[b]Meetings[/b]", id="workflow-meetings-label"
                    )
                    # Container that holds dynamically-added Checkbox
                    # widgets — rebuilt on workflow selection.
                    yield Vertical(id="meetings-list")
                with Vertical(id="workflow-summary-pane"):
                    yield Static(
                        "[b]About this workflow[/b]",
                        id="workflow-summary-label",
                    )
                    yield Static(
                        "[dim]Pick a workflow from the left to see "
                        "its summary.[/dim]",
                        id="workflow-summary",
                    )

            # ── Row 3: run controls ─────────────────────────────
            # Project root, budget, action buttons. Smaller / denser
            # than the two pane rows — these are top-level run knobs
            # that don't need a full pane each.
            yield Static("[b]Run controls[/b]", id="controls-label")
            with Horizontal(id="controls-row"):
                yield Label("Project root:", id="project-label")
                yield Input(
                    value=str(self.project_root),
                    placeholder="/path/to/project",
                    id="project-input",
                )
                yield Label("Budget:", id="budget-label")
                budget_value = (
                    f"{self.project.default_budget:.2f}"
                    if self.project is not None
                    else "5.00"
                )
                yield Input(
                    value=budget_value,
                    placeholder="$ — soft cap",
                    id="budget-input",
                )
                # Auto-merge: when checked, the run-bg subprocess
                # attempts a fast-forward merge of the run branch
                # back into the source branch on clean completion.
                # FF-only — if the source moved during the run, the
                # branch stays in place for manual resolution.
                yield Checkbox(
                    "Auto-merge branch on success",
                    value=False,
                    id="auto-merge-checkbox",
                )
                yield Button(
                    "▶ Go (g)",
                    id="go-button",
                    variant="primary",
                )
                yield Button(
                    "Cancel (esc)",
                    id="cancel-button",
                )
        yield Footer()

    def on_mount(self) -> None:
        # Populate the preset table.
        self._populate_presets()
        # T92 path: explicit default_workflow from a state-aware
        # action button takes precedence over project.last_workflow.
        # Falls back to project's last workflow when no explicit
        # default was passed.
        target_workflow: str | None = None
        if (
            self._default_workflow
            and self._default_workflow in list_workflows()
        ):
            target_workflow = self._default_workflow
        elif (
            self.project is not None
            and self.project.last_workflow
            and self.project.last_workflow in list_workflows()
        ):
            target_workflow = self.project.last_workflow

        # Populate the workflow table + select the default row if
        # there's a target. Falls back to whatever the first non-
        # separator row is when target isn't bundled, so the user
        # always lands on something concrete in the meetings pane.
        self._populate_workflow_table()
        if target_workflow:
            self._select_workflow_by_name(target_workflow)

        # T92 path: pre-fill the directive textarea when the action
        # button supplied one. Deferred via call_after_refresh because
        # _populate_presets queues a row_highlighted event for the
        # blank-preset row that clears the composer; we need our
        # default to win over that clear, which means setting it
        # after the highlighted-row handler runs.
        if self._default_directive is not None:
            self.call_after_refresh(self._apply_default_directive)

        # Focus the preset table by default — j/k navigates presets,
        # Enter selects, Tab moves to the composer.
        self.query_one("#preset-table", DataTable).focus()

    def _apply_default_directive(self) -> None:
        """Set the composer textarea to the operator-supplied default
        directive. Called via call_after_refresh from on_mount so
        we land after the blank-preset row_highlighted handler
        clears the composer."""
        if self._default_directive is None:
            return
        try:
            self.query_one(
                "#directive-composer", TextArea
            ).text = self._default_directive
        except Exception:  # noqa: BLE001
            pass

    def _populate_presets(self) -> None:
        """Build the preset table from bundled + per-project sources.
        Order: blank pseudo-row → bundled → divider → project-local.
        Cached as ``self._presets`` for row-index → preset lookup.
        Entries with None payload are non-selectable separators."""
        table = self.query_one("#preset-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Name", "Title", "Workflow")

        self._presets = []

        # Row 0 — blank pseudo-row. Selecting it clears the composer
        # + description so the user starts fresh.
        self._presets.append((_BLANK_PRESET, None))  # type: ignore[arg-type]
        table.add_row(
            "[b]── new blank ──[/b]",
            "[dim]start with empty fields[/dim]",
            "—",
        )

        # Row 1 — project's prime directive (the canonical "what is
        # this project for" preset). Only surfaces when a Project is
        # bound and a prime_directive has been captured. Auto-set on
        # the first non-empty directive launched against the project
        # (see _launch_run); operator can edit + re-save to update.
        if (
            self.project is not None
            and self.project.prime_directive is not None
            and self.project.prime_directive.strip()
        ):
            self._presets.append((_PRIME_PRESET, None))  # type: ignore[arg-type]
            table.add_row(
                "[b accent]★ prime[/b accent]",
                f"[dim]project canonical · "
                f"{self.project.prime_directive.strip().splitlines()[0][:50]}"
                "[/dim]",
                self.project.last_workflow or "—",
            )

        # Bundled — grouped by category with separator rows. Within
        # a category, presets sort alphabetically by name (the
        # filesystem order from list_directives). Categories
        # themselves sort alphabetically with 'other' pinned last so
        # uncategorized presets cluster at the bottom of the bundled
        # section. Case-insensitive comparison via normalized_category.
        bundled: list[tuple[str, DirectivePreset]] = []
        for name in list_directives():
            try:
                p = load_directive(name)
            except Exception:  # noqa: BLE001 — best-effort listing
                continue
            bundled.append((name, p))
        self._render_preset_group(table, bundled)

        # Project — inserted only when there's at least one. Same
        # category grouping applies to the project-local section.
        if self.project_root and self.project_root.is_dir():
            project_names = list_project_directives(self.project_root)
            if project_names:
                self._presets.append(("", None))  # type: ignore[arg-type]
                table.add_row(
                    "[dim]──── project ────[/dim]", "", ""
                )
                project_loaded: list[tuple[str, DirectivePreset]] = []
                for name in project_names:
                    try:
                        p = load_project_directive(name, self.project_root)
                    except Exception:  # noqa: BLE001
                        continue
                    project_loaded.append((name, p))
                self._render_preset_group(table, project_loaded)

    def _render_preset_group(
        self,
        table: "DataTable",
        items: list[tuple[str, "DirectivePreset"]],
    ) -> None:
        """Append a list of presets to the table grouped by category.
        Category headers are non-selectable separator rows (None
        payload). 'other' sorts last so uncategorized presets don't
        appear above categorized ones."""
        if not items:
            return
        by_category: dict[str, list[tuple[str, "DirectivePreset"]]] = {}
        for name, preset in items:
            by_category.setdefault(
                preset.normalized_category, []
            ).append((name, preset))

        def _category_sort_key(cat: str) -> tuple[int, str]:
            return (1 if cat == "other" else 0, cat)

        for category in sorted(by_category, key=_category_sort_key):
            entries = by_category[category]
            self._presets.append(("", None))  # type: ignore[arg-type]
            table.add_row(
                f"[dim]── {category} ──[/dim]", "", ""
            )
            for name, preset in entries:
                self._presets.append((name, preset))
                table.add_row(
                    name,
                    preset.title[:50]
                    + ("…" if len(preset.title) > 50 else ""),
                    preset.suggested_workflow or "—",
                )

    # ------------------------------------------------------------------ #
    # Workflow picker (post-26 redesign)
    # ------------------------------------------------------------------ #

    def _populate_workflow_table(self) -> None:
        """Build the workflow DataTable from ``list_workflows``,
        grouped by category. Same shape as ``_populate_presets``:
        category-header rows are non-selectable separators with
        ``None`` payload; selectable rows carry the workflow object."""
        try:
            table = self.query_one("#workflow-table", DataTable)
        except Exception:  # noqa: BLE001 — pre-mount race
            return
        table.clear(columns=True)
        table.add_columns("Name", "Meetings", "Description")

        self._workflows = []
        loaded: list[tuple[str, Workflow]] = []
        for name in list_workflows():
            try:
                w = load_workflow(name)
            except Exception:  # noqa: BLE001 — best-effort listing
                continue
            loaded.append((name, w))

        by_category: dict[str, list[tuple[str, Workflow]]] = {}
        for name, w in loaded:
            by_category.setdefault(
                w.normalized_category, []
            ).append((name, w))

        def _category_sort_key(cat: str) -> tuple[int, str]:
            return (1 if cat in ("other", "legacy") else 0, cat)

        for category in sorted(by_category, key=_category_sort_key):
            self._workflows.append(("", None))
            table.add_row(
                f"[dim]── {category} ──[/dim]", "", ""
            )
            for name, w in by_category[category]:
                self._workflows.append((name, w))
                desc_first_line = (
                    w.description.strip().splitlines()[0]
                    if w.description.strip()
                    else "—"
                )
                table.add_row(
                    name,
                    str(len(w.meetings)),
                    desc_first_line[:40]
                    + ("…" if len(desc_first_line) > 40 else ""),
                )

    def _select_workflow_by_name(self, name: str) -> None:
        """Programmatically pick a workflow by name. Moves the
        DataTable cursor + fires the detail render. Used by the
        on-mount default-selection path and preset suggestion."""
        for idx, (rn, w) in enumerate(self._workflows):
            if rn == name and w is not None:
                try:
                    table = self.query_one(
                        "#workflow-table", DataTable
                    )
                    table.move_cursor(row=idx)
                except Exception:  # noqa: BLE001
                    pass
                self._on_workflow_row_highlighted(idx)
                return

    def _on_workflow_row_highlighted(self, row: int | None) -> None:
        """Cursor landed on a workflow row → update selection + render
        the meetings list + summary. Separator rows leave selection
        unchanged so the operator can scroll past headers without
        losing their pick."""
        if row is None or row < 0 or row >= len(self._workflows):
            return
        name, workflow = self._workflows[row]
        if workflow is None:
            # Separator — keep prior selection.
            return
        self._selected_workflow_name = name
        self._render_workflow_detail(workflow)

    def _render_workflow_detail(self, workflow: Workflow) -> None:
        """Populate the meetings list (with enable/disable checkboxes)
        and the workflow summary pane."""
        # Reset meeting enable state — default-on for every meeting
        # in the newly-selected workflow.
        self._meeting_enabled = {m.id: True for m in workflow.meetings}

        # Rebuild meetings list. Textual's mount() lets us add nodes
        # one at a time; remove existing first to avoid duplicates
        # on re-selection.
        try:
            container = self.query_one("#meetings-list", Vertical)
        except Exception:  # noqa: BLE001
            return
        for child in list(container.children):
            child.remove()
        for meeting in workflow.meetings:
            container.mount(
                Checkbox(
                    f"{meeting.label}  {meeting.name}",
                    value=True,
                    id=f"meeting-toggle-{meeting.id}",
                )
            )

        # Summary panel: workflow blurb + meeting count + category +
        # any pipeline indicator.
        summary_lines = []
        if workflow.description.strip():
            summary_lines.append(workflow.description.strip())
        meta = [
            f"[b]{len(workflow.meetings)}[/b] meetings",
            f"category: [b]{workflow.normalized_category}[/b]",
        ]
        if workflow.pipeline is not None:
            meta.append("pipeline mode")
        summary_lines.append("\n[dim]" + " · ".join(meta) + "[/dim]")
        try:
            self.query_one("#workflow-summary", Static).update(
                "\n\n".join(summary_lines)
            )
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------ #
    # Selection-driven population (lazygit pattern)
    # ------------------------------------------------------------------ #

    def on_data_table_row_highlighted(
        self, event: DataTable.RowHighlighted
    ) -> None:
        """Cursor on a preset row → populate composer + description
        + workflow with that preset's content. The user is free to
        edit afterwards; presets are starting points, not locks.

        Special cases:
          - Blank pseudo-row: clear both editors so the user starts
            fresh.
          - Separator row (None payload, not blank): leave editors
            alone.
        """
        if event.data_table.id == "workflow-table":
            self._on_workflow_row_highlighted(event.cursor_row)
            return
        if event.data_table.id != "preset-table":
            return
        row = event.cursor_row
        if row is None or row < 0 or row >= len(self._presets):
            return
        name, preset = self._presets[row]

        composer = self.query_one("#directive-composer", TextArea)
        description = self.query_one("#description-composer", TextArea)

        if name == _BLANK_PRESET:
            # Clear for fresh-start composition.
            composer.text = ""
            description.text = ""
            # Don't touch workflow — user picks.
            return

        if name == _PRIME_PRESET:
            # Pop the project's canonical directive into the composer.
            # Description gets a generated one-liner since prime is
            # stored as raw text without metadata.
            if (
                self.project is not None
                and self.project.prime_directive is not None
            ):
                composer.text = self.project.prime_directive
                description.text = (
                    f"Prime directive for project "
                    f"{self.project.name}."
                )
                if self.project.last_workflow:
                    self._select_workflow_by_name(
                        self.project.last_workflow
                    )
            return

        if preset is None:
            # Inert separator row.
            return

        composer.text = preset.body
        description.text = preset.description
        # Workflow pre-select (always overridable). Drives the
        # workflow row's middle/right panes via _render_workflow_detail.
        if preset.suggested_workflow:
            self._select_workflow_by_name(preset.suggested_workflow)
        # Pre-fill the save-name input with the preset's name as a
        # convenience (user is likely editing-then-resaving). Only
        # populate when the field is currently empty so we don't
        # clobber a name the user has already typed.
        save_name = self.query_one("#save-name-input", Input)
        if not save_name.value.strip():
            save_name.value = name

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #

    def action_back(self) -> None:
        self.app.pop_screen()

    def _on_empty_directive_decision(self, confirmed: bool | None) -> None:
        """Callback for the empty-directive confirmation modal.
        Confirmed → set the bypass flag and re-enter action_go to
        continue the launch flow. Cancelled → leave the operator on
        NewRunScreen so they can write a directive (or hit Cancel)."""
        if confirmed:
            self._empty_directive_confirmed = True
            self.action_go()

    def action_go(self) -> None:
        """Launch the run. Validates inputs, optionally persists a
        preset, pre-flights the API key, then pushes the launch
        confirmation modal. Real Runner+LiveRunHandle construction
        happens after the user confirms (in _launch_run)."""
        # Slice B: one-run cap. Until per-run artifact tagging
        # lands (project_run_id_tagging memory), concurrent runs
        # against the same project would interleave Dodo memory and
        # clobber artifacts. Block + point the operator at the
        # active run.
        if self.app.has_active_run():  # type: ignore[attr-defined]
            active = self.app._active_run  # type: ignore[attr-defined]
            self.notify(
                f"A run is already in flight ({active.run_id}). "
                f"Wait for it to finish or abort it from the live "
                f"watch screen.",
                severity="warning",
                timeout=8,
            )
            return
        directive = self.query_one("#directive-composer", TextArea).text.strip()
        description = self.query_one(
            "#description-composer", TextArea
        ).text.strip()
        workflow_name = self._selected_workflow_name
        project_str = self.query_one("#project-input", Input).value
        budget_str = self.query_one("#budget-input", Input).value
        save_checked = self.query_one("#save-checkbox", Checkbox).value
        save_name = self.query_one("#save-name-input", Input).value.strip()

        if not directive and not self._empty_directive_confirmed:
            # Push confirmation modal: launching with an empty
            # directive is unusual but valid for workflows like
            # tdd-implement where the team works from seeded
            # lifecycle artifacts (features, tickets, contracts on
            # disk). Modal callback either re-enters action_go with
            # the confirmed flag set, or no-ops.
            from wonderland.tui.screens.empty_directive_modal import (
                EmptyDirectiveConfirmModal,
            )

            self.app.push_screen(
                EmptyDirectiveConfirmModal(
                    workflow_name=workflow_name,
                ),
                self._on_empty_directive_decision,
            )
            return
        if not workflow_name:
            self.notify("Pick a workflow.", severity="warning")
            return
        if not project_str:
            self.notify("Set the project root.", severity="warning")
            return
        try:
            budget = float(budget_str)
            if budget <= 0:
                raise ValueError("budget must be positive")
        except ValueError:
            self.notify(
                f"Invalid budget: {budget_str!r} (expected a positive number)",
                severity="error",
            )
            return

        project_path = Path(project_str).expanduser()

        # Bare-root path: project doesn't exist yet, OR exists but
        # has no production structure (empty / .git only / .gitignore
        # only). Push the skeleton picker (T71) so the operator can
        # apply a skeleton before launch — analysis 037 names the
        # skeleton as load-bearing for deliverable shape. The picker
        # dismisses with: a skeleton name (applied), "" (continue
        # without — operator override), or None (cancel).
        #
        # If the project root already has structure (src/, tests/,
        # etc.), skip the picker and proceed — operator has set
        # things up themselves.
        if is_bare_project_root(project_path):
            self._pending_post_skeleton = {
                "directive": directive,
                "workflow_name": workflow_name,
                "description": description,
                "save_checked": save_checked,
                "save_name": save_name,
                "budget": budget,
                "project_path": project_path,
            }
            self.app.push_screen(
                SkeletonPickerScreen(project_path),
                self._on_skeleton_picked,
            )
            return

        # API-key pre-flight: env var → config file. If neither has
        # one, push the Settings screen so the user can set it from
        # inside the TUI rather than dropping to the shell.
        api_key = self._resolve_api_key()
        if not api_key:
            self.notify(
                "No Anthropic API key found — opening Settings. Set "
                "the key, save, then press Go again to launch.",
                severity="warning",
                timeout=6,
            )
            self.app.push_screen(SettingsScreen())
            return

        # Save as preset first (if requested) so the saved record
        # captures whatever's in the form right now.
        if save_checked:
            if not save_name:
                self.notify(
                    "Save-as-preset is checked but no name given.",
                    severity="warning",
                )
                return
            if not project_path.is_dir():
                self.notify(
                    f"Project root doesn't exist; can't save preset to "
                    f"{project_path}/.wonderland/directives/",
                    severity="warning",
                )
                return
            preset = DirectivePreset(
                name=save_name,
                title=description.split("\n", 1)[0][:80] or save_name,
                description=description,
                body=directive,
                suggested_workflow=str(workflow_name),
            )
            try:
                path = save_directive(preset, project_path)
            except Exception as exc:  # noqa: BLE001
                self.notify(
                    f"Failed to save preset: {exc}",
                    severity="error",
                )
                return
            self.notify(f"Saved preset → {path}", timeout=3)
            # Refresh the table so the new preset appears.
            self._populate_presets()

        # Auto-merge: when the checkbox is on, the run-bg subprocess
        # will attempt a fast-forward merge back to the source branch
        # on clean completion. Captured here so the post-confirm
        # callback can plumb it into launch_background_run.
        try:
            auto_merge = self.query_one(
                "#auto-merge-checkbox", Checkbox
            ).value
        except Exception:  # noqa: BLE001
            auto_merge = False

        # Stash the validated launch parameters for the post-confirm
        # callback to read.
        self._pending_launch = {
            "directive": directive,
            "workflow_name": str(workflow_name),
            "project_path": project_path,
            "budget": budget,
            "auto_merge": auto_merge,
        }

        # Push the confirmation modal. Burning $3-5 deserves a
        # deliberate Yes — irreversible action gets a guarded prompt
        # per the project_tui_lazygit_principle exception.
        self.app.push_screen(
            LaunchConfirmationScreen(
                directive=directive,
                workflow_name=str(workflow_name),
                budget=budget,
                project_root=str(project_path),
            ),
            self._on_launch_confirmed,
        )

    def _resolve_api_key(self) -> str | None:
        """Pre-flight check: env var > config file. Returns the key
        or None if neither path has one."""
        env_key = os.environ.get("ANTHROPIC_API_KEY")
        if env_key:
            return env_key
        try:
            cfg = load_config()
        except Exception:  # noqa: BLE001 — bad config shouldn't crash
            return None
        return cfg.anthropic.api_key

    def _on_skeleton_picked(self, choice: str | None) -> None:
        """Callback fired when SkeletonPickerScreen dismisses.

        Dismiss values:
          - skeleton name (str): skeleton was applied; resume the
            launch flow against the now-populated project root.
          - "" (empty string): operator declined the skeleton;
            resume launch against the bare root anyway.
          - None: operator cancelled; abort the launch and return
            to the new-run composer.
        """
        if choice is None:
            # Cancelled — drop pending state and let operator edit
            # the project path or back out.
            self._pending_post_skeleton = None
            return
        params = getattr(self, "_pending_post_skeleton", None)
        if params is None:
            return  # defensive — shouldn't happen
        # Project root is now populated (or operator chose to
        # proceed bare). Re-enter action_go's post-skeleton flow
        # by directly inlining the rest of the launch path.
        self._pending_post_skeleton = None
        self._continue_launch_after_skeleton(params)

    def _continue_launch_after_skeleton(self, params: dict) -> None:
        """Resume the launch flow after the skeleton picker
        resolved. Mirrors the post-bare-root tail of action_go —
        save preset (if requested), then push the launch
        confirmation modal."""
        directive = params["directive"]
        workflow_name = params["workflow_name"]
        description = params["description"]
        save_checked = params["save_checked"]
        save_name = params["save_name"]
        budget = params["budget"]
        project_path = params["project_path"]

        # API-key pre-flight, same as action_go.
        api_key = self._resolve_api_key()
        if not api_key:
            self.notify(
                "No Anthropic API key found — opening Settings. Set "
                "the key, save, then press Go again to launch.",
                severity="warning",
                timeout=6,
            )
            self.app.push_screen(SettingsScreen())
            return

        if save_checked:
            if not save_name:
                self.notify(
                    "Save-as-preset is checked but no name given.",
                    severity="warning",
                )
                return
            preset = DirectivePreset(
                name=save_name,
                title=description.split("\n", 1)[0][:80] or save_name,
                description=description,
                body=directive,
                suggested_workflow=str(workflow_name),
            )
            try:
                path = save_directive(preset, project_path)
            except Exception as exc:  # noqa: BLE001
                self.notify(
                    f"Failed to save preset: {exc}",
                    severity="error",
                )
                return
            self.notify(f"Saved preset → {path}", timeout=3)
            self._populate_presets()

        self._pending_launch = {
            "directive": directive,
            "workflow_name": str(workflow_name),
            "project_path": project_path,
            "budget": budget,
        }
        self.app.push_screen(
            LaunchConfirmationScreen(
                directive=directive,
                workflow_name=str(workflow_name),
                project_root=str(project_path),
                budget=budget,
            ),
            self._on_launch_confirmed,
        )

    def _on_launch_confirmed(self, confirmed: bool | None) -> None:
        """Callback fired when the LaunchConfirmationScreen pops.
        Confirmed → kick off the launch worker; declined → no-op."""
        if not confirmed:
            return
        # Hand off to the worker that handles the async Runner build.
        self._launch_run()

    @work(exclusive=True)
    async def _launch_run(self) -> None:
        """Spawn the run as a detached subprocess via
        ``app.launch_background_run`` and push LiveRunScreen
        targeting the subprocess's run_id.

        Background mode (the only mode now): ``wonderland run-bg``
        runs the workflow in its own process; the TUI tails the
        events file via SubprocessRunHandle. Closing the TUI
        leaves the subprocess running — the operator can re-launch
        the TUI and the discovery path picks the run back up.
        """
        from datetime import datetime, timezone

        from wonderland.tui.screens.live_run import LiveRunScreen

        params = self._pending_launch
        try:
            workflow = load_workflow(params["workflow_name"])
        except Exception as exc:  # noqa: BLE001
            self.notify(
                f"Failed to load workflow: {exc}", severity="error"
            )
            return

        # We generate the run_id here so the App can pre-create the
        # run dir at a known path before the subprocess starts
        # writing into it. The subprocess uses our id via --run-id
        # so the dir paths align.
        run_id = datetime.now(tz=timezone.utc).strftime(
            "%Y%m%dT%H%M%S"
        )

        # P11 T78: record run_id + workflow on the project so the
        # library / dashboard show the latest run.
        # Prime-directive capture: first non-empty directive landed
        # against a project becomes its canonical "prime" directive,
        # surfaced in the preset table on subsequent runs so design
        # passes stay oriented across N>1 iterations.
        if self.project is not None:
            try:
                self.project.last_run_id = run_id
                self.project.last_workflow = params["workflow_name"]
                if (
                    self.project.prime_directive is None
                    and params["directive"].strip()
                ):
                    self.project.prime_directive = params["directive"]
                save_project(self.project)
            except Exception as exc:  # noqa: BLE001 — non-fatal
                self.notify(
                    f"Couldn't update project run history: {exc}",
                    severity="warning",
                )

        try:
            self.app.launch_background_run(  # type: ignore[attr-defined]
                directive=params["directive"],
                workflow_name=str(params["workflow_name"]),
                project_root=params["project_path"],
                budget=params["budget"],
                model=workflow.defaults.model,
                run_id=run_id,
                auto_merge=bool(params.get("auto_merge", False)),
            )
        except RuntimeError as exc:
            self.notify(
                f"Couldn't launch — {exc}",
                severity="error",
            )
            return

        # switch_screen swaps NewRunScreen for LiveRunScreen on the
        # stack — escape from the live-watch returns to the snapshot
        # library directly. The screen attaches to the active run
        # via SubprocessRunHandle which tails the events file.
        self.app.switch_screen(LiveRunScreen(run_id=run_id))

    # ------------------------------------------------------------------ #
    # Linear-form advance — Enter steps through fields
    # ------------------------------------------------------------------ #

    def _advance_from(self, current_id: str) -> None:
        """Move focus to the next form field after ``current_id``.
        At the end of the form (the Go button), fire action_go
        directly rather than advancing past it."""
        try:
            idx = self._FORM_ORDER.index(current_id)
        except ValueError:
            return
        if idx >= len(self._FORM_ORDER) - 1:
            # Already on the Go button (or past) — trigger launch.
            self.action_go()
            return
        next_id = self._FORM_ORDER[idx + 1]
        try:
            self.query_one(f"#{next_id}").focus()
        except Exception:  # noqa: BLE001 — best-effort focus
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle clicks (and Enter on focused buttons) for the
        Go and Cancel actions."""
        if event.button.id == "go-button":
            self.action_go()
        elif event.button.id == "cancel-button":
            self.action_back()

    def on_data_table_row_selected(
        self, event: DataTable.RowSelected
    ) -> None:
        """Enter on the preset table fires this event. Advance to the
        next form field (the directive composer)."""
        if event.data_table.id == "preset-table":
            self._advance_from("preset-table")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Enter inside an Input fires Submitted. Advance to the next
        form field."""
        if event.input.id:
            self._advance_from(event.input.id)

    def on_select_changed(self, event: Select.Changed) -> None:
        """When the user picks a workflow from the dropdown, advance
        to the next field. Note: the Select widget collapses the
        dropdown on selection automatically, so this just moves
        focus.

        Only fires when the Select has focus — preset auto-population
        sets the value programmatically without focusing the Select,
        so user-initiated changes are the only ones that advance.
        Textual posts Changed events asynchronously so a transient
        flag doesn't reliably distinguish user vs programmatic; the
        focus check is the structural fix.
        """
        # No-op now that the workflow Select widget has been replaced
        # by a DataTable picker. Left here so any in-flight tests that
        # post fake Select.Changed events still find the handler.
        del event

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """When the user checks the save-as-preset box, advance to
        the name input so they can type the slug. Toggling off
        leaves focus alone. Same focus-based filter as
        on_select_changed for programmatic vs user changes.

        Meeting-toggle checkboxes (added dynamically when a workflow
        is picked) update the local enable map without advancing
        focus — operator stays in the meetings pane to keep toggling.
        Per-meeting skipping at launch is a follow-on; for now the
        state is captured but not yet wired to the runner.
        """
        cb_id = event.checkbox.id or ""
        if cb_id.startswith("meeting-toggle-"):
            meeting_id = cb_id[len("meeting-toggle-"):]
            self._meeting_enabled[meeting_id] = event.value
            return
        if cb_id == "save-checkbox" and event.value:
            if event.checkbox.has_focus:
                self._advance_from("save-checkbox")

    def action_save_as_preset(self) -> None:
        """The 's' binding flips the save-as-preset checkbox on so
        the next Go saves before launching. The actual save happens
        in action_go (inline rather than a separate modal — keeps the
        lazygit pattern: no modals except for irreversible actions)."""
        checkbox = self.query_one("#save-checkbox", Checkbox)
        checkbox.value = not checkbox.value
        if checkbox.value:
            # Focus the name input so the user can type the slug.
            self.query_one("#save-name-input", Input).focus()
            self.notify(
                "Save-as-preset enabled — fill in the name and press 'g'.",
                timeout=3,
            )
        else:
            self.notify("Save-as-preset disabled.", timeout=2)


__all__ = ["NewRunScreen"]
