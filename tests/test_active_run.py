"""Tests for ``wonderland.tui.active_run`` — the App-level run
registry data structure that lets runs survive ``LiveRunScreen``
mount/unmount cycles."""

from __future__ import annotations

import asyncio

import pytest

from wonderland.tui.active_run import ActiveRun


def test_active_run_buffers_events_and_replays_on_subscribe() -> None:
    """A subscriber that registers after events have been ingested
    sees them in order via the replay path. This is the "operator
    pops live screen mid-run, then opens it again" case."""
    active = ActiveRun(run_id="20260510T140000", handle=object())
    active._ingest("event-1")
    active._ingest("event-2")

    seen: list[str] = []
    active.subscribe(seen.append)

    assert seen == ["event-1", "event-2"]


def test_active_run_fans_out_new_events_to_subscribers() -> None:
    """Subscribers also see events that arrive after they
    register — the tail behavior."""
    active = ActiveRun(run_id="run-1", handle=object())
    seen: list[str] = []
    active.subscribe(seen.append)

    active._ingest("hello")
    active._ingest("world")

    assert seen == ["hello", "world"]


def test_active_run_unsubscribe_stops_fanout() -> None:
    """Calling the returned unsubscribe handle removes the callback
    from future fanouts. Past replays are not undone."""
    active = ActiveRun(run_id="run-1", handle=object())
    seen: list[str] = []
    unsub = active.subscribe(seen.append)
    active._ingest("a")
    unsub()
    active._ingest("b")

    assert seen == ["a"]


def test_active_run_subscriber_error_doesnt_kill_fanout() -> None:
    """A misbehaving subscriber that raises shouldn't poison the
    feed for other subscribers. Errors swallowed silently — caller
    is responsible for diagnostics."""
    active = ActiveRun(run_id="run-1", handle=object())
    crashed: list[str] = []
    healthy: list[str] = []

    def crashing(event: str) -> None:
        crashed.append(event)
        raise RuntimeError("oops")

    active.subscribe(crashing)
    active.subscribe(healthy.append)
    active._ingest("event")

    assert crashed == ["event"]
    assert healthy == ["event"]


def test_active_run_status_lifecycle() -> None:
    """``mark_ended`` flips status + sets ended_at; is_terminal
    matches the distinction the App uses to gate new-run launches.
    """
    active = ActiveRun(run_id="run-1", handle=object())
    assert active.status == "running"
    assert not active.is_terminal

    active.mark_ended("complete")

    assert active.status == "complete"
    assert active.is_terminal
    assert active.ended_at is not None


@pytest.mark.asyncio
async def test_app_launch_run_drives_consumer_task() -> None:
    """Smoke test the App's run registry: ``launch_run`` spawns the
    consumer task that drains the handle's stream into the buffer.
    Uses a fake handle that yields a fixed event sequence so we
    don't need a real Runner."""
    from wonderland.tui import WonderlandApp

    class FakeHandle:
        async def stream_events(self):
            yield "first"
            yield "second"
            yield "third"

        def meetings(self):
            return []

        def set_user_question_handler(self, _h):
            pass

    app = WonderlandApp(show_welcome=False)
    async with app.run_test() as pilot:
        await pilot.pause()
        active = app.launch_run(FakeHandle(), run_id="20260510T140000")
        # Wait for the consumer task to drain — task ends when stream
        # exhausts. Defensive timeout so a hung task doesn't hang
        # the test.
        await asyncio.wait_for(active.task, timeout=2.0)

        assert active.buffer == ["first", "second", "third"]
        assert active.status == "complete"
        assert app.has_active_run() is False
        assert app.get_active_run("20260510T140000") is not None
        # Status moved to terminal — a fresh launch is now permitted
        # after clear_terminal_run.
        app.clear_terminal_run()
        assert app.get_active_run("20260510T140000") is None
        await pilot.press("q")


