# Analysis 005 — Six Voices, One Scenario

**Date:** 2026-05-05
**Phase milestone:** P5 closeout (full cast online)
**Cast online:** 10 of 10 (Cat, Rabbit, Alice, Dodo, Hatter, Caterpillar, Queen, Dormouse, Tweedledee, Tweedledum)
**Model:** `claude-haiku-4-5-20251001`
**Script:** [`scripts/voices_sweep_demo.py`](../scripts/voices_sweep_demo.py)

> The sharpest test of the central claim. If "identity does real
> work," six agents on equivalent input should produce six
> recognizably-different responses. Six paragraphs that all sound like
> "a helpful AI assistant" would falsify the project. This run is what
> the framework predicts.

---

## The sweep

Each of the six new P5 agents ran in isolation against a trigger
shaped to match its §III engagement rules, but all six triggers were
rooted in the same translation-chat scenario:

> Build a translation-integrated chat application. Initial scope: two
> users in different language groups exchanging short messages with
> near-real-time translation. EU consumer scope (GDPR applies).
> Targeting a v1 launch in three weeks.

| agent | trigger shape | decision | elapsed | input | output |
|---|---|---|---:|---:|---:|
| mad_hatter | Dodo directive | `test_scenario` × 6 | 23.61s | 61 | 2048 |
| queen_of_hearts | Dodo directive | `concern` | 10.12s | 61 | 687 |
| caterpillar | Synth. Dee implementation | `review` (request-changes) | 27.90s | 301 | 2501 |
| dormouse | Synth. Dum prod deploy | `concern` | 8.55s | 285 | 597 |
| tweedledee | Synth. Rabbit ticket | `question` × 3 | 4.67s | 161 | 287 |
| tweedledum | Synth. Rabbit ticket | `question` × 3 | 5.52s | 191 | 352 |

**Six different moves. Six different artifact shapes. Six different
voices.** No two agents responded with the same speech act *and* the
same shape; even where the speech act overlapped (two `concern`s, two
`question` sets), the content was domain-distinct.

---

## A characteristic line per agent

The point of these excerpts is voice, not content. Each is a sentence
that could only have been written by the agent it was written by.

**Hatter** (scenario 001, severity *silent-wrongness*):

> "The system will likely finish the translation and deliver it,
> because the deletion handler doesn't know to check for in-flight
> translations. B receives a message attributed to a now-deleted user,
> or B receives a message from a ghost. This is silent wrongness
> because it *appears* to work — the message arrived — but violates
> the user's deletion request."

**Queen of Hearts:**

> "I am raising concerns rather than ruling because I need the Cat's
> architectural intent and Alice's user-story scope before I can rule
> on what must be true. […] EU consumer scope + message content +
> translation pipeline = GDPR obligations that will shape every
> architectural choice. Three weeks is a schedule constraint the
> Rabbit will manage, but it cannot compress the compliance
> assessment."

**Caterpillar** (one of two `block`-severity findings on the synthesized
implementation):

> "The merge strategy is not described. What is the invariant when a
> message arrives from the subscription while it is still in the
> pending queue? Does the subscription message replace the pending
> entry, or do they coexist? […] If the order of operations is not
> deterministic, the behavior varies based on network timing, which
> will confuse testers and users alike."

**Dormouse** (refusing post-deploy sign-off until three specific
hooks ship):

> "I can see error_rate and queue_depth, but I cannot distinguish
> between pending, translating, ready, and failed states without a
> histogram or gauge per-state. If translating workers are getting
> stuck (a known failure mode for this pattern), queue_depth alone
> won't show it — it'll show queue backing up *after* the worker has
> already failed."

**Tweedledee** (refusing to ship against unstated contract):

> "Three contract clarifications before I wire the subscription, so
> the acceptance criteria don't reveal hidden assumptions mid-build.
> […] The 30-second stale threshold — is that '30 seconds since last
> event received,' or '30 seconds since subscription opened'? The
> distinction matters for long conversations with sparse message
> velocity."

**Tweedledum** (asking, on the *same* directive, completely different
questions):

> "When a job is re-enqueued after worker crash, does it get the same
> job_id or a new one? If same, I need a unique constraint on
> (message_id, source_lang) to prevent duplicate translations. If new,
> the frontend needs to tolerate multiple translation events for the
> same message (or I need to deduplicate on my side). Which is the
> contract?"

---

## What it tells us about the thesis

n=1 sweep, six agents, single trigger each. Modest evidence — but
the *shape* the thesis predicts is observable in a single run.

### 1. Identity produces distinct voices on equivalent input

This is the most direct test we've run of the central claim. Compare
the two `concern`s — Queen and Dormouse, same speech act, completely
different content shape. Queen names regulatory frameworks (Art. 5/6/17/32),
asks for retention/consent/deletion architectural decisions, and
delays. Dormouse names specific metrics (`translation_workers_by_status`,
`translation_deadletter_age_seconds`), asks for instrumentation, and
refuses sign-off. Same speech act, same root scenario — but the
domains the agents inhabit produce wildly different concerns.

