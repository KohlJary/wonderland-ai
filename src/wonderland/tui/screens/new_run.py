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
from wonderland.workflow import list_workflows, load_workflow


# Sentinel name for the "blank directive" pseudo-row at the top of
# the preset table — selecting it clears the composer + description
# so the user starts fresh.
_BLANK_PRESET = "__blank__"


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
        "workflow-select",
        "budget-input",
        "project-input",
        "save-checkbox",
        "save-name-input",
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
            with Horizontal(id="new-run-main"):
                with Vertical(id="preset-pane"):
                    yield Static("[b]Presets[/b]", id="preset-label")
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
                    yield Static(
                        "[b]Description[/b] [dim](optional — used if saved as preset)[/dim]",
                        id="description-label",
                    )
                    yield TextArea(
                        "",
                        id="description-composer",
                        language=None,
                    )
            yield Static("[b]Configuration[/b]", id="config-label")
            with Horizontal(id="config-row"):
                yield Label("Workflow:", id="workflow-label")
                # Prefill workflow from project default when the
                # project is set AND the workflow exists in the
                # bundled list. The Select widget is set after mount
                # via on_mount so we don't have to fight Select's
                # value= constructor (which rejects None / sentinels
                # depending on Textual version).
                yield Select(
                    [(w, w) for w in list_workflows()],
                    id="workflow-select",
                    allow_blank=True,
                    prompt="(pick a workflow)",
                )
                yield Label("Budget (soft cap):", id="budget-label")
                # Prefill budget from project default; legacy path
                # uses the historical $5.00 default.
                budget_value = (
                    f"{self.project.default_budget:.2f}"
                    if self.project is not None
                    else "5.00"
                )
                yield Input(
                    value=budget_value,
                    placeholder="$ — runs can exceed by 10-20%",
                    id="budget-input",
                )
            with Horizontal(id="project-row"):
                yield Label("Project root:", id="project-label")
                yield Input(
                    value=str(self.project_root),
                    placeholder="/path/to/project",
                    id="project-input",
                )
            with Horizontal(id="save-row"):
                yield Checkbox(
                    "Save as preset",
                    value=False,
                    id="save-checkbox",
                )
                yield Label("Name:", id="save-name-label")
                yield Input(
                    placeholder="my-directive-name",
                    id="save-name-input",
                )
            with Horizontal(id="action-row"):
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
        if target_workflow:
            self.query_one(
                "#workflow-select", Select
            ).value = target_workflow

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

        # Bundled
        for name in list_directives():
            try:
                p = load_directive(name)
            except Exception:  # noqa: BLE001 — best-effort listing
                continue
            self._presets.append((name, p))
            table.add_row(
                name,
                p.title[:50] + ("…" if len(p.title) > 50 else ""),
                p.suggested_workflow or "—",
            )

        # Project — inserted only when there's at least one
        if self.project_root and self.project_root.is_dir():
            project_names = list_project_directives(self.project_root)
            if project_names:
                # Visual separator row; use a tuple slot so the lookup
                # array stays parallel with the table rows. None means
                # "not selectable as a preset".
                self._presets.append(("", None))  # type: ignore[arg-type]
                table.add_row(
                    "[dim]──── project ────[/dim]", "", ""
                )
                for name in project_names:
                    try:
                        p = load_project_directive(name, self.project_root)
                    except Exception:  # noqa: BLE001
                        continue
                    self._presets.append((name, p))
                    table.add_row(
                        name,
                        p.title[:50] + ("…" if len(p.title) > 50 else ""),
                        p.suggested_workflow or "—",
                    )

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

        if preset is None:
            # Inert separator row.
            return

        composer.text = preset.body
        description.text = preset.description
        # Workflow pre-select (always overridable). The Select.Changed
        # event fires async but on_select_changed checks has_focus
        # before advancing, so this programmatic update doesn't jump
        # past the user.
        if preset.suggested_workflow:
            sel = self.query_one("#workflow-select", Select)
            sel.value = preset.suggested_workflow
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
        directive = self.query_one("#directive-composer", TextArea).text.strip()
        description = self.query_one(
            "#description-composer", TextArea
        ).text.strip()
        workflow_name = self.query_one("#workflow-select", Select).value
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
                    workflow_name=str(workflow_name)
                    if workflow_name and workflow_name != Select.BLANK
                    else None,
                ),
                self._on_empty_directive_decision,
            )
            return
        if workflow_name == Select.BLANK or not workflow_name:
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

        # Stash the validated launch parameters for the post-confirm
        # callback to read.
        self._pending_launch = {
            "directive": directive,
            "workflow_name": str(workflow_name),
            "project_path": project_path,
            "budget": budget,
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
        """Actually construct the Runner + LiveRunHandle and push
        LiveRunScreen against it. Pops the NewRunScreen after the
        push so escape from the live-watch returns to the snapshot
        library, not back to the new-run composer.
        """
        # Lazy imports to avoid pulling Runner machinery into the
        # new-run module's load path until launch time.
        from wonderland.observer import LiveRunHandle
        from wonderland.runner import Runner
        from wonderland.tui.screens.live_run import LiveRunScreen

        params = self._pending_launch
        try:
            workflow = load_workflow(params["workflow_name"])
        except Exception as exc:  # noqa: BLE001
            self.notify(
                f"Failed to load workflow: {exc}", severity="error"
            )
            return

        try:
            runner = await Runner.make_full_cast(
                project_root=params["project_path"],
                budget_dollars=params["budget"],
                model=workflow.defaults.model,
            )
        except Exception as exc:  # noqa: BLE001
            self.notify(
                f"Failed to construct runner: {exc}", severity="error"
            )
            return

        # P11 T78: when a project context is set, record run_id and
        # the workflow used on the project so the library shows last-
        # run summary AND so the next run on this project prefills
        # with the same workflow (per-task workflow choice survives
        # across runs as a usability hint, not a constraint).
        if self.project is not None:
            try:
                self.project.last_run_id = runner.run_id
                self.project.last_workflow = params["workflow_name"]
                save_project(self.project)
            except Exception as exc:  # noqa: BLE001 — non-fatal
                self.notify(
                    f"Couldn't update project run history: {exc}",
                    severity="warning",
                )

        handle = LiveRunHandle(
            runner=runner,
            workflow=workflow,
            directive=params["directive"],
        )

        # switch_screen swaps NewRunScreen for LiveRunScreen on the
        # stack — escape from the live-watch returns to the snapshot
        # library directly without an intermediate stop on the
        # composer the user already submitted.
        self.app.switch_screen(LiveRunScreen(handle=handle))

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
        if event.select.id == "workflow-select" and event.value != Select.BLANK:
            if event.select.has_focus:
                self._advance_from("workflow-select")

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """When the user checks the save-as-preset box, advance to
        the name input so they can type the slug. Toggling off
        leaves focus alone. Same focus-based filter as
        on_select_changed for programmatic vs user changes."""
        if event.checkbox.id == "save-checkbox" and event.value:
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