@pytest.mark.asyncio
async def test_live_run_screen_attaches_via_run_id_and_replays_buffer() -> None:
    """Slice A integration: launch a run on the App, push
    LiveRunScreen(run_id=...), verify the screen subscribes and the
    buffered events flow through. Then pop the screen — the run
    must keep going (consumer task still active, run still in
    registry)."""
    from wonderland.tui import WonderlandApp
    from wonderland.tui.screens.live_run import LiveRunScreen

    drained = asyncio.Event()

    class TwoEventHandle:
        async def stream_events(self):
            # Yield two cheap events the screen can dispatch
            # without crashing. We don't care about screen state
            # updates — only that the subscription path fires.
            yield "first-event"
            yield "second-event"
            # Signal completion before the generator ends so the
            # test can synchronize on the consumer being done.
            drained.set()

        def meetings(self):
            return []

        def set_user_question_handler(self, _h):
            pass

    app = WonderlandApp(show_welcome=False)
    async with app.run_test() as pilot:
        await pilot.pause()
        active = app.launch_run(TwoEventHandle(), run_id="run-x")
        # Wait until the consumer drains both events into the buffer.
        await asyncio.wait_for(drained.wait(), timeout=2.0)
        # Push the live screen with the run_id; it should pick up
        # the active run and subscribe.
        app.push_screen(LiveRunScreen(run_id="run-x"))
        await pilot.pause()
        # The screen's _unsubscribe should be set (= subscription
        # registered). It receives the buffered events synchronously
        # during ActiveRun.subscribe.
        assert app.screen is not None
        screen = app.screen
        assert isinstance(screen, LiveRunScreen)
        assert screen._unsubscribe is not None
        # Pop the screen; the run must keep going.
        await pilot.press("escape")
        await pilot.pause()
        # Buffer survives; consumer task survives (it's already
        # complete in this test, but the registry still holds it).
        assert active.buffer == ["first-event", "second-event"]
        await pilot.press("q")


@pytest.mark.asyncio
async def test_app_launch_run_rejects_concurrent_launches() -> None:
    """The one-at-a-time cap: launching a second run while the first
    is still in flight raises RuntimeError. NewRunScreen surfaces
    this as a notify; tests + Slice B's Go button gating depend on
    this behavior."""
    from wonderland.tui import WonderlandApp

    class HangingHandle:
        async def stream_events(self):
            # Never yield; never complete — simulates an in-flight run
            await asyncio.Event().wait()
            yield "unreachable"

        def meetings(self):
            return []

        def set_user_question_handler(self, _h):
            pass

    app = WonderlandApp(show_welcome=False)
    async with app.run_test() as pilot:
        await pilot.pause()
        first = app.launch_run(HangingHandle(), run_id="run-a")
        try:
            with pytest.raises(RuntimeError, match="already in flight"):
                app.launch_run(HangingHandle(), run_id="run-b")
        finally:
            # Cancel the hanging task so the test exits cleanly.
            if first.task is not None:
                first.task.cancel()
                with pytest.raises(
                    (asyncio.CancelledError, BaseException)
                ):
                    await first.task
        await pilot.press("q")


@pytest.mark.asyncio
async def test_app_launch_run_sets_global_user_question_handler() -> None:
    """Slice B: the App wires its global question handler onto
    the LiveRunHandle before the consumer task starts, so questions
    surface as AskUserModal regardless of which screen is mounted."""
    from wonderland.tui import WonderlandApp

    bound: list = []

    class CapturingHandle:
        async def stream_events(self):
            # Never produces events; just a hook for the handler binding.
            await asyncio.Event().wait()
            yield "unreachable"

        def meetings(self):
            return []

        def set_user_question_handler(self, handler):
            bound.append(handler)

    app = WonderlandApp(show_welcome=False)
    async with app.run_test() as pilot:
        await pilot.pause()
        active = app.launch_run(CapturingHandle(), run_id="run-q")
        try:
            assert len(bound) == 1
            # The bound handler is the App's _handle_user_question
            # — bound method, same instance.
            assert bound[0].__func__ is app._handle_user_question.__func__
        finally:
            if active.task is not None:
                active.task.cancel()
                with pytest.raises(
                    (asyncio.CancelledError, BaseException)
                ):
                    await active.task
        await pilot.press("q")


