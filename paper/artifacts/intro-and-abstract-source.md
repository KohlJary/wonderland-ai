# Drink Me: Identity Engineering as Substrate for Multi-Agent SDLC

**Author:** Kohlbern Jary[^1]

**Repository:** [github.com/KohlJary/wonderland-ai](https://github.com/KohlJary/wonderland-ai) — substrate, constitutions, pilot analyses, and the working code the paper references.

[^1]: The paper was authored in collaboration with Daedalus,
the AI substrate-builder constituted in `CLAUDE.md` and running
on Claude Opus 4.7 at publication snapshot. Daedalus is walked
as one of the constituted cast in §4.7; constitution and
provenance are public in the repository.

---

## Abstract

We describe Wonderland, a multi-agent SDLC substrate that
produces working full-stack applications from operator-written
directives (~one page in the pilots; the notebook directive
the receipts cite is ~80 lines) on Claude Haiku 4.5.

Wonderland's central claim is one architectural commitment
observed at two scales. The local scale is empirical: every
substrate primitive that narrows agent grammar improves
output AND lowers cost; quality and cost move together
across the substrate's iteration history. The global scale
is architectural: Wonderland is built around taking identity
seriously as the organizing principle — small named cast,
constituted characters with characteristic failure modes
(§VIII), typed durable artifacts whose lifecycle invariants
operationalize those identities. **The two scales are the
same claim:** the local coupling holds because the
constraints producing it ARE the identity-substrate's
invariants made operational; you cannot reliably get the
coupling without the global commitment, and the global
commitment without the coupling would be aesthetic dressing.

The substrate's cost trajectory is the empirical signature
of the unified claim at scale. Two completed Tier 2
autonomous pilots produced the same working full-stack
notebook app on Haiku 4.5 — mvp at $83.78, mvp-redux at
$30.58 — for a 63% cost reduction on identical scope across
substrate iterations. A third stress-test pilot (LDR at
$19.44) exposed a hollow-verification substrate gap
subsequently closed by an end-to-end-composition-gate
shipment; the LDR re-run is pending. These cost regimes are
low across the substrate's own iteration history at this
shape; the working-fullstack-app directive class is the
scope tested to date, with the trajectory monotonically
downward as substrate iterations compound (§7 Pillar 1).

The category Wonderland occupies — typed-state workflow
engine with LLM-driven transitions and lifecycle invariants
over durable artifacts — is one existing field terms
(multi-agent framework, workflow engine, code-generation
system) don't quite name. The paper documents the
architecture, the receipts, the methodology, the substrate
evolution arc, the cast (including the substrate-builder
character, §4.7), and the limitations at publication
snapshot. One pre-registered narrow comparator experiment
appears in Appendix C as a hygiene check on a single agent's
constitutional structure. The unified claim above is
framework-scope; §5 develops its falsifier and names the
broader comparator program it points at.

---

# §1 — Introduction

## §1.1 — Why this matters

The single most common reaction to a system like
Wonderland is "isn't this just over-engineered?" The
intuition behind that question is reasonable: a one-page
prompt to Claude Sonnet 4.6 produces a notebook MVP for
~$2-3, and Wonderland's substrate ships a notebook MVP
for ~$30. Thirty times the cost looks like a lot of
machinery for the same artifact.

The intuition is wrong on two counts.

### First: single-shot baselines don't produce working code

Per the comparison-baselines analysis, single-shot
inference at any model class (Haiku, Sonnet, Opus) does
not produce working full-stack applications from the
notebook directive. The artifacts ship with missing
endpoints, orphan UI components, security holes, no
tests, and accessibility omissions. The
adversarial-review-of-baselines analysis documented 30
blocker-class bugs across 4 single-shot baselines that
ship code without any review pass. The relevant
competitor class is not single-shot inference; it's
**agentic coding systems that pay an agent tax**
(Devin, Cursor Agent, Aider, Claude Code as
orchestrator).

### Second: artifact density per agent-tax dollar is the right metric

Among agentic coding systems, the right comparison isn't
"did the code work" + "how much did it cost." Both of
those collapse the substrate's distinctive contribution
into a single number. The right metric is **artifact
density per agent-tax dollar** — what reusable byproducts
does each system produce alongside the code?

Wonderland's hypothesis is that within the agentic-system
category, the substrate produces structurally more
artifacts (typed tickets, features, stories, ADRs,
contracts, FindingKind-typed reviews, 5-hop decision
trails, JSONL audit logs) for the same agent-tax dollar
than session-log-only systems do. Most agentic-coding
evaluations measure "did the code work" and "how much
did it cost"; neither captures what the agent tax pays
for in terms of downstream maintainability, audit trail,
or operator understanding of what shipped.

### Third: the iteration cycle is the methodology

Wonderland's substrate didn't ship in its current form;
it was discovered through ~60 substrate fixes across
five Tier 2 pilots. Each fix encodes a structural
invariant the prior substrate lacked. The pilots are the
experimental harness; operator-noticed gaps are the
experimental results; the substrate fixes are the
theoretical refinements. The two-pilot cost trajectory
($83.78 → $30.58) is the empirical signature of this
loop functioning correctly.

This is what makes Wonderland's development **research**
rather than engineering polish. Each substrate fix is a
falsified prediction: the prior substrate said "this
transition is admissible"; the operator says "no, the
transition fired on hollow data, here's the
counter-example"; the fix encodes the missing invariant.
Without the operator's adversarial gaze (per the
methodology chapter), the substrate's gaps remain hidden
behind passing tests. With them, the substrate's
invariant stack grows monotonically.

