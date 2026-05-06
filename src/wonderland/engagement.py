"""Structured engagement rules for per-character engagement policies.

Each agent's constitution describes engagement in tiered language:
"always engage with X", "selectively with Y", "rarely with Z", "almost
never with W". The Cheshire Cat's §III is the canonical example. This
module turns those tiers into machine-checkable rules.

The shape:

- ``Engagement`` is the tier enum (ALWAYS / SELECTIVELY / RARELY /
  ALMOST_NEVER).
- ``EngagementRule`` ties a tier to a SpeechAct, optionally gated by a
  ``condition`` predicate (e.g., "engage with `ticket` from the Rabbit
  *only when* it constrains architecture").
- ``EngagementRules`` is a collection: first matching rule wins, with a
  ``default`` tier (typically ALMOST_NEVER) for unmatched acts.
- ``make_engagement_policy`` produces a callable that
  ``Identity.engagement_policy`` can hold directly.

The categorize/engage split lets us preserve the *why* — an
ALWAYS-vs-SELECTIVELY engagement is observably different in
telemetry — even though the immediate decision is binary.

LLM tiebreak — the heuristic-then-LLM pattern from the gameplan task —
is deferred. The structure here makes adding it cheap when we have a
case where the rules are genuinely ambiguous; for now, every category
except ALMOST_NEVER means "engage."
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

from wonderland.utterance import SpeechAct, Utterance

if TYPE_CHECKING:
    from wonderland.identity import AgentMemory, EngagementPolicy


class Engagement(StrEnum):
    ALWAYS = "always"
    SELECTIVELY = "selectively"
    RARELY = "rarely"
    ALMOST_NEVER = "almost_never"


UtterancePredicate = Callable[[Utterance], bool]


@dataclass(frozen=True)
class EngagementRule:
    """One rule mapping a SpeechAct (with optional gating) to a tier.

    ``condition`` is an optional predicate over the utterance. If
    present, the rule only matches when both the speech_act matches and
    the condition returns True. If absent, the rule matches every
    utterance of the given speech_act.
    """

    speech_act: SpeechAct
    category: Engagement
    condition: UtterancePredicate | None = None

    def matches(self, u: Utterance) -> bool:
        if u.speech_act != self.speech_act:
            return False
        return self.condition is None or self.condition(u)


@dataclass(frozen=True)
class EngagementRules:
    """Ordered ruleset with a default tier for unmatched utterances.

    Order matters: the first matching rule wins. Place narrower rules
    (with conditions) before broader fallback rules for the same
    speech_act.
    """

    rules: tuple[EngagementRule, ...] = field(default_factory=tuple)
    default: Engagement = Engagement.ALMOST_NEVER

    @classmethod
    def of(
        cls, *rules: EngagementRule, default: Engagement = Engagement.ALMOST_NEVER
    ) -> EngagementRules:
        """Convenience constructor: ``EngagementRules.of(rule1, rule2, ...)``."""
        return cls(rules=tuple(rules), default=default)

    def categorize(self, u: Utterance) -> Engagement:
        """Return the tier this utterance falls into.

        Seed utterances (``u.is_seed=True``, set by Runner.convene when
        re-publishing prior-thread artifacts as context for a follow-up
        meeting) short-circuit to ALMOST_NEVER. Seeds are visible in
        thread history and engagement-state counts, but they are not
        engagement triggers — reacting to them as if they were fresh
        turns pulls agents into respond-mode against historical
        artifacts that were already negotiated/decided in their
        original thread."""
        if u.is_seed:
            return Engagement.ALMOST_NEVER
        for rule in self.rules:
            if rule.matches(u):
                return rule.category
        return self.default

    def should_engage(self, u: Utterance) -> bool:
        """Engagement decision: True for any tier except ALMOST_NEVER."""
        return self.categorize(u) is not Engagement.ALMOST_NEVER

    def speech_acts(self) -> set[SpeechAct]:
        """Distinct speech acts referenced by any rule.

        Useful for deriving a default ``interests`` set from rules — an
        agent that has no opinion at all about an act probably doesn't
        need to subscribe to it.
        """
        return {rule.speech_act for rule in self.rules}


def make_engagement_policy(rules: EngagementRules) -> EngagementPolicy:
    """Wrap an ``EngagementRules`` into an ``EngagementPolicy`` callable.

    The resulting policy ignores the memory argument — heuristic-only.
    A future LLM-tiebreak factory can take memory into account by
    consulting it (e.g., "have I already responded to this thread?").
    """

    def _policy(u: Utterance, _memory: AgentMemory | None = None) -> bool:
        return rules.should_engage(u)

    return _policy


# Convenience helpers for building rule sets readably.


def always(act: SpeechAct, *, condition: UtterancePredicate | None = None) -> EngagementRule:
    return EngagementRule(speech_act=act, category=Engagement.ALWAYS, condition=condition)


def selectively(act: SpeechAct, *, condition: UtterancePredicate | None = None) -> EngagementRule:
    return EngagementRule(speech_act=act, category=Engagement.SELECTIVELY, condition=condition)


def rarely(act: SpeechAct, *, condition: UtterancePredicate | None = None) -> EngagementRule:
    return EngagementRule(speech_act=act, category=Engagement.RARELY, condition=condition)


def almost_never(act: SpeechAct) -> EngagementRule:
    return EngagementRule(speech_act=act, category=Engagement.ALMOST_NEVER)


def speaker_is(name: str) -> UtterancePredicate:
    """Predicate factory: matches utterances whose speaker has the given name."""
    return lambda u: u.speaker.name == name


def addressed_to(name: str) -> UtterancePredicate:
    """Predicate factory: matches utterances explicitly addressed to ``name``.

    Caucus-broadcast utterances (addressed_to == "caucus") never match.
    """

    def _check(u: Utterance) -> bool:
        if isinstance(u.addressed_to, str):
            return False  # "caucus"
        return any(target.name == name for target in u.addressed_to)

    return _check


def body_contains_any(*needles: str) -> UtterancePredicate:
    """Predicate factory: True if any needle appears (case-insensitive) in body."""
    lowered = tuple(n.lower() for n in needles)

    def _check(u: Utterance) -> bool:
        body = u.content.body.lower()
        return any(needle in body for needle in lowered)

    return _check


def any_of(*predicates: UtterancePredicate) -> UtterancePredicate:
    """OR-combine predicates."""
    return lambda u: any(p(u) for p in predicates)


def all_of(*predicates: UtterancePredicate) -> UtterancePredicate:
    """AND-combine predicates."""
    return lambda u: all(p(u) for p in predicates)


__all__ = [
    "Engagement",
    "EngagementRule",
    "EngagementRules",
    "UtterancePredicate",
    "addressed_to",
    "all_of",
    "almost_never",
    "always",
    "any_of",
    "body_contains_any",
    "make_engagement_policy",
    "rarely",
    "selectively",
    "speaker_is",
]


# Avoid the unused-import warning when only used in TYPE_CHECKING blocks above.
_ = Iterable
