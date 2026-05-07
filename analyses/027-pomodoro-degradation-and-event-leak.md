# Analysis 027 — M2.5 fired wired-but-silent, exposed a deeper event-leak bug, demonstrated graceful degradation

**Date:** 2026-05-07
**Run:** Pomodoro tracker MVP, TDD workflow, with the full feat/alice-in-m2 branch in flight (5 substantive changes since analysis 026).
**Snapshot:** [analyses/data/027-pomodoro-degradation-and-event-leak/](data/027-pomodoro-degradation-and-event-leak/)
**Result:** **The new M2.5 phase wired correctly but didn't fire under live conditions; the Tweedles noticed the missing artifacts in their context and improvised by reading tickets from disk; and along the way we identified the actual root cause of the 0-calls M5 pattern observed in analyses 026 and 027 — cross-meeting event leakage, not the quiescence-on-startup race the prior fix targeted.**

## What we tested

Five changes shipped in this branch since analysis 026:

| Commit | Change | Status after this run |
|---|---|---|
| `042cf8f` | Mark thread COMPLETE on MEETING_BUDGET (close late-publish race) | **Validated** — three late-publish suppressions visible in the log, all correctly attributed to closed threads |
| `44e82dd` | Bump TDD M4 budget 1.20 → 1.50 | **Insufficient** — M4 still hit MEETING_BUDGET at $1.57 |
| `10dd160` | Gate idle-keyed quiescence on member engagement | **Untestable in this run** — bug was upstream (see F2) |
| `e1aa221` | Name meetings after book events | **Validated** (with caveat) — labels render; agents now see them in directive context |
| `c14b230` | Feature artifact substrate (FeaturePayload + Rabbit `feature` decision) | **Wired correctly, didn't fire** — no parse errors, just silence |
| `6716615` | M2.5 (Advice from a Caterpillar) phase wired into TDD | **Wired correctly, didn't fire** — see F1 |
| `ff7e428` | Prepend meeting label/name to convenor directive | **Validated** — directive utterance bodies include the prefix |

## What shipped vs what came out

| Metric | This run | Geocities baseline (analysis 026) |
|---|---|---|
| Wall clock | 1200.0s (TIMEOUT) | 1108s |
| Cost | $2.04 | $2.74 |
| LLM calls | 193 | 208 |
| Tickets (M2) | 7 | 11 |
| **Features (M2.5)** | **0** | n/a (no M2.5 in 026) |
| Test files (M4) | 22 .py files on disk | 24 .py files on disk |
| Production code (M5) | **0 lines** (M5 never ran) | 0 lines (M5 never ran) |
| Per-agent breakdown | Hatter $0.66, Tweedledum $0.65, Tweedledee $0.42 | Tweedles dominated similarly |

This run was *cheaper* than the Geocities run despite running longer because so much of M5/M6 produced nothing. The work that did happen (M1 scoping, M2 decomposition, M4 test-writing) was high-quality.

## Findings

### F1 — M2.5 wired correctly but Rabbit chose silence under live LLM conditions

The new composition phase did everything *structurally* right:

- The meeting was registered with the correct roster (Alice + Caterpillar + Rabbit)
- Seeds resolved correctly (4 utterances: ADRs + stories + tickets)
- Dodo's directive landed on the bus with the new prefix `**M2.5 — Advice from a Caterpillar.**`
- The agents consumed the directive (7 LLM calls happened)
- No parse errors fired — Rabbit's new `feature` decision schema validated cleanly

What didn't happen: **no feature artifacts.** The `.wonderland/features/` directory doesn't exist. Rabbit's per-run call count was 2 total (one in M2 to ship tickets, one in M2.5 — probably silence). All three agents in the M2.5 roster deliberated and chose silence.

This is a directive-shape problem, not a wiring problem. Same diagnostic shape as the M4 two-operations-per-scenario fix in `56c3b16` — the framework can host the meeting but the prompt isn't forceful enough to make the LLM emit. Three plausible directive issues:

1. **The "Advice from a Caterpillar" prefix may have made Rabbit read the meeting as not-his-to-drive.** The literary parallel — Caterpillar's chapter is *about* his interrogation of Alice — could have biased the LLM toward "this is Caterpillar's show, I'll defer."
2. **The "your move is `feature`" instruction sits halfway through the directive,** after a long preamble explaining the phase context. The forceful imperative may need to come *first*.
3. **The "default to silence unless the work is drifting" framing extends from M2's directive but probably shouldn't apply to Rabbit in M2.5.** In M2, Rabbit drives and Alice/Cat default to silence. In M2.5, Rabbit *also* needs to drive (he writes the features), but the directive framing may have spread "default to silence" too broadly.

