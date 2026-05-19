# wonderland-trail/ — the decision provenance behind demo/

> **682 markdown artifacts** documenting *why* every line of code
> in `demo/` exists. Produced by the same Claude Haiku 4.5
> instance that wrote the application code, across 3 milestones
> of the mvp-demo2 autonomous pilot. The trail makes the
> shipped artifact **maintainable**: every function traces back
> to a ticket, which traces back to a feature, which traces back
> to user stories grounded in operator-stated requirements.
>
> This is what a single-shot LLM (with or without filesystem
> tools) **cannot produce** — even if it ships functional code,
> there's no chain of decision-making for someone else to pick
> up the project from.

## What's in here

Curated copy of `projects/mvp-demo2/.wonderland/` (the live pilot
state; gitignored). Runtime noise (per-run telemetry, agent
episodic memory, low-level tool-call logs) excluded; everything
human-readable kept.

| Subdirectory | Count | Produced by | What it is |
|---|---:|---|---|
| `requirements/` | 21 | Alice (I1), Cat (I2), Rabbit (I3) | Discovery output — operator answers structured as `persona`, `situation`, `constraint`, `integration`, `deal_breaker`, `scope`, `success_criterion`, `out_of_scope` requirements with verbatim operator quotes. |
| `milestones/` | 3 | White Rabbit (milestone-plan primary) | The trajectory — M1 (capture notes offline with preview), M2 (search + tags), M3 (persists across restart). Each names `consumes_requirements`. |
| `stories/` | 25 | Alice (M1) + Caterpillar's M1 grounding | User stories with persona + situation + need + acceptance criteria + confusion-flags + `realizes_requirements` linkage. |
| `features/` | 11 | White Rabbit (M2 composition) | User-facing capabilities composed from stories. Each names `Sources:` (story citations), `Personas:`, `Stack span:`, `Tier:`, `Kind:` (capability vs foundation). |
| `tickets/` | 80 | White Rabbit (M3 decomposition) + Caterpillar (M3.5 consolidation) | Implementation atoms. Each has `Sources:`, `Owner:`, `Tier:`, `Stack span:` (frontend/backend/full-stack), explicit `Blocked by:` / `Blocks:` dependency graph, `Description:`, `Acceptance:`. |
| `architecture/` | 7 | Cheshire Cat (M4) | ADRs with `Context`, `Decision`, `Tradeoffs` (named explicitly), `Status`. |
| `rulings/` | 13 | Queen of Hearts (M4) | Security/compliance determinations with `Severity`, `Domain`, `Citation` (specific named threats — OWASP A09, SOC 2 CC7.2, GDPR Art. 32, etc.), `Finding`, `Required Remediation`, `Acceptance Criteria`, `Residual Risk`. |
| `contract-notes/` | 30 | Tweedledee + Tweedledum (M5) | Per-feature contract negotiation — `Current Shape`, `Proposed Change`, `Rationale`. Documents the frontend/backend seam decisions. |
| `test-scenarios/` | 369 | Mad Hatter (M6) + Alice (happy-path) | Per-ticket failing tests in scenario form. Each has `Severity` (breakage / silent-wrongness / degradation / curiosity / delight), `Setup`, `Trigger`, `Expected`, `Concern`. |
| `reviews/` | 52 | Caterpillar (M8) | Code review verdicts. Each has `Verdict` (accept / request-changes / block), per-finding `Location` (file:line), `Quote`, `Read`, `Concern`, `Request`. |
| `implementations/` | 67 | Tweedles (M7) | Implementation provenance — `Ticket` ref, `Contract` ref, `Approach`, `Invariants Enforced`, `Schema Changes`, `Ready for review`. |
| `feature-states.jsonl` | 41 lines | Substrate | Feature lifecycle audit log — every state transition (`proposed → in_design → designed → queued → in_progress → ready_for_review → verified`) with timestamp, actor, reason. |
| `ticket-states.jsonl` | 277 lines | Substrate | Same for tickets (`pending → queued → in_progress → done` / `aborted`). |
| `milestone-unlink.log` | 51 lines | Substrate (T-a1) | Milestone registry audit log for every unlink operation. |
| `project.yaml` | 1 file | Operator + skeleton | Project context (stack, entry point) — read by every meeting for runtime-shape grounding. |

**682 markdown files** + **4 JSONL/log files** = the full trail.

## How to trace a decision

Pick any file in `demo/src/` or `demo/frontend/src/` and trace
back through the chain:

1. **Find the implementation that shipped it.** Search
   `implementations/` for the relevant ticket reference, e.g.:
   ```
   grep -l "wildcard escaping" implementations/
   ```
   → `implementation-01KRXYY9-wildcard-escaping-in-search-queries-tag-name-normalization.md`

2. **Find the ticket the implementation served.** The
   implementation cites a `Ticket:` field. Open
   `tickets/ticket-<slug>.md`.

3. **Find the feature the ticket belongs to.** The ticket's
   `Sources:` field's first entry is the parent feature slug.
   Open `features/feature-<slug>.md`.

4. **Find the stories the feature composed from.** The
   feature's `Sources:` field names story slugs. Open
   `stories/story-<slug>.md` for each.

5. **Find the requirements the stories realize.** Each story's
   `realizes_requirements:` field names requirement slugs. Open
   `requirements/requirement-<slug>.md` for each — and read
   the **operator quote** at the bottom to see the literal
   words the operator said in discovery.

