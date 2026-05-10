"""EditProjectScreen — mutate a registered project's defaults
(P11 T77).

Changes the editable subset of a Project record. Read-only fields
(name, root_path, created_at, last_run_id) display for context but
can't be mutated — those represent identity / system-managed history.

Mutable fields:
  - last_workflow (Select; auto-updated by NewRunScreen on each
    successful launch, but manual override is reasonable when
    operators want to reset the prefill)
  - default_skeleton (Select; informational only — does NOT re-apply
    the skeleton on save, just updates the metadata)
  - default_budget (Input; per-run dollar default)

Archive / unarchive happen via the project library's keybinds
('x' / 'u'), not this form, so the operator can't accidentally
archive while editing other fields.

Notification preferences will land here once the auto-sentinel
notification work (roadmap 24e8ce94) ships — for now those default
fields persist through save unchanged.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
)

from wonderland.project import Project, save_project
from wonderland.skeleton import list_skeletons
from wonderland.workflow import list_workflows


class EditProjectScreen(Screen[Project | None]):
    """Form for editing a registered project's mutable defaults.
    Dismisses with the saved Project on success, None on cancel."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
        Binding("ctrl+s", "submit", "Save", show=True),
    ]

    _FORM_ORDER: tuple[str, ...] = (
        "edit-workflow-select",
        "edit-skeleton-select",
        "edit-budget-input",
        "edit-save-button",
    )

    def __init__(self, project: Project) -> None:
        super().__init__()
        self.project = project

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical(id="edit-project-root"):
            yield Static(
                f"[b]Edit project[/b] · [accent]{self.project.name}[/accent]",
                id="edit-project-header",
            )
            with VerticalScroll(id="edit-project-form-scroll"):
                with Vertical(id="edit-project-form"):
                    # Read-only context block
                    yield Label("[b]Identity[/b] [dim](read-only)[/dim]",
                                id="edit-identity-label")
                    yield Static(
                        f"[b]Name:[/b] {self.project.name}\n"
                        f"[b]Root:[/b] {self.project.root_path}\n"
                        f"[b]Created:[/b] "
                        f"{self.project.created_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
                        f"[b]Last run:[/b] "
                        f"{self.project.last_run_id or '[dim](none yet)[/dim]'}",
                        id="edit-identity-block",
                    )
                    yield Static(
                        "[dim]Name and path can't change after "
                        "registration. To rename, archive this "
                        "project (x in the library) and register a "
                        "fresh one against the same path.[/dim]",
                        id="edit-identity-help",
                    )

                    # Editable fields
                    yield Label(
                        "[b]Last workflow[/b] [dim](prefill hint; "
                        "auto-updates after each run)[/dim]",
                        id="edit-workflow-label",
                    )
                    yield Select(
                        [(w, w) for w in list_workflows()],
                        id="edit-workflow-select",
                        allow_blank=True,
                        prompt="(no preselection)",
                    )

                    yield Label(
                        "[b]Skeleton[/b] [dim](metadata only — does "
                        "not re-apply on save)[/dim]",
                        id="edit-skeleton-label",
                    )
                    yield Select(
                        [(s.name, s.name) for s in list_skeletons()],
                        id="edit-skeleton-select",
                        allow_blank=True,
                        prompt="(none)",
                    )

                    yield Label("[b]Default budget[/b]",
                                id="edit-budget-label")
                    yield Input(
                        value=f"{self.project.default_budget:.2f}",
                        placeholder="$ — dollars per run",
                        id="edit-budget-input",
                    )
                    yield Static(
                        "[dim]Pre-fills NewRunScreen's budget input "
                        "for runs on this project. Per-run override "
                        "always allowed.[/dim]",
                        id="edit-budget-help",
                    )

            with Horizontal(id="edit-project-action-row"):
                yield Button(
                    "▶ Save (ctrl+s)",
                    id="edit-save-button",
                    variant="primary",
                )
                yield Button(
                    "Cancel (esc)",
                    id="edit-cancel-button",
                )
        yield Footer()

    def on_mount(self) -> None:
        # Prefill the Selects from the project's current values.
        # Done in on_mount (not at compose time) to sidestep
        # Textual Select sentinel quirks — see new_project.py for
        # the same pattern.
        if self.project.last_workflow and self.project.last_workflow in list_workflows():
            self.query_one(
                "#edit-workflow-select", Select
            ).value = self.project.last_workflow
        skeleton_names = {s.name for s in list_skeletons()}
        if (
            self.project.default_skeleton
            and self.project.default_skeleton in skeleton_names
        ):
            self.query_one(
                "#edit-skeleton-select", Select
            ).value = self.project.default_skeleton
        self.query_one("#edit-workflow-select", Select).focus()

    # ------------------------------------------------------------------ #
    # Submit / cancel
    # ------------------------------------------------------------------ #

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "edit-budget-input":
            self.action_submit()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_submit(self) -> None:
        workflow = self.query_one("#edit-workflow-select", Select).value
        skeleton_name = self.query_one("#edit-skeleton-select", Select).value
        budget_str = self.query_one("#edit-budget-input", Input).value.strip()

        try:
            budget = float(budget_str)
            if budget <= 0:
                raise ValueError("budget must be positive")
        except ValueError:
            self.notify(
                f"Invalid budget {budget_str!r} (expected positive number).",
                severity="error",
            )
            self.query_one("#edit-budget-input", Input).focus()
            return

        # Same Select sentinel handling as new_project.py — only str
        # values count as a real selection.
        workflow_norm = workflow if isinstance(workflow, str) and workflow else None
        skeleton_norm = (
            skeleton_name if isinstance(skeleton_name, str) and skeleton_name else None
        )

        try:
            self.project.last_workflow = workflow_norm
            self.project.default_skeleton = skeleton_norm
            self.project.default_budget = budget
            save_project(self.project)
        except Exception as exc:  # noqa: BLE001
            self.notify(
                f"Failed to save project: {exc}",
                severity="error",
                timeout=8,
            )
            return

        self.notify(f"Saved {self.project.name!r}.", timeout=3)
        self.dismiss(self.project)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "edit-save-button":
            self.action_submit()
        elif event.button.id == "edit-cancel-button":
            self.action_cancel()


__all__ = ["EditProjectScreen"]
