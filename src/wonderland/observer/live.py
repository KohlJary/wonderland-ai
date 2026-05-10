"""``LiveRunHandle`` — wrap a real ``Runner`` + ``Workflow`` and emit
through the same ``RunHandle`` protocol that ``HistoricalRunHandle``
and ``MockTurtleHandle`` use.

The leap from "replay testbed" to "live operator interface": with
LiveRunHandle in place, the same ``LiveRunScreen`` consumes a real
run streaming from a Caucus bus exactly like it consumes a Mock
Turtle replay. UI code never branches on which source it's reading.

Lifecycle:
  - Constructor takes a Runner + Workflow + directive. Caller
    constructs the Runner via ``Runner.make_full_cast`` (or other
    factory) so test code can inject fakes.
  - ``stream_events()`` runs the run end-to-end:
      1. ``runner.setup()`` (creates dispatcher, agents, etc.)
      2. yield RunStarted
      3. drive ``run_workflow(...)`` — translate each emitted event
         into our ``RunEvent`` shape:
           - workflow's MeetingStartEvent → MeetingStarted
           - RunnerEvent(kind="utterance") → UtteranceEmitted +
             ArtifactShipped events for each attached artifact
           - workflow's MeetingEndEvent → MeetingEnded
           - terminal RunnerEvents (budget_exceeded / timeout /
             aborted) end the run with the matching outcome
      4. yield AgentTelemetryDelta per agent (final accumulated
         calls + cost from runner.telemetry)
      5. yield RunEnded
  - ``finally`` block calls ``runner.teardown()`` regardless of
    cancellation, so background threads / dispatcher tasks don't
    leak when the consumer aborts mid-stream.

Non-streaming methods (``summary``, ``meetings``, ``utterances``,
``artifacts``, ``per_agent_telemetry``) work against the in-progress
run — they snapshot accumulated state at call time. This means a
consumer can ask "what's been shipped so far?" mid-stream without
re-walking events.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

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
    RunStarted,
    UtteranceEmitted,
)
from wonderland.observer.interface import (
    AgentTelemetry,
    RunArtifact,
    RunHandle,
    RunMeeting,
    RunSummary,
)
from wonderland.utterance import Utterance

if TYPE_CHECKING:
    from wonderland.runner import Runner
    from wonderland.workflow import Workflow


class LiveRunHandle(RunHandle):
    """Wraps a live Runner+Workflow run and emits through the
    streaming RunHandle protocol.

    Parameters
    ----------
    runner:
        A constructed Runner (typically from ``Runner.make_full_cast(
        project_root=...)``). LiveRunHandle owns its lifecycle —
        setup is called at the start of ``stream_events()`` and
        teardown is called in a finally block.
    workflow:
        A loaded Workflow (e.g. from ``load_workflow("tdd-serial")``).
    directive:
        The user-facing directive text fed to the entry meeting's
        Dodo convene.
    """

    def __init__(
        self,
        runner: "Runner",
        workflow: "Workflow",
        directive: str,
    ) -> None:
        self._runner = runner
        self._workflow = workflow
        self._directive = directive
        # Accumulated state for the non-streaming methods. Updated
        # as events flow during stream_events.
        self._utterances_buffer: list[Utterance] = []
        self._meetings_buffer: list[RunMeeting] = []
        self._meeting_by_thread: dict[str, RunMeeting] = {}
        self._artifacts_buffer: list[RunArtifact] = []
        self._final_outcome: str | None = None
        self._started_at: datetime | None = None
        self._ended_at: datetime | None = None
        # User-question handler (T69). Optional — set via
        # ``set_user_question_handler`` before stream_events starts.
        # When None, the runner's default sentinel reply applies.
        self._user_question_handler: (
            Callable[[Utterance], Any] | None
        ) = None

    def set_user_question_handler(
        self,
        handler: "Callable[[Utterance], Any] | None",
    ) -> None:
        """Wire an async user-question handler. The TUI's LiveRunScreen
        injects a modal-based handler here; headless callers can
        leave it None for the sentinel-reply path."""
        self._user_question_handler = handler

    # ------------------------------------------------------------------ #
    # Streaming surface — the substantive method
    # ------------------------------------------------------------------ #

    async def stream_events(self) -> AsyncIterator:  # type: ignore[override]
        """Drive the live run; yield RunEvents in chronological order
        as they happen.

        Cancellation: if the consumer's ``async for`` is cancelled
        (e.g., the LiveRunScreen worker is stopped on screen
        unmount), the finally block still runs ``runner.teardown()``
        so background threads don't leak. The stream may be
        terminated mid-meeting; consumer treats "stream stopped
        without RunEnded" as cancelled.
        """
        # Lazy imports to avoid the workflow → observer dep being
        # required at module-import time for code that doesn't run
        # live.
        from wonderland.meeting import (
            AgentActEvent,
            AgentPassEvent,
            PhaseEndEvent,
            PhaseStartEvent,
            PriorityWindowOpenEvent,
            RotationCompleteEvent,
        )
        from wonderland.workflow import (
            MeetingEndEvent,
            MeetingStartEvent,
            run_workflow,
        )

        outcome = "RUNNING"
        try:
            await self._runner.setup()
            # Wire the user-question handler if one was registered.
            # Done after setup so the runner's watcher task is alive
            # and ready to consult the handler when QUESTION-to-
            # operator utterances arrive (T69).
            if self._user_question_handler is not None and hasattr(
                self._runner, "set_user_question_handler"
            ):
                self._runner.set_user_question_handler(
                    self._user_question_handler
                )
            self._started_at = datetime.now(tz=timezone.utc)
            yield RunStarted(
                timestamp=self._started_at,
                summary=self._build_summary(),
            )

            async for event in run_workflow(
                self._workflow, self._runner, self._directive
            ):
                # workflow.MeetingStartEvent → our MeetingStarted
                if isinstance(event, MeetingStartEvent):
                    thread_id = event.thread_id or event.meeting.id
                    rm = RunMeeting(
                        id=thread_id,
                        label=event.meeting.label,
                        name=event.meeting.name,
                        started_at=datetime.now(tz=timezone.utc),
                        ended_at=None,
                        outcome=None,
                        elapsed_seconds=None,
                        calls=0,
                        cost=0.0,
                    )
                    self._meetings_buffer.append(rm)
                    self._meeting_by_thread[thread_id] = rm
                    yield MeetingStarted(
                        timestamp=rm.started_at,
                        meeting=rm,
                        thread_id=thread_id,
                        iteration_index=event.iteration_index,
                        iteration_total=event.iteration_total,
                        iteration_label=event.iteration_label,
                    )
                # workflow.MeetingEndEvent → our MeetingEnded
                elif isinstance(event, MeetingEndEvent):
                    thread_id = event.thread_id or event.meeting.id
                    now = datetime.now(tz=timezone.utc)
                    # Update buffered meeting in place so subsequent
                    # non-streaming meetings() calls return final values.
                    rm = self._meeting_by_thread.get(thread_id)
                    if rm is not None:
                        # frozen=True dataclass; replace the entry
                        from dataclasses import replace
                        updated = replace(
                            rm,
                            ended_at=now,
                            outcome=event.outcome,
                            elapsed_seconds=event.elapsed_s,
                            calls=event.calls_delta,
                            cost=event.cost_delta,
                        )
                        # Replace in both indices
                        idx = self._meetings_buffer.index(rm)
                        self._meetings_buffer[idx] = updated
                        self._meeting_by_thread[thread_id] = updated
                        meeting_for_event = updated
                    else:
                        # Shouldn't happen, but fall back to a
                        # synthesized meeting from the event.
                        meeting_for_event = RunMeeting(
                            id=thread_id,
                            label=event.meeting.label,
                            name=event.meeting.name,
                            started_at=None,
                            ended_at=now,
                            outcome=event.outcome,
                            elapsed_seconds=event.elapsed_s,
                            calls=event.calls_delta,
                            cost=event.cost_delta,
                        )
                    yield MeetingEnded(
                        timestamp=now,
                        meeting=meeting_for_event,
                        thread_id=thread_id,
                        outcome=event.outcome,
                        elapsed_seconds=event.elapsed_s,
                        calls_delta=event.calls_delta,
                        cost_delta=event.cost_delta,
                        artifact_kinds=event.artifact_kinds,
                        iteration_index=event.iteration_index,
                        iteration_total=event.iteration_total,
                        iteration_label=event.iteration_label,
                    )
                elif isinstance(event, PhaseStartEvent):
                    yield PhaseStarted(
                        timestamp=datetime.now(tz=timezone.utc),
                        meeting_thread_id=event.thread_id,
                        phase_name=event.phase.name,
                        max_rotations=event.phase.max_rotations,
                        cast=event.cast,
                        exit_condition_artifact=event.phase.exit_condition_artifact,
                    )
                elif isinstance(event, PhaseEndEvent):
                    yield PhaseEnded(
                        timestamp=datetime.now(tz=timezone.utc),
                        meeting_thread_id=event.thread_id,
                        phase_name=event.phase_name,
                        reason=event.reason,
                        rotations_used=event.rotations_used,
                        total_windows=event.total_windows,
                        passes_per_agent=event.passes_per_agent,
                        acts_per_agent=event.acts_per_agent,
                    )
                elif isinstance(event, PriorityWindowOpenEvent):
                    yield PriorityWindowOpened(
                        timestamp=datetime.now(tz=timezone.utc),
                        meeting_thread_id=event.thread_id,
                        phase_name=event.phase_name,
                        agent_id=event.agent_id,
                        rotation_index=event.rotation_index,
                        window_index_in_phase=event.window_index,
                    )
                elif isinstance(event, AgentActEvent):
                    yield AgentActed(
                        timestamp=datetime.now(tz=timezone.utc),
                        meeting_thread_id=event.thread_id,
                        phase_name=event.phase_name,
                        agent_id=event.agent_id,
                        rotation_index=event.rotation_index,
                        utterance_id=event.utterance_id,
                    )
                elif isinstance(event, AgentPassEvent):
                    yield AgentPassed(
                        timestamp=datetime.now(tz=timezone.utc),
                        meeting_thread_id=event.thread_id,
                        phase_name=event.phase_name,
                        agent_id=event.agent_id,
                        rotation_index=event.rotation_index,
                        reason=event.reason,
                    )
                elif isinstance(event, RotationCompleteEvent):
                    yield RotationCompleted(
                        timestamp=datetime.now(tz=timezone.utc),
                        meeting_thread_id=event.thread_id,
                        phase_name=event.phase_name,
                        rotation_index=event.rotation_index,
                    )
                else:
                    # Everything else is a RunnerEvent (kind-tagged).
                    kind = getattr(event, "kind", None)
                    if kind == "utterance":
                        u = event.payload.get("utterance")
                        if u is not None:
                            self._utterances_buffer.append(u)
                            yield UtteranceEmitted(
                                timestamp=u.timestamp,
                                utterance=u,
                            )
                            # ArtifactShipped events for attached
                            # artifacts that resolve to a real path.
                            for attached in u.content.artifacts or []:
                                ra = self._resolve_artifact(
                                    attached, u.timestamp
                                )
                                if ra is not None:
                                    self._artifacts_buffer.append(ra)
                                    yield ArtifactShipped(
                                        timestamp=u.timestamp,
                                        artifact=ra,
                                    )
                    elif kind == "budget_exceeded":
                        outcome = "GLOBAL_BUDGET"
                    elif kind == "timeout":
                        outcome = "TIMEOUT"
                    elif kind == "aborted":
                        outcome = "ABORTED"
                    # state, consensus_alert, telemetry, budget_warning,
                    # escalation_prompt, complete: not translated for
                    # streaming consumers in v1. Add events for these
                    # later if the live-watch UI needs them.

            # Run finished cleanly (or via a non-cancellation outcome).
            self._ended_at = datetime.now(tz=timezone.utc)
            self._final_outcome = "COMPLETE" if outcome == "RUNNING" else outcome

            # Final per-agent telemetry deltas — once each, at the
            # end of the stream. Live runs could emit these
            # periodically for a smoother cost-ticker climb; v1
            # keeps it simple and parity with HistoricalRunHandle.
            for telemetry in self.per_agent_telemetry():
                yield AgentTelemetryDelta(
                    timestamp=self._ended_at,
                    telemetry=telemetry,
                )

            yield RunEnded(
                timestamp=self._ended_at,
                summary=self._build_summary(),
            )

            # Best-effort post-run digest. Daedalus's digest module
            # reads .wonderland/ state (telemetry + lifecycle +
            # artifacts + reviews) and writes a markdown summary to
            # .wonderland/digests/run-<id>.md. Skipped silently when
            # daedalus isn't installed (it's a sister package, not a
            # hard dep) or when project_root is missing (FakeRunner
            # test fixtures, etc.).
            project_root = getattr(self._runner, "project_root", None)
            if project_root is not None:
                try:
                    from daedalus.digest import write_digest  # type: ignore

                    write_digest(project_root)
                except ImportError:
                    pass  # daedalus not installed — skip digest
                except Exception:  # noqa: BLE001
                    # Digest writes are best-effort; never fail the
                    # run because the digest can't render.
                    pass
        finally:
            # Best-effort teardown. Even on cancellation, the runner's
            # background threads / dispatcher tasks need to stop or
            # they'll leak past the screen unmount.
            try:
                await self._runner.teardown()
            except Exception:  # noqa: BLE001
                pass

    # ------------------------------------------------------------------ #
    # Non-streaming methods — snapshot accumulated state
    # ------------------------------------------------------------------ #

    def summary(self) -> RunSummary:
        return self._build_summary()

    def meetings(self) -> list[RunMeeting]:
        return list(self._meetings_buffer)

    def utterances(
        self, *, thread_id: str | None = None
    ) -> Iterator[Utterance]:
        if thread_id is None:
            yield from self._utterances_buffer
            return
        for u in self._utterances_buffer:
            if u.thread_id == thread_id:
                yield u

    def per_agent_telemetry(self) -> list[AgentTelemetry]:
        # Snapshot from runner.telemetry. The Telemetry class exposes
        # per_agent_summary() (a method, not an attribute) returning
        # the aggregated per-agent stats.
        #
        # Pre-fix this method was reading via getattr(telemetry,
        # "per_agent", {}) which silently returned {} because no such
        # attribute exists — so the live-watch's end-of-run
        # AgentTelemetryDelta events fired with empty data, leaving
        # _total_cost stuck at whatever _meeting_cost_total last
        # accumulated. In pipeline-mode runs where late MeetingEnded
        # events from concurrent lanes never bumped the meeting
        # accumulator (timing race or event-stream cancellation),
        # the displayed total stayed at the partial value (squathero2
        # design pass: \$1.88 displayed vs \$2.45 actual).
        #
        # Fallback to the legacy getattr path for any test fixture
        # that mocks a "per_agent" attribute directly without the
        # full Telemetry surface.
        telemetry = self._runner.telemetry
        if hasattr(telemetry, "per_agent_summary"):
            per_agent_data = telemetry.per_agent_summary()
        else:
            per_agent_data = getattr(telemetry, "per_agent", {})

        out: list[AgentTelemetry] = []
        for name, row in per_agent_data.items():
            if isinstance(row, dict):
                calls = int(row.get("calls", 0))
                cost = float(row.get("cost", 0.0))
            else:
                # Object-with-attributes shape (legacy / test fixtures).
                calls = int(getattr(row, "calls", 0))
                cost = float(getattr(row, "cost", 0.0))
            out.append(AgentTelemetry(name=name, calls=calls, cost=cost))
        out.sort(key=lambda a: a.cost, reverse=True)
        return out

    def artifacts(self, *, kind: str | None = None) -> list[RunArtifact]:
        if kind is None:
            return list(self._artifacts_buffer)
        return [a for a in self._artifacts_buffer if a.kind == kind]

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _build_summary(self) -> RunSummary:
        project_root = getattr(self._runner, "project_root", None)
        return RunSummary(
            run_id=None,
            workflow_name=self._workflow.name,
            directive=self._directive,
            project_root=project_root,
            started_at=self._started_at,
            ended_at=self._ended_at,
            total_cost=getattr(self._runner, "total_cost", 0.0),
            total_calls=sum(t.calls for t in self.per_agent_telemetry()),
            outcome=self._final_outcome,
        )

    def _resolve_artifact(
        self,
        attached,
        emit_ts: datetime,
    ) -> RunArtifact | None:
        """Translate a bus-attached Artifact (utterance.Artifact —
        carries kind + payload dict) into a RunArtifact (path-based).

        Returns None if the payload doesn't carry a path (rare; some
        speech acts have artifact-shaped payloads without a file
        backing). Otherwise builds a RunArtifact pointing at the
        on-disk file using the utterance's timestamp as created_at
        (the artifact handler writes the file before the bus
        notification fires, so by the time we're here the file
        should exist; if it doesn't yet, the path is still useful
        as the canonical handle).
        """
        payload = (
            attached.payload if isinstance(attached.payload, dict) else {}
        )
        raw_path = payload.get("path")
        if not raw_path:
            return None
        path = Path(raw_path)
        title = payload.get("title", path.stem)
        return RunArtifact(
            kind=attached.kind,
            path=path,
            title=str(title),
            created_at=emit_ts,
        )


__all__ = ["LiveRunHandle"]
