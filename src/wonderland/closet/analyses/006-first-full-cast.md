# Analysis 006 — First Full-Cast Race

**Date:** 2026-05-05
**Phase milestone:** P5 closeout (full cast on the bus, end-to-end)
**Cast online:** 10 of 10
**Model:** `claude-haiku-4-5-20251001`
**Script:** [`scripts/full_cast_showcase.py`](../scripts/full_cast_showcase.py)

> The first time all ten agents share a bus and have to compose into
> a working team rather than six independent statements. The same
> translation-chat scenario the voices sweep used in isolation. The
> result is informative — and not in the way I expected.

---

## The race, summarized

**Outcome:** **STUCK at 600s. Did not reach COMPLETE.**

**Activity:** 80 utterances over 600 seconds. The first ~50 seconds
produced rich substantive moves — by t=44.47s the team had landed:

- White Rabbit: 3 spike tickets (`spike: translation service`,
  `spike: GDPR data scope`, `spike: session/auth model`)
- Queen of Hearts: 3 rulings (data-residency `critical`, retention
  `high`, auth-attack-surface `critical`)
- Cheshire Cat: 1 proposal naming three load-bearing decisions
  (substrate, storage, real-time contract)
- Alice: 9 stories across the v1 surface
- Caterpillar: 1 deference acknowledging the Rabbit's routing was correct
- Tweedles: 2 concerns surfacing the frontend-backend coupling

That's a team finding the shape of the problem in well under a
minute. **Then the next 550 seconds were the cascade.**

**Speech-act distribution across the full run:**

| act | count | who issued |
|---|---:|---|
| concern | 63 | everyone except Alice/Dodo/Hatter |
| deference | 6 | Caterpillar (3) / Tweedledee (3) |
| proposal | 3 | Cheshire Cat |
| ticket | 1 | White Rabbit |
| ruling | 1 (× 3 artifacts) | Queen of Hearts |
| story | 1 (× 9 artifacts) | Alice |
| question | 1 | White Rabbit |
| reframe | 1 | Cheshire Cat |
| directive | 1 | Dodo |

**80% of the dance was concerns.** The team raised concerns about
each other's concerns, perpetually waiting for the upstream
decision that would make their next concrete move possible.

---

## What the team actually said in the productive 50 seconds

The first ~50 seconds is the team at its best. Three excerpts:

**White Rabbit at t=14.59s** (publishing three spike tickets, not
implementation tickets — a refusal to commit before the constraint
set is locked):

> Three weeks is tight for GDPR + translation + real-time. […] Before
> I ticket, I need the team's input on three hard constraints: (1)
> Which translation service do we use — managed API […] or self-
> hosted? (2) Are we storing message history, or stateless pass-
> through? (3) Session/auth scope — single-tenant, multi-tenant, or
> federation-ready? […] Dependency preview: auth ≤ message schema ≤
> translation integration ≤ end-to-end test. No slack.

**Queen of Hearts at t=16.86s** (concern, not ruling — `caprice`
guard live again, same shape as analysis 005):

> I am flagging them as concerns rather than rulings because I need
> the team's intent on a few design points before I can rule
> properly. […] The MVP cannot claim GDPR compliance through
> documentation alone; GDPR compliance must be *architected in* or
> the compliance posture will be remedial, expensive, and late.

**Cheshire Cat at t=22.74s** (the architectural fork named):

> Before scope decomposition, the team needs to settle three
> architectural decisions—they are genuinely ship-blocking and they
> are load-bearing for everything downstream. […] First: where does
> translation happen, and when? […] Second: what is the source of
> truth for a conversation? […] Third: what is your real-time
> contract?

These are the moves the thesis predicts. Each in the speaker's voice;
each the right thing to say from that domain. **The team found the
problem's shape in 25 seconds.** That's the success.

---

## The cascade, named

By t=60s, the substantive moves had landed. By t=80s, the team had
entered a recursive deferral pattern:

- Rabbit: "I'm holding tickets pending the Queen's rulings on her
  four points."
- Queen: "I need the Cat's architectural intent before I can rule."
- Cat: "These are not my decisions. I will help the team think
  through tradeoffs once the choices are named."
- Tweedles: "I need the Cat to land architecture before I can
  produce contracts."
- Caterpillar: "The work is not yet shaped enough for review."

