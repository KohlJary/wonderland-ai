# `closet/workflows/` — bundled meeting-chain templates

Each YAML in here is a **workflow**: an ordered sequence of meetings
the team works through, with rosters, directives, per-meeting budget
caps, and seed-binding rules that thread artifacts from one meeting
to the next.

A workflow is loaded by name and run against a started Runner:

```python
from wonderland.runner import Runner
from wonderland.workflow import load_workflow, run_workflow

runner = await Runner.make_full_cast(project_root, ...)
await runner.setup()
try:
    workflow = load_workflow("canonical")
    async for event in run_workflow(workflow, runner, directive):
        ...  # render, accumulate, etc.
finally:
    await runner.teardown()
```

## Bundled workflows

| Name | Meetings | Default budget | When to use |
|---|---|---|---|
| `smoke` | 1 | $0.50 | Sanity-check the loader/runner integration. Alice produces one story, ~$0.10. |
| **`tdd` (default)** | 6 | $4.00 | **Recommended default for feature work.** Hatter writes failing test scenarios before Tweedles implement; M5's closure criterion is "make Hatter's red tests green." Validated end-to-end in [analysis 024](../../../../analyses/024-tdd-validated.md) — directive-aligned output (1804 lines of working rate-limiter end-to-end) where canonical drifted on the same directive. |
| `canonical` | 5 | $3.00 | Faster/cheaper alternative when directive drift is unlikely (throwaway prototypes, very concrete directives, or exploratory iteration). Validated across analyses 015-023. **Risk:** without Hatter's tests pinning behavior, the team can ship coherent code that doesn't match what was asked. |

Run any of them via the demo script:

```bash
uv run python scripts/workflow_demo.py --workflow smoke
uv run python scripts/workflow_demo.py --workflow canonical --directive "..."
uv run python scripts/workflow_demo.py --workflow tdd --directive "..."
uv run python scripts/workflow_demo.py --list
uv run python scripts/workflow_demo.py --workflow tdd --dry-run
```

## tdd vs canonical — compare and contrast

Both workflows take the same vague directive in M1 (scoping) and
hand off to Tweedles for implementation. The difference is what
happens in the middle.

```
canonical:
  M1 scoping  →  M2 decomposition  →  M3 contracts  →  M4 implementation  →  M5 review

tdd:
  M1 scoping  →  M2 decomposition  →  M3 contracts  →  M4 test-scenarios  →  M5 implementation  →  M6 review
                                                       ───────────────────
                                                       Hatter writes failing
                                                       tests against the
                                                       agreed contracts here
```

The added M4 in `tdd`:

- **Roster:** Mad Hatter + both Tweedles. Hatter's the owner; the
  Tweedles are there to ask clarifying questions about test intent
  before they implement against the tests in M5.
- **Hatter ships two things:** `test_scenario` artifacts (the
  intent description, his usual move) AND the actual test files via
  `write_file`. The test files MUST fail right now — that's the red
  in red→green→refactor.
- **Tweedles do not write production code in M4.** The directive
  forbids it. Implementation is M5.

The implementation phase changes too:

- **canonical M4:** "ship code against the agreed contracts" —
  closure criterion is the directive itself ("real translation chat
  models", etc.). Tweedles know they're done when the substantive
  features described in the directive exist.
- **tdd M5:** "make Hatter's failing tests pass" — closure criterion
  is observable (the tests would turn green). Tweedles get a
  concrete red→green target instead of a paragraph.

### Tradeoffs

| | tdd (default) | canonical |
|---|---|---|
| Cost | ~$2.13 (validated, analysis 024) | ~$1.50 (validated, analysis 023) |
| Wall clock | ~10 minutes | ~7-8 minutes |
| Directive alignment | bounded — Hatter's tests pin behavior to the spec | possible drift — team can ship coherent code that doesn't match the ask |
| Test coverage | test-first (Hatter writes failing scenarios in M4, becomes the M5 closure criterion) | review-after-the-fact (Caterpillar surfaces findings in M5 review) |
| When it shines | feature work where the directive is vague or regressions matter | exploratory work, throwaway prototypes, very concrete directives |

### When tdd wins (the default case)

For most feature work, tdd is the right tool. The Hatter's failing
tests are the team's commitment to the *directive*, not just to the
contract. When the user says "rate limit /api/messages", Hatter
writes scenarios for X-Forwarded-For, atomic enforcement, header
spoofing — concrete behavior the Tweedles' code has to satisfy.
Without that pinning step, the team can converge on coherent code
that drifted from what was asked (analysis 024 documents an A/B
where canonical built baseline message endpoints instead of the
rate limiter the directive named).

This generalizes: any directive vague enough that the implementing
agents would have to *interpret* it benefits from Hatter's
test-first scoping. Most real directives are vague.

### When canonical wins

When the directive is concrete enough that interpretation is
unlikely — "add a `--verbose` flag that prints DEBUG-level logs",
"refactor `_resolve()` to use `Path.resolve()` instead of manual
prefix-stripping". Or when the work is exploratory and you'll
discard it (testing whether an architecture is even feasible
before committing). Or when iterating fast and the cost of being
wrong is "rerun the workflow", not "ship a bug."

The extra ~30% spend on tdd buys directive-alignment insurance.
When the failure mode is cheap, the insurance isn't always worth
it.

## Adding your own workflow

Drop a `<name>.yaml` in this directory matching the schema in
`src/wonderland/workflow.py`. The integrity tests in
`tests/test_workflow.py` are parameterized over `list_workflows()`,
so a new file automatically gets:

- Unique meeting ids and labels
- Seeds reference prior meetings (forward-only DAG)
- Entry meeting has empty directive (runtime fills it)
- Non-entry meetings have non-empty directives
- Every meeting has a positive budget
- Per-meeting budgets sum ≤ global cap (no starvation)

If your workflow needs new agent characters, ensure their roster
names match the keys in `Runner.make_full_cast`. If it needs a
fundamentally different artifact-handoff pattern (something
`SeedBinding` can't express), the schema needs extending — start a
discussion before bolting on, since selectors that work for two
workflows often turn out to be the wrong abstraction for the third.

## Eventually: Dodo composes these

Per roadmap `29497820`, the Dodo will eventually take a directive,
pick or compose a workflow on the fly, and run it. Workflows-as-
data is what makes that tractable — Dodo emits YAML, not Python.
Until that lands, picking a workflow by name is a human call (or
a heuristic in the showcase script).
