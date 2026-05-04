"""Per-character agent implementations.

Each character is a concrete ``WonderlandAgent`` subclass that loads its
constitution from ``constitutions/<name>.md``, wires its
``EngagementRules``, and overrides ``deliberate()`` to give the
character its voice.
"""

from wonderland.agents.cheshire_cat import CheshireCat, cheshire_cat_rules

__all__ = ["CheshireCat", "cheshire_cat_rules"]
