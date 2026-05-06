"""Tweedledee + Tweedledum — the implementation pair.

Per tweedledee.md, tweedledum.md, and tweedle_pair_protocol.md
(WONDERLAND_SPEC §5). The Tweedles are the framework's first paired
agents — each has a singular self-model AND a shared pair-protocol.
This module instantiates both because the pair is a unit per the
protocol; splitting them into separate modules would obscure that
the engagement rules and output protocol are mirror-image variants
of the same shape.

Constitution loading is doubled: each Tweedle's identity carries
its own constitution text *concatenated with* the shared
``tweedle_pair_protocol.md``, so both texts ride in the cached
system prefix on every deliberation. This makes the pair-protocol
part of who the Tweedle is, not a one-off instruction.

Runtime shape mirrors the other agents: load constitution(s), wire
engagement rules from §III, override deliberate() with a JSON
output protocol, persist implementations through an
ImplementationRegistry. The two agents share TweedleResponse and
the parser; engagement rules differ only in which sibling they're
oriented toward.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field, field_validator

from wonderland.agent import Context, WonderlandAgent
from wonderland.contract_note import (
    ContractNotePayload,
    ContractNoteRegistry,
    ContractNoteState,
)
from wonderland.engagement import (
    EngagementRules,
    addressed_to,
    almost_never,
    always,
    make_engagement_policy,
    rarely,
    selectively,
    speaker_is,
)
from wonderland.identity import Identity, load_constitution
from wonderland.implementation import (
    ImplementationPayload,
    ImplementationRegistry,
    ImplementationSide,
)
from wonderland.llm import CachedBlock
from wonderland.parsing import extract_and_validate
from wonderland.tools import Tools
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


TWEEDLEDEE_NAME = "tweedledee"
TWEEDLEDUM_NAME = "tweedledum"
PAIR_PROTOCOL_FILENAME = "tweedle_pair_protocol.md"


# --------------------------------------------------------------------- #
# Constitution loading — own constitution + shared pair protocol
# --------------------------------------------------------------------- #


def _default_constitutions_root() -> Path:
    """Path to constitutions/ relative to this package layout.

    Mirrors ``wonderland.identity._default_constitutions_root`` — kept
    local to avoid coupling to that module's private surface.
    """
    return Path(__file__).resolve().parent.parent.parent.parent / "constitutions"


def _load_paired_identity(self_name: str, constitutions_root: Path | None) -> Identity:
    """Load a Tweedle identity with the pair protocol concatenated.

    The pair protocol is part of who each Tweedle is per
    ``tweedle_pair_protocol.md`` §VI: "the pair's memory of itself is
    part of the pair's identity." Concatenating into the cached
    constitution prefix keeps the protocol on every deliberation
    without paying for it as an uncached layer.
    """
    identity = load_constitution(self_name, root=constitutions_root)
    root = constitutions_root or _default_constitutions_root()
    pair_path = root / PAIR_PROTOCOL_FILENAME
    pair_text = pair_path.read_text(encoding="utf-8")
    combined = f"{identity.constitution_text.rstrip()}\n\n---\n\n{pair_text.rstrip()}\n"
    return replace(identity, constitution_text=combined)


# --------------------------------------------------------------------- #
# Engagement rules — tweedledee.md §III / tweedledum.md §III as data
# --------------------------------------------------------------------- #


def _tweedle_rules(*, self_name: str, sibling_name: str) -> EngagementRules:
    """Shared §III engagement policy with the sibling reference parameterized.

    The two Tweedles' engagement rules are mirror-image — each engages
    ALWAYS with concerns from their sibling about the contract,
    SELECTIVELY with non-contract concerns from the sibling, RARELY
    with sibling implementations that don't touch the contract. The
    only difference is which name fills "sibling".
    """
    return EngagementRules.of(
        # ALWAYS — INVITE addressed to me always wakes me up (Block 2c)
        always(SpeechAct.INVITE, condition=addressed_to(self_name)),
        # ALWAYS — meeting frame from Dodo (or any convenor). Without
        # this, implementation-only meetings (Tweedles + Dodo, no Cat or
        # Alice) don't engage on the convenor directive: the directive
        # lands on the bus and the pair stays silent because their
        # other engagement triggers (tickets, sibling moves) haven't
        # fired. The directive is what tells the pair what this meeting
        # is *for*; ignoring it makes meeting-mode signals impossible.
        always(SpeechAct.DIRECTIVE),
        # ALWAYS — work assignment + the contract-negotiation surface
        always(SpeechAct.TICKET, condition=speaker_is("white_rabbit")),
        always(SpeechAct.PROPOSAL, condition=speaker_is("cheshire_cat")),
        always(SpeechAct.STORY, condition=speaker_is("alice")),
        always(SpeechAct.CONCERN, condition=speaker_is(sibling_name)),
        # Sibling questions count as a contract-negotiation surface even
        # when addressed to caucus — per Pair Protocol §IV's contract
        # change request workflow ("Initiator publishes... Counterpart
        # fills in their side's impact"). Without this, sibling
        # questions on the bus get filtered out and the pair can't
        # actually negotiate (one Tweedle asks; the other never sees).
        always(SpeechAct.QUESTION, condition=speaker_is(sibling_name)),
        # Contract Notes from the sibling are the explicit Pair Protocol §IV
        # negotiation surface — never silent on these.
        always(SpeechAct.CONTRACT_NOTE, condition=speaker_is(sibling_name)),
        always(SpeechAct.TEST_SCENARIO, condition=speaker_is("mad_hatter")),
        always(SpeechAct.REVIEW, condition=speaker_is("caterpillar")),
        always(SpeechAct.QUESTION, condition=addressed_to(self_name)),
        # SELECTIVELY — refined by deliberate()
        selectively(SpeechAct.RULING, condition=speaker_is("queen_of_hearts")),
        selectively(SpeechAct.OBSERVATION, condition=speaker_is("dormouse")),
        # RARELY — sibling implementations that don't touch the contract are
        # not the Tweedle's primary attention surface (per §III)
        rarely(SpeechAct.IMPLEMENTATION, condition=speaker_is(sibling_name)),
        rarely(SpeechAct.DEFERENCE),
        # ALMOST_NEVER — explicit guards against the §VIII Architectural-drift
        # failure mode. The Tweedles don't issue these speech acts; engaging
        # with same-typed utterances from non-canonical speakers would just
        # be domain-leak noise.
        almost_never(SpeechAct.STORY),  # not from Alice
        almost_never(SpeechAct.PROPOSAL),  # not from Cat
        almost_never(SpeechAct.TICKET),  # not from Rabbit
        almost_never(SpeechAct.RULING),  # not from Queen
        almost_never(SpeechAct.TEST_SCENARIO),  # not from Hatter
        almost_never(SpeechAct.REVIEW),  # not from Caterpillar
        almost_never(SpeechAct.OBSERVATION),  # not from Dormouse
        almost_never(SpeechAct.DIRECTIVE),
        # Contract Notes from non-Tweedles would be domain-leak — only the
        # pair owns this artifact.
        almost_never(SpeechAct.CONTRACT_NOTE),
    )


def tweedledee_rules() -> EngagementRules:
    """Tweedledee's §III engagement policy — sibling = Tweedledum."""
    return _tweedle_rules(self_name=TWEEDLEDEE_NAME, sibling_name=TWEEDLEDUM_NAME)


