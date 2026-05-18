# Analysis 033 — Mvp-demo2 cost breakdown

Detailed economic analysis of the first end-to-end Tier 2 autonomous pilot (mvp-demo2). Captures per-workflow, per-agent, and per-meeting spend; identifies efficiency hotspots; surfaces adjustable patterns. Source artifact for the paper's economics section.

**Pilot context**: 3 milestones (data layer + search/tags + persistence), 22 workflow runs, 4320 LLM calls, ~5000 lines of code shipped, 61 passing tests. Total spend: **$83.78**.

## 1. Per-workflow distribution

```
tdd-implement      $69.08  (82.4%)  14 runs, $4.93/run
tdd-design         $14.31  (17.1%)   5 runs, $2.86/run
milestone-plan      $0.17  ( 0.2%)   1 run,  $0.17/run
tdd-decompose       $0.14  ( 0.2%)   1 run,  $0.14/run
discovery           $0.11  ( 0.1%)   1 run,  $0.11/run
```

**Implementation dominates** — 82% of spend lives in tdd-implement runs. Discovery + milestone-plan + tdd-decompose together = 0.5% of total. The pre-implementation workflow surface is essentially free at this scale; the cost is in actually writing + reviewing code.

Design at 17% is the second bucket and reflects what design actually does — coordinated multi-agent deliberation (stories → features → tickets) with all eight agents participating in some phase.

**Implication for paper**: cost-optimization effort should focus on tdd-implement. A 10% efficiency win on implementation = ~$7 saved per pilot. A 10% win on design = ~$1.40. A 10% win on discovery = pennies.

## 2. Per-agent breakdown

```
tweedledee       $32.06  (38.3%)  calls=1675  $0.0191/call  cache_hit=88%
tweedledum       $29.92  (35.7%)  calls=1565  $0.0191/call  cache_hit=88%
caterpillar       $9.17  (10.9%)  calls= 418  $0.0219/call  cache_hit=81%
mad_hatter        $4.99  ( 5.9%)  calls= 308  $0.0162/call  cache_hit=89%
alice             $3.21  ( 3.8%)  calls= 150  $0.0214/call  cache_hit=89%
cheshire_cat      $2.69  ( 3.2%)  calls= 113  $0.0238/call  cache_hit=77%
queen_of_hearts   $1.12  ( 1.3%)  calls=  30  $0.0375/call  cache_hit=62%
white_rabbit      $0.65  ( 0.8%)  calls=  61  $0.0107/call  cache_hit=93%
```

**Tweedles dominate at 74% combined** ($32.06 + $29.92 = $61.98). They do the heavy implementation work — both frontend (Tweedledee) and backend (Tweedledum) cost essentially the same per call ($0.0191) with the same cache hit rate (88%), indicating the substrate is splitting work between them fairly and their context-reuse is well-tuned.

**Caterpillar at 11%** is the review pass cost. He's invoked across multiple feature reviews per implementation pass, costs slightly more per call ($0.0219) due to broader context (he reads the whole feature deliverable), and his cache hit rate (81%) is lower than the Tweedles' because review prompts vary more per-feature.

**Mad Hatter at 5.9%** is the tea-party (M6 adversarial test design) cost. His 89% cache hit rate is the highest among non-trivial agents — tea-party is template-shaped, lots of reuse.

**Cheshire Cat at 3.2%** is architecture pass + ADR work. Lower cache hit (77%) reflects ADR work being one-off / per-decision.

**Outlier: Queen of Hearts** — only 30 calls but the most expensive per-call ($0.0375), lowest cache hit (62%). She's invoked rarely (security/auth rulings, surfaces only when needed) but her context isn't well-reused because each invocation is for a distinct security concern. **Small total impact ($1.12, 1.3%) but interesting as efficiency outlier**.

**White Rabbit at 0.8%** — extremely cheap, 93% cache hit, $0.0107/call (cheapest agent). He's the planner (milestone-plan + M2 composition) — short focused emissions, lots of cached substrate context.

## 3. Per-meeting top spenders

