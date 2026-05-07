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
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from wonderland.observer.interface import (
    AgentTelemetry,
    RunHandle,
    RunMeeting,
    RunSummary,
)
from wonderland.utterance import Utterance


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

    def __init__(self, snapshot_dir: str | Path) -> None:
        self._dir = Path(snapshot_dir)
        self._wonderland_dir = self._dir / "wonderland-snapshot"
        self._log_path = self._dir / "run.log"

        if not self._wonderland_dir.is_dir():
            raise FileNotFoundError(
                f"snapshot missing wonderland-snapshot/: {self._dir}"
            )
        if not self._log_path.is_file():
            raise FileNotFoundError(f"snapshot missing run.log: {self._dir}")

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
        dodo_db = self._wonderland_dir / "memory" / "dodo" / "episodic.sqlite"
        if not dodo_db.is_file():
            return

        conn = sqlite3.connect(str(dodo_db))
        try:
            query = "SELECT payload FROM utterances"
            params: tuple[Any, ...] = ()
            if thread_id is not None:
                query += " WHERE thread_id = ?"
                params = (thread_id,)
            query += " ORDER BY timestamp"
            for (payload,) in conn.execute(query, params):
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
        files = sorted(telemetry_dir.glob("run-*.json"))
        if not files:
            self._telemetry_cache = {}
            return self._telemetry_cache
        with files[-1].open(encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
        self._telemetry_cache = data
        return data

    def _first_last_utterance_timestamps(
        self,
    ) -> tuple[datetime | None, datetime | None]:
        dodo_db = self._wonderland_dir / "memory" / "dodo" / "episodic.sqlite"
        if not dodo_db.is_file():
            return (None, None)
        conn = sqlite3.connect(str(dodo_db))
        try:
            row = conn.execute(
                "SELECT MIN(timestamp), MAX(timestamp) FROM utterances"
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
        conn = sqlite3.connect(str(dodo_db))
        out: dict[str, tuple[datetime | None, datetime | None]] = {}
        try:
            rows = conn.execute(
                "SELECT thread_id, MIN(timestamp), MAX(timestamp) "
                "FROM utterances GROUP BY thread_id"
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
