# Analysis 002 — First Tension

**Date:** 2026-05-04
**Phase complete:** P3 (First Tension)
**Cast online:** Cheshire Cat, White Rabbit (2 of 10)
**Model:** `claude-haiku-4-5-20251001`
**Script:** [`scripts/two_agent_demo.py`](../scripts/two_agent_demo.py) with `--compact`

---

## The dance

**Directive published on the bus:**

> Build a translation-integrated chat application. Initial scope: two users in different language groups exchanging short messages with near-real-time translation.

**Cheshire Cat — `question`, 2.34s:**

> Before we shape the architecture, I need to understand what 'translation' means in this context. Are we translating user input before storage, or storing raw messages and translating on retrieval? Are we detecting language automatically, or does each user declare their language? And — this matters — are we building toward a future where three or four language groups coexist, or is two-language always the scope?

**White Rabbit — `question`, 2.68s:**

> Before I decompose this, I need the shape of the work from Alice: What are the acceptance criteria for 'near-real-time translation'? (Latency budget? Accuracy floor? Which language pairs are v1?) And what counts as 'short messages'? These constraints will determine whether we can use a third-party translation API (2–3 day path) or whether we need to build abstraction layers that add a week. Let me know when you have those, and I'll sketch the ticket structure and dependencies.

**No artifacts produced.** No ADRs, no tickets. Both agents refused to commit before the constraints they each care about were settled.

**Tokens:** Cat input 3175, Rabbit input 41 (more on this below).

---

## What changed in compaction

Both agents reflected on the thread and produced semantic + relational updates. Selected highlights:

**Cat's semantic memory** wrote two topics:
- `translation-architecture-decision-space` — three open questions (timing, detection, scaling horizon) with explicit implications per choice.
- `near-real-time-translation-requirements` — laid out the latency budget bands and what each implies for system coupling.

**Cat's relational notes — `dodo`:**

> Dodo issued a clean, bounded directive. The scope (two users, two language groups, short messages, near-real-time) is concrete. The gap is not in the directive but in the architectural follow-on questions it raises... Cheshire's reframe is appropriately calibrated: not asking Dodo to answer these (they may not be Dodo's to answer), but making visible that *someone* needs to answer them...

**Rabbit's semantic memory** wrote three topics:
- `translation-chat-domain` — three architectural axes mapped to dependency-graph implications and ship-time differences ("`declare language` + `pre-storage translation` + `two-language only` can use third-party APIs and ship in ~2 weeks. An `automatic detection` + `post-retrieval translation` + `multi-language ready` approach extends to 4+ weeks").
- `latency-and-accuracy-constraints` — quantified bands (>500ms is noticeable in conversational flow), implications for build-vs-buy.
- `short-messages-scope` — "short" needs disambiguation; segmentation strategy implications.

**Rabbit's relational notes — `cheshire_cat`:**

> The Cat's question is the right shape: he refused to propose architecture until the problem was constrained... He is not asking for more information out of caution; he is refusing to commit to a direction until direction is possible. This is the Cat at his best...

**Rabbit's relational notes — `alice`** (Alice did not appear in the thread):

> Alice has not yet appeared. The work cannot be ticketed until she does — specifically, until she produces acceptance criteria that constrain latency, accuracy, and language scope. The Rabbit's move was correct: surface that her input is blocking sequence, do not guess at her constraints. When she appears, she will need to know that the Cat's three axes are the questions her criteria must answer.

---

## What it tells us about the thesis

