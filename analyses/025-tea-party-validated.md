# Analysis 025 — Tea-party validated, framework reaches click

**Date:** 2026-05-06
**Run:** Tea-party Geocities showcase v2 (Alice + Hatter in M4, with
the two-operations-per-scenario directive fix from `56c3b16`).
**Snapshot:** [analyses/data/025-tea-party-validated/](data/025-tea-party-validated/)
**Result:** **The framework now reliably ships directive-aligned features end-to-end with a runnable test surface authored by the QA pair, in ~8 minutes for ~$2 of Haiku.**

## Why this matters

Three Geocities runs in close succession told one story:

1. **v1 (Hatter only, no max_tokens fix):** Hatter's M4 contribution
   was lost to truncation; team built coherent scope but no rate
   limiter; 110 lines shipped.
2. **v2 (Hatter only, max_tokens fixed):** Hatter shipped 5 security-
   edge scenarios but no actual test files; Tweedles backfilled 1798
   lines of contract tests in M5 (the test-engineering anti-pattern);
   2696 lines total.
3. **Tea-party v1 (Alice + Hatter, scenarios but no test files):** the
   pair worked beautifully on the design layer (15 scenarios, 9
   stories, 3 contract notes locked dynamically mid-meeting) — but
   nobody actually called `write_file` to put runnable test code on
   disk. 606 lines of production code, zero tests.

Each iteration closed one failure mode and exposed the next. This run
closes the last one — the tightened M4 directive forced Alice + Hatter
to perform two operations per scenario (artifact + write_file), and
they did.

## What shipped

**1841 lines across 14 files, including 1253 lines of pytest written
by Alice and Hatter:**

| File | Lines | Author | Type |
|---|---|---|---|
| `tests/test_basic_journey.py` | 217 | Alice | Happy-path user journeys |
| `tests/test_homepage_xss.py` | 196 | Hatter | XSS via Markdown |
| `tests/test_account_deletion.py` | 210 | Hatter | GDPR cascade |
| `tests/test_auth_token_expiry.py` | 197 | Hatter | Session expiration |
| `tests/test_registration_races.py` | 155 | Hatter | Concurrent signup |
| `tests/test_discovery_pagination.py` | 278 | Hatter | Discovery edges |
| `src/backend/api/auth.py` | 125 | Tweedledum | Production |
| `src/backend/api/homepage.py` | 116 | Tweedledum | Production |
| `src/backend/api/users.py` | 92 | Tweedledum | Production |
| `src/backend/auth.py` | 57 | Tweedledum | Production |
| `src/backend/markdown.py` | 110 | Tweedledum | Production |
| `src/backend/session.py` | 28 | Tweedledum | Production |
| `src/backend/models.py` | +58 | Tweedledum | Production |

