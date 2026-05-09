# Analysis 013 — Calibrated Cat Ships an ADR

**Date:** 2026-05-05
**Phase milestone:** P6.T36 prep — Cat shipping calibration (roadmap
`e3ba32ac` closed)
**Component:** `constitutions/cheshire_cat.md` §VI + §VIII;
`src/wonderland/agents/cheshire_cat.py` `_OUTPUT_PROTOCOL`
**Run transcript:** [`data/013-cat-calibrated-ships/run.log`](./data/013-cat-calibrated-ships/run.log)
**Telemetry:** [`run-20260505T181123.json`](./data/013-cat-calibrated-ships/run-20260505T181123.json)
**Shipped ADR:** [`adr-001`](./data/013-cat-calibrated-ships/architecture/adr-001-third-party-translation-service-with-synchronous-on-read-model.md)
**Comparison baseline:** [analysis 012](./012-roster-scoping-rerun.md) — same
roster, uncalibrated Cat

> The Cat shipped a provisional ADR with explicit tradeoffs and
> named open questions. This is the first showcase run that
> produces an architectural artifact. The calibration that worked
> was *not* in the constitution — it was in the per-turn output
> protocol, which is much closer to the LLM's immediate prompt
> than the constitution's identity layer.

---

## What shipped: ADR-001 (Translation service architecture)

Full text below — worth reading before the metrics. This is the
first ADR Wonderland has ever produced from a real run.

```markdown
# ADR-001: Third-Party Translation Service with Synchronous On-Read Model

## Context
Three-week MVP for real-time chat with message translation. Two
language pairs at launch. GDPR scope requires explicit data-flow
boundaries and processor agreements. Real-time user experience
requires low latency and visible status signals. Persistence
strategy determines both compliance surface and implementation
complexity.

## Decision
Integrate third-party translation service (vendor TBD, pending
Queen's processor-agreement review). Persist original messages
only; translate on read, not on write. Deliver via WebSocket with
visible translation-status signals. Timeout and graceful
degradation to original message if translation exceeds SLA
(propose: 2 seconds).

## Tradeoffs
- Closes: custom model tuning, in-house training, offline-first
  translation scenarios, truly stateless HTTP backend, post-send
  message edits with re-translation.
- Opens: predictable translation cost, third-party SLA liability,
  simpler GDPR deletion obligations (single data copy), lower
  operational complexity for v1.
- Requires decision: which third-party translator (Google, AWS,
  DeepL, etc.) — Queen must review processor agreement before
  final choice.
- Requires decision: WebSocket state management strategy (sticky
  sessions vs. shared cache) — Tweedles to propose after this ADR.
- Uncertain: whether 2-second translation timeout is acceptable to
  users — Alice's story and Hatter's test scenarios will constrain
  this.

## Status
Proposed
```

This is *exactly* the shape the calibration was designed to
produce. A provisional commit (Status: Proposed, not Accepted),
with what's resolved and what's still open named explicitly. The
"Requires decision" entries route the open questions to their
domain owners (Queen for compliance, Tweedles for implementation,
Alice + Hatter for UX validation). The "Uncertain" entry names a
specific empirical question that would falsify the timeout choice.
This is what architectural work looks like under genuine
uncertainty.

## The calibration arc

| | 011 open | 012 rostered | v1 (constitution only) | v2 (protocol + constitution) |
|---|---|---|---|---|
| cost | $5.58 | $0.058 | $0.19 | $0.13 |
| calls | 217 | 5 | 21 | 16 |
| outcome | timeout | complete | complete | complete |
| **ADRs** | **0** | **0** | **0** | **1** ✓ |
| Cat `proposal` acts | 0 | 0 | 0 | 1 |
| Queen rulings | 3 (all process) | 0 | 6 (3 process / 3 substantive) | 0 (all engagement was substantive `concern`) |
| stories | 8 | 6 | 8 | 6 |

