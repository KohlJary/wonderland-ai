# Wonderland

**An identity-native multi-agent development system.**

> Generic AI agents perform roles. Identity-native agents inhabit them.

> ### ▶ See it in action
>
> [**Building a Geocities — a tour of how Wonderland works**](./SHOWCASE.md).
> One vague directive. **$2.05.** 7 minutes 38 seconds. The team of
> ten characters produced 1841 lines of code (auth, per-user pages,
> Markdown rendering, GDPR-deletion path, session management) plus
> 1253 lines of tests written *before* the implementation existed —
> and the team's reviewer caught three real bugs in the result with
> file paths and line numbers. The artifact tree is a v1 scaffold,
> not a deployable; the framework's process is what shipped.
>
> If you're trying to figure out what this project actually *is*,
> start there.

Wonderland is a cast of agents — each named after an Alice-in-Wonderland
character — that collaborate on software development tasks. The Cheshire Cat
is the architect. The White Rabbit is the project manager. The Mad Hatter is
QA. Every character has a stable self-model (a "constitution"), persistent
per-agent memory, and a working relationship with the others.

The architectural claim is that **identity does real work**. An agent with a
constitution it inhabits across many threads behaves differently from an
agent reconstructed from a system prompt each turn. It accumulates judgment.
It develops calibrated views of its colleagues. It refuses to cross domain
boundaries because the boundary is part of who it is, not a policy applied
from outside. Whether that compounds into measurably better outcomes than a
generic-agents baseline is what the eval harness in P7 will measure; until
then, the [`analyses/`](./analyses) directory tracks the qualitative
observations as the system gets built out.

Five corollaries follow from this, each anchored in field analyses:

1. **Identity-based architecture lets smaller models outperform their
   expected capabilities.** The constitution carries the discipline a
   generic agent would have to invent turn-by-turn, so a small model
   acting in character can hold its own against a large model with a
   generic prompt. Default target is Claude Haiku 4.5; the falsifier
   is P7's generic-baseline-vs-identity-native eval.
   ([analysis 004](./analyses/004-first-race.md))
2. **Failure modes are part of identity.** Each constitution's §VIII
   names the specific shadow each virtue decays into — the
   Sephirah/Qlipha pairing, where the corruption is structural rather
   than additive. Agents course-correct from inside instead of waiting
   for an external guardrail.
   ([analysis 004](./analyses/004-first-race.md))
3. **Character-shaped agents degrade visibly rather than silently when
   parts of the system fail.** When the bus dropped feature-composition
   artifacts mid-run, the Tweedles noticed the contradiction and
   reached for the disk-resident artifacts via their tools — recovery
   was emergent, not designed.
   ([analysis 027](./analyses/027-pomodoro-degradation-and-event-leak.md))
4. **The team produces a small-team shape, including things the
   directive never asked for** — ADRs with named tradeoffs,
   persona-grounded specs, accessibility coverage that wasn't
   requested. Production shape as a derived property of constitutional
   grounding.
   ([analyses 034](./analyses/034-tdd-serial-phased-first-run.md),
   [035](./analyses/035-tdd-phased-teams-2hg-first-run.md))
5. **Friction is the substrate, not the inefficiency.** Every meeting
   in the workflow is engineered friction with a specific shape; §VIII
   puts that friction inside each constitution. Generic stacks have
   nothing analogous because they have roles, not characters; goals,
   not voices; consensus, not constitutions.

Full argument with the per-corollary mechanics in
[**THESIS.md**](./THESIS.md).

The framing the project is building around: *failures are how software
gets built.* The iterative cycle of ship-then-discover-then-fix depends
on recognizing what went wrong; agents whose failure modes are part of
their identity can participate in that cycle as colleagues, not as tools
that need supervising out of their bad habits.

## Status

In-progress, building in public. P1–P6 complete; P8 (operator
interface) shipping in sub-phases — three of five done as of
0.1.0, two remain. P7 (evals) is the final post-P8 phase.

