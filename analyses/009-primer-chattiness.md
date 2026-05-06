# Analysis 009 — The Primer's Chattiness Footprint, A vs B

**Date:** 2026-05-05
**Phase milestone:** P6.T34 follow-on (CLI smoke test surfaces a primer side-effect)
**Component:** `src/wonderland/primer.py` (T32 framework primer)
**Smoke runs:**
[`/tmp/cli-smoke/run.log`](/tmp/cli-smoke/run.log) (A — current primer) and
[`/tmp/cli-smoke-b/run.log`](/tmp/cli-smoke-b/run.log) (B — trimmed primer)

> The first end-to-end smoke of the T34 CLI runner exposed a second-
> order effect of the T32 framework primer: the team is *much*
> chattier than it should be. 56% of utterances in run A were
> `question`/`concern`, with the polite-deadlock pattern reappearing
> as procedural-caution preamble ("before I X, I need Y from Z").
> Two minimal primer edits cut visible utterances 6x and total cost
> 4x while letting the team converge cleanly instead of timing out.

---

## Run A — current primer, the chatty baseline

The smoke directive: `Build a simple Python script that prints a
haiku about cats`. Budget cap $0.30, timeout 90s, auto-respond
`ship the simplest version that compiles, defer everything else`
on escalation.

What happened in 90 seconds:

| metric | value |
|---|---|
| total cost | $0.59 (2x the budget cap, soft-cap behavior) |
| total LLM calls | 112 |
| outcome | timeout |
| visible utterances | 84 |
| `question` + `concern` | 47 (56% of utterances) |
| substantive artifacts on disk | 37 (3 ADRs, 9+ tickets, 5 stories, etc.) |
| budget-exceeded escalation | fired at $0.31, t=61s |

Three ADRs about haiku immutability and translation semantics.
Nine tickets decomposing what is, in plain reading, a fifty-line
script. The team was producing volume, but the volume was
performative — the architectural depth of the work was nowhere
near what 37 artifacts implied.

The visible flow shows the pattern explicitly:

```
[t=  3.17s] white_rabbit       concern        This directive is underspecified for proper ticketing. I need Alice to produce a story first…
[t= 12.11s] queen_of_hearts    question       Alice, before I assess this story for security and compliance implications, I need clarity…
[t= 14.25s] tweedledum         question       Alice, I need data semantics before I can build the persistence model…
[t= 17.28s] queen_of_hearts    question       Rabbit, before I engage with the security implications of this work, I need one clarification…
[t= 18.06s] tweedledee         question       Rabbit, before I can wire the haiku display, I need to understand the contract shape…
[t= 18.92s] alice              question       Rabbit, good catch on the generation vs. curation split — that's exactly the kind of clarification…
[t= 19.47s] tweedledum         question       Hatter, before I finalize the persistence model, I need to understand what failure modes…
[t= 20.42s] white_rabbit       question       Tweedledee raises a critical contract question that I need surfaced immediately…
```

This is the polite-deadlock pattern from analyses 006/007 wearing
a different costume. There, agents hedged on commitment by
softening proposals; here, they hedge by demanding clarification
before acting. Both produce the same end-state: lots of
utterances, few artifacts, no convergence.

The tell is the budget escalation at $0.31 — the team had not
shipped a single line of implementation code by the time they
spent more than the cap.

## Hypothesis — what in the primer amplifies this

Three candidates from the current primer text:

**§II — speech-act commentary (lines 124–127):**

> When you choose a speech act, the choice shapes how the team
> will read your utterance. A `concern` invites response; a
> `ruling` demands compliance; a `question` waits for an answer;
> a `reframe` asks the team to re-examine the premise. Choose
> deliberately.

