"""Browse all run snapshots under a given root directory.

Discovers any subdirectory containing a ``wonderland-snapshot/`` and a
``run.log`` — i.e. any valid ``HistoricalRunHandle`` input. By default
points at ``analyses/data/`` of the current checkout, so the entire
analysis corpus is browsable out of the box.

Click a row (or press Enter) to open the Run Summary view for that
snapshot.
"""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static

from wonderland.observer import HistoricalRunHandle
from wonderland.tui.screens.cast import CastBrowserScreen
from wonderland.tui.screens.run_summary import RunSummaryScreen


def _discover_snapshots(root: Path) -> list[Path]:
    """Find all valid snapshot directories under ``root``.

    A directory is a valid snapshot if it contains both
    ``wonderland-snapshot/`` and ``run.log``. Searches at any depth
    so nested layouts (e.g. ``analyses/data/029/v6/``) work.
    """
    if not root.is_dir():
        return []
    out: list[Path] = []
    for run_log in root.rglob("run.log"):
        snapshot_dir = run_log.parent
        if (snapshot_dir / "wonderland-snapshot").is_dir():
            out.append(snapshot_dir)
    out.sort(key=lambda p: str(p))
    return out


def _fmt_cost(c: float) -> str:
    return f"${c:.2f}"


def _fmt_duration(s: float | None) -> str:
    if s is None:
        return "—"
    if s < 60:
        return f"{s:.0f}s"
    return f"{s / 60:.1f}m"


class SnapshotLibraryScreen(Screen[None]):
    """Lists snapshots discovered under a root directory."""

    BINDINGS = [
        Binding("enter", "open_selected", "Open", show=True),
        Binding("c", "open_cast", "The Cast", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        # Vim nav (j/k/g/G) is provided by WonderlandApp.
    ]

    def __init__(self, snapshot_root: Path) -> None:
        super().__init__()
        self.snapshot_root = snapshot_root
        self._snapshot_paths: list[Path] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical():
            yield Static(
                f"[b]Snapshots under[/b] {self.snapshot_root}",
                id="library-header",
            )
            yield DataTable(id="snapshot-table", cursor_type="row")
        yield Footer()

    def on_mount(self) -> None:
        self._populate()

    def action_refresh(self) -> None:
        self._populate()

    def _populate(self) -> None:
        table = self.query_one("#snapshot-table", DataTable)
        table.clear(columns=True)
        table.add_columns(
            "Snapshot", "Workflow", "Outcome", "Time", "Calls", "Cost"
        )
        self._snapshot_paths = _discover_snapshots(self.snapshot_root)
        for path in self._snapshot_paths:
            try:
                handle = HistoricalRunHandle(path)
                summary = handle.summary()
            except Exception:  # noqa: BLE001 — best-effort load
                table.add_row(
                    str(path.relative_to(self.snapshot_root)),
                    "(load error)",
                    "—",
                    "—",
                    "—",
                    "—",
                )
                continue
            elapsed: float | None = None
            if summary.started_at and summary.ended_at:
                elapsed = (
                    summary.ended_at - summary.started_at
                ).total_seconds()
            table.add_row(
                str(path.relative_to(self.snapshot_root)),
                summary.workflow_name or "—",
                (summary.outcome or "—")[:14],
                _fmt_duration(elapsed),
                str(summary.total_calls),
                _fmt_cost(summary.total_cost),
            )
        if self._snapshot_paths:
            table.cursor_coordinate = (0, 0)

    def action_open_selected(self) -> None:
        table = self.query_one("#snapshot-table", DataTable)
        row = table.cursor_row
        if row is None or row >= len(self._snapshot_paths):
            return
        self.app.push_screen(RunSummaryScreen(self._snapshot_paths[row]))

    def action_open_cast(self) -> None:
        self.app.push_screen(CastBrowserScreen())

    def on_data_table_row_selected(self, _event: DataTable.RowSelected) -> None:
        self.action_open_selected()


__all__ = ["SnapshotLibraryScreen"]
