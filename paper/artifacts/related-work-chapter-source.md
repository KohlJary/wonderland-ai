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
