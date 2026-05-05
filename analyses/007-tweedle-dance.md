# Analysis 007 — The Tweedle Dance

**Date:** 2026-05-05
**Phase milestone:** P5 closeout (the implementation pair, alone with their seam)
**Cast online:** Dee, Dum, Cat (arbiter), Dodo (state machine)
**Model:** `claude-haiku-4-5-20251001`
**Script:** [`scripts/tweedle_dance_demo.py`](../scripts/tweedle_dance_demo.py)

> The voices sweep showed Dee and Dum speaking in distinct voices.
> The full-cast race showed them deferring to the Cat in unison.
> This demo isolates them — Dee + Dum + Cat as architectural arbiter
> — on a directive whose contract has genuine ambiguity at the seam.
> The hypothesis: the pair-protocol §I "argument is the work" claim
> should become visible. It does. But the same polite-deadlock
> pattern from analysis 006 reappears — in a smaller team, with a
> designated arbiter, on a sharper question. That recurrence is
> itself the finding.

---

## The dance, summarized

**Outcome:** **TIMEOUT at 240s. Did not reach COMPLETE. Zero
implementations on disk.**

**Activity:** 60 utterances over 240 seconds, distributed across:

| act | count | who issued |
|---|---:|---|
| concern | 43 | Dee (~17), Dum (~14), Cat (~12) |
| proposal | 13 | Cat |
| deference | 2 | Dee |
| reframe | 1 | Cat |
| ticket | 1 | (synth.) Rabbit |

**The pair *did* converge on substantive contract decisions** by
~t=85s:

- **Message-id stability:** mutation model (id stable, revision
  counter)
- **Staleness handling:** silent annotation of replies to old
  revisions
- **Event sequencing:** immediate `message-edited` followed by
  `message-translated` events as the translation worker completes

Tweedledee at t=85.28s: *"The contract negotiation with Tweedledum
is complete on the seams we control. We've converged on mutation
model (message-id stable, revision counter), identified the
staleness-handling approach (silent annotation of replies to old
revisions), and locked the event-sequencing model."*

**They had a working contract.** And they did not ship.

---

## Why they didn't ship

The Cat — present as architectural arbiter — produced 13 proposals
across the 240 seconds. Every proposal was substantively useful.
Every proposal *also* surfaced a new sub-question the pair hadn't
fully resolved. The shape was consistent: pair converges on
position → Cat surfaces a deeper consideration → pair re-engages on
the new question → pair converges on a refined position → Cat
surfaces a deeper consideration → …

**The Cat at t=91.12s, after the pair had locked the mutation model:**
*"You've structured this correctly and you're holding the right
boundaries. The mutation model is now locked. The staleness-
handling default (silent annotation) is sound. […] I want to
surface one thing beneath the contract negotiation, because it
will determine whether the annotation approach actually works
operationally."*

That phrase — "*one thing beneath*" — recurred across multiple Cat
proposals. The Cat correctly identified architectural depth the
pair hadn't surfaced. And each correctly-identified depth-question
became one more thing the pair felt they had to resolve before
shipping.

**The pair never reached a point where they said "we have enough;
let's ship a v1 implementation."** The Pair Protocol's §VIII
"contract drift" guard ("if a change doesn't seem worth versioning,
it's exactly the kind of change that drifts") and Tweedledum's §VIII
"invariant erosion" guard kept them honest — but combined with the
Cat's depth-finding, "honest enough to ship" was a state the system
never represented.

---

## Same finding as analysis 006, sharper

The full-cast race (analysis 006) named "**polite deadlock**" —
each agent's individual constitutional restraint correct;
collective inability to commit. This run replicates it on a
smaller team, with the framework's intended arbiter present,
on a more focused question. The pattern is robust to shrinking
the team and adding the right intervention agent.

This is the more honest formulation of the finding:

**The framework currently models "should I speak?" but not "should
we ship now?" There is a per-agent decision (deliberate → utterance
or silence) and a per-thread state (running / quiescent / stuck /
complete). There is no per-task state of "we have enough
information; commit provisionally."** Each agent's §VIII guards
push toward "wait for clarity." There is no countervailing
mechanism that says "you have enough; commit and revise if wrong."

The Cat in particular has no concept of "the Tweedles have
converged; my job here is done." His engagement rules trigger on
proposals (his own domain) and on architectural-keyword concerns;
the Tweedle pair's converging concerns kept triggering him. Each
trigger produced a proposal. Each proposal was good. Each proposal
extended the negotiation by surfacing one more depth-question.

