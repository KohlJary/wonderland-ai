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

A corollary the project takes seriously: **identity-based architecture
lets smaller models outperform their expected capabilities**. Most of the
judgment a generic agent has to derive turn-by-turn — what to engage with,
what to refuse, when to stay silent, who owns this domain — is carried by
the constitution itself. The model isn't being asked to *invent* the
discipline on each prompt; it's being asked to *act in character*, which
is a much easier task. The default target is Claude Haiku 4.5
(`claude-haiku-4-5-20251001`), and that choice is a thesis statement, not
a cost-savings move: if identity is doing the load-bearing work, a small
model with a strong constitution should hold its own against a large model
with a generic prompt. The early analyses are consistent with this — see
[analysis 004](./analyses/004-first-race.md) for a Haiku-driven team
running an autonomous /health directive to settlement, with three of four
agents correctly choosing silence — but the falsifier is P7's
generic-baseline-vs-identity-native eval.

A second corollary, brought into focus by §VIII of every constitution:
**failure modes are part of identity in this system**. Each character's
constitution explicitly names the failure mode that character is most at
risk of slipping into — Alice's *"product owner who keeps adding stories
during implementation,"* the Cat's *"false certainty,"* the Hatter's
*"scenario sprawl"* and *"severity inflation,"* the Dodo's *"performing
orchestration."* These aren't policies imposed from outside; they're
load-bearing parts of who the character is. An agent that recognizes its
own characteristic failure mode can course-correct from inside, rather
than waiting for a guardrail to intervene from outside. This is what
makes the project materially different from a generic multi-agent
architecture: the generic architecture defines what each agent should
*do*; Wonderland defines, with equal specificity, what each agent
should *not do*. [Analysis 004](./analyses/004-first-race.md) is the
cleanest evidence so far — three of four agents on a concrete operational
directive correctly chose silence because their constitutions named
padding, false certainty, and orchestration-performance as failure modes
to actively guard against, not because an external policy intervened.

A third corollary, observed when a phase of the workflow misfired:
**character-shaped agents degrade visibly rather than silently when
parts of the system fail**. Most LLM pipelines have two outcomes —
they succeed, or they produce silent garbage at the end of a path
where data was missing or contracts were violated. In
[analysis 027](./analyses/027-pomodoro-degradation-and-event-leak.md),
the new feature-composition phase wired correctly but didn't fire
under live conditions; the next meeting's directive then referenced
artifacts that didn't exist. The Tweedles read the directive
carefully, *noticed* the contradiction with their actual seed
manifest, flagged the mismatch as a `concern`, and reached for the
disk-resident artifacts via their `list_files`/`read_file` tools to
recover the data the bus channel was missing. They stayed within
their character roles — they didn't try to *be the Rabbit* and re-
emit the missing artifacts; they negotiated against what the Rabbit
had actually produced. None of this recovery was designed. It's
emergent from three converging properties: agents have intentions
tied to their constitutions (Tweedles want concrete artifacts to
negotiate against), the substrate offers multiple data channels (bus
*and* disk), and the framework gives characters tools to cross
between those channels. The literary parallel keeps earning its keep
— the recovery pattern works *because* the agents have characters
with intentions, not despite it.