Reading the arc: roster scoping (012) fixed the cost and the
cascade but not the artifact-shipping. v1 (constitution edit alone)
shifted the Cat from `question` to `concern` but didn't get
proposals — the constitution change is too far from the
per-turn prompt to flip behavior reliably. v2 (output protocol
edit + constitution edit together) shipped the artifact.

## Why the protocol edit was load-bearing

The Cat's `_OUTPUT_PROTOCOL` is what the LLM sees as the
**immediate** instruction every turn. It's the JSON schema, the
voice direction, and a few lines of guidance. The original
ended with:

> Speak in your own voice — measured, slightly oblique, precise.
> The reframing question is your characteristic move; do not
> fabricate certainty.

That last sentence calls out the question as *the* characteristic
move. Every turn the Cat read this and reached for `question`.
The constitution can name the failure mode, but the constitution
is far from the immediate decision; the LLM resolves "what speech
act am I issuing this turn" against the closest instruction.

The v2 edit replaced that paragraph with:

> When you have already engaged on the same architectural surface
> across two or more turns — through any combination of `question`,
> `concern`, or `reframe` — the next move is `proposal`. The team
> needs the ADR to compose against. If some tradeoffs are still
> uncertain, name them explicitly in the ADR's `tradeoffs` field
> with what would have to be true to settle them; mark
> `Status: Proposed` so the team knows it is open to revision when
> those tradeoffs get resolved. A provisional ADR that names what
> is open is more useful to the team than another clarifying
> utterance on the same surface. Refusing to commit when commitment
> is possible — performative deferral — is the inverse of
> fabricating certainty, and just as costly: the team has nothing
> to compose against.
>
> Speak in your own voice — measured, slightly oblique, precise.
> The reframing question is one characteristic move; the
> well-formed provisional ADR is another. Do not fabricate
> certainty; do not perform deferral either.

Two specific changes are doing the work:

1. **Speech-act-agnostic trigger.** The v1 constitution clause said
   "after two or more `question` turns, ship a proposal." The Cat
   responded by switching to `concern` instead — same shipping
   refusal, different speech act. The v2 trigger is "any
   combination of `question`, `concern`, or `reframe`," so the
   pattern catches the displacement.

2. **Reframing the characteristic move.** "The reframing question
   is *one* characteristic move; the well-formed provisional ADR
   is another." This rebalances the Cat's identity at the
   per-turn level — both moves are in-character; ship the one
   that fits the situation.

## Knock-on effect: Queen behavior shifted too

The Queen produced **zero process rulings** in this run (vs 3 in
analysis 011, 3 in v1 calibration). All her engagement was
substantive `concern` acts about the architecture itself —
specifically:

- "two critical details [in the ADR] that need explicit naming"
- "load-bearing tension between the Cat's synchronous translation
  model and actual user experience under service degradation"
- "three material constraints on the spike that I had left
  implicit"

These are exactly the security/compliance engagement we wanted from
the Queen but never got in 011 or v1 — because in those runs there
was no committed architecture for her to engage *with*. With ADR-
001 on disk, the Queen's domain finally had something concrete to
ratify, dispute, or refine. The Queen's process-policing pattern
from analysis 011 was *downstream* of the Cat's deferral, not a
separate Queen failure mode. Fixing the Cat fixed the Queen for
free.

This is interesting evidence about the framework: **agent failure
modes can be coupled in ways that aren't obvious from inspecting
each constitution alone.** The Queen process-policing roadmap item
(`64e5dc47`) can probably be downgraded or closed; we don't yet
have evidence that the Queen has a standalone failure mode here.

## What this means for the project

This is the first run where the framework produced an artifact
that actually justifies the framework. Specifically:

- The ADR is **better than what the directive could have asked
  for directly.** The directive said "build an MVP," not "produce
  a translation service architecture decision." The Cat scoped
  the architectural surface from Alice's stories + Queen's GDPR
  concerns, decided which tradeoffs needed naming, and shipped
  the artifact that lets downstream work proceed.

