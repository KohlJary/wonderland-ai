"""The Dodo — orchestrator. He convenes; he does not direct.

Per dodo.md and WONDERLAND_SPEC §3 / §6. The Dodo is structurally
different from the domain agents:

- Cat, Rabbit, Hatter, etc. **deliberate on content**. Each utterance
  on the bus is a potential trigger; their LLM decides what to say.
- The Dodo **deliberates on patterns**. Individual utterances rarely
  drive him directly; *thread state transitions* (quiescence, stuck,
  deadlock, completion) do. The ThreadMonitor (T18) provides those
  signals; the Dodo responds with procedural acts.

This module establishes the Dodo agent's shape: constitution loading,
narrow engagement rules, the two mechanical actions he can take from
T17 (``relay_directive`` to introduce external work; ``acknowledge``
to mark thread state transitions), and a silent default ``deliberate``.

Composition (T19) and escalation (T20) will add the LLM-driven
procedural acts. Quiescence/stuck/deadlock detection arrives in T18.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

from wonderland.agent import Context, WonderlandAgent
from wonderland.engagement import (
    EngagementRules,
    almost_never,
    always,
    body_contains_any,
    make_engagement_policy,
)
from wonderland.identity import load_constitution
from wonderland.utterance import (
    SpeechAct,
    Utterance,
    UtteranceContent,
)

if TYPE_CHECKING:
    from wonderland.caucus import Caucus
    from wonderland.llm import LLMClient
    from wonderland.memory import AgentMemory


DODO_NAME = "dodo"


# --------------------------------------------------------------------- #
# Engagement rules — dodo.md §III as data
# --------------------------------------------------------------------- #


def dodo_rules() -> EngagementRules:
    """The Dodo's §III engagement policy.

    Deliberately narrow. The Dodo's primary work is state-driven via
    the ThreadMonitor, not content-driven from per-utterance triggers.
    He only engages with utterances when content explicitly invokes a
    procedural concern he owns:

    - ``concern`` carrying conflict-resolution language (so he can
      step into the composition/escalation flow)
    - ``escalation`` (human-reviewer responses he must record)

    He does **not** subscribe to ``directive`` — directives originate
    *from* the Dodo (relayed from external sources); listening for
    them on the bus would just produce echoes. He does not engage
    with domain content of any kind; that's the most pernicious
    failure mode his constitution names (§VIII).
    """
    conflict_words = body_contains_any(
        "conflict",
        "disagree",
        "disagreement",
        "deadlock",
        "stuck",
        "blocked",
        "tension",
        "incompatible",
        "cannot proceed",
    )
    return EngagementRules.of(
        always(SpeechAct.CONCERN, condition=conflict_words),
        always(SpeechAct.ESCALATION),
        almost_never(SpeechAct.DIRECTIVE),
        almost_never(SpeechAct.DEFERENCE),
    )


# --------------------------------------------------------------------- #
# Dodo agent
# --------------------------------------------------------------------- #


class Dodo(WonderlandAgent):
    """The Dodo: convener, pattern-watcher, procedural-acts-only."""

    def __init__(
        self,
        memory: AgentMemory,
        bus: Caucus,
        llm: LLMClient | None = None,
        constitutions_root: Path | None = None,
    ) -> None:
        identity = load_constitution(DODO_NAME, root=constitutions_root)
        identity = replace(
            identity,
            engagement_policy=make_engagement_policy(dodo_rules()),
        )
        super().__init__(identity=identity, memory=memory, bus=bus, llm=llm)

    # ------------------------------------------------------------------ #
    # Mechanical procedural acts — no LLM
    # ------------------------------------------------------------------ #

    async def relay_directive(
        self,
        body: str,
        *,
        thread_id: str,
        addressed_to: str = "caucus",
    ) -> Utterance:
        """Introduce an external directive to the team.

        The Dodo doesn't *generate* directives — he relays them from
        external sources (a human, an operator, a parent system). The
        published utterance carries his identity as speaker because
        that's who placed it on the bus, but the content originates
        outside the system. Other agents see a directive and engage
        per their own rules.

        Records the relayed directive in episodic memory like any
        other published utterance.
        """
        utterance = Utterance(
            thread_id=thread_id,
            speaker=self.identity.as_agent_identity(),
            addressed_to=addressed_to,  # type: ignore[arg-type]
            speech_act=SpeechAct.DIRECTIVE,
            content=UtteranceContent(body=body),
        )
        await self.bus.publish(utterance)
        await self.memory.record(utterance)
        return utterance

    async def acknowledge(
        self,
        thread_id: str,
        *,
        state: str,
        body: str | None = None,
    ) -> Utterance:
        """Publish an ``acknowledgment`` marking a thread state transition.

        ``state`` is one of: ``quiescent``, ``stuck``, ``deadlocked``,
        ``complete``, ``abandoned``. ``body`` overrides the default
        templated wording — useful when the orchestrator has more
        context to convey (which agents engaged, escalation outcome,
        etc.).

        Brief and factual per §II ("Brief but they matter — the team
        knows where they are because you make where-they-are visible").
        """
        text = body or f"Thread {thread_id} → {state}."
        utterance = Utterance(
            thread_id=thread_id,
            speaker=self.identity.as_agent_identity(),
            addressed_to="caucus",
            speech_act=SpeechAct.ACKNOWLEDGMENT,
            content=UtteranceContent(body=text),
        )
        await self.bus.publish(utterance)
        await self.memory.record(utterance)
        return utterance

    # ------------------------------------------------------------------ #
    # Deliberate — silence by default
    # ------------------------------------------------------------------ #

    async def deliberate(self, context: Context) -> Utterance | None:
        """Default: silence. Per §VIII, performing orchestration is a
        failure mode the Dodo guards against. The state-driven
        actions (nudge, composition, escalation) live in their own
        methods invoked by the ThreadMonitor (T18) and the conflict
        flow (T19/T20). Per-utterance deliberation produces silence
        unless a subclass overrides — and there's rarely a reason to
        override, because the Dodo's voice should be thread-state-
        triggered, not utterance-triggered.
        """
        _ = context
        return None


__all__ = [
    "DODO_NAME",
    "Dodo",
    "dodo_rules",
]
