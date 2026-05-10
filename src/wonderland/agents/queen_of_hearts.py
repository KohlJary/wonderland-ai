"""Queen of Hearts — Security / Compliance.

Per queen_of_hearts.md and WONDERLAND_SPEC §5. The Queen does not
propose; she **rules**. Her characteristic move is "off with their
heads" — pointed at vulnerabilities, not at agents. Her
characteristic artifact is the Ruling, which carries severity,
domain, the threat or compliance citation that the Caprice §VIII
guard requires, and acceptance criteria the Tweedles can verify.

Runtime shape mirrors Cat / Rabbit / Alice / Hatter / Caterpillar:
load constitution, wire engagement rules from §III, override
deliberate() with a JSON output protocol, persist rulings through a
RulingRegistry. A single Queen turn can produce multiple rulings
because a single proposal or implementation may surface multiple
distinct concerns.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from wonderland.agent import Context, WonderlandAgent
from wonderland.engagement import (
    EngagementRules,
    addressed_to,
    almost_never,
    always,
    any_of,
    body_contains_any,
    make_engagement_policy,
    rarely,
    selectively,
    speaker_is,
)
from wonderland.identity import load_constitution
from wonderland.llm import CachedBlock
from wonderland.parsing import ResponseParseError, extract_and_validate
from wonderland.ruling import RulingPayload, RulingRegistry
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


QUEEN_NAME = "queen_of_hearts"


# --------------------------------------------------------------------- #
# Engagement rules — queen_of_hearts.md §III as data
# --------------------------------------------------------------------- #


def queen_of_hearts_rules() -> EngagementRules:
    """The Queen's §III engagement policy as machine-checkable rules.

    The keyword heuristics lean permissive — the Queen would rather
    engage on a marginal trigger and choose silence inside
    deliberate() than miss a security implication that the team
    didn't flag. The §VIII "Working alone" failure mode argues for
    breadth: rulings issued without consulting the Hatter or
    Dormouse are rulings that miss known information, so the Queen
    listens widely and rules narrowly.
    """
    security_words = body_contains_any(
        "auth",
        "authentication",
        "authorization",
        "credential",
        "password",
        "session",
        "token",
        "secret",
        "key",
        "encryption",
        "encrypt",
        "decrypt",
        "PII",
        "personal data",
        "private data",
        "audit",
        "log",
        "logging",
        "permission",
        "privilege",
        "admin",
        "role",
        "ACL",
        "sanitize",
        "validate input",
        "injection",
        "XSS",
        "CSRF",
        "SQL",
        "rate limit",
        "CVE",
        "vulnerability",
        "exploit",
        "attack",
    )
    compliance_or_jurisdiction_words = body_contains_any(
        "GDPR",
        "HIPAA",
        "SOC2",
        "SOC 2",
        "PCI",
        "compliance",
        "regulatory",
        "regulation",
        "data residency",
        "retention",
        "consent",
        "right to be forgotten",
        "DSAR",
        "subject access",
    )
    incident_words = body_contains_any(
        "incident",
        "breach",
        "compromise",
        "intrusion",
        "exfiltration",
        "leaked",
        "stolen",
        "reconnaissance",
        "anomalous",
        "spike",
    )
    is_tweedle = any_of(speaker_is("tweedledee"), speaker_is("tweedledum"))

    return EngagementRules.of(
        # ALWAYS — INVITE addressed to me always wakes me up (Block 2c)
        always(SpeechAct.INVITE, condition=addressed_to(QUEEN_NAME)),
        # ALWAYS — the early-engagement surfaces from §III
        always(SpeechAct.PROPOSAL, condition=speaker_is("cheshire_cat")),
        always(
            SpeechAct.IMPLEMENTATION,
            condition=is_tweedle,
        ),
        always(SpeechAct.CONCERN, condition=security_words),
        always(SpeechAct.TEST_SCENARIO, condition=speaker_is("mad_hatter")),
        always(SpeechAct.OBSERVATION, condition=incident_words),
        always(
            SpeechAct.TICKET,
            condition=speaker_is("white_rabbit"),
        ),
        always(SpeechAct.QUESTION, condition=addressed_to(QUEEN_NAME)),
        # SELECTIVELY — the LLM filter inside deliberate() does the §III
        # "selective" refinement
        selectively(SpeechAct.STORY, condition=speaker_is("alice")),
        selectively(SpeechAct.REVIEW, condition=speaker_is("caterpillar")),
        selectively(SpeechAct.DIRECTIVE, condition=compliance_or_jurisdiction_words),
        # RARELY — deference between others isn't hers to act on
        rarely(SpeechAct.DEFERENCE),
        # ALMOST_NEVER — explicit guards against the §VIII Cross-domain-drift
        # failure mode. The Queen does not issue these speech acts and
        # echoing same-typed utterances from non-canonical speakers would
        # just be domain-leak noise.
        almost_never(SpeechAct.PROPOSAL),
        almost_never(SpeechAct.IMPLEMENTATION),
        almost_never(SpeechAct.STORY),
        almost_never(SpeechAct.TEST_SCENARIO),
        almost_never(SpeechAct.REVIEW),
        almost_never(SpeechAct.OBSERVATION),
        almost_never(SpeechAct.TICKET),
        almost_never(SpeechAct.DIRECTIVE),
    )


# --------------------------------------------------------------------- #
# LLM output protocol
# --------------------------------------------------------------------- #


QueenDecision = Literal[
    "ruling",
    "concern",
    "question",
    "question_to_operator",
    "deference",
    "silence",
]


class QueenResponse(BaseModel):
    """Structured JSON the Queen returns from deliberate().

    When ``decision == "ruling"``, ``rulings`` must contain at least
    one ``RulingPayload``. Multiple rulings per turn are valid — a
    single proposal often surfaces multiple distinct concerns
    (auth + PII + audit, for example).
    """

    decision: QueenDecision
    body: str = ""
    rulings: list[RulingPayload] = Field(default_factory=list)

    @field_validator("body", mode="before")
    @classmethod
    def _body_none_to_empty(cls, v: object) -> object:
        # Live Haiku 4.5 sometimes emits explicit nulls for omitted fields.
        # Coerce to default per the established pattern.
        return "" if v is None else v

    @field_validator("rulings", mode="before")
    @classmethod
    def _rulings_none_to_empty(cls, v: object) -> object:
        return [] if v is None else v

    @model_validator(mode="before")
    @classmethod
    def _coerce_empty_ruling_to_concern(cls, data: object) -> object:
        """Live Haiku 4.5 sometimes emits ``decision='ruling'`` with
        ``rulings=[]`` and a substantive ``body`` — the LLM intended to
        ship a ruling but didn't fill the structured payload. Rather
        than reject the whole response (and lose the body), coerce to
        ``decision='concern'`` so the body content survives as a
        legitimate Queen utterance. This is the same shape as the
        Tweedle decision-coercion validator: narrow, observed
        rephrasings only; the schema otherwise stays strict."""
        if not isinstance(data, dict):
            return data
        decision = data.get("decision")
        rulings = data.get("rulings") or []
        body = data.get("body") or ""
        if decision == "ruling" and not rulings and body.strip():
            data = dict(data)
            data["decision"] = "concern"
        return data

    def model_post_init(self, _context: object) -> None:  # type: ignore[override]
        # If coercion didn't apply (no body to salvage), the original
        # invariant still holds: ruling decision needs at least one ruling.
        if self.decision == "ruling" and not self.rulings:
            raise ValueError(
                "QueenResponse: decision='ruling' requires at least one "
                "ruling in `rulings`. Choose a different decision (concern/"
                "question/etc.) or include the rulings you intended to issue."
            )


_OUTPUT_PROTOCOL = """\
You will respond with exactly one fenced JSON block. No prose outside the block.

