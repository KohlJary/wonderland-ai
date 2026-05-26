# §7 — Evidence

## §7.1 — What counts as evidence here

This artifact distinguishes four observational classes:

| Class | What it is | Counts as paper evidence? |
|---|---|---|
| **Documented pilot finding** | Behavior observed during a pilot with concrete cost / artifact / utterance citations from instrumented telemetry. | Yes. |
| **Operator observation, unsolicited** | The operator noticed a property of the output without being prompted to look for it. | Yes — qualitative but high-signal. |
| **Theseus review finding** | A structured complexity-hunting review of pilot output, performed by an adversarial subagent with explicit lens shift for freshly-generated code. Severity-tagged with file:line citations. | Yes — counts as structured operator-in-loop falsification (see methodology chapter (§5)). |
| **Hypothesis** | A possible property the system has, consistent with some observations but not tested rigorously. | No — explicitly excluded with reasoning. |

The five pillars below are all class 1 + 2 + 3. One
observation that fits class 4 (the "Haiku may be
architecturally optimal" hypothesis) is explicitly excluded;
see [§Excluded observations](#excluded-observations) at the end.

A note on the evidence stream's growth: the chapter started
at N=2 pilots (mvp-demo + mvp) and now draws on three
completed Tier 2 pilots that produced working-app artifacts
(mvp, obol-260522-1, mvp-demo-redux), one substrate-
stress-test pilot that exposed the hollow-verify gap (LDR;
pending re-run for working-app receipt status), and ~60
substrate fixes whose iteration-cycle chronicle lives in the
substrate-evolution chapter (§6).
N is still small in research-statistics terms; the pillars
remain framed as *observations with mechanism*, not *proven
properties*. The mechanism is what makes each claim
falsifiable in future pilots; per-substrate-version
reproducibility is what makes it research rather than
anecdote (see methodology chapter §Low-N defensibility).

---

## §7.2 — The canonical multi-agent ghost (chapter-leading concrete)

Before the five pillars, one concrete finding from the
redux pilot's Theseus review establishes what the substrate's
distinctive failure signature looks like and why the pillars
that follow are arranged around it.

The finding: in the mvp-redux notes app, the frontend
shipped a `searchAndFilterNotes()` helper that correctly
composed the backend's `?q=` (search) and `?tag=` (filter)
query parameters together. The helper was well-written —
correct types, correct call shape, would have produced
useful output. **The frontend never called it.** Instead,
the frontend wired explicit if/elif branching that *cleared*
the tag when search was active and vice versa, treating
the two parameters as mutually exclusive. The backend's
docstring, written by a different agent, marked them as
"mutually exclusive" too. Both agent reasonings were
individually correct against their respective contract
interpretations. The compose helper sits in the codebase
as orphan code — imported nowhere, tested nowhere, contradicting
the wiring three feet away.

This is **the canonical multi-agent failure signature in its
purest form.** Not hallucination (Pillar 3 explicitly
disproves that). Not a substrate bug (substrate worked
correctly). The agents individually did their jobs well —
and the seam between their work fragmented because no shared
invariant bound their interpretations of the contract
together. That's the failure mode multi-agent code
generation has that single-agent doesn't, and it's the
failure mode T-ab64's end-to-end composition gate
(`api_call_resolves_to_route` + import-graph reachability)
now structurally prevents at the API contract layer.

The finding does triple duty for the rest of the chapter:

- **Pillar 2 (multi-lens identity-anchored review)** —
  Theseus surfaced this finding *because* the multi-lens
  architecture produces work that's individually correct
  per-lens but reveals contract-seam fragmentation under
  cross-lens read. The pillar's claim that multi-lens review
  catches what single-lens misses is operationalized here:
  the canonical ghost is exactly the shape only a
  cross-cutting review reads as a bug.
- **Pillar 4 (convergent self-repair, with limit)** — the
  multi-agent ghost is the *limit case* on the convergence
  claim. Caterpillar's M8 review didn't catch it during the
  redux pilot; Theseus's structured fine-tooth-comb pass
  caught it post-pilot. The substrate's coherence-reading
  invariant works on intra-feature artifacts; cross-feature
  contract-seam fragmentation requires either more aggressive
  M8 directives (currently scoped tighter than that) or the
  T-ab64 end-to-end gates that now exist post-LDR.
- **Pillar 5 (constraints improve quality)** — the substrate's
  response to the finding (T-ab64 four new end-to-end
  checks) is the canonical example of the constraint→quality
  coupling: identifying a structural failure class, encoding
  it as a global invariant, validating that future
  manifestations of the failure class would be caught
  structurally. The chapter develops the receipt for the
  fix's validation in Pillar 5; here, the finding itself is
  the receipt for *why* the fix had to exist.

Pillars below take the architecture's behavior at this level
of specific concreteness throughout. Each pillar opens with
its claim, develops the mechanism, presents concrete pilot
evidence, names honest scope. The canonical multi-agent
ghost is the reader's grounding example for what
"identity-bearing characters producing legitimate but
non-composing work" actually looks like in shipped code.

---

## §7.3 — Pillar 1: Quality-cost coupling

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

The quality-cost inversion claim is the synthesis of an
operator-internal observation pinned during the substrate's
iteration history: *every substrate primitive that narrowed
agent grammar improved output AND lowered cost; the two never
moved against each other across the substrate's evolution.*
The receipt below is the pilot-level confirmation of that
within-substrate pattern at the cross-pilot scale.

- **mvp-demo → mvp pilot-level contrast.** mvp-demo cost
  ~$5+ in dead-end wedge runs and delivered a partial artifact
  for ~$40. mvp cost ~$1 in wedge runs and delivered a
  complete artifact for $83.78. The substrate matured between
  pilots; both quality AND cost-efficiency improved.

- **The headline receipt: mvp → redux on identical
  scope.** Per
  [analysis 046](https://github.com/KohlJary/wonderland-ai/blob/main/analyses/046-mvp-redux-cost-receipt.md):
  redux re-ran mvp's notebook directive on the
  post-T-ab51-T-ab57 substrate (0.10.1). Result: **$30.58
  vs the original $83.78 — a 63% cost reduction on identical
  scope, same model, same per-MTok pricing.** Working app
  with verified persistence, CRUD, search, tag filter. The
  cost reduction is not produced by any single fix; it's
  the aggregate signature of the substrate evolution stack
  documented in the substrate-evolution chapter (§6).

  The per-milestone trajectory shows the substrate's
  "foundation-once, capability-cheap" claim in numbers for
  the first time:

  | Milestone | Cost | Notes |
  |---|---|---|
  | M1 foundation | $15.59 | Test framework + 22 verify-spawned tickets |
  | M2 capability | $10.91 | Steady-state, 4 build-failure cycles, 3 verify-spawned bugs |
  | **M3 capability** | **$3.72** | Capability on solid foundation, minimal verify cycles |

  M3 at $3.72 is **13% of mvp's per-milestone
  average** (~$28). Same architectural lens; same model;
  same scope. The compounding is what Pillar 5 (constraints
  improve quality) predicts: each substrate constraint that
  closed a class of waste contributed to the trajectory.

- **The negative control: obol-260522-1 (cross-milestone
  bleed visible in cost).** The pilot between mvp and redux
  ran a larger CRM project on a substrate intermediate
  between mvp's and redux's. Total cost: $92.64 — 11% MORE
  than mvp, on a substrate that should have been better.
  Cost-driver analysis revealed cross-milestone bleed was
  the cause: agents reading off-scope artifacts produced
  redundant deliberation and rework cycles. The bleed was
  the failure case for "more substrate primitives → lower
  cost"; the keystone milestone-scope filter (§6 Phase 3)
  closed it.

  Redux ran post-keystone-fix and produced the trajectory.
  obol-260522 produced the gap; the fix closed it; redux
  validated. The negative control is part of the evidence:
  the coupling holds when the substrate primitives are
  load-bearing; when one fails to enforce the invariant it
  claimed to enforce (the early branching-memory primitive's
  write-isolation-without-read-teeth gap; see Pillar 4), the
  coupling breaks and the substrate work surfaces the gap.

### Honest scope

- N=3 working-app pilots (mvp, obol-260522-1, redux),
  with the LDR re-run pending. The coupling has held every
  time it's been observable on a non-degenerate substrate;
  the obol-260522 cost rise was the visible failure case
  that drove the Phase-3 substrate work and validated the
  framing (when invariants fail to be enforced, cost goes
  up; fixing the invariants brings it back down).
- The coupling is observed at the *substrate-iteration* level,
  not the *per-model* level — we haven't shown that
  Wonderland-on-Haiku produces higher quality than
  Wonderland-on-Sonnet at lower cost. That's a different
  comparison (a baseline experiment the
  [code-quality analysis](https://github.com/KohlJary/wonderland-ai/blob/main/paper/artifacts/code-quality-mvp.md)
  recommends).
- The mechanism (constraints narrow possibility space) is the
  paper's predictive claim; if a future substrate change
  improves output but increases cost, that would be a
  yellow-flag counterexample worth investigating (likely
  signal: the change is doing the agents' work for them
  rather than constraining their grammar).

---

## §7.4 — Pillar 2: Multi-lens identity-anchored review

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

The architectural choice: failure-modes-as-identity
isn't a quirk — it's the design decision that produces
multi-lens review.

### Concrete pilot evidence

during the mvp Tier 2 pilot:

> The operator observed unsolicited: "we're not just shipping
> code, it's *quality* code. They're accounting for all types
> of shit I never would have thought to through the review
> passes."

The unsolicited framing is significant: the operator wasn't
looking for quality evidence; they noticed it.

The
[code-quality analysis](https://github.com/KohlJary/wonderland-ai/blob/main/paper/artifacts/code-quality-mvp.md) supplies
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

**Redux Theseus review — the canonical multi-agent ghost
finding (paper-grade):** the structured Theseus complexity-
hunting review of redux surfaced a finding that's the
clearest receipt for both the multi-lens architecture's
strengths AND its characteristic blind spot:

> The `searchAndFilterNotes` Ghost is the canonical
> multi-agent artifact. One agent implemented the backend,
> documented that `q` and `tag` are "mutually exclusive,"
> and the frontend agent built a compose helper anyway
> (correctly!) but then wired the exclusive-branch logic
> instead. The helper exists in a liminal state — correct,
> tested nowhere, imported but unused. This is exactly what
> happens when two agents reason independently about an
> underspecified contract seam.

The finding is paper-grade in two ways. First, it's the
predicted shape: independent agents reasoning from their
respective lenses produce work that's individually correct
but doesn't compose at the contract seam. Second, it's
the predicted blind spot: multi-lens review catches more
than single-lens, but lens-pluralism doesn't automatically
produce contract-seam coherence — that requires explicit
substrate machinery to detect (eventually, T-ab64's
api_call_resolves_to_route check catches the
structurally-similar pattern at the API contract layer).
The multi-lens architecture produces high-quality code;
the architecture's blind spots produce specific failure
signatures the substrate then encodes invariants against.

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

---

## §7.5 — Pillar 3: Schema-as-safety: forced citation prevents hallucination

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

Three complementary data points:

- **Inside the substrate, expanded across pilots:**
  Caterpillar's M8 passes have now been observed across
  mvp-demo (7+ runs across 2 features), mvp
  (3 milestones × multiple features × multiple iterations
  each), obol-260522-1 (4+ milestones × multiple
  iterations), mvp-demo-redux (3 milestones × multiple
  iterations), and LDR (5 milestones × multiple
  iterations). **Across all five pilots, zero hallucinated
  findings observed.** Every cited line existed; every
  cited quote matched. The forced-citation discipline
  continues to hold on Haiku 4.5 across substrate
  generations 0.6 through 0.10.2.
- **Outside the substrate, as a probe:** the independent
  cold reviewer agent we spawned for the
  [code-quality analysis](https://github.com/KohlJary/wonderland-ai/blob/main/paper/artifacts/code-quality-mvp.md)
  was a fresh Claude instance with no Wonderland context
  and no Caterpillar constitution — just the instruction
  to review the code with file:line citations. Its
  findings were also grounded (we verified C2's
  revision_id mismatch claim against the actual source
  before quoting it).
- **The Theseus review subagent extends this:** every
  Theseus review on redux and LDR has been file:line
  grounded with verbatim citations. No findings have
  required walking back as hallucinated; every finding
  could be verified against the source. The forced-
  citation discipline transfers across instances because
  it lives in the schema, not the prompt.

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

---

## §7.6 — Pillar 4: Convergent self-repair, with a documented limit

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

This fix shipped in 0.8.0 and held cleanly across mvp:
the operator observed zero memory-bleed wedges across the
pilot's three milestones, validating the branching primitive
in its first end-to-end Tier 2 run.

**The architectural refinement that came later**:
T-a2's branching isolated WRITES but not READS. The
`compose_context` helper that retrieved relevant memory for
an agent's deliberation queried the full memory store
across branches, bypassing the inheritance_chain the
branches were supposed to provide. Even with per-milestone
branching, an agent could still see episodic memory from
adjacent milestones because reads escaped the branch.

T-ab52 fixed `compose_context` to honor the inheritance
chain. Write isolation finally had read-side teeth.

This is the paper-grade refinement to the original Pillar 4
claim: **memory branching is necessary but not sufficient
for convergent self-repair beyond code state.** The
property requires write isolation AND read isolation; either
alone provides the illusion of isolation without the
substance. T-a2 + T-ab52 together establish the boundary
where Pillar 4's self-repair extends to memory state, not
just code state. The full property statement: convergent
self-repair holds on code state always; it holds on memory
state only when both read and write isolation are enforced.

Engagement note: Pillar 4 was **patched twice** before the
memory-state extension held. T-a2 shipped on the strength of
the operator's ~3am insight; the property looked closed for
the duration of mvp. T-ab52 was the receipt that the property
had been only half-closed — the read-side gap wasn't
visible until later pilots stressed cross-milestone retrieval
patterns. The paper documents both patches because the gap
between them is itself a finding: an architectural claim can
look robust through one pilot and surface a structural hole
in the next, and the iteration cycle's job is to keep
closing those holes as they're recognized. The Pillar 4
claim as published is the post-T-ab52 version; the pre-T-ab52
version would have been overclaim.

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
- **Architectural response (mvp):** branching memory
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
  pilot** (mvp). It held cleanly but N=1 — future
  pilots may surface its own failure modes.
- The framing isn't "self-repair always works." It's "the
  system has natural error correction against its own
  bookkeeping faults, scoped to where the agents' epistemic
  ground is the code rather than the substrate's state."

---

## §7.7 — Pillar 5: Constraints improve quality

### Claim

Every substrate primitive that has forced agents to grapple
with more structure has tightened output. **Adding
load-bearing constraints is the architectural lesson, not
removing them.** This runs directly counter to the
conventional advice for working with LLMs ("give them
flexibility, write open-ended prompts").

### Mechanism


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
is an instance. The pre-mvp stack:

| Primitive | What it forced agents to grapple with | Output improvement |
|---|---|---|
| **Snapshot semantics** (P15) | "this milestone_plan emission is my FULL view, not a partial add" | Eliminated near-duplicate milestone churn (validation5: 8 files for 4 concepts → clean snapshot) |
| **Primary speaker** (P15 follow-up) | "only ONE agent's emissions of this kind survive" | Eliminated parallel-persona / parallel-technical milestone tracks (mvp-demo M2 fix) |
| **Active milestone scope blocks** (P19 prep) | "this is the scope you're designing inside" | Eliminated cross-milestone scope-creep absorption |
| **Coverage check filter exemptions** (T-a3 prep) | "these requirement kinds don't decompose into features" | Eliminated phantom-gap wedges on scope/constraint/success_criterion |
| **Branching memory** (T-a2) | "deliberation in milestone A doesn't bleed to milestone B" | Eliminated argument-history bleed across milestones (the load-bearing T2 autonomy unlock) |
| **Convergence detection** (T-a3) | "this finding is recurring; the contract is ambiguous" | Surfaced spec ambiguity that would have wedged indefinitely |
| **Cross-feature consolidation** (T-a5) | "this ticket duplicates one in a sibling feature" | Reduced ticket-graph noise; saved operator gate-approval work |

The post-mvp stack (continued the same pattern):

| Primitive | What it forced agents to grapple with | Output improvement |
|---|---|---|
| **Foundation/capability axis** (T-ab6, T-ab13, T-ab15) | "milestones are typed; the kind is a routing decision" | Routed foundation work to Caterpillar solo, capability work to Alice solo; closed the M1 overshoot pattern |
| **Milestone seed filter** (T-ab9, T-ab48) | "the substrate refuses to admit a story whose milestone tag doesn't match the active scope" | Closed the soft-bleed of cross-milestone story references |
| **Tools write-guard** (T-ab12) | "agents can read substrate paths but cannot write them out-of-band" | Eliminated bypass writes that broke typed-state lifecycle invariants |
| **Keystone milestone-scope filter** (T-ab51) | "every read of milestone-scoped state filters at the resolver, not at each consumer" | Closed cross-milestone bleed at story + feature + requirement axes simultaneously; eliminated the rework cycles that compounded obol-260522's cost |
| **Read-side teeth on memory branches** (T-ab52) | "compose_context honors the inheritance chain, not just the writes" | Made T-a2's write isolation operational; closed the leak where reads escaped the branch |
| **M8 roster narrowing** (T-ab54) | "review is Caterpillar's job alone; tweedles add window-opening overhead without commensurate signal" | Reduced M8 spend by ~60% with no review-quality regression |
| **Tool-result cap** (T-ab57) | "deliberation context bounds are structural; the agent doesn't have to remember to be brief" | 52% of total tool-result bytes saved across all tool-using agents |
| **Source-line context in build failures** (T-ab30, T-ab60) | "the substrate surfaces the failing line with its surrounding context; the agent doesn't need a separate read round" | Compressed npm-build convergence from 5-cycle to 1-pass |
| **Citation-chain flexibility** (T-ab62) | "feature.sources may cite requirements directly when no intermediate story layer was produced" | Unblocked legitimate foundation-feature flow without weakening the drift-detection invariant |
| **End-to-end verification gates** (T-ab64) | "lifecycle transitions admit only on global invariants, not per-layer conjunction" | Closed the hollow-verify gap LDR exposed; catches orphan components, unregistered API routes, placeholder text, parallel-write duplicates |

Each row across both tables is a substrate change that
improved output by narrowing what the agents had grammatical
freedom over. None of them were "make the agent smarter" —
all were "force the agent to confront more structure." The
post-mvp additions extended the same pattern with no
counterexamples: every primitive that narrowed agent grammar
improved output AND reduced cost. The cost trajectory
established in [Pillar 1](#pillar-1--quality-cost-coupling)
is the aggregate signature of the whole stack working
together; no individual primitive produces the reduction
alone.

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

---

## §7.8 — How the five pillars connect

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

## §7.9 — Excluded observations

Two things from the memory record that the paper should NOT
treat as evidence:

### "Haiku may be architecturally optimal"

This is an explicitly **UNTESTED HYPOTHESIS** from the
operator's qualitative observation: that Opus might perform
*worse* than Haiku on Wonderland. The operator's own framing
on this one: *"I've observed that qualitatively but I don't
have, like, data to back me up on it."*

This belongs in **future work** (run mvp-demo3 with Opus on
the same directive, compare), not in evidence. Including it
in the evidence chapter would weaken the chapter's
credibility — readers who notice the missing comparative
data would (correctly) read the whole chapter more
skeptically.

### Code-quality claims beyond what the cold reviewer said

The [code-quality analysis](https://github.com/KohlJary/wonderland-ai/blob/main/paper/artifacts/code-quality-mvp.md)
explicitly quotes a verbatim independent review. The
evidence chapter should reference that artifact, NOT
re-derive code-quality claims from our own reading. The
discipline: the reviewer said the code is "competent,
above-average for an MVP" with specific praise + one blocker
+ several concerns. That's the claim. Inflating it to "high
quality" or "production-ready" overstates and undermines the
chapter.

---