@pytest.mark.asyncio
async def test_app_discovers_live_background_run_on_startup(
    monkeypatch, tmp_path
) -> None:
    """On TUI startup the App scans registered projects for
    .wonderland/runs/<run_id>/status.json with status=running +
    pid alive, and re-registers the first match as the active
    run. This is what makes detached background runs visible
    again after a TUI restart."""
    import json
    import os
    from pathlib import Path

    from wonderland.project import (
        Project,
        register_project,
    )
    from wonderland.tui import WonderlandApp

    # Pre-register a project with a fake live background run on disk.
    monkeypatch.setenv("WONDERLAND_HOME", str(tmp_path / ".wonderland"))
    project_root = tmp_path / "alpha"
    run_id = "20260510T140000"
    run_dir = project_root / ".wonderland" / "runs" / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")
    (run_dir / "pid").write_text(f"{os.getpid()}\n")  # test pid is alive
    (run_dir / "status.json").write_text(json.dumps({
        "status": "running",
        "run_id": run_id,
        "started_at": "2026-05-10T14:00:00+00:00",
        "ended_at": None,
        "meetings_completed": 1,
        "total_cost": 0.10,
        "pid": os.getpid(),
        "workflow": "smoke-ask-user",
        "directive": "test",
    }), encoding="utf-8")
    register_project(Project(name="alpha", root_path=project_root))

    app = WonderlandApp(show_welcome=False)
    async with app.run_test() as pilot:
        await pilot.pause()
        # Discovery runs on on_mount. The recovered run is now
        # registered as the active run — same shape that
        # launch_background_run produces.
        assert app._active_run is not None
        assert app._active_run.run_id == run_id
        # Cancel the consumer task so the test exits cleanly
        # (the events file is empty + status=running, so the
        # tail loop would otherwise sit forever).
        if app._active_run.task is not None:
            app._active_run.task.cancel()
            try:
                await app._active_run.task
            except (asyncio.CancelledError, BaseException):
                pass
        await pilot.press("q")


@pytest.mark.asyncio
async def test_dashboard_renders_live_row_when_active_run_present() -> None:
    """Slice B: when an active run exists, the dashboard's runs
    column shows a synthetic ▶ live row at the top alongside any
    historical RunRecords on disk."""
    from textual.widgets import DataTable

    from wonderland.project import (
        Project,
        register_project,
        load_project,
    )
    from wonderland.tui import WonderlandApp
    from wonderland.tui.active_run import ActiveRun
    from wonderland.tui.screens.project_dashboard import (
        ProjectDashboardScreen,
    )

    class HangingHandle:
        async def stream_events(self):
            await asyncio.Event().wait()
            yield "unreachable"

        def meetings(self):
            return []

        def set_user_question_handler(self, _h):
            pass

    import os
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        os.environ["WONDERLAND_HOME"] = str(td) + "/.wonderland"
        root = os.path.join(td, "alpha")
        os.makedirs(root)
        register_project(Project(name="alpha", root_path=root))
        project = load_project("alpha")

        app = WonderlandApp(show_welcome=False)
        async with app.run_test() as pilot:
            await pilot.pause()
            # Inject an active run so the dashboard sees it.
            app._active_run = ActiveRun(
                run_id="20260510T140000",
                handle=HangingHandle(),
            )
            app.push_screen(ProjectDashboardScreen(project))
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, ProjectDashboardScreen)
            table = screen.query_one("#runs-table", DataTable)
            # Active row is the only one (no historical telemetry
            # files were created in this fixture).
            assert table.row_count == 1
            # Slice B flag set so the row-selected handler routes
            # to reattach instead of HistoricalRunHandle.
            assert screen._active_row_present is True
            await pilot.press("escape")
            await pilot.press("q")
