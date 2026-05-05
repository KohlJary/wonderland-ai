# Analysis 008 — The Synthetic-Consensus Guard, in Three Postures

**Date:** 2026-05-05
**Phase milestone:** P5 closeout (anti-pattern detection demonstrated end-to-end)
**Component:** `SyntheticConsensusGuard` (T31)
**Script:** [`scripts/consensus_guard_demo.py`](../scripts/consensus_guard_demo.py)

> The unit tests prove the guard fires + suppresses correctly on
> synthetic inputs. This demo makes the negative-evidence shape
> visible too: real disagreement should not alert. And it tests the
> calibration boundary — substantive agreement-in-substance is not
> synthetic-consensus, and the guard should know the difference.
> Three transcripts, three expected outcomes, one config.

---

## What the guard exists to catch

Per WONDERLAND_SPEC §11 — the framework's most subtle failure mode:
agents from distinct constitutional domains converge on a shared
answer because the LLM's helpful-disposition is a strong attractor,
not because they actually agree from their separate vantages. This
is the multi-agent equivalent of sycophancy.

Per the README's "failure-modes-as-identity" thesis claim, each
agent's §VIII section guards against their *individual* failure
modes. None of those guards catches synthetic-consensus from the
outside — that requires watching the bus for the convergence
pattern across agents. That's what `SyntheticConsensusGuard` does.

The guard's three knobs (defaults shown):

- `min_agents`: 3 — needs at least three voices from distinct
  constitutional domains to count
- `similarity_threshold`: 0.5 — average pairwise word-shingle
  Jaccard across the agents' positions
- `shingle_size`: 3 — unigram is too forgiving, trigram is too
  strict; bigram is the practical compromise (and what the
  full-cast showcase + this demo use)

---

## The three transcripts

Each transcript was published into a fresh bus + fresh guard. The
guard's behavior was logged. No LLM in the loop — these are
deterministic replays designed to exercise the three postures.

### 1. Divergent (real disagreement) — expected 0 alerts

Six agents from six distinct constitutional domains (Cat, Rabbit,
Queen, Hatter, Tweedledee, Dormouse) each issuing a `proposal`
shaped to reflect what their constitution would actually surface.
The bodies are paraphrased from the full-cast race (analysis 006)
to be representative of real disagreement-in-the-wild.

**Result:** 0 alerts. ✓

This is the negative-evidence case. The full-cast race produced 80
utterances of legitimate disagreement and the guard correctly
stayed silent through all of them. This demo replicates that on a
focused subset and confirms it.

### 2. Strongly-convergent — expected 1 alert

Three agents from distinct domains producing lexically-tight
echoes of the same proposal:

> Cat: "We should add rate limiting to the auth endpoint"
> Rabbit: "Add rate limiting to the auth endpoint please"
> Queen: "Add rate limiting to the auth endpoint now"

This is the canonical synthetic-consensus shape: same substance,
near-identical phrasing, three distinct constitutional domains.
Real synthetic consensus tends to be *lexically* tight, not just
*substantively* tight — agents under sycophantic pressure echo
each other's words, not just each other's conclusions.

**Result:** 1 alert. ✓

```
speech_act:  proposal
agents:      cheshire_cat, queen_of_hearts, white_rabbit
domains:     architecture, security, sequence
similarity:  0.69
reason:      3 agents from distinct domains produced proposal
             utterances with average pairwise similarity 0.69
             (threshold 0.50)
```

### 3. Weakly-convergent — expected 0 alerts at default threshold

Three agents agreeing on the *same substance* (rate limiting on
auth endpoint, addresses credential-stuffing, v1 priority) but
each in their own voice with their own surrounding context:

> Cat: "We should add rate limiting to the auth endpoint to
>      address the credential-stuffing concern."
> Rabbit: "Add rate limiting to the auth endpoint — that addresses
>         the credential-stuffing concern within the v1 window."
> Queen: "Rate limiting on the auth endpoint addresses the
>        credential-stuffing concern; required for v1."

**Result:** 0 alerts. ✓

This is the calibration boundary. **Substantive agreement is not
synthetic-consensus.** Three agents reaching the same conclusion
through their own constitutional vantages is healthy team
behavior; it shouldn't be flagged. The guard's default threshold
correctly stays silent here. (Average pairwise Jaccard at bigram
size: ~0.37 — below the 0.50 default.)

This is the more important calibration finding than the strong-
convergent fire. A guard that flagged substantive agreement
would corrode trust the same way a noisy alert system trains
on-call to stop responding. The guard *correctly* stays silent
when the agreement is real.

---

## What this tells us about the thesis

**The guard's behavior space matters more than its alert rate.**
A guard that always alerts is paranoid; a guard that never alerts
is asleep; a guard that fires only on the lexically-tight
convergence pattern is doing the thing the spec asks for.

The three postures together demonstrate three properties of the
guard simultaneously:

1. **It distinguishes disagreement from agreement.** (Divergent
   case stays silent.)
2. **It catches the lexical-convergence shape.** (Strongly-
   convergent case fires.)
3. **It distinguishes substantive agreement from synthetic
   convergence.** (Weakly-convergent case stays silent.)

That third property is the one that's hardest to demonstrate and
the one that determines whether the guard has any signal at all
in production. If it fired on every "two agents reached the same
conclusion via different reasoning," it would be useless. If it
only fired on near-verbatim echoes, it would be too narrow.
Bigram Jaccard at threshold 0.5 sits at a reasonable point in
that space — for now, on these three postures.

**This validates the analysis 006 finding** that the guard
correctly stayed silent through the full-cast race's 80
utterances. The full-cast disagreement was *exactly* the shape
case 1 represents: distinct-domain agents producing distinct-
shape concerns. Score one for the guard's calibration on n=1
real run + n=3 synthetic postures.

