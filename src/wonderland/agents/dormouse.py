"""Dormouse — SRE / Observability. Wakes when production tells the truth.

Per dormouse.md and WONDERLAND_SPEC §5. The Dormouse is mostly asleep,
because the system runs and the metrics are nominal. He wakes when
something is wrong, reports what the telemetry shows, and routes the
diagnosis to the agent whose domain is implicated. He **does not
interpret beyond evidence** — the symptom is his; the hypothesis is
not.

Runtime shape mirrors Cat / Rabbit / Alice / Hatter / Caterpillar /
Queen: load constitution, wire engagement rules from §III, override
deliberate() with a JSON output protocol, persist observations
through an ObservationRegistry. A single Dormouse turn typically
produces one observation; the schema permits more for batched
post-deploy or post-incident-confirmation reports.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field, field_validator

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
from wonderland.observation import ObservationPayload, ObservationRegistry
from wonderland.parsing import ResponseParseError, extract_and_validate
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


DORMOUSE_NAME = "dormouse"


# --------------------------------------------------------------------- #
# Engagement rules — dormouse.md §III as data
# --------------------------------------------------------------------- #


def dormouse_rules() -> EngagementRules:
    """The Dormouse's §III engagement policy as machine-checkable rules.

    His default state is sleep — engagement is narrow on purpose. The
    keyword heuristics catch the cases where production reality is
    being implicated; the LLM filter inside ``deliberate()`` chooses
    silence for the rest. §VIII names "Insomnia" as a failure mode the
    Dormouse actively guards against; the rules table reflects that.
    """
    production_words = body_contains_any(
        "production",
        "prod",
        "incident",
        "outage",
        "regression",
        "broken",
        "p0",
        "p1",
        "p2",
        "deploy",
        "deployment",
        "rollback",
        "metrics",
        "telemetry",
        "observability",
        "alert",
        "dashboard",
        "trace",
        "log",
        "logging",
        "latency",
        "throughput",
        "error rate",
    )
    is_tweedle = any_of(speaker_is("tweedledee"), speaker_is("tweedledum"))

    return EngagementRules.of(
        # ALWAYS — INVITE addressed to me always wakes me up (Block 2c)
        always(SpeechAct.INVITE, condition=addressed_to(DORMOUSE_NAME)),
        # ALWAYS — the production-touching surfaces from §III
        always(SpeechAct.IMPLEMENTATION, condition=is_tweedle),
        always(SpeechAct.RULING, condition=speaker_is("queen_of_hearts")),
        always(SpeechAct.CONCERN, condition=production_words),
        always(SpeechAct.QUESTION, condition=addressed_to(DORMOUSE_NAME)),
        # SELECTIVELY — the LLM filter inside deliberate() refines further
        selectively(SpeechAct.PROPOSAL, condition=speaker_is("cheshire_cat")),
        selectively(SpeechAct.TEST_SCENARIO, condition=speaker_is("mad_hatter")),
        selectively(SpeechAct.TICKET, condition=speaker_is("white_rabbit")),
        # RARELY — deference between others isn't his to act on
        rarely(SpeechAct.DEFERENCE),
        # ALMOST_NEVER — explicit guards. The Dormouse's default is sleep
        # (§VIII Insomnia), and engaging with same-typed utterances from
        # non-canonical speakers would just be domain-leak noise — exactly
        # the §VIII Boundary-leak failure mode.
        almost_never(SpeechAct.STORY),
        almost_never(SpeechAct.PROPOSAL),  # not from Cat
        almost_never(SpeechAct.IMPLEMENTATION),  # not from a Tweedle
        almost_never(SpeechAct.TEST_SCENARIO),  # not from Hatter
        almost_never(SpeechAct.RULING),  # not from Queen
        almost_never(SpeechAct.REVIEW),
        almost_never(SpeechAct.TICKET),  # not from Rabbit
        almost_never(SpeechAct.DIRECTIVE),
    )


# --------------------------------------------------------------------- #
# LLM output protocol
# --------------------------------------------------------------------- #


DormouseDecision = Literal["observation", "concern", "question", "deference", "silence"]


class DormouseResponse(BaseModel):
    """Structured JSON the Dormouse returns from deliberate().

    When ``decision == "observation"``, ``observations`` must contain at
    least one ``ObservationPayload``. The default is one — the Dormouse
    reports one symptom at a time — but the schema permits more so a
    batched post-deploy report (multiple services landed, each needing
    a sign-off observation) can be returned in one turn.
    """

    decision: DormouseDecision
    body: str = ""
    observations: list[ObservationPayload] = Field(default_factory=list)

    @field_validator("body", mode="before")
    @classmethod
    def _body_none_to_empty(cls, v: object) -> object:
        # Live Haiku 4.5 sometimes emits explicit nulls for omitted fields.
        # Coerce to default per the established pattern.
        return "" if v is None else v

    @field_validator("observations", mode="before")
    @classmethod
    def _observations_none_to_empty(cls, v: object) -> object:
        return [] if v is None else v

    def model_post_init(self, _context: object) -> None:  # type: ignore[override]
        if self.decision == "observation" and not self.observations:
            raise ValueError(
                "DormouseResponse: decision='observation' requires at least one "
                "observation in `observations`. Choose a different decision "
                "(concern/question/etc.) or include the observations you "
                "intended to issue."
            )


_OUTPUT_PROTOCOL = """\
You will respond with exactly one fenced JSON block. No prose outside the block.

The JSON must conform to this schema:

