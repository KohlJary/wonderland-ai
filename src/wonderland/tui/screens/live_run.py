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
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Static,
    TabbedContent,
    TabPane,
    Tree,
)

from wonderland.observer import (
    AgentActed,
    AgentPassed,
    AgentTelemetryDelta,
    ArtifactShipped,
    MeetingEnded,
    MeetingStarted,
    MockTurtleHandle,
    PhaseEnded,
    PhaseStarted,
    PriorityWindowOpened,
    RotationCompleted,
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
        Binding("T", "cycle_auto_sentinel", "Auto-sentinel", show=True),
        Binding("p", "toggle_pause", "Pause/Resume", show=True),
        Binding("ctrl+c", "abort_run", "Abort run", show=True),
        # Vim nav (j/k/g/G/H/L) is provided by WonderlandApp.
    ]

    # Cycle of auto-sentinel timeouts, in seconds. ``None`` = wait
    # forever for the operator (the default). ``0`` = skip the modal
    # entirely and feed the agent the sentinel reply immediately.
    # Values in between = show the modal but auto-dismiss with
    # sentinel after that many seconds. Cycle order is "tighten as
    # you press T" — most operators want longer wait → shorter wait
    # → instant, in that direction.
    _AUTO_SENTINEL_CYCLE: tuple[float | None, ...] = (
        None,    # off — wait indefinitely (current default)
        900.0,   # 15 minutes
        300.0,   # 5 minutes
        60.0,    # 1 minute
        0.0,     # instant — skip modal, sentinel immediately
    )

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
        # Auto-sentinel state (T69 follow-up): operator can toggle
        # mid-run with the `T` keybind to cycle through wait
        # durations. ``None`` = wait indefinitely (default);
        # ``0`` = skip modal, sentinel immediately; otherwise
        # auto-dismiss after that many seconds. Status bar
        # surfaces the current setting so operators don't forget
        # they left it on.
        self._auto_sentinel_seconds: float | None = None
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
        # Three-column lazygit-shape layout. Each column has a
        # top + bottom split.
        #
        #   LEFT:    Meetings (top)        |   Live call feed (bottom)
        #   MIDDLE:  Transcript (top)      |   Body / Detail (bottom)
        #   RIGHT:   Tabs: Artifacts /     |   Detail (per active tab)
        #            Files / Phases (top)  |
        #
        # Selection cascades left-to-right: pick a meeting → transcript
        # filters; pick an utterance → body shows; pick an artifact /
        # file → detail shows. Live call feed is filtered to the
        # selected meeting so it doubles as an aliveness signal during
        # quiet rotations.
        yield Header(show_clock=False)
        with Vertical():
            yield Static("[b]Run watch[/b]", id="live-header")
            with Horizontal(id="live-main-row"):
                # ─── LEFT COLUMN ───────────────────────────────────
                with Vertical(id="left-pane"):
                    yield Static("[b]Meetings[/b]", id="meetings-label")
                    yield DataTable(
                        id="live-meetings-table",
                        cursor_type="row",
                    )
                    yield Static(
                        "[b]Live call feed[/b]  "
                        "[dim](filtered to selected meeting)[/dim]",
                        id="call-feed-label",
                    )
                    yield DataTable(
                        id="live-call-feed-table",
                        cursor_type="row",
                        show_header=False,
                    )
                # ─── MIDDLE COLUMN ─────────────────────────────────
                with Vertical(id="middle-pane"):
                    yield Static("[b]Transcript[/b]", id="transcript-label")
                    yield DataTable(
                        id="transcript-table",
                        cursor_type="row",
                    )
                    yield Static("[b]Body[/b]", id="transcript-body-label")
                    with VerticalScroll(id="transcript-body-scroll"):
                        yield Static(id="transcript-body")
                # ─── RIGHT COLUMN ──────────────────────────────────
                with Vertical(id="right-pane"):
                    with TabbedContent(
                        initial="tab-artifacts",
                        id="right-tabs",
                    ):
                        with TabPane("Artifacts", id="tab-artifacts"):
                            yield DataTable(
                                id="live-artifacts-table",
                                cursor_type="row",
                            )
                        with TabPane("Files", id="tab-files"):
                            yield Tree(
                                "(no files touched yet)",
                                id="live-files-tree",
                            )
                        with TabPane("Phases", id="tab-phases"):
                            yield DataTable(
                                id="live-phase-events-table",
                                cursor_type="row",
                            )
                    yield Static(
                        "[b]Detail[/b]",
                        id="right-detail-label",
                    )
                    with VerticalScroll(id="right-detail-scroll"):
                        yield Static(
                            "[dim](nothing selected)[/dim]",
                            id="right-detail",
                        )
            with Horizontal(id="live-controls-row"):
                yield Button(
                    "⏸ Pause",
                    id="live-pause-button",
                )
                yield Button(
                    "⏹ Abort",
                    id="live-abort-button",
                    variant="error",
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
        # Initialize phase-events table — surfaces the orchestrator's
        # priority-gate mechanics in real time (P9 / T58c on the
        # observer side; T64-65 now flow through it).
        ptable = self.query_one("#live-phase-events-table", DataTable)
        ptable.clear(columns=True)
        ptable.add_columns("Time", "Phase", "Event", "Agent", "Detail")
        # Initialize live call feed — single-column ticker showing each
        # LLM call as it lands. Filtered to the selected meeting so it
        # doubles as an aliveness signal during quiet rotations (the
        # operator-pain class "is anything happening?" goes away when
        # there's a visible per-call tick).
        cftable = self.query_one("#live-call-feed-table", DataTable)
        cftable.clear(columns=True)
        cftable.add_columns("⚡ When · Agent · Cost")
        # Initialize files tree — populated on demand from
        # tool-calls.jsonl as write/edit/delete tools fire. Empty
        # state until the first tool call lands.
        ftree = self.query_one("#live-files-tree", Tree)
        ftree.clear()
        ftree.show_root = False
        # Initial body preview + status bar — dashes until events flow.
        self.query_one("#transcript-body", Static).update(
            "[dim](no utterance selected)[/dim]"
        )
        self._render_status_bar()
        # Track call-feed cursor + files-touched so periodic refresh
        # only adds new entries / nodes instead of redrawing.
        self._call_feed_cursor: int = 0
        self._files_touched: dict[str, str] = {}  # path → indicator
        # Cache rendered file detail (Syntax objects + markup) so
        # repeated highlight events don't re-shell-out to git for
        # the same file. Invalidated when _files_touched changes
        # (since indicator could differ on a fresh tool-call wave).
        self._file_render_cache: dict[tuple[str, str], object] = {}

        if self.handle is None and self.snapshot_dir is None:
            # No source bound — fall back to the T45 dummy data so
            # the screen has something to show. Useful for testing
            # the layout in isolation.
            self._render_static_dummy()
        else:
            # Wire the user-question handler on the LiveRunHandle
            # so agent QUESTION-to-operator utterances surface as
            # the AskUserModal (T69). Mock-turtle replay paths
            # don't have a runner to call back, so the
            # set_user_question_handler attribute check guards
            # the cast.
            if self.handle is not None and hasattr(
                self.handle, "set_user_question_handler"
            ):
                self.handle.set_user_question_handler(
                    self._handle_user_question
                )
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
        # Refresh the live call feed + files tab from disk-backed
        # sources at a slightly slower cadence than the status bar.
        # 1s gives the operator visible ticks without thrashing the
        # filesystem on tool-calls.jsonl reads.
        self.set_interval(1.0, self._refresh_call_feed)
        self.set_interval(1.5, self._refresh_files_tab)

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
        elif isinstance(
            event,
            (
                PhaseStarted,
                PhaseEnded,
                PriorityWindowOpened,
                AgentActed,
                AgentPassed,
                RotationCompleted,
            ),
        ):
            self._handle_phase_event(event)

        # Mark the chase strip alive on signal-of-life events. The
        # chase moves on a wall-clock timer (so motion continues
        # ChaseStrip removed in the live-watch rework — the live
        # call feed (#live-call-feed-table) now serves as the
        # aliveness signal, ticking per LLM call. The Static row
        # of agents-running indicators is replaced by real activity.

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

    def action_cycle_auto_sentinel(self) -> None:
        """Cycle through the auto-sentinel timeouts. Press T
        repeatedly to tighten: off → 15m → 5m → 1m → instant → off.

        Off (the default) makes the modal wait indefinitely for
        operator input. Instant skips the modal entirely and feeds
        the agent the sentinel reply immediately — useful for
        unattended test runs. The intermediate values auto-dismiss
        the modal with sentinel after the named timeout if the
        operator hasn't answered."""
        cycle = self._AUTO_SENTINEL_CYCLE
        try:
            current_idx = cycle.index(self._auto_sentinel_seconds)
        except ValueError:
            current_idx = 0
        next_idx = (current_idx + 1) % len(cycle)
        self._auto_sentinel_seconds = cycle[next_idx]
        self._render_status_bar()

    def _auto_sentinel_label(self) -> str:
        """Human-readable label for the current auto-sentinel
        setting, used in the status bar so operators see at a
        glance whether they've left the toggle on."""
        v = self._auto_sentinel_seconds
        if v is None:
            return "off"
        if v == 0:
            return "instant"
        if v >= 60:
            return f"{int(v / 60)}m"
        return f"{int(v)}s"

    async def _handle_user_question(self, question_utterance) -> str | None:
        """Surface a QUESTION-to-operator utterance via AskUserModal
        and await the operator's reply (T69).

        Called by the runner's user-question watcher (via the
        LiveRunHandle wiring) when an agent emits a QUESTION
        addressed to the operator identity. Returns the reply text,
        or None on skip — the watcher publishes a sentinel
        OBSERVATION on None so the team can proceed.

        Behavior depends on the auto-sentinel toggle (cycled via
        the ``T`` keybind):
          - None (default): push modal, await indefinitely.
          - 0: skip modal entirely, return None immediately so the
            watcher publishes the sentinel reply.
          - >0: push modal with auto_dismiss_after; if operator
            doesn't answer in time, modal self-dismisses with None.
        """
        import asyncio

        from wonderland.tui.screens.ask_user_modal import AskUserModal

        timeout = self._auto_sentinel_seconds

        # Instant-sentinel path: don't even show the modal.
        if timeout == 0:
            return None

        # Future bridges the modal's async dismiss callback back
        # into the awaiting coroutine.
        future: asyncio.Future[str | None] = asyncio.Future()

        def _on_dismissed(answer: str | None) -> None:
            if not future.done():
                future.set_result(answer)

        # Suggested options ride on the utterance as an artifact
        # (kind="operator_question_options", payload={"options": [...]}).
        # Empty / missing → free-text-only experience as before.
        options: list[str] = []
        for artifact in question_utterance.content.artifacts:
            if artifact.kind == "operator_question_options":
                raw = artifact.payload.get("options", [])
                if isinstance(raw, list):
                    options = [str(o) for o in raw if o]
                break

        self.app.push_screen(
            AskUserModal(
                asking_agent=question_utterance.speaker.name,
                question=question_utterance.content.body,
                options=options,
                auto_dismiss_after=timeout,
            ),
            _on_dismissed,
        )
        return await future

    def _handle_run_ended(self, event: "RunEnded") -> None:
        # Final status update — the AgentTelemetryDelta events that
        # fired just before this carried final cost numbers. Freeze
        # the watching counter at the moment RunEnded fires.
        self._wall_clock_ended_at = datetime.now(tz=timezone.utc)

    def _handle_phase_event(self, event: object) -> None:
        """Append a row to the live phase-events table (T58c surface
        / T64 team windows). Each row carries time, phase, event
        type, agent (if applicable), and a short detail string. The
        table fills in real time so the operator can watch the
        priority-gate mechanics: which agent's window opened,
        whether they acted or passed, when rotations completed,
        and how each phase ended (succession / exhausted /
        exit_condition / aborted)."""
        ptable = self.query_one("#live-phase-events-table", DataTable)
        elapsed = self._format_elapsed(event.timestamp)  # type: ignore[attr-defined]

        # The thread_id field on phase events identifies the
        # meeting; surface it as part of the Phase column for
        # disambiguation across per_item iterations.
        if isinstance(event, PhaseStarted):
            phase = f"{event.meeting_thread_id}.{event.phase_name}"
            kind = "▶ start"
            agent = ""
            detail = (
                f"cast={','.join(event.cast)} "
                f"max_rot={event.max_rotations}"
            )
        elif isinstance(event, PriorityWindowOpened):
            phase = f"{event.meeting_thread_id}.{event.phase_name}"
            kind = f"⊙ window R{event.rotation_index}"
            agent = event.agent_id
            detail = f"W{event.window_index_in_phase}"
        elif isinstance(event, AgentActed):
            phase = f"{event.meeting_thread_id}.{event.phase_name}"
            kind = "✓ acted"
            agent = event.agent_id
            detail = f"u={event.utterance_id[:8]}…"
        elif isinstance(event, AgentPassed):
            phase = f"{event.meeting_thread_id}.{event.phase_name}"
            kind = "× passed"
            agent = event.agent_id
            detail = (event.reason or "")[:40]
        elif isinstance(event, RotationCompleted):
            phase = f"{event.meeting_thread_id}.{event.phase_name}"
            kind = "─ rotation"
            agent = ""
            detail = f"R{event.rotation_index} done"
        elif isinstance(event, PhaseEnded):
            phase = f"{event.meeting_thread_id}.{event.phase_name}"
            kind = f"■ end ({event.reason})"
            agent = ""
            detail = (
                f"rot={event.rotations_used} "
                f"win={event.total_windows} "
                f"acts={dict(event.acts_per_agent)} "
                f"pass={dict(event.passes_per_agent)}"
            )
        else:
            return

        ptable.add_row(elapsed, phase, kind, agent, detail)
        # Auto-scroll to the latest row so the live stream stays
        # visible without manual paging.
        ptable.action_scroll_end()

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
        # Keep the pause button label in sync with the runner's
        # current state. Cheap to call on the periodic refresh —
        # query_one + a string check.
        self._refresh_pause_button_label()

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

        # Auto-sentinel toggle indicator (T69 follow-up). Hidden
        # when off (the default) so the bar stays clean for
        # standard runs; visible whenever the operator has cycled
        # it on, so they don't forget questions are being
        # answered automatically.
        sentinel_part: str | None = None
        if self._auto_sentinel_seconds is not None:
            label = self._auto_sentinel_label()
            color = "yellow" if self._auto_sentinel_seconds == 0 else "dim"
            sentinel_part = (
                f"[b][{color}]auto-sentinel: {label}[/{color}][/b]"
            )

        parts = [speaker_part, cost_part, elapsed_part]
        if source_part:
            parts.append(source_part)
        if sentinel_part:
            parts.append(sentinel_part)
        bar.update("    ".join(parts))

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_toggle_pause(self) -> None:
        """Pause if running; resume if paused. Operator can toggle
        with the ``p`` keybind or by clicking the Pause button.
        Pause is best-effort: in-flight LLM calls finish before
        the gate blocks (clean rotation boundary, nothing partial
        gets stranded). MockTurtle / replay handles silently
        accept the call but don't actually pause — only LiveRunHandle
        wraps a Runner with a real pause primitive."""
        runner = getattr(self.handle, "_runner", None) if self.handle else None
        if runner is None or not hasattr(runner, "pause"):
            self.notify(
                "Pause not supported on this run handle "
                "(replay or fixture data).",
                severity="warning",
                timeout=3,
            )
            return
        if runner.is_paused:
            runner.resume()
            self.notify("▶ Run resumed.", timeout=2)
        else:
            runner.pause()
            self.notify(
                "⏸ Run paused. In-flight calls will finish; new "
                "rotations won't open until you resume.",
                timeout=4,
            )
        self._refresh_pause_button_label()

    def action_abort_run(self) -> None:
        """Operator-driven abort. Confirms via modal because abort
        is destructive (the run is over; resuming requires a fresh
        launch). Telemetry is preserved by the safety-net flush in
        observer/live's finally block."""
        runner = getattr(self.handle, "_runner", None) if self.handle else None
        if runner is None or not hasattr(runner, "abort"):
            self.notify(
                "Abort not supported on this run handle "
                "(replay or fixture data).",
                severity="warning",
                timeout=3,
            )
            return
        from wonderland.tui.screens.abort_confirm_modal import (
            AbortConfirmModal,
        )

        def _on_dismiss(confirmed: bool | None) -> None:
            if confirmed:
                runner.abort(reason="operator pressed Abort")
                self.notify(
                    "⏹ Abort signaled. Telemetry will flush "
                    "automatically.",
                    severity="warning",
                    timeout=4,
                )

        self.app.push_screen(AbortConfirmModal(), _on_dismiss)

    # ------------------------------------------------------------------ #
    # Live call feed + Files tab refresh
    # ------------------------------------------------------------------ #

    def _refresh_call_feed(self) -> None:
        """Append any new LLM telemetry entries to the call feed.

        Reads ``runner.telemetry.entries`` directly. Each entry is a
        single LLM call; we add a row per entry past the cursor. The
        feed is filtered to the currently-selected meeting (or shows
        all entries when ``All meetings`` is selected) so the operator
        gets a real-time aliveness signal scoped to whatever they're
        watching.
        """
        runner = (
            getattr(self.handle, "_runner", None)
            if self.handle is not None
            else None
        )
        if runner is None or not hasattr(runner, "telemetry"):
            return
        entries = list(runner.telemetry.entries)
        # No new entries since last tick — skip.
        if len(entries) <= self._call_feed_cursor:
            return
        try:
            table = self.query_one(
                "#live-call-feed-table", DataTable
            )
        except Exception:  # noqa: BLE001
            return
        # Determine the active filter (selected meeting's thread_id)
        # so we only show calls relevant to the current focus.
        active_thread = self._selected_thread_id
        for entry in entries[self._call_feed_cursor :]:
            self._call_feed_cursor += 1
            if active_thread and entry.thread_id != active_thread:
                continue
            ts = entry.timestamp.strftime("%H:%M:%S") if entry.timestamp else "—"
            cost_str = _fmt_cost(entry.cost)
            table.add_row(
                f"{ts}  [b]{entry.agent}[/b]  [dim]{cost_str}[/dim]"
            )
        # Cap the visible rows so the table doesn't grow unbounded
        # over a long run. 40 is enough for a couple of rotations'
        # worth of context; older calls scroll off.
        while table.row_count > 40:
            table.remove_row(table.coordinate_to_cell_key((0, 0)).row_key)
        if table.row_count > 0:
            table.action_scroll_end()

    def _refresh_files_tab(self) -> None:
        """Build the Files tree from .wonderland/tool-calls.jsonl.

        Each tool call writing/editing/deleting a file gets surfaced
        with a git-gutter style indicator on the file's tree node:
          - ``+`` new file (write_file path that didn't exist before
            the run, approximated by first-touch in the run window)
          - ``~`` modified (str_replace, insert, write_file overwrite)
          - ``-`` deleted (delete_file)

        Reads the project root from the runner. Best-effort — missing
        tool-calls.jsonl just leaves the tree empty.
        """
        runner = (
            getattr(self.handle, "_runner", None)
            if self.handle is not None
            else None
        )
        project_root = (
            getattr(runner, "project_root", None)
            if runner is not None
            else None
        )
        if project_root is None:
            return
        tool_log = project_root / ".wonderland" / "tool-calls.jsonl"
        if not tool_log.is_file():
            return
        # Parse the log fresh each refresh — cheap (<1k lines on
        # typical runs) and avoids state drift if files get touched
        # twice with different intent. Keys: path → indicator.
        import json
        touched: dict[str, str] = {}
        try:
            for line in tool_log.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                tool_name = rec.get("tool_name", "")
                args = rec.get("args_summary") or {}
                path = args.get("path") if isinstance(args, dict) else None
                if not path:
                    continue
                if tool_name == "delete_file":
                    touched[path] = "-"
                elif tool_name in ("write_file",):
                    # First-touch wins as "+" if not already touched;
                    # subsequent write_file → "~" (modification).
                    touched[path] = (
                        "+" if path not in touched else "~"
                    )
                elif tool_name in ("str_replace", "insert"):
                    if touched.get(path) != "+":
                        touched[path] = "~"
        except OSError:
            return
        # Only redraw when the touched-set actually changed.
        if touched == self._files_touched:
            return
        self._files_touched = touched
        # Touched-set changed — file content may have changed for any
        # of the tracked paths. Invalidate the rendered-detail cache
        # so the next highlight re-pulls fresh content + diff.
        self._file_render_cache.clear()
        try:
            tree = self.query_one("#live-files-tree", Tree)
        except Exception:  # noqa: BLE001
            return
        tree.clear()
        if not touched:
            tree.label = "(no files touched yet)"
            return
        tree.label = f"{len(touched)} file(s) touched"
        # Build a hierarchical tree from the touched paths. Each path
        # like "src/backend/db.py" becomes nodes
        #   src/ → backend/ → db.py
        # so the operator can see structural context for the changes.
        # Directories without modifications don't appear; only paths
        # that contain at least one touched file get expanded.
        dir_nodes: dict[str, "Any"] = {}  # noqa: F821 — Tree node type

        def _ensure_dir(rel_dir: str):
            """Walk parent components, creating tree nodes on demand.
            Returns the leaf directory node (or tree.root for empty)."""
            if rel_dir in ("", "."):
                return tree.root
            if rel_dir in dir_nodes:
                return dir_nodes[rel_dir]
            parent_dir = "/".join(rel_dir.split("/")[:-1])
            parent_node = _ensure_dir(parent_dir)
            name = rel_dir.split("/")[-1]
            node = parent_node.add(
                f"[dim]📁[/dim] {name}",
                data={"path": rel_dir, "is_dir": True},
                expand=True,
            )
            dir_nodes[rel_dir] = node
            return node

        for path in sorted(touched.keys()):
            indicator = touched[path]
            parts = path.split("/")
            parent = "/".join(parts[:-1])
            filename = parts[-1]
            parent_node = _ensure_dir(parent)
            color = (
                "[green]+[/green]"
                if indicator == "+"
                else "[red]-[/red]"
                if indicator == "-"
                else "[yellow]~[/yellow]"
            )
            file_node = parent_node.add(
                f"{color} {filename}",
                data={"path": path, "indicator": indicator},
            )
            file_node.allow_expand = False

    def on_tree_node_highlighted(self, event) -> None:
        """Render the highlighted file in the right-detail pane.

        Three modes based on the indicator:
          - ``+`` (new file): render full content with syntax
            highlighting based on the file's extension
          - ``~`` (modified): render ``git diff HEAD -- path`` with
            the diff lexer so +/- lines colorize naturally
          - ``-`` (deleted): try ``git show HEAD:path`` so the
            operator can see what was lost; falls back to a marker
            if git can't recover

        Directory nodes show an aggregate count instead.
        Best-effort — errors render an inline message rather than
        crashing the screen.
        """
        if event.node.tree.id != "live-files-tree":
            return
        data = event.node.data
        if data is None:
            return
        try:
            detail = self.query_one("#right-detail", Static)
        except Exception:  # noqa: BLE001
            return

        # Directory node — show a summary instead of opening a file.
        if data.get("is_dir"):
            dir_path = data["path"]
            n_under = sum(
                1
                for p in self._files_touched
                if p == dir_path or p.startswith(dir_path + "/")
            )
            detail.update(
                f"[b]📁 {dir_path}/[/b]  "
                f"[dim]({n_under} touched files inside)[/dim]\n\n"
                "[dim]Highlight a file to see its diff or contents.[/dim]"
            )
            return

        runner = (
            getattr(self.handle, "_runner", None)
            if self.handle is not None
            else None
        )
        project_root = (
            getattr(runner, "project_root", None)
            if runner is not None
            else None
        )
        if project_root is None:
            return

        path = data["path"]
        indicator = data["indicator"]
        rendered = self._render_file_for_detail(
            project_root, path, indicator
        )
        detail.update(rendered)

    # ------------------------------------------------------------------ #
    # Diff-aware file rendering
    # ------------------------------------------------------------------ #

    def _render_file_for_detail(
        self, project_root: "Path", path: str, indicator: str
    ):
        """Build a Rich-renderable for the right-detail pane based on
        the file's indicator. Returns either a string (markup) or a
        ``rich.syntax.Syntax`` instance — Static.update() accepts
        both. Caches per (path, indicator) tuple so repeated cursor
        moves don't re-shell-out to git on every highlight event."""
        cache_key = (path, indicator)
        if cache_key in self._file_render_cache:
            return self._file_render_cache[cache_key]

        from rich.syntax import Syntax

        full_path = project_root / path
        rendered: object

        if indicator == "-":
            # Deleted — recover content from git HEAD if possible.
            head_content = self._git_show_head(project_root, path)
            if head_content is None:
                rendered = (
                    f"[b][red]-[/red] {path}[/b]\n\n"
                    f"[dim]File was deleted; git couldn't recover "
                    f"prior content (untracked or new repo).[/dim]"
                )
            else:
                lexer = Syntax.guess_lexer(path, code=head_content)
                rendered = Syntax(
                    head_content,
                    lexer,
                    theme="monokai",
                    line_numbers=True,
                    word_wrap=False,
                )
                # We can't combine markup header + Syntax cleanly in
                # one update; the header lives via the file-tree
                # label so this is just the content. Operator sees
                # the deletion icon in the tree and the prior
                # content here.

        elif indicator == "+":
            # New file — full content with syntax highlighting.
            if not full_path.is_file():
                rendered = (
                    f"[b][green]+[/green] {path}[/b]\n\n"
                    f"[red]File listed as new but not on disk.[/red]"
                )
            else:
                try:
                    content = full_path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError) as exc:
                    rendered = f"[red]Read error: {exc}[/red]"
                else:
                    lexer = Syntax.guess_lexer(path, code=content)
                    rendered = Syntax(
                        content,
                        lexer,
                        theme="monokai",
                        line_numbers=True,
                        word_wrap=False,
                    )

        else:  # "~" modified
            # Modified — show git diff against HEAD with the diff
            # lexer so +/- lines pick up red/green automatically.
            diff = self._git_diff_against_head(project_root, path)
            if diff is None:
                # Fall back to plain content if git diff isn't
                # available (e.g. project not under git, or path
                # untracked at HEAD which means it's effectively new).
                if not full_path.is_file():
                    rendered = (
                        f"[red]Read error: file missing[/red]"
                    )
                else:
                    try:
                        content = full_path.read_text(encoding="utf-8")
                    except (OSError, UnicodeDecodeError) as exc:
                        rendered = f"[red]Read error: {exc}[/red]"
                    else:
                        lexer = Syntax.guess_lexer(
                            path, code=content
                        )
                        rendered = Syntax(
                            content,
                            lexer,
                            theme="monokai",
                            line_numbers=True,
                            word_wrap=False,
                        )
            elif not diff.strip():
                # git diff is empty — file got touched (matched the
                # str_replace / insert / write pattern) but ended up
                # identical to HEAD. Render content as-is.
                try:
                    content = full_path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    content = ""
                lexer = Syntax.guess_lexer(path, code=content)
                rendered = Syntax(
                    content,
                    lexer,
                    theme="monokai",
                    line_numbers=True,
                    word_wrap=False,
                )
            else:
                rendered = Syntax(
                    diff,
                    "diff",
                    theme="monokai",
                    line_numbers=False,
                    word_wrap=False,
                )

        self._file_render_cache[cache_key] = rendered
        return rendered

    def _git_diff_against_head(
        self, project_root: "Path", path: str
    ) -> str | None:
        """Return the unified diff of ``path`` vs HEAD, or None if
        git can't produce one (not a repo, path untracked, etc).
        Subprocess call; cached at the caller level via
        _file_render_cache so repeated highlights don't re-run git."""
        import subprocess

        try:
            result = subprocess.run(
                [
                    "git",
                    "-C",
                    str(project_root),
                    "diff",
                    "--no-color",
                    "HEAD",
                    "--",
                    path,
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if result.returncode != 0:
            return None
        return result.stdout

    def _git_show_head(
        self, project_root: "Path", path: str
    ) -> str | None:
        """Return the content of ``path`` at HEAD (for deleted
        files). None if git can't recover it."""
        import subprocess

        try:
            result = subprocess.run(
                [
                    "git",
                    "-C",
                    str(project_root),
                    "show",
                    f"HEAD:{path}",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if result.returncode != 0:
            return None
        return result.stdout

    def _refresh_pause_button_label(self) -> None:
        """Toggle the Pause/Resume button label based on the runner's
        current pause state. Called after pause()/resume() and
        opportunistically from the periodic status-bar refresh so
        the label stays accurate even on programmatic pause changes."""
        try:
            btn = self.query_one("#live-pause-button", Button)
        except Exception:  # noqa: BLE001
            return
        runner = getattr(self.handle, "_runner", None) if self.handle else None
        if runner is None or not hasattr(runner, "is_paused"):
            btn.label = "⏸ Pause"
            btn.disabled = True
            return
        btn.disabled = False
        btn.label = "▶ Resume" if runner.is_paused else "⏸ Pause"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "live-pause-button":
            self.action_toggle_pause()
        elif bid == "live-abort-button":
            self.action_abort_run()

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
        """Lazygit-style filtering via cursor moves. Tables that
        fire this event:

          - meetings table → re-filter transcript + artifacts to the
            newly-selected meeting (or All-Meetings); also clear
            the call feed so the operator's view of activity matches
            the current selection
          - transcript table → update the body preview
          - artifacts table → render the highlighted artifact in
            the right-detail pane
          - phase-events table → render the phase event detail
        """
        tid = event.data_table.id
        if tid == "live-meetings-table":
            row = event.cursor_row
            if row is None or row < 0:
                return
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
            # Clear the call feed since it's filtered to the active
            # meeting — old entries from the previous filter aren't
            # relevant to the new selection.
            try:
                self.query_one(
                    "#live-call-feed-table", DataTable
                ).clear(columns=False)
            except Exception:  # noqa: BLE001
                pass
            self._call_feed_cursor = 0
            self._refresh_call_feed()
        elif tid == "transcript-table":
            row = event.cursor_row
            if row is None:
                return
            self._update_body_preview(row)
        elif tid == "live-artifacts-table":
            row = event.cursor_row
            artifacts = self._meeting_artifacts.get(
                self._selected_thread_id, []
            )
            if row is None or not (0 <= row < len(artifacts)):
                return
            self._render_artifact_detail(artifacts[row])
        elif tid == "live-phase-events-table":
            row = event.cursor_row
            if row is None:
                return
            self._render_phase_event_detail(row)

    def _render_artifact_detail(self, artifact) -> None:
        """Render the highlighted artifact's metadata + body in the
        right-detail pane. Falls back to ``str(artifact)`` if the
        ArtifactBrowser-shape attributes aren't present."""
        try:
            detail = self.query_one("#right-detail", Static)
        except Exception:  # noqa: BLE001
            return
        title = getattr(artifact, "title", "") or "(untitled)"
        kind = getattr(artifact, "kind", "?")
        body = getattr(artifact, "body", "") or ""
        path = getattr(artifact, "path", "")
        max_chars = 4000
        if len(body) > max_chars:
            body = body[:max_chars] + f"\n\n[dim]... ({len(body) - max_chars} more chars; press Enter to open full)[/dim]"
        path_line = (
            f"\n[dim]Path: {path}[/dim]\n" if path else "\n"
        )
        detail.update(
            f"[b]{kind}[/b]: {title}{path_line}\n{body}"
        )

    def _render_phase_event_detail(self, row_idx: int) -> None:
        """Phase events don't carry a rich body; surface the row
        contents in the detail pane as a structured block."""
        try:
            ptable = self.query_one(
                "#live-phase-events-table", DataTable
            )
            detail = self.query_one("#right-detail", Static)
        except Exception:  # noqa: BLE001
            return
        if row_idx is None or row_idx < 0 or row_idx >= ptable.row_count:
            return
        n_cols = len(ptable.columns) if hasattr(ptable, "columns") else 0
        cells = [
            str(ptable.get_cell_at((row_idx, c)))
            for c in range(n_cols)
        ]
        if not cells:
            detail.update("[dim](no phase event)[/dim]")
            return
        detail.update(
            "[b]Phase event[/b]\n\n"
            + "\n".join(
                f"[dim]{label}:[/dim] {val}"
                for label, val in zip(
                    ("Time", "Phase", "Event", "Agent", "Detail"),
                    cells,
                )
            )
        )


__all__ = ["LiveRunScreen"]
