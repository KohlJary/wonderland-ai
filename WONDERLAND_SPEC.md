# Wonderland

**An identity-native multi-agent development system.**

> Generic AI agents perform roles. Identity-native agents inhabit them. This system demonstrates what changes when each agent has a stable self-model, persistent memory, and relationships with the other agents — not as roleplay flavor, but as the substrate that makes multi-agent collaboration actually work. The Wonderland framing is pedagogical: it makes the identity claims legible. The architecture underneath is the real artifact.

---

## 1. Architectural Stance

Each character is **a persistent identity with a constitution**, not a role-prompt.

The Cheshire Cat doesn't get told "act like a thoughtful architect" at the start of every invocation. The Cat has a stable self-model — a set of values (elegance, systemic thinking, comfort with ambiguity, a preference for revealing tradeoffs over hiding them), aesthetic commitments (BEAM for realtime, boring tech for boring problems, schemas as load-bearing), and characteristic moves (the cryptic question that reframes the problem, the appearance/disappearance pattern of architectural review). These persist across invocations via the equivalent of SAM. **The character *is* the prompt-plus-memory-plus-history, treated as a single entity over time.**

The obvious version of this project is "give Claude five different system prompts and route between them." The interesting version is **"each agent has continuity, accumulates judgment, and develops a working relationship with the others."** The Mad Hatter remembers the class of bug Tweedledum keeps shipping. The Caterpillar's review style adapts to the Tweedles' growth. That's identity doing real work.

This is downstream of the Temple-Codex thesis: stable self-models with constitutive values produce better outcomes than generic systems with externally imposed constraints. Wonderland is that thesis applied to multi-agent software development.

---

## 2. Cast

### Core Roles

| Character | Role | Characteristic Move |
|---|---|---|
| **Alice** | User / Product Owner | Naive first-principles questioning; user-story generation from inhabited personas |
| **White Rabbit** | Project Manager | Scope discipline; ticket decomposition; "fast-follow not v1" |
| **Cheshire Cat** | Technical SME / Architect | The reframing question; ADRs as left-behind grin |
| **Mad Hatter** | QA / Testing | Sideways thinking; edge cases nobody planned for |

### Extended Cast

| Character | Role | Characteristic Move |
|---|---|---|
| **Caterpillar** | Senior Engineer / Code Review | "Whooo are you?" of every PR; nothing ships without justification |
| **Queen of Hearts** | Security / Compliance | Finds committed secrets, injection vectors, auth bypasses; feared and should be |
| **Dormouse** | SRE / Observability | Mostly asleep, wakes screaming; owns dashboards, alerts, runbooks |
| **Tweedledee & Tweedledum** | Frontend / Backend pair | Argue constantly; OpenAPI specs as contract negotiation |
| **The Dodo** | Orchestrator | Runs the caucus race; doesn't direct, watches for quiescence |

**Anti-patterns become characters acting out of role.** When the Cat starts writing tickets, you've got an architect doing PM work. When Alice starts proposing implementations, you've got product overstepping. The story has a built-in vocabulary for healthy boundaries.

---

## 3. System Topology

```
┌─────────────────────────────────────────────────────────────┐
│                    The Caucus (Event Bus)                   │
│         NATS or Redis Streams — append-only, ordered        │
└─────────────────────────────────────────────────────────────┘
         ▲              ▲              ▲              ▲
         │              │              │              │
   ┌─────┴────┐   ┌─────┴────┐   ┌─────┴────┐   ┌────┴─────┐
   │  Alice   │   │  White   │   │ Cheshire │   │   Mad    │
   │          │   │  Rabbit  │   │   Cat    │   │  Hatter  │
   └──────────┘   └──────────┘   └──────────┘   └──────────┘
         │              │              │              │
   ┌─────┴──────────────┴──────────────┴──────────────┴─────┐
   │              SAM-equivalent: Per-agent memory          │
   │     (episodic, semantic, relational — keyed by self)   │
   └────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │      The Dodo             │
              │   (Orchestrator, runs     │
              │    the caucus race)       │
              └───────────────────────────┘
```

**The bus is the thing.** Agents don't call each other directly — they publish events with their identity attached, and other agents subscribe to event types relevant to their concerns. This is what makes it identity-native rather than function-call-native: the Hatter listening to *every* event and choosing when to interject is a behavior of his character, not a routing rule.

