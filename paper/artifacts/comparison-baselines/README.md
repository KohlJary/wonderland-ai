# Comparison baselines — A / B1 / B2 vs Wonderland

> Three baselines run on `claude-haiku-4-5-20251001` against the
> same notebook directive that mvp-demo2 produced. The variable
> being tested is **substrate + scaffolding**, not the model.
> Two comparison axes: **code quality** (where baselines compete
> fairly) and **artifact trail** (where baselines structurally
> cannot compete by construction). The production-scale
> extrapolation is the load-bearing finding: the discipline
> differences look minor at notebook scale but each maps to a
> known production bug class.

## The four runs

| Run | What it models | Setup | Cost | Output |
|---|---|---|---|---|
| **A** — single-shot, no tools | "User pastes directive into claude.ai" | One inference call, max 8192 output tokens, minimal system prompt | $0.0417 | One backend file (truncated) + 4 frontend files, ZERO tests, ZERO configs |
| **B1** — custom tool loop | "User builds a minimal agent with filesystem tools" | 60-turn agent loop, write_file/read_file/list_files/run_bash tools, $5 budget cap | $1.4616 | 39 source files, 15 tests, hit iteration cap before verifying |
| **B2** — Claude Code subagent | "User runs Claude Code on the same model" | General-purpose subagent with Haiku model + Claude Code's full toolset, 87 tool calls in 6.4 min | ~$1.50–3 (subagent billing approximate; usage reports 73,843 tokens) | 24 source files, 17 tests, all passing per subagent's own verification |
| **Wonderland** — mvp-demo2 | The actual substrate + cast | Full pilot: discovery + milestone-plan + 3 × (design + implement) with operator gate-approval | **$83.78** | 49 source files (3,371 app + 1,577 test LOC), 61 tests, [682 markdown trail artifacts](../../../demo/wonderland-trail/) |

All four runs are reproducible — A and B1 via [`run_single_shot.py`](./run_single_shot.py) + [`run_tool_loop.py`](./run_tool_loop.py); B2 by spawning a Claude Code subagent on Haiku; Wonderland via the substrate at version 0.8.0 against `src/wonderland/closet/directives/notebook.yaml`.

---

## Axis 0 — Feature coverage (the most basic question)

Before evaluating *how well* the baselines build, we have to
check *whether* they built what was asked. The directive's
[notebook.yaml](../../src/wonderland/closet/directives/notebook.yaml)
names six core capabilities. Audit each baseline against the
list, code-read + actually-exercised:

| Capability (from directive) | A | B1 | B2 | Wonderland |
|---|---|---|---|---|
| Create note (title + markdown body) | ✓ partial (truncated mid-CSS) | ✓ end-to-end | ✓ end-to-end | ✓ end-to-end |
| Optional tags, one or more per note | ✗ | ✓ | ✓ | ✓ |
| Edit existing note | ✗ | ✓ PUT /api/notes/{id} | ✓ PUT /api/notes/{id} | ✓ PUT with `If-Match` collision detection |
| Delete existing note | ✗ | ✓ DELETE /api/notes/{id} → 200 | ✓ DELETE /api/notes/{id} → 200 | ✓ DELETE /api/notes/{id} |
| List most-recently-edited first | ✗ | ✓ `ORDER BY updated_at DESC` | ✓ `ORDER BY updated_at DESC` | ✓ `ORDER BY updated_at DESC, id DESC` (deterministic on ties) |
| Markdown preview pane next to editor | ✗ | ✓ `<MarkdownPreview>` inside NoteEditor | ✓ `<NotePreview>` in App | ✓ DOMPurify-sanitized `<Preview>` in EditorLayout |
| Filter list by tag | ✗ | ✓ `?tag=` query param | ✓ `?tag=` query param with SQLAlchemy join | ✓ rich tag-filter UI in Search |
| Search title + body + **tags** | ✗ | ✓ all three (Python `in` substring loop) | ✓ all three (SQLAlchemy `ilike` + `Note.tags.any(Tag.name.ilike(…))`) | ✓ all three (parameterized `_safe_ilike` + escape discipline) |

