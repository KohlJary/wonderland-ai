# Analysis 020 — Multi-Session Persistence: Memory Compounds at the Registry Level

**Date:** 2026-05-06
**Phase milestone:** P6.T38 (in progress) — multi-session persistence
showcase, third of P6's three. First showcase that runs the team
across multiple sessions on the same `.wonderland/` directory to test
whether memory accumulates and compounds.
**Components touched:**
- `src/wonderland/templates/fullstack-fastapi-react/` (new, committed
  earlier as 6773eeb) — first canonical project-skeleton template
- `src/wonderland/agent.py` — `max_tool_iterations: int = 20` (was 10),
  diagnosed via the parser-preview improvement landed in 6a68c04
- `src/wonderland/parsing.py` — error message includes 200-char preview
  + length of the LLM's actual response on `no JSON block found`
**Run transcripts + artifacts:**
- [Session 1 run.log](./data/020-multi-session/session1/run.log)
- [Session 1 wonderland snapshot](./data/020-multi-session/session1/wonderland-snapshot/) — registries + memory after Session 1
- [Session 1 team-diff.patch](./data/020-multi-session/session1/team-diff.patch) — 900-line backend diff against the seed
- [Session 2 run.log](./data/020-multi-session/session2/run.log)
- [Session 2 wonderland snapshot](./data/020-multi-session/session2/wonderland-snapshot/) — registries + memory after Session 2
- [Session 1 script](./data/020-multi-session/test_t38_session1.py)
- [Session 2 script](./data/020-multi-session/test_t38_session2.py)
**Comparison baselines:**
- [analysis 018](./018-the-breakthrough.md) — T36 single-session greenfield
- [analysis 019](./019-security-recovery.md) — T37 single-session reactive
- This analysis: T38 multi-session reactive-on-prior-session

