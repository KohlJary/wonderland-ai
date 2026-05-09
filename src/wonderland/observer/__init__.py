"""Observer / query API — the contract every TUI/web/MCP frontend
consumes.

Two implementations of ``RunHandle``:
  - ``HistoricalRunHandle`` — read a snapshot directory.
  - ``LiveRunHandle`` — subscribe to a running runner. (Not yet built.)
"""

from wonderland.observer.events import (
    AgentActed,
    AgentPassed,
    AgentTelemetryDelta,
    ArtifactShipped,
    MeetingEnded,
    MeetingStarted,
    PhaseEnded,
    PhaseStarted,
    PriorityWindowOpened,
    RotationCompleted,
    RunEnded,
    RunEvent,
    RunStarted,
    UtteranceEmitted,
)
from wonderland.observer.historical import HistoricalRunHandle
from wonderland.observer.interface import (
    AgentTelemetry,
    RunArtifact,
    RunHandle,
    RunMeeting,
    RunSummary,
)
from wonderland.observer.live import LiveRunHandle
from wonderland.observer.mock_turtle import MockTurtleHandle

__all__ = [
    "AgentActed",
    "AgentPassed",
    "AgentTelemetry",
    "AgentTelemetryDelta",
    "ArtifactShipped",
    "HistoricalRunHandle",
    "LiveRunHandle",
    "MeetingEnded",
    "MeetingStarted",
    "MockTurtleHandle",
    "PhaseEnded",
    "PhaseStarted",
    "PriorityWindowOpened",
    "RotationCompleted",
    "RunArtifact",
    "RunEnded",
    "RunEvent",
    "RunHandle",
    "RunMeeting",
    "RunStarted",
    "RunSummary",
    "UtteranceEmitted",
]
