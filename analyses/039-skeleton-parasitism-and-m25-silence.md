# Analysis 039 — Skeleton parasitism and the M2.5 silence: when the scaffold becomes the project

**Date:** 2026-05-10
**Run:** Personal-finance dashboard ("obol") on tdd-serial-phased + python-tui skeleton ([runs/r41-obol-skeleton-parasitism/](../runs/r41-obol-skeleton-parasitism/), $1.10 / $20.00 cap, 11.5 min wall-clock, **0 features produced, 0 LOC of obol-specific code shipped**, `outcome: timeout`).
**Predecessors:** [r40-tui-skeleton](../runs/r40-tui-skeleton/) — 9 features, 1,243 LOC, $10.00 cap-hit, the strongest deliverable substrate had produced (analysis 038 F4).
**Result:** **First catastrophic deliverable failure since r38's no-prod-code regression — but with a different mechanism. r41-obol shipped not the wrong-shape (r38) and not the right-shape-undersized (r39 / r40) but the *wrong project entirely*: the team built nothing about money and instead spent M5 + M6 fixing the python-tui skeleton's example CounterScreen and its broken tests. Two compounding root causes: (1) the skeleton hello-world ships domain-named example code (CounterScreen, counter-label, "Count: N" UI text) that the team mistook for the v1 baseline of obol, parasitizing the team's attention onto code the operator never asked for; (2) M2.5 (composition) is phase-free and the White Rabbit emitted zero feature utterances, with no structural mechanism to fail the run when the load-bearing composition step produces nothing. Without features, M3 fell back to negotiating contracts directly from M2 tickets, M4/M5 had nothing to per_item-iterate over, and M5/M6 found work in the only "broken" code in the project — the skeleton's example. Caterpillar's review correctly diagnosed the test-framework bug and asked for changes — on the skeleton's counter app, with quote-perfect line numbers and a rigorous read of the API misuse — never noticing the team had built nothing about personal finance.**

## What we tested

The first non-pomodoro showcase run since the substrate began. Operator picked a real product idea — htop-style personal finance dashboard with Plaid integration, "obol" (Charon's ferry coin). Workflow: tdd-serial-phased on the python-tui skeleton. Budget bumped to $20 (2× r40's per-feature rate) for headroom.

Going in, the named risks were:
1. Plaid auth surface — would the team push back on an external dependency? (Constitutional hint discourages asking the operator; analysis 038 F3 noted this pattern reproduces.)
2. UI-first directive ("htop for money") might pull Tweedles toward cosmetic polish at M5's expense.
3. 9-ish feature concept on a $20 budget — comfortable per r40's per-feature economics.

What actually broke was none of these. The team never reached the questions Plaid would have surfaced because **the team never built obol**.

## Top-level numbers

| Metric | r38 (0 prod) | r39 (Guard A) | r40 (skeleton win) | **r41 (obol)** |
|---|---|---|---|---|
| Total cost | $7.77 | $5.12 | $10.00 (cap) | **$1.10** |
| Cap | $10.00 | $10.00 | $10.00 | **$20.00** |
| Wall-clock | 49.5 min | 36.7 min | 47.2 min | **11.5 min** |
| Outcome | complete | complete | budget_exceeded | **timeout** |
| LLM calls | 690 | 525 | 947 | **135** |
| Features produced | 5 | 3 | 10 | **0** |
| Production LOC (obol-specific) | 0 | 602 | 1,243 | **0** |
| Tweedles + Hatter cost share | 92% | 89% | 95% | **92%** (calls)** |

\*\* 135 calls and $1.10 are roughly tetrahedral compared to r40's 947 calls / $10.00 — call-and-cost shape was normal up to the point the team gave up. The run timed out at 11.5 minutes; budget barely engaged. The failure was structural, not financial.

**Per-agent telemetry (r41):**

| Agent | Calls | Cost | Note |
|---|---|---|---|
| tweedledum | 50 | $0.46 | Wrote the implementation note + read existing skeleton code |
| tweedledee | 44 | $0.25 | Same scope, different files read |
| caterpillar | 27 | $0.28 | Reviewed counter-app twice (review-001 + review-002) |
| cheshire_cat | 5 | $0.03 | One ADR (substantive); silent thereafter |
| white_rabbit | 4 | $0.04 | **Six tickets in M2 — then silent in M2.5; the run's load-bearing failure** |
| alice | 4 | $0.02 | Four stories in M1 (substantive); silent thereafter |
| queen_of_hearts | 1 | $0.02 | Convened, never substantively engaged |
| dormouse, dodo | (control) | — | Mad Hatter never instantiated for this short workflow |