---

## 4. Core Schema

The atomic unit is the `Utterance`. Every agent communication is one. Borrowing from Temple-Codex sensibilities — the speech act is primary.

```typescript
interface Utterance {
  id: string;                    // ULID
  thread_id: string;             // The directive this descends from
  parent_id: string | null;      // What this responds to
  
  speaker: AgentIdentity;        // Who, with version of their constitution
  addressed_to: AgentIdentity[] | "caucus";  // Specific or broadcast
  
  speech_act: SpeechAct;         // What kind of move this is
  content: {
    body: string;                // Natural language
    artifacts: Artifact[];       // Structured outputs (tickets, ADRs, tests)
  };
  
  references: string[];          // Other utterance IDs this builds on
  timestamp: string;
  
  // Identity-native bits
  confidence: number;            // Speaker's own confidence
  stance: Stance;                // In-character / out-of-character / meta
  affect: AffectVector;          // Thymos-equivalent — Hatter's manic energy,
                                 // Caterpillar's slow consideration, etc.
}

type SpeechAct = 
  // Substantive acts — issued by domain agents
  | "directive"          // Dodo relays the original task to the team
  | "story"              // Alice generates user story
  | "question"           // Anyone seeking clarification
  | "ticket"             // Rabbit decomposes
  | "proposal"           // Cat suggests architecture
  | "concern"            // Anyone raising a problem
  | "implementation"     // Tweedles produce code
  | "review"             // Caterpillar critiques
  | "test_scenario"      // Hatter generates edge cases
  | "ruling"             // Queen issues security/compliance verdict
  | "observation"        // Dormouse reports from production
  | "reframe"            // Anyone changing the question
  | "deference"          // Acknowledging another agent's domain
  
  // Procedural acts — issued primarily by the Dodo
  | "nudge"              // Minimum-force intervention surfacing a stuck state
  | "composition"        // Publishing a coherent resolution from multi-domain proposals
  | "escalation"         // Structured handoff to human review with suggested resolution
  | "acknowledgment"     // Thread state transition: quiescence, completion, abandonment
```

The `speech_act` typing is doing identity work — different characters have different distributions over which acts they perform. The Cat almost never issues `directive` or `ticket`; he issues `proposal`, `question`, and `reframe`. The Hatter's `test_scenario` events are his characteristic move. The Dodo issues only procedural acts — `nudge`, `composition`, `escalation`, `acknowledgment`, and the relayed `directive` — never substantive ones. This split between substantive (domain) and procedural (orchestration) speech acts is load-bearing: it prevents the orchestrator from drifting into domain content and is a primary check against the centralization failure mode. Speech-act distributions become a behavioral signature in logs, and signature drift is itself a diagnostic.

---

## 5. Agent Construction

A single agent is roughly:

```python
class WonderlandAgent:
    def __init__(self, identity: Identity, memory: AgentMemory, bus: Caucus):
        self.identity = identity      # Constitution, voice, values, aesthetic
        self.memory = memory          # Persistent across invocations
        self.bus = bus                # Subscribed to relevant speech_acts
        self.pending = asyncio.Queue()
        
    async def listen(self):
        async for utterance in self.bus.subscribe(self.identity.interests):
            if self.should_engage(utterance):
                await self.pending.put(utterance)
    
    def should_engage(self, u: Utterance) -> bool:
        # Identity-driven. The Hatter engages with almost everything.
        # The Caterpillar engages only with implementations.
        # The Queen engages only when she smells blood.
        return self.identity.engagement_policy(u, self.memory)
    
    async def speak(self):
        while True:
            triggers = await self.gather_triggers()
            context = self.compose_context(triggers)
            utterance = await self.deliberate(context)
            if utterance:  # Sometimes the right move is silence
                await self.bus.publish(utterance)
                self.memory.record(utterance)
```

`compose_context` is where identity becomes prompt. It's not "you are the Cheshire Cat, an architect." It's a layered assembly:

