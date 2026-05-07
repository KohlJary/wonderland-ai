# P8 — User-facing Interface (TUI + Web)

**Goal:** A fresh-faced user installs Wonderland, opens an interface, understands what the system *is*, and can run their first directive without reading source code or any markdown files. By the end of P8 they can also: watch a live run with full visibility, browse what the team produced, configure their setup, and (when the framework is hosted) use it as a non-technical user via web.

**Architectural principle:** Headless observer/query API decoupled from rendering. TUI built in [Textual](https://textual.textualize.io/) — same component code renders to terminal *and* to web. CLI deferred indefinitely; if automation/scripting needs exist later, expose them on the same API, not as a separate frontend.

**Scope boundary:** P8 ships the *experience* of using Wonderland. It does not change the substrate (runner, agents, workflows). Bug fixes that surface during the work might land in lower P-numbers, but they're knock-ons, not goals.

---

## P8.1 — Observer / query API substrate

The load-bearing piece every other sub-phase consumes. Everything that's currently internal to `Runner` and the workflow capture gets re-exposed as a stable contract. The TUI, web mode, and any future MCP server consume the same surface.

**Replay-first design.** Build `HistoricalRunHandle` *before* `LiveRunHandle`. The historical case is load-bearing for development pace — every TUI iteration cycle uses real run data from `analyses/data/<NNN>/` snapshots without burning a single API call. We already have ~6 snapshots covering the framework's full failure-mode space (banner runs, MEETING_BUDGET cascades, M5-doesn't-fire, skeleton-overwrite). Those are the test fixtures. Once replay works, live mode is a strict extension of the same interface.

**Tasks:**

- `wonderland.observer` module: `RunHandle` interface (abstract). Two implementations:
  - `HistoricalRunHandle(snapshot_dir)` — reads from `analyses/data/<NNN>/wonderland-snapshot/` + `run.log`. Replays utterances at original timing, configurable speed (1x, 10x, instant, step-by-step). **Build this first.**
  - `LiveRunHandle(runner)` — subscribes to a running runner. Same interface as historical, just a different source.
- `wonderland.history` module: query API for past runs (list-snapshots-in-analyses, get-by-name, get-artifacts-by-kind, get-meeting-transcript, get-telemetry-slice). Reads from `analyses/data/` + `wonderland-snapshot/` directories.
- Episodic-memory merger: read all per-agent `episodic.sqlite` files for a snapshot, merge utterances by timestamp into a single chronological stream. This is what `HistoricalRunHandle` replays.
- `run.log` parser: structured parsing of the line-based log we currently render in `workflow_demo.py`. Extracts meeting-start/end events, state transitions, late-publish suppressions.
- Run aggregation helpers: current-meeting (live or replay-position), time-elapsed, budget-consumed, calls-by-agent, expected-vs-actual outcome — derived state the UI consumes directly without recomputing per render.
- Artifact loader helpers: read `.wonderland/<kind>/` markdown back into structured form (Story, Ticket, Feature, ContractNote, TestScenario, Review). Currently artifacts go to disk one-way; the inverse is needed for the artifact-browser views.
- Run-id assignment: stable identifier per run (existing telemetry filename convention is fine but should be promoted to first-class).
- Tests against fixture runs: every `analyses/data/<NNN>/` snapshot doubles as a test fixture. Validate the API surface against banner runs (e.g. 028) and edge-case runs (e.g. 029-v3 TIMEOUT, 029-v4 skeleton-overwrite, 029-v5 M5-RUNNING).

**Deliverable:** a Python API that any frontend can consume. Two operational modes:
1. *Historical* — load a snapshot, replay/inspect at any speed.
2. *Live* — attach to a running Runner.

The TUI in subsequent sub-phases starts in *replay mode*, iterates against fixtures until the layout/UX is solid, then enables live mode as a flag flip rather than a separate code path.

---

## P8.2 — TUI bootstrap + core navigation

Stand up the Textual app with the navigation skeleton and the views that don't require a live run. A fresh user can launch the TUI and see *what the system is* before running anything.

**Tasks:**