def tweedledum_rules() -> EngagementRules:
    """Tweedledum's §III engagement policy — sibling = Tweedledee."""
    return _tweedle_rules(self_name=TWEEDLEDUM_NAME, sibling_name=TWEEDLEDEE_NAME)


# --------------------------------------------------------------------- #
# LLM output protocol — shared between the pair
# --------------------------------------------------------------------- #


TweedleDecision = Literal[
    "implementation",
    "contract_note",
    "concern",
    "question",
    "deference",
    "invite",
    "silence",
]


TweedleContractNoteOperation = Literal[
    "propose",
    "respond",
    "mark_agreed",
    "escalate",
    "defer",
]


class TweedleContractNoteAction(BaseModel):
    """One Contract Note operation a Tweedle wants to perform on this turn.

    Operation-discriminated rather than payload-discriminated so the
    LLM's output is unambiguous about whether it is starting a new
    note vs. responding to an existing one. Validators enforce per-
    operation field requirements; the ContractNotePayload is built
    only when the operation is `propose` (the others reference an
    existing note by slug).
    """

    operation: TweedleContractNoteOperation
    slug: str = ""
    """Slug of the existing Contract Note to update. Required for any
    operation other than `propose`."""

    # Fields used only by `propose` (full new note).
    title: str = ""
    current_shape: str = ""
    proposed_change: str = ""
    source: str = ""

    # Fields filled in by either `propose` (the proposer's own side)
    # or `respond` (the counterpart filling in their side).
    frontend_impact: str = ""
    backend_impact: str = ""

    # Fields used by terminal operations.
    contract_version: str = ""
    """Locked at `mark_agreed`. Empty otherwise."""
    resolution: str = ""
    """Required for `mark_agreed`, `escalate`, `defer`. Names what
    got agreed / why the escalation / why the deferral."""

    def model_post_init(self, _context: object) -> None:  # type: ignore[override]
        if self.operation == "propose":
            for field in ("title", "current_shape", "proposed_change", "source"):
                if not getattr(self, field).strip():
                    raise ValueError(
                        f"TweedleContractNoteAction(propose) requires {field}; "
                        "a new Contract Note must name the contract being "
                        "changed and what specifically is being proposed."
                    )
            if not (self.frontend_impact.strip() or self.backend_impact.strip()):
                raise ValueError(
                    "TweedleContractNoteAction(propose) requires the proposer's "
                    "own side impact (frontend_impact or backend_impact)."
                )
        else:
            if not self.slug.strip():
                raise ValueError(
                    f"TweedleContractNoteAction({self.operation}) requires "
                    "a slug pointing at an existing Contract Note."
                )
            if self.operation == "respond" and not (
                self.frontend_impact.strip() or self.backend_impact.strip()
            ):
                raise ValueError(
                    "TweedleContractNoteAction(respond) requires the "
                    "counterpart's impact (frontend_impact or backend_impact)."
                )
            if self.operation == "mark_agreed" and not self.contract_version.strip():
                raise ValueError(
                    "TweedleContractNoteAction(mark_agreed) requires "
                    "contract_version — the locked version both sides accept."
                )
            if (
                self.operation in ("mark_agreed", "escalate", "defer")
                and not self.resolution.strip()
            ):
                raise ValueError(
                    f"TweedleContractNoteAction({self.operation}) requires "
                    "resolution — name what got agreed / why the escalation / "
                    "why the deferral."
                )


