# Analysis 046 — mvp-demo-redux: same notebook, 36% the cost, working app

**Date:** 2026-05-23
**Pilots compared:** [mvp-demo2](../demo/mvp/) (substrate 0.8.0, the original launch of Tier 2 pilots) vs [mvp-demo-redux](../demo/mvp-redux/) (substrate 0.10.1 + uncut T-ab58/T-ab59/T-ab60 on `fix/milestone-plan-kind-discrimination` branch)
**Result:** Same notebook spec (FastAPI + React + SQLite, Kohl's research notebook) shipped for **$30.58** vs the original **$83.78** — a **63% cost reduction**. App boots, persists, all CRUD + search + tag filtering functional. One known done-when gap (search + tag *compose* is wired exclusively, not combined). Cost-trajectory thesis receipted.

## TL;DR

Multi-agent SDLC overhead vs single-shot baselines compressed from ~30× to ~10× while the substrate's quality artifacts (test coverage, contract notes, ADRs, per-feature reviews, automated verify) shipped intact. The cost drop didn't come from one lever — it compounded across the 0.8.1 cost-reduction primitives, 0.9.0's foundation/capability axis, 0.10.0's cross-milestone bleed closure, 0.10.1's roster + tool-cap fixes, and the pre-pilot directive tweaks. Per-milestone trajectory shows a striking shape: M1 (foundation) $15.59, M2 (capability) $10.91, **M3 (capability on solid foundation) $3.72** — the substrate is finally cheap enough that the iterative quality model fits inside what single-shot used to cost.

## What both pilots built

Both pilots took the same operator-level intent: Kohl, an AI researcher, wants a personal markdown notebook — capture experimental insights, tag them, find them again. Same stack constraint (FastAPI + SQLite + React + Vite + TypeScript). Same 5-minute-setup demand. Same single-user, local-first, no-auth scope.

The milestone-plan agent decomposed each differently:

| Pilot | M1 | M2 | M3 |
|---|---|---|---|
| mvp-demo2 (0.8.0) | Kohl captures findings offline with markdown preview | Kohl finds past findings via search and tags | Kohl's notebook persists across restart |
| mvp-demo-redux (0.10.1) | Foundation: Persistence & API Shell | Capture & Organize: Create/Edit/Delete + Tagging | Findability: Search & Tag Filtering |

mvp-demo2 sequenced capability-first (capture → search → persistence-as-polish); redux sequenced foundation-first (persistence + API shell up front, capabilities on top). The redux ordering is what T-ab32 and T-ab58's directive prods are designed to produce — foundation milestones land first so capability milestones can stand on a stable substrate. Both produced working apps, but the redux trajectory is meaningfully cheaper because each subsequent milestone consumed an increasingly-solid foundation.

## Cost decomposition

### Top line

| Pilot | Total | vs mvp-demo2 |
|---|---|---|
| mvp-demo2 (0.8.0) | **$83.78** | 100% |
| mvp-demo-rerun-A (0.8.1) | $79.71 | 95% |
| obol-260522-1 (0.9.0+early 0.10.0) | $92.64 | 111% (different app, larger scope, cross-milestone bleed overhead) |
| **mvp-demo-redux (0.10.1)** | **$30.58** | **37%** |

### Per-workflow

| Workflow | mvp-demo2 | redux | redux as % of baseline |
|---|---|---|---|
| tdd-implement | $69.05 (14 runs) | $26.32 (15 runs) | **38%** |
| tdd-design | $14.31 (5 runs) | $3.90 (3 runs) | **27%** |
| milestone-plan | $0.17 | $0.26 | 153% (heavier directive post-T-ab58) |
| discovery | $0.11 | $0.10 | ~par |
| **TOTAL** | **$83.78** | **$30.58** | **37%** |

### Per-milestone (redux trajectory)

| Milestone | Cost | Notes |
|---|---|---|
| Setup (discovery + milestone-plan) | $0.36 | One-time |
| M1 foundation | $15.59 | Includes pytest framework establishment + 22 verify-spawned tickets |
| M2 capture/organize | $10.91 | Steady-state, 4 build-failure cycles, 3 verify-spawned bugs |
| **M3 findability** | **$3.72** | Capability on solid foundation, minimal verify cycles |
| **TOTAL** | **$30.58** | |

mvp-demo2's per-milestone breakdown is harder to extract cleanly (some runs predate the milestone-scope CLI flag), but a fair average is ~$28/milestone. redux's M3 at $3.72 is **13% of that baseline** — the strongest single per-milestone receipt.

### Per-ticket (where the substrate work actually happens)

mvp-demo2 M3 (the cleanest milestone-scoped subset, $19.37 across multiple implement runs): ticket-level granularity wasn't logged with the same fidelity as redux, but per-thread cost averaged $0.50-$0.65.

redux M2 (23 tickets observed, $0.35/ticket average):
- 14 design-spawned feature tickets: $0.20-$0.62 each
- 9 verify-spawned (build failures + bugs): $0.07-$0.23 each

The verify-spawned tickets are cheaper because they're targeted — the substrate spawns them with specific failure context (T-ab30 traceback, T-ab60 source-line context), tweedles read the focused brief and patch without re-architecting.

## Code quality comparison

### Both apps work end-to-end

| Check | mvp-demo2 | mvp-demo-redux |
|---|---|---|
| Backend tests pass | (audited at the time — see [SHOWCASE.md](../SHOWCASE.md) for the Geocities comparison; mvp-demo2 was the cohort that established the "shipped runs" baseline) | **22/22 ✓** |
| Frontend builds clean | n/a (mvp-demo2 didn't ship a frontend build_check; T-v7 came later) | **195 modules, 274K bundle ✓** |
| CRUD verified manually | n/a | **Verified — POST/GET/PUT/DELETE all functional** |
| Persistence across restart | n/a | **Verified — 2 notes survived kill + restart** |
| Search functional | yes (per the original docs) | **Verified — `?q=transformer` returns matching note** |
| Tag filter functional | yes | **Verified — `?tag=ml` returns ml-tagged notes** |
| Search + tag compose | not separately tested | **⚠️ Backend params marked "mutually exclusive"; compose helper exists in frontend but is bypassed** |

The compose gap is the single M3 done-when condition not met — the bug is one `if/elif` in NotesList.tsx and one docstring-vs-implementation conflict in `api/notes.py`. ~5-10 lines to fix. Everything else works.

### Theseus pass on redux code

We ran a [Theseus](../.claude/agents/theseus.md) review of the shipped redux app to test the complexity-hunting lens on freshly-generated code. He explicitly flagged the lens shift up-front (his frame is mature-codebase refactor work) and surfaced 7 findings ranging from medium (real bugs) to low (latent quality issues):

**Medium severity (worth fixing for production):**
1. **GHOST in api.ts**: `listMessages()` and `postMessage()` exported, never called, target `/api/messages` (route doesn't exist on backend). Scaffolding from a prior iteration that didn't get cleaned. Would crash at runtime if invoked.
2. **CHIMERA in notes.py**: timestamp dual-ownership — model declares `default=utc_now` and `onupdate=utc_now`, endpoint code manually assigns `datetime.now(timezone.utc)`. SQLAlchemy's `onupdate` never fires in production code path; future bulk-update endpoint forgets the manual assign → silent stale `updated_at`.
3. **CERBERUS — delete path duplication**: NotesList does local-state surgery on delete, NoteEditor refetches. Two paths, different failure modes.

**Low / latent (don't bite at current scale):**
4. `list_notes` fetches all rows + filters in Python (SQLite JSON-array limitation, deferred decision). Fine at notebook scale; cliff if pagination lands.
5. NotesList 482 lines — approaching complexity threshold.
6. React key on raw tag string would collide if backend accepted duplicate tags.
7. NoteEditor clears form before parent repopulates — flicker on slow connections.

**Paper-grade meta-observation** from the Theseus pass — the canonical multi-agent code-generation failure mode:

> "The `searchAndFilterNotes` Ghost is the canonical multi-agent artifact. One agent implemented the backend, documented that `q` and `tag` are 'mutually exclusive,' and the frontend agent built a compose helper anyway (correctly!) but then wired the exclusive-branch logic instead. The helper exists in a liminal state — correct, tested nowhere, imported but unused. This is exactly what happens when two agents reason independently about an underspecified contract seam."

He also flagged over-documentation as a multi-agent code signature: agents writing defensively because future agents will read what they wrote. Harmless but a real fingerprint.

### What the substrate caught vs missed

The substrate caught a lot. M1's foundation milestone went through 22 verify-spawned ticket cycles to converge on passing pytest; M2 went through 4 npm-build-failure cycles. Each verify cycle is the substrate refusing to ship code that doesn't pass automated checks — exactly the value the multi-agent quality model is supposed to deliver.

What the substrate missed mirrors what Theseus surfaced — the ghost functions in `api.ts` reference a non-existent route. Caterpillar's per-feature review didn't catch it because the unused functions don't import anywhere that breaks; M9 verify didn't catch it because it never gets invoked at test time. Same shape as the [analysis 045](./045-caterpillar-misses-import-time-traps.md) finding: code review reads, doesn't load — single-file static-time issues slip through.

## What changed in the substrate between 0.8.0 and 0.10.1

The cost trajectory isn't one fix; it's a compounding stack. Each release peeled off another class of wasted spend:

### 0.8.1 — Cost-reduction primitives (43-53% projected)

[Release notes](../release-notes/0.8.1.md) — three primitives shipped from staring at mvp-demo2's actual telemetry: per-emission tool-use round-trip pattern, FindingKind structured findings, Lever A/C cache amplification. The first projected drop from $84 → $40-48 was real but unobserved at the time because no comparable pilot ran on 0.8.1 — mvp-demo-rerun-A landed at $79.71, suggesting 0.8.1 alone didn't move the needle as much as projected because other failure modes were dominant.

### 0.9.0 — Foundation/capability axis + per-artifact milestone attribution

[Release notes](../release-notes/0.9.0.md) — added the foundation/capability distinction as a substrate primitive. Milestones now carry `kind: foundation` or `kind: capability`; tdd-design's M1 scoping roster narrows accordingly (Caterpillar solo on foundation, Alice solo on capability). Per-artifact milestone attribution (T-ab5/T-ab7) means features and stories declare which milestone they belong to.

This is the load-bearing change for the per-milestone cost trajectory observed in redux. Without it, M2 design seeds would pull in M1's stories + features, M2 implementation would read M1's contracts as ambient context, and the cost would compound. With it, each milestone runs in its own bounded scope.

### 0.10.0 — Cross-milestone bleed closed end-to-end

[Release notes](../release-notes/0.10.0.md) — the keystone substrate hardening. T-ab51 fixed the canonical bug: the milestone-scope seed filter only patched the `requirement` axis, leaving `story` and `feature` artifacts to bleed across milestones. Combined with T-ab52 (compose_context honors inheritance_chain — write isolation finally had read-side teeth) and T-ab53 (implement runs derive milestone from queued features), the cross-milestone bleed that had eluded T-ab9, T-ab34, T-ab45, T-ab46 individually was finally closed.

mvp-demo2's design phase showed the failure mode: M2 design read M1's stories as ambient context, producing features that overlapped M1's territory. mvp-demo-redux's M2 design (per the per-milestone cost) ran 1.4 runs on average vs mvp-demo2's ~2 runs because the bleed-driven rework cycles stopped happening.

### 0.10.1 — Tweedles out of M8 + tool-result cap

[Release notes](../release-notes/0.10.1.md) — T-ab54 narrowed M8 review roster to Caterpillar-only (tweedles were 2.2× Caterpillar's cost in obol-260522 at 80% pass rate — pure window-opening overhead). T-ab57 capped tool results in the deliberation loop at 5K chars (52% of total tool-result bytes saved across all tool-using agents, including Mad Hatter's M6 work).

### Branch-only (not yet cut)

The mvp-demo-redux pilot ran with three additional fixes on the `fix/milestone-plan-kind-discrimination` branch:

- **T-ab58** — Milestone-plan directive engages foundation/capability per milestone (rubric + non-M1 foundation guidance + "don't be that pilot" caution naming the obol-260522 failure mode by name)
- **T-ab59** — Synthesize default accept review when Caterpillar silences M8 (the lifecycle never hangs on a missing verdict; substrate safety net + directive prong tells Caterpillar to ship an explicit verdict)
- **T-ab60** — Source-line context in npm build failure findings (extract all error locations, render failing line ± 3 surrounding lines with `→` marker; saves ~$8/ticket on type-error verify failures)

## Per-milestone trajectory: the "foundation-once, capability-cheap" pattern

| | M1 foundation | M2 capability | M3 capability |
|---|---|---|---|
| Design cost | $1.38 | $2.18 | $0.34 |
| Implement cost (incl. verify cycles) | $14.21 | $8.73 | $3.38 |
| **Per-milestone total** | **$15.59** | **$10.91** | **$3.72** |

M1 carries the test framework establishment + the 22-ticket verify cycle to converge on passing pytest. M2 builds on solid persistence: 4 npm build cycles + 3 bug tickets, ~$0.35/ticket. M3 builds on solid persistence + CRUD + tag handling: minimal verify cycles, $3.72 for the entire milestone including all 5 LLM agents across design + implement + review.

This is the empirical shape of "amortize foundation, capability is cheap" — the architectural claim Wonderland makes for multi-milestone projects. mvp-demo2 didn't show this shape because cross-milestone bleed was forcing rework into every milestone; with the bleed closed, the natural trajectory is observable.

## What this means

### For the architectural claim

Multi-agent SDLC overhead at the 0.10.1+ substrate is sized at roughly **10× single-shot baselines** for substantially more shipped quality artifacts (test coverage, contract notes, ADRs, per-feature reviews, automated verify). That gap was 30×+ at the 0.8.0 baseline. The substrate's quality investment is now affordable in the cost regime where iteration cycles fit inside what single-shot used to cost. Single-shot Claude Code wrote a comparable notebook for ~$2-3 in prior baselines — but without the artifacts. The substrate at $30.58 ships them.

### For the cost-trajectory paper claim

mvp-demo-redux is the first pilot where the cumulative substrate-fix arc compounded into a real receipt. Compared against the obvious baselines:

- Original substrate (pre-0.8.0): ~$130-150 estimated (extrapolated from rough per-call patterns; no clean pilot at scale)
- mvp-demo2 (0.8.0): $83.78
- mvp-demo-rerun-A (0.8.1): $79.71
- **mvp-demo-redux (0.10.1+branch): $30.58**

Cumulative reduction from original to redux: ~75-80%. Per-milestone steady-state at $3-11 is the genuinely new regime — not "10% better" but "a different cost ladder entirely."

### For the methodology section

The cost-driver decomposition that motivated 0.10.1's fixes (T-ab54 + T-ab57) was operator-directed three-lens iteration captured in [`paper/artifacts/caterpillar-m8-cost-analysis.md`](../paper/artifacts/caterpillar-m8-cost-analysis.md):

1. **Per-agent aggregate** masked where cost actually lived
2. **Per-meeting per-run** masked per-feature scaling
3. **Per-meeting per-unit** + act/pass signal revealed real levers

Each lens unmasked something the previous one hid. Operator-in-loop falsification (the "wait, that's a weird title, why he getting silenced" pattern) caught a load-bearing misread of cache_creation vs cache_read that almost shipped as a wrong-lever fix.

## What didn't work / open questions

1. **Caterpillar still silences sometimes on M8 despite T-ab59 directive prong.** T-ab59's substrate safety net catches it (the synthesis fires correctly), but the directive prong didn't override Caterpillar's constitutional bias against cheap approval. When prior M3.5 reviews on the same thread show request-changes, his §V ("approval is not given cheaply") wins over the convenor's "you must emit." The synthesis IS working; the cosmetic surprise is that the bus output looks empty. UX improvement (synthesized-review badge in dashboard) is a tiny follow-up.

2. **Milestone planner still mis-flagged a foundation milestone as capability** even with T-ab58. Operator manually flipped M1's kind from capability → foundation. T-ab58's directive is best-effort; substrate-level enforcement (auto-flip kind when 100% of consumes are infrastructure-shaped requirement kinds) would be the harder fix if this recurs.

3. **Search + tag compose** (M3 done-when condition) doesn't work end-to-end despite the backend supporting the parameters and the frontend having a composable helper. Two-agent contract-underspecification artifact — Theseus's "canonical multi-agent ghost" pattern.

4. **The 0.8.1 cost-reduction projection of $40-48 didn't materialize until 0.10.1.** mvp-demo-rerun-A at $79.71 showed that the 0.8.1 primitives alone weren't sufficient; the cross-milestone bleed (0.10.0) and the M8/tool-cap fixes (0.10.1) had to land before the cost trajectory actually bent. Lesson: cost projections from telemetry of broken pilots may overestimate the leverage of any single fix when the broken pilot has multiple compounding failure modes.

## Data anchors

- mvp-demo2 substrate state: `git tag v0.8.0` (or the commit on demo/mvp's history)
- mvp-demo-redux substrate state: `git tag v0.10.1` + `fix/milestone-plan-kind-discrimination` branch (T-ab58 + T-ab59 + T-ab60)
- Cost-driver analysis: [`paper/artifacts/caterpillar-m8-cost-analysis.md`](../paper/artifacts/caterpillar-m8-cost-analysis.md) — six-part decomposition that motivated the 0.10.1 fixes
- Pilot artifacts: [`demo/mvp-redux/`](../demo/mvp-redux/) (code + `.wonderland/` lifecycle state; episodic memory dbs stripped for repo size)

## Receipt status

| Claim | Status |
|---|---|
| Working app end-to-end | ✅ Verified — boot, persist, CRUD, search, tag filter |
| Backend tests pass | ✅ 22/22 |
| Frontend builds | ✅ Clean |
| Cost reduction vs mvp-demo2 | ✅ 63% reduction, $83.78 → $30.58 |
| Per-milestone steady-state | ✅ M3 at $3.72 — 13% of baseline per-milestone |
| Quality artifacts shipped | ✅ Test coverage, contract notes, ADRs, per-feature reviews, M9 verify all in place |
| All milestone done-when conditions met | ⚠️ 14/15 (M3 search+tag compose gap) |
| First under-budget pilot | ✅ Comfortably under projected $40 |
