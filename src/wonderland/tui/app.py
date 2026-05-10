"""Top-level Textual app. Owns global state (snapshot search root,
current handle) and pushes/pops screens."""

from __future__ import annotations

from pathlib import Path

from textual.app import App
from textual.binding import Binding
from textual.widgets import DataTable

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

    def on_mount(self) -> None:
        # Register the Wonderland-flavored themes and set the project
        # default. Built-in Textual themes (gruvbox, dracula, etc.)
        # remain available — users can `app.theme = "..."` to pick one.
        for theme in WONDERLAND_THEMES:
            self.register_theme(theme)
        self.theme = DEFAULT_THEME_NAME

        # Push the project library underneath, then maybe push the
        # welcome modal on top. Welcome dismisses back to the library;
        # if the operator has already dismissed welcome (config flag),
        # we skip straight to the library.
        self.push_screen(ProjectLibraryScreen())
        if self._should_show_welcome():
            from wonderland.tui.screens.welcome_modal import WelcomeModal

            self.push_screen(WelcomeModal())

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
