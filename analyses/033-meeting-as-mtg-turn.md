# Analysis 033 — Meeting as MtG turn: phases, priority, and turns-as-budget

**Date:** 2026-05-08
**Status:** Architecture proposal (no run yet).
**Provenance:** Drafted in response to observed sprawl patterns across analyses 029-032. Not validated against a run; this document articulates the proposal so it can be argued with before code lands.
**Result (predicted):** **Adopt phases + priority rotation + turns-as-budget. Skip the stack. The proposal addresses constitutional failure modes structurally rather than via per-character directive bounds — the engine gains a way to *measure* sprawl and withdrawal from outside the agent, which the current substrate cannot.**

## What this is

A proposal to lift three primitives from Magic: The Gathering's turn structure into Wonderland's meeting engine: **phases**, **priority**, and **turns-as-budget**. Plus an explicit decision to *skip* the fourth primitive — **the stack** — because it solves a problem Wonderland doesn't have.

The current meeting model is: a roster of agents, a directive, a budget in dollars, and an engagement policy that decides who speaks. Meetings end when the budget is exhausted or the engagement policy declares quiescence. Within a meeting, there's no formal turn structure — agents emit utterances when the policy fires, and the policy is heuristic-then-LLM.

The proposed model adds structure: meetings have **phases** (workflow-defined), each phase grants **priority** to each cast member in rotation, and meetings are **budgeted in rotations**, not dollars. Dollars become a soft cap layered on top, not the primary structure.

## What problem this addresses

Three patterns recur across recent analyses:

### Hatter sprawl (analysis 030)

030 F3 named the shape directly: **Hatter's failure mode doesn't have a single direction.** Bound meta-discussion, he sprawls into code. Bound code, he sprawls into more scenarios. The directive needs to bound *all* available expansion paths simultaneously to compress him. The current fix is per-directive bounds added by hand, run-by-run.

The structural reading: **Hatter has no way to pass.** When the engagement policy fires for him, he produces output. There is no first-class "I have nothing to add for this phase" action. So whatever's currently unbounded becomes the expansion path.

### Tweedle volume (analysis 032)

032 reframed the cost story: Tweedles are 71.9% of total cost, not Hatter. The volume comes from M5 implementation iteration — `write_file` → `run_tests` → `write_file` cycles. This isn't sprawl in the same sense as Hatter; it's load-bearing work. But it's also unbounded: the only reason a Tweedle stops iterating is that the meeting budget runs out.

The structural reading: **iteration count is currently emergent, not structural.** "Three rotations max" would give a measurable cap that doesn't anchor the LLM the way "iterate ~3 times" did in 030 F1.

### Cat withdrawal (constitutional failure mode, §VIII)

Cat's failure mode is the inverse of Hatter's: the Cat goes silent after an ADR lands. There is currently no way for the engine to *see* this, because silence is indistinguishable from "engagement policy didn't fire." The Cat could be deliberately withholding, or the policy could have skipped him.

The structural reading: **passing should be a first-class action**, distinct from "wasn't asked to speak." If priority rotates and every cast member must explicitly act-or-pass, withdrawal becomes observable from outside the agent.

### The unifying observation

Every constitution's §VIII names a failure mode. None of them are currently observable from the engine's perspective — they're inferred post-hoc by reading the transcript. **Phases + priority give the engine an outside-the-agent measurement primitive: who passes when, who never passes, who passes always.** That is a substrate capability we don't currently have.

## The proposed model

### Phases (workflow-defined, not engine-defined)

A meeting is a sequence of phases. Phases are declared by the workflow YAML, not hard-coded. Examples:

- **TDD meeting** (M4): `red → green → refactor`
- **Tea Party** (M4 in tdd-serial): `clarify → red-tests → wait`
- **Trial** (M6): `present → review → defend → verdict`
- **Caucus Race** (M1): `propose → critique → consolidate`

Each phase has its own priority rotation. Phase boundaries are observable; phase-end is a meeting event the engine emits.

### Priority (rotation per phase)

In each phase, every cast member gets one **priority window**. Order is determined by the phase definition (workflow can declare an order, otherwise default-roster-order). On their window, an agent does exactly one of:

1. **Act** — emit one utterance, optionally with tool calls.
2. **Pass** — explicitly decline this window.

The phase advances when **all cast members pass in succession** (no act between two passes). Or when the workflow declares the phase's exit condition is met (e.g., a specific artifact shipped).

This gives **pass as first-class action**. Cat passing is not the same as Cat not being asked. Hatter consuming his window with one utterance and then passing on the next rotation is not the same as Hatter monologuing across an unbounded number of priority windows.

### Turns as budget

A meeting has a **rotation budget**, not (only) a dollar budget. "This meeting is 3 rotations" means each phase runs for at most 3 full passes around the cast, after which it's force-exited regardless of agent state.

Dollars stay as a **soft outer cap** — an emergency stop if pricing catastrophically diverges from the rotation expectation. But the primary unit of meeting time is rotations.

This rhymes with the existing memory `feedback_no_wall_clock_in_turn_based`: Wonderland is turn-based; rotations are the natural budget unit, dollars are an artifact of the underlying API and shouldn't drive the engine's pacing.

### What we skip: the stack

MtG's stack is a LIFO of pending actions, with players able to interject "instant-speed" responses before resolution. It exists because MtG is adversarial 2-player and needs a precise interrupt model.

Wonderland's meetings are 3-5 mostly-collaborative agents. The interrupts we'd want — Alice grounding, Cat questioning a premise, Queen forcing closure — are already expressible via priority rotation: those agents' priority windows come up next, and what they do in those windows is interjection-shaped. Adding a stack on top buys precision we don't need at a complexity cost we'd pay every turn.