- Textual app skeleton: main layout, theme, keybindings, navigation between views
- Welcome / Home view: brief framing ("Wonderland is a team of named characters that collaborate on software development"), recent runs, primary actions ("Start a new run," "Browse past runs," "Meet the cast," "Configure")
- About / What is Wonderland view: one-screen explanation of the paradigm — characters, meetings, workflows, artifacts. Written for someone who has never read README. Lifts text from the README's intro paragraphs.
- The Cast view: browse the characters as a gallery. Each card shows name, role one-liner, characteristic failure mode, link to full constitution. Friendly framing — "Meet the Cheshire Cat — your architect" not "agent loaded from `cheshire_cat.md`".
- Configuration view: API key entry (with secure storage), default budget, default workflow, project root favorites. First-launch flow asks for API key before anything else.
- Workflow Picker (used by the new-run wizard but designed standalone): browse bundled workflows. Each workflow shows its meetings as a graph, the cost profile, when to use it.
- Constitution Reader: drill into a character. Renders the markdown constitution with section navigation (I-VIII).

**Deliverable:** a TUI you can launch and use to *understand* the system. New-run flow shipped in P8.3.

---

## P8.3 — Run watcher (replay first, live second)

The bread-and-butter view. Designed and iterated against historical snapshots first; live mode is the same view with `LiveRunHandle` instead of `HistoricalRunHandle`. Same panes, same keybindings, same layout.

**Why replay-first matters here.** The view's correctness across the failure-mode space (banner / MEETING_BUDGET / TIMEOUT / M5-doesn't-fire / skeleton-overwrite) needs to be validated against runs that already exist on disk. Burning a fresh API run to test "what does the timeline look like when M4 hits MEETING_BUDGET?" is wasteful when 029-v6's snapshot already has that shape.

**Tasks:**

