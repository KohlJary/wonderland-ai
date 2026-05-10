"""``HistoricalRunHandle`` — read-only view over a Wonderland run
snapshot on disk.

Snapshot shape (matches what's preserved in ``analyses/data/<NNN>/``):

    <snapshot_dir>/
        run.log                  # workflow_demo.py output
        wonderland-snapshot/
            memory/
                <agent>/
                    episodic.sqlite
            telemetry/
                run-<id>.json
            stories/, tickets/, features/, contract-notes/,
            test-scenarios/, implementations/, reviews/, architecture/

The Dodo's episodic.sqlite is used as the canonical utterance stream
(he subscribes bus-wide as the convenor; every utterance lands in his
memory). Other agents' SQLites are partial views — useful for cross-
checking but not as the primary source.

Parsing strategy:
  - ``summary()`` parses the head of run.log for directive, workflow,
    project root.
  - ``meetings()`` parses START/END lines from run.log.
  - ``utterances()`` reads payload JSON from Dodo's SQLite.
  - ``per_agent_telemetry()`` reads the latest ``telemetry/run-*.json``.

Lazy-loaded: parses on first access, caches result.
"""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from wonderland.observer.interface import (
    AgentTelemetry,
    RunArtifact,
    RunHandle,
    RunMeeting,
    RunSummary,
)
from wonderland.utterance import Utterance


# Map ``.wonderland/<dir>/`` directory names → canonical artifact kind
# strings used in utterance payloads. The directory and the kind name
# diverged historically (``test-scenarios`` on disk vs
# ``test_scenario`` in the schema); this is the bridge.
_ARTIFACT_DIR_TO_KIND = {
    "stories": "story",
    "tickets": "ticket",
    "features": "feature",
    "contract-notes": "contract_note",
    "test-scenarios": "test_scenario",
    "implementations": "implementation",
    "reviews": "review",
    "architecture": "adr",
    "rulings": "ruling",
}