**B1 (Haiku tool loop): all 6 capabilities work end-to-end.**
Tested by curl: create with tags persists, list returns
most-recent-first, search finds matches in title / body /
tags, tag filter narrows to that tag, edit and delete return
correct responses, markdown preview renders inside NoteEditor.

**B2 (Claude Code subagent): all 6 capabilities work end-to-end,
but ships a silent-wrongness bug on search.** Search for the
literal character `%` returns 3 results instead of 1 (every
note matches, because `ilike(f"%{search}%")` treats user-input
`%` as a SQL LIKE wildcard, not a literal). This is the exact
bug class Wonderland's `_safe_ilike` + `_escape_like_pattern`
discipline guards against — and that
[`demo/wonderland-trail/test-scenarios/scenario-01KRXVFV-text-search-ignores-special-characters-sql-injection-boundary.md`](../../demo/wonderland-trail/test-scenarios/)
documents as a Hatter scenario severity `silent-wrongness`.

**B1 happens to dodge the wildcard bug** because it uses a
Python `in` substring loop (the O(N) cliff). The
discipline-gap and the bug-avoidance are linked: B1 sidestepped
the wildcard bug by using a worse-scaling implementation that
never sends `%` to SQL LIKE in the first place. Trading one
class of problem for another, not solving either deliberately.

**Wonderland: all 6 capabilities + the escape discipline.**
Live-verified during cross-checking (see §9 of
[code-quality-mvp-demo2.md](../code-quality-mvp-demo2.md)):
literal `%` search returns 1 (correctly).

### A subtler finding from this exercise: schema-name divergence

