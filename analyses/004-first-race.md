# Analysis 004 — First Race

**Date:** 2026-05-04
**Phase milestone:** P4.T22 (Showcase 1 — first end-to-end autonomous run)
**Cast online:** Cheshire Cat, White Rabbit, Dodo, Alice (4 of 10)
**Model:** `claude-haiku-4-5-20251001`
**Script:** [`scripts/health_endpoint_showcase.py`](../scripts/health_endpoint_showcase.py)

> The first time the system runs end-to-end without a human in the
> loop. The Dodo relays a directive; the team works it; the team goes
> quiet; the Dodo records completion. No orchestrator told anyone to
> stop. The thread reached "done" because nobody had anything left to
> say.

---

## The race

**Directive Dodo relayed:**

> Add a GET /health endpoint to our Phoenix web app. It will be polled every 5 seconds by our Kubernetes liveness probe — no other consumers in v1, no auth, no dependency checks. Return HTTP 200 with the JSON body {"status":"ok"} whenever the app is up. Ship as the next deploy.

**Transcript:**

| t (s) | speaker | speech_act | what happened |
|------|---|---|---|
| 0.00 | dodo | `directive` | relays the directive (mechanical, no LLM) |
| 7.26 | white_rabbit | `ticket` | one ticket, owner Tweedledee, 0.25–0.5d / 85% |
| 23.02 | thread_monitor | (transition) | running → quiescent (no open expectations; silent 15.8s) |
| 23.02 | dodo | `acknowledgment` | publishes "Thread health-thread → complete" |
| 23.02 | thread_monitor | (transition) | running → complete |

**Per-agent activity:**

| agent | LLM calls | input | output | decision(s) |
|---|---|---|---|---|
| alice | 2 | 7855 | 38 | `silence`, `silence` |
| cheshire_cat | 1 | 3210 | 19 | `silence` |
| white_rabbit | 1 | 83 | 368 | `ticket` (1 ticket) |
| dodo | 0 | — | — | mechanical only (relay + acknowledge) |

**Outcome:** COMPLETE in 23.02s. One artifact on disk: `tickets/ticket-001-add-get-health-endpoint-for-kubernetes-liveness-probe.md`.

**Rabbit's ticket** (excerpt):

> **Owner:** Tweedledee
> **Tier:** v1
> **Estimate:** 0.25–0.5 days, 85% confident
>
> **Acceptance:**
> - GET /health returns HTTP 200
> - Response body is valid JSON: {"status":"ok"}
> - Endpoint requires no authentication
> - Endpoint has no dependency checks — returns 200 as long as app process is alive
> - Endpoint is included in next deploy
>
> **Risk:** Very low. Phoenix routing is straightforward; controller is single line of work.

---

## What the team did

