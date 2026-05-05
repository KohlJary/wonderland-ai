"""SyntheticConsensusGuard — watches the bus for the §11 anti-pattern.

Per WONDERLAND_SPEC §7 / §11. The framework's most subtle failure
mode: agents with distinct constitutional domains converge on a
shared answer because the LLM's helpful-disposition is a strong
attractor, not because they actually agree from their separate
vantages. This is the multi-agent equivalent of sycophancy, and
nothing about the per-agent guards (each agent's §VIII section
reminds them not to soften their dissent) catches it from outside.

The guard's job is to **notice the pattern and surface it** —
specifically, when N or more agents from distinct constitutional
domains produce stance-similar utterances of the same speech_act
on the same thread within a window. The guard does not silence
anyone; per the spec, "the framework rewards honest disagreement
and surfaces it; it does not reward agents for keeping the peace
at the cost of truth." Surfacing is what this module does.

Design choices, kept honest about the heuristic-vs-strict split:

- **Domain mapping** — extends DOMAIN_PRIMACY (conflict.py) with the
  Tweedles sharing a virtual "implementation" domain (they're a pair
  per tweedle_pair_protocol.md, so two Tweedles agreeing isn't two
  voices) and the Dodo a virtual "orchestration" domain (he doesn't
  issue substantive acts, but the entry keeps the map total).
- **Similarity** — word-shingle Jaccard (cheap, deterministic, no
  LLM round-trip). Catches lexical convergence reliably; misses
  semantic convergence with low lexical overlap. Sufficient for the
  spec's "log + surface in transcripts initially; tighten later"
  framing. Embedding-based similarity is an obvious upgrade path.
- **Substantive-only filter** — procedural acts (nudge, composition,
  escalation, acknowledgment) are excluded from the analysis. They
  are bookkeeping, not positions, and false-positive alerts on the
  Dodo's procedural hum would corrode trust in the guard.
- **Duplicate suppression** — once an alert fires for a given
  (thread, speech_act, agent-set), the guard does not re-fire until
  the agent set changes. Otherwise every subsequent same-set utterance
  re-triggers and the alert log loses signal.
"""

from __future__ import annotations

import asyncio
import contextlib
import re
from collections import deque
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from itertools import combinations
from typing import TYPE_CHECKING

from wonderland.conflict import DOMAIN_PRIMACY
from wonderland.utterance import (
    SpeechAct,
    Utterance,
    is_substantive,
)

if TYPE_CHECKING:
    from wonderland.caucus import Caucus


# --------------------------------------------------------------------- #
# Domain mapping — extends DOMAIN_PRIMACY for the synthetic-consensus check
# --------------------------------------------------------------------- #


def default_agent_domains() -> dict[str, str]:
    """Map agent name → constitutional domain string for similarity grouping.

    Built from ``DOMAIN_PRIMACY`` (the inverse table maps each domain to
    its canonical owning agent), extended with two virtual domains:

    - **implementation** for both Tweedles. The pair shares one domain
      because per the Tweedle Pair Protocol they are a unit; two Tweedles
      agreeing is one constitutional voice, not two.
    - **orchestration** for the Dodo. He doesn't issue substantive
      utterances and is filtered out by the substantive-only check, but
      the entry keeps the map total so the guard never silently skips
      an unmapped agent.
    """
    mapping: dict[str, str] = {
        agent_name: domain.value for domain, agent_name in DOMAIN_PRIMACY.items()
    }
    mapping["tweedledee"] = "implementation"
    mapping["tweedledum"] = "implementation"
    mapping["dodo"] = "orchestration"
    return mapping


# --------------------------------------------------------------------- #
# Shingle + Jaccard
# --------------------------------------------------------------------- #


_WORD_RE = re.compile(r"[a-z0-9]+")


def shingles(body: str, *, size: int = 3) -> set[str]:
    """Return the set of word-shingles (n-grams) of `body`.

    Lowercased, alphanumeric-only tokenization. Falls back to the bare
    word set when the body has fewer words than the shingle size, so a
    one-word "yes" is still comparable.
    """
    words = _WORD_RE.findall(body.lower())
    if len(words) < size:
        return set(words)
    return {" ".join(words[i : i + size]) for i in range(len(words) - size + 1)}