```
$7.45  kohl-organizes-notes-with-optional-tags / review (M8)
$4.24  architecture (Cheshire Cat M4)
$3.20  kohl-organizes-notes-with-optional-tags / impl (test-allows-multiple-conflicting...)
$3.10  kohl-searches-notes-by-title-and-body-content / review
$2.87  kohl-drafts-and-saves-experimental-notes / review
$2.82  kohl-can-organize-notes-with-tags / impl (pytest)
$2.50  kohl-searches-notes-by-title-and-body-content / impl (test-assertions-lack-fail-detail)
$2.38  kohl-can-find-past-notes-by-title-or-content-search / review
$2.36  kohl-organizes-notes-with-optional-tags / impl (test-assertions-lack-clarity)
$1.93  kohl-can-find-past-notes-by-title-or-content-search / impl (test-expects-or-takes)
$1.89  kohl-can-find-past-notes-by-title-or-content-search / impl (test-failed-tests-...)
$1.52  kohl-can-create-and-save-experimental-notes / review
$1.45  kohl-searches-notes-by-title-and-body-content / impl (pytest-run-failed)
$1.35  kohl-can-find-past-notes-by-title-or-content-search / impl (pagination-field-...)
$1.25  scoping (Alice + Caterpillar M1)
```

**Reviews are the most expensive single meetings.** The top review (tag organization, $7.45) cost almost as much as the entire tdd-design phase for M2. Reviews involve broader context (whole feature deliverable + sibling tickets + contracts) and multi-agent deliberation (Caterpillar + concerns from Cat / Queen / Tweedles).

**Tag-handling feature was the most expensive** by far. The review hit $7.45 alone, plus multiple expensive implementation passes for "test-allows-multiple-conflicting" + "test-assertions-lack-clarity" follow-ups. Suggests the tag-handling spec had under-determined edge cases that surfaced through review-implementation iteration.

**Recurring pattern in expensive impl meetings**: ticket slugs like `test-allows-multiple-conflicting`, `test-assertions-lack-clarity`, `test-failed-tests-test-...`, `test-expects-or-takes` — these are review-synthesized tickets about TEST QUALITY, not feature behavior. Caterpillar's reviews kept surfacing test-coverage gaps that the next implementation pass had to address. **The tests-of-tests recursive pattern is a real cost driver** worth a substrate observation.

## 4. Cache efficiency analysis

Cache hit rate per agent (descending):

| Agent | Cache hit | Per-call cost |
|---|---|---|
| white_rabbit | 93% | $0.0107 |
| mad_hatter | 89% | $0.0162 |
| alice | 89% | $0.0214 |
| tweedledee | 88% | $0.0191 |
| tweedledum | 88% | $0.0191 |
| caterpillar | 81% | $0.0219 |
| cheshire_cat | 77% | $0.0238 |
| queen_of_hearts | 62% | $0.0375 |

**Strong inverse correlation between cache hit rate and per-call cost.** This validates that the substrate's caching is doing meaningful work — agents with stable templated contexts (Rabbit's planning, Hatter's tea-party) get cheaper calls. Agents with per-invocation variance (Cat's per-architecture ADRs, Queen's per-security-concern rulings) pay more per call.

**Per-call cost spread is narrow** — $0.0107 (cheapest) to $0.0375 (most expensive) is a 3.5x range. Most agents cluster around $0.019-0.024. Suggests no agent is dramatically misconfigured; differences are explained by call-pattern variance, not bad caching discipline.

## 5. Trends + adjustable patterns

### Cost driver 1: review-driven test-quality follow-ups

The "tests of tests" pattern. Caterpillar's reviews surface findings like "test assertions lack clarity" or "test allows multiple conflicting interpretations" — synthesized as follow-up tickets, the Tweedles then re-implement the tests, which Caterpillar reviews again. Each cycle costs $2-4. Saw 5+ such cycles across the pilot.

**Adjustment lever**: tighter test-design phase (M6 tea-party) upfront so Tweedles ship better tests on first pass. OR: a substrate rule that test-quality findings can't synthesize follow-up implementation tickets (they're meta-feedback, not bugs). Worth filing.

### Cost driver 2: review passes broadly

Reviews cost ~2x implementation per meeting on average. They involve Caterpillar reading the entire feature deliverable + sibling tickets + contracts + ADRs — that's a lot of context per call even with 81% cache hit. **No clear fix** without sacrificing review quality.

### Cost driver 3: feature complexity correlates with review cost

The most expensive feature reviews were tag-handling ($7.45) and search ($3.10) — both features with multi-dimensional behavior (tag case-sensitivity, search ranking, pagination semantics). Simple features like "demo readiness" had cheaper reviews. **No clear adjustment** — this is the substrate doing what it should (more careful review on more complex features).

