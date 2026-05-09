# Run Grading Rubric

Structured walkthrough for analyzing a Wonderland test run. Walk it top to bottom; don't skip sections. The output of this walkthrough is the *raw material* for a written analysis (e.g. `analyses/NNN-<slug>.md`). The rubric is the *checklist*; the analysis is the *story*.

This is the qualitative analog of the eventual P7 eval harness — informal, manual, but consistently structured so runs can be compared meaningfully across analyses.

---

## I. Run-level summary

**Quantitative facts. Pure data extraction; no interpretation.**

- [ ] Total wall-clock elapsed: `_____s`
- [ ] Total cost: `$_____ / cap $_____`
- [ ] Total LLM calls: `_____`
- [ ] Outcome of run: `___` (completed all meetings / GLOBAL_BUDGET / aborted / interrupted)

**Per-meeting summary** — fill in for every meeting in the workflow:

| Meeting | Outcome | Time | Calls | Cost / Cap |
|---|---|---|---|---|
| M1 | | | | |
| M2 | | | | |
| M2.5 (tdd only) | | | | |
| M3 | | | | |
| M4 | | | | |
| M5 | | | | |
| M6 (tdd only) | | | | |

**Per-agent cost breakdown** — from `.wonderland/telemetry/run-*.json`. Note any agent that's surprisingly absent or surprisingly dominant.

| Agent | Calls | Cost |
|---|---|---|
| | | |

**Source commands:**
```bash
grep -E "M[0-9.]+.*(START|END)|Total elapsed|Total cost" /tmp/<project>.log
python3 -c "import json,glob; d=json.load(open(glob.glob('/tmp/<proj>/.wonderland/telemetry/run-*.json')[-1])); ..."
```

---

## II. Per-meeting walkthrough

**For each meeting, ask:**

### Did the meeting produce its intended artifact?

Each meeting has a defined output kind. Verify the artifact actually shipped:

