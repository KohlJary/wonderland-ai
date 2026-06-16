# 047 — T-ab74: content-level scope leak (title-gate design)

**Status:** implemented (`scope_leak.py` + M3.75 hook + 9 tests, all green)
**Roadmap:** T-ab74 (`d16bfb33`)
**Origin:** ldr-final fresh pilot M1 design, 2026-06-06 (`tdd-design-m1-20260606T131014`, $2.04, 0 op-Qs)
**Relates to:** T-ab73 (structural ticket scope-lock), T-ab50 (explicit-signal>heuristic), T-ab63 pass 2 (title-token clustering), T-a5 (cross-feature consolidation), T-ab70 (reverted over-correction — the cautionary tale)

## Problem

The ldr-final M1 design run was the cleanest pilot to date — 5 correctly-M1-scoped
features, 0 operator questions, $2.04. But **3 of 23 tickets describe M2/M6 work**
under an M1 directive that said *"no dashboard, no /partner-setup UI, no card
endpoints, SCOPE LOCK on M1."*

The three leaks:

| Ticket title | Describes | Belongs to |
|---|---|---|
| `protect-dashboard-backend-route-behind-auth-middleware` | `GET /dashboard` returning partner profile data | m6 / m2 |
| `frontend-dashboard-page-structure-api-integration...` | dashboard skeleton with time/weather/news card placeholders | m6 |
| `frontend-call-protected-dashboard-endpoint-and-handle-401-redirect` | React component displaying partner profile | m6 / m2 |

Three *other* tickets reference the same surfaces but are **legitimate**:

| Ticket title | Cross-milestone surface appears as | Verdict |
|---|---|---|
| `implement-session-middleware-and-get-auth-me-endpoint` | guard target: *"guard /dashboard … (stubs for now; actual dashboard lands in M3)"* | legit |
| `frontend-sign-up-and-sign-in-routes-forms...` | redirect target: *"on 200, redirect to /dashboard"* | legit |
| `backend-signin-endpoint-session-middleware...` | protected route: *"protect /dashboard route with middleware"* | legit |

## Why T-ab73 can't catch it

