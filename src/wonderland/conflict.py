"""Conflict resolution data types — domain primacy, dissent, composition.

Per WONDERLAND_SPEC §7. When multi-agent proposals on the same thread
contradict, the framework's job is to either *compose* them (the
proposals fit together; the Dodo publishes the synthesis as a
``composition`` speech-act) or *escalate* (they don't fit; the Dodo
emits an Escalation Brief for human review per T20).

This module owns the pure data shapes:

- ``ConflictDomain`` enum + ``DOMAIN_PRIMACY`` lookup — the table the
  spec names: which character holds the primary call within each
  domain. Used as escalation hint when proposals don't compose.
- ``Conflict`` — a set of contradicting proposals (or other utterances)
  on a thread, optionally tagged with a domain hint from the caller.
- ``Dissent`` — a position that wasn't chosen, preserved as part of
  the resolution artifact. The dissent is *information*, not an
  apology — when later evidence shows the dissent was correct, the
  relational memory updates and that domain's voice gets weighted
  accordingly in future conflicts.
- ``Resolution`` — what came out: either a composed synthesis (with
  any preserved dissents) or a non-composition flagged for
  escalation (with the suggested domain/owner from the table).

The Dodo's methods that *use* these types live in
``wonderland.agents.dodo`` — composition-via-LLM, publishing the
COMPOSITION utterance, etc.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ConflictDomain(StrEnum):
    """Domains the spec §7 table assigns ownership of."""

    USER_NEED = "user_need"
    ARCHITECTURE = "architecture"
    SEQUENCE = "sequence"
    SEVERITY = "severity"
    CODE_QUALITY = "code_quality"
    SECURITY = "security"
    PRODUCTION = "production"


DOMAIN_PRIMACY: dict[ConflictDomain, str] = {
    ConflictDomain.USER_NEED: "alice",
    ConflictDomain.ARCHITECTURE: "cheshire_cat",
    ConflictDomain.SEQUENCE: "white_rabbit",
    ConflictDomain.SEVERITY: "mad_hatter",
    ConflictDomain.CODE_QUALITY: "caterpillar",
    ConflictDomain.SECURITY: "queen_of_hearts",
    ConflictDomain.PRODUCTION: "dormouse",
}
"""Per WONDERLAND_SPEC §7. Maps each conflict domain to the canonical
agent name that owns the primary call within it. Used by the Dodo as
the escalation hint when proposals don't compose — *not* as autonomous
decision authority. The framework escalates; the human decides."""


def domain_owner(domain: ConflictDomain) -> str:
    """Return the canonical agent name that owns the given domain."""
    return DOMAIN_PRIMACY[domain]


@dataclass(frozen=True)
class Dissent:
    """A position that wasn't chosen, preserved as part of the resolution.

    The dissent is information, not an apology — when later evidence
    shows the dissent was correct, the relational memory updates and
    that voice gets weighted accordingly in future conflicts.
    """

    speaker: str
    position: str
    rationale: str = ""


@dataclass(frozen=True)
class Conflict:
    """A set of contradicting utterances on a thread.

    ``proposals`` is the input set — typically multiple PROPOSAL
    utterances from different agents that arrived close together
    without intervening composition or acceptance. ``domain_hint``
    lets the caller suggest which domain the conflict is primarily
    about; the Dodo's compose step may revise this hint.
    """

    thread_id: str
    proposals: tuple[str, ...]  # utterance IDs
    proposal_bodies: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    """(speaker_name, body) pairs — the LLM-readable form of the conflicting positions."""
    domain_hint: ConflictDomain | None = None


@dataclass(frozen=True)
class Resolution:
    """The Dodo's resolution of a conflict.

    Two shapes:

    - **Composed** (``composed=True``, non-empty ``composition_text``):
      the proposals fit together; the Dodo publishes ``composition_text``
      as a COMPOSITION utterance. ``dissents`` may be present if the
      composition acknowledged minority positions.
    - **Not composed** (``composed=False``, ``suggested_domain`` set):
      the proposals don't fit together; the resolution carries the
      suggested primary domain (from the DOMAIN_PRIMACY table) and the
      Dodo's escalation flow (T20) takes over from here. ``dissents``
      preserves all the agents' positions for the Escalation Brief.
    """

    thread_id: str
    composed: bool
    composition_text: str = ""
    suggested_domain: ConflictDomain | None = None
    suggested_owner: str | None = None
    dissents: tuple[Dissent, ...] = ()
    rationale: str = ""

    @property
    def is_composition(self) -> bool:
        return self.composed and bool(self.composition_text)

    @property
    def needs_escalation(self) -> bool:
        return not self.composed


__all__ = [
    "DOMAIN_PRIMACY",
    "Conflict",
    "ConflictDomain",
    "Dissent",
    "Resolution",
    "domain_owner",
]
