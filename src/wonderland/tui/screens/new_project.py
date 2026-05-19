"""NewProjectScreen — register a new project via TUI form (P11 T76).

Replaces the T75 'use the CLI for now' notify with an in-TUI flow.
Form fields:

  - name (validated against the registry: non-empty, unique)
  - path (expanded + resolved; warns on bare-root vs non-bare detect)
  - prime directive (TextArea + demo-directive picker; the operator's
    canonical project framing — feeds into every workflow run)
  - default skeleton (Select drawn from list_skeletons())
  - default budget (Input, dollar-validated)

On confirm:
  1. Validate (name, path, uniqueness, budget)
  2. Register via wonderland.project.register_project()
  3. If a skeleton was selected AND the path is bare AND the operator
     ticked the 'Apply now' checkbox: apply_skeleton() to the path
  4. Push StartDiscoveryModal — recommends jumping straight into the
     discovery workflow (P15 T-m8 UX: the flow is
     discovery → milestone-plan → tdd-design → tdd-implement and
     discovery is the natural first move).

Workflow selection is per-RUN, not per-project (NewRunScreen), so
this form doesn't ask for it. The prime directive replaces it as
the load-bearing per-project decision.

Layout follows project_tui_lazygit_principle: single-pane form
(this is a registration step, not a navigation surface — full canvas
is appropriate). Tab/Enter advances through fields.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
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

from wonderland.directive import (
    DirectivePreset,
    list_directives,
    load_directive,
)
from wonderland.project import (
    Project,
    list_projects,
    register_project,
)
from wonderland.skeleton import (
    apply_skeleton,
    is_bare_project_root,
    list_skeletons,
    load_skeleton,
    write_project_context_from_skeleton,
)


@dataclass(frozen=True)
class NewProjectResult:
    """Payload returned from NewProjectScreen on successful project
    creation. Carries the newly-registered project plus the
    operator's choice on the post-create discovery prompt — the
    project_library handler launches the discovery workflow when
    ``start_discovery`` is True, otherwise it just surfaces the
    new project in the library."""

    project: Project
    start_discovery: bool


class NewProjectScreen(Screen["NewProjectResult | None"]):
    """Form for registering a new project. Dismisses with a
    ``NewProjectResult`` (project + start_discovery flag) on
    success, None on cancel."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
        Binding("ctrl+s", "submit", "Create", show=True),
    ]

    _FORM_ORDER: tuple[str, ...] = (
        "name-input",
        "path-input",
        "directive-preset-table",
        "directive-composer",
        "skeleton-select",
        "apply-skeleton-checkbox",
        "budget-input",
        "create-button",
    )

    def __init__(self) -> None:
        super().__init__()
        self._existing_names: set[str] = set()
        self._existing_paths: set[Path] = set()
        # Operator default: prefill the path field with cwd unless cwd
        # is already a registered project root. Captures the common
        # case "I'm sitting in the directory I want to register"
        # without forcing operators who launch wonderland-tui from
        # somewhere generic (~/.config, etc.) to clear the field.
        # Resolved + checked against the registry in on_mount.
        self._cwd_default: Path = Path.cwd().resolve()
        # Cache of (name, preset) tuples in display order so the
        # preset-table's row index → preset payload is a constant-
        # time lookup in the row-select handler. None payload
        # marks the "blank" pseudo-row at the top.
        self._directive_presets: list[
            tuple[str, "DirectivePreset | None"]
        ] = []

    def _populate_directive_presets(self) -> None:
        """Fill the directive preset table with bundled directives in
        the ``demo`` category. Same shape as NewRunScreen's preset
        table, scoped to demos and without the per-project /
        save-as-preset rows (this screen is for creating a project,
        not running one). A blank pseudo-row at the top lets the
        operator clear the composer for a from-scratch directive."""
        try:
            table = self.query_one("#directive-preset-table", DataTable)
        except Exception:  # noqa: BLE001 — pre-mount race
            return
        table.clear(columns=True)
        table.add_columns("Demo", "Title")

        self._directive_presets = []

        # Row 0: blank — clear the composer.
        self._directive_presets.append(("", None))
        table.add_row(
            "[b]── blank ──[/b]",
            "[dim]start with an empty composer[/dim]",
        )

        # Demo-category bundled presets.
        for name in list_directives():
            try:
                preset = load_directive(name)
            except Exception:  # noqa: BLE001
                continue
            if preset.normalized_category != "demo":
                continue
            self._directive_presets.append((name, preset))
            table.add_row(name, preset.title)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical(id="new-project-root"):
            yield Static(
                "[b]New project[/b] · register a Wonderland working venue",
                id="new-project-header",
            )
            with VerticalScroll(id="new-project-form-scroll"):
                with Vertical(id="new-project-form"):
                    yield Label("[b]Name[/b]", id="name-label")
                    yield Input(
                        placeholder="my-project",
                        id="name-input",
                    )
                    yield Static(
                        "[dim]Stable identifier; unique within your "
                        "registry. Pick something you'll remember "
                        "across sessions.[/dim]",
                        id="name-help",
                    )

                    yield Label("[b]Project root[/b]", id="path-label")
                    yield Input(
                        placeholder="/path/to/project (or ~/projects/foo)",
                        id="path-input",
                    )
                    yield Static(
                        "",  # populated dynamically based on the entered path
                        id="path-status",
                    )

                    yield Label(
                        "[b]Prime directive[/b] [dim](the project's "
                        "canonical framing — every workflow run starts "
                        "from this)[/dim]",
                        id="directive-label",
                    )
                    # Two-pane row mirroring NewRunScreen's directive
                    # row, scoped to demo-category presets: left
                    # picker, right composer. Selecting a row
                    # populates the composer; the operator can edit
                    # freely from there. Blank pseudo-row at the top
                    # clears the composer for a from-scratch directive.
                    with Horizontal(id="directive-row"):
                        with Vertical(id="directive-preset-pane"):
                            yield Static(
                                "[b]Demos[/b] "
                                "[dim](pick one to start)[/dim]",
                                id="directive-preset-label",
                            )
                            yield DataTable(
                                id="directive-preset-table",
                                cursor_type="row",
                            )
                        with Vertical(id="directive-composer-pane"):
                            yield Static(
                                "[b]Directive[/b]",
                                id="directive-composer-label",
                            )
                            yield TextArea(
                                "",
                                id="directive-composer",
                                language=None,
                            )
                    yield Static(
                        "[dim]Leave blank to set later — the "
                        "discovery workflow will help you shape it "
                        "from operator interviews.[/dim]",
                        id="directive-help",
                    )

                    yield Label(
                        "[b]Skeleton[/b] [dim](optional — applies "
                        "on bare roots)[/dim]",
                        id="skeleton-label",
                    )
                    yield Select(
                        [(s.name, s.name) for s in list_skeletons()],
                        id="skeleton-select",
                        allow_blank=True,
                        prompt="(no skeleton)",
                    )
                    with Horizontal(id="skeleton-apply-row"):
                        yield Checkbox(
                            "Apply skeleton now (only if root is bare)",
                            value=False,
                            id="apply-skeleton-checkbox",
                        )
                    yield Static(
                        "[dim]Stored as the project's default record. "
                        "Tick the box to lay the skeleton's files down "
                        "into the path immediately (skipped on "
                        "non-bare roots to avoid clobbering).[/dim]",
                        id="skeleton-help",
                    )

                    yield Label("[b]Default budget[/b]", id="budget-label")
                    yield Input(
                        value="5.00",
                        placeholder="$ — dollars per run",
                        id="budget-input",
                    )
                    yield Static(
                        "[dim]Pre-filled into NewRunScreen. The "
                        "Wonderland team can exceed by 10-20%.[/dim]",
                        id="budget-help",
                    )

            with Horizontal(id="new-project-action-row"):
                yield Button(
                    "▶ Create (ctrl+s)",
                    id="create-button",
                    variant="primary",
                )
                yield Button(
                    "Cancel (esc)",
                    id="cancel-button",
                )
        yield Footer()

    def on_mount(self) -> None:
        # Snapshot existing projects so validation doesn't re-read on
        # every keystroke. The screen is short-lived (one
        # registration), so this snapshot's freshness is fine.
        all_projects = list_projects(include_archived=True)
        self._existing_names = {p.name for p in all_projects}
        self._existing_paths = {p.root_path for p in all_projects}
        # Prefill path with cwd if it's not already a project root.
        # Operators who launch the TUI from inside a project they
        # want to register get a one-key path: type a name, submit.
        if self._cwd_default not in self._existing_paths:
            path_input = self.query_one("#path-input", Input)
            path_input.value = str(self._cwd_default)
            # Trigger the path-status feedback render manually since
            # programmatic .value = ... doesn't fire Input.Changed.
            self._render_path_status(str(self._cwd_default))
        # Populate the directive preset table now that widgets are
        # mounted (DataTable.add_row before mount doesn't render).
        self._populate_directive_presets()
        self.query_one("#name-input", Input).focus()

    def on_data_table_row_selected(
        self, event: DataTable.RowSelected
    ) -> None:
        """Operator picked a directive preset — populate the composer
        with the preset's body. Blank pseudo-row clears the composer.
        Non-preset tables (none currently, but defensive) are
        ignored."""
        if event.data_table.id != "directive-preset-table":
            return
        idx = event.cursor_row
        if idx < 0 or idx >= len(self._directive_presets):
            return
        _name, preset = self._directive_presets[idx]
        composer = self.query_one("#directive-composer", TextArea)
        composer.text = preset.body if preset is not None else ""

    # ------------------------------------------------------------------ #
    # Live path-status feedback
    # ------------------------------------------------------------------ #

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "path-input":
            return
        self._render_path_status(event.value.strip())

    def _render_path_status(self, path_str: str) -> None:
        """Update the path-status helper label based on the current
        path field value. Pulled out of on_input_changed so on_mount
        can prime it after programmatic prefill (since setting
        Input.value doesn't fire Input.Changed)."""
        status = self.query_one("#path-status", Static)
        if not path_str:
            status.update("")
            return
        try:
            resolved = Path(path_str).expanduser().resolve()
        except Exception as exc:  # noqa: BLE001
            status.update(f"[red]Invalid path: {exc}[/red]")
            return
        if not resolved.exists():
            status.update(
                "[yellow]Path doesn't exist yet — it'll be created on "
                "first apply (or first run).[/yellow]"
            )
        elif is_bare_project_root(resolved):
            status.update(
                "[green]Path exists and is bare — a skeleton will lay "
                "down a working starter tree.[/green]"
            )
        else:
            status.update(
                "[dim]Path exists and already has structure. Skeleton "
                "won't auto-apply (would clobber).[/dim]"
            )

    # ------------------------------------------------------------------ #
    # Form advance via Enter
    # ------------------------------------------------------------------ #

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id is None:
            return
        self._advance_from(event.input.id)

    def _advance_from(self, current_id: str) -> None:
        try:
            idx = self._FORM_ORDER.index(current_id)
        except ValueError:
            return
        if idx >= len(self._FORM_ORDER) - 1:
            self.action_submit()
            return
        next_id = self._FORM_ORDER[idx + 1]
        try:
            widget = self.query_one(f"#{next_id}")
            widget.focus()
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------ #
    # Submit / cancel
    # ------------------------------------------------------------------ #

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_submit(self) -> None:
        name = self.query_one("#name-input", Input).value.strip()
        path_str = self.query_one("#path-input", Input).value.strip()
        directive_body = self.query_one(
            "#directive-composer", TextArea
        ).text.strip()
        skeleton_name = self.query_one("#skeleton-select", Select).value
        apply_now = self.query_one("#apply-skeleton-checkbox", Checkbox).value
        budget_str = self.query_one("#budget-input", Input).value.strip()

        # Validation ---------------------------------------------------
        if not name:
            self.notify("Name is required.", severity="warning")
            self.query_one("#name-input", Input).focus()
            return
        if name in self._existing_names:
            self.notify(
                f"Name {name!r} already in use — pick a different one.",
                severity="warning",
            )
            self.query_one("#name-input", Input).focus()
            return
        if not path_str:
            self.notify("Path is required.", severity="warning")
            self.query_one("#path-input", Input).focus()
            return
        try:
            resolved_path = Path(path_str).expanduser().resolve()
        except Exception as exc:  # noqa: BLE001
            self.notify(f"Invalid path: {exc}", severity="error")
            return
        if resolved_path in self._existing_paths:
            # Not strictly a hard error (analyses 037's reframe — same
            # path can be aliased to different project names for
            # staging vs. prod) — but warn the operator they're
            # creating a duplicate.
            self.notify(
                "Heads up: another project is already registered at "
                "this path. Continuing anyway.",
                severity="warning",
                timeout=5,
            )
        try:
            budget = float(budget_str) if budget_str else 5.00
            if budget <= 0:
                raise ValueError("budget must be positive")
        except ValueError:
            self.notify(
                f"Invalid budget {budget_str!r} (expected positive number).",
                severity="error",
            )
            self.query_one("#budget-input", Input).focus()
            return

        # Select.value can be a string, Select.BLANK, or Select.NULL
        # depending on Textual version + whether allow_blank=True. Only
        # accept str values; everything else means "no selection."
        skeleton_norm = (
            skeleton_name if isinstance(skeleton_name, str) and skeleton_name else None
        )
        # Prime directive: empty text means "set it later" (the
        # discovery workflow will help shape it from operator
        # interviews).
        prime_norm = directive_body if directive_body else None

        # Build + register --------------------------------------------
        try:
            project = Project(
                name=name,
                root_path=resolved_path,
                default_skeleton=skeleton_norm,
                default_budget=budget,
                prime_directive=prime_norm,
            )
            register_project(project)
        except Exception as exc:  # noqa: BLE001
            self.notify(
                f"Failed to register project: {exc}",
                severity="error",
                timeout=8,
            )
            return

        # Skeleton apply (optional, only on bare roots) ---------------
        # Two paths:
        #   - Bare root → full apply: lay files + write project.yaml
        #   - Non-bare root → retrofit only: write project.yaml from
        #     the picked skeleton's manifest. Doesn't clobber existing
        #     files; gives the team's substrate the runtime fact
        #     even when the operator is adopting an existing tree.
        if apply_now and skeleton_norm is not None:
            try:
                skeleton = load_skeleton(skeleton_norm)
                if is_bare_project_root(resolved_path):
                    written = apply_skeleton(
                        skeleton, resolved_path,
                        prime_directive=prime_norm,
                    )
                    self.notify(
                        f"Project registered + skeleton applied "
                        f"({len(written)} files).",
                        timeout=4,
                    )
                else:
                    pc_path = write_project_context_from_skeleton(
                        skeleton, resolved_path,
                        prime_directive=prime_norm,
                    )
                    if pc_path is not None:
                        self.notify(
                            f"Project registered. Files not laid down "
                            f"(non-bare root); project context written "
                            f"to .wonderland/project.yaml.",
                            timeout=6,
                        )
                    else:
                        # Manifest had no stack — nothing to retrofit.
                        self.notify(
                            f"Project registered. Skeleton not applied: "
                            f"path is not bare (would risk clobbering).",
                            timeout=6,
                        )
            except Exception as exc:  # noqa: BLE001
                self.notify(
                    f"Project registered, but skeleton apply "
                    f"failed: {exc}",
                    severity="error",
                    timeout=8,
                )
        else:
            self.notify(f"Project {name!r} registered.", timeout=3)

        # P15 T-m8 UX — recommend jumping into the discovery
        # workflow as the natural first move. The modal pushes
        # above this screen + dismisses with True (yes) / False
        # (later); callback dismisses NewProjectScreen with a
        # NewProjectResult carrying the project + the choice.
        from wonderland.tui.screens.start_discovery_modal import (
            StartDiscoveryModal,
        )

        def _on_discovery_choice(
            start_discovery: bool | None,
        ) -> None:
            self.dismiss(
                NewProjectResult(
                    project=project,
                    start_discovery=bool(start_discovery),
                )
            )

        self.app.push_screen(
            StartDiscoveryModal(project.name), _on_discovery_choice
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create-button":
            self.action_submit()
        elif event.button.id == "cancel-button":
            self.action_cancel()


__all__ = ["NewProjectScreen"]
