"""Detail view for one meeting within a snapshot — the full utterance
transcript in chronological order. Drilling into a meetings-table row
in Run Summary lands here.

The framework's *deliberation* lives in this view: who said what to
whom, in what order, with what speech act. Reading the transcript is
how you understand a meeting that worked or one that broke.

P8.3 will replace this with a richer multi-pane Run Watcher (replay-
aware, with timeline + agent state + artifact tree). This view is the
simpler "give me the conversation" alternative; both will live
alongside.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import ModalScreen, Screen
from textual.widgets import DataTable, Footer, Header, Static

from wonderland.observer import HistoricalRunHandle, RunMeeting
from wonderland.tui.screens.artifact_browser import (
    ArtifactBrowserScreen,
    ArtifactDetailScreen,
)
from wonderland.utterance import Utterance


def _fmt_cost(c: float) -> str:
    return f"${c:.4f}"


def _fmt_duration(s: float | None) -> str:
    if s is None:
        return "—"
    if s < 60:
        return f"{s:.1f}s"
    return f"{s / 60:.1f}m"


def _fmt_relative_time(t: datetime, anchor: datetime | None) -> str:
    """Format a timestamp as offset-from-meeting-start."""
    if anchor is None:
        return t.strftime("%H:%M:%S")
    delta = (t - anchor).total_seconds()
    if delta < 60:
        return f"+{delta:>5.1f}s"
    return f"+{delta / 60:>5.1f}m"


class MeetingDetailScreen(Screen[None]):
    """Full transcript of one meeting from a historical run.

    Layout: top half is a row-per-utterance table; bottom half is a
    live preview pane showing the full body of whichever row the
    cursor's currently on. Enter opens a modal with the full
    utterance metadata + body for deeper inspection.
    """

    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
        Binding("enter", "expand_selected", "Expand", show=True),
        Binding("a", "open_meeting_artifacts", "Artifacts", show=True),
        Binding("f", "filter_next_speaker", "Filter speaker", show=True),
        Binding("F", "filter_prev_speaker", "Prev speaker", show=False),
        # Vim nav (j/k/g/G/H/L) is provided by WonderlandApp.
    ]

    def __init__(self, snapshot_dir: Path, meeting: RunMeeting) -> None:
        super().__init__()
        self.snapshot_dir = snapshot_dir
        self.meeting = meeting
        # Cached for cursor → utterance lookup on highlight + expand.
        # Holds the FILTERED view (what's currently rendered in the
        # table). Use _all_utterances for the unfiltered list.
        self._utterances: list[Utterance] = []
        self._all_utterances: list[Utterance] = []
        # Speaker filter: None = show all; otherwise a speaker name.
        # The cycle key 'f' rotates through speakers found in this
        # meeting (None → speaker1 → speaker2 → ... → None).
        self._filter_speaker: str | None = None
        self._speakers_in_meeting: list[str] = []
        # Tracks the most recent preview content (the Static's
        # public API doesn't expose a getter for what was passed to
        # update(), so we mirror it here for tests + future inspection).
        self._last_preview_text: str = ""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical():
            yield Static(id="meeting-header")
            yield DataTable(id="utterance-table", cursor_type="row")
            yield Static("[b]Body[/b]", id="preview-label")
            with VerticalScroll(id="preview-scroll"):
                yield Static(id="preview-body")
        yield Footer()

    def on_mount(self) -> None:
        self._render_header()
        self._render_utterances()
        # Focus the table so j/k work out of the box.
        table = self.query_one("#utterance-table", DataTable)
        table.focus()
        # Prime the preview with the first row.
        self._update_preview(0)

    def _render_header(self) -> None:
        m = self.meeting
        name_part = f"  {m.name}" if m.name else ""
        elapsed = _fmt_duration(m.elapsed_seconds)
        if self._filter_speaker:
            filter_line = (
                f"[b]Filter:[/b] [cyan]{self._filter_speaker}[/cyan]    "
                f"({len(self._utterances)} of {len(self._all_utterances)} "
                f"utterances)    "
                f"[dim]press 'f' to cycle, 'F' to go back[/dim]"
            )
        else:
            filter_line = (
                f"[b]Filter:[/b] all speakers    "
                f"({len(self._all_utterances)} utterances)    "
                f"[dim]press 'f' to filter by speaker[/dim]"
            )
        lines = [
            f"[b]{m.label}[/b]{name_part}    "
            f"[b]Outcome:[/b] {m.outcome or '—'}",
            f"[b]Thread:[/b] {m.id}    "
            f"[b]Time:[/b] {elapsed}    "
            f"[b]Calls:[/b] {m.calls}    "
            f"[b]Cost:[/b] {_fmt_cost(m.cost)}",
            filter_line,
        ]
        self.query_one("#meeting-header", Static).update("\n".join(lines))

    def _render_utterances(self) -> None:
        try:
            handle = HistoricalRunHandle(self.snapshot_dir)
        except Exception as exc:  # noqa: BLE001
            self.query_one("#meeting-header", Static).update(
                f"[red]Failed to load snapshot:[/red] {exc}"
            )
            return

        # Load full transcript once, then derive the filtered view.
        # Cycling the filter just re-renders without re-reading.
        self._all_utterances = list(
            handle.utterances(thread_id=self.meeting.id)
        )
        # Speakers present in this meeting, sorted for stable cycling.
        # Excludes Dodo's procedural moves to avoid the "filter to
        # nudges and acknowledgments" anti-feature; Dodo is the
        # convenor, not a participant.
        seen: set[str] = set()
        for u in self._all_utterances:
            if u.speaker.name != "dodo" and u.speaker.name not in seen:
                seen.add(u.speaker.name)
        self._speakers_in_meeting = sorted(seen)

        self._refresh_filtered_view()

    def _refresh_filtered_view(self) -> None:
        """Re-render the utterance table for the current filter
        without re-reading the SQLite. Cheap; just a list comprehension
        + table repopulation."""
        if self._filter_speaker is None:
            self._utterances = list(self._all_utterances)
        else:
            self._utterances = [
                u
                for u in self._all_utterances
                if u.speaker.name == self._filter_speaker
            ]

        table = self.query_one("#utterance-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Time", "Speaker", "Act", "Addressed", "Body")

        anchor = self.meeting.started_at
        for u in self._utterances:
            time_str = _fmt_relative_time(u.timestamp, anchor)
            body = (u.content.body or "").strip().split("\n", 1)[0] or "(no body)"
            if len(body) > 100:
                body = body[:100] + "…"
            if isinstance(u.addressed_to, str):
                addressed = u.addressed_to
            else:
                addressed = ",".join(a.name for a in u.addressed_to) or "—"
            table.add_row(
                time_str,
                u.speaker.name,
                u.speech_act.value,
                addressed[:18],
                body,
            )

        # Refresh header to show new filter status + counts.
        self._render_header()
        # Re-prime the preview pane.
        self._update_preview(0 if self._utterances else -1)

    def _update_preview(self, row_index: int) -> None:
        """Refresh the body-preview pane to reflect the utterance at
        ``row_index``. Called on row-highlight changes (cursor move
        from j/k or mouse hover)."""
        preview = self.query_one("#preview-body", Static)
        if row_index < 0 or row_index >= len(self._utterances):
            text = "(no utterance selected)"
            preview.update(text)
            self._last_preview_text = text
            return
        u = self._utterances[row_index]
        body = u.content.body or "(no body)"
        artifact_summary = ""
        if u.content.artifacts:
            kinds = ", ".join(
                f"{a.kind}: {a.payload.get('title', '?')}"
                for a in u.content.artifacts
            )
            artifact_summary = f"\n\n[b]Artifacts:[/b] {kinds}"
        text = body + artifact_summary
        preview.update(text)
        self._last_preview_text = text

    def on_data_table_row_highlighted(
        self, event: DataTable.RowHighlighted
    ) -> None:
        """Cursor moved to a different row — refresh the preview pane."""
        self._update_preview(event.cursor_row)

    def on_data_table_row_selected(
        self, _event: DataTable.RowSelected
    ) -> None:
        """Mouse-click / Enter on a row routes here. DataTable's
        default Enter handling intercepts before screen-level bindings
        fire, so this is the load-bearing path for expand."""
        self.action_expand_selected()

    def action_expand_selected(self) -> None:
        """Enter on a row — open the full utterance in a modal."""
        table = self.query_one("#utterance-table", DataTable)
        row = table.cursor_row
        if row is None or row < 0 or row >= len(self._utterances):
            return
        self.app.push_screen(
            UtteranceModalScreen(
                self._utterances[row], self.meeting, self.snapshot_dir
            )
        )

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_open_meeting_artifacts(self) -> None:
        """Open the artifact browser filtered to this meeting's
        time range — see only the artifacts that *this* meeting
        shipped."""
        self.app.push_screen(
            ArtifactBrowserScreen(self.snapshot_dir, meeting=self.meeting)
        )

    def action_filter_next_speaker(self) -> None:
        """Cycle the speaker filter forward.

        Sequence: None (all) → speakers[0] → speakers[1] → ... → None.
        """
        self._cycle_filter(direction=1)

    def action_filter_prev_speaker(self) -> None:
        """Cycle the speaker filter backward."""
        self._cycle_filter(direction=-1)

    def _cycle_filter(self, *, direction: int) -> None:
        speakers = self._speakers_in_meeting
        if not speakers:
            return
        # Build the cycle as [None, speakers[0], speakers[1], ...] so
        # advancing past the last lands back on None (= all).
        cycle: list[str | None] = [None] + list(speakers)
        try:
            current_idx = cycle.index(self._filter_speaker)
        except ValueError:
            current_idx = 0
        next_idx = (current_idx + direction) % len(cycle)
        self._filter_speaker = cycle[next_idx]
        self._refresh_filtered_view()

    # ------------------------------------------------------------------ #
    # Vim navigation
    # ------------------------------------------------------------------ #

class UtteranceModalScreen(ModalScreen[None]):
    """Full-screen view of one utterance — speaker, act, all metadata,
    full body, and any attached artifacts.

    Reachable via Enter on a row in MeetingDetailScreen. Escape pops
    back. The modal is what you'd open to read Caterpillar's full M6
    review or one of Hatter's longer test_scenario rationales.

    When the utterance has attached artifacts, a selectable list at
    the bottom of the modal lets you drill from utterance → its
    artifact's rendered markdown directly. Tab switches focus between
    the body scroll and the artifact list; Enter on an artifact opens
    its detail screen.
    """

    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
        Binding("q", "back", "Back", show=False),
        Binding("enter", "open_artifact", "Open artifact", show=True),
        # Vim nav (j/k/g/G/H/L) is provided by WonderlandApp.
    ]

    DEFAULT_CSS = """
    UtteranceModalScreen {
        align: center middle;
    }
    #modal-container {
        width: 90%;
        height: 85%;
        background: #0a0a14;
        border: round #00d9d9;
        padding: 1 2;
    }
    #modal-meta {
        height: auto;
        margin-bottom: 1;
        color: #b794f4;
    }
    #modal-body-scroll {
        height: 1fr;
    }
    #modal-body {
        color: #e6e6f0;
    }
    #modal-artifacts-label {
        margin-top: 1;
        color: #b794f4;
    }
    #modal-artifacts-table {
        height: auto;
        max-height: 8;
        margin-top: 1;
    }
    """

    def __init__(
        self,
        utterance: Utterance,
        meeting: RunMeeting,
        snapshot_dir: Path,
    ) -> None:
        super().__init__()
        self.utterance = utterance
        self.meeting = meeting
        self.snapshot_dir = snapshot_dir
        # Resolved RunArtifacts for each utterance.Artifact, keyed by
        # filename match. Populated on mount.
        self._resolved_artifacts: list = []  # list[RunArtifact]

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Static(id="modal-meta")
            yield Static("[b]Body[/b]", id="modal-body-label")
            with VerticalScroll(id="modal-body-scroll"):
                yield Static(id="modal-body")
            # Artifact list is shown below the body when the utterance
            # has attached artifacts. Otherwise hidden (display: none
            # via on_mount, since Textual doesn't easily allow
            # conditional compose).
            yield Static(
                "[b]Artifacts (Enter to open)[/b]",
                id="modal-artifacts-label",
            )
            yield DataTable(id="modal-artifacts-table", cursor_type="row")

    def on_mount(self) -> None:
        u = self.utterance
        # addressed_to: "caucus" or list[AgentIdentity]
        if isinstance(u.addressed_to, str):
            addressed = u.addressed_to
        else:
            addressed = ", ".join(a.name for a in u.addressed_to) or "—"
        anchor = self.meeting.started_at
        time_str = _fmt_relative_time(u.timestamp, anchor)
        absolute = u.timestamp.strftime("%H:%M:%S.%f")[:-3]
        meta_lines = [
            f"[b]Meeting:[/b] {self.meeting.label} "
            f"({self.meeting.name or self.meeting.id})",
            f"[b]Speaker:[/b] {u.speaker.name}    "
            f"[b]Act:[/b] {u.speech_act.value}    "
            f"[b]Addressed:[/b] {addressed}",
            f"[b]Time:[/b] {time_str} (abs {absolute})",
            f"[b]Utterance ID:[/b] {u.id}",
        ]
        if u.parent_id:
            meta_lines.append(f"[b]Parent:[/b] {u.parent_id}")
        if u.is_seed:
            meta_lines.append("[b]Seed:[/b] yes (replayed from prior meeting)")
        self.query_one("#modal-meta", Static).update("\n".join(meta_lines))

        body_widget = self.query_one("#modal-body", Static)
        body_widget.update(u.content.body or "(no body)")

        # Resolve attached artifacts to their on-disk RunArtifact
        # equivalents (so we can drill from the modal into the
        # artifact's full markdown).
        self._resolve_and_render_artifacts()

    def _resolve_and_render_artifacts(self) -> None:
        label = self.query_one("#modal-artifacts-label", Static)
        table = self.query_one("#modal-artifacts-table", DataTable)
        if not self.utterance.content.artifacts:
            # Hide the artifact UI when there are none to show.
            label.display = False
            table.display = False
            return

        # Lazy-import to avoid circular reference at module load.
        from wonderland.observer import HistoricalRunHandle

        try:
            handle = HistoricalRunHandle(self.snapshot_dir)
            all_artifacts = handle.artifacts()
        except Exception:  # noqa: BLE001 — best-effort; fall back to text
            all_artifacts = []

        # Match utterance.Artifact → RunArtifact by filename
        # (basename of the path stored in the artifact's payload).
        # The full path stored in the utterance points at the
        # original project root (e.g. /tmp/wonderland-...), which
        # doesn't exist in the snapshot — but the basename does.
        by_basename = {a.path.name: a for a in all_artifacts}
        self._resolved_artifacts = []
        table.clear(columns=True)
        table.add_columns("Kind", "Title", "Status")
        for a_attached in self.utterance.content.artifacts:
            payload = a_attached.payload or {}
            payload_path = payload.get("path", "")
            basename = Path(payload_path).name if payload_path else ""
            run_artifact = by_basename.get(basename)
            if run_artifact is None:
                # Couldn't resolve — render as a non-selectable row
                # so the user still sees the utterance lists this
                # artifact, but pressing Enter won't navigate.
                title = payload.get("title", "?")
                table.add_row(a_attached.kind, str(title)[:60], "(not on disk)")
                self._resolved_artifacts.append(None)
            else:
                title = run_artifact.title[:60]
                table.add_row(run_artifact.kind, title, "✓")
                self._resolved_artifacts.append(run_artifact)

        # Focus the artifacts table when the modal opens — that's
        # the new interaction worth highlighting. Tab to switch to
        # the body scroll if needed.
        table.focus()

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_open_artifact(self) -> None:
        """Enter on an artifact row → push ArtifactDetailScreen."""
        table = self.query_one("#modal-artifacts-table", DataTable)
        row = table.cursor_row
        if row is None or row < 0 or row >= len(self._resolved_artifacts):
            return
        run_artifact = self._resolved_artifacts[row]
        if run_artifact is None:
            return  # not on disk; can't open
        self.app.push_screen(ArtifactDetailScreen(run_artifact))

    def on_data_table_row_selected(
        self, _event: DataTable.RowSelected
    ) -> None:
        self.action_open_artifact()


__all__ = ["MeetingDetailScreen", "UtteranceModalScreen"]