During the audit I initially POSTed with `tag_names: [...]`
(Wonderland's field name) — and both B1 and B2 returned `200
OK` with **empty tags**. Pydantic's default `extra='ignore'`
silently dropped the unknown field. The directive doesn't
specify a field name; both `tag_names` (Wonderland) and `tags`
(B1, B2) are valid choices. But contract-name divergence
between frontend and backend, or between client SDK versions,
silently losing data is itself a real production concern. The
substrate primitive that would prevent this — Pydantic
`model_config = ConfigDict(extra='forbid')` — appears in
neither baseline. Not a defect; a default-permissive choice
with substrate implications.

### What Axis 0 establishes

Before any of the discipline / artifact-trail framings, the
baseline cases:

- **A** doesn't cover the feature surface at all (truncated).
- **B1 + B2 cover the feature surface end-to-end** — they
  ship working notebooks.
- **B2 ships a silent-wrongness bug on the search feature**
  that the directive's own success criteria
  (*"find a note you wrote last week"*) would expose under
  realistic usage with punctuated content.
- **Wonderland covers the surface AND ships the discipline**
  that prevents the silent-wrongness bug.

The remaining axes describe *how well* the baselines that
shipped functional apps built them — and what's missing that
makes them less maintainable. But Axis 0 is the precondition:
the baselines that build *something* are competitive enough
for the rest of the comparison to be interesting. If they
weren't, the comparison would collapse to "Wonderland builds
working apps and the baselines don't," which is much weaker
than the actual finding: *"all three single-agent approaches
build a working app; Wonderland builds one with discipline +
provenance the others don't have, at higher upfront cost
that buys exactly what production deployment requires."*

---

## Axis 1 — Code quality (where baselines compete)

### Quantitative metrics

| Metric | A (no tools) | B1 (tool loop) | B2 (Claude Code) | Wonderland |
|---|---:|---:|---:|---:|
| App LOC | ~600 (truncated) | ~2,200 | ~760 (incl. CSS modules) | 3,371 |
| Test LOC | 0 | ~400 | 281 | 1,577 |
| **Test:code ratio** | **0.00** | **0.18** | **0.37** | **0.47** |
| Test count | 0 | 15 (14 pass / **1 fail**) | 17 (all pass) | 61 (all pass) |
| Backend file split | 1 (truncated) | 1 (monolithic) | 4 (main / models / schemas / database) | 4 (models / db / main / api/) |
| Frontend components | 4 (partial) | 7 | 5 | 9 |
| Configuration files | 0 | yes (`pyproject.toml`, `package.json`, `vite.config.ts`) | yes | yes |
| Vite build succeeds | n/a | ✓ (296 modules) | ✓ (252 modules; tsc has 7 errors but Vite tolerates) | ✓ (41 modules — leaner) |
| Cost | $0.0417 | $1.4616 | ~$1.50–3 estimate (subagent billing not directly trackable) | $83.78 |
| Time | 36s | 4.7 min | 6.4 min | hours (multi-milestone) |

### Discipline-difference observations

Spot-check of disciplines that emerged in the Wonderland output but not in the baselines:

| Discipline | A | B1 | B2 | Wonderland |
|---|---|---|---|---|
| SQL escape helpers for LIKE wildcards | n/a (no search) | **Missing** (uses Python `in` substring after `query.all()`) | **Missing** (uses SQLAlchemy `.contains()` on column — parameterized so no injection but no escape discipline) | `_escape_like_pattern` + `_safe_ilike` (`notes.py:196-246`) with **anti-bypass docstring** |
| Tz-aware datetime normalization | n/a | **Missing** (uses `datetime.utcnow()`, naive — 38 deprecation warnings at test runtime) | **Missing** (uses `datetime.utcnow()`, naive — 54 deprecation warnings at test runtime) | `ensure_tz_aware()` (`models.py:114-131`) handles naive vs aware, emits ISO8601 with Z suffix |
| Schema normalization | n/a | **Missing** (tags as JSON string column on Notes) | Present (proper `Note`/`Tag`/`note_tags` association table) | Present + `AuditLog` table with `state_hash` |
| Optimistic locking + collision detection | n/a | **Missing** | **Missing** | `revision_id` + `If-Match` header + `AuditLog.state_hash` for tamper detection |
| XSS prevention on markdown render | n/a | `react-markdown` (sanitized by default — different valid approach) | `react-markdown` (sanitized by default — same approach as B1) | `DOMPurify.sanitize()` before `dangerouslySetInnerHTML` |
| Inline contract/ticket references | n/a | None | None | **39** references across 8 source files — same contract (`contract-note-01KRY0B8`) cited from backend `models.py` AND frontend `api.ts` |
| Severity-tagged tests | n/a | n/a (no tests) | None | 24 tests tagged with Hatter's vocabulary (`breakage` / `silent-wrongness` / `degradation` / `curiosity`) |

Independent cold reviewer's verdict on Wonderland's `demo/` (see [code-quality artifact](../code-quality-mvp-demo2.md) for the full review): *"competent, above-average code for an MVP. Backend has notably good security discipline around LIKE-wildcard escaping and an over-engineered-but-thoughtful audit/revision design. Tests are unusually self-aware about edge cases. … no security blockers."*

No independent review has been run on A / B1 / B2 outputs. The discipline gaps above are observable directly without one.

---

## Axis 2 — Artifact trail (where baselines structurally cannot compete)

This is the axis the user surfaced mid-pilot and that reshapes the comparison's framing:

> *"Even if they do produce functional apps, they won't have our artifact trail, the chain of decision making, a full board of tickets."*

By construction, single-shot agents (with or without tools) produce code. They do not produce:

| Artifact class | Wonderland (mvp-demo2 pilot) | A / B1 / B2 |
|---|---:|---|
| `requirements/` — operator answers structured with `kind`, `confidence`, verbatim quotes | **21** | 0 |
| `milestones/` — trajectory with `consumes_requirements` linkage | **3** | 0 |
| `stories/` — persona + situation + need + acceptance + confusion-flags + `realizes_requirements` | **25** | 0 |
| `features/` — story citations + persona + stack span + kind (capability vs foundation) | **11** | 0 |
| `tickets/` — sources + owner + stack_span + explicit `Blocked by:` dependency graph | **80** | 0 |
| `architecture/` (ADRs) — Context + Decision + **named Tradeoffs** | **7** | 0 |
| `rulings/` (security) — Severity + Domain + **Citation** (OWASP A09, SOC 2 CC7.2, GDPR Art. 32) + Required Remediation + Acceptance Criteria | **13** | 0 |
| `contract-notes/` — Current Shape + Proposed Change + Rationale (frontend/backend seam negotiation) | **30** | 0 |
| `test-scenarios/` — Severity + Setup + Trigger + Expected + Concern | **369** | 0 |
| `reviews/` (Caterpillar) — Verdict + per-finding Location + Quote + Read + Concern + Request | **52** | 0 |
| `implementations/` — Ticket ref + Contract ref + Invariants Enforced + Schema Changes | **67** | 0 |
| Lifecycle audit logs (JSONL) — every state transition with timestamp, actor, reason | **3 files**, hundreds of entries | 0 |

**Total Wonderland artifact trail: 682 markdown files + 4 audit-log files** (curated copy at [`demo/wonderland-trail/`](../../../demo/wonderland-trail/) for paper readers).

The asymmetry is structural, not engineering effort. A single-shot agent that ships code has no scaffold for shipping the *reasoning* alongside the code. The artifact trail is what makes the resulting code maintainable: any function in `demo/src/` traces back through implementations → tickets → features → stories → requirements → operator quote, in five hops, every artifact human-readable markdown.

---

## Production-scale extrapolation

The discipline differences in Axis 1 look minor at notebook scale: one user, one device, small data. But each B1 / B2 gap maps to a known production bug class that gets expensive fast at any real scale:

| B1 / B2 gap | Looks like at notebook scale | What it becomes at production scale |
|---|---|---|
| Python `in` substring search after `query.all()` | "kind of slow on big notebooks" | O(N) cliff. 10K notes × 100 concurrent users → the server falls over. The fix isn't "add an index" — the entire search architecture has to be replaced. |
| Tags as JSON string in a column | "works for one user" | Renaming a tag across 10K notes = data migration. Indexing tags for query = impossible. The schema decision propagates into every query and has to be unwound. |
| Naive `datetime.utcnow()` | "the timestamp shows up fine" | The famous *"users in different timezones see wrong dates"* production bug. Plus DST transitions, plus leap seconds, plus rows written before tz-aware was added. Standard distributed-systems pain. |
| No audit log | "we can see edits in git or something" | First SOC 2 / HIPAA / GDPR audit needs forensic reconstruction of *"what was state at time T,"* the exact bug the trail's `adr-01KRXX85-audit-trail-schema-full-state-snapshots-with-timestamped-revisions.md` explicitly designs against (*"full snapshots eliminate this risk; if storage grows in v2 switch to hybrid"*). |
| No optimistic locking | "single user, doesn't matter" | First lost-write incident with two tabs open. Or two devices. Or one user retrying a flaky network. Customer-facing data-loss bug; the fix is to add what Wonderland's `revision_id` + `If-Match` + `state_hash` machinery already does. |
| No SQL escape helpers | "search for `100%` returns weird results sometimes" | Either silent-correctness bugs on user-controlled search input (the case Hatter's `test_search_wildcard_issues.py` actively guards against) OR, if escape gets added later under deadline pressure, the bypass-bug pattern the substrate's anti-bypass docstring explicitly warns against. |
| No tests beyond happy path / no frontend tests | "manual testing catches things" | The class of bug that ships because the integration test that would have caught it was never written. Frontend conflict-state machines, async race conditions, multi-tab state — all the things Wonderland's Hatter scenarios + Caterpillar reviews actively probe. |

The reframe this produces: **the notebook directive is the right test case precisely because it's small enough that the discipline differences look minor.** A system that produces discipline by default on small problems is the system that produces discipline by default when the stakes raise. A system that needs to be *prompted* into discipline ships discipline gaps every time the prompt doesn't explicitly ask for one — and at production scale, no one writes prompts comprehensive enough to forestall all of them.

### And the gap widens with directive complexity

The notebook is a deliberately-small directive — single user, single device, six core capabilities, ~3,400 lines of application code. The substrate's value-add at this scale already shows the discipline differences above.

For a more complex project the gap should widen, because each substrate primitive's value compounds with directive complexity:

- **More features** → more cross-feature dependencies → more places where Caterpillar's M8 cross-ticket coherence review catches what single-agent generation can't see (sibling features filling claimed gaps; contract drift between Tweedles; orphaned components never wired into the entry point).
- **More architectural decisions** → more ADRs the baselines simply don't produce + more places where the tradeoffs section would foreclose downstream rework.
- **More elaborate schema** → more migration work that Wonderland's lifecycle tracking + audit log capture; baselines tend to ship monolithic schemas that have to be unwound later.
- **Larger attack surface** → more Queen rulings with citations (OWASP / SOC 2 / GDPR). Already a serious gap on the notebook; load-bearing for anything with user data + retention requirements.
- **Longer trajectory** → more milestones where the substrate's branching memory + Mock Turtle consolidation matter, vs single-agent baselines whose context window is the only memory they have.
- **More implementation surface** → more places where static-time bugs (e.g. squathero3's Pydantic field-shadow bug per [`project_caterpillar_static_blindspot.md`](../../.claude/projects/-home-jaryk-wonderland-ai/memory/project_caterpillar_static_blindspot.md)) get caught by M9's verify build-checks, vs baselines that ship the bug into the working tree.

Per pilot evidence: the `squathero` family of pilots (more complex than mvp-demo / mvp-demo2 — migrations, multiple architectural domains, ~11 ADRs in a single M4 pass) consistently surfaced substrate primitives the simpler notebook directive didn't stress. The Caterpillar `verify_imports` tool, the M3.5 ticket-consolidation pass, the convergence-failure detection — all earned their place on more complex pilots, then carried forward to the simpler ones for free.

**The notebook comparison establishes a floor.** The gap widens approximately monotonically with directive complexity, because each piece of substrate-machinery that looks like overhead on a small project becomes load-bearing on a large one. Future-work item 68a882b3 (design-all-first vs interleaved comparative pilot) and the cross-shape-transferability section of the future-work chapter are the open follow-ups that would quantify this.

### The economic argument sharpens

- Wonderland costs **$83.78** to produce code with the disciplines that would be required for the production version anyway.
- B1 costs **$1.46** to produce code with discipline gaps that would each become a production bug.
- A costs **$0.04** to produce code that can't even fit a full app in one inference.

The first SOC 2 finding, first lost-write incident, first tag-rename migration, or first slow-search SEV reverses the savings — and unlike the LLM spend, those costs include engineering hours under incident pressure, plus customer trust damage, plus compliance exposure.

Per `project_quality_cost_inversion.md` (Pillar 1 of the evidence chapter): quality and cost move together under identity constraints. The comparison-baselines data extends this from "across substrate iterations" to "across scaffolding approaches at fixed model class." Wonderland is more expensive than the single-shot baselines in upfront LLM cost; it is less expensive than the baselines in total cost-of-ownership because the disciplines it produces are exactly what production deployment requires.

---

## How this comparison maps to the paper

- **Pillar 1 (quality-cost coupling)** — extended from "substrate iterations" to "comparative scaffolding." Wonderland's higher per-pilot cost buys disciplines that the baselines either lack or ship with bugs.
- **Pillar 2 (multi-lens identity-anchored review)** — the discipline-difference table is the receipt. Each item Wonderland produces is traceable to a specific character's lens (Hatter for severity-tagged tests + escape scenarios; Queen for audit log + security rulings; Caterpillar for cross-ticket coherence; Cat for ADR tradeoffs).
- **Pillar 5 (constraints improve quality)** — substrate constraints aren't a tax on cost; they're the forcing function that produces production-shaped output by default.
- **Thesis Corollary 4 (production shape as a derived property)** — sharpened: the property isn't just that Wonderland produces shipping-shaped code, it's that *at production scale, the "production shape" disciplines are the floor that matters*. Vibe-coded MVPs scale into incidents; Wonderland-shaped MVPs scale into maintainable systems.
- **Limitations chapter** — closes the recommended-baselines line item from the code-quality artifact §8.

---

## What this directive doesn't surface — the comparison's biggest blind spot

The notebook directive is **the most charitable scenario
possible for the single-shot baselines.** It's a well-structured
spec — names every capability, the stack, the persona, the
deal-breakers, the success criteria. *The directive itself
does most of the cognitive work that, in a less-scoped
scenario, Wonderland's discovery + milestone-plan workflows
would do.* When the prompt is *"build a personal markdown
notebook with these 6 capabilities on
Python+FastAPI+SQLite+React+Vite+TypeScript, single-user no
auth,"* even a single-shot agent has enough to work with.

The substrate's *real* differentiation lives in the work the
directive in this case made unnecessary. Four scenario shifts
that the current comparison doesn't exercise but that future
comparative pilots should:

- **Vague prompts.** *"Build me a notebook app"* (no
  capabilities listed, no stack named, no persona, no
  deal-breakers). Baselines would make assumptions and ship
  what they assumed; Wonderland's I1/I2/I3 interviews surface
  ambiguity, deal-breakers, deferred personas before any code
  is written. The Pillar 4 "production shape as derived
  property" finding tightens *much* more under vague prompts
  than under prescriptive ones.
- **Higher-complexity directives** (squathero-class). 11+
  architectural decisions, multi-domain schemas, larger
  attack surface. The static-blindspot Pydantic bug
  Caterpillar's M8 missed (per
  `project_caterpillar_static_blindspot.md`) is the kind of
  finding the notebook doesn't surface — the directive is
  small enough to fit in any agent's attention; squathero
  isn't. Cross-feature coordination, M3.5 ticket
  consolidation, sibling-feature visibility all become
  load-bearing rather than nice-to-have.
- **Long trajectories.** Multi-milestone, multi-month,
  multi-operator. Branching memory + Mock Turtle consolidation
  + interviews-as-amendable-state aren't really exercised by
  a 3-milestone notebook pilot. The Tier 2 autonomy claim
  hasn't been tested over the kind of trajectory where memory
  bleed would otherwise compound.
- **Production deployment + first incident.** The disciplines
  Wonderland produced (optimistic locking, audit log, escape
  helpers, normalized schema) are the disciplines you would
  *add to the baseline-shipped app* after the first SOC 2
  finding, first lost-write, first tag-rename migration. They
  are priced into Wonderland's $84; they're deferred-cost on
  the baselines. The current artifact doesn't quantify the
  deferred cost because no baseline has been run through a
  realistic-load incident.

The honest framing of this comparison's value:

- **Within the spec'd, well-prompted, single-shot-friendly
  scenario:** the gap is narrower than it would be on harder
  cases. Baselines DO produce working notebooks. Wonderland
  produces a *better-disciplined, better-documented* notebook
  at significantly higher upfront cost.
- **The gap widens monotonically** with directive vagueness,
  complexity, trajectory length, and time-to-first-incident.
- **The dollar gap inverts at production deployment** — the
  disciplines Wonderland front-loads are the ones you'd
  spend engineering hours backfilling under deadline pressure
  later.

A future comparative pilot run on a vaguer prompt or on a
squathero-class directive would close the comparison's
biggest blind spot. Filed in the
[future-work chapter](../future-work-chapter-source.md#comparative-experiments-the-rigor-expansion).

---

## Honest limitations of this comparison

- **N=1 directive class.** All four runs targeted variants of the notebook directive. Different work shapes (CLI tools, TUI projects, ML pipelines, security-critical systems) may have different baselines-vs-Wonderland economics. The future-work chapter's cross-shape-transferability section is the open follow-up.
- **One model class (Haiku 4.5).** The comparison's variable is substrate/scaffolding at fixed model. A Sonnet baseline would test whether higher-capability models compensate for missing substrate; that's a separate experiment (also recommended in the code-quality artifact §8.2).
- **Single-shot baselines didn't get multi-turn refinement.** B1 hit iteration cap; an operator running it in a tight loop, reading output, and re-prompting could plausibly close some gaps. The point isn't that no human can produce disciplined code with a single agent — it's that *the substrate produces it without operator intervention*.
- **Wonderland had operator gate-approval.** mvp-demo2 was a Tier 2 autonomy pilot — operator skipped duplicates at gate points and approved transitions. The baselines had no equivalent. A fair criticism: a baseline run with operator-equivalent intervention (manually editing output, re-running) might close more gaps than the unattended versions reported here.
- **Claude Code (B2) billing isn't directly trackable** from the parent session — costs there are an estimate based on the subagent's reported tool-call count, not measured token-by-token.
- **The "production-scale extrapolation" section is mechanism-based, not empirical.** No bug-class incident was observed in production for these baselines (because they're not in production); the claim is that the gap-to-incident mapping is well-established in the software-engineering literature for each named pattern.

---

## See also

- [`run_single_shot.py`](./run_single_shot.py) — A baseline script (reproducible).
- [`run_tool_loop.py`](./run_tool_loop.py) — B1 baseline script (reproducible).
- [`single-shot-haiku-4-5/`](./single-shot-haiku-4-5/) — A baseline output.
- [`haiku-tools-custom/`](./haiku-tools-custom/) — B1 baseline output (metadata + transcript + workspace).
- [`haiku-claude-code/`](./haiku-claude-code/) — B2 baseline output (TBD).
- [`../code-quality-mvp-demo2.md`](../code-quality-mvp-demo2.md) — independent cold review of the Wonderland output.
- [`../../../demo/wonderland-trail/`](../../../demo/wonderland-trail/) — the artifact trail that's the second axis's receipt.
- [`../evidence-chapter-source.md`](../evidence-chapter-source.md) — the five pillars this comparison extends.
- [`../thesis-chapter-source.md`](../thesis-chapter-source.md) — the corollaries this comparison sharpens.

---

## Bugs found by actually running the baselines

A static-analysis + actually-run check across all three. (The
B2 subagent's claims were verified independently; the B1
claims were verified by running its committed workspace.)

### A — single-shot no tools

- Output **truncated mid-CSS rule** at the 8192 output-token
  cap (cut off in `padding-`). The "app" is a markdown
  document with code blocks, not a runnable artifact. No
  tests can be run because none exist; no build can be run
  because there are no config files.
- This is the **floor data point**: a no-tool single-shot on
  the current generation Haiku 4.5 cannot fit a full app's
  worth of code into a single inference.

### B1 — custom tool loop on Haiku

- ✗ **Test failure: 14 pass / 1 fail.** `integration_test.py::test_user_workflow`
  fails with `sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: notes` —
  the integration test that's *supposed* to verify end-to-end
  user workflow doesn't initialize the DB schema before
  running. **A bug the agent loop shipped without catching**,
  despite the agent's `run_bash` access to `pytest`.
- ✗ **38 datetime.utcnow() deprecation warnings** emitted
  during the test run. Will hard-error in a future Python
  version (likely 3.14). The static check shows the gap;
  runtime confirms it.
- ✗ Python `in` substring search after `query.all()` — works
  at test scale (~3 notes), O(N) cliff at any real scale.
- ✓ **Frontend builds cleanly** with `vite build` (296
  modules, 957ms). No tsc errors.

### B2 — Claude Code subagent on Haiku

- ✓ **All 17 tests pass** (verified by running
  `.venv/bin/pytest -v` on the subagent's output, confirming
  its self-report).
- ✗ **54 datetime.utcnow() deprecation warnings** at runtime
  — same gap as B1, larger count because the schema-level
  `server_default=func.now()` triggers the deprecation per
  test setup. Same future-Python breakage risk.
- ✗ **7 TypeScript errors** under `tsc --noEmit`:
  - 3 unused `React` imports (TS6133) — newer JSX runtime
    not configured in tsconfig.
  - 3 missing CSS module type declarations (TS2307) — the
    `.module.css` files exist but no `vite-env.d.ts`
    declares them for tsc.
  - 1 **real bug**: `Property 'inline' does not exist on
    type 'ClassAttributes<HTMLElement> & HTMLAttributes<HTMLElement> & ExtraProps'.`
    in `NotePreview.tsx:16:26` — passes an `inline` prop to
    react-markdown's component that the library's type
    doesn't declare. The component receives an undeclared
    prop at runtime.
- ✗ **Silent-wrongness search bug:** `GET /api/notes?search=%`
  (URL-encoded literal `%`) returns ALL notes instead of just
  the one containing a literal `%`. Root cause:
  `main.py:56` uses `Note.title.ilike(f"%{search}%")` without
  escaping LIKE metacharacters — user-input `%` becomes a
  wildcard. Verified by curl during Axis 0 audit:
  3 notes created, search for `%` returned 3 (expected 1).
  Wonderland's `_safe_ilike` + `_escape_like_pattern`
  discipline + `test_search_wildcard_issues.py` regression
  test explicitly prevents this class. **The B2 test suite's
  17/17 pass count doesn't include a test for this case** —
  it would have failed if one existed.
- ✓ **Frontend builds with `vite build`** anyway (252
  modules, 1.02s) — Vite's bundler is more permissive than
  `tsc --noEmit`. The tsc errors don't block production
  bundling but would block any CI pipeline running `tsc`.

### Wonderland — mvp-demo2 demo/

- ✓ **All 61 tests pass** (verified during code-quality
  artifact prep).
- ✓ **Frontend builds with `vite build`** (41 modules — 6-7×
  leaner than the baselines, 629ms — fewer transitive
  dependencies because the substrate doesn't pull in
  unneeded scaffolding).
- ✗ Real bugs flagged by the [independent cold reviewer](../code-quality-mvp-demo2.md):
  - **B1**: silent `If-Match` bypass when client omits header
    (latent at single-user v1 scope; acute at multi-user v2).
  - **C2**: revision_id serialization mismatch between
    `list_notes` (Z-suffix) and `read_note`/`update_note`
    (naive isoformat) — produces different revision_ids
    for the same logical state, depending on the endpoint
    surfacing it (latent at single-user; acute at
    multi-tab).
  Both honestly framed in the code-quality artifact §6 as
  "latent at v1 / acute at v2" — infrastructure shape
  correct, implementation has bugs that the spec'd scope
  doesn't trip.

### What the run-it-don't-just-read-it check surfaces

The static-analysis-only review missed two things the
actually-run check caught:

1. **B1's integration test fails.** The static review noted
   "15 tests exist" — running them shows only 14 actually
   pass. A baseline that *ships its own test as broken*
   without noticing is a stronger signal of substrate gap
   than just "fewer tests than Wonderland."
2. **B2 ships a runtime-undeclared prop.** tsc catches it;
   the agent's self-report didn't. A frontend that builds
   in dev mode but errors under stricter typechecking is
   the class of bug that surfaces at the worst moment (CI
   pipeline, refactor, dependency upgrade).

Wonderland's M9 `pytest_passes` + `npm_build` build-checks
catch the first class (any test failure halts the feature's
ready_for_review transition); the substrate doesn't yet have
a `tsc --noEmit` build-check, so this is itself a
limitations-chapter follow-up (it would have caught the C4
contract-drift bug in `body_preview` comment that the
cold reviewer flagged).