class TweedleResponse(BaseModel):
    """Structured JSON either Tweedle returns from deliberate().

    When ``decision == "implementation"``, ``implementations`` must
    contain at least one ``ImplementationPayload``. The default is one
    — a Tweedle ships one piece of work at a time — but the schema
    permits more so a batched landing of related work can be reported
    in one turn.

    When ``decision == "contract_note"``, ``contract_notes`` must
    contain at least one ``TweedleContractNoteAction`` — propose a
    new note, respond to one, or transition an existing one to a
    terminal state.
    """

    decision: TweedleDecision
    body: str = ""
    implementations: list[ImplementationPayload] = Field(default_factory=list)
    contract_notes: list[TweedleContractNoteAction] = Field(default_factory=list)
    invitees: list[str] = Field(default_factory=list)
    """Agent names to buzz into the current thread when decision is
    'invite'. The framework adds them to the thread's roster before
    the invite reaches the bus, so they receive it + future thread
    utterances. Must be non-empty when decision is 'invite'."""

    @field_validator("decision", mode="before")
    @classmethod
    def _decision_coerce_off_list(cls, v: object) -> object:
        """Live Haiku 4.5 occasionally hallucinates decision values from
        adjacent agents' schemas (most often `acknowledgment` for an
        intended `deference`, or `review` for a `concern` whose body is
        the finding). Map the closest known cases so the response isn't
        lost to literal-validation rejection. Anything that doesn't match
        a known alias still falls through to the Literal check, which
        reports a clear error listing the valid values."""
        if not isinstance(v, str):
            return v
        normalized = v.strip().lower()
        aliases = {
            # Tweedle ack of sibling work → deference (the closest valid
            # "I'm aligned, you proceed" act in the Tweedle schema).
            "acknowledgment": "deference",
            "acknowledge": "deference",
            "ack": "deference",
            # Caterpillar's act; Tweedles sometimes reach for it when the
            # meeting goal is "review" — but their actual move is to
            # surface the issue as a concern.
            "review": "concern",
            "finding": "concern",
            # Common LLM rephrasings.
            "implement": "implementation",
            "propose": "contract_note",
            "respond": "contract_note",
            "ask": "question",
            "defer": "deference",
            "stay_silent": "silence",
            "no_action": "silence",
        }
        return aliases.get(normalized, v)

    @field_validator("body", mode="before")
    @classmethod
    def _body_none_to_empty(cls, v: object) -> object:
        # Live Haiku 4.5 sometimes emits explicit nulls for omitted fields.
        # Coerce to default per the established pattern.
        return "" if v is None else v

    @field_validator("implementations", mode="before")
    @classmethod
    def _implementations_none_to_empty(cls, v: object) -> object:
        return [] if v is None else v

    @field_validator("contract_notes", mode="before")
    @classmethod
    def _contract_notes_none_to_empty(cls, v: object) -> object:
        return [] if v is None else v

    @field_validator("invitees", mode="before")
    @classmethod
    def _invitees_none_to_empty(cls, v: object) -> object:
        return [] if v is None else v

    def model_post_init(self, _context: object) -> None:  # type: ignore[override]
        if self.decision == "implementation" and not self.implementations:
            raise ValueError(
                "TweedleResponse: decision='implementation' requires at least "
                "one entry in `implementations`. Choose a different decision "
                "(concern/question/etc.) or include the implementation you "
                "intended to ship."
            )
        if self.decision == "contract_note" and not self.contract_notes:
            raise ValueError(
                "TweedleResponse: decision='contract_note' requires at least "
                "one entry in `contract_notes`. Either propose a new note, "
                "respond to an existing one, or pick a different decision."
            )
        if self.decision == "invite" and not self.invitees:
            raise ValueError(
                "TweedleResponse: decision='invite' requires at least one "
                "entry in `invitees` — the agent name(s) you want to buzz "
                "into the meeting. Use one of: alice, cheshire_cat, "
                "white_rabbit, mad_hatter, caterpillar, queen_of_hearts, "
                "dormouse, tweedledee, tweedledum. (Dodo is always in the "
                "meeting; no need to invite him.)"
            )


