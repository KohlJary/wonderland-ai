# Analysis 037 — Skeleton was load-bearing all along; directive backfill recovers the deliverable

**Date:** 2026-05-09
**Run:** Pomodoro tdd-serial-phased v4 ([runs/r39-question-user/](../runs/r39-question-user/), $5.1170 / $10.00 cap, 36.7 min wall-clock, 3 features, completed end-to-end).
**Predecessors:** [r38-diff-tool-v2](../runs/r38-diff-tool-v2/) — 5 features, $7.77, 49.5 min, **0 LOC production code in src/** (analysis 036's headline regression).
**Result:** **r39 shipped 602 LOC of real Pomodoro logic in `src/` (`app.py`, `review.py`, `__init__.py`) — the M5 + M6 convenor directive update from analysis 036 worked. But the bigger finding reframes the entire r33-r38 trajectory: every TUI run since r33 has been against a *bare project root* (no skeleton). The 032 banner used a `fullstack-fastapi-react` skeleton that pre-laid `src/`, `tests/`, `frontend/` directories and a `conftest.py` already wired to import from production modules. r33-r38 ran without that scaffolding, and the deliverable shape progressively degraded as the team's path-of-least-resistance defaulted to whatever pytest could already see. r38 was the reductio: production logic inlined into `tests/conftest.py` because there was no canonical `src/` to write to. r39 shows that an explicit M5 directive can backfill skeleton-shaped guidance and recover production-code deliverability, at a ~10% per-feature cost premium.**

## What we tested

Per analysis 036's "What's next" — re-run pomodoro through tdd-serial-phased after Guard A landed (M5 + M6 convenor directive updates that explicitly require production code in non-test directories). Same workflow, same directive, same model.

The bet: schema-level instruction-following would stick like the str_replace nudge did. If yes, production code materializes despite the absence of a skeleton; if no, the regression reproduces and we'd need Guard B (structural phase exit-condition).

What we *didn't* realize before drafting analysis 036: every run since r33 has been against a bare project root. The directive guard was effectively *creating* the structural intent that the skeleton would have provided. That's a load-bearing reframe.

## Top-level numbers

| Metric | r35 phased | r36 teams | r37 diff (2-ftr) | r38 diff (5-ftr) | **r39 + Guard A (3-ftr)** |
|---|---|---|---|---|---|
| Total cost | $7.88 | $8.85 | $3.77 | $7.77 | **$5.12** |
| Wall-clock | 76.5 min | 53.3 min | 20.9 min | 49.5 min | **36.7 min** |
| Features | 5 | 5 | 2 | 5 | **3** |
| **$/feature** | $1.58 | $1.77 | $1.89 | $1.55 | **$1.71** |
| **min/feature** | 15.3 | 10.7 | 10.4 | 9.9 | **12.2** |
| Total LLM calls | 698 | 811 | 395 | 690 | **525** |
| **Production LOC in src/** | n/a (no src/) | 2198 | ~250 | **0** | **602** |
| Test files | 23 | 20 | 2 | 9 | **7** |
| Tests passing cleanly | 99 (mixed) | 107 | 13 | 79 (mostly xpassed) | **32 cleanly** |
| Diff bytes saved | n/a | n/a | 300K | 755K | **241K** |
| Caterpillar reviews | 20 | 7 | 9 | 4 | **10** |

**Per-feature cost up 10% vs r38 ($1.55 → $1.71)** — the directive added meaningful work. **Per-feature wall-clock up 23%** ($9.9 → $12.2 min) — same shape, more iteration to materialize structure that wasn't pre-laid. But the deliverable went from **0 LOC of runnable code → 602 LOC of runnable code**, including actual `start_session`, `elapsed_ms`, `remaining_ms` logic plus daily-review aggregation. The cost premium pays for the deliverable.

## Per-agent telemetry

| Agent | r38 calls | r38 cost | r39 calls | r39 cost |
|---|---|---|---|---|
| tweedledee | 283 | $3.04 | 212 | $1.89 |
| tweedledum | 223 | $2.26 | 175 | $1.55 |
| **mad_hatter** | 110 | $1.54 | **79** | **$0.84** |
| **caterpillar** | 35 | $0.65 | **33** | **$0.64** |
| alice | 17 | $0.11 | 12 | $0.07 |
| cheshire_cat | 13 | $0.07 | 9 | $0.06 |
| white_rabbit | 5 | $0.07 | 2 | $0.04 |
| queen_of_hearts | 4 | $0.03 | 3 | $0.03 |

Tweedles + Hatter all consumed less per feature than r38 — the directive guard tightened M5 enough that fewer iterations were needed to settle. Caterpillar was nearly identical (33 calls) but produced 2.5× more reviews (4 → 10), suggesting denser per-call work — exactly what we'd want from a more-focused review pass.

## Diff tool — adoption held steady

| Agent | r38 % diff | r39 % diff | r39 bytes saved |
|---|---|---|---|
| tweedledee | 68% | **69%** | 194,346 |
| tweedledum | 94% | **76%** | 66,645 |
| caterpillar | 80% | 0% (1 write only) | 0 |
| mad_hatter | 0% | 7% | (irrelevant, mostly new files) |

Tweedledum dropped from 94% to 76% — still strong adoption. **Total diff savings: 241K bytes (67.8% reduction on diff calls).** Lower than r38's 755K — but r38's number was inflated by the conftest-inline pathology (one giant fixture file getting patched repeatedly). r39's diff savings are more representative of normal M5 iterate-red-green cycles on actual production code.

The directive change for "production code goes in `src/`" did NOT crowd out the str_replace nudge. Both schema-level hints continue to stick.

## Findings

### F1 — Skeleton was load-bearing all along

The key reframe. Going back through the run history:

- **032 banner and earlier** (`analyses/data/...`): the `run.log` header reads *"Skeleton: fullstack-fastapi-react → /tmp/wonderland-tdd-serial-pomodoro-v3"*. Pre-laid `src/`, `tests/`, `frontend/` directories. Pre-laid `conftest.py` wired to import from `src.*`. The "MANDATORY first move: call `list_files` on the project root" guidance in M5 referenced *real* skeleton structure.
- **r33-r38** (TUI runs): bare project roots. The user types a path in NewRunScreen; the path goes through as-is. The skeleton-shaped guidance in M5 was orphaned — referencing structure that didn't exist.

What happened over r33-r38 as the team adapted to skeleton-less defaults:

| Run | What materialized | Shape |
|---|---|---|
| r35 | `./*.py` + `./src/*.ts` (mixed Python + TS) | Tweedles invented basic separation |
| r36 | `src/{models,api,client,ui,...}.py` (7 files, MVC-ish) | Cleanest improvisation of structure |
| r37 | `./timer.py`, `./daily_review.py`, `./src/*.ts`, `./test_tz_debug.py` | Scattered; 2 features only |
| r38 | (nothing in src/); ~810 LOC inlined in `tests/conftest.py` | Full collapse — fixture-resident logic |

The trajectory wasn't a substrate regression; it was the **structural-default-of-no-skeleton** progressively winning out. r38 was the reductio: when there's no canonical `src/` to write to and the tests already import from `conftest.py`, the path of least resistance for "make tests green" is to inline production logic where it's already wired up.

The directive backfill in Guard A (analysis 036) is essentially **manually communicating what the skeleton communicates structurally** — "tests/ is for tests, production code goes in src/." r39 confirms that schema-level instruction-following can carry that load when no skeleton exists, at the cost of an explicit verbal directive Tweedles have to read every iteration.

### F2 — The M5 + M6 directive update worked

Disk inventory in r39:

```
runs/r39-question-user/
├── src/
│   ├── __init__.py        (1 LOC)
│   ├── app.py             (377 LOC — start_session, elapsed/remaining
│   │                        calculation, completion handler, validation)
│   └── review.py          (224 LOC — completed_session_count + aggregation)
├── tests/
│   ├── conftest.py        (97 LOC — small, no inlined production logic)
│   ├── __init__.py
│   └── test_*.py          (7 files, 32 passing cleanly)
└── .wonderland/           (artifacts: 12 stories, 8 tickets, 3 features,
                              1 ADR, 9 contracts, 69 scenarios,
                              3 implementations, 10 reviews)
```

**602 LOC of production code shipped to `src/`**. `tests/conftest.py` is small (97 LOC) and contains only fixtures, not implementation logic. The 32 tests pass cleanly against `src/` imports — no `xfail` decorators left orphaned, no `xpassed` markers from inlined-logic tests.

Worth examining what the M5 directive's added paragraph did concretely:

> *"Production code lives in non-test directories. Test fixtures are NOT production code. … If your tests pass because you inlined the logic in `tests/conftest.py` or another test fixture, you have not shipped a feature; you have shipped a sophisticated test double. The `implementation` artifact you emit must name `files_touched` paths in non-test locations…"*

The "skeleton-or-equivalent rule" follow-up explicitly named the convention for bare project roots: `src/` for Python, `frontend/src/` for frontend. Tweedledee picked `src/` and shipped there. Tweedledum followed. The structural intent was communicated at the directive level rather than the skeleton level — and it stuck.

### F3 — Caterpillar's review pass was substantially deeper

10 reviews in r39 vs r38's 4. The first review (`001-pomodoro-v1-implementations.md`) is a high-level inventory; reviews 002-009 surface specific bugs by file and line:

- `review-005`: *"session-completion-duplicate-completion-detection-inverted"* — caught a logic-inversion bug
- `review-006`: *"storage-abstraction-incompatible-interfaces-between-app-py-and-review-py"* — cross-module contract violation
- `review-008`: *"break-session-completion-path-untested"* — coverage gap
- `review-009`: *"review-aggregation-storage-iteration-lacks-safety"* — defensive-coding issue

These are real bugs that would have shipped without the review. The M6 directive change ("first check before any code-level review: did production code actually ship to a non-test location?") didn't fire as the load-bearing finding because production code DID ship — but the additional review headroom let Caterpillar surface the next layer of issues. The directive update worked even though its stated headline check turned out to be unnecessary this run.

### F4 — Diff-tool adoption held; both schema-level hints compose cleanly

Tweedledum dropped from r38's 94% to 76% diff adoption. Tweedledee 68% → 69%. Total bytes saved: 241K (vs r38's 755K). The lower r39 number is a *better* signal than r38's: r38's 755K was inflated by the conftest-inline pathology where a single fixture file got patched repeatedly. r39's saved-bytes reflect normal M5 iterate-red-green on real production files.

Caterpillar dropped to 0% diff (her one write was a new review document, full-write is correct). Mad Hatter at 7% (mostly new test files, again correct).

The two schema-level hints — "use str_replace for incremental edits" and "production code lives in non-test directories" — both remained sticky. Adding the second didn't crowd out the first. This is encouraging for further schema-level guidance: the LLM seems to integrate multiple instruction-following hints rather than substitute one for another.

### F5 — The operator-question affordance was available but not used

T69 (the user-question affordance via QUESTION-to-operator utterances) was active for r39. The team emitted 9 questions on the bus across the run. **Zero of them addressed the operator.** All went to caucus or to specific sibling agents.

This isn't a failure mode — it's the substrate working as designed. The constitutional hint in primer.py says:

> *"Use this sparingly: most ambiguities should resolve through M3 contract negotiation, M2.5 composition, or pair-internal deliberation. The operator is not a fallback for 'I don't know what to write'; they are the decision-holder for things only they can decide."*

The team treated the operator as a fallback they didn't need. Cat raised architectural ambiguities to caucus; Queen and Alice answered. Tweedles negotiated contracts in M3. The internal team-resolution path worked, and the operator escalation channel sat unused — exactly the behavior the soft-default phrasing prescribes.

This is comforting: when the team CAN resolve internally, they do. The affordance is there for the hard cases (analysis 036 named this — directive-level architectural ambiguity that contracts can't disambiguate). For r39's 3-feature Pomodoro shape, the team had enough to work with.

Future N=4+ runs may surface cases where ask-operator IS needed. The fact that it didn't fire this run isn't bad — it's a "it's there, but the team is using it sparingly per the constitutional guidance" finding.

### F6 — Question-affordance integration with the broader meeting structure is clean

Worth noting: the team's pattern of caucus-level architectural questions in M1 → contracts in M3 → implementations in M5 produced clean separations. Cat surfaced "data permanence" as a question in M1; Queen and Alice resolved it in caucus. M3 nailed the contracts (9 contract notes shipped — the highest count we've seen, vs r38's 5 and r36's 4). M5 had clear targets.

The contract-note count is a leading indicator. r36: 4 contracts → 2200 LOC production. r38: 5 contracts → 0 LOC. r39: **9 contracts → 602 LOC.** More contract specificity correlates with more production code shipped, which makes mechanical sense (more agreed seams = more clarity for Tweedles' M5 work). Worth tracking across future runs.

### F7 — TUI's NewRunScreen should not accept bare project roots silently

The forward-looking implication. r33-r38's deliverability regression had a single root cause that wasn't substrate or constitution: the TUI accepts any project root path the user types, and bare roots produce skeleton-less runs. The user-facing experience of "type a path, click Go" doesn't communicate that the skeleton was previously load-bearing.

Three options for P8.6 (the spinup phase still pending in the gameplan):

1. **Skeleton picker in NewRunScreen.** Detect bare roots; offer to lay down a skeleton (`fullstack-fastapi-react`, `python-cli`, `react-spa`, etc. — bundled in `closet/skeletons/` if it exists, or a minimal default).
2. **Warn on bare-root selection.** "No skeleton detected — runs may shape oddly without one. Continue / pick a skeleton." Less invasive but requires the user to learn what a skeleton is.
3. **Default skeleton on first-use.** When the project root is empty, lay down a minimal skeleton automatically. Most opinionated but solves the issue without operator decision.

I lean toward (1) — skeleton picker as a first-class step in the new-run flow. The user gets to see options, the substrate communicates "this matters," and skeleton-less is still possible for advanced users who explicitly choose "no skeleton."

This is exactly the work that p8.6-spinup was scoped for in the gameplan. The directive backfill in Guard A is a partial workaround; skeleton restoration is the primary fix.

## What this analysis doesn't show

- **N=1 on the directive guard.** r39 is one run after the directive update. The 32-clean-passes / 602-prod-LOC outcome is good but variance hasn't been characterized. A second run with the same directive + workflow would let us distinguish "guard works reliably" from "guard worked once."
- **3 features vs 5 features means per-feature normalization carries caveats.** Rabbit's grouping is highly variable (2-5 features across runs). Total numbers don't compare directly; per-feature numbers compare with run-shape variance.
- **The skeleton hypothesis isn't proven, just consistent.** F1's argument is structural — looking at r33-r38 disk inventories tells a clean story of progressive collapse — but we haven't done the controlled experiment of running r39's workflow with a skeleton to see if it produces *even better* results (or just equivalent results with less directive overhead).
- **The 9 internal questions resolved cleanly in r39, but the team didn't always need to escalate.** Future runs with directives that genuinely require operator input (e.g., "build $X, with the budget split between Y and Z" where the split isn't specified) would test whether ask-operator fires when the team genuinely can't resolve.

## What's next

1. **Pivot back to P8.6 — new-project spinup with skeleton picker.** F7 is the primary fix; the directive backfill is a workaround. This is the next item on the P8 gameplan and is now the load-bearing item to ship. Slot it as the next active phase.
2. **Bundle some skeletons.** `closet/skeletons/` should ship at least a `python-cli`, `react-spa`, and `fullstack-fastapi-react` (recover the one used in early analyses). Skeleton picker in NewRunScreen consumes them.
3. **Re-run pomodoro on tdd-serial-phased *with* a skeleton, post-P8.6.** A/B against r39: same workflow, same directive, but with `fullstack-fastapi-react` laid down. Predicted: lower per-feature cost (less directive-reading overhead since skeleton already communicates structure), still-shipping production code, possibly even better deliverable shape than r39 because the skeleton provides scaffolding for cross-feature consistency.
4. **Document the skeleton-as-substrate finding in the README.** This is a thesis-level corollary worth surfacing: "the project-skeleton is a substrate primitive. It's not just starter code; it's how the meeting structure communicates 'production code goes here' without having to re-explain it every iteration."

## Headline

**The M5 + M6 directive update from analysis 036 worked. r39 shipped 602 LOC of real Pomodoro logic in `src/` against 32 cleanly-passing tests — no `xfail` markers, no fixture-resident logic. Per-feature cost rose ~10% (the directive added explicit work), but the deliverable shape recovered.** The bigger reframe: **skeleton was load-bearing all along.** Every TUI run since r33 has been against a bare project root, and the deliverability regression across r33-r38 was the team's progressively-degrading adaptation to the structural-default-of-no-skeleton. r38 was the reductio (production logic in `tests/conftest.py`). The directive backfill in Guard A is essentially manually communicating what the skeleton communicates structurally. **The primary fix isn't more directive content; it's restoring the skeleton primitive.** P8.6 (new-project spinup with skeleton picker) is now the load-bearing next item — Guard A is a workaround that buys time, skeleton-as-substrate is the durable solution. Diff tool adoption stayed strong (Tweedledum 76%, Tweedledee 69%); operator-question affordance was available but the team didn't need it (9 internal questions, all caucus-level). The substrate is healthy; the missing piece is the structural scaffolding that used to come with `analyses/data/...` runs and silently went away when the TUI stopped imposing it.
