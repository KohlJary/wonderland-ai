# Analysis 022 — Consolidation alone (and the self-healing M4)

**Date:** 2026-05-06
**Run:** T38 Session 1, fresh project_root, post-consolidation scripts
**Snapshot:** [analyses/data/022-consolidation-alone/](data/022-consolidation-alone/)
**Result:** $1.12, 641s wall-clock, 1 of 7 tickets shipped, 2 late-publish suppressions

## Why this matters

Analysis 021 diagnosed the recurring "Tweedles ship backend, then nothing"
pattern as a broken M3/M4 boundary — Tweedles overshoot M3 with tool calls,
M3 closes during the slow tool loop, implementations get suppressed as
late-publish, M4 opens with no fresh signal. The fix proposed two changes:
M3+M4 consolidation (a script-level change to the canonical workflow) AND
turn-based quiescence detection (a substrate change to the Runner /
ThreadMonitor).

This run isolates **consolidation alone**, against the still-wall-clock
quiescence model, to attribute the fix accurately. If consolidation alone
solves the problem, the substrate change becomes optional. If not, we know
where the load-bearing fix actually lives.

The result is informative in both expected and surprising ways.

## Setup

- **Script:** `/tmp/test_t38_session1.py`, post-consolidation. M3 (contract
  negotiation) and M4 (implementation) merged into one design-and-ship
  meeting (tools-on, two-part directive, combined budget 1.80). Old M5
  (review) renumbered to M4. Snapshot:
  [test_t38_session1.py](data/022-consolidation-alone/test_t38_session1.py).
- **Substrate:** unchanged. Wall-clock quiescence still 60s.
- **Project root:** fresh (`/tmp/t38-consolidation-validation/`) — no
  inherited memory from prior analyses. Isolates this run cleanly.
- **Session 1 only:** Session 2 deferred. Goal is variable isolation, not
  multi-session validation.

## What shipped

| Layer | Files | Bytes |
|---|---|---|
| `src/backend/api/auth.py` | new | 2408 |
| `src/backend/auth.py` | new | 3895 |
| `src/backend/models.py` | modified | +34 lines |
| `src/backend/api/__init__.py` | modified | +2 lines |
| Frontend | **untouched** | — |

Artifacts persisted: 5 stories, 1 ADR, 7 tickets, 7 contract notes, **1
implementation, 1 review.** The implementation is HTTP Basic Auth
([implementation-001](data/022-consolidation-alone/wonderland-snapshot/implementations/implementation-001-http-basic-auth-signup-and-login-endpoints.md));
the review accepts it
([review-001](data/022-consolidation-alone/wonderland-snapshot/reviews/review-001-http-basic-auth-signup-and-login-endpoints.md)).

Compared to the seven decomposed tickets (auth, messages schema,
conversation init, message fetch, conversation list, two-user exchange
test, user search), the team shipped exactly one — ticket-001, the auth
ticket. Six tickets and the entire frontend went unimplemented.

## Headline finding 1: consolidation alone is insufficient

In M3 (the merged design-and-ship meeting), the Tweedles reached
`state=counterpart_assessed` on three contract notes but never reached
`state=agreed`, and never started Part 2 of the directive (implementation).
M3 wall-clock-quiesced at t=453s while Tweedledee was mid-deliberation on
the contract responses. The two suppression events:

```
[late-publish] tweedledee → thread 'design-and-ship' (already COMPLETE)
  — suppressing implementation: "I see you've proposed three contract
  notes (004, 005, 006)..."
[late-publish] tweedledee → thread 'design-and-ship' (already COMPLETE)
  — suppressing contract_note: "Reading your three responses..."
```

This is the same failure mode as analyses 020 and 021. The boundary moved
from M3-to-M4 to mid-M3, but the underlying mechanism — wall-clock timer
closing an actively-deliberating meeting — is unchanged.

**The M3/M4 boundary was a symptom, not the cause.** Removing the boundary
just relocated the failure point.

That said, consolidation is not zero-value:
- 2 suppressions in this run vs ~6 in 020/021 — fewer boundaries, fewer
  opportunities for the bug to fire.
- Cost down to $1.12 from prior ~$3 per session, but that's because the
  team shipped less, not because they got more efficient. **Cheaper in the
  way that crashing your car is cheaper than driving it: less fuel
  consumed.**
- Single-meeting design+ship matches what the system "wants to do" —
  Tweedles overshooting M3 with tool calls in 020/021 was an early
  indicator the boundary felt artificial to the agents themselves.

## Headline finding 2: M4 self-healed (the surprise)

The unexpected part: **M4 (review) recovered from M3's failure by pivoting
into a recovery-implementation meeting.** I did not predict this.

Sequence:
- M4 opens at t=453s. Caterpillar reads the working tree via tools, finds
  it clean — no diff to review.
- Tweedledum (t=458s): "The working tree is clean and matches HEAD. The
  directive mentions code shipped in a prior thread, but..."
- Tweedledee (t=485s): "I see the baseline codebase but the working tree
  is clean."
