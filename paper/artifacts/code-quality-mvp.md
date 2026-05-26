# Code quality analysis — mvp shipped artifact

> Source material for the paper's quality argument. The cost
> story is interesting; the cost-AT-quality story is the one
> that's novel. ~$84 of Haiku-class LLM time produced a working
> full-stack markdown notebook app that an independent senior
> reviewer (a fresh Claude instance with no Wonderland context)
> reads as *"competent, above-average code for an MVP"* with
> one real correctness bug and several legitimate concerns.
> This artifact pairs that independent review verbatim with
> our own quantitative metrics + pattern receipts.

---

## 1. Disposition (TL;DR)

Direct quote from the independent reviewer (full review in
[§5](#5-independent-cold-review-verbatim)):

> This is competent, above-average code for an MVP. Backend has
> notably good security discipline around LIKE-wildcard escaping
> and an over-engineered-but-thoughtful audit/revision design.
> Tests are unusually self-aware about edge cases. There are
> **no security blockers**, but there is one **correctness
> blocker** in the optimistic-concurrency layer that defeats the
> entire point of having it, and several **concerning** issues
> I'd want addressed before tagging v1: race-prone tag creation,
> unbounded recompute on hot paths, and a frontend that has
> overgrown its load-bearing component (`Editor.tsx` at 683
> lines). Ship it as a personal-use app today; do not ship it
> as a multi-user app without addressing the blocker.

The three punchlines worth pulling out of that disposition:

1. **No security blockers.** Notable for code produced
   autonomously by Haiku-class agents with operator
   participating only as gate-approver.
2. **Reviewer recommends shipping the artifact at the spec'd
   scope.** "Single user, no authentication" was the directive
   ([analysis 034](https://github.com/KohlJary/wonderland-ai/blob/main/src/wonderland/closet/analyses/034-mvp-demo2-autonomous-pilot.md));
   reviewer's verdict is ship-it-at-that-scope.
3. **Reviewer's blocker + concerning findings are
   latent-at-v1, acute-at-v2.** Both B1 (silent `If-Match`
   bypass) and C2 (revision_id serialization mismatch) live in
   the optimistic-concurrency layer. Single-user-no-auth means
   no concurrent writers, so neither bug gets exercised in the
   spec'd use case. The substrate built the infrastructure
   correctly enough for the scope; the bugs would become
   showstoppers only if scope grew to multi-user. We frame
   that distinction honestly in [§6](#6-honest-weaknesses--what-they-mean-for-the-substrate).

---

## 2. Quantitative metrics

### Code volume

| Bucket | LOC |
|---|---|
| Application total | 3,371 |
| └ Backend (Python) | 1,037 |
| └ Frontend (TypeScript / TSX) | 2,334 |
| Test code | 1,577 |
| **Test:code ratio** | **0.47** |

For an MVP, 47% test:code is solid. The substrate's TDD-shaped
workflow (Hatter's M6 failing-test phase paired with M7
implementation) was designed to produce this; it did.

### Surface area

| Surface | Count |
|---|---|
| API endpoints | 8 |
| Backend functions | 16 |
| Frontend exported functions / components | 19 |
| Pydantic models (request / response schemas) | 7 |
| SQLAlchemy tables (Note, Tag, AuditLog) | 3 |
| Total tests | 61 |
| └ Severity-tagged tests (Hatter's vocabulary) | 24 |

### Severity distribution across the 24 tagged tests

| Severity | Count |
|---|---|
| `curiosity` | 11 |
| `degradation` | 8 |
| `silent-wrongness` | 4 |
| `breakage` | 1 |
| `delight` | 0 |

The vocabulary is Mad Hatter's, defined in
`constitutions/mad_hatter.md` §II. Half of the 24 tagged tests
are at `silent-wrongness` or worse — the dangerous class of
bugs where the system appears to work but returns the wrong
thing. These tests exist *because* Hatter's M6 scenario design
generated them.

### Contract / ticket / ruling references in source

| File | References |
|---|---|
| `src/backend/api/notes.py` | 10 |
| `frontend/src/App.tsx` | 9 |
| `frontend/src/api.ts` | 6 |
| `src/backend/models.py` | 5 |
| `frontend/src/Editor.tsx` | 4 |
| `frontend/src/Search.tsx` | 2 |
| `frontend/src/NoteList.tsx` | 2 |
| `frontend/src/useBootNotes.ts` | 1 |
| **Total** | **39** |

Each reference is a citation back to a `contract-note-XXX`, a
`ticket-NNN`, or a `ruling-NNN` — the substrate's design
artifacts. **The same contract (`contract-note-01KRY0B8`)
appears in both backend `models.py` and frontend `api.ts`** —
the cross-ticket coherence Caterpillar's M8 review is
designed to enforce, visible in the wild as inline citations
on both sides of the seam.

### Comment density

- Backend: 67 explanatory comment lines (excluding docstrings)
- Frontend: 86 explanatory `//` comment lines

Comments are concentrated where contracts are non-obvious or
where past bugs are being explicitly guarded against (see §3).
Not a comment-everything codebase; not a comment-nothing one.

---

## 3. Pattern receipts — what's genuinely good

Five patterns the cold reviewer called out for praise; we'll
include line citations + the reviewer's exact wording where
applicable.

### 3.1. SQL LIKE-wildcard escaping with anti-bypass discipline

Reviewer's framing: *"exemplary. … I almost never see this
discipline outside hardened codebases."*

In `demo/mvp/src/backend/api/notes.py:196-220`:

```python
def _escape_like_pattern(s: str) -> str:
    """Escape SQL LIKE metacharacters (%, _) so they are treated as literals.

    CRITICAL: The pattern returned by this function MUST be used with a
    LIKE comparison that specifies escape='\\' (double-backslash in Python string).
    If the escape parameter is omitted, the escaping is ineffective and user input
    containing % or _ will be treated as SQL wildcards — this is a correctness bug
    and a security issue.

    DO NOT call this function and then use .ilike() without escape='\\'.
    Use the _safe_ilike() helper instead to enforce this contract at the call site.
    ...
    """
```

And the contract-enforcement helper at `notes.py:223-246`:

```python
def _safe_ilike(column, pattern: str):
    """Helper to apply LIKE comparison with automatic escape character enforcement.

    Wraps SQLAlchemy's .ilike() to enforce the contract that escaped patterns
    (from _escape_like_pattern()) MUST be used with escape='\\'.

    This prevents the bug where a caller forgets to include escape="\\" in the
    ilike() call, causing % and _ in user input to become wildcards.
    ...
    """
    return column.ilike(pattern, escape="\\")
```

What makes this paper-grade evidence:

- It's not just "the team escaped LIKE wildcards." It's
  *"the team escaped LIKE wildcards AND noticed that the
  natural calling convention has a silent-footgun shape AND
  built a helper to enforce the contract at the call site
  AND wrote a docstring explaining the failure mode AND
  shipped tests that assert the bug class is prevented."*
- The class of bug this prevents (search for `100%`
  returning `100 percent` because `%` is a wildcard) is the
  kind of subtle correctness issue most teams ship and only
  notice when a user complains.
- The discipline is uncharacteristic of code produced under
  cost pressure — and the test budget for this feature was
  ~$26 (M1 design + implementation).

This pattern's origin: a Hatter `test_scenario` shipped during
M6 of the search feature, which became `test_search_wildcard_issues.py`
(see §3.5 below) — the scenario was written first; the
implementation came later.

### 3.2. Timezone-aware datetime normalization

Reviewer's framing: *"rigorous. … handles naive datetimes
(SQLite reality), aware datetimes, and missing values, and
emits ISO8601 with a `Z` suffix instead of `+00:00`."*

In `demo/mvp/src/backend/models.py:114-131`:

```python
def ensure_tz_aware(dt: datetime | None) -> str:
    """Convert datetime to UTC ISO8601 string with Z suffix.

    If dt is naive (no tzinfo), assume UTC.
    If dt is aware, convert to UTC.
    Always returns ISO8601 with explicit Z suffix for UTC.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    elif dt.tzinfo is None:
        # Naive datetime: assume UTC (SQLite doesn't track tz)
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        # Timezone-aware: convert to UTC
        dt = dt.astimezone(timezone.utc)

    # Return ISO8601 with Z suffix for UTC (replaces +00:00)
    return dt.isoformat().replace("+00:00", "Z")
```

The inline comment *"SQLite doesn't track tz"* names the
specific failure mode the code is guarding against — SQLite
stores datetimes as naive ISO strings, and code that assumes
SQLAlchemy returns tz-aware datetimes for a
`DateTime(timezone=True)` column gets bitten across SQLite vs
Postgres deploys. The fix here is correct: assume UTC for
naive, convert explicitly for aware, normalize on output.

(Foreshadowing §6: this exact helper is ALSO where the
substrate's one real correctness bug lives — `ensure_tz_aware`
isn't used everywhere it should be, and the inconsistency
produces divergent revision_ids for the same logical state.
The fact that the helper exists is good; the fact that it's
not the only path datetimes take to the hash function is the
bug.)

### 3.3. Markdown sanitization before `dangerouslySetInnerHTML`

In `demo/mvp/frontend/src/Preview.tsx:25-56`:

```typescript
export function Preview({ body }: PreviewProps) {
  // Parse markdown and sanitize HTML once per body change
  const htmlContent = useMemo(() => {
    if (!body || body.trim() === '') {
      return '';
    }
    try {
      const rawHtml = marked(body);
      const cleanHtml = DOMPurify.sanitize(rawHtml);
      return cleanHtml;
    } catch (err) {
      // Malformed markdown: show error inline, not as crash
      console.error('Markdown parse error:', err);
      return `<p style="color: #999; font-style: italic;">Error parsing markdown</p>`;
    }
  }, [body]);

  return (
    <div
      className="preview"
      dangerouslySetInnerHTML={{ __html: htmlContent }}
      ...
    />
  );
}
```

The only use of `dangerouslySetInnerHTML` in the codebase is
guarded by `DOMPurify.sanitize()` — the correct pattern.
The try/catch around `marked()` prevents a malformed-markdown
crash from killing the editor. Each invariant is named in the
file's header docstring:

```typescript
 * Security: uses DOMPurify to sanitize HTML and prevent XSS.
 * ...
 * Invariants:
 * - all HTML is sanitized before rendering (no XSS)
 * - empty body renders as empty div (no error state)
 * - malformed markdown gracefully degrades (renders what it can parse)
```

XSS-defense-as-stated-invariant. This is Queen of Hearts'
`ruling` shape (security with citation + remediation) made
flesh in the source.

### 3.4. Custom hooks (not inlined effects)

The codebase has two named, single-responsibility custom hooks:
`useLocalStorageDebounce` and `useBootNotes`. Both are extracted
into their own files. `useLocalStorageDebounce.ts` (44 lines)
shown in full:

```typescript
import { useEffect, useRef } from 'react';

/**
 * useLocalStorageDebounce — manages debounced localStorage writes
 *
 * Usage:
 *   const debouncedWrite = useLocalStorageDebounce('key', 300);
 *   debouncedWrite({ title: 'foo', body: 'bar' });
 *
 * The hook debounces writes so that fast keystrokes don't thrash the storage.
 * Each call resets the debounce timer; the write happens 300ms after the last call.
 * ...
 */
export function useLocalStorageDebounce<T>(key: string, delayMs: number = 300) {
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, []);

  return (value: T) => {
    // Clear existing timer
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }

    // Set new timer
    timerRef.current = setTimeout(() => {
      try {
        localStorage.setItem(key, JSON.stringify(value));
      } catch (err) {
        console.error(`Failed to write to localStorage[${key}]:`, err);
      }
    }, delayMs);
  };
}
```

Notable for a small hook: cleanup on unmount, try/catch around
storage writes (handles QuotaExceededError gracefully),
generic-typed value, documented usage example, configurable
delay with sensible default. This is the kind of helper a
senior dev would extract on day three of a project; the
Tweedles extracted it as part of feature 1.

### 3.5. Tests as scenario documentation (the Hatter pattern)

`demo/mvp/tests/test_search_wildcard_issues.py:1-15` (the file's
header):

```python
"""Tests for LIKE-wildcard escaping in search queries.

Hatter's scenario exploration: SQL LIKE metacharacter (%, _) handling.

Severity: silent-wrongness
- User searches for literal %, expects to find notes containing %
- Current implementation treats % as a wildcard, returning wrong results
- No error raised; results are silently incorrect
- Affects search correctness and data integrity

Related scenario artifact: scenario-01KRXVFV-text-search-ignores-special-characters-sql-injection-boundary.md
"""
```

And the first test, lines 14-50:

```python
def test_search_with_percent_sign_as_literal_wildcard_bug(client):
    """
    GET /api/search?q=100% should find only notes containing literal '100%'.

    CURRENT BUG: The implementation uses ilike() without escaping LIKE metacharacters.
    % is a SQL LIKE wildcard (matches zero or more chars).

    So searching for '100%' actually searches for LIKE '%100%%' (after adding %% padding),
    which matches '100' followed by anything, not just literal '100%'.

    Examples:
    - '100% complete' — matches (correct by accident)
    - '100 percent' — matches (WRONG — should not match, % doesn't occur literally)
    - 'My 100 apples' — matches (WRONG — should not match)

    Severity: silent-wrongness. User gets wrong results without error message.
    """
```

This is literally the Mad Hatter constitution made flesh in
actual code. A test_scenario shipped during M6 — citing its
scenario artifact GUID, naming severity, demonstrating the bug
*before* the fix existed. The test was written first; the
escape helpers in §3.1 came second; the test passes now
because the implementation handles the case. **Red-green TDD
captured in the test file itself.**

The reviewer called this file *"the standout"*:

> `test_search_wildcard_issues.py` is the standout. It actively
> asserts the absence of a class of silent-wrongness bug
> (LIKE-wildcard leakage), with comments documenting what the
> bug *would* look like. This is regression-test discipline I
> respect.

### 3.6. App entry point wiring (cross-ticket coherence in the wild)

`demo/mvp/frontend/src/App.tsx` correctly imports + mounts every
component the design produced — Editor, NoteList, Search,
EditorLayout — and wires them through view-state switching with
URL pathname sync. The header docstring enumerates the
contracts each section honors:

```typescript
 * Contracts:
 * - ticket-007: Editor pane with title input, markdown body editor, keystroke buffer
 * - ticket-013: Search UI component with text input, tag filter, pagination
 * - ticket-037: Add search route and wire navigation to search view
 * - contract-note-01KRXRTT: Note model and CRUD endpoint contract
 * - search endpoint shape: GET /api/search?q=...&tags=...&page=...&page_size=...
 * - ticket-066: Frontend load-on-boot and localStorage merge reconciliation
 * - ruling-012: Merge strategy for offline localStorage vs. backend on app boot (OPTIMISTIC)
```

This is what passes Caterpillar's M8 cross-ticket coherence
check: every component referenced in the design is actually
imported, rendered, and reachable from the entry point. The
mvp-demo (first pilot) failed M8 in two places with
orphaned components; mvp doesn't.

---

## 4. Anti-pattern absence audit

Quantitative grep pass for the standard anti-pattern classes:

| Anti-pattern | Found? | Notes |
|---|---|---|
| Hardcoded secrets / API keys / passwords | **None** | grep'd for `(api[_-]?key\|secret\|password\|token)\s*=\s*[\"'][^\"']{8,}` — zero hits. `DATABASE_URL` is env-driven. |
| `eval` / `Function()` / dynamic code | **None** | The only `regex.exec` use is the legitimate regex API in `Search.tsx:74`, with input escaped before construction. |
| SQL string concatenation / injection | **None** | All queries use SQLAlchemy ORM with parameter binding. LIKE patterns explicitly escaped (§3.1). |
| Bare `except:` clauses | **None** | All except clauses name a specific exception. |
| `dangerouslySetInnerHTML` without sanitization | **None** | The one usage (`Preview.tsx:45`) is DOMPurified (§3.3). |
| TODO / FIXME / XXX / HACK markers | **One** | `models.py:39` — and that one is tracked to `ticket-081` (revision_id caching), not orphaned. |
| Global mutable state | **None (production code)** | `app.dependency_overrides` in `conftest.py` is test-only and properly cleared after each test. |
| Dead code (unused exports) | **None per reviewer** | "Every export is used." |
| Wildcard CORS | **No** | `main.py:29` restricts `allow_origins` to `http://localhost:5173`. |

The audit's significance: not just "no critical anti-patterns"
but *"the team's choices reflect awareness of the anti-patterns
they're avoiding"* — env-driven secrets, named exception types,
sanitization-before-injection, tracked TODOs.

---

## 5. Independent cold review (verbatim)

The rigor move: we asked an independent Claude instance — fresh
context, no Wonderland background, dropped into `demo/mvp/` cold —
to do a senior code review. The instruction was to underclaim
if anything, lead with what matters most, name concrete
file:line citations, and treat the output as professional
review that would be quoted verbatim in a research artifact.

What follows is the reviewer's report. We've edited only for
formatting; the findings are intact.

---

### 5.1. Praise

- **LIKE-wildcard escaping is exemplary.** `_escape_like_pattern`
  (`notes.py:196-220`) escapes `\` before `%`/`_` in the right
  order, and the author noticed that `ilike()` without
  `escape='\\'` is a silent footgun and built `_safe_ilike`
  (`notes.py:223-246`) to enforce the contract at the call
  site. The accompanying docstring explicitly names the failure
  mode. I almost never see this discipline outside hardened
  codebases. The `test_search_wildcard_issues.py` file actively
  tests for the bug class being prevented.

- **Markdown is sanitized.** `Preview.tsx:33` runs `marked()`
  output through `DOMPurify.sanitize()` before injecting via
  `dangerouslySetInnerHTML`. The `try/catch`
  (`Preview.tsx:31-40`) prevents a malformed-markdown crash
  from killing the editor. This is the right pattern.

- **Highlight rendering escapes regex metachars.**
  `Search.tsx:65` `query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')`
  before constructing `new RegExp(...)`. A user search for `(`
  doesn't blow up. Small thing, easily forgotten, done
  correctly.

- **Timestamp normalization is rigorous.** `models.py:114-131`
  `ensure_tz_aware` handles naive datetimes (SQLite reality),
  aware datetimes, and missing values, and emits ISO8601 with
  a `Z` suffix instead of `+00:00`. The contract is asserted
  in `test_notes_edge_cases.py:266-280`.

- **Deterministic ordering on ties.**
  `Note.updated_at.desc(), Note.id.desc()` (`notes.py:360`,
  `:675`) — sub-second test inserts will produce identical
  timestamps and the secondary sort prevents non-deterministic
  pagination.

- **Tag-name normalization is centralized.**
  `_normalize_and_validate_tag_names` (`notes.py:249-279`)
  strips whitespace, rejects empty, dedupes; both
  `POST /api/notes` and `POST /api/notes/{id}/tags` route
  through it. No drift.

- **Test fixtures are clean.** `conftest.py` uses an in-memory
  SQLite with `StaticPool` and FastAPI's `dependency_overrides`
  — every test gets a fresh DB without disk I/O. This is the
  right pattern; I've seen teams botch it badly.

- **CORS is scoped, not `*`.** `main.py:29` restricts
  `allow_origins` to `http://localhost:5173`.

- **Edge-case test file exists and is honest.**
  `test_notes_edge_cases.py:14-54` documents the
  empty-array-clears-tags behavior with a comment asking "is
  this intended or a bug?" rather than asserting it's correct.

### 5.2. Blocker

**B1.** The collision-detection contract is silently bypassed
when the client omits the `If-Match` header. `notes.py:443`:

```python
if if_match is not None and if_match != current_revision_id:
```

If the client sends no header, the update proceeds with no
check — the contract docstring (`notes.py:421`) calls this
"backward-compatible for v1 single-user scope." This means a
buggy or stale client that simply forgets the header gets the
silent-overwrite behavior the whole revision_id machinery is
supposed to prevent. The audit log is all infrastructure built
to detect this scenario, and the API hands attackers /
buggy-clients an opt-out. For a personal single-user app this
is "fine"; for anything multi-user, **this defeats the entire
feature**. Either require `If-Match` on PUT (415/428) or
document it loudly as "advisory in v1." Right now it's
neither.

### 5.3. Concerning

**C1.** Tag auto-creation has a TOCTOU race.
`_associate_tags` and `associate_tag` both do
`SELECT … WHERE name = ?` then `INSERT` if absent.
`Tag.name` has `unique=True` (`models.py:159`) so two
concurrent requests creating the same tag will hit a SQLite
`IntegrityError` and return a 500.
`test_concurrent_tag_creation_same_name_explicit_handling`
admits it does not actually test concurrency. With SQLite +
uvicorn the window is narrow, but it's still a real bug.
Fix: `INSERT … ON CONFLICT DO NOTHING` and re-select, or
catch `IntegrityError` and retry.

**C2.** `revision_id` is recomputed for every note on every
list call, AND **different endpoints produce different
revision_ids for the same logical state**. `compute_revision_id`
reads `updated_at` from `to_dict()` in `list_notes`, which
serializes via `ensure_tz_aware` (Z suffix), while `read_note`
and `update_note` pass `note.updated_at.isoformat()` (`...000Z`
vs raw naive ISO without suffix). The two paths produce
different strings for the same datetime, and therefore
different revision_ids for the same note state depending on
which endpoint surfaced it. A client doing `GET /api/notes` to
populate a list and then `PUT /api/notes/{id}` with the cached
revision_id will get a spurious 409. **Requesting changes:**
unify on one serialization helper.

**C3.** `Editor.tsx` is 683 lines and conflates six
responsibilities. Load, save, boot reconciliation, save-time
conflict resolution, localStorage debouncing, and ~200 lines
of inline `styles`. It has two parallel conflict-state
machines (`bootConflict` / `saveConflict`), each with their
own handlers. Extract `useEditorState`,
`useBootReconciliation`, `useSaveConflict` hooks; move styles
to a CSS module.

**C4.** Frontend/backend contract drift on `body_preview`.
Backend truncates to 100 chars (`notes.py:690`); frontend
`api.ts:44` comment says "First 150 chars of body". Runtime
works (server is authoritative) but type-level comments lie.
Minor in isolation, **concerning** as a signal that contract
sync isn't being enforced.

**C5.** `Editor.tsx` `useEffect` runs on every parent
re-render — `useEffect(..., [noteId, onBodyChange])`. Stable
across current callers, but fragile.

**C6.** `Editor.tsx` revision_id restored from localStorage
contradicts the file's own invariant docstring.

**C7.** `Search.tsx` has two `useEffect`s that race — patched
with a guard but design is fragile.

**C8.** `DATABASE_URL` defaults to `sqlite:///./app.db`
(relative path) — multiple invocations from different CWDs
silently use different databases.

### 5.4. Test quality

> The 61-test count is a fair description but undersells
> variation in depth.
>
> **Genuinely good:** `test_search_wildcard_issues.py` is the
> standout — regression-test discipline I respect.
> `test_tag_scenarios.py` has narrative scenario comments and
> explicit severity tags. `test_notes_edge_cases.py:14-54`
> documents `tag_names=[]` clears-vs-preserves ambiguity
> rather than rubber-stamping it.
>
> **Gaps:**
> - **No frontend tests.** `package.json:11` has a `vitest`
>   script and `vitest` dep but `find` returns zero `.test.*`
>   files. The conflict-resolution state machine in `Editor.tsx`
>   is the highest-risk code in the repo and has no tests.
>   **This is the biggest single gap.**
> - **No PUT/collision tests.** The most-engineered piece of
>   the backend (revision_id + audit log) has effectively no
>   behavioral coverage. **C2** above would have been caught
>   by such a test.
> - **No test of the no-If-Match bypass** (B1). The "advisory
>   in v1" semantics are undocumented and untested.
> - **No concurrency tests** (C1 would surface).
> - **Audit-log tests are absent.** The `AuditLog` model has
>   tamper-detection fields (`state_hash`), JSON-encoded
>   snapshots, and collision-state semantics. Zero tests
>   verify any of this.
>
> **Test infrastructure is solid.** `conftest.py` is the
> right shape.

### 5.5. Reviewer's overall disposition

> I would request changes before approving a v1 tag, with
> **B1** and **C2** as required, **C1/C3/C7** as strongly
> preferred, the rest as follow-ups. The code is better than
> I expected from a "small starter app" and shows real
> engineering taste in the search-escaping and
> timestamp-normalization layers. The weakest link is that
> the most sophisticated piece — the revision_id/audit-log
> subsystem — is also the least tested and contains the one
> real correctness bug.

---

## 6. Honest weaknesses + what they mean for the substrate

Three reviewer findings deserve specific framing for the
paper because each illustrates *where the substrate reaches
and where it doesn't*. This is the credibility-making
section: we surface our own failure modes before a reader
finds them.

### 6.0. Scope-honesty preface

The directive specified single-user, no-authentication, local
SQLite. The reviewer's blocker (B1) and most pointed concern
(C2) both live in the optimistic-concurrency layer —
infrastructure that **only gets exercised under concurrent
writers**, which the spec'd scope doesn't have. Both findings
are latent at v1 and would become acute at v2.

- **Latent at v1:** the code runs the spec'd use case
  correctly. No user trips either bug.
- **Acute at v2:** if the app gained multi-user scope, B1
  would silently overwrite concurrent edits and C2 would
  produce spurious 409 Conflicts on the natural list →
  click-to-edit → save flow.

That's not us excusing the bugs — they're real, and the
reviewer was right to flag them as the most important
findings. It's framing them accurately: the substrate built
optimistic-concurrency infrastructure (which is meaningful —
mvp-demo's pilot didn't build any) and the infrastructure has
shape-correct design with implementation bugs that the v1
scope doesn't exercise. The bugs are evidence about substrate
limits, not about whether the shipped artifact works.

### 6.1. B1: silent `If-Match` bypass — failure mode of the operator's gate

The "advisory in v1, required later" semantics is a design
decision the substrate didn't catch as ambiguous because
**there was no point in the workflow where someone was asked
"is the optimistic-locking enforcement required or advisory?"**
The Queen's M4 ruling could have surfaced this; she didn't —
likely because the team didn't frame it as a security-domain
choice. The operator was gate-approver at the feature level,
not at the contract-clause level, so this slipped through.

The substrate did the right design-shape thing: the
implementation honors `If-Match` when sent and includes the
audit-log machinery to record collisions. It just left the
"is the header required?" question implicit. For single-user
scope, implicit is fine. For multi-user scope, implicit is
a security bug.

**Implication for the substrate:** a Queen ruling pass with
explicit "what's required vs advisory?" prompts on auth /
optimistic-locking / rate-limiting features would catch this
class. Filed as future work in the b3f440c8 cluster.

### 6.2. C2: cross-endpoint serialization mismatch — failure mode of M8 static review

The most pointed reviewer concern, and worth examining
carefully because it's the canonical M8-blindspot pattern.
The relevant code:

```python
# list_notes — uses to_dict()'s Z-suffix path
note_dict = note.to_dict()
revision_id = compute_revision_id(
    note.title, note.body, tag_ids,
    note_dict["updated_at"],  # ensure_tz_aware → ISO8601 with Z
)

# read_note + update_note — use raw isoformat() with no Z handling
revision_id = compute_revision_id(
    note.title, note.body, tag_ids,
    note.updated_at.isoformat(),  # naive ISO from SQLite
)
```

Both functions read correctly in isolation. The bug only
manifests when a client uses a revision_id obtained from one
endpoint as the `If-Match` header for another — and Caterpillar's
M8 review reads files for coherence, not behavioral
integration across endpoints. M9's verify step would catch this
*if* an integration test existed; the test gap and the
implementation gap reinforce each other.

**Implication for the substrate:** this is the canonical
class of bug that yields cheaply to integration testing but is
invisible to per-file review. M9's `pytest_passes` check
*could* catch it if Hatter's M6 had generated a scenario like
"client lists notes, picks one's revision_id, PUTs with that
revision_id, expects 200." Hatter generated scenarios for
search-escaping (which is why §3.1 + §3.5 are exemplary) but
not for revision_id round-tripping. Filed as future work:
**cross-endpoint scenario coverage as a first-class Hatter
generation prompt during M6**.

**Practical impact at v1:** none. Single-user means no
concurrent writers means no scenario where revision_id
mismatch matters. The optimistic-locking infrastructure exists
correctly-shaped but unexercised. If the app's scope expanded
to multi-user, this bug would surface as spurious 409
Conflicts on the natural list → click-to-edit → save flow.
Reviewer's "ship at v1 scope, fix before v2" disposition
captures this exactly.

### 6.3. C3 + frontend test gap — failure modes of substrate scope

`Editor.tsx` at 683 lines is the classic
single-component-grows-too-large pattern. The substrate had
no signal to split it — it shipped as one ticket, each
follow-up review added behavior to the same component, and no
agent has the responsibility of saying "this component should
become three." The Caterpillar's M8 review could
theoretically catch this as a "structural complexity" finding,
but the constitution prioritizes correctness + coherence over
size limits.

Similarly the frontend test gap: `vitest` is installed
(`package.json:11`) but zero tests are written. Hatter's M6
scenarios for frontend features did exist, but they got
documented as scenarios without being translated into runnable
frontend tests during M7 — the Tweedles' M7 directive doesn't
explicitly require frontend test execution, only that the
implementation make the scenarios true. This is a real gap.

**Implication for the substrate:** an M7 phase output
requirement of "the Hatter scenarios for this ticket exist as
runnable tests in the appropriate test directory" would close
the gap. Frontend test execution would need an `npm test`
build-check parallel to `pytest_passes` / `npm_build`. Filed
as future work.

### 6.4. Honest framing of the test count

The 61-test count is a real number — every test passes — but
the reviewer's framing is the more accurate read: the tests
are unusually self-aware about the bugs they're guarding
against (the Hatter-scenario pattern), and the test
infrastructure is solid, but the most-engineered subsystem
(revision_id + audit log) has effectively no behavioral
coverage. We claim the 61-test number with the test:code
ratio (0.47) honestly; we don't claim "comprehensive
coverage."

---

## 7. What this demonstrates

Six claims the paper can make, each with the citations to
support it:

### 7.1. Quality at Haiku price-point

A small model (Haiku 4.5) with strong constitutions + a
substrate that enforces multi-lens review produces code an
independent senior reviewer (also Claude) describes as
*"competent, above-average code for an MVP"* with *"real
engineering taste in the search-escaping and
timestamp-normalization layers."* Cost: $83.78
([analysis 033](https://github.com/KohlJary/wonderland-ai/blob/main/src/wonderland/closet/analyses/033-mvp-demo2-cost-breakdown.md)).

The framing the paper should use: not *"Haiku can write
code"* (it can; everyone knows) but *"Haiku produces code with
discipline that the reviewer almost never sees outside hardened
codebases, at MVP cost"*.

### 7.2. The multi-lens-review thesis is operator-visible

This artifact's §3.1 (LIKE escaping with anti-bypass) and §3.3
(DOMPurify sanitization) and §3.5 (test_scenario as test) are
each multi-character outputs:
- Hatter's M6 scenario generation produced the test
- Queen's M4 ruling pass framed the security shape
- Caterpillar's M8 review caught earlier patterns where the
  contract wasn't enforced at the call site
- Tweedledum's M7 implementation built the helpers

No single character would have produced this discipline alone.
That's the architectural argument made concrete with code
receipts. Per memory:
`project_multi_lens_review_produces_quality_code.md` —
operator noticed this pattern unsolicited during the pilot.

### 7.3. The quality-cost coupling thesis is reinforced

Substrate fixes that improved output also reduced wedge waste.
mvp-demo had ~$5+ of dead-end run cost; mvp had ~$1.
Code quality observed by independent reviewer is genuinely
above-MVP-average; cost was $83.78 ($28 per effective
milestone). Per memory:
`project_quality_cost_inversion.md`.

### 7.4. Schema-as-safety prevents hallucinated review

The reviewer's praise for the helper functions
(`_escape_like_pattern`, `_safe_ilike`, `ensure_tz_aware`,
`_normalize_and_validate_tag_names`) cites specific behaviors
and lines. None of the praise is hallucinated — the code
exists at those lines doing those things. The schema-driven
discipline of cited findings (constitutions §V: review shapes
with location + quote + read + concern + request) means
Caterpillar's reviews ARE specific in the same way the cold
reviewer's are. Per memory:
`project_caterpillar_no_hallucination.md`.

### 7.5. M8's reach: per-file coherence, NOT cross-endpoint behavior

The C2 bug (revision_id serialization mismatch) is the
canonical example of what M8's static-coherence review can't
see. Two endpoints read correctly in isolation; the bug
emerges from their interaction. M9's `pytest_passes` would
catch it given an integration test, but Hatter's M6 didn't
generate that specific scenario. This is a known limit of the
current substrate — characterized + filed, not glossed over.
Per memory: `project_caterpillar_static_blindspot.md`.

### 7.6. Frontend coverage is the visible substrate gap

Zero frontend tests despite `vitest` being installed. The
Tweedles' M7 directive doesn't require Hatter scenarios to be
translated into runnable frontend tests; M9's `npm_build`
verifies compile + bundle, not behavior. The single biggest
test-coverage gap in the codebase is exactly where the substrate
has no enforcement loop. This is honest evidence for the
limitations chapter.

---

## 8. Comparison baselines (recommended follow-up)

The artifact above grades Wonderland's output against an
independent reviewer's professional standards. To close the
rigor loop, the paper should establish a baseline showing
what code *without* Wonderland looks like for the same
directive. Three recommended experiments, in increasing rigor:

### 8.1. Single-shot Haiku 4.5 against the same directive

Cheapest. ~$0.20-0.50. Give Haiku 4.5 the literal `notebook`
directive (`projects/mvp-demo2/.wonderland/directives/notebook.yaml`)
with a "produce a working full-stack markdown notebook app"
framing and capture what it generates in one inference.
Compare: how many files? How many endpoints? Are there
escape helpers? Is markdown sanitized? Are there tests?

Hypothesis: single-shot will produce a 2-3-file sketch with no
test coverage, no security helpers, and inline `dangerouslySetInnerHTML`
with no sanitization. (Charitably: maybe basic CRUD with no
search or tag features.)

### 8.2. Single-shot Sonnet 4.6 against the same directive

The harder rebuttal: *"but Sonnet would have produced equivalent
quality for less attention, no Wonderland needed."* Test the
rebuttal directly. ~$1-2 of inference.

Hypothesis: Sonnet single-shot produces something
shape-comparable to mvp in CRUD scope but lacks the
multi-lens discipline (no anti-bypass docstrings on escape
helpers, no severity-tagged tests citing scenario artifacts,
no cross-file contract citations). Sonnet's output will be
cleaner-looking-on-the-surface, lower-discipline-on-inspection.

### 8.3. OSS markdown-notebook contrast

Find an existing OSS markdown-notebook app of comparable
scope (Joplin / SilverBullet / dendron are too big; an
abandoned single-author hobby project would be the right
comparison). Read its security discipline, test coverage,
contract clarity. Compare.

Hypothesis: most OSS hobby projects of this scope lack the
escape-helper discipline + severity-tagged tests + contract
references. Wonderland's output reads more like a small
internal-tools-team artifact than a hobby project — even
though no human wrote the bulk of it.

### 8.4. Honest caveat

These comparisons are experimental tests of *the substrate*,
not of *the model*. Variable being tested: identity
engineering + multi-lens review + workflow primitives. Input
is the same directive in all three setups. The differences
that emerge are differences *the substrate produces*, not
differences the underlying model would produce on its own.

---

## 9. Live verification (2026-05-18 — operator-run)

Cross-checking the artifact end-to-end against the actual
pilot location (`projects/mvp-demo2/`) instead of just the
curated `demo/mvp/` copy. Started the backend on `:8001`, the
Vite dev server on `:5174` (ports shifted from the 5173/8000
defaults because the operator had other services on them).

**What ran clean:**

- Backend `/health` → `{"status":"ok"}`
- `uv run pytest tests/` → **61 passed in 1.29s**
- CRUD via curl: created 3 notes, listed in reverse-chrono
  order, retrieved individually.
- **LIKE-wildcard escape discipline confirmed in production
  behavior:** posted a note titled `"100% complete"`, then
  searched for the URL-encoded `%`. Result: 1 note matched
  ("100% complete"), not all 3. The `_escape_like_pattern` +
  `_safe_ilike` machinery at `notes.py:196-246` works as
  designed — the bug class `test_search_wildcard_issues.py`
  guards against doesn't manifest.
- Vite frontend on `:5174` proxies `/health` and `/api/*` to
  the backend correctly.

**A UX rough edge — operator-noticed during browser use:**

The list view doesn't auto-refresh when a note is submitted
from the editor. Save returns 200; the new note exists in the
backend; the list pane in the browser keeps showing the prior
state until manual refresh. That's the class of UX bug that
should have surfaced in a Hatter `test_scenario` around the
editor → list → save round-trip (severity: `degradation` —
system technically works but breaks the persona's mental
model of "I saved it; I should see it"), or in a contract
note specifying who refetches and when. It surfaced in
operator browser use, not in pytest. The substrate's
test-scenario surface is largely backend-end-to-end, not
frontend-state-cascade — another instance of the
[no-frontend-test enforcement loop gap](#62-c2-cross-endpoint-serialization-mismatch--failure-mode-of-m8-static-review)
the cold reviewer flagged.

**Two real bugs surfaced that validate findings already in
this artifact:**

1. **Stale schema on disk (validates M1's "no migration
   story" finding).** The pre-existing `app.db` in
   `projects/mvp-demo2/` was created during an early pilot
   iteration with a different schema (old `notes.tags`
   NOT NULL column from before the `Note` / `Tag` association
   table was extracted). The current SQLAlchemy model
   doesn't supply that column on INSERT. `Base.metadata.create_all()`
   doesn't migrate existing tables — only creates missing
   ones. Result: first POST returned `500 IntegrityError`
   from a stale column the code no longer knows about.

   The cold reviewer's [M1 finding](#54-test-quality)
   predicted this exactly: *"`main.py:21` runs
   `Base.metadata.create_all` on every startup. Fine for
   dev; please add an Alembic migration story before any
   prod use. The docstring acknowledges this."* It bit on
   first operator-run verification — at the dev-vs-prod
   boundary, exactly where M1 said it would.

   Mitigation in verification: moved `app.db` aside, let
   the fresh `create_all` rebuild. App then worked cleanly.

2. **Partial `node_modules` install (validates the
   substrate's missing `npm install` build-check, filed as
   future work).** The first `npm install` left
   `node_modules/` present but with `dompurify` not actually
   resolved on disk — likely from an interrupted earlier
   install that the operator-verification flow's
   `(test -d node_modules || npm install)` guard treated as
   "already installed." Vite then errored at runtime:
   *"Failed to resolve import 'dompurify' from
   'src/Preview.tsx'."*

   The dep is **correctly declared** in
   `frontend/package.json` (both `dompurify` and
   `@types/dompurify`); the pilot didn't ship a missing-dep
   bug. The verification flow had stale dep cache.

   Wonderland's M9 substrate check has `npm_build` but no
   `npm install` step — meaning a partial-install
   environment would pass `npm_build` only if the missing
   deps happen not to be touched by the bundler's
   tree-shake. Filed in the
   limitations (§8) as a
   substrate gap.

   Mitigation in verification: clean reinstall
   (`rm -rf node_modules package-lock.json && npm install`).
   App then loaded.

**What this verification adds to the paper:**

The M1 finding ("missing migration story") was previously
framed as a known limitation with the caveat *"fine for dev,
flag before prod."* Live verification confirms it **bites at
the first dev-to-anywhere-else boundary**, not just in
abstract production. Operator-run-verification IS one of
those boundaries. The framing tightens: the substrate's
output is shipping-shaped, and the rough edges that get
called "fine for dev" surface as actual incidents in the
first non-trivial use, not just on production deployment.

The methodology chapter's operator-noticed-findings as
research-grade signal (§5)
applies here too — these bugs surfaced during a verification
the operator was running to *poke at the app for paper
purposes*, not during a structured eval. They're more
credible-as-findings precisely because nobody was looking
for them.

---

## See also

- Cost breakdown analysis (Appendix E.1) —
  per-workflow + per-agent spend.
- Pilot narrative (Appendix D) — how it
  was built, what shipped per milestone.
- Workflow walkthrough (Appendix A) — the
  substrate mechanics that produced this output.
- Cast walkthrough (Appendix B) — the characters
  whose multi-lens review shaped it.
- Limitations chapter source (§8)
  — both bugs found here are linked from there as
  empirically-validated substrate gaps.
- The actual code lives at `demo/mvp/` (curated paper-reader
  copy) and `projects/mvp-demo2/` (live pilot state) —
  clone + run + verify the artifact yourself.