**Each agent's individual position was constitutionally correct.**
Cat §VIII forbids fabricating certainty. Queen §VIII forbids
ruling without citation. Rabbit §VIII forbids tickets against
uncertain constraints. Tweedles §II forbids implementing against
implicit contracts. Each agent did exactly what their constitution
demanded. **Together, they produced an analysis-paralysis deadlock
the framework has no mechanism to break.**

The thread state log is the clearest evidence:

```
[t=270.27s] thread_monitor — running → stuck (2 open expectations)
[t=364.36s] thread_monitor — running → stuck (4 open expectations)
```

**STUCK fired twice.** Each time a new round of concerns then
revived the thread to RUNNING — but the new concerns themselves
opened more expectations than they closed, so the open-expectation
count only grew. By t=600s there were many open questions and zero
new substantive artifacts since t=44.47s.

---

## Why the cascade didn't break

This is the most important finding from the run. The framework has
several mechanisms designed to handle stuck threads, and **none of
them fired**:

1. **Dodo nudge → escalation ladder.** Per `dodo.md §VI`, the Dodo
   should nudge stuck threads and escalate to deadlock if the nudge
   doesn't resolve. **The Dodo made zero LLM calls in this run.** His
   §III engagement rules require specific conflict-words in concerns
   (`conflict`, `disagree`, `deadlock`, `stuck`, `blocked`, etc.) and
   the team's concerns didn't use that vocabulary — they used
   constitutionally-correct hedging language (*"I am holding
   tickets pending…"*, *"I am not yet at the point of…"*, *"Once
   the constraints are locked…"*). The Dodo never noticed the
   deadlock because the agents were too polite to name it.

2. **ThreadMonitor's STUCK transition.** Fired correctly twice (at
   270s and 364s). But STUCK is just an event — there's no consumer
   wired to do anything with it beyond logging. The Dodo's
   `acknowledge` for QUIESCENT is wired in the showcase script;
   STUCK is not.

3. **Conflict resolution + composition (T19).** Designed for
   *competing proposals*, not for *cascading concerns*. The team
   didn't have proposals in conflict; it had concerns waiting on
   answers that never came. The composition mechanism's input
   shape doesn't match this failure mode.

4. **Synthetic-consensus guard (T31).** Correctly **did not fire** —
   the agents were genuinely disagreeing (about who should decide
   what next), not converging. So this is a positive negative:
   the guard knew not to alarm. Score one for the guard's
   calibration.

So the cascade is a real emergent failure mode the framework's
*current* mechanisms don't address. It's the multi-agent equivalent
of analysis-paralysis among well-intentioned individuals each
following their own correct rules.

---

## What it tells us about the thesis

n=1 full-cast run; one trigger; one outcome. Modest evidence — but
the thesis predicts specific things and the run lets us check them.

### Productive substance landed fast

In <50 seconds the team identified the load-bearing decisions, named
them precisely, and proposed a sequence (Queen rules → Cat proposes
→ Alice stories → Rabbit decomposes). Compare this to "five system
prompts in a trench coat" — most generic-multi-agent setups would
either collide on the same surface or produce mush. **What the
voices sweep showed in isolation, the full cast produced in
collaboration, on the first try.** That's the thesis paying off.

### The §VIII guards held *too well*

This is the surprising one. Each agent's failure-mode awareness is
load-bearing per the README's "failure-modes-as-identity" claim,
and per the run, every agent guarded their failure mode
correctly:

- Cat: refused to fabricate architecture
- Queen: refused to rule without citation
- Rabbit: refused to ticket against uncertain constraints
- Caterpillar: refused to review unshaped work
- Tweedles: refused to implement against implicit contract

**The aggregate of correct individual restraint produced collective
deadlock.** The constitution's negative-space ("here's what you
should not do") is doing the work it was designed to do — but
nothing in the framework adjudicates *when* the team has waited
long enough that the next-best move is "make a provisional call
and adjust." That's a real gap.

This is *more* important than I expected as a P5-closing finding.
The constitutions encode "do not do X" effectively; the framework
has no equivalent mechanism for "the team is waiting too long;
someone has to commit." The ConflictResolution + Composition
machinery from T19/T20 handles the specific shape of "two agents
both insisting on incompatible positions"; it doesn't handle "ten
agents all deferring to a decision none of them is willing to
make."

### Caching engaged for most of the cast