T-ab73 gates a ticket's **milestone field**, resolved structurally: `ticket → sources[0]
→ parent feature → feature.milestone`, compared to the active scope. It hard-rejects
at `TicketRegistry.write` when the parent feature belongs to a different milestone.

The three leaks **pass** that gate because their parent feature
(`session-middleware-and-protected-route-enforcement`) is *legitimately M1*. The leak
is in the ticket **prose** authored during M3 decomposition, not in the structural
milestone field. T-ab73 closed the structural axis; this is the content axis.

## Detection signal: ticket TITLE vs foreign-milestone surface tokens

The sharp, structural discriminator: **the title names the deliverable; the body
references context.** In all six tickets above, the title alone separates leak from
legit perfectly:

- leak titles contain a foreign-milestone surface noun (`dashboard`) as the deliverable
- legit titles are M1 work (`session-middleware`, `signin`, `signup`); `dashboard`
  appears only in the body as a guard/redirect target

So: scan the **title only**. Body references stay legitimate (no false-positive on
guard-stubs). This mirrors T-ab50's "explicit signal beats LLM heuristic" — we move
detection out of LLM-pattern-matching into a deterministic token check.

### Foreign-token derivation

At the M3.75 hook the active scope is still set (`set_active_milestone_scope(None)` runs
in the `finally` *after* consolidation fires) and `MilestoneRegistry` is on disk.

1. Load all milestones. Identify the active one via `scope.slug`.
2. `active_tokens` = tokenize(`active.slug` + `active.name`) ∪ tokenize(`scope.goal`)
   ∪ tokenize(each `scope.done_when`) ∪ `scope.consumes` tokens.
3. `foreign_tokens` = ⋃ tokenize(`m.slug` + `m.name`) for every `m != active`,
   minus `active_tokens`, minus a generic-stopword set.
4. A ticket leaks iff `normalize_title_tokens(ticket.title) ∩ foreign_tokens ≠ ∅`.

ldr-final roster tokenizes cleanly:

```
m1-auth-foundation          → {auth, foundation}         (active — excluded)
m2-partner-profile-storage  → {partner, profile, storage}
m3-time-card                → {time, card}
m4-weather-card             → {weather, card}
m5-news-card                → {news, card}
m6-dashboard-integration... → {dashboard, integration, demo, readiness}
```

`foreign_tokens` after subtracting active + generic stopwords (`storage, integration,
demo, readiness, foundation, core, base, setup, management, support, time`):
`{partner, profile, dashboard, weather, news, card}`.

Validation against the six tickets — **3/3 leaks flagged, 3/3 legit cleared:**

| Ticket title | Title tokens ∩ foreign | Flag? |
|---|---|:--:|
| protect-**dashboard**-backend-route | {dashboard} | ✅ leak |
| frontend-**dashboard**-page-structure | {dashboard} | ✅ leak |
| frontend-call-protected-**dashboard**-endpoint | {dashboard} | ✅ leak |
| session-middleware-and-get-auth-me | ∅ | clean |
| sign-up-and-sign-in-routes-forms | ∅ | clean |
| signin-endpoint-session-middleware | ∅ | clean |

`time` is deliberately stopworded (too generic — `session timeout` etc. tokenize to
`timeout`, not `time`, so the card-family loses only its weak token, keeping
`weather`/`news`/`card`/`dashboard`/`partner`/`profile`).

## Action: auto-retract at M3.75 — NOT hard-reject at write

We just reverted T-ab70 (`ffad1cb`) because over-aggressive *in-the-retry-path* scope
enforcement drove Rabbit into a 42-minute zero-feature question loop. **Do not put this
check in `TicketRegistry.write`.** A write-time hard-reject on an ambiguous content
signal would re-create that failure mode: Rabbit retries a ticket it can't tell how to
satisfy.

Instead, mirror the **T-a5 cross-feature precedent exactly**: detect at the post-design
M3.75 hook (`_maybe_fire_cross_feature_consolidation`'s sibling), deterministic, no agent
calls, and **auto-retract** leaking tickets to `ABORTED` via `ticket_lifecycle`. The
file stays on disk for forensics; `ABORTED` is recoverable; the work isn't lost — it gets
re-decomposed when that milestone's own design run fires (the T-ab73 philosophy: *"save
it for that milestone's design run"*). Because it runs **after** the design loop exits,
it is structurally outside the retry path — no loop risk.

This makes false-positive cost bounded and recoverable (ABORTED + on-disk + stderr +
operator un-abort), which justifies acting autonomously rather than merely flagging.

### v1 conservatism

- **Title-only** decision. Body-mention of foreign surfaces emits a `[scope-leak]`
  stderr *soft signal* (no action) so we collect body-leak prevalence data for future
  calibration without FP-killing legit guard-stub tickets.
- Reuse `cross_feature._normalize_title_tokens` / `_TITLE_STOPWORDS`, extended with the
  milestone-scaffolding stopwords above.

## Implementation plan

1. **New module `src/wonderland/scope_leak.py`** (sibling to `cross_feature.py`):
   - `_foreign_milestone_tokens(project_root, scope) -> frozenset[str]`
   - `find_content_scope_leaks(project_root, scope) -> list[ScopeLeakDecision]`
     (pure read-side; `ScopeLeakDecision{ticket_slug, title, foreign_tokens,
     foreign_milestones}`)
   - `retract_content_scope_leaks(project_root, scope, *, actor) -> list[...]`
     (walks PENDING→QUEUED→IN_PROGRESS→ABORTED like `consolidate_cross_feature_duplicates`)
2. **Wire into the hook**: in `_maybe_fire_cross_feature_consolidation` (or a new sibling
   `_maybe_fire_content_scope_leak_retraction`) call after cross-feature consolidation,
   guarded by the same `name in ("tdd-design","tdd-decompose")` + `get_active_milestone_scope()
   is not None`. stderr instrument: `[scope-leak] workflow=… milestone=… retracted=N`.
   Order it *after* cross-feature dedup so we don't retract a ticket that's about to be
   consolidated anyway.
3. **Tests** (`tests/test_scope_leak.py`): the six ldr-final titles as fixtures
   (3 flag / 3 clear); no-active-scope no-op; single-milestone-project no-op; recoverable
   ABORTED state assertion; body-mention soft-signal does NOT retract.

## Risks + calibration knobs

- **FP from generic foreign tokens** — bounded by recoverable ABORTED + stopword list.
  Knob: `_SCOPE_STOPWORDS`.
- **FN when a milestone slug is non-descriptive** (e.g. `m6-phase-six`) — foreign tokens
  would be empty; check silently passes. Acceptable; the structural T-ab73 gate still
  covers the parent-feature axis. Documented limitation.
- **Token collision across in-scope work** — if M1 legitimately owned a token that also
  names a later milestone, step 2's `active_tokens` subtraction protects it.

## Action decision (resolved 2026-06-07)

**Operator chose auto-retract.** v1 transitions title-flagged tickets to `ABORTED` at the
M3.75 hook (recoverable, file-on-disk, no agent calls, outside the retry path). Rationale:
closes the leak autonomously toward the Tier-2 goal, FP cost bounded by recoverability +
the sharp 3/3-vs-3/3 title signal. Body-mention remains a soft `[scope-leak]` stderr signal
with no action.
