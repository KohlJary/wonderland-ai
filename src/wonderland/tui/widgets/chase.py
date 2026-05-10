"""ChaseStrip — Alice chasing the White Rabbit, ambient liveness
indicator on the live-run screen (P11.5 T84).

A horizontal track where Alice ('a') chases the White Rabbit ('R')
along a row of dots. Two separate signals drive it:

  - **Motion** comes from a wall-clock timer (~500ms). The chase
    moves continuously while the screen is mounted, so the operator
    always sees something moving — including during the long stretches
    where an agent is mid-deliberation and no utterances are landing.
    "TUI is alive" and "run is making progress" are different
    questions; motion answers the first.

  - **Color/dim** shifts based on utterance recency. ``mark_alive()``
    is called from LiveRunScreen on each UtteranceEmitted /
    AgentActed event. If no utterance has landed in
    ``IDLE_THRESHOLD_SECS``, the .-idle class flips on; CSS dims
    the row. Motion keeps going (so the screen still feels alive),
    but the muted color signals "we're not making progress."

This separation matters because the original design tied motion
directly to events and the chase froze entirely during the 10-30s
deliberation calls — exactly when you want a visible "still working"
signal.

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
    TICK_INTERVAL_SECS: float = 0.4

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
        self._last_alive: float = time.monotonic()
        self._tick_count: int = 0

    def on_mount(self) -> None:
        self._render_track()
        # Wall-clock motion. Runs continuously while the screen is
        # mounted — the chase never stops just because a deliberation
        # call is in flight. set_interval ties to the Textual event
        # loop, so the cost is one screen refresh per TICK_INTERVAL.
        self.set_interval(self.TICK_INTERVAL_SECS, self._wall_tick)

    def _wall_tick(self) -> None:
        """Advance the chase by one step on the wall-clock timer +
        re-evaluate idle state. Idle detection is independent of
        motion: motion keeps going while idle (operator sees the
        TUI is alive), but the .-idle class dims the color so the
        muted appearance signals 'no actual run progress.'"""
        self._tick_count += 1
        self._rabbit_position = (
            self._rabbit_position + 1
        ) % self.TRACK_WIDTH
        if self._tick_count % 2 == 0:
            self._alice_position = (
                self._alice_position + 1
            ) % self.TRACK_WIDTH
        # Idle re-eval on every tick — cheap, and snapping to dim
        # within ~400ms of crossing the threshold is the right
        # responsiveness.
        if (
            time.monotonic() - self._last_alive
            > self.IDLE_THRESHOLD_SECS
        ):
            self.add_class("-idle")
        self._render_track()

    def mark_alive(self) -> None:
        """LiveRunScreen calls this on each UtteranceEmitted /
        AgentActed event. Marks the run as actively producing signal
        so the .-idle dim clears. Motion is not affected — this only
        controls the color/dim state."""
        self._last_alive = time.monotonic()
        self.remove_class("-idle")

    # Kept for back-compat with anything that still calls .tick()
    # directly. Maps to the wall-clock tick semantics — useful for
    # tests that want to advance the chase deterministically without
    # waiting for the timer.
    tick = _wall_tick

    def reset(self) -> None:
        """Snap both characters back to the starting frame. Useful
        for run-restart scenarios."""
        self._alice_position = 0
        self._rabbit_position = 4
        self._last_alive = time.monotonic()
        self._tick_count = 0
        self.remove_class("-idle")
        self._render_track()

    def _render_track(self) -> None:
        track = [self._TRACK_CHAR] * self.TRACK_WIDTH
        # Rabbit takes precedence if both happen to land on the
        # same cell (Alice never catches him; he's always rendered
        # on top to reinforce the "Rabbit ahead" frame).
        track[self._alice_position] = self._ALICE
        track[self._rabbit_position] = self._RABBIT
        self.update("".join(track))


__all__ = ["ChaseStrip"]