- Caterpillar (t=512s): "The Tweedles have raised a legitimate point.
  The working tree is clean — there is no diff to review."
- The team collectively reasons through the situation, notices the
  contracts were locked but never implemented, confirms the auth
  contract specs (Tweedledee t=549s, Tweedledum t=550s), then:
- **Tweedledum (t=560s):** `implementation` utterance — "Shipping
  ticket-001 backend: HTTP Basic auth endpoints (signup, login) + users
  table with email_hash..."
- Caterpillar reviews the shipped code; produces review-001 (verdict:
  accept) with cross-domain references back to Tweedledee for the
  frontend.

This is not a feature of the orchestration model. It's emergent behavior
from the agents reading the situation in natural language and doing the
reasonable thing. The directive said "review the code that shipped"; they
noticed nothing shipped; they shipped some.

Why this matters:
- **Wonderland has more orchestration-failure resilience than the model
  assumes.** When the wall-clock kills a meeting mid-process, downstream
  meetings can sometimes recover the lost work through agent reasoning.
- **It's a partial recovery, not a full one.** M4 hit the per-meeting
  budget cap (`MEETING_BUDGET`) before the team could ship the other six
  tickets or the frontend. Self-healing scales as O(1 ticket per recovery
  meeting), not O(N).
- **It's not a feature to rely on.** A proper fix (turn-based quiescence)
  prevents the failure from happening in the first place. Self-healing is
  the ER, not the doctor's office.

## Quantitative comparison

| Metric | 020 (S1) | 021 (S1) | 022 (this run) |
|---|---|---|---|
| Wall clock | ~12 min | ~12 min | 10.7 min |
| Cost | ~$3 | ~$3 | $1.12 |
| Late-publish events | ~6 | ~5 | 2 |
| Implementations persisted | 0 | 0 | 1 |
| Tickets shipped | 0 (backend only via direct write) | 0 (same) | 1 |
| M5/M4 outcome | unclear | unclear | recovery shipped 1 ticket |

The pattern: consolidation reduces the number of failure points (boundaries
between meetings) which reduces the number of late-publish events. It does
not eliminate them. The remaining failures still lose substantial work —
in this run, contract notes 001-003 *agreed-state* responses and the
attempted implementation utterance both got suppressed.

## Diagnosis (sharpened from 021)

The M3/M4 consolidation work was correct in spirit but addressed the wrong
layer. The actual binding constraint is:

> The wall-clock quiescence model closes meetings based on bus-event
> silence, but bus silence does not imply agent inactivity. An agent can
> be deep in a tool loop or mid-LLM-call for 30+ seconds while emitting
> nothing to the bus. The wall-clock model interprets this as quiescence
> and closes the meeting. When the agent finally emits, it lands in a
> COMPLETE thread and gets suppressed.

Consolidation reduced the surface area where this failure can fire (one
fewer boundary), but the underlying termination mechanism is unchanged.

The fix is **turn-based quiescence**: per-agent state tracking on the
Runner (IDLE / ENGAGED_PENDING / AWAITING_RESPONSE / IN_TOOL_LOOP /
COMPLETING). The ThreadMonitor reads agent-state events instead of (or
alongside) bus-event timestamps. A meeting is quiescent iff all members
are IDLE — by construction can't happen mid-deliberation.

This is roadmap item [22eef6fd](.daedalus/roadmap/) and the next P1.

## What we filed

No new roadmap items from this run. Existing items remain accurate:

- `22eef6fd` (P1) — turn-based quiescence detection. **Confirmed as the
  load-bearing fix.**
- `903e6137` (P1) — M3+M4 consolidation. **Demoted in priority** — net
  positive but not the primary win. Will be subsumed into the workflow-
  as-data extraction once turn-based quiescence is in.

New observation worth saving (informally for now): **Agents recover from
orchestration failures by re-reading the directive in the next meeting
and doing the reasonable thing.** This is a property of the natural-
language substrate, not the orchestration model. Worth understanding when
designing future workflows — it suggests we can be slightly less paranoid
about clean meeting termination as long as the next meeting's directive
gives them context to recover.

## What's next

1. **Turn-based quiescence** (task #81 in this session, roadmap
   `22eef6fd`). Substrate change to `runner.py` + `agent.py`. The
   load-bearing fix.
2. **Re-run T38 Session 1 with both consolidation + quiescence.** Look
   for: zero late-publish suppressions, all 7 tickets shipped, frontend
   code present, M4 functions as actual review meeting.
3. **Then Session 2** to validate multi-session compounding under the
   fixed substrate.
4. **Then workflow-as-data extraction** — once the substrate is right,
   extract the validated 4-meeting shape into a canonical workflow
   template (`workflows/canonical.yaml` or similar). This sets up the
   eventual TDD-variant workflow and the Dodo dynamic-workflow-generation
   work.

The breath on this work block is probably: implement quiescence (this
session or next) → rerun T38 (next session) → workflow extraction (later
session).
