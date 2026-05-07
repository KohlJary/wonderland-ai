"""Abstract `RunHandle` interface — the contract every TUI/web/MCP
frontend consumes.

Two implementations:
  - ``HistoricalRunHandle`` — reads from a snapshot directory
    (``analyses/data/<NNN>/``). Iterating against past runs is the
    load-bearing development path for the TUI; UI code never needs to
    branch on "is this live or historical?"
  - ``LiveRunHandle`` — subscribes to a running ``Runner``. Same
    interface, just a different source. (Not yet implemented; built
    as a strict extension once the historical UX is solid.)

The interface is deliberately narrow. Frontends should be able to
implement everything they need by calling the methods here; if they
reach for ``.wonderland/`` files directly, that's a sign the
interface needs another method, not a sign the frontend should
bypass it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator

from wonderland.utterance import Utterance


@dataclass(frozen=True)
class RunMeeting:
    """A meeting within the run — identifier, timing, outcome."""

    id: str
    label: str
    name: str | None
    started_at: datetime | None
    ended_at: datetime | None
    outcome: str | None  # COMPLETE / MEETING_BUDGET / TIMEOUT / ABORTED / RUNNING
    elapsed_seconds: float | None
    calls: int
    cost: float


@dataclass(frozen=True)
class RunSummary:
    """High-level run metadata."""

    run_id: str | None
    workflow_name: str | None
    directive: str | None
    project_root: Path | None
    started_at: datetime | None
    ended_at: datetime | None
    total_cost: float
    total_calls: int
    outcome: str | None  # global outcome if known


@dataclass(frozen=True)
class AgentTelemetry:
    """Per-agent cost and call counts for the run."""

    name: str
    calls: int
    cost: float


class RunHandle(ABC):
    """Read-only view of a Wonderland run.

    Implementations:
      - ``HistoricalRunHandle(snapshot_dir)`` for completed runs
        preserved on disk.
      - ``LiveRunHandle(runner)`` for currently-executing runs.
    """

    @abstractmethod
    def summary(self) -> RunSummary:
        """Run-level metadata: workflow, directive, total cost, etc."""

    @abstractmethod
    def meetings(self) -> list[RunMeeting]:
        """All meetings in the run, in workflow order."""

    @abstractmethod
    def utterances(
        self,
        *,
        thread_id: str | None = None,
    ) -> Iterator[Utterance]:
        """Stream utterances chronologically.

        ``thread_id`` filters to a single meeting (matches the
        ``Meeting.id`` from the workflow YAML, e.g. ``"scoping"`` or
        ``"composition"``). When ``None``, yields everything across
        the run.
        """

    @abstractmethod
    def per_agent_telemetry(self) -> list[AgentTelemetry]:
        """Per-agent call count + cost. Sorted by cost descending."""


__all__ = [
    "AgentTelemetry",
    "RunHandle",
    "RunMeeting",
    "RunSummary",
]