- New-Run Wizard:
  - Step 1: workflow selection (with explanations from P8.2's Workflow Picker)
  - Step 2: project root (existing or new; if new, skeleton picker)
  - Step 3: directive entry (multi-line input, with example directives from past runs as prompts)
  - Step 4: budget confirmation (default from workflow, editable, shows "this typically costs $X")
  - Step 5: review and launch
- Run Watcher (the most complex view; multi-pane). Renders the same way for live and replay; only the data source changes:
  - **Top bar:** workflow name, current meeting (with name like "M2.5 — Advice from a Caterpillar"), elapsed time, cost burn rate, total cost / cap. In replay mode: a playback control (▶ / ‖ / step / speed-selector).
  - **Meeting timeline (left):** vertical list of all meetings, current one highlighted, completed ones checkmarked with their cost/duration, future ones grayed.
  - **Utterance stream (center):** scrollable bus events, one per line, agent name + speech act + body preview. Click/keypress to expand. Filterable by speaker. In replay mode: utterances appear at their original timestamps (configurable speed).
  - **Active agents panel (right):** who's deliberating, who's idle, who's emitted recently. Visual indicator of state transitions.
  - **Artifact tree (bottom or tabbed):** live-updating `.wonderland/` tree. Clicking an artifact opens a viewer. In replay mode: shows the artifact tree as it existed at the current playback position.
- State transition visualizations: when threads transition (RUNNING → STUCK → QUIESCENT → COMPLETE), surface as inline events so the user can see *why* the meeting ended.
- Late-publish indicator: when the late-publish guard suppresses an utterance, surface it as an explanatory note ("Hatter's response arrived after M4 closed — this is why his late test_scenario didn't ship; the team will work without it").
- Pause/abort controls: explicit user "stop this run" button (live mode: calls runner.abort; replay mode: pauses playback).
- Convenor escalation prompt UI: when Dodo escalates a deadlock to the human, the TUI surfaces the prompt and accepts the response (existing escalation registry hook). This is critical for the human-in-the-loop spec section. Live-mode-only.
- Cost projection: as the run proceeds, project total cost based on remaining meetings' caps. Lets the user know early if the run will hit global budget. (Live mode; replay shows actual final cost from the snapshot.)
- Replay-mode-specific: speed selector (1x / 4x / 16x / instant), step-forward / step-back keybindings, jump-to-meeting (e.g. "show me M5"), seek bar.

**Build order:**

1. Replay mode against `analyses/data/028-pomodoro-end-to-end/wonderland-snapshot/` (the banner run — clean shape).
2. Iterate the view against `029-substrate-convergence/v3/` (TIMEOUT shape), `v4/` (skeleton-overwrite shape), `v5/` (M5 RUNNING), `v6/` (banner with cost). Each is a different layout-correctness test.
3. Once replay UX is solid, add `LiveRunHandle` and the new-run-wizard. Live mode is structurally a strict extension of replay; the layout work transfers directly.

**Deliverable:** a fresh user can either watch a past run or run their first directive end-to-end with full visibility, in the same view, with the same controls.

---

## P8.4 — Inspection / browsing

Post-run reflection. What did the team produce, and was it good? This sub-phase becomes naturally cheap because P8.1's `HistoricalRunHandle` already does the data loading; P8.4 is just rendering specific cuts of it as views.

**Tasks:**

- Snapshot Library: top-level view of all `analyses/data/<NNN>/` snapshots, sortable by date / cost / outcome / workflow. The Run History list essentially. Click to open in either Run Summary view or Run Watcher (replay).
- Run Summary view: outcome (complete / budget cap / timeout / aborted), final cost vs cap, time elapsed, per-agent telemetry, artifact counts by kind, what shipped on disk (test files, production code, docs).
- Meeting Detail view: full transcript per meeting. Filterable by speaker / speech act. Linkable to artifacts mentioned.
- Artifact Browser: per-kind listing (stories, tickets, features, ADRs, contracts, test scenarios, reviews, implementations). Each item is rendered as the user-facing markdown — not the JSON payload — with cross-references to other artifacts.
- Code Diff Viewer: what production code shipped from the run. Side-by-side or unified diff against pre-run state. File-tree navigation.
- Test File Viewer: what test files shipped. Useful both for understanding what was pinned and for users who want to actually run pytest themselves.
- Review Findings panel: Caterpillar's findings rendered as a list with severity, file:line links, and any responses the Tweedles made.

**Deliverable:** a user can answer "what did the team build, and was it good?" without leaving the TUI. Works against any historical snapshot — including the analyses/data/ corpus we already have.

---

## P8.5 — Orientation / education for fresh users

Brought forward as its own sub-phase because it's load-bearing for adoption. Most users will not read README first.

**Tasks:**

- First-Run Tutorial: detected on launch when no past runs exist. Walks through:
  - "Welcome — here's what's about to happen when you launch your first run"
  - Brief tour of the cast (3-4 minutes max — the visitor is curious, not committed yet)
  - Picks the smoke workflow as the first run (cheap, fast, demonstrates the loop)
  - Pre-fills a tiny demo directive ("Add a /time endpoint that returns the current time as JSON")
  - Watches the run land with the user
  - Explains what just happened in summary
- Workflow Visualizer: graphical render of a workflow as a meeting graph. Nodes are meetings (labeled with their book-event names), edges are seed flows. Clicking a node opens that meeting's directive and roster. Helps users develop a mental model of "what's going to happen."
- Inline help / tooltips: every panel and control has a `?` keybind that opens contextual help. The TUI itself teaches its own use.
- Glossary view: terms specific to the framework (directive, convenor, meeting, seed, artifact, speech act, expectation, quiescence). Searchable. Linked from anywhere those terms appear.
- "Why is this happening?" panel: during a live run, the user can press a key and get a current-state explanation written for non-experts. "The team is currently in M2.5 (Advice from a Caterpillar). The Rabbit just shipped feature artifacts. Alice and the Caterpillar are reviewing them. M3 starts when this meeting completes."
- Sample directive library: bundled examples ranked by complexity, with explanations of what each one demonstrates. Helps new users gauge what kinds of directives produce good results.

**Deliverable:** a fresh-faced user with zero context can launch the TUI, understand what they're looking at within 5 minutes, and ship their first run without ever reading README.

---

## P8.6 — Cross-run analytics

For users who run the framework repeatedly. Less critical for fresh-faced users; load-bearing for power users and for the eventual P7 eval harness.

**Tasks:**

- Run Comparison view: side-by-side A/B of two runs. Same directive across two workflows, or two iterations of the same directive. Diffs artifact sets, cost breakdowns, and outcome shapes. (Mirrors what we do informally when writing analyses.)
- Cost Dashboard: cumulative spend across all runs, per-project totals, per-workflow averages, trend lines. Useful for budget planning and for surfacing cost regressions.
- Telemetry Explorer: per-agent call breakdowns, cost-per-decision, cost-per-shipped-line. The metrics that matter for the project's "small model + strong constitution" thesis.
- Failure-Mode Tracker: across runs, surface where MEETING_BUDGET caps fired, where parse retries clustered, where late-publishes happened. Helps identify systematic substrate issues (the kind of stuff that drove the iterations we did this branch).

**Deliverable:** a user can ask "is the framework getting more efficient over time?" and get a concrete answer.

---

## P8.7 — Web mode + non-technical-user UX

Textual's web rendering brings the TUI to a browser nearly for free. This sub-phase is the polish pass that makes that experience actually good for non-technical users.

**Tasks:**

- Enable Textual web mode: `textual serve wonderland.tui:app` or equivalent. Verify all P8.2-P8.6 views render correctly in browser.
- Browser-specific UX adjustments: keybindings that work in browser, click-friendly targets where keyboard-driven flows feel awkward, typography tuning for browser rendering.
- Bring-your-own-API-key flow: the web app prompts for the user's Anthropic API key on first use. Stored client-side (localStorage) — never sent to a server we run. The framework's runs use the user's key for all API calls.
- "Demo mode" with replay: for users who want to *see* what Wonderland does before committing their API key, ship pre-recorded run replays from the analyses snapshots. They can watch a real Geocities or pomodoro run unfold without spending any money.
- Hosting scaffolding: Dockerfile or simple deployment guide so anyone (the project, individuals, third parties) can host the web version. The runner stays local-first; the web app is an optional layer.
- Privacy / data handling docs: clear statements about what stays local (API key, runs, artifacts) and what doesn't (nothing, by default).

**Deliverable:** a non-technical user can visit a Wonderland-hosted (or self-hosted) URL, supply their API key, and use the framework with zero terminal exposure.

---

## P8.8 (later, if warranted) — Proper SPA frontend

Textual web mode is sufficient for most needs but has UX ceiling: it's still a TUI rendered in a browser. If specific views earn the upgrade (cost dashboard, run comparison, code diff viewer especially benefit from web-native UX), build them as a proper React/Svelte/whatever app on top of the same observer/query API.

**This is deliberately deferred** until usage data tells us which views earn the investment. Don't preemptively double-implement.

---

## Cross-cutting concerns

- **Local-first invariant:** the framework runs locally without ever needing a server. The TUI is a local Python app. The web app is *optional* and brings its own tradeoffs.
- **API stability:** the P8.1 observer/query API is the contract every frontend depends on. Breaking changes there cascade to every downstream surface. Versioning matters.
- **Replay-first development pace:** every TUI iteration cycle uses real run data from `analyses/data/<NNN>/` snapshots. We *never* burn a fresh API run to test UI behavior — the snapshots already cover the failure-mode space. New API runs are reserved for testing *framework-level* changes (substrate, agents, directives), not UI-level changes. This is the load-bearing development discipline for keeping P8 cost-cheap.
- **Snapshots as test fixtures:** each `analyses/data/<NNN>/` snapshot is a structured test case. Banner runs (025, 028, 029-v6), TIMEOUT cascades (029-v3), M5-doesn't-fire patterns (026, 027, 029-v5), skeleton-overwrite (029-v4). Every UI view should be validated against the relevant fixtures. New analyses-data snapshots from future runs become future test fixtures.
- **Performance:** live run views need to handle utterance bursts (Hatter sometimes ships 5 scenarios in one emit). Render budget per frame matters.
- **Accessibility:** Textual has accessibility primitives; use them. Web-mode users may include screen-reader users.
- **Telemetry of the TUI itself:** opt-in usage analytics so we know which views are actually used and which are dead weight.

---

## Estimated effort

Rough sketch — full effort dominated by P8.3 (live run watcher) and P8.5 (educational layer):

| Sub-phase | Estimated effort | Cumulative |
|---|---|---|
| P8.1 | 1 week | 1w |
| P8.2 | 2 weeks | 3w |
| P8.3 | 3-4 weeks | 6-7w |
| P8.4 | 2 weeks | 8-9w |
| P8.5 | 2 weeks | 10-11w |
| P8.6 | 1-2 weeks | 11-13w |
| P8.7 | 1 week | 12-14w |
| **Total** | **12-14 weeks** of focused effort |

Most of P8 is parallel-able with P7 evals work — the eval harness consumes the same observer/query API the TUI does, so P8.1 unblocks both.

---

## What this skeleton doesn't yet specify

- Exact component decomposition in Textual (will fall out of P8.2 prototyping)
- Color palette / branding (Wonderland-themed? Carroll's illustrations as inspiration?)
- Specific keybindings (will fall out of usage)
- Whether/how to integrate with existing IDE workflows (VS Code panel? defer to later)
- Internationalization (defer)

These are intentionally not specified — they're decisions that benefit from prototyping rather than upfront design.
