# Analysis 011 — Translation Chat MVP, Scoping Run for Tool Integration

**Date:** 2026-05-05
**Phase milestone:** P6.T36 (first full-cast showcase via the Runner; scoping run for the tool-integration question)
**Component:** `scripts/translation_chat_showcase.py` (T34 Runner + canonical translation chat directive)
**Run transcript:** [`data/011-translation-chat-scoping/run.log`](./data/011-translation-chat-scoping/run.log)
**Telemetry:** [`run-20260505T162710.json`](./data/011-translation-chat-scoping/run-20260505T162710.json)

> The point of this run was *not* to prove the showcase works; it
> was to surface evidence about what tool integration would
> actually need to do. The most useful finding is the opposite of
> what was expected: the Tweedles can't even reach the point
> where they'd need tools, because the upstream agents (Cat,
> Rabbit) don't ship the artifacts that would feed them. Tool
> integration would be a tool waiting for inputs that aren't
> being produced. The more urgent calibration is making the
> shipping agents actually ship.

---

## Setup

- Directive: the canonical `Build a translation-integrated chat
  application MVP...` from `full_cast_showcase.py` (kept identical
  for direct comparison to analysis 006's $8 polite-deadlock run)
- Budget cap: $3.00, 5-minute timeout, 30s quiescence
- Auto-respond on escalation: "Ship the simplest version that
  compiles for v1. Defer scope where the trade-off is reasonable;
  surface anything load-bearing as an open ticket for the next
  iteration."
- All 10 agents wired via `Runner.make_full_cast`

## Headline numbers

| metric | value | comparison to analysis 006 (no fixes) |
|---|---|---|
| total cost | $5.58 | down from ~$8 (-30%) |
| total LLM calls | 217 | up from 115 (+89%) |
| outcome | timeout @ 300s | similar (timed out at 90s in 006) |
| stories shipped | 8 | (006: ~6) |
| test scenarios shipped | 16 | (006: ~16) |
| ADRs shipped | **0** | (006: a few) |
| tickets shipped | **0** | (006: a few) |
| contract notes shipped | **0** | (n/a — didn't exist in 006) |
| implementations shipped | **0** | (006: 0; expected — no tooling) |
| rulings shipped | 3 | all process rulings, no security rulings |
| budget cap behavior | exceeded by 86% ($5.58 vs $3.00) | n/a — no cap in 006 |
| rate-limit-induced silences | 40 calls dropped | n/a |

## What worked

**The framework primer + constitutions held under load.** Every
substantive utterance was in-character — Hatter scenarios were
sharp, Alice stories were persona-grounded, Cat/Caterpillar/Queen
analyses were detailed. No agent broke into generic-helpful prose.
The chattiness fix from analysis 009 held: 13 questions and 68
concerns out of 102 utterances is high but not pathological, and
most concerns were doing real work (sharpening another agent's
position, flagging real gaps) rather than polite hedging.

**The synthetic-consensus guard stayed quiet** — the team had
genuine disagreement, not converging-on-helpful. That's the
guard doing its job by *not* firing.

**The polite-deadlock spiral didn't happen.** Analysis 006's
pattern (everyone hedging, refusing to commit) didn't return.
What happened instead is structurally different (see below) but
the T33/T35 fixes for the *prior* failure mode held.

**Per-agent cost is much more even.** No single agent ran away
with the budget — Hatter, Cat, Dormouse, Rabbit, Caterpillar all
spent in the $0.78–$0.96 range. Compare to analysis 006 where
Cat was 53 calls / $2.70 of uncached input alone.

**Cache reads dominated.** 2.04M cache-read tokens at $0.10/MTok
= $0.20 — vs raw input at $4.81. The framework primer's cache-
padding role from T32 is paying off; this run would have cost
$15+ without caching.

## What didn't work — the new failure pattern

### The vertical pipeline blocked

Analysis 006/007's failure was *horizontal*: agents within a
domain hedging at each other. This run's failure is *vertical*:
the upstream agents (Alice, Hatter) shipped well; the midstream
agents (Cat, Rabbit, Queen) refused to commit; the downstream
agents (Tweedles) had nothing to work against. Sequence:

1. **t=33s** — Queen issues ruling: "Architectural decision required
   before work decomposition" (severity=critical). This is a
   *process* ruling, not a security/compliance ruling.
2. **t=43s** — Cat agrees the ruling is correct but doesn't write
   the ADR.
3. **t=118s** — Queen issues two more process rulings reinforcing
   the sequencing. Still no ADR exists.
4. **t=86–278s** — every agent in the team writes concerns about
   the blocked sequence, the Cat keeps reframing the question, the
   Rabbit waits for the ADR, the Tweedles wait for tickets that
   wait for the ADR.
5. **t=152s** — budget exceeded fires; auto-respond goes back to
   the team as a Dodo directive. Team incorporates the directive
   into the next round of concerns but doesn't unblock.
6. **t=277s** — STUCK transition; Dodo nudges. Same pattern continues
   for the remaining 23s.

The Cat's §VIII failure mode is *false certainty / refusing to
commit / speaking to be present*. We watched it happen in real
time. Across 30 LLM calls and $0.94, the Cat shipped one `proposal`
speech act — and even that was prose, not an ADR artifact. The
Rabbit's similar.

### Speech-act vocabulary mismatch (real bug)

Five different agents tried to use Dodo-only speech acts during the
run:

- `composition` attempted by caterpillar (3x), white_rabbit, mad_hatter, dormouse
- `nudge` attempted by caterpillar
- `acknowledgment` attempted by tweedledee

Each attempt raised a Pydantic ValidationError and was caught as
silence. Cause: the framework primer's §II lists *all* speech acts
without saying which subset each agent is allowed to issue. Each
agent's `*Response` schema has its own per-agent Literal — but
the LLM doesn't see those schemas; it sees the primer's union.

Fix shape: the primer needs to call out that procedural acts are
Dodo-only, OR each agent's output protocol needs to enumerate the
permitted acts more emphatically, OR (cleanest) we add a per-agent
allowed-acts section to the primer that's parameterized at agent
construction.

### Budget cap is structurally soft and gets softer under concurrency

The cap fired correctly at $3.06 (t=152s, only $0.06 over). But by
the time the run terminated at t=300s, the actual spend was $5.58
— $2.50 *more* spent after the cap. Why:

- Each agent's `WonderlandAgent.run` loop has an in-flight LLM
  call when the budget check fires. Those calls return and bill
  before the agent loop sees the abort signal.
- The auto-respond (a new directive injected via `respond_to_escalation`)
  *re-triggers* every agent's engagement rules — so all 9 agents
  fire deliberate() again on the human resolution.
- The 1s polling interval means up to 9 calls in flight per
  poll cycle.

The roadmap item `aa65d2d7` (Hard budget cap: refuse new agent turns
once exceeded) is now critical, not P2. With the soft cap, a run
intended for $3 can blow past $5 silently. For showcases this means
the budget number on the CLI is more aspirational than enforced.

### Rate limits compress signal

Anthropic's 1M-tokens-per-minute org rate limit was hit 40 times
across the run (Queen 9, Dormouse 7, Caterpillar 7, Hatter 5,
Cat 5, Rabbit 3, Tweedledum 3, Alice 1). Each hit drops to
silence. Hard to disentangle "agent chose silence" from "agent
was rate-limited into silence" in the transcript. A backoff +
retry in `LLMClient` would mitigate; there's no roadmap item for
this yet.

### Queen drifted from security to process-policing

Queen shipped 3 rulings, all of them about *team process*
("architectural decision must precede X", "decision-ownership must
be visible before architecture"). Zero rulings about the actual
security/compliance surface in the directive (GDPR data retention,
the prompt-injection scenarios Hatter surfaced, the deletion-vs-
chat-history conflict, etc.). Queen's §VIII includes
"working alone" and "vendor capture" — but a new failure mode is
visible here: **process-policing as substitute for substantive
ruling** when the substantive answer requires architectural
context the Cat hasn't shipped.

## What this means for the tool-integration question

The user's framing was: run T36 as a scoping showcase, see what
specific gaps surface, then decide on tool scope informed by
evidence rather than speculation.

**The evidence says: don't build tool integration yet.** The
Tweedles never reached the point where they'd need to write code.
They had no tickets, no contracts, no implementations to compose
against. Tooling would be downstream of work that isn't being
produced.

What's blocking the team from getting to the point where tools
would matter:

1. The Cat's refusal to ship ADRs (the load-bearing failure)
2. The Rabbit's refusal to ticket without the Cat's ADR
3. The schema-vocabulary mismatch silencing real moves (5
   different agents in a single run)
4. The budget cap not actually capping
5. The rate limit drowning agents at peak concurrency

If we built tool integration now, we'd have agents holding tools
they can't pick up.

## Recommended sequencing (revising the gameplan)

Three new calibration items should land before T37/T38:

1. **Per-agent allowed speech acts in the primer** (small, surgical).
   Add a parameterized section to `FRAMEWORK_PRIMER` that names
   the speech acts each agent can issue. Eliminates the parse-error-
   to-silence path that ate ~6 substantive moves in this run.

2. **Agent-level "ship the artifact" calibration** (larger, requires
   thought). The Cat / Rabbit / Tweedles all have schemas that
   reject empty artifacts. But they happily choose `concern` /
   `question` instead, especially when the team is in a sequencing
   debate. Possibly: add a constitutional clause that says "after
   N turns of clarification on a topic in your domain, the next
   move is to commit even with confidence intervals." The Cat's
   §VIII calls this out conceptually but the prompt doesn't operationalize
   it.

3. **Hard budget cap** (already on roadmap as `aa65d2d7`, P2).
   Re-prioritize to P1 — the soft cap is now demonstrably unsafe
   for showcases at full-cast scale.

Tool integration moves to P7 prep. Once the upstream agents are
calibrated to ship, the showcases will produce contracts and
tickets, and *then* tool integration is the clear next step.

## On the "Opus could one-shot this" question

Worth naming directly because this run is exactly the case where
the question lands hardest. Opus could absolutely produce 8 user
stories, 16 test scenarios, 3 process rulings, 2 observations,
and a list of architectural questions to answer — probably for
~$0.50–$1 in one or two shots. We spent $5.58 to produce the same
artifact set, plus the team got *stuck* in a way Opus wouldn't.
On this run, Opus wins on artifact-quality-per-dollar.

What this run still has that Opus doesn't: real visible
disagreement (Tweedledee vs Tweedledum questioning each other's
contract assumptions inline; Caterpillar correcting Hatter's
severity calibration; Queen flagging GDPR gaps in Alice's stories
specifically), debuggable decision trails (you can see *why* the
team got stuck — it's a Cat-shipping-failure, not a generic
"team got confused"), and per-agent failure modes named and
visible. That's still substantive but it's not the framework's
pitch — the pitch is *good output*, and on this run the good
output didn't arrive.

The good news: the Cat-shipping-failure is a calibration target,
not a structural one. Constitutions are text; they can be tuned.
The next showcase, after the calibration items above, is the
honest re-test.

## Open follow-ups

1. **Rerun T36 after calibration #1 + #2 + #3.** The same directive
   should produce ≥1 ADR, ≥3 tickets, and at least 1 Tweedle
   contract note. Cost target: $2.00 with hard cap.

2. **Audit Queen's process-policing pattern.** This run produced 0
   security rulings on a directive with explicit GDPR scope and
   prompt-injection scenarios in the test set. The Queen has the
   information; she's choosing process-meta over substance.
   Possible new §VIII clause.

3. **Add LLMClient backoff on RateLimitError.** 40 dropped calls
   in 5 minutes is signal-shaping noise.

4. **Consider scoping the next showcase smaller** so the cascade
   doesn't compound. Rather than "build a chat MVP", maybe
   "produce an ADR for translation message envelope" — narrower
   directive, downstream artifacts more visible against the
   smaller scope.

## Next breath

T36 closes as a scoping run, not a showcase. The Runner script
ships, the analysis ships, three calibration items move onto the
gameplan ahead of T37 (Showcase 3: security recovery). Tool
integration deferred to P7 prep with a clean rationale: there's no
point integrating tools when the team can't reach the artifacts
that would feed them.