Two effects: (a) explicitly framing `concern`/`question` as
*conversation-opening* moves teaches the LLM that those acts
keep the thread alive — a useful framing if the issue is silence
but exactly wrong if the issue is over-engagement. (b) "Choose
deliberately" makes every utterance feel high-stakes, encouraging
the kind of careful preamble we see ("before I assess this, I
need clarification on…").

**§VIII — disposition (lines 302–316):**

> Your value to the team is your specific way of seeing the
> work… When silence is correct, choose it. When your domain is
> implicated, surface what only you can surface.

Silence gets three words. "Surface what only you can surface"
gets the vivid framing. With ten agents reading the same primer,
each is implicitly invited to find an angle — and finding an
angle on every utterance is what produces 56%-question/concern
rate.

**§I — cast table characteristic moves (line 75):**

Each agent has a `characteristic move` listed in present-active
verb form: "ask the naive question", "demand estimates", "rule
with citation", "report what telemetry shows". These are
designed to anchor identity, but they also create implicit
pressure to *demonstrate* the move repeatedly.

## Run B — trimmed primer

Two minimal edits, both substituting calmer prose without
changing the framework substance:

**§II rewritten** (commentary about act effects → invitation to
stop performing the act-choice):

> Acts have weight by virtue of being on the bus at all. You do
> not need to preface your contribution with what kind of
> contribution it is, or to explain why this act and not
> another. The schema already encodes the act; the team reads
> it from there.

**§VIII reframed** (silence-first instead of speak-first):

> Most of the time, the right move is silence. Your value to
> the team is your specific way of seeing the work, which means
> most threads will pass through your listening loop without
> you having anything domain-specific to add. That is the
> design, not a failure of engagement.
>
> […]
>
> When your domain is genuinely implicated and only you can
> surface what needs surfacing, speak. Otherwise, the team's
> silence is what lets it work. A clarifying question that the
> next speaker would have answered anyway is noise. A concern
> that restates what the previous utterance already implied is
> noise. The bus is not a conversation to keep alive; it is a
> workspace for substantive moves.

Token count: 3451 (vs prior ~3361). Combined-prefix cache
threshold from T32 is preserved.

## Run B results — same directive, same budget, same auto-respond

| metric | A | B | Δ |
|---|---|---|---|
| total cost | $0.59 | $0.15 | **−75%** |
| total LLM calls | 112 | 27 | **−76%** |
| outcome | timeout | complete | ✓ |
| elapsed | 90s | 54s | −40% |
| visible utterances | 84 | 14 | **−83%** |
| `question` + `concern` share | 47/84 = 56% | 5/14 = 36% | −20pp |
| budget-exceeded escalation | fired at $0.31 | did not fire | n/a |
| substantive artifacts on disk | 37 | 8 | −78% |

(Implementation artifacts are zero in both runs — the Tweedles do
not yet have tooling to actually write code to disk, so this
isn't a comparison axis at the current build state.)

Run B converged cleanly via the normal terminal-state path:
running → stuck (Dodo nudged at t=39s) → quiescent → complete at
t=54s. No escalation, no timeout. The artifacts produced were two
stories, two test-scenario batches, and a few procedural acts —
shaped right for a trivial directive.

## What this is and isn't evidence of

**It is evidence:** the primer's prose has substantial behavioral
weight on engagement and chattiness, beyond its cache-padding
role. Two paragraphs of edits dropped cost 4x and visible
utterance count 6x while producing a *cleaner* terminal state.
That is not a marginal effect — it suggests the primer needs to
be tuned with the same care as a constitution, not as boilerplate.

**It isn't evidence:** that B is correctly calibrated for
substantive directives. The zero-implementation count in *both*
runs is a red herring — the Tweedles do not currently have
tooling to write code to disk, so an `implementation` artifact
literally cannot land at this stage of the build. The relevant
under-engagement signal in B is upstream of that: Rabbit waited
for Alice to answer his question before decomposing — Alice
never answered, so no decomposition happened. The Tweedles fired
three LLM calls each but never spoke. That conservatism may turn
out to be correct for a haiku script (nothing genuinely needed
ticketing) and wrong for a real directive that needs scope
broken down before contract negotiation can happen.

**The risk:** if "the bus is not a conversation to keep alive" is
read by agents as "do not pursue follow-up", we have traded
performative procedural-caution for premature disengagement. Both
are failure modes; both are within the framework's design space
to tune. The non-trivial showcase directives in T36–T38 will
exercise this distinction: if the team converges without
producing tickets, decomposing scope, or surfacing concrete
contract notes, the trim went too far.

## What lands now (run A as committed)

Per the user's call ("let's do A with the understanding B might
be coming depending on how the next test fares"), the trimmed
primer ships as the new default. A more substantial directive —
something that genuinely needs the Tweedles to ship code, not
just the team to converge on scope — is the test that will
distinguish "well-tuned" from "over-corrected". The Real Threads
showcases (T36 translation chat MVP, T37 security recovery, T38
multi-session persistence) are exactly that test.

## Open follow-ups, in priority order

1. **Validate on a non-trivial directive.** The chattiness fix is
   established; the under-engagement risk is open. Showcases T36–
   T38 will surface this naturally. If they show the team
   converging without shipping, soften §VIII once more —
   specifically the "bus is not a conversation to keep alive"
   line, which is the sharpest discouragement of follow-up work.

2. **Hard budget cap** (roadmap `aa65d2d7`). Run A's $0.59
   against a $0.30 budget shows the soft cap can overshoot 2x.
   Hard cap requires gating `WonderlandAgent.run()` on
   `Telemetry.total_cost > budget_dollars` — invasive, but the
   alternative is dashboard surprises during showcase runs.

3. **Distinguish budget-exceeded brief from polite-deadlock
   brief** (roadmap `ac3c6dc5`). Run A's escalation brief said
   "Thread has been STUCK (budget exceeded: $0.31 > $0.30)" — the
   parenthetical reason is right but the leading STUCK framing is
   wrong, since there's no nudge ladder in the budget case.

## Next breath

T34 closes here. The Runner ships, telemetry ships, the CLI
ships, the chattiness fix lands as a follow-on commit, and three
calibration items move to the roadmap for follow-up. T35 (Contract
Note artifact, Pair Protocol §V) is the next gameplan item — and
the contract-note mechanism is exactly the structural addition
that should let the Tweedles transition from negotiating to
shipping in the showcases ahead.