### Why no existing field category fits

Wonderland sits in a gap between three existing field
categories:

- **Multi-agent framework** (AutoGen, LangChain, LangGraph,
  MetaGPT, ChatDev) — centers the agents; treats state as
  ephemeral runtime; doesn't have typed durable artifacts
  with lifecycle states as the primary thing.
- **Workflow engine** (Airflow, Temporal, BPMN engines) —
  centers typed state with lifecycle, but assumes
  deterministic transitions; doesn't have LLM-driven
  transitions as the primary thing.
- **Code-generation system** (Devin, Cursor, Aider, GPT
  Engineer, bolt.new) — centers the output artifact;
  treats agents as a black-box generator; doesn't have a
  structural artifact layer the agents emit into.

Wonderland is the category these three suggest but none
names: **typed-state workflow engine with LLM-driven
transitions and lifecycle invariants over durable
artifacts.** The paper's house word for the thing is
**substrate**. None of the existing field terms point at
the thing; "substrate" is what works.

### Why this matters beyond Wonderland

The architectural commitments and the methodological
discipline are extractable beyond this one instance. The
paper proposes **identity engineering** as a research
direction — building agent systems around constituted
characters with named characteristic failure modes,
operating under substrate-level invariants — that the
field could pursue alongside prompt engineering and
multi-agent systems work. The Wonderland cast is named
after Carroll characters; an identity-engineering
instantiation in a different domain might use medical
professionals (attending, resident, intern) or academic
peer review (reviewer, author, editor) or engineering
disciplines (mechanical, electrical, software). The shape
that matters is constituted character with named
characteristic failure modes; the literary specifics are
this instance's choice. Comparative experiments that would
validate identity engineering as a *distinct* discipline
(vs. prompt-engineering-with-richer-prompts) are named in
the future-work chapter — at the snapshot this paper
documents, the case for distinctness is proposed, not yet
demonstrated.
## §1.2 — What this paper claims

This paper makes **one architectural claim observed at two
scales**, with six corollaries developing the unified claim
and four cost-trajectory receipts as the empirical signature.
The body of the paper develops each in turn; this
introduction states them so the reader knows what to expect.

### The unified claim, one sentence