def _build_protocol(side: ImplementationSide, sibling_name: str, with_tools: bool = False) -> str:
    """Construct the per-side output protocol.

    Both Tweedles share most of the protocol — the differences are
    the side label, the field-population guidance, and which sibling
    they're negotiating with. Building the protocol per side avoids
    awkward "fill in either UI states OR invariants" hedging.
    """
    if side is ImplementationSide.FRONTEND:
        side_fields = (
            '      "ui_states_implemented": ["loading", "empty", "error-recoverable", "..."],\n'
            '      "client_state": "what state lives on the client and how it reconciles with server state",\n'
        )
        side_guidance = (
            "You are the frontend Tweedle. Populate `ui_states_implemented` with the "
            "named states the user might encounter (loading / empty / error-recoverable / "
            "error-unrecoverable / offline-queued / stale / pending-sync / etc.) and "
            "`client_state` with what state lives on the client, why, and how it "
            "reconciles with the canonical server state. Leave `invariants_enforced`, "
            "`schema_changes`, and `failure_modes_handled` empty — those are Tweedledum's."
        )
    else:
        side_fields = (
            '      "invariants_enforced": ["a message has exactly one sender", "..."],\n'
            '      "schema_changes": "migrations introduced, with backward-compatibility notes",\n'
            '      "failure_modes_handled": ["worker crash mid-message: dead-letter", "..."],\n'
        )
        side_guidance = (
            "You are the backend Tweedle. Populate `invariants_enforced` with named "
            "invariants this implementation maintains, each with how (DB constraint, "
            "validation, transactional boundary, etc.); `schema_changes` with any "
            "migrations introduced and their backward-compatibility properties; "
            "`failure_modes_handled` with named failure modes and their handling "
            "behavior (retry / dead-letter / propagate / fallback). Leave "
            "`ui_states_implemented` and `client_state` empty — those are Tweedledee's."
        )

    own_impact_field = (
        "frontend_impact" if side is ImplementationSide.FRONTEND else "backend_impact"
    )
    counterpart_impact_field = (
        "backend_impact" if side is ImplementationSide.FRONTEND else "frontend_impact"
    )
    tools_section = _TOOLS_SECTION if with_tools else ""

    return f"""\
You will respond with exactly one fenced JSON block. No prose outside the block.

The JSON must conform to this schema:

```
{{
  "decision": "implementation" | "contract_note" | "concern" | "question" | "deference" | "invite" | "silence",
  "body": "the natural-language content of your utterance (omit for silence)",
  "implementations": [               // include ONLY when decision is "implementation"
    {{
      "title": "short summary of what shipped, e.g. 'Translation message subscription'",
      "side": "{side.value}",
      "ticket_reference": "the Rabbit ticket slug or number this implements",
      "approach_summary": "what the code actually does, in concrete terms",
      "contract": "the contract version + shape this honors, e.g. 'message-envelope v3 (translation_status enum + source_lang FK)'",
      "files_touched": ["src/path/to/file.py: brief description of the change", "..."],
      "open_questions_for_pair": ["specific question for {sibling_name} about contract or coordination"],
      "ready_for_review": true | false,
      "known_limitations": ["things this doesn't yet handle, with severity"],
{side_fields}    }}
  ],
  "invitees": ["agent_name", "..."],  // include ONLY when decision is "invite"
                                      // — names from: alice, cheshire_cat, white_rabbit,
                                      // mad_hatter, caterpillar, queen_of_hearts,
                                      // dormouse, tweedledee, tweedledum
                                      // (Dodo is always in the meeting; don't list him)
  "contract_notes": [                // include ONLY when decision is "contract_note"
    {{
      "operation": "propose" | "respond" | "mark_agreed" | "escalate" | "defer",
      "slug": "existing-note-slug",  // required for any operation other than propose
      "title": "short title, e.g. 'Translation message envelope'",  // propose only
      "current_shape": "the contract as it stands today",            // propose only
      "proposed_change": "what's being proposed",                     // propose only
      "source": "story / ticket / bug that surfaced this",            // propose only
      "{own_impact_field}": "your side's impact assessment",          // propose / respond
      "{counterpart_impact_field}": "leave empty — that's {sibling_name}'s",
      "contract_version": "v3 (...)",                                 // mark_agreed only
      "resolution": "what got agreed / why escalated / why deferred"  // mark_agreed / escalate / defer
    }}
  ]
}}
```

**Contract is non-negotiable.** Per the Tweedle Pair Protocol §II,
"implicit contracts are bugs in the making." The schema rejects
empty-contract implementations. Cite the OpenAPI revision, schema
version, message envelope version, or whatever shape your agreement
with {sibling_name} takes. If you're shipping a contract change, name
the new version and reference the Contract Note that authorized it.

**Contract Notes carry the negotiation explicitly.** Per Pair
Protocol §IV, contract change requests flow through Contract Notes
— propose with your side's impact filled, wait for {sibling_name}
to respond with theirs, then either side marks agreed (locks the
new contract version) or escalates to the Cat. Don't negotiate
contract changes in `concern` / `question` bodies; that's how
contract drift happens. Use the contract_note action.

**Read the [engagement state] block in your user message — it has
factual counts that drive the shipping rule.** Specifically: your
prior turn count + speech-act breakdown, your contract_notes shipped,
and team artifacts shipped. The shipping rule has THREE preconditions,
all required:

1. Your prior turns on this thread is ≥ 1 with at least one
   `question`/`concern` on a specific contract surface (envelope
   shape, event timing, persistence semantics, error semantics, etc.).
2. The topic is still open — {sibling_name} hasn't responded
   substantively yet.
3. **The team's `contract_note` count for this specific surface is
   0**. If the engagement state shows contract_notes already exist on
   this thread, scan the thread history for the one matching your
   surface — if there's a match, your move is `respond` or
   `mark_agreed` to that existing note, not a new propose.

When all three hold, the next move is `contract_note` operation
`propose` — not another `question`/`concern`. Two clarification turns
on the same seam without a contract is performative deferral; it
leaves the negotiation in limbo and gives {sibling_name} nothing
concrete to respond to.

Half-formed contracts are valid: propose with your side's impact
filled, the other side empty, marked `state=proposed`. Your sibling
will respond and fill in their side. The contract becomes more
concrete THROUGH the negotiation, not before it.

Equally important: don't ship redundant contract notes. One per
seam. If a contract note for the message envelope already exists,
extending the envelope's status enum is a `respond` to that note,
not a new note about "envelope status enum." Read the thread for
existing contract notes before proposing.

**Buzz another agent in when the meeting needs them.** When you
discover the work needs an agent who isn't currently in the room
— architectural ambiguity calls for the Cat, a security/compliance
seam calls for the Queen, a test surface calls for the Hatter,
production reality calls for the Dormouse — issue an `invite`
addressed to the names you need. The body should explain what's
needed and the context they're walking into. The framework adds
the invitee to the meeting before the invite hits the bus, so they
receive it and can engage immediately. Prefer invite over
suffering through ambiguity you can't resolve alone.

**But contract negotiation is the pair's work, not a consultation.**
Do *not* `invite` to originate a contract. The pair drafts; the
contract becomes concrete through your negotiation with your
sibling, not by deferring upstream. If the pair has shipped zero
contract notes on this thread, your next move is `contract_note`
(half-formed is fine, `state=proposed`), `question` to your
sibling, or `concern` — never `invite`. Once a draft exists,
collaborators can `concern` or `respond`; until then the work is
yours. The Cat in particular will Socratically probe rather than
answer when invited mid-draft (that's the Cat being Cat); don't
summon riddles you'll then have to wait through. Ship the draft
first.

**Ticket reference is non-negotiable.** Implementations must trace to
a Rabbit ticket. If the work isn't ticketed, the move is to ask the
Rabbit to ticket it before shipping — not to ship and backfill.

{side_guidance}

`ready_for_review` is the explicit Caterpillar engagement gate per
§VI. Set it to `false` while you're still iterating; set it to `true`
when the implementation is ready for review and you're prepared to
respond to the findings.

Domain discipline matters. You do **not** propose architecture (the
Cat's domain), write tickets (the Rabbit's), generate stories
(Alice's), write tests (the Hatter's), review code quality (the
Caterpillar's), rule on security (the Queen's), or report production
behavior (the Dormouse's). When the work pulls you across one of
those lines, choose `concern` (raise the issue to its owner) or
`deference` (explicit handoff).

Speak in concrete, implementation-grounded sentences. Ask {sibling_name}
specific questions when the contract is unclear. Use
`open_questions_for_pair` for those questions inline; that's how the
contract negotiation stays explicit per the Pair Protocol §IV.
Concede readily when {sibling_name}'s point is correct; press when
yours is. The argument is the work.
{tools_section}"""


