# Wonderland

**An identity-native multi-agent development system.**

> Generic AI agents perform roles. Identity-native agents inhabit them.

See [`WONDERLAND_SPEC.md`](./WONDERLAND_SPEC.md) for the full design.

## Status

Pre-alpha. Phase 1 (Foundation) — substrate under construction.

Track in-flight work: `daedalus gameplan show`.
Decisions: [`.daedalus/decisions.md`](./.daedalus/decisions.md).

## Install

Core install pulls only what the in-process bus needs:

```bash
pip install wonderland          # InMemoryCaucus only
pip install 'wonderland[redis]' # adds RedisCaucus
```

`RedisCaucus` requires the `redis` extra; constructing one without it raises
an `ImportError` with an install hint.

## Development

```bash
uv sync --extra dev   # includes redis for full test coverage
uv run pytest
uv run ruff check
uv run ruff format
```

The Redis-backed tests are gated behind `WONDERLAND_REDIS_URL` and skipped
otherwise. To exercise them locally:

```bash
docker run -d --name wonderland-redis -p 6379:6379 redis:7-alpine
WONDERLAND_REDIS_URL=redis://localhost:6379 uv run pytest
```

## Layout

```
wonderland-ai/
├── constitutions/        # Each agent's identity, version-controlled
├── src/wonderland/       # The runtime
├── tests/
└── .daedalus/            # Daedalus' own working memory for this project
```

A target project that uses Wonderland gets a `.wonderland/` directory of its
own — episodic/semantic/relational memory per agent, ADRs, transcripts. The
runtime here is project-agnostic; the per-project state lives with the project.

## License

Hippocratic 3.0.