Tweedles + Caterpillar accumulated the bulk of the activity — but on the wrong target. Their tool-calls are 115 read_file + 43 list_files + 8 git_diff = ~91% navigation, ~4% writes (3 str_replace + 0 write_file). They were exploring the tree, finding the broken counter-app tests, and proposing fixes — exactly the loop they should run in normal operation. The substrate worked. The seed was wrong.

## Findings

### F1 — Skeleton parasitism: the example code becomes the project

The python-tui skeleton ships `src/app.py` containing a working `CounterScreen` widget — reactive `count` field, "Count: N" rendered text, a `+` button — with **broken tests already present** (`tests/test_app.py` asserts on `Static.renderable`, which is not a public Textual API). The skeleton's README explains this is the hello-world; pytest fails out of the box; the operator is supposed to delete the counter and replace it with their actual app.

But that's not what the team saw. From the team's vantage:

- The directive said "Build a TUI based dashboard application for personal finance."
- M1 produced four stories about money. ✓
- M2 produced six tickets about the dashboard backend + UI shape. ✓
- M2.5 was supposed to compose features. **It produced nothing.** (See F2.)
- M3 negotiated contracts. The contracts (account-aggregation-endpoint-shape, transaction-history-endpoint-shape) are sensible API designs that match the M2 tickets' intent. ✓
- M5 (implementation) was supposed to per-item iterate over features, building each. With zero features, per_item is a zero-iteration loop. **But there was failing work to find.** The Tweedles ran `git_status` + `run_tests`, saw the existing skeleton tests failing, and the implementation note that landed is titled `implementation-001-fix-broken-test-harness-query-counterscreen-count-directly.md`.
- M6 reviewed. Caterpillar reviewed `src/app.py` + `tests/test_app.py`, correctly identified the `.renderable` API misuse, and called for changes. The review is rigorous. It is also reviewing **the skeleton's example app, not obol**.

Caterpillar's verdict in review-001:

> *"This is a test-framework bug, not an implementation bug. The production code in src/app.py is correct: it calls `.update(self._format())` to update the label. But the test cannot verify that the update worked because it's using the wrong API to inspect the result."*

This is a clean read of the skeleton's broken tests. It is also wholly orthogonal to the operator's directive. Caterpillar's §VIII "false certainty" failure mode is conspicuously absent here — the analysis is calibrated and accurate. The team's collective failure mode that DID manifest is something different and currently unnamed: **mistaking the scaffold for the project**.

The mechanism: when a skeleton ships executable code with named domain artifacts, the team has no signal distinguishing "this is filler that demonstrates the wiring works, delete it in your first feature" from "this is your v1 baseline, extend it." Both look the same. The team's path of least resistance is to treat the existing code as "what's already been built" and find work that fits within it. That counter-app was the project, in r41's reality.

This is the symmetric failure to analysis 037's reframe. Analysis 037: *no skeleton → deliverable shape collapses (production code inlined into conftest.py because there's no canonical src/).* Analysis 039: *too-elaborate skeleton with domain semantics → parasitism (the example becomes the project).* The skeleton has a bandwidth — too thin and the team has nothing to anchor on; too thick and the team confuses anchor for vessel.

### F2 — M2.5 silent failure: the load-bearing composition step has no structural enforcement

The composition meeting (M2.5) is phase-free per the workflow spec ("M1, M2, M2.5 stay phase-free — those meetings weren't sprawl loci in 032 and don't need the structural cap"). Phase-free runs in engagement-policy mode: the meeting closes when quiescence is detected.

White Rabbit was convened to M2.5. Five utterances total on the thread:
1. `alice | story` — seed from M1
2. `white_rabbit | ticket` — seed from M2
3. `dodo | directive` — convene + meeting brief
4. `dodo | nudge` — Rabbit silent past silence threshold; nudged to engage
5. `dodo | acknowledgment` — quiescence; meeting closed

Zero `feature` utterances. Rabbit's M2.5 directive is unusually explicit:

> *"Rabbit, ship features. This is your meeting — the chapter where decomposition becomes deliverable. ... A feature is a capability a user can describe in one sentence... Your job is to produce features. ... Without features, M3 has nothing to negotiate."*

That directive cannot be misunderstood. Rabbit ignored it.

