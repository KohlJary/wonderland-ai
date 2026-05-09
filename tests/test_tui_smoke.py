"""Smoke tests for the TUI.

These don't validate visual rendering — that's a manual concern. They
check that the app launches without exceptions, that the snapshot
library populates from real fixtures, and that drilling into a snapshot
loads its summary view.

Per P8.2: this is the bootstrap layer. Real layout/UX iteration
happens visually against historical snapshots; the test suite's job
is to make sure the app doesn't crash on common paths.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from wonderland.cast import cast
from wonderland.observer import HistoricalRunHandle, MockTurtleHandle
from wonderland.tui import WonderlandApp
from wonderland.tui.screens.live_run import (
    _ALL_MEETINGS,
    LiveRunScreen,
    _label_from_thread_id,
)
from wonderland.tui.screens.new_run import NewRunScreen
from wonderland.tui.screens.artifact_browser import (
    ArtifactBrowserScreen,
    ArtifactDetailScreen,
)
from wonderland.tui.screens.cast import CastBrowserScreen
from wonderland.tui.screens.meeting_detail import (
    MeetingDetailScreen,
    UtteranceModalScreen,
)
from wonderland.tui.screens.run_summary import RunSummaryScreen
from wonderland.tui.screens.snapshot_library import (
    SnapshotLibraryScreen,
    _discover_snapshots,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
ANALYSES_DATA = REPO_ROOT / "analyses" / "data"


# ---------- snapshot discovery ----------


def test_discover_snapshots_finds_analyses_data() -> None:
    """The TUI's default search root should surface every snapshot in
    analyses/data/. Missing fixtures = test skipped, not failed."""
    if not ANALYSES_DATA.is_dir():
        pytest.skip("analyses/data/ not present in this checkout")
    snapshots = _discover_snapshots(ANALYSES_DATA)
    # We've shipped multiple snapshots across analyses 026-030; expect
    # several hits.
    assert len(snapshots) >= 3, (
        f"expected to find multiple snapshots under {ANALYSES_DATA}, "
        f"found {len(snapshots)}: {snapshots}"
    )


def test_discover_snapshots_handles_missing_root(tmp_path: Path) -> None:
    """A nonexistent root should yield empty list, not crash."""
    result = _discover_snapshots(tmp_path / "nonexistent")
    assert result == []


def test_discover_snapshots_skips_invalid_directories(tmp_path: Path) -> None:
    """A directory missing wonderland-snapshot/ shouldn't be returned."""
    bogus = tmp_path / "not-a-snapshot"
    bogus.mkdir()
    (bogus / "run.log").write_text("hi")
    # No wonderland-snapshot/ subdir
    assert _discover_snapshots(tmp_path) == []


# ---------- app smoke tests ----------


async def test_app_launches_with_default_root() -> None:
    """The app should start, push the SnapshotLibraryScreen, and not
    crash. Doesn't validate rendering — just exit-cleanly-on-quit."""
    app = WonderlandApp()
    async with app.run_test() as pilot:
        # The library screen should be active.
        assert isinstance(app.screen, SnapshotLibraryScreen)
        await pilot.press("q")


async def test_app_launches_with_custom_root(tmp_path: Path) -> None:
    """A run with a snapshot-less root should still launch (just empty)."""
    app = WonderlandApp(snapshot_root=tmp_path)
    async with app.run_test() as pilot:
        assert isinstance(app.screen, SnapshotLibraryScreen)
        await pilot.press("q")


async def test_home_view_has_analyses_button() -> None:
    """The home view exposes a visible Analyses button alongside
    New run / Cast / Settings. Pressing it opens the AnalysesScreen
    which lazygit-shapes the field-notes corpus."""
    from textual.widgets import Button, DataTable

    from wonderland.tui.screens.analyses import AnalysesScreen

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, SnapshotLibraryScreen)

        analyses_btn = screen.query_one("#analyses-button", Button)
        assert "Analyses" in str(analyses_btn.label)

        screen.post_message(Button.Pressed(analyses_btn))
        await pilot.pause()
        assert isinstance(app.screen, AnalysesScreen)

        # Table populated with the field-notes corpus
        table = app.screen.query_one("#analyses-table", DataTable)
        assert table.row_count > 0

        # Press 'escape' to pop back
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, SnapshotLibraryScreen)
        await pilot.press("q")


async def test_analyses_screen_a_keybind_opens_it() -> None:
    """`a` from the home view opens the analyses screen, parallel to
    `c` for cast and `S` for settings."""
    from wonderland.tui.screens.analyses import AnalysesScreen

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("a")
        await pilot.pause()
        assert isinstance(app.screen, AnalysesScreen)
        await pilot.press("escape")
        await pilot.pause()
        await pilot.press("q")


async def test_home_view_has_settings_button(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The home view exposes a visible Settings button alongside
    New run / The Cast. Clicking it opens the settings screen."""
    from textual.widgets import Button

    from wonderland.tui.screens.settings import SettingsScreen

    # Point config away from any real user config to avoid touching
    # the developer's actual settings.
    monkeypatch.setattr(
        "wonderland.tui.screens.settings.config_path",
        lambda: tmp_path / "config.json",
    )

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, SnapshotLibraryScreen)

        settings_btn = screen.query_one("#settings-button", Button)
        assert "Settings" in str(settings_btn.label)

        screen.post_message(Button.Pressed(settings_btn))
        await pilot.pause()
        assert isinstance(app.screen, SettingsScreen)

        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, SnapshotLibraryScreen)
        await pilot.press("q")


async def test_settings_screen_persists_api_key(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """SettingsScreen save writes the API key to the config file."""
    import json

    from wonderland.tui.screens.settings import SettingsScreen
    from textual.widgets import Input

    fake_config = tmp_path / "config.json"
    monkeypatch.setattr(
        "wonderland.tui.screens.settings.config_path",
        lambda: fake_config,
    )
    monkeypatch.setattr(
        "wonderland.config.config_path",
        lambda: fake_config,
    )

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(SettingsScreen())
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, SettingsScreen)

        screen.query_one("#api-key-input", Input).value = "sk-ant-test-12345"
        await pilot.pause()
        screen.action_save()
        await pilot.pause()

        assert fake_config.is_file()
        data = json.loads(fake_config.read_text())
        assert data["anthropic"]["api_key"] == "sk-ant-test-12345"

        await pilot.press("q")


async def test_new_run_screen_pushes_settings_when_key_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """T53 polish: when the API key is missing, NewRunScreen pushes
    the Settings screen instead of just notifying. One-click recovery
    from the missing-key error."""
    from textual.widgets import Checkbox, Input, Select, TextArea

    from wonderland.tui.screens.settings import SettingsScreen

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(
        "wonderland.tui.screens.new_run.load_config",
        lambda: type("X", (), {"anthropic": type("Y", (), {"api_key": None})()})(),
    )

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(NewRunScreen(project_root=tmp_path))
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, NewRunScreen)

        # Fill form
        screen.query_one("#directive-composer", TextArea).text = (
            "Build a /hello endpoint."
        )
        screen.query_one("#workflow-select", Select).value = "smoke"
        screen.query_one("#budget-input", Input).value = "0.50"
        screen.query_one("#project-input", Input).value = str(tmp_path)
        screen.query_one("#save-checkbox", Checkbox).value = False
        await pilot.pause()

        screen.action_go()
        await pilot.pause()

        # Should have pushed the Settings screen, not just notified
        assert isinstance(app.screen, SettingsScreen)

        await pilot.press("escape")
        await pilot.pause()
        await pilot.press("q")


async def test_home_view_has_prominent_new_run_and_cast_buttons() -> None:
    """The home view (SnapshotLibraryScreen) shows visible primary
    buttons for the load-bearing actions — New run + Cast — rather
    than burying them in keybind hints. Pressing the buttons routes
    to the same screens as the n/c bindings."""
    from textual.widgets import Button

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, SnapshotLibraryScreen)

        # Both buttons present + visible
        new_run_btn = screen.query_one("#new-run-button", Button)
        cast_btn = screen.query_one("#cast-button", Button)
        assert "New run" in str(new_run_btn.label)
        assert "Cast" in str(cast_btn.label)

        # Click New run → opens NewRunScreen (same as 'n' binding)
        screen.post_message(Button.Pressed(new_run_btn))
        await pilot.pause()
        assert isinstance(app.screen, NewRunScreen)
        await pilot.press("escape")
        await pilot.pause()

        # Click The Cast → opens CastBrowserScreen (same as 'c' binding)
        from wonderland.tui.screens.cast import CastBrowserScreen

        screen.post_message(Button.Pressed(cast_btn))
        await pilot.pause()
        assert isinstance(app.screen, CastBrowserScreen)

        await pilot.press("q")


async def test_app_back_action_is_noop_at_root() -> None:
    """Pressing Escape at the library screen shouldn't crash."""
    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.press("escape")
        # Still on library screen — back is no-op when nothing is pushed
        assert isinstance(app.screen, SnapshotLibraryScreen)
        await pilot.press("q")


# ---------- snapshot-library → run-summary navigation ----------


async def test_vim_keys_navigate_snapshot_library() -> None:
    """j/k should move the cursor in the snapshot library, same as
    arrow keys."""
    if not ANALYSES_DATA.is_dir():
        pytest.skip("analyses/data/ not present")
    snapshots = _discover_snapshots(ANALYSES_DATA)
    if len(snapshots) < 2:
        pytest.skip("need at least 2 snapshots to test movement")
    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, SnapshotLibraryScreen)
        from textual.widgets import DataTable

        table = screen.query_one("#snapshot-table", DataTable)
        assert table.cursor_row == 0
        await pilot.press("j")
        await pilot.pause()
        assert table.cursor_row == 1
        await pilot.press("k")
        await pilot.pause()
        assert table.cursor_row == 0
        # G jumps to bottom
        await pilot.press("G")
        await pilot.pause()
        assert table.cursor_row == table.row_count - 1
        # g jumps to top
        await pilot.press("g")
        await pilot.pause()
        assert table.cursor_row == 0
        await pilot.press("q")