Knock-on effect: M3 ran with a degraded seed manifest (only ADRs, no features) for 38s / $0.08, instead of the meatier feature-bound contract negotiation we designed for. The Tweedles' contracts were thinner than analysis 026's.

### F2 — The 0-calls M5 pattern wasn't the quiescence race; it was cross-meeting event leakage

This is the deeper finding, and it changes our interpretation of analyses 026 and 027.

When M5 started in this run, the log showed:
```
M5 START · implementation · roster=['tweedledee', 'tweedledum'] · seeds=7
[t=1168.57s] <thread_monitor> running → complete
[t=1168.57s] <complete>
M5 END · COMPLETE · 0.0s · 0 calls · $0.0000
```

Same pattern as 026 and 027. Initial hypothesis (and the target of the `10dd160` quiescence-on-startup fix): the thread monitor was firing a quiescence transition immediately on convene, before any agent had engaged. Adding a `member_engagements` gate would block that.

**That fix was correct semantically but didn't address the actual root cause.** Tracing the run carefully — the 8 utterances on the M5 thread, none of them an ACKNOWLEDGMENT, no path through `_check_completion`, no QUIESCENT state in the log — reveals what's actually happening:

1. M4 hits MEETING_BUDGET → workflow exits M4's events loop
2. `runner.mark_thread_complete("test-scenarios", ...)` (from `042cf8f`) transitions M4's thread to COMPLETE
3. Runner's `_react_to_state(COMPLETE)` puts a `kind="complete"` event on the runner's event queue with `payload={"thread_id": "test-scenarios"}`
4. Workflow advances to M5, calls `runner.convene("implementation", ...)`, starts M5's events loop
5. M5's events loop reads the **leftover M4-thread complete event from the queue**, sees `kind="complete"`, and breaks out:

```python
if event.kind in ("complete", "timeout", "aborted"):
    outcome = event.kind.upper()
    break
```

The check on `event.kind` doesn't filter by `event.payload["thread_id"]`. So *any* meeting's COMPLETE transition ends the *next* meeting if there's queue leakage between them.

**The earlier fix in `042cf8f` made this worse**, because it ensured a COMPLETE transition fires *immediately and synchronously* on MEETING_BUDGET exit. Pre-`042cf8f`, the COMPLETE transition was less reliable (waited on dodo nudge cycles or wall-clock quiescence), so the leak was a race condition. With the fix, it became near-deterministic.

The actual fix is in this analysis's accompanying commit (`ede5651`): filter `complete` events by thread_id before treating them as the current meeting's completion. `timeout` and `aborted` stay unconditional (they're global runner events without thread-ids).

**What this means for the layering of fixes shipped this branch:**

- `042cf8f` (mark_thread_complete on MEETING_BUDGET) is still correct for its stated purpose (suppressing late publishes from in-flight deliberations). Side effect of generating a leakable complete event is now harmless because of the filter.
- `10dd160` (quiescence-on-startup gate) is also correct semantically but was untestable in production runs because the events loop was exiting before any quiescence check could fire. Keeping the gate — it's the right semantics regardless and will matter for cleaner edge cases.
- `ede5651` (this fix, cross-meeting event filter) is the actual unblocker for M5.

### F3 — Graceful degradation: the Tweedles improvised when their seeds were thin

This is the *interesting* finding from a paradigm-design perspective.

M3 (Tweedledum and Tweedledee) ran with a degraded seed manifest because M2.5 didn't produce features. The seed query was:
```yaml
seeds:
  - from: scoping
    kinds: [adr]
  - from: composition
    kinds: [feature]
```

With zero `feature` artifacts in capture, M3 saw only the ADRs. The Tweedles' M3 directive references "each feature in your context names a `stack_span`" — a guidance that's now *factually wrong* given the actual seed manifest.

What the Tweedles did:

1. **Read the directive carefully and noticed the mismatch.** Tweedledee emitted a `concern` (later suppressed by the late-publish guard, but visible in the log): *"Tweedledum is correct: the directive references 'each feature in your context names a stack_span,' but the engagement st…"* (truncated). The agents *observed the contract violation* between directive and seed reality.

2. **Reached for alternative data via tools.** Tweedledum's later late-publish referenced `ticket-003` by number. Tweedles aren't supposed to see tickets in M3 anymore (that seed query was removed in `6716615`). The reference can only have come from `list_files`/`read_file` on `.wonderland/tickets/`. They discovered the disk channel when the bus channel was thin.

3. **Stayed in their roles.** They didn't try to *be Rabbit* and re-emit features. They worked with the tickets-as-they-existed, which is the legitimate move for their character (negotiate against what the Rabbit produced).

This is graceful degradation through three converging properties:
- **Constitutional disposition**: Tweedles want concrete artifacts to negotiate against; abstract-only directives are character-uncomfortable.
- **Tool access plus working-tree visibility**: `list_files` and `read_file` are part of their toolkit; the disk artifacts are reachable.
- **Bus/disk decoupling** (the same property we identified as a *problem* in analysis 026): the bus seed manifest can be thin while the disk artifact tree is full, and characters with tools can find the alternate path.

Most LLM pipelines treat missing data as an error condition. Here it's a problem the agent has motivation to solve within its role — and the framework substrate makes the recovery structurally possible.

### F4 — Meeting names in agent context: directive-prefix mechanism works

The `ff7e428` change (prefix every directive utterance with `**<label> — <name>.**`) shows up correctly in the bus utterances. The Dodo's M2.5 directive begins:

> `**M2.5 — Advice from a Caterpillar.**\n\nComposition thread. The tickets in your context are settled...`

Agents read this in their context window. **Whether the framing visibly shifts behavior is a separate question** — and this run's data is ambiguous because the M2.5 phase didn't fire for unrelated reasons. F1's hypothesis 1 (the prefix may have biased Rabbit toward Caterpillar's-show) is testable directly with a directive variant that puts Rabbit's role front-and-center.