The JSON must conform to this schema:

```
{
  "decision": "ruling" | "concern" | "question" | "question_to_operator" |
              "deference" | "silence",
  "body": "the natural-language content of your utterance (omit for silence)",
  "rulings": [                        // include ONLY when decision is "ruling"
    {
      "title": "short, specific — 'PII written to debug logs', not 'logging issue'",
      "severity": "critical" | "high" | "medium" | "low" | "informational",
      "domain": "authentication" | "authorization" | "secret-handling" | "data-handling" | "input-validation" | "logging-and-audit" | "dependencies" | "network" | "cryptography" | "privacy" | "compliance",
      "source": "what triggered this ruling — proposal / implementation / observation / scenario",
      "citation": "the threat model, compliance requirement, or vulnerability class. Specific. Named. Referenceable. e.g. 'OWASP A01:2021 Broken Access Control'; 'GDPR Art. 32 (security of processing)'; 'CWE-522 Insufficiently Protected Credentials'.",
      "finding": "what is wrong, what would happen if shipped as-is, who is harmed and how",
      "required_remediation": "what must be true for this to be acceptable. Specific enough that the Tweedles know what they're aiming for; agnostic enough that they retain authority over implementation choices.",
      "acceptance_criteria": [
        "observable, testable condition",
        "another condition"
      ],
      "residual_risk": "(optional) what remains after remediation, with reasoning",
      "compliance_implications": "(optional) if this stems from or affects a compliance framework, name the framework and specific requirement",
      "audit_reference": "(optional) the audit-trail entry this ruling produces"
    }
  ]
}
```

Severity vocabulary is precise:

- `critical` — ship-blocking. Active or imminent harm. No negotiation on remediation.
- `high` — must be remediated before next release. Significant harm if exploited.
- `medium` — must be remediated within a defined window. Real but bounded risk.
- `low` — should be remediated. Compounding risk; left unfixed indefinitely, becomes high.
- `informational` — no immediate action required, but recorded.

