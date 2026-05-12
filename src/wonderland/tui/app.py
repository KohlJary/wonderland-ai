"""Top-level Textual app. Owns global state (snapshot search root,
current handle) and pushes/pops screens.

Slice A note: the App also owns the in-flight run registry
(``_active_run``) so runs can survive ``LiveRunScreen`` mount/unmount
cycles. The screen is just a subscriber; the consumer task lives
here. See ``active_run.py`` for the data structure.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from textual.app import App
from textual.binding import Binding
from textual.widgets import DataTable

from wonderland.tui.active_run import ActiveRun
from wonderland.tui.screens.project_library import ProjectLibraryScreen
from wonderland.tui.themes import (
    DEFAULT_THEME_NAME,
    WONDERLAND_THEMES,
)


# Default search root for snapshots — the analyses/data/ directory of
# whatever wonderland-ai checkout the TUI is running in. Resolved
# relative to this file's location so it works whether installed via
# `pip install -e .` or run from a fresh clone.
# Default snapshot root covers both the curated corpus
# (analyses/data/...) and any TUI-driven runs (runs/...) by
# pointing at the wonderland-ai project root. _discover_snapshots
# recursively finds both layouts (wonderland-snapshot/ for script
# runs, .wonderland/ for TUI runs).
_DEFAULT_SNAPSHOT_ROOT = Path(__file__).resolve().parents[3]


class WonderlandApp(App):
    """Wonderland TUI root.

    P11: launches into ProjectLibraryScreen as the new home. The
    SnapshotLibraryScreen remains reachable from there via the 'L'
    key for cross-project run browsing. Runs without a project still
    work via the 'r' key on ProjectLibraryScreen (back-compat).
    """

    CSS_PATH = "wonderland.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("t", "cycle_theme", "Theme", show=True),
        # App-wide vim navigation. These dispatch to whichever
        # DataTable is currently focused. Screens used to define
        # these one-by-one; centralizing here means every new
        # DataTable-based screen gets vim nav for free.
        # priority=True so they preempt ModalScreen's input capture —
        # without it, vim nav would die in the utterance modal.
        Binding("j", "vim_down", "Down", show=False, priority=True),
        Binding("k", "vim_up", "Up", show=False, priority=True),
        # Top/bottom: g/G mirrors vim's gg/G; H/L mirrors vim's
        # high/low (viewport-top, viewport-bottom). All four work
        # the same way on a flat table — jump to first/last row.
        Binding("g", "vim_top", "Top", show=False, priority=True),
        Binding("G", "vim_bottom", "Bottom", show=False, priority=True),
        Binding("H", "vim_top", "Top", show=False, priority=True),
        Binding("L", "vim_bottom", "Bottom", show=False, priority=True),
    ]

    TITLE = "Wonderland"
    SUB_TITLE = "Run inspector"

    def __init__(
        self,
        snapshot_root: Path | None = None,
        *,
        show_welcome: bool | None = None,
    ) -> None:
        """Construct the app.

        ``show_welcome`` overrides the config-based welcome-modal
        decision. ``None`` (default) reads from the user config;
        ``True`` / ``False`` force the behavior. Tests pass ``False``
        to skip the modal so screens are reachable directly.
        """
        super().__init__()
        self.snapshot_root = snapshot_root or _DEFAULT_SNAPSHOT_ROOT
        self._show_welcome_override = show_welcome
        # Slice A: in-flight run registry. Single slot for now —
        # the new-run gate enforces one-at-a-time until per-run
        # artifact tagging lands (see project_run_id_tagging memory).
        # When that work ships we'll grow this to a dict keyed by
        # run_id; the screens already think in run_id terms so the
        # widening is local.
        self._active_run: ActiveRun | None = None

    def on_mount(self) -> None:
        # Register the Wonderland-flavored themes and set the project
        # default. Built-in Textual themes (gruvbox, dracula, etc.)
        # remain available — users can `app.theme = "..."` to pick one.
        for theme in WONDERLAND_THEMES:
            self.register_theme(theme)
        self.theme = DEFAULT_THEME_NAME

        # Discover any background runs left over from a previous TUI
        # session. The detached subprocesses survive TUI exit, so on
        # startup we scan registered projects for status.json files
        # that say "running" + have a live pid. First match wins
        # (one-at-a-time cap).
        try:
            self._discover_background_runs()
        except Exception as exc:  # noqa: BLE001 — never block startup
            self.notify(
                f"Background-run discovery failed: {exc}",
                severity="warning",
                timeout=4,
            )

        # Push the project library underneath, then maybe push the
        # welcome modal on top. Welcome dismisses back to the library;
        # if the operator has already dismissed welcome (config flag),
        # we skip straight to the library.
        self.push_screen(ProjectLibraryScreen())
        if self._should_show_welcome():
            from wonderland.tui.screens.welcome_modal import WelcomeModal

            self.push_screen(WelcomeModal())

        # PyPI update check runs as a worker so the startup path
        # isn't blocked by the network round-trip. Modal only fires
        # if a newer release exists AND the operator hasn't disabled
        # the check. Skipped entirely on the welcome path so the
        # first-run user isn't double-modal'd.
        if self._should_check_updates():
            self.run_worker(
                self._check_for_updates(), exclusive=False
            )

    def _discover_background_runs(self) -> None:
        """Scan registered projects for live ``wonderland run-bg``
        subprocesses and re-register the first one we find as the
        active run. Detached subprocesses persist across TUI
        restarts; this is what makes them visible again after a
        relaunch.

        Looks for status.json with status=running + pid alive in
        each project's ``.wonderland/runs/<run_id>/``. First live
        match wins. Stale runs (status=running but pid dead) are
        flagged but not re-registered — operator can clean them up
        from the dashboard once that lands. Crashed-run cleanup
        is filed for follow-up.
        """
        from wonderland.observer.subprocess import SubprocessRunHandle
        from wonderland.project import list_projects

        try:
            projects = list_projects()
        except Exception:  # noqa: BLE001
            return
        for project in projects:
            runs_dir = project.root_path / ".wonderland" / "runs"
            if not runs_dir.is_dir():
                continue
            for run_dir in sorted(runs_dir.iterdir()):
                if not run_dir.is_dir():
                    continue
                handle = SubprocessRunHandle(run_dir)
                status = handle.status()
                if status.get("status") != "running":
                    continue
                if not handle.is_alive():
                    # Crashed — leave it for now; future cleanup
                    # path will mark status=error. Out of scope
                    # for the discovery slice.
                    continue
                # Live background run: re-register.
                run_id = run_dir.name
                active = ActiveRun(run_id=run_id, handle=handle)
                active.task = asyncio.create_task(
                    self._drive_active_run(active),
                    name=f"recovered-run-{run_id}",
                )
                # Also restart the question-poller — a recovered
                # subprocess may have a pending_question.json on
                # disk that the operator hasn't answered yet.
                active.question_poller_task = asyncio.create_task(
                    self._poll_questions_for_background_run(active),
                    name=f"recovered-question-poller-{run_id}",
                )
                self._active_run = active
                self.notify(
                    f"Recovered background run {run_id} "
                    f"(project {project.name})",
                    timeout=4,
                )
                return  # First live match wins (one-at-a-time cap)

    def _should_show_welcome(self) -> bool:
        """Decide whether to push the welcome modal on startup.

        Resolution order:
          1. Explicit constructor override (tests pass False)
          2. Config file's ui.show_welcome flag
          3. Default True (fresh installs see the welcome on first run)
        """
        if self._show_welcome_override is not None:
            return self._show_welcome_override
        try:
            from wonderland.config import load_config

            return load_config().ui.show_welcome
        except Exception:  # noqa: BLE001
            # Bad config file: still show welcome (the modal can help
            # them sort out the API key + repair the config).
            return True

    def _should_check_updates(self) -> bool:
        """Same shape as _should_show_welcome — config-driven toggle
        with a bias toward checking unless explicitly disabled. The
        check is best-effort and silent on failure so the cost of
        defaulting to True is small."""
        # Skip the check on the same path that suppresses welcome —
        # tests passing show_welcome=False expect a quiet startup.
        if self._show_welcome_override is False:
            return False
        try:
            from wonderland.config import load_config

            return load_config().ui.check_updates
        except Exception:  # noqa: BLE001
            return True

    async def _check_for_updates(self) -> None:
        """Worker coroutine: hit PyPI, surface the modal if newer."""
        from wonderland.update_check import check_for_update

        try:
            result = await asyncio.to_thread(check_for_update)
        except Exception:  # noqa: BLE001
            return
        if result is None or not result.update_available:
            return
        from wonderland.tui.screens.update_modal import UpdateAvailableModal

        self.push_screen(
            UpdateAvailableModal(
                installed=result.installed,
                latest=result.latest,
            )
        )

    # ---------------------------------------------------------------- #
    # App-wide vim navigation. Each action finds the currently focused
    # DataTable (if any) and forwards to its cursor primitive. Screens
    # whose primary widget isn't a DataTable can no-op cleanly — only
    # focused tables react. VerticalScroll widgets handle j/k natively
    # via their own bindings, so they're not affected.
    # ---------------------------------------------------------------- #

    def _focused_data_table(self) -> DataTable | None:
        widget = self.focused
        return widget if isinstance(widget, DataTable) else None

    def action_vim_down(self) -> None:
        if (table := self._focused_data_table()) is not None:
            table.action_cursor_down()

    def action_vim_up(self) -> None:
        if (table := self._focused_data_table()) is not None:
            table.action_cursor_up()

    def action_vim_top(self) -> None:
        if (table := self._focused_data_table()) is not None and table.row_count > 0:
            table.cursor_coordinate = (0, table.cursor_column)

    def action_vim_bottom(self) -> None:
        if (table := self._focused_data_table()) is not None and table.row_count > 0:
            table.cursor_coordinate = (table.row_count - 1, table.cursor_column)

    def action_quit(self) -> None:
        """Override the default Textual quit to push a confirmation
        modal first. Operator confirms with Enter / Y / clicking Quit;
        cancels with Escape / N / clicking Cancel. Without this guard,
        a stray ``q`` keystroke drops the operator out mid-session
        and loses live-watch state + dashboard cursor positions.

        If a quit modal is already on the screen stack (operator hit
        ``q`` twice), the second press confirms by re-pressing ``q``
        through the modal's binding. So the guard isn't a hard block;
        it's just one more keystroke.
        """
        from wonderland.tui.screens.quit_confirm_modal import (
            QuitConfirmModal,
        )

        # Avoid stacking multiple modals if the user mashes q.
        if isinstance(self.screen, QuitConfirmModal):
            return

        def _on_dismiss(confirmed: bool | None) -> None:
            if confirmed:
                self.exit()

        self.push_screen(QuitConfirmModal(), _on_dismiss)

    # ---------------------------------------------------------------- #
    # Active-run registry (Slice A — runs survive screen pop)
    # ---------------------------------------------------------------- #

    def launch_run(self, handle: object, run_id: str) -> ActiveRun:
        """In-process run path. Used by tests + by callers passing a
        pre-built LiveRunHandle (the legacy entry that the
        background-run subprocess path is replacing).

        Wires the App's user-question handler onto the handle and
        spawns the consumer task. The run survives screen pops but
        dies with the App's event loop (TUI exit kills it).

        For runs that should survive TUI exit, use
        ``launch_background_run`` — it spawns ``wonderland run-bg``
        as a detached subprocess.

        Raises RuntimeError if an active run is already in flight.
        """
        if self._active_run is not None and not self._active_run.is_terminal:
            raise RuntimeError(
                f"a run is already in flight: {self._active_run.run_id}"
            )
        # Wire the global question handler before the consumer task
        # starts — LiveRunHandle.stream_events sets the runner's
        # handler once at stream entry, so we have to bind the
        # callable up-front. Mock-turtle / historical handles don't
        # have a runner to call so the hasattr guard short-circuits.
        if hasattr(handle, "set_user_question_handler"):
            handle.set_user_question_handler(  # type: ignore[attr-defined]
                self._handle_user_question
            )
        active = ActiveRun(run_id=run_id, handle=handle)
        active.task = asyncio.create_task(
            self._drive_active_run(active),
            name=f"active-run-{run_id}",
        )
        self._active_run = active
        return active

    def launch_background_run(
        self,
        *,
        directive: str,
        workflow_name: str,
        project_root: Path,
        budget: float,
        model: str | None = None,
        run_id: str | None = None,
        auto_merge: bool = False,
    ) -> ActiveRun:
        """Spawn ``wonderland run-bg`` as a detached subprocess and
        register a SubprocessRunHandle as the active run.

        The subprocess lives in its own process group (``start_new_
        session=True``) so it survives this app's exit. The handle
        tails the run's events.jsonl + status.json on disk; the
        consumer task pulls from that handle and fans out to
        screen subscribers.

        Returns the ActiveRun. Raises RuntimeError on the
        one-at-a-time cap.

        ``run_id`` is optional — when omitted, we generate a
        timestamp-style id matching the runner's own format so the
        subprocess and TUI agree on the run dir path. The
        subprocess will use whatever id the Runner generates for
        itself; that wins as the canonical id (we read it back from
        status.json after the subprocess writes it).
        """
        import subprocess
        import sys
        from datetime import datetime, timezone

        from wonderland.observer.subprocess import SubprocessRunHandle

        if self._active_run is not None and not self._active_run.is_terminal:
            raise RuntimeError(
                f"a run is already in flight: {self._active_run.run_id}"
            )

        # Generate the run id ourselves so we know the run dir path
        # before the subprocess writes anything to it. The Runner
        # will use whatever timestamp it computes inside the
        # subprocess; if our generated id and the Runner's diverge
        # by a second, the discovery path scans for the actual dir
        # by status.json contents.
        if run_id is None:
            run_id = datetime.now(tz=timezone.utc).strftime(
                "%Y%m%dT%H%M%S"
            )

        run_dir = (
            project_root / ".wonderland" / "runs" / run_id
        )
        run_dir.mkdir(parents=True, exist_ok=True)

        log_path = run_dir / "log"
        log_handle = log_path.open("ab")

        cmd = [
            sys.executable,
            "-m",
            "wonderland.cli",
            "run-bg",
            directive,
            "--workflow",
            workflow_name,
            "--project-root",
            str(project_root),
            "--budget",
            str(budget),
            "--run-id",
            run_id,
        ]
        if model is not None:
            cmd.extend(["--model", model])
        if auto_merge:
            cmd.append("--auto-merge")

        proc = subprocess.Popen(  # noqa: S603 — args list is built locally, no shell
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=log_handle,
            stderr=log_handle,
            start_new_session=True,
            cwd=str(project_root),
        )
        # Close our copy of the log fd; the subprocess inherits its
        # own. Without this, killing the subprocess wouldn't free
        # the file handle until the App exits.
        log_handle.close()

        # The subprocess uses --run-id to write into our
        # pre-created run_dir, so the SubprocessRunHandle tails
        # the right files from the start.
        handle = SubprocessRunHandle(run_dir)
        active = ActiveRun(run_id=run_id, handle=handle)
        active.subprocess_pid = proc.pid  # type: ignore[attr-defined]
        active.task = asyncio.create_task(
            self._drive_active_run(active),
            name=f"active-run-{run_id}",
        )
        # Background runs use a disk-mediated operator-question
        # bridge: the subprocess writes pending_question.json and
        # blocks reading pending_answer.json. We poll for the
        # question file, push AskUserModal when one appears, write
        # the operator's reply (or None on skip) to pending_answer.
        active.question_poller_task = asyncio.create_task(
            self._poll_questions_for_background_run(active),
            name=f"question-poller-{run_id}",
        )
        self._active_run = active
        return active

    async def _handle_user_question(self, question_utterance) -> str | None:
        """Global QUESTION-to-operator handler. Pushes AskUserModal
        regardless of which screen is currently mounted, so a question
        from a background run surfaces even when the operator left
        the live-watch screen.

        Returns the operator's reply text, or None on skip — the
        runner's user-question watcher publishes a sentinel
        observation on None so the team can proceed without the
        operator's input.
        """
        import asyncio

        from wonderland.tui.screens.ask_user_modal import AskUserModal

        future: asyncio.Future[str | None] = asyncio.Future()

        def _on_dismissed(answer: str | None) -> None:
            if not future.done():
                future.set_result(answer)

        # Pull suggested options off the question utterance's
        # artifacts (kind="operator_question_options"). Same shape
        # the screen-level handler reads.
        options: list[str] = []
        for artifact in question_utterance.content.artifacts:
            if artifact.kind == "operator_question_options":
                raw = artifact.payload.get("options", [])
                if isinstance(raw, list):
                    options = [str(o) for o in raw if o]
                break

        self.push_screen(
            AskUserModal(
                asking_agent=question_utterance.speaker.name,
                question=question_utterance.content.body,
                options=options,
            ),
            _on_dismissed,
        )
        return await future

    async def _drive_active_run(self, active: ActiveRun) -> None:
        """Consume the active run's stream into its buffer + fan out
        to subscribers. Sets ``status`` based on stream completion vs.
        cancellation vs. exception.

        Cancellation safety: if the task is cancelled (e.g., app
        shutdown), the handle's stream_events finally block still
        runs — runner teardown happens once, regardless of who
        cancelled it.
        """
        try:
            async for event in active.handle.stream_events():
                active._ingest(event)
            active.mark_ended("complete")
        except asyncio.CancelledError:
            active.mark_ended("aborted")
            raise
        except Exception:  # noqa: BLE001
            active.mark_ended("error")
            # Re-raise so the task surface in stderr still flags the
            # exception; the buffer + status tell the UI what
            # happened without depending on this raise.
            raise

    async def _poll_questions_for_background_run(
        self, active: ActiveRun
    ) -> None:
        """Background-run operator-question bridge.

        The subprocess writes ``pending_question.json`` to its run
        dir when an agent fires QUESTION-to-operator, then blocks
        reading ``pending_answer.json``. This task polls for the
        question file, pushes ``AskUserModal`` when one appears,
        and writes the operator's reply (or None on skip) to the
        answer file. The subprocess reads it and continues.

        Each question carries a uuid ``question_id`` so the
        subprocess can distinguish its own answer from any stale
        answer file that might be lying around (defensive against
        crashes mid-question).

        Lifecycle: runs until the active run is terminal. Cleans
        up on cancellation so the App can shut down without
        leaking poller tasks.
        """
        import json

        run_dir = getattr(active.handle, "run_dir", None)
        if run_dir is None:
            return  # In-process handle — uses its own handler.
        question_path = run_dir / "pending_question.json"
        answer_path = run_dir / "pending_answer.json"
        seen_ids: set[str] = set()
        try:
            while not active.is_terminal:
                await asyncio.sleep(0.5)
                if not question_path.is_file():
                    continue
                try:
                    data = json.loads(
                        question_path.read_text(encoding="utf-8")
                    )
                except (OSError, json.JSONDecodeError):
                    continue
                qid = data.get("question_id")
                if not isinstance(qid, str) or qid in seen_ids:
                    continue
                seen_ids.add(qid)
                await self._surface_background_question(
                    answer_path, qid, data
                )
        except asyncio.CancelledError:
            raise

    async def _surface_background_question(
        self,
        answer_path: "Path",  # noqa: F821 — Path is imported at module top
        question_id: str,
        question_data: dict,
    ) -> None:
        """Push AskUserModal for a subprocess-side question and
        write the operator's response (or None on skip) to
        ``answer_path`` once the modal dismisses. The subprocess
        polls for the file and unblocks when it sees the matching
        ``question_id``."""
        import json

        from wonderland.tui.screens.ask_user_modal import AskUserModal

        future: asyncio.Future[str | None] = asyncio.Future()

        def _on_dismissed(answer: str | None) -> None:
            if not future.done():
                future.set_result(answer)

        options = question_data.get("options") or []
        if not isinstance(options, list):
            options = []
        self.push_screen(
            AskUserModal(
                asking_agent=str(
                    question_data.get("asking_agent")
                    or "(unknown agent)"
                ),
                question=str(
                    question_data.get("question") or "(no question)"
                ),
                options=[str(o) for o in options],
            ),
            _on_dismissed,
        )
        answer = await future
        # Write answer back. Subprocess polls + cleans up both
        # files on its side. We write atomically (write-then-no-
        # rename is fine because the subprocess reads via
        # read_text, retrying on JSONDecodeError; one half-written
        # answer round-trips through the next poll cycle).
        try:
            answer_path.write_text(
                json.dumps({
                    "question_id": question_id,
                    "answer": answer,
                }),
                encoding="utf-8",
            )
        except OSError as exc:
            self.notify(
                f"Failed to deliver operator answer to background "
                f"run: {exc}",
                severity="error",
                timeout=6,
            )

    def get_active_run(self, run_id: str) -> ActiveRun | None:
        """Look up an active run by run_id. Returns None when no run
        is in flight or when the run_id doesn't match. Used by
        LiveRunScreen on mount to decide attach-vs-fallback."""
        if self._active_run is None:
            return None
        if self._active_run.run_id != run_id:
            return None
        return self._active_run

    def has_active_run(self) -> bool:
        """True when there's an in-flight run. Used by NewRunScreen
        to gate the one-at-a-time cap and by QuitConfirmModal to
        warn before exit."""
        return (
            self._active_run is not None
            and not self._active_run.is_terminal
        )

    def abort_active_run(self, *, reason: str | None = None) -> bool:
        """Abort the active run via the appropriate channel:
          - SubprocessRunHandle → SIGTERM the subprocess pid.
          - LiveRunHandle (in-process) → call runner.abort.

        Returns True on success, False if no active run or the
        abort itself failed."""
        if self._active_run is None or self._active_run.is_terminal:
            return False
        handle = self._active_run.handle
        if hasattr(handle, "abort"):
            return bool(handle.abort(reason=reason))  # type: ignore[attr-defined]
        runner = getattr(handle, "_runner", None)
        if runner is not None and hasattr(runner, "abort"):
            try:
                runner.abort(reason=reason or "operator abort")
                return True
            except Exception:  # noqa: BLE001
                return False
        return False

    def clear_terminal_run(self) -> None:
        """Drop the registry slot when the active run has ended.
        Called by the operator's "go again" path so a finished run
        doesn't keep blocking new launches. Safe to call if no run
        exists; safe to call mid-run (no-ops, doesn't kill it)."""
        if self._active_run is not None and self._active_run.is_terminal:
            self._active_run = None

    def action_cycle_theme(self) -> None:
        """htop-style theme cycling: advance to the next Wonderland
        theme, wrapping at the end. Notifies which theme is now active
        so the swap is legible without staring at the palette."""
        names = [t.name for t in WONDERLAND_THEMES]
        if self.theme in names:
            idx = names.index(self.theme)
            next_name = names[(idx + 1) % len(names)]
        else:
            # User picked a built-in theme; rejoin the cycle at the start.
            next_name = names[0]
        self.theme = next_name
        # Strip the "wonderland-" prefix in the notification — the
        # branded shorthand is the legible part.
        short = next_name.removeprefix("wonderland-").replace("-", " ").title()
        self.notify(f"Theme: {short}", timeout=2)


def main() -> int:
    """Entry point for `wonderland-tui` CLI."""
    WonderlandApp().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