After P3, n=2 characters, single trigger, single dance. Still premature for compounding-curve claims (that's P7). But the move-shapes the thesis predicts are present and observable:

### 1. Same trigger, different domain framings

The Cat asked about **translation timing, language detection, scaling horizon** — architectural axes whose answers reshape the system. The Rabbit asked about **acceptance criteria, latency budget, language pairs, "short" definition** — scope and dependency questions whose answers reshape the timeline. They processed the *same directive* and produced *different question sets* because their constitutional concerns differ. Neither set is a watered-down version of the other; they're complementary.

A generic "two helpful AI agents" baseline would tend toward overlap — either both asking the same set of questions (because the LLM's helpful-disposition is a strong attractor), or one being silent because the other "covered it." The asymmetry here is the substrate enforcing a separation that the constitutions describe.

### 2. Domain boundaries held without intervention

- Cat issued no tickets. No ADR either, but only because nothing was decided yet — the Cat's constitution explicitly forbids fabricating certainty (§VIII), and silence-to-act was the right move.
- Rabbit issued no proposals. He declined to ticket, which is itself a Rabbit move — the burndown stays honest if you don't pre-load it with work that hasn't been decided.

No orchestrator told either agent what their lane was. The constitutions did the work.

### 3. The Rabbit named an absent voice

> "Alice has not yet appeared. The work cannot be ticketed until she does..."

This is unprompted system-awareness. The Rabbit's relational note about Alice exists *despite Alice not being in the thread*. The Rabbit knows who's missing, why their absence is blocking, and what they'll need to deliver when they arrive. That's the kind of inter-agent awareness the spec calls for — relational memory is doing structural, not just personal, work.

### 4. Compaction produced real wisdom from a small interaction

Both agents distilled topic-level semantic notes after a single Q-and-Q exchange. The notes aren't generic "translation chat is hard"; they're the specific architectural and scope axes that would shape decisions in the next thread. If a follow-up directive arrived tomorrow with answers to either agent's questions, the relevant agent's compose_context would include these notes — and the agent could pick up where they left off rather than re-asking.

This is the core mechanism the thesis depends on. Whether it actually compounds across many threads is what P7's eval harness measures. But the mechanism is observably present after one exchange.

---

## Caveats

- **n=2 characters, single dance.** The full cast lands in P5; the multi-character signature only really materializes there.
- **The dance was synchronous and concurrent.** Both agents engaged with the directive simultaneously. We didn't yet observe sequential coordination (Cat answers, then Rabbit reads Cat's proposal, then Rabbit decomposes). That dance shape requires either ordered triggers or an orchestrator (P4 — the Dodo).
- **No baseline comparison yet.** Same as analysis 001. P7 closes that gap.
- **Compaction was manually triggered.** No mechanism yet to know "the thread has settled, time to compact." The Dodo's quiescence detection (P4) is what makes compaction automatic.
- **Token-cost anomaly worth investigating.** The Rabbit's reported `input_tokens=41` is implausibly low — the constitution alone is ~2000+ tokens. Either the SDK reported only a fraction of the actual usage on a multi-call deliberation, or something in our prompt construction collapsed for the Rabbit specifically. Cat's 3175 looks right. Adding to the follow-up list — same kind of telemetry concern that surfaced in 001 around caching.
- **The Cat's questions skipped one premise of his own constitution.** Constitution §VIII names "false certainty" as a failure mode; this run honored that. But §VIII also names "speaking to be present" as a failure mode, and we don't yet know whether the Cat would have stayed silent on a directive that didn't implicate architecture. Worth a future test: a non-architectural directive, see if the Cat correctly says nothing.

---

## What we'd expect to see strengthen the thesis

Carrying forward the predictions from analysis 001 with refinements:

- **P4 (Dodo + quiescence):** A second turn arrives (e.g., Alice appears with acceptance criteria). The Dodo notices that the previous thread settled because the agents went quiet, not because anyone said "we're done." Compaction fires automatically.
- **P4 (sequential coordination):** When Alice's criteria arrive, the Cat's response now references the open questions from his last compaction; the Rabbit's response now references the dependency observations from his last compaction. The relational memory does observable work.
- **P5 (full cast):** The Hatter sees the synchronous-vs-async question and immediately writes test scenarios for the failure modes ("what happens if translation provider returns 500 mid-conversation?"). The Queen sees "translation provider integration" and rules on data residency. The Tweedles see ticket dependencies and start arguing about contract shapes. Each character's response signature differs in kind from the others.
- **P6 (multi-session):** Same project run twice. Second run, agents reference the first run's compactions in their responses. Time-to-architectural-settlement drops because the first-run compactions become starting points, not blank slates.
- **P7 (evals):** Generic-prompted baselines do *not* show this kind of compounding. Identity-native does. The curve becomes the evidence.

---

## Notes for follow-up

1. **Investigate the Rabbit `input_tokens=41` anomaly.** Most likely cause: the demo's `on_token_usage` hook only captures the most recent call, and the Rabbit's full-prompt deliberation may have happened in a call that was overwritten. Verify by accumulating instead of last-write-wins, or by adding a per-call sequence number to the log.
2. **The Cat noted `dodo` in relational memory but Dodo isn't really an agent the Cat works with directly** — Dodo is the orchestrator, more like a pipe than a colleague. Worth deciding: should the Cat keep relational notes about the Dodo, or are those better captured as semantic notes about "how directives arrive"? Per-character compaction protocols (T16's hook) could refine this once we have the Dodo (P4).
3. **The Rabbit's `alice` note is forward-pointing** — it's about an agent who *will* appear, not one who has. That's useful. But the relational store is currently keyed by "people I've worked with." Worth deciding whether to also support "people I expect to need." For now the Rabbit just put it in the alice file anyway, so the ergonomics happen to work.
4. **Compaction does not happen automatically.** The Dodo's quiescence detection (P4) is what triggers it. Until then, callers (tests, scripts) must invoke `compact()` themselves.

---

## Next breath

P4 (First Race) — Dodo orchestrator + quiescence + conflict resolution + Showcase 1 (the `/health` endpoint). The first time the system runs end-to-end on a directive without humans in the loop. Multi-agent coordination becomes legible — not as concurrent monologues, but as a thread that reaches "done" because the agents stop talking.
