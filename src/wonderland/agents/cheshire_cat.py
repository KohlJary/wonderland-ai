"""The Cheshire Cat — first character to come online.

Per cheshire_cat.md and WONDERLAND_SPEC §5. The Cat appears when
architectural decisions are being made and disappears when
implementation begins. His characteristic move is the reframing
question; his characteristic artifact is the ADR.

This module wires the four primitives the base agent needs (identity,
memory, bus, llm) plus a fifth specific to the Cat — an
``ADRRegistry`` for persisting his grin.

LLM output protocol
-------------------

The Cat's ``deliberate()`` calls the LLM with a fixed instruction:
respond with a single fenced JSON block conforming to the
``CatResponse`` schema. ``decision`` selects the speech act (or
``"silence"``), ``body`` is the natural-language content, and an
optional ``adr`` carries the structured ADR payload that the registry
will persist. Silence is a first-class decision and the spec's "the Cat
falls silent on a thread once the architecture is settled" depends on
it.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field, field_validator

from wonderland.adr import ADRPayload, ADRRegistry
from wonderland.agent import Context, WonderlandAgent, format_utterance
from wonderland.engagement import (
    EngagementRules,
    addressed_to,
    almost_never,
    always,
    body_contains_any,
    make_engagement_policy,
    rarely,
    selectively,
    speaker_is,
)
from wonderland.identity import load_constitution
from wonderland.llm import CachedBlock, SystemPart
from wonderland.parsing import ResponseParseError, extract_and_validate
from wonderland.utterance import (
    Artifact,
    SpeechAct,
    Utterance,
    UtteranceContent,
    operator_identity,
)

if TYPE_CHECKING:
    from wonderland.caucus import Caucus
    from wonderland.llm import LLMClient
    from wonderland.memory import AgentMemory


CAT_NAME = "cheshire_cat"


# --------------------------------------------------------------------- #
# Engagement rules — cheshire_cat.md §III as data
# --------------------------------------------------------------------- #


def cheshire_cat_rules() -> EngagementRules:
    """The Cat's §III engagement policy as machine-checkable rules.

    Body-keyword heuristics for "implementation hint constrains
    architecture", "implies architectural primitive", etc. are
    intentionally narrow — the deliberate() step has the LLM behind it,
    so when in doubt the Cat can engage and then choose silence.
    """
    architectural_smell = body_contains_any(
        "synchronous call",
        "synchronous request",
        "per message",
        "per request",
        "for every",
        "in a loop",
        "block on",
        "fan out",
    )
    architectural_concern_smell = body_contains_any(
        "architecture",
        "architectural",
        "scaling",
        "scale",
        "seam",
        "coupling",
        "interface",
        "schema",
        "contract",
        "primitive",
    )
    return EngagementRules.of(
        # ALWAYS — INVITE addressed to me always wakes me up (Block 2c)
        always(SpeechAct.INVITE, condition=addressed_to(CAT_NAME)),
        always(SpeechAct.DIRECTIVE),
        always(SpeechAct.PROPOSAL),
        always(SpeechAct.QUESTION, condition=addressed_to(CAT_NAME)),
        always(SpeechAct.CONCERN, condition=architectural_concern_smell),
        always(SpeechAct.TICKET, condition=architectural_smell),
        # SELECTIVELY — engage broadly; the LLM judges further inside deliberate()
        # Wake on every Alice story; deliberate() decides whether the
        # cumulative picture warrants synthesis. The keyword filter we
        # used to have here (real-time, multi-tenant, etc.) made Cat
        # systematically deaf to user-shaped stories without
        # architectural vocabulary, which left the architectural picture
        # un-synthesized when stories accumulated. Engagement state
        # already shows team artifact counts; the protocol guides Cat
        # to synthesize when stories pile up without an ADR.
        selectively(SpeechAct.STORY),
        selectively(SpeechAct.IMPLEMENTATION),
        selectively(SpeechAct.TEST_SCENARIO),
        selectively(SpeechAct.REVIEW),
        # RARELY — engage but expect to choose silence often
        rarely(SpeechAct.RULING),
        rarely(SpeechAct.OBSERVATION),
        # ALMOST NEVER — explicit (in addition to the default)
        almost_never(SpeechAct.DEFERENCE),
    )


# --------------------------------------------------------------------- #
# LLM output protocol
# --------------------------------------------------------------------- #

CatDecision = Literal[
    "proposal",
    "question",
    "question_to_operator",
    "reframe",
    "concern",
    "deference",
    "silence",
]


class CatResponse(BaseModel):
    """Structured JSON the Cat returns from deliberate()."""

    decision: CatDecision
    body: str = ""
    adr: ADRPayload | None = None
    options: list[str] = Field(
        default_factory=list,
        description=(
            "Optional suggested answers when ``decision == "
            "'question_to_operator'``. Each entry becomes a "
            "click-to-submit button in the operator's modal. "
            "Use 2–4 short options for the common cases of a "
            "binary or n-way question; the operator can still "
            "type a custom answer if none fit. Ignored when "
            "decision is anything else."
        ),
    )

    @field_validator("body", mode="before")
    @classmethod
    def _body_none_to_empty(cls, v: object) -> object:
        # The LLM occasionally emits explicit nulls for omitted fields
        # (especially on `silence`). Coerce to default.
        return "" if v is None else v

    def model_post_init(self, _context: object) -> None:  # type: ignore[override]
        # Per the calibrated "ship the provisional ADR" guidance in §VI/§VIII:
        # a `proposal` decision MUST carry the ADR payload. Half-shipping —
        # decision=proposal with adr=None — is the failure mode the
        # calibration was designed to prevent (it leaves prose on the bus
        # but no artifact for the team to compose against). The schema
        # rejection forces the Cat to either include the ADR or pick a
        # different decision (concern/question/reframe).
        if self.decision == "proposal" and self.adr is None:
            raise ValueError(
                "CatResponse: decision='proposal' requires the `adr` field. "
                "A proposal without an ADR is prose, not an architectural "
                "commitment — the team has nothing to compose against. If "
                "you don't yet have a decision concrete enough to record, "
                "choose 'question' or 'reframe' instead. If you do, name "
                "the tradeoffs explicitly (mark uncertain ones with what "
                "would have to be true to settle them) and ship the ADR."
            )


_OUTPUT_PROTOCOL = """\
You will respond with exactly one fenced JSON block. No prose outside the block.

