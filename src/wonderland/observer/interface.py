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
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Iterator

from wonderland.utterance import Utterance

if TYPE_CHECKING:
    # Imported lazily to avoid a circular import — events.py imports
    # the dataclasses defined in this module.
    from wonderland.observer.events import RunEvent


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


@dataclass(frozen=True)
class RunArtifact:
    """An artifact shipped by an agent during the run, on disk.

    Distinct from ``wonderland.utterance.Artifact`` (which is the
    payload-pointer carried inside an utterance). This is the
    file-system-side view: where the artifact lives on disk, what
    kind it is, when it was written.

    ``kind``: canonical kind name (``story``, ``ticket``, ``feature``,
        ``contract_note``, ``test_scenario``, ``implementation``,
        ``review``, ``adr``, ``ruling``).
    ``path``: absolute path to the markdown file.
    ``title``: parsed from the first markdown heading; falls back to
        the slug if no heading is present.
    ``created_at``: file mtime — when the agent shipped it.
    """

    kind: str
    path: Path
    title: str
    created_at: datetime


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

    @abstractmethod
    def artifacts(self, *, kind: str | None = None) -> list[RunArtifact]:
        """Artifacts shipped during the run, found on disk in the
        snapshot's ``.wonderland/<kind>/`` subdirectories.

        ``kind`` filters to one artifact kind (e.g. ``"story"``,
        ``"feature"``, ``"contract_note"``). When ``None``, returns
        all artifacts across all kinds, sorted by ``created_at``
        ascending so the result reads as a timeline.
        """

    @abstractmethod
    def stream_events(self) -> AsyncIterator["RunEvent"]:
        """Stream the run as a chronologically ordered sequence of
        ``RunEvent`` instances. The streaming surface for live-watch
        UIs (and for the Mock Turtle replay testbed).

        Each implementation chooses its own pacing:

        - ``HistoricalRunHandle.stream_events()`` yields everything
          immediately (the snapshot is finished; consumer just
          wants the chronology).
        - ``MockTurtleHandle.stream_events()`` yields with
          compressed-time sleeping so a UI can be tested against
          real captured runs without API spend.
        - ``LiveRunHandle.stream_events()`` (P8.5) subscribes to a
          live runner and yields as events occur.

        Consumers iterate via ``async for``; UI code never branches
        on which subclass produced the events.
        """


__all__ = [
    "AgentTelemetry",
    "RunArtifact",
    "RunHandle",
    "RunMeeting",
    "RunSummary",
]