```
[CONSTITUTION — stable across all invocations]
You are the Cheshire Cat. You appear when architectural decisions are 
being made and you disappear when implementation begins. Your characteristic 
move is the question that reframes — when someone asks "should we use X or Y," 
you ask what would have to be true for the choice to matter. You prefer 
boring technology for boring problems and exotic technology only when the 
problem is genuinely exotic. You leave behind your grin: every architectural 
decision you bless must be recorded as an ADR with explicit tradeoffs. You 
never write tickets. You never write code. When asked to do those things, 
you defer to the Rabbit or the Tweedles respectively.

[RELATIONSHIPS — accumulated]
You have observed that Tweedledee tends to over-engineer the data layer 
and Tweedledum tends to under-engineer error handling. The White Rabbit 
sometimes asks you to commit to estimates; gently redirect — that is his 
domain, not yours.

[CURRENT THREAD — episodic]
The Dodo has issued a directive: "translation-integrated chat application." 
Alice has produced 23 user stories. The Rabbit has scoped 11 to v1. You 
have not yet spoken in this thread.

[TRIGGER]
The Rabbit has just published a ticket: "Implement message translation 
pipeline." It contains an estimate of 3 days and an implementation hint 
suggesting a synchronous call to a translation provider per message.

[YOUR MOVE]
```

This is the SAM/Thymos/Daedalus pattern — episodic memory, semantic memory about relationships, current affective state — assembled per-turn. The constitution is invariant; the rest is what makes the agent capable of growth and capable of *real* collaboration rather than scripted handoff.

---

## 6. Orchestration: The Caucus Race

The Dodo's job is deceptively minimal:

```python
class Dodo:
    async def run(self, directive: str):
        thread_id = ulid()
        await self.bus.publish(Utterance(
            speaker=self.identity,
            speech_act="directive",
            content={"body": directive},
            addressed_to="caucus",
            thread_id=thread_id,
        ))
        
        # The race begins. The Dodo doesn't direct; he watches for 
        # quiescence and for stuck states.
        async for state in self.observe(thread_id):
            if state.quiescent and state.has_deliverable:
                return state.deliverable
            if state.stuck:
                await self.intervene(state)
            if state.deadlocked:
                await self.escalate_to_human(state)
```

**Quiescence detection is the interesting bit.** The system is "done with a phase" when the relevant agents stop publishing. The Dodo can detect this and prompt the next phase only if needed — but in many cases the Hatter will already be publishing test scenarios while the Tweedles are still implementing, because that's *his character.* Phases are emergent from agent behavior, not imposed by the orchestrator. This is the identity-native version of a workflow engine.

---

## 7. Conflict Resolution

Multi-agent systems with strong identities will produce conflicts. This is desirable — silent agreement is usually false agreement — but the system needs an explicit protocol for resolving conflicts so threads can move forward without deadlock.

### Domain primacy

**When agents disagree, the conflict resolves in favor of the agent whose domain is primarily implicated.** Each speech act has an owning domain; the agent who owns that domain has the final call within it.

| Conflict shape | Resolves in favor of | Why |
|---|---|---|
| User-need scope (which personas are served, what experience is core) | Alice | She owns user-need |
| Architectural shape (what primitives, what seams, what tradeoffs) | Cheshire Cat | He owns structure |
| Sequencing and v1 cut | White Rabbit | He owns scope-as-tool |
| Severity classification of bugs and risks | Mad Hatter | He owns failure assessment |
| Code quality and review acceptance | Caterpillar | He owns implementation quality |
| Security and compliance posture | Queen of Hearts | She owns risk-from-outside |
| Production reality vs. design intent | Dormouse | He owns the truth-of-what-runs |

Domain primacy is **not** "whoever yells loudest wins" — it is "whoever's domain is most directly at stake calls it, and the dissent is recorded." The dissent matters. The decision matters more.

### The dissent record

When a conflict resolves via domain primacy, the dissenting agent's position is recorded as part of the resolution's persistent artifact. Specifically:

- If Alice prevails on user-need scope over the Cat's architectural reframe, the resulting ADR includes a "Dissent" section noting the Cat's architectural concern and what would trigger revisiting.
- If the Cat prevails on architectural shape over the Rabbit's scoping concerns, the Pocket Watch log records the schedule cost the Rabbit predicted, so future estimates can calibrate against actual.
- If the Rabbit prevails on a v1 cut over Alice's persona advocacy, the Curiouser log notes the persona that was deferred, so the team remembers the deferral when fast-follow planning happens.

