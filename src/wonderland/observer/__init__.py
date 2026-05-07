"""Observer / query API — the contract every TUI/web/MCP frontend
consumes.

Two implementations of ``RunHandle``:
  - ``HistoricalRunHandle`` — read a snapshot directory.
  - ``LiveRunHandle`` — subscribe to a running runner. (Not yet built.)
"""

from wonderland.observer.historical import HistoricalRunHandle
from wonderland.observer.interface import (
    AgentTelemetry,
    RunHandle,
    RunMeeting,
    RunSummary,
)

__all__ = [
    "AgentTelemetry",
    "HistoricalRunHandle",
    "RunHandle",
    "RunMeeting",
    "RunSummary",
]
