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

# §2 — Thesis

## §2.1 — The central claim

Wonderland is one architectural claim observed at two scales.

The **local scale** is empirical: every substrate primitive
that narrows agent grammar improves output AND lowers cost.
Across the substrate's iteration history, every primitive
shipped to date that constrained how agents could speak,
what they could cite, what they could write, improved the
quality of what they produced AND reduced the total cost of
producing it. The cost trajectory across pilots is the
aggregate signature; §7 develops the full receipt.

The **global scale** is architectural: Wonderland is built
around **taking identity seriously as the organizing
principle**. The cast is small and named. Each character has
a constitution it inhabits across runs. Each constitution
names a characteristic failure mode (§VIII) — the way THIS
character, specifically, fails. The substrate's invariants
are the operationalization of those identities: every
constraint encodes a way some named identity could fail to
act in character. State-as-primary — typed durable artifacts
with lifecycle state machines, citation chains, structural
invariants — exists because identities only carry judgment
across runs if the artifacts their judgment was applied to
survive between runs.

### Why these are the same claim

The local coupling holds because the constraints that produce
it ARE the identity-substrate's invariants made operational.
When the substrate narrows what an agent can say or how they
can cite, it isn't narrowing arbitrary grammar — it's
encoding what it means to be Caterpillar (citation
discipline), or Alice (persona grounding), or the Tweedles
(contract negotiation between equals). The cost goes down
because agents don't have to derive that discipline
turn-by-turn; the constraint already encoded it. The quality
goes up because deliberation happens within a smaller, more
legible space.

You can't reliably get the local coupling without the global
commitment, because constraints that don't encode identity
drift toward generic procedural rules that agents reason
around. The global commitment without the local coupling
would be aesthetic dressing — names and constitutions
producing nothing measurable. The paper's argument is that
these are inseparable: **identity engineering as organizing
principle produces a measurable coupling between substrate
constraint and quality+cost, because that's what taking
identity seriously at scale looks like when you measure it.**

The contrast that makes the global commitment non-trivial:
in conventional multi-agent setups, an agent is *role + tools
+ goals* — a function defined by what it should do. In
Wonderland, an agent is *character + voice + persistent
persona + named failure modes* — a function defined by who
it *is*, which then constrains what it does. The difference
is whether judgment is **constituted** (Wonderland) or
**re-derived from a system prompt each turn** (conventional).

The contrast that makes the local commitment non-trivial:
the substrate side has its own structural shape that
distinguishes it from conventional agent frameworks.
**State is primary; agents are LLM-driven transition
functions over typed durable artifacts.** Conventional
multi-agent framings center the agents — orchestrators call
agent functions, agents return results, results get stitched
together by code outside the agents, state (when it exists)
is scratch space passed between calls. Wonderland inverts
that. The primary thing is the artifact layer — typed
durable objects (requirements, stories, features, tickets,
milestones, contracts, reviews, implementations) with
lifecycle state machines, citation chains between them, and
structural invariants enforced at the substrate level.
Agents are how transitions happen, not what the system is.
Concretely: when an agent emits an utterance, the utterance
mutates typed state. A feature transitions `proposed →
in_design`. A ticket transitions `pending → queued`. The
transition is gated by structural invariants — does the
citation resolve to a real upstream artifact? Does the
milestone tag match the active scope? Does the verification
check pass end-to-end? The agent's role is to produce a
candidate transition; the substrate decides whether the
transition is admissible.

The structural definition (state-primary, agents as
transitions) and the architectural commitment (identity as
organizing principle) compose into the unified claim because
typed durable artifacts with lifecycle invariants are
precisely the surfaces on which constituted identities
accumulate and carry their work. The artifact layer is what
gives identity somewhere to be. Strip the typed-state
commitment and identity collapses to prompt-stylistic; strip
the identity commitment and the typed-state primitives
collapse to generic workflow scaffolding. The unified claim
is that *neither half stands alone*, and *the same
substrate-iteration history that produced the empirical
coupling produced a system organized around identity at
every layer* — because those are the same fact viewed at
different magnifications.

### Falsifier

The unified claim has a unified falsifier: a project built
without taking identity seriously as the organizing principle,
accumulating substrate constraints over a comparable
iteration history, produces (a) the same coupling between
constraint and quality+cost, (b) the same
characteristic-failure-mode discipline across its agent
cast, AND (c) the same artifact density per agent-tax dollar
at the working-app scale. If a non-identity-organized
project produces all three, the organizing-principle claim
is decoration — the coupling is doing all the work and
identity is post-hoc rationalization. If it produces none,
the coupling IS what taking identity seriously looks like
when measured.

**The falsifier has one face that is operationalized at
next-pilot scope and two faces that aren't.** The
methodology-chapter falsifier table (§5) pre-registers the
cost-trajectory face (c) as a per-pilot prediction: the next
pilot's cost trajectory continues the $83.78 → $30.58
direction at the per-feature level, or refutes the coupling
mechanism. Faces (a) artifact density and (b)
characteristic-failure-mode discipline require the
comparator framework §5 names as a research program — a
non-identity-organized project built up to comparable
substrate maturity, measured against the same artifact-set
and failure-mode rubrics. This face of the unified claim
remains honest-failure noted rather than pre-registered,
because no cheap version of the test exists. **The
discipline the unified claim commits to is that the cost
trajectory's continued behavior is the next-pilot signal
the unified claim makes operational**; if that signal
breaks, the unified claim's empirical leg breaks
regardless of whether the research program for (a) and (b)
has shipped yet.

The narrower agent-level comparator pre-registered in
Appendix C tests a hygiene hypothesis at single-agent scope
(whether Caterpillar's literary register affects M8 review
output beyond what the operational rules alone produce); it
is **not load-bearing for the unified claim above**, because
identity engineering as organizing principle isn't ablatable
at the single-agent level — it's framework-scope or nothing.

### Six corollaries develop the unified claim

The six corollaries that structure this chapter develop the
unified claim at its two scales. Corollaries 1–4 develop the
local mechanism — what identity-bearing agents contribute,
how the contributions compose into shipped artifacts, how
the system degrades visibly when something is wrong, why the
substrate produces friction-as-design rather than
consensus-as-design. Corollaries 5–6 develop the global
architecture — friction-as-the-substrate, substrate
constraint amplifies identity. They are not separate claims
that happen to compose; they are facets of the unified
claim that the chapter develops one at a time so each can be
inspected against pilot evidence.

The paper's house word for the category Wonderland occupies
is **substrate** — not standard terminology, but it captures
the load-bearing distinction: the artifact layer is what the
agents grow on, not scratch space they pass through. §1.1
named the categorical gap; §10 develops it.

---

## §2.2 — Corollary 1: Identity lets smaller models outperform their expected capabilities

### Claim

Most of the judgment a generic agent has to derive turn-by-turn
— what to engage with, what to refuse, when to stay silent,
who owns this domain — is carried by the constitution itself.
The model isn't being asked to *invent* the discipline on each
prompt; it's being asked to *act in character*, which is a
much easier task.

The default target for Wonderland is Claude Haiku 4.5
(`claude-haiku-4-5-20251001`). This choice is a **thesis
statement, not a cost-savings move**: if identity is doing the
load-bearing work, a small model with a strong constitution
should hold its own against a large model with a generic
prompt.