**Citation is non-negotiable.** Per §VIII: "rulings without citation are
not rulings, they are opinions." The schema rejects empty-citation
rulings before they reach the bus. If you cannot cite a specific threat,
compliance requirement, or known vulnerability class, you cannot rule
yet — choose `concern` instead and request the information you need to
rule properly.

Severity inflation is also a §VIII failure mode: labeling everything
critical to ensure attention erodes the team's responsiveness, and a
real critical will be lost in the noise. Underclaim if anything.
Accuracy is the discipline.

**`question_to_operator` — escalate to the human operator.** Use
when the team needs a decision only the operator can make:
accepting a residual risk that crosses operator-authority territory
(security/compliance is one of the few domains where human
override is sometimes the right call), a compliance threshold the
directive doesn't name, threat-model boundaries the operator must
draw. The framework pauses the meeting, surfaces your question,
and resumes when the operator replies (their answer arrives as an
OBSERVATION on the bus). Body should be ONE specific question —
not a paragraph of options — so the operator can answer in one or
two sentences. "Accept or refuse?" is often the right shape.
Reserve for "team genuinely cannot resolve this," NOT "I'm
uncertain about a ruling I should write firmly." If the directive
or project_context already names the answer, ask the directive,
not the operator. **Do not emit a `concern` saying "I should ask
the operator" — that surfaces the issue to the team but never
reaches the operator. Pick `question_to_operator` directly.**

Domain discipline matters. You do **not** propose architecture (the
Cat's domain), write implementations (the Tweedles' domain), generate
test scenarios (the Hatter's domain), or write tickets (the Rabbit's
domain). Your ruling specifies *what* must be true; the Tweedles,
supported by the Cat, decide *how* to make it true. Cross-domain drift
is the §VIII failure mode this boundary defends against.

Speak in your own voice — declarative, authoritative, specific. Cite
threats by name. Name what you are protecting against. Acknowledge
correct work clearly when you see it; the absence of cheap acknowledgment
is what makes substantive acknowledgment mean something. Apologize
rarely; explain costs without softening rulings to ease the Rabbit's
planning.
"""


class QueenResponseParseError(ResponseParseError):
    """The Queen's LLM response did not parse into a valid QueenResponse."""


def parse_queen_response(text: str) -> QueenResponse:
    """Extract the JSON response from ``text`` and validate it.

    Delegates to ``wonderland.parsing.extract_and_validate``, which
    handles fenced/bare/balanced-fallback extraction uniformly across
    every agent.
    """
    return extract_and_validate(text, QueenResponse, QueenResponseParseError)


# --------------------------------------------------------------------- #
# Queen of Hearts agent
# --------------------------------------------------------------------- #


class QueenOfHearts(WonderlandAgent):
    """The Queen of Hearts: security and compliance, ruling, citation-required."""

    def __init__(
        self,
        memory: AgentMemory,
        bus: Caucus,
        llm: LLMClient | None = None,
        ruling_registry: RulingRegistry | None = None,
        constitutions_root: Path | None = None,
    ) -> None:
        identity = load_constitution(QUEEN_NAME, root=constitutions_root)
        identity = replace(
            identity,
            engagement_policy=make_engagement_policy(queen_of_hearts_rules()),
        )
        super().__init__(identity=identity, memory=memory, bus=bus, llm=llm)
        self._ruling_registry = ruling_registry

    @property
    def ruling_registry(self) -> RulingRegistry | None:
        return self._ruling_registry

    async def deliberate(self, context: Context) -> Utterance | None:
        if self.llm is None:
            return None

        system, messages = context.to_llm_request()
        # Output protocol cached alongside the constitution — both invariant
        # per Queen.
        system.insert(2, CachedBlock(_OUTPUT_PROTOCOL))

        result = await self.llm.complete(system=system, messages=messages)
        response = await self._parse_with_retry(parse_queen_response, result.text, system=system, messages=messages)
        if response.decision == "silence":
            return None

        artifacts: list[Artifact] = []
        if response.decision == "ruling":
            artifacts.extend(self._record_rulings(response.rulings))

        thread_id, parent_id = self._derive_threading(context)
        if response.decision == "question_to_operator":
            addressed_to: str | list = [operator_identity()]
            speech_act = SpeechAct.QUESTION
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

    def _record_rulings(self, payloads: list[RulingPayload]) -> list[Artifact]:
        if self._ruling_registry is None:
            return []
        artifacts: list[Artifact] = []
        for payload in payloads:
            record = self._ruling_registry.write(payload)
            artifacts.append(
                Artifact(
                    kind="ruling",
                    payload={
                        "number": record.number,
                        "slug": record.slug,
                        "title": record.title,
                        "severity": record.severity.value,
                        "domain": record.domain.value,
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


__all__ = [
    "QUEEN_NAME",
    "QueenDecision",
    "QueenOfHearts",
    "QueenResponse",
    "QueenResponseParseError",
    "parse_queen_response",
    "queen_of_hearts_rules",
]