A fourth corollary, surfacing across analyses 034 and 035 once the
phased orchestrator made the team's per-meeting work legible: **what the
team produces is shaped like what a small team would produce, including
things the directive never asked for.** A generic LLM given a sparse
directive ("Build a Pomodoro timer app: focus sessions, configurable
breaks, daily review, persistent settings") ships what was literally
asked — a working single-file MVP. Wonderland on the same directive
ships a different shape: an ADR with named tradeoffs and open questions,
persona-driven user stories with confusion-flags, test scenarios that
distinguish failure modes from happy paths, a review pass that catches
real bugs by file and line, and — notably — accessibility coverage that
the directive never requested. In
[analysis 034](./analyses/034-tdd-serial-phased-first-run.md) the team
produced an explicit deaf-user persona (Priya, *"29, deaf software
engineer"*) and visual + haptic alert scenarios; in
[analysis 035](./analyses/035-tdd-phased-teams-2hg-first-run.md), a
different run on the same directive surfaced voice-input accessibility
scenarios instead. Neither was asked for. The mechanism is
constitutional: Alice grounds in personas, and a persona-grounded view
of "who actually uses this software" includes users with disabilities by
default. The broader effect — accessibility, architecture,
persona-shaped specs, review-pass discipline — is **production-shape as
a derived property of constitutional grounding, rather than a feature
you have to remember to ask for.** Vibe-coded MVPs on a sparse directive
are throwaway by default; Wonderland's output is shaped like what a
junior team's couple-day TDD push would produce, with the artifact trail
that lets someone else maintain the result.

A fifth corollary, which is really the architectural commitment the
other four sit on top of: **friction is the substrate, not the
inefficiency.** Most multi-agent systems engineer friction *out* —
consensus-seeking loops, reflection passes that smooth dissent, voting
mechanisms that median competing positions toward agreement. The
result reads fluently and ships nothing real, because nothing in the
loop has the standing or the constitutional grounding to say *no,
that's wrong, and here's the persona-shaped reason why.* Wonderland
inverts that move: every meeting in the workflow is engineered
friction with a specific shape. M1 is multiple stakeholder voices
arguing about scope; M2 is Alice grounding the White Rabbit's
compression; M2.5 is the Caterpillar auditing Rabbit's features
against Alice's stories; M3 is the Tweedles negotiating contract
boundaries; M4 is the Mad Hatter's failure-mode scenarios pulling
against Alice's happy paths; M6 is the Trial — explicit adversarial
review. The implementation in M5 is what crystallizes out *because*
the prior meetings ground each other against each other. And §VIII
is the meta-move: each character carries internal friction between
their virtues and their named failure modes, so the agents aren't
only generating friction with each other — they carry it inside
their own constitutions. That's why a character can recognize when
it's about to go off the rails: the rails are constitutionally
specified. Generic "AI agents collaborate" stacks have nothing
analogous because they have roles, not characters; goals, not voices;
consensus, not constitutions.

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

`wonderland-tui` is the operator interface. Type a directive, pick
a workflow, hit Go, and watch the team work in real time. The same
screen that renders live runs also replays past ones at compressed
clock time, so iterating on the UX never costs API tokens.

```bash
pip install wonderland-ai
wonderland-tui                       # opens the home view
```

First-run flow: the home view has prominent New run / Cast /
Settings buttons. Open Settings, paste an Anthropic API key
(saved to your platform's user-config dir), back out, then
New run → pick the `ping` preset (cheapest, ~$0.20) → confirm →
watch.

What's in it:

- **Home view** — `New run`, `The Cast`, and `Settings` as primary
  buttons; the past-runs table below lists every captured snapshot
  with workflow / outcome / duration / cost.
- **New run composer** — preset picker (left) + directive editor
  (right) + description editor + workflow / budget / project-root
  config + inline save-as-preset form. Bundled directives:
  `pomodoro`, `hello-endpoint`, `translation-chat`, `geocities`,
  `ping`. Per-project presets live at
  `<project>/.wonderland/directives/`. Enter steps through the
  form like a paper form.
- **Live-watch screen** — three focusable panes (lazygit-style):
  meetings ribbon (left, with per_item iteration discriminators
  for serial workflows), transcript table + body preview pane
  (top-right), artifacts table (bottom-right). Selection in the
  meetings list filters the transcript and artifacts panes;
  cursor moves on the transcript drive the body preview. Status
  bar shows current speaker, live cost ticker, watching elapsed
  time + source-time elapsed. Same screen consumes live runs
  (via `LiveRunHandle`) and replays of past runs (via
  `MockTurtleHandle`) interchangeably.
- **Cast view** — single-page lazygit shape: character list at
  top, bio + constitution side-by-side below. Selection drives
  both panes. Bios cover both the literary character and how
  it shapes each agent's constitution.
- **Settings** — Anthropic API key (password-masked, persists to
  the user-config dir) + optional model override. Reachable from
  home, also auto-pushed when New run finds no API key set so
  fresh `pip install` users have a one-click recovery path.
- **Theme cycling** — `t` rotates through four Wonderland-flavored
  palettes (Tea Party / Looking Glass / Trial / Caucus); built-in
  Textual themes (gruvbox, dracula, nord, …) remain available.
- **Vim navigation** throughout — `j`/`k` to move, `g`/`G` and
  `H`/`L` for top/bottom, `Enter` to drill in / advance, `Tab` to
  cycle focus across panes, `Escape` to back out.

The replay-first design carries forward: drives the smoke tests,
keeps UX iteration free of API spend, and means anyone curious
about how the framework actually behaves can `wonderland-tui` →
press `w` on a snapshot to watch a captured run play back at 5×
speed.

## Project layout

```
wonderland-ai/
├── WONDERLAND_SPEC.md      # The design document
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
