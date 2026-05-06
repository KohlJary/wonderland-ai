# Analysis 021 — Multi-Session Validation: Design Compounds, Execution Doesn't

**Date:** 2026-05-06
**Phase milestone:** P6.T38 (in progress) — multi-session validation rerun.
The clean end-to-end follow-up to [analysis 020](./020-multi-session-persistence.md),
which closed with "Session 2 hit `max_tool_iterations=10` and shipped 0
source files; bumped to 20 — validation rerun is the next analysis's
work." This is that analysis.
**Components touched (substrate, between 020 and this run):**
- `src/wonderland/agent.py` — `max_tool_iterations: int = 20` (already
  in place from 020's diagnostic; carried into this run)
- `/tmp/test_t38_session1.py` — added `_commit_session_baseline()` to
  the `finally` block so Session 1's work commits as a discrete commit
  on top of the seed
- `/tmp/test_t38_session2.py` — added `_commit_prior_baseline_if_dirty()`
  defensive baseline-commit on entry, so Session 2's `git_diff HEAD` is
  guaranteed to show only Session 2's additions (regardless of whether
  Session 1 finished cleanly)
**Run transcripts + artifacts:**
- [Session 1 run.log](./data/021-multi-session-validation/session1/run.log)
- [Session 1 team-diff.patch](./data/021-multi-session-validation/session1/team-diff.patch) — diff against the seed
- [Session 2 run.log](./data/021-multi-session-validation/session2/run.log)
- [Session 2 team-diff.patch](./data/021-multi-session-validation/session2/team-diff.patch) — diff against Session 1's commit
- [Session 2 wonderland snapshot](./data/021-multi-session-validation/session2/wonderland-snapshot/) — accumulated registries + memory after both sessions
- [git log](./data/021-multi-session-validation/git-log.txt) · [cumulative diff stat](./data/021-multi-session-validation/cumulative-diff.stat)
- [Session 1 script](./data/021-multi-session-validation/test_t38_session1.py) · [Session 2 script](./data/021-multi-session-validation/test_t38_session2.py)
**Comparison baseline:**
- [analysis 020](./020-multi-session-persistence.md) — same setup, prior
  iteration with `max_tool_iterations=10`