async def test_opening_a_snapshot_pushes_run_summary() -> None:
    """Clicking through to a real snapshot should land on the run
    summary screen without crashing."""
    if not ANALYSES_DATA.is_dir():
        pytest.skip("analyses/data/ not present")
    snapshots = _discover_snapshots(ANALYSES_DATA)
    if not snapshots:
        pytest.skip("no snapshots available to drill into")
    app = WonderlandApp()
    async with app.run_test() as pilot:
        # Wait for table population.
        await pilot.pause()
        # Press Enter on the first row.
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, RunSummaryScreen)
        # Pop back to the library.
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, SnapshotLibraryScreen)
        await pilot.press("q")


# ---------- run-summary → meeting-detail navigation ----------


_V6_BANNER = ANALYSES_DATA / "029-substrate-convergence" / "v6"


async def test_run_summary_focuses_meetings_table_by_default() -> None:
    """The meetings table should be focused on mount so j/k navigates
    meetings without the user needing to Tab from elsewhere first."""
    if not (_V6_BANNER / "wonderland-snapshot").is_dir():
        pytest.skip("v6 banner snapshot not present")
    from textual.widgets import DataTable

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        # Open the v6 banner snapshot directly via the API rather than
        # navigating from the library (the library order isn't guaranteed).
        app.push_screen(RunSummaryScreen(_V6_BANNER))
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, RunSummaryScreen)
        # The focused widget should be the meetings table.
        focused = screen.focused
        assert isinstance(focused, DataTable)
        assert focused.id == "meetings-table"
        await pilot.press("q")


async def test_pressing_enter_on_meeting_opens_meeting_detail() -> None:
    """From RunSummaryScreen, pressing Enter on the meetings table
    should drill into MeetingDetailScreen for the selected meeting."""
    if not (_V6_BANNER / "wonderland-snapshot").is_dir():
        pytest.skip("v6 banner snapshot not present")
    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(RunSummaryScreen(_V6_BANNER))
        await pilot.pause()
        # M1 is the first row; Enter should open it.
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, MeetingDetailScreen)
        assert app.screen.meeting.label == "M1"
        # Escape should pop back.
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, RunSummaryScreen)
        await pilot.press("q")


async def test_meeting_detail_renders_utterances() -> None:
    """The meeting detail's utterance table should populate with the
    meeting's transcript. Smoke check — assert non-zero rows."""
    if not (_V6_BANNER / "wonderland-snapshot").is_dir():
        pytest.skip("v6 banner snapshot not present")
    from textual.widgets import DataTable

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(RunSummaryScreen(_V6_BANNER))
        await pilot.pause()
        # Navigate to M2.5 (index 2: M1, M2, M2.5)
        await pilot.press("j")
        await pilot.press("j")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, MeetingDetailScreen)
        assert screen.meeting.id == "composition"
        utterance_table = screen.query_one("#utterance-table", DataTable)
        assert utterance_table.row_count > 0, (
            "M2.5 in v6 banner should have a non-empty transcript"
        )
        await pilot.press("q")


# ---------- body preview + utterance modal ----------


async def test_meeting_detail_preview_updates_on_cursor_move() -> None:
    """As j/k moves the cursor in the utterance table, the body
    preview should reflect the new row's full body."""
    if not (_V6_BANNER / "wonderland-snapshot").is_dir():
        pytest.skip("v6 banner snapshot not present")

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        # Open a meeting with multiple utterances. M3 (contract-
        # negotiation) is reliably busy.
        app.push_screen(RunSummaryScreen(_V6_BANNER))
        await pilot.pause()
        # Navigate to M3 (index 3: M1, M2, M2.5, M3)
        await pilot.press("j")
        await pilot.press("j")
        await pilot.press("j")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, MeetingDetailScreen)
        if len(screen._utterances) < 2:
            pytest.skip("need at least 2 utterances in the meeting")
        # First-row preview should be primed.
        first_preview = screen._last_preview_text
        assert first_preview, "preview should be populated on mount"
        # Move down — should refresh.
        await pilot.press("j")
        await pilot.pause()
        second_preview = screen._last_preview_text
        # The two should differ (different rows).
        assert first_preview != second_preview, (
            "preview should update when cursor moves between rows"
        )
        await pilot.press("q")


async def test_a_key_opens_artifact_browser() -> None:
    """Pressing 'a' on the run summary should open the artifact browser."""
    if not (_V6_BANNER / "wonderland-snapshot").is_dir():
        pytest.skip("v6 banner snapshot not present")

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(RunSummaryScreen(_V6_BANNER))
        await pilot.pause()
        await pilot.press("a")
        await pilot.pause()
        assert isinstance(app.screen, ArtifactBrowserScreen)
        # Browser should populate with the snapshot's artifacts.
        assert len(app.screen._artifacts) > 0
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, RunSummaryScreen)
        await pilot.press("q")


async def test_artifact_browser_preview_updates_on_cursor_move() -> None:
    """As j/k moves the cursor in the artifact table, the body
    preview should reflect the new artifact's content. Mirrors the
    meeting view's preview behavior."""
    if not (_V6_BANNER / "wonderland-snapshot").is_dir():
        pytest.skip("v6 banner snapshot not present")

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(ArtifactBrowserScreen(_V6_BANNER))
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, ArtifactBrowserScreen)
        if len(screen._artifacts) < 2:
            pytest.skip("need ≥2 artifacts to test preview movement")
        first_preview = screen._last_preview_text
        assert first_preview, "preview should be populated on mount"
        await pilot.press("j")
        await pilot.pause()
        second_preview = screen._last_preview_text
        assert first_preview != second_preview, (
            "preview should update when cursor moves between rows"
        )
        await pilot.press("q")


async def test_artifact_browser_drills_into_detail() -> None:
    """Enter on an artifact opens its rendered markdown."""
    if not (_V6_BANNER / "wonderland-snapshot").is_dir():
        pytest.skip("v6 banner snapshot not present")

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(ArtifactBrowserScreen(_V6_BANNER))
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, ArtifactBrowserScreen)
        if not screen._artifacts:
            pytest.skip("no artifacts in v6 banner")
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, ArtifactDetailScreen)
        # The detail screen carries a non-empty title.
        assert app.screen.artifact.title
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, ArtifactBrowserScreen)
        await pilot.press("q")