def jaccard(a: set[str], b: set[str]) -> float:
    """Jaccard similarity over two shingle sets. Empty/empty == 0."""
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


# --------------------------------------------------------------------- #
# Alert + guard
# --------------------------------------------------------------------- #


@dataclass(frozen=True)
class ConsensusAlert:
    """Surfaced when the guard detects suspected synthetic consensus.

    The alert is *informational* — it does not silence agents. A
    consumer (the Dodo in a future evolution, or a human reviewer)
    decides whether the consensus is real or synthetic. The
    ``sample_bodies`` are the excerpts a reviewer needs to make that
    judgment without re-reading the thread.
    """

    thread_id: str
    speech_act: SpeechAct
    agents: tuple[str, ...]
    """Names of the agents that triggered the alert. Sorted for stable equality."""
    domains: tuple[str, ...]
    """Distinct constitutional domains those agents represent. Sorted."""
    average_pairwise_similarity: float
    """Average Jaccard across all agent pairs in the set."""
    sample_bodies: tuple[str, ...]
    """One representative body per agent — for the reviewer to inspect."""
    at: datetime
    reason: str


@dataclass
class _ThreadWindow:
    thread_id: str
    recent: deque[Utterance] = field(default_factory=deque)
    alerted: set[tuple[SpeechAct, frozenset[str]]] = field(default_factory=set)