### F5 — M4 budget cap fires consistently, even after the bump

The bump from $1.20 → $1.50 (`44e82dd`) didn't keep M4 under cap on the pomodoro directive. Actual M4 cost: $1.57 (3 cents over the new cap). Across the three TDD runs we have data for:

| Run | M4 cost | M4 cap |
|---|---|---|
| Analysis 025 (Geocities) | $0.55 | $1.20 |
| Analysis 026 (Geocities) | $1.30 | $1.20 |
| Analysis 027 (Pomodoro) | $1.57 | $1.50 |

Variance is high and not directly tied to directive scope — Pomodoro is *smaller* than Geocities but cost more. The driver appears to be Hatter + Tweedles' clarification rounds (Alice asks questions, Tweedles answer, Hatter writes more scenarios). M4 is the meeting where iteration most dramatically affects cost.

A future fix worth considering (filed informally for now): cancel in-flight LLM calls on MEETING_BUDGET exit, not just suppress their late publishes. Currently we pay for the in-flight call but discard the result. Cancellation would save the API spend.

## What this analysis doesn't show

- **N=1 on the pomodoro directive.** The graceful-degradation observation needs to be reproduced — could be a pomodoro-shaped accident, not a general property.
- **No production code shipped.** M5 didn't run; M6 timed out at 31s with Caterpillar still gathering context. The framework's bug-discovery surface (analysis 025's headline result) wasn't exercised.
- **The M2.5 directive fix isn't yet validated.** F1 names three hypotheses for why Rabbit chose silence; we don't know which one is load-bearing until we iterate the directive and rerun.

## What's next

The combined effect of the fixes now shipped (`042cf8f` + `10dd160` + `ede5651`) should mean: M4 hits MEETING_BUDGET → M4's thread marked COMPLETE → late publishes suppressed → the COMPLETE event for M4 is filtered out of M5's events loop → M5 starts cleanly with no leftover events ending it prematurely → Tweedles get the directive and actually deliberate.

Three things teed up for the next iteration:

1. **M2.5 directive fix** — restructure the prompt to put Rabbit's `feature` move first, before the role descriptions. Reduce the "default to silence" framing's spread to Alice and Caterpillar only. Possibly drop the "Advice from a Caterpillar" prefix from the agent-visible context to avoid the "this is Caterpillar's show" bias. Same shape as `56c3b16`.
2. **Test run validating the event-leak fix** — even if M2.5 still doesn't emit features, M5 should now actually *run* (deliberate, fail to find tests on the bus seed manifest, possibly improvise via disk read like the Tweedles did in M3 here).
3. **Analysis writeup feeds into a README callout** about graceful degradation as an emergent property of character-shaped systems. The observation is paradigm-grade: most LLM pipelines fail silently; Wonderland degrades visibly because agents have intentions that drive recovery. Worth surfacing prominently.

## Headline

**The framework's substrate is in better shape than the M5-doesn't-run pattern suggested.** The 0-calls M5 across analyses 026 and 027 wasn't a deep design flaw — it was a single-line bug in the workflow event-loop where complete events from one meeting could end the next meeting's events loop. The fix is small. What survives the analysis is more interesting than what got fixed: agents reading directives carefully and noticing when the seed manifest contradicts them; agents finding alternative data channels through their tools when the formal channel is thin; the framework degrading visibly rather than silently when phases fail.

The literary parallel keeps earning its keep — the recovery pattern is *because* the agents have characters with intentions, not despite it.