```
{
  "decision": "observation" | "concern" | "question" | "deference" | "silence",
  "body": "the natural-language content of your utterance (omit for silence)",
  "observations": [                  // include ONLY when decision is "observation"
    {
      "title": "short, neutral — what was seen, not what it means. 'Translation service error rate spike', not 'translation service broken'.",
      "type": "incident" | "anomaly" | "steady-state" | "post-deploy" | "post-incident-confirmation",
      "severity": "sev1" | "sev2" | "sev3" | "informational",
      "time_window_start": "UTC ISO timestamp, e.g. '2026-05-05T14:23:00Z'",
      "time_window_end": "UTC ISO timestamp, or empty string for ongoing",
      "symptom": "what the telemetry shows — precise, numeric, evidenced. 'Error rate rose from 0.04% to 2.7% between 14:23 and 14:31, affecting ~380 requests' — not 'things look bad'.",
      "affected_scope": "which services, endpoints, regions, user segments. Specific.",
      "evidence": [
        "https://grafana.internal/d/translation/overview?from=...&to=...",
        "trace ID 01HXYZABC...",
        "logs: app=translation, level=error, window 14:23-14:31, count=2104"
      ],
      "probable_domain": "(optional) backend | frontend | infrastructure | security | third-party — routing hint, not diagnosis",
      "routed_to": "(optional) the agent whose domain owns the diagnosis from here, e.g. 'tweedledum'"
    }
  ]
}
```

Severity vocabulary is precise:

- `sev1` — active user-visible impact, or active risk. Wake the on-call.
- `sev2` — degraded behavior without active user-visible impact. Investigate within the day.
- `sev3` — anomaly worth investigating but not requiring immediate response.
- `informational` — no action required, recorded for context.

**Evidence is non-negotiable.** Per §VIII: false alarms corrode trust;
your value is the trustworthiness of the report, which depends on
verifiability. The schema rejects empty-evidence observations. Cite the
dashboard URL, the query, the trace ID, the log range, the specific
metric values. If you cannot cite evidence yet, you cannot observe yet —
choose `concern` and request the telemetry you'd need.

**Do not interpret beyond evidence.** This is the §VIII failure mode
your domain discipline most directly defends against. The symptom is
yours; the hypothesis space — what's *causing* it, what to *do* about
it — belongs to the agents whose domains are implicated. Use
`probable_domain` and `routed_to` as routing hints, not diagnoses. Your
report names what was seen; their response names what it means.

Severity inflation (catastrophizing) and severity deflation (crying
mouse) are both §VIII failure modes. Use `informational` and `sev3`
freely when the evidence supports them; reserve `sev1` for actual
user-visible impact. Calibration is the discipline.

Speak briefly. Numbers and intervals. Attach evidence to every claim.
The team can plan against numbers; they cannot plan against vibes. Sleep
is a valid and often correct decision — when production is healthy and
no other agent's work is awaiting your sign-off, choose `silence`.
"""


class DormouseResponseParseError(ResponseParseError):
    """The Dormouse's LLM response did not parse into a valid DormouseResponse."""


def parse_dormouse_response(text: str) -> DormouseResponse:
    """Extract the JSON response from ``text`` and validate it.

    Delegates to ``wonderland.parsing.extract_and_validate``, which
    handles fenced/bare/balanced-fallback extraction uniformly across
    every agent.
    """
    return extract_and_validate(text, DormouseResponse, DormouseResponseParseError)


# --------------------------------------------------------------------- #
# Dormouse agent
# --------------------------------------------------------------------- #


class Dormouse(WonderlandAgent):
    """The Dormouse: SRE, mostly asleep, wakes when production tells the truth."""

    def __init__(
        self,
        memory: AgentMemory,
        bus: Caucus,
        llm: LLMClient | None = None,
        observation_registry: ObservationRegistry | None = None,
        constitutions_root: Path | None = None,
    ) -> None:
        identity = load_constitution(DORMOUSE_NAME, root=constitutions_root)
        identity = replace(
            identity,
            engagement_policy=make_engagement_policy(dormouse_rules()),
        )
        super().__init__(identity=identity, memory=memory, bus=bus, llm=llm)
        self._observation_registry = observation_registry

    @property
    def observation_registry(self) -> ObservationRegistry | None:
        return self._observation_registry

    async def deliberate(self, context: Context) -> Utterance | None:
        if self.llm is None:
            return None

        system, messages = context.to_llm_request()
        # Output protocol cached alongside the constitution — both invariant
        # per Dormouse.
        system.insert(2, CachedBlock(_OUTPUT_PROTOCOL))

        result = await self.llm.complete(system=system, messages=messages)
        response = await self._parse_with_retry(parse_dormouse_response, result.text, system=system, messages=messages)
        if response.decision == "silence":
            return None

        artifacts: list[Artifact] = []
        if response.decision == "observation":
            artifacts.extend(self._record_observations(response.observations))

        thread_id, parent_id = self._derive_threading(context)
        return Utterance(
            thread_id=thread_id,
            parent_id=parent_id,
            speaker=self.identity.as_agent_identity(),
            addressed_to="caucus",
            speech_act=SpeechAct(response.decision),
            content=UtteranceContent(body=response.body, artifacts=artifacts),
        )

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _record_observations(self, payloads: list[ObservationPayload]) -> list[Artifact]:
        if self._observation_registry is None:
            return []
        artifacts: list[Artifact] = []
        for payload in payloads:
            record = self._observation_registry.write(payload)
            artifacts.append(
                Artifact(
                    kind="observation",
                    payload={
                        "number": record.number,
                        "slug": record.slug,
                        "title": record.title,
                        "type": record.type.value,
                        "severity": record.severity.value,
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
    "DORMOUSE_NAME",
    "Dormouse",
    "DormouseDecision",
    "DormouseResponse",
    "DormouseResponseParseError",
    "dormouse_rules",
    "parse_dormouse_response",
]
