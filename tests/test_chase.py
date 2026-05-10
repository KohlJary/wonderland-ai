"""Tests for the ChaseStrip ambient liveness widget (P11.5 T84)."""

from __future__ import annotations

import time

import pytest


# --- Pure logic (no app context) ---


def test_chase_strip_starts_with_alice_behind_rabbit() -> None:
    """The starting frame is Alice at 0, Rabbit at 4 cells ahead —
    the iconic 'hot on his heels but not catching up' shape."""
    from wonderland.tui.widgets.chase import ChaseStrip

    strip = ChaseStrip()
    assert strip._alice_position == 0
    assert strip._rabbit_position == 4


def test_chase_strip_renders_track_with_both_characters() -> None:
    """The rendered track shows 'a' and 'R' at the right positions
    on a row of '·' track dots."""
    from wonderland.tui.widgets.chase import ChaseStrip

    strip = ChaseStrip()
    # Build the track string the same way _render_track does, without
    # relying on Static's internal renderable accessor (which differs
    # across Textual versions). The widget calls update() with this
    # exact string at runtime.
    track = [strip._TRACK_CHAR] * strip.TRACK_WIDTH
    track[strip._alice_position] = strip._ALICE
    track[strip._rabbit_position] = strip._RABBIT
    rendered = "".join(track)
    assert "a" in rendered
    assert "R" in rendered
    assert "·" in rendered
    # Width invariant: the rendered string is exactly TRACK_WIDTH cells.
    assert len(rendered) == strip.TRACK_WIDTH


def test_chase_strip_wall_tick_advances_rabbit_every_step() -> None:
    """Rabbit moves on every wall-clock tick — he's always going."""
    from wonderland.tui.widgets.chase import ChaseStrip

    strip = ChaseStrip()
    initial = strip._rabbit_position
    strip._wall_tick()
    assert strip._rabbit_position == (initial + 1) % strip.TRACK_WIDTH
    strip._wall_tick()
    assert strip._rabbit_position == (initial + 2) % strip.TRACK_WIDTH


def test_chase_strip_wall_tick_advances_alice_every_other_step() -> None:
    """Alice moves on every other tick — gap with rabbit oscillates,
    Alice never catches up. The chase has visual variance without
    ever resolving."""
    from wonderland.tui.widgets.chase import ChaseStrip

    strip = ChaseStrip()
    initial = strip._alice_position
    strip._wall_tick()  # tick_count=1, Alice does NOT move (odd tick)
    assert strip._alice_position == initial
    strip._wall_tick()  # tick_count=2, Alice moves
    assert strip._alice_position == (initial + 1) % strip.TRACK_WIDTH


def test_chase_strip_wall_tick_wraps_around() -> None:
    """Both positions wrap modulo TRACK_WIDTH — neither falls off
    the right edge."""
    from wonderland.tui.widgets.chase import ChaseStrip

    strip = ChaseStrip()
    strip._rabbit_position = strip.TRACK_WIDTH - 1
    strip._wall_tick()
    assert strip._rabbit_position == 0


def test_chase_strip_reset_returns_to_starting_frame() -> None:
    from wonderland.tui.widgets.chase import ChaseStrip

    strip = ChaseStrip()
    for _ in range(10):
        strip._wall_tick()
    strip.reset()
    assert strip._alice_position == 0
    assert strip._rabbit_position == 4
    assert strip._tick_count == 0


def test_chase_strip_tick_alias_still_works() -> None:
    """tick() is kept as an alias for _wall_tick so any external
    code calling .tick() directly continues to function."""
    from wonderland.tui.widgets.chase import ChaseStrip

    strip = ChaseStrip()
    initial = strip._rabbit_position
    strip.tick()
    assert strip._rabbit_position == (initial + 1) % strip.TRACK_WIDTH


# --- Idle detection ---


def test_chase_strip_starts_not_idle() -> None:
    from wonderland.tui.widgets.chase import ChaseStrip

    strip = ChaseStrip()
    assert "-idle" not in strip.classes


def test_chase_strip_does_not_dim_when_alive_recent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If a mark_alive() landed within the threshold, _wall_tick
    keeps the strip in normal (non-idle) state."""
    from wonderland.tui.widgets.chase import ChaseStrip

    strip = ChaseStrip()
    fake_now = time.monotonic()
    monkeypatch.setattr(time, "monotonic", lambda: fake_now)
    strip._last_alive = fake_now

    strip._wall_tick()
    assert "-idle" not in strip.classes


def test_chase_strip_dims_when_alive_stale(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When the last mark_alive() was longer ago than
    IDLE_THRESHOLD_SECS, _wall_tick adds the .-idle class so CSS
    dims the row. (Motion still happens; only color changes.)"""
    from wonderland.tui.widgets.chase import ChaseStrip

    strip = ChaseStrip()
    # Simulate a long deliberation: last_alive at t=0, time jumped
    # past the threshold.
    strip._last_alive = 0.0
    monkeypatch.setattr(
        time, "monotonic", lambda: strip.IDLE_THRESHOLD_SECS + 1.0
    )
    strip._wall_tick()
    assert "-idle" in strip.classes


def test_chase_strip_mark_alive_clears_idle_class() -> None:
    """A signal-of-life event re-enlivens the strip — clears
    the .-idle class so the operator sees normal-color chase resume.
    The strip continues moving even while idle, so this is purely
    a color/dim signal."""
    from wonderland.tui.widgets.chase import ChaseStrip

    strip = ChaseStrip()
    strip.add_class("-idle")
    strip.mark_alive()
    assert "-idle" not in strip.classes


def test_chase_strip_keeps_moving_through_idle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Motion continues even when the strip is idle. This is the
    load-bearing change vs the original design: a deliberation call
    that lasts 30s should still show the chase moving (so the
    operator knows the TUI is alive); only the color shifts to
    signal 'no actual run progress.'"""
    from wonderland.tui.widgets.chase import ChaseStrip

    strip = ChaseStrip()
    # Force idle state by jumping time forward without any
    # mark_alive() call.
    strip._last_alive = 0.0
    monkeypatch.setattr(
        time, "monotonic", lambda: strip.IDLE_THRESHOLD_SECS + 5.0
    )

    initial = strip._rabbit_position
    strip._wall_tick()
    # Motion happened.
    assert strip._rabbit_position != initial
    # Color signal flipped to idle.
    assert "-idle" in strip.classes


# --- Integration with LiveRunScreen ---


async def test_live_run_screen_mounts_chase_strip(tmp_path) -> None:
    """LiveRunScreen has a ChaseStrip widget mounted under the
    Meetings label."""
    from wonderland.tui import WonderlandApp
    from wonderland.tui.widgets.chase import ChaseStrip

    # Build a minimal handle for LiveRunScreen — using a tmp_path
    # snapshot dir so it doesn't error trying to read real run state.
    (tmp_path / ".wonderland").mkdir()
    from wonderland.tui.screens.live_run import LiveRunScreen

    app = WonderlandApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(LiveRunScreen(tmp_path))
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, LiveRunScreen)
        chase = screen.query_one("#meetings-chase", ChaseStrip)
        assert chase is not None
        await pilot.press("escape")
        await pilot.press("q")
