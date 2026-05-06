# Analysis 017 — The First End-to-End Arc Completion

**Date:** 2026-05-06
**Phase milestone:** P6.T36 — translation chat MVP enchilada,
v14 closes the loop from vague directive to source-on-disk
**Components touched:**
- `src/wonderland/agent.py` (listen() now records seeds for context)
- `/tmp/test_t36_enchilada.py` (per-meeting convenor directives,
  pure-pair M3 roster) — snapshot at
  [`data/017-first-arc-completion/test_t36_enchilada.py`](./data/017-first-arc-completion/test_t36_enchilada.py)
**Run transcripts + artifacts:**
- [v14 run.log](./data/017-first-arc-completion/v14/run.log)
- [v14 wonderland artifacts](./data/017-first-arc-completion/v14/wonderland-artifacts/)
- [v14 shipped source: src/types/contract.ts](./data/017-first-arc-completion/v14/contract.ts)
**Comparison baseline:**
[analysis 016](./016-cat-story-deafness.md) — v10 produced every
artifact type *except* code on disk; this is the first run where
something hits the working tree end-to-end.

> v14 ran the full 5-meeting enchilada from the directive
> "translation chat MVP" through to a real frontend type-definitions
> file on disk that cites two of the four agreed contract notes by
> name. ~$0.49, 5 meetings, 6 stories → 1 ADR → 6 tickets → 4
> `state=agreed` contract notes → 1 source file. The arc closes,
> just barely. M4 robustness is now the next bottleneck — only
> Tweedledee shipped a file before parse-errors and schema-mismatch
> ended both Tweedles' turns.

---

## What changed since v10

Three substrate fixes, each surfaced by a focused diagnostic in
the analysis 016 followup:

1. **`Utterance.is_seed`** — convene-re-stamped seeds short-circuit
   to `Engagement.ALMOST_NEVER` so prior-thread artifacts don't
   pull agents into respond-mode against historical work.
2. **`listen()` records seeds for context** (the missing half of
   the seed semantics): seeds are recorded in episodic memory but
   not queued for engagement. v13 surfaced the bug — without this,
   `compose_context` queries memory and finds zero seeded artifacts;
   the LLM literally can't see the "locked context" the directive
   references.
3. **Tweedle DIRECTIVE engagement** — `always(SpeechAct.DIRECTIVE)`
   added to Tweedle engagement rules so meetings without Cat or
   Alice on roster still have a meeting-frame signal.

Plus four script-level changes coupled to the substrate:

4. **Per-meeting `convenor_directive`** for M2/M3/M5 (M1/M4 already
   had one). Each meeting now gets an explicit Dodo turn telling
   participants what *this* thread is for. Without this, downstream
   meetings had no fresh-engagement signal — every seed was a
   seed, every story was prior-thread.
5. **Pure Tweedle pair in M3** (Cat removed from contract-negotiation
   roster). v13 surfaced that with Cat in the room and ADRs in
   context, the Tweedles deferred — "Cat will lead, we'll wait" —
   even when the directive said "this is the pair's work." Pair
   Protocol is between Tweedledum and Tweedledee; an architect
   in the room invites architectural deference, not contract
   drafting.
6. **Working-tree-as-implementation-artifact** — `git_status` /
   `git_diff` tools added; Caterpillar protocol updated to read
   the diff for review; Tweedle protocol nudged to ship code via
   `write_file` as the deliverable, with the bus utterance as
   a brief record (not a metadata dump).
7. **`_ensure_git_repo()`** in `Runner.make_full_cast` — initializes
   project_root with empty initial commit + `.wonderland/` gitignore
   so reviewers' diffs aren't drowned in framework state writes.

## v14 outcome by meeting

Single run, 5 meetings, ~$0.49 / $3.00 budget cap:

| # | Meeting | Outcome | New artifacts | This-meeting cost |
|---|---|---|---|---|
| M1 | scoping | MEETING_BUDGET | 6 stories, 6 rulings, 1 ADR | $0.13 |
| M2 | decomposition | COMPLETE | 6 tickets | $0.04 |
| M3 | contract-negotiation | COMPLETE | **16 contract_note ops, 4 reached `state=agreed`** | $0.25 |
| M4 | implementation | COMPLETE | **1 file on disk**: `src/types/contract.ts` | $0.07 |
| M5 | review | MEETING_BUDGET | (Tweedles continued contract refinement; Caterpillar silent) | minimal |

