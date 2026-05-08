"""Cast view — browse the characters that staff Wonderland.

Two screens:
  - ``CastBrowserScreen``: list of all cast members with their role
    + characteristic failure mode
  - ``CastMemberDetailScreen``: drill into one member; shows the
    high-level "what they do in the system" summary, then the full
    constitution markdown rendered below.

Reachable from the Snapshot Library via the ``c`` binding. The cast
is the same regardless of which snapshot's open — it's the team
itself, not a per-run thing.
"""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Markdown, Static

from wonderland.cast import CastMember, cast


# Repo root resolved from this file's location — same convention as
# the snapshot-library's default snapshot_root.
_REPO_ROOT = Path(__file__).resolve().parents[4]


class CastBrowserScreen(Screen[None]):
    """List the characters in the system."""

    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
        Binding("enter", "open_selected", "Open", show=True),
        # Vim nav (j/k/g/G) is provided by WonderlandApp.
    ]

    def __init__(self) -> None:
        super().__init__()
        self._cast: list[CastMember] = cast()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical():
            yield Static(
                "[b]The Cast[/b]    "
                "[dim]The team that staffs Wonderland[/dim]",
                id="cast-header",
            )
            yield DataTable(id="cast-table", cursor_type="row")
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
        table.focus()

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_open_selected(self) -> None:
        table = self.query_one("#cast-table", DataTable)
        row = table.cursor_row
        if row is None or row < 0 or row >= len(self._cast):
            return
        self.app.push_screen(CastMemberDetailScreen(self._cast[row]))

    def on_data_table_row_selected(
        self, _event: DataTable.RowSelected
    ) -> None:
        self.action_open_selected()


class CastMemberDetailScreen(Screen[None]):
    """Detail view for one character — high-level role summary plus
    the constitution markdown rendered below it."""

    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
    ]

    def __init__(self, member: CastMember) -> None:
        super().__init__()
        self.member = member

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical():
            yield Static(id="member-header")
            yield Static(id="member-summary")
            yield Static(
                "[b]Constitution[/b]    "
                "[dim](the character speaking in their own voice)[/dim]",
                id="constitution-label",
            )
            with VerticalScroll(id="constitution-scroll"):
                yield Markdown(id="constitution-markdown")
        yield Footer()

    def on_mount(self) -> None:
        m = self.member
        header_lines = [
            f"[b]{m.display_name}[/b]    [dim]{m.role}[/dim]",
            f"[b]Failure mode:[/b] {m.failure_mode}",
        ]
        self.query_one("#member-header", Static).update("\n".join(header_lines))

        # Role summary: the outside-view "what they do in the system".
        self.query_one("#member-summary", Static).update(m.summary)

        # Constitution: the in-character voice.
        path = _REPO_ROOT / m.constitution_path
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            content = (
                f"# Failed to load constitution\n\n"
                f"Tried path: {path}\n\n"
                f"Error: {exc}"
            )
        self.query_one("#constitution-markdown", Markdown).update(content)

    def action_back(self) -> None:
        self.app.pop_screen()


__all__ = ["CastBrowserScreen", "CastMemberDetailScreen"]
