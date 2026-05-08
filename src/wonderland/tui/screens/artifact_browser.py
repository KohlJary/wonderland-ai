"""Browse all artifacts shipped during a run, optionally drilling
into one to read its full markdown.

Two screens here:
  - ``ArtifactBrowserScreen``: lists every artifact in a snapshot,
    columns kind / title / time. Sorted chronologically — reading
    top-to-bottom is reading the run's outputs in the order they
    were shipped.
  - ``ArtifactDetailScreen``: rendered markdown of one artifact.

Reachable from the Run Summary screen via the ``a`` binding, and
from the Utterance Modal via its artifact list (future wiring).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Markdown, Static

from wonderland.observer import HistoricalRunHandle, RunArtifact, RunMeeting


_PREVIEW_MAX_CHARS = 8000  # cap preview body so massive artifacts don't choke the pane


def _fmt_relative_time(t: datetime, anchor: datetime | None) -> str:
    if anchor is None:
        return t.strftime("%H:%M:%S")
    delta = (t - anchor).total_seconds()
    if delta < 60:
        return f"+{delta:>5.1f}s"
    return f"+{delta / 60:>5.1f}m"


class ArtifactBrowserScreen(Screen[None]):
    """List all artifacts in a snapshot, chronologically."""

    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
        Binding("enter", "open_selected", "Open", show=True),
        # Vim nav (j/k/g/G/H/L) is provided by WonderlandApp.
    ]

    def __init__(
        self,
        snapshot_dir: Path,
        *,
        meeting: RunMeeting | None = None,
    ) -> None:
        super().__init__()
        self.snapshot_dir = snapshot_dir
        # When set, the browser filters to artifacts shipped during
        # this meeting's time range. Used by the "press `a` from a
        # meeting detail" flow so you can see the artifacts that
        # particular meeting produced.
        self.meeting = meeting
        self._artifacts: list[RunArtifact] = []
        # Mirror of the most recent preview content. ``Static`` doesn't
        # expose what was passed to update(), so we keep a copy here
        # for tests + future inspection — same pattern as
        # MeetingDetailScreen._last_preview_text.
        self._last_preview_text: str = ""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical():
            yield Static(id="browser-header")
            yield DataTable(id="artifact-table", cursor_type="row")
            yield Static("[b]Body[/b]", id="preview-label")
            with VerticalScroll(id="preview-scroll"):
                yield Static(id="preview-body")
        yield Footer()

    def on_mount(self) -> None:
        try:
            handle = HistoricalRunHandle(self.snapshot_dir)
        except Exception as exc:  # noqa: BLE001
            self.query_one("#browser-header", Static).update(
                f"[red]Failed to load snapshot:[/red] {exc}"
            )
            return

        all_artifacts = handle.artifacts()

        # Apply meeting-scoped filter when one was passed in.
        #
        # Attribution is via the bus, not file mtime: walk every
        # utterance in this meeting's thread and collect every
        # artifact path that any speaker attached to their content.
        # An artifact "belongs to" a meeting iff some agent attached
        # it to a contribution in that meeting.
        #
        # We can't use mtime here — snapshots are bundled by
        # ``shutil.copy``, which rewrites mtimes to the bundle time,
        # so all snapshot artifacts post-date the meeting windows
        # and a time-range filter rejects everything. The bus is
        # the canonical record of what each meeting actually shipped.
        if self.meeting:
            paths_in_meeting: set[str] = set()
            for u in handle.utterances(thread_id=self.meeting.id):
                for attached in u.content.artifacts or []:
                    payload = (
                        attached.payload
                        if isinstance(attached.payload, dict)
                        else {}
                    )
                    raw_path = payload.get("path")
                    if raw_path:
                        # Basename match — the stored path is the
                        # original project path, not the snapshot
                        # path, but the filename matches.
                        paths_in_meeting.add(Path(raw_path).name)
            self._artifacts = [
                a for a in all_artifacts if a.path.name in paths_in_meeting
            ]
        else:
            self._artifacts = all_artifacts

        # Anchor for relative time: meeting start if filtered, else
        # run start.
        if self.meeting and self.meeting.started_at:
            anchor = self.meeting.started_at
        else:
            anchor = handle.summary().started_at

        # Header rollup: counts per kind, plus filter context.
        from collections import Counter

        counts = Counter(a.kind for a in self._artifacts)
        rollup = "  ".join(f"[b]{k}[/b]: {n}" for k, n in sorted(counts.items()))
        if self.meeting:
            scope_line = (
                f"[b]Filtered to {self.meeting.label}"
                f"{f' ({self.meeting.name})' if self.meeting.name else ''}"
                f"[/b] — {len(self._artifacts)} of {len(all_artifacts)} "
                f"artifacts shipped during this meeting"
            )
        else:
            scope_line = f"[b]Artifacts shipped:[/b] {len(self._artifacts)}"
        self.query_one("#browser-header", Static).update(
            f"{scope_line}\n{rollup}" if rollup else scope_line
        )

        table = self.query_one("#artifact-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Time", "Kind", "Title", "File")
        for a in self._artifacts:
            time_str = _fmt_relative_time(a.created_at, anchor)
            file_name = a.path.name
            title = a.title[:60] + ("…" if len(a.title) > 60 else "")
            table.add_row(time_str, a.kind, title, file_name)
        table.focus()
        # Prime the preview pane with the first row.
        self._update_preview(0 if self._artifacts else -1)

    def _update_preview(self, row_index: int) -> None:
        """Refresh the body-preview pane to reflect the artifact at
        ``row_index``. Called on row-highlight changes (cursor move
        from j/k or mouse hover). Plain-text preview to keep parity
        with MeetingDetailScreen; Enter still drills into the
        Markdown-rendered ArtifactDetailScreen."""
        preview = self.query_one("#preview-body", Static)
        if row_index < 0 or row_index >= len(self._artifacts):
            text = "(no artifact selected)"
            preview.update(text)
            self._last_preview_text = text
            return
        a = self._artifacts[row_index]
        try:
            body = a.path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            body = f"(could not read {a.path.name}: {exc})"
        if len(body) > _PREVIEW_MAX_CHARS:
            body = body[:_PREVIEW_MAX_CHARS] + "\n\n[dim]… (truncated; press Enter for full body)[/dim]"
        preview.update(body)
        self._last_preview_text = body

    def on_data_table_row_highlighted(
        self, event: DataTable.RowHighlighted
    ) -> None:
        """Cursor moved to a different row — refresh the preview pane."""
        self._update_preview(event.cursor_row)

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_open_selected(self) -> None:
        table = self.query_one("#artifact-table", DataTable)
        row = table.cursor_row
        if row is None or row < 0 or row >= len(self._artifacts):
            return
        self.app.push_screen(ArtifactDetailScreen(self._artifacts[row]))

    def on_data_table_row_selected(
        self, _event: DataTable.RowSelected
    ) -> None:
        self.action_open_selected()


class ArtifactDetailScreen(Screen[None]):
    """Render the markdown of one artifact."""

    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
        Binding("q", "back", "Back", show=False),
    ]

    def __init__(self, artifact: RunArtifact) -> None:
        super().__init__()
        self.artifact = artifact

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical():
            yield Static(id="detail-header")
            with VerticalScroll(id="detail-scroll"):
                yield Markdown(id="detail-markdown")
        yield Footer()

    def on_mount(self) -> None:
        a = self.artifact
        meta_lines = [
            f"[b]Kind:[/b] {a.kind}    "
            f"[b]Title:[/b] {a.title}",
            f"[b]Path:[/b] {a.path}",
            f"[b]Shipped at:[/b] {a.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
        ]
        self.query_one("#detail-header", Static).update("\n".join(meta_lines))

        try:
            content = a.path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            content = f"# Error loading artifact\n\n```\n{exc}\n```"
        self.query_one("#detail-markdown", Markdown).update(content)

    def action_back(self) -> None:
        self.app.pop_screen()


__all__ = ["ArtifactBrowserScreen", "ArtifactDetailScreen"]