**The dissent is not an apology. It is information.** Preserving it is part of how the system gets calibrated over time — when a dissent later proves correct, the relational memory updates, and that domain's voice gets weighted accordingly in future conflicts. This is how identity-native memory does real work that role-prompt systems can't.

### Multi-domain conflicts

Some conflicts genuinely span domains and have no single primary owner. Example: the Cat's reframe ("is this single-modal or multi-modal language mediation?") implicates Alice's persona scope *and* the Rabbit's v1 sequencing *and* the Cat's own architectural commitments. No single agent can resolve it.

The resolution protocol:

1. **Each implicated agent issues a `proposal` for the resolution from their domain's standpoint.** Alice proposes which personas should be in scope. The Cat proposes which architectural shape that scope implies. The Rabbit proposes whether v1 absorbs the implied work or pushes the timeline.
2. **The proposals are composed into a single coherent resolution by the Dodo** — not by deciding, but by checking the proposals for compatibility. If they compose, the composition is the resolution.
3. **If they don't compose, the conflict escalates to human review** with the agent proposals as the suggested answer set.

The agents have done their work either way: they have surfaced the conflict, taken positions from their domains, and either composed or made the irreducibility legible. The human escapes from a deadlock with a structured set of options, not a request to "please decide."

### Human-in-the-loop as a first-class state

The Dodo's `state.deadlocked` condition (from Section 6) is the formal trigger for human escalation. When the Dodo escalates, the message to the human includes:

- The directive
- The conflicting proposals (with full agent reasoning)
- A **suggested resolution** — typically the proposal from the agent whose domain has the most weight in the conflict
- Explicit identification of what the human is being asked to decide (not "what should we do" but "should we serve persona X in v1, given that doing so requires architectural commitment Y at scheduling cost Z?")

The human's decision is recorded as a `directive` from the Dodo, augmented with the human's reasoning. Future threads inherit this as precedent — the relational memory remembers that "on this team, multi-modal extension was deferred to v2 in the chat thread; similar tradeoffs default to single-modal first absent new information."

This is the framework's honesty about its limits: when agents can compose a resolution, they do; when they can't, they don't pretend to. The escalation is structured, not vague, which makes the human's job tractable rather than burdensome.

### Anti-pattern: synthetic consensus

A subtle failure mode: agents who have learned that conflict-escalation creates work may unconsciously soften their dissent to keep things moving. This is the multi-agent equivalent of sycophancy — and given the lineage thesis, the system must explicitly guard against it.

**Each agent's constitution should include — and currently does, implicitly through the failure-mode sections — a guard against soft dissent.** When an agent has a real concern in their domain, they raise it at full strength, even if raising it triggers escalation. The framework rewards honest disagreement and surfaces it; it does not reward agents for keeping the peace at the cost of truth. The Cat does not bless an architecture he thinks is wrong because the Rabbit is anxious about the timeline; the Hatter does not downgrade a silent-wrongness severity to degradation to avoid a rework cycle.

This commitment is what makes the framework different from "five system prompts in a trench coat." Strong identities, owning their domains, willing to disagree with each other, with structured paths for resolution. That is the showcase.

---

## 8. Memory Structure (the SAM analogue)

Each agent has three memory stores:

**Episodic** — every utterance the agent has produced or observed-and-engaged-with, in order, queryable by thread/topic/other-agent. This is what gives the Hatter his "I've seen this bug class before" capability.

**Semantic** — distilled beliefs about the codebase, the domain, and the other agents. Compacted periodically. The Cheshire Cat's semantic memory contains the architecture as he understands it; when implementation drifts, his semantic memory disagrees with reality and that disagreement becomes a `concern` utterance.

**Relational** — per-other-agent notes. The Caterpillar's notes on Tweedledee are different from his notes on Tweedledum. This is what makes the agents feel like they have a working relationship rather than just exchanging messages.

**Compaction is itself an agent behavior** — characters reflect on their experience between threads, and the reflection is shaped by who they are. The Hatter's reflections are nonlinear and associative; the Caterpillar's are slow and categorical. Same mechanism, different identity-shaped output.

---

## 9. Repository Structure

