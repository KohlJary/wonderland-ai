"""Live-watch screen — render a run as it happens (or as it's
replayed via Mock Turtle).

Three regions:
  - **Meetings ribbon** (top): one row per meeting, status updates as
    MeetingStarted/Ended events arrive. Per_item iterations get their
    own rows.
  - **Transcript pane** (middle, takes most of the screen): the most
    recent utterances scrolling in real-time.
  - **Status bar** (bottom): current speaker, live cost ticker, elapsed
    time.

T45 (this file) ships the layout only — renders against hand-built
dummy data so we can verify the UI shape before wiring it to the
streaming surface. T46 wires MockTurtleHandle.stream_events() into the
on_mount() so the screen actually goes live.

Per the gameplan: per_item iterations may have iteration_label=None
until roadmap 7a5ff815 lands; this screen synthesizes a discriminator
from the thread_id slug suffix as a graceful fallback.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static

from wonderland.observer import (
    AgentTelemetryDelta,
    ArtifactShipped,
    MeetingEnded,
    MeetingStarted,
    MockTurtleHandle,
    RunArtifact,
    RunEnded,
    RunHandle,
    RunStarted,
    UtteranceEmitted,
)
from wonderland.tui.screens.artifact_browser import ArtifactDetailScreen
from wonderland.utterance import Utterance


# Sentinel thread_id for the "All meetings" pseudo-row at the top of
# the meetings table — selecting it shows the unfiltered rolling
# transcript across all meetings (T46 behavior).
_ALL_MEETINGS = "__all__"


def _fmt_cost(c: float) -> str:
    return f"${c:.4f}"


def _fmt_elapsed(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes}:{secs:02d}"


def _label_from_thread_id(
    meeting_label: str,
    thread_id: str,
    base_meeting_id: str,
) -> str:
    """Synthesize a per_item iteration discriminator from the thread_id
    slug suffix when iteration_label is None. e.g., for base id
    ``test-scenarios``, thread_id ``test-scenarios-focus-session-with-
    visual-countdown`` → ``M4: Focus Session With Visual Countdown``.

    The base meeting id has to be passed in by the caller — it can't
    be inferred from the thread_id alone because base ids may
    themselves contain hyphens (``test-scenarios``, ``contract-
    negotiation``). The streaming consumer holds the base id in the
    meetings() lookup, so passing it through is cheap.

    Returns the original meeting_label if thread_id == base_meeting_id
    (not a per_item iteration) or if the prefix doesn't match.
    """
    if thread_id == base_meeting_id:
        return meeting_label
    prefix = f"{base_meeting_id}-"
    if not thread_id.startswith(prefix):
        return meeting_label
    slug = thread_id[len(prefix):]
    if not slug:
        return meeting_label
    pretty = slug.replace("-", " ").title()
    return f"{meeting_label}: {pretty}"


class LiveRunScreen(Screen[None]):
    """Three-region live view of a run.

    T45 scope: layout + static rendering against hand-built dummy
    data. T46 wires real streaming.
    """

    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
        Binding("enter", "open_meeting", "Open meeting", show=True),
        # Vim nav (j/k/g/G/H/L) is provided by WonderlandApp.
    ]

    def __init__(
        self,
        snapshot_dir: Path | None = None,
        *,
        handle: RunHandle | None = None,
        speed: float = 5.0,
        max_dwell_seconds: float = 2.0,
    ) -> None:
        """Three input paths:

          - ``snapshot_dir`` set, ``handle=None`` → wrap a
            MockTurtleHandle around the snapshot at the given speed
            + dwell. The replay path; default for the
            ``w`` (watch) entry from the snapshot library.
          - ``handle`` set explicitly → use it directly. Used by
            P8.5's NewRunScreen → LiveRunHandle handoff for live
            runs, and by anything else that wants to plug a
            different RunHandle in (e.g., a future AbortableHandle).
          - Both None → fall back to the T45 dummy data so the
            screen has something to show. Useful for layout testing
            in isolation.

        ``handle`` takes precedence over ``snapshot_dir`` when both
        are provided.
        """
        super().__init__()
        self.snapshot_dir = snapshot_dir
        self.handle = handle
        self.speed = speed
        self.max_dwell_seconds = max_dwell_seconds
        # Internal state — populated via on_mount stub for T45,
        # rewired to streaming subscription in T46.
        self._meetings_seen: dict[str, dict] = {}
        # Order of meeting thread_ids in the order they first appear,
        # so the ribbon shows them in run-time order rather than dict
        # iteration order.
        self._meeting_order: list[str] = []
        self._current_speaker: str | None = None
        # Cost accumulates across MeetingEnded events as the run plays;
        # AgentTelemetryDelta events at the end fill in final per-agent
        # totals. _per_agent_cost is the authoritative dict; _total_cost
        # is the rolling display value (sum of meeting cost deltas
        # until the per-agent finals overwrite).
        self._meeting_cost_total: float = 0.0
        self._per_agent_cost: dict[str, float] = {}
        self._per_agent_calls: dict[str, int] = {}
        self._total_cost: float = 0.0
        # Source-time tracking (where the run is at, in its own
        # timeline) — updated per event.
        self._stream_started_at: datetime | None = None
        self._latest_event_at: datetime | None = None
        # Wall-clock tracking (how long the user has been watching) —
        # _started_at is set when the first event arrives; _ended_at
        # is set when RunEnded fires so the counter freezes rather
        # than ticking past run completion. The 500ms refresh tick
        # uses _ended_at when set, datetime.now() otherwise.
        self._wall_clock_started_at: datetime | None = None
        self._wall_clock_ended_at: datetime | None = None

        # Per-meeting buffers — populated as events arrive, used to
        # re-render the transcript + artifacts panes when meeting
        # selection changes (lazygit-style filtering).
        # _meeting_transcripts[__all__] is the unfiltered rolling
        # stream — appended to on every UtteranceEmitted.
        self._meeting_transcripts: dict[str, list[tuple[Utterance, datetime]]] = {
            _ALL_MEETINGS: [],
        }
        self._meeting_artifacts: dict[str, list[RunArtifact]] = {
            _ALL_MEETINGS: [],
        }
        # Currently-selected thread_id; drives transcript + artifact
        # pane content. Defaults to All-Meetings — the unfiltered
        # rolling-stream view that matches T46 behavior.
        self._selected_thread_id: str = _ALL_MEETINGS
        # The most-recently-started thread on the bus — used to
        # attribute ArtifactShipped events to the right meeting.
        # Updated in _handle_meeting_started; distinct from
        # _selected_thread_id (user-driven).
        self._last_open_thread_id: str | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical():
            yield Static("[b]Run watch[/b]", id="live-header")
            with Horizontal(id="live-main-row"):
                # Left pane — meetings list (focusable).
                with Vertical(id="left-pane"):
                    yield Static("[b]Meetings[/b]", id="meetings-label")
                    yield DataTable(
                        id="live-meetings-table",
                        cursor_type="row",
                    )
                # Right pane — transcript table (top), body preview
                # (middle, updates as the user moves the transcript
                # cursor), artifacts table (bottom). All filter to
                # the meeting selected in the left pane.
                with Vertical(id="right-pane"):
                    yield Static("[b]Transcript[/b]", id="transcript-label")
                    yield DataTable(
                        id="transcript-table",
                        cursor_type="row",
                    )
                    yield Static("[b]Body[/b]", id="transcript-body-label")
                    with VerticalScroll(id="transcript-body-scroll"):
                        yield Static(id="transcript-body")
                    yield Static(
                        "[b]Artifacts[/b]",
                        id="artifacts-label",
                    )
                    yield DataTable(
                        id="live-artifacts-table",
                        cursor_type="row",
                    )
            yield Static(id="live-status")
        yield Footer()

    def on_mount(self) -> None:
        # Initialize the meetings table with an "All meetings"
        # pseudo-row at index 0 — selecting it shows the unfiltered
        # rolling transcript (T46 default behavior).
        table = self.query_one("#live-meetings-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Meeting", "Status", "Calls", "Cost")
        table.add_row("[b]All meetings[/b]", "—", "—", "—")
        # Initialize the transcript table.
        ttable = self.query_one("#transcript-table", DataTable)
        ttable.clear(columns=True)
        ttable.add_columns("Time", "Speaker", "Act", "Body")
        # Initialize artifacts table.
        atable = self.query_one("#live-artifacts-table", DataTable)
        atable.clear(columns=True)
        atable.add_columns("Kind", "Title")
        # Initial body preview + status bar — dashes until events flow.
        self.query_one("#transcript-body", Static).update(
            "[dim](no utterance selected)[/dim]"
        )
        self._render_status_bar()

        if self.handle is None and self.snapshot_dir is None:
            # No source bound — fall back to the T45 dummy data so
            # the screen has something to show. Useful for testing
            # the layout in isolation.
            self._render_static_dummy()
        else:
            # Stream events from the bound source. The @work decorator
            # runs the consumer in a background task so the UI stays
            # responsive — keystrokes, scroll, and meeting drill-down
            # all keep working while the stream drains.
            self._consume_stream()

        # Refresh the status bar every 500ms so the elapsed counter
        # ticks even when no events are arriving (during quiet
        # periods between calls). The set_interval handle auto-
        # cancels when the screen unmounts.
        self.set_interval(0.5, self._render_status_bar)

        table.focus()

    @work(exclusive=True)
    async def _consume_stream(self) -> None:
        """Subscribe to the bound RunHandle's stream_events() and
        update the screen state as each event arrives.

        Runs in a Textual worker so the UI thread stays responsive.
        Auto-cancels when the screen unmounts (the handle's finally-
        block teardown runs cleanly).
        """
        # Resolve the source: explicit handle > snapshot_dir wrapped
        # in MockTurtle. The handle path supports any RunHandle —
        # MockTurtleHandle, LiveRunHandle, or any future variant.
        if self.handle is not None:
            handle: RunHandle = self.handle
        elif self.snapshot_dir is not None:
            try:
                handle = MockTurtleHandle(
                    self.snapshot_dir,
                    speed=self.speed,
                    max_dwell_seconds=self.max_dwell_seconds,
                )
            except Exception as exc:  # noqa: BLE001
                self.query_one("#live-header", Static).update(
                    f"[red]Failed to load snapshot:[/red] {exc}"
                )
                return
        else:
            return  # Should never happen given the on_mount branch.

        # Cache the base meeting ids once so we can discriminate
        # per_item iterations against them. For live runs against
        # LiveRunHandle.meetings() pre-stream, this returns []; the
        # stream's MeetingStarted events handle the discriminator
        # gracefully via the slug-suffix fallback.
        base_meeting_ids = [m.id for m in handle.meetings()]

        async for event in handle.stream_events():
            self._dispatch_event(event, base_meeting_ids)

    def _dispatch_event(
        self,
        event,
        base_meeting_ids: list[str],
    ) -> None:
        """Route a streaming event to the appropriate state-updater.
        Each updater is small + idempotent so the rendering pass
        runs cleanly per event."""
        # Track source-time progression
        ts = getattr(event, "timestamp", None)
        if ts is not None and self._stream_started_at is None:
            self._stream_started_at = ts
        if ts is not None:
            self._latest_event_at = ts
        # Wall-clock starts on the first event (before the stream
        # had any events to deliver, the user wasn't really watching
        # anything yet).
        if self._wall_clock_started_at is None:
            self._wall_clock_started_at = datetime.now(tz=timezone.utc)

        if isinstance(event, RunStarted):
            self._handle_run_started(event)
        elif isinstance(event, MeetingStarted):
            self._handle_meeting_started(event, base_meeting_ids)
        elif isinstance(event, UtteranceEmitted):
            self._handle_utterance_emitted(event)
        elif isinstance(event, ArtifactShipped):
            self._handle_artifact_shipped(event)
        elif isinstance(event, AgentTelemetryDelta):
            self._handle_agent_telemetry_delta(event)
        elif isinstance(event, MeetingEnded):
            self._handle_meeting_ended(event)
        elif isinstance(event, RunEnded):
            self._handle_run_ended(event)

        # Status bar updates after every event so the elapsed timer
        # stays current.
        self._render_status_bar()

    # ------------------------------------------------------------------ #
    # Event handlers
    # ------------------------------------------------------------------ #

    def _handle_run_started(self, event: "RunStarted") -> None:
        s = event.summary
        directive = (s.directive or "")[:120]
        if len(s.directive or "") > 120:
            directive = directive + "…"
        header = self.query_one("#live-header", Static)
        header.update(
            f"[b]Watching[/b] {s.workflow_name or '—'} · "
            f"[dim]{directive}[/dim]"
        )

    def _handle_meeting_started(
        self,
        event: "MeetingStarted",
        base_meeting_ids: list[str],
    ) -> None:
        thread_id = event.thread_id
        display_label = self._compose_meeting_label(event, base_meeting_ids)
        if thread_id not in self._meetings_seen:
            self._meeting_order.append(thread_id)
        self._meetings_seen[thread_id] = {
            "label": display_label,
            "status": "in-progress",
            "calls": 0,
            "cost": 0.0,
        }
        # Track the most-recently-started thread for artifact attribution.
        self._last_open_thread_id = thread_id
        self._render_meetings_ribbon()

    def _handle_utterance_emitted(self, event: "UtteranceEmitted") -> None:
        u = event.utterance
        speaker = u.speaker.name
        self._current_speaker = speaker

        # Buffer into both the All-Meetings stream and the per-meeting
        # transcript. The per-meeting buffer drives the lazygit-style
        # filtering when the user selects a specific meeting in the
        # left pane.
        self._meeting_transcripts[_ALL_MEETINGS].append((u, event.timestamp))
        thread_buffer = self._meeting_transcripts.setdefault(u.thread_id, [])
        thread_buffer.append((u, event.timestamp))

        # Append-render to the visible transcript only when the
        # currently-selected meeting includes this utterance. Avoids
        # writing ahead of where the user has paged to.
        if self._selected_thread_id in (_ALL_MEETINGS, u.thread_id):
            self._append_transcript_row(u, event.timestamp)

    def _handle_artifact_shipped(self, event: "ArtifactShipped") -> None:
        a = event.artifact
        # Attribute to the most-recently-opened meeting on the bus
        # (tracked via _last_open_thread_id in _handle_meeting_started).
        # Distinct from _selected_thread_id, which is user-driven.
        owning_thread = self._last_open_thread_id or _ALL_MEETINGS
        self._meeting_artifacts[_ALL_MEETINGS].append(a)
        thread_artifacts = self._meeting_artifacts.setdefault(owning_thread, [])
        thread_artifacts.append(a)

        # Refresh the artifacts table when the selected filter
        # includes this artifact. (For All-Meetings selection, every
        # artifact appears.)
        if self._selected_thread_id in (_ALL_MEETINGS, owning_thread):
            self._render_artifacts_table()

    def _handle_agent_telemetry_delta(
        self, event: "AgentTelemetryDelta"
    ) -> None:
        # AgentTelemetryDelta carries the agent's accumulated cost +
        # calls. Overwrites any earlier value for the same agent
        # (live runs will fire deltas multiple times per agent; the
        # latest one is authoritative).
        self._per_agent_cost[event.telemetry.name] = event.telemetry.cost
        self._per_agent_calls[event.telemetry.name] = event.telemetry.calls
        # Once per-agent totals start arriving, they're the source of
        # truth for total cost — overwrite the meeting-accumulated
        # estimate.
        self._total_cost = sum(self._per_agent_cost.values())

    def _handle_meeting_ended(self, event: "MeetingEnded") -> None:
        thread_id = event.thread_id
        if thread_id not in self._meetings_seen:
            # Unknown meeting — synthesize a row from the end event.
            self._meetings_seen[thread_id] = {
                "label": event.meeting.label,
                "status": "complete",
                "calls": 0,
                "cost": 0.0,
            }
            self._meeting_order.append(thread_id)
        m = self._meetings_seen[thread_id]
        # Outcome → status
        outcome_to_status = {
            "COMPLETE": "complete",
            "MEETING_BUDGET": "over-budget",
            "GLOBAL_BUDGET": "over-budget",
            "TIMEOUT": "over-budget",
            "ABORTED": "over-budget",
        }
        m["status"] = outcome_to_status.get(event.outcome, "complete")
        m["calls"] = event.calls_delta
        m["cost"] = event.cost_delta
        # Accumulate into the live cost ticker so it ticks up per
        # meeting rather than waiting for AgentTelemetryDelta at the
        # end. AgentTelemetryDelta later overwrites _total_cost with
        # the authoritative sum.
        self._meeting_cost_total += event.cost_delta
        if not self._per_agent_cost:
            # Only use the rolling meeting-cost total before any
            # AgentTelemetryDelta has fired.
            self._total_cost = self._meeting_cost_total
        self._render_meetings_ribbon()

    def _handle_run_ended(self, event: "RunEnded") -> None:
        # Final status update — the AgentTelemetryDelta events that
        # fired just before this carried final cost numbers. Freeze
        # the watching counter at the moment RunEnded fires.
        self._wall_clock_ended_at = datetime.now(tz=timezone.utc)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _compose_meeting_label(
        self,
        event: "MeetingStarted",
        base_meeting_ids: list[str],
    ) -> str:
        """Build the display label for a meeting cell. Combines the
        meeting label, name, and per_item iteration discriminator
        when applicable."""
        m = event.meeting
        # Find the base meeting id this thread belongs to.
        base_id = None
        for b in base_meeting_ids:
            if event.thread_id == b:
                # Not a per_item iteration — base label only.
                if m.name:
                    return f"{m.label} — {m.name}"
                return m.label
            if event.thread_id.startswith(f"{b}-"):
                base_id = b
                break

        # Per_item iteration. Prefer the explicit iteration_label
        # from the event; fall back to slug-derived discriminator.
        if event.iteration_label:
            disc = event.iteration_label
        elif base_id is not None:
            slug = event.thread_id[len(base_id) + 1:]
            disc = slug.replace("-", " ").title()
        else:
            disc = event.thread_id

        # Optional iteration count badge: "(2/3)"
        if event.iteration_index and event.iteration_total:
            disc = f"({event.iteration_index}/{event.iteration_total}) {disc}"

        if m.name:
            return f"{m.label} — {m.name}: {disc}"
        return f"{m.label}: {disc}"

    # ------------------------------------------------------------------ #
    # T45: dummy-data rendering
    # ------------------------------------------------------------------ #

    def _render_static_dummy(self) -> None:
        """Hand-built data so the layout renders without a live
        stream. Used when the screen is constructed without a
        snapshot_dir — useful for layout testing in isolation.
        """
        self._stream_started_at = datetime.now(tz=timezone.utc)
        self._latest_event_at = self._stream_started_at

        # Pretend we've seen three meetings, the third is in progress.
        for thread_id, label, status, cost in (
            ("scoping", "M1 — The Caucus Race", "complete", 0.0328),
            ("decomposition", "M2 — The Rabbit's Errand", "complete", 0.0442),
            ("composition", "M2.5 — Advice from a Caterpillar", "in-progress", 0.0156),
        ):
            self._meetings_seen[thread_id] = {
                "label": label,
                "status": status,
                "calls": 0,
                "cost": cost,
            }
            self._meeting_order.append(thread_id)
        self._render_meetings_ribbon()

        self._current_speaker = "white_rabbit"
        self._total_cost = 0.0926
        self._render_status_bar()

    def _render_meetings_ribbon(self) -> None:
        table = self.query_one("#live-meetings-table", DataTable)
        # Preserve the user's cursor position across re-renders, so
        # streaming events don't jump them off their selection.
        prev_cursor = table.cursor_row if table.row_count > 0 else 0
        table.clear(columns=True)
        table.add_columns("Meeting", "Status", "Calls", "Cost")
        # Row 0 is always the All-Meetings pseudo-row.
        n_all = len(self._meeting_transcripts.get(_ALL_MEETINGS, []))
        table.add_row(
            "[b]All meetings[/b]",
            "—",
            str(n_all),
            _fmt_cost(self._total_cost),
        )
        for thread_id in self._meeting_order:
            m = self._meetings_seen[thread_id]
            status_icon = {
                "pending": "·",
                "in-progress": "⟳",
                "complete": "✓",
                "over-budget": "⚠",
            }.get(m["status"], "?")
            table.add_row(
                m["label"],
                f"{status_icon} {m['status']}",
                str(m.get("calls", 0)),
                _fmt_cost(m["cost"]),
            )
        # Restore cursor (clamp to valid range)
        max_row = table.row_count - 1
        if max_row >= 0:
            table.cursor_coordinate = (
                min(max(prev_cursor, 0), max_row),
                table.cursor_column,
            )

    def _format_elapsed(self, ts: datetime) -> str:
        if self._stream_started_at is None:
            return "—"
        secs = (ts - self._stream_started_at).total_seconds()
        return f"+{secs:.1f}s"

    def _append_transcript_row(self, u: Utterance, ts: datetime) -> None:
        """Append an utterance to the transcript table for the
        currently-selected filter. The body cell is a one-line
        preview; the full body shows in the body-preview pane below
        when the row is selected."""
        table = self.query_one("#transcript-table", DataTable)
        body_preview = (u.content.body or "").strip().split("\n", 1)[0] or "(no body)"
        if len(body_preview) > 80:
            body_preview = body_preview[:80] + "…"
        table.add_row(
            self._format_elapsed(ts),
            u.speaker.name,
            u.speech_act.value,
            body_preview,
        )

    def _update_body_preview(self, row_index: int) -> None:
        """Refresh the body preview pane based on the transcript
        cursor row. Looks up the utterance from the per-meeting
        buffer for the currently-selected filter."""
        body = self.query_one("#transcript-body", Static)
        utterances = self._meeting_transcripts.get(self._selected_thread_id, [])
        if row_index < 0 or row_index >= len(utterances):
            body.update("[dim](no utterance selected)[/dim]")
            return
        u, ts = utterances[row_index]
        addressed = u.addressed_to if isinstance(u.addressed_to, str) else (
            ",".join(a.name for a in u.addressed_to) or "—"
        )
        header_lines = [
            f"[b cyan]{u.speaker.name}[/b cyan]  "
            f"[yellow]{u.speech_act.value}[/yellow]  "
            f"[dim]→ {addressed}[/dim]  "
            f"[dim]{self._format_elapsed(ts)}[/dim]",
        ]
        if u.content.artifacts:
            kinds = ", ".join(
                f"{a.kind}: {a.payload.get('title', '?')}"
                for a in u.content.artifacts
            )
            header_lines.append(f"[b]Artifacts:[/b] {kinds}")
        body_text = u.content.body or "(no body)"
        body.update("\n".join(header_lines) + "\n\n" + body_text)

    def _render_artifacts_table(self) -> None:
        """Re-render the artifacts table for the currently-selected
        meeting. Called on selection change + on each new
        ArtifactShipped that matches the filter."""
        table = self.query_one("#live-artifacts-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Kind", "Title")
        artifacts = self._meeting_artifacts.get(self._selected_thread_id, [])
        for a in artifacts:
            title = (a.title or a.path.name)[:80]
            table.add_row(a.kind, title)

    def _refresh_panes_for_selection(self) -> None:
        """Re-render the transcript table and artifacts table for
        whatever meeting is currently selected. Called when the
        meetings-table cursor moves to a new row."""
        table = self.query_one("#transcript-table", DataTable)
        table.clear(columns=False)
        utterances = self._meeting_transcripts.get(self._selected_thread_id, [])
        for u, ts in utterances:
            self._append_transcript_row(u, ts)
        self._render_artifacts_table()
        # Reset body preview to row 0 (or empty if no rows).
        self._update_body_preview(0 if utterances else -1)

    def _render_status_bar(self) -> None:
        bar = self.query_one("#live-status", Static)
        speaker_part = (
            f"[b]Speaking:[/b] [cyan]{self._current_speaker}[/cyan]"
            if self._current_speaker
            else "[dim]Speaking: idle[/dim]"
        )
        cost_part = f"[b]Cost:[/b] {_fmt_cost(self._total_cost)}"

        # Wall-clock elapsed (how long the user has been watching) —
        # ticks via the 500ms refresh interval until RunEnded freezes
        # _wall_clock_ended_at. Falls back to dashes before the first
        # event arrives.
        if self._wall_clock_started_at is not None:
            end_ts = self._wall_clock_ended_at or datetime.now(tz=timezone.utc)
            wall_elapsed = (end_ts - self._wall_clock_started_at).total_seconds()
            elapsed_part = f"[b]Watching:[/b] {_fmt_elapsed(wall_elapsed)}"
            if self._wall_clock_ended_at is not None:
                # Frozen — make it visible.
                elapsed_part = (
                    f"[b]Watched:[/b] {_fmt_elapsed(wall_elapsed)} [dim](done)[/dim]"
                )
        else:
            elapsed_part = "[dim]Watching: —[/dim]"

        # Source-time elapsed (where in the run we are) — useful as
        # a secondary indicator since playback is compressed.
        if self._stream_started_at and self._latest_event_at:
            source_elapsed = (
                self._latest_event_at - self._stream_started_at
            ).total_seconds()
            source_part = f"[dim]Run time: {_fmt_elapsed(source_elapsed)}[/dim]"
        else:
            source_part = ""

        parts = [speaker_part, cost_part, elapsed_part]
        if source_part:
            parts.append(source_part)
        bar.update("    ".join(parts))

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_open_meeting(self) -> None:
        """Enter on a row routes through here. With the lazygit-
        style multi-pane layout (T48), Enter on the meetings table
        is a no-op (selection already filters the panes); Enter on
        the artifacts table opens the artifact's markdown."""
        focused = self.focused
        if isinstance(focused, DataTable) and focused.id == "live-artifacts-table":
            row = focused.cursor_row
            artifacts = self._meeting_artifacts.get(self._selected_thread_id, [])
            if row is None or row < 0 or row >= len(artifacts):
                return
            self.app.push_screen(ArtifactDetailScreen(artifacts[row]))

    def on_data_table_row_selected(
        self, _event: DataTable.RowSelected
    ) -> None:
        self.action_open_meeting()

    def on_data_table_row_highlighted(
        self, event: DataTable.RowHighlighted
    ) -> None:
        """Lazygit-style filtering via cursor moves. Three tables can
        fire this event:

          - meetings table → re-filter transcript + artifacts to the
            newly-selected meeting (or All-Meetings)
          - transcript table → update the body preview to the
            newly-selected utterance
          - artifacts table → no-op (selecting an artifact doesn't
            change anything; Enter opens the detail screen)
        """
        if event.data_table.id == "live-meetings-table":
            row = event.cursor_row
            if row is None or row < 0:
                return
            # Row 0 is the All-Meetings pseudo-row.
            if row == 0:
                new_selection = _ALL_MEETINGS
            else:
                order_idx = row - 1
                if order_idx >= len(self._meeting_order):
                    return
                new_selection = self._meeting_order[order_idx]
            if new_selection == self._selected_thread_id:
                return
            self._selected_thread_id = new_selection
            self._refresh_panes_for_selection()
        elif event.data_table.id == "transcript-table":
            row = event.cursor_row
            if row is None:
                return
            self._update_body_preview(row)


__all__ = ["LiveRunScreen"]
