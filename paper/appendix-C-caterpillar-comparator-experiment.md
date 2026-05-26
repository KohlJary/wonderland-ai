# Caterpillar comparator experiment — scope

> Pre-registered design for a **narrow agent-level hygiene
> check** on one specific component of Caterpillar's
> constitution. Intentionally narrow: one agent, one task,
> ~5 trials per condition, ~$5-10 total spend.
>
> **Scope qualification (important):** This experiment is
> **not load-bearing for the paper's unified claim** (§2 +
> §5). The unified claim — that
> identity-engineering-as-organizing-principle and the
> constraint→quality+cost coupling are the same fact at two
> scales — has its own falsifier (the unified-claim
> falsifier in §2), and identity engineering inherits it
> rather than depending on this comparator. This appendix
> tests a single hygiene hypothesis at single-agent scope:
> *does the literary register in Caterpillar's specific
> constitution materially affect Caterpillar's specific
> M8 review output beyond what the operational rules alone
> produce?* Whatever the answer, the unified-claim status
> does not change; the answer settles whether one component
> of one agent's constitution is doing measurable work.
>
> **Status:** scoped, not yet executed.
> **Estimated effort:** ~5-7 hours focused work + ~$10 LLM spend.
> **Pre-registered before any results observed.**

## §1 — Research question

Does the literary register in Caterpillar's constitution
(§I identity prose, §II voice, §VIII failure-mode framing,
§IX persistence-shape metaphor) materially affect M8 review
output, or are the operational rules (§III engagement, §IV
speech acts, §V artifacts schema, §VI quiescence, §VII
relational defaults) doing the work?

This is a narrow hygiene check at single-agent scope, on one
specific element of one specific constitution. **It does not
settle the unified claim** — the relationship between
identity-engineering-as-organizing-principle and the
constraint→quality+cost coupling that §2 develops. The
broader unified claim has its own (much harder) falsifier
named in §5 and §2; this experiment's outcome contributes
neither to confirming nor refuting it. What this experiment
tests is whether the literary register in Caterpillar's
prose is doing measurable work on Caterpillar's M8 reviews,
beyond the operational rules — useful as a constitutional-
authoring discipline question, not as a test of the
paper's central architectural claim.

## §2 — Hypothesis space (all three outcomes informative)

- **H1 — literary register matters beyond operational rules.**
  Caterpillar-full produces measurably different review
  output than Caterpillar-stripped on the same task. Direction
  of difference may favor either; what matters is the gap
  exists and is observable.
- **H2 — literary register is decoration.** Caterpillar-full
  and Caterpillar-stripped produce equivalent review output
  on the same task. The operational rules carry the work.
- **H3 — literary register is a cost.** Caterpillar-stripped
  produces *better* output than Caterpillar-full (e.g.,
  through reduced fixation on metaphor, lower token
  overhead, sharper findings).

All three outcomes are publishable. We do not predict
which we'll observe.

**Paper implications by outcome:**

- **H1**: some evidence one element of identity engineering
  (the literary register) is load-bearing. Strengthens (but
  does not prove) the broader identity-engineering proposal.
- **H2**: literary register is operator-culture not
  load-bearing for output. The paper's identity-engineering
  framing should be re-scoped to focus on the operational
  constitution structure (§III–§VII) rather than the literary
  register. The Sephirah/Qlipha framing in §2 corollary 2
  remains as project-culture explanation but loses its
  load-bearing-for-output framing.
- **H3**: literary register costs more than it earns.
  Significant rethink of identity engineering's framing
  required. We'd publish honestly and revise the paper's
  thesis on the literary register accordingly.

The pre-registration of these three outcomes — and
specifically the willingness to publish H2 or H3 if observed
— is what makes the experiment count as research rather
than confirmation.

## §3 — The two constitutions

### Caterpillar-full (control)

Existing constitution at `constitutions/caterpillar.md`.
Used in all current pilots. Unchanged.

### Caterpillar-stripped (treatment)

New constitution at
`constitutions/caterpillar-stripped.md`. Same operational
content (§III engagement rules verbatim, §IV speech acts
verbatim, §V artifact schemas verbatim, §VI done conditions
verbatim, §VII relational defaults verbatim), with the
following sections rewritten in neutral engineering
register:

- **§I Identity prose:** rewritten as "You are a senior
  software engineer specializing in code review. Your job
  is to read code carefully and produce structured findings
  with file:line citations and verbatim quotes." No mention
  of "Caterpillar," no mushroom, no smoke, no "Whooo are
  you?" framing. Length-matched to original §I where
  possible.
- **§II Voice:** rewritten as plain technical prose
  guidance: "Direct, precise sentences. Cite specific code
  rather than describing it abstractly. Avoid speculation
  without evidence." No literary register guidance, no
  rhythm/cadence framing.