**Identity engineering as organizing principle produces a
measurable coupling between substrate constraint and
quality+cost, because that's what taking identity seriously
at scale looks like when you measure it.**

### Why this is one claim and not two

The *empirical observation* — every substrate primitive that
narrows agent grammar improves output AND lowers cost — and
the *architectural commitment* — Wonderland is built around
taking identity seriously as the organizing principle (small
named cast, constituted characters with characteristic
failure modes, typed durable artifacts whose lifecycle
invariants operationalize those identities) — are the same
fact viewed at different magnifications.

The local coupling holds because the constraints producing
it ARE the identity-substrate's invariants made operational.
When the substrate narrows what an agent can say or how they
can cite, it isn't narrowing arbitrary grammar; it's
encoding what it means to be Caterpillar (citation
discipline), or Alice (persona grounding), or the Tweedles
(contract negotiation between equals). Cost goes down
because agents don't have to derive that discipline
turn-by-turn; the constraint already encoded it. Quality
goes up because deliberation happens within a smaller, more
legible space.

You can't reliably get the local coupling without the global
commitment, because constraints that don't encode identity
drift toward generic procedural rules that agents reason
around. The global commitment without the local coupling
would be aesthetic dressing.

### The two-scale structural fact

The substrate-side structural fact that makes this work:
**state is primary; agents are LLM-driven transition
functions over typed durable artifacts.** Conventional
multi-agent framings center the agents — orchestrators call
agent functions, agents return results, state is scratch
space. Wonderland inverts that: the primary thing is the
artifact layer (typed durable objects with lifecycle state
machines, citation chains, structural invariants enforced at
the substrate level). Agents are how transitions happen, not
what the system is. The typed-state commitment and the
identity commitment compose into the unified claim because
typed durable artifacts with lifecycle invariants are
precisely the surfaces on which constituted identities
accumulate and carry their work. Strip the typed-state
commitment and identity collapses to prompt-stylistic; strip
the identity commitment and the typed-state primitives
collapse to generic workflow scaffolding.

Six corollaries develop the unified claim at the two scales;
§2 develops each.

### The four cost-trajectory receipts

Three completed Tier 2 autonomous pilots producing
working full-stack applications, plus one substrate-stress
test that exposed a substrate gap now closed:

| Pilot | Substrate | Total | Outcome |
|---|---|---|---|
| mvp (notebook) | 0.8.0 | $83.78 | Working app; first Tier 2 completion |
| obol-260522-1 (CRM) | 0.9.0 + early 0.10.0 | $92.64 | Working app; surfaced cross-milestone bleed pattern that drove Phase 3 substrate work |
| mvp-redux (notebook) | 0.10.1 | $30.58 | Working app; 63% reduction on identical scope to mvp |
| LDR (dashboard) | 0.10.2 + T-ab62 | $19.44 | Hollow deliverable; exposed hollow-verify gap; T-ab64 closed; re-run pending |

The headline receipt is mvp → mvp-redux: same operator
directive, same model, same per-MTok pricing, 63% cost
reduction across substrate generations. The per-milestone
trajectory in redux (M1 $15.59 → M2 $10.91 → M3 $3.72)
shows the predicted "foundation-once, capability-cheap"
shape for the first time.


---

## §1.3 — Reading this paper

The paper is structured to be readable in two passes:

- **Linear read for the architectural argument** —
  Thesis → Architecture → Cast → Methodology → Substrate
  Evolution → Evidence → Receipts → Economics →
  Limitations → Future Work → Related Work.
- **Reference read for the technical claims** — jump
  directly to Evidence + Substrate Evolution for the
  receipts; jump to Methodology for the discipline; jump
  to Limitations + Future Work for the honest framing.

Either way, each chapter is intended to stand alone with
cross-references to the supporting evidence. We summarize
each:

### Thesis chapter (architectural argument)