6. **(For architectural questions)** Find the ADRs. Open
   `architecture/adr-<slug>.md` to see the named tradeoffs
   the team committed to.

7. **(For security questions)** Find the relevant rulings.
   Open `rulings/ruling-<slug>.md` to see the cited threat
   model (OWASP / SOC 2 / GDPR) and the required remediation.

8. **(For seam/contract questions)** Find the contract note.
   Open `contract-notes/contract-note-<id>.md` to see what
   shape the frontend and backend agreed to.

9. **(For "was this reviewed?")** Find the relevant Caterpillar
   review. Open `reviews/review-<slug>.md` to see the verdict
   + the per-finding citations.

Every artifact is **plain markdown with frontmatter** — readable
in any text editor, greppable, traceable, git-friendly.

## Lifecycle audit trail

The JSONL logs let you reconstruct *when* + *why* each artifact
transitioned state. Example: trace a feature's path:

```bash
grep "kohl-can-create-and-save" feature-states.jsonl
```

```json
{"feature_slug":"kohl-can-create-and-save...","from_state":null,"to_state":"proposed","by":"system","at":"2026-05-18T14:43:03Z","notes":"Auto-transition from meeting 'composition' on emission"}
{"feature_slug":"kohl-can-create-and-save...","from_state":"proposed","to_state":"in_design","by":"system","at":"2026-05-18T15:12:18Z","notes":"M3 decomposition emitted tickets"}
{"feature_slug":"kohl-can-create-and-save...","from_state":"in_design","to_state":"designed","by":"system","at":"2026-05-18T15:31:42Z","notes":"M5 contract negotiation complete"}
{"feature_slug":"kohl-can-create-and-save...","from_state":"designed","to_state":"queued","by":"operator","at":"2026-05-18T15:34:11Z","notes":"Dashboard queue action"}
{"feature_slug":"kohl-can-create-and-save...","from_state":"queued","to_state":"in_progress","by":"system","at":"2026-05-18T15:38:50Z","notes":"M6/M7 fired on first ticket"}
{"feature_slug":"kohl-can-create-and-save...","from_state":"in_progress","to_state":"ready_for_review","by":"system","at":"2026-05-18T17:22:09Z","notes":"All tickets DONE; rolled up via derived state"}
{"feature_slug":"kohl-can-create-and-save...","from_state":"ready_for_review","to_state":"verified","by":"operator","at":"2026-05-18T17:48:33Z","notes":"Dashboard verify action"}
```

This is the **complete audit trail** of every feature's
lifecycle, including which transitions were operator-driven
vs system-driven. Same shape for tickets in
`ticket-states.jsonl`.

## What's NOT in here (lives in `projects/mvp-demo2/.wonderland/`)

- `runs/` — 90 files of per-run telemetry (cost, agent calls,
  token usage). Useful for cost analysis (see
  `paper/artifacts/cost-breakdown-mvp-demo2.md`); not load-bearing
  for decision-trail reading.
- `memory/` — per-agent episodic memory (T-a2 branching memory
  artifacts). Opaque to outside readers.
- `telemetry/` — aggregate run metrics.
- `tool-calls.jsonl` — 5,750 lines of low-level tool invocations
  (every `read_file`, `write_file`, etc. an agent ran).
- `phase-events.jsonl` — 1,683 lines of meeting phase
  transitions (intra-meeting bookkeeping).

These exist in the live pilot state but aren't useful for the
"trace the decision provenance" use case the trail supports.

## How this connects to the paper

The trail is the load-bearing evidence for two specific paper
claims:

- **Corollary 4 — Production shape as a derived property.**
  *"Vibe-coded MVPs on a sparse directive are throwaway by
  default; Wonderland's output is shaped like what a junior
  team's couple-day TDD push would produce, with the artifact
  trail that lets someone else maintain the result."* The
  trail IS that "artifact trail that lets someone else
  maintain the result." This directory is the receipt.

- **Comparison baseline framing.** Single-shot LLMs (with or
  without tools) can produce functional code; they cannot
  produce the maintainable decision trail. The comparison
  artifact (`paper/artifacts/comparison-baselines/`) frames
  the two axes — **code quality** (where baselines compete
  fairly) and **artifact trail** (where baselines structurally
  cannot compete). This directory populates the second axis
  for Wonderland's column.

## See also

- [`../README.md`](../README.md) — what the demo/ app is + how
  to run it.
- [`../../paper/artifacts/workflow-walkthrough.md`](../../paper/artifacts/workflow-walkthrough.md)
  — per-meeting breakdown of which character produces which
  artifact in which workflow.
- [`../../paper/artifacts/cast-walkthrough.md`](../../paper/artifacts/cast-walkthrough.md)
  — per-character breakdown of artifact shapes (each character's
  §V — Artifacts section).
- [`../../paper/artifacts/code-quality-mvp-demo2.md`](../../paper/artifacts/code-quality-mvp-demo2.md)
  — independent cold review of the shipped code, with
  references back to the inline contract citations the trail
  produced.
- [`../../src/wonderland/closet/analyses/034-mvp-demo2-autonomous-pilot.md`](../../src/wonderland/closet/analyses/034-mvp-demo2-autonomous-pilot.md)
  — the pilot narrative.
