# Analysis 034 — Mvp-demo2: first end-to-end Tier 2 autonomous pilot

> A working full-stack markdown notebook — backend, frontend, tests,
> and all — produced autonomously by ten characters who collaborate
> across the entire software production pipeline. **$83.78** spend.
> **3 milestones** designed, implemented, and verified. **5000 lines
> of code** (~3400 application + ~1600 test), **61 passing tests**,
> SQLi-safe LIKE patterns, timezone-aware datetime handling, custom
> React hooks, modular component design. The operator was a gate-
> approver who skipped a few duplicate features and watched the team
> build.

This is the showcase for what Wonderland looks like running end-to-end
without operator hand-fixing the substrate. It supersedes the earlier
Geocities pilot ([analysis 028](./028-pomodoro-end-to-end.md), referenced
from the project README) as the headline demonstration — that was a
single-directive run; this is multi-milestone autonomous operation.

---

## What got built

A personal markdown notebook web app. The directive came from the
``notebook`` directive ([analysis source](../directives/notebook.yaml)):

> Build a personal markdown notebook web app. Single user, no
> authentication. Capture markdown notes, tag them for organization,
> find them later via search. Notes persist across page reloads and
> server restarts. Stack: Python + FastAPI + SQLite backend, React
> + Vite + TypeScript frontend.

**Final artifact** (`projects/mvp-demo2/`):

```
src/backend/
  models.py              119 lines — Note + Tag SQLAlchemy models
  api/notes.py           496 lines — 7 endpoints (CRUD + tag CRUD + search)
  main.py + db.py         68 lines — FastAPI app + engine
  + health.py             11 lines

frontend/src/
  Editor.tsx             311 lines — main editor pane
  Search.tsx             626 lines — search + tag filter UI
  NoteList.tsx           249 lines
  TagInput.tsx           141 lines
  App.tsx                149 lines
  api.ts                 138 lines — typed API client
  Preview.tsx             58 lines — markdown preview pane
  EditorLayout.tsx        67 lines — split-pane wrapper
  + custom hooks         (useLocalStorageDebounce, useBootNotes)

tests/                  1577 lines across 5 test modules
  - 61 tests, all passing
  - Includes edge cases, search wildcard scenarios, tag scenarios
```

The code is shaped like what an experienced developer would write
on day one: SQL injection prevention with explicit ``_escape_like_pattern``
+ ``_safe_ilike`` helpers (with inline warnings against bypassing the
escape), timezone-aware datetime normalization handling SQLite's
naive datetimes, tag case-sensitivity decision documented inline with
its contract reference, modular React components with custom hooks.
Not toy code; not perfect code either — closer to a *credible v1*
than a *finished v2*.

## How it was built — the pilot's flow

The substrate orchestrated five workflow types in sequence, with
the operator pressing buttons at gate points but never editing
artifacts or killing wedged runs.

### 1. Discovery — $0.11

Alice (the user-voice) and Cheshire Cat (architecture) interview
the operator about the project. Operator answered ~15 questions
about persona, scope, performance targets, non-goals. Output: 23
requirement artifacts.

### 2. Milestone-plan — $0.17

White Rabbit (lead) + Alice + Cheshire Cat group the requirements
into a multi-run trajectory. Output: 3 milestones:

- **M1**: Kohl captures findings offline with markdown preview
- **M2**: Kohl finds past findings via search and tags
- **M3**: Kohl's notebook persists across restart

Notable: this pilot's milestone-plan produced 3 milestones with
larger per-milestone scope than the previous pilot's 4-5 milestone
output. Same project, different decomposition. Worth noting that
**milestone count varies across runs** — the trajectory shape is
a substrate-influenced choice, not a deterministic property of
the directive.

### 3. M1 design + implementation — ~$26

`tdd-design` ran scoped to M1. The flow:
- M1 phase: Alice + Caterpillar ship stories (persona-anchored)
- M2 phase: White Rabbit composes features from stories
- M3 phase: White Rabbit decomposes features into tickets
- M3.5 phase: Caterpillar consolidates per-feature duplicates
- M4 phase: Cheshire Cat ships an ADR
- M5 phase: Tweedles + Caterpillar negotiate contracts

Then `tdd-implement` ran per feature:
- M6 phase: Mad Hatter (tea-party) designs adversarial test scenarios
- M7 phase: Tweedledee (frontend) + Tweedledum (backend) implement
- M8 phase: Caterpillar reviews the deliverable
- M9 phase: Substrate runs pytest_collects + pytest_passes + npm_build

Each implementation pass that drew a `request-changes` verdict from
Caterpillar generated follow-up tickets. The team iterated until
M8 returned `accept`, at which point M1's features transitioned
to `ready_for_review` for operator gate.

**Operator gate-approver action at M1 close**: review the features,
mark them `verified` from the dashboard. M1 complete.

### 4. M2 design + implementation — ~$30

Same flow as M1 but scoped to M2 (search + tags + recall surface).
This is where the **substrate's iterative improvement during the
pilot** showed up:

- First M2 design attempt: Alice drifted into M1-flavored stories
  (capture flow, multi-tab edit). Recovered on rerun via existing-
  stories context carryover.
- **Mid-pilot substrate fix** shipped: auto-synthesize the workflow
  directive from milestone scope when operator leaves it blank.
  Tested on M3 design.
- M2 design produced 5 features, 3 of which were M1-overlap
  duplicates. Operator gate-approver action: skip the duplicates,
  queue only the 2 legitimate M2 features (search + tags).
