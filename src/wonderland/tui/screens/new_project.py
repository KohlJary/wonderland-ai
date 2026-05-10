"""NewProjectScreen — register a new project via TUI form (P11 T76).

Replaces the T75 'use the CLI for now' notify with an in-TUI flow.
Form fields:

  - name (validated against the registry: non-empty, unique)
  - path (expanded + resolved; warns on bare-root vs non-bare detect)
  - default workflow (Select drawn from list_workflows())
  - default skeleton (Select drawn from list_skeletons())
  - default budget (Input, dollar-validated)

On confirm:
  1. Validate (name, path, uniqueness, budget)
  2. Register via wonderland.project.register_project()
  3. If a skeleton was selected AND the path is bare AND the operator
     ticked the 'Apply now' checkbox: apply_skeleton() to the path
  4. Pop back to ProjectLibraryScreen with refresh + selection on the
     new project (T79 dashboard will replace this in a later phase)

Layout follows project_tui_lazygit_principle: single-pane form
(this is a registration step, not a navigation surface — full canvas
is appropriate). Tab/Enter advances through fields.
"""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Button,
    Checkbox,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
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
from wonderland.workflow import list_workflows


class NewProjectScreen(Screen[Project | None]):
    """Form for registering a new project. Dismisses with the
    registered Project on success, None on cancel."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
        Binding("ctrl+s", "submit", "Create", show=True),
    ]

    _FORM_ORDER: tuple[str, ...] = (
        "name-input",
        "path-input",
        "workflow-select",
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
                        "[b]Initial workflow[/b] [dim](optional)[/dim]",
                        id="workflow-label",
                    )
                    yield Select(
                        [(w, w) for w in list_workflows()],
                        id="workflow-select",
                        allow_blank=True,
                        prompt="(no preselection — pick per run)",
                    )
                    yield Static(
                        "[dim]Workflow choice is per-run (TDD for "
                        "features, smoke for sanity checks, etc.). "
                        "This sets a starting hint; NewRunScreen "
                        "auto-updates it to whatever you actually "
                        "ran most recently.[/dim]",
                        id="workflow-help",
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
        self.query_one("#name-input", Input).focus()

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
        workflow = self.query_one("#workflow-select", Select).value
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
        workflow_norm = workflow if isinstance(workflow, str) and workflow else None
        skeleton_norm = (
            skeleton_name if isinstance(skeleton_name, str) and skeleton_name else None
        )

        # Build + register --------------------------------------------
        try:
            project = Project(
                name=name,
                root_path=resolved_path,
                last_workflow=workflow_norm,
                default_skeleton=skeleton_norm,
                default_budget=budget,
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
                    written = apply_skeleton(skeleton, resolved_path)
                    self.notify(
                        f"Project registered + skeleton applied "
                        f"({len(written)} files).",
                        timeout=4,
                    )
                else:
                    pc_path = write_project_context_from_skeleton(
                        skeleton, resolved_path
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

        self.dismiss(project)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create-button":
            self.action_submit()
        elif event.button.id == "cancel-button":
            self.action_cancel()


__all__ = ["NewProjectScreen"]