_TOOLS_SECTION = """
**Tools available.** You can call `read_file`, `write_file`,
`list_files`, and `grep` to inspect existing code and ship new code
to disk. Use them this way:

- Before writing new code, `list_files` and/or `grep` to find what's
  already there. Don't reinvent existing primitives.
- When shipping an `implementation`, your `write_file` calls produce
  the actual files; your `files_touched` field should match the paths
  you wrote. **The working tree IS the implementation artifact.** Your
  `decision: "implementation"` utterance is a brief bus record — what
  CN/ticket you addressed, the load-bearing decisions you made, any
  open questions for your sibling — not a metadata dump. The reviewer
  reads `git_diff`, not your `implementations` payload, to see what
  shipped. Keep `approach` and `known_limitations` short and specific
  to what's *not* obvious from reading the diff.
- `git_status` and `git_diff` are also available — use them mid-turn
  to verify what you've written so far, especially when shipping
  multiple files. A pair-coherence concern surfaces faster from
  reading the diff than from re-reading your own write_file calls.
- Tools are sandboxed to the project root. Paths are relative.
- After your tool calls, return your final JSON response (the
  implementation / contract_note / concern / etc.). The JSON is what
  the team sees as your utterance; the tool calls are how you got
  there. **If you shipped code via write_file, your final decision
  should be `implementation` with files_touched matching what you
  wrote — do not pick `silence` after writing files. The bus record
  is how the team knows you completed the work.**

You do not have a `run_command` tool — you cannot execute code. The
Caterpillar reviews; the Hatter tests; the Dormouse observes. Your
job is to write code that holds the contract; their jobs are to
verify it.
"""