**Decision: skip the stack initially.** Revisit if a specific meeting pattern surfaces that priority rotation alone can't express.

## How this addresses each failure mode

| Failure mode | Current handling | Under phases + priority |
|---|---|---|
| Hatter sprawl | Per-directive bounds (030 F3) | One utterance per priority window. Sprawl across windows is bounded by rotation count. |
| Tweedle iteration unboundedness | Meeting budget exhaustion | Rotation budget caps iteration count structurally (and without anchoring, since "3 rotations" describes the meeting, not the per-Tweedle iteration count). |
| Cat withdrawal | Invisible to engine | Pass-vs-not-asked distinction makes withdrawal observable. |
| Queen categorical force | Rare emission | Queen's window comes up like everyone else's; she passes when not load-bearing, acts when force is needed. |
| Hatter monologue | No structural cap | Single utterance per window; next window goes to next cast member. |
| Synthetic consensus | Detected post-hoc via guard instrumentation | If everyone passes after one agent acts, that's "consensus by no-one-pushed-back" — observable, can fire the existing guard differently. |

The shape that emerges: **failure modes become engine-visible.** The engine can count passes per agent per phase per meeting. A Hatter who never passes is a sprawl-mode Hatter. A Cat who always passes after his first utterance is a withdrawal-mode Cat. We don't need to *name* this in the agent's prompt; we measure it from outside.

## Implementation sketch

This is a substrate change, not a behavioral one. Touches:

1. **`Meeting` engine** — currently has `roster` + `engagement_policy`. Adds `phases: list[Phase]` + per-phase `priority_order: list[AgentID]`. The meeting loop becomes: for each phase, rotate priority, collect act-or-pass per agent, advance when all-pass-in-succession or phase-exit-condition met or rotation-budget exhausted.

2. **`Workflow` YAML schema** — adds `phases:` per meeting block. Default phases (a single phase named `discussion`) keep backward compatibility for workflows that don't care.

3. **`RunEvent`** — adds `PhaseStarted`, `PhaseEnded`, `PriorityWindowOpened`, `AgentPassed`. Existing observers (HistoricalRunHandle, MockTurtleHandle, LiveRunHandle) all have to handle the new events.

4. **Engagement policy** — currently decides "who speaks next." Under the new model, it decides "given this agent's priority window, do they want to act or pass?" That's the same heuristic-then-LLM logic, just re-scoped.

5. **Constitutions** — *do not* change. The phases + priority structure is engine-side. Constitutions don't need to know about phases (though they may benefit from being aware that "I can pass" is a first-class option).

6. **Telemetry** — adds per-phase, per-window cost attribution. The TUI live view gets a phase indicator.

## What this proposal doesn't address

- **Multi-priority-window actions.** What if Hatter wants to do a long planning step that spans multiple windows? Under this model, he can't — he gets one utterance per window. If this matters, it argues for a per-agent "I'd like to extend my window" mechanism, but that's the stack creeping back in. For now, force long thinking into a single utterance; if that's too constraining, revisit.
- **Inter-meeting structure.** Workflows already have meeting sequences (M1 → M2 → M3 → ...). Phases are intra-meeting. The two are orthogonal.
- **Dynamic priority order.** MtG has fixed turn order. We could allow the engagement policy to set priority order per phase based on directive content — but this is a complication to defer until we know the static ordering is wrong.
- **Validation against a real run.** This proposal is unargued-with by reality. The first implementation should ship behind a `phases:` opt-in on the workflow so existing workflows stay on the old model until phases prove out.

## Risk: anchoring (the 030 F1 lesson)

Analysis 030 F1 surfaced a sharp lesson: **directives that quantify expected effort tend to anchor the LLM rather than cap it.** "3 cycles is enough" was read as "do at least 3."

The MtG model risks the same shape. If we tell agents "you have one utterance per priority window, and there will be 3 rotations," they may stretch their utterance to fill the implied time, or generate filler passes to consume the budget.

Mitigation: **rotations are an engine concept, not an agent concept.** Agents don't see "3 rotations remaining" in their context. They see their priority window, the directive, the meeting state, and they act-or-pass. The engine counts rotations from outside. This is the same separation that keeps wall-clock out of agents' contexts (per the no-wall-clock memory).

If we want to surface budget pressure to agents, we surface it as state-of-the-meeting ("M5 is on its third pass with no fix landing") rather than as a remaining-rotations counter.

## What's next

1. **This document, reviewed.** The decision to skip the stack is the load-bearing call; if reviewers think the stack is necessary, the proposal needs revising.
2. **Roadmap items filed** for the engine work, the workflow schema, and the observer-side event additions.
3. **First implementation behind opt-in.** Add `phases:` to one workflow (probably `tdd-serial`) and run it. Compare cost + output quality against the 032 banner ($4.7236, 1080 LOC, 10 test files). The headline metric is whether Hatter's call count drops without his test quality dropping.
4. **If the first run is good:** roll phases into the other workflows, deprecate the no-phases path.
5. **If the first run regresses:** the analysis is a stronger artifact than the code — we still learned which structural primitive doesn't transfer.

## Headline

**Lift phases + priority + turns-as-budget from MtG; skip the stack.** The win is that constitutional failure modes (sprawl, withdrawal, monologue) become engine-observable rather than transcript-inferred. Substrate gains a measurement primitive it currently lacks. The risk is anchoring, mitigated by keeping rotations engine-side and out of agent context. First implementation lands behind a workflow opt-in so we can compare against the 032 banner with controlled variables.
