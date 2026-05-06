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
| `canonical` | 5 | $3.00 | Standard greenfield-on-skeleton feature work. Validated end-to-end across analyses 015-023. |
| `tdd` | 6 | $4.00 | Test-first variant — Hatter writes failing tests before Tweedles implement. Use for safety-critical or regression-prone surfaces. |

Run any of them via the demo script:

```bash
uv run python scripts/workflow_demo.py --workflow smoke
uv run python scripts/workflow_demo.py --workflow canonical --directive "..."
uv run python scripts/workflow_demo.py --workflow tdd --directive "..."
uv run python scripts/workflow_demo.py --list
uv run python scripts/workflow_demo.py --workflow tdd --dry-run
```

## canonical vs tdd — compare and contrast

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

| | canonical | tdd |
|---|---|---|
| Cost | ~$1.50 (validated, analysis 023) | ~$2.00-2.50 (estimated; not yet smoke-tested live) |
| Wall clock | ~7-8 minutes | ~10-12 minutes (estimated) |
| Implementation drift | possible — Tweedles interpret a directive | bounded — Tweedles implement to a runnable spec |
| Test coverage | review-after-the-fact (Caterpillar in M5) | test-first (Hatter in M4) |
| When it shines | greenfield exploratory work, throwaway prototypes | safety-critical surfaces, regression-prone code paths |

### When canonical wins

For the standard "build me a feature on a working skeleton" flow,
canonical is the right tool. Hatter's role as review-after-the-fact
is sufficient when the feature is exploratory and bug discovery is
cheap (you re-run the showcase, you see the bug, you ship the fix).
The extra meeting in tdd costs real money for relatively little
gain when the feature is throwaway-grade or hasn't been
production-hardened yet.

### When tdd wins

When a regression would be expensive — auth flows, payment paths,
data-integrity invariants, security boundaries — tdd's test-first
shape pins behavior in a way canonical doesn't. The Tweedles can't
silently drop a contract requirement because Hatter's tests would
catch it. The extra ~30% spend buys a stronger safety guarantee.

Tdd is also better when **you don't trust the directive yet**.
canonical assumes the directive is rich enough to drive
implementation; tdd assumes Hatter's tests will surface the
directive's ambiguities before Tweedles commit to an interpretation.

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