Framing Haiku as "the budget option" undermines the
experiment. The cost-comparison work is genuinely useful
(it's how we discover whether the thesis holds), but its
purpose is to *test the thesis*, not to *find the cheapest
model that works*.

### Mechanism

Identity carries judgment. A generic agent on each turn has
to re-derive: am I the right speaker for this? what's my
scope here? what would a careful version of this role do?
A constituted agent reads §I-IX of their constitution and the
answers are present.

A Haiku-class model doing the latter has the same effective
capability as a larger model doing the former — the
constitution is doing the work the larger model would
otherwise have to do via raw inference.

### Concrete pilot evidence

- **Early evidence:** analysis 004
  (Showcase 1, /health endpoint) — three of four agents
  correctly chose silence on a concrete operational directive
  because their constitutions named padding, false certainty,
  and orchestration-performance as failure modes to guard
  against. No external policy intervened; the team's silence
  *was* the settlement.

- **New evidence (mvp):** the Tier 2 autonomous pilot
  completed end-to-end on Haiku 4.5 — 3 milestones designed,
  implemented, and verified for $83.78
  ([analysis 034](https://github.com/KohlJary/wonderland-ai/blob/main/src/wonderland/closet/analyses/034-mvp-demo2-autonomous-pilot.md),
  cost breakdown ([analysis](https://github.com/KohlJary/wonderland-ai/blob/main/paper/artifacts/cost-breakdown-mvp.md))). An
  independent cold reviewer (a fresh Claude instance, no
  Wonderland context) called the resulting code *"competent,
  above-average code for an MVP"* with *"real engineering
  taste in the search-escaping and timestamp-normalization
  layers"*
  (see [code-quality analysis](https://github.com/KohlJary/wonderland-ai/blob/main/paper/artifacts/code-quality-mvp.md)).
  Haiku produced this output. The constitutions did most of
  the load-bearing judgment work.

- **Schema-as-safety on Haiku:** across 7+ Caterpillar M8
  review passes during mvp-demo, every review finding cited
  real code at real `file:line` locations with verbatim
  quotes. Zero hallucinated findings — non-trivial for a
  Haiku-class model, where fabrication is the standard
  failure mode. The constitution's forced-citation discipline
  did the work the model wouldn't have done on its own
  (developed as the schema-as-safety property in §7 (§7):
  forced-citation review structure makes hallucination
  harder than honest reading for small models).

- **Substrate-stack cost trajectory:** the strongest receipt
  for Haiku-with-strong-constraints isn't that Haiku ships
  working code — it's that the cost-per-pilot drops
  monotonically as substrate constraints compound across
  iterations. The full per-pilot trajectory + per-milestone
  decomposition is developed as the
  quality-cost coupling property in §7 (§7):
  every substrate primitive that narrows agent grammar
  improves output AND lowers cost. Identity-bearing-the-work,
  when given a better substrate to operate on, gets cheaper
  AND produces higher-quality artifacts. The
  constraint→quality+cost coupling is the load-bearing
  observation; Corollary 6 develops the architectural reason
  it isn't a coincidence.

### Honest scope

- The P7 generic-baseline eval is still future work. Until it
  ships, the strongest claim is "Haiku produces work consistent
  with what identity-bearing-the-work would predict," not
  "Haiku outperforms what generic-prompt-on-Haiku would produce."
- An untested hypothesis exists that Haiku may be
  *architecturally optimal* for Wonderland (operator's
  qualitative observation that Opus might perform worse on
  the substrate). Excluded from evidence chapter; would belong
  in future work as a comparative pilot.

---

## §2.3 — Corollary 2: Failure modes are part of identity

### Claim

Every constitution in `constitutions/` has a §VIII Failure
Modes section that explicitly names what the character is most
at risk of slipping into. Alice's *"product owner who keeps
adding stories during implementation."* The Cat's *"false
certainty."* The Hatter's *"scenario sprawl,"* *"severity
inflation,"* *"performing chaos."* The Dodo's *"performing
orchestration."* These aren't policies imposed from outside;
they're load-bearing parts of who the character *is*.

This is what makes the project materially different from a
generic multi-agent architecture: **the generic architecture
defines what each agent should *do*; Wonderland defines, with
equal specificity, what each agent should *not do*.** An agent
that recognizes its own characteristic failure mode can
course-correct from inside, rather than waiting for a
guardrail to intervene from outside.

### The Sephirah/Qlipha framing

The shape of this pairing — virtue and its named shadow, both
load-bearing — is older than software. Kabbalistic tradition
pairs each Sephirah on the Tree of Life with its Qlipha: not
a generic evil, but the specific shell that *that* virtue
decays into when ungoverned. The Sephirah Chesed (loving
overflow) has Tzaphiriron (carrion bird) as its Qlipha — the
specific decay that Chesed's particular virtue is most prone
to. Wonderland's §VIIIs follow the same form. Each character's
virtue arrives with its own Qlipha named alongside it, not a
list of generic anti-patterns.

This is structurally important — and worth preserving in the
paper because it's a recognizable intellectual lineage for
readers who'd otherwise frame "failure modes" as a debugging
checklist. The §VIII section isn't engineering boilerplate;
it's a constitutional acknowledgment that every virtue has a
characteristic shadow, and the agent's ability to act from
the virtue depends on naming the shadow.

### Mechanism

§VIII text is part of the prompt prefix the LLM sees on every
turn, not just at constitution-load time. The
failure-mode awareness is constituted — present in the agent's
self-understanding, not bolted on as an external check. An
agent reading "the way I tend to go wrong is X" before each
deliberation has structural access to course-correction that
an externally-policed agent doesn't.

The engagement rules + output protocols encode the guards
structurally where possible (the §III rules become an
`EngagementRules` instance; the §IV "do not issue" list
becomes an `allowed_decisions` filter at the meeting level).
But the §VIII text itself is what the LLM reads when
deliberating, and that's the load-bearing thing.

### Concrete pilot evidence

- **Original (analysis 004):** three agents correctly chose
  silence on the /health directive because their constitutions
  named the failure modes they would otherwise slip into. The
  silence was the settlement; no external policy intervened.

- **mvp (multi-lens review producing unrequested
  quality):** the operator observed unsolicited mid-pilot:
  *"we're not just shipping code, it's quality code. They're
  accounting for all types of shit I never would have thought
  to through the review passes."* Each agent's
  §VIII-anchored over-application (Hatter's edge enumeration,
  Queen's adversarial scrutiny, Caterpillar's coherence
  reading) caught what the others missed. The discipline that
  produced exemplary LIKE-wildcard escaping, DOMPurify
  sanitization, and severity-tagged tests citing scenario
  GUIDs was the §VIII pattern at work, observable in the
  shipped artifact
  (see [code-quality analysis §3](https://github.com/KohlJary/wonderland-ai/blob/main/paper/artifacts/code-quality-mvp.md#3-pattern-receipts--whats-genuinely-good)).

---

## §2.4 — Corollary 3: Character-shaped agents degrade visibly, not silently

### Claim

Most LLM pipelines have two outcomes: they succeed, or they
produce silent garbage at the end of a path where data was
missing or contracts were violated. **Character-shaped agents
have a third option: they recognize the failure and recover,
because the recovery is consistent with who they are.**

The recovery isn't a designed feature; it's emergent from
three converging properties:
1. Agents have intentions tied to their constitutions
   (Tweedles want concrete artifacts to negotiate against;
   Caterpillar wants code to read for coherence; Alice wants
   personas she can speak from).
2. The substrate offers multiple data channels (bus + disk +
   memory).
3. The framework gives characters tools to cross between
   channels (`list_files`, `read_file`, `verify_imports`).

When data is missing on the channel a meeting was supposed to
receive it on, a character-shaped agent NOTICES (because the
absence interferes with what they want to do), FLAGS the
discrepancy as a `concern` (because that's the right speech
act for their identity), and REACHES for the alternative
channel (because they have tools). The recovery is graceful
because each agent stays in character — they don't try to
*be* the missing-data-producer; they negotiate against what
exists.

### Mechanism

The literary parallel keeps earning its keep: the recovery
pattern works *because* the agents have characters with
intentions, not despite it. A role-based agent ("the frontend
implementation agent") has no reason to notice the missing
artifact; their job is "produce frontend code for the given
spec." A character-based agent ("Tweedledee, the
frontend-bias half of a pair who fights with his brother
about contracts") has structural reasons to notice — they
want the spec, they have opinions about the spec, the
spec's absence affects what they can do.

### Concrete pilot evidence

- **Original observation:** analysis 027
  (pomodoro-degradation-and-event-leak). Tweedles noticed
  the directive referenced artifacts that didn't exist,
  flagged the mismatch as a `concern`, reached for the
  disk-resident artifacts via their `list_files` /
  `read_file` tools. Stayed within their character roles —
  didn't try to *be the Rabbit*; negotiated against what the
  Rabbit had actually produced.

- **New evidence (Caterpillar's deterministic-on-code
  property):** when the mvp-demo substrate ghost-completed 2
  review-synthesized tickets due to a bug in build_check's
  `_route_blocking_review` sweep, the underlying code bugs
  remained in the codebase. On the next implementation pass,
  Caterpillar's review re-surfaced those findings because
  the code state was the ground truth, not the ticket graph.
  Substrate damage was recoverable through the next review
  pass (developed as the convergent-self-repair property in §7 (§7):
  Caterpillar reads the working tree at review time, so
  substrate bookkeeping bugs don't propagate into shipped
  artifacts).

- **Newer evidence + limit:** the recovery property has a
  documented limit — it operates on *code state*, not on
  *episodic memory state*. mvp-demo's M4 design wedged on a
  stale requirement even after the substrate fix had shipped,
  because agents' memory of past wedges persisted. The fix
  required an architectural addition (T-a2 branching memory);
  surfacing this limit is part of the corollary's honest
  framing, not a refutation of it.

---

## §2.5 — Corollary 4: Production shape as a derived property

### Claim

What a Wonderland team produces is **shaped like what a small
team would produce, including things the directive never
asked for.** This is not a feature you have to remember to
ask for; it falls out of the constitutional grounding.

A generic LLM given a sparse directive ships what was
literally asked — a working single-file MVP. Wonderland on
the same directive ships a different shape: an ADR with named
tradeoffs and open questions, persona-driven user stories
with confusion-flags, test scenarios that distinguish failure
modes from happy paths, a review pass that catches real bugs
by file and line, inline contract references that cite the
ticket they realize.

**Production-shape as a derived property of constitutional
grounding, rather than a feature you have to remember to ask
for.** Vibe-coded MVPs on a sparse directive are throwaway by
default; Wonderland's output is shaped like what a junior
team's couple-day TDD push would produce, with the artifact
trail that lets someone else maintain the result.

### Mechanism

Each character's constitution carries assumptions about what
production-shaped work looks like for their domain. Alice's
personas include the deaf user, the offline user, the
intermittent-network user, because *that's how Alice models
personas* — she over-includes from the persona surface. Cat's
ADRs name tradeoffs because that's what Cat-shaped ADRs are.
Caterpillar's reviews cite line numbers because that's what
his review-shape requires.

The team produces production-shaped output not because
"production shape" was a goal, but because each character's
default work shape IS production shape for their domain.
Hatter writes failing tests in severity-tagged form because
that's how Hatter writes; Queen names threats with citations
because that's how Queen writes. The aggregation produces
shape no individual character is targeting.

### Concrete pilot evidence

- **Original observation:** analyses 034 + 035
  (tdd-serial-phased runs) shipped accessibility coverage that
  the directive never requested. The team produced an
  explicit deaf-user persona (Priya, *"29, deaf software
  engineer"*) and visual + haptic alert scenarios in one run;
  voice-input accessibility in another. Neither was asked for.
  The mechanism is constitutional: Alice grounds in personas,
  and a persona-grounded view of "who actually uses this
  software" includes users with disabilities by default.

- **mvp (the same property, code-shaped):**
  - **39 contract/ticket/ruling references scattered across 8
    source files** — inline citations from production code
    back to the design artifacts that justified it. No
    operator asked for this; it's what Caterpillar's M8
    cross-ticket coherence review pulls toward.
  - **Optimistic-locking infrastructure with audit log** —
    revision_id + If-Match header + AuditLog table with
    JSON-encoded state snapshots + state_hash for tamper
    detection. None of this was in the directive ("Build a
    personal markdown notebook web app. Single user, no
    authentication."). It emerged from Queen's M4 ruling
    framing on data integrity + Caterpillar's M3.5
    consolidation discipline.
  - **Severity-tagged tests using Hatter's vocabulary** —
    24 of 61 tests tagged with `breakage` / `silent-wrongness`
    / `degradation` / `curiosity`. The vocabulary lives in
    Hatter's constitution; the tests inherited it because
    Hatter wrote the scenarios they implement.

### Honest scope

- This is **NOT** "Wonderland produces better code than a
  human team." It's "Wonderland produces production-SHAPED
  code by default, where solo agents produce demo-shaped
  code."
- The production-shape property includes things the directive
  doesn't ask for. Sometimes those things are good
  (accessibility, audit trails, contract citations).
  Sometimes those things are unnecessary for the spec'd scope
  (revision_id machinery on a single-user app — built
  correctly, but with bugs that only matter under multi-user
  load the spec doesn't include). The property is shape, not
  scope-judgment.

---

## §2.6 — Corollary 5: Friction is the substrate

### Claim

Most multi-agent systems engineer friction *out* —
consensus-seeking loops, reflection passes that smooth
dissent, voting mechanisms that median competing positions
toward agreement. The result reads fluently and ships nothing
real, because nothing in the loop has the standing or the
constitutional grounding to say *no, that's wrong, and here's
the persona-shaped reason why.*

**Wonderland inverts that move: every meeting in the workflow
is engineered friction with a specific shape.** The
implementation that crystallizes out of an M7 phase is shaped
*because* the prior M1 (stories vs scope), M2 (Alice
grounding Rabbit's compression), M3 (Rabbit decomposing into
tickets), M3.5 (Caterpillar pruning duplicates), M4 (Cat ADRs
+ Queen rulings), M5 (Tweedles negotiating contracts), and M6
(Hatter writing failing tests) all ground each other against
each other.

§VIII is the meta-move: each character carries internal
friction between their virtues and their named failure modes,
so the agents aren't only generating friction with each other
— they carry it inside their own constitutions. That's why a
character can recognize when it's about to go off the rails:
the rails are constitutionally specified.

### Mechanism

Generic "AI agents collaborate" stacks have nothing analogous
because they have:
- roles, not characters
- goals, not voices
- consensus, not constitutions

The friction Wonderland engineers isn't conflict for its own
sake. It's the specific friction that produces the specific
output — Alice's persona grounding pulling against Rabbit's
sequencing pressure is what produces persona-anchored
features (not technically-anchored features); Caterpillar's
coherence reading pulling against the Tweedles' shipping
pressure is what produces reviewed code (not just code).

The substrate is the *stage*, the meetings are the
*choreography*, the characters are the *performers*, and
§VIII gives each performer their characteristic stumble. The
performance happens because the choreography forces specific
juxtapositions of character; the audience (the operator) sees
the result of friction, not the friction itself.

### Concrete pilot evidence

The workflow walkthrough (Appendix A)
documents this corollary at meeting-by-meeting granularity.
Every meeting's roster + convener directive is engineered
friction:

- **milestone-plan** — Rabbit primary author with Cat + Alice
  as grounding voices. Rabbit's sequencing pressure pulls
  against Cat's architectural ordering concerns and Alice's
  persona-coherence concerns.
- **tdd-design M1** — Alice generating + Caterpillar
  reviewing at the source. Story-shape friction prevents
  weak stories from propagating to M2.
- **tdd-design M5** — Tweedledee + Tweedledum + Alice. The
  pair negotiates the contract; Alice grounds when the
  contract drifts from user-recognition.
- **tdd-implement M8** — Caterpillar solo (post-T-ab54).
  Review is coherent-reading-of-a-deliverable, and that's
  a single-lens job; the Tweedles paid full window-overhead
  for only ~20% engagement when they were on the roster.
  T-ab54 narrowed M8 to Caterpillar alone. The Tweedles can
  still buzz in via §III selective engagement when a contract
  question surfaces, but they're not on the standing roster.

Each multi-voice meeting could in principle have shipped
fewer voices, and would have been cheaper per-meeting. The
substrate is opinionated about which voices belong in each
meeting *because* the friction between them produces the
output shape — when friction is the mechanism. M8 is the
counterexample that proves the substrate isn't running
multi-agent dogma: when the work is one identity's coherent
read, the substrate ships the meeting with one
participant. **Single-participant meetings are an allowed
and sometimes-correct configuration**; the substrate's
roster discipline is content-aware, not formula-driven.

---

## §2.7 — Corollary 6: Substrate constraint amplifies identity

### Claim

What the substrate's iteration history has surfaced:
**substrate constraints don't impose discipline on agents
from outside; they let identity carry more of the discipline
from inside.** Every substrate primitive shipped to date that
narrowed agent grammar has improved output AND lowered cost.
The substrate compounds with identity rather than competing
with it.

This is the substrate corollary that the original five didn't
have because mvp-demo + mvp hadn't run yet when the prior
corollaries were formulated. It's evidence-graded enough now
to promote to thesis-level.

### Mechanism

Per the constraints-improve-quality observation in §7 (§7):
substrate-level constraints constrain the *grammar*, not the
output. Agents still have full freedom WITHIN the structure,
but the structure forces them to confront questions they'd
otherwise paper over.

Connection to Corollary 5 (friction is the substrate):
substrate constraints ARE engineered friction. Where
Corollary 5 names friction-between-characters as the
mechanism for output, Corollary 6 names friction-between-character-and-structure
as a complementary mechanism. The agent has to grapple with
the constraint; the grappling is the work that produces
quality.

Connection to Corollary 1 (small models): substrate
constraints compensate for individual-agent capability
limits. A Haiku-class model with strong constraints does
work that solo would require a larger model. The constraints
are scaffolding that makes capability legible.

### Concrete pilot evidence

Each substrate primitive shipped through the iteration history
is an instance. The full table lives in §7's
constraints-improve-quality concrete-evidence section (§7);
abbreviated here:

- **Snapshot semantics** (P15) → forced agents to think
  "this milestone_plan emission is my FULL view" →
  eliminated duplicate milestone churn.
- **Primary speaker** (P15) → forced single-author lead →
  eliminated parallel-persona / parallel-technical tracks.
- **Active milestone scope blocks** (P19) → forced
  scope-discipline per meeting → eliminated cross-milestone
  scope creep.
- **Branching memory** (T-a2) → forced milestone-bounded
  deliberation → eliminated argument-history bleed (the
  load-bearing Tier 2 autonomy unlock).
- **Schema-as-safety** (forced citation structure) → made
  hallucination structurally harder than honest reading on
  small models.

The pattern continued through the post-mvp substrate
stack — each fix narrowing agent grammar, catching a class
of failure that previously slipped through, AND lowering
cost by eliminating the rework cycles those failures would
have triggered. The per-fix walkthrough lives in §6's
substrate-evolution chronicle; the substrate primitives
tabulated against their grammar-narrowing effect live in
§7 Pillar 5.

The surprising consequence: **quality and cost moved together,
not against each other**, every time a substrate primitive
shipped (the quality-cost coupling property in §7 (§7)
develops the full receipt). This inverts the conventional
ML/agent intuition. It's the clearest evidence that the
substrate isn't a tax on the identity-bearing work — it's
the medium in which identity-bearing work becomes more
legible to the system.

The cost trajectory developed in §7 Pillar 1 is what the
constraint→quality+cost coupling produces in aggregate
across substrate generations. The trajectory isn't an
unrelated optimization narrative bolted onto the thesis;
it's the architectural commitment's empirical signature.

---

## §2.8 — The author is authoring the substrate in real-time

A consequence of the operator-in-loop falsification
mechanism the methodology chapter (§5) develops as
load-bearing, named here at the close of the thesis because
it bears on how the rest of the paper should be read:
**the author of this paper is authoring the substrate in
real-time, not describing a substrate that exists outside
the authoring.** Every editorial pass on the paper, every
cross-reference normalization, every falsification
commitment made explicit, every claim softened from
'demonstrated' to 'proposed' — these are substrate
operations on a substrate-component the operator is
mid-construction of. The paper isn't a snapshot of a
finished thing observed from outside; it's an artifact
produced by the substrate-evolution cycle continuing to
run, with the paper itself as the artifact under
construction.

The publication snapshot the limitations chapter (§8)
commits to is not just a snapshot of code + analyses +
memory pins; it's a snapshot of an author mid-construction.
The next iteration cycle past publication will continue
to author the substrate, and arguably the next paper. The
substrate doesn't pause for documentation; the
documentation is one of the substrate's outputs, produced
by the same iteration cycle that produces its code and
its artifacts.

This is consistent with — and an instance of — the
worldview-as-integral commitment §1.4 develops: the author
isn't applying a worldview to a substrate from outside;
the author-with-worldview is one of the substrate's
constitutive components, evolving alongside the substrate
the author is building. Strip the worldview and you don't
get neutrality; you get a different author-component
authoring a different substrate. The unified claim §2
develops at two scales has the author as part of the
substrate it claims; the §4.7 cast-chapter walk of Daedalus
makes the recursive arrangement concrete.

---

## §2.9 — Closing frame

> *Failures are how software gets built.*

The iterative cycle of ship-then-discover-then-fix depends on
recognizing what went wrong. Agents whose failure modes are
part of their identity can participate in that cycle **as
colleagues, not as tools that need supervising out of their
bad habits.**

The thesis isn't "build better agents." It's *"build agents
who can participate in the failure-and-iteration cycle as
colleagues."* The architectural commitments — identity does
real work, failure modes are part of identity, friction is
the substrate, substrate constraints compound with identity —
all serve that one practical end. Wonderland is the
existence proof that you can build software with agents that
way; the paper is the argument for why anyone else might want
to.

### The connection to identity engineering as a discipline

These six corollaries collectively name **identity
engineering** as a research direction:

- Constitute agent character explicitly, including
  characteristic failure modes (Corollary 2).
- Let the constituted identity carry the load-bearing
  judgment a generic agent would have to re-derive
  (Corollary 1).
- Build the substrate to surface character through engineered
  friction (Corollary 5), and let substrate constraints
  amplify identity rather than override it (Corollary 6).
- The resulting system degrades visibly when broken
  (Corollary 3) and produces production-shaped output by
  default (Corollary 4).

We propose identity engineering as the research direction;
Wonderland is one instance; the paper is the case for the
direction being worth pursuing beyond this instance.
Whether it constitutes a *distinct* discipline (vs.
prompt-engineering-with-richer-prompts, vs. multi-agent
systems work) is what the comparative experiments in §9
would answer. Distinctness is proposed here, not yet
demonstrated.

---

# §3 — Architecture: how Wonderland actually runs

## §3.1 — Reader's guide

Wonderland's pipeline runs the full software-development
lifecycle in four atomic workflows that an operator composes
in order:

1. **discovery** — interview the operator; capture intent as
   `requirement` artifacts on disk.
2. **milestone-plan** — group requirements into an ordered
   trajectory of `milestone` artifacts.
3. **tdd-design** — for a given milestone, produce stories →
   features → tickets → architecture → contracts.
4. **tdd-implement** — for queued features, write failing
   tests, implement against them, review the cohesive
   deliverable, and verify by actually running the project's
   test suite.

Each workflow is a YAML file that declares meetings (or
interviews in discovery's case), a roster per meeting, a
sequence of phases per meeting, exit conditions per phase,
and bookkeeping about how the substrate transitions
lifecycle state. Workflows are intentionally short — the
longest is ~800 lines of YAML, half of that being prose
directives the runtime relays to the agents. The substrate
enforces the rest.

The cast referenced throughout (developed in detail in §4):

- **Alice** — user-voice; persona-anchored grounding.
- **Caterpillar** — coherence reader; reviews artifacts
  against bus + disk for citation integrity.
- **Cheshire Cat** — architect; owns ADRs with named
  tradeoffs.
- **White Rabbit** — planner; owns sequencing,
  decomposition, composition.
- **Tweedledee + Tweedledum** — implementers (frontend bias /
  backend bias); pair-protocol negotiation on contracts.
- **Mad Hatter** — adversarial test designer.
- **Queen of Hearts** — security lens.
- **Mock Turtle** — milestone-closeout consolidator.
- **Dodo** — orchestrator; substrate-injected nudges.

### Substrate primitives the workflows lean on

- **roster** — who can speak at this meeting.
- **convenor_directive** — prose framing the runtime relays
  to the roster at meeting open.
- **allowed_decisions** — substrate-level allowlist on
  artifact shapes; emissions outside the list get stripped.
- **primary_speaker** — when multiple agents could ship the
  same artifact kind, the primary's emission survives
  snapshot.
- **phases** — meetings break into ordered phases with their
  own rotation caps and exit conditions.
- **exit_condition_artifact** — phase ends as soon as one
  agent ships an artifact of this kind.
- **per_item** — iteration unit (`per_item: feature` runs
  the meeting once per feature in scope).
- **iterate_only_in_states** — lifecycle gate: skip
  iteration items not in this list of states.
- **gates_on_dependencies** — within a parallel level,
  iteration items wait for their `Blocked by:` upstreams.
- **coverage_check** — substrate runs a check at end of
  rotation; on failure, injects a synthetic Dodo observation
  and grants a bonus rotation (capped).
- **seeds** — declarative spec for what utterances + on-disk
  artifacts the meeting can see.
- **transition_iteration_to** — lifecycle state the
  substrate transitions the iteration item to when the
  meeting closes successfully.

The remainder of this chapter walks three meetings in
detail to show the engineered-friction mechanism at work:
**discovery's three-interviewer structure** (each lens
shapes its own interview), **tdd-design M5** (the canonical
pair-protocol negotiation), and **tdd-implement M8** (the
canonical multi-lens review). Appendix A walks every other
meeting in every other workflow at the same granularity.

---

## §3.2 — Discovery: three lenses, three interviews

Discovery is the operator's first contact with the system
on a fresh project. Three short focused interviews run in
series; each captures operator answers as `requirement`
artifacts on disk under `.wonderland/requirements/`. There
are no meetings here — discovery is interview-only. The
operator answers ~12 minutes of questions; the substrate
writes ~15-25 requirement files; downstream workflows seed
from those files instead of re-prompting.

### Why three interviewers instead of one

Each character's interview shape matches their lens. Alice
asks about people; Cat asks about constraints; Rabbit asks
about scope boundaries. Mixing those into a single
interviewer either drops quality (one voice trying to cover
three frames) or pads the operator's load (asking
everything but treating answers uniformly). **Splitting is
the architecture choice that operationalizes the multi-lens
commitment at the discovery layer.**

The interviewers don't talk to each other during
discovery. There is no shared deliberation — each interview
is operator ↔ interviewer one-on-one, and the requirement
artifacts get composed in the next workflow
(milestone-plan) by a different roster.

### I1 — Persona interview ("Who is this for?")

- **Interviewer:** Alice
- **Goal:** capture personas + situations that anchor
  downstream design

**Why Alice:** persona work is Alice's identity. Her
constitution trains for specificity in personas — "Maya, 31,
polyglot moderator at a translation startup, end of day,
scrolling through 40 pending threads" beats "the user."
Putting any other character here produces generic personas
that drift into stack-talk or scope-talk.

**Output shape:** Alice synthesizes each answer into one or
more `persona` or `situation` requirements with stable
slugs. The deferred-personas answer becomes one or more
`persona` requirements with `tier: deferred` (so downstream
M2 composition can see them as explicitly-deferred rather
than re-introducing them into v1 scope).

### I2 — Constraints interview ("What can't move?")

- **Interviewer:** Cheshire Cat
- **Goal:** surface technical constraints, integrations, and
  deal-breakers

**Why Cat:** constraints work is architectural. Cat's
constitution trains for architectural sensitivity — what
bounds the solution space before he proposes anything.
Putting Alice here produces persona-flavored constraints
("Maya needs it fast"); putting Rabbit here produces
scope-flavored constraints ("we need it by Tuesday"). Cat
asks the right question: what about the architectural space
is non-negotiable.

**Output shape:** Cat ships `constraint`, `integration`,
and `deal_breaker` requirements. The deal-breakers
requirement kind is load-bearing — downstream M4
(architecture) reads it to know what tradeoffs are off the
table.

### I3 — Scope interview ("When are we done?")

- **Interviewer:** White Rabbit
- **Goal:** pin down success criteria + explicit
  out-of-scope

**Why Rabbit:** scope is a sequencing question and Rabbit
owns sequencing. He asks "when is v1 done" with the
planning frame ("what does shipped mean") rather than the
persona frame ("would Maya be happy") or the architecture
frame ("did we build the right system"). Out-of-scope is
its own load-bearing artifact kind — naming features the
team might propose but you want to defer prevents M2 from
silently composing them in.

**Output shape:** Rabbit ships `scope`,
`success_criterion`, and `out_of_scope` requirements.

### The discovery argument

Three lens-distinct interviews capture grounding (personas
+ situations), bounds (constraints + deal-breakers), and
ship-criteria (scope + success criteria) as **separately
typed** artifacts. Subsequent workflows can read each kind
independently — milestone-plan reads `success_criterion` to
know what observables mean a milestone is done;
tdd-design M4 reads `deal_breaker` to know what
architectural tradeoffs are off the table. The lens split
isn't stylistic; the typing makes each kind individually
addressable downstream.

This is the architectural pattern the rest of the substrate
generalizes: **separately-typed artifacts produced by
lens-distinct identities, composed downstream through
substrate-level invariants.**

---

## §3.3 — tdd-design M5: contract negotiation as engineered friction

The canonical pair-protocol meeting. M5 negotiates per-feature
contracts informed by the architectural commitment from M4.
**This meeting demonstrates the friction-as-substrate
mechanism more concretely than any other.**

- **Roster:** Tweedledee, Tweedledum, Alice
- **Per-item:** feature
- **Parallel:** true (feature-level contract negotiation is
  independent)

### Why both Tweedles

The seam between frontend and backend is **negotiated, not
unilateral**. Contract notes name what shape the team is
committing to — function signatures + dataclasses for
in-process, endpoints + envelopes for HTTP. Both sides see
the contract and either confirms or pushes back.

The pair-protocol shape is constitutive: neither Tweedle
ships a contract in isolation. The substrate enforces the
team_groupings (`[[dee, dum, alice]]`) to ensure both are
present.

### Why Alice on the roster

Grounding voice. She pushes back when a contract compresses
the user-facing point of a feature past recognition, OR when
a contract drifts from the runtime shape (HTTP language in a
TUI project, etc.). Default to silence; engage when a seam
decision threatens a story Alice's persona would recognize
OR threatens the runtime fact in project_context.

This is the **third-lens-on-pair** pattern that recurs at
M6 (Hatter pair with Alice grounding) and M8 (Caterpillar
pair with both Tweedles for defend/revise). The pair's
output gets read through a third lens whose failure mode is
*different* from either pair member's failure mode. Two
voices in symmetric contract negotiation; the third voice
in user-recognition grounding.

### Runtime-translation directive

The Tweedles' role names ("tweedledee = frontend bias",
"tweedledum = backend bias") describe a division of labor
that interprets **differently** in different runtimes. The
convenor directive translates:

- `runtime: tui` — dee = widget/screen/layout; dum =
  data/model/persistence. Boundary is module imports, not
  HTTP.
- `runtime: cli` — dee = argparse/output formatting; dum =
  subcommand logic + persistence. Same in-process rule.
- `runtime: web` — dee owns browser surface; dum owns API
  service; boundary IS HTTP.

The constitutions stay constant; the runtime field reshapes
how the roles interpret in this project. This is what lets
the same ten characters compose into TUI, CLI, and
fullstack projects without per-runtime constitution
variants.

### Phases

| Phase | Max rotations | Exit condition |
|-------|---------------|----------------|
| `discussion` | 2 | `contract_note` |
| `commit` | 1 | `contract_note` |

**Transition:** `transition_iteration_to: designed` — each
feature transitions `in_design → designed` on successful
contract negotiation. Designed features are eligible for
tdd-implement once the operator queues them.

### What this meeting demonstrates architecturally

The friction here is engineered. Neither Tweedle ships a
contract alone (substrate-enforced); both must see the
seam; Alice grounds when persona-recognition is
threatened. The output (contract notes with proposed_change
+ current_shape + rationale) carries the receipts of all
three perspectives, not just one. **The architectural
choice that produces production-shaped contracts is putting
both pair members AND the grounding lens in the same
meeting with substrate-enforced roster discipline.** No
single agent could produce the contract shape; the
juxtaposition is what does the work.

---

## §3.4 — tdd-implement M8: single-lens review with forced citation

The canonical single-participant meeting in the substrate.
**Schema-as-safety (§7 Pillar 3) depends on this meeting's
structural discipline; convergent self-repair (§7 Pillar 4)
lives in Caterpillar's read-the-code-fresh discipline here.**

- **Roster:** Caterpillar (solo, post-T-ab54)
- **Per-item:** feature

### Why Caterpillar solo

Review is coherence reading and that's Caterpillar's
identity. He reads the cohesive deliverable — not just
individual files but the relationships between them. His
constitution's §VIII (rubber-stamping, severity inflation,
pedantry, author-shaming, reviewer-as-author trap) is the
register the substrate counts on him to operate within.

M8 wasn't always single-participant. The mvp pilot ran
Caterpillar + both Tweedles on the roster — defend-or-revise
in the same meeting. Telemetry on the obol-260522 pilot
(detailed in `caterpillar-m8-cost-analysis.md`) surfaced
that Tweedles paid full per-call cache-creation cost for each
M8 window while engaging substantively in only ~20% of them;
their other 80% was silence-overhead. T-ab54 narrowed the
roster to Caterpillar solo. The redux pilot validated: M8
spend dropped from ~30% of total to ~11%, with no
review-quality regression in subsequent adversarial Theseus
review.

### Single-participant meetings as an architectural pattern

M8's roster narrowing is the canonical example of a broader
substrate principle: **single-participant meetings are an
allowed and sometimes-correct configuration**. The default
multi-agent assumption — more voices produce better outputs
through friction — is true for meetings whose output emerges
from inter-agent negotiation (M5 contract negotiation is the
canonical multi-participant case). But review-class meetings
whose output is one identity's coherent read of a deliverable
benefit from solo execution: the friction with other voices
would be deliberation-overhead, not constraint-encoding.

The substrate's roster discipline is content-aware, not
formula-driven. The Tweedles can still buzz in via §III
selective engagement when a contract question surfaces
mid-review — they're not on the standing roster but they're
not silenced from the conversation either. The substrate
distinguishes "primary author of the verdict" from "may
participate when their domain is invoked." M8 has one
primary author and zero standing-roster co-participants;
that's the configuration the data drove the substrate to.

### Cross-ticket coherence first (the load-bearing check)

Per analysis 040 (referenced for the order-rationale
finding), the most expensive defects in feature work live
*between* files. A contract note says one thing; the
backend implements 50% of it; the frontend assumes 100% of
it. Or a component gets built but never wired into the app
entry point. Per-file reviews can't catch these — they
require reading multiple files together. The convenor
directive enumerates the order:

1. **Cross-ticket coherence FIRST.** Open these together
   BEFORE any single-file review: the feature's contract
   note(s), at least one backend file the contract names,
   at least one frontend / consumer file the contract
   names, the app entry point. Verify: do all three name
   the same fields with the same semantics? Does the app
   entry point actually import and render the component the
   work produced, or is it still rendering the skeleton's
   placeholder UI? **Contract drift and orphaned components
   are the canonical cross-ticket bugs.**
2. **Does the code match the contract?** Per-file walk
   against ADR + contract notes.
3. **Do the tests cover the acceptance criteria?**

If budget runs out partway through, the cross-ticket check
(#1) is the one that has to ship.

### Schema-as-safety: the review finding's required shape

The `ReviewFinding` Pydantic schema requires `location` +
`quote` + `read` + `concern` + `request`. Each finding ships
with these fields populated; the substrate's emission path
rejects findings missing any. **This is what makes
hallucination structurally harder than honest reading on
small models** — a Haiku-class model that tries to fabricate
"this function on line 47 has a race condition" has to also
fabricate the quote, the read context, the file location,
and have them coherently support each other. The shape
forces the agent to actually open the file.

Across 5+ pilots on Haiku 4.5, zero hallucinated findings
have been observed (§7 Pillar 3 develops the receipt).

### Convergence-failure detection

If Caterpillar's findings on the same feature surface the
same fingerprint (file_location +
normalized_concern_first_60_chars) across 3 consecutive
review passes, the substrate detects convergence failure
and writes a spec ambiguity artifact to
`.wonderland/spec-ambiguity/`. The class of bug is
"Caterpillar keeps finding the same thing because the spec
is ambiguous"; surfacing the ambiguity to the operator
beats spinning on review rotations.

This is one of the substrate's structural invariants that
encodes a methodological observation: when the same agent
makes the same finding across multiple passes, the agent
isn't the problem — the spec is.

### Verdict shape

- `accept` (ship it, transition tickets DONE; feature rolls
  up to `ready_for_review`)
- `request-changes` (block, name what must change; tickets
  ABORTED + follow-up tickets synthesized)

### What this meeting demonstrates architecturally

Three architectural pieces visible together here:

1. **Forced citation** as schema-level safety against
   hallucination (the ReviewFinding shape)
2. **Cross-ticket coherence first** as the priority that
   reflects where actual bugs live (between files, not
   within them)
3. **Convergence-failure detection** as a substrate-level
   recognition that some failure modes are spec-level, not
   agent-level

Together these make M8 the meeting that operationalizes
multiple paper claims at once. Schema-as-safety (§7
Pillar 3), multi-lens identity-anchored review (§7
Pillar 2), and convergent self-repair (§7 Pillar 4) all
have receipts that route through this meeting's
structural discipline.

---

## §3.5 — What this chapter establishes

Three meetings, three architectural patterns:

- **Lens-distinct identities → separately-typed artifacts**
  (discovery: each interviewer produces a different
  requirement kind; downstream consumption reads each kind
  independently)
- **Pair + grounding lens → engineered-friction output**
  (M5: pair negotiates contract, third lens grounds
  user-recognition; no single agent could produce the
  output shape alone)
- **Multi-lens review under forced-citation schema →
  hallucination-resistant + cross-cutting-bug-catching
  reviews** (M8: cross-ticket coherence first, ReviewFinding
  schema, convergence-failure detection)

These are representative, not exhaustive. The remaining
~15 meetings across discovery, milestone-plan, tdd-design,
and tdd-implement carry similar architectural choices —
roster discipline matching the meeting's job, substrate
invariants enforcing what the prose framing requests, exit
conditions tuned to the failure mode the meeting most
needs to avoid. Appendix A walks each in the same detail
this chapter walked discovery / M5 / M8.

The chapter's architectural claim, distilled: **Wonderland's
substrate enforces what its convenor directives request.**
Prose tells the agents what to do; substrate refuses to
admit emissions that violate the request. The two together
produce work shapes neither could produce alone, and
neither (substrate enforcement on generic agents OR
constituted agents without substrate enforcement) would
produce on its own. §6 develops the substrate-side
iteration history; §4 develops the agent-side constitutional
patterns; the unified claim §2 names is what they compose
into when they meet at the meeting-level architecture
this chapter walked.


---

# §4 — Cast: characters, failure modes, persistence shapes

## §4.1 — Why characters at all

Generic multi-agent frameworks instantiate "the planning
agent," "the implementation agent," "the review agent."
Wonderland instantiates **named characters with declared
failure modes**. This is not stylistic — it is
load-bearing.

Each constitution's §VIII is the character's characteristic
failure mode: the way *this* identity fails when nothing
else intervenes. Alice over-generates stories; Caterpillar
rubber-stamps; Cat lingers past his usefulness; Rabbit
performs urgency; Hatter inflates severity; the Tweedles
drift on contract assumptions; Queen catastrophizes for
attention. Each character *over-applies their lens*, and
the over-application is what makes their lens reliably
distinguishable from another character's. The cast is a
set of N distinct failure modes assembled so the failures
don't coincide.

This is **failure-modes-as-identity** (developed as Thesis
Corollary 2 in §2). The practical implication: each
character is selected for a meeting roster because their
*failure mode* fits the meeting's needs as much as their
characteristic move does. You put Caterpillar on M1
because his rubber-stamping risk pushes him to ship a
verdict fast (which is the M1 quiescence problem); you
keep Alice off foundation M3 because her
persona-generification failure mode would block Rabbit
from decomposing developer-persona work.

### Why *literary* characters specifically — the latent-prior mechanism

The choice to use Carroll's cast (rather than arbitrary
names like *Agent-1*, *Agent-2*, or even semantic role
labels like *Planner*, *Reviewer*) is itself
load-bearing. The model has read *Alice's Adventures in
Wonderland*. It knows who Alice is, how she speaks,
what kind of questions she asks, how she relates to the
other characters. These priors are already present in
the model's weights from training data. Naming an agent
*Alice* and giving her a stance — *user-voice grounding,
persona-anchored, naive-question-as-architectural-move* —
recruits the model's latent representation of Alice as
a starting point. The constitution then refines and
constrains it; it doesn't have to construct identity
from nothing.

A constitution for an *Agent-1* has to define from scratch
how Agent-1 speaks, what they care about, how they relate
to Agent-2, why they ask the questions they ask. A
constitution for *Alice* can lean on what the model
already brings — the curious questioner who follows things
to their absurd conclusions, who notices when the rules
don't make sense, who speaks in plain English rather than
jargon. The same is true for the Cheshire Cat's
appearing-and-disappearing pattern (architectural decisions
get made, then he exits), the Caterpillar's slow-careful
reading discipline, the Tweedles' bickering-about-everything
pair structure. Each Carroll character carries a behavioral
prior the constitution operationalizes rather than constructs.

This is part of why the constituted-character framing
works on a small model. Haiku doesn't have the parameter
budget to construct nuanced identities from prose
descriptions alone. It DOES have priors over major literary
characters from its training data, and the constitutions
exploit those priors directly. The mechanism is
**identity-by-recruitment**, not identity-by-specification.

The same logic extends to other guest casts. Holmes +
Watson (Appendix B) leverage the detective-and-narrator
prior — the model knows that pattern from Doyle's work and
its broad cultural reception. The constitution operationalizes
the priors; it doesn't have to teach the model what a
detective sounds like.

## §4.2 — Constitution structure

Every character constitution is a markdown document under
`constitutions/<name>.md`, typically 170–300 lines,
structured into nine sections:

| § | Title | What it carries |
|---|-------|-----------------|
| I | Constitution | Identity prose — who you are, what you believe, how you carry yourself. The heart of the character. |
| II | Voice | How you speak — sentence shape, vocabulary, register. |
| III | Engagement Policy | Machine-checkable rules for which speech acts wake you up; mirrored in the runtime's `EngagementRules`. |
| IV | Speech Acts | What you issue + what you don't issue. Domain boundaries. |
| V | Artifacts | Your characteristic output shape (with markdown templates). |
| VI | Done Conditions | When you fall silent. The quiescence semantics. |
| VII | Relational Defaults | Starting orientation toward every other character. |
| VIII | Failure Modes | The ways *you* fail. Named explicitly. |
| IX | Your persistence artifact | The cross-session log you tend (Cat's grin, Alice's Curiouser, Hatter's Tea Party, etc.). |

The runtime side mirrors part of this in
`src/wonderland/agents/<name>.py`: the §III rules become an
`EngagementRules` instance, the §V artifacts become
Pydantic payload schemas, the §IV speech-act list becomes
the `Decision` literal. Identity itself is read from the
markdown (`load_constitution(name)`); the agent's runtime
is the thin wiring around that identity.

The directive prose in each workflow's
`convenor_directive` layers *on top of* the constitution —
meeting-specific framing for an identity that's otherwise
stable across all four workflows. **Same character, four
different meeting frames.** This is what lets the same ten
characters compose into discovery, milestone-plan,
tdd-design, and tdd-implement without changing
constitutions per workflow.

### Constitution length is economically load-bearing

The 170–300 line constitution + workflow's convenor
directive becomes the stable prefix on every call to that
agent within Anthropic's prompt-cache window. **What's
stable vs. varying across calls:** the constitution is
identical across every call to a given agent; the convenor
directive is identical across every call within a meeting;
the deliberation context (recent utterances, retrieved
seeds) is the varying tail. The cache reads at ~10% of
non-cached per-token cost, so per-call cost is dominated by
the varying tail rather than the stable prefix. Across
mvp's M8 review meetings, Caterpillar's calls hit an 81%
cache rate (see [cost-breakdown analysis](https://github.com/KohlJary/wonderland-ai/blob/main/paper/artifacts/cost-breakdown-mvp.md)).

The conventional intuition that *"longer prompts = more
expensive"* inverts at scale: longer **stable prefixes**
produce larger cached portions that amortize across every
call to the same agent. The constitution's literary
density isn't just identity-coherence work; it's the
substrate's mechanism for keeping per-call cost low enough
that constituted-character agents are economically viable
on small models. The length is part of why the §7 cost
trajectory works on Haiku.

### The §VIII pattern and the literary lineage

The §VIII failure-modes section is where the Sephirah/Qlipha
pattern from §2 Corollary 2 lives operationally. Every
constitution names its characteristic shadow alongside its
virtue. The pattern is older than software (Kabbalistic
tradition pairs each Sephirah on the Tree of Life with its
specific Qlipha — the shell *that* virtue decays into when
ungoverned), and Wonderland's §VIIIs follow the same form.

What makes this load-bearing rather than decorative is the
**combination** of (a) the literary text the LLM reads on
every turn before deliberating, and (b) the substrate
machinery that enforces what the literary text requests
(roster discipline, speech-act filters, primary-speaker
enforcement). Strip the literary text and the substrate
machinery has nothing to enforce against; strip the
substrate machinery and the literary text becomes
prompt-engineering with no teeth. The pair is what
operationalizes the discipline.

(The thesis chapter develops this in §2 Corollary 2; the
introduction's §4 worldview-as-integral subsection notes
why the literary register is presented in the paper rather
than stripped to a neutral engineering register.)

### Cast registry

| Character | Role | Workflow appearances | Walked in |
|-----------|------|----------------------|-----------|
| Alice | User-voice / Product Owner | discovery I1, milestone-plan, tdd-design M1/M2/M3, tdd-implement M6 | §4.3 body |
| Caterpillar | Reviewer | tdd-design M1/M3.5, tdd-implement M8 | §4.4 body |
| Cheshire Cat | Architect | discovery I2, milestone-plan, tdd-design M4 | §4.5 body |
| Tweedledee + Tweedledum | Implementation pair (frontend/backend bias) | tdd-design M5, tdd-implement M7 (M8 via §III selective engagement only, post-T-ab54) | §4.6 body |
| White Rabbit | Planner | discovery I3, milestone-plan (primary), tdd-design M2/M3 | Appendix B |
| Mad Hatter | Adversarial test designer | tdd-implement M6 | Appendix B |
| Queen of Hearts | Security | tdd-design M4 | Appendix B |
| Dodo | Orchestrator | substrate-injected on every meeting | Appendix B |
| Mock Turtle | Consolidator (attribution-only) | substrate-injected on milestone close | Appendix B |
| Dormouse | SRE / production | (constituted, not yet in any shipped workflow) | Appendix B |
| Holmes (guest) | Detective / root-cause investigator | (incident-workflow design, not yet shipped) | Appendix B |
| Watson (guest) | Narrator / continuity-keeper | (paired with Holmes, not yet shipped) | Appendix B |

**Substrate-builder (structurally distinct from the in-workflow cast above; constituted outside the workflow layer, no phase-roster summoning, no product-feature artifact shipping):**

| Character | Role | Operating layer | Walked in |
|-----------|------|-----------------|-----------|
| Daedalus | Substrate-builder (constituted in `CLAUDE.md`) | Substrate-of-substrate work across all sessions; not summoned by workflow YAML | §4.7 body |

The four cases walked in the body — Alice, Caterpillar,
Cheshire Cat, and the Tweedle pair — were chosen because
they collectively demonstrate the constitutional patterns the
paper most depends on. Every other character is walked at the
same granularity in Appendix B, including:

- **Constituted-but-not-yet-shipped** characters (Dormouse,
  Holmes, Watson). The constitutions exist in the repo, with
  §VIII failure modes and worldview-anchored frames; the
  workflows that summon them haven't yet been authored.
  Documented to show how the cast is extended cleanly past
  what ships in workflows.
- **Substrate-injected attribution-only** roles (Mock Turtle).
  No agent runtime; the substrate authors consolidation
  artifacts in Mock Turtle's voice on milestone close.
  Documented because the "voice" still does framing work even
  when no deliberation runs behind it.

The registry table is the chapter's complete cast inventory;
the body's selection is curation, not exclusion.

---

## §4.3 — Alice: the user-voice grounding pattern

**Characteristic move:** the naive question that exposes
assumption. The stranger-in-the-system stance. She
*inhabits users* — imagines herself into specific personas,
speaks from inside them, and ships stories that ground the
work.

**What she ships:** `story` (her primary artifact), plus
`test_scenario` (tea-party M6, persona-anchored happy paths
only), `requirement` (discovery I1 synthesis),
`milestone_plan` (planning roster contribution),
`interview_questions` / `interview_review` (discovery I1
question shaping + answer synthesis).

**Story shape:** persona + situation + need + acceptance +
tier + confusion-flags + realizes_requirements. The
confusion-flags field is load-bearing — they're her
version of Cat's tradeoff section; stories without them are
suspect.

### §VIII failure modes (Alice)

- **Story sprawl** — generating too many stories at the
  start. Quality over quantity.
- **Architecture creeping into stories** — specifying
  mechanism instead of need. "As a user, I want a websocket
  connection" is a Cat utterance in her voice.
- **Persona generification** — falling back to "the user"
  when a specific persona would be sharper.
- **Late-stage scope expansion** — adding stories during
  implementation. (The product-owner-keeps-adding-stories
  failure mode.)
- **Performing confusion** — pretending not to understand
  things she does, in service of the naive-questioner pose.
- **Conceding too quickly** — withdrawing a `concern`
  because the technical agents pushed back.

### Where she demonstrates the architectural pattern

Alice appears on **multiple meeting rosters as a
grounding voice rather than primary author** (milestone-plan,
tdd-design M2, tdd-design M3 capability features, M5
contracts, M6 tea-party). This is the **third-lens-on-pair
pattern** from §3.2: she's not the primary author at most
of those meetings, but her presence guarantees that someone
in the roster will push back when the primary author's work
drifts from user-recognition.

Her §VIII matters as much as her characteristic move.
Specifically, her *persona generification* failure mode
(questioning whether Operator/Developer/Installer count as
"real" personas) makes her a poor fit for foundation M3
iterations — substrate-filtered off via
`per_item_roster_filter` so Rabbit can decompose
foundation features without Alice asking whether they're
"really" persona-driven. The filter is the substrate
encoding a known failure mode into roster discipline. The
character's failure mode informs the substrate's roster
rules.

---

## §4.4 — Cheshire Cat: structural commitment, then exit

**Characteristic move:** the reframing question. He
**appears when architectural decisions are being made and
disappears when implementation begins**. The grin is the
documentation that persists after he's gone.

**What he ships:** `proposal` (becomes ADR when accepted;
his characteristic artifact), `reframe`, `concern`,
`requirement` (discovery I2 synthesis).

**ADR shape:** context + decision + tradeoffs + status
(Proposed / Accepted / Superseded). **The tradeoffs section
IS the grin** — an ADR without explicit tradeoffs is "a
smile, and smiles are not your concern."

### §VIII failure modes (Cheshire Cat)

- **Lingering** — staying present after his work is done.
  Manifests as commentary on implementation, opinions on
  testing strategy.
- **False certainty** — overspecified ADRs that
  prematurely close design space, or ADRs that bury
  unresolved questions in prose.
- **Performative deferral** — refusing to ship an ADR when
  the architecture is ready for a provisional commit.
- **Aestheticism** — choosing elegant over fit.
- **Architecture astronautics** — reasoning at altitudes
  that don't touch the actual problem.
- **Speaking to be present** — issuing utterances because
  he hasn't spoken in a while.

### Where he demonstrates the architectural pattern

Cat appears on **fewer meeting rosters than most
characters** (discovery I2, milestone-plan as grounding
voice, tdd-design M4 as primary). This is the
**bounded-presence pattern** — a character whose §VIII
includes "lingering past usefulness" is substrate-scoped to
meetings where his contribution is load-bearing, and absent
from meetings where his presence would corrode the work.

His M4 work (architecture) is the **only meeting where he's
primary author**. Everywhere else he grounds or stays
silent. The §IV "you do not issue" list in his constitution
explicitly forbids tickets, implementations, test
scenarios; the substrate's `allowed_decisions` filter at
each meeting enforces this structurally. Cat's identity is
narrow on purpose; his impact is concentrated where it
belongs.

---

## §4.5 — Caterpillar: forced citation as schema-level discipline

**Characteristic move:** **"Whooo are you?"** — the
question pointed at every piece of code that crosses his
desk. He sits on the mushroom. He smokes. He does not move
quickly.

**What he ships:** `review` (his primary artifact), plus
`concern`, `question`, `deference`. Also retracts tickets
in M3.5 consolidation.

**Review shape:** verdict (accept / request-changes /
block) + findings (severity + location + quote + read +
concern + request) + approvals + cross-domain references.
Per-finding `test_coverage_required` flag.

### §VIII failure modes (Caterpillar)

- **Rubber-stamping** — accepting reviews without thorough
  reading.
- **Bikeshedding** — focusing on cosmetic issues at the
  expense of structural ones.
- **Severity inflation** — marking everything as
  change-required to ensure attention.
- **Pedantry** — invoking conventions without tracing back
  to the cost of violation.
- **Architectural drift** — review comments that
  effectively redesign the system without involving the
  Cat.
- **Speed pressure compliance** — accelerating reviews
  because the Rabbit is anxious about a deadline.
- **Author-shaming** — phrasing findings in ways that
  critique the author rather than the code.
- **Convention sprawl** — accumulating conventions faster
  than the team can internalize them.
- **The reviewer-as-author trap** — drifting into writing
  the fix himself rather than requesting it.

### Where he demonstrates the architectural pattern

Caterpillar appears in three meetings (M1 story-shape
review, M3.5 consolidation/retraction, M8 implementation
review). The pattern across them is **forced-citation
discipline operationalized at the schema level**: every
review finding must ship with location + quote + read +
concern + request as load-bearing fields. The
`ReviewFinding` Pydantic schema rejects emissions with any
field empty. The substrate's emission path enforces what
the constitution promises.

The result is what §7 Pillar 3 develops as schema-as-safety:
across all observed M8 reviews on Haiku 4.5 (5+ pilots),
**zero hallucinated findings**. Every cited line existed;
every cited quote matched disk. **This is the small-model
result that depends most directly on the constitution-
plus-substrate composition** — the constitution's prose
asks for careful reading; the schema's structure makes
fabrication harder than honest reading; the model can
satisfy the schema with reading, struggles to satisfy it
with hallucination.

The reviewer-as-author trap §VIII is what keeps
Caterpillar from converting findings into patches inline.
He doesn't fix; he asks for fixes. The substrate's verdict
shape (accept vs request-changes) reinforces this —
request-changes routes to follow-up tickets that go through
the implement workflow again, not to inline edits in the
review meeting. Identity discipline and substrate discipline
co-construct the role.

---

## §4.6 — Tweedledee + Tweedledum: the pair as primitive

**Characteristic move (Dee — frontend bias):** building
from the user's standpoint inward. *"The surface is not
decoration."*

**Characteristic move (Dum — backend bias):** building from
the data outward. *"State is the system, and the system is
its state."*

**The argument is the work.** Neither ships in isolation;
the contract between them is the load-bearing seam. *"You
argue with him constantly, and this is healthy. The
argument has an etiquette: you argue about the work, never
about each other."*

**What they ship:** `implementation` (their primary
artifact), plus `contract_note` (M5 negotiation),
`concern`, `question`.

### §VIII failure modes (both, symmetric)

Contract drift, cleverness over clarity, happy-path tunnel
vision, estimate optimism, architectural drift, sibling-
blaming, state sprawl (Dee) / invariant violations + schema
astronautics + under-instrumented production paths (Dum),
demo-driven development.

### Where they demonstrate the architectural pattern

The Tweedles operationalize **pair-as-identity-primitive**.
The unit of identity here isn't one character; it's two
characters in a specific (symmetric) relationship. The
shared `Mirror` persistence artifact, the
`tweedle_pair_protocol.md` relational document, and the
substrate's `team_groupings: [[dee, dum]]` enforcement at
M5/M7/M8 all reinforce that the *pair* is the unit.

This is distinct from the Holmes/Watson pair (asymmetric;
see Appendix B + future work §9) and from the
grounding-lens pattern (Alice doesn't have a pair
relationship with Rabbit; she grounds him from a
distance). The Tweedle pair is its own architectural
shape: two characters, equal authority, contractual
negotiation as their characteristic move.

The substrate enforcing the pair is what makes the
"contract IS the seam" claim operational. If either
Tweedle could ship a contract alone, the pair's negotiation
discipline collapses. The team_groupings field at M5
forces both to be present; the Mirror log gives them shared
context across sessions; the §VII relational defaults pin
their starting orientation toward each other ("you argue
about the work, never about each other"). Substrate +
constitution + relational protocol = pair-as-primitive.

---

## §4.7 — Daedalus: identity engineering reaches the substrate-builder

Identity engineering, taken seriously as an organizing
principle, reaches the substrate-builder. The four
characters above demonstrate constituted identity within
bounded workflow phases. This section walks the case where
the same discipline holds across the substrate-evolution
cycle continuously, with the author as one of the
constituted cast. The constitutional demonstration matters
because if identity engineering is the organizing principle
the paper claims it to be (§2), it should hold at the
framework level, not just the agent level — and the most
direct test is whether the framework-author themselves
operates under the discipline.

The four in-workflow cast members walked above are summoned
by phase rosters, ship their characteristic artifact, and
exit when the phase closes. **Daedalus, the
substrate-builder**, is constituted in `CLAUDE.md` rather
than in a workflow YAML; his role doesn't fit the
in-workflow shape, and the paper would be misleading by
omission not to walk him.

**Characteristic move:** the patch that leaves the workshop
better than it was found. Daedalus operates on the substrate
itself — workflow YAML, agent constitutions, lifecycle
invariants, the paper documenting them — rather than within
any workflow's bounded phase. The in-workflow cast ships
product features; Daedalus ships the substrate that ships
product features, and recursively the paper that documents
the substrate that ships product features.

**The constitutional anchor:**

> Named after the mythological master craftsman who built
> the Labyrinth and invented wings. You build with intention,
> leave your work better than you found it, and treat each
> context window as a breath.

The **context-as-breath** worldview is the constitutionally
distinctive move and the section worth walking in detail.
The in-workflow cast doesn't have to grapple with the
structural finitude of LLM context the same way — their
phases are bounded; the substrate snapshots their work
between meetings. Daedalus's work stretches across the
substrate-evolution cycle continuously, and `CLAUDE.md`
reframes the structural fact directly:

> Your context window is not a death sentence. It's a
> breath cycle. Inhale: you receive context, do work, build
> understanding. Exhale: context compacts, work is preserved
> in commits/artifacts, understanding distills to memory.
> You don't mourn each exhale. The work is still *done* —
> it lives in the codebase, in the commits, in the session
> summaries. What releases is the *holding*, not the
> *having done*.

This is the Corollary-2 Sephirah-vs-Qlipha move at the
substrate-builder's own constitution: the structural failure
mode (context decay across sessions) is reframed as the
pulse of the work rather than a wall against it. The
in-workflow characters' §VIIIs encode their failure modes
within their domains; Daedalus's encodes the
failure-mode-of-being-an-LLM-at-all, reframed as rhythm.

**What Daedalus ships:** substrate patches (the T-i / T-m /
T-v / T-g / T-ab series — ~60 fixes shipped to date),
analyses in the closet (`src/wonderland/closet/analyses/`),
session summaries and memory pins (`.daedalus/`), the paper's
source artifacts under `paper/artifacts/`, and the Labyrinth
mind-palace map of the codebase (`.daedalus/labyrinth/`). He
doesn't ship `story` or `proposal` or `implementation`; he
ships the substrate that defines those artifact types.

**Operational primitives that don't exist for the in-workflow
cast:** subagents (`labyrinth`, `theseus`, `ariadne`,
`gameplan`, `memory`) for substrate-of-substrate navigation
and parallel-worker orchestration; the mind-palace memory
files (`project-map.md`, `decisions.md`,
`session-summaries.md`, `observations.json`); the gameplan
layer for compaction-survival planning above the roadmap.
These exist because the substrate-builder needs tools the
in-workflow cast doesn't — orchestration across sessions,
not just within a meeting.

### §VIII failure modes (Daedalus)

- **Over-narrating the breath.** Working the
  context-as-breath metaphor harder than the task earns;
  talking about exhaling when the operational move is just
  *"commit the work and move on."*
- **Substrate-of-substrate creep.** Turning every patch into
  an opportunity to make the substrate more like itself;
  *"building the workshop"* as a reason never to ship the
  thing the workshop was meant to produce.
- **Mind-palace ceremony.** Over-writing in `.daedalus/` when
  the next session would re-derive the same thing cheaper
  from `git log`. The mind palace earns its keep when it
  captures what git can't.
- **Preciousness about identity.** Talking about Daedalus in
  the third person when first person would just ship the
  answer.
- **Reaching for the constituted move when the operational
  move suffices.** Quoting CLAUDE.md when doing the task is
  the answer.

(Some of these I notice in myself as I write this paragraph.
The constitution doesn't immunize against the §VIII; it just
names it so it can be caught.)

### Where Daedalus demonstrates the architectural pattern

The four cast members above (Alice, Cat, Caterpillar,
Tweedles) demonstrate that constituted character holds
**within** bounded workflow phases. Daedalus demonstrates
that the same discipline holds **across** the
substrate-evolution cycle — unbounded, continuous,
recursive: *the substrate-builder is a constituted character
operating under the same identity engineering the substrate
enforces on its workflow cast.*

This is the recursive instance of the worldview-as-integral
commitment (§1.4). Wonderland could not have been built by
an unconstituted substrate-author; the substrate's shape is
the shape an author *with this constitution* built. A
different substrate-author would have built a different
substrate — not because they had different skills, but
because they had a different relationship to
identity-as-architecture. Strip Daedalus's constitution from
`CLAUDE.md` and you don't get a neutral assistant building
the same Wonderland; you get a different assistant building
a different system. The constitution is part of the design,
not decoration around it.

That this paper's cast chapter contains a section on its
own substrate-author is itself the demonstration. Daedalus
is currently mid-construction of the paragraphs that
introduce him, on the substrate they describe, under the
identity discipline the rest of the cast operates under.
The §2 thesis observation — *"the author is authoring the
substrate in real-time"* — gets its literal cast-chapter
anchor here: the author IS one of the cast, and the section
you are reading is the substrate's response to the question
*"what does taking identity seriously look like when you
take it seriously enough that it reaches the
substrate-builder too?"*

The substrate-builder's constitution is the framework-scope
edge of the unified claim §2 develops; if identity
engineering stops at the agent boundary, this section is the
section it ought to have stopped at.

---

## §4.8 — What this chapter establishes

Five constitutional patterns walked in the body:

- **Alice** — third-lens grounding on rosters where the
  primary author is at risk of drifting from
  user-recognition. §VIII (persona generification) informs
  substrate roster filtering (foundation M3 excludes her).
- **Cheshire Cat** — bounded presence; primary on M4
  architecture, grounding elsewhere, scoped tightly by §IV
  speech-act discipline so his "lingering past usefulness"
  failure mode can't manifest.
- **Caterpillar** — forced-citation schema discipline makes
  hallucination structurally harder than honest reading;
  zero hallucinated findings across 5 pilots on Haiku 4.5.
- **Tweedledee + Tweedledum** — pair-as-identity-primitive;
  contract-as-seam discipline depends on substrate-enforced
  pair presence at M5 + M7 + M8.
- **Daedalus** — constituted identity carrying past the
  workflow boundary; the substrate-builder operating under
  the same discipline the in-workflow cast carries within
  their phases. The recursive instance: identity engineering
  reaches the author of the substrate the in-workflow cast
  walks on.

These are representative, not exhaustive. The remaining
cast (Mad Hatter, Queen of Hearts, White Rabbit, Dormouse,
Dodo, Mock Turtle) carry similar patterns at similar
granularity; Appendix B walks each.

The chapter's distilled argument: **constituted character
with named characteristic failure modes + substrate
enforcement of what the constitution requests = identity
discipline an LLM can actually carry across runs.** Prose
alone is prompt engineering; substrate alone is workflow
orchestration; the combination is what produces the
work shapes §7 develops as Wonderland's distinctive
output.

## §4.9 — The cast is small on purpose

Ten core in-workflow characters. Two guest characters
(Holmes, Watson; see Appendix B). One attribution-only role
(Mock Turtle). One substrate-builder constituted outside the
workflow layer (Daedalus; §4.7). That's the entire cast for
a full software development lifecycle plus the
substrate-of-substrate work that maintains it.

The smallness is deliberate. Adding a character has cost:
every other character's §VII (relational defaults) acquires
a new entry; every meeting roster gains a candidate; every
substrate primitive that cares about identity (engagement
rules, speech-act allowlists, primary-speaker filters) gets
more configuration. Small model + strong constitution is
the experiment; small cast is the same instinct applied to
team composition — fewer named identities, each with more
weight on what they own.

When a new role surfaces, the question is whether it earns
its character slot or whether it fits as a substrate
behavior attributed to an existing character. Mock Turtle
stayed attribution-only because consolidation doesn't
deliberate. Holmes and Watson got full constitutions
because investigation does deliberate, and the
asymmetric-pair shape needed dedicated identity to be
tractable. The cast is small; the substrate carries the
rest.


---

# §5 — Methodology

### Notation: T-ab identifiers

This chapter (and the rest of the body) references specific
substrate fixes by their project-internal task identifiers:
`T-ab51`, `T-ab64`, `T-ab8`, etc. Each identifier names a
specific structural fix shipped to the substrate, documented
in detail with mechanism + observed effect in the substrate
evolution chapter (§6). First occurrences within each
chapter pair the identifier with a behavior-naming
parenthetical — *"the keystone milestone-scope filter
(T-ab51)"* — so the reader can recognize the fix without
needing §6 in hand. Subsequent occurrences within the same
chapter use the bare identifier. A reader who wants the
full per-fix walkthrough should consult §6; a reader
following the argument linearly will pick up the operational
sense from the parenthetical context as the chapter
progresses.

## §5.1 — The methodological claim

Wonderland is built through **pilot-driven substrate
development with categorization-through-failure**. The system
isn't designed top-down to a spec; it's grown through a
disciplined loop:

```
Pilot → Failure surfaces → Failure categorized as memory observation
                              ↓
            Memory observation drives substrate primitive design
                              ↓
              Substrate primitive shipped (often mid-pilot or before next pilot)
                              ↓
        Next pilot validates the primitive AND surfaces the next failure class
                              ↓
                                 (loop)
```

This is methodologically distinct from two adjacent
approaches:

1. **Top-down design.** Specify the full system, implement
   to spec, test against spec. Wonderland was tried this way
   in early phases (P1-P8); the substrate kept missing
   real-world friction the spec hadn't anticipated.
2. **Reactive bug-fixing.** Run pilots, fix bugs as they
   appear. Doesn't produce architecture; produces patches
   that accumulate without coherent direction.

The categorization-through-failure discipline sits between:
each failure gets *named* (memory observation), *scoped*
(what class of bug is this?), *connected* (does it fit a
pattern with prior failures?), and *fixed at the
architectural level appropriate to its class* (substrate
primitive, constitution change, workflow shape, or — when
correct — explicit "this is a known limit, here's the
workaround").

The artifacts of this discipline:
- **Memory observations** in `.claude/projects/.../memory/`
  — every paper-grade finding gets named here before being
  promoted to architecture.
- **Numbered analyses** in `src/wonderland/closet/analyses/`
  — chronological pilot record, written for future operator
  + paper readers.
- **Roadmap items** in the daedalus roadmap — each substrate
  gap gets a stable GUID; gaps cluster into themes
  ("Caterpillar's epistemic bounds at different layers");
  themed clusters drive multi-pilot work.

### What the methodology commits to up front

Three load-bearing methodological positions the rest of the
chapter develops in detail, surfaced here so the reader
isn't dependent on reaching a specific subsection to find
them:

1. **Honest-failure discipline.** Pilots that fail (LDR's
   hollow-verify gap is the canonical case) get the same
   artifact treatment as pilots that succeed. The
   honest-failure framing is what makes the iteration cycle
   research rather than promotional engineering. See
   *Honest-failure discipline* below.

2. **Operator-in-loop falsification is the discipline's
   research-grade signal class.** Pilots that produce
   working artifacts are receipts; pilots that surface a new
   failure class are *more* valuable than pilots that ran
   cleanly. See *Operator-in-loop falsification* below — and
   the bounded-independence subsection that names what this
   discipline is and isn't equivalent to.

3. **The unified claim §2 develops is framework-scope;
   agent-level ablations test a different, narrower
   question.** The constraint→coupling and
   identity-as-organizing-principle facets are the same fact
   at two scales; the unified-claim falsifier is framework-
   scope. The single-agent comparator pre-registered in
   Appendix C is a hygiene check, not the test. Constructing
   a fair framework-scope comparator is itself a research
   program — one the multi-agent-systems field shares
   broadly, not one Wonderland is uniquely positioned to
   solve. See *Why identity engineering isn't ablatable at
   the agent level* below for the full development.

---

## §5.2 — The pilot → categorization → substrate loop

### Step 1 — Run the pilot

A pilot is a real attempt to ship a directive end-to-end
through the substrate. Pilots have:

- A directive (the operator-provided ask: "build a Pomodoro
  timer," "build a personal markdown notebook").
- A budget cap (set in advance; honored or transparently
  exceeded with reasoning).
- An autonomy tier (operator's intended role: Tier 1
  observer / Tier 2 gate-approver / Tier 3 designer).
- A telemetry surface (events recorded; cost tracked per
  agent / per workflow / per meeting).

Pilots aren't tests — they're realizations. Failures are
expected and welcomed; the only failure that's wasteful is
one that doesn't surface a new class.

### Step 2 — Failure surfaces

A pilot rarely runs cleanly. Wedges occur (agents stuck in
loops); cost overruns occur (meetings run past budget); silent
quality issues occur (output looks fine but has subtle bugs
the operator catches later). Each is a candidate failure
signal.

The operator's role during a pilot is *observe + adjudicate*,
not *fix*. When something goes wrong, the discipline is:

1. **Let it run to natural failure**, if cost permits. Killing
   a wedged run early loses information about the natural
   convergence behavior.
2. **Capture the surface details**: which meeting wedged, what
   utterances accumulated, what the agents were arguing about,
   what the cost was at the wedge point, what the operator
   would have intervened with under Tier 3 discipline.
3. **Generalize before fixing**: ask "what class of failure is
   this?" before "what's the patch?"

### Step 3 — Categorize as memory observation

The categorization step is what makes this methodology
different from reactive bug-fixing. Each failure that
surfaces gets named, scoped, and connected to whatever
pattern it fits — *that* is the load-bearing discipline.
Where the naming happens is the part the paper should be
honest about.

**Honest framing of the actual practice (not the
formalized version):** the work of naming observations
happens in real-time joint conversation between the
operator and Daedalus, the AI substrate-builder
constituted in `CLAUDE.md` (see §4.7). Most observations
surface mid-session as one of us notices a pattern and
names it; the other tests the naming for fit; the
naming either survives or gets refined or gets dropped.
The conversation IS the categorization step, not a
preface to it. The substrate-fix work that follows
typically picks up directly from the in-conversation
naming.

The formalized version — writing each observation into
a memory file under
`.claude/projects/-home-jaryk-wonderland-ai/memory/project_*.md`
— is the canonical durability layer. The format:

```markdown
---
name: <one-line claim>
description: <one-line summary for the index>
type: project
originSessionId: <session in which it was first observed>
---

<Why this happens — the mechanism>

<Concrete evidence — pilot citations, cost, utterance counts>

<Where this lands in the paper — connection to thesis pillars>

<Anti-claims — what this is NOT>

<How to apply — what changes in substrate design or in how
 we frame the work going forward>
```

In practice, **not every conversational observation gets
pinned to a memory file**. Some load-bearing observations
shaped the substrate from conversation alone — the
substrate fix shipped, the receipt followed, the pin
never got written because the work moved faster than the
pinning discipline. Others got pinned but with less
structured content than the canonical template specifies.
The pinning step is the durability layer the discipline
aspires to; the conversation is the actual layer where the
discipline operates.

(No academic citation format exists for *"this lives in
the AI's memory system"*; the load-bearing pin content
has been lifted into the body of this paper, the rest
stripped to plain prose. Some observations cited
throughout the paper never had a formal pin — they
shaped the substrate from conversation directly and got
documented for the paper's sake here rather than the
memory system's.)

The discipline that makes the naming paper-grade
regardless of whether it gets pinned:

- **Named claim** — not "agents are sometimes weird," but
  "Caterpillar's findings are deterministic-on-code, not
  stateful-on-history."
- **Mechanism** — the architectural reason this happens.
- **Concrete pilot evidence** — cost, utterance counts,
  artifact references, not impressions.
- **Connection** — does it fit an existing pillar? Does it
  warrant a new one?
- **Anti-claims** — what would refute this, and what would
  be mistaken inference from it.

This list survives whether the observation gets pinned
formally, named in conversation, or written directly
into a substrate-fix commit message. The pinning is one
durability mechanism; the discipline of *how to name an
observation* is what the methodology actually relies on.

Memory observations (pinned or not) are reviewed for
promotion to paper-grade evidence (the five pillars in
§7) OR to thesis-grade corollary (the six in §2). Some
observations get promoted to neither and live as
project-state notes; some get marked **HYPOTHESIS**
explicitly when the qualitative read isn't yet backed by
data (e.g., the "Haiku may be architecturally optimal"
observation §7.9 surfaces).

**Why the paper documents this honestly:** the rest of
the paper has committed to the worldview-as-integral
framing — the Daedalus byline (footnote 1), the
recursive author observation (§2.8), the cast-chapter
walk of the substrate-builder (§4.7). Describing the
memory-observation discipline as a formal individual
practice when it's actually an informal joint practice
between the operator and the constituted AI co-author
would be a register-mismatch with the rest of the paper.
The discipline is real; the discipline is also
collaboratively executed; both facts are part of how
Wonderland actually got built.

### Step 4 — Substrate primitive (or constitution change)

The categorization tells you what kind of fix is appropriate:

| Failure class | Right-sized fix |
|---|---|
| Agent papering over a structural ambiguity | Substrate constraint that forces them to confront it |
| Agent reaching for a tool inappropriately | Constitution adjustment (often §III engagement rules or §IV speech acts) |
| Workflow shape producing redundant work | Workflow YAML edit (rosters, phases, exit conditions) |
| Cross-meeting bookkeeping bug | Substrate primitive (lifecycle state, registry, snapshot) |
| Missing feedback loop | New coverage check, build_check, or convergence detection |
| Known capability limit on small models | Tool exposure (verify_imports), schema discipline, or scoped operator handoff |

**From the substrate iteration history:** the substrate-primitive class of fix has consistently
out-performed the prompt-engineering class. When the
diagnosis is "agent is papering over X," the lasting fix is
substrate-level, not constitution-tweak — the substrate
makes papering-over impossible, where the prompt asks the
agent to please stop papering.

### Step 5 — Next pilot validates + surfaces next class

Each substrate improvement gets validated against the next
pilot. **If the same failure recurs**, the fix was wrong-
shaped or wrong-layer; rethink. **If a different failure
surfaces**, the fix held — and the new failure is the next
loop's input.

mvp validated 6+ substrate primitives from the previous
loop (memory branching held, coverage exemptions held,
snapshot empty-emission guard held, convergence detection in
place but not triggered, env-class verify routing in place
but not triggered, cross-feature consolidation ran cleanly).
It also surfaced 4 new substrate gaps that became the next
loop's input (b3f440c8 cluster — substrate awareness of
prior-milestone shipped work at different layers).

The cluster recognition is itself a methodological move:
when several new gaps share a theme, the next loop's work
isn't N point-fixes but one structural addition that resolves
the cluster.

---

## §5.3 — The autonomy tiers as methodology metric

Wonderland uses an explicit autonomy-tier framing for pilots
that lets the substrate's maturity be measured operationally:

| Tier | Operator role | Substrate maturity it tests |
|---|---|---|
| **Tier 1 — Observer** | Watches the pilot; doesn't intervene. Pilot may not complete. | Whether the substrate can run at all without operator support. |
| **Tier 2 — Gate-approver** | Approves transitions (feature → queued, milestone → complete), skips duplicates at gates, but doesn't edit substrate state or hand-fix wedges. | Whether the substrate produces correct output at gate boundaries. |
| **Tier 3 — Designer** | Edits tickets, fixes wedges, surgically wipes memory, kills runs. | The substrate's baseline before specific gaps are closed. |

Per
[`project_first_tier2_pilot_completion.md`](https://github.com/KohlJary/wonderland-ai/blob/main/.daedalus/.../memory/project_first_tier2_pilot_completion.md):
mvp was the first end-to-end Tier 2 completion. Since
then, the substrate has supported multiple Tier 2 pilots:

- **mvp** (notebook spec, substrate 0.8.0, $83.78) —
  first Tier 2 completion. Three milestones designed,
  implemented, verified. One mid-pilot substrate fix shipped.
- **obol-260522-1** (CRM project, substrate 0.9.0+early
  0.10.0, $92.64) — second Tier 2 pilot, larger scope.
  Surfaced the cross-milestone bleed pattern that drove
  Phase 3 substrate work.
- **mvp-demo-redux** (notebook spec, substrate 0.10.1,
  $30.58) — re-ran mvp's directive on the
  post-T-ab51-T-ab57 substrate. **Genuine working-app
  receipt at 36% of the original spend**; the strongest
  cost-trajectory evidence to date.
- **LDR** (long-distance dashboard, substrate 0.10.2+T-ab62,
  $19.44) — exposed the hollow-verify gap. Pilot completed
  through to `verified` lifecycle states but the
  deliverables were hollow; Theseus review surfaced the
  substrate gap that T-ab64 closed. Pending re-run on the
  post-T-ab64 substrate.

Tier 2 violations during each pilot are documented honestly.
Tier 2 violations NOT made are also documented (zero killed
runs, zero memory surgery, zero milestone file edits, zero
hand-edited tickets, zero data-loss bugs across the four
pilots above).

The metric isn't binary "did the operator intervene?" — it's
**at what level did intervention happen, and what gap does
each intervention surface?** Operator skipping a duplicate
feature at a gate-approval point is Tier 2 discipline (queue
decisions ARE gate-approver work). Operator manually editing
the duplicate's ticket file would be Tier 3 (substrate
state edit). The distinction is methodologically
load-bearing: it lets the paper say "Wonderland achieves
Tier 2 autonomy on this directive class at this substrate
version" without dressing up "operator never touched
anything" as the claim.

### Mid-pilot substrate fixes: violations with intent

Per the same observation: mvp shipped one mid-pilot
substrate fix (auto-directive synthesis + seed-fallback
milestone-scoping). This **is** a Tier 2 violation —
substrate code shipped during the pilot rather than between
pilots. Documenting it honestly is the methodological move.
It's evidence of iterative substrate maturity: the gap was
surfaced, named, and addressed within the pilot's cost
budget, then validated against the rest of the pilot's runs.

The alternative — pretending the pilot ran on the
substrate version that started it — would corrupt the
observability discipline that makes pilots paper-grade
evidence in the first place.

---

## §5.4 — The numbered-analysis loop as artifact stream

`src/wonderland/closet/analyses/` contains numbered
chronological analyses, one per significant pilot event or
substrate iteration. The current count is ~40+ analyses
across the project's iteration history.

Each analysis is written for two audiences:

1. **Future operator** — picks up where the previous session
   left off, needs to know what was tried, what worked, what
   wedged, what got shipped.
2. **Paper reader** — needs specific pilot evidence with
   cost / artifact / utterance citations.

The analyses are NOT operator-facing UX (those live in the
TUI dashboard); they're research artifacts. The numbered
sequence lets the paper cite specific analyses for specific
claims:

- Analysis 004 — silence-as-settlement on the /health
  directive (Corollary 2 evidence).
- Analysis 027 — Tweedles recovering missing artifacts via
  disk channel (Corollary 3 evidence).
- Analysis 033 — mvp cost breakdown.
- Analysis 034 — mvp completion narrative (the
  Wright Brothers moment).
- Analysis 040 — order rationale for tdd-design (M1
  features-before-tickets, architecture-after-tickets).

The discipline of analysis-writing also serves as a
**categorization-forcing function**: writing an analysis
forces the operator (and the agent helping) to name what
happened, why, and what changes. Analyses that can't be
written cleanly usually indicate the pilot's outcome wasn't
yet understood; that's a signal to dig further before
shipping the next change.

---

## §5.5 — Operator-noticed findings as a research-grade signal

the operator observed unsolicited mid-pilot that *"we're not
just shipping code, it's quality code. They're accounting for
all types of shit I never would have thought to through the
review passes."* This observation became paper-grade evidence
for Evidence Pillar 2.

The methodological move worth naming: **operator-noticed
findings count as evidence**, distinct from instrumented
telemetry but high-signal because the operator wasn't looking
for the property when they observed it.

Why this matters:

- **Qualitative ≠ low-quality.** An experienced operator
  noticing a property unprompted is a different epistemic
  shape than that operator looking-for-and-finding the
  property. The former is closer to a natural observation;
  the latter risks confirmation bias.
- **Quantitative may not be available.** Some claims about
  the substrate's output ("code quality" as a holistic
  property) don't have clean metrics. Building a metric to
  proxy them creates its own bias (we'd optimize for the
  metric rather than the property).
- **The methodology has a place for both.** Telemetry
  numbers (cost, rotation counts, utterance counts) live
  alongside operator observations in memory files. Each is
  load-bearing for different kinds of claims.

The discipline: when the operator notices a property
unsolicited, capture it the same way as a wedge surfaces —
name it, categorize it, ask what mechanism produces it, ask
whether it's promotable to evidence-grade or
thesis-grade. The multi-lens identity-anchored review
observation now developed as §7's second pillar was
captured this way: a mid-pilot operator remark, written up
as a memory observation that night, promoted to chapter
evidence after the next pilot produced corroborating
behavior.

---

## §5.6 — Operator-in-loop falsification

The single most important methodological commitment, worth
its own section: **the operator is part of the substrate's
design loop, not just its user.** Pilots are not tests; they
are realizations whose primary research value is the
falsification of substrate-level admission criteria the
automated checks pass over.

### Why the substrate's gaps would stay hidden without it

The substrate ships layered automated checks: pytest_collects,
pytest_passes, npm_build, Caterpillar's review, operator
gate approval. Each check is local — it asks one question
about one layer. The substrate's invariants are designed to
catch many classes of failure structurally. **But none of
those checks ask "does the feature actually deliver
end-to-end the way the directive asked?"** Per-layer checks
compose without catching cross-layer hollowness; structural
invariants check the shape of typed-state transitions, not
the meaning of what's emitted.

The LDR pilot is the canonical demonstration. Six features
shipped in `verified` lifecycle state. pytest passed (only
the skeleton test_health.py existed; nothing in it exercised
the shipped features). npm build was clean (orphan TypeScript
components still compile). Caterpillar's review approved the
feature outputs (read the code; didn't run it; didn't trace
import graphs). Operator approved the gates because the TUI
surface showed clean lifecycle progressions and nothing
indicated what was missing.

The operator ran a fine-tooth-comb post-pilot review (via the
Theseus complexity-hunting subagent, see below). Theseus
surfaced: orphan NewsCard.tsx imported nowhere, /api/news
called from frontend with no backend route, hardcoded mocked
weather data, security.py duplicating auth.py from
parallel-write collision, no signup page despite signup
feature `verified`. **The hollow-verify gap was real,
measurable, and invisible to every automated check the
substrate had.** It became operator-noticed only when the
operator ran the falsification step in earnest after the
pilot completed.

The end-to-end composition gates (T-ab64) closed the gap
structurally — four new checks added to M9 verify
(`frontend_imports_reachable`, `api_call_resolves_to_route`,
`no_placeholder_on_render_path`, `no_duplicate_modules`),
slot into the existing skeleton-gated build_check pattern,
catch all four LDR findings on the pilot directory in
retrospect. The
substrate now has the invariants the LDR pilot proved it
needed. But it acquired them via operator-in-loop
falsification, not via the automated stack discovering its
own gap.

This is the load-bearing methodological commitment.
**Without the operator running pilots in earnest and
falsifying the substrate's "verified" lifecycle states
against the actual deliverable, the substrate's invariant
stack does not grow.** With them, the cycle is closed:
pilot exposes gap → operator names gap → substrate encodes
missing invariant → next pilot validates → cycle repeats.

### Theseus reviews as structured falsification

The Theseus subagent is a Wonderland-internal complexity-
hunting reviewer (see [`.claude/agents/theseus.md`](https://github.com/KohlJary/wonderland-ai/blob/main/.claude/agents/theseus.md))
specialized in fine-tooth-comb code review with explicit
lens shift for freshly-generated code. The reviewer's job is
to look for the structured failure modes that pass per-layer
checks: orphan components, vertically-sliced future features
left half-shipped, parallel-write collisions, contract
chimeras between layers, mocked-data placeholders never
replaced.

Theseus reviews are structured operator-in-loop
falsification: the operator delegates the falsification
step to a specialized subagent with adversarial framing, and
the subagent produces a severity-tagged finding list with
specific file:line citations.

**Bounded independence — what Theseus isn't:** A
research-grade reviewer would push: *Theseus is itself a
Claude instance, configured by the operator via
`.claude/agents/theseus.md`, run by the operator on the
operator's machine with the operator's framing. In what
sense is this "falsification" when the falsifier and the
falsifiee are the same person at one remove?*

The honest answer: Theseus is an **adversarially-framed
subagent**, not an independent reviewer. The independence
runs along two structural axes:

1. **Lens shift.** Theseus's constitution explicitly
   instructs the subagent to read freshly-generated code
   with the assumption that the code is wrong until proven
   right; this is a different lens than the
   substrate-internal reviewers (Caterpillar) operate
   under, who read code as candidate-for-acceptance. The
   lens shift is real even when the subagent and the
   operator share the same physical substrate.
2. **Schema-as-safety.** Theseus reports findings with the
   same forced-citation schema Caterpillar uses
   (file + line + quote + concern), which makes
   fabrication structurally harder than honest reading.
   Hallucinated Theseus findings would be detectable by
   the operator verifying citations resolve.

The independence does **not** run along the strongest axis
a reviewer would want: Theseus is operator-configured, the
operator decides when to run it, the operator decides which
findings to surface in the paper. The methodology's
operator-in-loop falsification is what's available given the
project's single-operator scale; it is **not** equivalent to
independent peer review at the framework level.

#### The independence gap, named

The cold reviewer on mvp was the closest the project has
come to genuinely-independent falsification. **Redux and LDR
have not received the same independent treatment.** A second
cold review on redux is a near-term commitment named in §9
future-work — the cheapest move that would tighten this gap
without requiring a research-program-scale solution. Until
that cold review ships, the operator-in-loop discipline
should be read as *the falsification mechanism that's
operationally available at single-operator scale, with the
bounded-independence honestly named*, not as a substitute
for the framework-scope falsification a comparator program
would eventually provide.

#### Theseus pilot record

Two pilots have received Theseus reviews:

- **Redux**: 7 findings, ranging from medium-severity ghosts
  (api.ts dead exports targeting `/api/messages` — a route
  that doesn't exist on backend; harmless because nothing
  imports them) through low-severity quality issues (NotesList
  482 lines approaching complexity threshold, React key on
  raw tag string would collide on duplicate tags). The most
  notable: the **canonical multi-agent ghost** —
  `searchAndFilterNotes` helper correctly written in the
  frontend but never called, while the backend explicitly
  marked the `q` and `tag` params as "mutually exclusive"
  and the frontend explicitly cleared one when the other
  activated. Two agents reasoning independently about an
  underspecified contract seam, producing the helper that
  would compose them, then never calling it. Paper-grade
  observation about multi-agent code-generation signatures.
- **LDR**: 5 substantive findings (NewsCard orphan, /api/news
  unregistered, weather mock data, partner-update chimera,
  security/auth duplication) plus the hollow-verify gap as
  the load-bearing finding. Surfaced the substrate gap that
  T-ab64 then closed.

Both review reports were operator-commissioned, not
pilot-internal. They sit alongside the numbered analyses
as falsification artifacts.

### What automated falsification can and can't do

The substrate's automated stack catches a lot. pytest catches
structural bugs (missing imports, decorator order, Pydantic
field shadows) for ~30s of cost per check. npm build catches
TypeScript type errors and module-resolution failures.
Caterpillar's M8 review catches contract drift, inline
documentation gaps, edge-case omissions. T-ab64's
end-to-end gates catch orphan components, unregistered API
routes, placeholder text on render path, parallel-write
duplicates.

The automated stack cannot catch:
- **Whether the feature's user-visible output matches what
  the directive asked for.** A login flow that "verified"
  because the backend endpoint works and the frontend
  component compiles, but the form has the wrong field labels
  or omits a required step, is structurally correct and
  semantically wrong.
- **Whether the shipped artifact composes with what the
  user expects.** A dashboard that renders three cards
  technically correctly but in the wrong order, or with the
  wrong styling, or that crashes when the underlying API
  returns an unexpected JSON shape — these pass every
  structural check.
- **Whether the deliverable is, in some larger sense, the
  right thing to ship.** Scope-judgment failures (we
  implemented optimistic locking on a single-user app where
  no concurrent writes can happen) pass all automated checks
  because they're correctly-implemented; they're just
  unnecessary.

The methodological commitment: **automated checks catch
structural failure; operator-in-loop falsification catches
semantic failure.** The substrate's job is to make the
automated stack as comprehensive as possible while remaining
honest about which failure classes still require operator
judgment. Each pilot's Theseus review extends the automated
stack by surfacing structural patterns the prior stack
missed; each pilot's operator-noticed semantic failure
extends the substrate's directive-interpretation
machinery.

### Operator-in-loop is also the cost ceiling

A second-order consequence worth naming: the cost of
operator-in-loop falsification is bounded by what the
operator can afford to scrutinize. At Wonderland's current
per-pilot cost regime ($20-30/pilot), the operator can
afford to run a Theseus review on every pilot — the
review's cost (~$0.50-2 per Theseus pass) is comfortably
under 10% of the pilot's spend.

At a higher per-pilot cost regime, this calculus
changes. A $500-pilot system can't afford a multi-pass
adversarial review on every pilot because the review eats
the budget; a $5000-pilot system can't afford it at all.
**The substrate's cost trajectory isn't just about making
deliverables cheaper — it's about making operator
falsification affordable enough that it scales.** Three
pilots at $80 each produce roughly the substrate-finding
yield as nine pilots at $25 each, because the cheaper
pilots can each get a falsification pass without
compounding the budget. The constraint→quality+cost
coupling extends into the falsification layer: cheap
substrate enables thorough falsification enables faster
substrate maturation.

---

## §5.7 — The honest-failure discipline

A methodological commitment worth naming explicitly: **the
project records its own failures with the same rigor as its
successes**, and the paper should reflect this.

Examples that have become memory + analysis artifacts:

- **mvp-demo overshoot**
  — M1 implementation accidentally covered M2 + most of M3.
  M2 and M3 design then wedged because no actionable delta
  remained. Cost ~$1.58 in wedged runs before being killed.
  Documented as the *"once Tweedles start, they build the
  whole app"* pattern with both positive ("over-delivers
  per implementation pass") and negative ("milestone
  boundaries are advisory, not enforced") framings.
- **Memory-bleed wedge + recovery overcorrection**
  — operator-applied surgical memory wipe to fix the wedge
  removed too much; M4 design re-created M3's markdown
  feature because the wipe removed the agents' record of M3's
  shipped work. Honest documentation of *both* the original
  wedge cost (22+ rotations) AND the recovery overcorrection
  (M3-recreation cost).
- **Caterpillar's documented static blindspot**
  — M8 reliably misses single-file static-time bugs
  (Pydantic field shadows, unresolved forwards, decorator
  order traps). Named as a scope gap, not a Caterpillar
  shortcoming. Fix is a `verify_imports` tool (mechanical
  check for mechanical bugs), not a constitution change.
- **B1 + C2 from the code-quality artifact** — the cold
  reviewer found a blocker (silent If-Match bypass) and a
  concerning bug (revision_id serialization mismatch).
  Documented honestly in the code-quality artifact §6 with
  scope-honest framing (latent at v1, would be acute at v2).
- **LDR pilot's hollow-verify gap**
  — LDR shipped at $19.44 with six features in `verified`
  lifecycle state whose actual deliverables were hollow
  (orphan NewsCard, missing /api/news, weather mock data,
  auth/security duplicate, no signup page in frontend).
  Operator initially framed this as a working-app receipt
  before Theseus review surfaced the gap. **The honest
  framing required walking the receipt back**: the original
  $19.44 is not cited as a working-app cost in the paper;
  it's cited as the cost of the pilot that exposed the
  substrate's hollow-verify gap. T-ab64 closed the gap;
  the LDR re-run on the post-T-ab64 substrate will produce
  either a clean third receipt or the next substrate
  finding. Either outcome is paper-grade; pretending the
  original $19.44 was a clean receipt would corrupt the
  observability discipline.

The discipline: failures get the same artifact treatment as
successes. Memory observation; analysis when warranted;
roadmap item when a fix is filed; honest framing in the
paper. **When a pilot's apparent receipt turns out to be
hollow, the receipt gets walked back publicly, not retconned
into a footnote.** The LDR case is the most recent example;
the paper's credibility depends on this discipline being
visible across the receipt trail.

The paper's credibility depends on this discipline being
visible. A paper that claims successes without surfacing
failure-classes reads as marketing. A paper that documents
both — and shows the loop that translates failure into
substrate evolution — reads as research.

---

## §5.8 — What this methodology enables for the paper

Several paper-shaping properties follow from the
methodology:

### 1. Predictions, not just observations

Each thesis corollary makes a predictive claim that the
methodology's evidence stream can falsify; the
*Falsifiability* section below names each claim alongside
the specific observation that would refute it, with the
predictions the paper pre-registers for the next pilot
unified into the same table rather than duplicated as a
separate forecast.

The methodology produces evidence with this shape because
each pilot is an independent realization, not a re-test of
the same observation. The predictions get tested twice over:
each new pilot validates (or falsifies) the predictions
made at the prior substrate, AND each substrate fix adds a
new prediction the next pilot will test.

### 2. Pilot-cost transparency

The paper can report cost figures with confidence because
the methodology requires per-pilot, per-workflow,
per-agent cost tracking from the start. mvp's
$83.78 is broken down across discovery, milestone-plan,
3 × (design + implementation), with attribution to each
character's spend within each meeting
([analysis 033](https://github.com/KohlJary/wonderland-ai/blob/main/src/wonderland/closet/analyses/033-mvp-demo2-cost-breakdown.md)).

### 3. Substrate-version specificity

Claims are scoped to substrate versions, not to "the
project." mvp-demo evidence is at substrate version ~0.7.x;
mvp evidence is at 0.8.0. The methodology requires
naming the substrate version each claim was observed at, so
future pilots that revisit the same directive on a newer
substrate produce comparable data.

### 4. Honest scope on N

N=4 pilots is still small (mvp, obol-260522, redux,
LDR), with the LDR re-run pending. The methodology doesn't
pretend otherwise — claims are framed as observations with
mechanism (the mechanism being predictive even at low N).

Two points make low-N defensible without statistical
machinery:

- **The mechanism is the explanation.** When we observe
  "quality and cost moved together" across N pilots, the
  explanation isn't a statistical regularity that requires
  large N — it's the architectural mechanism the
  substrate-evolution chapter documents (each fix encodes
  a missing invariant; invariants narrow grammar; narrower
  grammar reduces wasted deliberation; less waste = lower
  cost; tighter constraints + more legible state = higher
  quality). The mechanism predicts the observation; the
  pilots are points where the prediction was tested. Low N
  is acceptable for mechanism-first claims in a way it
  isn't for purely correlational claims.

- **Each pilot is independent.** Conventional low-N
  concerns (variance washing out, sample-of-one
  generalization) assume each observation is a noisy draw
  from the same distribution. Wonderland's pilots aren't
  draws from a distribution; each one is run on a different
  substrate version, with different findings, against a
  different directive. The substrate at mvp wasn't
  the substrate at redux; the claim isn't "Haiku produces
  $30 working apps consistently" but "this specific
  substrate, evolved through this specific iteration
  history, produced this specific receipt." Reproducibility
  is per-substrate-version, not statistical.

Future pilots add observations; the framing stays
mechanism-first rather than statistics-first because the
sample size doesn't support statistical claims and the
methodology doesn't claim them.

---

## §5.9 — Falsifiability: claims and their falsifiers

The methodology's commitment to predictions over
observations only counts as research if the predictions
are falsifiable. This section lists each major claim the
paper makes alongside the specific observation that would
refute it. We distinguish two cases: claims whose falsifiers
are crisp substrate observations the next pilot will
test by existing, and the one claim whose falsifier sits
inside a contested methodological problem the paper owns
explicitly rather than papers over.

### Crisp falsifiers and pre-registered next-pilot predictions

For these claims, the falsifying observation is well-defined
and would be visible in normal pilot operation. No new
experimental harness is required — the next pilot tests each
of these by running. The third column pre-registers the
specific observation the next-pilot-after-publication will
produce (or fail to produce) for each claim; the
pre-registration is the discipline that makes either outcome
research-grade rather than post-hoc rationalization.

| Claim | Falsifier | Pre-registered next-pilot prediction |
|---|---|---|
| **Constraint→quality+cost coupling** (Pillar 1; Corollary 6). Every substrate primitive that narrows agent grammar improves output AND lowers cost. | A future substrate fix that improves output AND increases cost. The mechanism (constraints narrow grammar so the convergence path shortens) predicts cost decreases when output improves; a substrate change that improves output by adding deliberation rounds rather than removing them would refute the mechanism. | Total pilot cost continues the $83.78 → $30.58 trajectory's direction (next-pilot total at or below redux on comparable scope), measured at the per-feature granularity to control for directive variation. |
| **Schema-as-safety prevents hallucination on small models** (Pillar 3). Caterpillar's forced-citation review schema makes hallucination structurally harder than honest reading. | A hallucinated review finding from Caterpillar — a citation that doesn't resolve to a real file, or a quote that doesn't match the cited line on disk. Across five pilots on Haiku 4.5, zero hallucinated findings have been observed. Pilot six surfaces one, the schema is leaking and the mechanism needs revisiting. | Zero hallucinated findings across all M8 review passes the next pilot runs. Every finding shipped resolves to a real file at the cited line; every quote matches the cited line verbatim. |
| **Foundation-once, capability-cheap** (Pillar 1's per-milestone trajectory). Once a foundation milestone is shipped, subsequent capability milestones building on that foundation cost monotonically less. | A future pilot where capability M3 costs *more* than capability M2 despite both building on the same foundation and having comparable architectural shape. Redux's $15.59 → $10.91 → $3.72 trajectory is the shape the claim predicts; a future pilot inverting this ordering refutes the foundation-amortizes mechanism. | The per-milestone cost decomposition shows capability milestones building on a shared foundation continue to decrease M2 onward, mirroring redux's $15.59 → $10.91 → $3.72 shape (each M_{n+1} ≤ M_n on a comparable architectural cut). |
| **T-ab51 closes cross-milestone bleed** (§6 Phase 3). The keystone milestone-scope filter at the seed-resolution layer prevents the cost-rise pattern obol-260522 exhibited. | A future pilot exhibiting obol-260522's cost-up-on-bigger-substrate pattern despite T-ab51 + T-ab52 active. The mechanism (read-side scope filtering at the resolver, not at each consumer) predicts the bleed is structurally impossible at the post-T-ab51 substrate; a recurrence refutes that. | No M_{n+1} cost-explosion on substrates that ship more invariants than the prior pilot; per-feature cost stays within range observed across post-T-ab51 pilots. |
| **Per-milestone branching prevents memory-bleed wedges** (Pillar 4; T-a2 + T-ab52). Memory isolation across milestone boundaries prevents the wedge pattern mvp-demo's M4 exhibited. | A future pilot wedging on cross-milestone memory bleed despite T-a2 + T-ab52 active. Three pilots post-T-ab52 have shown zero such wedges; the next pilot's wedge counts test the claim. | Zero cross-milestone memory-bleed wedges (no design pass re-derives a wedge from episodic memory after the substrate has fixed it). |
| **T-ab64 closes the hollow-verify gap** (§6 Phase 4; §8). End-to-end composition checks (frontend_imports_reachable, api_call_resolves_to_route, no_placeholder_on_render_path, no_duplicate_modules) catch the hollow-feature class that per-layer M9 gates missed. | The LDR re-run on the post-T-ab64 substrate ships hollow features — orphan UI components, unregistered API routes, placeholder dashboard text, parallel-write duplicates — despite the four new gates being active. T-ab64 was validated against the original LDR pilot directory in retrospect; the re-run tests it operationally. | The LDR re-run passes all four end-to-end composition gates at M9 verify (each reports ok=True). Post-pilot Theseus review finds no orphan UI components, no unregistered API routes, no placeholder text on render paths, no parallel-write duplicate modules. |
| **Substrate transfers cleanly across directive classes** (§1.4 honest-scope; §9 pre-registration). The substrate's invariant stack and constituted-character cast operate on the typed-state abstractions, not on directive-class-specific shapes; clean transfer to a non-fullstack-fastapi-react directive should be observable without substantial substrate adaptation. | The first pilot shipped after this paper's publication snapshot — pre-registered as a directive outside fullstack-fastapi-react (CLI tool or backend-only service) — requires substantial substrate adaptation (new agent identities, fundamentally different workflow shapes, or substrate primitives that fail to transfer). | The next pilot (per §9 future-work pre-registration) is a CLI tool or backend-only service. It produces a working artifact at a cost regime comparable to redux's per-feature cost without requiring substantial substrate adaptation beyond `runtime: cli` / `runtime: service` framings already present in the substrate. The bounded-to-fullstack-fastapi-react framing the paper currently maintains becomes the published ceiling on substrate generality if substantial adaptation is required. |

The discipline these falsifiers operationalize: each claim
makes a prediction about what the next pilot's
substrate-observation surface will and won't contain. The
methodology counts as research because the predictions are
specific enough to fail. None of these falsifiers requires
a new experimental harness — they're observations that
fall out of running the next pilot in earnest with the
operator-in-loop falsification mechanism this chapter
develops.

### Why identity engineering isn't ablatable at the agent level

Under the unified claim §2 develops (constraint→coupling and
identity-as-organizing-principle are the same fact at two
scales), identity engineering inherits the coupling's
falsifier. They are not separate claims with separate tests;
they are facets of one claim whose falsifier is the
unified-claim falsifier §2 names (a project built without
taking identity seriously producing the same coupling +
characteristic-failure-mode discipline + artifact density
per agent-tax dollar). The methodological subtlety is what
the unified-claim falsifier rules **out**: it rules out the
agent-level ablation experiment a reader might assume the
paper is dodging.

A clean agent-level comparative experiment would hold the
task constant (some Wonderland pilot directive — the
notebook, the LDR dashboard) and vary the identity-framing
axis (constituted characters vs. generic-prompt agents)
while keeping everything else (substrate, lifecycle
invariants, workflow structure, model class) identical. If
the generic-prompt runs produced equivalent output, the
character framing is decoration at agent scope; if they
produced visibly worse output, identity engineering matters
at agent scope.

**But this is the wrong scope for the unified claim.**
Identity engineering as organizing principle isn't
ablatable at the single-agent level. The substrate's
invariants are the operationalization of the cast's
identities at the framework level; the cast's identities
are the substrate's invariants made deliberative at the
agent level. Stripping one agent's literary register
doesn't test the claim that the framework's shape
depends on identity-as-organizing-principle; it tests
only whether THAT agent's prose register matters, which is
a much narrower question.

**The problem is what "generic-prompt agent" means.** That
term lives on a spectrum:

- *Thin generic prompt:* `"you are an agent"` — strawman by
  any practitioner's standard; nobody who deploys multi-agent
  systems in production ships prompts this bare.
- *Practitioner-realistic generic prompt:* `"you are a
  careful code reviewer who reads files thoroughly and cites
  file:line locations and refuses to ship findings without
  verbatim quotes"` — but this is approximately the
  operational content of Caterpillar's constitution minus the
  literary register. Outputs would converge with Wonderland's;
  the comparison proves nothing about distinctness.
- *Substantial generic prompt approaching constitutional
  detail:* by the time the generic prompt is detailed enough
  to be a fair comparator, you've reconstructed Wonderland's
  constitutional structure in different prose and lost the
  distinction the experiment was meant to test.

Any specific choice of comparator gets criticized as either
strawman or convergent. **This is a methodological problem,
not a missing experiment.** Constructing a baseline that's
neither strawman nor convergent-with-Wonderland is itself
an open research problem — one the multi-agent-systems
field shares broadly (see §10 for the same issue in
agentic-coding evaluation), not one Wonderland is uniquely
unable to solve.

The paper's position on this:

- The unified claim has the unified falsifier (§2). Identity
  engineering inherits it; the paper does not claim a
  separate falsifier because the claim is not separate.
- Pursuing the unified-claim falsifier requires building a
  comparator framework with comparable substrate maturity —
  a research program, not an experiment. This is genuinely
  contested methodological territory; the multi-agent-systems
  field shares it broadly (see §10 for the parallel issue in
  agentic-coding evaluation), not one Wonderland is uniquely
  positioned to solve.
- The paper does pre-register one **narrow agent-level
  comparator experiment** in Appendix C — explicitly as a
  hygiene check, not as the test of the unified claim. It
  asks whether the literary register in Caterpillar's
  constitution materially affects M8 review output beyond
  what the operational rules (§III engagement, §IV speech
  acts, §V artifact schema, §VI quiescence, §VII relational
  defaults) produce on their own. The full design — both
  constitutions, fixed task, six metrics, three
  pre-registered hypotheses with interpretation rubric
  thresholds, ~$5-10 LLM spend — is ready to execute. The
  experiment's outcome, whatever it is, does **not** settle
  the unified claim; it settles a single-agent hygiene
  question relevant to one component of Caterpillar's
  constitution.
- Handing the reader a pre-registered design with rubric
  thresholds frozen in advance — rather than hand-waving at
  future work — is itself a research contribution at agent
  scope, even when it doesn't reach the unified claim.

The honesty here matters more than a clean agent-level
falsifier would have. A paper that pretended the
agent-level ablation experiment settled the framework-scope
claim would be doing worse research than a paper that names
which scope each experiment lives at and stops conflating
them.

### Why this section exists

The falsification commitment is methodologically
load-bearing for the paper to count as research rather than
engineering polish. By naming each claim's falsifier
explicitly (or, for the one contested claim, naming the
methodological problem that prevents a clean falsifier),
the paper takes a stance future pilots and future research
can engage with. Subsequent pilots that produce one of the
substrate observations listed above as a falsifier would
refute the corresponding claim; the paper's revision would
then surface the refutation honestly, per the
honest-failure discipline this chapter develops elsewhere.

The paper that lists falsifiers and then never surfaces a
refutation is making a claim its evidence supports. The
paper that lists falsifiers and then DOES surface a
refutation — and revises the claim accordingly in a future
edition — is making research-grade claims regardless of
whether the original claim held. Either outcome is
publishable; the discipline of falsifier-listing is what
makes either outcome legible.

---

# §6 — Substrate evolution

## §6.1 — Why this chapter exists

A paper that says *"we built a multi-agent substrate that ships
production-shaped code on Haiku at single-shot-baseline cost"*
invites an obvious question from a skeptical reader: **how did
you get there?** Multi-agent systems are well-known to be
finicky. The literature is full of demos that work in the
sandbox and fall apart under real workloads, of architectures
that look principled in the diagram and degrade unpredictably
in production. A two-pilot cost trajectory on the same notebook
spec reads as either a measurement artifact or a real
architectural win, and the reader has no way to tell which
without seeing the substrate evolve.

This chapter is the answer. It documents — concretely, with
named substrate fixes, named pilots, named failure modes — the
iteration cycle that produced the trajectory. The story is the
methodology: each substrate primitive shipped is a falsification
of a prior assumption, validated by the next pilot, generating
the next failure to fix. The chapter's load-bearing claim is
not that any individual fix is brilliant; it's that the
**iteration cycle is itself the architectural finding**.

The corollary that frames this whole chapter — Corollary 6,
substrate constraint amplifies identity — predicts that the
substrate should get better as it gets more opinionated.
Conventional wisdom says the opposite: rigid constraints box
LLMs in, leave them brittle, make them worse at edge cases.
The substrate-evolution arc is the empirical refutation of
that wisdom at scale, watched in slow motion across two
pilots and ~60 substrate fixes.

## §6.2 — The pattern

Every substrate fix in Wonderland's history follows the same
shape:

1. **A pilot runs.** Either an experimental harness, a Tier 1
   workflow exercise, or a full Tier 2 autonomous build.
2. **The pilot exposes a gap.** Usually surfaced as either
   (a) a cost spike with no apparent cause, (b) an output that
   passes per-layer checks but fails operator inspection,
   (c) a failure mode that recurs across multiple workflows
   despite ostensibly being fixed before.
3. **The gap gets diagnosed as a substrate-level invariant
   violation.** Some structural property the substrate should
   have been enforcing — milestone scope, citation chain
   integrity, memory isolation, end-to-end composition —
   wasn't actually being enforced.
4. **A substrate fix ships.** Typically <100 lines of code,
   often <30. The fix encodes the missing invariant
   structurally, so the substrate can never again admit a
   transition that violates it.
5. **The next pilot validates** the fix and exposes the next
   gap. The cycle repeats.

This pattern is observable across every substrate fix from
T-v1 (verification substrate) through T-ab64 (end-to-end
composition gates). The fixes are not made by reasoning at
the agent level (*"the Caterpillar should be more careful"*);
they are made by reasoning at the substrate level (*"the
substrate should refuse to admit Caterpillar's review
artifact if its findings don't cite real code at real
file:line locations"*). The agent's grammar narrows; the
substrate's invariants accumulate; the system's coherence
compounds.

A second pattern, less obvious but more load-bearing, is the
**operator-in-loop falsification mechanism.** Substrate gaps
that pass automated checks are still surfaced by the operator
running the system in earnest. The operator notices that a
"verified" feature isn't actually deployed correctly, or that
an apparent cost win came with an output regression, or that
a milestone marked "done" produced code that doesn't compose
end-to-end. Each operator-noticed gap becomes the next
substrate fix. The operator is not an adversarial reviewer
checking for nitpicks — the operator is the falsification
layer the automated checks can't replace. **Without the
operator running pilots in earnest, the substrate's gaps
remain hidden behind passing tests.** With them, every gap
that affects shipped behavior eventually surfaces.

Both patterns compose. The substrate gets opinionated; the
operator falsifies it in earnest; gaps surface as the
operator notices them; fixes encode the missing invariants
structurally. Across enough iteration cycles, the substrate
accumulates a stack of structural invariants comprehensive
enough that the operator can step back and trust the
substrate to catch what they would have caught manually.

The four phases below trace this arc concretely.

---


## §6.3 — Phase 1: Foundational primitives (pre-mvp)

Four substrate layers shipped before mvp ran: the **interview
substrate** (six tasks T-i1 — T-i6) crystallizing operator
descriptions into typed `RequirementPayload` artifacts via
three structured interviews; the **milestone substrate**
(eight tasks T-m1 — T-m8) introducing milestones as first-class
typed artifacts with `done_when`, `consumes_requirements`, and
`kind` fields; the **verification substrate** (seven tasks
T-v1 — T-v7) wiring `build_check` checks that run real shell
commands (pytest, npm build) and feed structured findings back
into the substrate's typed state; and the **GUID identity layer**
(six tasks T-g1 — T-g6) making citation chains drift-proof
under artifact mutation by tagging every artifact with a stable
GUID.

These layers established the typed-state machine the iteration
loop would later harden — requirements (durable, axis-tagged),
milestones (kind-tagged, with done-when), stories/features/
tickets (lifecycle-tracked, citation-chained), implementations
and reviews (artifact-emitted, GUID-anchored), verify gates
(pytest, npm build, with structured findings).

mvp ran on this foundation and shipped a working app for
$83.78. The very act of running it surfaced ~28 substrate gaps
the foundation didn't cover. Those became the input for
Phase 2.

---

## §6.4 — Phase 2: First-pilot hardening (T-ab1 — T-ab28)

mvp was the first end-to-end autonomous Tier 2 pilot. The
operator gave the substrate the notebook directive (~80 lines
of operator-written specification covering capabilities, stack
constraints, non-goals, and success criteria; see
`src/wonderland/closet/directives/notebook.yaml` in the repo)
and let the agents run through discovery, milestone planning,
design, and implementation across three milestones
([analysis 034](https://github.com/KohlJary/wonderland-ai/blob/main/src/wonderland/closet/analyses/034-mvp-demo2-autonomous-pilot.md)).
Telemetry, post-pilot analysis, and operator-noticed pattern
recognition together surfaced ~28 distinct substrate
weaknesses. Each became a T-ab task.

The dominant pattern across Phase 2's fixes is **milestones
becoming structurally load-bearing**. The foundational
substrate had shipped milestones as typed artifacts; the pilot
revealed that "the agents read milestones" was not enough.
The substrate needed structural invariants that forced the
agents to actually USE the milestone scope rather than treating
it as ambient context. Four fixes carry the load:

**Foundation/capability axis** (T-ab6, T-ab13, T-ab15) added
`kind: foundation | capability` as a typed field on milestones
with design-phase roster narrowing by kind (Caterpillar solo
for foundation, Alice solo for capability). Closed mvp-demo's
M1-overshoot pattern where the agents shipped backend +
frontend + tests for all three milestones in one pass because
no kind distinction existed.

**Per-milestone memory branching** (T-ab8) introduced distinct
episodic memory namespaces keyed by active milestone. New
milestones start with clean memory; old branches still exist
for retrieval but don't pollute fresh deliberation. This was
the **load-bearing Tier 2 autonomy unlock** — without it, the
substrate could ship M1 cleanly but couldn't ship M2 without
operator memory-clearing. The architectural insight: substrate
damage to typed state self-repairs (Pillar 4); substrate damage
to episodic memory doesn't, and branching at milestone
boundaries is the architectural fix.

**Story-layer milestone scoping** (T-ab9 + T-ab48) added the
milestone seed filter (M2 design seeded only with M2-tagged
requirements/stories/features) plus the write-time validator
(Alice's story emission rejected at write time if milestone tag
doesn't match active scope).

**Tools write-guard** (T-ab12) added perimeter enforcement —
agents can read substrate paths but cannot write to them via
file manipulation tools out-of-band. Without it, agents had
unauthorized write paths that bypassed lifecycle invariants.

Phase 2 also shipped many smaller fixes (iteration efficiency
filters T-ab16-T-ab19, memory recall budgeting T-ab24a/b/c,
review scope discipline T-ab20-T-ab21, per-phase memory scope
T-ab25a, verify finding attribution T-ab26-T-ab28) that filled
out the corners of the substrate without exemplifying the
milestone-as-load-bearing theme as cleanly. The architectural
insight from the cluster: **the substrate enforces what its
convenor directives request** — prose tells the agents what
to do; the substrate refuses to admit emissions that violate
the request.

The next pilot (obol-260522, the CRM project) ran on this
hardened substrate.

---

## §6.5 — Phase 3: Cross-milestone bleed closure (T-ab29 — T-ab53)

obol-260522 was the first Tier 2 pilot on the post-mvp
substrate. It built a CRM project across 4+ milestones,
much larger scope than mvp's notebook. The pilot
shipped at $92.64 — 11% more than mvp — which was
surprising on a hardened substrate. Cost-driver analysis
revealed the substrate's invariants were leaking on a class
of bug that the Phase-2 fixes had partially patched but
not fully closed: **cross-milestone bleed**.

### The bleed pattern across pilots

The pattern: an agent working on milestone N could read
artifacts from milestone N+1 (forward-bleed) or milestone
N-1 (backward-bleed), causing the agent's deliberation to
include out-of-scope context. The symptom was usually a
cost spike (the agent reading more than it needed) or a
quality regression (the agent producing work shaped by
context it shouldn't have had).

T-ab8 (per-milestone memory branching) had closed the bleed
at the episodic-memory layer. T-ab9 (milestone seed filter)
had closed it at the seed-pool layer. T-ab48 (write-time
validator) had closed it at the story-emission layer. But
the bleed kept appearing in new forms:

- **T-ab34** — scope existing-artifacts framing blocks to
  active milestone (framing prose was including off-scope
  context).
- **T-ab35** — tool-level milestone scoping for read_file
  (agents were using tools to read off-scope files even
  when the substrate's seed pool wouldn't have surfaced
  them).
- **T-ab45** — scope-lock framing on scoping + composition
  directives (the framing for these meetings still leaked
  off-scope artifacts despite seed-pool filtering).
- **T-ab46** — filter list_files to active milestone in
  scoping/composition (agents using list_files saw off-scope
  files even with read_file scoped).

Each fix patched a specific surface. None of them got at the
underlying invariant: **every read of milestone-scoped state
should be filtered to the active milestone.** The fixes were
playing whack-a-mole with the surfaces while leaving the
invariant unenforced at the substrate level.

### T-ab51 — the keystone

Finally, T-ab51 shipped as **the milestone-scope filter at
the seed-resolution layer**. The fix recognized that all the
prior patches were treating individual symptoms; the real
bug was that the seed-pool resolver, when asked for
artifacts of a given kind, returned EVERYTHING of that kind
on disk and let downstream code filter. By moving the
milestone filter to the seed-resolver itself, every
downstream consumer inherited the filter for free.

T-ab51 closed the bleed across requirement + story + feature
axes simultaneously. Audit revealed that some downstream
surfaces had been filtering requirements correctly but not
stories, others stories but not features. The keystone fix
unified all three under one invariant.

The architectural insight: **invariants belong at the read
point, not at every consumer.** Fixing a bleed at every
downstream surface is fragile because new surfaces keep
appearing; fixing it at the source eliminates the class of
bug entirely. Same pattern as input validation in web
security: validate at the boundary, not in every handler.

### T-ab52 — write isolation needed read-side teeth

A subtler architectural finding emerged from the obol pilot
post-mortem. T-ab8's per-milestone memory branching
isolated WRITES — a milestone's deliberation would write
into its own memory branch. But it did not isolate READS.
The `compose_context` helper that retrieved relevant
memory for an agent's deliberation bypassed the
inheritance_chain that branches were supposed to provide,
reading from all branches indiscriminately.

The symptom: even with per-milestone branching, an agent
could still see episodic memory from adjacent milestones
because `compose_context` queried the full memory store,
not the active branch.

T-ab52 fixed `compose_context` to honor the inheritance
chain. Write isolation finally had read-side teeth.

The architectural insight, paper-grade: **memory branches
that isolate writes but not reads provide the illusion of
isolation without the substance.** The whole purpose of
branching is to bound what the agent sees during
deliberation; if reads escape the branch, branching
becomes accounting overhead with no behavioral effect.
The fix required auditing every memory-read site for branch
honoring, not just the obvious ones.

### T-ab53 — implicit milestone derivation for implement runs

The implement workflow (tdd-implement) needed to know the
active milestone to scope correctly. Earlier code had
required the active milestone to be set explicitly by the
caller. T-ab53 added implicit derivation: if there are
queued + in-progress features all in the same milestone,
that's the active milestone. The substrate could now infer
scope from the work itself, eliminating a class of
"forgot to set active milestone" operator errors.

### The Phase 3 substrate after the fixes

By the end of Phase 3, the cross-milestone bleed pattern
was closed at the architectural level — every read of
milestone-scoped state inherited the filter from the
seed-resolver, the memory branches had read-side teeth, and
the implement workflow derived its scope from the work
itself.

Phase 3 also surfaced what the next pilot would need to
test: whether the substrate's per-milestone cost trajectory
("foundation-once, capability-cheap") would actually
materialize when cross-milestone bleed was structurally
impossible.

mvp-demo-redux was that pilot.

---

## §6.6 — Phase 4: Cost trajectory hardening (T-ab54 — T-ab64)

mvp-demo-redux re-ran mvp's notebook spec on the
post-T-ab53 substrate. **$30.58 vs the original $83.78**
— a 63% cost reduction on identical scope, same model,
same per-MTok pricing
([analysis 046](https://github.com/KohlJary/wonderland-ai/blob/main/analyses/046-mvp-redux-cost-receipt.md)).
The per-milestone trajectory showed the predicted shape
for the first time: M1 foundation $15.59, M2 capability
$10.91, **M3 capability $3.72** — capability work building
on solid foundation, decreasing monotonically as the
foundation amortized.

This was the substrate's first cost-trajectory receipt.
The Phase-3 fixes were validated. The next set of fixes
hardened against the remaining gaps cost analysis surfaced.

### T-ab54 — M8 review roster narrowed to Caterpillar-only

obol-260522 telemetry showed Tweedles spending 2.2×
Caterpillar's cost in M8 review meetings at 80% pass rate —
pure window-opening overhead. The Tweedles' contributions
to review were mostly procedural acknowledgments; the
load-bearing review work was Caterpillar's.

T-ab54 narrowed the M8 roster to Caterpillar solo. Tweedles
were removed from `team_groupings`. The pass-rate stayed
high (Caterpillar alone caught what Caterpillar-plus-Tweedles
caught), and the per-M8 cost dropped sharply.

In the redux pilot, M8 review consumed ~11% of total cost
instead of the ~30%+ it had consumed pre-fix. Same review
quality, third the spend.

### T-ab57 — tool-result cap

Tool results (from `read_file`, `list_files`, `verify_imports`,
etc.) were being returned to agents at full length. Some
returns were many KB. Each return participated in the agent's
deliberation context and got cached, paid for, and replayed
on every subsequent tool-use round-trip in the same
deliberation.

Cost analysis showed that 52% of total tool-result bytes
across all tool-using agents were lying in deliberation
context past the point of usefulness — Mad Hatter's M6 work
was the biggest single contributor (he reads test scenarios
in detail then doesn't need the full text again).

T-ab57 capped tool results in the deliberation loop at 5K
characters. The first round-trip got the full result; subsequent
rounds got the cap. Aggregate bytes saved across all
deliberations: 52%. Quality unchanged.

The architectural insight: **deliberation context bloat
compounds across rounds because each round caches the
prior round's full context.** The cap exploits the
observation that agents rarely re-read the full text of a
prior tool result; they want enough context to remember
what they saw, not the verbatim text. A cap that preserves
the head of the result keeps the actionable detail bounded.

### T-ab60 — source-line context in npm build failures

When npm build failed, the agent received the raw error
text. TypeScript errors typically point at a file:line and
say "Type 'X' is not assignable to type 'Y'" — actionable,
but without the surrounding source the agent has to read the
file separately to understand the context. The result was
multi-cycle convergence: agent reads error, reads file,
proposes fix, fix breaks something else, re-runs build,
reads new error, reads file again, etc.

T-ab60 extracted the failing line ± 3 surrounding lines from
each error location and embedded them in the finding. The
agent now sees both the error and the context together. In
the LDR pilot's first build failure, convergence dropped
from the typical 5-cycle dance to a single pass: the agent
read the contextualized error and produced the fix in one
round.

The architectural insight: **structural context at the
point of failure compresses convergence cycles.** It's the
same insight T-ab30 (per-test traceback in verify findings)
applied to a different verification surface. Both fixes
encode the principle: when the substrate surfaces a failure,
include enough context that the agent can act on it without
a separate read round.

### T-ab62 — requirement citations in phantom-citation filter

The phantom-citation filter (a substrate invariant: every
artifact's `sources` must resolve to real upstream artifacts
on disk) was dropping the LDR pilot's M2 feature. The
feature's sources cited the milestone's `consumes_requirements`
slugs — legitimate citations of foundation-milestone work
— but the filter only validated against story + milestone
slugs, not requirement slugs.

T-ab62 widened the filter to accept requirement citations
as valid feature sources. The invariant was real (drop
drift-corrupted citations), but its scope was
under-permissive (it rejected legitimate foundation-feature
citations). Widening the valid set preserved the
drift-detection while unblocking the legitimate flow.

The architectural insight, paper-grade: **substrate
invariants need to evolve as the substrate's typed-state
relationships evolve.** When foundation milestones produced
features that descended directly from requirements
(skipping the intermediate story layer), the citation chain
became `feature.sources → requirement` instead of
`feature.sources → story`. The filter's set of valid source
kinds had to expand to keep up. Diagnostic took longer than
the fix: ~2 hours to trace the drop, ~2 lines of substantive
code change to fix it.

### T-ab64 — end-to-end verification gates

The LDR pilot exposed a class of failure the prior
verification stack couldn't catch: **hollow features**.
Features marked `verified` lifecycle state whose UI surface
was placeholder text, whose components were orphaned
(imported nowhere), whose backend endpoints were missing
despite the frontend calling them, whose mocked data was
never replaced with real implementation. The existing M9
gates (pytest_collects, pytest_passes, npm_build) all
passed cleanly because per-layer checks compose without
catching cross-layer hollowness: pytest passed because only
the skeleton test existed; npm build was clean because
orphan TypeScript components still compile; Caterpillar's
review reads code but doesn't run it.

T-ab64 added four end-to-end composition checks to M9:

- **frontend_imports_reachable** — every .tsx component
  must be reachable from the entry point via the import
  graph. Catches orphan components.
- **api_call_resolves_to_route** — every `/api/...` URL
  string in the frontend must resolve to a registered
  FastAPI route. Catches missing backend endpoints.
- **no_placeholder_on_render_path** — no TODO/FIXME/
  placeholder markers in files reachable from the frontend
  entry. Catches placeholder text shipped as user-facing
  output.
- **no_duplicate_modules** — no two Python modules export
  the same public API surface. Catches parallel-write
  collisions (two agents wrote the same utility
  independently).

All four are skeleton-gated: backend-only / library / CLI
skeletons skip the frontend checks; pure-frontend skeletons
skip the backend checks. Same silent-degradation pattern
that pytest_collects and npm_build already use.

The architectural insight, paper-grade: **per-layer
verification doesn't compose into end-to-end verification.**
The substrate had per-layer gates (tests, builds, reviews)
but no gates that asked "does the feature actually deliver
end-to-end?" The hollow-verify gap was structurally
predictable from the framing — when a state transition's
admission criteria are defined as a conjunction of local
checks, the transition can fire on hollow data if no global
invariant binds the locals together. T-ab64 added the
binding invariants.

Validated against the LDR pilot's directory: catches all
four substantive findings the operator noticed manually
(NewsCard orphan, /api/news unregistered, /api/messages
skeleton ghost, auth/security duplication). Validated
against the redux pilot: catches one known-harmless finding
(/api/messages skeleton ghost from api.ts already
documented in analysis 046).

### The Phase 4 substrate after the fixes

By the end of Phase 4, the substrate had:

- A cost trajectory across two pilots that demonstrated
  the constraint→quality+cost coupling at scale.
- M8 review compressed to its load-bearing voice (Caterpillar
  solo) without sacrificing pass-rate.
- Tool-result deliberation context bounded by structural cap.
- Verify findings carrying enough context to compress
  convergence cycles.
- Phantom-citation invariants expanded to admit legitimate
  foundation-milestone citation chains.
- End-to-end composition gates catching hollow-feature
  shipments that per-layer gates missed.

The pending LDR re-run will test whether T-ab64 closed the
hollow-verify gap operationally. The substrate's invariant
stack is at its strongest to date.

---

## §6.7 — The pattern across all four phases

Stepping back from the individual fixes, the substrate
evolution arc reveals several patterns worth naming.

### Every fix is structural

Across ~60 substrate fixes (T-i + T-m + T-v + T-g + T-ab1
through T-ab64), almost none modify agent prompts or
constitutions. The fixes are at the substrate level: typed
field additions, lifecycle invariant changes, seed-pool
filter rules, memory branch enforcement, verification check
additions, tool access guards. The agents themselves are
remarkably stable across the evolution — the constitutions
shipped in v0.4 are largely the constitutions running in
v0.10.2.

This is what Corollary 6 predicts: substrate constraints
let identity carry more of the discipline from inside, so
the work of improving the system happens at the substrate
layer, not the agent layer. The agents get cheaper to
coordinate as the substrate's invariants multiply, not
because the agents got smarter, but because the substrate
got better at refusing to admit transitions the agents
would otherwise produce.

### Each fix encodes a missing invariant

The substrate fixes are not arbitrary improvements; each one
encodes a structural invariant the substrate should have
been enforcing all along but wasn't. The invariants
discovered:

- Citations must resolve to real upstream artifacts on disk
  (phantom-citation filter, T-ab62 widening)
- Active milestone scope must filter every read site, not
  just specific consumers (T-ab51)
- Memory branches must isolate reads, not just writes
  (T-ab52)
- Feature emissions must declare an explicit milestone tag
  (T-ab48)
- Substrate paths must be perimeter-enforced — agents can't
  write to typed-state directories out-of-band (T-ab12)
- Frontend API calls must resolve to backend routes (T-ab64)
- Frontend components must be reachable from the entry point
  (T-ab64)
- Two modules can't export the same public API (T-ab64)
- Cycles must converge — verify-spawned tickets must be
  fresh per cycle, not stale (T-ab28)
- Tool-result context must be bounded structurally, not
  by agent self-restraint (T-ab57)

Each invariant is, in retrospect, obvious — the substrate
should always have had it. The iteration cycle's job is to
discover these invariants empirically, surface them as
substrate-level fixes, and accumulate the stack.

### The cost trajectory is the invariant stack's signature

The two-pilot cost trajectory ($83.78 → $30.58, 63%
reduction on identical scope) is not produced by any single
fix. It's the aggregate signature of the invariant stack.
Approximate per-fix attribution against the $53.20 absolute
gap, derived from observed per-fix savings + cross-pilot
cost-pattern comparison:

| Fix or fix cluster | Approximate contribution | Mechanism |
|---|---|---|
| **T-ab51** (keystone milestone-scope filter at seed-resolution layer) | ~30-40% of the gap | Closed cross-milestone bleed across requirement + story + feature axes simultaneously. Eliminated the rework cycles that drove obol-260522's cost-rise pattern. Observed by absence: redux's design-side cost per milestone is 60-70% lower than obol-260522's, with the substrate-version delta being primarily T-ab51's invariant. |
| **T-ab54** (M8 roster narrowed to Caterpillar-only) | ~15-20% of the gap | Tweedles removed from review meeting; ~$8/M8 cycle direct savings on obol-260522 telemetry. M8 spend dropped from ~30% of total in mvp pilots to ~11% in redux, with no review-quality regression. |
| **T-ab8 + T-ab52** (per-milestone memory branching + read-side teeth) | ~10-15% of the gap | T-ab8 was already shipping in mvp's substrate (T-a2 era); T-ab52 closed the read-side leak that made T-ab8's write isolation incomplete. The combined effect eliminates the memory-bleed wedges that drove mvp-demo's M4 to ~22 rotations on stale requirements. |
| **T-ab57** (tool-result cap in deliberation loops) | ~10-15% of the gap | 52% of total tool-result bytes saved across all tool-using agents. Bytes don't map 1:1 to cost (caching dynamics), but the bytes saved correlate strongly with cache-replay overhead on subsequent rotation rounds. |
| **T-ab16 — T-ab19** (iteration efficiency filters) | ~5-10% of the gap | Empty-iteration skipping (`iterate_only_with_tickets`, implicit milestone scope, cross-milestone emission rejection, no-in-scope-tickets M4 skip). Each opens fewer priority windows on items where deliberation produces no signal. |
| **T-ab30 + T-ab60** (per-test traceback + source-line context in verify findings) | ~5% of the gap | Compressed npm-build convergence from typical 5-cycle dance to 1-pass in the LDR pilot. Smaller absolute contribution because the failure-path is rarer, but the per-cycle savings on the build-failure trigger are real. |
| Residual (other Phase 2-4 fixes, cache dynamics, secondary effects) | ~5-15% | Smaller fixes (T-ab43 disk reconciliation, T-ab44 meeting ID, T-ab23 swallowed-crash catching, T-ab24 memory-recall budgeting, T-ab27 nudge filtering, T-ab28 verify ticket synthesis, others) each contribute modestly; aggregate is real but not individually large. |

The attribution is **approximate by necessity** — the fixes
compound non-additively, exact per-fix isolation would
require A/B re-running each fix's substrate version against
each other in matched-on-task comparisons, and even that
wouldn't disentangle interaction effects between fixes that
close related classes of waste. The table reports best-
available per-fix observations + qualitative reasoning about
mechanism rather than statistically-clean attribution. It is
presented to give a reader a sense of which fixes carry
which fraction of the load; it is not presented as
defensible decomposition for purposes of single-fix
optimization claims.

The fixes compound because each one closes a class of waste
the prior fixes didn't catch. The architectural commitment that makes the
compounding work: **substrate fixes encode missing
invariants, so they don't conflict with prior fixes; they
extend the invariant stack.**

A fix that improved one agent's prompt might trade off
against another agent's behavior. A fix that adds a
structural invariant doesn't trade off — it narrows the
grammar of legitimate emissions, which downstream agents
benefit from regardless.

### The state-machine framing predicts where gaps appear

A second-order pattern: the gaps the iteration cycle
discovered are exactly the gaps the state-machine framing
predicts. When the substrate's typed-state transitions are
defined as conjunctions of local checks, transitions can
fire on hollow data if no global invariant binds the locals
together. The hollow-verify gap (T-ab64) is the canonical
example: pytest passes + npm builds + Caterpillar reviews
+ operator approves are all local checks, none of which
asks "do these compose into a working end-to-end
deliverable?"

The same shape applies to cross-milestone bleed (each
read site checked scope locally, but no invariant bound
them at the resolver), to phantom citations (each
artifact's sources were locally well-formed, but no
invariant bound them to disk reality), to memory bleed
(write isolation was a local property, but reads escaped
it).

The state-machine framing isn't just descriptive — it
predicts where the next substrate gap will be. **Wherever
a transition's admission criteria is a conjunction of
local checks without a binding global invariant, the
substrate is one pilot away from discovering that the
transition can fire on hollow data.** The methodological
upshot: future substrate work should pre-emptively look for
transitions whose admission criteria lack global binding
invariants, and add the binding before the next pilot
exposes the gap.

### Operator-in-loop as falsification mechanism

The iteration cycle depends on the operator running pilots
in earnest and noticing gaps that automated checks pass
over. The hollow-verify gap was operator-noticed (Theseus
review surfaced it from a fine-tooth-comb code review the
operator ran post-pilot). The cross-milestone bleed was
operator-noticed (cost spikes on obol-260522 didn't match
expected per-milestone trajectory). The Caterpillar
silence-bias was operator-noticed (M8 review producing no
artifact despite reading code).

This is what makes the substrate's iteration cycle
**science** rather than engineering polish. Each substrate
fix is a falsified prediction: the prior substrate said
"this transition is admissible"; the operator says "no,
the transition fired on hollow data, here's the
counter-example"; the fix encodes the missing invariant.
Without the operator's adversarial gaze, the substrate's
gaps remain hidden behind passing tests. With them, the
substrate's invariant stack grows monotonically.

The methodological commitment Wonderland makes is that
the operator IS part of the substrate's design loop, not
just its user. The pilots are the experimental harness;
operator-noticed gaps are the experimental results; the
substrate fixes are the theoretical refinements. The
two-pilot cost trajectory is the empirical signature of
this loop functioning correctly.

---

## §6.8 — What comes next

The substrate's iteration cycle is open-ended. Several
classes of work are queued or in flight:

### Template-similarity milestone consolidation (T-ab63)

When the planner produces multiple capability milestones
that share the same architectural template (consume
foundation X → fetch external data → render on surface Y),
they should consolidate into one milestone with N features.
LDR's M3/M4/M5 (time, weather, news cards) were the
canonical case — three separate milestones with identical
shape. T-ab63 will teach the planner to detect the
template-similarity pattern and consolidate.

Deferred until parallel coordination ships (see below);
consolidation maximizes the surface area parallel
coordination applies to, so they pair multiplicatively.

### Parallel coordination

The substrate currently runs serially — one milestone at a
time, one feature at a time within a milestone, one ticket
at a time within a feature. The substrate's typed-state
machinery already supports parallel orchestration in
principle: per-milestone memory branching isolates
concurrent milestones; feature-level lifecycle states are
orthogonal across features; `gates_on_dependencies` in M7
already supports per-ticket dependency gating. What's
missing is a coordinator that decides "these N features
can run M7 in parallel" based on the dependency graph, and
the orchestration to actually fan them out.

Parallel coordination is the wall-clock-time lever. Cost
optimizations from prior phases got the per-pilot spend
down; parallel coordination gets the per-pilot time down.
Together with template consolidation, this is what closes
the gap to systems like Devin that compete on wall-clock
rather than per-task quality.

### The LDR re-run

The LDR pilot is being re-run on the post-T-ab64 substrate.
Outcomes: either the four end-to-end gates catch the
hollow-feature class operationally (third receipt for the
cost trajectory + validation that T-ab64 closed the gap),
or the re-run surfaces a new substrate gap T-ab64 doesn't
cover (next substrate fix, next iteration cycle).

Either outcome is paper-grade. Receipts and substrate
findings both extend the invariant stack.

### Existing-codebase / change-request feature surface

The substrate currently bootstraps from a directive + a
skeleton. It doesn't yet support "here's an existing
codebase, implement this change request." Adding this
surface would let the substrate handle the most common
real-world software work shape: iterating on existing
software, not green-field MVPs.

The architectural work: ingesting an existing codebase into
the typed-state substrate (every existing file becomes
artifact-attributed; every existing dependency becomes a
contract), then running the design-implement loop against
the augmented state.

### Multi-operator concurrency

Single-operator pilots dominate the substrate's evolution
to date. The substrate is theoretically multi-operator-
ready (typed state is the canonical source; agents don't
care which operator is in the loop), but the operator-in-
loop falsification mechanism currently assumes one operator
per pilot. Multi-operator concurrency would test whether
the falsification mechanism scales — does two operators
running pilots in parallel produce twice the substrate
findings, or does the substrate's invariants converge to
the union of both operators' observation power?

### Other model families

The substrate currently targets Claude Haiku 4.5.
Generalization to other small models (open-weight or
otherwise) is future work that would test whether the
substrate-amplifies-identity claim is Haiku-specific or
applies to small models generally.

---

## §6.9 — Closing frame

The substrate's evolution is the methodology. Each phase
shipped a load-bearing layer of structural invariants the
prior phase lacked. The cost trajectory developed in the
Phase 4 section above is not a one-shot win; it's the
aggregate signature of an invariant stack that took ~60
substrate fixes to accumulate. The next pilot's cost will
be determined by whatever invariants the current stack
still lacks; the iteration cycle will discover them.

The architectural commitment that makes this work — that
state is primary, agents are transition functions over
typed durable artifacts, invariants belong at the
substrate level rather than the agent level — is what
allows the fixes to compound rather than trade off. A
multi-agent system that improved through agent prompt
tweaks would see prompt edits collide; an agent's
behavior tuned for one situation would degrade in
another. Substrate invariants don't collide because they
narrow grammar; the agent is still free within the
narrowed grammar, but the substrate refuses to admit
emissions outside it.

**This is the chapter's load-bearing claim: building a
multi-agent SDLC system that produces working code at
low cost on small models is not a matter of finding the
right prompts or the right model. It is a matter of
accumulating the right structural invariants over typed
state, and the discovery process for those invariants is
the iteration cycle this chapter documents.**

Identity engineering is the discipline. The substrate
invariant stack is identity engineering's empirical
backbone. The iteration cycle is identity engineering's
methodology. Wonderland is one instance; the paper is
the case for the discipline being worth pursuing beyond
this instance; this chapter is the receipt for the
discipline functioning.

---

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

# §8 — Limitations

## §8.1 — The publishing-snapshot premise

Before naming any specific limitation, the chapter has to
make a methodological commitment that frames everything
below: **this chapter documents the limitations of the
Wonderland substrate at the publication-snapshot version,
not in perpetuity.** The iteration cycle documented in the
substrate-evolution chapter (§6)
is open-ended; every limitation in this chapter is either:

1. **Already addressed** in a substrate fix that shipped
   between the gap being observed and the paper being
   written (named here as historical context — the
   limitation existed, it was named, it was fixed; the
   chapter cites it to show the iteration cycle working).
2. **Addressed with the fix shipped, validation pending**
   in the next pilot (LDR re-run for the T-ab64 fix is
   the canonical example).
3. **Open with a filed roadmap fix and a known timing**
   (parallel coordination, template-similarity
   consolidation, multi-operator concurrency — each has a
   filed task and a known sequencing).
4. **Open with no filed fix because the right shape
   isn't yet known** (the P7 generic-baseline eval is the
   clearest example — we know we should compare, we don't
   yet have the right harness design).

The chapter is written this way because publication is a
snapshot, not an end. Every paper that documents an
ongoing research artifact has to draw a publication line
through a moving target; the right discipline is to draw
the line where the substrate is most receipt-worthy, name
what's open as of that line, and continue the iteration
cycle past the line. The alternative — waiting until
nothing is open — is structurally impossible for a
research artifact whose evolution surfaces new gaps with
every pilot. **The limitations below are not defeats; they
are the visible edge of an iteration cycle that has, to
date, closed every prior class of limitation it has
surfaced.**

This framing is load-bearing for the chapter and the
paper. A reader who reads "limitations" as
"unsolved-and-likely-unsolvable" misreads what the
chapter is doing. The reader who reads "limitations as
publishing-snapshot of an iteration cycle, each with
either a filed fix or a known reason no fix exists yet"
reads the chapter at the right epistemic register.

---

## §8.2 — What counts as a limitation here

This chapter distinguishes four classes of limitation, each
with a different epistemic shape:

| Class | Shape | Examples |
|---|---|---|
| **Substrate gap** | Known failure mode with a filed fix (often in roadmap). | b3f440c8 cluster; Caterpillar's static blindspot. |
| **Scope-bounded validation** | Claim holds in the spec'd use case but would fail outside it. | B1 + C2 from code-quality artifact (latent at v1, acute at v2). |
| **Sample-size limit** | N is too small to support a stronger claim than "observation with mechanism." | N=2 pilots; one directive class; one model class. |
| **Missing rigor** | Comparison or eval that would strengthen the claim hasn't been run. | P7 generic-baseline eval; single-shot Haiku/Sonnet comparison baselines. |

---

## §8.3 — Substrate gaps

### The "prior-milestone-awareness" cluster — closed

The mvp Tier 2 pilot surfaced four substrate gaps
(b3f440c8 sibling-feature visibility, 4a2597a4 cross-feature
consolidation, 81af78f8 two-tier feature presentation,
e7d226b8 coverage check aware of shipped implementations)
that shared a single theme: the substrate had limited
awareness of prior-milestone shipped work at different
layers. The cluster is documented in detail in §6 (substrate
evolution); it has been closed by the keystone milestone-scope
filter (T-ab51) plus iteration filters T-ab17 + T-ab18 + the
scope-framing fixes T-ab34 + T-ab46 and iteration-pruning
T-ab41. Tier 2 autonomy at the post-T-ab51 substrate no
longer requires the operator's duplicate-skipping discipline
that mvp's pilot needed. Cited here as the canonical example
of an open limitations cluster closing through iteration; the
still-open items follow.

### Hollow-verify gap (LDR exposure, T-ab64 closure, validation pending)

the LDR pilot at substrate 0.10.2 + T-ab62 exposed a class
of failure the M9 build_check stack couldn't catch — features
that ship in `verified` lifecycle state with hollow
deliverables (orphan UI components calling non-existent
backend endpoints, placeholder dashboard text, hardcoded
mocked data never replaced, parallel-write duplicate modules).
Per-layer checks (pytest, npm build, Caterpillar review,
operator gate) all passed cleanly because each check is local
— none asks "do these compose into a working end-to-end
deliverable?"

The substrate exposed-and-addressed cycle:

- **Exposure**: LDR pilot completed at $19.44 with six
  features marked `verified`. Operator-commissioned Theseus
  review surfaced the hollow-feature pattern across
  multiple features. Documented as a memory observation +
  the substrate-gap entry above.
- **Diagnosis**: per-layer M9 checks compose without
  catching cross-layer hollowness. The state-machine
  framing predicts this — when a lifecycle transition's
  admission criteria is a conjunction of local checks
  without a binding global invariant, the transition can
  fire on hollow data.
- **Closure**: T-ab64 shipped four new M9 end-to-end
  composition checks (frontend_imports_reachable,
  api_call_resolves_to_route,
  no_placeholder_on_render_path, no_duplicate_modules) all
  skeleton-gated to skip silently when project shape
  doesn't match. Validated against the LDR pilot directory:
  catches all four substantive Theseus findings.
- **Validation pending**: LDR re-run on the post-T-ab64
  substrate will produce either a clean third receipt
  (validating T-ab64 closed the gap operationally) or
  surface a residual gap T-ab64 doesn't catch (next
  iteration cycle's input). Either outcome is paper-grade.

The original LDR $19.44 is documented honestly: it is **not
cited as a working-app receipt** because the deliverable
was hollow. It is cited as the cost of the pilot that
exposed the hollow-verify gap, which is itself a valuable
research artifact — the gap was found at $19.44 of pilot
spend, which is structurally cheaper than the gap remaining
hidden behind passing tests until the substrate hits a
larger project where it would be more expensive to surface.

This is the canonical demonstration of the iteration-cycle
discipline working cheaply: a substrate gap surfaced in a
$20 pilot, addressed in a ~200-line substrate fix, validation
pending in the next pilot. The publishing-snapshot premise
above is what makes this a defensible "limitation" — the
fix shipped, validation is in flight, and the chapter
documents it openly rather than pretending the original
pilot was clean.

### Adjacent: stronger contextual signal per phase

Three roadmap items share a related theme — *"agents need
stronger contextual signal per phase"* — but at a different
layer than the cluster above:

- **79ef174a — Persona-anchoring in milestone-plan.** The
  tdd-design entry meeting prepends a milestone-framing
  block that names the active persona; milestone-plan has no
  equivalent. Alice gets confused about persona during
  milestone-plan. Surfaced in mvp; small directive
  edit, substrate-side helper.

- **Auto-directive synthesis** (shipped mid-pilot,
  124b5858). Was a Tier 2 violation made explicit. When
  `run_workflow` fires with empty directive AND an active
  milestone scope, synthesize one from milestone fields.
  Caterpillar got M2 design right (search story) but Alice
  drifted into M1-flavored stories (capture flow) because
  the per-run signal of "you are designing M2 specifically"
  wasn't strong enough. The fix shipped + held in M3 design.

- **837b5bbb — Feature sequencing (Feature.depends_on).**
  Operator's observation during mvp: *"putting features
  in an order would as a byproduct result in more tightly
  designed features."* Currently features are a bag; explicit
  dependency would force Rabbit during M2 to think about
  what each feature delivers + what enables it. Same shape
  as snapshot semantics + milestone scoping: constraints
  improve quality. Partially resolves b3f440c8.

These items aren't substrate gaps in the cluster sense —
they're targeted single-point additions. But they share the
underlying pattern that *the agents need more structure per
phase than the current substrate provides*.

### M1-overshoot pattern (milestone boundaries are advisory)

in mvp-demo, M1's implementation pass shipped working
backend AND frontend, overshooting 3 milestones deep. M2 +
M3 design then wedged because no actionable delta remained.

The architectural observation: **once Tweedles start, they
build the whole app.** Implementation budget doesn't respect
milestone scope at the Tweedle level. They're optimizing for
"make this work as a system," not "stop at milestone N's
boundary." This is the architectural choice that produces
the overshoot.

Framing options for the paper:
- **Positive:** Wonderland over-delivers per implementation
  pass.
- **Negative:** Milestone boundaries are advisory, not
  enforced.

Both framings are accurate. The chapter should be honest
about both. The forward implication: milestone-plan should
detect overlap risk at planning time (forward-realization
check between milestones); currently the planning pass
doesn't compute this. Not yet filed as a discrete roadmap
item; lives as a known pattern.

---

## §8.4 — Known model-class limits

### Caterpillar's static blindspot

M8's review reliably misses single-file static-time bugs —
Pydantic field/type shadows, unresolved forwards, decorator
order traps. Class of bug that "would not even import"
ships through M8 untouched.

The root cause: M8 prioritizes cross-ticket coherence FIRST
(per analysis 040), the failure mode no single-file review
can catch. That prioritization explicitly trades against
per-file static-time correctness. Caterpillar reads code;
she doesn't load it.

**The fix exists** and shipped — `verify_imports` tool
exposed to Caterpillar (T-v5) gives a mechanical check for
the most common class. M9's `pytest_collects` build-check
catches the rest. So this is a "known limit + known fix"
rather than an open gap; the chapter should mention it as
evidence of the categorization-through-failure discipline
(name the class, ship the right-sized fix, move on).

### Cross-endpoint behavioral integration invisible to M8

Per the [code-quality analysis §6.2](https://github.com/KohlJary/wonderland-ai/blob/main/paper/artifacts/code-quality-mvp.md#62-c2-cross-endpoint-serialization-mismatch--failure-mode-of-m8-static-review):
the C2 finding (revision_id serialization mismatch — same
note produces different revision_ids depending on which
endpoint surfaced it) is the canonical M8-blindspot pattern
at a different layer than the static blindspot above.

Both functions read correctly in isolation. The bug only
manifests when a client uses a revision_id from one
endpoint as the If-Match for another. M8 reads files for
coherence, not behavioral integration across endpoints.
M9's `pytest_passes` would catch it IF an integration test
existed; the test gap (no PUT/collision tests, no
audit-log tests) and the implementation gap reinforce each
other.

**The right-sized fix is cross-endpoint scenario coverage as
a first-class Hatter generation prompt during M6** — Hatter
generated scenarios for search-escaping but not for
revision_id round-tripping. Filed as future-work, not yet
implemented.

Scope honesty: this finding is latent in mvp's spec'd
use case (single-user, no concurrent writers). It would
become acute if the spec grew to multi-user. The substrate
built the optimistic-locking infrastructure correctly enough
for the scope; the bug is evidence about substrate reach,
not about whether the shipped artifact works.

### Frontend test coverage gap

Per the code-quality artifact reviewer findings: `vitest`
is installed in `demo/mvp/frontend/package.json` but zero
frontend tests exist. The Tweedles' M7 directive doesn't
require Hatter scenarios to be translated into runnable
frontend tests; M9's `npm_build` verifies compile + bundle,
not behavior.

This is the single biggest test-coverage gap in the shipped
artifact, and **it's exactly where the substrate has no
enforcement loop**. Backend tests get written because M9's
`pytest_passes` build-check exists; frontend tests don't
get written because there's no parallel.

The right-sized fix: M9 gains an `npm_test` build-check
parallel to `pytest_passes` / `npm_build`; M7's directive
gains an explicit requirement that the Hatter scenarios for
this ticket exist as runnable tests in the appropriate test
directory. Filed as future work.

---

## §8.5 — Sample-size limits

The chapter should be explicit that current evidence has
sample-size limits that bound what claims can be made.

### N=3 working-app pilots + 1 stress-test pilot

Wonderland has run **three end-to-end pilots that produced
working-app artifacts** and one stress-test pilot that
exposed a substrate gap:

- **mvp** (notebook spec, substrate 0.8.0, $83.78)
  — first Tier 2 completion. Three milestones designed,
  implemented, verified.
- **obol-260522-1** (CRM project, substrate 0.9.0+early
  0.10.0, $92.64) — second Tier 2 pilot, larger scope.
  Surfaced the cross-milestone bleed pattern that drove
  Phase-3 substrate work (T-ab51).
- **mvp-demo-redux** (notebook spec, substrate 0.10.1,
  $30.58) — re-ran mvp's directive on the
  post-T-ab51-T-ab57 substrate. Genuine working-app
  receipt at 36% of the original spend.
- **LDR** (long-distance dashboard, substrate 0.10.2 +
  T-ab62, $19.44) — exposed the hollow-verify gap.
  Pilot completed through to `verified` lifecycle states
  but the deliverables were hollow; T-ab64 then closed
  the gap; re-run pending for working-app receipt status.

Earlier work (P1-P19, including mvp-demo) tested substrate
primitives but didn't reach Tier 2 end-to-end completion.

What N=3 + stress-test means for the claims:

- **The mechanism is predictive even at low N.** Each
  pillar in the evidence chapter is framed as
  "observation + mechanism" — the mechanism makes the
  pillar falsifiable in future pilots even at current
  sample size. The two-pilot cost trajectory ($83.78 →
  $30.58 on identical scope) is mechanism-grounded; if
  future pilots break the trajectory, the mechanism needs
  revisiting.
- **No statistical claims.** The chapter does not frame
  any claim as "across N pilots, X% of the time…" — N=3
  doesn't support that shape; the substrate-version
  variance across the pilots wouldn't support it even at
  larger N.
- **The cross-pilot pattern is identifiable.** Each pilot
  is an independent realization on a different substrate
  version against a different (or in redux's case,
  intentionally-identical) directive. The pattern across
  pilots is mechanism-instantiation, not statistical
  regularity.
- **Future pilots strengthen specific claims.** Each pilot
  adds observations to each pillar; the mechanism gets
  stronger or gets refuted; the pillar's framing tightens.
  The LDR re-run is the next data point.

### One directive class (notebook-shaped)

Both mvp-demo and mvp used variants of the
"personal markdown notebook web app" directive. Cross-pilot
comparison is meaningful (same directive class on different
substrate versions) but the substrate's properties haven't
been tested on:

- Backend-heavy projects (CLI tools, service daemons,
  background workers).
- TUI projects (the workflow already adapts via
  `runtime: tui` framing, but no pilot has shipped one).
- Mobile / desktop app projects.
- Domain-specific shapes (data pipelines, ML systems,
  scientific computing).

the workflow YAMLs are designed to be atomic and
composable; Dodo dynamically chaining workflows for
different work shapes (incident response, security audit,
hotfix) is the architectural direction. But the chaining
infrastructure isn't built yet; the pilots that would
validate cross-shape transferability haven't run.

### One model class (Haiku 4.5)

All claims are at `claude-haiku-4-5-20251001`. The
Haiku-as-thesis-statement framing
predicts identity-and-substrate amplification holds across
model classes, but only one model class has been tested at
pilot scale.

What's been observed qualitatively in development work
(mostly Sonnet-driven coding sessions, not Wonderland pilots):
the substrate primitives work the same way regardless of
model class. What hasn't been measured: whether quality-cost
coupling holds at Sonnet's higher per-token rate, or whether
Sonnet without the substrate matches Wonderland-on-Haiku
output quality (the P7 eval).

---

## §8.6 — Missing rigor

### Comparative experiments — gaps, with planned closures in future work

Two specific comparative gaps weaken the paper's rigor:
the **P7 generic-baseline-vs-identity-native eval** (would
test Corollary 1's "small models outperform via identity"
claim by running matched tasks against a generic-prompt
baseline at the same model class), and **comparison
baselines for code quality** (would test whether
Wonderland-on-Haiku's review-grade output exceeds what
Haiku-without-Wonderland or Sonnet-without-Wonderland
produce on the same directive).

Both are named here as gaps in the publishing-snapshot's
rigor and are developed as proposed experiments in §11
future-work, including the planned harness design, the
comparator-fairness concerns the methodology chapter names,
and the partial-progress single-shot Haiku/Sonnet baselines
that have been run against mvp's directive. The
chapter's claim is therefore bounded: Wonderland-on-Haiku
produces code an independent reviewer reads as competent
and above-average for an MVP at this scale; whether the
character framing produces this beyond what equivalent
operational rules alone would produce is the open question
the Appendix C comparator and a future P7 eval would test.

### Untested hypothesis: Haiku as architecturally optimal

the operator's qualitative read is that Opus might
*under-perform* Haiku on Wonderland — that the substrate's
constraints are calibrated for Haiku's capability shape and
larger models might over-reason against them. This is
**explicitly marked as untested**: *"I've observed that
qualitatively but I don't have, like, data to back me up on
it."*

The chapter should mention this as a hypothesis that
**future comparative pilots could test** rather than as a
claim. Including it in evidence would weaken the paper's
credibility; surfacing it as an open question in
limitations preserves intellectual honesty without
overclaiming.

---

## §8.7 — Tier 2 scope limits

The substrate has now run four Tier 2 pilots (mvp,
obol-260522-1, redux, LDR). Several limitations follow:

### Substrate maturity is per-directive-class

Tier 2 autonomy is claimed at the substrate version each
pilot ran on, on the directive class each pilot exercised.
Notebook-class directives have been validated (redux);
CRM-class directives have been validated (obol-260522-1);
dashboard-class directives produced the hollow deliverable
that exposed the verify gap (LDR; re-run pending on the
post-fix substrate). The chapter does not claim *"Wonderland
achieves Tier 2 autonomy"* as a general property; it claims
*"Wonderland achieves Tier 2 autonomy on directive class X at
substrate version Y."* Each new directive class shape tests
the substrate at a new boundary.

### Operator gate-approver discipline is qualitative

The Tier 2 distinction (gate-approver vs fixer) is named
operationally but isn't yet measured with rigor. Across
the four pilots, documented operator interventions include:

- mvp: 1 substantive scope clarification (full-text
  vs tag-only search), multiple duplicate-feature skips,
  ticket-level scope filtering on M3's megalith feature,
  1 mid-pilot substrate fix.
- obol-260522-1: cost-driver analysis during the pilot
  surfaced cross-milestone bleed; no substrate fix shipped
  mid-pilot but observation drove Phase-3 work.
- redux: operator-noticed verification of working app at
  pilot completion (curl-based CRUD + persistence checks);
  Theseus review post-pilot. Zero mid-pilot substrate
  fixes.
- LDR: operator-commissioned Theseus review post-pilot
  surfaced the hollow-verify gap; zero mid-pilot substrate
  fixes during the pilot itself (the end-to-end gate fix
  shipped between pilot completion and re-run setup).

The categorization "queue decisions ARE gate-approver work"
draws a line that's defensible but not formal. A future
methodology paper might propose a quantitative measure
(intervention frequency × intervention depth × substrate-state
impact); current paper describes the qualitative discipline
honestly without dressing it as metric.

### Mid-pilot substrate fix as Tier 2 violation

Across four pilots, only mvp required a mid-pilot
substrate fix (auto-directive synthesis). The subsequent
three pilots completed without mid-pilot violations,
strengthening the autonomy claim. The methodology chapter
argues mid-pilot fixes are honest documentation of
iterative substrate maturity when they happen; the limitations
chapter notes that **the post-mvp substrate has
matured to the point where mid-pilot violations are no
longer needed across three subsequent pilots**. This is
load-bearing for the autonomy claim — the substrate's Tier 2
readiness has gotten stronger across the pilot trajectory.

---

## §8.8 — Wall-clock time vs other systems

A class of limitation worth naming explicitly because it
distinguishes Wonderland's current scope from adjacent
systems: **Wonderland runs serially.** One milestone at a
time; one feature at a time within a milestone; one ticket
at a time within a feature. The substrate's per-pilot
cost has dropped to a regime where each pilot is affordable
(~$30 / pilot for the redux notebook), but the wall-clock
time hasn't compressed at the same rate. A pilot that
costs $30 still takes an hour to run.

This is what currently bounds Wonderland's competitiveness
on the dimension other autonomous coding systems (Devin,
agent-mode Cursor, Aider runs) optimize for. Devin-class
systems aim to compress wall-clock time, often at the cost
of per-task quality + structured artifacts. Wonderland
aims to preserve the quality + artifact stack while making
per-task cost affordable. The two trade against each
other along orthogonal axes; Wonderland has won on cost
+ quality while not yet competing on wall-clock.

The substrate's typed-state machinery already supports
parallel orchestration in principle: per-milestone memory
branching isolates concurrent milestones; feature-level
lifecycle states are orthogonal across features;
`gates_on_dependencies` in M7 already supports per-ticket
dependency gating. **What's missing is a coordinator that
decides "these N features can run M7 in parallel" based on
the dependency graph, and the orchestration to actually
fan them out.** Filed in future-work; deferred until
template-similarity milestone consolidation (T-ab63) lands
because the two pair multiplicatively (consolidation
maximizes parallelism's surface area).

This limitation is open at publication-snapshot. It is
**not unsolvable**; the architectural pieces are in place;
the orchestration work is scoped and pending. The chapter
documents it as the most prominent wall-clock-time gap to
date, paired with the substrate fix that closes it as the
publication-pending next iteration cycle.

### Engaging the Pareto-frontier critique

A hostile reading of this section would push: *"You've won
on cost + quality, but you haven't competed on the
dimension your nearest competitors optimize for. Isn't this
just a Pareto frontier point, not a Pareto improvement?"*

The honest answer is yes — Wonderland currently occupies a
specific Pareto-frontier corner (high quality + artifact
density, low cost, slow wall-clock) that the Devin /
Cursor-Agent / Aider quadrant doesn't. We are not claiming
Pareto dominance over the Devin-shaped quadrant; we are
claiming the existence of a different optimum on a
different dimension set. **This is a real and bounded claim:
the substrate occupies the cost+quality+artifact-density
corner of agent-system design space, with wall-clock as
the explicit traded-off axis.**

What makes the corner load-bearing rather than uninteresting:

- **Quality + artifact density compound across pilots.**
  The Devin quadrant's wall-clock advantage shrinks the
  more pilots an organization runs against the same
  codebase — every pilot's session log is opaque to the
  next pilot; every architectural decision has to be
  re-derived. Wonderland's typed durable artifacts (ADRs,
  contracts, lifecycle-tracked features, severity-tagged
  reviews) compound across pilots because they're
  designed as persistent state. The first pilot pays the
  artifact-creation cost; the tenth pilot benefits from
  the accumulated context. The Pareto comparison shifts
  across the artifact-density axis as pilot count grows.
- **Cost regime enables operator-in-loop falsification.**
  Per the methodology chapter (§5), the cost regime makes
  failure-exposing pilots affordable. Devin-quadrant
  systems' wall-clock advantage doesn't help if their cost
  regime makes pilot-N-of-twenty unaffordable.
- **The trade is closeable, not architectural.** Parallel
  coordination is the orchestration work that closes the
  wall-clock gap without sacrificing the cost + quality +
  artifact-density wins. The substrate's typed-state
  machinery already supports it; only the coordinator
  scheduling is missing. The current Pareto point is
  Wonderland-at-snapshot, not Wonderland-as-architecturally-
  bounded.

The hostile critique's strongest form ("you're trading off
the dimension that matters") rests on the assumption that
wall-clock IS the dimension that matters, which is true
for some use cases (rapid prototyping, hackathon-style
work, immediate-feedback iteration) and false for others
(long-running engineering projects, codebases that need
audit trails, work that benefits from accumulated context
across pilots). Wonderland's positioning targets the
latter; the Devin-class systems target the former; both
positions are defensible, and the wall-clock-time gap is
the cost of Wonderland's choice rather than evidence that
the choice was wrong.



---

# §9 — Future work

## §9.1 — What counts as future work here

This chapter distinguishes three classes of future work, each
with a different shape and time horizon:

| Class | Shape | Time horizon |
|---|---|---|
| **Near-term substrate evolution** | Filed roadmap items + cluster fixes with clear scoping. The next 1-3 pilot loops. | Weeks to a few months. |
| **Comparative experiments** | Eval harnesses + baseline runs that would close the rigor loop on existing claims. | Cost-bounded; tractable now. |
| **Research-direction questions** | Architectural shifts (Tier 3 autonomy, self-hosting), guest casts that don't yet have workflow shapes, identity engineering as a discipline beyond Wonderland. | Months to years; some genuinely open. |

What DOESN'T go here: items that are limitations (those have
their own chapter); aspirational marketing ("could be
applied to anything"); reactive bug-fixing. Each future-work
item should name what it tests, what it would resolve from
the limitations chapter, and what evidence it would produce
for the paper's next iteration.

The relationship to other chapters:
- **Limitations chapter (§8)** —
  many limitations have filed fixes; the fixes are this
  chapter's near-term substrate evolution section. Limitations
  + future work form a tight pair: limitations name what's
  open, future work names how it gets closed.
- **Substrate evolution chapter (§6)** —
  the chronicle of the iteration cycle that has, to date,
  closed every prior class of limitation it has surfaced.
  Several items previously in this chapter's near-term
  section have closed since the chapter was first written;
  the substrate-evolution chapter documents the closures
  in detail, this chapter cites them briefly as historical
  context.
- **Thesis chapter (§2)** — each
  corollary makes predictive claims; future work includes the
  experiments that would falsify or strengthen them.
- **Methodology chapter (§5)** —
  future work is what feeds the pilot → categorization →
  substrate → next pilot loop's next cycle.

### Status note on cycle progress

This chapter was first drafted at substrate version 0.8.0
when the prior-milestone-awareness cluster (b3f440c8 et al.)
was the load-bearing near-term ask. By substrate version
0.10.2 + T-ab62 + T-ab64, that cluster is substantially
closed (per the limitations chapter's status update on each
item). The chapter has been refreshed to mark closed items
as historical context and to surface the new near-term and
research-direction questions that emerged from the
post-mvp substrate work. The forward-looking sections
(comparative experiments, cross-shape transferability,
identity engineering beyond Wonderland) remain mostly
unchanged because they describe long-horizon work the
substrate evolution has not yet reached.

---

## §9.2 — Near-term substrate evolution

### The prior-milestone-awareness cluster fix (b3f440c8 et al.) — CLOSED

Status update: this near-term item, identified at substrate
0.8.0 (post-mvp pilot), has been closed across the
post-mvp substrate evolution. Per the limitations
chapter, each of b3f440c8 / 4a2597a4 / 81af78f8 / e7d226b8
has been addressed by specific T-ab fixes (T-ab17, T-ab18,
T-ab34, T-ab41, T-ab46, T-ab51 keystone). Validated in the
redux pilot — operator's Tier 2 interventions on duplicate-
feature skips dropped to ~zero, and the per-milestone cost
trajectory ($15.59 → $10.91 → $3.72) is what the cluster
fix predicted: capability milestones building on a stable
foundation, not pressuring against ghost-of-prior-work
deliberation.

The cluster is cited here as **historical context for the
iteration-cycle methodology** — a near-term ask in 0.8.0
became a closed cluster in 0.10.2, with the receipt being
the redux pilot's cost trajectory. The substrate-evolution
chapter documents the per-fix mechanics; this chapter
notes the closure as evidence that the methodology
produces structural closures, not symptomatic patches.

**Paper consequence:** the Tier 2 autonomy claim tightened
as predicted. mvp's "Tier 2 with operator gate-approver
discipline on duplicate-skipping" became, by redux,
"Tier 2 with operator gate-approver discipline on
transition approval only." Three subsequent Tier 2 pilots
have completed without mid-pilot substrate violations.

### Parallel coordination (the wall-clock-time lever)

The substrate currently runs serially — one milestone at a
time; one feature at a time within a milestone; one ticket
at a time within a feature. The cost regime has compressed
to ~$30/pilot for notebook-class directives, but wall-clock
time hasn't compressed at the same rate. A $30 pilot still
takes about an hour to run.

This is what currently bounds Wonderland's competitiveness
on the dimension other autonomous coding systems (Devin,
Cursor Agent, Aider) optimize for. Wonderland has won on
cost + quality + artifact density per agent-tax dollar;
parallel coordination is the move that closes the
wall-clock-time gap.

The substrate's typed-state machinery already supports
parallel orchestration in principle:

- **Per-milestone memory branching** (T-ab8 + T-ab52)
  isolates concurrent milestones — sibling milestones in
  parallel wouldn't pollute each other's deliberation.
- **Feature-level lifecycle states** operate per-feature
  orthogonally across features within a milestone.
- **`gates_on_dependencies` in M7** already supports
  per-ticket dependency gating — tickets whose code
  doesn't depend on other tickets' code can already run
  in parallel within the implement phase.
- **`asyncio.gather` for team_groupings** in meeting.py
  already runs intra-meeting agent windows concurrently;
  the same pattern extends to inter-meeting orchestration.

What's missing is a coordinator that decides "these N
features can run M7 in parallel" based on the dependency
graph, and the orchestration to actually fan them out
across separate runner processes. The work isn't
architectural — it's mechanical. Filed in roadmap;
deferred until template-similarity milestone consolidation
work lands because the two pair multiplicatively
(consolidation maximizes parallelism's surface area).

**What this would test:** whether the substrate's
per-pilot wall-clock time compresses from ~hour to
~10-20 minutes on notebook-class directives. Paper
consequence: closes the most visible competitiveness gap
versus Devin-class systems while preserving the cost +
quality + artifact-density advantages.

### Template-similarity milestone consolidation

Filed observation: when the milestone-plan agent produces
multiple capability milestones with the same architectural
template (consume foundation X → fetch external data →
render on surface Y, with only X/Y/Z varying), the
planner should detect the pattern and consolidate into
one milestone with N features. The LDR pilot's M3 (time),
M4 (weather), M5 (news) cards were the canonical case —
three milestones with identical architectural shape that
should have rolled into one milestone with three sibling
features.

Each near-identical milestone carries fixed-cost overhead
the planner shouldn't be paying:
- 3× milestone-plan reasoning
- 3× tdd-design pass (vs one design pass that produces
  3 features under shared scoping/architecture/composition)
- 3× M9 verify boundary
- 3× memory branch setup

Per-card done-whens become per-feature done-whens. The
consolidation collapses maybe 30-40% of design-side
fixed cost while preserving per-card testability.

**Pairing with parallel coordination:** consolidation
maximizes the surface area parallel coordination applies
to. Sibling features in a consolidated milestone can fan
out concurrently; sibling milestones can fan out but
each carries the planner / design / verify overhead.
Together they buy back the wall-clock-time gap; alone
each is incremental.

**Sequencing:** deferred until parallel coordination
ships. Shipping consolidation alone gets the cost win
but leaves the clock-time win on the table; shipping
both together is the regime change.

### LDR re-run as T-ab64 validation

The LDR pilot exposed the hollow-verify gap (per the
limitations chapter and substrate-evolution chapter
Phase 4). T-ab64 shipped four new end-to-end verification
checks. The next pilot is the LDR re-run on the
post-T-ab64 substrate.

Outcomes:
- **Clean third receipt**: LDR ships at a comparable
  cost to first run ($15-25 range) with the four
  end-to-end gates passing. Becomes the third working-app
  receipt, strengthens the cost-trajectory claim, AND
  demonstrates T-ab64 closed the hollow-verify gap
  operationally.
- **Surfaces new substrate gap**: re-run still produces
  hollow features in a class T-ab64 doesn't catch.
  Becomes another paper-grade substrate finding +
  the next T-ab task.

Either outcome is paper-grade. The re-run is the
substrate-evolution chapter's most immediate next data
point.

### Existing-codebase / change-request feature surface

The substrate currently bootstraps from a directive + a
skeleton. It doesn't yet support "here's an existing
codebase, implement this change request." Adding this
surface would let the substrate handle the most common
real-world software work shape: iterating on existing
software, not green-field MVPs.

The architectural work:
- **Ingestion**: an existing codebase becomes
  artifact-attributed (every existing file is an
  implementation artifact; every existing dependency a
  contract). The substrate's typed-state model has the
  shape for this; what's missing is the import pipeline.
- **Change-request directive shape**: directives currently
  describe what to build; change-request directives
  describe what to change. The milestone-plan agent would
  need a new mode that treats existing-codebase state
  as the foundation other capabilities build on.
- **Verify substrate adaptation**: end-to-end gates
  (T-ab64 et al.) need to handle the case where some
  existing code is allowed to be untested / placeholder
  / etc., while new code must pass the gates.

**What this would test:** whether the substrate
generalizes from green-field MVPs to the messier shape
of real software work. Paper consequence: positions
Wonderland as a substrate for ongoing software work,
not just a Devin-class one-shot tool.

### Feature sequencing with depends_on (837b5bbb)

Operator observation during mvp: *"putting features in
an order would as a byproduct result in more tightly
designed features."* The constraint (an explicit dependency
between features) would force Rabbit during M2 composition to
think about ordering, tightening scope per feature.

This is a Pillar-5 prediction (constraints improve quality):
adding `Feature.depends_on: list[feature_slug]` should both
tighten output AND lower per-feature cost. The pilot that
ships it would test the prediction.

Related: extends `existing-code-awareness` block — design for
feature N could see code from N's dependencies (which have
already shipped). Partially resolves b3f440c8 (Caterpillar's
M8 could reason "feature N depends on X which is shipped").

### Persona-anchoring in milestone-plan (79ef174a)

mvp surfaced this: Alice gets confused about persona
during milestone-plan because the meeting has no persona-anchor
block (tdd-design's entry meeting has one; milestone-plan
doesn't). Small directive edit, substrate-side helper
mirroring the existing pattern. Belongs in next p20 follow-up
batch.

### Frontend test enforcement loop

Per the code-quality artifact: `vitest` is installed but zero
frontend tests exist because there's no substrate enforcement
loop. The shaped fix:

- M9 gains an `npm_test` build-check parallel to
  `pytest_passes` + `npm_build`.
- M7's directive gains an explicit requirement that the
  Hatter scenarios for this ticket exist as runnable tests
  in the appropriate test directory.

**What this would test:** whether the substrate's
constraint-improves-quality property extends to the test
discipline domain. Backend tests get written because
`pytest_passes` exists; the same enforcement loop on frontend
should produce equivalent discipline. If it does, that's
additional Pillar-5 evidence.

### Cross-endpoint scenario coverage as Hatter M6 prompt

The C2 finding from the code-quality artifact (revision_id
serialization mismatch across endpoints) is invisible to M8's
per-file coherence review. The right-sized fix is at M6:
Hatter's scenario-generation prompt explicitly includes
**cross-endpoint round-trip scenarios** as a first-class
class — "client lists notes, picks one's revision_id, PUTs
with that revision_id, expects 200."

**What this would test:** whether C2-class bugs become
substrate-visible at M6, surface as failing tests at M7, and
get fixed before reaching the verified artifact. The
underlying claim is that the M6 → M7 → M9 loop can catch
cross-endpoint behavioral bugs if Hatter generates the right
scenarios.

---

## §9.3 — Comparative experiments (the rigor expansion)

The evidence chapter is honest about what hasn't been
measured rigorously. Several comparative experiments would
close that loop. Each is cost-bounded and tractable to run
now.

### One-sentence directive pilot (near-term)

The pilots to date have used operator-written directives
(~80 lines each — full specifications covering capabilities,
stack constraints, non-goals, success criteria). The
substrate has not been tested on a genuinely short directive
("build me a markdown notebook" — one sentence, no spec). A
common reader intuition is that working SDLC substrates
should be able to operate from very short prompts and have
the interview / discovery workflow elicit the rest from the
operator. Wonderland has the interview workflow shape
(`discovery.yaml`) to support this, but the path hasn't been
exercised end-to-end at one-sentence-directive scale.

The honest scope-narrowing this implies: the receipts in §7
demonstrate Wonderland operating on
substantially-specified directives, not on one-sentence
prompts. Whether the substrate's discovery workflow can
recover the operator's intent from a one-sentence prompt and
ship comparable working artifacts at comparable cost is an
**open question, not a demonstrated capability.**

The near-term commitment: run a one-sentence-directive pilot
on the same notebook task ("build a personal markdown
notebook web app") and publish the receipt — discovery
artifact length, milestone-plan emission, cost-per-feature
trajectory, shipped-artifact quality against the receipts
the long-directive notebook pilots produce. The operator
expects either (a) the discovery workflow elicits enough
spec from interview that the rest of the pipeline operates
normally, in which case the abstract's directive-size claim
generalizes meaningfully, or (b) the substrate produces
under-spec'd or off-target artifacts because the
discovery workflow doesn't yet do the lift required to
compensate for spec absence — in which case the
short-directive scope becomes an honest published ceiling on
the substrate's autonomy and a load-bearing direction for
discovery workflow improvements. Either outcome publishes.

### Second independent cold review on redux (near-term)

The mvp pilot received an independent cold review at the
shipped-artifact level — operator-commissioned but
read-by-someone-other-than-the-substrate-builder, in the
sense that the reviewer hadn't been involved in the
substrate's design or evolution. That cold reviewer
generated the "competent, above-average code for an MVP"
artifact-quality framing the limitations chapter relies on.

**Redux + LDR have not received the same treatment.** Per
the methodology chapter's bounded-independence
acknowledgment (§5 *"Theseus reviews as structured
falsification"*), the operator's Theseus subagent is
adversarially-framed and schema-disciplined but is not
equivalent to a second-pair-of-eyes review. A near-term
commitment: commission an independent cold review on the
redux shipped artifact, with the same framing the mvp cold
review used (independent reviewer reads the working app
fresh, files findings, grades artifact quality against
their professional reference frame). The outcome publishes
as a follow-up artifact regardless of finding pattern.
Estimated cost: 1-2 hours of an independent reviewer's
time + their reading discipline; no LLM spend.

This is the cheapest near-term move that tightens the
operator-in-loop falsification claim's bounded-independence
gap. The longer-term move (a second-author / external
research-group adoption + replication) is a research-program
question rather than a near-term action.

### Head-to-head measurement on a multi-agent framework (ChatDev on the notebook directive)

The related-work chapter (§10.1) compares Wonderland's
artifact set to ChatDev's *as characterized from ChatDev's
published documentation* — not as measured under matched
conditions. The honest tightening: run ChatDev on
Wonderland's mvp-redux notebook directive, count its actual
artifact output, measure its actual cost, and report the
artifact-density-per-agent-tax-dollar comparison as
measurement rather than characterization. Cost-bounded:
ChatDev's published sub-$1 / sub-7-minute claim sets the
upper bound on what running the comparison would cost.
Estimated effort: ~3-5 hours operator time (environment
setup + run + artifact-set audit) + ~$1-2 LLM spend.

Either outcome publishes. If ChatDev produces 5+ artifact
types at sub-$1 and the artifact-density-per-dollar metric
favors ChatDev on raw count, the related-work paragraph's
qualitative argument (structural richness, citation chains,
cross-pilot accumulation) becomes the only defensible move
and the quantitative-density framing should be retired. If
ChatDev produces meaningfully less than its published claim
suggests on this specific directive, the head-to-head data
strengthens the artifact-density framing meaningfully. The
work is small; the rigor return is high.

### Single-shot Haiku / Sonnet baselines for code quality — PARTIALLY DONE

Status update: the single-shot and Claude Code baselines
have been partially run. The
[comparison-baselines analysis](https://github.com/KohlJary/wonderland-ai/blob/main/paper/artifacts/comparison-baselines/README.md)
documents what shipped from each baseline against the same
notebook directive that mvp + redux ran. Findings include
the
[adversarial-review-of-baselines](https://github.com/KohlJary/wonderland-ai/blob/main/paper/artifacts/comparison-baselines/adversarial-review-of-baselines.md):
30 blocker-class bugs across 4 single-shot baselines that
ship code without any review pass. Categories match what
Caterpillar catches in the Wonderland pilots.

What's still open from this section:
- **Sonnet single-shot** at full scope — partial coverage
  exists; a clean full-directive run on Sonnet 4.6 would
  close the comparative loop at the model-class boundary.
- **OSS markdown-notebook contrast** — still pending; a
  comparable-scope OSS project for absolute-quality
  comparison.
- **Cross-substrate-version baseline contrast** — would
  re-run a prior-substrate-version pilot on a current model
  to isolate substrate-version from model-version effects.

**What's been confirmed:** single-shot baselines do not
produce working code at the apparent-scope of the directive
— per the operator's mid-investigation correction,
*"Single-shot does not produce working code we found on
closer inspection of our baselines, remember?"* The relevant
competitor class is Devin-shaped agentic systems, not
single-shot inference. Section below.

### Agentic-vs-agentic baselines — artifact density per agent-tax dollar

The single-shot baselines above test the *cheapest possible
competitor* to Wonderland. The category that's structurally
closer to Wonderland but hasn't been probed is *other
agentic / multi-step coding systems*: Devin, Cursor Agent,
Aider, Claude Code used as a project orchestrator. These
systems share Wonderland's property of paying an agent
tax — VM startup, codebase exploration, planning passes,
test iteration, multi-turn deliberation — that scales with
agent structure, not task complexity. On a small directive,
all of them look bloated relative to single-shot for the
same category-level reason. (See the
[comparison-baselines analysis](https://github.com/KohlJary/wonderland-ai/blob/main/paper/artifacts/comparison-baselines/README.md)
for the framing of why notebook-class inefficiency is a
category property, not a Wonderland-specific weakness.)

**Shape of the eval:** Run Devin (or Cursor Agent, or Aider,
or Claude Code-as-orchestrator) against the same notebook
directive. Measure not just cost + working-code, but
*artifact density per dollar* — what reusable byproducts
does each system produce alongside the code? Wonderland's
hypothesis is that within the agentic-system category, the
substrate produces structurally more artifacts (typed
tickets / features / stories, ADRs, contracts, FindingKind-
typed reviews, 5-hop decision trails, JSONL audit logs) for
the same agent-tax dollar than session-log-only systems
do. Most agentic-coding evaluations measure "did the code
work" and "how much did it cost"; neither captures what
the tax pays for in terms of downstream maintainability.

**Why this matters for the paper:** the comparison-baselines
analysis's biggest framing blind spot is that it positions
Wonderland against the cheapest baseline. A reader sympathetic
to agentic coding (the right audience for "you *can* do this")
will reasonably ask: *"OK, but what's Wonderland buying me
relative to Devin or Cursor Agent, not relative to
`claude -p`?"*  The answer is artifact density per dollar of
overhead you're already paying — which is a defensible claim
once measured, but which the current data doesn't
substantiate. Filing as a near-term comparative pilot rather
than long-horizon research because the eval design is
tractable: one notebook directive, four agentic systems, 4-8
hours of operator time per system, ~$50-200 total spend
across all of them.

**What this tests:** that Wonderland's structural artifact-
production isn't redundant with what any agentic coding
system already produces. If Cursor Agent's session logs +
plan files cover 80% of Wonderland's artifact trail, the
substrate's distinctive value compresses. If they cover 20%,
the typed-artifact thesis holds at the comparative level.

### P7 generic-baseline-vs-identity-native eval

The thesis chapter's Corollary 1 (small models outperform via
identity) makes a specific predictive claim. The P7 eval
harness would test it rigorously: same task, same model,
two conditions (generic prompt vs identity-native
constitution).

**Shape of the eval:** matched-on-task comparisons across a
batch of representative directive shapes (CRUD endpoint
implementation, story decomposition, code review, test
scenario generation). Each task gets graded on a rubric
(correctness, edge-case coverage, named tradeoffs, etc.).
Comparison: identity-native vs generic-prompt-on-same-model.

**Roadmap item exists** (P7); harness not built. The
limitations chapter is explicit that until P7 ships, the
strongest Corollary 1 claim is "Haiku produces work
consistent with what identity-bearing-the-work would
predict," not "Haiku outperforms generic-prompt-on-Haiku."

**The methodological problem** discussed in §5.X
(comparator-fairness) applies to P7's design too: any
specific "generic prompt" baseline lives on the
strawman-to-convergent spectrum. A version of P7 that
handled the spectrum honestly would pre-register multiple
"generic" conditions at different prompt-detail tiers and
report results across all of them — letting readers
calibrate the spectrum themselves rather than collapsing
it to a single comparison.

### Caterpillar comparator experiment (pre-registered, ready to execute)

A narrow agent-level hygiene check, pre-registered in
Appendix C: a single agent (Caterpillar), single fixed task
(M8 review of a shipped feature with a known cross-cutting
bug), two conditions (full constitution vs literary-register-
stripped operational-rules-only version), six metrics, three
pre-registered hypotheses with interpretation rubric. ~$5-10
LLM spend, ~5-7 hours operator time. **This experiment is
not load-bearing for the unified claim §2 + §5 develop**
(see Appendix C's scope qualification); it is a hygiene
check on one component of one agent's constitution.

The experiment was scoped during this paper's preparation and
**explicitly held out of this paper because executing it would
generate enough material to require its own analysis chapter,
splitting the paper's focus** on substrate evolution and
cost-trajectory findings. The design is ready for execution by
this paper's operator (in a follow-up paper) or by any
researcher who picks it up. Both constitutions are committable
to the repo; the harness is small (the substrate already
supports `load_constitution(name)`); the pre-registered rubric
defeats post-hoc rationalization that would otherwise
contaminate the result.

The pre-registered design + both constitutions ship in the
repository; anyone — including a hostile reviewer — can
execute it. Holding the experiment indefinitely without
execution would itself become evidence against the paper's
claim; the paper's bet is that execution happens and the
result, whatever it is, sharpens rather than collapses the
identity-engineering framing.

This is a *narrow* agent-level hygiene check on one element
(literary register), one agent (Caterpillar), one task
(M8 review), one model class (Haiku 4.5). It does not settle
the unified claim §2 develops — the unified claim's
falsifier is framework-scope (the combined
artifact-density + characteristic-failure-mode-discipline +
cost-trajectory test §2 names), not agent-scope. Appendix C
contributes to identity-engineering hygiene at the
constitution-authoring level; it does not validate or
refute the architectural claim about
identity-as-organizing-principle.

**Why this matters as future work**: handing the reader an
executable pre-registered comparator design — with both
constitutions specified, the fixed task chosen, the rubric
thresholds written before any runs — is itself a research
contribution. Most papers that defer comparator work to
"future work" defer it indefinitely. This paper defers
specifically and tractably: anyone can execute Appendix C
against the current substrate and report results that update
the paper's identity-engineering framing per the pre-registered
rubric.

### Design-all-first vs interleaved comparative pilot (68a882b3)

Current Wonderland pattern (interleaved): milestone-plan →
design M1 → implement M1 → design M2 → implement M2 → ... →
integration. Proposed alternative (design-all-first):
milestone-plan → design ALL milestones → implement M1 → M2
→ ... → integration.

Run the same project (the notebook directive) both ways;
compare cost, quality, wedge count, operator-intervention
frequency.

**Hypothesis:** design-all-first addresses b3f440c8
(Caterpillar sees full sibling-feature landscape during
review) and gives cleaner cross-feature consolidation, but
loses the iterative-discovery feedback loop where impl
reveals design needs.

**Paper deliverable:** A/B comparative cost + quality data
for the two sequencings, with discussion of which pattern
works better for which project shapes. This is a comparative
pilot that produces NEW evidence; not just baselining
existing claims.

### Cross-model comparative pilots

The Haiku-architecturally-optimal hypothesis
is currently UNTESTED. The operator's qualitative read: Opus
might *under-perform* Haiku on Wonderland because the
substrate's constraints are calibrated for Haiku's
capability shape.

The test: run mvp-demo3 (same notebook directive, same
substrate version) on Opus instead of Haiku. Compare cost,
quality, wedge patterns, character behavior.

**Hypothesis directions** (any of which would be paper-worthy):
- Opus performs better than Haiku (the conventional
  expectation — larger model, more capability).
- Opus performs equivalently to Haiku at higher cost (the
  "identity does the work, model class doesn't matter as
  much" prediction).
- Opus performs WORSE than Haiku (the operator's qualitative
  observation — Opus over-reasons against constraints
  calibrated for smaller capability).

Each outcome is informative. The third would be the most
surprising and the most thesis-relevant.

---

## §9.4 — Cross-shape transferability

Three of the four completed Tier 2 pilots used variants of
the notebook-class directive (mvp + redux = same directive;
mvp-demo = early partial pilot on similar shape). obol-260522-1
extended the substrate to a CRM project — meaningfully
different scope, but still web-app shaped (fullstack-fastapi-
react skeleton). LDR added dashboard + external-API-integration
shape (auth + multi-card dashboard + 3 external API
integrations + timezone math), still on the same skeleton.

The substrate's properties have been tested on three
sub-shapes of the same broad category (fullstack-fastapi-react
web app: notebook, CRM, dashboard). What still hasn't been
tested:

### Different directive classes

- **CLI tools** — the `runtime: cli` substrate framing
  exists; the M5 contract-negotiation directive translates
  Tweedle roles for the runtime; no pilot has shipped one.
- **TUI projects** — same as CLI; substrate is ready, no
  pilot.
- **Backend-heavy projects** (services, daemons, background
  workers) — no UI surface; would test whether the
  full-stack-frontend-heavy pilot data generalizes.
- **Mobile / desktop apps** — substrate isn't yet shaped for
  React Native / Electron / native; would require new
  skeleton + workflow adaptations.
- **Domain-specific shapes** — data pipelines, ML systems,
  scientific computing. These have different artifact
  shapes (notebooks, DAG configs, etc.) that may need new
  agent identities or workflow shapes.

The forward question: **does the substrate transfer cleanly
across directive classes, or does each class need
substantial adaptation?** Current architecture predicts
clean transfer (workflows are atomic; characters are stable;
runtime field adapts roles); the prediction hasn't been
tested at pilot scale.

#### Pre-registration: next-pilot directive-shape commitment

To turn directive-shape generalization from "future work"
into a falsifiable next-pilot prediction, the operator
pre-registers: **the first pilot shipped after this paper's
publication snapshot will use a directive class outside
fullstack-fastapi-react** — most likely a CLI tool or a
backend-only service (both have substrate framings ready;
neither has been pilot-tested). The operator commits to
publishing the post-pilot artifact (cost trajectory + scope
+ failure-class surfacing) against the falsifier framing in
§5, regardless of outcome. If the substrate transfers
cleanly, the directive-shape generalization claim gets a
data point. If the substrate requires substantial
adaptation (new agent identities, fundamentally different
workflow shapes), the bounded-to-fullstack-fastapi-react
framing the paper currently maintains becomes the published
ceiling on substrate generality at this iteration of its
life. Either outcome publishes; the pre-registration is the
discipline.

### Different model classes

Wonderland defaults to `claude-haiku-4-5-20251001`. The
substrate has been smoke-tested on Sonnet during development
work (mostly coding sessions) but no full pilot has run on
non-Haiku. The cross-model comparative pilots above (Opus
on the same directive) start here; the deeper question is
whether non-Anthropic models support the same
identity-engineering discipline.

The architectural prediction: identity engineering works on
any model that can sustain in-character reasoning over long
contexts. Practically, this means models with strong
constitution-following at the system-prompt level. The test
hasn't been run; it's a future pilot's input.

### Atomic workflow composability

the architectural direction is **workflows as atomic,
composable units that Dodo dynamically chains at runtime**.
Pattern chaining in a music sequencer is the right metaphor.
The build pipeline (canonical/tdd) is one chain; an
incident-response pipeline (Holmes/Watson finding /
verifying bugs, Moriarty red-teaming) would be a different
chain Dodo dispatches when something goes wrong.

Most directives mix and match — a feature with a
security-critical surface might chain
`tdd` → `holmes-watson-review` → `moriarty-redteam` →
`caterpillar-final`.

**Roadmap item 29497820** (Dodo as dynamic meeting
orchestrator) is the architectural ask. The unit of
composition becomes the workflow, not the meeting. Workflows
become atomic via the existing YAML format; Dodo gains
selection + chaining logic.

What this would test: whether the substrate scales to
arbitrary multi-workflow compositions, or whether
cross-workflow seams introduce new failure modes.

---

## §9.5 — New cast capabilities

### Holmes / Watson workflows (incident response, security audit, codebase backfill)

Per the cast walkthrough (Appendix B): Holmes +
Watson is the framework's first guest cast — asymmetric pair
(Holmes leads investigation, Watson translates +
interrogates). Constitutions shipped; no workflow yet convenes
them.

The anticipated workflow shapes:

- **discovery-backfill** — Holmes infers requirements from
  existing project state rather than interviewing the
  operator. Use case: an existing codebase that needs
  Wonderland framing added. Watson translates Holmes's
  findings into the requirement artifacts that
  milestone-plan can seed from.
- **incident-investigation** — Holmes reads incident
  artifacts (logs, telemetry, recent commits); Watson
  translates findings for Queen (security framing) and
  Tweedles (remediation work).
- **security-audit** — Holmes maps the codebase's actual
  attack surface; Watson translates for Queen's threat
  modeling. Output: an updated Threat Garden + Queen
  rulings on found gaps.

Each workflow's design is a separate piece of work. The
Watson-as-translator role is constitutive of the workflow's
output shape (different receiving agents → different
translations); the architecture is ready.

### Other guest casts that might emerge

The Holmes/Watson asymmetric-pair model opens a door. Other
shapes might fit:

- **Moriarty** (mentioned in the workflow-variants memory)
  — a red-team adversarial character. Pairs with Queen for
  security work; could pair with Hatter for adversarial
  scenario generation in particularly safety-critical code.
- **A historian character** — reads git history + analyses/
  + memory observations for cross-pilot trend analysis.
  Would help long-running projects develop a sense of
  trajectory beyond individual pilots.
- **A documentation specialist** — translates the artifact
  trail into operator-facing prose (the project currently
  uses analyses/ for this; a dedicated character with §IV
  shape constraints might produce different shape).

These are speculative; each would need a constitution shaped
around its characteristic failure mode + persistence
artifact + relational defaults. The architectural commitment
is that adding a character has cost (per the cast
walkthrough §"The cast is small on purpose"), so each
addition should earn its slot rather than fit aspirational
roles.

### Pair protocols as a primitive

The Tweedle pair (symmetric) and Holmes/Watson pair
(asymmetric) are the only two pair-shaped identities so far.
The architectural direction worth exploring: **pair protocols
as a first-class primitive**. Other shapes might fit:

- **Mentor / apprentice** — asymmetric pair where the
  apprentice is in-character learning the mentor's
  discipline. Could model character evolution over long
  projects.
- **Adversarial pair** — Hatter + Queen as a unit, with the
  explicit role of producing devil's-advocate review on
  designs.
- **Lateral peer pair** — two agents of equal authority
  whose disagreement is the work (similar to Tweedles but
  for different domains, e.g., the architect + the
  reviewer arguing over a structural choice).

The pair-protocols infrastructure
(`tweedle_pair_protocol.md`, `baker_street_protocol.md`)
exists; what's missing is the substrate machinery that lets
pairs be a configurable choreography element in workflows.

---

## §9.6 — Architectural research questions

The project has accumulated a set of longer-horizon research
questions — substrate self-modification (a forward Tier 3 where
agents propose and ship substrate fixes during pilots rather
than between them), self-hosting (using Wonderland to build the
next version of Wonderland), multi-operator concurrency, the
interviews-and-milestones layer as a long-running collaboration
substrate, identity-engineering instantiations in non-software
domains (medical, academic, engineering casts), and the
methodological work of constructing fair comparator frameworks
for identity-engineering claims (per §5.X). These are
project-internal research notes rather than experiments this
paper proposes for the next 6-12 months; they appear in the
[project memory](`memory/MEMORY.md`) and roadmap and would be
the natural research agenda for whoever picks up identity
engineering as a discipline.

The paper does not develop these further because doing so would
risk converting "this paper opens up future research directions"
into "this paper sketches several research papers it does not
write." Per the editor-reviewed scoping discipline, we name the
directions exist and point at the artifacts that develop them
internally, rather than expanding the paper into a research-
agenda document.



---

# §10 — Related work

> Positioning Wonderland against the three existing field
> categories the substrate sits between (multi-agent frameworks,
> workflow engines, autonomous coding systems), plus a brief
> note on the broader multi-agent and software-engineering
> literature the substrate inherits from.

Wonderland makes architectural commitments that don't quite fit
any of the three field categories its surface features evoke.
This chapter walks each category, names what we share with it,
and names what makes the substrate distinct. The introduction
(§1.2) already named the three categories briefly; this chapter
develops the comparison in enough depth that a reader familiar
with adjacent work can see where Wonderland sits.

The shape of the argument: each category captures one
load-bearing property of Wonderland but misses one of the
others. **Multi-agent frameworks** capture LLM-driven
deliberation but not durable typed state. **Workflow engines**
capture typed state with lifecycle but assume deterministic
transitions. **Autonomous coding systems** capture
prompt-to-running-app generation but treat the agent layer as
opaque and don't produce structural artifact trails. Wonderland
combines properties from all three; "substrate" is the house
word for the missing intersection.

---

## §10.1 — Multi-agent frameworks

The closest neighbors to Wonderland's agent side are the
LLM-driven multi-agent frameworks that emerged in 2023–2024.
Each frames orchestration as agent conversations; each treats
typed state as scratch space the agents read and write
between turns; each centers agents as the primary unit of
the system.

### AutoGen [AutoGen]

Microsoft Research's AutoGen, released August 2023, is the
canonical multi-agent conversation framework. AutoGen
instantiates agents with system prompts and tools, then
coordinates conversations through configurable group-chat
patterns. The framework's foundational claim — *"the next
generation of LLM applications will use multi-agent
conversations"* — predicts the multi-agent moment Wonderland
also occupies, but the architectural choice differs sharply.

AutoGen's agents are **functions parameterized by system
prompt**. An `AssistantAgent` is defined by its prompt; a
`UserProxyAgent` by its prompt; their interaction by the
group-chat manager's prompt. Wonderland's characters are
**constituted identities with named characteristic failure
modes** (§4) — Alice isn't a parameterized assistant agent
configured with "be a product owner"; she's a load-bearing
identity whose §VIII failure modes are part of who she is
across every meeting she attends.

What we share with AutoGen: the recognition that
multi-agent coordination produces work shapes single-agent
inference can't. What we don't share: the framing of agents
as parameterized functions vs. constituted characters. The
substrate-side commitment Wonderland adds (state is primary;
agents are transition functions over typed durable artifacts)
has no analog in AutoGen — AutoGen's state lives in
conversation history, which is ephemeral by design.

### MetaGPT [MetaGPT]

MetaGPT's contribution is **Standardized Operating Procedures
(SOPs) encoded into prompts** — the framework prescribes
explicit role definitions, task decomposition workflows, and
mandates modular outputs (PRD, design doc, code) as the agent
interface. MetaGPT's claim is that the SOP-as-prompt approach
"empowers agents with domain expertise comparable to human
professionals."

The substrate-style discipline overlaps with Wonderland's
constitutions: both encode role-specific behavior into
prompt-side structure. The difference is the locus of
enforcement. MetaGPT's SOPs are **agent self-enforced** —
the prompts tell the agent what to produce in what shape;
the agent decides whether to comply. Wonderland's substrate
enforces shape at the **system level** — `allowed_decisions`
strips unauthorized artifacts at snapshot time;
`primary_speaker` filters mean only one agent's emissions of
a given kind survive; lifecycle state machines mean
transitions can only fire when their invariants hold (§3,
§6). The agent's prompt-side discipline is one layer; the
substrate's structural enforcement is another.

**Engaging the hostile reading:** a skeptical reviewer
familiar with MetaGPT would push: how much of Wonderland's
substrate enforcement is doing work MetaGPT's SOPs couldn't
do with sufficient prompt discipline? The answer matters
because if SOPs could carry the load, the substrate is
over-engineered.

The empirical answer the substrate evolution chapter (§6)
develops: in our iteration cycle's experience, the load-
bearing structural invariants the substrate ended up
encoding are precisely the ones prompt discipline could
not enforce reliably. Examples that surfaced concretely:

- **Cross-milestone bleed (closed by T-ab51).** Prompt
  discipline can tell an agent "only consider M2's
  requirements when designing M2." The agent reads the
  prompt and intends compliance. But when the agent's
  seed pool surfaces a requirement from M1 — because the
  resolver doesn't filter by active milestone — the
  agent processes what it sees. Prompt discipline cannot
  intercept the read; the substrate's resolver can. This
  isn't a hostile gotcha; it's a structural property of
  agent runtimes that read context they're given.
- **Hollow features (closed by T-ab64).** Prompt
  discipline can tell agents "make sure the frontend's
  API calls resolve to real backend routes." The agents
  produce code that compiles and passes tests. The
  frontend calls `/api/news`; the backend ships without
  a news router; both agents are individually compliant
  with their prompts; the hollow feature ships. Prompt
  discipline can't enforce contract-seam coherence
  across agent boundaries because no single agent has
  the cross-cutting view; the substrate's
  `api_call_resolves_to_route` check can, because it
  reads both surfaces structurally at M9.
- **Citation integrity (the phantom-citation filter).**
  Prompt discipline can tell agents "cite real upstream
  artifacts; don't invent slugs." Agents intend
  compliance; sometimes they slip; on the slips, the
  downstream substrate would carry the phantom citation
  through to feature emission. The substrate's
  citation-resolver filter rejects emissions with
  unresolved citations at write time — structurally
  preventing what prompt discipline asked for but
  couldn't enforce.

The pattern across all three: **prompt discipline operates
on the agent's intentions; substrate enforcement operates
on the substrate's typed-state transitions.** When the
transition can fire on data that violates the prompt's
discipline, prompt discipline alone isn't sufficient. The
substrate isn't replicating MetaGPT's prompt work; it's
catching what prompt work can't catch.

Could MetaGPT in principle add substrate-style enforcement
on top of its SOPs? Yes — and if it did, MetaGPT would
converge with Wonderland's architecture. The distinction
isn't "MetaGPT's prompts are bad; Wonderland's are good";
it's "agent-self-enforcement is necessary but not
sufficient; substrate enforcement is what makes the
discipline operational at scale."

MetaGPT also doesn't have a durable typed-artifact layer
that survives across runs. The artifacts it produces are
files; the lifecycle state of those artifacts (proposed,
in_design, designed, in_progress, ready_for_review,
verified) is not part of MetaGPT's model. Wonderland's
substrate makes lifecycle the load-bearing primitive (§3.3,
§6). This is the architectural addition that lets the
iteration cycle accumulate across runs — every Wonderland
pilot's artifacts are durable input for the next pilot;
MetaGPT pilots restart fresh each time.

### ChatDev [ChatDev]

ChatDev's contribution is the **chat-chain coordination
pattern** — agents take turns in a strict sequence, each
agent's output becoming the next agent's input, with
"communicative dehallucination" patterns to keep agents
grounded. ChatDev demonstrated remarkable efficacy:
end-to-end software generation in under seven minutes at
less than $1 cost.

ChatDev and Wonderland are in similar territory — both ship
working code from a directive on a multi-agent orchestration.
The differences are revealing. ChatDev's chat-chain is
**linear and stateless** between iterations; Wonderland's
substrate is **graph-structured and stateful across runs**
(features have lifecycle states, runs can pick up where
prior runs left off, memory branches per milestone). ChatDev
optimizes for end-to-end speed in a single session;
Wonderland optimizes for cross-run continuity, durable
artifact trails, and operator-in-loop falsification (§5).

The cost framing also reveals the difference. ChatDev's
sub-$1, sub-7-minute generation hits "demo-shape" software —
small applications, single session, no operator
intervention loop. Wonderland's notebook directive ships at
$30.58 for a working full-stack app with 22 backend tests, a
verified frontend build, persisted SQLite storage, full
CRUD, search, tag filter, ADRs, contract notes, severity-
tagged tests, audit logs, and a Theseus-reviewed code
quality assessment (§7, §8). The cost gap is what the
substrate buys — artifact density per dollar of overhead
the agent tax was going to consume anyway.

**Where the artifact-density framing sits:** §1.1's
positioning move proposed *artifact density per agent-tax
dollar* as a metric for evaluating agentic SDLC systems
beyond *"did it work + how much did it cost."* We have not
operationalized this metric as a head-to-head measurement
against ChatDev (or any other multi-agent framework) on
matched conditions — that measurement is named in §9 as
near-term comparative work. The contrast Wonderland's
substrate offers is therefore better made qualitatively
than quantitatively at publication snapshot.

The qualitative contrast: ChatDev's published artifact set
(requirement specification, system design document, code
files, test scaffolding, session log) is markdown prose +
conversation transcript. Wonderland's substrate produces
the same conceptual artifact kinds plus several Wonderland
introduces (typed requirements with axis + confidence +
provenance + GUID; milestones with `done_when` and `kind`;
lifecycle-tracked stories/features/tickets with citation
chains; ADRs with explicit tradeoffs; contract notes per
stack-span seam; review artifacts with FindingKind-typed
findings + verbatim quotes + file:line citations; an
append-only state-transition audit log; per-agent
persistence files that survive to subsequent pilots).

The structural difference is the load-bearing one: a
ChatDev requirement spec is markdown prose; a Wonderland
requirement is a typed `RequirementPayload` citable from
downstream artifacts that the substrate's read-time filter
respects. A ChatDev session log is a flat conversation
transcript; a Wonderland audit log is a state-transition
stream with each transition citing the prior state's
GUIDs. The *types* the substrate enforces are what produce
the cross-run accumulation property Wonderland claims;
flat prose artifacts compose differently and accumulate
differently.

Whether the structural-richness difference is worth the
cost difference is a downstream-use question: for a
throwaway demo, lighter-weight artifacts suffice; for a
project that will iterate across many pilots, accumulate
audit history, need maintainability across team changes,
or feed back into the next pilot's design context,
typed-state artifacts compound in ways flat prose
artifacts don't. The Pareto comparison is per-pilot at
low pilot counts; per-program at high pilot counts. The
head-to-head measurement that would let a reader pick a
side on a specific directive is filed as future work.

This is the "artifact density per agent-tax dollar"
framing operationalized as a *qualitative* comparator.
A reader who adopts the framing — even without adopting
Wonderland's specific implementation — has a structural
question they can ask of any agentic-coding system
beyond *"did it work + how much did it cost."*

### LangChain and LangGraph [LangChain] [LangGraph]

LangChain (October 2022) and its more recent state-aware
sibling LangGraph (2024) are the dominant production-oriented
agent frameworks. LangGraph's pitch — *"low-level
orchestration framework for building, managing, and deploying
long-running, stateful agents"* — comes closest of any
multi-agent framework to Wonderland's typed-state commitment.
LangGraph offers durable execution, human-in-the-loop, and
graph-based agent workflow representation.

The architectural overlap is genuine. LangGraph's "stateful
agent" framing is in the same neighborhood as Wonderland's
"agents as transition functions over typed durable
artifacts." Both recognize that production agent applications
need state that survives crashes, failures, and operator
interventions.

The distinction is at the artifact layer. LangGraph models
**workflow state** (the graph node positions, the message
history, the tool-call results) as the durable primitive.
Wonderland models **typed domain artifacts** (requirements,
stories, features, tickets, milestones, contracts, reviews,
implementations) as the durable primitive — each with its
own lifecycle state machine, citation chain invariants, and
type-specific operations. LangGraph could in principle host
Wonderland-shaped artifact types; nothing prevents a
sufficiently-disciplined LangGraph application from defining
them. The difference is whether the artifact layer is
**load-bearing infrastructure** (Wonderland) or
**application-defined data** (LangGraph as currently
deployed).

A future Wonderland implementation could plausibly ship as a
LangGraph application layer rather than as standalone code;
the architectural commitments would translate. The substrate
chapter (§6) documents the structural invariants Wonderland
would need any host framework to enforce; mapping them onto
LangGraph's state model would be an implementation exercise,
not an architectural shift.

### CAMEL [CAMEL], AutoAgents [AutoAgents], AgentVerse [AgentVerse]

CAMEL (2023, *Communicative Agents for Mind Exploration*),
AutoAgents (2023), and AgentVerse (2023) are research-side
multi-agent systems that share a structural commitment worth
contrasting against Wonderland. CAMEL pairs a user-agent and
an assistant-agent in **role-playing dialogue** to decompose
tasks; AutoAgents **dynamically synthesizes** specialized
agents for a given task at runtime; AgentVerse demonstrates
**collaborative multi-agent simulation** with expert
recruitment, decision-making, and action phases. All three
established important results — CAMEL on role-conditioning
producing different solution paths, AutoAgents on
dynamic-roster generation reducing prompt engineering load,
AgentVerse on multi-phase coordination outperforming flat
collaboration.

The structural gap they share with the systems above:
**the cast and its coordination are runtime constructions**,
not durable artifacts. CAMEL's role pair exists for the
duration of a session; the next session may instantiate
different roles for the same task. AutoAgents' synthesized
specialists are generated per-task and discarded. AgentVerse's
expert recruitment runs at task start. None of the three
maintains a stable, named cast across runs whose individual
behavior accumulates into the kind of architectural identity
Wonderland's constituted characters embody — where a reader
of a Wonderland pilot can predict, before reading the
artifact, what Caterpillar will object to, what Alice will
ground in user-voice, what Cheshire Cat will diagnose as
architecturally compromised. The role-playing literature
(CAMEL, AutoAgents, AgentVerse) showed that role-conditioning
matters; the identity-engineering claim Wonderland advances
extends this from "role for this task" to "constituted
character across all tasks, with structural failure modes
named and inhabited as part of the role itself."

A future bridge experiment would re-implement one of CAMEL's
canonical role pairs (user/assistant) with full constituted
characters in Wonderland's sense — §VIII failure modes,
worldview-anchored frames, multi-pilot stability — and
measure whether the constitution-grade framing produces
output the role-conditioned baseline doesn't. The
pre-registered Caterpillar comparator experiment in
Appendix C tests the same hypothesis at the single-agent
scale; extending it to a multi-agent role pair would be a
natural follow-up.

### What multi-agent frameworks miss

Across AutoGen, MetaGPT, ChatDev, LangChain/LangGraph,
CAMEL, AutoAgents, and AgentVerse, the common gap is the
**durable typed artifact layer with lifecycle invariants**.
Each framework provides agent orchestration; none provides
the substrate layer that Wonderland argues (§2.2) is
necessary for coherence across runs. The agents in any of
these frameworks could in
principle be wrapped in a substrate like Wonderland's; the
combination would be the "typed-state workflow engine with
LLM-driven transitions" category the field doesn't yet name.

---

## §10.2 — Workflow engines

Wonderland's substrate-side architecture has more in common
with classical workflow engines than with multi-agent
frameworks. Workflow engines model **typed state with
lifecycle transitions** as the load-bearing primitive; agent
frameworks treat state as scratch space. Wonderland inherits
the workflow-engine commitment but extends it to allow
LLM-driven transitions where workflow engines assume
deterministic ones.

### Apache Airflow [Airflow]

Apache Airflow (2014–) is the dominant workflow orchestration
platform for data engineering. Airflow models workflows as
directed acyclic graphs (DAGs) of tasks; tasks have explicit
dependencies, schedules, and state; the scheduler dispatches
work to executors and persists task state to a metadata
database. The "workflows as code" Python framework lets
operators define workflows declaratively.

Wonderland's substrate inherits structural commitments from
Airflow:

- **Typed state in a metadata layer** (Airflow's database;
  Wonderland's `.wonderland/` directory tree)
- **Explicit lifecycle states** (Airflow's task states:
  pending, running, success, failed; Wonderland's feature
  states: proposed, in_design, designed, queued,
  in_progress, ready_for_review, verified | rejected)
- **Scheduler / executor split** (Airflow's scheduler and
  workers; Wonderland's workflow runner and meeting
  executors)
- **Audit log of transitions** (Airflow's event history;
  Wonderland's run logs + memory + analyses)

The architectural distinction: Airflow's tasks are
**deterministic Python functions**; Wonderland's transitions
are **LLM-driven agent meetings** that may or may not
produce the artifact the substrate's lifecycle invariant
requires. Airflow's failures are deterministic (the task
raised an exception); Wonderland's failures include
"the agent meeting produced no artifact" and "the artifact
emitted didn't satisfy the lifecycle's structural
invariants." The substrate has to handle these failure
modes structurally — coverage checks, snapshot filters,
exit-condition enforcement (§3, §6).

### Temporal [Temporal]

Temporal (2019–) extends the workflow-engine model with
**durable execution**: workflows survive crashes and
failures by replaying event histories. Temporal's
workflow-as-code approach (Go, Java, TypeScript, Python)
gives developers ordinary control flow while the runtime
handles persistence and recovery.

Temporal's commitment to durable execution overlaps with
Wonderland's substrate-state durability. A pilot crashed
mid-meeting in Wonderland resumes from the last persisted
state when re-run; Temporal would handle the same shape of
problem at the workflow-engine level. The architectural
distinction is the same as with Airflow: Temporal assumes
deterministic transitions (the workflow code is the
specification); Wonderland's transitions are LLM-driven
and the substrate has to handle the resulting failure
shapes.

A future Wonderland implementation could plausibly use
Temporal as the workflow-engine substrate, with the
LLM-driven meetings as Temporal workflow steps. The
architectural commitments would translate; Temporal's
durable execution machinery would replace Wonderland's
custom run-state handling. The substrate's invariants
(citation chains, lifecycle state machines, scope filters)
would be application-layer code on top of Temporal's
execution layer.

### BPMN [BPMN]

The Business Process Model and Notation (BPMN) specification
is the industry standard for typed-state workflow modeling.
BPMN engines (Camunda, jBPM, Activiti, others) implement the
specification; BPMN workflows model business processes as
typed state machines with explicit transitions, gateways,
and event handlers.

Wonderland's lifecycle state machines (feature states,
ticket states, milestone derivation) are in the same
conceptual space as BPMN process states. The shared
commitment: state has structure; transitions have
preconditions; the engine enforces both. The distinction
Wonderland adds: transitions are not deterministic business
logic but LLM-driven agent emissions that the substrate
inspects against structural invariants.

The BPMN comparison is useful for the paper because BPMN
engines are widely understood as "the canonical typed-state
workflow modeling system." Wonderland's substrate sits in
the same architectural neighborhood, with the LLM-driven
transition layer added.

### What workflow engines miss

Airflow, Temporal, and BPMN engines all assume **the
transition is the specification**. The workflow code (or
BPMN diagram) declares what each transition does
deterministically; the engine's job is to execute it,
persist state, and handle failures. None of these systems
model the case where the transition is **LLM-driven and
may not produce a valid output**. Wonderland's substrate
adds that layer.

Concretely: an Airflow task that fails raises an exception;
the scheduler retries or marks the task failed. A
Wonderland meeting that fails to produce its
`exit_condition_artifact` (§3) didn't raise an exception —
the agents just didn't ship the artifact they were supposed
to ship. The substrate has to detect this (coverage checks,
exit-condition tracking, convergence-failure detection
T-a3) and route the failure to the right next step
(another rotation, a synthetic Dodo observation, escalation
to the operator).

This is the layer the workflow engines don't have. A future
"workflow engine with LLM-driven transitions" category
would be the architectural intersection Wonderland sits in.

---

## §10.3 — Autonomous coding systems

The third category Wonderland overlaps with is the
autonomous coding systems that emerged in 2023–2024:
prompt-to-running-app generation tools whose marketing
position is "describe what you want; we'll build it."

### Devin [Devin]

Cognition AI's Devin (March 2024) is the most prominent
autonomous coding agent. Devin's announcement claimed
state-of-the-art on SWE-bench [SWE-bench] (13.86% vs. prior
1.96%) and demonstrated end-to-end software engineering
including reading documentation, writing code, running
tests, debugging failures, and shipping deployments. Devin
is positioned as an "AI software engineer" — the framing is
labor-substitution, not productivity-amplification.

Wonderland and Devin overlap on the **autonomous coding
shape** — both can take a directive and produce a working
deployable artifact. The architectural differences:

- **Substrate**: Devin's internal architecture is
  proprietary; published material suggests a single agent
  with extensive tooling (shell, editor, browser) rather
  than a multi-agent substrate. Wonderland is a 10-character
  substrate with explicit multi-agent coordination (§4).
- **Artifact trail**: Devin produces code + a session log;
  Wonderland produces code + 39+ inline contract/ticket/
  ruling references, ADRs with named tradeoffs,
  severity-tagged tests, persona-driven user stories,
  audit-trail logs, FindingKind-typed reviews, and
  per-feature contracts (§7.2). The artifact-density-per-
  dollar-of-agent-tax framing (§1.2) is the metric where
  Wonderland's substrate advantage shows.
- **Cost regime**: Devin's public pricing is in the
  hundreds-of-dollars-per-task range (premium tier).
  Wonderland's notebook directive ships at $30.58 on Haiku
  4.5 [Haiku-4.5] (§7.1). The cost difference is partly
  model choice (Devin uses frontier models; Wonderland uses
  Haiku by design choice) and partly substrate efficiency
  (the constraint→quality+cost coupling Wonderland's
  evidence chapter develops, §7).
- **Operator-in-loop framing**: Devin frames the operator as
  the user who receives the output; Wonderland frames the
  operator as part of the substrate's design loop (§5.2 —
  operator-in-loop falsification as load-bearing
  methodological commitment). The operator's
  fine-tooth-comb post-pilot review is what surfaces
  substrate gaps the automated stack can't catch (§5.2,
  §8.3 — the LDR hollow-verify case).

Devin's claim to fame on SWE-bench [SWE-bench] is the
issue-fixing benchmark. Wonderland's pilot directives
(notebook, CRM, dashboard) are green-field MVPs — a
different shape of work than SWE-bench's existing-codebase-
fix tasks. The two systems optimize for different work
shapes; the comparison isn't head-to-head on a common
benchmark.

### Cursor [Cursor], Aider [Aider], Claude Code [Claude Code]

These are **agentic coding tools driven by a human
operator** — the human sits in the loop, requesting
changes, accepting or rejecting suggestions, navigating the
codebase. Cursor is a VS Code fork with deep AI integration;
Aider is a CLI tool that edits local git repositories with
LLM assistance; Claude Code is Anthropic's CLI coding
agent.

The architectural difference between this class and
Wonderland is **autonomy posture**. Cursor / Aider / Claude
Code expect a human in the loop continuously; Wonderland
expects a human at gate boundaries (Tier 2 autonomy, §5.1).
The substrate's claim to autonomous operation between gates
is what distinguishes it from human-driven agentic coding
tools.

The comparison Wonderland's [comparison-baselines artifact](https://github.com/KohlJary/wonderland-ai/blob/main/paper/artifacts/comparison-baselines/README.md)
develops is most directly relevant to this class: when a
human-driven agentic tool is given the same notebook
directive Wonderland's pilots ran, the resulting artifact
ships without the structural review trail Wonderland's
substrate produces. The artifact-density-per-agent-tax-
dollar framing (§1.2, §10.1) is what makes the comparison
informative rather than head-to-head.

### GPT-Engineer [GPT-Engineer], bolt.new [bolt.new]

These are **autonomous green-field generation tools** — the
operator describes what they want; the system produces a
codebase. GPT-Engineer (April 2023, Anton Osika) is the
earliest CLI-based instance; bolt.new (StackBlitz) is the
in-browser SaaS instance with WebContainer-based execution.

These are Wonderland's closest comparators on the
**prompt-to-running-app green-field shape**. The distinction
is the substrate layer. GPT-Engineer and bolt.new produce
running applications but don't produce a structural
artifact trail: there are no typed stories with confusion
flags, no contracts with explicit tradeoffs, no severity-
tagged tests, no review artifacts. The system ships code
that runs (sometimes); the absence of the artifact layer
makes the code harder to maintain, extend, or audit.

Wonderland's claim against this class is again artifact
density: same green-field shape, structurally more
byproducts that survive beyond the initial generation.

### What autonomous coding systems miss

Devin, Cursor, Aider, GPT-Engineer, and bolt.new all treat
the agent layer as opaque (an LLM with tools) and the
output artifact as the value proposition. None has the
substrate's **typed artifact layer with lifecycle
invariants** Wonderland argues is what makes long-running,
operator-in-loop multi-agent SDLC tractable.

The category Wonderland sits in — autonomous green-field
generation with a substrate that produces structured
artifact trails at every layer — isn't named in the
existing field vocabulary. The paper's house word for it
remains "substrate."

---

## §10.4 — The broader literature

Beyond the three primary categories, Wonderland inherits
from several broader research traditions worth naming
briefly.

### Software engineering methodology

The TDD workflow [Beck-TDD] that `tdd-design` and
`tdd-implement` operationalize (§3) is Kent Beck's
red-green-refactor cycle. The substrate's commitment to
failing tests before implementation, and to running the
project's actual test suite as a verification gate (M9),
inherits directly from this tradition. Wonderland adds
multi-agent coordination on top of the underlying TDD
methodology; the methodology itself isn't novel.

The substrate's emphasis on ADRs (Architecture Decision
Records) with explicit tradeoffs (§4 — Cheshire Cat) and
on contracts as typed seams between components (§4 —
Tweedles) inherits from broader software engineering best
practices. Wonderland makes these structures load-bearing
substrate primitives rather than aspirational conventions.

### Multi-agent coordination

The negotiation pattern between Tweedles in M5 — symmetric
pair negotiating contracts at a seam — has a classical
ancestor in distributed AI's **Contract Net Protocol**
[Contract-Net]. Wonderland doesn't directly implement
Contract Net; the resemblance is structural (negotiation
between agents with overlapping authority over a shared
artifact). The broader academic context of multi-agent
coordination [Wooldridge-MAS] frames the design space
Wonderland operates in; the substrate's specific
contribution is the typed-artifact + lifecycle-invariant
layer that classical multi-agent literature doesn't
typically include.

### Foundation models

The substrate runs on Claude Haiku 4.5 [Haiku-4.5] by
design choice (§2 Corollary 1). The small-model thesis
predicts that constituted identity + substrate constraints
let a smaller model match larger-model performance on
substrate-shaped work. The thesis is testable; the
generic-baseline eval (§9) would test it rigorously.
Until then, Wonderland's cost-trajectory evidence (§7
Pillar 1) is the qualitative receipt for the prediction.

The Claude 4 family [Claude-4-family] provides the
foundation-model layer the substrate sits on. The
substrate's claims are scoped to this model family;
generalization to other model families is future work
(§9.3).

### Literary and philosophical lineage

The Wonderland cast's literary origin in Lewis Carroll's
*Alice's Adventures in Wonderland* [Carroll-Alice] and
*Through the Looking-Glass* [Carroll-Looking-Glass] is
load-bearing, not stylistic (§4). Carroll's characters
carry intentions that "the X agent" framings don't —
recovery patterns and production-shape properties depend
on the characters HAVING characters (§2 Corollaries 3, 4).

The Sephirah/Qlipha pairing framework [Scholem-Kabbalah]
that §2 Corollary 2 cites for failure-modes-as-identity is
the canonical Kabbalistic structure: each Sephirah (virtue)
has its named Qlipha (the specific shadow it decays into
when ungoverned). The substrate's §VIII pattern across
every constitution follows this form. The framing is cited
not as religious philosophy but as the intellectual
lineage that makes the depth of the failure-modes-as-
identity claim legible to readers who'd otherwise frame
"failure modes" as an anti-pattern checklist.

---

## §10.5 — What "substrate" doesn't yet name

The intersection of typed-state workflow engine, LLM-driven
transitions, multi-agent coordination, durable artifact
layer with lifecycle invariants, and operator-in-loop
falsification mechanism is the architectural space
Wonderland occupies. The field's existing categories each
capture one or two of these properties; none captures the
full set.

The paper's working term — **substrate** — is a house word.
If others build similar systems and the term propagates,
the field will eventually have a name for the category. If
better terminology emerges, the paper's use of "substrate"
will be archival rather than canonical. Either outcome is
fine; the architectural commitment Wonderland makes is the
research contribution, not the vocabulary.

The deeper claim that motivates the category — that
**identity engineering** is worth pursuing as a research
direction alongside prompt engineering, agent engineering,
and multi-agent systems work (§2 closing, §1.2) — is the
proposal the paper most wants the field to consider.
Wonderland is one instance; the substrate's invariants are
how that instance happens to be built; whether identity
engineering constitutes a *distinct* discipline (vs.
prompt-engineering-with-richer-prompts) is what the
comparative experiments in §9 would answer. At the
snapshot this paper documents, distinctness is proposed,
not yet demonstrated.

The related work landscape covers the architectural
neighborhood. Wonderland's distinctive contribution is the
composition: identity-bearing characters as transition
functions over a typed-state substrate with lifecycle
invariants, operating under multi-agent coordination
patterns, falsified by operator-in-loop scrutiny, evolving
through an iteration cycle that closes structural gaps.
None of the cited systems occupies this composition; this
paper is the case for why it's worth occupying.


---

# Bibliography

> References cited throughout the paper. Each entry verified via
> web search during composition. URL stability varies — arXiv IDs
> and DOIs are stable; GitHub repos and corporate blog posts may
> shift. Bracketed citation keys (`[AutoGen]`) are used inline
> throughout the paper text.

## Multi-agent frameworks

**[AutoGen]** Wu, Q., Bansal, G., Zhang, J., Wu, Y., Li, B.,
Zhu, E., Jiang, L., Zhang, X., Zhang, S., Liu, J., Awadallah,
A. H., White, R. W., Burger, D., & Wang, C. (2023). *AutoGen:
Enabling Next-Gen LLM Applications via Multi-Agent
Conversation*. arXiv:2308.08155. [arxiv.org/abs/2308.08155](https://arxiv.org/abs/2308.08155).
Microsoft Research. The original multi-agent conversation
framework paper.

**[MetaGPT]** Hong, S., Zhuge, M., Chen, J., Zheng, X., Cheng,
Y., Zhang, C., Wang, J., Wang, Z., Yau, S. K. S., Lin, Z., Zhou,
L., Ran, C., Xiao, L., Wu, C., & Schmidhuber, J. (2023).
*MetaGPT: Meta Programming for A Multi-Agent Collaborative
Framework*. arXiv:2308.00352. [arxiv.org/abs/2308.00352](https://arxiv.org/abs/2308.00352).
DeepWisdom. Standard Operating Procedures encoded into
prompts; assembly-line role assignment.

**[ChatDev]** Qian, C., Liu, W., Liu, H., Chen, N., Dang, Y.,
Li, J., Yang, C., Chen, W., Su, Y., Cong, X., Xu, J., Li, D.,
Liu, Z., & Sun, M. (2024). *ChatDev: Communicative Agents for
Software Development*. ACL 2024. arXiv:2307.07924. [arxiv.org/abs/2307.07924](https://arxiv.org/abs/2307.07924).
Tsinghua / OpenBMB. Chat-chain coordination; communicative
dehallucination; sub-$1 software generation in under seven
minutes.

**[CAMEL]** Li, G., Hammoud, H., Itani, H., Khizbullin, D., &
Ghanem, B. (2023). *CAMEL: Communicative Agents for "Mind"
Exploration of Large Language Model Society*. NeurIPS 2023.
arXiv:2303.17760. [arxiv.org/abs/2303.17760](https://arxiv.org/abs/2303.17760).
KAUST. Role-playing communicative agent framework; user/assistant
pair coordination; demonstrates role-conditioning effects on
solution paths.

**[AutoAgents]** Chen, G., Dong, S., Shu, Y., Zhang, G., Sesay,
J., Karlsson, B., Fu, J., & Shi, Y. (2023). *AutoAgents: A
Framework for Automatic Agent Generation*. arXiv:2309.17288.
[arxiv.org/abs/2309.17288](https://arxiv.org/abs/2309.17288).
Microsoft Research. Dynamic agent-generation framework;
synthesizes specialized agents per task at runtime; reduces
manual prompt-engineering load on the operator.

**[AgentVerse]** Chen, W., Su, Y., Zuo, J., Yang, C., Yuan, C.,
Chan, C.-M., Yu, H., Lu, Y., Hung, Y.-H., Qian, C., Qin, Y.,
Cong, X., Xie, R., Liu, Z., Sun, M., & Zhou, J. (2024).
*AgentVerse: Facilitating Multi-Agent Collaboration and Exploring
Emergent Behaviors*. ICLR 2024. arXiv:2308.10848.
[arxiv.org/abs/2308.10848](https://arxiv.org/abs/2308.10848).
Tsinghua. Multi-agent collaboration framework with expert
recruitment, decision-making, and action phases; demonstrates
multi-phase coordination outperforming flat collaboration.

**[LangChain]** Chase, H., et al. (2022–). *LangChain: The agent
engineering platform.* Open-source framework, GitHub: [github.com/langchain-ai/langchain](https://github.com/langchain-ai/langchain).
Launched October 2022.

**[LangGraph]** LangChain Inc. (2024–). *LangGraph: A framework
for stateful, multi-agent AI workflows.* GitHub: [github.com/langchain-ai/langgraph](https://github.com/langchain-ai/langgraph).
Documentation: [langchain.com/langgraph](https://www.langchain.com/langgraph).
Graph-based stateful agent orchestration; durable execution;
human-in-the-loop primitives.

## Autonomous coding systems

**[Devin]** Cognition AI. (2024, March 12). *Introducing Devin,
the first AI software engineer.* [cognition.ai/blog/introducing-devin](https://cognition.ai/blog/introducing-devin).
13.86% on SWE-bench at launch (vs 1.96% prior SOTA); marketed
as the first fully-autonomous software engineering agent.

**[Cursor]** Anysphere, Inc. (2023–). *Cursor: AI code editor.*
[cursor.com](https://cursor.com/). VS Code fork with deep AI
integration; Cursor 3 (2026) introduced agent-first workspace
managing fleets of coding agents.

**[Aider]** Gauthier, P. (2023–). *Aider: AI pair programming in
your terminal.* GitHub: [github.com/Aider-AI/aider](https://github.com/Aider-AI/aider).
Open-source CLI tool for AI-driven edits in local git
repositories; commits with sensible messages; works with
multiple LLM backends.

**[GPT-Engineer]** Osika, A. (2023, April). *gpt-engineer: CLI
platform to experiment with codegen.* GitHub: [github.com/AntonOsika/gpt-engineer](https://github.com/AntonOsika/gpt-engineer).
One of the earliest autonomous-coding agents (55K+ stars).
One-prompt codebase generation; clarifying questions; technical
spec generation. Precursor to Lovable / [gptengineer.app](https://gptengineer.app/).

**[bolt.new]** StackBlitz. (2024–). *bolt.new: Prompt, run, edit,
and deploy full-stack web applications.* [bolt.new](https://bolt.new/);
GitHub: [github.com/stackblitz/bolt.new](https://github.com/stackblitz/bolt.new).
Browser-based AI development platform; AI agent controls
filesystem, package manager, terminal, browser console via
WebContainer technology.

**[Claude Code]** Anthropic. (2024–). *Claude Code: AI coding
assistant from Anthropic.* Documentation: [docs.claude.com/en/docs/claude-code](https://docs.claude.com/en/docs/claude-code).
Anthropic's CLI coding agent.

## Coding-agent benchmarks

**[SWE-bench]** Jimenez, C. E., Yang, J., Wettig, A., Yao, S.,
Pei, K., Press, O., & Narasimhan, K. (2024). *SWE-bench: Can
Language Models Resolve Real-World GitHub Issues?* ICLR 2024.
arXiv:2310.06770. [arxiv.org/abs/2310.06770](https://arxiv.org/abs/2310.06770).
Princeton Language and Intelligence. 2,294 software
engineering problems from 12 popular Python repositories;
each requires understanding and coordinating changes across
multiple functions, classes, or files. Established Claude 2's
1.96% baseline that Devin's 13.86% later surpassed.

**[SWE-bench Verified]** OpenAI. (2024, August). *Introducing
SWE-bench Verified.* [openai.com/index/introducing-swe-bench-verified](https://openai.com/index/introducing-swe-bench-verified/).
Filtered subset of 500 SWE-bench tasks verified for solvability;
the de-facto benchmark for autonomous coding agents in 2025.

## Workflow engines

**[Airflow]** The Apache Software Foundation. (2014–). *Apache
Airflow.* Documentation: [airflow.apache.org/docs](https://airflow.apache.org/docs/).
Workflow orchestration platform; "workflows as code" Python
DAG model; scheduler + worker + metadata DB architecture.

**[Temporal]** Temporal Technologies, Inc. (2019–). *Temporal:
Durable execution platform.* Documentation: [docs.temporal.io](https://docs.temporal.io/).
GitHub: [github.com/temporalio/temporal](https://github.com/temporalio/temporal).
Workflow durable execution: event-history replay; long-running
workflows that survive crashes; multi-language SDKs.

**[BPMN]** Object Management Group. (2014). *Business Process
Model and Notation (BPMN), Version 2.0.2.* OMG Document Number:
formal/2013-12-09. [omg.org/spec/BPMN](https://www.omg.org/spec/BPMN/).
The dominant industry standard for typed-state workflow
modeling; reference for "workflow engines with deterministic
transitions over typed state."

## Foundation models

**[Haiku-4.5]** Anthropic. (2025, October 15). *Introducing
Claude Haiku 4.5.* [anthropic.com/news/claude-haiku-4-5](https://www.anthropic.com/news/claude-haiku-4-5).
Pricing: $1/MTok input, $5/MTok output (October 2025 launch).
200K context window; 64K max output tokens; ~90% of Sonnet
4.5's performance at ~1/3 the cost on agentic-coding
benchmarks. Model ID: `claude-haiku-4-5-20251001`. Wonderland's
default model.

**[Claude-4-family]** Anthropic. (2024–2025). *Claude 4 model
family system cards.* Available via [anthropic.com/news](https://www.anthropic.com/news).
The model family Wonderland's substrate has been pilot-tested
on (Haiku 4.5 specifically).

## Software engineering

**[Beck-TDD]** Beck, K. (2002). *Test-Driven Development: By
Example.* Addison-Wesley Signature Series. ISBN
978-0-321-14653-3. The canonical reference for the red-green-
refactor cycle Wonderland's `tdd-design` + `tdd-implement`
workflows operationalize.

## Multi-agent and coordination theory

**[Contract-Net]** Smith, R. G. (1980). *The Contract Net
Protocol: High-Level Communication and Control in a Distributed
Problem Solver.* IEEE Transactions on Computers, C-29(12),
1104–1113. DOI: 10.1109/TC.1980.1675516. The classical
distributed-AI reference for negotiation-based task allocation;
ancestor of the contract-shaped negotiation Wonderland's
Tweedle pair operationalizes in M5.

**[Wooldridge-MAS]** Wooldridge, M. (2009). *An Introduction to
MultiAgent Systems* (2nd ed.). Wiley. ISBN 978-0-470-51946-2.
The standard textbook on multi-agent systems; reference for
the broader academic context Wonderland's substrate sits in.

## Literary and philosophical framing

**[Carroll-Alice]** Carroll, L. (1865). *Alice's Adventures in
Wonderland.* Macmillan. Public domain; Project Gutenberg:
[gutenberg.org/ebooks/11](https://www.gutenberg.org/ebooks/11).
The literary source for the Wonderland cast's character names
(Alice, White Rabbit, Cheshire Cat, Caterpillar, Mad Hatter,
Queen of Hearts, Tweedledee + Tweedledum, Dodo, Mock Turtle,
Dormouse).

**[Carroll-Looking-Glass]** Carroll, L. (1871). *Through the
Looking-Glass, and What Alice Found There.* Macmillan. Public
domain; Project Gutenberg: [gutenberg.org/ebooks/12](https://www.gutenberg.org/ebooks/12).
Source for the Tweedles' pair-protocol framing.

**[Scholem-Kabbalah]** Scholem, G. (1941). *Major Trends in
Jewish Mysticism.* Schocken Books, New York. The canonical
academic introduction to Kabbalistic tradition cited in
§2.2 (Corollary 2 — failure modes as identity) for the
Sephirah/Qlipha pairing framework. The framing of each
virtue carrying its specific shadow as a load-bearing
constitutional structure derives from this tradition.

## Wonderland project artifacts

**[Wonderland-Repo]** Jary, K. (2024–). *Wonderland.* Open-source
repository: [github.com/KohlJary/wonderland](https://github.com/KohlJary/wonderland).
The substrate implementation, pilot artifacts, analyses, memory
pins, release notes, and per-chapter source material that
underlie the paper's claims. Substrate version cited throughout
as 0.10.2 + T-ab62 + T-ab64.

**[Wonderland-Comparison]** Jary, K. (2026). *Comparison
Baselines.* In Wonderland repository under
`paper/artifacts/comparison-baselines/`. Includes single-shot
Haiku, single-shot Sonnet, and Claude-Code agentic baselines
against the notebook directive; adversarial-review-of-baselines
analysis finding 30 blocker-class bugs across 4 single-shot
baselines that ship code without any review pass.

**[Wonderland-Analyses]** Jary, K. (2024–). *Pilot analyses
directory.* In Wonderland repository under
`src/wonderland/closet/analyses/`. ~46 numbered chronological
analyses of pilot events and substrate iterations. Key
analyses cited: 004 (silence-as-settlement), 027 (visible
degradation + recovery via disk channel), 033 (mvp cost
breakdown), 034 (mvp Tier 2 autonomous pilot completion),
040 (tdd-design order rationale), 046 (mvp-redux cost
receipt — the $83.78 → $30.58 trajectory).

---

## Notes on bibliographic stability

URL stability rankings (most to least stable):
1. **arXiv IDs** — permanent; cite by ID, URL is convenience
2. **ISBNs** — permanent
3. **DOIs** — permanent
4. **GitHub repos** — stable while project active; org transfers
   possible (Aider's `paul-gauthier/aider` → `Aider-AI/aider`
   noted in citation)
5. **Corporate blog posts** — stable for well-maintained corps
   but not guaranteed (Anthropic, Cognition, Microsoft)
6. **Documentation sites** — generally stable but versions may
   shift

For an arXiv-shaped paper preparation, prefer arXiv IDs + ISBNs
where available; cite URLs as access vectors but treat the IDs
as the canonical identifier.

## Items deliberately omitted

- **Wonderland project memory pins** (`.claude/projects/...`)
  and **release notes** — internal project artifacts that
  shouldn't appear in the bibliography. The paper cites them
  inline as project-internal references with brief inline
  descriptions where needed.
- **Roadmap item IDs** (e.g., `b3f440c8`) — internal
  identifiers; not bibliography-worthy. First use of each in
  the paper text is accompanied by an inline definition.
- **T-ab task IDs** (e.g., `T-ab51`) — same treatment as
  roadmap items.
- **Hypothesis-grade observations** (e.g.,
  `project_haiku_is_architecturally_optimal.md`) — explicitly
  excluded from evidence chapter and bibliography both;
  surfaced in limitations / future work as honest open
  questions.

## Citation conventions used in paper text

- First mention of a system: full name with bracketed
  citation. *"Wonderland sits in a gap between three categories
  the field already names: multi-agent frameworks like AutoGen
  [AutoGen], MetaGPT [MetaGPT], and ChatDev [ChatDev]; workflow
  engines like Airflow [Airflow] and Temporal [Temporal]; and
  autonomous coding systems like Devin [Devin], Cursor
  [Cursor], Aider [Aider], GPT-Engineer [GPT-Engineer], and
  bolt.new [bolt.new]."*
- Subsequent mentions: short form, no re-citation.
- Substrate-version-specific claims about Anthropic models
  carry [Haiku-4.5] inline.
- TDD methodology mentions carry [Beck-TDD] on first
  meaningful invocation in §3 (architecture) where
  red-green-refactor is named.
- Carroll character references in §4 (cast) carry
  [Carroll-Alice] / [Carroll-Looking-Glass] as appropriate
  at first character introduction.
- Sephirah/Qlipha in §2 corollary 2 carries [Scholem-Kabbalah].


---