def _parse_title_from_markdown(path: Path, fallback: str) -> str:
    """Read the first heading from a markdown file as its title.

    Tries ``# Heading`` first (proper H1), then ``## Heading`` (the
    artifact convention for stories/tickets/etc, which strip an
    "Item NNN: " prefix). Falls back to the supplied default.
    """
    try:
        with path.open(encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.rstrip()
                if line.startswith("# "):
                    return line[2:].strip()
                if line.startswith("## "):
                    title = line[3:].strip()
                    if ":" in title:
                        return title.split(":", 1)[1].strip()
                    return title
                if line.strip():
                    break  # first non-empty non-heading: bail
    except OSError:
        pass
    return fallback


# Match log lines like:
#   "  M2.5 (Advice from a Caterpillar) START · composition · roster=..."
#   "  M1 START · scoping · roster=..."
_MEETING_START_RE = re.compile(
    r"^\s*(M[\d.]+)(?:\s+\((.+?)\))?\s+START\s+·\s+([\w-]+)"
)
# Match log lines like:
#   "  M2.5 (Advice from a Caterpillar) END · COMPLETE · 16.4s · 8 calls · $0.0930"
#   "  M5 END · COMPLETE · 0.0s · 0 calls · $0.0000"
_MEETING_END_RE = re.compile(
    r"^\s*(M[\d.]+)(?:\s+\((.+?)\))?\s+END\s+·\s+(\w+)\s+·\s+([\d.]+)s\s+·\s+(\d+)\s+calls\s+·\s+\$([\d.]+)"
)
# Run-level summary lines from the bottom of run.log
_TOTAL_COST_RE = re.compile(r"^\s*Total\s+cost:\s+\$([\d.]+)")
_TOTAL_ELAPSED_RE = re.compile(r"^\s*Total\s+elapsed:\s+([\d.]+)s")
_DIRECTIVE_RE = re.compile(r"^\s*Directive:\s+(.+)$")
_WORKFLOW_RE = re.compile(r"^\s*Running workflow '([\w-]+)'")
_PROJECT_ROOT_RE = re.compile(r"^\s*Project root:\s+(.+)$")


class HistoricalRunHandle(RunHandle):
    """View over a completed run preserved in a snapshot directory.

    Construct from any ``analyses/data/<NNN>/`` path or any directory
    matching the snapshot shape. All accessors are lazy and cached;
    the constructor does cheap shape validation only.
    """

    def __init__(
        self,
        snapshot_dir: str | Path,
        *,
        run_id: str | None = None,
        time_window: tuple[datetime, datetime] | None = None,
        workflow_name: str | None = None,
    ) -> None:
        """Construct a read-only handle over a snapshot.

        ``run_id`` (TUI-driven, project-scoped .wonderland/ only):
        scope the handle to a single run within a project that has
        accumulated artifacts across many runs. When set:
          - ``_load_telemetry`` reads ``telemetry/run-<run_id>.json``
            instead of the latest file.
          - ``utterances()``, ``stream_events()``, etc. filter to
            timestamps within ``time_window`` (which the caller
            should derive from the run's started_at + elapsed).
        Without ``run_id`` the handle behaves project-scoped — the
        original semantics for analyses/data snapshots, which are
        already one-snapshot-per-run by construction.

        ``time_window`` is the (start, end) UTC datetime range used
        to filter Dodo's cumulative episodic memory down to
        utterances that belong to the named run. Required when
        ``run_id`` is set; ignored otherwise. Caller should derive
        from ``RunRecord.started_at`` + ``elapsed_seconds`` (with
        a small slop on the end to catch the final RunEnded
        artifact).
        """
        self._dir = Path(snapshot_dir)
        # Two snapshot layouts are accepted:
        #   1. Script-driven (analyses/data/...) — contains
        #      ``wonderland-snapshot/`` and ``run.log`` at the top.
        #   2. TUI-driven (project_root/.wonderland/) — contains
        #      ``.wonderland/`` and no run.log (TUI runs don't yet
        #      write the verbose log; telemetry.json carries the
        #      cost + outcome data).
        # Both layouts have the same internal structure inside the
        # wonderland directory (memory/, telemetry/, stories/, etc.),
        # so once we resolve which one is present, the rest of the
        # accessors work uniformly.
        wonderland_snapshot = self._dir / "wonderland-snapshot"
        dot_wonderland = self._dir / ".wonderland"
        if wonderland_snapshot.is_dir():
            self._wonderland_dir = wonderland_snapshot
        elif dot_wonderland.is_dir():
            self._wonderland_dir = dot_wonderland
        else:
            raise FileNotFoundError(
                f"snapshot missing wonderland-snapshot/ or "
                f".wonderland/: {self._dir}"
            )
        # run.log is optional. Methods that depend on it (summary's
        # directive/workflow header, meetings()) gracefully degrade
        # when it's absent.
        self._log_path = self._dir / "run.log"

        # Run-scoping fields (None = project-scoped behavior).
        self._run_id = run_id
        self._time_window = time_window

        # Optional workflow name → used at stream_events time to load
        # the static workflow definition and build the meeting label
        # lookup from ``workflow.meetings``. Without this, TUI runs
        # (which don't write run.log) end up with an empty meeting
        # lookup and the synthetic-label fallback dumps thread_ids
        # into the meetings pane. With it, we resolve every thread to
        # the proper ``M<N> — <name>``.
        self._workflow_name = workflow_name
        self._workflow_meetings_cache: list[Any] | None = None

        self._summary_cache: RunSummary | None = None
        self._meetings_cache: list[RunMeeting] | None = None
        self._telemetry_cache: dict[str, Any] | None = None

    @property
    def snapshot_dir(self) -> Path:
        return self._dir

    # ------------------------------------------------------------------ #
    # Public API — RunHandle implementation
    # ------------------------------------------------------------------ #

    def summary(self) -> RunSummary:
        if self._summary_cache is not None:
            return self._summary_cache

        directive: str | None = None
        workflow: str | None = None
        project_root: Path | None = None
        total_cost = 0.0
        elapsed_seconds: float | None = None

        if self._log_path.is_file():
            with self._log_path.open(encoding="utf-8", errors="replace") as f:
                for line in f:
                    if directive is None:
                        m = _DIRECTIVE_RE.match(line)
                        if m:
                            directive = m.group(1).strip()
                            continue
                    if workflow is None:
                        m = _WORKFLOW_RE.match(line)
                        if m:
                            workflow = m.group(1)
                            continue
                    if project_root is None:
                        m = _PROJECT_ROOT_RE.match(line)
                        if m:
                            project_root = Path(m.group(1).strip())
                            continue
                    m = _TOTAL_COST_RE.match(line)
                    if m:
                        total_cost = float(m.group(1))
                        continue
                    m = _TOTAL_ELAPSED_RE.match(line)
                    if m:
                        elapsed_seconds = float(m.group(1))
                        continue
        else:
            # TUI runs don't write run.log yet — fall back to the
            # snapshot directory itself as project_root so the UI
            # has something coherent to display. Directive and
            # workflow_name remain None until the TUI writes them
            # (forward-looking work).
            project_root = self._dir

        telemetry = self._load_telemetry()
        run_id = telemetry.get("run_id")
        total_calls = int(telemetry.get("total_calls", 0))
        outcome = telemetry.get("outcome")

        # Started/ended timestamps come from the first/last utterance
        # in Dodo's memory. We don't want to require run.log to carry
        # absolute timestamps (it doesn't right now).
        started_at, ended_at = self._first_last_utterance_timestamps()

        self._summary_cache = RunSummary(
            run_id=run_id,
            workflow_name=workflow,
            directive=directive,
            project_root=project_root,
            started_at=started_at,
            ended_at=ended_at,
            total_cost=total_cost or float(telemetry.get("total_cost", 0.0)),
            total_calls=total_calls,
            outcome=outcome,
        )
        return self._summary_cache

    def meetings(self) -> list[RunMeeting]:
        if self._meetings_cache is not None:
            return self._meetings_cache

        starts: dict[str, dict[str, Any]] = {}  # label → metadata
        ends: dict[str, dict[str, Any]] = {}
        order: list[str] = []  # labels in encounter order

        if not self._log_path.is_file():
            # TUI runs without run.log can't reconstruct the per-
            # meeting START/END timeline. Future work: derive from
            # phase-events.jsonl + telemetry. For now, return empty
            # so callers (TUI run summary) display "0 meetings"
            # rather than crashing.
            self._meetings_cache = []
            return self._meetings_cache

        with self._log_path.open(encoding="utf-8", errors="replace") as f:
            for line in f:
                m = _MEETING_START_RE.match(line)
                if m:
                    label, name, mid = m.group(1), m.group(2), m.group(3)
                    if label not in starts:
                        starts[label] = {"id": mid, "name": name}
                        order.append(label)
                    continue
                m = _MEETING_END_RE.match(line)
                if m:
                    label = m.group(1)
                    ends[label] = {
                        "name": m.group(2),
                        "outcome": m.group(3),
                        "elapsed": float(m.group(4)),
                        "calls": int(m.group(5)),
                        "cost": float(m.group(6)),
                    }

        # Build start/end times from Dodo's memory per thread_id.
        thread_ranges = self._thread_time_ranges()

        meetings: list[RunMeeting] = []
        for label in order:
            s = starts[label]
            e = ends.get(label)
            mid = s["id"]
            tr = thread_ranges.get(mid, (None, None))
            meetings.append(
                RunMeeting(
                    id=mid,
                    label=label,
                    name=s["name"] or (e["name"] if e else None),
                    started_at=tr[0],
                    ended_at=tr[1],
                    outcome=e["outcome"] if e else None,
                    elapsed_seconds=e["elapsed"] if e else None,
                    calls=e["calls"] if e else 0,
                    cost=e["cost"] if e else 0.0,
                )
            )

        self._meetings_cache = meetings
        return meetings

    def utterances(
        self,
        *,
        thread_id: str | None = None,
    ) -> Iterator[Utterance]:
        """Iterate utterances in chronological order.

        When the handle was constructed with ``time_window``, results
        are filtered to utterances whose ``timestamp`` falls inside
        the window — this is how project-scoped Dodo memory gets
        sliced down to a single run for the TUI's "open finished
        run" path.
        """
        dodo_db = self._wonderland_dir / "memory" / "dodo" / "episodic.sqlite"
        if not dodo_db.is_file():
            return

        conn = sqlite3.connect(str(dodo_db))
        try:
            query = "SELECT payload FROM utterances"
            clauses: list[str] = []
            params: list[Any] = []
            if thread_id is not None:
                clauses.append("thread_id = ?")
                params.append(thread_id)
            if self._time_window is not None:
                start, end = self._time_window
                # Stored timestamps are ISO-format strings; lex-order
                # matches chronological order for ISO-8601 with the
                # same offset, which is how Dodo writes them.
                clauses.append("timestamp >= ?")
                clauses.append("timestamp <= ?")
                params.append(start.isoformat())
                params.append(end.isoformat())
            if clauses:
                query += " WHERE " + " AND ".join(clauses)
            query += " ORDER BY timestamp"
            for (payload,) in conn.execute(query, tuple(params)):
                yield Utterance.model_validate_json(payload)
        finally:
            conn.close()

    def per_agent_telemetry(self) -> list[AgentTelemetry]:
        telemetry = self._load_telemetry()
        per_agent = telemetry.get("per_agent", {})
        out = [
            AgentTelemetry(
                name=name,
                calls=int(row.get("calls", 0)),
                cost=float(row.get("cost", 0.0)),
            )
            for name, row in per_agent.items()
        ]
        out.sort(key=lambda a: a.cost, reverse=True)
        return out

    def _parse_end_markers(self) -> list[dict[str, Any]]:
        """Parse all META END lines from run.log in chronological
        order. Each entry carries the cost/calls/outcome/elapsed for
        that meeting (or per_item iteration). Used by stream_events
        to populate MeetingEnded.cost_delta / calls_delta / outcome
        which the run.log captures but the meetings() dedup-by-label
        loses for per_item iterations.
        """
        out: list[dict[str, Any]] = []
        if not self._log_path.is_file():
            # TUI runs predate the log writer; stream_events still
            # works for utterances + meetings (degraded), just no
            # per-iteration end markers to attach.
            return out
        with self._log_path.open(encoding="utf-8", errors="replace") as f:
            for line in f:
                m = _MEETING_END_RE.match(line)
                if not m:
                    continue
                label, name, outcome, elapsed, calls, cost = m.groups()
                out.append(
                    {
                        "label": label,
                        "name": name,
                        "outcome": outcome,
                        "elapsed_s": float(elapsed),
                        "calls": int(calls),
                        "cost": float(cost),
                    }
                )
        return out

    async def stream_events(self):
        """Streaming view of the snapshot — yields RunEvents in
        chronological order with no sleeping (the snapshot is finished;
        the consumer just wants the chronology).

        Order:
          1. RunStarted with the run's summary.
          2. For each meeting (detected via utterance thread_id
             transitions): MeetingStarted, then UtteranceEmitted /
             ArtifactShipped events for each utterance on that
             thread, then MeetingEnded.
          3. AgentTelemetryDelta for each agent with the final
             accumulated calls + cost.
          4. RunEnded with the final summary.

        Per_item iteration metadata (iteration_index, iteration_total,
        iteration_label) on MeetingStarted/MeetingEnded is left None
        in T41. Lighting it up depends on the meetings() parser
        learning about per_item iterations — filed as roadmap
        7a5ff815. Until that ships, consumers can derive iteration
        identity from the thread_id (e.g. ``test-scenarios-foo``).

        T47 update: MeetingEnded.cost_delta / calls_delta / outcome
        now populate from the run.log's META END markers, in
        chronological order. Per_item iterations get their per-
        iteration cost rather than 0.

        Substrate divergence (artifacts written via tool call without
        a corresponding bus speech-act emission, per roadmap 92cec468)
        means some on-disk artifacts won't appear as ArtifactShipped
        events here. The non-streaming ``artifacts()`` method remains
        authoritative for "what shipped to disk" — this stream is
        "what landed on the bus."
        """
        # Lazy imports to avoid circular dep at module-load time.
        from wonderland.observer.events import (
            AgentTelemetryDelta,
            ArtifactShipped,
            MeetingEnded,
            MeetingStarted,
            RunEnded,
            RunStarted,
            UtteranceEmitted,
        )

        summary = self.summary()
        # Anchor timestamp for events that don't have a natural one
        # (RunStarted before the first utterance, RunEnded after the
        # last). Falls back to epoch only if the snapshot has no
        # timing info at all.
        run_start_ts = summary.started_at or datetime.fromtimestamp(0, tz=timezone.utc)
        run_end_ts = summary.ended_at or run_start_ts

        yield RunStarted(timestamp=run_start_ts, summary=summary)

        # Build a thread_id → RunMeeting map for label/name lookup.
        # Two sources, in priority order:
        #
        #  1. ``self.meetings()`` — parsed from run.log when present
        #     (script-driven runs). Empty for TUI runs that don't
        #     write run.log, which is why the synthetic fallback
        #     used to bite for every thread.
        #  2. The static workflow definition, when ``workflow_name``
        #     was passed to the constructor. Loads the workflow,
        #     reads ``workflow.meetings`` for label + name. This is
        #     what the dashboard now uses for finished-run replay
        #     to ensure pipeline thread_ids resolve to a clean
        #     ``M<N> — <name>``.
        meeting_lookup: dict[str, RunMeeting] = {m.id: m for m in self.meetings()}
        if not meeting_lookup and self._workflow_name:
            try:
                from wonderland.workflow import load_workflow

                workflow = load_workflow(self._workflow_name)
                for wm in workflow.meetings:
                    meeting_lookup[wm.id] = RunMeeting(
                        id=wm.id,
                        label=wm.label,
                        name=wm.name,
                        started_at=None,
                        ended_at=None,
                        outcome=None,
                        elapsed_seconds=None,
                        calls=0,
                        cost=0.0,
                    )
            except Exception:  # noqa: BLE001
                # Workflow load failure is recoverable — falls
                # through to the structural-extraction path below.
                pass

        def _strip_pipeline_prefix(thread_id: str) -> str:
            """Pipeline workflows namespace threads with
            ``pipe.<outer_slug>.`` (see ``workflow._make_lane``).
            Strip that prefix so the remainder lines up with the
            base meeting ids in the lookup. No-op for non-pipeline
            threads."""
            if thread_id.startswith("pipe."):
                rest = thread_id[len("pipe."):]
                # ``rest`` is ``<outer_slug>.<inner>`` — the inner
                # part is what we want. Split on the first dot.
                _outer, _, inner = rest.partition(".")
                return inner if inner else thread_id
            return thread_id

        def _build_synthetic(
            thread_id: str, label: str, name: str | None
        ) -> RunMeeting:
            return RunMeeting(
                id=thread_id,
                label=label,
                name=name,
                started_at=None,
                ended_at=None,
                outcome=None,
                elapsed_seconds=None,
                calls=0,
                cost=0.0,
            )

        def _iteration_label_from_thread_id(thread_id: str) -> str | None:
            """Recover an iteration discriminator from a pipeline
            thread_id. Two pipeline shapes the substrate emits:

              ``pipe.<feature>.<meeting_id>``
                  Single-level (e.g. design runs) — the feature
                  is the iteration. Returns the humanised feature
                  slug.

              ``pipe.<feature>.<meeting_id>-<sub_slug>``
                  Two-level (implementation runs with per-ticket
                  iterations inside per-feature lanes). Returns
                  ``<feature> / <sub_slug>`` so each row in the
                  meetings pane is distinct per-ticket — matches
                  the live path's iteration_label shape (line ~1354
                  in workflow.py: ``f"{outer_label} / {sub_label}"``).

            Returns None for non-pipeline threads. We rely on
            ``meeting_lookup`` to find the meeting_id boundary
            within the inner segment — without it (no workflow
            passed + no run.log), the sub_slug can't be reliably
            extracted, so we fall back to feature-only.
            """
            if not thread_id.startswith("pipe."):
                return None
            rest = thread_id[len("pipe."):]
            outer, dot, inner = rest.partition(".")
            if not dot or not outer:
                return None
            outer_h = (
                outer.replace("-", " ").strip().capitalize() or outer
            )
            # Identify the meeting_id boundary in ``inner``. Longest
            # match against the lookup to avoid mis-truncating when
            # one meeting id is a prefix of another.
            best_base = None
            for base_id in meeting_lookup:
                if inner == base_id:
                    return outer_h  # Pure base meeting, no sub-slug.
                if inner.startswith(f"{base_id}-"):
                    if best_base is None or len(base_id) > len(best_base):
                        best_base = base_id
            if best_base is not None:
                sub_slug = inner[len(best_base) + 1:]
                sub_h = (
                    sub_slug.replace("-", " ").strip().capitalize()
                    or sub_slug
                )
                return f"{outer_h} / {sub_h}"
            # Unknown meeting_id — return the feature alone.
            return outer_h

        def _meeting_for(thread_id: str) -> RunMeeting:
            # Direct hit on the full thread_id (script-driven runs
            # where the meeting id IS the thread_id).
            if thread_id in meeting_lookup:
                return meeting_lookup[thread_id]
            # Strip the pipeline prefix — for ``pipe.<outer>.<inner>``
            # we match against ``<inner>``.
            inner = _strip_pipeline_prefix(thread_id)
            if inner in meeting_lookup:
                m = meeting_lookup[inner]
                return _build_synthetic(thread_id, m.label, m.name)
            # Per-iteration thread: ``<base>-<slug>`` shape on either
            # the original or the post-pipeline-strip form. Iterate
            # the lookup to find the longest matching base id —
            # longest-match disambiguates cases where one meeting id
            # is a prefix of another (none today, but cheap to
            # protect against).
            best: tuple[int, str, RunMeeting] | None = None
            for base_id, m in meeting_lookup.items():
                for candidate in (thread_id, inner):
                    if candidate.startswith(f"{base_id}-"):
                        if best is None or len(base_id) > best[0]:
                            best = (len(base_id), base_id, m)
            if best is not None:
                _, _, m = best
                return _build_synthetic(thread_id, m.label, m.name)
            # No match. Don't dump the raw thread_id into the label
            # field — the meetings pane would render it verbatim.
            # Use a placeholder ``Meeting`` label and stash the
            # thread_id-derived id in the ``id`` field for anyone
            # who wants to inspect it.
            return _build_synthetic(thread_id, "Meeting", None)

        # Index disk artifacts by basename for resolving bus-attached
        # artifacts to their on-disk RunArtifact equivalent. Matches
        # the resolution pattern used by the TUI's modal-artifact-link.
        artifacts_by_basename = {a.path.name: a for a in self.artifacts()}

        # Pre-parse the run.log's META END markers in chronological
        # order. Each MeetingEnded event consumes the next marker that
        # matches its meeting's label, populating cost_delta /
        # calls_delta / outcome with the actual numbers from the log
        # rather than zeros (T47 fix).
        end_markers = self._parse_end_markers()
        # Track the next marker index per label so per_item iterations
        # of the same meeting consume their END markers in order.
        marker_cursor: dict[str, int] = {}

        def _next_end_marker(label: str) -> dict[str, Any] | None:
            """Pop the next chronologically-ordered END marker that
            matches ``label``. Returns None if none remain (shouldn't
            happen in well-formed snapshots, but tolerated)."""
            cursor = marker_cursor.get(label, 0)
            for i in range(cursor, len(end_markers)):
                if end_markers[i]["label"] == label:
                    marker_cursor[label] = i + 1
                    return end_markers[i]
            marker_cursor[label] = len(end_markers)
            return None

        current_thread_id: str | None = None
        meeting_open_ts: datetime | None = None
        last_event_ts: datetime = run_start_ts

        for u in self.utterances():
            last_event_ts = u.timestamp

            # Meeting transition?
            if u.thread_id != current_thread_id:
                # Close the prior meeting with its actual cost/calls
                # /outcome from the run.log END marker.
                if current_thread_id is not None and meeting_open_ts is not None:
                    prev = _meeting_for(current_thread_id)
                    end_data = _next_end_marker(prev.label)
                    if end_data is not None:
                        outcome = end_data["outcome"]
                        elapsed = end_data["elapsed_s"]
                        calls = end_data["calls"]
                        cost = end_data["cost"]
                    else:
                        # Fall back to inferred values when no marker
                        # is available (rare; only happens if the run
                        # was killed before the END was logged).
                        outcome = prev.outcome or "COMPLETE"
                        elapsed = (u.timestamp - meeting_open_ts).total_seconds()
                        calls = 0
                        cost = 0.0
                    yield MeetingEnded(
                        timestamp=u.timestamp,
                        meeting=prev,
                        thread_id=current_thread_id,
                        outcome=outcome,
                        elapsed_seconds=elapsed,
                        calls_delta=calls,
                        cost_delta=cost,
                        artifact_kinds={},
                    )
                # Open the new one.
                new_meeting = _meeting_for(u.thread_id)
                yield MeetingStarted(
                    timestamp=u.timestamp,
                    meeting=new_meeting,
                    thread_id=u.thread_id,
                    iteration_label=_iteration_label_from_thread_id(
                        u.thread_id
                    ),
                )
                current_thread_id = u.thread_id
                meeting_open_ts = u.timestamp

            yield UtteranceEmitted(timestamp=u.timestamp, utterance=u)

            for attached in u.content.artifacts or []:
                payload = (
                    attached.payload if isinstance(attached.payload, dict) else {}
                )
                raw_path = payload.get("path")
                if not raw_path:
                    continue
                run_artifact = artifacts_by_basename.get(Path(raw_path).name)
                if run_artifact is not None:
                    yield ArtifactShipped(
                        timestamp=u.timestamp,
                        artifact=run_artifact,
                    )

        # Close the final meeting (same end-marker lookup as above).
        if current_thread_id is not None and meeting_open_ts is not None:
            final = _meeting_for(current_thread_id)
            end_data = _next_end_marker(final.label)
            if end_data is not None:
                outcome = end_data["outcome"]
                elapsed = end_data["elapsed_s"]
                calls = end_data["calls"]
                cost = end_data["cost"]
            else:
                outcome = final.outcome or "COMPLETE"
                elapsed = (last_event_ts - meeting_open_ts).total_seconds()
                calls = 0
                cost = 0.0
            yield MeetingEnded(
                timestamp=last_event_ts,
                meeting=final,
                thread_id=current_thread_id,
                outcome=outcome,
                elapsed_seconds=elapsed,
                calls_delta=calls,
                cost_delta=cost,
                artifact_kinds={},
            )

        # Per-agent telemetry deltas — the final accumulated values.
        # In T41 we emit these once at the end of the stream rather
        # than continuously throughout (no per-call timing in the
        # snapshot to attribute to). Live and Mock-Turtle handles
        # may emit deltas more frequently.
        for telemetry in self.per_agent_telemetry():
            yield AgentTelemetryDelta(
                timestamp=run_end_ts,
                telemetry=telemetry,
            )

        yield RunEnded(timestamp=run_end_ts, summary=summary)

    def artifacts(self, *, kind: str | None = None) -> list[RunArtifact]:
        out: list[RunArtifact] = []
        for dir_name, canonical_kind in _ARTIFACT_DIR_TO_KIND.items():
            if kind is not None and kind != canonical_kind:
                continue
            artifact_dir = self._wonderland_dir / dir_name
            if not artifact_dir.is_dir():
                continue
            for path in sorted(artifact_dir.glob("*.md")):
                if not path.is_file():
                    continue
                stem = path.stem  # e.g. "feature-001-foo-bar"
                title = _parse_title_from_markdown(path, fallback=stem)
                # tz-aware UTC for consistency with utterance timestamps
                # (which are tz-aware UTC). Mixing the two throws.
                created_at = datetime.fromtimestamp(
                    path.stat().st_mtime, tz=timezone.utc
                )
                out.append(
                    RunArtifact(
                        kind=canonical_kind,
                        path=path,
                        title=title,
                        created_at=created_at,
                    )
                )
        out.sort(key=lambda a: a.created_at)
        return out

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _load_telemetry(self) -> dict[str, Any]:
        if self._telemetry_cache is not None:
            return self._telemetry_cache
        telemetry_dir = self._wonderland_dir / "telemetry"
        if not telemetry_dir.is_dir():
            self._telemetry_cache = {}
            return self._telemetry_cache
        # Run-scoped: prefer the named run's telemetry file. Falls
        # through to "latest" if the named file is missing — robust
        # against the case where a caller passes an old run_id whose
        # telemetry file got cleaned up or moved.
        if self._run_id is not None:
            target = telemetry_dir / f"run-{self._run_id}.json"
            if target.is_file():
                with target.open(encoding="utf-8") as f:
                    data: dict[str, Any] = json.load(f)
                self._telemetry_cache = data
                return data
        files = sorted(telemetry_dir.glob("run-*.json"))
        if not files:
            self._telemetry_cache = {}
            return self._telemetry_cache
        with files[-1].open(encoding="utf-8") as f:
            data = json.load(f)
        self._telemetry_cache = data
        return data

    def _window_clause(self) -> tuple[str, list[Any]]:
        """SQL fragment + params for the optional time-window filter.
        Returns ('', []) when the handle is project-scoped.
        """
        if self._time_window is None:
            return "", []
        start, end = self._time_window
        return (
            " WHERE timestamp >= ? AND timestamp <= ?",
            [start.isoformat(), end.isoformat()],
        )

    def _first_last_utterance_timestamps(
        self,
    ) -> tuple[datetime | None, datetime | None]:
        dodo_db = self._wonderland_dir / "memory" / "dodo" / "episodic.sqlite"
        if not dodo_db.is_file():
            return (None, None)
        where, params = self._window_clause()
        conn = sqlite3.connect(str(dodo_db))
        try:
            row = conn.execute(
                "SELECT MIN(timestamp), MAX(timestamp) FROM utterances"
                + where,
                tuple(params),
            ).fetchone()
        finally:
            conn.close()
        if not row or row[0] is None:
            return (None, None)
        return (datetime.fromisoformat(row[0]), datetime.fromisoformat(row[1]))

    def _thread_time_ranges(
        self,
    ) -> dict[str, tuple[datetime | None, datetime | None]]:
        dodo_db = self._wonderland_dir / "memory" / "dodo" / "episodic.sqlite"
        if not dodo_db.is_file():
            return {}
        where, params = self._window_clause()
        conn = sqlite3.connect(str(dodo_db))
        out: dict[str, tuple[datetime | None, datetime | None]] = {}
        try:
            rows = conn.execute(
                "SELECT thread_id, MIN(timestamp), MAX(timestamp) "
                "FROM utterances"
                + where
                + " GROUP BY thread_id",
                tuple(params),
            ).fetchall()
        finally:
            conn.close()
        for thread_id, mn, mx in rows:
            if not thread_id:
                continue
            out[thread_id] = (
                datetime.fromisoformat(mn) if mn else None,
                datetime.fromisoformat(mx) if mx else None,
            )
        return out


__all__ = ["HistoricalRunHandle"]
