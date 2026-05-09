"""Analyses view — read the project's field-notes corpus from
inside the TUI.

Single-page lazygit-style layout: list of all analyses at the top
(numbered + titled), markdown content of the selected one below.
Selection drives content (cursor moves on the list re-render the
viewer). The same shape Cast view uses; the same shape live-watch
uses for the meeting/transcript split.

The analyses are the project's load-bearing thinking. Surfacing
them in the TUI means a fresh ``pip install`` user can browse
'why is this framework the way it is' without leaving the
terminal — answers the legibility question the README's call-to-
action couldn't quite reach on its own.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Markdown, Static

from wonderland.analyses import AnalysisEntry, list_analyses, load_analysis


class AnalysesScreen(Screen[None]):
    """List + markdown-render the analyses on a single page."""

    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
        # Vim nav (j/k/g/G/H/L) is provided by WonderlandApp.
    ]

    def __init__(self) -> None:
        super().__init__()
        self._entries: list[AnalysisEntry] = list_analyses()
        self._loaded: dict[str, str] = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical():
            yield Static(
                "[b]Analyses[/b]    "
                "[dim]The project's field notes — what each run revealed[/dim]",
                id="analyses-header",
            )
            yield DataTable(id="analyses-table", cursor_type="row")
            yield Static(id="analysis-meta")
            with VerticalScroll(id="analysis-scroll"):
                yield Markdown(id="analysis-markdown")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#analyses-table", DataTable)
        table.clear(columns=True)
        table.add_columns("#", "Title")
        for e in self._entries:
            number_str = (
                f"{e.number:03d}" if e.number != 9999 else "—"
            )
            title = e.title
            if title.lower().startswith("analysis "):
                # 'Analysis 032 — TDD-serial v3...' → strip prefix
                # since the # column already shows it.
                idx = title.find(" — ")
                if idx > 0:
                    title = title[idx + 3:]
            if len(title) > 70:
                title = title[:70] + "…"
            table.add_row(number_str, title)
        # Prime with the most recent — they're sorted ascending so
        # cursor on the last row is the freshest analysis.
        if self._entries:
            last = len(self._entries) - 1
            table.cursor_coordinate = (last, 0)
            self._render_analysis(last)
        else:
            self.query_one("#analysis-meta", Static).update(
                "[dim](no analyses found — bundled at "
                "src/wonderland/closet/analyses/)[/dim]"
            )
        table.focus()

    def _render_analysis(self, row: int) -> None:
        if row < 0 or row >= len(self._entries):
            return
        e = self._entries[row]
        # Cache the loaded content so cycling back doesn't re-read.
        if e.slug not in self._loaded:
            try:
                self._loaded[e.slug] = load_analysis(e.slug)
            except OSError as exc:
                self._loaded[e.slug] = (
                    f"# Failed to load analysis\n\n"
                    f"Tried: {e.path}\n\n"
                    f"Error: {exc}"
                )
        meta = (
            f"[b]{e.title}[/b]    "
            f"[dim]{e.path.name}[/dim]"
        )
        self.query_one("#analysis-meta", Static).update(meta)
        self.query_one("#analysis-markdown", Markdown).update(
            self._loaded[e.slug]
        )

    def on_data_table_row_highlighted(
        self, event: DataTable.RowHighlighted
    ) -> None:
        if event.data_table.id != "analyses-table":
            return
        if event.cursor_row is None:
            return
        self._render_analysis(event.cursor_row)

    def action_back(self) -> None:
        self.app.pop_screen()


__all__ = ["AnalysesScreen"]