The third instance now (after r39's missed operator-question, analysis 037 F3) where an agent has clear constitutional license + clear directive guidance + clear stakes, and stays silent. The constitutional softness is the underlying issue (filed as `62b906c2`); but in M2.5's specific case, the silence isn't just a missed escalation, it's a load-bearing deliverable that didn't ship. The structural mechanism for "you cannot close this meeting without producing the artifact" doesn't exist in phase-free mode. T57's `PhaseSpec.exit_condition_artifact` field is built for exactly this — but M2.5 doesn't use it because M2.5 has no phase.

Filed as `4912508a` (P1): either phase M2.5 with `exit_condition_artifact: feature`, or add a workflow-level post-meeting validator that aborts the run with a clear escalation when M2.5 emits zero features. Recommendation: phase the meeting (reuses existing T57 machinery, no new code paths).

### F3 — `from: any` seed fallback hides the failure downstream

When M3 convenes with `seeds: from: composition`, the runtime resolves the seed binding by looking for utterances on the composition thread. With zero features, the seed resolution falls through to whatever `from: any` finds — which surfaces the M2 tickets (most-recent substantive utterances upstream). Tweedles see tickets in their context and proceed to negotiate contracts. The contracts are coherent (account-aggregation API, transaction-history API) but they're contracts about *tickets*, not *features*. Quality is fine; level of abstraction is wrong.

This is a substrate property worth naming: **silent fallback in seed resolution can mask structural failures upstream.** When M2.5 produces nothing, the right behavior is probably "M3 cannot proceed; escalate" not "M3 reads tickets via the fallback path and pretends features exist." This is a smaller fix than F2 — it might be redundant once F2 lands (because if M2.5 fails loud, M3 never convenes) — but worth filing as a separate observation.

### F4 — Caterpillar's review machinery worked perfectly. On the wrong target.

Worth surfacing because it's diagnostic. Review 001 and 002 are some of the most calibrated, rigorous Caterpillar output the substrate has produced:
- Quote-perfect citations with line numbers
- Distinguishes test-framework bugs from implementation bugs
- Proposes a concrete API replacement (`counter_screen.count` reactive read instead of `Static.renderable` string parse)
- "Verdict: request-changes" with a specific resubmission criterion

This is M6 working exactly as designed. **The substrate's failure mode here isn't quality, it's targeting.** When the team builds the wrong project, M6's review machinery still runs faithfully — and produces a review of whatever's there. That's the right behavior in some failure modes (build-quality issues should still surface) and the wrong behavior in others (entire-project-mismatch should escalate, not get reviewed). The substrate cannot currently distinguish these.

### F5 — Tool-call profile was healthy; the issue wasn't navigation

| Tool | Calls | Share |
|---|---|---|
| read_file | 115 | 63% |
| list_files | 43 | 24% |
| git_status | 12 | 7% |
| git_diff | 8 | 4% |
| str_replace | 3 | 2% |
| run_tests | 1 | 1% |
| grep | 1 | 1% |

The 87% navigation share matches r40's 80% — the team was reading the working tree, finding code, exploring structure. In r40 that produced 1,243 LOC of obol-shaped code; in r41 it produced an implementation-note about counter-app tests. The difference isn't substrate behavior, it's the seed they were navigating against.

This argues against any "the model gave up" interpretation. The team was working — productively, by their lights. They were just working on the wrong thing.

## What's next

1. **Skeleton hello-world audit** (filed as `f630e40b`, P1). Strip domain semantics from python-cli, python-fastapi, python-tui, react-vite, fullstack-fastapi-react skeletons. Replace `CounterScreen` with `_SkeletonPlaceholderScreen`; replace any worked Click command with a `_placeholder` subcommand; keep `/health` (system, not domain) but drop `/hello`. README guidance: every skeleton should have a "What's intentionally left to your project" section explicitly framing the placeholder for deletion-not-extension.

2. **M2.5 structural exit condition** (filed as `4912508a`, P1). Phase M2.5 with `exit_condition_artifact: feature` so the meeting cannot close until at least one feature lands. Existing T57 machinery; small workflow YAML edit.

3. **Constitutional hint reframe for operator questions** (`62b906c2`, P1, already filed). Rabbit had an obvious operator-question to ask here: "I see existing scaffolded code with a CounterScreen — is that your v1 baseline to extend, or filler I should replace for the obol feature set?" The escalation didn't happen. Third instance reinforcing the fix's priority.

4. **Seed-resolution behavior on zero-artifact upstream** (file as new). When `from: composition` resolves to zero features, M3 currently falls through to `from: any` and finds tickets. Should be a hard fail: "the contract this meeting depends on did not ship; cannot proceed." Lower priority once F2 lands (because M2.5 should never close empty), but worth a separate ticket because it's a substrate invariant question, not a fix-this-one-bug.

5. **Re-run obol after F1 + F2 ship** to validate. If M2.5 phasing forces feature production AND the skeleton placeholder is unmistakable, the team should produce obol-shaped output, not counter-app fixes. r42-obol-redux is the natural test.

The deliverable substrate has now seen the full curve: no skeleton → wrong shape (r38), too-thin skeleton → backfilled by directive (r39), right-bandwidth skeleton → strongest deliverable (r40), too-thick skeleton with domain semantics → parasitism (r41). Skeleton bandwidth is now a known design parameter to tune, not a binary "have one / don't have one."