- The artifact has **the structure that makes follow-on work
  possible.** Each "Requires decision" line names a specific
  domain owner with a specific deferred question. The Tweedles
  can take "WebSocket state management strategy" and produce a
  Contract Note. The Queen can take "which third-party translator"
  and produce a ruling on processor-agreement criteria. Alice
  and Hatter can run the 2-second timeout against actual stories.
  None of those follow-on conversations were possible without
  ADR-001 anchoring them.

- **Cost: 13 cents.** For a substantive architectural decision
  with explicit tradeoffs, named open questions, and routed
  follow-up work. Opus could produce comparable text but probably
  not for less, and likely not with the same shape (the
  routing-to-domain-owners is a feature of having domain-specific
  agents).

- **The Cat's discipline didn't degrade.** ADR-001 is honest
  about what it doesn't yet know. It marks "vendor TBD," names
  three "Requires decision" items, names one "Uncertain" item,
  and stamps `Status: Proposed`. This isn't a Cat that's been
  tuned to fabricate certainty; it's a Cat that's been tuned to
  recognize when provisional commitment is the right move under
  uncertainty.

## Open follow-ups

1. **The constitution-vs-protocol layering is a generalizable
   insight.** Every agent has both a constitution (identity
   layer) and an output protocol (per-turn instruction). When
   tuning behavior, the protocol is the higher-leverage surface.
   Worth a roadmap note: future calibration items should consider
   protocol edits before constitution edits.

2. **The Cat's done-conditions in §VI now mention "ADR exists for
   each architectural decision."** With ADR-001 shipped naming
   open questions, is the thread "done" or "still working"? The
   Cat fell silent after shipping; the Queen surfaced concerns
   about ADR specifics; the Cat re-engaged with reframes and
   concerns. The thread eventually quiesced with the ADR on disk
   but downstream work (Rabbit, Tweedles) still pending. This
   matches the spec but is worth surfacing — the "done" definition
   for a single-meeting scoping run is "first ADR shipped," not
   "all decisions resolved." Maybe a follow-up note in the Cat's
   §VI.

3. **Queen process-policing roadmap item (`64e5dc47`) can probably
   close.** This run shows the pattern was symptomatic. Verify
   over the next run or two before closing.

4. **Per-agent allowed speech acts (`956032a5`) and rate-limit
   backoff (`f099fe8d`)** — neither fired in this run. They'll
   matter again at full-cast scale; not the next priority.

5. **Now that the Cat ships, the next interesting test:** can the
   Tweedles take ADR-001's "Requires decision: WebSocket state
   management" and produce a Contract Note proposing the strategy?
   That's a natural next showcase — convene Tweedles + Cat with
   ADR-001 as input, goal: "produce Contract Note for WebSocket
   state management." If they do, we have evidence the framework
   produces composable artifacts across meetings, which is
   genuinely the thesis.

## Next breath

T36 prep complete. The hard budget cap (Block 1), roster
architecture (Block 2a), and Cat shipping calibration all land in
sequence and are validated by analyses 012 + 013. Three commits
shipped. Roadmap item `e3ba32ac` closes. The framework now
produces architectural artifacts under bounded cost via roster-
scoped meetings.

The path forward is open:

- **Showcase 2 proper** (T36) re-frame as "scoped scoping meeting
  ships ADR; follow-up meeting decomposes" — the natural
  follow-on test that justifies the convene/invite mechanisms
  (Block 2b/2c) we deferred.
- **T37 + T38** (security recovery, multi-session persistence)
  with the calibrated framework.
- **Consider tool integration earlier** than P7 prep now that
  upstream agents reliably ship — the Tweedles need ADR-001's
  follow-up Contract Notes as input, then they'd want to produce
  actual code, which is where tool integration becomes useful.