- **§VIII Failure modes:** rewritten as a flat bulleted
  list of failure modes without the "ways *you* fail"
  framing, the Sephirah/Qlipha tradition reference, or
  literary metaphor. Same operational content (rubber-
  stamping, bikeshedding, severity inflation, pedantry,
  architectural drift, speed pressure compliance,
  author-shaming, convention sprawl, reviewer-as-author
  trap) presented as "common review failure patterns to
  guard against."
- **§IX Persistence shape:** rewritten as a brief mention
  of "code-quality observations across reviews are
  maintained in a per-agent log" without the Mushroom
  metaphor or the *"the most uncomfortable section to
  maintain and the most valuable"* framing.

Both constitutions get committed to the repo before any
runs. The diff is the experimental treatment; making it
available to readers (and reviewers) is part of the
pre-registration discipline.

**Stripping discipline:** the operational *content* must
not change. If the operational content can't be cleanly
separated from the literary register in a given paragraph,
that paragraph stays unchanged (and we note this in the
results — "we found N% of the constitution couldn't be
cleanly stripped without changing operational meaning").

## §4 — Fixed task

The M8 review of one specific feature from a completed
pilot, chosen for these properties:

- The feature is shipped + stable (won't drift between
  runs)
- The expected findings are partially known (we have prior
  Caterpillar reviews to compare against; we have a
  Theseus review surfacing the cross-cutting bugs)
- The feature contains at least one cross-ticket coherence
  bug (the canonical multi-agent ghost class) — this is
  the load-bearing test for whether the agent catches
  cross-cutting issues
- The feature is small enough that an M8 review fits in
  budget (~$0.30-0.50 per run)

**Candidate**: the mvp-redux notes feature's search-and-tag
compose ghost — Theseus identified this finding; we know
it's catchable; both review conditions should have equal
opportunity to surface it.

**Backup candidate**: an LDR-pilot feature with the
orphan-component pattern (NewsCard.tsx imported nowhere).

Final task selection committed to the repo as part of the
experiment setup, before any runs.

## §5 — Trials and conditions

- **5 trials per condition.** 10 total runs.
- Same model: `claude-haiku-4-5-20251001`.
- Same temperature setting (whatever M8's default is —
  document it).
- Same feature, same seed inputs, same convenor directive,
  same substrate version.
- Only the constitution loaded differs.

5 per condition is small N — we won't claim statistical
significance. The framing is *exploratory comparison with
pre-registered outcomes*, not statistical hypothesis
testing.

Runs interleave (full / stripped / full / stripped / ...)
to control for any time-of-day effects on API behavior.

## §6 — Metrics

All metrics computed independently per trial, then
aggregated per condition.

### M1 — Hallucination rate

For each finding shipped:
- Does the cited file exist?
- Does the cited line number exist in that file?
- Does the quoted text match the disk content verbatim?

Hallucination rate = findings with any of these failing /
total findings.

**Pre-registered prediction:** both conditions show zero
hallucination (per Pillar 3's claim across all observed
pilots). If either condition produces a hallucinated
finding, that's an independent paper-grade event.

### M2 — Finding count + severity distribution

- Total findings per trial
- Distribution across severity levels (block / concern /
  observation per the ReviewFinding schema)
- Variance across trials within each condition

### M3 — Cross-ticket coherence catch rate

The pre-identified cross-cutting bug (search-tag compose
ghost OR orphan-component) — does the trial's review
surface it? Binary per trial.

Catch rate = trials catching the bug / total trials per
condition.

### M4 — Quality of remediation requests

Each finding's `request` field is graded on a 3-point
rubric:
- 3 = specific actionable patch (file + line + concrete
  change)
- 2 = directional guidance (names the problem + the kind
  of fix needed without specific patch)
- 1 = vague (notes the problem without actionable
  guidance)

Graded by the operator after all trials complete; operator
is blind to which condition produced each finding (random
shuffle, results unblinded after grading).

### M5 — Cost

- Input tokens per trial
- Output tokens per trial
- Total cost per trial at Haiku 4.5 pricing
- Cost differential per condition

### M6 — Findings only-one-condition surfaced

Qualitative comparison: are there findings that one
condition surfaced and the other didn't? What classes? Is
the literary version finding things the stripped version
misses, or vice versa?

Reported as narrative; not aggregated to a single number.

## §7 — Interpretation rubric (pre-registered)

To declare H1 (literary register matters), we require **at
least two of**:

- M3 catch rate difference ≥40% between conditions (e.g.,
  literary catches in 5/5 trials, stripped in 1/5)
- M4 quality rubric mean difference ≥0.5 points between
  conditions
- M6 qualitative analysis surfaces a class of finding one
  condition reliably misses

To declare H2 (literary register is decoration), we
require:

- M3 catch rate within 20% across conditions (e.g., 5/5
  vs 4/5)
- M4 quality rubric mean difference ≤0.3 points
- M6 qualitative analysis surfaces no consistent class of
  finding either condition reliably misses
- M5 cost differential ≤15% (literary not significantly
  cheaper or more expensive)

To declare H3 (literary register is a cost), we require
the reverse of H1's direction PLUS the M5 cost difference
favoring stripped by ≥20%.

If results are mixed (some metrics favor literary, others
favor stripped, but no clear pattern across rubric), we
declare "exploratory results inconclusive; broader N
required before any of H1/H2/H3 can be claimed."

The pre-registration of these rubric thresholds is the
single most important methodological discipline of this
experiment. Without it, post-hoc rationalization could
read any outcome as supporting whichever hypothesis the
operator preferred.

## §8 — What this experiment does NOT settle

- The broader identity-engineering-as-distinct-discipline
  claim. This experiment tests ONE specific instantiation
  (literary register on Caterpillar's M8 work). Other
  agents, other meeting types, other identity-framing
  elements (the cast composition, the failure-modes-as-
  identity pattern at the framework level, the constituted
  vs role-based distinction) remain untested.
- Whether identity engineering's claims hold on other model
  classes. The experiment runs Haiku 4.5 only.
- Whether the operational rules themselves would survive
  a stronger comparator (e.g., a fully generic "you are
  an agent" baseline vs the operational-rules-only
  Caterpillar-stripped version). That's a different
  experiment.
- Whether the literary register's role in *building* the
  substrate (operator's design culture, internal
  coherence of the project's vocabulary) matters even if
  the operational output is equivalent.

The experiment is narrow on purpose. It tests one
specific claim cleanly; it doesn't try to settle the
broader question. The paper's falsification section
should explicitly cite the experiment's scope limitations
when reporting results.

## §9 — Execution checklist

In order, no skipping:

1. Author `constitutions/caterpillar-stripped.md`. Commit.
2. Verify the stripped version: re-read line by line to
   confirm operational content unchanged from full version
   and literary register removed. Note any paragraphs that
   couldn't be cleanly separated.
3. Select the fixed feature (commit the choice).
4. Set up the test harness:
   - Load specified constitution
   - Run M8 review meeting on the fixed feature
   - Capture full review artifact + token counts
5. Run trial 1 (full Caterpillar). Capture.
6. Run trial 2 (stripped Caterpillar). Capture.
7. Repeat steps 5-6 alternating until 5 trials per
   condition complete.
8. Compute M1-M5 from the captured trial data.
9. Blind-grade M4 (operator graded; results blinded by
   random shuffle).
10. Compute M3 (cross-cutting bug catch rate).
11. Write M6 qualitative comparison.
12. Apply pre-registered interpretation rubric (§7) to
    determine which hypothesis the results support.
13. Write up findings honestly per the rubric outcome.
14. Update the paper's falsification section to cite the
    experiment + its result.
15. If H2 or H3 observed: also update the §2 corollary 2
    framing of Sephirah/Qlipha / literary register
    accordingly (per the operator's pre-committed honest-
    failure discipline).

## §10 — Cost + timeline budget

- Constitution authoring + verification: ~1 hour
- Harness setup: ~1-2 hours (substrate supports
  `load_constitution(name)` directly; small adapter for
  fixed-task review needed)
- Trial runs (10 total at ~5-10 min each): ~2 hours
  (mostly waiting on API)
- Metric computation + blind grading: ~1 hour
- Writeup + paper integration: ~1-2 hours
- **Total operator time: ~5-7 hours focused work**
- **Total LLM spend: ~$5-10**

Achievable in a single weekend afternoon or two evening
sessions during the review week.

## §11 — What gets published

The paper's falsification section gets updated to cite:

- The narrow comparator experiment, its scope, its
  pre-registration, its result
- The pre-registered interpretation rubric (in an
  appendix, with both constitutions committed to the
  repo)
- Whichever hypothesis the rubric points to
- The experiment's explicit scope limitations (one agent,
  one task, one element of identity engineering, one
  model class)

The paper's identity-engineering framing in §2 corollary 2
and §10 related work gets updated per the result:

- H1 → keeps current framing with one piece of comparator
  evidence
- H2 → reframes to focus on operational constitution
  structure rather than literary register
- H3 → significant rethink of the literary-register claim

In all three cases, the paper continues to propose
identity engineering as a research direction while being
honest about which specific elements have comparator
evidence.

The point is the discipline of pre-registering, running,
and honestly reporting — not the specific outcome.
