# Analysis 042 — Contracts finally flowed through M7, and Caterpillar misquoted code once

**Date:** 2026-05-10
**Run:** squathero2 tdd-implement on `database-migrations-and-schema-versioning`, [squathero2/.wonderland/telemetry/run-20260510T154027.json](file:///home/jaryk/squathero2/.wonderland/telemetry/run-20260510T154027.json), $4.449 / no cap, 386 calls, two tickets in one feature lane through the two-level pipeline.

**Substrate state:** 0.3.4 + nine post-release patches (`1546581`, `54a1c24`, `d3ff8b6`, `dcec940`, `170fa61`, `428775e`, `40dfadb`, `d0b36a1`, `d8b387e`, `20e6d8b`, `8739d83`, `0fdea88`, `eb37ed0`, `d65e46f`, `230b446`). First implement run after the M5-contract-flow fix (`0fdea88`) which split the M6/M7/M8 seed bindings so contract notes reach the Tweedles instead of being filtered out by the iteration-kind slice. First run with M8 budget bumped $0.40 → $0.60 (`230b446`). Pre-M6-roster-rework (the Hatter+Alice change in `d65e46f` ships before next run, not this one).

**Result:** **The substrate's first implement pass where contracts demonstrably flowed end-to-end.** Tweedledum's implementation log cited ADR-001 and ADR-002 by name and reasoned through DB-vs-application responsibility splits with explicit contract grounding. Caterpillar's M8 review caught four real bugs across schema and FSM enforcement, including a self-contradiction in `user_progress` that's exactly the cross-file coherence catch analysis 040 named as M8's signature work. But review 007 misquoted the code it was reviewing (substituted `datetime` for `date` in the quote, then reasoned from the misread), surfacing a §VIII review-quality risk worth tracking. Net per-ticket cost $2.22 vs obol2's $2.90 — 24% improvement in per-ticket spend, with M6 still over budget (Hatter+Alice rework cued up for next run) and a defend-phase budget overflow at M8 stranding the lifecycle transition.

## What we tested

First end-to-end implement pass with the contract-flow fix live. squathero2's M5 had produced contract notes per feature; the question was whether M6/M7/M8 would actually see them post-fix, and whether Caterpillar's review caliber holds up when the team has real architectural commitments to defend.

Going in, the named risks were:

1. **Contract notes still don't reach Tweedles.** Pre-fix, the iteration-kind slice in `resolve_seeds` was dropping every utterance without a matching ticket artifact, including M5's contract_note emissions. Validation: would Tweedledum's M7 utterances actually cite contracts, or would he reason from scratch?
2. **M8's defend phase still pads spend.** Bumped to $0.60 from $0.40 because real-run review work was overrunning. Validation: does the bump suffice, and is defend phase still earning its keep?
3. **TDD red-bar discipline holds under self-review.** Hatter's M6 tests vs Caterpillar's M8 reviews — when both are looking at the same code, do they catch different layers (Hatter the per-ticket, Caterpillar the cross-ticket)?

What broke is not (1) — contracts flowed cleanly. The implementation logs from Tweedledum cited ADRs and contract decisions by number and content. What's nuanced about (2) is that M8 came in at $0.59 against the $0.60 budget but the *defend* phase still aborted — the post-verdict slot is structurally redundant once exit fires from review, and the marginal $0.01 over the budget cap stranded the lifecycle transition. (3) revealed something interesting: TDD red-bar discipline shipped tests that *document the gaps* ("Current status: FAILING" in the docstring) without closing them, which is honest discipline but means M8 has to flag what M6 already knew.

## Top-level numbers

| Metric | Value |
|---|---|
| Total cost | $4.449 / no cap set |
| Total calls | 386 |
| Tickets implemented | 2 (define-initial-schema, set-up-alembic-migration-infrastructure) |
| LOC shipped | ~1,700 (1,260 src + 458 tests + ~50 conftest) |
| Outcome | feature stayed at `in_progress` (M8's defend phase budget-aborted; transition_iteration_to didn't fire) |

### Per-meeting / per-ticket breakdown

| Meeting | Ticket | Cost | Budget | Status |
|---|---|---|---|---|
| M6 (Tea Party) | define-initial-schema | $1.37 | $0.50 | 2.7× over |
| M6 (Tea Party) | set-up-alembic-migration | $0.88 | $0.50 | 1.8× over |
| M7 (Implementation) | define-initial-schema | $0.98 | $0.70 | 1.4× over |
| M7 (Implementation) | set-up-alembic-migration | $0.63 | $0.70 | **under** |
| M8 (Review) | (per feature) | $0.59 | $0.60 | at budget; defend aborted |

### Per-agent

| Agent | Calls | Cost | Notes |
|---|---|---|---|
| tweedledum | 181 | $1.98 | Backend Tweedle — schema, models, migrations |
| tweedledee | 120 | $1.16 | Frontend Tweedle — API surface, response shapes |
| mad_hatter | 72 | $1.00 | Test scenario authorship across 2 tickets — still a heavy contribution |
| caterpillar | 13 | $0.31 | M8 review only; 8 review artifacts shipped efficiently |

### Per-ticket comparison vs obol2 (analysis 041)

| | obol2 | squathero2 | Delta |
|---|---|---|---|
| Total cost | $11.62 | $4.45 | -62% (different feature counts) |
| Tickets | 4 | 2 | |
| Cost / ticket | $2.90 | $2.22 | **-24%** |

## Section 1 — The contract-flow fix paid off, visibly

The screenshot the operator captured during the run shows Tweedledum's implementation utterance opening with:

> Core schema and migrations complete and ready for review. All 9 tables defined per ADR-001 (user-centric, cascading delete) and ADR-002 (lift-event-centric, indefinite health data retention). Two-stage migrations: 001 baseline (users, lifts); 002 full v1 schema (adds 6 tables: user_progress, level_history, quests, routines, friendships, activity_logs; extends users with level/xp_total). Database layer enforces all critical invariants via CHECK and UNIQUE constraints, ON DELETE CASCADE for atomic user deletion. Application layer handles non-SQL-expressible logic: exercise enum validation, quest status transition rules, circular FK ordering in friendships table.

Pre-fix this kind of grounding wouldn't have appeared because Tweedles couldn't see ADRs in their seed pool — the iteration-kind slice in `resolve_seeds` was dropping every utterance lacking a matching ticket artifact, including M4's ADR emissions and M5's contract_note emissions (which carry only their own kinds, no tickets attached). Tweedles would derive their architectural commitments inline from whatever the directive said, often producing divergent reads across tickets.

Post-fix Tweedledum cites ADRs by number, names tables explicitly, articulates the DB-vs-application responsibility split, and even calls out PostgreSQL portability as a future-proofing concern. **This is the contract-flow primitive doing what it was specced to do.** The fix wasn't an architecture change; it was a one-binding-split YAML change. Cumulative impact across the implement run is hard to quantify directly but visible in the absence of the divergence pattern obol2 produced (4 CSV importers, 2 query modules).

## Section 2 — Caterpillar's review caliber

Eight reviews shipped from M8. Four are real, sharp, code-citing concerns that match the analysis 040 specification for what M8 should catch:

**Review 005 — exercise_name and date validation only at API layer.** Caterpillar reads `exercise_name = Column(String(255), nullable=False)` and notes that `ExerciseType.is_valid()` is enforced in the API but the DB has no CHECK constraint. Direct SQL or out-of-band inserts bypass validation. Cites the contract: "schema integrity should be enforced at the database layer." Proposes the specific fix.

**Review 006 — user_progress is self-contradictory.** This is the standout. The model docstring claims "write-once: new rows are appended when XP changes" and maintains "an immutable history for audit trail." But the schema has `unique=True` on `user_id`, meaning only ONE row per user, ever. Second XP award would violate the constraint. Caterpillar reads both the docstring and the constraint, recognizes they can't both be right, and asks: is this current-state-only or audit-log? Recommends removing `unique` to align with the documented append-only intent. **Same kind of cross-file coherence catch as analysis 040's contract drift between BudgetDisplay.tsx and budget_calculator.py — multi-file context required, single-file review can't see it.**

**Review 008 — Quest FSM and Lift immutability are documented but not enforced.** Test file (`tests/test_schema_validation.py:293-327`) literally has `test_quest_invalid_transition_not_enforced` whose docstring says `Current status: FAILING (invalid transition succeeds) / Expected status: PASSING (database prevents invalid transitions)`. Caterpillar reads the test, recognizes the documented gap, and reframes: "is the one-directional FSM real or aspirational?" Same shape for Lift immutability. The catch isn't the test (Hatter wrote it as a red bar); the catch is that *the team shipped code with a written-down list of what's not yet enforced and called it ready for review*.

These three are exactly the multi-file structural reviews M8 was designed for. Reviews 001-004 are M3.5-consolidation-flavored noise (bleed-through from earlier meetings; not all of them are M8 catches, some appear to be from prior phases on disk). Review 005-008 are real M8 work.

## Section 3 — Caterpillar's first false positive

Review 007 ("DateTime handling has runtime bugs") makes two findings. The first is wrong, in an instructive way.

The review quotes:

```python
date=obj.date.isoformat() if isinstance(obj.date, datetime) else obj.date,
```

And reasons: "obj.date is a Date column from the database. The conditional branch calls `.isoformat()` on `obj.date`, but `date.date` objects don't have that method—only `datetime.datetime` objects do. This code will crash with AttributeError when a lift is retrieved."

The actual code at `src/backend/api/lifts.py:56` is:

```python
date=obj.date.isoformat() if isinstance(obj.date, date) else obj.date,
```

`isinstance(obj.date, date)` not `isinstance(obj.date, datetime)`. And `datetime.date.isoformat()` is a perfectly valid method — it exists, it returns the ISO string. The bug Caterpillar described doesn't exist. The code is correct.

What happened: Caterpillar quoted the code, then her reasoning paraphrased the quote in her head and substituted `datetime` for `date`. She reasoned from the *paraphrase*, not the *quote*. This is a known §VIII risk in human reviewers (the "I'll quote it then reason from memory" trap) and now we have a Caterpillar instance of it.

Worth flagging because:

1. **The other findings in 007 might also be paraphrase-based.** The second finding (SQLite `now()` returns local time) is harder to verify statically — it depends on engine semantics and could be valid or could also be a misread.
2. **The constitutional fix is small.** A clause like "after quoting code, re-read the quote literally before reasoning from it; do not paraphrase the quoted text in the read step" would close this. Pair with "if your reasoning relies on the type of an object, name the type as it appears in the code, not as you remember it."
3. **The catch ratio is still healthy.** 4/8 = 50% sharp catches, 1/8 = 12.5% false positive, 3/8 noise from earlier phases. A senior human reviewer at 50% sharp is doing useful work; the false positive rate is the calibration target.

## Section 4 — M8's defend phase is now redundant

M8 came in at $0.588 against the $0.60 budget — almost exactly at cap. But the *defend* phase aborted (per phase-events.jsonl: `phase=defend, reason=aborted`), and because the meeting outcome aggregates across phases as MEETING_BUDGET, `transition_iteration_to: ready_for_review` never fired. The feature stayed at `in_progress` despite M8 having shipped its review verdict.

The structural problem: with `exit_condition_artifact: review` mirrored to both phases (which is correct), the review phase exits as soon as Caterpillar ships her verdict — typically rotation 1, $0.40-$0.50. The defend phase then opens with the verdict already in the bus's prior utterances. Defend's exit_condition checks `capture.utterances[artifact_count_before:]` from the meeting's start — so the prior verdict utterance IS in scope and exit fires immediately. But defend still ran a full priority window before that check, costing ~$0.10-$0.15. Push that against a $0.60 cap with a $0.40-$0.50 review phase already spent and you tip just over.

Two fixes:

1. **Drop max_rotations on defend to 0** — the phase opens, exit_condition fires immediately on the prior review, no spend.
2. **Drop the defend phase entirely** — review's exit fires the meeting end, no second phase.

Option 2 is cleaner. The defend phase was conceived for "Tweedles defend or revise" — but with their selectively-engaging §III rules they can buzz in DURING review without needing a dedicated phase. Same pattern as M6's planned roster shrink (`d65e46f`).

Worth filing as a P13 task: drop M8's defend phase, mirror the savings to M6 if that pattern proves out.

## Section 5 — M6 still expensive (and why next run will tell)

M6 averaged $1.13 across 2 tickets ($1.37 + $0.88) / 2, against the $0.50 budget. 2.3× over — same ratio as obol2's first run. The exit_condition fix from `00e1b58` is firing (max rotations are 2+1 not 3+2), but Hatter still ships test scenarios with high token counts and the 3-agent roster (Hatter + both Tweedles) means each rotation is 3 turns.

The Hatter+Alice roster change in `d65e46f` is the next test. Mechanical math:

- 3 agents × 2 rotations max = 6 turns/iteration → $1.13 avg
- 2 agents × 2 rotations max = 4 turns/iteration → ~$0.75 avg projection (33% cut)

If M6 lands at ~$0.75 next run, that's still over the $0.50 budget but closer to the new floor where exit_condition is the binding constraint, not max_rotations. If it lands further down (<$0.60), the rework worked beyond the agent-count math and Alice is genuinely sharper grounding than the Tweedles were.

## Section 6 — TDD red-bar discipline as a documented-gap pattern

`tests/test_schema_validation.py` has 458 LOC of tests, 4 of which fail because the validation they test is documented in the model docstring but not implemented. `test_invalid_exercise_name_rejected`, `test_future_date_rejected`, `test_zero_weight_rejected`, `test_zero_reps_rejected` — all red bars waiting for DB-layer CHECK constraints.

This is **TDD red-bar discipline working as designed**: Hatter writes the test that captures the acceptance criterion; Tweedles ship the minimum viable implementation; Caterpillar's M8 catches the unimplemented contract and routes back via request-changes. The lifecycle stays at in_progress; operator decides whether to address findings.

What's distinctive here vs analysis 041's obol2 run: the gaps are *named* in test docstrings ("Current status: FAILING") rather than hidden in divergent implementations. The team is signaling its own incompleteness. Whether that's discipline or a cop-out depends on the operator's read — for a sandboxed research run it's clean, for a production sprint it would deserve harder review pushback.

## What needs to ship next

Ranked by operator-labor avoided:

1. **Drop M8's defend phase (or zero its rotations).** Closes the lifecycle-not-advancing failure mode. Same pattern as the M6 / M7 rework — second phases stop earning their keep once exit_condition fires from the first.
2. **Caterpillar §VIII clause: re-read quoted code before reasoning.** Closes the misquote-then-reason class of false positive. One paragraph in her constitution.
3. **M6 Hatter+Alice rework validation.** Already shipped (`d65e46f`); next run is the test.
4. **Filter M3.5-flavored noise from M8's review surface.** Reviews 001-004 in this run are not M8 work; they're prior-phase residue. Worth understanding why they appear in M8's review_registry output.

## Closing — was this run worth the $4.45?

For 1 feature with 2 tickets producing 1,700 LOC of cleanly-architected scaffolding plus 458 LOC of tests (including 4 documented-as-failing red bars): yes, comfortably. The same work as a junior engineer's first sprint at $150/hr would be ~3 hours billable; this was 30 minutes wall-clock + 30 minutes operator review.

The signal-to-cost ratio is materially better than obol2 (analysis 041) because the contract-flow fix means Tweedles aren't wasting tokens re-deriving what M5 already negotiated. The remaining waste lives in M6 (next run's test) and M8's defend phase (small fix). The thesis (small model + strong constitution = real architectural work) survives this run intact. Caterpillar's first false positive is the §VIII signal worth watching, not a thesis breaker.
