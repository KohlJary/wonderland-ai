"""Detail view for one snapshot — summary header, meetings table,
per-agent telemetry, recent utterances. Same data layout as
``scripts/inspect_run.py`` but interactive.

Future work (P8.3) replaces the static tables with a multi-pane Run
Watcher that supports replay scrubbing. This view is the simpler
"give me the gist" alternative; both will live alongside.
"""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static

from wonderland.observer import HistoricalRunHandle


def _fmt_cost(c: float) -> str:
    return f"${c:.4f}"


def _fmt_duration(s: float | None) -> str:
    if s is None:
        return "—"
    if s < 60:
        return f"{s:.1f}s"
    return f"{s / 60:.1f}m"


class RunSummaryScreen(Screen[None]):
    """Detail view of one historical run snapshot."""

    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
        # Vim navigation — forwarded to the currently-focused DataTable.
        # Tab cycles between tables (Textual default).
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("g", "cursor_top", "Top", show=False),
        Binding("G", "cursor_bottom", "Bottom", show=False),
    ]

    def __init__(self, snapshot_dir: Path) -> None:
        super().__init__()
        self.snapshot_dir = snapshot_dir

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical():
            yield Static(id="summary-header")
            yield Static("[b]Meetings[/b]", id="meetings-label")
            yield DataTable(id="meetings-table", cursor_type="row")
            yield Static("[b]Per-agent telemetry[/b]", id="agents-label")
            yield DataTable(id="agents-table", cursor_type="row")
            yield Static("[b]Recent utterances[/b]", id="utterances-label")
            yield DataTable(id="utterances-table", cursor_type="row")
        yield Footer()

    def on_mount(self) -> None:
        try:
            handle = HistoricalRunHandle(self.snapshot_dir)
        except Exception as exc:  # noqa: BLE001
            self.query_one("#summary-header", Static).update(
                f"[red]Failed to load snapshot:[/red] {exc}"
            )
            return
        self._render_summary(handle)
        self._render_meetings(handle)
        self._render_agents(handle)
        self._render_utterances(handle)

    def _render_summary(self, handle: HistoricalRunHandle) -> None:
        s = handle.summary()
        elapsed: float | None = None
        if s.started_at and s.ended_at:
            elapsed = (s.ended_at - s.started_at).total_seconds()
        directive = s.directive or ""
        if len(directive) > 200:
            directive = directive[:200] + "…"
        lines = [
            f"[b]Snapshot:[/b] {self.snapshot_dir}",
            f"[b]Workflow:[/b] {s.workflow_name or '—'}    "
            f"[b]Outcome:[/b] {s.outcome or '—'}",
            f"[b]Cost:[/b] {_fmt_cost(s.total_cost)}    "
            f"[b]Calls:[/b] {s.total_calls}    "
            f"[b]Elapsed:[/b] {_fmt_duration(elapsed)}",
            f"[b]Directive:[/b] {directive}",
        ]
        self.query_one("#summary-header", Static).update("\n".join(lines))

    def _render_meetings(self, handle: HistoricalRunHandle) -> None:
        table = self.query_one("#meetings-table", DataTable)
        table.clear(columns=True)
        table.add_columns(
            "Label", "Name", "Outcome", "Time", "Calls", "Cost"
        )
        for m in handle.meetings():
            table.add_row(
                m.label,
                m.name or "—",
                m.outcome or "—",
                _fmt_duration(m.elapsed_seconds),
                str(m.calls),
                _fmt_cost(m.cost),
            )

    def _render_agents(self, handle: HistoricalRunHandle) -> None:
        table = self.query_one("#agents-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Agent", "Calls", "Cost")
        for t in handle.per_agent_telemetry():
            table.add_row(t.name, str(t.calls), _fmt_cost(t.cost))

    def _render_utterances(self, handle: HistoricalRunHandle) -> None:
        table = self.query_one("#utterances-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Thread", "Speaker", "Act", "Body")
        # First N utterances — keeps the view manageable. P8.3 will
        # supersede this with a scrollable, filterable, replay-aware
        # stream view.
        max_rows = 30
        for i, u in enumerate(handle.utterances()):
            if i >= max_rows:
                break
            body = (u.content.body or "(no body)").strip().split("\n", 1)[0]
            if len(body) > 80:
                body = body[:80] + "…"
            table.add_row(u.thread_id, u.speaker.name, u.speech_act.value, body)

    def action_back(self) -> None:
        self.app.pop_screen()

    # ------------------------------------------------------------------ #
    # Vim navigation — forwards to whichever DataTable currently holds
    # focus. Tab cycles between the three tables (Textual default).
    # ------------------------------------------------------------------ #

    def _focused_table(self) -> DataTable | None:
        focused = self.focused
        if isinstance(focused, DataTable):
            return focused
        return None

    def action_cursor_down(self) -> None:
        table = self._focused_table()
        if table is not None:
            table.action_cursor_down()

    def action_cursor_up(self) -> None:
        table = self._focused_table()
        if table is not None:
            table.action_cursor_up()

    def action_cursor_top(self) -> None:
        table = self._focused_table()
        if table is not None and table.row_count > 0:
            table.cursor_coordinate = (0, table.cursor_column)

    def action_cursor_bottom(self) -> None:
        table = self._focused_table()
        if table is not None and table.row_count > 0:
            table.cursor_coordinate = (table.row_count - 1, table.cursor_column)


__all__ = ["RunSummaryScreen"]