- [x] **P1 — Foundation** ([overview](./WONDERLAND_SPEC.md#12-build-order))
      Schema, Caucus event bus, episodic memory, agent base class.
- [x] **P2 — First Voice** ([analysis 001](./analyses/001-first-voice.md))
      The Cheshire Cat comes online and produces ADRs in his own voice.
- [x] **P3 — First Tension** ([analysis 002](./analyses/002-first-tension.md))
      White Rabbit joins the bus. Semantic + relational memory layers.
      Compaction-as-agent-behavior — agents reflect between threads.
- [x] **P4 — First Race** ([analysis 003](./analyses/003-alice-alone.md) ·
      [analysis 004](./analyses/004-first-race.md))
      Alice agent. Dodo orchestrator with quiescence detection. Conflict
      resolution, composition, and human-in-the-loop escalation. Showcase 1:
      a `/health` endpoint directive runs end-to-end against live Haiku 4.5,
      reaching settlement because the team goes quiet — no human in the loop.
- [x] **P5 — Full Cast**
      The remaining six characters land: Mad Hatter (test scenarios),
      Caterpillar (code review), Queen of Hearts (security/compliance
      rulings), Dormouse (production observations), and the Tweedles
      (frontend + backend implementation, with a shared pair protocol).
      `wonderland init` CLI ships the `.wonderland/` skeleton. Synthetic-
      consensus guard observes the bus for the §11 anti-pattern — three
      or more distinct constitutional domains converging on the same
      position is suspect, and the guard surfaces it for review.
- [x] **P6 — Real Threads**
      The hard showcases plus the substrate maturation that made them
      work. **Showcase 2: translation chat MVP** ([analyses
      015](./analyses/015-tweedles-ship-real-code.md)–[018](./analyses/018-the-breakthrough.md))
      — 1580 lines shipped from a vague directive in $0.93. **Showcase 3:
      security recovery** ([analysis 019](./analyses/019-security-recovery.md))
      — reactive response to a synthesized credential-stuffing
      incident; the framework's first non-greenfield run. **Showcase 4:
      multi-session persistence** ([analyses
      020](./analyses/020-multi-session-persistence.md)–[023](./analyses/023-quiescence-and-split-phases.md))
      — memory compounding across sessions, plus the substrate fixes that
      closed the "Tweedles don't ship" bug class (turn-based quiescence
      replacing wall-clock, parse-retry recovering malformed LLM
      responses, working-tree-as-implementation-artifact). **Workflow-as-
      data extraction** ([analysis 024](./analyses/024-tdd-validated.md)):
      meeting chains live in `closet/workflows/` as YAML; the TDD variant
      becomes the recommended default for feature work, with canonical
      retained for fast iteration when directive drift is unlikely. **The
      pair protocol pays off** in
      [analysis 025](./analyses/025-tea-party-validated.md): Alice and the
      Mad Hatter are paired in M4 (the tea party — they're already paired
      in the source material) so Alice writes user-journey scenarios and
      Hatter writes failure-mode scenarios, each producing both the
      artifact and a runnable pytest file. The Geocities showcase ships
      1841 lines from a vague directive in 7m 38s for $2.05, with
      Caterpillar catching three production-blocking bugs in the diff —
      the framework's bug-discovery surface working as designed. See
      [`SHOWCASE.md`](./SHOWCASE.md) for the friend-facing tour and
      [`analyses/`](./analyses) for the full build log of the iteration
      that got the framework here.
- [x] **P8.1 — Observer API** & **P8.2 — TUI Inspector** *(0.0.1 release)*
      `HistoricalRunHandle` reads any snapshot directory; the
      Textual TUI ships as a read-only run inspector with
      lazygit-style multi-pane drill-down (snapshot library →
      run summary → meeting detail → utterance modal →
      artifact browser, plus Cast view + theme cycling).
- [x] **P8.3 — Streaming + Mock Turtle**
      `RunHandle.stream_events()` async-iterator interface +
      `MockTurtleHandle` that replays a snapshot at compressed
      clock time. The testbed P8.4's live-watch screen iterates
      against without API spend.
- [x] **P8.4 — Live-watch screen**
      The streaming surface goes visual: meetings ribbon fills
      in as `MeetingStarted` events arrive, transcript scrolls
      live, body preview tracks the utterance cursor, artifacts
      pane filters per-meeting. All three panes focusable, Tab
      cycles, lazygit principle throughout. Iterated entirely
      against Mock Turtle replay.
- [x] **P8.5 — Directive issuing + LiveRunHandle** *(this release)*
      `NewRunScreen` is the directive composer (preset picker
      with bundled `pomodoro` / `hello-endpoint` /
      `translation-chat` / `geocities` / `ping` directives, plus
      per-project saves to `.wonderland/directives/`); selection
      drives composer + workflow pre-fill; Enter steps through
      the form like a paper form. `LaunchConfirmationScreen`
      guards the irreversible spend with directive preview +
      soft-cap budget. `LiveRunHandle` wraps a real Runner+Caucus
      and emits through the same streaming protocol Mock Turtle
      uses, so the live-watch screen consumes a real run
      interchangeably with a replay. Settings screen accepts
      API key + model from inside the TUI — fresh `pip install`
      users no longer drop to the shell to write a config file.
      First end-to-end TUI run shipped a story for $0.0119
      against the smoke workflow.
- [ ] **P8.6 — New-project spinup**
      Skeleton picker + stack-detection routine for adopting
      existing non-Wonderland projects. Closes the on-ramp from
      "I have a project idea" to "team's ready to start" without
      leaving the TUI.
- [ ] **P8.7 — First-use polish**
      Welcome screen, error states, abort flow, quiescence
      indicator, README + SHOWCASE refresh.
- [ ] **P7 — Evals**
      Generic-baseline vs Wonderland comparison. The compounding
      curve. Reordered after P8 so the eval harness has a usable
      operator surface.

[`WONDERLAND_SPEC.md`](./WONDERLAND_SPEC.md) is the design document.
[`constitutions/`](./constitutions) holds each character's identity in plain
text — these are the actual identity artifacts the runtime loads.

## Try it

Two demo scripts run live against the Anthropic API. You'll need an API
key (see *Configuration* below).

```bash
# A single Cheshire Cat reflecting on a directive
uv run python scripts/cat_demo.py

# Cat + Rabbit on the same bus, with optional compaction afterward
uv run python scripts/two_agent_demo.py --compact
```

Both scripts publish a translation-chat directive by default; pass
`--directive "..."` to use your own.

## The TUI

`wonderland-tui` is the operator interface. Register a project,
queue features for the team, watch them work in real time, verify
or reject what they ship. The same screen that renders live runs
also replays past ones at compressed clock time, so iterating on
the UX never costs API tokens.

```bash
pip install wonderland-ai
wonderland-tui                       # opens the project library
```

First-run flow: the library opens empty. Open `Settings`, paste an
Anthropic API key (saved to your platform's user-config dir), back
out. Press `n` to create a project — pick a path, pick a skeleton
(`python-tui`, `python-cli`, `python-fastapi`, `react-vite`,
`fullstack-fastapi-react`), and the substrate writes a
`.wonderland/project.yaml` carrying the stack as authoritative
project context the team consults at every meeting. The project's
dashboard opens automatically.

The screens, in the order an operator typically meets them:

- **Project library** — your projects with metadata. `n` for new,
  Enter to open the dashboard, `s` for settings.
- **New project** — name, path, skeleton picker, workflow default.
  Skeleton apply lays down a working scaffold AND writes
  `project.yaml` so M4 architecture and M5 contracts ground in
  the runtime fact, not just the directive's prose. Existing
  non-bare projects get a retrofit path that writes `project.yaml`
  without clobbering existing files.
- **Per-project dashboard** — the operator's primary attention
  surface in P12. Features tree on the left (each feature
  expandable to show its constituent tickets); state filter chips
  (designed / queued / ready_review / in_progress / verified /
  rejected); detail pane on the right renders the highlighted
  feature or ticket markdown. State-aware action buttons —
  `Design`, `Implement`, `Verify`, `Custom run` — surface counts
  for what's actionable; the highest-priority action gets the
  primary variant. Drill-down tabs for run history, raw artifacts,
  the project's working tree, and metrics charts.
- **Lifecycle moves from the dashboard** — `q` queues a designed
  feature for implementation; `Verify` opens a modal that captures
  the operator's verdict with optional notes (verified / rejected
  → recorded in `.wonderland/feature-states.jsonl` for next-run
  context); `m`/`D` mark and bulk-delete duplicate tickets when
  Rabbit's M3 ships revision-pass redundancy.
- **New run composer** — preset picker (left) + directive editor
  (right) + workflow / budget / project-root config + inline
  save-as-preset form. Bundled directives: `pomodoro`,
  `hello-endpoint`, `translation-chat`, `geocities`, `ping`.
  Per-project presets live at `<project>/.wonderland/directives/`.
  Empty directives push a confirmation modal so a launch doesn't
  silently ship without intent.
- **Live-watch screen** — three focusable panes (lazygit-style):
  meetings ribbon (with per_item iteration discriminators for
  parallel and pipeline workflows), transcript table + body
  preview pane, artifacts table. Selection filters across panes;
  status bar shows current speaker, live cost ticker, watching
  elapsed time + source-time elapsed. Same screen consumes live
  runs (`LiveRunHandle`) and replays of captured runs
  (`MockTurtleHandle`) interchangeably.
- **Operator-question modal** — when an agent emits a
  `question_to_operator` (architectural ambiguity contracts can't
  disambiguate, business priority calls, schema-vs-directive
  conflicts), the framework pauses the meeting and surfaces the
  question as a modal. Your reply lands on the bus as an
  `observation` from the operator identity; the meeting resumes
  with the team seeing the answer in their context.
- **Cast view** — single-page lazygit shape: character list at
  top, bio + constitution side-by-side below. Bios cover both
  the literary character and how it shapes each agent's
  constitution. Useful for understanding why an agent made a
  particular call when reviewing a captured run.
- **Settings** — Anthropic API key (password-masked, persists to
  the user-config dir) + optional model override. Reachable from
  the library, also auto-pushed when New run finds no API key
  set so fresh `pip install` users have a one-click recovery
  path.
- **Theme cycling** — `t` rotates through four Wonderland-flavored
  palettes (Tea Party / Looking Glass / Trial / Caucus); built-in
  Textual themes (gruvbox, dracula, nord, …) remain available.
- **Vim navigation** throughout — `j`/`k` to move, `g`/`G` and
  `H`/`L` for top/bottom, `Enter` to drill in / advance, `Tab` to
  cycle focus across panes, `Escape` to back out. Per-screen
  bindings show in the footer.

The replay-first design carries forward: drives the smoke tests,
keeps UX iteration free of API spend, and means anyone curious
about how the framework actually behaves can `wonderland-tui` →
open a project → drill into Runs → press `w` on a snapshot to
watch a captured run play back at 5× speed. Project context, the
features-as-tree dashboard, the verify/reject modal, and the
operator-question pipeline are the P11/P12 additions that pulled
the framework from "watch a run happen" to "drive a project's
feature lifecycle through several runs."

## Project layout

```
wonderland-ai/
├── WONDERLAND_SPEC.md      # The design document
├── THESIS.md               # Long-form thesis (architectural claim + corollaries)
├── constitutions/          # Each character's identity, version-controlled
├── src/wonderland/         # The runtime
│   ├── closet/             # Data the team reaches for at runtime
│   │   ├── skeletons/      # Project skeletons the team builds on top of
│   │   └── workflows/      # Meeting-chain templates (canonical, tdd, smoke)
│   └── ...                 # agent.py, runner.py, caucus.py, workflow.py, ...
├── scripts/                # Demo scripts; workflow_demo.py runs any bundled workflow
├── analyses/               # Field notes on the thesis as it gets stress-tested
├── tests/
└── .daedalus/              # Daedalus' working memory for this project
```

A target project that runs Wonderland gets a `.wonderland/` directory of
its own — per-agent episodic/semantic/relational memory, ADRs, tickets,
transcripts, contract notes, test scenarios, implementations, reviews.
The runtime here is project-agnostic; per-project state lives with the
project.

```bash
wonderland init [path]   # create the .wonderland/ skeleton; idempotent
```

`init` creates `architecture/`, `tickets/`, `stories/`, `escalations/`,
and `memory/` plus a README documenting the layout. Re-running is safe —
existing artifacts and a user-edited README are left alone.

## Install

Distribution name on PyPI is `wonderland-ai`; the import path stays
`import wonderland`. Core install includes the TUI (the primary
user-facing surface) and the in-process bus:

```bash
pip install wonderland-ai           # core + TUI
pip install 'wonderland-ai[redis]'  # adds RedisCaucus
```

`RedisCaucus` requires the `redis` extra; constructing one without it
raises `ImportError` with an install hint.

## Configuration

Wonderland reads user-level config (API keys, model overrides) from a
JSON file at the platform-appropriate location:

| OS      | Path                                                          |
|---------|---------------------------------------------------------------|
| Linux   | `~/.config/wonderland/config.json` (honors `XDG_CONFIG_HOME`) |
| macOS   | `~/Library/Application Support/wonderland/config.json`        |
| Windows | `%APPDATA%\wonderland\config.json`                            |

```json
{
  "anthropic": {
    "api_key": "sk-ant-...",
    "model": "claude-haiku-4-5-20251001"
  }
}
```

API-key resolution order: explicit constructor arg → `ANTHROPIC_API_KEY`
env var → config file. The env var wins if set.

## Development

```bash
uv sync --extra dev   # includes redis for full test coverage
uv run pytest
uv run ruff check
uv run ruff format
```

Live LLM tests are gated behind `WONDERLAND_LLM_SMOKE=1` and skipped
otherwise; running them costs Anthropic API tokens. Redis-backed tests
are gated behind `WONDERLAND_REDIS_URL`. To exercise both:

```bash
docker run -d --name wonderland-redis -p 6379:6379 redis:7-alpine
WONDERLAND_REDIS_URL=redis://localhost:6379 \
WONDERLAND_LLM_SMOKE=1 \
  uv run pytest
```

## Sponsoring

Wonderland runs on a personal Anthropic budget — one person, one API
key. The architecture is designed to be cheap (small models, heavy
caching) but multi-agent runs at scale still add up. If any of my
work has been useful to you — to read, build on, or argue with —
[GitHub Sponsors](https://github.com/sponsors/KohlJary) keeps the
Cheshire Cat in tea and the Hatter in scenarios.

## License

[MIT](./LICENSE).