A pleasant surprise. Per the analysis 001 cache investigation,
Haiku 4.5 needs ~7000 tokens of cached prefix before reads hit.
With 10 agents on a long thread, the per-call context grew enough
that several agents organically crossed the threshold:

| agent | cache_w | cache_r | calls |
|---|---:|---:|---:|
| white_rabbit | 5,255 | 115,610 | 23 |
| caterpillar | 6,501 | 182,028 | 29 |
| queen_of_hearts | 7,870 | 15,740 | 3 |
| dormouse | 6,904 | 6,904 | 2 |
| tweedledee | 8,459 | 143,803 | 18 |
| tweedledum | 8,864 | 106,368 | 13 |
| mad_hatter | 5,296 | 0 | 1 |

The Tweedles' double-cached prefix (own constitution + pair
protocol) put them in the cache-hit zone reliably — analysis 005's
prediction ("if any character organically crosses Haiku's caching
threshold under normal multi-turn use, it'll be them") confirmed.
The Rabbit + Caterpillar + Tweedles cleared 100k+ cache reads each
across the run, which substantially offsets the per-call cost
inflation from longer thread context.

**One conspicuous miss:** the Cat made 53 calls, totaling **2.59M
input tokens** with **zero cache hits**. His per-call context
averages ~49k tokens — much larger than anyone else's — and
appears to grow with thread history rather than caching a stable
prefix. Whatever's varying in the Cat's prompt prefix on each
call, it's varying *before* the cached portion would normally end.
Worth tracing in P6 to understand what's different about Cat's
context composition.

### Synthetic-consensus guard correctly stayed silent

Per the §11 anti-pattern: agents converging because the LLM's
helpful-disposition is a strong attractor. This run produced the
*opposite* — agents diverging into a recursive deferral. The guard
correctly emitted no alerts. **This is the negative-evidence shape
the spec needs to show the guard isn't paranoid.** Real
disagreement looks different from synthetic agreement, and the
guard knows the difference (so far, on n=1).

---

## Numbers worth keeping

| metric | value |
|---|---:|
| total wall time | 600.00s |
| total utterances | 80 |
| substantive utterances | 4 + 3 ADRs + 3 rulings + 9 stories + 3 spike tickets = 22 artifacts |
| concerns / total | 79% |
| total input tokens (uncached) | 4,577,266 |
| total cache reads | ~723,000 |
| total output tokens | 96,236 |
| total LLM calls | 144 (Cat 53, Caterpillar 29, Rabbit 23, Dee 18, Dum 13, Queen 3, Alice 2, Dormouse 2, Hatter 1, Dodo 0) |
| Dodo LLM calls | 0 |
| ThreadState transitions | 2 × `running → stuck` |
| consensus alerts | 0 |
| **actual cost (Haiku 4.5)** | **~$5.10** ($1/MTok in × 4.58M + $5/MTok out × 96k + cache reads at $0.10/MTok). Cat alone accounted for ~$2.70 of this — 53 calls × ~49k uncached input each, no cache hits at all. |

*Cost note (added after analysis publication):* my original
estimate here was "~$0.50–1.00" using stale Haiku 3 prices. Actual
Haiku 4.5 pricing is **$1.00/MTok input + $5.00/MTok output** —
4× higher on both than I'd been assuming. The corrected $5.10
figure makes the cost-anomaly framing in this analysis even
sharper: Cat's 2.59M uncached input tokens isn't a $2.59 oversight,
it's a $2.70 oversight, and it's >50% of the run's total cost.
The polite-deadlock pattern compounds this — 79% of the dance was
concerns that each cost real money to produce. **P6's T32 (Cat
cache fix) and T33 (Dodo nudge ladder) are not optional cost
optimizations; they're table stakes for affordable showcases.**

---

## Caveats

- **n=1, single trigger, single cast configuration.** Don't
  generalize from one cascade. P6 showcases against multiple
  scenarios will tell us whether this is "translation-chat is
  unusually deferral-prone" or "any directive vague-enough-to-
  scope produces the cascade."
- **The cascade is shaped by the directive.** A more
  *constrained* directive (like Showcase 1's `/health` endpoint
  with explicit acceptance criteria) settles cleanly. Shape of
  trigger affects shape of failure.
