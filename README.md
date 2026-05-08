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

A fourth corollary, which is really the architectural commitment the
other three sit on top of: **friction is the substrate, not the
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

In-progress, building in public. Phase 5 of 7 complete.

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
- [>] **P6 — Real Threads** *(in progress)*
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
- [ ] **P7 — Evals**
      Generic-baseline vs Wonderland comparison. The compounding curve.

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

A terminal interface ships with the project as the long-term home for
operating Wonderland — issuing directives, watching live runs, and
inspecting past ones. The first cut focuses on the inspection half,
since it's the cheapest place to iterate (snapshots run for free); the
directive-issuing and live-watching halves arrive in later sub-phases.

```bash
pip install 'wonderland-ai[tui]'
wonderland-tui                       # opens the snapshot library
```

What's in it today:

- **Snapshot library** — every captured run under `analyses/data/`,
  with workflow, outcome, duration, call count, and cost.
- **Run summary** — per-meeting cost, agent telemetry, and a
  meetings table you can drill into.
- **Meeting detail** — full transcript with body preview as you
  navigate; press Enter on an utterance for the expanded view, with
  attached artifacts you can drill into.
- **Speaker filter** — `f`/`F` cycle the meeting transcript by
  speaker.
- **Artifact browser** — every artifact the team produced for a run,
  globally or scoped to a single meeting (`a` from a meeting).
- **Cast view** — `c` from the library opens the team roster, with
  each character's role summary and constitution side-by-side.
- **Theme cycling** — `t` rotates through Wonderland-flavored
  palettes (Tea Party, Looking Glass, Trial, Caucus); built-in
  Textual themes (gruvbox, dracula, nord, …) remain available.
- **Vim navigation** throughout — `j`/`k` to move, `g`/`G` for
  top/bottom, `Enter` to drill in, `Escape` to back out.

The current build is replay-first by design: it consumes the same
snapshots the analyses are written from, so smoke tests double as
exercise of the historical-run observer API. Issuing directives from
the TUI and watching live runs are the next two sub-phases — the
goal is for `wonderland-tui` to be the way most users interact with
the framework, with the demo scripts above remaining as minimal
"hello world" entry points.

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
`import wonderland`. Core install pulls only what the in-process bus
needs:

```bash
pip install wonderland-ai           # InMemoryCaucus only
pip install 'wonderland-ai[redis]'  # adds RedisCaucus
pip install 'wonderland-ai[tui]'    # adds the TUI (Textual)
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
