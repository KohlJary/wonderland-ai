# 035 — ldr-ophanic: Substrate Fixes, the Diagram Arc, and What the Failures Taught Us

**Pilot:** ldr-ophanic (a partner-dashboard app: auth + live time card + weather card + news card)
**Window:** 2026-06-16 → 2026-06-19
**Substrate:** Haiku-only, fixed-substrate (the P21 diagram build-tracker + this cycle's tool-loop fixes)
**Outcome:** 4 working milestones delivered (M1–M4), M5 designed; one correctness bug propagated across two milestones; several paper-grade findings, most handed to us by the failures rather than the successes.

This analysis is unusual: the headline isn't "the run went well" (it did, mostly). It's that running the substrate *honestly* — fixing it at the substrate level and refusing to hand-patch its output — surfaced findings you can't manufacture. The bugs were more instructive than the builds.

---

## I. Run-level facts

| | Value |
|---|---|
| Total cost | **$44.06** across 27 runs |
| — implement | $29.52 (12 runs) |
| — design | $13.23 (10 runs — ~7 were fix-validation re-runs) |
| — planning | $0.97 (2 runs) |
| Milestones delivered | M1 auth foundation, M2 time card, M3 weather card, M4 news card (first pass) |
| Milestones designed not built | M5 graceful degradation |
| $/milestone (raw) | ~$11.02 |
| $/milestone (implement only) | **$7.38** |

The app: FastAPI + SQLite backend, React/Vite/TS frontend, real external API integration (Open-Meteo + RSS), hourly background polling with a SQLite cache, timezone resolution, signed-cookie auth, and a graceful-degradation error taxonomy.

---

## II. The engineering: tool-loop exhaustion was one bug wearing three masks

The starting symptom was narrow — "the M2 frontend (a `TimeCard`) never builds." It unified with two long-standing complaints into a single root cause.

**Root cause:** `_complete_with_tools` ran reads and writes against one shared iteration cap (20). An agent reading deep — Tweedledee tracing a data-flow chain, or Caterpillar reading a growing file tree at review time — exhausted the cap **on reads alone**, hit `return ""`, and the empty string was parsed downstream as *silence*. Silence auto-approves at M8. So:
- **The frontend Tweedle that never builds** = read-exhausts before it writes.
- **Caterpillar "goes quieter the further along you are"** = same loop, and it scales with project size (more files → more reads → exhaust sooner). The "worse with scope" pattern was the tell.

**Telemetry receipt (pre-fix baseline):** on obol-260522-1, **~37% of implement deliberations edited code then PASSED without emitting an artifact**, ~83% of those carrying the ≥17-iteration exhaustion signature. (Crucial measurement caveat: counting edits requires the *full* edit set — Tweedles use `str_replace` ~10× more than `write_file`; a write_file-only count is blind to ~90% of edits and flips the result.)

**Fixes shipped:**
1. **Split-budget tool loop** — reads get a separate generous budget (30), writes/checks a tight convergence budget (15), plus a convergence nudge and an exhaustion-recovery forcing call. Exploration can no longer starve the turns needed to commit.
2. **Per-loop read cache, invalidate-on-write** — identical reads are free and don't spend budget, so the read budget tracks *unique* surface area, not total reads. (Targets Tweedles, which re-read dependency chains; Caterpillar's reads were ~all unique, so the split budget is *its* fix — the two fixes target different agents.)
3. **(b)+(d) hollow-build gate** — even when Caterpillar is silenced and auto-approve fires, the substrate cross-checks the wiring diff; a UI node with a done ticket but orphaned/missing code blocks the auto-approve and synthesizes a fix ticket.
4. **Tombstone-on-prune** — pruning a ticket deleted its file but never updated the append-only ledger, leaving phantom `queued` tickets (state without artifact). Prune now records an `aborted` tombstone, plus a sweep that heals existing phantoms.

**Result on the fixed substrate:** implement ran at **0% edited-but-passed, 0% exhaustion across M2/M3/M4** (7 deliberations on the fixed window for M2, 3 for M4 — all ACT). Caterpillar review silence dropped from majority (on big pre-fix projects) to 1-of-6 in the fixed window. The fix isn't a one-milestone fluke; it held across three.

---

## III. The diagram arc (P21) validated end-to-end

The build-tracker closed the loop on a real run: **drawn** at planning (`dashboard-page.oph` etc.) → **linked** to tickets at design (21 node↔ticket links) → **built-against** at implementation (Tweedledee read `dashboard-page.oph` 3× while building) → **verified** at review (Caterpillar ran `verify_wiring` 2×).

The diagram did load-bearing work *both directions*: on the pre-fix run it **caught** the TimeCard as a hollow build (orphaned — marked done, absent from code); on the fixed run it **confirmed** the real build (wired). Same tool catching the lie before and certifying the truth after. This is the failure class — "ships as a file, never wired into the running app" — made structurally catchable.

---

## IV. What the failures taught us (the paper-grade part)

### 1. Review can be anchored by confident-but-wrong comments
M3's weather card shipped a staleness bug: `is_stale = now - cached_at`, with `cached_at` frozen at row creation, so a cache refreshed hourly reports stale after 90 min of *row life* regardless of refreshes (it measures row age, not data age; the correct key is `last_successful_fetch_at`). Caterpillar **caught it** on the first review. The follow-up "fix" doubled down the wrong way — froze `cached_at` and added emphatic justification (`# deliberate and load-bearing`, `# correctly identifies data older than 90min`). The re-review **ACCEPTED it.** The review verified *"does the code match its stated invariant?"* (yes) instead of *"is the staleness logic correct?"* (no). The loop converged on **confidently wrong**, anchored by the implementer's own assertive comments.

