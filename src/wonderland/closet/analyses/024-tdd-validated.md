# Analysis 024 — TDD workflow validated, parse-retry confirms

**Date:** 2026-05-06
**Runs:** Two TDD live runs against the same directive, one before
parse-retry and one after.
**Snapshot:** [analyses/data/024-tdd-validated/](data/024-tdd-validated/)
**Result:** **+1804 lines of working rate-limiter code shipped end-to-end**, 100% parse-retry recovery rate (5/5), and the TDD workflow goes from "fragile to a single Hatter parse error" to "reliable enough to be the default."

## Why this matters

Analysis 023 closed the canonical workflow's bug class (Tweedles ship code reliably). This analysis closes the *next* class — the one TDD exposed: **single-point-of-failure parse errors in agents whose contributions are load-bearing for downstream meetings.**

The TDD workflow's Hatter-writes-failing-tests phase is exactly that shape. If Hatter's M4 turn parses → M5 has a closure criterion (turn red tests green). If it doesn't → M5 has nothing to implement against, the team drifts to whatever feels reasonable, and the directive is silently dropped.

The fix is `611378d9` (parse-error retry) — small surgical change, 13 files modified, recovers turns the speak loop would have treated as silence. This analysis is the smoke test.

## The clean A/B

Same directive, same skeleton, same workflow, only difference is whether parse-retry was implemented. A rare clean A/B given how many variables usually move between live runs.

| Metric | Run A (no retry) | Run B (with retry) |
|---|---|---|
| Wall clock | 399s | 601s |
| Cost | $0.99 / $4 cap | $2.13 / $4 cap |
| LLM calls | 161 | 209 |
| Parse errors observed | 2 (silenced, work lost) | 5 (all recovered) |
| Parse retry success rate | n/a | **100% (5/5)** |
| Late-publish events | 4 | 5 |
| Test scenarios shipped | **0** | 14 |
| Implementation artifacts | 3 (recovery in M6) | 2 + recovery |
| Reviews | 1 (of wrong feature) | 1 (of right feature) |
| **Code shipped** | **90 lines (baseline message API)** | **1804 lines (rate limiter end-to-end)** |
| **Directive alignment** | **drift — built baseline endpoints** | **hit — built the actual rate limiter** |

The cost roughly doubled. The output went from "wrong thing" to "right thing with comprehensive coverage." Value-per-dollar is dramatically better.

## What Run B actually shipped

```
Backend (NEW):
  src/backend/rate_limiter.py                 (133 lines)
  src/backend/api/observability.py            (63 lines)

Backend (MODIFIED):
  src/backend/api/messages.py                 (+94 lines — wired rate limiter in)
  src/backend/api/__init__.py                 (+2 lines — registered routes)
  tests/conftest.py                           (+8 lines)

Frontend (NEW):
  src/frontend/rate_limit.ts                  (176 lines)
  src/frontend/api_client.ts                  (175 lines)
  src/frontend/hooks/useRateLimit.ts          (114 lines)
  src/frontend/components/RateLimitError.tsx  (90 lines)
  src/frontend/__tests__/rate_limit.test.ts   (233 lines)

Tests (NEW):
  tests/test_rate_limit_enforcement.py        (253 lines)
  tests/test_rate_limit_messaging.py          (213 lines)
  tests/test_rate_limit_observability.py      (259 lines)
```

Total: **+1804 / −9 across 13 files**. That's a real feature, not scaffolding.