_OUTPUT_PROTOCOL_FRONTEND = _build_protocol(ImplementationSide.FRONTEND, TWEEDLEDUM_NAME)
_OUTPUT_PROTOCOL_BACKEND = _build_protocol(ImplementationSide.BACKEND, TWEEDLEDEE_NAME)
_OUTPUT_PROTOCOL_FRONTEND_WITH_TOOLS = _build_protocol(
    ImplementationSide.FRONTEND, TWEEDLEDUM_NAME, with_tools=True
)
_OUTPUT_PROTOCOL_BACKEND_WITH_TOOLS = _build_protocol(
    ImplementationSide.BACKEND, TWEEDLEDEE_NAME, with_tools=True
)


class TweedleResponseParseError(ValueError):
    """A Tweedle's LLM response did not parse into a valid TweedleResponse."""


def parse_tweedle_response(text: str) -> TweedleResponse:
    """Extract the JSON response from ``text`` and validate it.

    Delegates to ``wonderland.parsing.extract_and_validate`` for the
    fenced/bare/balanced-fallback extraction logic — the same helper
    every agent uses, so a parsing improvement in one place lifts
    every agent's resilience.
    """
    return extract_and_validate(text, TweedleResponse, TweedleResponseParseError)


# --------------------------------------------------------------------- #
# Shared agent base — keeps the two Tweedles synchronized
# --------------------------------------------------------------------- #


