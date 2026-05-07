"""Top-level Textual app. Owns global state (snapshot search root,
current handle) and pushes/pops screens."""

from __future__ import annotations

from pathlib import Path

from textual.app import App
from textual.binding import Binding

from wonderland.tui.screens.snapshot_library import SnapshotLibraryScreen


# Default search root for snapshots — the analyses/data/ directory of
# whatever wonderland-ai checkout the TUI is running in. Resolved
# relative to this file's location so it works whether installed via
# `pip install -e .` or run from a fresh clone.
_DEFAULT_SNAPSHOT_ROOT = (
    Path(__file__).resolve().parents[3] / "analyses" / "data"
)


class WonderlandApp(App):
    """Wonderland TUI root.

    First cut (P8.2): launches into the SnapshotLibraryScreen. Future
    cuts will add a Welcome screen, Cast browser, Run Watcher with
    replay, etc.
    """

    CSS_PATH = "wonderland.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
    ]

    TITLE = "Wonderland"
    SUB_TITLE = "Run inspector"

    def __init__(self, snapshot_root: Path | None = None) -> None:
        super().__init__()
        self.snapshot_root = snapshot_root or _DEFAULT_SNAPSHOT_ROOT

    def on_mount(self) -> None:
        self.push_screen(SnapshotLibraryScreen(self.snapshot_root))


def main() -> int:
    """Entry point for `wonderland-tui` CLI."""
    WonderlandApp().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
