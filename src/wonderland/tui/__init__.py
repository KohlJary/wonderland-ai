"""Wonderland TUI — local interface for browsing runs and (later)
watching live ones. Built on Textual.

P8.2 (this commit): bootstrap with snapshot-library + run-summary
screens. Replay-first per the P8 skeleton — every iteration cycle
uses real run data from analyses/data/<NNN>/ snapshots.

Launch via the `wonderland-tui` script (after pip install) or:

    uv run python -m wonderland.tui

Future sub-phases will add more screens (Cast, Workflow Picker,
Run Watcher with replay, etc.) layered on top of this skeleton.
"""

from wonderland.tui.app import WonderlandApp

__all__ = ["WonderlandApp"]
