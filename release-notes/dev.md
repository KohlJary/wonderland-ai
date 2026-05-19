# Dev — unreleased

Active changes accumulating toward the next cut. On release, copy this file to `release-notes/<version>.md` and wipe back to header-only.

### `prime_directive` auto-syncs from Project registry to per-project `.wonderland/project.yaml`

Closes the follow-up from the original `prime_directive` field commit (`4be781d`): the Project registry stored `prime_directive` globally, but the per-project ProjectContext YAML (the thing actually seeded into MEETINGS via the `project_context` kind) didn't automatically pick it up. Operators had to manually edit `project.yaml`. Surfaced on obol-demo2 where the 6-milestone plan landed in the registry without the prime_directive carryover, so M4 / M5 / M8 design would have gone back to seeing only `stack + entry_point` — losing the "htop for money" framing after discovery.

Two sync points landed:

1. **`new_run.py:_launch_run`** — after writing the Project's last_run_id / last_workflow / prime_directive on run launch, mirror the prime_directive into the per-project ProjectContext. Best-effort, no-op when project.yaml doesn't exist (legacy projects without context memory), prime_directive is empty, or it's already in sync. Fires BEFORE `launch_background_run` so the subprocess reads the freshly-synced YAML.

2. **`skeleton.py:apply_skeleton` + `write_project_context_from_skeleton`** — both now accept an optional `prime_directive` parameter that gets written into the ProjectContext at project-create time. `new_project.py` passes `prime_norm` through both paths (bare-root apply + non-bare-root retrofit). Net-new projects get `prime_directive` in `project.yaml` from day one rather than waiting for first launch.

4 new tests in `test_skeleton.py` covering: directive-persists path, none-omitted back-compat, whitespace-treated-as-none, retrofit path via `write_project_context_from_skeleton`. 47/47 tests pass (test_skeleton + test_project_context).

For projects already on disk that were created before this commit: the next launch will sync automatically. Or use the one-line `load_project_context` / `save_project_context` round-trip if the operator wants to populate immediately without launching.

### Episodic memory branching — ContextVar → workflow-scoped global

Branching memory was nominally working: schema v2 has a `branch_id` column with index, `inheritance_chain()` correctly returns `[PROJECT_BRANCH, "design:m3-..."]` for active design scopes, and `run_workflow` calls `set_active_branch_id("design:<slug>")` at entry. But every single utterance from every run was tagged `branch_id='project'` regardless of the active milestone — diagnosed on obol M3 design where 1,179/1,179 of Caterpillar's utterances landed on `'project'`, letting M2 deliberation bleed into M3 recall and prompting the design caucus to loop on M2's Feature 002 instead of designing M3 budget features.

Root cause: `_active_branch` was implemented as a `ContextVar`, which captures its value at `asyncio.create_task` time. The Runner spawns each agent's `run()` as a background task during `Runner.start()` — BEFORE `run_workflow` later calls `set_active_branch_id`. Each agent task carries a snapshot of the default `PROJECT_BRANCH` for its entire lifetime; later `set_active_branch_id` calls modify only the workflow task's contextvar; agents' `memory.record(utterance)` reads its own task's stale snapshot and writes `branch_id='project'` every time.

Fix: replace the `ContextVar` with a module-level mutable `str`. The asyncio event loop is single-threaded, so process-wide visibility is structurally consistent with how workflow scope actually works. Pipeline parallelism within one workflow correctly shares the branch (all parallel ticket-impl threads belong to the same milestone-impl scope). Concurrent runners in the same process aren't a current use case; if they become one, the right fix is per-Runner state, not a return to ContextVar's brokenness.

The token returned by `set_active_branch_id` is now the prior branch_id string (was previously a ContextVar.Token); `reset_active_branch_id` tolerates legacy Token-shaped callers during migration by resetting to PROJECT_BRANCH on type mismatch — defensive, not load-bearing.

What this changes:
- Future workflow runs correctly tag utterances with their milestone-scoped branch id.
- Future agent recall (via `inheritance_chain`) correctly filters to project + active-branch — historical PROJECT_BRANCH content stops being the catch-all.

