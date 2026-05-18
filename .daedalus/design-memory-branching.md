# T-a2 — Branching episodic memory at the design level

Design proposal for p20's load-bearing substrate change. Read this end-to-end before any implementation lands; the substrate change is small but load-bearing and the operator should agree on shape first.

## Problem (one-line)

Flat per-agent episodic memory carries wedge churn across milestone boundaries, so substrate fixes don't propagate retroactively and the only operator remediation is surgical keyword wipe — which loses useful history alongside the churn.

## Insight (operator, this session)

> "Episodic memory might need to like, branch at the design level."

Memory branches scoped to milestones (and per-feature inside implementation) align with the existing **milestones-as-trajectory** ontology. Branches scope churn structurally; no need for keyword surgery, no need for "memory invalidation" primitive, no need for agents to second-guess their own recall.

## Architecture

### Storage model

Single per-agent SQLite store at the existing path (`<project_root>/.wonderland/memory/<agent_name>/episodic.sqlite`). Schema v2 adds a `branch_id` column to the existing `utterances` table:

```sql
ALTER TABLE utterances ADD COLUMN branch_id TEXT NOT NULL DEFAULT 'project';
CREATE INDEX idx_branch ON utterances (branch_id, timestamp);
```

`project` is the special root branch — receives consolidated summaries on milestone close. Other branch_ids are structured strings:

- `design:m1-data-layer-schema-and-api-contract` — M1's design pass (M1-M5 phases of tdd-design)
- `impl:m1-data-layer:feat:note-data-layer-with-indexed-search-and-filtering` — implementation pass for one feature, scoped to its milestone
- `archived:design:m1-data-layer-schema-and-api-contract` — superseded by consolidation, still on disk for forensics but not in default reads

### Branch as contextvar

`get_active_branch_id() -> str | None`, mirroring `get_active_milestone_scope()`. Set by the workflow runner at the start of each design/impl pass, cleared at the end. Pass start derives branch_id from the active milestone + (for impl) the active feature.

### Write path

`EpisodicStore.record(utterance)` reads `get_active_branch_id()` and tags the utterance. Default to `"project"` when no branch active (operator-driven utterances, system events, legacy data).

### Read path

`EpisodicStore.query_by_thread(thread_id, *, branches=None)`:
- `branches=None` (default): read all branches — operator/dashboard view
- `branches=["project", "design:m2-...]`: agent-time scoped read — current branch + project root

