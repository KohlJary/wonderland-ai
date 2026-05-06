# Analysis 023 — Quiescence rework + split phases (closing the loop)

**Date:** 2026-05-06
**Runs:** Two T38 Session 1 runs back-to-back
**Snapshots:**
[023-quiescence-validation/](data/023-quiescence-validation/) (Run A) ·
[023-split-validation/](data/023-split-validation/) (Run B)
**Result:** The "Tweedles don't ship" bug class is closed.

## Why this matters

Analysis 022 sharpened the diagnosis from 021: the wall-clock quiescence
model was the root cause of meetings closing mid-deliberation, not the
M3/M4 boundary. This analysis lands two changes — turn-based quiescence
(commit `305d3b2`) and re-splitting M3+M4 — and validates them in two
runs that together close the loop.

Run A: consolidation + turn-based quiescence. Tests the substrate fix
in isolation against the previous (consolidated) workflow shape.

Run B: split phases + turn-based quiescence. Restores the 5-meeting
shape now that the substrate can hold meetings open through tool loops.

## Run A — Quiescence rework, consolidated workflow

| Metric | 022 | 023-A | Δ |
|---|---|---|---|
| Wall clock | 641s | 359s | **−44%** |
| Cost | $1.12 | $0.83 | −26% |
| LLM calls | n/a | 102 | — |
| Late-publish | 2 | 3 | +1 |
| Source code shipped | 1 ticket | **0 tickets** | regression |

The substrate fix worked exactly as designed — meetings no longer close
mid-tool-loop. M1 went from 239s in 022 (with 120s of dead wall-clock
wait after a Queen parse error) to 80s in 023-A, an immediate 3× speedup
just from removing the timer tax.

But the merged design-and-ship workflow regressed in a new way:
**Tweedles emitted single `implementation` decisions whose bodies were
contract proposals, then went IDLE.** Turn-based quiescence correctly
detected they were done (per the agent's own state) and closed M3 in
81s — but the team never progressed to actual source-code work.

Working tree was byte-identical to the seed template. Zero source code
shipped. The two `implementation` artifacts on the bus were the
synthesized "Files written in tweedledee's frontend turn" coercion
format — which puzzled me, because that artifact only fires when
`_last_write_file_paths` is non-empty (i.e., write_file actually
succeeded), and yet no source file showed any modification.

## The mystery (and what it actually was)

The `write_file` mystery was load-bearing for understanding what
happened. Resolution: I added a stderr breadcrumb to
`Tools.write_file` logging path + size + resolved location for every
call, then ran Run B.

Result: Tweedles use `write_file` for contract notes too, writing them
into `.wonderland/contract-notes/*.md` paths via the tool — redundantly
with the framework's own contract_note artifact persistence. In Run A,
the `write_file` calls all landed in `.wonderland/contracts/*.md`
(Tweedles writing their proposed contracts as files). I had excluded
`.wonderland/` from my "working tree clean" diff and missed it.

The synthesized artifact was reporting truthfully — files WERE written.
Just not source code. Mystery: solved without a code bug.

The diagnostic log line was removed before merging. Worth remembering
the pattern: when an artifact disagrees with disk, suspect the diff
filter before assuming a bug in the artifact pipeline.

## Run B — Split phases + quiescence

Re-split M3 (contract negotiation, no tools used) and M4 (implementation,
tools-on) into separate meetings with focused single-purpose directives.
M3's directive explicitly forbids `write_file`. M4's directive mandates
shipping code through `write_file`. Now safe under turn-based quiescence
because the substrate holds meetings open until everyone goes IDLE — no
risk of premature closure.

| Metric | Value |
|---|---|
| Wall clock | 469.6s (~7.8 min) |
| Cost | $1.33 / $3.00 cap |
| LLM calls | 123 |
| `write_file` calls | 14 |
| Late-publish events | 2 (M3 race, see below) |
| Parse errors | 2 (recoverable per `611378d9`) |
| Outcomes | M1-M4 COMPLETE, M5 MEETING_BUDGET |
| Reviews persisted | 1 |
| **Source diff vs seed** | **+1539 / −99 across 8 files** |

Code that shipped:

| File | Δ | Type |
|---|---|---|
| `src/backend/models.py` | +237 | translation chat models |
| `src/backend/api/messages.py` | +407 | message endpoints w/ translation |
| `src/backend/translation_service.py` | NEW (153) | translation service layer |
| `src/backend/auth.py` | NEW (38) | auth helper |
| `src/backend/main.py` | +9 | wire new routes |
| `frontend/src/App.tsx` | +304 | conversation UI |
| `frontend/src/api.ts` | +89 | API client extensions |
| `tests/test_messages.py` | +401 | translation flow tests |

This is a real translation chat MVP. Both frontend AND backend shipped.
Caterpillar reviewed `src/backend/api/messages.py` with translation
integration findings ([review-001](data/023-split-validation/wonderland-snapshot/reviews/)).

## Three findings worth pulling out

### Finding 1: turn-based quiescence is the load-bearing fix

Run A shows the substrate change works in isolation: 44% wall-clock
speedup, no false-positive closures during slow tool loops, all meetings
COMPLETE. The wall-clock tax (60s + 60s for STUCK→QUIESCENT cycle on
parse errors) is gone.

### Finding 2: split phases now work because the substrate can support them

Pre-021, splitting M3+M4 was the wrong call because wall-clock quiescence
killed M3 mid-tool-loop. Post-022, consolidation hid the symptom but
broke shipping. Post-023, split phases work BECAUSE turn-based quiescence
holds the meeting open until Tweedles actually finish. The two changes
compose: substrate fix enables the workflow shape that was previously
unsafe.

### Finding 3: code-shipping is the artifact, the utterance is ancillary

Run B had two parse errors — Tweedledee returned an empty string,
Tweedledum returned a 16782-char response without a JSON wrapper. Under
the old framing this would be a major loss. But the working tree
captures the actual work: write_file calls fired regardless of whether
the LLM produced a parseable wrapping utterance. The bus utterance is
the team's own communication record; the deliverable is the diff.

This framing is consistent with the longstanding "working-tree-as-
implementation-artifact" comment in the code. Worth naming explicitly.

## Residual issues filed

- **`c664d71b`** (P2 bug) — Race between agent IDLE and pending trigger.
  When an agent has multiple triggers queued, the race window between
  finishing turn N and picking up trigger N+1 can result in the meeting
  closing before the next utterance lands. 2 events per Run B, both
  Tweedles responding to each other's contract proposals after M3
  closed. Polish item, not load-bearing — lost utterances are
  ancillary commentary.
- **`611378d9`** (P1 feature) — Parse-error retry. Already filed.
  Run B's two parse errors would benefit; the lost work was bus-
  observability, not source code.

## What's next

The bug class is closed. Remaining P6 work:

1. **T39: Transcript annotation tooling.** The last task in the P6
   gameplan — publishing the analyses with annotated transcripts as
   the public-facing surface for what Wonderland actually does. Then
   P6 can close and we move to P7 (Evals: generic-baseline vs
   Wonderland comparison).

2. **Workflow extraction (deferred).** Still on deck (`903e6137`,
   `f0e4afea` family). Now we have a validated 5-meeting shape worth
   canonicalizing as data on disk. Punted from this work block; pick up
   when the substrate has had time to settle.

3. **The two race/parse fixes** above can be picked up in P7-era polish.

The shape of the framework right now: turn-based quiescence + split
design/implementation phases + working-tree-as-artifact = reliable
code shipping under bounded cost.
