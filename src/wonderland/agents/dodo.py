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

import inspect
import sys
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, field_validator

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
    addressed_to,
    almost_never,
    always,
    body_contains_any,
    make_engagement_policy,
)
from wonderland.escalation import (
    AgentProposalSchema,
    EscalationBrief,
    EscalationRecord,
    EscalationRegistry,
)
from wonderland.identity import load_constitution
from wonderland.llm import CachedBlock
from wonderland.parsing import extract_and_validate
from wonderland.thread_monitor import ThreadMonitor, ThreadState
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
# Escalation channel — where the Brief gets emitted besides disk
# --------------------------------------------------------------------- #


EscalationChannel = Callable[[EscalationBrief, EscalationRecord], Any]
"""A channel callable invoked after the Brief is persisted. Sync or async.

The Dodo always writes the Brief to disk via the EscalationRegistry. The
channel is the *additional* notification — stderr by default, swap in
a webhook/Slack/email handler when needed.
"""


def stderr_escalation_channel(brief: EscalationBrief, record: EscalationRecord) -> None:
    """Default channel: emit a single-line notice to stderr pointing at the file."""
    sys.stderr.write(
        f"\n[ESCALATION → {record.path}]\n  Decision required: {brief.decision_required}\n\n"
    )


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

    @field_validator("composition", "rationale", mode="before")
    @classmethod
    def _str_none_to_empty(cls, v: object) -> object:
        return "" if v is None else v

    @field_validator("dissents", mode="before")
    @classmethod
    def _dissents_none_to_empty(cls, v: object) -> object:
        return [] if v is None else v


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


class ConflictResponseParseError(ValueError):
    """The composition LLM response did not parse into a valid ConflictResponse."""


class BriefProseResponse(BaseModel):
    """Just the prose fields the LLM writes for an Escalation Brief.

    Structured fields (agent_proposals, suggested_resolution, owner,
    domain) are not the LLM's to write — they're derived from the
    Conflict + Resolution data the Dodo already holds. Keeping them
    out of the LLM's hands avoids fabrication.
    """

    decision_required: str = Field(min_length=1)
    stakes: str = ""
    background: str = ""

    @field_validator("stakes", "background", mode="before")
    @classmethod
    def _str_none_to_empty(cls, v: object) -> object:
        return "" if v is None else v


_BRIEF_PROTOCOL = """\
You are drafting the prose for an Escalation Brief. The structured
fields (agent_proposals, suggested_resolution, suggested_owner,
suggested_domain) are already filled from the conflict data. Your job
is the three prose fields:

```
{
  "decision_required": "A specific, answerable question. Not 'what should we do' but 'should X happen, given Y and Z?' One or two sentences. The question must be one a human can decide on with the information they're given here.",
  "stakes": "What changes depending on the answer. User-facing implications, schedule implications, architectural implications. Be concrete.",
  "background": "Brief context — directive, relevant prior utterances, any constraints. The human should be able to enter the situation cold and decide in minutes."
}
```

Respond with exactly one fenced JSON block conforming to that schema.
No prose outside the block. No commentary on the decision itself —
that's the human's call. Your job is to make their job tractable.

Speak in the Dodo's voice — observational, not opinion-bearing. The
agents' positions are theirs, not yours; you don't add a position of
your own to the Brief.
"""


class BriefResponseParseError(ValueError):
    """The escalation-brief LLM response did not parse into a valid BriefProseResponse."""


def parse_brief_response(text: str) -> BriefProseResponse:
    """Extract the JSON response from ``text`` and validate it.

    Delegates to ``wonderland.parsing.extract_and_validate``, which
    handles fenced/bare/balanced-fallback extraction uniformly across
    every agent.
    """
    return extract_and_validate(text, BriefProseResponse, BriefResponseParseError)


async def _emit_via_channel(
    channel: EscalationChannel,
    brief: EscalationBrief,
    record: EscalationRecord,
) -> None:
    """Invoke a channel callable, awaiting if it returns a coroutine."""
    result = channel(brief, record)
    if inspect.iscoroutine(result):
        await result