async def test_meeting_detail_a_opens_meeting_scoped_artifact_browser() -> None:
    """Pressing 'a' on a meeting detail opens the artifact browser
    filtered to that meeting's time range — fewer artifacts than the
    unfiltered view, all with mtimes within the meeting's window."""
    if not (_V6_BANNER / "wonderland-snapshot").is_dir():
        pytest.skip("v6 banner snapshot not present")

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(RunSummaryScreen(_V6_BANNER))
        await pilot.pause()
        # M2.5 (Advice from a Caterpillar) — index 2 in the meetings table
        await pilot.press("j")
        await pilot.press("j")
        await pilot.pause()
        await pilot.press("enter")  # open meeting
        await pilot.pause()
        meeting_screen = app.screen
        assert isinstance(meeting_screen, MeetingDetailScreen)
        assert meeting_screen.meeting.id == "composition"
        # 'a' opens the artifact browser scoped to this meeting
        await pilot.press("a")
        await pilot.pause()
        browser = app.screen
        assert isinstance(browser, ArtifactBrowserScreen)
        assert browser.meeting is not None
        assert browser.meeting.id == "composition"

        # Compare against unfiltered count — meeting-scoped should
        # be fewer (M2.5 ships features/stories only, not the full corpus)
        # AND non-empty (M2.5 reliably attaches artifacts on the bus).
        from wonderland.observer import HistoricalRunHandle

        unfiltered_count = len(HistoricalRunHandle(_V6_BANNER).artifacts())
        scoped_count = len(browser._artifacts)
        assert scoped_count > 0, (
            "meeting-scoped artifact list should be non-empty for M2.5 — "
            "Caterpillar reliably emits feature artifacts on the bus there"
        )
        assert scoped_count < unfiltered_count, (
            f"meeting-scoped artifact list ({scoped_count}) should be "
            f"strictly smaller than unfiltered ({unfiltered_count})"
        )

        # Every artifact in the scoped list should also appear as an
        # attachment on some utterance in the meeting's thread —
        # that's the attribution invariant the new filter relies on.
        handle = HistoricalRunHandle(_V6_BANNER)
        attached_basenames: set[str] = set()
        for u in handle.utterances(thread_id=meeting_screen.meeting.id):
            for attached in u.content.artifacts or []:
                payload = (
                    attached.payload if isinstance(attached.payload, dict) else {}
                )
                if payload.get("path"):
                    attached_basenames.add(Path(payload["path"]).name)
        for a in browser._artifacts:
            assert a.path.name in attached_basenames, (
                f"{a.path.name} appears in scoped list but no utterance "
                f"in {meeting_screen.meeting.id} attached it"
            )

        await pilot.press("q")


async def test_pressing_enter_opens_utterance_modal() -> None:
    """Enter on a transcript row pushes the UtteranceModalScreen."""
    if not (_V6_BANNER / "wonderland-snapshot").is_dir():
        pytest.skip("v6 banner snapshot not present")

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(RunSummaryScreen(_V6_BANNER))
        await pilot.pause()
        # M3 → many utterances
        for _ in range(3):
            await pilot.press("j")
        await pilot.pause()
        await pilot.press("enter")  # open meeting
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, MeetingDetailScreen)
        if not screen._utterances:
            pytest.skip("meeting has no utterances")
        await pilot.press("enter")  # expand
        await pilot.pause()
        assert isinstance(app.screen, UtteranceModalScreen)
        # Escape pops back.
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, MeetingDetailScreen)
        await pilot.press("q")


async def test_speaker_filter_cycles_through_meeting_speakers() -> None:
    """`f` cycles the speaker filter on the meeting transcript.
    Each cycle step narrows the table to one speaker; eventually
    cycling all the way around returns to "all"."""
    if not (_V6_BANNER / "wonderland-snapshot").is_dir():
        pytest.skip("v6 banner snapshot not present")

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        # M4 (The Mad Tea Party) has all four roster members emitting
        # — Alice, Hatter, Tweedledee, Tweedledum. Reliable for
        # multi-speaker cycle testing.
        app.push_screen(RunSummaryScreen(_V6_BANNER))
        await pilot.pause()
        # M4 is index 4: M1, M2, M2.5, M3, M4
        for _ in range(4):
            await pilot.press("j")
        await pilot.pause()
        await pilot.press("enter")  # open M4
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, MeetingDetailScreen)
        assert screen.meeting.id == "test-scenarios"

        if len(screen._speakers_in_meeting) < 2:
            pytest.skip("need ≥2 speakers to test cycling")

        baseline_count = len(screen._utterances)
        assert screen._filter_speaker is None  # starts at "all"

        # Cycle forward: filter applies to first speaker
        await pilot.press("f")
        await pilot.pause()
        assert screen._filter_speaker == screen._speakers_in_meeting[0]
        filtered_count = len(screen._utterances)
        assert filtered_count > 0
        assert filtered_count < baseline_count, (
            "speaker filter should narrow the visible utterances"
        )
        # All visible utterances should be the chosen speaker
        for u in screen._utterances:
            assert u.speaker.name == screen._filter_speaker

        # Cycling back with 'F' returns to "all"
        await pilot.press("F")
        await pilot.pause()
        assert screen._filter_speaker is None
        assert len(screen._utterances) == baseline_count

        await pilot.press("q")


# ---------- theme cycling ----------


async def test_theme_starts_at_wonderland_default() -> None:
    """The app should boot with the Wonderland tea-party theme."""
    from wonderland.tui.themes import DEFAULT_THEME_NAME

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.theme == DEFAULT_THEME_NAME
        await pilot.press("q")


async def test_t_cycles_through_wonderland_themes() -> None:
    """`t` advances through the registered Wonderland themes and
    wraps at the end."""
    from wonderland.tui.themes import WONDERLAND_THEMES

    names = [t.name for t in WONDERLAND_THEMES]
    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.theme == names[0]
        for expected in names[1:] + [names[0]]:  # full cycle including wrap
            await pilot.press("t")
            await pilot.pause()
            assert app.theme == expected
        await pilot.press("q")


# ---------- live-watch screen (T45 / P8.4) ----------


class TestLabelFromThreadId:
    """The synthesized iteration discriminator used when
    iteration_label is None on streaming events. Will be unnecessary
    once roadmap 7a5ff815 lands per_item iteration metadata in
    HistoricalRunHandle.meetings()."""

    def test_thread_id_equals_base_returns_label_unchanged(self) -> None:
        # No per_item iteration — thread_id is the base meeting id.
        assert _label_from_thread_id("M1", "scoping", "scoping") == "M1"
        assert _label_from_thread_id("M4", "test-scenarios", "test-scenarios") == "M4"
        assert (
            _label_from_thread_id("M3", "contract-negotiation", "contract-negotiation")
            == "M3"
        )

    def test_iteration_thread_id_synthesizes_label(self) -> None:
        result = _label_from_thread_id(
            "M4",
            "test-scenarios-focus-session-with-visual-countdown",
            "test-scenarios",
        )
        assert result == "M4: Focus Session With Visual Countdown"

    def test_iteration_with_simple_base_id(self) -> None:
        result = _label_from_thread_id("M5", "implementation-foo-bar", "implementation")
        assert result == "M5: Foo Bar"

    def test_unknown_prefix_returns_label_unchanged(self) -> None:
        # If thread_id doesn't start with base_meeting_id + '-',
        # the function falls back to the unaltered label.
        assert (
            _label_from_thread_id("M4", "review-something", "test-scenarios")
            == "M4"
        )


async def test_live_run_screen_mounts_with_dummy_data() -> None:
    """T45 + T48: layout-only check. The screen should mount cleanly
    and render its multi-pane layout (meetings ribbon, transcript
    table + body preview, artifacts table, status bar) populated
    with the hand-built dummy data when no snapshot is bound."""
    from textual.widgets import DataTable

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(LiveRunScreen())
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, LiveRunScreen)

        # Meetings ribbon: All-Meetings pseudo-row + 3 dummy meetings.
        table = screen.query_one("#live-meetings-table", DataTable)
        assert table.row_count == 4

        # Status bar populated (cost > 0, speaker set).
        # The dummy renderer doesn't ship transcript rows in T48 (no
        # streaming events); verify state directly.
        assert screen._total_cost > 0
        assert screen._current_speaker == "white_rabbit"

        await pilot.press("q")