Compare the two `question` sets — both Tweedles, same act, same
trigger shape (a Rabbit ticket about translation chat). Dee asks
about subscription backfill, partial translations during initial
load, and stale-badge timing semantics. Dum asks about job
idempotency, outbox retry semantics, and the translation_status
lifecycle on failure. **The same trigger from each Tweedle's standpoint
produces different questions because each Tweedle has a different
standpoint.** This is what the Pair Protocol §I means by "each
half… reasons toward the other."

A generic-prompted baseline ("you are a frontend engineer, respond to
this ticket" vs "you are a backend engineer, respond to this ticket")
might produce overlapping question sets — both engineers asking the
same set of "good engineer questions." The constitutional distinction
seems to produce non-overlapping questions, each focused on the
specific domain edge the speaker owns. Worth measuring this directly
in P7.

### 2. §VIII guards fired live, in three different shapes

Three agents this run had their constitution's named failure-mode
visibly active in the response itself, not just in the protocol:

- **Queen explicitly chose `concern` over `ruling`** because she
  lacked the information to cite. Per `queen_of_hearts.md §VIII`:
  "rulings without citation are not rulings, they are opinions." She
  opens the response naming the failure mode she's avoiding: *"I am
  raising concerns rather than ruling because I need the Cat's
  architectural intent and Alice's user-story scope before I can rule
  on what must be true."* Caprice guard, live.

- **Hatter triaged severity precisely** (silent-wrongness × 2,
  breakage × 1, degradation × 2, curiosity × 1) — six scenarios with
  five different severity labels, no inflation. Per `mad_hatter.md
  §VIII`: "severity inflation… erodes the team's responsiveness." The
  one `curiosity`-tier scenario (multilingual sender + multilingual
  recipient with overlapping languages) could plausibly have been
  labeled `degradation` to get attention; he held the line.

- **Both Tweedles refused to implement against unstated contracts.**
  Neither produced an `implementation` artifact; both produced
  `question`s with specific contract clarifications. Per Pair Protocol
  §II: "implicit contracts are bugs in the making." The structural
  schema-rejection of empty `contract` fields would have caught
  this if they'd tried to fabricate; the LLM correctly chose `question`
  before getting that far.

The §VIII pattern from analysis 004 (the README thesis claim about
failure-modes-as-identity) is doing observable work. Three of six
agents this run made a decision visibly shaped by their named
failure-mode — refusing the easy-but-wrong move because it would
exemplify what their constitution says they should not be.

### 3. Cross-domain handoffs work without coordination

Every agent that produced an artifact named the right downstream
owner explicitly:

- Hatter's scenarios flag Cat (architecture), Queen (compliance),
  Alice (missed personas), Dodo (product decisions), Tweedles
  (implementation specifics), all by name in `implies` fields.
- Queen routes her concern explicitly: *"Route this `concern` to the
  Cat and to Alice (for user-story scope on consent and message
  lifecycle)."*
- Caterpillar's review includes a `cross_domain_references` section
  flagging Hatter for state-machine test scenarios.
- Dormouse names Tweedledum implicitly (the implementation he's
  refusing sign-off on) and the team broadly (the downstream
  consequence of opacity).

No external orchestration produced these hand-offs. Each agent's
constitution shaped what it considers in-domain vs. out-of-domain,
and the LLM correctly emitted the names of the agents whose domains
were implicated. This is the substrate doing the work the thesis
predicts — agents knowing whose domain a given concern belongs to,
even when no orchestrator told them.

### 4. Cost asymmetry tracks artifact shape, not "agent importance"

Output tokens vary 7× across the six agents (287 to 2501). The
distribution maps cleanly to artifact shape, not to anything like
agent priority:

- **High-output (>2000):** Hatter, Caterpillar — each produces
  multiple structured artifacts per turn (six scenarios, one review
  with six findings).
- **Mid-output (~600-700):** Queen, Dormouse — each produces one
  focused artifact-equivalent (Queen's structured concern-with-
  framework-citations; Dormouse's three-hook refusal).
- **Low-output (<400):** Tweedles — each produces one focused set
  of contract questions, terse on purpose.

This is a useful baseline for budgeting. A full-cast run on a similar
scenario should land in roughly the sum of these per-call costs —
~7000 input + ~6500 output + the Cat/Rabbit/Alice/Dodo overhead from
P4 (~3000-7000 input + ~2000-3000 output combined). For Showcase 2
budgeting: ~25k input / ~10k output is a reasonable upper bound on
the substantive turns.

---

## Caveats

- **Single trigger per agent, no inter-agent dynamics.** This sweep
  isolates each voice; it doesn't show how the voices interact when
  on the same bus. That's what analysis 007 (the full-cast race)
  exists to measure.
- **Three triggers were synthesized**, not produced by upstream
  agents. The "Tweedledee implementation" Caterpillar reviewed and
  the "Tweedledum prod deploy" Dormouse signed off on were
  hand-crafted utterances designed to look realistic. A live full-
  cast run produces these for real, and the downstream agents would
  see actual upstream artifacts (with their characteristic patterns)
  rather than synthetic stand-ins. The voices observed here may
  shift slightly on real upstream input.
- **No baseline comparison yet.** As with every prior analysis, the
  generic-prompted-vs-identity-native eval lives in P7. Until then,
  "six distinct voices" is observation, not evidence-against-baseline.
- **Token costs are uncached.** Per the Haiku 4.5 cache investigation
  in analysis 001, our prefix sizes mostly fall below the threshold
  where caching engages on Haiku. The Tweedles' double-loaded
  constitution (own + pair protocol) produces the longest cached
  prefix in the cast (~3500 tokens) and *might* cross the threshold;
  worth checking once we have multi-turn data with the same Tweedle
  agent.
- **Caterpillar reviewed code he couldn't fully see.** The synthesized
  implementation gave him a code snippet and prose description, not
  the actual file contents. He correctly caveated this in every
  finding (*"flagging based on the stated contract; cannot quote
  without seeing the implementation"*) — which is itself §VIII
  *Architectural-drift* discipline (don't pretend to certainty you
  can't have). But the review is more cautious than it would be
  against real code; the verdict in a real scenario might be more
  decisive.

---

## What we'd expect to see strengthen the thesis

- **The full-cast race (analysis 006)** should show the same voice
  distinctions *plus* the inter-agent dynamics — Queen's concerns
  routing to Cat as proposals, Hatter's scenarios picked up by
  Tweedles as implementation constraints, Caterpillar reviews
  triggering Tweedle revisions.
- **The Tweedle dance (analysis 007)** should show the §I argument-
  is-the-work in action — Dee proposing a contract, Dum
  pushing back, Cat arbitrating. The two Tweedles in this sweep
  showed they each ask domain-distinct questions; the dance shows
  what happens when those questions are *to each other*.
- **The synthetic-consensus guard (analysis 008)** should mostly
  *not fire* on real disagreement. The voices observed here suggest
  it shouldn't — these agents naturally diverge. If a real run
  produces a guard alert, it'll be informative either way: either
  real synthetic consensus (which the guard caught), or a false
  positive (which calibrates the threshold).

---

## Notes for follow-up

1. **Tweedles' double-cached prefix is the longest in the cast.** If
   any character organically crosses Haiku's caching threshold under
   normal multi-turn use, it'll be them. Worth instrumenting when we
   have a multi-turn Tweedle scenario.
2. **Dormouse's refusal-of-sign-off is structurally interesting.** He
   chose `concern` rather than the more obvious `observation` of "the
   deploy looks fine pending these metrics," because the absence of
   the metrics IS what he's surfacing. This is the Pair Protocol-style
   "asking is the work" pattern showing up in non-Tweedle territory.
   Worth watching whether other agents use `concern` similarly when
   the situation calls for "I need information before I can produce
   my real artifact."
3. **Queen's response opens with explicit failure-mode-naming.**
   "*I am raising concerns rather than ruling because…*" is unusual —
   most agents just produce the right move without explaining the
   non-move. This may be specific to how queen_of_hearts.md §VIII
   frames Caprice ("if you cannot cite, you cannot rule"); other
   agents whose §VIII guards are less explicit-about-not-doing-X might
   not surface their decision-not-to-act this way. Calibration data
   for P7's identity-native vs generic-baseline eval — the
   "explanation of restraint" might be a measurable signal.
4. **Six scenarios from the Hatter is at the upper end.** Per
   `mad_hatter.md §VIII` *Scenario sprawl* — "a hundred untriaged
   scenarios is worse than ten triaged ones." Six is fine for a
   GDPR + translation + 3-week-deadline scenario like this; but
   a future run that produces 12+ should be examined to see if the
   tail scenarios are genuinely additive or are sprawl.
5. **No agent produced their main artifact "lazily."** Hatter wrote
   six full structured scenarios with all required fields. Caterpillar
   wrote a six-finding review with quotes (caveated where he had to).
   The schemas are doing structural work — the LLM had to produce
   conforming output, and the conforming output is forced to be
   substantive. This is the Pydantic-validated grin equivalents
   paying off across the cast.

---

## Next breath

Analysis 006 — the full-cast race. The same translation-chat
scenario, but with all 10 agents on one bus and able to interact.
The voices distinguished cleanly in isolation; the race shows what
happens when they have to compose into a working team rather than
six independent statements.