- M2 implementation ran with parallel intra-feature pipelining
  (multiple tickets per feature running concurrently).

### 5. M3 design + implementation — ~$22

Final milestone — persistence + integration validation. The
substrate fix from mid-M2 worked: M3 design got the auto-synthesized
directive ("Design milestone M3: persistence-across-restart. M1
already shipped capture; M2 shipped search+tags; leave their
territory alone").

Rabbit composed a single "megalith" feature for M3 covering the
save+persist work but also picking up some off-scope additions.
Operator gate-approver action: queue only the on-scope tickets
within the megalith (10 of them), leave the off-scope ones unqueued.
That's ticket-level scope filtering — within the gate-approver
discipline because queue decisions ARE gate-approver work.

**M3 close**: features verified. Working app shipped.

## What was different from the first pilot

The previous pilot ([mvp-demo](./)), also targeting the notebook
directive, was the substrate's first encounter with this project
shape. It surfaced multiple wedge classes:

- **Memory bleed**: M2 design wedged for 22+ rotations on a stale
  requirement that Alice had argued about in M1's design — her
  episodic memory carried the deliberation forward
- **Coverage check false positives**: requirements of kind ``scope``
  and ``constraint`` flagged as "unrealized" indefinitely because
  they don't decompose into features
- **Snapshot wipes**: an empty milestone_plan emission deleted
  M1's file
- **Ghost completions**: build_check's review-routing marked
  freshly-synthesized tickets as DONE within seconds of creation

Each surfaced an operator intervention requirement: SQL DELETE on
memory, file edits to milestone consumes_requirements, killing
processes mid-stream. The pilot eventually shipped a partial
artifact for ~$40 with significant fixer-level operator participation.

**Between mvp-demo and mvp-demo2**, six substrate improvements
landed:

- **T-a1**: MilestoneRegistry audit log on every unlink
- **T-a2**: branching episodic memory at the design/impl level
  with Mock Turtle consolidation on milestone-close
- **T-a3**: convergence-failure detection that flags spec ambiguity
  when reviews oscillate
- **T-a4**: env-class verify routing that surfaces operator-
  attention items for missing deps instead of synthesizing
  Tweedle implementation tickets
- **T-a5**: cross-feature ticket consolidation that deduplicates
  near-identical tickets across features
- Coverage check exemptions for non-realizable requirement kinds
  (scope, constraint, success_criterion)

All shipped as part of release **0.8.0**.

The result: mvp-demo2 completed end-to-end with operator
participating primarily as gate-approver. Zero killed runs. Zero
memory surgery. Zero hand-edited tickets. **One** mid-pilot
substrate fix (auto-directive synthesis), which counts as a Tier
2 violation worth documenting honestly.

## What this demonstrates

### 1. Autonomous Tier 2 operation is reachable on Haiku-class models

Identity engineering + constraint substrate works on a small model.
The operator's role was largely watching, approving, and skipping
duplicates — not building. The team produced a working artifact.

### 2. Substrate evolves through pilot-driven discovery

Each pilot surfaces the next layer of failure modes. Mvp-demo
showed wedge-and-data-loss; the fixes from T-a1–T-a5 closed those
classes. Mvp-demo2 showed bounded-visibility issues (Caterpillar
can't see sibling features; Rabbit composes M1-overlap features
during M2 design). Those gaps are characterized + filed for the
next iteration ([roadmap items b3f440c8, 4a2597a4, 81af78f8,
e7d226b8](./)). The substrate doesn't reach perfection; it reaches
the next pilot's failure mode.

### 3. Quality and cost move together

Substrate fixes that improved output also reduced wedge waste.
Mvp-demo had ~$5+ of dead-end run cost; mvp-demo2 had ~$1. Code
quality observed by operator was better (sql escape discipline,
edge case handling), and the per-effective-milestone cost ($28)
was a real number — not an abstraction.

### 4. Multi-lens review produces quality the operator didn't have to ask for

Operator noticed unsolicited during the pilot: *"we're not just
shipping code, it's quality code. They're accounting for all
types of shit I never would have thought to through the review
passes."* The architecture's failure-modes-as-identity choice
produces N distinct epistemic frames reviewing each deliverable
— Hatter's edge-case enumeration, Queen of Hearts' security
discipline, Caterpillar's coherence reading, Cat's architectural
smell. Each over-applies their lens; that over-application is
the *feature*.

## What the artifact actually does

Verifying the working app (post-pilot):

```bash
cd projects/mvp-demo2

# Backend
uv sync
uv run uvicorn src.backend.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Create a note (title + markdown body).
Add tags. Save. Refresh — the note persists. Search by substring
in title or body. Filter by tag. Edit. Delete. Restart the server
— everything's still there.

Run the tests:

```bash
cd projects/mvp-demo2
uv run pytest tests/    # 61 tests, all passing
```

## See also

- [Cost breakdown analysis](./033-mvp-demo2-cost-breakdown.md) —
  per-workflow + per-agent spend, efficiency hotspots, optimization
  levers
- [Release notes 0.8.0](../../../../release-notes/0.8.0.md) — the
  substrate improvements that enabled this pilot's completion
- [Branching memory design](../../../../.daedalus/design-memory-branching.md)
  — T-a2 architecture proposal (the load-bearing fix)
- [Paper notes](../../../../paper/) — source material for the
  Wonderland paper draws on this analysis + the cost breakdown
  + multiple memory observations