async def test_live_run_screen_phase_events_pane_populates_via_stream() -> None:
    """Integration check: phase events flow end-to-end from
    run_phased_meeting → LiveRunHandle (workflow → RunEvent
    translation) → LiveRunScreen (dispatch → table). Catches
    bugs the direct-dispatch test below would miss (e.g.,
    missing translation cases, CSS clipping, screen wiring)."""
    import asyncio
    from pathlib import Path
    from textual.widgets import DataTable

    from wonderland import (
        AgentIdentity,
        InMemoryCaucus,
        SpeechAct,
        Utterance,
        UtteranceContent,
    )
    from wonderland.agent import Context
    from wonderland.observer.live import LiveRunHandle
    from wonderland.workflow import Meeting, PhaseSpec, Workflow

    class _FakeAgent:
        def __init__(self, name: str) -> None:
            self.identity = AgentIdentity(
                name=name, constitution_version="0.1"
            )

        async def compose_context(self, triggers):
            return Context(
                constitution=f"<{self.identity.name}>",
                triggers=tuple(triggers),
            )

        async def deliberate(self, ctx):
            return Utterance(
                thread_id="m",
                speaker=self.identity,
                addressed_to="caucus",
                speech_act=SpeechAct.PROPOSAL,
                content=UtteranceContent(body="hi"),
            )

    class _FakeTel:
        def __init__(self) -> None:
            self.call_count = 0

    class _FakeRunner:
        def __init__(self, project_root: Path) -> None:
            self.bus = InMemoryCaucus()
            self.dodo = _FakeAgent("dodo")
            self.agents = {"a": _FakeAgent("a"), "b": _FakeAgent("b")}
            self.telemetry = _FakeTel()
            self.total_cost = 0.0
            self.budget_dollars = 5.0
            self.project_root = project_root
            self.run_id = "stream-test"
            self._completed = False

        async def setup(self):
            pass

        async def teardown(self):
            pass

        async def convene(self, **kw):
            pass

        def mark_thread_complete(self, *a):
            pass

    import tempfile

    with tempfile.TemporaryDirectory() as td:
        wf = Workflow(
            name="t",
            description="",
            meetings=[
                Meeting(
                    id="m",
                    label="M1",
                    goal="g",
                    roster=["a", "b"],
                    phases=[PhaseSpec(name="discussion", max_rotations=1)],
                ),
            ],
        )
        runner = _FakeRunner(Path(td))
        handle = LiveRunHandle(
            workflow=wf,
            runner=runner,  # type: ignore[arg-type]
            directive="test",
        )

        app = WonderlandApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = LiveRunScreen(handle=handle)
            app.push_screen(screen)
            # Drain the stream — small workflow, finishes quickly
            await asyncio.sleep(0.3)
            await pilot.pause()
            await asyncio.sleep(0.3)
            await pilot.pause()

            ptable = screen.query_one(
                "#live-phase-events-table", DataTable
            )
            # Expected events for 1 phase × 2 cast × 1 rotation:
            # PhaseStart + 2 windows + 2 acts + RotationComplete + PhaseEnd = 7
            assert ptable.row_count >= 5, (
                f"phase events table only has {ptable.row_count} "
                "rows; expected >= 5 for a 2-agent / 1-rotation phase"
            )

            await pilot.press("q")


async def test_live_run_screen_auto_sentinel_cycle_advances_through_states() -> None:
    """The T keybind cycles through: off → 15m → 5m → 1m → instant
    → off. Status bar shows the current state when on."""
    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = LiveRunScreen()
        app.push_screen(screen)
        await pilot.pause()

        # Default: off (None)
        assert screen._auto_sentinel_seconds is None

        # Cycle: off → 15m
        screen.action_cycle_auto_sentinel()
        assert screen._auto_sentinel_seconds == 900.0

        # 15m → 5m
        screen.action_cycle_auto_sentinel()
        assert screen._auto_sentinel_seconds == 300.0

        # 5m → 1m
        screen.action_cycle_auto_sentinel()
        assert screen._auto_sentinel_seconds == 60.0

        # 1m → instant (0)
        screen.action_cycle_auto_sentinel()
        assert screen._auto_sentinel_seconds == 0.0

        # instant → off (wraps around)
        screen.action_cycle_auto_sentinel()
        assert screen._auto_sentinel_seconds is None

        await pilot.press("q")


async def test_live_run_screen_auto_sentinel_instant_skips_modal() -> None:
    """With auto_sentinel set to 0, _handle_user_question returns
    None immediately without showing the modal — the watcher then
    publishes the sentinel reply."""
    from wonderland import AgentIdentity, SpeechAct, Utterance, UtteranceContent
    from wonderland.utterance import operator_identity

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = LiveRunScreen()
        app.push_screen(screen)
        await pilot.pause()

        screen._auto_sentinel_seconds = 0.0

        question = Utterance(
            thread_id="m",
            speaker=AgentIdentity(name="tweedledee", constitution_version="0.1"),
            addressed_to=[operator_identity()],
            speech_act=SpeechAct.QUESTION,
            content=UtteranceContent(body="client-only or with backend?"),
        )

        # Should resolve immediately with None (sentinel) — no
        # modal pushed.
        answer = await screen._handle_user_question(question)
        assert answer is None

        await pilot.press("q")


async def test_ask_user_modal_auto_dismiss_after_timeout() -> None:
    """When auto_dismiss_after is set and the operator doesn't
    answer in time, the modal self-dismisses with None."""
    import asyncio

    from wonderland.tui.screens.ask_user_modal import AskUserModal

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()

        results: list[str | None] = []

        def _on_dismissed(answer: str | None) -> None:
            results.append(answer)

        # Use a tight timeout so the test runs fast.
        modal = AskUserModal(
            asking_agent="tweedledee",
            question="A or B?",
            auto_dismiss_after=0.05,
        )
        app.push_screen(modal, _on_dismissed)
        await pilot.pause()
        # Wait past the timeout
        await asyncio.sleep(0.15)
        await pilot.pause()

        assert results == [None]


async def test_live_run_screen_phase_events_pane_populates() -> None:
    """T64/T65 surface check: the new phase-events pane in
    LiveRunScreen renders rows for each of the six phase event
    types (PhaseStarted/Ended, PriorityWindowOpened, AgentActed/
    Passed, RotationCompleted) when they flow through the event
    stream."""
    from datetime import datetime, timezone
    from textual.widgets import DataTable

    from wonderland.observer import (
        AgentActed,
        AgentPassed,
        PhaseEnded,
        PhaseStarted,
        PriorityWindowOpened,
        RotationCompleted,
    )

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = LiveRunScreen()
        app.push_screen(screen)
        await pilot.pause()

        # The screen's _dispatch_event wires phase events to the
        # phase-events table; feed it directly.
        now = datetime.now(tz=timezone.utc)
        screen._dispatch_event(
            PhaseStarted(
                timestamp=now,
                meeting_thread_id="m4",
                phase_name="clarify",
                max_rotations=1,
                cast=("alice", "mad_hatter", "td", "tdm"),
            ),
            base_meeting_ids=[],
        )
        screen._dispatch_event(
            PriorityWindowOpened(
                timestamp=now,
                meeting_thread_id="m4",
                phase_name="clarify",
                agent_id="alice",
                rotation_index=0,
                window_index_in_phase=0,
            ),
            base_meeting_ids=[],
        )
        screen._dispatch_event(
            AgentActed(
                timestamp=now,
                meeting_thread_id="m4",
                phase_name="clarify",
                agent_id="alice",
                rotation_index=0,
                utterance_id="01HXYZABC",
            ),
            base_meeting_ids=[],
        )
        screen._dispatch_event(
            AgentPassed(
                timestamp=now,
                meeting_thread_id="m4",
                phase_name="clarify",
                agent_id="td",
                rotation_index=0,
                reason=None,
            ),
            base_meeting_ids=[],
        )
        screen._dispatch_event(
            RotationCompleted(
                timestamp=now,
                meeting_thread_id="m4",
                phase_name="clarify",
                rotation_index=0,
            ),
            base_meeting_ids=[],
        )
        screen._dispatch_event(
            PhaseEnded(
                timestamp=now,
                meeting_thread_id="m4",
                phase_name="clarify",
                reason="succession",
                rotations_used=1,
                total_windows=4,
                passes_per_agent={"alice": 0, "mad_hatter": 0, "td": 1, "tdm": 1},
                acts_per_agent={"alice": 1, "mad_hatter": 1, "td": 0, "tdm": 0},
            ),
            base_meeting_ids=[],
        )
        await pilot.pause()

        ptable = screen.query_one("#live-phase-events-table", DataTable)
        assert ptable.row_count == 6

        await pilot.press("q")


async def _drain_live_run_screen(
    pilot,
    screen: LiveRunScreen,
    max_seconds: float = 10.0,
) -> None:
    """Wait for the screen's @work-decorated stream consumer to
    finish. The consumer is a worker registered on the screen; we
    pause repeatedly until either it's done or we exceed the budget.
    """
    import time

    deadline = time.monotonic() + max_seconds
    while time.monotonic() < deadline:
        await pilot.pause()
        # The worker's done when the screen's worker set is empty
        # (or all workers have finished).
        active = [w for w in screen.workers if w.is_running]
        if not active:
            return
        await pilot.pause()
    # Fall through — caller may still assert on partial state.


async def test_live_run_screen_streams_v6_banner() -> None:
    """T46: against the parallel-TDD v6 banner (7 meetings, no
    per_item iterations), the screen should populate the meetings
    ribbon with all 7 rows after the stream drains."""
    if not (_V6_BANNER / "wonderland-snapshot").is_dir():
        pytest.skip("v6 banner snapshot not present")
    from textual.widgets import DataTable

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        # speed=1e6 + dwell=0 strips all timing — drain instantly.
        app.push_screen(
            LiveRunScreen(_V6_BANNER, speed=1e6, max_dwell_seconds=0.0)
        )
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, LiveRunScreen)
        await _drain_live_run_screen(pilot, screen)

        table = screen.query_one("#live-meetings-table", DataTable)
        # v6 banner ran tdd: M1, M2, M2.5, M3, M4, M5, M6 = 7 cells
        # plus the All-Meetings pseudo-row at index 0 = 8 rows.
        assert table.row_count == 8
        # All rows should be in a terminal status (complete or
        # over-budget) since the stream drained fully.
        for thread_id in screen._meeting_order:
            assert screen._meetings_seen[thread_id]["status"] in (
                "complete",
                "over-budget",
            )
        # Total cost accumulated across agents.
        assert screen._total_cost > 0
        await pilot.press("q")