1. **Three of four agents stayed silent.** Alice deliberated twice (on
   the directive and on Rabbit's ticket) and chose silence both times.
   Cat deliberated once on the directive and chose silence. Dodo never
   called the LLM at all — his role was mechanical relay + mechanical
   acknowledge. The only voice in the substance of the work was the
   Rabbit, because the only thing the directive required was
   decomposition into a unit of work.

2. **Alice's §VIII held.** Her constitution explicitly names "the
   product owner who keeps adding stories during implementation" as a
   failure mode. The directive was an operational change with no
   user-facing surface — a Kubernetes liveness probe doesn't have a
   persona. Inventing one would have been the textbook §VIII failure.
   She didn't. Two LLM calls, 38 total output tokens, both `silence`.
   The cheapest possible right answer.

3. **Cat's §VIII held too.** Returning HTTP 200 with `{"status":"ok"}`
   is not an architectural decision — there's no fork in the road, no
   coupling to surface, no seam to name. ADR-fabrication would have
   been the §VIII failure. He chose silence; 19 output tokens.

4. **Rabbit produced exactly one ticket.** 0.25–0.5d, 85% confidence,
   crisp acceptance criteria that map 1:1 to the directive's stated
   constraints. He did not invent dependencies the directive didn't
   imply. He did not over-decompose into "set up routing" + "add
   controller" + "add response" — the work is a single piece, so it's
   one ticket. This is Rabbit at his best per §I: scope-honest,
   estimate-honest, decomposition-honest.

5. **The Dodo never deliberated on content.** All four of his actions
   were mechanical: the directive relay (templated publish), the
   acknowledge on quiescence (templated publish). His LLM call count
   is zero. His constitution §VIII says doing domain work is the
   pernicious failure mode — and the showcase honors that exactly.

6. **The thread closed itself.** No one said "we're done." No one
   asked "are we done?" The team went silent because they had nothing
   to add. The ThreadMonitor noticed (15.8s of silence with no open
   expectations), the Dodo published the acknowledgment, and the
   thread transitioned to COMPLETE. Per dodo.md §VI: "your silence
   after done is itself information."

---

## Grading the predictions from analysis 003

Analysis 003 named four falsifiable predictions for this run. Results:

### ✓ "Alice will produce fewer stories than this run"

Analysis 003's Alice produced 7 stories on the open-ended translation
chat directive. Showcase 1's Alice produced **0**. The §VIII restraint
claim — that she should not pad operational directives with persona
stories — survives the test. Stronger than predicted: I expected her
to produce *fewer*, not *zero*. Zero is the right answer here, and
she got it.

### N/A "At least one of her stories will be addressed to an oncall persona, not an end-user"

Untested. Alice's silence is the correct outcome when the directive
doesn't implicate a user the system serves. The oncall persona would
have been the *least bad* story she could write; the right answer was
no story at all.

### N/A "The Cat will produce an ADR that references one of Alice's confusion_flags"

Untested. Both Alice and Cat stayed silent. The hand-off mechanism
predicted in analysis 003 needs an open product directive to exercise
— P5/P6 showcases (translation chat MVP, security recovery) are where
this prediction gets its real test.

### ✓ "The Rabbit will produce tickets that map 1:1 to Alice's acceptance conditions"

Modified-pass. Alice produced no acceptance conditions, so the test
was instead: *do the Rabbit's ticket acceptance criteria map 1:1 to
the directive's constraints?* Yes — every constraint stated in the
directive (HTTP 200, JSON `{"status":"ok"}`, no auth, no dependency
checks, ships next deploy) appears as an acceptance condition. He
neither dropped one nor invented one. This is the spirit of the
prediction even though Alice wasn't the source.

**Score: 1/4 strict, 2/4 strict + spirit. The two N/As are downstream
of the very correct §VIII outcome — when the lynchpin says nothing,
the predictions about what flows from her can't fire.**

---

## What it tells us about the thesis

After T22, n=4 characters online, single trigger, autonomous
end-to-end. The hypothesis was: identity-native agents with stable
constitutions can run a directive to settlement without a human in
the loop. They did. Three observations:

### 1. Silence is the most-used speech act in this showcase

Three of four agents (Alice ×2, Cat ×1) chose `silence`. The Dodo
chose silence in deliberation (his content-deliberate is hard-wired
to None). Only the Rabbit produced a substantive utterance.

A generic-prompted "agent, respond to this directive" baseline would
overwhelmingly produce *content*. The Cat-baseline would suggest an
architecture; the Alice-baseline would write a user story; the
Dodo-baseline would summarize. Each would feel productive. Each would
also be wrong here — the directive doesn't need architecture, doesn't
have a user, doesn't need summarizing. The showcase didn't *need*
extra utterances; the constitutions correctly suppressed them.

This is the part of the thesis that's hardest to instrument: the
counter-factual. "What would have been said but wasn't" doesn't show
up in transcripts. The artifact-light outcome is the evidence — one
ticket, no padding.

### 2. Quiescence detection works as a settlement signal

15.8 seconds of bus-silence with no open expectations triggered the
ThreadMonitor's `running → quiescent` transition. The Dodo's
acknowledge fired automatically off that transition. The
acknowledgment itself (with "complete" in the body) triggered
`running → complete`, and the showcase script exited. No human
intervention; no "are we done yet?" timer; no orchestrator
announcement. The team's silence *was* the settlement.

The 15-second threshold is a tunable. Too short and you risk
declaring quiescence while an agent is still mid-deliberation
(Alice's solo run took 31s end-to-end for 7 stories). Too long and
the showcase drags for no benefit. 15s worked here because the
heaviest deliberator (Rabbit's ticket) finished in 7.3s; the rest of
the wait was confirming silence. P5+ with the full cast may need
calibration.

### 3. The procedural/substantive bicameral split paid off

The Dodo emitted two procedural utterances (DIRECTIVE on relay,
ACKNOWLEDGMENT on completion). Neither carried domain content. The
Rabbit emitted one substantive utterance (TICKET) with the actual
work. Looking at the transcript, the procedural utterances are
trivial to skim — they're routing/state markers — and the substantive
utterance is where the eye lands. This wouldn't be true in a system
where every agent emits prose around every action. The
procedural-vs-substantive distinction in `SpeechAct` (PROCEDURAL_ACTS
= nudge/composition/escalation/acknowledgment) is doing legibility
work I didn't fully appreciate when the split was first written.

---

## Caveats

- **Single trigger, single dance.** This is one run. The thesis
  predicts *consistency* — an identity-native team should produce
  this kind of disciplined outcome reliably across many runs and
  many directive shapes. T22 demonstrates the mechanism; P7's eval
  harness is what generates the consistency claim.
- **Concrete directive shaped the silence outcome.** The directive
  was structured almost like a story already (acceptance criteria
  embedded inline). A vaguer directive would have triggered Alice
  into story-writing — analysis 003 showed exactly that. The
  showcase tested the *concrete-directive flow*; the
  *open-directive flow* is exercised in earlier analyses and will
  reappear in P5+ showcases.
- **Conflict ladder untested.** No conflict arose, so the
  composition + escalation flow (T19/T20) didn't fire. The showcase
  script does react to STUCK/DEADLOCKED transitions (it prints a
  note), but neither happened. P5+ needs a directive where the cast
  genuinely disagrees, then we'll see whether the Dodo's composition
  attempt + escalation fallback work end-to-end.
- **Cat's silence is correct but invisible.** "Silence is itself
  information" is in the constitution, but a transcript with one
  acting agent doesn't prove the silent agents *engaged and chose
  silence* versus *didn't engage at all*. Token usage is the only
  signal here: Cat's 3210 input + 19 output confirms he deliberated
  and chose silence. Worth surfacing this distinction in transcripts
  — a "silent-after-deliberation" marker would make the choosing
  visible. Adding to follow-ups.
- **Dodo's relational work was zero in this run.** He relayed and
  acknowledged but didn't deliberate. In a stuck or conflicted
  thread, his composition + escalation flows do the heavy lifting,
  and his LLM cost would dominate. P5+ will give us that data.
- **Bug fix landed mid-showcase.** The first attempt with this
  directive completed the dance correctly but raised a
  ValidationError in teardown — Alice's LLM emitted
  `{"decision":"silence","body":null,"stories":null}` and the parser
  rejected nulls. Fixed by adding `field_validator(mode="before")`
  to coerce None → defaults across AliceResponse, CatResponse,
  RabbitResponse, ConflictResponse, BriefProseResponse; 5 new tests
  cover the regression. Mentioning here because the *original*
  showcase output captured before the fix is what's being analyzed
  — the substantive outcome (ticket, completion, timing) is
  identical in both runs; only the teardown differs.

---

## What's next for the thesis

- **P4 closes after T23 (`wonderland init` CLI).** The init CLI lets
  someone point Wonderland at a real project directory and have the
  `.wonderland/` skeleton appear. After that, P4 ships.
- **P5 (Full Cast).** The remaining 6 agents come online: Hatter,
  Caterpillar, Queen, Dormouse, Tweedledee, Tweedledum. Speech-act
  signatures per character become observable across many runs.
  Synthetic-consensus guard lands here because disagreement
  finally has more than two voices to disagree with.
- **P6 (Real Threads).** The hard showcases — translation chat MVP
  (the directive that's been the throughline of analyses 001–003),
  security recovery scenario, multi-session persistence. The
  conflict ladder gets exercised. The compaction layer's value
  becomes measurable: does a second run referencing the first run's
  compactions reach settlement faster?
- **P7 (Evals).** Generic-prompted vs identity-native baseline. The
  compounding curve. The legibility-of-value mitigation from
  WONDERLAND_SPEC §11.

---

## Notes for follow-up

1. **Surface "silent-after-deliberation" in transcripts.** When an
   agent engages and chooses silence, the showcase printer currently
   shows nothing — but the silent decision is meaningful (e.g., Cat
   actively deciding "no architecture decision needed here"). A
   post-run transcript marker like `[silent-after-deliberation: cat]`
   would make the suppression visible to readers.
2. **Calibrate quiescence threshold per showcase.** 15s worked for
   /health. P5+ showcases with longer-deliberating agents (Hatter
   generating test scenarios) may need 20–30s. Could be made
   adaptive — wait long enough that the slowest recent deliberation
   has had time to finish.
3. **Token-cost telemetry per turn rather than per agent.** Per-agent
   totals hide the per-call shape. For analyses 005+ I want to see
   "Alice call 1: 3839 in / 19 out" rather than "alice total: 7855
   in / 38 out" — the per-call view shows the cost of each silence
   versus each substantive turn.
4. **Showcase 1 didn't exercise the conflict ladder.** That was
   expected for /health. P5+ needs at least one showcase whose
   directive *should* surface a real cross-domain conflict, so we
   can watch composition + escalation work end-to-end.
5. **Bug surfaced + fixed: null-field coercion in agent response
   parsers.** Five new tests (one per response schema) prevent
   regression. Worth keeping an eye on whether the LLM emits other
   schema-noise (extra fields, type drift) we should be tolerant of.

---

## Next breath

P4.T23 — `wonderland init` CLI. After that, P4 closes. The
README's status table flips P4 to ✓; P5 becomes the active phase
and the cast finally fills in.