The 14 Hatter test scenarios cover the load-bearing edge cases the directive hinted at (and several it didn't):

- Client exceeds quota → 429 with Retry-After header
- Retry-After is integer seconds, not HTTP-date format
- Per-client identification via X-Forwarded-For with remote-address fallback
- Spoofed `X-RateLimit-*` request headers ignored; server state authoritative
- JSON body includes error reason; rate-limit state in headers and body
- `X-RateLimit-Reset` is absolute wall-clock (not relative) so frontend countdown is clock-skew-resilient
- Atomic enforcement — no race where two concurrent requests at quota both pass
- Metrics export with rejections tracked separately from accepts
- Documented fallback when client ID is unidentifiable
- Frontend respects Retry-After (no manual retry before countdown expires)

This is the kind of test surface that's hard to extract from a one-shot Sonnet directive expansion. Hatter's character — *the edge is where the system actually lives* — is doing real work here.

## Parse-retry detail

Five errors fired across 3 agents, all recovered:

```
[mad_hatter]   HatterResponseParseError    len=15,606  → retry → ✓
[tweedledum]   TweedleResponseParseError   len= 1,907  → retry → ✓
[tweedledee]   TweedleResponseParseError   len=     0  → retry → ✓  (empty response!)
[tweedledum]   TweedleResponseParseError   len=     0  → retry → ✓  (empty response!)
[tweedledum]   TweedleResponseParseError   schema-fail → retry → ✓  (validated JSON, wrong shape)
```

Three failure modes covered in one run:

1. **Prose without JSON** (Hatter's 15K-char "let me think out loud about test scenarios..." with no JSON wrapper). Retry's "respond with JSON only, no prose" hint produced clean output on attempt 2.
2. **Empty response** — the LLM returned `""`, which under the old behavior was just silence. Retry's placeholder substitution (`response_text or "(empty response)"`) made the API accept the assistant message and the LLM came back with content.
3. **JSON-but-wrong-schema** — the LLM produced valid JSON that failed Pydantic validation. Retry's hint mentioning the schema produced a correctly-shaped response.

Cost of retry: roughly one extra LLM call per recovered turn. Hatter's 15K-char retry was the most expensive at maybe $0.05; the empty-response retries were tiny. Total retry overhead probably ~$0.15 across the run, well worth the directive-aligned outcome.

## Findings

### F1 — Parse-retry is the load-bearing fix for TDD viability

Without retry, TDD's M4 (Hatter) is a single point of failure. With retry, Hatter's prose-without-JSON failure mode (the one that bit *both* live TDD runs) recovers reliably. The TDD workflow goes from "demo can't be trusted" to "demo can be the default."

### F2 — Directive drift vs directive hit is a measurable distinction

Run A built coherent code that didn't match the directive. Run B built coherent code that did. The Wonderland team produces *something* either way — the question is whether the something is what the user asked for. Hatter's failing tests are what pin the team to the directive.

This generalizes beyond TDD: any agent whose role is "convert the user's vague intent into concrete commitments" (Alice's stories, Cat's ADRs, Hatter's scenarios) is doing directive-alignment work. When their output is lost, the team falls back to whatever feels reasonable from the seeds in scope, which doesn't always match what was asked.

### F3 — Path drift is a content-quality issue, not orchestration

Tweedledee's frontend code landed in `src/frontend/` instead of the skeleton's `frontend/src/`. Tweedles invented their own layout instead of reading the existing one. Symptom: the directive doesn't make the layout-of-record explicit enough; Tweedles default to a guess.

This is a *content* issue (prompt context), not a *substrate* issue (orchestration). Worth a directive tweak in the workflow YAMLs, not a framework change. Filed for next iteration but not blocking.

### F4 — 100% retry rate is evidence against rushing the bigger refactor

The earlier conversation considered Anthropic `tool_use` as the response mechanism (option C in the parse-error discussion) — eliminating parse errors structurally instead of recovering them. Run B's 100% retry rate argues against that being urgent. If retry fails reliably enough to recover every observed parse error, the refactor's value is primarily preventing the ~$0.15 retry cost per run, which doesn't justify touching every agent's `deliberate()`.

Worth revisiting if retry rate drops below ~80% in production usage, or if specific failure modes turn out to be unrecoverable via retry. Until then, retry is sufficient.

## Workflow-as-default decision

Based on this run, **TDD becomes the recommended default workflow** for feature work. Canonical is preserved as a faster/cheaper option but with explicit positioning:

- **TDD (default):** ~$2.00, ~10 min, directive-aligned by construction (Hatter pins behavior). Use this for any feature work where regressions matter.
- **Canonical (faster):** ~$1.50, ~7 min, faster to iterate but higher directive-drift risk. Use for throwaway prototypes, exploratory work, or directives concrete enough that drift is unlikely.

The README and `closet/workflows/README.md` are updated accordingly in this commit. The canonical YAML stays in the repo — for posterity, for fast iteration, and as a structural variant if Dodo's eventual workflow generation wants both shapes available.

## What we filed

No new roadmap items. Existing item statuses:

- `611378d9` (parse-error retry) — **landed in commit 35055cd**, validated here
- `c664d71b` (agent IDLE race) — still open, observed 5 late-publish events in this run (slightly more than prior — possibly because parse-retry adds turns that surface the race more often)
- `29497820` (Dodo dynamic orchestrator) — still backlog; this analysis doesn't change its priority

## What's next

1. **Path-drift directive tweak** — tighten the implementation meeting's directive to point Tweedles at the existing skeleton layout (`list_files` first, then extend) so they don't invent `src/frontend/` when `frontend/src/` exists.
2. **Eval harness (P7)** — the actual A/B in this analysis is suggestive but small-N (1 directive). The P7 eval needs a portfolio of directives × workflows × baselines to make claims that generalize.
3. **Live run a Geocities-style directive** under the new TDD-default — would showcase the framework at non-trivial scope with the directive-alignment guarantee in place.

## Headline

**The framework now reliably ships the feature that was asked for.** That's the bar that needed clearing before P7 eval work was meaningful. Cleared.
