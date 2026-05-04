# Decisions

## D-001 — Wonderland is a project plugin, not a project

**Date:** 2026-05-04
**Status:** Accepted

Wonderland (the runtime + cast in this repo) initializes into a target project's `.wonderland/` directory, the same way Daedalus initializes into `.daedalus/`. The wonderland-ai repo ships the runtime, the constitutions, and the orchestration; per-project memory and ADRs accumulate inside the host project's `.wonderland/`.

**Implications:**
- Constitutions (`constitutions/*.md`) ship with the runtime — version-controlled with the system, not the host project.
- Per-project state lives under `<project_root>/.wonderland/` — episodic/semantic/relational memory, transcripts, ADRs.
- The runtime takes a `project_root` argument and resolves all per-project paths relative to it.

## D-002 — Python

**Date:** 2026-05-04
**Status:** Accepted

The runtime is Python. The spec uses Python in its examples and there is no compelling reason to introduce language friction at the substrate layer. BEAM/Phoenix appears in the spec only as a *target* the system might build for, not as a runtime dependency.

## D-003 — Redis Streams as the Caucus

**Date:** 2026-05-04
**Status:** Accepted

The event bus is Redis Streams. Per WONDERLAND_SPEC §3 / §12: "Redis Streams is fine to start; NATS later if needed." Append-only, ordered, durable, supports consumer groups for multi-agent subscription. Operationally familiar.

**Revisit if:** ordering across thread shards becomes a bottleneck, or we want the bus to live across machines without managing Redis HA.

## D-004 — SQLite per-agent under .wonderland/

**Date:** 2026-05-04
**Status:** Accepted

Each agent's SAM-equivalent memory lives in its own SQLite database under `<project_root>/.wonderland/memory/<agent_name>/`. Episodic, semantic, and relational layers are tables (or sibling DBs) within that scope.

**Why per-agent:** the agent owns its memory; isolating storage matches the identity-native stance. No cross-agent reads through the storage layer — observations of other agents flow through the bus.

**Revisit if:** cross-agent memory queries become common (they shouldn't — that's what the bus is for).

## D-005 — Anthropic SDK with prompt caching, default Haiku 4.5

**Date:** 2026-05-04
**Status:** Accepted (with follow-up)

LLM calls go through the Anthropic SDK. Default model: `claude-haiku-4-5-20251001` to keep development costs low. The wrapper still emits `cache_control: ephemeral` markers on invariant prefixes (constitution + per-agent protocol) so caching can engage when the prefix is large enough.

**Update 2026-05-04 — cache thresholds, measured:**

Empirical bisection (see commit `<this commit>`) showed Haiku 4.5 has two distinct prompt-cache thresholds higher than the published Sonnet thresholds:

| Threshold | Behavior |
|---|---|
| < ~4096 tok | No caching at all. Markers ignored; full input billed. |
| ~4096–7000 tok | **Pessimal.** Cache *writes* (1.25× input cost) but never *reads*. We pay the write tax with no benefit. |
| > ~7000 tok | Caching engages fully — write once, read on subsequent calls at 0.10×. |

Sonnet 4.6 by contrast caches at ~2000 tokens — well below our current cached-prefix size of ~3100 tokens (Cat constitution + output protocol).

**Decision for now:** stay on Haiku 4.5 even though caching doesn't fire at current prefix sizes. The per-token cost gap (Haiku ~$1/M input vs Sonnet ~$3/M) means uncached Haiku may still beat cached Sonnet depending on real per-directive token consumption — and we don't yet have data on that. By P3+ the cached prefix will grow naturally (relationships layer, possibly a shared "framework primer" block), and may cross the Haiku cache threshold organically.

**Revisit:** new roadmap item — cost analysis once the full agent workflow is implemented and we have real per-directive token telemetry. Compare Haiku-no-cache and Sonnet-with-cache on the same showcase directives.

## D-006 — ADRs live in .wonderland/architecture/

**Date:** 2026-05-04
**Status:** Accepted

The Cheshire Cat's ADRs are written to `<project_root>/.wonderland/architecture/adr-NNN-*.md`. Per D-001, these are per-project artifacts. The Cat writes them in-character; the format is fixed by his constitution (Context / Decision / Tradeoffs / Status — Tradeoffs is the grin, non-optional).