Helper `inheritance_chain(active_branch) -> list[str]`:
- For `design:m2-...` → returns `["project", "design:m2-..."]`
- For `impl:m2-...:feat:foo` → returns `["project", "impl:m2-...:feat:foo"]` (note: does NOT include `design:m2-...` — implementation works from spec artifacts on disk, not design-time argument churn. Discussion-worthy: should implementation see its milestone's design memory? Arguments both ways below.)

### Consolidation (Mock Turtle's new role)

On milestone close (operator gate, or auto-trigger on M9 verify COMPLETE), fire a `consolidate_branch(branch_id)` workflow:

1. Read all utterances on the branch
2. Mock Turtle generates a **milestone summary utterance**: "M_n closed. Shipped features: F_x, F_y. Key contracts: ... Key decisions: ..."
3. Summary utterance gets written to the `project` branch
4. Original branch's utterances get `branch_id` rewritten to `archived:<original>` — still on disk for paper-trail / forensics, but not returned by default reads

Mock Turtle's persona is the memory keeper; this promotion from passive observer to active consolidator extends his existing role rather than introducing a new agent.

### Migration

Schema v1 → v2 fills the new column with `"project"` for all existing rows. The mvp-demo agent memories become project-level legacy data — visible to all future branches as background context. Not ideal (carries the wedge churn) but acceptable for the existing pilot; future projects start clean.

## Open questions worth resolving before implementation

### Q1: Does impl branch inherit design branch?

**Arguments for inheritance (impl sees design memory):**
- Tweedles benefit from seeing the design-time deliberation about contracts, edge cases, architectural decisions
- Continuity: the team has already had these conversations

**Arguments against inheritance:**
- Design churn (Caterpillar's review concerns, Rabbit's composition concerns) wasn't meant for Tweedles' eyes
- Memory bleed risk: a wedged design pass would bleed its argument churn into implementation
- The spec artifacts on disk (features, tickets, contract notes, ADRs) ARE the contract. If something needed to survive design → impl, it was supposed to be written to one of those artifacts. If it only exists in design memory, it was meta-discussion, not load-bearing context.

**Provisional answer**: NO inheritance. Impl works from project-level + own-branch only. This is the cleaner semantic — and surfaces design-impl gaps as substrate-level bugs ("the decision was discussed but never written to a contract note") rather than masking them via memory.

### Q2: When does a branch get archived?

**Options:**
- On milestone close (M9 verify COMPLETE on the last feature)
- On operator explicit "close this milestone"
- Time-based (older than N days)
- Manual via `daedalus memory consolidate <branch>`

**Provisional answer**: On operator-acknowledged milestone close. Operator gate ensures consolidation only happens on a clean state; auto-close on M9 risks consolidating a partial state (e.g., M9 passes for the last feature but earlier features had open issues).

### Q3: What about agents that participate across multiple branches simultaneously?

In pipeline-parallelized runs, two features in different implementation branches run concurrently. Each branch has its own implementation context. An agent records to whichever branch is active in its execution context.

**Resolution**: contextvar is task-local (asyncio-aware), so concurrent tasks each see their own active branch. No cross-contamination.

### Q4: Querying for forensics / paper data

Operator/dashboard/paper-analysis queries that want to see "everything that happened, including wedges, archived or not" need `branches=None`. The default semantic for agents is scoped; the override for analysis is unscoped. Clean separation.

## Implementation chunks

Recommended sequencing for shipping T-a2:

**Chunk A: Schema + read/write path (the core)**

- Add schema v2 migration to EpisodicStore (`branch_id` column + index)
- Add `branches: list[str] | None` parameter to `query_by_thread` + `query_by_speaker`
- Add `get_active_branch_id() / set_active_branch_id()` contextvar helpers (parallel structure to `get_active_milestone_scope`)
- Update `record()` to read active branch
- Backward-compatibility: `branches=None` returns all branches (existing behavior); `branches=[...]` filters

Tests: ~6 cases (schema migrates cleanly, default branch tagging, filtered reads, multi-branch reads, contextvar isolation between tasks, legacy data is queryable).

**Chunk B: Runner integration**

- Wire `set_active_branch_id` calls into the workflow runner at design/impl pass boundaries
- Branch ID derivation: from active milestone scope + (for impl) active feature slug
- Cleanup: clear branch on pass end

Tests: ~4 cases (design pass tags utterances correctly, impl pass tags correctly, no leakage between concurrent runs, project-level fallback when no scope active).

**Chunk C: Consolidation primitive + Mock Turtle wiring**

- New workflow phase: `consolidate-milestone` (1 meeting, Mock Turtle solo)
- Mock Turtle directive: read branch, generate summary, ship as `milestone_summary` utterance to project branch
- Substrate hook: on summary utterance write, rewrite branch_id of original utterances to `archived:*`
- Operator gate: dashboard button "Close milestone N + consolidate memory"

Tests: ~5 cases (consolidation runs cleanly, summary lands at project level, archived rewrite happens, default reads exclude archived, forensic reads include archived).

**Chunk D: Operator-facing dashboard surface**

- Dashboard view: show branch tree for the project (project root + per-milestone branches + per-feature impl sub-branches)
- "Memory branches" pane shows utterance counts per branch + consolidation status
- Optional: branch inspection modal — show utterances scoped to one branch

Tests: ~3 cases (dashboard renders branch tree, click-through to branch utterances, consolidation status visible).

**Chunk E: Migration tooling for existing pilots**

- `daedalus memory migrate-to-branches <project>` — runs schema v2 migration on all per-agent stores, leaves all data as `project` branch
- Optional: heuristic-based assignment ("utterances during M2 design timestamp range → design:m2 branch")

Tests: ~3 cases (migration is idempotent, existing data preserved as project-level, schema_meta version bumps correctly).

**Total scope estimate**: 5 chunks, probably 3-5 sessions of focused work. Chunks A + B are the minimum-viable substrate change; C is the consolidation flow; D + E are operator UX + back-compat.

## Risks

- **Schema migration on live agent DBs**: write a careful idempotent migration. Existing mvp-demo DBs need to survive the upgrade. Test against a copy of mvp-demo's `.wonderland/memory/`.
- **Performance**: adding a `branch_id` index is cheap; the per-agent query patterns are all narrow. Should be fine.
- **Constitution churn**: Mock Turtle's directive needs an update to teach the consolidation work. That's constitutional editing — light touch per the "don't lightly change constitutions" feedback, but unavoidable here.
- **Pipeline-parallel runs**: contextvar discipline matters. Verify with a test that simulates two concurrent implementation tasks tagging utterances to different branches.

## Decisions needed from operator

1. Q1 above — does impl inherit design branch memory? (Provisional: NO, but worth confirming.)
2. Q2 above — when does consolidation fire? (Provisional: operator gate, but auto-on-M9 is also viable.)
3. Sequencing: ship A+B as a chunk (minimum-viable) and validate against the substrate before C? Or A+B+C as one chunk?

## Sequencing within p20

T-a2 is the largest item but has no dependencies — can start as soon as T-a1 instrumentation is in place. T-a3/T-a4 don't depend on T-a2. T-a7 (the pilot) wants T-a2 done before firing.

Reasonable session-level plan:
- **Session 1 (this one)**: T-a1 investigation + this design doc.
- **Session 2**: T-a2 chunk A (schema + read/write path).
- **Session 3**: T-a2 chunk B (runner integration) + start C.
- **Session 4**: T-a2 chunk C done + T-a3/T-a4 in parallel.
- **Session 5**: T-a2 chunks D + E (operator surface + migration).
- **Session 6**: T-a7 — the pilot.
