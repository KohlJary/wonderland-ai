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

from wonderland.tui import WonderlandApp
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
