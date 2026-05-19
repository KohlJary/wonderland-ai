# Dev — unreleased

Active changes accumulating toward the next cut. On release, copy this file to `release-notes/<version>.md` and wipe back to header-only.

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
