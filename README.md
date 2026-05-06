# Wonderland

**An identity-native multi-agent development system.**

> Generic AI agents perform roles. Identity-native agents inhabit them.

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
      Substrate fixes for the polite-deadlock pattern surfaced in P5
      ([analysis 006](./analyses/006-first-full-cast.md),
      [analysis 007](./analyses/007-tweedle-dance.md)) before the showcases run:
      framework primer for cache-padding ([T32](./analyses/009-primer-chattiness.md)),
      Dodo nudge ladder on STUCK transitions (T33), Contract Note artifact for
      the Tweedles' negotiation surface ([T35](./analyses/010-contract-note-acceptance.md)),
      Runner + budget caps + interactive escalation CLI (T34), and
      [roster architecture](./analyses/012-roster-scoping-rerun.md) for
      scoped meetings (T36 prep, Block 1+2a). Calibration to operationalize
      "ship the artifact" landed in
      [analysis 013](./analyses/013-cat-calibrated-ships.md) and the framework
      now produces architectural artifacts cleanly under bounded cost — first
      shipped ADR-001 in 100s for $0.13. Cross-meeting composition validated
      in [analysis 014](./analyses/014-cross-meeting-composition.md): a single
      ADR drives 5 agreed Tweedle Contract Notes in a follow-up meeting for
      $0.10. Tool integration ships real code in
      [analysis 015](./analyses/015-tweedles-ship-real-code.md). The full
      5-meeting translation-chat enchilada
      ([analysis 016](./analyses/016-cat-story-deafness.md)) surfaced Cat's
      STORY engagement filter as a critical-path bottleneck — once
      broadened (every Alice story + cumulative-synthesis protocol), every
      artifact type lands in one $1.04 run. Substrate fixes (`is_seed`
      flag, working-tree-as-artifact via git_status/git_diff) compose into
      [analysis 017](./analyses/017-first-arc-completion.md) — the first
      end-to-end arc completion: vague directive → 6 stories → 1 ADR → 6
      tickets → 4 agreed contracts → real frontend types on disk citing
      the contracts by name, in $0.49. Three more substrate improvements
      (shared parser with brace-balanced JSON fallback, decision-coercion
      validator, Caterpillar engaging on directives) compose in
      [analysis 018](./analyses/018-the-breakthrough.md) into a working
      module: **9 files, 1580 lines** (SQLAlchemy models with invariants,
      a SQL migration with check constraints, React component, hook,
      types, pytest test file with fixtures), all citing the contracts
      that produced them by name, $0.93 / 100 calls.
      [Analysis 019](./analyses/019-security-recovery.md) is the second
      showcase — a synthesized credential-stuffing incident landing as a
      Dormouse observation against a *pre-seeded* FastAPI auth service.
      The team responds with **+296 lines of new rate-limiting code,
      modifications to 4 existing files (+722 / -42), 4 Caterpillar
      reviews citing RFC 6585, 18 Hatter test_scenarios pointing at
      specific class names in the proposed implementation**, in $3.04 /
      200 calls / 211s. First showcase to test reactive (vs greenfield)
      behavior; first time Caterpillar's working-tree review path produces
      substantive code-review findings (line ranges, code quotes, RFC
      citations). [Analysis 020](./analyses/020-multi-session-persistence.md)
      is the third — multi-session continuation. Two sessions ran on the
      same `.wonderland/`: Session 1 built the translation chat (870-line
      backend diff), Session 2 added user-blocking. Memory compounds at
      the registry level: contract-notes count 1–8 → 9–11 across sessions,
      Rabbit's tickets cite Session 1's endpoints by name, Cat correctly
      declined a redundant ADR. Tweedles' tool-loop hit `max_tool_iterations=10`
      mid-exploration in Session 2 and didn't ship code; cap bumped to 20.
      [Analysis 021](./analyses/021-multi-session-validation.md) is the
      validation rerun with the iter-bump and an inter-session git-commit
      step in place — Session 1 ran at -49% elapsed / -48% cost vs the
      020 baseline ($0.80 / 92 calls / 8.7 min), Session 2 actually
      shipped code this time (+214 lines / 4 files / new `blocks.py`).
      Headline finding: **memory compounds for design artifacts but
      regressed for execution artifacts** — stories went 5→10, tickets
      5→9, contract-notes 6→8, ADRs 1→2 across sessions, but
      `implementations/` and `reviews/` registries didn't even get
      created (zero successful artifact persists). Mechanism: M3/M4
      meeting boundary suppresses late-arriving implementation
      utterances; Caterpillar exhausts shared iter cap on read tools
      before the review utterance can synthesize. Four roadmap items
      filed; the two P1s (M3+M4 consolidation, turn-based quiescence)
      address the bug class architecturally before the next showcase.
      [Analysis 022](./analyses/022-consolidation-alone.md) isolates
      consolidation as a variable: Session 1 against the consolidated
      4-meeting workflow but the still-wall-clock substrate. Result:
      late-publish events down 6→2, but consolidation alone is
      insufficient — the wall-clock model still kills meetings
      mid-deliberation. Surprise finding: M4 self-healed by pivoting
      from review into recovery-implementation, shipping 1 of 7 tickets
      and producing a real review artifact. Sharpens the 021 diagnosis:
      the M3/M4 boundary was a symptom; wall-clock quiescence is the
      cause. Turn-based quiescence is the load-bearing fix, next P1.
      [Analysis 023](./analyses/023-quiescence-and-split-phases.md)
      closes the loop. Two runs: (A) consolidation + turn-based
      quiescence — the substrate works (44% wall-clock speedup, no
      false-positive closures) but the merged workflow short-circuits;
      (B) re-split phases + turn-based quiescence — code ships
      reliably (1539 lines across 8 files, real translation chat MVP
      end-to-end). The substrate fix enables the workflow shape that
      was previously unsafe. The "Tweedles don't ship" bug class is
      closed. Worth naming explicitly: working-tree-as-implementation-
      artifact — the bus utterance is ancillary to the actual
      deliverable, which is the diff.
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

## Project layout

```
wonderland-ai/
├── WONDERLAND_SPEC.md     # The design document
├── constitutions/         # Each character's identity, version-controlled
├── src/wonderland/        # The runtime
├── scripts/               # Demo scripts
├── analyses/              # Field notes on the thesis as it gets stress-tested
├── tests/
└── .daedalus/             # Daedalus' working memory for this project
```

A target project that runs Wonderland gets a `.wonderland/` directory of
its own — per-agent episodic/semantic/relational memory, ADRs, tickets,
transcripts. The runtime here is project-agnostic; per-project state
lives with the project.

```bash
wonderland init [path]   # create the .wonderland/ skeleton; idempotent
```

`init` creates `architecture/`, `tickets/`, `stories/`, `escalations/`,
and `memory/` plus a README documenting the layout. Re-running is safe —
existing artifacts and a user-edited README are left alone.

## Install

Core install pulls only what the in-process bus needs:

```bash
pip install wonderland          # InMemoryCaucus only
pip install 'wonderland[redis]' # adds RedisCaucus
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
