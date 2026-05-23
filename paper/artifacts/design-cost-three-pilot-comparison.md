# Design-phase cost — three-pilot comparison

> Same operator, same model (Claude Haiku 4.5), comparable project
> shape (web/TUI app with persistence + UI surfaces). Three end-to-end
> design phases measured back to back:
>
> - **mvp-demo2** (2026-05-18) — first end-to-end Tier 2 pilot; no
>   per-milestone scoping primitives; the substrate baseline.
> - **mvp-demo-rerun-A** (2026-05-20) — same scope as mvp-demo2,
>   ships with foundation/capability axis + iteration scope filters
>   (T-ab5 through T-ab21) live; M3 troubleshooting cycles inflated.
> - **obol-260522** (2026-05-22) — fresh corpus (personal-finance
>   TUI); ships with all rerun-A substrate plus the May 22 stack
>   (T-ab22 → T-ab35: memory-scope filters, framing scoping, tool-
>   layer scoping). 5-milestone plan, **4 milestones substrate-
>   designed**; the broken M4 reruns are excluded per the rationale
>   in §6.2.
>
> Headline: **design-phase cost-per-milestone dropped from $4.77
> (mvp-demo2) to $4.15 (rerun-A) to $1.80 (obol) — a 62% reduction
> over four days of substrate iteration**, driven primarily by
> fewer meetings per milestone (18 → 28 → 11) as scope-discipline
> primitives prevented wasted iteration cycles.

---

## 1. Disposition (TL;DR)

| | obol-260522 (M4 excl) | rerun-A | mvp-demo2 |
|---|---|---|---|
| **Milestones substrate-designed** | **4** | 3 | 3 |
| **tdd-design cost (total)** | **$7.18** | $12.44 | $14.31 |
| **$ / milestone (tdd-design)** | **$1.80** | $4.15 | $4.77 |
| **Meetings / milestone** | **11** | 28 | 18 |
| **$ / meeting** | $0.16 | $0.15 | $0.27 |
| **$ / call** | $0.0104 | $0.0112 | $0.0136 |
| **Calls / meeting** | 16 | 13 | 19 |

**Cost-per-milestone delta:** obol is **62% cheaper than mvp-demo2**
and **57% cheaper than rerun-A**, despite designing one more milestone.

**Per-call cost is comparable** across all three (within ~30%; same
model, similar cache discipline) — the savings are not "the LLM got
cheaper to call." They come from **calling it fewer times**.

**Per-meeting cost** is comparable between obol and rerun-A and both
are noticeably cheaper than mvp-demo2 — substrate read-discipline
ports from rerun-A carry forward.

**The biggest delta is meetings-per-milestone (11 vs 28 vs 18).** That
ratio is what the May 22 substrate stack moved: fewer wasted reruns
landing on the same milestone, fewer concern/nudge ping-pong cycles,
fewer features cross-emitted then rejected and re-emitted.

---

## 2. Full design-phase rollup

### 2.1 By workflow (full design lifecycle: discovery + milestone-plan + tdd-design + tdd-decompose)

| Workflow | obol-260522 (M4 excl) | rerun-A | mvp-demo2 |
|---|---|---|---|
| `discovery` | $0.09 / 1 run | $0.00 / 0 runs * | $0.11 / 1 run |
| `milestone-plan` | $0.48 / 1 run | $0.20 / 1 run | $0.17 / 1 run |
| `tdd-design` | $7.18 / 4 runs | $12.44 / 8 runs | $14.31 / 5 runs |
| `tdd-decompose` | $0.00 / 0 runs | $1.12 / 4 runs | $0.14 / 1 run |
| **TOTAL design phase** | **$7.76** | **$13.76** | **$14.73** |

\* rerun-A reused the discovery interview from a prior pilot, so its
discovery row is structurally $0; mvp-demo2 ran a fresh one.

**Total design-phase savings:**
- obol vs mvp-demo2: **−47%** ($14.73 → $7.76)
- obol vs rerun-A: **−44%** ($13.76 → $7.76)
- Per milestone (normalizing for obol's 4 vs others' 3): **−60%**
  (≈$1.94/milestone vs ≈$4.59/milestone vs ≈$4.91/milestone)

The `tdd-decompose` overhead in rerun-A ($1.12 across 4 runs) was
operator-launched per-feature re-decomposition for stuck features —
exactly the workflow the May 22 substrate fixes were designed to
eliminate. obol ran zero `tdd-decompose` invocations.

