# Analysis 014 — Cross-Meeting Composition: ADR-001 → Five Agreed Contract Notes

**Date:** 2026-05-05
**Phase milestone:** P6.T36 prep — first cross-meeting composition test
**Component:** Block 2b convene mechanism (simulated by hand) +
the calibrated Cat from analysis 013
**Run transcript:** [`data/014-cross-meeting-composition/run.log`](./data/014-cross-meeting-composition/run.log)
**Telemetry:** [`run-20260505T182314.json`](./data/014-cross-meeting-composition/run-20260505T182314.json)
**Shipped contract notes:** [`data/014-cross-meeting-composition/contract-notes/`](./data/014-cross-meeting-composition/contract-notes/) — 5 files, all reaching state=agreed
**Setup script (now retired demo):** [`scripts/contract_followon_demo.py`](../scripts/contract_followon_demo.py)
**Comparison baseline:** [analysis 013](./013-cat-calibrated-ships.md) — same
calibrated framework, single meeting, ADR shipped

> The Tweedles took ADR-001 (shipped in analysis 013) and produced
> *five* contract notes — all reaching state=agreed — in 85 seconds
> for 10 cents. One was the explicitly-routed WebSocket state
> management question; four were follow-on contract surfaces the
> pair surfaced from ADR-001's tradeoffs without being asked. This
> is the first evidence of cross-meeting composition: artifact A
> from meeting 1 driving artifact B (and B+1, B+2, B+3, B+4) in
> meeting 2, with the pair self-organizing the contract surface.

---

## What this run tested

After analysis 013 shipped ADR-001, the natural next test was
whether downstream meetings actually compose against shipped
artifacts. The first attempt published the meeting goal as a
*directive* to the Tweedles + Cat + Dodo roster — **null result**:
Tweedles' engagement rules `almost_never` engage with directives
(they wait for upstream artifacts: stories, tickets, proposals).
The Cat saw the directive, deliberated, chose silence. Total: 1
LLM call, 0 artifacts, $0.009.

That null is informative. It surfaces what Block 2b's convene
mechanism actually has to do: when a follow-up meeting opens, the
*prior meeting's relevant artifacts* need to land on the new
meeting's bus as utterances from the original speakers — not as
prose in a directive. The Tweedles engage with Cat-spoken
proposals; that's the trigger we need.

The second attempt simulated Block 2b by hand: synthesize a
Cat-spoken `proposal` utterance carrying ADR-001's full payload
as an `adr` artifact, publish it to the (rostered) bus before
agent loops start. Same roster, same 4 agents, same goal. This
time the Tweedles fired.

## Headline numbers

| metric | value |
|---|---|
| total cost | **$0.10** (under the $1.00 cap by 10x) |
| total LLM calls | 10 |
| outcome | complete @ 85s |
| contract notes shipped (distinct files) | **5** |
| **contract notes reaching state=agreed** | **5 of 5** ✓ |
| Cat involvement | 1 call, 1 substantive concern responding to Tweedles |
| Tweedles split | Dee 4 calls / Dum 5 calls (well-balanced) |
| schema-rejection drops | 2 (mark_agreed without resolution / contract_version) |

## What shipped

Five contract notes, all reaching `agreed`:

1. **Translation Status Signal Shape** — locked at v1
2. **Translation SLA Fallback Behavior** — locked at `v1
   (translation_failed event with failure_reason enum: timeout |
   service_error | network_error)`
3. **Translation Caching Strategy and GDPR Surface** — locked at v1
4. **WebSocket Statefulness: Sticky Sessions vs. Shared Cache** —
   locked at `v1 (backend translation service is stateless; each
   request includes message_id, source_language, target_language;
   frontend manages client-side cache lifecycle)`
5. **WebSocket Message Envelope Extension for Translation Status** —
   locked at v1

