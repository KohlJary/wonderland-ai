# Wonderland

**An identity-native multi-agent development system.**

> Generic AI agents perform roles. Identity-native agents inhabit them.

See [`WONDERLAND_SPEC.md`](./WONDERLAND_SPEC.md) for the full design.

## Status

Pre-alpha. Phase 1 (Foundation) — substrate under construction.

Track in-flight work: `daedalus gameplan show`.
Decisions: [`.daedalus/decisions.md`](./.daedalus/decisions.md).

## Development

```bash
uv sync --extra dev
uv run pytest
uv run ruff check
uv run ruff format
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
