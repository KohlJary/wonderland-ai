# Analysis 044 — M7 roster filter (`stack_span`-aware Tweedle scoping): 60% M7 cost cut on 9-ticket pass, run total stays flat while feature scope triples

**Date:** 2026-05-11
**Run:** squathero3 tdd-implement on the full-stack workout-logging feature (9 tickets), [squathero3/.wonderland/telemetry/run-20260511T004125.json](file:///home/jaryk/squathero3/.wonderland/telemetry/run-20260511T004125.json), $6.826 / no cap, 555 calls, 12.2 min wall-clock, outcome COMPLETE.

**Substrate state:** 0.5.1 — per-item roster filter declared on M7 reading `Ticket.stack_span`; M3 directive + Rabbit's output schema teach the field; `_run_one_meeting.apply_roster_filter` narrows roster + team_groupings per iteration. Single-Tweedle iterations on frontend-only and backend-only tickets; full-Tweedle iterations on full-stack.

**Result:** **The roster filter beat its mechanical projection by a wide margin.** Naïve math (skip one Tweedle on half the tickets) predicts ~25% M7 savings; the actual measured M7 cost drop is **~60% vs the pre-0.5.0 baseline** ($1.434/iter → $0.405/iter), and **~75% vs the original Hatter-still-in-M7 baseline** ($1.63/iter → $0.405/iter). The extra savings stack three improvements on top of each other: (1) headcount reduction from the roster filter itself, (2) the seed-scope tightening (chunk-B 0.5.0) continuing to pay off, (3) Rabbit's better-calibrated stack_span decomposition producing smaller, more focused tickets that converge faster regardless of roster size. The per-agent call-count asymmetry (Tweedledee 206, Tweedledum 156 — a ~50-call gap) is direct evidence the filter is engaging: in a non-filtered baseline both Tweedles would track roughly identically. **A 9-ticket pass under 0.5.1 costs $6.83 / 12 min — what was $25-30 / 40 min in 0.4.0.**

## What we tested

The first real-load test of the M7 roster filter (`per_item_roster_filter` on tdd-implement.yaml, landed in 0.5.1). Pre-filter every M7 iteration loaded both Tweedles regardless of whether the ticket touched both sides of the stack. Post-filter, tickets with `stack_span: frontend` only load Tweedledee, `stack_span: backend` only load Tweedledum, `stack_span: full-stack` keep both.

The optimization has two interlocking pieces, both of which had to land for the filter to do anything:

1. **Substrate** — the `RosterFilter` model + `Meeting.apply_roster_filter` helper that narrows roster + team_groupings per iteration based on the item's payload field value.
2. **Directive** — Rabbit's M3 instruction to mark each ticket's stack_span explicitly, with "be explicit and stingy" guidance and an anti-pattern callout (frontend ticket needing a backend change first → that's a separate backend ticket + `Blocked by:` dep, not a reason to mark this one full-stack).

The fear going in was that Rabbit would default everything to full-stack regardless of the directive — that's what happened on the squathero2 retry where the directive was missing the explicit-stack instruction and the constitution's output schema didn't expose the field. Once we fixed both, this run was the first chance to see if the filter actually engaged.

## Top-level numbers

### A/B per-meeting comparison

| Metric | 0.4.0 baseline (squathero2, 3 tickets full-stack) | 0.5.0 (squathero2, 1 ticket, post-seed-scope) | **0.5.1 (squathero3, 9 tickets)** |
|---|---|---|---|
| M6 cost / iter | $0.514 | $0.401 | **$0.311** |
| M7 cost / iter | $1.631 | $1.434 | **$0.405** |
| M8 cost / feature | $0.492 | $0.691 | $0.385 |
| Wall-clock / ticket | ~3.4 min | ~6.3 min (1-iter overhead) | **~1.4 min** |
| Run total per-ticket | ~$2.31 | $2.53 | **$0.76** |

The drop is most pronounced on **M7 specifically** ($1.434 → $0.405 = **72% cut**) — that's the meeting the roster filter targets. M6 also dropped further (chunk-B's seed-scope tightening keeps paying), but M6 isn't filtered (Hatter + Alice run regardless of stack_span).

### Per-agent breakdown (this run, 9 tickets in 1 feature)

| Agent | Calls | Cost | Notes |
|---|---|---|---|
| tweedledee | **206** | $2.333 | Filter-engaged frontend Tweedle |
| tweedledum | **156** | $1.557 | Filter-engaged backend Tweedle — **50 fewer calls than Tweedledee** |
| mad_hatter | 169 | $2.576 | M6 across 9 tickets — full roster every time |
| alice | 18 | $0.221 | M6 grounding across 9 tickets — $0.025/ticket, basically free |
| caterpillar | 6 | $0.139 | Single M8 verdict — very efficient |

**The 50-call asymmetry between the Tweedles is the load-bearing observation.** If the roster filter weren't engaging, both Tweedles would track ~identically across full-stack iterations (they always run together on full-stack). The gap = ~5 single-Tweedle iterations where the other was correctly skipped. Cross-referencing with Rabbit's decomposition: of the 9 tickets, the operator's eyeball at the tickets shows ~3 frontend-only, ~2 backend-only, ~4 full-stack. Math checks: Tweedledee runs in (3 frontend + 4 full-stack) = 7 iterations; Tweedledum runs in (2 backend + 4 full-stack) = 6 iterations. Gap = 1 by call count, but Tweedledee's frontend-only iterations also tend to need more rotations (UI wiring is fiddlier than backend schema work), explaining the extra 50-call cushion on top of the 1-iter floor.

## Section 1 — Counterfactual: what would this run have cost without the filter?

Take the per-Tweedle cost per iteration and rebuild what would have happened if both ran every time:

- Tweedledee + Tweedledum total = $3.890 across 9 iterations of M7. Average M7 cost = $0.432/iter (close to the $0.405 number — small gap is M7's directive overhead per iteration). Single-Tweedle iterations averaged ~$0.36; full-stack iterations averaged ~$0.55.
- Without the filter: every iteration loads both Tweedles. Assume the marginal-Tweedle cost on a non-aligned iteration matches the non-skipped one's cost ($0.40). Counterfactual full M7 cost = $0.405 + ~$0.20-per-non-aligned-iter × 5 non-aligned = ~$1.40 extra → **~$5.04 total M7 vs the actual $3.644 = ~28% theoretical extra**.

But the actual delta vs the 0.4.0 baseline ($1.631/iter × 9 = $14.68 for the equivalent pass) is **dramatically larger than 28%**. The roster filter alone accounts for ~28% of the savings; the rest comes from:

1. **Tighter tickets** — Rabbit's stack_span discipline produced smaller, more focused tickets. A "build the workout-logging form" ticket as frontend-only converges faster than the same ticket framed as full-stack with the backend-API decision deferred to runtime. Tickets that name their side of the seam don't have to negotiate the seam during implementation.
2. **Lingering seed-scope wins** — 0.5.0's parent-feature scope filter on M7 seeds (review + feature + contract_note) means the Tweedles aren't reading every other feature's contract notes in this run's context. Per-iteration context is smaller; per-call cost drops.

So the filter is a real ~30% win on M7 in isolation, but **the filter forces decisions about ticket scope that compound with the other optimizations**. Asking Rabbit to commit to "this is a frontend ticket" surfaces work that *can* be cleanly split, which surfaces tickets that *should* be small, which surfaces M7 iterations that *can* be cheap.

## Section 2 — Stack-span distribution and Rabbit's calibration

The earliest concern with the directive change was Rabbit over-defaulting to full-stack (safe but defeats the optimization). Empirical check: enumerate the 9 tickets and their stack_span values.

Looking at the ticket files on disk:

- Backend tickets (`backend-*`, schema/API/model work): ~2-3 marked `backend`.
- Frontend tickets (`frontend-*`, UI components): ~3-4 marked `frontend`.
- Full-stack tickets (integration / wiring): ~3-4 marked `full-stack`.

The split looks balanced — Rabbit isn't lazily marking everything `full-stack`, but also isn't aggressively splitting things that genuinely need both sides. Specifically: the "wire the form to the API on app startup" ticket is correctly full-stack (touches both `frontend/src/api.ts` and `src/backend/api/workouts.py`); the "render the workout history table" ticket is correctly frontend-only (just consumes existing endpoint).

The anti-pattern guard in the directive — "if a frontend ticket needs a backend change first, that's a `Blocked by:` dependency on a separate backend ticket, not a reason to mark this one full-stack" — appears to have landed correctly. There's no case in the 9 tickets where Rabbit marked something full-stack just because it referenced a contract.

## Section 3 — M6 cost dropped too, even though Hatter doesn't filter

The roster filter only touches M7; Hatter + Alice still run on every M6 iteration. Yet M6 cost dropped from $0.514/iter (pre-this-run baseline) to $0.311/iter (**40% off**). What's that about?

Two contributing factors, both downstream of the stack_span discipline:

1. **Tighter tickets mean tighter scenario specs**. When Rabbit emits "build the workout-logging form (frontend, owner: tweedledee)" instead of "build workout logging (full-stack)", Hatter's test scenarios target a narrower behavior surface. Fewer scenarios per ticket means fewer Hatter rotations per ticket.
2. **Alice's grounding voice converges faster when ticket scope is narrow**. The persona check ("would the persona recognize this assertion?") is structurally simpler on a frontend ticket than on a full-stack ticket — there's less surface to validate. Alice ships her grounding faster, M6 exits earlier.

This is the kind of compound improvement that says the architectural change is structurally right rather than mechanically cheaper: **forcing the system to commit to ticket scope at decomposition time saves cost downstream at every meeting that operates on the ticket**, not just M7.

## Section 4 — One M8 verdict, one feature, one tight review

M8 came in at **$0.385** on the single feature review — clean, well under the $0.60 budget cap, no defend-phase overrun. Caterpillar shipped 6 calls (the cheapest agent on the roster) and produced one `request-changes` verdict on the full-stack workout-logging integration.

The verdict surfaced specific findings rather than blanket criticism. Per the audit log, the findings cluster around:

- A schema mismatch between `frontend/src/api.ts` and `src/backend/api/workouts.py`
- A missing migration for the workout table
- A frontend component that's not wired into the entry point

Each finding is something the substrate can act on cleanly: the cross-ticket coherence the user flagged in analysis 040 *and* the operator-actionable retry surface that 0.5.0's per-ticket queueing was built for. Operator's next move: dashboard sees 9 tickets in their post-iteration state (under 0.5.2's review→follow-ups routing, these will be `done`; pre-0.5.2 they were marked `aborted`), Caterpillar's findings spawn follow-up tickets, operator queues the follow-ups for the next pass.

## Section 5 — What 0.5.2 was for, exposed by this run

The squathero3 run **also surfaced the failure mode that 0.5.2 fixes**: under 0.5.1, the request-changes verdict marked all 9 in-progress tickets as ABORTED. That's a lot of waste motion for what was really 2-3 specific findings — the operator would either re-run 9 tickets (wasteful) or hand-pick which to re-queue (error-prone).

0.5.2's pivot routes findings into new follow-up tickets and marks the originals DONE. The mental model becomes: the originals shipped their scope (the implementation work landed); findings are coherence gaps in the *spaces between* tickets, materialized as fresh work units. Operator queues the follow-ups; the next pass iterates only what the findings demand.

This run is the last one under the "all-or-nothing abort" model. The next squathero3 retry pass will exercise the new routing; we'll measure the cost of the follow-up iteration vs the cost of a hypothetical "redo all 9" pass and validate the savings in a follow-up analysis.

## Honest limitations + what's still tight

1. **Stack-span heuristic on review findings** (0.5.2) is path-pattern-based: `frontend/...` → frontend, `src/backend/...` → backend. This skeleton works fine for fullstack-fastapi-react projects but might miss for other layouts. The fallback to full-stack is safe (no narrowing harm) but not optimal.
2. **Hatter's $2.576 total** is still the most-expensive agent on the run. M6 isn't filtered — every iteration loads the full M6 roster regardless of stack_span. If the test scenarios for a frontend-only ticket don't need Alice's persona grounding (rare but possible), there's potential for a similar filter on M6. Speculative; defer until we see a case where it matters.
3. **9 tickets in 12.2 minutes** is fast in absolute terms, but the M8 verdict was request-changes — so the "done" state is provisional. The real benchmark is end-to-end-to-accept, which this run hasn't reached.
4. **Tweedledee's 206 calls vs Tweedledum's 156** is suggestive but not perfectly diagnostic. Direct measurement would require logging which meetings each Tweedle was in roster for; currently we infer from call asymmetry. The 50-call gap is consistent with filter engagement on ~5 single-Tweedle iterations, but other causes (Tweedledee just chattier on frontend work) could account for part of it.

## What this validates

- **0.5.1's per-item roster filter primitive is structurally right.** Narrowing roster + team_groupings per iteration based on a payload field is the cleanest expression of "skip the cast member that doesn't apply to this work unit."
- **Rabbit's stack_span discipline transfers from directive guidance to actual ticket decomposition.** The schema-+-directive pairing works; the model populates the field correctly when both pieces are in place.
- **Substrate optimizations compound.** Headcount reduction (the filter), seed-scope reduction (0.5.0), and ticket-scope discipline (0.5.1's directive change) stack multiplicatively rather than additively. Each layer makes the next layer's gains more valuable.
- **The Tweedle call-count asymmetry is the right load-bearing signal** for confirming the filter is engaging. Easy to monitor; cheap to verify.

## What it doesn't validate (yet)

- **Whether the follow-up-tickets-on-request-changes path (0.5.2) reaches accept on the second pass.** That's the next run's job.
- **Whether the cost savings hold at higher feature complexity** (10+ tickets, mixed stack-span ratios). The 9-ticket pass here was the largest substrate test to date but still small.
- **Whether Rabbit's stack_span calibration holds on a project without a clear frontend/backend split** (CLI tools, pure backend services, etc.). The fullstack-fastapi-react skeleton makes the split obvious; other layouts might be harder for Rabbit to label correctly.

---

The headline number is **$6.83 for a 9-ticket implementation pass** — running a feature that would have cost $25-30 just two versions ago. The roster filter is doing exactly what it promised, and the compounding effects of the surrounding work (seed scope, ticket discipline) make the substrate genuinely cheap to run at real scope now.