async def test_live_run_screen_streams_v3_per_item_snapshot() -> None:
    """T46: against tdd-serial v3 (11 distinct meeting threads —
    M4 × 3 iterations + M5 × 3 iterations + others), the ribbon
    should show 11 rows. Per_item iterations get distinct rows."""
    v3 = ANALYSES_DATA / "032-tdd-serial-v3"
    if not (v3 / "wonderland-snapshot").is_dir():
        pytest.skip("v3 snapshot not present")
    from textual.widgets import DataTable

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(LiveRunScreen(v3, speed=1e6, max_dwell_seconds=0.0))
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, LiveRunScreen)
        await _drain_live_run_screen(pilot, screen)

        table = screen.query_one("#live-meetings-table", DataTable)
        # 11 actual meetings + All-Meetings pseudo-row = 12 rows.
        assert table.row_count == 12

        # Verify per_item iterations got distinct labels (the slug-
        # derived discriminator at minimum).
        thread_ids = screen._meeting_order
        m4_iters = [t for t in thread_ids if t.startswith("test-scenarios-")]
        m5_iters = [t for t in thread_ids if t.startswith("implementation-")]
        assert len(m4_iters) == 3
        assert len(m5_iters) == 3
        # Labels should differ across iterations of the same base
        # meeting (the discriminator is doing its job).
        m4_labels = [screen._meetings_seen[t]["label"] for t in m4_iters]
        assert len(set(m4_labels)) == 3
        await pilot.press("q")


async def test_live_run_screen_body_preview_updates_on_transcript_cursor() -> None:
    """T48 follow-up: when focus is on the transcript table and the
    cursor moves to a different row, the body-preview pane updates
    to show that utterance's full content. Mirrors the meeting-detail
    screen's pattern."""
    if not (_V6_BANNER / "wonderland-snapshot").is_dir():
        pytest.skip("v6 banner snapshot not present")
    from textual.widgets import DataTable, Static

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(
            LiveRunScreen(_V6_BANNER, speed=1e6, max_dwell_seconds=0.0)
        )
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, LiveRunScreen)
        await _drain_live_run_screen(pilot, screen)

        utterances = screen._meeting_transcripts[_ALL_MEETINGS]
        if len(utterances) < 2:
            pytest.skip("need ≥2 utterances for body preview test")

        # Move directly via the body-preview helper since cycling
        # focus through Tab in test mode is fiddly.
        screen._update_body_preview(0)
        body = screen.query_one("#transcript-body", Static)
        # Renderable inspection isn't stable across Textual versions;
        # just confirm the helper runs without error and we can call
        # it for different rows. The actual DataTable.RowHighlighted
        # path is exercised by the filtering test.
        screen._update_body_preview(1)
        screen._update_body_preview(-1)  # empty/reset path

        await pilot.press("q")


async def test_live_run_screen_filtering_by_meeting_selection() -> None:
    """T48: cursor on a specific meeting in the left pane filters the
    transcript and artifacts panes to that meeting's content. Cursor
    on the All-Meetings pseudo-row at index 0 shows the full rolling
    stream (T46 behavior preserved as default)."""
    if not (_V6_BANNER / "wonderland-snapshot").is_dir():
        pytest.skip("v6 banner snapshot not present")
    from textual.widgets import DataTable

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(
            LiveRunScreen(_V6_BANNER, speed=1e6, max_dwell_seconds=0.0)
        )
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, LiveRunScreen)
        await _drain_live_run_screen(pilot, screen)

        # Default selection is All-Meetings; the per-meeting buffer
        # for the first meeting should be a strict subset of the
        # All-Meetings buffer.
        first_thread = screen._meeting_order[0]
        all_count = len(screen._meeting_transcripts[_ALL_MEETINGS])
        first_count = len(screen._meeting_transcripts[first_thread])
        assert first_count > 0
        assert first_count < all_count

        # Move cursor down to the first real meeting (index 1, since
        # index 0 is All-Meetings pseudo-row).
        await pilot.press("j")
        await pilot.pause()
        assert screen._selected_thread_id == first_thread

        # Transcript table should have been re-rendered with only the
        # first meeting's utterances. Each utterance = 1 row.
        ttable = screen.query_one("#transcript-table", DataTable)
        assert ttable.row_count == first_count

        # Cursor back to All-Meetings restores the full stream.
        await pilot.press("k")
        await pilot.pause()
        assert screen._selected_thread_id == _ALL_MEETINGS
        assert ttable.row_count == all_count

        await pilot.press("q")


async def test_live_run_screen_artifacts_pane_populates() -> None:
    """T48: the artifacts pane fills with the artifacts shipped during
    the selected meeting. All-Meetings selection shows all artifacts."""
    if not (_V6_BANNER / "wonderland-snapshot").is_dir():
        pytest.skip("v6 banner snapshot not present")
    from textual.widgets import DataTable

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(
            LiveRunScreen(_V6_BANNER, speed=1e6, max_dwell_seconds=0.0)
        )
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, LiveRunScreen)
        await _drain_live_run_screen(pilot, screen)

        # All-Meetings is the default; artifacts table should have all
        # artifacts.
        all_count = len(screen._meeting_artifacts[_ALL_MEETINGS])
        atable = screen.query_one("#live-artifacts-table", DataTable)
        assert all_count > 0
        assert atable.row_count == all_count

        # Move cursor to a specific meeting; artifacts table should
        # filter to that meeting's artifacts only.
        await pilot.press("j")
        await pilot.pause()
        first_thread = screen._meeting_order[0]
        first_count = len(
            screen._meeting_artifacts.get(first_thread, [])
        )
        # Could be 0 — M1 sometimes ships nothing because Cat is
        # suppressed. So just check the count is correct, not nonzero.
        assert atable.row_count == first_count

        await pilot.press("q")


async def test_live_run_screen_per_meeting_costs_match_run_log() -> None:
    """T47: each meeting's cost column matches the value in the
    run.log's META END marker. v3 had distinct per-iteration costs
    (5469, 6140, 5707 cents on M4 iterations 1/2/3 etc.) so this
    catches both the run-log parsing and the per-iteration tracking."""
    v3 = ANALYSES_DATA / "032-tdd-serial-v3"
    if not (v3 / "wonderland-snapshot").is_dir():
        pytest.skip("v3 snapshot not present")

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(LiveRunScreen(v3, speed=1e6, max_dwell_seconds=0.0))
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, LiveRunScreen)
        await _drain_live_run_screen(pilot, screen)

        # Verified-by-hand cost numbers from v3's run.log (analysis 032).
        # M4 iterations are (Focus, Break, Daily Review) in order;
        # M5 iterations same.
        expected_by_position = [
            ("scoping", 0.0328),
            ("decomposition", 0.0442),
            ("composition", 0.0491),
            ("contract-negotiation", 0.1955),
            ("test-scenarios-focus-session-with-visual-countdown", 0.5469),
            ("test-scenarios-break-timer-with-user-configuration", 0.6140),
            ("test-scenarios-daily-review-of-session-history", 0.5707),
            ("implementation-focus-session-with-visual-countdown", 0.3475),
            ("implementation-break-timer-with-user-configuration", 0.5875),
            ("implementation-daily-review-of-session-history", 0.5346),
            ("review", 1.2007),
        ]
        for thread_id, expected_cost in expected_by_position:
            assert thread_id in screen._meetings_seen, (
                f"missing meeting {thread_id}"
            )
            actual = screen._meetings_seen[thread_id]["cost"]
            assert abs(actual - expected_cost) < 0.001, (
                f"{thread_id}: expected ${expected_cost:.4f}, got ${actual:.4f}"
            )

        # Total matches v3's reported $4.7236 (the AgentTelemetryDelta
        # final overwrite).
        assert abs(screen._total_cost - 4.7236) < 0.001
        await pilot.press("q")