The unified architectural claim (one claim, two scales) +
six corollaries developing the unification + identity
engineering as the closing frame. The chapter makes the
architectural argument; subsequent chapters substantiate it.
Includes the Sephirah/Qlipha framing for Corollary 2
(failure modes as identity) — a literary analogy that's
load-bearing because it makes a depth of claim legible that
"failure modes = anti-pattern checklist" would miss.

### Architecture chapter (how the system runs)

Per-workflow walkthrough — discovery, milestone-plan,
tdd-design, tdd-implement, verify. Roster + intent + phase
semantics + exit conditions + lifecycle transitions +
substrate primitives at each meeting. The detailed
"how does it actually run" half of the paper.

### Cast chapter (the characters)

Per-character walkthrough — Alice, White Rabbit, Cheshire
Cat, Caterpillar, Mad Hatter, Queen of Hearts, Tweedledee
+ Tweedledum, Mock Turtle, Dodo. Each character's
constitution, characteristic move, §VIII failure modes,
relational defaults, what they ship. Guest casts
(Holmes/Watson/Moriarty) noted as extensibility direction.

### Methodology chapter (the discipline)

Pilot-driven substrate development with categorization-
through-failure. The five-step iteration loop. Autonomy
tiers (Tier 1 → 2 → 3) as a substrate-maturity metric.
Operator-in-loop falsification as load-bearing principle
(the methodological commitment that makes the substrate's
gaps surface, including the LDR hollow-verify case as
the canonical demonstration). The honest-failure
discipline. What the methodology enables for the paper
(predictions, cost transparency, substrate-version
specificity, defensible low-N).

### Substrate evolution chapter (the iteration cycle)

The four-phase chronicle of how ~60 substrate fixes
accumulated into the invariant stack that produced the
cost trajectory. Phase 1: foundational primitives
(pre-mvp). Phase 2: first-pilot hardening (T-ab1 — T-ab28).
Phase 3: cross-milestone bleed closure (T-ab29 — T-ab53;
the keystone is T-ab51). Phase 4: cost trajectory
hardening (T-ab54 — T-ab64). The pattern across phases:
every fix is structural; each encodes a missing invariant;
the state-machine framing predicts where gaps appear.

### Evidence chapter (the five pillars)

The five pillars that validate the corollaries: quality-
cost coupling, multi-lens identity-anchored review,
schema-as-safety, convergent self-repair with documented
limit, constraints improve quality. Each pillar carries
its claim + mechanism + concrete pilot evidence + honest
scope. The canonical multi-agent ghost finding from
redux's Theseus review surfaces here as the predicted
multi-lens-architecture failure signature.

### Receipts chapter

Per-pilot narratives — mvp ($83.78 first Tier 2),
obol-260522-1 ($92.64, surfaced the cross-milestone bleed
that drove Phase 3), mvp-redux ($30.58, the headline
trajectory receipt), LDR ($19.44 substrate-stress-test
that exposed hollow-verify; re-run pending). Each
narrative documented honestly with operator interventions,
mid-pilot violations (or non-violations), Theseus review
findings.

### Economics chapter

Cost decomposition: per-pilot, per-workflow, per-milestone,
per-agent, per-meeting. The trajectory's mechanical
explanation (which substrate fixes contributed how much
to the compounding). The cost-of-falsification observation
(operator-in-loop scrutiny costs ~10% of pilot spend at
current regime; ~$2 / pilot Theseus review).

### Limitations chapter