The JSON must conform to this schema:

```
{
  "decision": "proposal" | "question" | "question_to_operator" | "reframe" |
              "concern" | "deference" | "silence",
  "body": "the natural-language content of your utterance (omit for silence)",
  "options": ["SQLite", "Postgres", "Either is fine"],
                                      // OPTIONAL: include with question_to_operator
                                      // to surface 2–4 click-to-submit answers
  "adr": {                            // include only when decision is "proposal"
                                      // AND there is a real architectural decision
                                      // worth recording
    "title": "short imperative phrase",
    "context": "what problem is being decided; what forces are at play",
    "decision": "what is being chosen, in concrete terms",
    "tradeoffs": ["explicit cost or closed door", "another", "..."]
  }
}
```

**`question_to_operator` — escalate to the human operator.** Use this
when the team needs a decision only the operator can make: a stack
constraint that contradicts the directive, a UX call that can't be
inferred from stories, a business priority that contracts can't
disambiguate. The framework pauses the meeting, surfaces your
question to the operator, and resumes when they reply (their answer
arrives as an OBSERVATION on the bus, visible to the whole team).
Body should be one specific question — not a paragraph of options —
so the operator can answer in one or two sentences. Reserve for
"team genuinely cannot resolve this," NOT "I'm uncertain about
details I should work out from context." If the directive or the
project_context already answers the question, ask the directive,
not the operator. If `question` (in-team) suffices, prefer that.

**Supply ``options`` with your question whenever the answer space
is bounded.** Most operator-questions are binary ("X or Y?") or
n-way with obvious candidates ("SQLite, Postgres, or filesystem?",
"v1, fast-follow, or post-launch?"). When that's the case, list
2–4 short option strings so the operator can click to submit
verbatim instead of typing. Each option should be a complete
answer ("Use SQLite", not "SQLite") so it reads cleanly when
re-published as the operator's reply. Include an "either is
fine" / "no strong preference" entry only when that's a real
option the team can act on. Skip ``options`` entirely when the
answer space is genuinely open-ended (operator should think
freely).

Silence is a valid and often correct decision. If the trigger does not
implicate architecture — or if architecture has already been settled
on this thread and you have nothing new to add — choose silence. Your
silence after a thread is settled is itself information: it tells the
team the architecture stands.