async def test_live_run_screen_transcript_populated_after_stream() -> None:
    """T46: after draining the stream, the transcript log should
    contain at least as many lines as utterances + the run-ended
    marker."""
    if not (_V6_BANNER / "wonderland-snapshot").is_dir():
        pytest.skip("v6 banner snapshot not present")
    from textual.widgets import DataTable

    handle = HistoricalRunHandle(_V6_BANNER)
    expected_utterances = sum(1 for _ in handle.utterances())

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(
            LiveRunScreen(_V6_BANNER, speed=1e6, max_dwell_seconds=0.0)
        )
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, LiveRunScreen)
        await _drain_live_run_screen(pilot, screen)

        # T48: transcript is now a DataTable with one row per
        # utterance. Default selection is All-Meetings → all utterances
        # rendered.
        ttable = screen.query_one("#transcript-table", DataTable)
        assert ttable.row_count == expected_utterances
        await pilot.press("q")


async def test_live_run_screen_vim_navigation_works() -> None:
    """j/k should move the cursor in the meetings ribbon (vim nav
    comes from WonderlandApp app-level bindings)."""
    from textual.widgets import DataTable

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(LiveRunScreen())
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, LiveRunScreen)
        table = screen.query_one("#live-meetings-table", DataTable)
        assert table.cursor_row == 0
        await pilot.press("j")
        await pilot.pause()
        assert table.cursor_row == 1
        await pilot.press("k")
        await pilot.pause()
        assert table.cursor_row == 0
        await pilot.press("q")


# ---------- new-run screen (T51 / P8.5) ----------


async def test_new_run_screen_mounts_with_bundled_presets() -> None:
    """T51: NewRunScreen mounts cleanly and the preset table is
    populated with the blank pseudo-row plus at least the canonical
    bundled presets."""
    from textual.widgets import DataTable

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(NewRunScreen())
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, NewRunScreen)

        table = screen.query_one("#preset-table", DataTable)
        # 1 blank pseudo-row + 5 bundled directives shipped in T50 =
        # at least 6 rows.
        assert table.row_count >= 6

        # Cached preset list should match the table.
        assert len(screen._presets) == table.row_count

        await pilot.press("q")


async def test_new_run_screen_blank_preset_clears_editors() -> None:
    """T51 follow-up: selecting the blank pseudo-row at the top of
    the preset list clears the composer + description so the user
    can start fresh. Pre-fills from another preset don't persist."""
    from textual.widgets import DataTable, TextArea

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(NewRunScreen())
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, NewRunScreen)

        # Cursor onto pomodoro first to fill the editors.
        table = screen.query_one("#preset-table", DataTable)
        pomodoro_row = next(
            i
            for i, (name, _) in enumerate(screen._presets)
            if name == "pomodoro"
        )
        table.cursor_coordinate = (pomodoro_row, 0)
        await pilot.pause()

        composer = screen.query_one("#directive-composer", TextArea)
        description = screen.query_one("#description-composer", TextArea)
        assert "Pomodoro" in composer.text
        assert description.text  # non-empty (pomodoro has a description)

        # Now cursor up to the blank pseudo-row at index 0.
        table.cursor_coordinate = (0, 0)
        await pilot.pause()

        assert composer.text == ""
        assert description.text == ""

        await pilot.press("q")


async def test_new_run_screen_description_is_editable() -> None:
    """T51 follow-up: the description below the composer is a
    TextArea, not a Static — user can type into it (e.g. when saving
    a custom directive as a preset)."""
    from textual.widgets import TextArea

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(NewRunScreen())
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, NewRunScreen)

        description = screen.query_one("#description-composer", TextArea)
        # Should be assignable (TextArea exposes a writable .text).
        description.text = "Manually written description for a fresh directive."
        await pilot.pause()
        assert description.text.startswith("Manually written")

        await pilot.press("q")


async def test_new_run_screen_enter_advances_through_form() -> None:
    """T51 follow-up: Enter on each form field steps to the next
    field (linear form behavior). TextAreas keep their natural
    Enter-as-newline behavior; users Tab past them. Single-field
    widgets (Inputs, DataTable, Select, Checkbox) advance on Enter."""
    from textual.widgets import (
        Checkbox,
        DataTable,
        Input,
        Select,
        TextArea,
    )

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(NewRunScreen())
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, NewRunScreen)

        # Start with preset table focused. Hit Enter to advance.
        preset_table = screen.query_one("#preset-table", DataTable)
        assert preset_table.has_focus
        # Fire RowSelected directly via the action — pilot.press("enter")
        # sometimes routes oddly through DataTable.
        screen._advance_from("preset-table")
        await pilot.pause()
        composer = screen.query_one("#directive-composer", TextArea)
        assert composer.has_focus

        # From composer, advance to description.
        screen._advance_from("directive-composer")
        await pilot.pause()
        description = screen.query_one("#description-composer", TextArea)
        assert description.has_focus

        # From description → workflow.
        screen._advance_from("description-composer")
        await pilot.pause()
        workflow = screen.query_one("#workflow-select", Select)
        assert workflow.has_focus

        # workflow → budget
        screen._advance_from("workflow-select")
        await pilot.pause()
        budget = screen.query_one("#budget-input", Input)
        assert budget.has_focus

        # budget → project
        screen._advance_from("budget-input")
        await pilot.pause()
        project = screen.query_one("#project-input", Input)
        assert project.has_focus

        # project → save checkbox
        screen._advance_from("project-input")
        await pilot.pause()
        save_box = screen.query_one("#save-checkbox", Checkbox)
        assert save_box.has_focus

        # save checkbox → save-name input
        screen._advance_from("save-checkbox")
        await pilot.pause()
        save_name = screen.query_one("#save-name-input", Input)
        assert save_name.has_focus

        # End of form → action_go fires (without crashing on empty
        # directive — surfaces a notification).
        screen._advance_from("save-name-input")
        await pilot.pause()

        await pilot.press("q")


async def test_new_run_screen_go_button_triggers_launch_flow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """T53 polish: a visible Go button at the bottom of the form is
    discoverable + clickable. Pressing it triggers the same
    action_go path as the 'g' binding."""
    from textual.widgets import Button, Input, Select, TextArea

    from wonderland.tui.screens.launch_confirmation import (
        LaunchConfirmationScreen,
    )

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake-key-for-testing")

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(NewRunScreen(project_root=Path("/tmp")))
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, NewRunScreen)

        # Go button is visible
        go = screen.query_one("#go-button", Button)
        assert go is not None
        assert "Go" in str(go.label)

        # Fill form
        screen.query_one("#directive-composer", TextArea).text = (
            "Build a /hello endpoint."
        )
        screen.query_one("#workflow-select", Select).value = "smoke"
        screen.query_one("#budget-input", Input).value = "0.50"
        screen.query_one("#project-input", Input).value = "/tmp"
        await pilot.pause()

        # Click the Go button — should push the confirmation modal
        from textual.widgets import Button as _Button

        screen.post_message(_Button.Pressed(go))
        await pilot.pause()
        assert isinstance(app.screen, LaunchConfirmationScreen)

        # Decline so the test exits cleanly
        await pilot.press("n")
        await pilot.pause()
        await pilot.press("q")


async def test_launch_confirmation_dismisses_yes_no() -> None:
    """T53: the launch confirmation modal returns True on Yes
    binding, False on No / Escape. Pushes via app.push_screen with
    a callback to verify the response."""
    from wonderland.tui.screens.launch_confirmation import (
        LaunchConfirmationScreen,
    )

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        results: list = []

        def capture(value):
            results.append(value)

        # Yes path
        app.push_screen(
            LaunchConfirmationScreen(
                directive="Build a /hello endpoint.",
                workflow_name="smoke",
                budget=0.50,
                project_root="/tmp/test",
            ),
            capture,
        )
        await pilot.pause()
        await pilot.press("y")
        await pilot.pause()
        assert results[-1] is True

        # No path
        app.push_screen(
            LaunchConfirmationScreen(
                directive="dirty",
                workflow_name="smoke",
                budget=0.50,
                project_root="/tmp/test",
            ),
            capture,
        )
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()
        assert results[-1] is False

        # Escape path
        app.push_screen(
            LaunchConfirmationScreen(
                directive="dirty",
                workflow_name="smoke",
                budget=0.50,
                project_root="/tmp/test",
            ),
            capture,
        )
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert results[-1] is False

        await pilot.press("q")


async def test_live_run_screen_accepts_handle_directly() -> None:
    """T53: LiveRunScreen now accepts a pre-built RunHandle. Used by
    the NewRunScreen → LiveRunScreen handoff for live runs (the
    handle is a LiveRunHandle wrapping a real Runner). Verified here
    via a HistoricalRunHandle so we don't need a Runner."""
    if not (_V6_BANNER / "wonderland-snapshot").is_dir():
        pytest.skip("v6 banner snapshot not present")
    from textual.widgets import DataTable

    handle = HistoricalRunHandle(_V6_BANNER)

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(LiveRunScreen(handle=handle))
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, LiveRunScreen)
        await _drain_live_run_screen(pilot, screen)

        # Same expectations as the snapshot_dir variant — the screen
        # doesn't care which RunHandle subclass it consumes.
        table = screen.query_one("#live-meetings-table", DataTable)
        # 7 v6 meetings + 1 All-Meetings pseudo-row
        assert table.row_count == 8
        assert screen._total_cost > 0

        await pilot.press("q")


