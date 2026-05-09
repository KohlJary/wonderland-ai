"""Skeleton picker — pre-launch step for the NewRunScreen flow
when the project root is bare (T71 / P8.6).

Per analysis 037: every TUI run since r33 has been against bare
project roots, and the deliverable shape progressively collapsed
because there was no skeleton communicating "production code goes
in src/." This picker fills that gap — when the operator types a
bare path in NewRunScreen, the picker shows the bundled skeletons
and lets them apply one before launch.

Layout follows the project_tui_lazygit_principle: list on the
left, preview on the right, action row at the bottom. Dismisses
with the chosen skeleton name (str), the sentinel "" for
"continue without skeleton", or None for cancel/back. The caller
(NewRunScreen) interprets these and either applies + relaunches
or aborts.
"""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Static

from wonderland.skeleton import (
    Skeleton,
    apply_skeleton,
    list_skeletons,
)


class SkeletonPickerScreen(Screen[str | None]):
    """Pick a skeleton (or opt out) before launching a run on a
    bare project root.

    Dismiss values:
      - skeleton name (str): apply this skeleton, then proceed
      - "" (empty string): continue without a skeleton (operator
        override; warning was acknowledged)
      - None: cancel — return to NewRunScreen without launching
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
        Binding("enter", "apply_selected", "Apply", show=True),
        Binding("s", "skip", "Skip (no skeleton)", show=True),
    ]

    def __init__(self, project_root: Path) -> None:
        super().__init__()
        self.project_root = project_root
        self._skeletons: list[Skeleton] = []
        self._notify_warning: str | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical():
            yield Static(
                f"[b]Skeleton picker[/b] — "
                f"[dim]project root: {self.project_root}[/dim]",
                id="skeleton-picker-header",
            )
            yield Static(
                "[dim]This project root is bare. Pick a skeleton to "
                "lay down a working hello-world (src/, tests/, "
                "conftest.py, etc.) before the team starts. The "
                "skeleton communicates structure to the agents — "
                "without it, deliverable shape can collapse "
                "(see analysis 037).[/dim]",
                id="skeleton-picker-blurb",
            )
            with Horizontal(id="skeleton-picker-row"):
                with Vertical(id="skeleton-list-pane"):
                    yield Static("[b]Available skeletons[/b]",
                                 id="skeleton-list-label")
                    yield DataTable(
                        id="skeleton-list-table",
                        cursor_type="row",
                    )
                with Vertical(id="skeleton-preview-pane"):
                    yield Static("[b]Preview[/b]",
                                 id="skeleton-preview-label")
                    with VerticalScroll(id="skeleton-preview-scroll"):
                        yield Static(
                            "[dim](no skeleton selected)[/dim]",
                            id="skeleton-preview",
                        )
            with Horizontal(id="skeleton-action-row"):
                yield Button(
                    "Apply selected",
                    id="skeleton-apply-button",
                    variant="primary",
                )
                yield Button(
                    "Continue without skeleton",
                    id="skeleton-skip-button",
                )
                yield Button(
                    "Cancel",
                    id="skeleton-cancel-button",
                )
        yield Footer()

    def on_mount(self) -> None:
        # Populate the skeleton table.
        table = self.query_one("#skeleton-list-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Name", "Description")
        self._skeletons = list_skeletons()
        for s in self._skeletons:
            table.add_row(s.name, s.description)
        if self._skeletons:
            table.cursor_coordinate = (0, 0)
            self._render_preview(self._skeletons[0])
        table.focus()

    def on_data_table_row_highlighted(
        self,
        event: DataTable.RowHighlighted,
    ) -> None:
        if event.data_table.id != "skeleton-list-table":
            return
        row = event.cursor_row
        if 0 <= row < len(self._skeletons):
            self._render_preview(self._skeletons[row])

    def _render_preview(self, skeleton: Skeleton) -> None:
        preview = self.query_one("#skeleton-preview", Static)
        top_dirs = skeleton.top_level_dirs()
        dirs_line = ", ".join(f"`{d}/`" for d in top_dirs) or "(no top-level dirs)"
        lines = [
            f"[b]{skeleton.name}[/b]",
            "",
            skeleton.description,
            "",
            f"[b]Top-level layout:[/b] {dirs_line}",
            f"[b]Files shipped:[/b] {len(skeleton.files)}",
        ]
        if skeleton.manifest.language:
            lines.append(f"[b]Language:[/b] {skeleton.manifest.language}")
        lines.append("")
        lines.append(
            f"[dim]Apply will copy these files into "
            f"{self.project_root}.[/dim]"
        )
        # Post-apply commands — the operator's path to a runnable
        # project. Auto-runner is deferred (roadmap 3a22d99e); for
        # now, surface the commands so the operator can copy-paste
        # into a shell after applying. Phrase in yellow so it
        # registers as a required follow-up, not optional polish.
        if skeleton.manifest.post_apply:
            lines.append("")
            lines.append(
                "[b yellow]Setup commands "
                "(run after apply, before launch):[/b yellow]"
            )
            for step in skeleton.manifest.post_apply:
                lines.append(f"  [dim]# {step.description}[/dim]")
                cwd_hint = (
                    "" if step.cwd in (".", "") else f"  [dim](cd {step.cwd}/)[/dim]"
                )
                lines.append(f"  [b]$[/b] {step.command}{cwd_hint}")
        preview.update("\n".join(lines))

    # --- Actions ---

    def action_apply_selected(self) -> None:
        table = self.query_one("#skeleton-list-table", DataTable)
        row = table.cursor_row
        if row is None or row >= len(self._skeletons):
            self.notify("Pick a skeleton first.", severity="warning")
            return
        skeleton = self._skeletons[row]
        try:
            written = apply_skeleton(skeleton, self.project_root)
        except FileExistsError as exc:
            self.notify(
                f"Refusing to overwrite: {exc}",
                severity="error",
                timeout=8,
            )
            return
        except Exception as exc:  # noqa: BLE001
            self.notify(
                f"Failed to apply skeleton: {exc}",
                severity="error",
                timeout=8,
            )
            return
        self.notify(
            f"Applied {skeleton.name} ({len(written)} files) → "
            f"{self.project_root}",
            timeout=4,
        )
        self.dismiss(skeleton.name)

    def action_skip(self) -> None:
        """Continue without a skeleton — operator override.
        Returns the empty string sentinel so NewRunScreen knows
        the operator deliberately declined."""
        self.dismiss("")

    def action_cancel(self) -> None:
        """Back out without launching."""
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "skeleton-apply-button":
            self.action_apply_selected()
        elif event.button.id == "skeleton-skip-button":
            self.action_skip()
        elif event.button.id == "skeleton-cancel-button":
            self.action_cancel()


__all__ = ["SkeletonPickerScreen"]