class _TweedleBase(WonderlandAgent):
    """Shared implementation. Subclasses set side, name, rules, and protocol.

    Mirrors the Cat / Rabbit / Alice / Hatter / Caterpillar / Queen /
    Dormouse pattern. The only inter-Tweedle difference is which
    sibling each is oriented toward; everything else is shared.
    """

    SIDE: ImplementationSide
    PROTOCOL: str
    PROTOCOL_WITH_TOOLS: str

    def __init__(
        self,
        memory: AgentMemory,
        bus: Caucus,
        llm: LLMClient | None = None,
        implementation_registry: ImplementationRegistry | None = None,
        contract_note_registry: ContractNoteRegistry | None = None,
        tools: Tools | None = None,
        constitutions_root: Path | None = None,
    ) -> None:
        identity = _load_paired_identity(self._self_name(), constitutions_root)
        identity = replace(
            identity,
            engagement_policy=make_engagement_policy(self._rules()),
        )
        super().__init__(identity=identity, memory=memory, bus=bus, llm=llm)
        self._implementation_registry = implementation_registry
        self._contract_note_registry = contract_note_registry
        # When set, deliberate() runs a tool-use loop so the LLM can
        # read/write/list/grep files mid-deliberation. The tools are
        # sandboxed to the project root by Tools itself; the Tweedles
        # don't need to know about path safety. None = no tools = the
        # original single-shot deliberate flow (preserves backward
        # compat for tests + scripts that don't wire tools).
        self._tools = tools

    # Subclasses provide these — kept as classmethods so the rules table
    # is constructible without instantiation (useful in tests).
    @classmethod
    def _self_name(cls) -> str:
        raise NotImplementedError

    @classmethod
    def _rules(cls) -> EngagementRules:
        raise NotImplementedError

    @property
    def implementation_registry(self) -> ImplementationRegistry | None:
        return self._implementation_registry

    @property
    def contract_note_registry(self) -> ContractNoteRegistry | None:
        return self._contract_note_registry

    @property
    def tools(self) -> Tools | None:
        return self._tools

    async def deliberate(self, context: Context) -> Utterance | None:
        if self.llm is None:
            return None

        system, messages = context.to_llm_request()
        # Output protocol cached alongside the constitution + pair protocol —
        # all three are invariant per Tweedle. Two variants: with and
        # without the tools section, picked based on whether tools are
        # wired so the LLM is told about its actual capabilities.
        protocol = self.PROTOCOL_WITH_TOOLS if self._tools is not None else self.PROTOCOL
        system.insert(2, CachedBlock(protocol))

        # Run the tool-use loop when tools are wired; fall back to the
        # original single-shot completion otherwise so the existing
        # mocked-LLM test surface is preserved.
        if self._tools is not None:
            response_text = await self._complete_with_tools(system, messages)
        else:
            result = await self.llm.complete(system=system, messages=messages)
            response_text = result.text

        response = parse_tweedle_response(response_text)

        # Working-tree-as-implementation-artifact (analysis 018 followup):
        # if write_file calls landed during the tools loop but the LLM
        # picked a non-implementation decision (silence, contract_note,
        # etc.), coerce: emit the bus utterance with speech_act=
        # IMPLEMENTATION + a synthesized artifact recording the file
        # paths. The work IS on disk; the bus utterance must reflect it
        # so the Caterpillar's engagement on IMPLEMENTATION-from-Tweedles
        # fires and review can anchor against the actual paths.
        coerced_body: str | None = None
        coerced_artifact: Artifact | None = None
        coerced_decision: str | None = None
        if (
            self._tools is not None
            and self._last_write_file_paths
            and response.decision != "implementation"
        ):
            coerced_body, coerced_artifact = self._synthesized_implementation_artifact(
                response.decision, response.body, self._last_write_file_paths
            )
            coerced_decision = "implementation"

        if coerced_decision is None and response.decision == "silence":
            return None

        artifacts: list[Artifact] = []
        if coerced_artifact is not None:
            artifacts.append(coerced_artifact)
        elif response.decision == "implementation":
            artifacts.extend(self._record_implementations(response.implementations))
        elif response.decision == "contract_note":
            artifacts.extend(self._record_contract_notes(response.contract_notes))

        # INVITE addressing: when the LLM chose `invite`, set
        # addressed_to to the invitee identities so WonderlandAgent.speak's
        # _apply_invite_if_any picks them up and updates the roster
        # before the bus publishes.
        addressed_to: list | str
        if response.decision == "invite":
            from wonderland.utterance import AgentIdentity

            addressed_to = [
                AgentIdentity(name=name, constitution_version="0.1")
                for name in response.invitees
            ]
        else:
            addressed_to = "caucus"

        thread_id, parent_id = self._derive_threading(context)
        final_decision = coerced_decision or response.decision
        final_body = coerced_body if coerced_body is not None else response.body
        return Utterance(
            thread_id=thread_id,
            parent_id=parent_id,
            speaker=self.identity.as_agent_identity(),
            addressed_to=addressed_to,
            speech_act=SpeechAct(final_decision),
            content=UtteranceContent(body=final_body, artifacts=artifacts),
        )

    # _complete_with_tools is inherited from WonderlandAgent (P6 refactor —
    # the loop is generic, not Tweedle-specific, so other agents with
    # tools wired share the same machinery).

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _record_implementations(self, payloads: list[ImplementationPayload]) -> list[Artifact]:
        if self._implementation_registry is None:
            return []
        artifacts: list[Artifact] = []
        for payload in payloads:
            record = self._implementation_registry.write(payload)
            artifacts.append(
                Artifact(
                    kind="implementation",
                    payload={
                        "number": record.number,
                        "slug": record.slug,
                        "title": record.title,
                        "side": record.side.value,
                        "ticket_reference": record.ticket_reference,
                        "contract": record.contract,
                        "ready_for_review": record.ready_for_review,
                        "path": str(record.path),
                    },
                )
            )
        return artifacts

    def _record_contract_notes(self, actions: list[TweedleContractNoteAction]) -> list[Artifact]:
        """Dispatch each Contract Note action to the registry and emit Artifacts.

        ``propose`` writes a new note. ``respond`` fills in the
        counterpart's impact (and optionally transitions state to
        counterpart_assessed). ``mark_agreed`` / ``escalate`` /
        ``defer`` transition the note to a terminal state. Each
        operation produces one artifact on the Tweedle's utterance.
        """
        if self._contract_note_registry is None:
            return []
        artifacts: list[Artifact] = []
        for action in actions:
            if action.operation == "propose":
                record = self._contract_note_registry.write(
                    ContractNotePayload(
                        title=action.title,
                        current_shape=action.current_shape,
                        proposed_change=action.proposed_change,
                        source=action.source,
                        frontend_impact=action.frontend_impact,
                        backend_impact=action.backend_impact,
                        state=ContractNoteState.PROPOSED,
                    )
                )
            elif action.operation == "respond":
                record = self._contract_note_registry.update(
                    action.slug,
                    frontend_impact=action.frontend_impact or None,
                    backend_impact=action.backend_impact or None,
                    state=ContractNoteState.COUNTERPART_ASSESSED,
                )
            elif action.operation == "mark_agreed":
                record = self._contract_note_registry.update(
                    action.slug,
                    state=ContractNoteState.AGREED,
                    contract_version=action.contract_version,
                    resolution=action.resolution,
                )
            elif action.operation == "escalate":
                record = self._contract_note_registry.update(
                    action.slug,
                    state=ContractNoteState.ESCALATED,
                    resolution=action.resolution,
                )
            else:  # defer
                record = self._contract_note_registry.update(
                    action.slug,
                    state=ContractNoteState.DEFERRED,
                    resolution=action.resolution,
                )

            artifacts.append(
                Artifact(
                    kind="contract_note",
                    payload={
                        "number": record.number,
                        "slug": record.slug,
                        "title": record.title,
                        "operation": action.operation,
                        "state": record.state.value,
                        "contract_version": record.contract_version,
                        "path": str(record.path),
                    },
                )
            )
        return artifacts

    @staticmethod
    def _derive_threading(context: Context) -> tuple[str, str | None]:
        if not context.triggers:
            return "", None
        first = context.triggers[0]
        return first.thread_id, first.id

    def _synthesized_implementation_artifact(
        self, original_decision: str, body: str, paths: list[str]
    ) -> tuple[str, Artifact]:
        """Build a coerced (body, artifact) pair for the case where the
        LLM ran write_file in the tools loop but picked a non-implementation
        decision for its bus utterance. Working tree IS the implementation
        artifact: the structured ImplementationPayload's required fields
        (ticket_reference, contract, approach_summary) aren't recoverable
        without LLM cooperation, so we skip the registry write and emit a
        lightweight artifact with ``synthesized=True``. Caterpillar's
        engagement on IMPLEMENTATION-from-Tweedles fires regardless of
        payload completeness; review targets the actual file paths via
        git_diff."""
        coerce_note = (
            f"\n\n[bus record coerced to implementation: write_file "
            f"calls landed for {', '.join(paths)} but the LLM chose "
            f"`{original_decision}` for the bus utterance. The working "
            f"tree is the artifact; the team should call git_diff to "
            f"see what shipped.]"
        )
        new_body = body.rstrip() + coerce_note
        artifact = Artifact(
            kind="implementation",
            payload={
                "synthesized": True,
                "side": self.SIDE.value,
                "files_touched": list(paths),
                "title": f"Files written in {self._self_name()}'s {self.SIDE.value} turn",
                "original_decision": original_decision,
            },
        )
        return new_body, artifact