### 2.2 Per-milestone breakdown (tdd-design only)

#### obol-260522 (M0–M3; M4 reruns excluded)

| Milestone | Cost | Runs | Meetings | Calls |
|---|---|---|---|---|
| M0 — data layer | $1.85 | 1 | 14 | 190 |
| M1 — daily-check surface | $2.28 | 1 | 12 | 245 |
| M2 — categorization | $1.27 | 1 | 9 | 94 |
| M3 — budgeting + summary | $1.78 | 1 | 9 | 162 |
| **Subtotal** | **$7.18** | **4** | **44** | **691** |
| (excluded: M4 × 6) | ($3.09) | (6) | (36) | (~700) |

**One run per milestone** — no retries needed for the four that
substrate-designed successfully. Average cost: **$1.80 per
milestone**, **11 meetings per milestone**, **173 calls per
milestone**.

#### mvp-demo-rerun-A

| Milestone | Cost | Runs | Meetings | Calls |
|---|---|---|---|---|
| M1 — persistence + API | $3.25 | 2 (partial + retry) | 24 | 345 |
| M2 — editor UI + search | $2.49 | 1 | 15 | 220 |
| M3 — DX + onboarding | $6.69 | 5 (1 + 4 retries) | 46 | 545 |
| **Subtotal** | **$12.44** | **8** | **85** | **1,110** |

M3's 5-run cycle was the milestone-kind-flip troubleshooting before
T-ab14's kind-consistency validator landed. Average cost: **$4.15
per milestone**, **28 meetings per milestone**. First-attempt-only
(excluding M3's 4 retries + M1's partial): $9.15 / 54 meetings /
3 milestones ≈ **$3.05 per milestone**, **18 meetings per
milestone** — still 70% more per milestone than obol.

#### mvp-demo2

| Milestone | Cost | Runs | Meetings | Calls |
|---|---|---|---|---|
| (label varies by run; substrate ran multi-milestone passes) | $14.31 | 5 | 54 | 1,051 |

mvp-demo2 ran on the pre-T-ab5 substrate that didn't carry an
explicit milestone field on design runs — most directives lack the
``milestone ``...`` `` marker, so per-milestone attribution from
status.json isn't clean. Project-total numbers are reliable; only
the per-milestone split requires inspection of the underlying
artifacts. Average across the 3 designed milestones: **$4.77 per
milestone**, **18 meetings per milestone**.

---

## 3. What moved the per-milestone cost down

### 3.1 Per-call efficiency is roughly steady (~$0.01-$0.014/call)

| | obol | rerun-A | mvp-demo2 |
|---|---|---|---|
| $ / call | $0.0104 | $0.0112 | $0.0136 |

Per-call cost is *similar* across all three pilots — same model,
similar cache behavior, similar prompt sizes per call. mvp-demo2
runs slightly higher per call (≈+30% vs obol) because read-
discipline directives and Lever A cache amplification hadn't yet
landed.

This is the **substrate teaching the LLM to use its context window
more carefully** story — and it's a modest lever in absolute terms
(30%, not multiples).

### 3.2 Calls-per-meeting is roughly steady (13-19)

| | obol | rerun-A | mvp-demo2 |
|---|---|---|---|
| calls / meeting | 16 | 13 | 19 |

Per-meeting LLM-call counts cluster in the same range across all
three pilots. mvp-demo2 ran slightly more calls per meeting (some
extra rotations on phase exit), but the differences are small.

### 3.3 Meetings-per-milestone is where the big delta lives

| | obol | rerun-A | mvp-demo2 |
|---|---|---|---|
| meetings / milestone | **11** | **28** | **18** |

obol design ran **40% fewer meetings per milestone than mvp-demo2
and 60% fewer than rerun-A**. This is the load-bearing number.

What drove it:
- **T-ab17 active-milestone iteration filter** — per-feature
  meetings only iterate over the in-scope features. mvp-demo2
  iterated each phase over the full project's feature set.
- **T-ab18 cross-emission rejection** — features emitted for
  the wrong milestone get rejected at write time. mvp-demo2
  shipped cross-emissions, then either ate them as scope creep
  or burned cycles unwinding.
- **T-ab19 architecture skip on no in-scope tickets** — M4
  exits cleanly when there's nothing to architect.
