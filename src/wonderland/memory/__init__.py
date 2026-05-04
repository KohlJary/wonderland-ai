"""Per-agent memory layers — the SAM-equivalent.

Per WONDERLAND_SPEC §8. Each agent owns its memory; cross-agent
observations flow through the Caucus, not through shared storage. This
package will grow:

- ``episodic`` (T5) — every utterance the agent produced or observed
- ``semantic`` (T-future) — distilled beliefs, compacted over time
- ``relational`` (T-future) — per-other-agent notes
"""

from wonderland.memory.episodic import EpisodicStore

__all__ = ["EpisodicStore"]
