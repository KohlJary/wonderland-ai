"""ChaseStrip — Alice chasing the White Rabbit, ambient liveness
indicator on the live-run screen (P11.5 T84).

A horizontal track where Alice ('a') chases the White Rabbit ('R')
along a row of dots. Each `tick()` call advances them one step.
Cosmetic by intent, diagnostic in effect: the widget is wired into
the LiveRunScreen's AgentActed handler, so the chase only moves when
agents are actually emitting utterances. When the run is stuck (no
acts landing for N seconds), the strip dims — operators get a
passive ambient signal of "we're not moving" without waiting for
Dodo's nudge ladder to fire.

Single-cell characters by default for terminal-width safety. Emoji
upgrade is easy if a future settings flag enables it; the track
math + render path stay the same.
"""

from __future__ import annotations

import time

from textual.reactive import reactive
from textual.widgets import Static


class ChaseStrip(Static):
    """Horizontal chase indicator with idle-detection dimming.

    Public surface:
      - ``tick()``: advance both characters one step. Call from
        whatever event signals "the run is alive."
      - ``reset()``: snap both back to their starting positions.

    Internal:
      - ``_alice_position`` / ``_rabbit_position``: track indices.
        Rabbit is always 1 step ahead-ish; Alice catches up
        occasionally so the chase has visible variance.
      - ``_last_tick``: monotonic timestamp of last tick. Read by
        ``_check_idle`` to decide whether to add the .idle class.
    """

    DEFAULT_CSS = """
    ChaseStrip {
        height: 1;
        padding: 0 1;
        color: $accent;
        background: $surface;
        text-align: left;
    }
    ChaseStrip.-idle {
        color: $foreground 30%;
    }
    """

    TRACK_WIDTH: int = 28
    IDLE_THRESHOLD_SECS: float = 15.0
    _CHECK_IDLE_INTERVAL_SECS: float = 2.0

    _ALICE: str = "a"
    _RABBIT: str = "R"
    _TRACK_CHAR: str = "·"

    _alice_position: reactive[int] = reactive(0)
    _rabbit_position: reactive[int] = reactive(4)

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        # Stagger Alice + Rabbit so they don't collide on tick 1.
        # 4 cells of separation reads as "Alice is hot on the
        # Rabbit's heels but not catching up" — the iconic frame.
        self._alice_position = 0
        self._rabbit_position = 4
        self._last_tick: float = time.monotonic()
        self._tick_count: int = 0

    def on_mount(self) -> None:
        self._render_track()
        self.set_interval(
            self._CHECK_IDLE_INTERVAL_SECS, self._check_idle
        )

    def tick(self) -> None:
        """Advance the chase by one step. Called externally on each
        signal-of-life event (AgentActed in LiveRunScreen). The
        Rabbit moves every tick; Alice moves on alternating ticks
        so the gap oscillates — gives the chase visual variance
        without ever resolving (Alice never catches the Rabbit, of
        course)."""
        self._tick_count += 1
        self._rabbit_position = (
            self._rabbit_position + 1
        ) % self.TRACK_WIDTH
        if self._tick_count % 2 == 0:
            self._alice_position = (
                self._alice_position + 1
            ) % self.TRACK_WIDTH
        self._last_tick = time.monotonic()
        self.remove_class("-idle")
        self._render_track()

    def reset(self) -> None:
        """Snap both characters back to the starting frame. Useful
        for run-restart scenarios."""
        self._alice_position = 0
        self._rabbit_position = 4
        self._last_tick = time.monotonic()
        self._tick_count = 0
        self.remove_class("-idle")
        self._render_track()

    def _check_idle(self) -> None:
        """Periodic check: if no tick fired in the last N seconds,
        flag as idle so the CSS dims the row. The diagnostic value:
        operator can glance at the screen and see 'we're frozen'
        without waiting for Dodo's nudge ladder to escalate."""
        if time.monotonic() - self._last_tick > self.IDLE_THRESHOLD_SECS:
            self.add_class("-idle")

    def _render_track(self) -> None:
        track = [self._TRACK_CHAR] * self.TRACK_WIDTH
        # Rabbit takes precedence if both happen to land on the
        # same cell (Alice never catches him; he's always rendered
        # on top to reinforce the "Rabbit ahead" frame).
        track[self._alice_position] = self._ALICE
        track[self._rabbit_position] = self._RABBIT
        self.update("".join(track))


__all__ = ["ChaseStrip"]
