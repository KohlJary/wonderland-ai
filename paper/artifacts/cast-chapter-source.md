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