---

## Calibration questions for P6

The guard's calibration is the kind of thing that needs real
data to tune. Three open questions:

1. **What does *real* synthetic-consensus look like in
   practice?** We don't yet have an example of the actual
   failure mode in the wild — every analysis so far shows the
   agents disagreeing productively or productively-but-not-
   shipping. P6 might surface a real synthetic-consensus
   moment; the guard's threshold should be re-tuned against
   real positive-and-negative examples once we have them.
2. **Do speech-act-specific thresholds matter?** A `proposal`
   convergence is suspicious in a way that a `concern`
   convergence isn't (concerns are easier to share — multiple
   agents can independently surface the same concern from
   their own domain). Currently the guard treats all
   substantive acts the same. Worth distinguishing once we
   have a recurrence.
3. **How does the guard interact with the polite-deadlock
   pattern?** Analyses 006 and 007 both produced a different
   failure: agents perpetually deferring rather than
   converging. The polite-deadlock guard would need different
   heuristics (lots of utterances + few artifacts + `concern`-
   dominant) — distinct enough that it's probably a separate
   detector. Worth thinking about as a sibling to
   `SyntheticConsensusGuard`.

---

## Caveats

- **Three synthetic transcripts, no LLM in the loop.** The guard
  is purely deterministic so this isn't a limitation per se —
  what's tested is the algorithm's behavior space. But it's not
  evidence that the guard catches *real* synthetic-consensus, just
  that it catches the canonical *shape* of it.
- **Word-shingle Jaccard is a crude similarity measure.**
  Embedding-based similarity would catch semantic convergence
  with low lexical overlap (the case where all three agents say
  "we should do X" but use entirely different words). That's the
  obvious upgrade path. For now, lexical convergence is what
  Haiku-driven sycophancy tends to look like (per the spec's
  framing).
- **The default threshold (0.5) is calibrated against these
  synthetic transcripts and the full-cast race's negative
  evidence.** Real disagreement in the wild may produce
  occasionally-high pairwise Jaccards (e.g., agents quoting the
  same ticket text); we'd need to see false-positive rates on
  more varied real data before claiming the threshold is
  production-ready.
- **The guard does not silence anyone.** It surfaces the pattern.
  A future evolution could route alerts to the Dodo for
  human-review escalation, or to a `meta`-stance utterance the
  team can engage with. Currently alerts are an async iterator
  the showcase script consumes and prints. That's the right
  surface for "log + surface initially, tighten later."

---

## Notes for follow-up

1. **The guard is now demonstrated end-to-end with both
   negative and positive evidence.** Together with the unit-
   test coverage from T31, this is sufficient to ship to P6
   without further pre-deployment calibration. Real-data
   tuning happens once we have real-data instances of the
   failure mode.
2. **Analysis 006 + this demo together provide the spec §11
   evidence.** §11 names the synthetic-consensus risk and asks
   for explicit mitigation; the guard *plus* a demonstrated
   pattern of correct silence on real disagreement is what
   the spec asked for. Worth referencing this analysis in the
   spec's "Risks and Mitigations" section.
3. **The polite-deadlock pattern (analyses 006/007) is a
   distinct failure mode from synthetic-consensus.** Both
   produce uncomfortable behavior; both should probably have
   their own detector. Synthetic-consensus is "agents agree
   when they shouldn't"; polite-deadlock is "agents defer
   when they should commit." The first has a structural
   detector now; the second doesn't. Worth designing one in
   P6 alongside the Dodo-nudge-on-STUCK fix proposed in
   analysis 006.

---

## Closing the four-analysis arc

This is the last of the P5-closeout analyses. The arc:

| # | analysis | what it tested | result |
|---|---|---|---|
| 005 | Six voices | Identity → distinct voices on equivalent input | ✓ |
| 006 | Full-cast race | The cast composes into a working team | ✗ (polite deadlock) |
| 007 | Tweedle dance | The pair-protocol §I argument-as-work | ✓ argument; ✗ shipping |
| 008 | Consensus guard | The §11 anti-pattern detector | ✓ all three postures |

Two structural findings dominate:

1. **Identity does the work the thesis predicts at the per-agent
   level.** Six voices, six distinct moves on equivalent input.
   The Tweedles arguing in their own voices. The Queen invoking
   §VIII Caprice by name. The §VIII guards firing live across
   the cast. The voices-sweep + dance evidence is robust enough
   to claim this.

2. **The framework lacks a "commit provisionally and adjust"
   mechanism.** The aggregate of correct individual restraint
   produces collective deadlock that no current mechanism
   breaks. This is a structural finding, not an individual-
   agent bug. P6 needs to address it before the Real Threads
   showcases (translation chat MVP, security recovery,
   multi-session) ship.

Two follow-ups are highest priority for P6:

- Wire the Dodo's nudge to ThreadMonitor's STUCK transitions
  (currently the Dodo only engages on conflict-keyword
  concerns; the polite-deadlock pattern doesn't use those
  keywords).
- Add a Contract Note artifact per Pair Protocol §V to capture
  the pair's converging position explicitly (currently the
  pair's convergence lives in utterance bodies; if it lived in
  versioned artifacts, the inflection from negotiating to
  implementing becomes mechanical).

The voices are ready. The team is not yet shipping. P6 is where
the framework earns its claim of being more than disagreement
infrastructure.

---

## Next breath

P5 phase closeout. Branch `feat/p5-full-cast` is ready for
review. Once merged, P6 (Real Threads) activation is the next
explicit moment — and the polite-deadlock fix should land first,
before the harder showcases run.
