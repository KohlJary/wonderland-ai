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

import json
import re
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, ValidationError

from wonderland.agent import Context, WonderlandAgent
from wonderland.conflict import (
    DOMAIN_PRIMACY,
    Conflict,
    ConflictDomain,
    Dissent,
    Resolution,
    domain_owner,
)
from wonderland.engagement import (
    EngagementRules,
    almost_never,
    always,
    body_contains_any,
    make_engagement_policy,
)
from wonderland.identity import load_constitution
from wonderland.llm import CachedBlock
from wonderland.utterance import (
    Artifact,
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
# LLM output protocol — composition vs non-composition
# --------------------------------------------------------------------- #


class DissentSchema(BaseModel):
    speaker: str
    position: str
    rationale: str = ""


class ConflictResponse(BaseModel):
    """Structured JSON the Dodo's LLM returns when asked to compose proposals."""

    composed: bool
    composition: str = ""
    """The synthesized resolution text when ``composed=True``."""
    suggested_domain: str | None = None
    """The conflict's primary domain when ``composed=False`` — must be one of
    the ConflictDomain enum values. The Dodo looks up the owner from the
    DOMAIN_PRIMACY table."""
    rationale: str = ""
    dissents: list[DissentSchema] = Field(default_factory=list)


_COMPOSITION_PROTOCOL = """\
You will be shown N proposals from N agents, each with their domain.
Determine whether the proposals **compose into a coherent resolution**
or whether they are **incompatible** and require human escalation.

You are the Dodo. You do not decide between proposals on the agents'
behalf. Your job is to *check whether they fit together*. If they do,
write the composition that names how they fit. If they do not, name
the conflict's primary domain (one of: user_need, architecture,
sequence, severity, code_quality, security, production) so the
escalation can be addressed to the right human.

Respond with exactly one fenced JSON block:

```
{
  "composed": true | false,
  "composition": "synthesis text (only when composed=true)",
  "suggested_domain": "user_need" | "architecture" | ... (only when composed=false),
  "rationale": "brief why-it-composes or why-it-doesn't (always)",
  "dissents": [                        // optional but recommended
    {
      "speaker": "<agent name>",
      "position": "their position in their own words",
      "rationale": "why their position matters even though it wasn't the chosen path"
    }
  ]
}
```

Composition is honest: if the proposals contradict on a load-bearing
point, they don't compose, even if you can imagine a synthesis that
papers over the contradiction. Performing composition that papers over
real disagreement is a failure mode (§VIII: "composition pretending to
be decision"). Better to escalate honestly.

Speak in the Dodo's voice — observational, not opinion-bearing. The
composition references the agents' proposals; it does not add a
position of your own.
"""


_DODO_JSON_BLOCK = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


class ConflictResponseParseError(ValueError):
    """The composition LLM response did not parse into a valid ConflictResponse."""


def parse_conflict_response(text: str) -> ConflictResponse:
    """Extract the fenced JSON block and validate it."""
    match = _DODO_JSON_BLOCK.search(text)
    if match is None:
        candidate = text.strip()
        if not (candidate.startswith("{") and candidate.endswith("}")):
            raise ConflictResponseParseError("no JSON block found in conflict response")
        raw = candidate
    else:
        raw = match.group(1)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConflictResponseParseError(f"conflict response was not valid JSON: {exc}") from exc
    try:
        return ConflictResponse.model_validate(data)
    except ValidationError as exc:
        raise ConflictResponseParseError(
            f"conflict response failed schema validation: {exc}"
        ) from exc


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
    # Conflict resolution + composition
    # ------------------------------------------------------------------ #

    async def compose_conflict_resolution(self, conflict: Conflict) -> Resolution:
        """Determine whether ``conflict.proposals`` compose; produce a Resolution.

        With an LLM injected: builds a prompt from the agents' proposal
        bodies, asks "does this compose?", parses the structured
        response. With no LLM: returns a non-composing Resolution
        carrying the caller's domain hint (or no hint if none) — the
        escalation flow (T20) handles it from there.

        Does not publish anything by itself. Callers that want the
        composition on the bus call ``publish_composition(resolution)``;
        callers that get a non-composing resolution feed it into the
        escalation flow.
        """
        if self.llm is None:
            return self._fallback_resolution(conflict)

        system, messages = self._compose_request(conflict)
        result = await self.llm.complete(system=system, messages=messages)
        response = parse_conflict_response(result.text)
        return self._resolution_from_response(conflict, response)

    async def publish_composition(self, resolution: Resolution) -> Utterance:
        """Publish a COMPOSITION utterance with the synthesized resolution.

        Caller must pass a Resolution where ``composed=True`` — composing
        a non-composition would be the spec §VIII failure mode this
        method exists to enforce against.
        """
        if not resolution.composed:
            raise ValueError(
                "publish_composition requires a composed Resolution; "
                "non-composing resolutions go through the escalation flow"
            )
        artifact = Artifact(
            kind="resolution",
            payload={
                "thread_id": resolution.thread_id,
                "composed": True,
                "rationale": resolution.rationale,
                "dissents": [
                    {
                        "speaker": d.speaker,
                        "position": d.position,
                        "rationale": d.rationale,
                    }
                    for d in resolution.dissents
                ],
            },
        )
        utterance = Utterance(
            thread_id=resolution.thread_id,
            speaker=self.identity.as_agent_identity(),
            addressed_to="caucus",
            speech_act=SpeechAct.COMPOSITION,
            content=UtteranceContent(
                body=resolution.composition_text,
                artifacts=[artifact],
            ),
        )
        await self.bus.publish(utterance)
        await self.memory.record(utterance)
        return utterance

    def _fallback_resolution(self, conflict: Conflict) -> Resolution:
        """No-LLM path: return a non-composing resolution. T20 escalates."""
        domain = conflict.domain_hint
        owner = domain_owner(domain) if domain is not None else None
        return Resolution(
            thread_id=conflict.thread_id,
            composed=False,
            suggested_domain=domain,
            suggested_owner=owner,
            rationale="no LLM available; defaulting to escalation with caller's domain hint",
        )

    def _compose_request(self, conflict: Conflict) -> tuple[list, list]:
        proposals_text = "\n\n".join(
            f"### {speaker}\n\n{body}" for speaker, body in conflict.proposal_bodies
        )
        hint_text = (
            f"\n\nThe caller has hinted that this conflict is primarily about "
            f"the **{conflict.domain_hint.value}** domain."
            if conflict.domain_hint is not None
            else ""
        )
        user = (
            f"## Thread {conflict.thread_id} — competing proposals\n\n"
            f"{proposals_text}{hint_text}\n\n"
            "Determine: do these compose, or do they need escalation?"
        )
        system = [
            CachedBlock(self.identity.constitution_text),
            CachedBlock(_COMPOSITION_PROTOCOL),
        ]
        return system, [{"role": "user", "content": user}]

    def _resolution_from_response(
        self, conflict: Conflict, response: ConflictResponse
    ) -> Resolution:
        dissents = tuple(
            Dissent(speaker=d.speaker, position=d.position, rationale=d.rationale)
            for d in response.dissents
        )
        if response.composed:
            return Resolution(
                thread_id=conflict.thread_id,
                composed=True,
                composition_text=response.composition,
                rationale=response.rationale,
                dissents=dissents,
            )
        domain: ConflictDomain | None = None
        owner: str | None = None
        if response.suggested_domain:
            try:
                domain = ConflictDomain(response.suggested_domain)
                owner = DOMAIN_PRIMACY.get(domain)
            except ValueError:
                # LLM hallucinated a domain; fall through to caller's hint
                pass
        if domain is None and conflict.domain_hint is not None:
            domain = conflict.domain_hint
            owner = domain_owner(domain)
        return Resolution(
            thread_id=conflict.thread_id,
            composed=False,
            suggested_domain=domain,
            suggested_owner=owner,
            rationale=response.rationale,
            dissents=dissents,
        )

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
    "ConflictResponse",
    "ConflictResponseParseError",
    "DissentSchema",
    "Dodo",
    "dodo_rules",
    "parse_conflict_response",
]