> Two sessions ran on the same `project_root` and the same
> `.wonderland/` directory. Session 1 (translation chat MVP on the
> fullstack template) shipped 870 lines of backend code in $1.55.
> Session 2 (user-blocking on top of Session 1's work) designed a
> coherent extension — 3 stories, 4 tickets, 5 contract notes (via
> the same registry whose numbering continues from 8 → 11), 1
> Caterpillar review — but shipped 0 source files. The reason: the
> tools loop hit `max_tool_iterations=10` while the Tweedles were
> reading existing code, and the loop bailed before they could emit
> their final JSON response. The diagnostic preview surfaced this
> ("`preview: '<empty string>'`"); the cap is now 20.
>
> **The compounding shape is real and visible on disk.** Same
> registry, continuous numbering across sessions, Rabbit citing
> Session 1 endpoints by name in his Session 2 tickets, Cat
> correctly *not* shipping a redundant ADR for blocking. Memory
> works at the artifact-and-citation layer — that's the
> load-bearing thesis claim. What it doesn't yet drive is the
> Tweedles' `write_file` behavior in continuation sessions, which
> is the next iteration's target.

---

## Why this matters

T36 (analysis 018) and T37 (analysis 019) ran the team in single
sessions — fresh `.wonderland/`, fresh memory each time. That's
enough to test "identity does the work *within* a session" but
doesn't speak to the harder thesis claim: that constitutions plus
persistent registries produce *compounding judgment* across
sessions. P7's eval is supposed to show a measurable curve: per-
session cost flattens as memory accumulates; per-session output
gets richer as agents reach for prior decisions instead of
re-deriving.

T38 is the first showcase where that compounding can be measured.
The simplest design: same `project_root`, same `.wonderland/`,
multiple sessions on adjacent features. Session 1 builds the MVP;
Session 2 adds a feature that *should* reach for Session 1's
decisions; Session 3 (planned, not yet run) responds to an
incident that touches both prior sessions' work.

This analysis covers Sessions 1 and 2 with a partial result — Session
2 designed cleanly but didn't ship code. The diagnosis is in hand;
the validation rerun is the work the next analysis covers.

## Setup

Two substrate pieces from earlier commits:

1. **`src/wonderland/templates/fullstack-fastapi-react/`** (committed
   6773eeb) — a working hello-world FastAPI + SQLAlchemy + SQLite +
   React + Vite + TypeScript app. ~600 lines of plausible-looking
   real code with a `/health` endpoint, `/api/messages` echo flow,
   one-message React UI, baseline pytest coverage. Smoke-tested:
   `pip install -e ".[dev]" && pytest` → 4/4 passing in 0.03s.
   The team builds features ON TOP of this skeleton rather than
   inventing the stack from a vague directive.

2. **Pre-seed pattern from T37** — `_seed_template_into(project_root)`
   copies the template into the project root, runs `git init`, and
   commits the seed as the initial git state. The team's
   `write_file` calls show as a clean diff against the seed
   baseline; Caterpillar's `git_diff HEAD` is exactly what shipped.
   The helper is idempotent on `.git` existing — Session 2 reuses
   the project root, sees `.git` already present, and skips the
   copy + commit. This is what makes multi-session continuity work.

Default `project_root` is `/tmp/t38-multi-session/` so re-running
the same script targets the same directory. The `.wonderland/` lives
inside `project_root` (per the framework's standard layout), so
preserving the project root preserves all registries + episodic
memory across sessions.

## Session 1: translation chat on the fullstack seed

Same shape as the T36 enchilada (5-meeting flow: scoping →
decomposition → contracts → implementation → review). The directive
explicitly tells the team the codebase exists and to read it first.

**Result:** $1.55 / 150 calls / 17min, 870 insertions / 47 deletions
across 5 backend files.

The team:
- Replaced the placeholder `HelloMessage` model + `/api/messages`
  echo with a real translation-chat backend (12045-byte
  `messages.py` with conversation routing, translation status
  state machine, audit trail logic)
- Extended `models.py` from 1188 → 6757 bytes (real translation
  models on top of the seed's `Base`)
- Added `src/backend/api/users.py` (137-line user surface)
- Factored out `src/backend/api/schemas.py` (2290 bytes) — the
  team noticed the value of separating Pydantic schemas from
  endpoint handlers without being told to
- Extended `tests/test_messages.py` from 633 → 8277 bytes
- Wired the new users router into `src/backend/api/__init__.py`

3 Caterpillar reviews + 6 mark_agreed contracts + 2 ADRs + 2
implementation declarations.

Frontend untouched — Tweedledee parse-errored repeatedly. The
asymmetry is real but didn't block the substantive backend work.

**Why this is a good Session 1 baseline:** the source tree is
in a state Session 2 can extend. There's a real `Conversation`
schema, a real `messages` endpoint, a real `users` surface — all
named entities the next session can reach for. The
`.wonderland/` registry has artifacts numbered 1–8 (contract
notes), 1–3 (reviews), 1–2 (ADRs), 1–6 (tickets). The next
session inherits all of it.

## Session 2: user-blocking on top of Session 1

Same project root. `.wonderland/` carries forward. Working tree
carries forward (Session 1's changes are uncommitted but on disk).
The directive says explicitly:

> THIS IS A CONTINUATION SESSION — the translation-chat backend
> was built in a prior session and lives in the working tree. The
> team's memory carries over: every story, ADR, contract note,
> implementation, and review from the prior session is in your
> registries. Reach for them by name (ADR-001, ADR-002,
> contract-note-001 through 008, review-001 through 003) when
> they're load-bearing for the new work.

Same 5-meeting shape as Session 1 with directives at each meeting
flagging the continuation.

**Result:** registries grew, code didn't ship.

What landed:
```
+ stories/  4–6 (blocking-themed)
+ tickets/  7–10 (block schema, block visibility on
            existing endpoint, block/unblock endpoints,
            audit-trail-integrated-with-translation-logging)
+ contract-notes/  9, 9, 10, 10, 11 (numbering collisions on
            9 and 10 — concurrent-write bug in the registry)
+ reviews/  4 (backend-block-unblock-state-machine-and-api)
```

What didn't:
```
0 implementations declared
0 source files modified in Session 2
```

## The compounding evidence

This is the load-bearing finding. Three signals visible on disk:

### 1. Registry numbering continues across sessions

The contract-notes directory after Session 2:

```
contract-note-001-message-envelope-original-translated-fields-with-status.md  ┐
contract-note-002-polling-behavior-refresh-interval-and-update-detection.md    │
contract-note-003-language-display-logic-which-text-renders-to-sender-vs-receiver.md  │
contract-note-004-translation-failure-visibility-and-error-propagation.md      │ Session 1
contract-note-005-message-envelope-dual-language-display-with-translation-status.md   │
contract-note-006-polling-contract-get-conversations-id-messages-returns-all-messages-with-status.md  │
contract-note-007-optimistic-render-timing-message-appears-immediately-translation-arrives-async.md   │
contract-note-008-translated-text-nullability-semantics.md                     ┘
contract-note-009-block-visibility-enforcement-in-message-api.md               ┐
contract-note-009-conversation-participants-block-state-schema.md               │
contract-note-010-blocked-conversation-visibility-in-ui.md                      │ Session 2
contract-note-010-message-fetch-block-enforcement-visibility-filter.md          │
contract-note-011-block-semantics-one-way-mutual-send-and-receive.md            ┘
```

The registry counted 8 → 9 → 10 → 11 across sessions. Same goes for
stories (1–3 → 4–6), tickets (1–6 → 7–10), reviews (1–3 → 4). The
agents weren't told "use the next number"; they reached for the
registry's `next_number()` and got continuation.

The duplicate `009` and `010` filenames are a separate concurrency
bug — when both Tweedles propose contract notes simultaneously,
both get assigned the same next number. Worth filing for fix; not
a defeat of the persistence claim, just a registry-write race.

### 2. Tickets cite Session 1 endpoints by name

Rabbit's Session 2 tickets:
- `Backend: Extend Conversation schema with participant block state`
  — *extend*, not *create*; references the existing Conversation schema
- `Backend: GET /conversations/{id}/messages enforces block visibility`
  — references the EXACT endpoint Tweedledum built in Session 1
- `Backend: Block enforcement audit trail integrated with translation
  logging` — connects to Session 1's translation event audit work

Without persistence, Rabbit would have ticketed against an imagined
schema. With persistence, he ticketed against the actual one.

### 3. Cat declined a redundant ADR

Session 1 produced ADR-001 (asymmetric translation state machine)
and ADR-002 (dual-language display + polling sync). The Session 2
directive explicitly told Cat: "weigh in only if blocking implies
a fresh architectural decision ADR-001/002 don't already cover. If
extending an existing ADR is enough, say so explicitly — don't
ship a redundant ADR."

Cat shipped no ADR in Session 2. The architectural picture was
already settled enough; blocking is a feature on top, not an
architectural commitment requiring a new record. This is exactly
the "characterful refusal to over-produce" the constitution names
(§VII forbids redundant ADRs).

The compounding here is in *what wasn't shipped*. A fresh-memory
Cat would have re-derived a translation architecture and shipped
ADR-001-of-this-session. The persistent-memory Cat said "I've
already shipped that; nothing changed."

## What didn't happen — and why

Session 2 designed cleanly through M2 (tickets) and into M3
(contract notes) and M5 (review), but **shipped no code in M4**.
The diagnostic preview improvement (commit 6a68c04, parsing.py)
revealed two distinct failure modes from the LLM responses that
parse-errored:

```
preview: '<empty string>' (len=0)
```
→ `_complete_with_tools` returned `""` after exhausting
`max_tool_iterations=10` without a non-tool-use stop. The Tweedle
called tools 10+ times in a row (read_file existing models.py,
read_file messages.py, read_file users.py, list_files src/, etc.)
and the loop bailed before the LLM produced its final JSON
response. **Continuation-session Tweedles legitimately need more
reads than greenfield Tweedles**: they have to understand what
already shipped before designing the diff. The cap of 10 was
calibrated for greenfield work where the Tweedle reads at most
2-3 files before writing.

```
preview: "Now I'll update the messages.py endpoint to add block
          operations and enforce block visibility..." (len=128)
```
→ LLM emitted prose narration without producing JSON. Different
failure: the model "thought" it was about to do more tool work
but stopped with a non-tool-use stop_reason and emitted a
narrative sentence instead of the schema. This is a protocol-
adherence drift, not iter exhaustion — needs a separate fix
(probably a sharper "your final response MUST be JSON" nudge
in the protocol when the LLM has already done several tool
calls in a turn).

**Fix in this commit:** `max_tool_iterations: int = 20` (was 10).
The toolset (read/write/list/grep/git_status/git_diff) is local-
only with no network or process-spawning paths; risk of feedback
loops is low. Worst case is verbose exploration, not infinite
loops. The protocol-drift fix is deferred to the next iteration.

## What this validates about the thesis

**Memory compounds at the artifact-and-citation layer.** The
persistence machinery (registries, episodic memory, relational
memory, compaction) — all of which already existed before T38 —
genuinely produces continuation behavior:
- Registries number across sessions
- Agents reach for prior artifacts by name
- Architectural over-production is suppressed (no redundant ADR)
- Decomposition references existing surface, not invented surface

This is the harder thesis claim that T36 and T37 couldn't speak
to. Single-session showcases test "identity does the work within
a session." T38 tests "identity-plus-persistence does the work
across sessions."

**Memory does NOT yet drive `write_file` behavior in continuation
sessions.** Reading the existing code is what blocked us — the
team correctly explored before designing, but the substrate
budget for that exploration was too tight. This is a substrate
calibration finding, not a thesis defeat. With the bumped cap,
the next run should see Session 2 ship the block code as a
focused diff.

## What's still incomplete

For the planned T38 follow-up:

1. **Validate the iter-bump fix** — re-run Session 1 + Session 2
   from a clean `project_root` with the bumped cap. Confirm
   Session 2 ships actual code and the diff is small/focused
   (extending, not rewriting).

2. **Inter-session git-commit step** — Session 1's modifications
   were uncommitted between sessions, which left Session 2's
   reviewer (Caterpillar) unable to distinguish "Session 1's
   changes" from "Session 2's changes" in `git_diff HEAD`. Add a
   commit step at end of each session so the next session's diff
   is clean.

3. **Registry concurrent-write bug** — contract-note-009 and -010
   each have two files. The `next_number()` call doesn't take a
   lock; concurrent Tweedle writes get the same number. Worth a
   small fix (file-system lock or sequential allocation through a
   single writer).

4. **Protocol nudge for prose-without-JSON** — the 128-char
   "Now I'll update..." preview. The LLM hallucinated continuation
   intent without producing the structured response. A protocol
   line like "If you have already made one or more tool calls in
   this turn AND the LLM API tells you you're at the iter limit,
   your next response MUST be the final JSON; further tool calls
   will be discarded" might address it.

5. **Session 3** — incident-response on top of two sessions of
   work. Tests both whether persistence holds across multiple
   sessions and whether reactive (T37-shape) work composes with
   continuation context.

## Files touched

```
src/wonderland/agent.py                      # max_tool_iterations 10 → 20
                                              # (parsing.py preview already in 6a68c04)
analyses/020-multi-session-persistence.md    # this writeup
analyses/data/020-multi-session/
  test_t38_session1.py                       # script snapshot
  test_t38_session2.py                       # script snapshot
  session1/run.log                           # full transcript
  session1/wonderland-snapshot/              # post-S1 registries+memory
  session1/team-diff.patch                   # 900-line clean diff
  session2/run.log                           # full transcript
  session2/wonderland-snapshot/              # post-S2 registries+memory

# Already committed in earlier commits:
src/wonderland/templates/fullstack-fastapi-react/  # 6773eeb (the seed)
src/wonderland/parsing.py                          # 6a68c04 (preview)
```

The next iteration's analysis (021, planned) covers:
- Re-run with the iter bump from a clean state
- Inter-session commit handling
- Whatever Session 3 surfaces about long-arc memory effects