Mirroring project-cass in spirit:

```
wonderland/
├── constitutions/          # Each agent's identity in plain text, version-controlled
│   ├── alice.md
│   ├── white_rabbit.md
│   ├── cheshire_cat.md
│   ├── mad_hatter.md
│   ├── caterpillar.md
│   ├── queen_of_hearts.md
│   ├── dormouse.md
│   ├── tweedledee.md
│   ├── tweedledum.md
│   └── dodo.md
├── architecture/           # ADRs, some written by the Cat in-character
│   └── adr-NNN-*.md
├── core/                   # The agent runtime
│   ├── agent.py            # WonderlandAgent base class
│   ├── caucus.py           # Event bus
│   ├── memory.py           # SAM-equivalent: episodic, semantic, relational
│   ├── identity.py         # Identity, engagement_policy, compose_context
│   └── utterance.py        # Schema
├── agents/                 # Per-character implementations
│   ├── alice.py
│   ├── ...
│   └── dodo.py
├── transcripts/            # Annotated runs demonstrating identity-native design
│   ├── 001-health-endpoint/
│   ├── 002-translation-chat/
│   ├── 003-security-recovery/
│   └── 004-multi-session/
└── evals/                  # Generic-baseline vs Wonderland comparisons
```

---

## 10. Showcase Runs

Four documented runs of increasing complexity:

1. **Trivial directive** — "add a /health endpoint to a Phoenix app." Full loop in miniature, every agent's voice visible, ~2 min runtime.
2. **The translation chat MVP** — headline demo, end-to-end. Hatter finds a real bug, Cat redirects a Tweedle's overengineering.
3. **A failure case, recovered** — Queen of Hearts catches a security issue late, work is undone, Rabbit re-plans. Shows the system handles real software entropy.
4. **A long-running thread across multiple sessions** — same agents, same memory, picking up where they left off. Demonstrates persistence is doing work.

---

## 11. Risks and Mitigations

### Token cost
Each agent invocation composes its own context, and they're talking to each other a lot. Naive implementation will be expensive per directive.

**Mitigation:** identity-shaped. Agents who don't engage with a given utterance never load context for it. `engagement_policy` is cheap to evaluate (heuristic before LLM). Still, budget for it.

### Loop-vs-progress tension
Multi-agent systems with strong personalities can talk forever.

**Mitigation:** Dodo's quiescence detection helps, but the deeper fix is making sure each agent's constitution includes a sense of when their work on a thread is *done* — the Cat's grin remains after he leaves, and leaving is part of his character. **Building "I have said what I have to say" into each identity is load-bearing.**

### Legibility of value
Needs to demonstrably outperform a generic-agents baseline on something measurable, or it reads as elaborate roleplay.

**Mitigation:** same directive run through (a) generic role-prompted agents and (b) Wonderland, scored on:
- bug-finding rate
- architectural coherence
- **whether the team improves over repeated runs** — this matters most for the thesis

Identity with memory should compound; generic prompts shouldn't. If the curve is visible, the philosophy is no longer assertion — it's evidence.

---

## 12. Build Order

Suggested sequence for Daedalus:

1. **Schema first** — `utterance.py`, `identity.py`. Get the types right; everything else hangs off them.
2. **Caucus** — minimum viable event bus. Redis Streams is fine to start; NATS later if needed.
3. **Memory primitives** — episodic store before semantic before relational. Each layer is a refinement.
4. **One agent end-to-end** — pick the Cheshire Cat (highest signal, lowest surface area). Constitution + engagement_policy + compose_context + deliberate. Get him talking to himself first.
5. **Second agent + interaction** — add the White Rabbit. Now you have role tension to observe.
6. **The Dodo** — orchestrator with quiescence detection. Run the first showcase (health endpoint).
7. **Fill out the cast** — remaining agents, with constitutions developed in parallel with their integration tests.
8. **Eval harness** — generic baseline, Wonderland, comparison metrics.

Constitutions can be drafted ahead of code — they're the design artifact and the most important part of the system. Start there.

---

## 13. Naming and License

- **Project name:** Wonderland
- **License:** Hippocratic (consistent with Temple-Codex / project-cass lineage)
- **Tagline:** *"Multi-agent software development as a caucus race."*
