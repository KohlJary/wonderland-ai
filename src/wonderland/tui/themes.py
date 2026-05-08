"""Wonderland-flavored color themes for the TUI.

Each theme is a Textual ``Theme`` keyed on a meeting or character —
swap with the ``t`` binding from any screen. The TCSS uses design
tokens (``$primary``, ``$accent``, ``$surface``, ``$panel``, etc.)
so a theme switch propagates without the stylesheet caring.

The palettes:
  - Tea Party: cyan + purple, the project's default voice
  - Looking Glass: silver monochrome, dignified, signal-not-flash
  - Trial: red on black, Queen of Hearts territory
  - Caucus: green + amber, M1's energetic pluralism

Built-in Textual themes (gruvbox, dracula, nord, etc.) remain
available via ``App.theme = "<name>"`` for users who want them.
"""

from __future__ import annotations

from textual.theme import Theme


TEA_PARTY = Theme(
    name="wonderland-tea-party",
    primary="#b794f4",      # light purple
    secondary="#00d9d9",    # cyan
    accent="#00d9d9",       # cyan again — accent matches secondary intentionally
    warning="#f6ad55",      # warm amber
    error="#fc8181",        # soft red
    success="#68d391",      # green
    foreground="#e6e6f0",
    background="#0a0a14",
    surface="#1f1438",
    panel="#2d1b4e",
    boost="#1a0f2e",
    dark=True,
)


LOOKING_GLASS = Theme(
    name="wonderland-looking-glass",
    primary="#c8c8d0",      # silver
    secondary="#9a9aa8",    # dimmer silver
    accent="#e6e6f0",       # near-white
    warning="#d4a574",      # muted amber
    error="#c47474",        # muted red
    success="#7e9c84",      # muted green
    foreground="#e6e6f0",
    background="#0d0d10",
    surface="#1c1c22",
    panel="#26262e",
    boost="#16161a",
    dark=True,
)


TRIAL = Theme(
    name="wonderland-trial",
    primary="#e53e3e",      # heart red
    secondary="#f6e05e",    # crown gold
    accent="#fc8181",       # softer red for cursor
    warning="#f6ad55",
    error="#feb2b2",
    success="#9ae6b4",
    foreground="#f7e6e6",
    background="#0c0303",
    surface="#2c0a0a",
    panel="#430f0f",
    boost="#1a0606",
    dark=True,
)


CAUCUS = Theme(
    name="wonderland-caucus",
    primary="#68d391",      # spring green
    secondary="#f6ad55",    # warm amber
    accent="#9ae6b4",       # lighter green
    warning="#f6e05e",
    error="#fc8181",
    success="#68d391",
    foreground="#e8efe6",
    background="#0a1108",
    surface="#1a2615",
    panel="#243525",
    boost="#13201a",
    dark=True,
)


# Cycling order — Tea Party first since it's the project's default voice.
WONDERLAND_THEMES: list[Theme] = [TEA_PARTY, LOOKING_GLASS, TRIAL, CAUCUS]
DEFAULT_THEME_NAME = TEA_PARTY.name


__all__ = [
    "TEA_PARTY",
    "LOOKING_GLASS",
    "TRIAL",
    "CAUCUS",
    "WONDERLAND_THEMES",
    "DEFAULT_THEME_NAME",
]
