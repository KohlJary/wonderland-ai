# Evidence chapter source

> Synthesis of paper-grade evidence claims from across the
> Wonderland project's observational record. Five pillars,
> each with a claim, mechanism, concrete pilot evidence, and
> honest scope. Source material for the paper's Evidence
> chapter — companion to workflow-walkthrough.md (architecture)
> and cast-walkthrough.md (cast). Code-quality-mvp-demo2.md
> supplies the artifact-level evidence the pillars predict.

## What counts as evidence here

This artifact distinguishes three observational classes:

| Class | What it is | Counts as paper evidence? |
|---|---|---|
| **Documented pilot finding** | Behavior observed during mvp-demo or mvp-demo2 with concrete cost / artifact / utterance citations. | Yes. |
| **Operator observation, unsolicited** | The operator noticed a property of the output without being prompted to look for it. | Yes — qualitative but high-signal. |
| **Hypothesis** | A possible property the system has, consistent with some observations but not tested rigorously. | No — explicitly excluded with reasoning. |

The five pillars below are all class 1 + 2. One observation
that fits class 3 (the "Haiku may be architecturally optimal"
hypothesis) is explicitly excluded; see [§Excluded
observations](#excluded-observations) at the end.

A note on the cleanness of the evidence: most of it comes
from two pilots (mvp-demo + mvp-demo2). N=2 is a small sample
in research terms. The pillars are framed as *observations
with mechanism*, not *proven properties* — the mechanism
makes each claim falsifiable in future pilots even where the
current N is small.

---

## Pillar 1 — Quality-cost coupling

### Claim

In Wonderland, **output quality and per-run cost move in the
same direction**, not against each other. Every substrate
improvement shipped to date has produced both higher-quality
output AND lower per-feature cost.

This inverts the conventional LLM/agent intuition that "more
quality = more tokens = more cost." Identity engineering +
substrate constraints decouple them.

### Mechanism

Better substrate constraints narrow the possibility space the
agents have to negotiate. Fewer concerns to surface, fewer
Caterpillar clarification rounds, fewer Rabbit re-emissions,
fewer redundant tool calls. The agents converge faster because
*there's less for them to legitimately worry about*. Quality
goes up because scope drift is fenced in; cost goes down
because the convergence path is shorter.

The architectural property: **constraints aren't a tax on
quality, they're a forcing function for it.** When the agent
grammar is tighter, the agent has fewer ways to drift, and
the path to a correct answer is shorter than the path to a
drift-then-recover.

### Concrete pilot evidence

Per
[`project_quality_cost_inversion.md`](../../.claude/projects/-home-jaryk-wonderland-ai/memory/project_quality_cost_inversion.md):

- **mvp-demo M2/M3/M3.5 cost dropped after active-milestone
  scope propagation shipped** — the substrate fix narrowed
  what each meeting was responsible for, and the per-meeting
  spend dropped accordingly while output quality (no
  cross-milestone scope-creep) went up.
- **validation5 cost-per-feature dropped after scoped retract
  + tea-party skip shipped** — Caterpillar gained the
  `retract` primitive (cheaper than `delete_file` because it's
  scoped to slugs); review-synthesized tickets gained a
  tea-party skip (saved ~$0.50/ticket). Both improved output
  + reduced cost.
- **mvp-demo → mvp-demo2 pilot-level contrast.** Per
  [`project_first_tier2_pilot_completion.md`](../../.claude/projects/-home-jaryk-wonderland-ai/memory/project_first_tier2_pilot_completion.md):
  mvp-demo cost ~$5+ in dead-end wedge runs and delivered a
  partial artifact for ~$40. mvp-demo2 cost ~$1 in wedge runs
  and delivered a complete artifact for $83.78. The substrate
  matured between pilots; both quality AND cost-efficiency
  improved.

### Honest scope

- N=2 pilots. The coupling has held every time it's been
  observable; we don't claim it's universal across all
  possible substrate changes.
- The coupling is observed at the *substrate-iteration* level,
  not the *per-model* level — we haven't shown that
  Wonderland-on-Haiku produces higher quality than
  Wonderland-on-Sonnet at lower cost. That's a different
  comparison (a baseline experiment the
  [code-quality artifact](./code-quality-mvp-demo2.md#8-comparison-baselines-recommended-follow-up)
  recommends).
- The mechanism (constraints narrow possibility space) is the
  paper's predictive claim; if a future substrate change
  improves output but increases cost, that would be a
  yellow-flag counterexample worth investigating (likely
  signal: the change is doing the agents' work for them
  rather than constraining their grammar).

### Where this lands in the paper

This is the surprising-finding section. The conventional
intuition is the foil; the architecture is the explanation;
the cross-pilot cost data is the receipt. Frame the section
title as something like "Quality-cost coupling under identity
constraints" — the property is architectural, not accidental.

---

## Pillar 2 — Multi-lens identity-anchored review

### Claim

Code that ships through Wonderland is reviewed by **N
distinct epistemic frames by construction** — Hatter's edge
enumeration, Queen's adversarial scrutiny, Caterpillar's
coherence reading, Cat's architectural smell, Alice's
persona grounding. Each agent over-applies their lens, and
the over-application is the *feature*. The result is code
that accounts for considerations a single solo-agent
generation would miss.

This is the **mechanism by which quality emerges** in
Wonderland. Pillar 1 (quality-cost coupling) is the
observable effect; multi-lens review is what produces the
quality side of the coupling.

### Mechanism

Each agent's §VIII (failure modes) section pins them to a
particular epistemic frame. Hatter's characteristic failure
is *scenario sprawl* — generating too many edge cases.
Queen's is *severity inflation* — over-flagging security.
Caterpillar's is *severity inflation in code review* —
over-flagging coherence issues. Each is constitutionally
biased toward *over-applying* their lens.

Solo-agent generation gets one lens — whichever the prompt
happens to evoke. Multi-agent generation with
identity-anchored failure modes gets N distinct lenses by
construction. Code that ships isn't "single-agent generation
reviewed once"; it's "single-agent generation that survived
being read through N distinct epistemic frames, each prone to
over-application."

The architectural choice: failure-modes-as-identity (per
[`project_failure_modes_thesis.md`](../../.claude/projects/-home-jaryk-wonderland-ai/memory/project_failure_modes_thesis.md))
isn't a quirk — it's the design decision that produces
multi-lens review.

### Concrete pilot evidence

Per
[`project_multi_lens_review_produces_quality_code.md`](../../.claude/projects/-home-jaryk-wonderland-ai/memory/project_multi_lens_review_produces_quality_code.md),
during the mvp-demo2 Tier 2 pilot:

> The operator observed unsolicited: "we're not just shipping
> code, it's *quality* code. They're accounting for all types
> of shit I never would have thought to through the review
> passes."

The unsolicited framing is significant: the operator wasn't
looking for quality evidence; they noticed it.

The
[code-quality artifact](./code-quality-mvp-demo2.md) supplies
the receipts that back this observation:

- `_escape_like_pattern` + `_safe_ilike` discipline
  (`notes.py:196-246`) — the cold reviewer called this
  *"exemplary. … I almost never see this discipline outside
  hardened codebases."* The pattern emerged from Hatter's
  M6 scenario about LIKE wildcards, Queen's security framing
  in M4, Caterpillar's M8 review catching the
  contract-not-enforced-at-call-site issue.
- `ensure_tz_aware()` (`models.py:114-131`) — handles
  SQLite-naive vs aware vs missing datetimes. Caterpillar's
  M8 cross-ticket coherence check would have surfaced any
  cross-endpoint datetime inconsistency.
- DOMPurify-before-`dangerouslySetInnerHTML` (`Preview.tsx:33`)
  — Queen's M4 security framing on user-provided markdown.
- Severity-tagged tests using Hatter's vocabulary —
  `test_search_wildcard_issues.py` cites a scenario artifact
  GUID and demonstrates the bug *before* the fix existed.

No single agent would have produced this code alone. The
discipline emerges from the multi-lens pass.

### Honest scope

- This is **NOT** "Wonderland reviews code better than
  humans." It's "Wonderland's review catches things one
  would-be-solo developer might not."
- This is **NOT** "any multi-agent system works this way."
  It's specifically the identity-with-characteristic-failure-modes
  architecture. Generic "more agents = more eyes" doesn't
  capture it — each agent's lens has to be distinct AND prone
  to over-applying for the breadth to work.
- The operator's observation is qualitative; we don't
  dress it as quantitative. But qualitative observation from
  an experienced operator IS evidence, just a different kind.

### Where this lands in the paper

The mechanism section under Identity Engineering. Connect
forward to quality-cost coupling (Pillar 1) — multi-lens
review is the architecture, quality is the output,
quality-cost coupling is the surprising side effect of doing
this on a small model.

---

## Pillar 3 — Schema-as-safety: forced citation prevents hallucination

### Claim

Forcing a small model to ship findings in a structured
schema with required verbatim citation makes hallucination
**structurally harder than honest reading**. Across 7+
Caterpillar M8 review passes on Haiku 4.5 during mvp-demo,
every review finding was grounded — citing real code at real
`file:line` locations with verbatim quotes matching disk.
Zero hallucinated findings.

This is non-trivial. The standard small-model failure mode on
code review is fabrication: "this function on line 47 has a
race condition" when line 47 doesn't have a function.

### Mechanism

Per
[`project_caterpillar_no_hallucination.md`](../../.claude/projects/-home-jaryk-wonderland-ai/memory/project_caterpillar_no_hallucination.md),
four reinforcing constraints keep the agent grounded:

1. **Forced citation structure.** The `ReviewFinding` Pydantic
   schema requires `location` + `quote` + `read` + `concern`
   + `request`. Hallucinating that whole tuple coherently is
   much harder than hallucinating a sentence — the agent has
   to actually open the file to fill it out.
2. **`verify_imports` tool** (T-v5) gives a static-time probe
   for the most common hallucination class (claimed-but-missing
   imports / symbols). Cheap (~$0.01-0.05/review); mechanical.
3. **Code-as-ground-truth + convergent self-repair** (see
   Pillar 4): even if a hallucinated finding slipped through,
   the next review pass would re-read the code and not find
   what the prior finding claimed. Hallucinations are
   self-extinguishing.
4. **Constitution character.** Caterpillar's identity is the
   careful coherence-reader, not the creative bug-spotter.
   The persona pulls toward "I see exactly this and it
   concerns me" rather than imaginative pattern-matching.

The transferable lesson: **prefer artifact schemas that
require verbatim grounding (file + line + quote) over
free-text.** The schema does safety work the model wouldn't
do on its own. This is a small-model-specific finding —
larger models hallucinate less to begin with, but the schema
discipline still pays off in code quality of the findings.

### Concrete pilot evidence

Two complementary data points:

- **Inside the substrate:** Caterpillar's M8 passes during
  mvp-demo (7+ runs across 2 features) and mvp-demo2 (3
  milestones × multiple features × multiple iterations each).
  Zero hallucinated findings observed. Every cited line
  existed; every cited quote matched.
- **Outside the substrate, as a probe:** the independent cold
  reviewer agent we spawned for the
  [code-quality artifact](./code-quality-mvp-demo2.md#5-independent-cold-review-verbatim)
  was a fresh Claude instance with no Wonderland context and
  no Caterpillar constitution — just the instruction to
  review the code with file:line citations. Its findings were
  also grounded (we verified C2's revision_id mismatch
  claim against the actual source before quoting it). The
  forced-citation discipline transfers across instances
  because it lives in the schema, not the prompt.

### Honest scope

- "Zero hallucinated findings" is the observation across the
  recorded review passes; we don't claim Caterpillar will
  *never* hallucinate. If a future pilot surfaces one, it's
  a counterexample worth understanding (what slipped past
  the schema?).
- The pattern (forced citation → reduced hallucination) is
  specific to *review-shaped* artifacts. Less directly
  applicable to generation-shaped artifacts where there's
  nothing to cite (e.g., Alice's stories aren't grounded in
  existing code; they're proposed new state).

### Where this lands in the paper

Section on architecture / agent design. Frame it as
**schema-as-safety: forcing the agent to cite verbatim
quotes makes hallucination structurally harder than honest
reading, especially on small models.** This is one of the
paper's most directly transferable lessons — practitioners
designing agent systems can apply it without buying into the
full Wonderland substrate.

---

## Pillar 4 — Convergent self-repair, with a documented limit

### Claim

Wonderland exhibits **convergent self-repair on code state**:
substrate bookkeeping bugs (ghost completions, stuck states,
lost attributions) don't propagate into the shipped artifact
because Caterpillar reads the working tree at review time,
not the ticket graph. Bugs surface again on the next review
pass.

But this self-repair has a **documented limit**: it operates
on code state, NOT on episodic memory state. When the
substrate fixes itself, agents' memory of past substrate
failures persists and can re-create phantom wedges. This
limit is what motivated the branching-memory architectural
fix (T-a2).

Surfacing the limit is part of the claim. The paper that
only says "self-repair works" undersells the system; the
paper that names the limit and shows the architectural
response is more credible AND more useful to readers.

### Mechanism (the positive case)

Per
[`project_caterpillar_state_independence.md`](../../.claude/projects/-home-jaryk-wonderland-ai/memory/project_caterpillar_state_independence.md):

Caterpillar reads the working tree at review time. Concerns
derive from what the code does, not from what tickets exist
or what prior reviews said. Ticket history is provenance and
operator UX; M8's review is essentially stateless against
ticket state — it inspects what's there.

When the mvp-demo substrate ghost-completed 2
review-synthesized tickets (bug in build_check's
`_route_blocking_review` sweep), the underlying code bugs
they described remained in the codebase. On the next
implementation pass, Caterpillar's review surfaced those same
findings again, because they were still observable in the
source. The substrate damage was recoverable through the next
review pass.

### Mechanism (the limit)

Per
[`project_substrate_fixes_dont_propagate_through_memory.md`](../../.claude/projects/-home-jaryk-wonderland-ai/memory/project_substrate_fixes_dont_propagate_through_memory.md):

In mvp-demo's M2/M3 design, a wedge on stale `scope` and
`constraint` requirements was fixed substrate-side
(coverage check exempted those kinds). The live substrate
stopped emitting coverage-gap observations. **But M4 design
wedged on the same issue anyway** — agents had 291
utterances mentioning those requirements in their episodic
memory across previous runs and re-derived the wedge from
context.

Caterpillar even verified live state in the wedged run ("I've
read the milestone definitions on disk: M2's
`consumes_requirements` is clean") but the loop continued
because the other agents kept recalling memory.

**The architectural fix:** branching episodic memory at the
design level (T-a2 — operator insight, ~3am). Each design
pass gets a branch rooted at the project's "milestone N
closed" snapshot. Wedge churn from one milestone's design
doesn't bleed into siblings. On milestone close, Mock Turtle
consolidates to a project-level summary that captures
conclusions without deliberation.

This fix shipped in 0.8.0 and held cleanly across mvp-demo2
— per
[`project_first_tier2_pilot_completion.md`](../../.claude/projects/-home-jaryk-wonderland-ai/memory/project_first_tier2_pilot_completion.md):
*"Memory branching held — zero memory-bleed wedges across
milestones."*

### Concrete pilot evidence

- **Positive case (mvp-demo M1):** ghost-completed tickets,
  underlying bugs persisted in source, next review pass
  re-surfaced them. Substrate-damage was recoverable through
  the M8 loop.
- **Limit case (mvp-demo M4):** stale-requirement wedge fixed
  substrate-side, agents re-derived the wedge from memory,
  operator surgically wiped 291 utterances, M4 design then
  re-created M3's markdown feature because the wipe also
  removed the agents' record of M3's shipped work.
- **Architectural response (mvp-demo2):** branching memory
  held; zero memory-bleed wedges across the 3 milestones.

The arc is the evidence: positive case demonstrates the
self-repair property, limit case demonstrates the boundary,
architectural response demonstrates the substrate evolved to
address the boundary.

### Honest scope

- The positive case requires the review loop to actually run.
  If an operator manually merges implementation without M8
  review, code bugs persist regardless of ticket state.
- The branching-memory fix is **new and validated on one
  pilot** (mvp-demo2). It held cleanly but N=1 — future
  pilots may surface its own failure modes.
- The framing isn't "self-repair always works." It's "the
  system has natural error correction against its own
  bookkeeping faults, scoped to where the agents' epistemic
  ground is the code rather than the substrate's state."

### Where this lands in the paper

Section on substrate maturity / architectural properties.
Frame as "convergent self-repair" — it's part of why the
substrate can ship with rough edges and still produce coherent
output. Then immediately name the limit + the
branching-memory response. The combined section is stronger
than either half alone: the limit doesn't undermine the
property; it characterizes where the property applies and
where it requires explicit substrate intervention to extend.

---

## Pillar 5 — Constraints improve quality

### Claim

Every substrate primitive that has forced agents to grapple
with more structure has tightened output. **Adding
load-bearing constraints is the architectural lesson, not
removing them.** This runs directly counter to the
conventional advice for working with LLMs ("give them
flexibility, write open-ended prompts").

### Mechanism

Per
[`project_constraints_improve_quality.md`](../../.claude/projects/-home-jaryk-wonderland-ai/memory/project_constraints_improve_quality.md):

Substrate-level constraints constrain the *grammar*, not
the output. Agents still have full freedom WITHIN the
structure, but the structure forces them to confront
questions they'd otherwise paper over.

The connection to multi-lens review (Pillar 2): each agent's
characteristic failure mode is itself a constraint —
something that pins them to a particular epistemic frame.
Without that pinning, you get diffuse generalists; with it,
you get specialized lenses that collectively cover more.

The connection to the small-model thesis: Haiku-class models
benefit MORE from constraints than frontier models because
the constraints compensate for individual-agent capability
limits. **The architecture lets a small model do work that
solo would require a larger one.**

### Concrete pilot evidence

Each substrate primitive shipped during the iteration history
is an instance:

| Primitive | What it forced agents to grapple with | Output improvement |
|---|---|---|
| **Snapshot semantics** (P15) | "this milestone_plan emission is my FULL view, not a partial add" | Eliminated near-duplicate milestone churn (validation5: 8 files for 4 concepts → clean snapshot) |
| **Primary speaker** (P15 follow-up) | "only ONE agent's emissions of this kind survive" | Eliminated parallel-persona / parallel-technical milestone tracks (mvp-demo M2 fix) |
| **Active milestone scope blocks** (P19 prep) | "this is the scope you're designing inside" | Eliminated cross-milestone scope-creep absorption |
| **Coverage check filter exemptions** (T-a3 prep) | "these requirement kinds don't decompose into features" | Eliminated phantom-gap wedges on scope/constraint/success_criterion |
| **Branching memory** (T-a2) | "deliberation in milestone A doesn't bleed to milestone B" | Eliminated argument-history bleed across milestones (the load-bearing T2 autonomy unlock) |
| **Convergence detection** (T-a3) | "this finding is recurring; the contract is ambiguous" | Surfaced spec ambiguity that would have wedged indefinitely |
| **Cross-feature consolidation** (T-a5) | "this ticket duplicates one in a sibling feature" | Reduced ticket-graph noise; saved operator gate-approval work |

Each row is a substrate change that improved output by
narrowing what the agents had grammatical freedom over.
None of them were "make the agent smarter" — all were "force
the agent to confront more structure."

### Honest scope

- This is **NOT** the same as rigid prompting. Rigid prompting
  constrains the OUTPUT. Substrate constraints constrain the
  GRAMMAR — agents still choose what to say within the
  structure, but the structure forces them to confront
  specific questions.
- This pattern was observed iterating; we don't claim it's
  universal. A future substrate change that adds constraint
  without improving output would be evidence the principle
  has limits we haven't found yet.
- The applicability to other LLM systems depends on whether
  those systems have an analogous "grammar" surface to
  constrain. For agent systems that don't model decisions,
  artifacts, and meeting structure explicitly, the lesson
  becomes "be opinionated about your data shapes" rather
  than "constrain agent grammar."

### Where this lands in the paper

Section on substrate philosophy / architectural principles.
"Constraints improve quality" gets its own section, framed
as a counter to the conventional "be flexible" wisdom. Each
row in the table becomes a concrete example. The
anti-claim — "isn't this just rigid prompting?" — is the
foil; address it explicitly.

Connect forward to the small-model thesis: Haiku benefits
more from constraints than Sonnet because the constraints
compensate for capability limits. **The architecture lets a
small model do work that solo would require a larger one.**

---

## How the five pillars connect

The pillars aren't independent — they form a structure that
the paper can use to organize the evidence chapter as a
single argument:

```
Failure-modes-as-identity (architectural choice)
            ↓
Multi-lens identity-anchored review (Pillar 2 — mechanism)
            ↓
Constraints improve quality (Pillar 5 — generalized principle)
            ↓
Quality emerges (observed effect)
            ↓
Quality-cost coupling (Pillar 1 — surprising side effect on small models)

In parallel:
Schema-as-safety (Pillar 3 — specific instance of "constraints improve quality"
                              applied to review artifacts)
Convergent self-repair (Pillar 4 — emergent property of code-as-ground-truth +
                                    multi-lens review, with limit characterized)
```

Pillars 2 and 5 are mechanism / generalized principle.
Pillars 1, 3, 4 are observed properties that follow from the
mechanism. The structure lets the chapter open with the
mechanism, then walk through the properties as predictions
the mechanism makes, validated by pilot evidence.

This is the chapter's argument arc:
1. Wonderland makes a specific architectural choice
   (failure-modes-as-identity + multi-lens review under
   substrate constraints).
2. From that choice, four properties follow that wouldn't
   be predicted from "more agents = more eyes."
3. Pilot evidence on a Haiku-class model demonstrates the
   properties at low N but with the mechanism intact.
4. The mechanism makes each property falsifiable in future
   work — which is the right shape for a research claim.

---

## Excluded observations

Two things from the memory record that the paper should NOT
treat as evidence:

### "Haiku may be architecturally optimal"

Per
[`project_haiku_is_architecturally_optimal.md`](../../.claude/projects/-home-jaryk-wonderland-ai/memory/project_haiku_is_architecturally_optimal.md)
— marked **UNTESTED HYPOTHESIS** in the memory itself. The
operator observed *qualitatively* that Opus might perform
worse than Haiku on Wonderland but explicitly noted: *"I've
observed that qualitatively but I don't have, like, data to
back me up on it."*

This belongs in **future work** (run mvp-demo3 with Opus on
the same directive, compare), not in evidence. Including it
in the evidence chapter would weaken the chapter's
credibility — readers who notice the missing comparative
data would (correctly) read the whole chapter more
skeptically.

### Code-quality claims beyond what the cold reviewer said

The [code-quality artifact](./code-quality-mvp-demo2.md)
explicitly quotes a verbatim independent review. The
evidence chapter should reference that artifact, NOT
re-derive code-quality claims from our own reading. The
discipline: the reviewer said the code is "competent,
above-average for an MVP" with specific praise + one blocker
+ several concerns. That's the claim. Inflating it to "high
quality" or "production-ready" overstates and undermines the
chapter.

---

## What's NOT in this chapter (lives elsewhere)

To prevent scope creep when drafting:

| Topic | Lives in |
|---|---|
| Wright Brothers moment (mvp-demo2 completion narrative) | Separate "Wright Brothers" chapter; analysis 034 is the source. |
| Per-pilot cost breakdowns | Analysis 033 + the economics chapter. |
| How the workflows actually run | workflow-walkthrough.md → architecture chapter. |
| Who the agents are + their failure modes | cast-walkthrough.md → cast chapter. |
| The actual code that shipped | code-quality-mvp-demo2.md → quality chapter. |
| Substrate gaps still open (b3f440c8 cluster) | Limitations chapter. |
| Comparison baselines (single-shot Haiku vs Sonnet) | Future work chapter; recommended in code-quality §8. |
| Thesis statement (identity engineering, small-model thesis, failure-modes-as-identity) | Thesis chapter; this evidence chapter validates predictions the thesis makes. |
| Methodology (pilot-driven substrate development, categorization through failure) | Methodology chapter. |
| Holmes/Watson guest cast extensibility | Cast chapter §Guest casts; future-work chapter for the workflow shape that convenes them. |

The evidence chapter is the load-bearing receipt for the
thesis chapter's claims. Keep it focused on the five pillars
+ the framing that connects them.

---

## See also

- [Workflow walkthrough](./workflow-walkthrough.md) — the
  substrate mechanics that produce these properties.
- [Cast walkthrough](./cast-walkthrough.md) — the characters
  whose multi-lens review is Pillar 2's mechanism.
- [Code quality analysis](./code-quality-mvp-demo2.md) — the
  artifact-level evidence Pillars 1, 2, 3 predict.
- [Cost breakdown analysis](./cost-breakdown-mvp-demo2.md) —
  the economic data Pillar 1 cites.
- [Pilot narrative](./mvp-demo2-pilot-narrative.md) — the
  trajectory that Pillar 4's arc story tracks.
