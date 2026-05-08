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
from wonderland.tui.screens.artifact_browser import ArtifactBrowserScreen
from wonderland.tui.screens.meeting_detail import MeetingDetailScreen


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
        Binding("enter", "open_selected", "Open meeting", show=True),
        Binding("a", "open_artifacts", "Artifacts", show=True),
        # Vim nav (j/k/g/G/H/L) is provided by WonderlandApp.
        # Tab cycles focus between the three tables (Textual default).
    ]

    def __init__(self, snapshot_dir: Path) -> None:
        super().__init__()
        self.snapshot_dir = snapshot_dir
        self._meetings_cache: list = []  # populated in _render_meetings

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
        # Focus meetings table by default so j/k navigation lands
        # there without needing to Tab from another widget first.
        self.query_one("#meetings-table", DataTable).focus()

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
        self._meetings_cache = handle.meetings()
        for m in self._meetings_cache:
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

    def action_open_artifacts(self) -> None:
        """Open the artifact browser for this snapshot."""
        self.app.push_screen(ArtifactBrowserScreen(self.snapshot_dir))

    def action_open_selected(self) -> None:
        """Enter on the meetings table opens the meeting transcript.

        On the other tables (agents, utterances), it's a no-op for now —
        agent drill-down and utterance focus aren't built yet.
        """
        focused = self.focused
        if not isinstance(focused, DataTable):
            return
        if focused.id != "meetings-table":
            return
        row = focused.cursor_row
        if row is None or row >= len(self._meetings_cache):
            return
        meeting = self._meetings_cache[row]
        self.app.push_screen(
            MeetingDetailScreen(self.snapshot_dir, meeting)
        )

    def on_data_table_row_selected(self, _event: DataTable.RowSelected) -> None:
        # Mouse-click / Enter on a row routes through here too.
        self.action_open_selected()


__all__ = ["RunSummaryScreen"]