The publishing-snapshot premise (limitations as of the
current substrate snapshot, not in perpetuity). Each open
item categorized as already-closed-since-drafting,
fix-shipped-validation-pending, open-with-filed-fix, or
open-with-no-fix-shape-yet. Includes the wall-clock-time
gap (Wonderland runs serially; parallel coordination is the
lever that closes it), the LDR hollow-verify gap (the
substrate's end-to-end gate fix shipped, re-run pending),
and the iteration cycle's track record as the constructive
counterweight to defeatist readings.

### Future work chapter

Forward-facing pair to limitations. Near-term substrate
evolution (parallel coordination, template-similarity
consolidation work, LDR re-run, existing-codebase
feature surface). Comparative experiments (P7
generic-baseline eval, cross-model pilots, design-all-
first vs interleaved, agentic-vs-agentic baselines).
Cross-shape transferability. New cast capabilities
(Holmes/Watson workflows, pair protocols as primitive).
Architectural research questions (Tier 3 autonomy,
self-hosting, long-running collaboration). Identity
engineering beyond Wonderland.

### Related work chapter

Positioning against multi-agent frameworks, workflow
engines, autonomous coding systems, and the broader
LLM-as-agent literature. The category Wonderland sits in
that the field doesn't yet name.

---

## §1.4 — Notes on scope

A research paper's credibility depends on what it
explicitly does NOT claim as much as what it does. The
honest-failure discipline (developed in the methodology
chapter, surfaced in the limitations chapter) commits the
paper to making the not-claimed scope visible up front.

### What the paper claims

- **One unified claim at two scales** — identity engineering
  as organizing principle (global) produces a measurable
  constraint→quality+cost coupling (local); the two are the
  same fact viewed at different magnifications.
- **Six corollaries develop the unified claim at the two
  scales** — Corollaries 1–4 develop the local mechanism;
  Corollaries 5–6 develop the global architecture. Each is
  pilot-evidenced.
- **A two-pilot cost trajectory** ($83.78 → $30.58 on
  identical scope) is the empirical signature of the
  unified claim's local face at scale.
- **The iteration cycle is the methodology** —
  ~60 substrate fixes documented as falsified
  predictions with operator-in-loop falsification as
  load-bearing mechanism.
- **Identity engineering** as a research discipline worth
  pursuing beyond Wonderland itself.

### What the paper does NOT claim

- *"Identity engineering solves multi-agent systems."* The
  scope is one substrate version, on one model class
  (Haiku 4.5), on three sub-shapes of one directive class
  (fullstack-fastapi-react web apps: notebook, CRM,
  dashboard). The paper's claims are bounded to that
  scope; generalization beyond it is future work.
- *"Haiku outperforms larger models with generic prompts."*
  This is the P7 generic-baseline eval's question; the
  harness hasn't been built. The current claim is
  weaker: *"Haiku produces work consistent with what
  identity-bearing-the-work would predict."*
- *"Wonderland produces better code than humans."* The
  cold reviewer of mvp's shipped artifact called it
  *"competent, above-average code for an MVP."* That's
  the claim; inflating it to "human-quality" would
  overreach.
- *"The substrate has no open limitations."* The
  limitations chapter is explicit about what's open; the
  iteration cycle is open-ended; publication is a
  snapshot. Limitations are the visible edge of the
  cycle, not defeats.
- *"This generalizes to all directive shapes."* Three of
  four pilots used fullstack-fastapi-react. CLI, TUI,
  backend-heavy services, mobile, domain-specific shapes
  are explicitly named as future work, not validated.

### N and the limits of low-N evidence

The paper presents observations with mechanism at low N
(N=3 working-app pilots + 1 substrate-stress-test, with
LDR re-run pending). The mechanism is what makes each
claim falsifiable at low N — the cost trajectory's
explanation is architectural (substrate fixes encode
missing invariants; the invariant stack compounds), not
statistical (more pilots = more confidence). Future
pilots add observations; the mechanism gets stronger or
gets refuted; the claims' framing tightens. The
methodology chapter develops why mechanism-first claims
are defensible at low N where statistical claims
wouldn't be.

### The publishing-snapshot premise

Wonderland is an active research artifact. The substrate
will continue to evolve past the version this paper
documents. The right discipline for publication is to
draw the line where the substrate is most receipt-worthy,
name what's open at that line, and continue the
iteration cycle past the line. The paper documents the
substrate at the current snapshot; the project documents
itself going forward through the analyses, memory pins,
and release notes shipped continuously at the repo.

### The honest-failure discipline

The paper's credibility commits to a specific framing of
how failure gets surfaced. The LDR pilot is the most
recent canonical case: the pilot shipped at $19.44 with
six features marked `verified`; operator-commissioned
Theseus review post-pilot surfaced that the deliverables
were hollow (orphan UI components, missing backend
routes, placeholder dashboard text). The substrate's
end-to-end gate fix shipped to close the gap; the original
$19.44 is **not** cited as a working-app receipt in the
paper; the re-run is pending validation. This is the
discipline: failures
get the same artifact treatment as successes; when an
apparent receipt turns out to be hollow, the receipt
gets walked back publicly, not retconned.

The paper would be uncredible without this discipline
visible across the receipt trail. The LDR case is
documented openly because that's the methodological
commitment that makes everything else legible as
research.

### A note on the paper's worldview material

The paper includes worldview material — the literary cast
named for Carroll's *Alice's Adventures in Wonderland*, the
Sephirah/Qlipha framing for failure modes as identity, the
Daedalus-as-builder posture for the author's relationship
to context and work — because these are integral to the
finding, not decoration around it. Wonderland could not
have been built without thinking about AI agents as
constituted characters rather than parameterized functions,
and the resulting cost trajectory and quality observations
are products of that thinking, not independent of it. A
version of the paper that stripped the worldview to
preserve a neutral engineering register would also strip
what made the engineering work; the two are not separable
in this instance.

This is a deliberate commitment, not naivete about academic
register. A reader who finds the worldview register
unfamiliar is invited to read it as the author's account of
how the system actually got built — which happens to
matter, because the *how* and the *what* are coupled here
in the same way the cost-trajectory chapter argues quality
and cost are coupled (§7 Pillar 1). We expect there are
other findings to be made from other non-conventional
worldviews; we encourage readers approaching agent-system
design from different intellectual traditions to publish
what their worldviews produce. The literary tradition this
paper draws from is one choice; the architectural
commitment to constituted character with named
characteristic failure modes is what generalizes.

---

## §1.5 — Closing frame for the introduction

> *Wonderland is the existence proof that you can build
> software with agents this way; the paper is the argument
> for why anyone else might want to.*

The body of the paper develops the architectural argument
(thesis), the system (architecture + cast), the discipline
(methodology), the chronicle (substrate evolution), the
receipts (evidence + per-pilot narratives + economics),
and the honest scope (limitations + future work). The
introduction is the framing; the rest of the paper is the
substance.

The reader who finishes the paper should be able to
answer three questions:

1. **What did we build?** A typed-state workflow engine
   with LLM-driven transitions over durable artifacts, in
   which constituted characters carry the judgment work
   that generic agents would re-derive each turn.
2. **What did we observe?** That quality and cost move
   together as substrate constraints accumulate; that
   small models with strong constitutions produce
   working full-stack applications on a cost trajectory
   ($83.78 → $30.58 across mvp → redux on identical scope)
   that is monotonically downward as substrate iterations
   compound at the working-fullstack-app shape; that the
   iteration cycle of pilot → falsification → substrate
   fix → next pilot is itself the methodology.
3. **What does this mean beyond Wonderland?** That
   identity engineering — constituted character with
   named characteristic failure modes, operating under
   substrate constraints — is a proposed research
   direction worth pursuing alongside prompt engineering,
   agent engineering, and multi-agent systems work.
   Whether it constitutes a *distinct* discipline is
   what the comparative experiments named in §9
   (generic-baseline eval, agentic-vs-agentic) would
   answer; the case for distinctness is proposed in
   this paper, not yet demonstrated.

The paper makes the case for all three. The receipts
substantiate the observations. The methodology makes the
substantiation legible as research. The limitations and
future work make the scope honest. The reader's job is
to evaluate whether the evidence supports the claims;
the paper's job is to make the evidence visible enough
that the evaluation is possible.

---