> Two sessions ran on the same `project_root` and `.wonderland/`,
> with the inter-session commit step in place so each session has a
> clean `HEAD` to diff against. Session 1 (translation chat MVP)
> shipped **at -49% of analysis 020's elapsed time and -48% of its
> cost**: $0.80 / 92 calls / 8.7 min. Session 2 (user-blocking)
> *did* ship code this time — `+214 lines / 4 files` of real backend
> work, including a new `blocks.py` API surface — vs. zero in
> analysis 020.
>
> But the headline finding is sharper than "the iter bump worked."
> **Memory compounds for design artifacts but BROKE for execution
> artifacts.** Stories went 5 → 10 across sessions; tickets 5 → 9;
> contract notes 6 → 8; ADRs 1 → 2 — registry numbering continuous,
> Tweedledum's Session 2 backend code citing Session 1's contracts
> by name. *Implementations and reviews regressed to zero.* Analysis
> 020's snapshot had `implementations/` (2 entries) and `reviews/`
> (3 entries). This run's snapshot has neither directory at all —
> the registry never created them because no implementation or
> review utterance ever published cleanly with non-empty content.
>
> The Tweedles ship code via tool side-effects (`write_file` lands
> on disk regardless), and Caterpillar reads code via tools (13
> calls in Session 2's M5, real engagement). But neither produces
> a persisted artifact, so the *provenance* of the shipped code
> isn't recorded — it's there in the git history, but not in
> `.wonderland/` where the next session would look for it.

---

## Why this matters

Analysis 020 established that **registry-level memory compounds**:
contract notes count continuously across sessions, agents cite prior
artifacts by number, redundant ADRs get correctly declined. That's the
load-bearing thesis claim and it survived.

What analysis 020 deferred was *whether the iter-bump fixed the
implementation-phase silence*. This run answers: **partially.** Code
ships now (Session 2: +214 lines, +1 new file). But the *artifact
describing the implementation* doesn't reach the registry. That
matters because Session 3+ memory needs implementation artifacts to
do its job — Caterpillar reading "review-001 found X" is what gives
the next reviewer the "we already raised this" muscle. Without
implementation/review persistence, the compounding curve has a hole.

This analysis surfaces the precise mechanism by which execution-side
memory fails. The fix is architectural and is filed as four roadmap
items (see *What we filed* below).

## Setup

Same as analysis 020, plus the inter-session commit pattern:

1. Session 1 seeds the fullstack-fastapi-react template into
   `/tmp/t38-multi-session/`, commits the seed, runs the 5-meeting
   sequence, **and now commits Session 1's work as a separate
   commit** on top of the seed (via `_commit_session_baseline()`
   in the script's `finally` block).
2. Session 2 reads the existing `.wonderland/` and source tree,
   runs the same 5-meeting sequence on top, and **defensively
   captures any uncommitted Session 1 work as a baseline before
   starting** (via `_commit_prior_baseline_if_dirty()`). Result:
   `git_diff HEAD` in Session 2 shows only Session 2's additions
   — which is what Caterpillar reads in M5.

Final git history at `/tmp/t38-multi-session/`:
```
dd1c42f session 2: user blocking (backend only — frontend Tweedle no-op'd)
248fdf5 session 1: translation chat
77f1cb0 seed: fullstack-fastapi-react baseline (T38 Session 1)
```

## What shipped

### Session 1 (greenfield translation chat on the seed)

| | Analysis 020 (S1) | This run (S1) |
|---|---|---|
| Total cost | $1.55 | **$0.80** (-48%) |
| LLM calls | 150 | **92** (-39%) |
| Elapsed | 17 min | **8.7 min** (-49%) |

Code shipped:
- `src/backend/api/auth.py` (+264 lines, NEW) — full auth surface
- `src/backend/api/messages.py` (+239 / -42, replaced placeholder echo)
- `src/backend/models.py` (+261 lines, replaced HelloMessage placeholder)
- `src/backend/api/__init__.py` (+4 lines)

Artifacts persisted to `.wonderland/`:
- 5 stories (Alice)
- 1 ADR (Cat — translation-chat data model)
- 5 tickets (Rabbit)
- 6 contract notes (Tweedles)
- **0 implementations** *(see findings)*
- **0 reviews** *(Caterpillar made only 2 calls / $0.0124 — barely engaged in M5)*

### Session 2 (user-blocking continuation)

| | Analysis 020 (S2) | This run (S2) |
|---|---|---|
| Total cost | (lower; design only) | $1.09 / 93 calls |
| Elapsed | ~6 min | 6.9 min |
| Implementation utterances | 0 (iter exhaustion) | **1 (placeholder)** |
| Code shipped | **0 source files** | **+214 / -0 across 4 files** |

Code shipped (vs. Session 1's commit):
- `src/backend/api/blocks.py` (+131 lines, NEW) — block surface
- `src/backend/models.py` (+34 lines) — Block model added
- `src/backend/api/messages.py` (+45 lines) — block enforcement at send + list
- `src/backend/api/__init__.py` (+4 lines)

Artifacts added in Session 2 (cumulative shown):
- Stories 6–10 (5 new — block, list-blocks, blocked-msg-feedback, unblock, language-pair-fast-follow)
- ADR-002: "User blocking — additive model with silent-blocking semantics" *(Cat shipped a second ADR despite the M2 directive saying don't if ADR-001 covers it; Cat judged the new feature warranted a fresh ADR — defensible call)*
- Tickets 6–9 (4 new)
- Contract notes 7–8 (2 new — user-blocking-and-message-gating, block-enforcement-at-send-and-list)
- **0 new implementations**
- **0 new reviews** *(Caterpillar made 13 calls / $0.0853 — substantial engagement, but no review artifact persisted)*

## Wins

### 1. The inter-session commit pattern works cleanly

`HEAD` now tells the story: seed → Session 1's commit → Session 2's
commit. Caterpillar's `git_diff HEAD` in M5 of Session 2 sees only
Session 2's additions (this validates the change). The session
scripts now have idempotent commit helpers (`_commit_session_baseline`
in S1, `_commit_prior_baseline_if_dirty` in S2) that are safe to
re-run.

### 2. Session 1 is dramatically faster and cheaper than baseline

Half the cost, half the elapsed time, two-thirds the call count vs
analysis 020. Some of that is variance (Haiku is non-deterministic
across runs), but the consistency of "M2 finished in 83s with
Rabbit shipping 5 tickets in one turn" suggests substrate-level
gains too: the parser-preview improvement (committed before this
run) catches malformed responses faster, and the iter bump means
fewer retries.

### 3. Memory compounding for design artifacts works as designed

The interesting numbers are the deltas:

| Artifact kind | Session 1 | After Session 2 | Delta |
|---|---|---|---|
| Stories | 5 | 10 | +5 |
| ADRs | 1 | 2 | +1 |
| Tickets | 5 | 9 | +4 |
| Contract notes | 6 | 8 | +2 |

Continuous numbering (`contract-note-007` and `008` continue from
`006`), Tweedledum's S2 `models.py` Block class extending the User
and Message ForeignKey relationships established in S1's `models.py`,
and Cat's S2 ADR explicitly framing blocking as "additive to ADR-001"
rather than re-deriving the data model — the design layer
compounds exactly as the thesis predicts.

### 4. Tweedledum's S2 backend code cites Session 1 by name

`blocks.py` imports `User` and `Message` from `src/backend/models.py`
(both originally added in Session 1), references the existing
`get_db()` session factory, and uses the same FastAPI dependency
pattern as `messages.py`. This is the asymmetric-extension behavior
the showcase was designed to test: the team reaches into existing
work rather than re-architecting around it.

## Findings (the headline)

### F1 — Execution-side memory regressed to zero

Analysis 020's snapshot had `implementations/` (2 artifacts) and
`reviews/` (3 artifacts). This run's snapshot has **neither
directory**. The registries are created lazily — they only exist
once the first artifact of that kind successfully persists. So:
no successful `implementation` utterance with non-empty payload
ever published in either session, and no successful `review`
utterance either.

This is a regression vs analysis 020, which had Caterpillar
producing 3 reviews against Session 2's pre-existing
implementation. The mechanism by which it regressed is two
distinct failure paths, one per session:

**Session 1 — implementation utterances suppressed as late-publish.**
Both Tweedles overshot M3 (contract negotiation) into implementation
work. Their tool calls (`write_file`) succeeded mid-loop and landed
backend code on disk. Their resulting `implementation` utterances
took >60 seconds to compose (because the tool loop is slow), and
M3's wall-clock quiescence closed the thread beneath them. The
late-publish stop-gap then suppressed the utterances entirely:

```
[late-publish] tweedledee → thread 'contract-negotiation' (already COMPLETE)
  — suppressing implementation: "Responding to your three proposals.
  I've filled in frontend impact on all three..."
[late-publish] tweedledum → thread 'contract-negotiation' (already COMPLETE)
  — suppressing implementation: "I've responded to your three propositions
  with full backend impact filled in..."
```

The CODE landed on disk. The UTTERANCE describing it was thrown away.
M4 (the actual implementation thread) opened and ran 60 seconds of
silence — the Tweedles had nothing fresh to engage with because
they'd already done the work in M3-overshoot.

**Session 2 — Tweedle asymmetric failure pattern.** M3 in S2 did
NOT produce contract negotiation at all (Tweedles silent for the
full 10s before M3 quiesced — separate quiescence-timing anomaly,
see F3). M4 then had:

- `M4[t=345.84s] tweedledee implementation: "Files written in tweedledee's frontend turn [side=frontend]"` — **clean publish, but the artifact title is the literal placeholder default from `_synthesized_implementation_artifact`'s no-files-detected path. Frontend files on disk are unchanged from the seed.** Either Tweedledee's `write_file` calls hit a path that rejected them, or they wrote identical content (no-op).
- `M4[t=353.09s] tweedledum contract_note: "(no body)"` — **empty body. The parse-error signature.** Tweedledum was the one actually writing the backend code (the +214 lines visible in the diff), but their implementation utterance failed to validate, got coerced into a contract_note shell, and persisted no useful artifact.

Net result, both sessions: backend code lands, *artifacts describing
it don't*. The git history records *what* shipped; the registry
doesn't record *why* — which is what compounding judgment depends on.

### F2 — Caterpillar engages substantively but produces no artifact

Session 2 M5: Caterpillar made **13 LLM calls / $0.0853**. That's
real engagement — it's reading the diff via `git_diff`, exploring
the changes via `read_file`, surveying via `git_status`. Yet no
review artifact persisted.

The mechanism is almost certainly the read-tool exhaustion of the
shared iteration cap. Caterpillar's loop is read-heavy by design
(it has to understand the diff before it can review it). With a
flat `max_tool_iterations=20` covering both reads and the final
synthesis call, a 30-file changeset eats the budget on exploration
and leaves nothing for the review utterance.

This is exactly the asymmetry the **read/write iter-cap split**
roadmap item (`98ec46b0`) addresses: pure-read tools shouldn't
count against a cap that exists to prevent runaway *side effects*.

### F3 — M3 quiescence anomaly: 10s vs the configured 60s

Session 2's M3 lasted only 10 seconds: Dodo issued the
contract-negotiation directive at `t=292.31s`, and the thread
monitor flipped to `quiescent` at `t=302.32s`. With
`quiescence_seconds=60.0` configured, this should have waited
another 50 seconds for any Tweedle response.

This appears to be a thread-monitor wall-clock reset bug — the
seed-replay bursts at `t=292.31s` may not have correctly reset
the inactivity timer, so the monitor was already 50+ seconds
into its quiescence countdown when the seeds replayed. Worth a
roadmap item to investigate, but the M3+M4 consolidation makes
this moot for the canonical sequence (no M3 boundary to time out
beneath).

## Diagnosis: the M3/M4 boundary is broken

Three distinct bugs surfaced this run, all stemming from the same
architectural assumption — that contract negotiation and
implementation are separable phases. Looking at what the system
actually *wants* to do:

- Session 1: Tweedles try to combine both phases and get cut off
- Session 2 M3: Tweedles refuse to engage in contract negotiation at all
- Session 2 M4: One Tweedle ships placeholder utterance, the other ships code-without-utterance

The team is voting against the separation, repeatedly, in different
ways. The original justifications for the split (frozen-seam
checkpoint, asymmetric tool surface, cross-meeting composition test)
either never materialized in practice or are already covered by other
mechanisms (artifact-level state machine, ADR→tickets handoff).

**The fix is to consolidate M3+M4 into a single "design and ship"
meeting** — filed as `903e6137`. With turn-based quiescence
(`22eef6fd`) replacing wall-clock, the combined meeting stays open
exactly as long as anyone is doing work and closes when the team
is genuinely done. No more late-publish suppressions; no more
mid-tool-loop closures.

## Tweedle asymmetry: a real pattern

Looking across analyses 018, 020, and this one, a clear behavioral
asymmetry between the Tweedles is emerging:

- **Tweedledum (backend)** is *more eager to grab `write_file`* and
  start implementing. Often parse-errors on the resulting utterance
  (the response is so heavy with tool-call results that JSON
  formatting fails). Code lands on disk; the utterance describing
  it is sometimes lost.
- **Tweedledee (frontend)** is *more cautious about implementation*
  before contracts agree. Often publishes clean utterances (no
  parse errors) but doesn't ship code — the placeholder
  `"Files written in tweedledee's frontend turn"` artifact title
  is the no-files-detected fallback.

This isn't necessarily a bug. Tweedledee correctly recognizes
that frontend client code depends on backend types being firm —
generating it before the contracts close means rewriting it. The
problem is *system-level*: the meeting boundary closes before
backend types stabilize, so Tweedledee's restraint produces
silence rather than a held-back commit.

Combined design-and-ship meeting + turn-based quiescence would
let Tweedledum ship backend, Tweedledee see backend land, then
Tweedledee ship frontend against the now-stable types — all
within one meeting, one tool-loop pair, one cohesive thought.

## What we filed

Four roadmap items shipped during this analysis cycle, three of
which are P1 because they unblock cleaner showcase runs:

| ID | Priority | Title |
|---|---|---|
| [`903e6137`](#consolidate-m3-m4) | P1 | Consolidate contract-negotiation + implementation into one meeting |
| [`22eef6fd`](#turn-based-quiescence) | P1 | Turn-based quiescence detection (replace wall-clock) |
| [`98ec46b0`](#split-iter-cap) | P2 | Split max_tool_iterations: read tools don't increment counter |
| [`0aab0178`](#local-router) | P2 | Local-model router for substrate calls (Ollama) |

The first two compose: combined meeting + turn-based quiescence
addresses the M3/M4 leak class, the late-publish suppression
class, and the meeting-closes-mid-tool-loop class — three of
this analysis's four findings collapse into a single architectural
fix. The third addresses Caterpillar's review-artifact failure
(F2). The fourth is unrelated to this analysis but was filed in
the same conversation; it's a development-cost optimization.

## What's next

Land the M3+M4 consolidation and turn-based quiescence (the two
P1 items). Re-run T38 against that substrate. Expect:

- One meeting between decomposition and review, instead of two
- No late-publish suppressions
- `implementations/` and `reviews/` directories populated again
- Tweedledee ships frontend code against now-stable backend types
- Caterpillar's review artifact persists (split iter cap helps too)

Then T38 Session 3: incident response on top of two prior sessions
of work. With turn-based quiescence in place, the slower deliberation
of "Dormouse observation lands → team responds against existing
codebase + existing decisions" should run cleanly without the
meeting-boundary leaks that dominated this analysis.

The thesis is unchanged: identity-native agents with persistent
memory should compound. The compounding works for design; the
mechanism by which it currently fails for execution is now
documented and architecturally addressable.
