"""``ActiveRun`` — App-level handle + event buffer for an in-flight run.

Background-run substrate (Slice A). Owned by ``WonderlandApp``, not
by any single screen — that's the whole point. The Runner used to die
when ``LiveRunScreen`` popped (worker cancelled, stream torn down);
with ``ActiveRun`` the consumer task lives on the app, the screen is
just a subscriber that replays the buffer + tails new events when
mounted.

For now, runs only survive across screen pops within one running
TUI session — closing the app still tears the consumer down. The
roadmap item for true detached background processes is separate
work (notifications, remote control, etc.).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Literal

ActiveRunStatus = Literal["running", "complete", "aborted", "error"]

EventCallback = Callable[[Any], None]


@dataclass
class ActiveRun:
    """One in-flight run owned by the App.

    The ``buffer`` retains every event the consumer task has pulled
    so a freshly-mounted ``LiveRunScreen`` can replay the run from
    the beginning before tailing new events. Memory grows linearly
    with the run; bounded by the run's natural completion (typically
    minutes, low-thousands of events). Not pruned — analyses
    + transcripts work cleaner with the full set, and a finished
    run releases the buffer when ``WonderlandApp.unregister_run``
    drops the reference.

    Subscribers are notified synchronously on the App's event loop.
    Callbacks should be cheap (state-update style); heavy work
    belongs on a Textual worker.
    """

    run_id: str
    handle: Any  # LiveRunHandle (avoid import cycle in the dataclass header)
    buffer: list[Any] = field(default_factory=list)
    subscribers: list[EventCallback] = field(default_factory=list)
    status: ActiveRunStatus = "running"
    started_at: datetime = field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    ended_at: datetime | None = None
    task: asyncio.Task | None = None
    # Background runs use a disk-mediated operator-question bridge:
    # the subprocess writes pending_question.json, the App polls
    # for it via this task and surfaces the question through
    # AskUserModal. None for in-process runs (the LiveRunHandle's
    # direct handler covers them) or before the poller starts.
    question_poller_task: asyncio.Task | None = None

    def subscribe(self, callback: EventCallback) -> Callable[[], None]:
        """Register ``callback`` to receive every event — past
        (replayed from the buffer right now) and future (as the
        consumer task pulls them).

        Returns an unsubscribe function. Idempotent — calling the
        unsubscribe multiple times is fine; calling it after the run
        ends is fine.
        """
        for event in self.buffer:
            try:
                callback(event)
            except Exception:  # noqa: BLE001
                # A subscriber error during replay shouldn't poison
                # the run for other subscribers. Log to stderr would
                # be ideal but the App already has notify-style
                # error surfacing; for now swallow + continue.
                pass
        self.subscribers.append(callback)

        def _unsubscribe() -> None:
            try:
                self.subscribers.remove(callback)
            except ValueError:
                pass

        return _unsubscribe

    def _ingest(self, event: Any) -> None:
        """Buffer an event and fan it out to live subscribers.
        Called by the App's consumer task as each event arrives
        from the wrapped handle's stream."""
        self.buffer.append(event)
        # Iterate a copy so subscribers can unsubscribe themselves
        # mid-fanout without mutating the live list.
        for callback in list(self.subscribers):
            try:
                callback(event)
            except Exception:  # noqa: BLE001
                pass

    def mark_ended(self, status: ActiveRunStatus) -> None:
        self.status = status
        self.ended_at = datetime.now(tz=timezone.utc)

    @property
    def is_terminal(self) -> bool:
        return self.status != "running"


__all__ = ["ActiveRun", "ActiveRunStatus", "EventCallback"]