class SyntheticConsensusGuard:
    """Watches the bus; emits ConsensusAlert when distinct-domain agents converge.

    Use as start/stop, with ``alerts()`` as the consumer iterator:

        guard = SyntheticConsensusGuard(bus, min_agents=3, similarity_threshold=0.5)
        await guard.start()
        try:
            async for alert in guard.alerts():
                ...
        finally:
            await guard.stop()

    Defaults are tuned for the framework's first cast-online runs and
    the spec's "log + surface, tighten later" stance. Adjust as the
    Caucus log surfaces real disagreement vs. real synthetic-consensus
    rates.
    """

    def __init__(
        self,
        bus: Caucus,
        *,
        min_agents: int = 3,
        similarity_threshold: float = 0.5,
        window_size: int = 10,
        shingle_size: int = 3,
        agent_to_domain: dict[str, str] | None = None,
        substantive_only: bool = True,
        agent_name: str = "synthetic_consensus_guard",
    ) -> None:
        if min_agents < 2:
            raise ValueError("min_agents must be >= 2 (consensus requires at least two voices)")
        if not 0.0 <= similarity_threshold <= 1.0:
            raise ValueError("similarity_threshold must be in [0.0, 1.0]")
        if window_size < min_agents:
            raise ValueError(
                f"window_size ({window_size}) must be >= min_agents ({min_agents}); "
                "otherwise the window can never contain enough utterances to fire"
            )
        self._bus = bus
        self._min_agents = min_agents
        self._threshold = similarity_threshold
        self._window_size = window_size
        self._shingle_size = shingle_size
        self._agent_to_domain = agent_to_domain or default_agent_domains()
        self._substantive_only = substantive_only

        # Synchronous subscription per the T14 fix — bus publishes between
        # construction and iteration must not be lost.
        self._iterator: AsyncIterator[Utterance] = self._bus.subscribe(agent_name)
        self._threads: dict[str, _ThreadWindow] = {}
        self._alerts: asyncio.Queue[ConsensusAlert] = asyncio.Queue()
        self._consume_task: asyncio.Task[None] | None = None

    # ------------------------------------------------------------------ #
    # Inspection
    # ------------------------------------------------------------------ #

    def known_threads(self) -> list[str]:
        return sorted(self._threads.keys())

    def window_for(self, thread_id: str) -> tuple[Utterance, ...]:
        info = self._threads.get(thread_id)
        return tuple(info.recent) if info else ()

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    async def start(self) -> None:
        self._consume_task = asyncio.create_task(
            self._consume_loop(), name="synthetic-consensus-guard"
        )

    async def stop(self) -> None:
        if self._consume_task is not None and not self._consume_task.done():
            self._consume_task.cancel()
        if self._consume_task is not None:
            with contextlib.suppress(asyncio.CancelledError):
                await self._consume_task
        self._consume_task = None
        with contextlib.suppress(Exception):
            await self._iterator.aclose()  # type: ignore[attr-defined]

    async def alerts(self) -> AsyncIterator[ConsensusAlert]:
        """Yield alerts as they fire. Caller iterates until cancelled."""
        while True:
            alert = await self._alerts.get()
            yield alert

    # ------------------------------------------------------------------ #
    # Internal loop + state
    # ------------------------------------------------------------------ #

    async def _consume_loop(self) -> None:
        async for utterance in self._iterator:
            alert = self._observe(utterance)
            if alert is not None:
                await self._alerts.put(alert)

    def _observe(self, u: Utterance) -> ConsensusAlert | None:
        if self._substantive_only and not is_substantive(u.speech_act):
            return None
        if u.speaker.name not in self._agent_to_domain:
            # Unknown speakers (humans, external systems, test stubs) shouldn't
            # influence the heuristic — silently skip rather than guess a domain.
            return None

        info = self._threads.setdefault(u.thread_id, _ThreadWindow(thread_id=u.thread_id))
        info.recent.append(u)
        while len(info.recent) > self._window_size:
            info.recent.popleft()

        return self._check_for_alert(info, u)

    def _check_for_alert(
        self, info: _ThreadWindow, latest: Utterance
    ) -> ConsensusAlert | None:
        # Group recent utterances on this thread by speech_act, keeping the
        # *latest* utterance from each agent so an agent who spoke twice
        # contributes one position, not two.
        same_act = [
            u for u in info.recent if u.speech_act is latest.speech_act
        ]
        latest_per_agent: dict[str, Utterance] = {}
        for u in same_act:
            latest_per_agent[u.speaker.name] = u

        # Filter to known agents and group by domain — distinctness here is
        # *constitutional domain*, not just speaker name. Two Tweedles
        # agreeing is one voice; the Cat and the Rabbit agreeing is two.
        by_domain: dict[str, Utterance] = {}
        for agent_name, u in latest_per_agent.items():
            domain = self._agent_to_domain.get(agent_name)
            if domain is None:
                continue
            # Keep the most recent utterance per domain — if two
            # implementation-domain Tweedles both spoke, we use the latest as
            # the domain's representative position.
            existing = by_domain.get(domain)
            if existing is None or u.timestamp >= existing.timestamp:
                by_domain[domain] = u

        if len(by_domain) < self._min_agents:
            return None

        # Compute pairwise similarity across the per-domain representatives.
        # Take all pairs; require the average to clear the threshold.
        items = sorted(by_domain.items())  # stable ordering for sample_bodies
        domains = [d for d, _ in items]
        utterances = [u for _, u in items]
        shingle_sets = [
            shingles(u.content.body, size=self._shingle_size) for u in utterances
        ]

        pair_scores = [
            jaccard(shingle_sets[i], shingle_sets[j])
            for i, j in combinations(range(len(items)), 2)
        ]
        if not pair_scores:
            return None
        avg_similarity = sum(pair_scores) / len(pair_scores)
        if avg_similarity < self._threshold:
            return None

        agents = tuple(sorted(u.speaker.name for u in utterances))
        suppression_key = (latest.speech_act, frozenset(agents))
        if suppression_key in info.alerted:
            return None
        info.alerted.add(suppression_key)

        return ConsensusAlert(
            thread_id=info.thread_id,
            speech_act=latest.speech_act,
            agents=agents,
            domains=tuple(sorted(domains)),
            average_pairwise_similarity=avg_similarity,
            sample_bodies=tuple(_excerpt(u.content.body) for u in utterances),
            at=datetime.now(UTC),
            reason=(
                f"{len(items)} agents from distinct domains produced "
                f"{latest.speech_act.value} utterances with average pairwise "
                f"similarity {avg_similarity:.2f} (threshold {self._threshold:.2f})"
            ),
        )


def _excerpt(body: str, *, limit: int = 240) -> str:
    """Trim a body to a reviewer-friendly excerpt."""
    body = body.strip()
    if len(body) <= limit:
        return body
    return body[: limit - 1].rstrip() + "…"


__all__ = [
    "ConsensusAlert",
    "SyntheticConsensusGuard",
    "default_agent_domains",
    "jaccard",
    "shingles",
]
