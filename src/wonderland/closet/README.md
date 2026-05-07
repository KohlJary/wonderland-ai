# `closet/` — where the team gets dressed

Two siblings live here, both data-on-disk that the framework reads
at runtime to spin up team activity:

| Directory | What's in it | Used by |
|---|---|---|
| `skeletons/` | Project scaffolds (working hello-world apps) the team builds features on top of | `wonderland.scaffold` (planned) — copies a skeleton into a project_root and `git init`s it |
| `workflows/` | Meeting-chain definitions — ordered sequences of meetings with rosters, directives, and seed-binding rules | `wonderland.workflow` (in progress) — loads a workflow by name and executes it via the Runner |

## Why "closet"

Wonderland already has a labyrinth, a caucus, a tea party. The closet
is where you go to grab the right coat for the job — pick a skeleton
to dress your project in, pick a workflow to dress your team's
process in. The contents are inert until something pulls them out.

## What goes in a workflow

A workflow file (`workflows/<name>.yaml`) declares an ordered
sequence of meetings. Each meeting names its roster, its goal, the
directive the convener delivers, the per-meeting budget cap, and
how to seed the meeting from prior meetings' artifacts.

The canonical 5-meeting sequence (scoping → decomposition →
contract negotiation → implementation → review) lives at
`workflows/canonical.yaml` — validated end-to-end across analyses
015-023. Future variants (TDD-style with separated test-write +
test-pass meetings, spike workflows, hotfix workflows) live as
sibling files.

## What's NOT here

- **Agent constitutions** live at `constitutions/` (top-level) —
  who each agent IS doesn't change between workflows.
- **Tools** live at `src/wonderland/tools.py` — what an agent CAN
  do doesn't change between workflows.
- **The Runner / ThreadMonitor** live at `src/wonderland/runner.py`
  — how meetings actually run doesn't change between workflows.

The closet is for the *what gets done*, not the *who/how*.

## Eventually: Dodo's job

Per roadmap `29497820` (Dodo as dynamic meeting orchestrator), the
Dodo will eventually compose workflows on the fly — given a
directive, pick a workflow template, mutate it (different rosters,
extra meetings, different seed-binding) for the situation, and run
it. Workflows-as-data is the substrate that makes Dodo's
composition tractable: the alternative (workflows-as-code) would
require Dodo to generate and `exec` Python.