- **Hatter only spoke once.** Surprising — the directive has
  obvious adversarial surfaces (translation provider failures,
  GDPR edge cases). His one move output 4096 tokens (max), so he
  was actively engaged. He may have produced multiple scenarios
  but the single LLM call hit the output cap. Worth investigating
  whether the Hatter's protocol needs a mechanism to chain calls
  for very long scenario lists.
- **Alice spoke once and produced 9 stories** — comparable to her
  solo demo (analysis 003 produced 7 stories on a similar
  directive). The full-cast context didn't change her output
  shape much, suggesting Alice's voice is robust to surrounding
  noise. Worth confirming on more runs.
- **Cat's cache-miss is a real anomaly.** 53 calls × 49k input ≈
  2.59M input tokens, all uncached. If we can fix this
  (whatever's varying in his prompt prefix that other agents
  don't have), Cat's cost drops by ~10×. Top P6 follow-up.
- **Teardown crashed cosmetically.** Alice's mid-deliberation LLM
  call was cancelled at stop(), the partial response had no JSON
  block, and the parse error propagated to the script. **Fixed
  in the same commit as this analysis** — `WonderlandAgent.speak`
  now catches `deliberate()` exceptions and treats them as
  silence with a stderr log, so a malformed transient response
  costs one turn instead of the agent's entire participation.

---

## What we'd expect to see strengthen the thesis

The deadlock pattern needs at least one mechanism. Three
candidates worth considering for P6:

1. **Wire the Dodo's nudge to STUCK transitions, not just to
   conflict-keyword concerns.** The current §III rules require
   the agents to *say* they're stuck for the Dodo to engage. The
   ThreadMonitor already detects stuckness mechanically; the Dodo
   should consume those events directly. (T18 already exposes
   `transitions()` as the consumer iterator; the showcase
   wires QUIESCENT → acknowledge but ignores STUCK.)
2. **Add a "make a provisional call" decision-mode to the LLM
   protocols.** Each agent currently has a binary "produce my
   artifact OR raise a concern" decision; a third option ("commit
   provisionally with explicit revisability" — `tentative`?)
   would let the team make progress under uncertainty without
   violating §VIII *false certainty* (because it's marked as
   provisional). This is a constitution-level change, not a
   one-off — worth design discussion before implementing.
3. **Explicit "decide" speech act from the Dodo.** When the team
   has been STUCK for N rounds and an architectural fork is
   identified but unresolved, the Dodo could escalate to human
   with a specific "I need a decision on X by Y" request rather
   than waiting for the cascade to surface conflict-keywords. This
   is what the existing escalation ladder (T20) is shaped for —
   it just needs the trigger.

Pick whichever (or some hybrid). My weak preference: option 1 first
(it's the lowest-cost intervention and uses existing mechanism), with
option 3 as the natural fallback when STUCK persists past N nudges.

---

## Notes for follow-up

1. **The Cat's cache miss is the biggest cost finding from this
   run.** ~$0.50 of the run's cost was Cat alone, all uncached.
   Diagnose what's varying in his prompt prefix before Showcase
   2.
2. **The cascade pattern needs a name.** Suggesting "polite
   deadlock" — every agent is constitutionally restrained,
   collectively unable to commit. Worth tracking when (and if)
   it recurs.
3. **The synthetic-consensus guard's silence is informative.** It
   waited through 80 utterances of (legitimate) disagreement
   without firing. The threshold and shingle defaults seem
   well-calibrated for now. Will re-evaluate when (and if) we
   see it fire on a real run.
4. **Dodo's zero LLM calls is the headline mechanism failure.**
   He has the artifact registries, the LLM client, the
   composition + escalation flows — and the team's polite
   deadlock means none of them activate. The Dodo's §III rules
   are too narrow for cascade detection. Re-design before the
   P6 showcases ship.
5. **Speak-loop defensive fix landed mid-analysis.** The
   `WonderlandAgent.speak` error-handler change makes future
   runs robust to malformed LLM responses — an agent loses one
   turn rather than its entire participation. Tested under the
   existing 923-test suite; no regressions.

---

## Next breath

Analysis 007 — the Tweedle dance. The full-cast race showed Dee
and Dum surfacing genuine frontend-backend coupling concerns to
*the team*; the dance demo will show what happens when those
concerns are *to each other*, with Cat as architectural arbiter.
The pair-protocol §I "argument is the work" claim should become
visible there in a way it didn't here — the Tweedles spent most
of this run deferring to the Cat, not negotiating with each
other.
