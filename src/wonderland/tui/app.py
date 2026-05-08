"""Top-level Textual app. Owns global state (snapshot search root,
current handle) and pushes/pops screens."""

from __future__ import annotations

from pathlib import Path

from textual.app import App
from textual.binding import Binding
from textual.widgets import DataTable

from wonderland.tui.screens.snapshot_library import SnapshotLibraryScreen
from wonderland.tui.themes import (
    DEFAULT_THEME_NAME,
    WONDERLAND_THEMES,
)


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

    def __init__(self, snapshot_root: Path | None = None) -> None:
        super().__init__()
        self.snapshot_root = snapshot_root or _DEFAULT_SNAPSHOT_ROOT

    def on_mount(self) -> None:
        # Register the Wonderland-flavored themes and set the project
        # default. Built-in Textual themes (gruvbox, dracula, etc.)
        # remain available — users can `app.theme = "..."` to pick one.
        for theme in WONDERLAND_THEMES:
            self.register_theme(theme)
        self.theme = DEFAULT_THEME_NAME
        self.push_screen(SnapshotLibraryScreen(self.snapshot_root))

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