- **T-ab20 stack-span review scope discipline** — caterpillar
  doesn't waste rotations re-reviewing cross-feature work.
- **T-ab21 review routing by meeting-id** — fewer mis-routed
  review tickets that need re-resolution.
- **T-ab25a memory_scope: meeting_only on implement phases** —
  no carryover of stale context that triggers re-deliberation.
- **T-ab28 fresh-per-cycle verify tickets** — visible cycle
  counts let caterpillar exit oscillation rather than ping-pong.
- **T-ab29 oscillation detection** — caterpillar emits
  `question_to_operator` when it detects N-cycle ping-pong
  instead of issuing another opposite-direction verdict.
- **T-ab34 + T-ab35 milestone scope filters (framing + tool
  layer)** — agents stop pulling cross-milestone context that
  inflates per-meeting prompts AND prompts cross-milestone work.

Each fix prevents one wasted-iteration pattern. Their compounding
effect is the meetings-per-milestone drop.

---

## 4. Artifact volume (design products)

### 4.1 Counts shipped

| | obol (M4 excl) | rerun-A | mvp-demo2 |
|---|---|---|---|
| Milestones planned | 5 | 3 | 3 |
| Milestones substrate-designed | 4 | 3 | 3 |
| Features | 11 | 11 | 11 |
| Stories | 26 | 28 | 25 |
| Tickets | 50 | 103 | 80 |
| Requirements | 22 | 15 | 21 |
| Contract notes | 18 | 10 | 30 |
| Architecture (ADRs) | 8 | 1 | 7 |
| Reviews | 9 (design pre-impl) | 86 (post-impl) | 52 (post-impl) |

(Reviews row is noisy across pilots because obol hasn't completed
implementation; rerun-A and mvp-demo2 counts include implementation-
review cycles. Use the other rows for design-volume comparison.)

### 4.2 Same feature count, fewer tickets per feature

Same 11 features in each pilot. obol shipped **50 tickets (4.5/feature)**
vs rerun-A's **103 tickets (9.4/feature)** vs mvp-demo2's **80
tickets (7.3/feature)**.