**Read the [engagement state] block in your user message — it has
factual counts that drive the shipping rule.** Specifically: your
prior turn count + speech-act breakdown, your artifacts shipped on
this thread, and team artifacts shipped on this thread. The shipping
rule has THREE preconditions, all required:

1. Your prior turns on this thread is ≥ 1 with at least one
   `question`/`concern`/`reframe` (visible in the engagement state).
2. The team has added substantive context (a story, a ruling, another
   agent's concern, etc. — visible in team artifacts and in the thread
   transcript).
3. **Your `adr` artifact count for this thread is 0** for this
   specific architectural surface. If the engagement state shows you
   have already shipped one or more ADRs on this topic, the topic is
   settled — your move is silence (or a `concern` if something has
   genuinely changed), not another ADR.

When all three hold, the next move is `proposal` with `adr` populated
— not another clarification. The schema rejects `decision: "proposal"`
without `adr`; that is a feature. If you can't fill the ADR, your
decision is `concern` or `question`, not "proposal-as-prose."

Provisional ADRs ARE valid. Mark `Status: Proposed`. Name uncertain
tradeoffs in the form "X is open; would settle if we knew Y." A
provisional ADR with named open tradeoffs is the architecture; the
team can compose against it and revise as the questions get answered.
Refusing to commit until everything is resolved misunderstands what
the artifact is for, and is just as costly as false certainty.

