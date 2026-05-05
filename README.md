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

## Status

In-progress, building in public. Phase 4 of 7 complete.

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
- [ ] **P5 — Full Cast** *(next)*
      Hatter, Caterpillar, Queen of Hearts, Dormouse, Tweedles. Per-character
      artifact handlers. Synthetic-consensus guard. Init CLI lands first
      (carried over from P4) so the cast agents arrive into a stable
      `.wonderland/` skeleton.
- [ ] **P6 — Real Threads**
      Showcases 2–4: translation chat MVP, security recovery, multi-session.
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

## License

[MIT](./LICENSE).