def parse_conflict_response(text: str) -> ConflictResponse:
    """Extract the JSON response from ``text`` and validate it.

    Delegates to ``wonderland.parsing.extract_and_validate``, which
    handles fenced/bare/balanced-fallback extraction uniformly across
    every agent.
    """
    return extract_and_validate(text, ConflictResponse, ConflictResponseParseError)


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
        # INVITE addressed to me always wakes me up (Block 2c)
        always(SpeechAct.INVITE, condition=addressed_to(DODO_NAME)),
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
        escalation_registry: EscalationRegistry | None = None,
        constitutions_root: Path | None = None,
    ) -> None:
        identity = load_constitution(DODO_NAME, root=constitutions_root)
        identity = replace(
            identity,
            engagement_policy=make_engagement_policy(dodo_rules()),
        )
        super().__init__(identity=identity, memory=memory, bus=bus, llm=llm)
        self._escalation_registry = escalation_registry

    @property
    def escalation_registry(self) -> EscalationRegistry | None:
        return self._escalation_registry

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

    async def nudge(
        self,
        thread_id: str,
        *,
        body: str | None = None,
        addressed_to: str = "caucus",
        reason: str = "",
    ) -> Utterance:
        """Publish a ``nudge`` reminding the team that a thread is stuck.

        Per dodo.md §IV, a nudge is the procedural reminder when a
        thread is approaching deadlock. Brief, observational, never
        opinion-bearing — the Dodo names that the team has paused
        with open expectations and asks the implicated agents to
        respond or commit provisionally. Per §VIII, the Dodo does
        not make the team's decisions; the nudge is information,
        not direction.

        ``reason`` is the ThreadStateChange.reason text from the
        ThreadMonitor (e.g., "3 open expectation(s); silent 30.4s")
        and gets folded into the default body when ``body`` isn't
        supplied.
        """
        if body is None:
            suffix = f" ({reason})" if reason else ""
            body = (
                f"Thread {thread_id} → stuck{suffix}. The team has paused "
                f"with open expectations; if commitments are pending "
                f"information, name what you need; if commitments can be "
                f"made provisionally, make them."
            )
        utterance = Utterance(
            thread_id=thread_id,
            speaker=self.identity.as_agent_identity(),
            addressed_to=addressed_to,  # type: ignore[arg-type]
            speech_act=SpeechAct.NUDGE,
            content=UtteranceContent(body=body),
        )
        await self.bus.publish(utterance)
        await self.memory.record(utterance)
        return utterance

    async def escalate_deadlock(
        self,
        thread_id: str,
        *,
        reason: str = "",
        thread_summary: str = "",
        channel: EscalationChannel | None = None,
    ) -> EscalationRecord:
        """Escalate a DEADLOCKED thread to human review.

        Distinct from ``escalate(conflict, resolution, ...)`` (T20),
        which is shaped for two competing proposals that didn't
        compose. The deadlock case has a different shape: the team
        has produced lots of utterances + few artifacts, with open
        expectations that nudges didn't break. Per analyses 006/007
        ("polite deadlock"), this happens when each agent's
        constitutional restraint is correct in isolation but the
        aggregate produces collective non-commitment.

        Templated EscalationBrief — the structured synthesis the LLM
        does in ``escalate()`` doesn't apply here because there is no
        conflict to compose, just paralysis to surface.
        """
        if self._escalation_registry is None:
            raise RuntimeError(
                "Dodo needs an escalation_registry to persist deadlock "
                "briefs. Pass one at construction or via the property."
            )

        from wonderland.escalation import AgentProposalSchema, EscalationBrief

        # The deadlock brief is shaped for human review even though there
        # are no agent proposals to choose between. We use a single
        # placeholder "team" proposal naming the polite-deadlock pattern
        # so the schema's min_length=2 on agent_proposals isn't blocked.
        # (A future refinement: support a separate brief-shape for
        # process-deadlock distinct from substance-conflict.)
        proposals = [
            AgentProposalSchema(
                speaker="team",
                position=(
                    f"Thread has been STUCK ({reason}). Multiple agents have "
                    "open expectations and the nudge ladder did not break the "
                    "deadlock."
                ),
                rationale=(
                    "The team's individual constitutional restraint is correct "
                    "in isolation. The collective effect is that no one is "
                    "willing to commit provisionally. Per dodo.md §VIII this "
                    "is the framework's escalation point, not the Dodo's "
                    "decision point."
                ),
            ),
            AgentProposalSchema(
                speaker="dodo",
                position="Surface the deadlock to human review.",
                rationale=(
                    "The Dodo's nudges did not produce a commitment. Further "
                    "nudges would be repetition, not progress. A human "
                    "reviewer can either name a provisional decision the team "
                    "can adopt or change the directive scope so the team can "
                    "make progress."
                ),
            ),
        ]
        brief = EscalationBrief(
            thread_id=thread_id,
            decision_required=(
                f"Thread {thread_id} has reached the nudge-threshold deadlock. "
                "What provisional decision would let the team progress, or "
                "should the directive scope change?"
            ),
            agent_proposals=proposals,
            suggested_resolution=(
                "A provisional decision from a human reviewer is the next move. "
                "The team will adopt the decision and make subsequent revisions "
                "via the normal flow (concerns, reframes, follow-up tickets)."
            ),
            stakes=(
                "Without intervention the thread will remain stuck and the directive will not ship."
            ),
            background=thread_summary or "(no thread summary supplied)",
        )

        record = self._escalation_registry.write(brief)
        await self._publish_escalation_utterance(brief, record)
        await _emit_via_channel(channel or stderr_escalation_channel, brief, record)
        return record

    # ------------------------------------------------------------------ #
    # State-driven behavior — consumes ThreadMonitor.transitions()
    # ------------------------------------------------------------------ #

    async def watch_thread_states(self, monitor: ThreadMonitor) -> None:
        """Consume ``monitor.transitions()`` and emit procedural acts.

        This is the structural anti-deadlock fix from analyses 006/007.
        The Dodo's per-utterance engagement (§III) only catches
        concerns carrying explicit conflict-keywords; the team's
        polite-deadlock concerns use constitutionally-correct hedging
        instead, so the Dodo never fires on the cascade. Wiring the
        Dodo to ThreadMonitor's STUCK transitions gives him a
        structural detector for the pattern that doesn't depend on
        the agents naming it themselves.

        Behavior per transition:

        - ``running → stuck``: emit a NUDGE; record the nudge with
          the monitor so the deadlock_after_nudges threshold trips
          DEADLOCKED on subsequent stuck transitions.
        - ``stuck → deadlocked``: escalate to human review via
          ``escalate_deadlock``. The escalation registry must be
          configured (passed at construction) for this path; without
          it, the deadlock is logged via acknowledge instead.
        - ``running → quiescent``: emit ACKNOWLEDGMENT(state="complete").
          Consolidates the thread-closure logic that showcase scripts
          previously did ad-hoc. The acknowledgment itself triggers
          the COMPLETE transition.

        Other transitions (RUNNING → ABANDONED, etc.) are logged via
        acknowledge but don't trigger procedural acts. Caller cancels
        the coroutine when the showcase is done.

        Run alongside ``Dodo.run()`` — they share the bus and the
        memory but consume different event streams.
        """
        async for change in monitor.transitions():
            if change.to_state is ThreadState.STUCK:
                # Record the nudge before publishing so the deadlock
                # threshold is consistent even if the publish path yields
                # to other coroutines before this loop iteration completes.
                monitor.record_nudge(change.thread_id)
                await self.nudge(change.thread_id, reason=change.reason)
            elif change.to_state is ThreadState.DEADLOCKED:
                if self._escalation_registry is not None:
                    await self.escalate_deadlock(change.thread_id, reason=change.reason)
                else:
                    await self.acknowledge(
                        change.thread_id,
                        state="deadlocked",
                        body=(
                            f"Thread {change.thread_id} → deadlocked "
                            f"({change.reason}). No escalation registry "
                            "configured; logging only."
                        ),
                    )
            elif change.to_state is ThreadState.QUIESCENT:
                await self.acknowledge(
                    change.thread_id,
                    state="complete",
                    body=(
                        f"Thread {change.thread_id} → complete. The team has "
                        "gone quiet with no open expectations; the directive "
                        "is settled."
                    ),
                )

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
    # Escalation — when proposals don't compose, the human decides
    # ------------------------------------------------------------------ #

    async def escalate(
        self,
        *,
        conflict: Conflict,
        resolution: Resolution,
        thread_summary: str = "",
        channel: EscalationChannel | None = None,
    ) -> EscalationRecord:
        """Draft + persist an Escalation Brief; publish ESCALATION; emit via channel.

        Requires ``resolution.needs_escalation`` (i.e., ``composed=False``).
        Calling escalate on a composing Resolution is the §VIII failure
        mode this method exists to enforce against — raises
        ``ValueError``.

        With LLM injected: the LLM drafts the prose fields
        (decision_required, stakes, background) given the conflict +
        resolution + thread_summary. Without LLM: a templated fallback
        produces a minimally-useful Brief from the structured data.

        Persistence requires an ``escalation_registry`` was passed at
        construction. Without one, raises ``RuntimeError`` — escalation
        without disk storage would silently lose the Brief, which is
        worse than failing loudly.

        ``channel`` defaults to ``stderr_escalation_channel``. Pass a
        custom callable (sync or async) for webhook/Slack/file logging.
        """
        if not resolution.needs_escalation:
            raise ValueError(
                "escalate requires a non-composing Resolution "
                "(composed=False). Composing resolutions go through "
                "publish_composition."
            )
        if self._escalation_registry is None:
            raise RuntimeError(
                "Dodo needs an escalation_registry to persist Briefs. "
                "Pass one at construction or via the property."
            )

        if self.llm is None:
            brief = self._fallback_brief(conflict, resolution, thread_summary)
        else:
            brief = await self._draft_brief_via_llm(conflict, resolution, thread_summary)

        record = self._escalation_registry.write(brief)
        await self._publish_escalation_utterance(brief, record)
        await _emit_via_channel(channel or stderr_escalation_channel, brief, record)
        return record

    def _fallback_brief(
        self,
        conflict: Conflict,
        resolution: Resolution,
        thread_summary: str,
    ) -> EscalationBrief:
        """Templated Brief used when no LLM is available.

        Less articulate than the LLM-drafted version but structurally
        complete — the human still gets a tractable handoff.
        """
        proposals = [
            AgentProposalSchema(
                speaker=speaker,
                position=body,
                rationale=(
                    f"position from {speaker}'s domain"
                    if resolution.suggested_owner != speaker
                    else "position from the suggested-resolution agent"
                ),
                domain=(
                    resolution.suggested_domain.value
                    if resolution.suggested_owner == speaker
                    and resolution.suggested_domain is not None
                    else None
                ),
            )
            for speaker, body in conflict.proposal_bodies
        ]
        suggested = self._format_suggested_resolution(resolution, conflict)
        return EscalationBrief(
            thread_id=conflict.thread_id,
            decision_required=(
                f"How should the conflict on thread {conflict.thread_id} resolve, "
                f"given the {len(proposals)} agent positions below?"
            ),
            agent_proposals=proposals,
            suggested_resolution=suggested,
            suggested_owner=resolution.suggested_owner,
            suggested_domain=(
                resolution.suggested_domain.value
                if resolution.suggested_domain is not None
                else None
            ),
            stakes="(no LLM available to articulate stakes)",
            background=thread_summary or "(no thread summary supplied)",
        )

    async def _draft_brief_via_llm(
        self,
        conflict: Conflict,
        resolution: Resolution,
        thread_summary: str,
    ) -> EscalationBrief:
        """Ask the LLM to write the prose fields; combine with structured data.

        The LLM only writes the prose (decision_required, stakes,
        background). The structured fields (agent_proposals,
        suggested_resolution, suggested_owner, suggested_domain) come
        from the data we already have — keeping the LLM out of fields
        where it could fabricate.
        """
        assert self.llm is not None
        system, messages = self._brief_request(conflict, resolution, thread_summary)
        result = await self.llm.complete(system=system, messages=messages)
        prose = parse_brief_response(result.text)

        proposals = [
            AgentProposalSchema(
                speaker=speaker,
                position=body,
                rationale=next(
                    (d.rationale for d in resolution.dissents if d.speaker == speaker),
                    "",
                ),
                domain=(
                    resolution.suggested_domain.value
                    if resolution.suggested_owner == speaker
                    and resolution.suggested_domain is not None
                    else None
                ),
            )
            for speaker, body in conflict.proposal_bodies
        ]
        return EscalationBrief(
            thread_id=conflict.thread_id,
            decision_required=prose.decision_required,
            agent_proposals=proposals,
            suggested_resolution=self._format_suggested_resolution(resolution, conflict),
            suggested_owner=resolution.suggested_owner,
            suggested_domain=(
                resolution.suggested_domain.value
                if resolution.suggested_domain is not None
                else None
            ),
            stakes=prose.stakes,
            background=prose.background or thread_summary,
        )

    def _brief_request(
        self,
        conflict: Conflict,
        resolution: Resolution,
        thread_summary: str,
    ) -> tuple[list, list]:
        proposals_text = "\n\n".join(
            f"### {speaker}\n\n{body}" for speaker, body in conflict.proposal_bodies
        )
        suggested = (
            f"Suggested primary domain: {resolution.suggested_domain.value} "
            f"(owner: {resolution.suggested_owner})"
            if resolution.suggested_domain is not None
            else "No primary-domain hint available."
        )
        rationale_text = (
            f"\n\nWhy escalation is needed: {resolution.rationale}" if resolution.rationale else ""
        )
        background_text = f"\n\nThread summary so far:\n{thread_summary}" if thread_summary else ""
        user = (
            f"## Thread {conflict.thread_id} — escalation brief draft\n\n"
            f"**Competing proposals:**\n\n{proposals_text}\n\n"
            f"{suggested}{rationale_text}{background_text}\n\n"
            "Draft the prose fields the human reviewer needs."
        )
        system = [
            CachedBlock(self.identity.constitution_text),
            CachedBlock(_BRIEF_PROTOCOL),
        ]
        return system, [{"role": "user", "content": user}]

    async def _publish_escalation_utterance(
        self,
        brief: EscalationBrief,
        record: EscalationRecord,
    ) -> Utterance:
        artifact = Artifact(
            kind="escalation",
            payload={
                "number": record.number,
                "slug": record.slug,
                "path": str(record.path),
                "decision_required": brief.decision_required,
                "suggested_owner": brief.suggested_owner,
                "suggested_domain": brief.suggested_domain,
            },
        )
        utterance = Utterance(
            thread_id=brief.thread_id,
            speaker=self.identity.as_agent_identity(),
            addressed_to="caucus",
            speech_act=SpeechAct.ESCALATION,
            content=UtteranceContent(
                body=f"Escalating to human review: {brief.decision_required}",
                artifacts=[artifact],
            ),
        )
        await self.bus.publish(utterance)
        await self.memory.record(utterance)
        return utterance

    @staticmethod
    def _format_suggested_resolution(
        resolution: Resolution,
        conflict: Conflict,
    ) -> str:
        """Pick the suggested resolution text from the conflict's proposals.

        If the suggested owner is one of the agents who proposed, surface
        their position. Otherwise fall back to the resolution's
        rationale.
        """
        if resolution.suggested_owner is not None:
            for speaker, body in conflict.proposal_bodies:
                if speaker == resolution.suggested_owner:
                    return (
                        f"Lean toward {speaker}'s position "
                        f"(domain: {resolution.suggested_domain.value if resolution.suggested_domain else 'unspecified'}):\n\n"
                        f"{body}"
                    )
        return (
            resolution.rationale
            or "No suggested resolution — the agents' proposals are the input set."
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
    "BriefProseResponse",
    "BriefResponseParseError",
    "ConflictResponse",
    "ConflictResponseParseError",
    "DissentSchema",
    "Dodo",
    "EscalationChannel",
    "dodo_rules",
    "parse_brief_response",
    "parse_conflict_response",
    "stderr_escalation_channel",
]