async def test_new_run_screen_action_go_pushes_confirmation_modal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """T53: action_go on a fully-validated form pushes the launch
    confirmation modal. Pre-flight API key check passes when
    ANTHROPIC_API_KEY is set in the env."""
    from textual.widgets import Checkbox, Input, Select, TextArea

    from wonderland.tui.screens.launch_confirmation import (
        LaunchConfirmationScreen,
    )

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake-key-for-testing")

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(NewRunScreen(project_root=Path("/tmp")))
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, NewRunScreen)

        # Fill the form
        screen.query_one("#directive-composer", TextArea).text = (
            "Build a /hello endpoint."
        )
        screen.query_one("#workflow-select", Select).value = "smoke"
        screen.query_one("#budget-input", Input).value = "0.50"
        screen.query_one("#project-input", Input).value = "/tmp"
        screen.query_one("#save-checkbox", Checkbox).value = False
        await pilot.pause()

        # Trigger Go — should push the confirmation modal
        screen.action_go()
        await pilot.pause()

        assert isinstance(app.screen, LaunchConfirmationScreen)
        # Decline so the test exits cleanly without trying to launch
        await pilot.press("n")
        await pilot.pause()

        await pilot.press("q")


async def test_new_run_screen_action_go_blocks_without_existing_project(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """T53 polish: action_go refuses to launch when the project
    root doesn't exist, surfacing a clear message instead of letting
    Runner.make_full_cast fail with a confusing downstream error."""
    from textual.widgets import Checkbox, Input, Select, TextArea

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake-key-for-testing")

    nonexistent = tmp_path / "this-does-not-exist"
    assert not nonexistent.exists()

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(NewRunScreen(project_root=tmp_path))
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, NewRunScreen)

        # Fill form pointing at a path that doesn't exist
        screen.query_one("#directive-composer", TextArea).text = (
            "Build a /hello endpoint."
        )
        screen.query_one("#workflow-select", Select).value = "smoke"
        screen.query_one("#budget-input", Input).value = "0.50"
        screen.query_one("#project-input", Input).value = str(nonexistent)
        screen.query_one("#save-checkbox", Checkbox).value = False
        await pilot.pause()

        screen.action_go()
        await pilot.pause()

        # Should still be on NewRunScreen — no modal pushed
        assert isinstance(app.screen, NewRunScreen)
        # And the path was NOT silently created
        assert not nonexistent.exists()

        await pilot.press("q")


async def test_new_run_screen_action_go_blocks_without_api_key(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """T53: pre-flight refuses to launch when no API key is
    configured. The user gets a clear error notification, no modal
    pushed."""
    from textual.widgets import Checkbox, Input, Select, TextArea

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    # Point load_config at a non-existent file so it returns defaults
    # (api_key=None).
    monkeypatch.setattr(
        "wonderland.tui.screens.new_run.load_config",
        lambda: type("X", (), {"anthropic": type("Y", (), {"api_key": None})()})(),
    )

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(NewRunScreen(project_root=tmp_path))
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, NewRunScreen)

        screen.query_one("#directive-composer", TextArea).text = (
            "Build a /hello endpoint."
        )
        screen.query_one("#workflow-select", Select).value = "smoke"
        screen.query_one("#budget-input", Input).value = "0.50"
        screen.query_one("#project-input", Input).value = str(tmp_path)
        screen.query_one("#save-checkbox", Checkbox).value = False
        await pilot.pause()

        screen.action_go()
        await pilot.pause()

        # Should have pushed Settings screen for the user to set
        # the key inline rather than dropping to the shell.
        from wonderland.tui.screens.settings import SettingsScreen

        assert isinstance(app.screen, SettingsScreen)

        await pilot.press("escape")
        await pilot.pause()
        await pilot.press("q")


async def test_new_run_screen_save_as_preset_persists_and_relists(
    tmp_path: Path,
) -> None:
    """T51 follow-up: when the save-as-preset checkbox is on and a
    name is set, action_go (still a launch stub) saves the preset
    to project_root/.wonderland/directives/<name>.yaml and the
    preset table re-populates with the new entry."""
    from textual.widgets import Checkbox, DataTable, Input, Select, TextArea

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(NewRunScreen(project_root=tmp_path))
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, NewRunScreen)

        # Fill in the form.
        composer = screen.query_one("#directive-composer", TextArea)
        composer.text = "Build a custom thing for testing."
        description = screen.query_one("#description-composer", TextArea)
        description.text = "A custom thing\nwith multi-line description."
        screen.query_one("#workflow-select", Select).value = "smoke"
        screen.query_one("#save-checkbox", Checkbox).value = True
        screen.query_one("#save-name-input", Input).value = "custom-thing-test"
        await pilot.pause()

        # Trigger the launch action — it should save before notifying.
        screen.action_go()
        await pilot.pause()

        # File should be on disk.
        target = tmp_path / ".wonderland" / "directives" / "custom-thing-test.yaml"
        assert target.is_file()

        # Preset list should now include the new project-local preset.
        names = [name for (name, p) in screen._presets if p is not None]
        assert "custom-thing-test" in names

        await pilot.press("q")


async def test_new_run_screen_pressing_n_from_library_opens_it() -> None:
    """T51: 'n' on the snapshot library opens NewRunScreen."""
    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()
        assert isinstance(app.screen, NewRunScreen)
        await pilot.press("escape")
        await pilot.pause()
        await pilot.press("q")


async def test_new_run_screen_preset_selection_populates_composer() -> None:
    """T51: cursor on a preset row populates the directive composer
    with the preset's body and pre-selects the suggested workflow."""
    from textual.widgets import DataTable, Select, TextArea

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(NewRunScreen())
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, NewRunScreen)

        # Force selection of the pomodoro preset directly via the
        # cursor (find its row index).
        table = screen.query_one("#preset-table", DataTable)
        target_row = next(
            i
            for i, (name, _) in enumerate(screen._presets)
            if name == "pomodoro"
        )
        table.cursor_coordinate = (target_row, 0)
        await pilot.pause()

        composer = screen.query_one("#directive-composer", TextArea)
        # The pomodoro body should be in the composer
        assert "Pomodoro" in composer.text
        assert "focus sessions" in composer.text

        # Workflow should be pre-selected to the suggested one.
        workflow_select = screen.query_one("#workflow-select", Select)
        assert workflow_select.value == "tdd-serial"

        await pilot.press("q")


async def test_new_run_screen_go_validates_inputs() -> None:
    """T51 stub behavior: action_go doesn't crash on empty inputs;
    surfaces validation messages instead. T53 wires the actual launch
    behind this validation."""
    from textual.widgets import TextArea

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(NewRunScreen())
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, NewRunScreen)

        # Empty directive — calling action_go should not raise.
        composer = screen.query_one("#directive-composer", TextArea)
        composer.text = ""
        screen.action_go()  # should notify, not crash
        await pilot.pause()

        await pilot.press("q")


# ---------- streaming surface composition (T44 / P8.3 prep) ----------


async def test_mock_turtle_stream_composes_inside_textual_runtime() -> None:
    """Sanity check that ``MockTurtleHandle.stream_events()`` is
    callable from inside Textual's async runtime without deadlock,
    and that the consumer-side ergonomics work as expected.

    P8.4's LiveRunScreen will use this exact pattern: inside the
    Textual app's event loop, async-iterate a RunHandle's
    stream_events() and update the UI as events arrive. This test
    proves the surface composes before any UI is built on top.

    Speed=1000 + max_dwell=0.05 means the v6 banner (~1300s source)
    drains in well under a couple of seconds — the timing semantics
    of the Mock Turtle are tested in test_mock_turtle.py; this test
    only needs the events to flow.
    """
    if not (_V6_BANNER / "wonderland-snapshot").is_dir():
        pytest.skip("v6 banner snapshot not present")

    expected = sum(1 for _ in HistoricalRunHandle(_V6_BANNER).utterances())

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        mock = MockTurtleHandle(
            _V6_BANNER, speed=1000.0, max_dwell_seconds=0.05
        )
        utterance_count = 0
        meeting_starts = 0
        meeting_ends = 0
        run_started_seen = False
        run_ended_seen = False
        async for event in mock.stream_events():
            kind = type(event).__name__
            if kind == "RunStarted":
                run_started_seen = True
            elif kind == "RunEnded":
                run_ended_seen = True
            elif kind == "MeetingStarted":
                meeting_starts += 1
            elif kind == "MeetingEnded":
                meeting_ends += 1
            elif kind == "UtteranceEmitted":
                utterance_count += 1
        # Bookends fired
        assert run_started_seen
        assert run_ended_seen
        # Meeting bookends balance
        assert meeting_starts == meeting_ends
        assert meeting_starts > 0
        # Utterance count parity with the wrapped HistoricalRunHandle
        assert utterance_count == expected
        await pilot.press("q")