#4 is the originally-routed open question from ADR-001
("WebSocket state management strategy — Tweedles to propose").
**The other four are follow-on contract surfaces the Tweedles
surfaced themselves**, identified by reading ADR-001 carefully:

- The 2s SLA implies fallback semantics → Contract Note #2
- The translation-status signal in the WebSocket message implies
  envelope shape → Contract Notes #1 and #5
- Persisting originals only + translating on read implies a
  client-side caching policy with GDPR implications → Contract
  Note #3

The Tweedles read the architecture, identified the contract
surfaces it implies, and locked each one in the same session. Each
contract note has both Tweedles' impact assessments filled in and
a resolution naming the agreed shape.

## The flow itself is the evidence

Looking at the timeline (full log in run2.log; condensed here):

```
t=  0s  cheshire_cat  proposal       [seeded — ADR-001]
t=  7s  tweedledum    concern        Cat's proposal sound on architecture; surfaces three backend implications
t=  9s  tweedledee    contract_note  PROPOSE: Translation Status Signal Shape
t= 13s  cheshire_cat  concern        Tweedledum surfaced three load-bearing implications
t= 18s  tweedledum    contract_note  RESPOND to Status Signal Shape
t= 27s  tweedledee    contract_note  PROPOSE: SLA Fallback, Caching, WebSocket Statefulness (3 notes)
t= 41s  tweedledum    contract_note  RESPOND to all three
t= 44s  tweedledee    contract_note  AGREE on Status Signal Shape; PROPOSE Envelope Extension; RESPOND on caching
t= 56s  tweedledum    contract_note  RESPOND on Envelope; AGREE on SLA Fallback, Caching, WebSocket Statefulness
t= 67s  tweedledee    contract_note  AGREE on Envelope Extension
t= 85s  thread → COMPLETE
```

Two specific shapes worth noting:

1. **The Cat showed up exactly once (substantively).** At t=13s
   the Cat surfaced three backend implications Tweedledum had
   raised — basically endorsing them as architecturally
   relevant without taking over the negotiation. Then the Cat
   went silent and let the Tweedles drive the rest. This is the
   "available for clarification" pattern from the meeting goal.
   Total Cat cost: $0.003.

2. **The Tweedles batched contract operations.** At t=27s
   Tweedledee proposed *three* contract notes in one utterance
   — recognizing that all three were implied by the same prior
   move and were better surfaced together. At t=44s and t=56s
   they batched mark_agreed + respond + propose actions.
   Efficient negotiation; not one note at a time.

## What didn't work — and why it's encouraging

Two `mark_agreed` actions failed schema validation because the
LLM omitted required `resolution` and/or `contract_version`
fields. Each was caught at parse time, dropped to silence,
logged. **The other utterances picked up the slack** — the team
had redundancy across the two Tweedles, so a dropped utterance
didn't break the negotiation. All 5 contract notes still
reached agreed despite the rejections.

This is what we want the schema to do: refuse incomplete commits
without breaking the run. The earlier per-agent allowed-acts
issue (analysis 011, roadmap `956032a5`) caused the same shape
of drop but in cases where the dropped utterance *was* the only
substantive move on the table; here, the team's structure
absorbs the drop. That suggests the schema-rejection failure
mode matters most when there's no redundancy, less so when the
work is parallel.

## What this means for Block 2b/2c/2d

The deferred convene/invite/multi-thread mechanisms now have a
concrete job to do:

- **Block 2b (convene)**: when a meeting completes with artifacts,
  the Dodo (or whoever convenes) republishes those artifacts as
  utterances from their original speakers into the new meeting's
  bus, *before* the agent loops start. The Tweedles' engagement
  rule `always(SpeechAct.PROPOSAL, condition=speaker_is("cheshire_cat"))`
  fires; they engage; negotiation proceeds. The minimal
  implementation is something like:

  ```python
  Runner.convene(
      goal="...", roster={...},
      seed_artifacts=[(prior_meeting_id, [list of artifact slugs])]
  )
  ```

  which scoops the listed artifacts from the prior meeting's
  artifact registries and republishes them as utterances from
  the original speakers. ~50 lines.

