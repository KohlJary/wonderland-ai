# `closet/skeletons/` — project-scaffolding skeletons

Project skeletons the Wonderland team can build features on top of,
rather than inventing the entire stack from a vague directive.

> Renamed from `templates/` and moved under `closet/` (which also
> houses `workflows/` — the meeting-chain templates the team works
> through). "Skeleton" reads more honestly: these aren't generic
> scaffolds, they're working hello-world apps the team extends.

The premise (per analysis 019 follow-up): real engineers don't
argue about which test framework to use on day 1 — they pick a
stack, run a scaffold command, and start adding features. The
Wonderland team should make the choices that *matter*
(architecture, contracts, behavior, what to ship) and inherit the
ones that don't (project structure, build config, test runner).

## How templates get used

For now (pre-feature-landing): showcase scripts copy a template
into `project_root` via `shutil.copytree`, then `git init` and
commit as the initial state. Mirrors the pattern in
`analyses/data/019-security-recovery/test_t37_security_recovery.py`.

The eventual first-class surface (roadmap `f0e4afea`):

```bash
wonderland scaffold <project_root> --template <name>
```

```python
from wonderland.scaffold import lay_down_template
lay_down_template(project_root, "fullstack-fastapi-react")
```

```python
runner = await Runner.make_full_cast(
    project_root,
    template="fullstack-fastapi-react",
    ...
)
```

## What a template should contain

- A working "hello world" wired through every layer the template
  spans (backend has a /health endpoint that returns 200; frontend
  fetches from it and renders something).
- A README at the template root explaining what's there, what the
  team is expected to build on top of it, and what was *intentionally
  left undone*.
- pyproject.toml / package.json / Dockerfile / etc. with reasonable
  defaults — the team shouldn't have to argue about pytest vs
  unittest.
- A `.gitignore` covering the language's build artifacts.
- A baseline test file demonstrating the test framework works.

The team's job becomes "extend this skeleton" — read existing
files via `read_file`, add features via `write_file`, the
Caterpillar reviews diffs against the initial commit.

## What a template should NOT contain

- Domain-specific code. The translation chat MVP isn't part of
  `fullstack-fastapi-react`; it's what the team builds on top.
- Architectural decisions the team should be making. The template
  picks a HTTP framework but doesn't pick a state-management
  library; the template picks a DB but doesn't pick a schema.
- Excessive configuration. Every option is a choice the team
  could have made; if the template makes too many, it's
  pre-deciding the architecture rather than the boilerplate.

## Current templates

| Template | Status | Used by |
|---|---|---|
| `fullstack-fastapi-react/` | initial | T38 (planned) |

Future templates (filed as needed, not speculatively):
- `python-fastapi-sqlite/` — backend-only
- `react-vite-typescript/` — frontend-only
- `python-cli/` — click + pytest