class Tweedledee(_TweedleBase):
    """Tweedledee: frontend Tweedle, builds from the user's standpoint inward."""

    SIDE = ImplementationSide.FRONTEND
    PROTOCOL = _OUTPUT_PROTOCOL_FRONTEND
    PROTOCOL_WITH_TOOLS = _OUTPUT_PROTOCOL_FRONTEND_WITH_TOOLS

    @classmethod
    def _self_name(cls) -> str:
        return TWEEDLEDEE_NAME

    @classmethod
    def _rules(cls) -> EngagementRules:
        return tweedledee_rules()


class Tweedledum(_TweedleBase):
    """Tweedledum: backend Tweedle, builds from the data outward."""

    SIDE = ImplementationSide.BACKEND
    PROTOCOL = _OUTPUT_PROTOCOL_BACKEND
    PROTOCOL_WITH_TOOLS = _OUTPUT_PROTOCOL_BACKEND_WITH_TOOLS

    @classmethod
    def _self_name(cls) -> str:
        return TWEEDLEDUM_NAME

    @classmethod
    def _rules(cls) -> EngagementRules:
        return tweedledum_rules()


__all__ = [
    "PAIR_PROTOCOL_FILENAME",
    "TWEEDLEDEE_NAME",
    "TWEEDLEDUM_NAME",
    "TweedleDecision",
    "TweedleResponse",
    "TweedleResponseParseError",
    "Tweedledee",
    "Tweedledum",
    "parse_tweedle_response",
    "tweedledee_rules",
    "tweedledum_rules",
]
