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
from wonderland.tui import WonderlandApp
from wonderland.tui.screens.artifact_browser import (
    ArtifactBrowserScreen,
    ArtifactDetailScreen,
)
from wonderland.tui.screens.cast import (
    CastBrowserScreen,
    CastMemberDetailScreen,
)
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


async def test_cast_member_detail_renders_summary_and_constitution() -> None:
    """Enter on a cast row drills into the detail screen, which
    populates both the role summary and the rendered constitution."""
    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("c")
        await pilot.pause()
        await pilot.press("enter")  # open first member (Alice)
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, CastMemberDetailScreen)
        assert screen.member.name == "alice"
        # The constitution path the screen will load must exist on disk.
        repo_root = Path(__file__).resolve().parents[1]
        const_path = repo_root / screen.member.constitution_path
        assert const_path.is_file(), (
            f"constitution missing: {const_path}"
        )
        # Pop back to browser
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, CastBrowserScreen)
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
