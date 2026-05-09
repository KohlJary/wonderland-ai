"""Cast view — browse the characters that staff Wonderland.

Single-page lazygit-style layout (per the project_tui_lazygit_principle
memory): cast member list at top, bio + constitution side-by-side
below, all filtered by the row currently selected in the list. Tab
cycles focus across the panes; cursor moves drive the content.

Reachable from the home view via the ``c`` binding or the visible
'The Cast' button. The cast is the same regardless of which run's
open — it's the team itself, not a per-run thing.
"""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Markdown, Static

from wonderland.cast import CastMember, cast


# Repo root resolved from this file's location — same convention as
# the snapshot-library's default snapshot_root.
_REPO_ROOT = Path(__file__).resolve().parents[4]


class CastBrowserScreen(Screen[None]):
    """Single-page lazygit-shape cast view.

    Top: cast list (DataTable, focusable). Cursor row drives the
    content of the panes below.

    Below: side-by-side panes — Bio (left, who the character is +
    how the literary character shapes the constitution) +
    Constitution (right, the in-character voice). Both update as
    the cursor moves in the list.
    """

    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
        # Vim nav (j/k/g/G/H/L) is provided by WonderlandApp.
    ]

    def __init__(self) -> None:
        super().__init__()
        self._cast: list[CastMember] = cast()
        self._loaded_constitutions: dict[str, str] = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical():
            yield Static(
                "[b]The Cast[/b]    "
                "[dim]The team that staffs Wonderland[/dim]",
                id="cast-header",
            )
            yield DataTable(id="cast-table", cursor_type="row")
            yield Static(id="cast-member-header")
            with Horizontal(id="cast-detail-row"):
                with Vertical(id="cast-bio-pane"):
                    yield Static("[b]Bio[/b]", id="cast-bio-label")
                    with VerticalScroll(id="cast-bio-scroll"):
                        yield Static(id="cast-bio")
                with Vertical(id="cast-constitution-pane"):
                    yield Static(
                        "[b]Constitution[/b]    "
                        "[dim](the character speaking)[/dim]",
                        id="constitution-label",
                    )
                    with VerticalScroll(id="constitution-scroll"):
                        yield Markdown(id="constitution-markdown")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#cast-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Name", "Role", "Characteristic failure mode")
        for member in self._cast:
            failure_short = member.failure_mode.split(" — ", 1)[0]
            if len(failure_short) > 60:
                failure_short = failure_short[:60] + "…"
            table.add_row(member.display_name, member.role, failure_short)
        # Prime the detail panes with row 0 (Alice by default).
        if self._cast:
            self._render_member_detail(0)
        table.focus()

    def _render_member_detail(self, row: int) -> None:
        """Update the bio + constitution panes for the cast member at
        ``row`` in the table. Called on cursor moves and on mount."""
        if row < 0 or row >= len(self._cast):
            return
        m = self._cast[row]

        header_lines = [
            f"[b]{m.display_name}[/b]    [dim]{m.role}[/dim]",
            f"[b]Failure mode:[/b] {m.failure_mode}",
        ]
        self.query_one("#cast-member-header", Static).update(
            "\n".join(header_lines)
        )

        # Bio — character-and-system intro
        self.query_one("#cast-bio", Static).update(m.bio)

        # Constitution — load lazily, cache for repeat selections
        if m.name not in self._loaded_constitutions:
            path = _REPO_ROOT / m.constitution_path
            try:
                self._loaded_constitutions[m.name] = path.read_text(
                    encoding="utf-8", errors="replace"
                )
            except OSError as exc:
                self._loaded_constitutions[m.name] = (
                    f"# Failed to load constitution\n\n"
                    f"Tried path: {path}\n\n"
                    f"Error: {exc}"
                )
        self.query_one("#constitution-markdown", Markdown).update(
            self._loaded_constitutions[m.name]
        )

    def on_data_table_row_highlighted(
        self, event: DataTable.RowHighlighted
    ) -> None:
        """Cursor moved in the cast table → re-render bio +
        constitution panes for the newly-highlighted row. The
        lazygit-style filtering pattern: selection drives content."""
        if event.data_table.id != "cast-table":
            return
        if event.cursor_row is None:
            return
        self._render_member_detail(event.cursor_row)

    def action_back(self) -> None:
        self.app.pop_screen()


__all__ = ["CastBrowserScreen"]
