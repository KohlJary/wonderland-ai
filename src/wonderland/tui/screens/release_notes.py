"""Release-notes viewer — browse versioned release notes from
inside the TUI.

Same shape as ``AnalysesScreen``: list of versions (newest first)
on top, markdown content of the selected one below. Selection
drives content. Reachable from the project library home action
menu.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Markdown, Static

from wonderland.release_notes import (
    ReleaseNote,
    list_release_notes,
    load_release_note,
)


class ReleaseNotesScreen(Screen[None]):
    """List + markdown-render the release notes on a single page."""

    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
        # Vim nav (j/k/g/G/H/L) is provided by WonderlandApp.
    ]

    def __init__(self) -> None:
        super().__init__()
        self._entries: list[ReleaseNote] = list_release_notes()
        self._loaded: dict[str, str] = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical():
            yield Static(
                "[b]Release notes[/b]    "
                "[dim]What shipped in each version — newest first[/dim]",
                id="release-notes-header",
            )
            yield DataTable(
                id="release-notes-table", cursor_type="row"
            )
            yield Static(id="release-note-meta")
            with VerticalScroll(id="release-note-scroll"):
                yield Markdown(id="release-note-markdown")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#release-notes-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Version", "File")
        for entry in self._entries:
            table.add_row(entry.version, entry.path.name)
        if self._entries:
            table.cursor_coordinate = (0, 0)
            self._render_note(0)
        else:
            self.query_one(
                "#release-note-meta", Static
            ).update(
                "[dim](no release notes found — should live at "
                "release-notes/<version>.md at the repo root)[/dim]"
            )
        table.focus()

    def _render_note(self, row: int) -> None:
        if row < 0 or row >= len(self._entries):
            return
        entry = self._entries[row]
        if entry.version not in self._loaded:
            try:
                self._loaded[entry.version] = load_release_note(
                    entry.version
                )
            except OSError as exc:
                self._loaded[entry.version] = (
                    f"# Failed to load {entry.version}\n\n"
                    f"Tried: {entry.path}\n\nError: {exc}"
                )
        meta = (
            f"[b]{entry.version}[/b]    "
            f"[dim]{entry.path.name}[/dim]"
        )
        self.query_one("#release-note-meta", Static).update(meta)
        self.query_one(
            "#release-note-markdown", Markdown
        ).update(self._loaded[entry.version])

    def on_data_table_row_highlighted(
        self, event: DataTable.RowHighlighted
    ) -> None:
        if event.data_table.id != "release-notes-table":
            return
        if event.cursor_row is None:
            return
        self._render_note(event.cursor_row)

    def action_back(self) -> None:
        self.app.pop_screen()


__all__ = ["ReleaseNotesScreen"]