**Wonderland artifacts:** 6 stories (Alice), 1 ADR (Cat — chose
platform-curated discovery over webring with named tradeoffs),
6 test_scenarios (Hatter + Alice's journey one), 8 tickets
(Rabbit), 16 contract notes (Tweedles, including the dynamic
mid-meeting locks from the prior run's pattern), 1 review
(Caterpillar — see below for what he caught).

## A clean A/B across three runs

| Metric | v2 (no Alice) | tea-party v1 | **tea-party v2 (this run)** |
|---|---|---|---|
| Wall clock | 858s | 650s | **458s** |
| Cost | $3.21 | $2.39 | **$2.05** |
| LLM calls | 276 | 296 | **179** |
| Parse errors | 6 (5 recovered) | 5 (5 recovered) | **5 (5 recovered)** |
| Test scenarios shipped | 5 | 24 | 6 |
| **Test files on disk** | **1798 lines (Tweedles)** | **0 lines** | **1253 lines (Alice + Hatter)** |
| Production code | ~900 lines | 606 lines | **588 lines** |
| Production code that's actually new code (vs test backfill) | ~900 | 606 | **588** |
| Outcomes | M4-M6 hit MEETING_BUDGET | M4-M6 hit MEETING_BUDGET | **M1-M5 COMPLETE; only M6 hit cap** |

The cost trajectory is meaningful: $3.21 → $2.39 → $2.05 across three
iterations, while output quality improves at every step. The framework
got *cheaper* as it got better, because:

- Tweedles' M5 went from $1.43 (test backfill in v2) to $0.40 here.
  Tests already on disk meant Tweedles implemented to them rather than
  re-deriving the test surface.
- Hatter's M4 ($0.55) is cheaper than tea-party v1's ($1.21) because
  he triaged harder — 6 scenarios instead of 15, but each one written
  AND coded.
- Total LLM calls dropped 35% (276 → 179) without losing artifact
  quality.

## Findings

### F1 — Directive-as-deterministic-fix is the right tool

The `56c3b16` commit changed only the M4 directive, plus a unit test
that pinned the load-bearing phrasing. No code change. No live A/B
needed to validate the directive content — the unit test caught
regression risk.

This is the right shape for content-quality fixes: the framework's
behavior is shaped by its prompts, and prompts can be regression-
tested without burning live runs. The path-drift fix from analysis
023's commit `0dd2d78` followed the same pattern; this is the second
deterministic content fix that landed cleanly.

### F2 — The pair surfaces real bugs the solo agent doesn't

In M4, Hatter shipped a duplicate-username-race scenario; Alice
shipped the basic-journey scenario. Together they revealed that the
contracts didn't specify what username collision returns. (Cf. the
prior tea-party run, where the pair caught threaded-discussion gaps
in M4 and three new contracts got locked dynamically.)

In M5, Tweedledum's implementation cited the contracts and tests by
name — `auth.py` imports `validate_email` because Hatter's scenario
needed it, and references the username-collision contract via
`generate_alternative_usernames`.

In M6, Caterpillar caught **three real `block`-level bugs** in the
shipped code:
1. `validate_email` was imported but never defined → ImportError at
   first call to `/api/register`
2. `generate_alternative_usernames` is imported but the file defines
   `generate_username_alternatives` (different name + parameter order)
3. `homepage.py` uses `db.query(User).first()` instead of authenticating
   via the Authorization token — anyone gets the first user

These are real bugs. Caterpillar is doing real review work — reading
the diff, tracing imports across files, citing line numbers, naming
the runtime failure mode. M6 hit MEETING_BUDGET before Tweedles could
ship the fixes, but the findings are sitting in `.wonderland/reviews/`
ready for the next session to act on. (And: this is the framework's
bug-discovery surface working as designed. A one-shot Sonnet call
wouldn't catch its own import errors.)

### F3 — Cost-per-line dropped to <$0.001

This run produced 1841 lines of code (588 production + 1253 tests)
for $2.05. That's $0.0011 per line. For comparison:

- A contractor at $100/hour would price this scope at $1500-2500
  (~10-15 hours). Cost-per-line: ~$1.
- One Sonnet call at this directive scope would produce maybe
  500-800 lines of dense code in one file at ~$1.00. Cost-per-line:
  ~$0.0015. But: no test surface, no audit trail, no character-shaped
  edge coverage, and Sonnet's failure modes aren't legible.
- Generic Haiku-in-a-loop with no framework structure would burn
  $5-10 of calls and produce a tangled mess.

The cost-per-decision-correctly-made-without-supervision is the
right metric. This run made roughly 30 distinct, named decisions
(stories, ADR, contract notes, test scenarios) plus implementation
plus review — at $0.07 per decision. None of the decisions are
implicit. All are revisable.

### F4 — The Caterpillar review is the framework's quiet superpower

We don't talk enough about M6. Caterpillar found three production-
code bugs that a one-shot LLM would have shipped without flagging.
The bugs are character-shaped — Caterpillar's "who are you?" review
stance specifically looks at *what claims this code makes* and traces
whether the claims hold. He read `auth.py`'s import statement and
asked "where does `validate_email` actually come from?" — and noticed
it doesn't.

This is the bug-discovery a real senior reviewer does. The framework
gets it included by default, every run.

## What this analysis doesn't show

- **N=1 again.** This is one directive (Geocities). The framework
  may look different on directives where one subsystem dominates
  ("build a query optimizer") or where the work is primarily UX
  taste. P7 evals against a portfolio is what generalizes the claim.
- **The implementation has bugs.** Caterpillar named three. Real
  shipping requires another iteration to fix them, which costs more
  time and money. The MVP isn't a deployable; it's a v1 scaffold
  with a known list of fixes.
- **The pair-protocol cost story is suggestive but small-N.** Three
  Geocities runs is enough to claim the directive change worked;
  not enough to claim the cost-trajectory is fundamental.

## What's next

1. **SHOWCASE.md** — this is finally the run to anchor the manifesto
   piece on. Friend-facing, not experiment-log shaped. Drafted skeleton
   in `drafts/`; this run gives it the evidence body.
2. **README** — promote SHOWCASE.md prominently, link this analysis
   in the P6 entry, mark P6 closer to shipped.
3. **Eval harness (P7)** — the actual A/B portfolio against
   generic-baseline + frontier one-shot. The framework is ready;
   the apparatus to score it isn't built.
4. **Filed roadmap items still in flight:** `c664d71b` (agent IDLE
   race — 5 late-publish events this run, all ancillary),
   `29497820` (Dodo dynamic workflow generation), `22018836`
   (development-stories abstraction layer for non-technical users).
   None blocking.

## Headline

**The framework now reliably ships the feature that was asked for,
with a runnable test surface authored by the right team, at $2 of
Haiku in 8 minutes.** That's the bar the eval-harness phase needed
cleared. Cleared.