### Cost driver 4: Caterpillar's per-call cost vs Tweedles'

Caterpillar costs $0.0219/call vs Tweedles' $0.0191/call. Caterpillar has 1/4 the calls but his calls are 15% more expensive. If we could reduce review-call cost by 10%, it'd save $0.92. Small lift.

### Anti-pattern not observed: persona-cost inflation

Anticipated finding: that some agents might over-emit due to characteristic failure modes (Hatter over-applying edge cases = more output tokens). Data doesn't support — Hatter has the HIGHEST cache hit rate (89%) and a middle-of-pack per-call cost. His verbosity isn't driving cost; substrate caching absorbs it.

## 6. Economic comparison: mvp-demo (pilot 1) vs mvp-demo2 (pilot 2)

| Metric | mvp-demo (pilot 1) | mvp-demo2 (pilot 2) |
|---|---|---|
| Total spend | $40.14 | $83.78 |
| Total calls | unknown (no telemetry) | 4320 |
| Workflow runs | 17 (many aborted) | 22 (none aborted) |
| tdd-design runs | 10 (many wedged + restarted) | 5 (1 wedge, recovered) |
| tdd-implement runs | 7 | 14 |
| Wedge waste estimate | ~$5+ (multiple killed runs) | ~$1 (one wedge, recovered via rerun context-carryover) |
| Working app shipped | No (M1 partial) | Yes (3 milestones) |
| Per-effective-milestone | N/A (incomplete) | $27.93 |

**Mvp-demo2 spent 2x what mvp-demo did but shipped a working app vs none.** Per-effective-milestone (mvp-demo2): ~$28. Mvp-demo never reached "effective milestone" because of substrate wedges. The headline isn't "mvp-demo2 was cheaper" — it's "mvp-demo2 was the first to actually complete, at a per-milestone rate that lets a 5-milestone pilot land in the $80-150 range."

## 7. Paper-grade observations

1. **Implementation work is 82% of cost.** Optimization focus belongs there. The substrate's pre-implementation workflows are essentially free at this scale.

2. **Tweedles cost ~74% of total spend** — appropriate given they do the actual code writing. Their cost-per-call is well-controlled (88% cache hit, $0.019/call) and roughly equal between frontend (Tweedledee) and backend (Tweedledum) work.

3. **Cache hit rate is high across all agents** (62%-93%). The substrate's prompt-caching discipline is paying off — most calls are not paying full input-token cost.

4. **Review passes are the most expensive single meetings**, with the tag-handling review ($7.45) as the top-line item. Review cost scales with feature complexity — appropriate but adjustable via tighter upfront tea-party design.

5. **Test-quality follow-ups are a recurring cost driver.** 5+ cycles of "Caterpillar surfaces test-quality finding → Tweedles re-implement tests → Caterpillar reviews again." Substrate doesn't currently distinguish meta-feedback findings from bug findings. **Worth filing as a substrate-improvement roadmap item**.

6. **Per-agent cost variance is narrow** — $0.0107 (Rabbit cheapest) to $0.0375 (Queen most expensive per call) is a 3.5x range. No agent is dramatically misconfigured.

7. **Quality-cost coupling validated economically.** The substrate fixes that improved quality (branching memory, coverage check exemptions, auto-directive synthesis) also reduced wedge waste — mvp-demo2 has ~$1 of wedge waste vs mvp-demo's ~$5+, while shipping more.

## 8. Adjustable patterns for next-pilot economic optimization

In rough priority order by leverage:

1. **Substrate distinction between meta-feedback findings and bug findings** at Caterpillar's M8 review. Test-quality findings ("assertions lack clarity") shouldn't synthesize implementation tickets — they're feedback to the test author, not work for the implementer. Could save 3-5 implementation passes per pilot (~$8-15).

2. **Tighter M6 tea-party upfront** so Tweedles ship better tests on first pass. Hatter's already cheap (5.9% of total); investing more in tea-party rotation budget might reduce expensive test-quality review cycles.

3. **Review-pass parallelization** — currently Caterpillar reviews one feature at a time. Pipeline parallelization across feature reviews would reduce wall-clock without changing total cost — quality-of-life improvement for operators waiting on results, not a cost win.

4. **None of these are urgent.** Pilot is already economically viable. Optimization is a polish concern, not a feasibility one.
