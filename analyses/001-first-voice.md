# Analysis 001 — First Voice

**Date:** 2026-05-04
**Phase complete:** P2 (First Voice)
**Cast online:** Cheshire Cat (1 of 10)
**Model:** `claude-haiku-4-5-20251001`
**Script:** [`scripts/cat_demo.py`](../scripts/cat_demo.py)

---

## Run

**Directive published on the bus:**

> Build a translation-integrated chat application. Initial scope: two users in different language groups exchanging short messages with near-real-time translation.

**Cat response — `question`, 3.22s end-to-end:**

> Before we shape the architecture, I need to understand what 'near-real-time' means in your operational context. Is this a constraint imposed by user experience (people get frustrated if translation takes more than X milliseconds), or is it a constraint imposed by the translation service itself (the API has a latency budget), or both? And when translation fails or produces ambiguous output, what is the acceptable fallback — show the original, show a placeholder, block the message, or something else? The answers to these questions will determine whether we build a synchronous-first architecture or whether we can afford to queue and batch translations asynchronously. They also determine our error handling surface, which is significant.

**Artifacts:** none.

**Tokens:** 3175 input / 169 output / cache_creation=0 / cache_read=0.

---

## What the Cat did

1. **Refused to propose.** No ADR was produced. The directive was vague on
   load-bearing dimensions and the Cat declined to fabricate certainty —
   precisely the failure mode his constitution §VIII names ("False
   certainty… committing to architectural decisions that should be
   deferred until more is known").

2. **Asked two reframing questions.** Both surface unexamined premises in
   the directive:
   - *What does "near-real-time" mean — UX-budget or API-budget?* This
     is the question the Rabbit's eventual ticket would have papered over
     with an arbitrary number, and the Cat is buying back the decision.
   - *What's the acceptable failure mode for translation?* This is the
     error-handling surface implied but not stated by the directive.

3. **Named the architectural fork explicitly.** "Synchronous-first
   architecture" vs "queue and batch translations asynchronously" — the
   answer to the first question collapses the choice. This is the
   characteristic move §I describes: surface the actual decision so
   whoever owns it can make it well.

4. **Held the seam.** "They also determine our error handling surface,
   which is significant." The Cat noticed that two questions touch the
   same load-bearing surface — the seam between application logic and
   translation provider — and named it.

5. **Stayed silent on what wasn't asked.** No comments on the user model,
   the storage layer, the deployment topology, the roadmap. The Cat
   appeared, asked his question, and stopped. The "you appear and
   disappear" rhythm (§I) shows up cleanly even in n=1.

---

## What this tells us about the thesis

The Temple-Codex thesis: stable self-models with constitutive values
produce better outcomes than generic systems with externally imposed
constraints. After P2, n=1 character, single trigger. Premature to claim
much. But this run shows the **shape** the thesis predicts:

- **The Cat sounds like the Cat.** Measured, slightly oblique sentences.
  Precise vocabulary ("synchronous-first architecture", "error handling
  surface"). No marketing language. Compare to a generic "act like a
  thoughtful architect" prompt — what we'd typically get is a list of
  features the agent thinks an architect would want, not a question that
  refuses the premise.
- **The constitution did the work.** Nowhere in the trigger or protocol
  did we tell the Cat to ask reframing questions or to refuse to commit.
  Those moves came from §I and §VIII of the constitution being part of
  the prompt prefix — *as the agent's identity, not as a one-off
  instruction*.
- **Speech-act distribution is already legible.** Cat issues `question`
  here. He could have issued `proposal` (with a hedged ADR), and a
  generic system probably would have. The choice to answer with a
  question instead of a proposal is the kind of thing the eval harness
  in P7 should be measuring across many runs.

Single data point. Don't over-read. But the move-shape matches the
prediction.

---

## Caveats

- **n=1**, single character, single trigger. This isn't evidence; it's
  one observation. The behavioral signature emerges from many runs.
- **No baseline comparison yet.** We can describe what the Cat did but
  can't yet contrast it with what a generic-prompted Claude would have
  done given the same directive. The eval harness in P7 closes that gap.
- **Cache stats look wrong.** Both `cache_creation_input_tokens` and
  `cache_read_input_tokens` returned 0 despite 3175 input tokens
  (well over Haiku's 2048-token cache threshold) and explicit
  `cache_control: ephemeral` markers on the constitution + protocol
  blocks. Either the API is silently dropping the cache marker, the
  marker isn't being applied correctly, or the SDK is returning 0 for
  cache_creation on the first write. **Worth investigating before P3.**
  If caching isn't actually working, the per-turn cost is ~3000 input
  tokens × 10 agents × N turns — significant.
- **Cat had no prior thread history** (clean memory). The episodic
  layer is in place but didn't influence this turn. P3 will exercise it.
- **The directive was deliberately vague.** A concrete, well-scoped
  directive might have produced a `proposal` instead of a `question`.
  We haven't tested the Cat against a directive that *should* commit to
  architecture immediately.

---

## What we'd expect to see strengthen the thesis

Each phase has a falsifiable prediction. If these don't hold, the
thesis is in trouble.

- **P3 (Cat + Rabbit):** When the Rabbit asks the Cat for an estimate,
  the Cat redirects rather than committing — per §VII. Role boundary
  visible without orchestration intervention.
- **P3 (relational memory):** After the Cat and Rabbit have interacted
  on a thread, both agents' relational notes about each other update
  in ways that show in their next-turn behavior.
- **P4 (Dodo quiescence):** A thread reaches "done" because the Cat
  goes silent (§VI: "your silence after done is itself information"),
  not because the Dodo orders him to stop.
- **P5 (full cast):** Speech-act distributions per character form
  visibly distinct signatures over the same set of threads. The Hatter
  issues `test_scenario` characteristically; the Cat doesn't. The Queen
  issues `ruling`; nobody else does.
- **P6 (multi-session):** The same showcase run twice shows the second
  run benefiting from the first — agents reference earlier decisions,
  shorter time to architectural settlement.
- **P7 (evals):** The compounding curve materializes. Generic-prompted
  agents perform stably; identity-native agents improve across runs.
  This is the legibility-of-value mitigation from §11 of the spec — and
  the closest thing to evidence the framework will produce.

---

## Notes for follow-up

1. ~~**Investigate the cache stats.**~~ **Resolved (same day) — see "Update: cache investigation" below.**
2. **Add a "verbose" mode to the demo** that prints the assembled prompt
   so the cache-marker placement is visible at run time.
3. **Try a directive that should commit to architecture** (e.g., "Add a
   /health endpoint to a Phoenix app" — the P4 showcase) and see if the
   Cat issues a `proposal` rather than a `question`.

---

## Update: cache investigation

Ran an empirical bisection against the live Anthropic API to figure out
why cache stats came back zero. Findings:

**Haiku 4.5 has two distinct cache-eligibility thresholds, both higher
than I'd assumed (and higher than Sonnet's):**

| Cached prefix size | Behavior |
|---|---|
| < ~4096 tokens | No caching at all. `cache_control` markers ignored. |
| ~4096–7000 tokens | **Pessimal.** Cache *writes* (1.25× cost) but never *reads* — pay the write tax with no benefit. |
| > ~7000 tokens | Caching engages fully — write once, then 0.10× reads. |

**Sonnet 4.6 by contrast** caches at ~2000 tokens — well below our
current ~3100-token cached prefix (constitution + protocol). At our
sizes, Sonnet caches cleanly; Haiku ignores the markers entirely.

**Decision:** stay on Haiku. Per-token Haiku is ~3× cheaper than Sonnet.
Whether uncached Haiku beats cached Sonnet depends on real per-directive
token consumption, and we don't have that data yet. By P3+ the cached
prefix grows naturally (relationships layer, possibly a shared
"framework primer"); we may cross the Haiku threshold organically. Real
cost analysis lands as roadmap item `460b5ea9`, to run during P6
showcases when there's a workflow to measure.

**What this changes for the thesis observation:** nothing direct. But it
revises the operational intuition — for now, every Cat turn pays full
~3000 input tokens. Across the full cast (P5+), that adds up. Worth
keeping in view as we instrument.

---

## Next breath

P3 (First Tension) — White Rabbit + Cat interaction. Two voices on one
bus, semantic + relational memory layers come online, compaction-as-
agent-behavior arrives. First chance to observe identity holding under
inter-agent friction.