**On disk after the run:**

```
.wonderland/
  stories/         6 files
  architecture/    1 ADR
  tickets/         6 files
  rulings/         6 files
  contract-notes/  4 (3 mark_agreed)
src/types/
  contract.ts      1640 bytes (cites CN-005 + CN-006)
```

This is the first run in the project's history where the directive
"translation chat MVP" produced a working-tree file — the deliverable
the showcase was always supposed to test.

## What the shipped file says

The file Tweedledee wrote, lightly trimmed:

```typescript
/**
 * Frontend type definitions aligned to locked contracts.
 * Contract versions referenced:
 * - CN-005: translation gateway (message envelope with translation_status)
 * - CN-006: consent audit trail (per-session consent state)
 *
 * These types are the frontend's reading of the backend contract.
 * Changes here require Contract Note negotiation with Tweedledum.
 */

export type TranslationStatus = 'completed' | 'failed' | 'pending' | 'not_requested';

export interface MessageEnvelope {
  id: string;
  sender_id: string;
  recipient_id: string;
  conversation_id: string;
  source_language: string;
  original_text: string;
  translated_text: string | null;
  ...
}
```

Two things stand out:

1. **The contract is cited by name** in the docstring. CN-005 and CN-006
   exist in `.wonderland/contract-notes/` from the same run. The file
   isn't generic; it's specifically the frontend's reading of the
   contracts the pair agreed to that day.
2. **The "changes here require Contract Note negotiation" comment**
   is character-true Tweedledee: the Pair Protocol §V (the contract
   note artifact) lives at the seam between his side and his
   sibling's. He's not just shipping types; he's documenting the
   ongoing-coordination obligation the framework set up.

## What's still broken

**M4 is the new bottleneck.** Only Tweedledee shipped a file before
parse-errors and schema-mismatch ended both Tweedles' turns:

- **`tweedledee` parse error**: "no JSON block found in Tweedle
  response — treating as silence" — same pattern that's been
  recurring across runs. The LLM narrates before the JSON, the
  parser doesn't find a fenced block, the turn is lost.
- **`tweedledum` produced no file**: backend got the directive
  but emitted nothing actionable. M4 had 11 LLM calls total
  (~5 per Tweedle); only one survived.
- **M5 Tweedles tried `decision="review"`**: pydantic rejected with
  "Input should be 'implementation', 'contract_note', 'concern',
  'question', 'deference', 'invite' or 'silence'" — a Tweedle
  reached for the Caterpillar's speech act because the meeting
  framing said "review thread." Wrong agent's schema. Treated
  as silence.
- **Caterpillar emitted nothing actionable in M5**. He had the
  directive (engaged), `git_status` and `git_diff` available,
  one file on disk to review. Either he hit silence, picked
  `concern` without `findings`, or his protocol still
  expects an `implementation` artifact rather than reading the
  working tree directly.

## Why this is still a milestone

For the analysis-thesis ledger: **the framework has now produced a
working artifact end-to-end from a vague directive, under bounded
cost, with no human in the loop**. The artifact cites the
contracts that produced it. The contracts cite the ADR that
produced them. The ADR synthesizes the stories that produced it.
The stories follow from the directive. The lineage is
end-to-end traceable through the on-disk artifacts.

That doesn't mean the framework is *good* yet — only one file
shipped, M5 misfired, parse errors continue. But the loop closes
once. Every prior run had a different bottleneck (M3 silence, M4
silence, ADR-less M1, etc.); v14 completes the chain even if
imperfectly.

The next analysis pushes on M4 robustness: making both Tweedles
ship reliably, fixing the parse-errors-on-narrative-prefix
pattern, and hooking up Caterpillar's git_diff review path so M5
produces actual findings.

## Files touched in this analysis

```
src/wonderland/agent.py                         # listen() records seeds
                                                  for context (the
                                                  missing half of is_seed
                                                  semantics)
analyses/data/017-first-arc-completion/
  test_t36_enchilada.py                         # script snapshot
  v14/run.log                                   # full transcript
  v14/wonderland-artifacts/                     # registries + memory
  v14/contract.ts                               # the shipped source
```

The script changes (per-meeting directives, pure-pair M3) live
only in /tmp; the snapshot is committed for reproducibility.