| Meeting | Expected primary artifact | Where to look |
|---|---|---|
| M1 (Caucus Race) | story, adr, ruling | `.wonderland/stories/`, `architecture/`, `rulings/` |
| M2 (Rabbit's Errand) | ticket | `.wonderland/tickets/` |
| M2.5 (Caterpillar) | feature | `.wonderland/features/` |
| M3 (Tweedles) | contract_note (some agreed) | `.wonderland/contract-notes/` |
| M4 (Tea Party) | test_scenario + actual `tests/*.py` files | `.wonderland/test-scenarios/` AND project `tests/` dir |
| M5 (implementation) | production code on disk + implementation utterance | project `src/` and/or `frontend/` dirs |
| M6 (Trial) | review + (optionally) follow-up implementation | `.wonderland/reviews/`, `implementations/` |

If a meeting completed COMPLETE but produced **no artifacts of its primary kind**, that's a red flag — record what *did* happen instead.

### Was the meeting cost reasonable?

Compare against the meeting's cap and against prior runs of the same workflow+directive. A meeting at 50% of cap is healthy; at 90%+ it's stressed; over cap (MEETING_BUDGET) is a red flag.

### Are the artifacts well-formed?

Open 1-2 sample artifacts and check:

- **stories**: name a persona, describe a need, list acceptance criteria
- **tickets**: have title, owner, tier, estimate, description, dependencies
- **features**: have title, description, tickets, personas, stack_span, tier
- **contract_notes**: name the seam, list both sides' obligations, have a state (proposed/agreed)
- **test_scenarios**: describe a real failure mode, name the persona or system invariant
- **reviews**: cite specific files and line numbers; severity is set; concrete enough to act on

### Per-meeting deep dives

**M2.5 (Caterpillar) — the hardest to grade. Specific checks:**

- [ ] Did Rabbit emit `feature` decisions, or did he choose silence? (silence = directive failure)
- [ ] Aggregation ratio: `features count / tickets count`. Lower than 1.0 means real composition; ≥1.0 means 1:1 renaming (acceptable but not the goal). 0.5-0.7 is healthy aggregation.
- [ ] Does each feature name a persona from M1 stories? (anti-bag-of-tickets check)
- [ ] Does each feature name a stack_span? (M3 needs this)
- [ ] Did Caterpillar speak? Was his intervention substantive (challenged a feature claim) or default-silence?
- [ ] Did Alice push back on any feature for story-coherence reasons?

**M4 (Tea Party) — scope discipline check:**

- [ ] How many test_scenarios shipped? Compare to feature count — should be ~1-3 per feature, not 5-10+.
- [ ] How many test files on disk? `ls tests/test_feature_*.py | wc -l` — should match features.
- [ ] Does each test scenario reference a specific feature, or is it system-wide-invariants? (system-wide = scope leak from M4 into M6's territory)
- [ ] Did M4 hit MEETING_BUDGET? If yes, sprawl-pattern returning.

**M5 (implementation) — actually-running check:**

- [ ] Did M5 actually deliberate? (calls > 0; not 0/0s)
- [ ] Did Tweedles use `run_tests`? Look for the tool in the bus utterances or in bash-style telemetry.
- [ ] How many production files shipped? Both halves of stack (frontend + backend) or just one?
- [ ] Did any "implementation" speech-acts come *after* M5 closed (late-publish suppressions)?

**M6 (Trial) — review depth:**

- [ ] How many findings did Caterpillar surface? (review artifact count)
- [ ] Are findings concrete (file:line)? Or vague?
- [ ] Did Tweedles ship fix-implementations in M6 in response to findings?
- [ ] Did M6 hit MEETING_BUDGET before the review-and-fix loop closed?

---

## III. Output verification

**Run the shipped tests yourself:**

```bash
cd /tmp/<project>
uv venv && uv pip install -e ".[dev]"
.venv/bin/python -m pytest tests/ 2>&1 | tail -5
```

Record:
- [ ] Tests passing: `___ / ___`
- [ ] Tests failing: `___ / ___`
- [ ] Tests skipped: `___ / ___`

**Cross-stack coverage:**

```bash
find /tmp/<project>/src -name "*.py" -newer /tmp/<project>/.git/HEAD | wc -l   # backend
find /tmp/<project>/frontend/src -name "*.tsx" -o -name "*.ts" -newer /tmp/<project>/.git/HEAD | wc -l   # frontend
```

- [ ] Backend files shipped: `___`
- [ ] Frontend files shipped: `___`
- [ ] Imbalance ratio: `frontend / backend = ___` (~0.5-1.0 is healthy; <0.3 is concerning)

**Code-smell smoke check** (open 1-2 production files):
- [ ] Does the code at least import without `ImportError`?
- [ ] Are types coherent (functions called with right argument shapes)?
- [ ] Are there obvious unimplemented stubs (`raise NotImplementedError`)?

---

## IV. Behavioral signals

**Did the cast behave in character?**

- [ ] **Alice's grounding voice fired in M2 / M2.5 when expected** — look for `concern` utterances from her in those threads. If she went totally silent, that's a missed grounding pass.
- [ ] **Caterpillar's "what does this claim?" stance is visible** — his M6 findings should reference *what the code claims* (not just bugs in isolation).
- [ ] **Cheshire Cat's silences were correct** — he should default to silence in M2/M2.5 unless architecture is implicated. Speaking too much in M2 is failure-mode.
- [ ] **White Rabbit didn't drift past his lane** — he should not be issuing proposals or implementations.
- [ ] **Tweedles defended their contracts under M6 pressure** — they shouldn't capitulate to every Caterpillar finding without considering it.

**Failure-mode check (per constitutional §VIII):**

| Character | Failure mode | Did it appear this run? |
|---|---|---|
| Alice | Adding stories during implementation | |
| Cheshire Cat | False certainty | |
| White Rabbit | Anxious-thoroughness, scope creep | |
| Mad Hatter | Scenario sprawl, severity inflation | |
| Tweedles | Implementation drift from contracts | |
| Caterpillar | Review-paralysis, finding-inflation | |
| Queen of Hearts | Ruling without grounding | |
| Dodo | Performing orchestration | |

If a failure mode appeared, was it caught (by the grounding-voice partner) or did it ship?

---

## V. Failure modes / red flags

**Substrate-level issues to look for:**

- [ ] **Empty-body utterances on the bus.** Search log for `body=''` or empty preview content. Empty bodies cause Anthropic API BadRequest later.
- [ ] **Late-publish accumulation.** Count `late-publish` events in the log. Healthy: <5 per run. Concerning: 10+.
- [ ] **Parse retries that didn't recover.** Search for `deliberate() raised` (vs `parse retry succeeded`). Each one is a lost turn.
- [ ] **API errors (BadRequest, etc).** Any `BadRequestError`, `RateLimitError`, etc. in the log.
- [ ] **Cross-meeting event leakage.** Did any meeting end abruptly with 0 calls / 0s? (regression of the bug fixed in `ede5651`)
- [ ] **Premature thread quiescence.** Look for `running → quiescent` immediately after meeting start with no agent utterances.

**Workflow-level:**

- [ ] Did any meeting hit `MEETING_BUDGET` and cut off mid-work?
- [ ] Did the run hit `GLOBAL_BUDGET` before completing all meetings?
- [ ] Did wall-clock `TIMEOUT` fire?

---

## VI. Cross-run trajectory

**Compared to the most recent prior run with the same workflow + directive:**

| Metric | Prior run | This run | Δ |
|---|---|---|---|
| Total cost | | | |
| Total calls | | | |
| Test pass rate | | | |
| Production lines shipped | | | |
| MEETING_BUDGET caps fired | | | |

**Compared to the same workflow on different directives** (rough trajectory check):

| Metric | This run | Last 3 runs avg |
|---|---|---|
| Cost-per-line | | |
| Test pass rate | | |
| Cross-stack imbalance | | |

If a metric is moving the wrong way: investigate. If it's moving the right way: name what we changed that drove it.

---

## VII. Headline / overall grade

**Two questions to settle before writing the analysis:**

1. **Did the framework do what it was supposed to?** (Did each meeting produce its intended output? Did the pipeline close end-to-end?)
2. **Was the output good?** (Tests pass? Code is coherent? Findings are real? Cross-stack covered?)

A run can answer YES to (1) and NO to (2) — that's a "framework correctness, output quality" split. The analysis story is different in each case.

**Suggested grading band:**

- **Banner run** — both YES, and at least one metric improved noticeably vs prior runs. Worth a major analysis writeup; potentially README-callout-grade findings.
- **Solid run** — both YES, no surprises. Brief analysis; main interest is trajectory data.
- **Substantive failure** — partial NO on (1) or (2). Analysis explains what failed, what survived, what the next iteration should target.
- **Wash** — run completed mechanically but produced ~nothing of value. Document briefly; iterate the directive or substrate before another run.

Pick the band first; write the analysis at the right intensity.

---

## VIII. Analysis writeup template

Once the rubric is filled out, the analysis follows naturally:

```markdown
# Analysis NNN — <slug>

**Date:** YYYY-MM-DD
**Run:** <directive name>, <workflow>, <one-line state of branch>
**Snapshot:** [analyses/data/NNN-<slug>/](data/NNN-<slug>/)
**Result:** **<one-line headline>**

## Headline numbers
[from §I]

## What we tested
[the specific changes shipped in this branch since prior analysis]

## Findings
F1 — ...
F2 — ...
[each finding has: the observation, the evidence, the implication]

## What this analysis doesn't show
[explicit caveats]

## What's next
[concrete next moves: bug fixes, directive iterations, new experiments]

## Headline (closing)
[the same one-liner from the top, but elaborated with what survives the analysis]
```

---

## IX. When the rubric itself needs updating

If a run surfaces a *category* of finding the rubric doesn't have a slot for, add the slot. The rubric should grow as the framework's failure-mode space gets explored. Document the rubric update in the analysis that motivated it.

If a section never gets filled in across 5+ runs, consider deleting it — dead checks are noise.

The rubric is itself an iterative artifact, not a fixed contract.