What this **doesn't** fix:
- Existing on-disk episodic data (e.g. obol's pilot history) is tagged `'project'` for every utterance and there's no way to retroactively re-attribute it to a milestone — the substrate didn't track that metadata at write time. Operators iterating on an existing project should wipe per-agent `episodic.sqlite` files (via `scripts/wipe-design.sh` or manual) before the first run on the new branching semantics; otherwise the legacy data continues to leak into recall through the PROJECT_BRANCH path.

Test: the prior `test_contextvar_isolation_between_tasks` was encoding the buggy semantic as the spec — it asserted that three concurrent tasks each see their own branch. Replaced with `test_active_branch_is_process_wide_across_spawned_tasks` which encodes the new contract: an observer spawned BEFORE the parent task's `set_active_branch_id` call still sees the new branch, because the global propagated. This is exactly the Runner-spawns-agents-first / run-workflow-sets-branch-later case that was broken in production.

284/284 tests pass across `test_episodic` + `test_workflow`.

Surfaced by obol M3 design pass (paper-grade): operator noticed M2 features leaking into M3 design caucus, traced to per-agent episodic memory. Branching memory was the architectural fix per `project_substrate_fixes_dont_propagate_through_memory.md`; this is the substrate work catching up to the design intent.

### Read-time phantom-citation filter in `seeds_fallback` — closes the obol M3 dangling-reference loop

Surfaced by the obol M3 design caucus looping for several turns on Feature 002's citations to non-existent stories. Root cause: phantom citations can become phantom *after* the on-emission strip catches them at composition time. A story gets retracted in a later run, or its .md file goes missing (substrate bug `d9c120d4`), and any features citing that story now carry dangling references through every downstream meeting that pulls them as seeds.

`seeds_fallback._load_features` and `_load_tickets` now run a citation-resolution check on each candidate artifact BEFORE the milestone-scope filter. Features whose `Sources:` line cites a story slug or GUID that doesn't resolve to a real story on disk get dropped from the seed pool with a `WARNING`-level log line naming the phantom citations. Same shape for tickets, which can cite features or stories.

The check reuses existing T-g5 machinery — `_source_resolves` and `_collect_disk_slugs_and_guids` from the on-emission strip path. New `collect_phantom_citations()` in `workflow` exports the per-sources phantom-detection logic so the on-load filter and the on-emission strip share validation logic, plus testing wedges directly on it without spinning up a full workflow.

Operator impact:
- Pilots no longer loop on coherence-fix proposals for artifacts whose cited stories were retracted in a prior run.
- The filter is read-only: it doesn't modify disk artifacts, only filters them out of seed pools. Operators clean up phantom citations manually (or via retract) when they want to fix the disk state.
- WARNING-level log emission on every drop, so the substrate is honest about what it found rather than the prior defensive-default that quietly kept corrupted records in scope.

What this **doesn't** fix:
- The root cause of phantom citations getting written in the first place (substrate bug `9231bcd5`) — that needs separate work on the agent-side citation-write path.
- The lost-feature-.md bug class (substrate bug `d9c120d4`) — needs investigation in the M2 substrate retract / wipe paths.

But it closes the loop on bug `0c98c694` (defensive-default leak): the prior `if primary is None: include` branch in `_load_features` was masking exactly this class of drift. With the new filter, unattributable features whose unattributability stems from phantom citations get explicitly dropped + warned rather than silently included.

6 new tests covering: clean-feature happy path, phantom-detection across slug/GUID/`<guid>:<slug>` citation forms, ticket-cites-feature-or-story polymorphism, the read-time `_load_features` drop, the read-time `_load_tickets` drop, and no-active-milestone-scope still applies the citation filter. Plus repairs to 6 existing fixtures that cited placeholder slugs (`"s"`, `"x"`, `"see-my-money-at-a-glance"`) without registering matching stories — latent corruption the new filter correctly surfaced; fixtures now register a placeholder story via a shared helper before citing.

384/384 tests pass across the affected suites (`test_seeds_fallback`, `test_workflow`, `test_coverage`, `test_feature`, `test_ticket`).

### `exec_smoke_probe` tool — runtime probe for Caterpillar's M8 review

Surfaced by the obol M2 post-mortem: M2 shipped a SQLite CHECK constraint (`CHECK (transaction_date <= DATE('now'))`) which SQLite refuses to enforce because `DATE('now')` is non-deterministic. The constraint is syntactically valid and passes static review, `verify_imports`, and the unit test suite — but every INSERT raises `DATABASE_ERROR: non-deterministic use of date() in a CHECK constraint`. The entire transaction-creation surface (manual entry + CSV import) was non-functional. Cat's three M8 reviews on that feature caught real findings (duplicate Account dataclass, LedgerScreen index-vs-id bug, etc.) but couldn't see the CHECK rejection — static review reading source code has no way to know which constraints SQLite will refuse at INSERT.

Fix: add a third runtime tool to Cat's review kit alongside `git_diff` and `verify_imports`. `exec_smoke_probe(snippet, timeout_seconds=30.0)` runs a Python snippet in the project root via `python -c`, captures stdout + stderr + exit code, truncates to ~4 KiB. Snippet length capped at 16 KiB. The tool's primary signal is the exit code + stderr content; ToolError only surfaces infrastructure problems (no Python, timeout, oversized snippet).

Cat's `_TOOLS_SECTION` directive prose gains a new bullet teaching when to reach for the probe: any diff that touches side-effect-producing code (DB writes, SQL execution, file I/O, subprocess invocation, network calls). The class of bug articulated: SQL CHECK rejected at INSERT, schema drift surfacing as FK violations, framework wiring that 404s or no-ops silently, async coroutines that deadlock.

Validated against the actual M2 bug: a 6-line probe (`init_test_accounts(); add_transaction(...)` → `print(result)`) surfaces the `non-deterministic use of date()` error in seconds. Cat reading that output would file a `block`-severity bug finding with the traceback message quoted.

11 new tests covering happy path, traceback capture, in-project-root execution, empty/oversized snippet rejection, timeout enforcement, output truncation, and dispatch wiring. 84/84 `test_tools.py` pass.

Caveats / follow-ups:
- The schema-drift bug class (M1 TEXT PK → M2 INTEGER PK without migration) is partially probe-catchable but harder — needs the probe to set up M1-era DB state, which Cat would have to know to do. A narrower `verify_schema_stable` tool (compare current CREATE TABLE statements against existing DB at standard paths) would catch it directly; filed as future work.
- Probes that write to the filesystem leave artifacts (test DBs, temp files). For obol-class projects this is benign; for projects with shared global state, Cat's directive guidance ("flag probe side-effects that the production code shouldn't have") is the discipline mechanism, not a substrate sandbox.
- Cost: each probe is a single tool-use round-trip; the snippet + output sit in Cat's context for the rest of the review. Tightening over time if probe-output-bloat becomes a cost driver.

Origin: operator post-mortem on the obol M2 review pass where multiple Cat verdicts shipped despite the runtime-blocking CHECK bug. The pattern echoes the mvp-demo2 stale-schema and partial-node_modules findings that surfaced during live verification — runtime-only bugs cluster as a class that static review structurally cannot reach.

### `demo/` reorganized into `demo/<pilot>/` for multi-pilot artifacts

Mvp-demo2's shipped artifact moved from `demo/` to `demo/mvp/`. The `demo/` parent is now reserved for additional pilot reference applications (e.g. `demo/crm/` if/when the CRM pilot ships, future obol artifact at `demo/obol/`, etc.). Pyproject's sdist exclusion still prefix-matches everything under `demo/`, so the PyPi build remains unaffected.

Path references updated across:
- `paper/README.md` — repo layout section reflects the new convention
- `paper/artifacts/code-quality-mvp-demo2.md` — all 8 file:line citations
- `paper/artifacts/comparison-baselines/README.md` — wonderland-trail links + cold-reviewer references; also fixed one stale relative-path link that had been one `../` short
- `paper/artifacts/limitations-chapter-source.md`, `mvp-demo2-pilot-narrative.md`, `future-work-chapter-source.md`
- `src/wonderland/closet/analyses/034-mvp-demo2-autonomous-pilot.md`
- `release-notes/0.8.1.md` — historical doc, but dead links updated so readers don't 404
- `demo/mvp/README.md` — self-references (header, run instructions, all 7 relative links retargeted from `../<path>` to `../../<path>`)

Git tracked all 700+ moves as renames (R) cleanly, so blame/log on the artifact files still threads through to the pre-rename commits.