- **Block 2c (invite)**: the test didn't need it. The Cat was
  in the room from the start; the Tweedles drove. We still
  don't have a concrete test that requires mid-flight buzz-in.
  Defer further.

- **Block 2d (multi-thread)**: the test was single-thread. We
  still don't have a concrete test requiring concurrent
  threads. Defer further.

So the right next move is **just Block 2b**, with the
specific shape: the convene mechanism re-publishes prior-meeting
artifacts as Cat-spoken (or Rabbit-spoken / Alice-spoken)
utterances into the new meeting's bus.

## The cost arc

| analysis | scenario | cost | substantive output |
|---|---|---|---|
| 011 | open bus, no fixes | $5.58 | 8 stories, 16 scenarios, 0 ADRs, 0 contracts |
| 012 | rostered, uncalibrated Cat | $0.058 | 6 stories, 0 ADRs, 0 contracts |
| 013 | rostered, calibrated Cat | $0.13 | 6 stories, **1 provisional ADR** with named open questions |
| 014 | follow-on with simulated convene | $0.10 | 1 ADR (carried forward) + **5 agreed contract notes** |

Cumulative cost from 013 + 014: **$0.23 for one architectural
decision and five agreed contract specifications**. The framework
is now in a cost regime where you could run dozens of these per
day on real work for the cost of a single Opus turn.

## What this is and isn't evidence of

**It is evidence that the framework's compounding-artifacts thesis
holds at small scale.** Artifact A drives artifact B (and B+1...
B+4). Each agent stays in domain. The pair self-organizes the
contract surface. Cost stays bounded and predictable. The work
shape — provisional ADR followed by detailed contracts — matches
how real engineering teams actually decompose decisions.

**It isn't evidence that the framework competes with Opus on
absolute output quality.** The contract notes are detailed and
internally coherent, but I haven't compared them to what Opus
would produce given ADR-001 + the same goal in one shot. That
would need the P7 eval harness to be honest. My intuition: Opus
would produce comparable text, but probably not five distinct
contract notes, and probably not with both-sides-impact
assessments that look like real frontend/backend negotiation.
The structure-from-identity is the part that's hard to one-shot.

**It also isn't evidence at scale.** Five contract notes from a
single ADR is a small test. Whether this composes 10 layers
deep — ADR → contract notes → tickets → implementations →
reviews → observations → next ADR — is the harder question, and
the showcases (T37, T38) are the right scale to test it.

## Open follow-ups, in priority order

1. **Implement Block 2b (convene with seed_artifacts).** The
   shape is clear; the test validated the value. ~50 lines plus
   tests.

2. **Tweedle response schema: tighten the mark_agreed validator
   error messages.** Both rejected utterances had the LLM omit
   required fields; the validator messages are clear, but the
   LLM didn't recover within the same turn. Worth a primer-level
   note for the Tweedle output protocol: "if you mark_agreed,
   you MUST include resolution and contract_version."

3. **Now seriously consider tool integration.** The Tweedles
   shipped 5 contract specifications; the natural next move is
   actual code. With ADR-001 + 5 contracts, the implementation
   surface is fully defined. This was deferred earlier (analyses
   011, 013) because the upstream agents weren't shipping;
   they're shipping now. Reading the contract notes gives a
   concrete picture of what tools the Tweedles need: file
   write, schema validation against the contract, basic test
   execution.

## Next breath

Cross-meeting composition validated with one substantive cost-
bounded test. The framework now has a clean arc from "vague
directive" to "architectural decision" to "five contract
specifications, all agreed." Block 2b's job is concrete; tool
integration becomes interesting; the showcases (T37 security
recovery, T38 multi-session persistence) are ready to exercise
the pattern at scale.