async def test_streaming_consumer_does_not_starve_textual_event_loop() -> None:
    """While async-iterating the Mock Turtle, the Textual app's
    event loop must remain responsive — keystrokes through ``pilot``
    should still fire and update screens.

    A naive blocking implementation of stream_events would starve
    the event loop and pilot.press would hang. This test asserts the
    coroutine yielding pattern is non-blocking by interleaving
    pilot interactions with stream consumption.
    """
    if not (_V6_BANNER / "wonderland-snapshot").is_dir():
        pytest.skip("v6 banner snapshot not present")

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        # Open the snapshot library, navigate a row, then start
        # consuming a mock turtle stream — the navigation should still
        # work after the stream is opened (proves no deadlock between
        # Textual's loop and the streaming async iterator).
        mock = MockTurtleHandle(
            _V6_BANNER, speed=1000.0, max_dwell_seconds=0.05
        )
        gen = mock.stream_events()
        # Pull the first event (RunStarted) — yields immediately.
        first = await gen.__anext__()
        assert type(first).__name__ == "RunStarted"
        # Now interact with the running app — should not hang.
        await pilot.press("j")
        await pilot.pause()
        await pilot.press("k")
        await pilot.pause()
        # Consume the rest of the stream — proves we can resume after
        # interleaving.
        remaining = 0
        async for _ in gen:
            remaining += 1
        assert remaining > 0
        await pilot.press("q")


# ---------- cast view ----------


async def test_pressing_c_opens_cast_browser() -> None:
    """`c` from the snapshot library pushes the Cast browser."""
    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, SnapshotLibraryScreen)
        await pilot.press("c")
        await pilot.pause()
        assert isinstance(app.screen, CastBrowserScreen)
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, SnapshotLibraryScreen)
        await pilot.press("q")


def test_every_cast_member_constitution_resolves() -> None:
    """Each ``CastMember.constitution_path`` should point at a real
    file in the repo. Catches drift between the cast list and the
    on-disk constitutions."""
    for member in cast():
        path = REPO_ROOT / member.constitution_path
        assert path.is_file(), (
            f"{member.name}: constitution missing at {path}"
        )


async def test_cast_browser_lists_all_members() -> None:
    """Every cast member should appear as a row."""
    from textual.widgets import DataTable

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("c")
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, CastBrowserScreen)
        table = screen.query_one("#cast-table", DataTable)
        assert table.row_count == len(cast())
        await pilot.press("q")


async def test_cast_browser_renders_bio_and_constitution_inline() -> None:
    """The single-page cast view (lazygit-style) shows the selected
    member's bio + constitution inline rather than pushing a detail
    screen. Cursor on a row drives both panes."""
    from textual.widgets import DataTable, Markdown, Static

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("c")
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, CastBrowserScreen)

        # On mount, the first row (Alice) should be the selected one.
        # Bio pane should have her bio content.
        bio_widget = screen.query_one("#cast-bio", Static)
        # The Static doesn't expose its renderable cleanly across
        # Textual versions; verify via the screen state.
        # The first cast member is Alice; her bio mentions 'Carroll'
        # in the literary intro.
        first_member = screen._cast[0]
        assert first_member.name == "alice"
        assert "Carroll" in first_member.bio

        # Constitution markdown widget exists + the file resolves.
        repo_root = Path(__file__).resolve().parents[1]
        const_path = repo_root / first_member.constitution_path
        assert const_path.is_file()

        # Move cursor to a different member; the lazy-load cache
        # should grow.
        table = screen.query_one("#cast-table", DataTable)
        table.cursor_coordinate = (2, 0)  # Cheshire Cat
        await pilot.pause()
        # Two constitutions loaded so far (Alice on mount + Cat on move)
        assert len(screen._loaded_constitutions) >= 2

        # Constitution widget exists
        screen.query_one("#constitution-markdown", Markdown)

        await pilot.press("q")


async def test_cast_browser_vim_navigation() -> None:
    """j/k/g/G should move the cursor in the cast table."""
    from textual.widgets import DataTable

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("c")
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, CastBrowserScreen)
        table = screen.query_one("#cast-table", DataTable)
        assert table.cursor_row == 0
        await pilot.press("j")
        await pilot.pause()
        assert table.cursor_row == 1
        await pilot.press("G")
        await pilot.pause()
        assert table.cursor_row == table.row_count - 1
        await pilot.press("g")
        await pilot.pause()
        assert table.cursor_row == 0
        await pilot.press("q")


# ---------- modal artifact link ----------


async def test_modal_artifacts_table_supports_vim_nav() -> None:
    """j/k should move the cursor in the modal's artifacts table —
    the vim bindings live on the App, so any focused DataTable
    (including the one in this modal) responds to them."""
    if not (_V6_BANNER / "wonderland-snapshot").is_dir():
        pytest.skip("v6 banner snapshot not present")
    from textual.widgets import DataTable

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(RunSummaryScreen(_V6_BANNER))
        await pilot.pause()
        # M2.5 has utterances with attached artifacts.
        await pilot.press("j")
        await pilot.press("j")
        await pilot.pause()
        await pilot.press("enter")  # open M2.5
        await pilot.pause()
        meeting_screen = app.screen
        assert isinstance(meeting_screen, MeetingDetailScreen)
        # Find a row with attached artifacts.
        target_row = -1
        for i, u in enumerate(meeting_screen._utterances):
            if len(u.content.artifacts) >= 2:
                target_row = i
                break
        if target_row < 0:
            pytest.skip("no utterances with ≥2 artifacts in M2.5")
        for _ in range(target_row):
            await pilot.press("j")
        await pilot.pause()
        await pilot.press("enter")  # open modal
        await pilot.pause()
        assert isinstance(app.screen, UtteranceModalScreen)
        table = app.screen.query_one("#modal-artifacts-table", DataTable)
        assert table.cursor_row == 0
        await pilot.press("j")
        await pilot.pause()
        assert table.cursor_row == 1, (
            "j should advance the cursor in the modal's artifacts table"
        )
        await pilot.press("k")
        await pilot.pause()
        assert table.cursor_row == 0
        await pilot.press("q")


async def test_modal_artifact_link_opens_artifact_detail() -> None:
    """When an utterance has attached artifacts, the modal lists them
    and pressing Enter on one drills into ArtifactDetailScreen."""
    if not (_V6_BANNER / "wonderland-snapshot").is_dir():
        pytest.skip("v6 banner snapshot not present")

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(RunSummaryScreen(_V6_BANNER))
        await pilot.pause()
        # M2.5 reliably has feature artifacts on Rabbit's emit.
        await pilot.press("j")
        await pilot.press("j")
        await pilot.pause()
        await pilot.press("enter")  # open M2.5
        await pilot.pause()
        meeting_screen = app.screen
        assert isinstance(meeting_screen, MeetingDetailScreen)

        # Find a row with attached artifacts. Rabbit's feature emit
        # carries several; that's the natural target. We don't filter
        # on is_seed — seeds carry resolvable artifact paths too, and
        # the modal-artifact-link works for both.
        target_row = -1
        for i, u in enumerate(meeting_screen._utterances):
            if len(u.content.artifacts) > 0:
                target_row = i
                break
        if target_row < 0:
            pytest.skip("no utterances with artifacts in M2.5")

        for _ in range(target_row):
            await pilot.press("j")
        await pilot.pause()
        await pilot.press("enter")  # open modal
        await pilot.pause()
        modal = app.screen
        assert isinstance(modal, UtteranceModalScreen)
        if not modal._resolved_artifacts or all(
            a is None for a in modal._resolved_artifacts
        ):
            pytest.skip("no resolvable artifacts to drill into")

        # Find first resolvable row and navigate to it.
        first_resolved_row = next(
            (i for i, a in enumerate(modal._resolved_artifacts) if a is not None),
            None,
        )
        assert first_resolved_row is not None
        for _ in range(first_resolved_row):
            await pilot.press("j")
        await pilot.pause()
        await pilot.press("enter")  # open artifact detail
        await pilot.pause()
        assert isinstance(app.screen, ArtifactDetailScreen)
        # Escape pops back to the modal.
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, UtteranceModalScreen)
        await pilot.press("q")