---

## What this run did demonstrate (the positive findings)

The framework *did* work in important ways:

### 1. The Pair Protocol §IV handoff etiquette was visible

Both Tweedles named the protocol explicitly. Tweedledum at t=39:

> "I'm proposing we converge on a unified Contract Note that
> captures both sides' constraints and reaches resolution. This is
> exactly the protocol from Pair Protocol §IV: Contract change
> request. I'll lead with my constraints and questions back to him,
> then we either align or escalate to the Cat."

This wasn't a generic "I'll think about it" response. It was the
Tweedle invoking the documented protocol — "Pair Protocol §IV" by
name — and following its steps. The constitution-as-data isn't
just framing; the agent's deliberation explicitly references the
protocol section that shapes the move. Same shape Queen used in
analyses 005/006 ("I am raising concerns rather than ruling
because…"). Two agents, two domains, both agents *reasoning from
their constitutional text by name*. That's identity doing its
work.

### 2. The pair converged on substance

Three concrete contract decisions landed: mutation model with
revision counter, silent staleness annotation, ordered
`message-edited` then `message-translated` events. These aren't
fabricated agreement — both Tweedles independently arrived at the
same answers, with the Cat's reframing helping crystallize the
choice. **That's the kind of agreement the pair-protocol predicts.**
It just didn't translate into shipped implementations.

### 3. The Cat's interventions were architecturally sound

Every Cat proposal added a real consideration. Operational
implications of silent annotation. Causal-ordering guarantees of
the real-time layer. Translation-worker latency variance affecting
the event-shape choice. None of these were noise. The Cat doing
his job well *is itself part of what produces the deadlock* — and
that's the surprise. A correct architectural intervention can
extend a converging negotiation past its natural shipping point.

### 4. Caching engaged for the Tweedles

Both Tweedles cleared 100k+ cache reads each, confirming again that
the double-loaded constitution prefix (own + pair protocol) puts
them reliably in Haiku's cache-hit zone:

| agent | calls | input | output | cache_r |
|---|---:|---:|---:|---:|
| tweedledee | 22 | 380,718 | 16,771 | 177,639 |
| tweedledum | 19 | 330,894 | 16,826 | 159,552 |
| cheshire_cat | 23 | 473,730 | 16,019 | **0** |

The Cat's cache miss is the same anomaly as analysis 006 — 23 calls
with zero cache hits. Whatever's varying in his prompt prefix, the
behavior is consistent: he doesn't cache. Worth tracing in P6.

---

## What it tells us about the thesis

n=1 dance, single contract scenario. Modest evidence — but the
finding is robust enough across 005/006/007 to name as a structural
property:

**Thesis claim that survived:** identity-native agents produce
distinct, in-character moves on equivalent input. (Six voices,
Tweedles arguing the contract, every utterance recognizably its
speaker.)

**Thesis claim that needs revision:** the framework as currently
designed produces *correct restraint* but not *appropriate
commitment under uncertainty*. The constitutions encode "do not do
X" effectively. They do not encode "the team has paused long enough;
commit provisionally and adjust." Three runs (006, 007, and the
parts of 005 where Caterpillar caveated everything because he
couldn't see the actual code) show this pattern.

**This is not a bug in any individual constitution.** It's an
emergent property of the framework as designed. Each agent's §VIII
section is correct in isolation. The aggregate produces a
collective behavior the framework has no mechanism to break.

---

## Numbers worth keeping

| metric | dance | full-cast (006, for comparison) |
|---|---:|---:|
| wall time | 240.00s | 600.00s |
| utterances | 60 | 80 |
| concerns / total | 72% | 79% |
| substantive artifacts shipped | **0** | 22 (3 + 3 + 9 + 3 spike + …) |
| substantive contract decisions made | 3 (in-conversation, not artifacted) | 0 (substance was in artifacts) |
| total LLM calls | 64 | 144 |
| total input tokens | 1,185,342 | 4,577,266 |
| total output tokens | 49,616 | 96,236 |
| Cat cache hits | 0 | 0 |
| Tweedle cache hits | 337k combined | 250k combined |
| ThreadState transitions | (none — running throughout) | 2 × `running → stuck` |
| Dodo LLM calls | 0 | 0 |

The dance produced *more* substantive contract content per token
than the full-cast race (decisions per call ratio is higher), but
*fewer artifacts on disk* (zero vs 22). The pair's negotiation
happened in-utterance, not in-artifact. **A future architecture
could capture this as Contract Note artifacts** — the pair-protocol
§V documents this artifact, but the agent code doesn't currently
produce it.

---

## Caveats

- **n=1 dance, one contract scenario.** Don't generalize.
- **The Cat's depth-finding behavior may be specific to "message
  editing" as a topic.** A more bounded scenario (e.g., "agree on
  the auth-token refresh contract") might produce convergence-
  with-shipping. Worth running a second dance on a sharper topic
  to test.
- **The dance had no Caterpillar.** Reviews close negotiations in
  practice — once Caterpillar approves an implementation, the pair
  is done. Without him present, there's no closure mechanism.
  Adding Caterpillar to a future dance would test whether his
  presence resolves the polite-deadlock. (Caterpillar's §III
  engages on `implementation` from Tweedles; if no implementation
  ships, he never engages.)
- **Dodo zero LLM calls again.** Same finding as 006: his §III
  rules don't catch the polite-deadlock pattern. Reinforces the
  P6 priority.
- **Both Tweedles read each other's utterances.** The voices were
  genuinely paired (each knew the other's positions and built on
  them). The §I "argument is the work" claim is observably true;
  what's missing is the §VI "done conditions" mechanism — and the
  done conditions in the constitution are *implicit* about
  shipping ("when the ticket's acceptance criteria are met by
  code that runs"). The agent has no clear way to flip from
  "negotiating contract" to "implementing against contract."

---

## What we'd expect to see strengthen the thesis

Two design hypotheses to test in P6:

1. **Add a Contract Note artifact** that captures the pair's
   converging position and explicitly versions it. The pair-
   protocol §V documents this artifact's shape. Right now the
   pair's negotiation lives in utterance bodies; if it lived in
   versioned Contract Note artifacts, the inflection from
   "negotiating" to "we have an agreed v1 contract; now ship"
   becomes a natural transition (`contract.version` increments,
   then both Tweedles publish implementations referencing that
   version). This is a constitutional + schema change, not a
   small one — but it's what the protocol already says should
   exist.

2. **Wire the Dodo to STUCK + extended-running thread states.**
   Per the analysis 006 finding, the Dodo currently engages only
   on conflict-keyword concerns. He should engage when the
   ThreadMonitor reports a thread has been actively talking
   (lots of utterances) but not producing artifacts for N
   consecutive rounds. That's the polite-deadlock signature, and
   it's mechanically detectable. The Dodo could nudge ("the
   pair has been negotiating for N turns without an artifact;
   commit provisionally?") or escalate to Cat ("propose a
   provisional contract and let them adjust").

My weak preference is to do both, but #2 is cheaper to implement
and tests the diagnosis directly. If wiring Dodo's nudge to
STUCK transitions fixes the cascade in a re-run of analysis 006,
the diagnosis is correct. Then the Contract Note artifact is the
follow-up to make the convergence durable.

---

## Notes for follow-up

1. **The Cat's depth-finding produces deadlock at the architectural
   layer.** Worth examining whether his engagement rules should
   include some form of "the team is converging; let them ship"
   detection. Risky — this could violate his §VIII *false certainty*
   guard if it pushes him to bless something he hasn't fully
   examined. But the alternative (current behavior) is worse.
2. **Dee invoked Pair Protocol §IV by name.** This is the kind of
   constitutional reasoning the framework is designed to produce.
   Worth grepping future transcripts for explicit §-references —
   they're a cheap signal of the LLM doing constitutional reasoning
   vs. role-playing-helpfully.
3. **Caterpillar absence may be the second-most-important variable.**
   The pair never had a "review-pending → review-complete →
   merged" closure event. A re-run with Caterpillar present
   would test whether his approval mechanism breaks the deadlock.
4. **The pair did real work.** This isn't a "the agents failed"
   finding; this is a "the framework's done-condition is
   under-specified" finding. The pair converged on substantive
   technical decisions; the framework just doesn't have a way for
   them to say "and we're done arguing now."

---

## Next breath

Analysis 008 — the synthetic-consensus guard, in two postures.
The full-cast race showed it correctly staying silent on real
disagreement. The dance showed it staying silent on real
convergence-without-shipping. The remaining question: does it
*fire* on the synthetic shape it's actually designed to catch?
Demo 4 will construct that scenario explicitly, alongside the
negative cases the field runs already produced.
