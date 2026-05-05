"""Per-character agent implementations.

Each character is a concrete ``WonderlandAgent`` subclass that loads its
constitution from ``constitutions/<name>.md``, wires its
``EngagementRules``, and overrides ``deliberate()`` to give the
character its voice.
"""

from wonderland.agents.alice import Alice, alice_rules
from wonderland.agents.cheshire_cat import CheshireCat, cheshire_cat_rules
from wonderland.agents.dodo import Dodo, dodo_rules
from wonderland.agents.white_rabbit import WhiteRabbit, white_rabbit_rules

__all__ = [
    "Alice",
    "CheshireCat",
    "Dodo",
    "WhiteRabbit",
    "alice_rules",
    "cheshire_cat_rules",
    "dodo_rules",
    "white_rabbit_rules",
]