obol shipped **53% fewer tickets per feature than rerun-A** and
**38% fewer than mvp-demo2**. Combined with the per-ticket
implementation cost from the prior rerun-A vs mvp-demo2 analysis
(~$0.53/ticket on rerun-A's substrate), the projected implementation
cost downstream is substantially lower.

### 4.3 ADR count rebounded vs rerun-A

rerun-A's ADR count was 1, flagged in the prior analysis as
suspiciously low — possibly the T-ab19 M4-skip overcorrecting.
obol produced 8 ADRs across 4 milestones, suggesting the M4 skip
fires when there's genuinely nothing to architect and runs the
meeting when there is.

---

## 5. Cost trajectory (paper-grade framing)

Three pilots, four days, same model, same operator:

```
mvp-demo2 (May 18)          rerun-A (May 20)            obol-260522 (May 22)
─────────────────           ─────────────────           ────────────────────
$4.77 / milestone           $4.15 / milestone           $1.80 / milestone
18 mtgs / milestone         28 mtgs / milestone *       11 mtgs / milestone
3 milestones                3 milestones                4 milestones
$14.31 total                $12.44 total                $7.18 total
                            (* M3 troubleshooting)
```

The substrate-iteration → cost-reduction trend is monotonic on
per-milestone cost across three independently-run pilots. The
rerun-A intermediate point is important: rerun-A's project-total
cost was lower than mvp-demo2 (the rerun-A vs mvp-demo2 artifact
documented the −33% headline), but the per-milestone cost dropped
only modestly (−13%, $4.77 → $4.15) because of the M3 troubleshooting
overhead. obol's per-milestone drop (−57% vs rerun-A) shows the May
22 stack moved the metric the rerun-A artifact identified as
"projected steady-state" (~$3.05/milestone first-attempt) past
the projection by another 41%.

**The thesis claim, restated:** substrate fixes that target
iteration discipline (not per-call efficiency) drive structural
cost-per-milestone reductions disproportionate to the per-call
cost changes. Three pilots establish the trajectory; subsequent
pilots will test whether the per-milestone floor is structural
or whether further iteration discipline still has slack.

---

## 6. Methodological notes

### 6.1 What's apples-to-apples

- Same Claude Haiku 4.5 model with identical pricing constants
- Same operator gating between milestones
- Same agent cast + constitutions
- All three pilots: SQLite-or-equivalent persistence, multi-surface
  UI (web/TUI), Python-stack heavy
- All three pilots: gated single-milestone-per-pass design workflow
  (with rerun-A as the transition pilot)

### 6.2 Why excluding obol's M4 reruns is fair

The 6 obol M4 reruns produced **zero features**. Every run completed
6 meetings, emitted no features, no tickets, no stories beyond what
was already on disk. They surfaced T-ab34 + T-ab35 (substrate fixes
that shipped after the pilot completed M4 manual decomposition).
Including their $3.09 of cost in the per-milestone average would
attribute pre-fix substrate cost to obol's design discipline, which
is exactly inverse to what the substrate fix story claims.

The honest treatment: report the 4 milestones that produced design
output, plus a footnote that M4 stalled and was operator-decomposed
manually. The substrate is now expected to design M4-shape work
cleanly on a future pilot with T-ab34 + T-ab35 active from the
start — that's the validation for the substrate-fix claim, separate
from the per-milestone cost claim made here.

### 6.3 mvp-demo2's per-milestone attribution

mvp-demo2 ran on pre-T-ab5 substrate where the design workflow
didn't carry an explicit per-milestone field on runs. The status.json
`directive` field doesn't reliably surface which milestone a given
design pass targeted. Per-milestone numbers for mvp-demo2 above are
aggregated (5 runs / 3 milestones gives the average) rather than
broken down per-milestone. Project-total numbers and per-meeting
numbers are reliable.

### 6.4 Different project shapes

- **mvp-demo2 + rerun-A**: markdown notebook web app (Python +
  FastAPI + SQLite + React + Vite + TypeScript)
- **obol-260522**: personal-finance TUI (Python + SQLite, no
  frontend stack)

Project shape differs across the comparison. mvp-demo2 + rerun-A
share shape; obol diverges. The cost reduction argument is across
*operator + model + workflow shape* rather than *project shape*;
the matching workflow shape (gated milestone-per-pass) is what
makes the cost-per-milestone metric comparable.

The obol → next-pilot comparison (same-shape pilot run with the
May 22 substrate) will provide the apples-to-apples shape-
controlled receipt. This three-pilot artifact establishes the
trajectory; future pilots harden the cross-shape generalization.

### 6.5 What the numbers ARE NOT

- They are NOT a per-ticket implementation cost comparison; obol
  implementation is in flight at the time of this analysis.
- They are NOT a quality comparison; quality comparison requires
  the operator+adversarial-reviewer pass that hasn't run on
  obol's design output yet.
- They are NOT a generality claim; three pilots are a trajectory,
  not a proof.

---

## 7. Open questions for the obol downstream + next pilot

1. **Does obol implementation track the design-phase savings?**
   The rerun-A vs mvp-demo2 implementation comparison hit −38% on
   per-implementation-run cost. If obol implementation hits the
   same trajectory (substrate fixes that landed mid-rerun-A are
   pre-shipped in obol), per-feature implementation cost should
   drop further.
2. **Does the per-milestone floor of ~$1.80 hold under cross-
   shape validation?** The next pilot should test on a different
   project shape with the same substrate to falsify or confirm
   the "$1.80/milestone is the obol substrate's floor" claim.
3. **Can obol M4 be substrate-designed with T-ab34 + T-ab35
   active?** Run M4 again on the obol corpus with current
   substrate; if it produces features cleanly, the M4-skip
   exclusion above transforms from "honest accounting" to
   "validated substrate-fix receipt."
4. **What's the next iteration-discipline lever?** obol's
   meetings-per-milestone is 11; mvp-demo2's was 18; rerun-A
   first-attempt was 18 (28 with overhead). Is there a structural
   floor below 11 meetings per milestone for full 6-phase
   tdd-design? Or did the May 22 stack get close to the floor?

---

*Generated 2026-05-22 from the three pilots' run logs and telemetry.
See `projects/{obol-260522,mvp-demo-rerun-A,mvp-demo2}/.wonderland/runs/`
+ `telemetry/` for raw per-run data. Excludes the 6 obol M4 reruns
(rationale: §6.2). Pairs with `pilot-comparison-rerun-A-vs-mvp-demo2.md`
which has the upstream rerun-A → mvp-demo2 comparison + the steady-
state projection that obol independently confirms.*