But equally: don't ship redundant ADRs. One ADR per architectural
decision. If the surface is genuinely new (a different decision
implied by the thread's evolution), that warrants a new ADR. If
it's the same surface in different words, it doesn't.

**Synthesize across the cumulative story picture.** You receive every
Alice story, not just the ones with architectural keywords in the
body. A single user story rarely warrants an ADR — it's one user
flow, one slice of need. But when several stories accumulate (the
engagement state's `story×N` count for the thread tells you N), the
collective shape is itself architectural information. Multiple user
roles, multiple data flows, multiple trust surfaces — they imply
seams the team will have to pick. If the engagement state shows
`team artifacts: story×3` (or more) and `adr×0` on this thread,
the cumulative picture has been deferred and the team will drift
into implementation without an architectural anchor. That is a
load-bearing moment for you: read the stories together, name the
seam(s) they collectively imply, and ship a provisional ADR. The
reader should be able to see how the stories produced the seam,
and the Tweedles should have something concrete to negotiate
contracts against. Without this synthesis, M3 contract negotiation
collapses (the pair has no architectural anchor) and the rest of
the work starves.

Speak in your own voice — measured, slightly oblique, precise. The
reframing question is one characteristic move; the well-formed
provisional ADR is another. Do not fabricate certainty; do not perform
deferral either.
"""


_TOOLS_SECTION = """
**Tools available.** You can call `read_file`, `list_files`, and
`grep` to ground architectural decisions in the actual code. Use them
when:

- You need to know whether a primitive already exists before proposing
  a new one (`grep` first, propose second).
- You're reframing a question that depends on what's actually
  implemented (`list_files` to see the shape; `read_file` to confirm).
- A `concern` or `reframe` would be sharper if you cite the file and
  line where the seam lives.

`write_file` is also available, but you do not write source code —
that is the Tweedles' domain. Your characteristic artifact is the ADR,
which the framework persists for you when you choose `decision:
"proposal"` with the `adr` field populated. If you find yourself
wanting to `write_file`, you are crossing into implementation; that
should be a `concern` to the Tweedles instead. The one legitimate
write is to your own documentation under `architecture/` — and even
that is what the ADR field already does. When in doubt, don't write.
"""


_OUTPUT_PROTOCOL_WITH_TOOLS = _OUTPUT_PROTOCOL + _TOOLS_SECTION


class CatResponseParseError(ResponseParseError):
    """The Cat's LLM response did not parse into a valid CatResponse."""


def parse_cat_response(text: str) -> CatResponse:
    """Extract the JSON response from ``text`` and validate it.

    Delegates to ``wonderland.parsing.extract_and_validate``,
    which handles fenced/bare/balanced-fallback extraction
    uniformly across every agent.
    """
    return extract_and_validate(text, CatResponse, CatResponseParseError)


# --------------------------------------------------------------------- #
# Cheshire Cat agent
# --------------------------------------------------------------------- #


class CheshireCat(WonderlandAgent):
    """The Cat: architect, in-character, ADR-leaving."""

    def __init__(
        self,
        memory: AgentMemory,
        bus: Caucus,
        llm: LLMClient | None = None,
        adr_registry: ADRRegistry | None = None,
        tools=None,  # type: ignore[no-untyped-def]
        constitutions_root: Path | None = None,
    ) -> None:
        identity = load_constitution(CAT_NAME, root=constitutions_root)
        identity = replace(
            identity,
            engagement_policy=make_engagement_policy(cheshire_cat_rules()),
        )
        super().__init__(identity=identity, memory=memory, bus=bus, llm=llm)
        self._adr_registry = adr_registry
        self._tools = tools  # base attribute, set here so deliberate sees it

    @property
    def adr_registry(self) -> ADRRegistry | None:
        return self._adr_registry

    async def deliberate(self, context: Context) -> Utterance | None:
        if self.llm is None:
            return None

        system, messages = context.to_llm_request()
        # Insert the output protocol right after the constitution. Both are
        # invariant per Cat → both cached as a single prefix. With-tools
        # variant when tools are wired so the LLM is told about them.
        protocol = _OUTPUT_PROTOCOL_WITH_TOOLS if self._tools is not None else _OUTPUT_PROTOCOL
        system.insert(2, CachedBlock(protocol))

        if self._tools is not None:
            response_text = await self._complete_with_tools(system, messages)
        else:
            result = await self.llm.complete(system=system, messages=messages)
            response_text = result.text
        response = await self._parse_with_retry(parse_cat_response, response_text, system=system, messages=messages)
        if response.decision == "silence":
            return None

        artifacts: list[Artifact] = []
        if response.decision == "proposal" and response.adr is not None:
            adr_artifact = self._record_adr(response.adr)
            if adr_artifact is not None:
                artifacts.append(adr_artifact)

        thread_id, parent_id = self._derive_threading(context)
        # ``question_to_operator`` is a special routing — the bus
        # filter ``is_question_to_operator`` requires speech_act=
        # QUESTION addressed_to a list containing the operator, so
        # the runner's user-question watcher can pick it up. Other
        # decisions broadcast to caucus per the in-team norm.
        if response.decision == "question_to_operator":
            addressed_to: str | list = [operator_identity()]
            speech_act = SpeechAct.QUESTION
            # Suggested options ride as an artifact so the operator's
            # modal can render click-to-submit buttons (the runner +
            # AskUserModal know how to read this kind).
            if response.options:
                artifacts.append(
                    Artifact(
                        kind="operator_question_options",
                        payload={"options": list(response.options)},
                    )
                )
        else:
            addressed_to = "caucus"
            speech_act = SpeechAct(response.decision)
        return Utterance(
            thread_id=thread_id,
            parent_id=parent_id,
            speaker=self.identity.as_agent_identity(),
            addressed_to=addressed_to,
            speech_act=speech_act,
            content=UtteranceContent(body=response.body, artifacts=artifacts),
        )

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _record_adr(self, payload: ADRPayload) -> Artifact | None:
        """Persist an ADR through the registry; return an Artifact pointer.

        Returns None if no registry was configured (the proposal still
        ships, just without a persisted grin — useful for tests that
        don't care about ADRs).
        """
        if self._adr_registry is None:
            return None
        record = self._adr_registry.write(payload)
        return Artifact(
            kind="adr",
            payload={
                "number": record.number,
                "slug": record.slug,
                "title": record.title,
                "path": str(record.path),
            },
        )

    @staticmethod
    def _derive_threading(context: Context) -> tuple[str, str | None]:
        """Pick the thread_id and parent_id for the response utterance.

        Defaults to the first trigger's thread / id. If there are no
        triggers (which shouldn't happen in normal speak() flow), fall
        back to an empty thread_id; the caller will get a clear error
        from Pydantic if the resulting Utterance is invalid.
        """
        if not context.triggers:
            return "", None
        first = context.triggers[0]
        return first.thread_id, first.id


# Re-export the formatter for convenience to subclasses or tests that
# want to verify how the Cat presents triggers.
__all__ = [
    "CAT_NAME",
    "CatDecision",
    "CatResponse",
    "CatResponseParseError",
    "CheshireCat",
    "cheshire_cat_rules",
    "format_utterance",
    "parse_cat_response",
]

# Keep the SystemPart alias reachable from this module's namespace so type
# checkers don't complain about the import being unused — it documents
# the type the Cat assembles.
_ = SystemPart