### 2. A certified bug propagates as a template
We deliberately did **not** hand-patch the weather bug (see §V). M4's news card — same card pattern — then copied the weather card's broken staleness logic **verbatim**: `cache_age = now - news_cache.cached_at`, the identical `"cached_at is immutable"` comment, `last_successful_fetch_at` present but unused. The substrate didn't learn from M3; it propagated the failure. **The cost of a missed/false-accepted review finding is not one bug — it's one bug × every sibling that pattern-matches to it.** This is the dark mirror of quality-cost coupling: clean patterns compound down, a certified-wrong pattern compounds up. And it vindicates the don't-patch decision — patching weather would have propagated the *correct* template and hidden the propagation mechanism entirely.

### 3. The ledger lies on follow-up runs (false-negative)
Worked tickets stay `queued` (never marked done) on a follow-up run where Caterpillar's re-review has no ticket-worthy findings — the M8 *accept* path lacks the done-marking step the request-changes path has. Long-standing. Consequence: ticket state is unreliable on follow-ups; **trust the code, not the ledger.** This is the same state-vs-ground-truth divergence as the phantom-ticket bug, just inverted (artifact says done, ledger says queued).

### A through-line: trust the artifact
Phantom tickets (state says live, artifact gone), stuck-queued tickets (artifact done, state queued), the false-accepted fix (verdict says fixed, code broken), str_replace blindness (telemetry undercounts the real edits). Every hard call this run came down to **the artifact/code is ground truth — not the ledger, not the verdict, not the convenience metric.** The substrate's posture (typed durable artifacts as the source of truth) is precisely what made its own bugs diagnosable.

---

## V. Methodological stance: don't patch the output

When substrate-generated code had a bug the substrate should have caught, we did **not** hand-fix it. The broken `cached_at` staleness was left in place as an honest capability-boundary receipt. Rationale: a hand-patch makes the output look clean while hiding exactly where the substrate's capability ends, and converts a real limitation into an invisible one. The legitimate lever is the substrate (the review capability), not the generated code. (Distinct from *unwedging* — re-queuing tickets, sweeping phantoms, resetting state — which clears the runway for the substrate to act rather than doing its job for it.) This stance is what produced finding §IV.2.

---

## VI. The cost/complexity thesis

Against the fair baseline (mvp-demo-redux, a recent clean pilot — not the first-ever Tier-2 stumble):

| | redux | ldr-ophanic |
|---|---|---|
| $/milestone (raw) | $10.21 | $11.02 |
| **$/milestone (implement)** | $8.79 | **$7.38** |
| source LOC | 2,079 | 3,346 (+61%) |
| **external API integrations** | **0** | **4** |
| **scheduled/polling jobs** | **0** | **9** |
| DB tables | 5 | 18 (3.6×) |

Raw per-milestone is a near-tie (ldr ~8% higher), and the *entire* overage is the design phase — the fix-validation re-runs (10 design runs vs 3), a one-time cost. Decomposed, the **implement phase is ~16% cheaper per milestone on a categorically more complex app**: redux was self-contained CRUD/search; ldr took on two subsystem *classes* redux never attempted (live external integration, background polling/caching).

**The defensible claim:** not "we got cheaper" (raw, we didn't) but **"we held cost flat across a measured complexity jump while raising quality, and the quality apparatus covered its own cost out of the waste it eliminated."** Cost-per-milestone stayed flat; cost-per-unit-complexity went *down*. The mechanism: the efficiency the substrate fixes generate (0% wasted deliberations, clean-design→cheap-implement, no rework) is large enough to absorb both the harder app *and* the cost of the richer machinery (more review passes, diagram verification, hollow-build gates — none free). It's self-funding. Caveat: this is N=2 cross-pilot; a third complexity point landing flat would upgrade "held cost across a jump" to "cost decoupled from complexity."

---

## VII. Open items / next levers

- **The staleness bug** (frozen `cached_at` in weather + news) — left unfixed by design. The real fix is the *review-capability* lever (§IV.1): make the verifier independently re-derive the property under test rather than reading the code's self-justification. This is the single highest-value substrate change suggested by the run, because it also stops the propagation (§IV.2).
- **`UsersTable: missing`** — `verify_wiring` flags an M1 DB-layer node as hollow; likely a DB-layer limitation of the reverse-adapter (strongest on React, rough on SQL schema) rather than a real gap. Unconfirmed.
- **M8 accept path** — add the done-marking step so follow-up runs stop leaving stuck-queued tickets (§IV.3).
- **M5** — designed but thin ("skint"), because its scope was front-loaded into M2/M3's card error-states; the genuine delta is manual-refresh + observability. Note: M5's *goal* (trustworthy "when was this last current") is gated on the staleness bug — it could verify-pass while failing its actual purpose.

---

## VIII. One-line takeaway

The substrate held cost flat across a real complexity jump while improving quality — and the most valuable outputs of the run were the failure modes it exposed (review anchored by confident comments; certified bugs propagating as templates), which only surfaced because we fixed the substrate at the substrate level and let its output stand honestly.
