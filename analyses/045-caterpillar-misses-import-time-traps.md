# Analysis 045 — Caterpillar reads for coherence, not for import-time correctness; squathero3 shipped a Pydantic `date: date` shadow that no one caught until the operator tried to run it

**Date:** 2026-05-11
**Trigger:** [squathero3/.wonderland/reviews/review-001-full-stack-workout-logging-implementation.md](file:///home/jaryk/squathero3/.wonderland/reviews/review-001-full-stack-workout-logging-implementation.md)
**Substrate state:** 0.5.2. M8 routing now synthesizes follow-up tickets from findings (per 0.5.2); this run pre-dates that pivot so its `request-changes` verdict marked the originals ABORTED — but that's not the interesting failure mode here.

**Result:** Tweedledum shipped a `WorkoutSessionCreate(BaseModel)` with `date: date = Field(...)` after a `from datetime import date` at module top. Pydantic 2.13's "field name clashing with a type annotation" check rejects this at import time with `PydanticUserError`. The model literally can't load — the API surface is dead before the first request hits it. Caterpillar's `request-changes` verdict cited three findings: a schema mismatch between frontend/backend, a missing migration, and a component not wired into the entry point — all real, all coherence-grade. **The Pydantic shadow wasn't in her findings list.** The operator caught it manually trying to `uv run uvicorn` the backend.

## What Caterpillar's current review catches

Per [analysis 040](./040-cross-ticket-coherence-vs-review-scope.md) the M8 directive prioritises cross-ticket coherence FIRST — does the contract note name a field that the backend implements and the frontend assumes? Does the app entry point actually import the component the work produced? That guidance landed; Caterpillar's review-001 surfaces exactly those classes of bugs. Cross-ticket reading is the thing single-file review can't do, so M8 spends its budget there.

What that prioritisation explicitly trades away: **per-file static-time correctness**. A Pydantic model with a field-name/type-name shadow is a single-file bug — it doesn't require reading the contract note OR the consumer to catch. A simple import smoke test (`uv run python -c "from src.backend.main import app"`) would have surfaced it in 200ms. Caterpillar's reviewer-on-rotation doesn't run code; she reads it. And in reading, she's looking for cross-file shape mismatch, not for "would this even import."

## Why this is a real category, not a one-off

Three classes of single-file static-time bugs that Caterpillar's current review will reliably miss:

1. **Pydantic / dataclass field-vs-type shadows.** `field_name: type_name = Field(...)` where `type_name` is in the class namespace because of an import. The error is mechanical and would be caught by `python -c "import ..."`, but reading the file you'd have to notice the import line + the field declaration together.

2. **Unresolved type forwards.** A model references a class defined below it in the file, no `from __future__ import annotations` at top. Pydantic builds the field early and crashes on the unresolved forward reference. Same pattern: visible-on-read if you know to look, invisible if you're scanning for "does this implement the contract."

3. **Decorator + factory-default order traps.** `Field(default_factory=lambda: SomeEnum.DEFAULT)` where `SomeEnum` isn't imported, or where the factory closes over a class-level name that hasn't been defined yet. Pydantic eagerly evaluates the default during model construction. Cross-file review won't notice; a single import smoke would.

These are all "would this even load" bugs. Caterpillar's M8 doesn't load anything; she reads. So this class of bug ships when the Tweedles write it.

## Reasonable fixes, in increasing scope

1. **Small directive nudge.** Add to Caterpillar's M8 convenor_directive a numbered check: "Before the cross-ticket coherence walk, ask yourself — could you copy-paste the file's imports + class declarations into a Python REPL and have it load? If the answer is no, name that as a `block` finding." Doesn't require running code, just asks Caterpillar to mentally trace import semantics. Cheap to ship; might catch the obvious shadows.

2. **Static import-pass tool for Caterpillar.** Give Caterpillar a `verify_imports` tool that runs `python -c "import <module>"` against the project's source files and surfaces any ImportError / PydanticUserError / SyntaxError. Tool-call cost is trivial; the pass becomes mechanical. Worth doing because it's the kind of check that's *systematic* — a human reviewer would run the tests + try to import the module + then start reading. Caterpillar currently skips the first two.

3. **Per-meeting smoke tests** in the workflow. After M7 ships implementation, run the project's test suite (or just `python -c "import ..."` against the changed files). If anything fails, the iteration enters M8 with that data in seed context — Caterpillar then knows there's a load-time bug *before* she starts reading for coherence. This is the most ambitious: requires the substrate to actually invoke tooling on the workspace, which it currently doesn't.

(2) is probably the right move. Static-import verification is exactly the kind of mechanical check Caterpillar already does for git diffs (she reads `git_status` / `git_diff` to find what shipped); adding "verify it imports" to that pre-flight is in keeping with her character (§I: "approval is not given cheaply") without changing what she fundamentally reads for. The directive change for (1) is also free and could ship as a backup signal.

## What 0.5.2's follow-up-ticket routing means for this category

If we were re-running squathero3 today under 0.5.2's routing, Caterpillar's review-001 would still miss the Pydantic shadow. The original tickets would transition to DONE; three follow-up tickets would land QUEUED for the schema-mismatch, missing-migration, and unwired-component findings. The Pydantic shadow would ship to the operator's dev environment uncaught. The operator would `uv run uvicorn`, see the error, file a new ticket manually.

That's not necessarily wrong — the manual loop closes — but it's not free. The squathero3 cost was $5 to ship a feature, but the operator still spent debugging time identifying the bug + writing the fix. The next layer of automation is closing that loop too: either Caterpillar catches load-time bugs, or the substrate runs the import smoke between M7 and M8 so the team sees the error in their context.

## What this validates about the failure-modes thesis

Per the project memory: "every constitution's §VIII names its characteristic failure mode; this is what differentiates Wonderland from generic multi-agent architectures." Caterpillar's §VIII canonical failure is "severity inflation / deflation" — over- or under-rating findings. This isn't that; this is a *blind spot* — a class of bug she structurally doesn't look for. Worth distinguishing in the constitution literature: severity calibration is one failure mode, scope blind-spot is another. Same agent, different gap.

The fact that the operator caught it in 200ms with `python -c "..."` is the right tell: it's a check that *systematic tooling* handles trivially. The substrate's job, when faced with a failure mode that yields cheaply to mechanical checks, is to wire in the mechanical check rather than train the agent harder. Caterpillar gets to keep reading for what only careful reading can catch (cross-ticket coherence, intent drift, requirement omissions); the substrate fills in the rest.

## Honest limitations

- **Single data point.** One run, one Pydantic shadow, one missed catch. Could be Tweedledum being sloppy, could be a Caterpillar pattern. The fact that the failure mode is *mechanically predictable* (Pydantic raises a specific error class at module load) makes it worth filing without needing more samples.
- **The fix isn't free.** Giving Caterpillar a `verify_imports` tool means tool-call cost in M8. Probably trivial ($0.01-0.05 / review) but worth measuring before declaring it the default.
- **Scope creep risk.** "Also check that tests pass" / "also check that the linter is happy" / "also check coverage" is the obvious creep. Worth scoping the static check to "does this import" specifically; broader sanity checks belong in a separate meeting or as a config knob.

---

The substrate just shipped a working webapp for $5. The single human-debugging incident was a one-line Pydantic shadow Caterpillar didn't think to look for. That's a remarkable cost/output ratio with a discoverable, fixable gap. Both observations matter; this analysis files the gap so the next iteration can close it.
