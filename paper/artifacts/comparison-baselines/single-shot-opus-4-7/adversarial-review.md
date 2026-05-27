# Adversarial review — single-shot-opus-4-7 (Claude Opus 4.7)

**Setup:** Single Anthropic API call to `claude-opus-4-7` with the notebook directive as user message + minimal "expert full-stack engineer, produce complete code" system prompt. `max_tokens=8192` (hit), 77.7s elapsed, $0.6287 input+output. Output is one markdown file with fenced code blocks per source file; truncated mid-function in `frontend/src/api.ts` at line 747.

## Findings summary

| Severity | Count |
|---|---|
| block | 5 |
| change-required | 8 |
| suggestion | 4 |
| note | 3 |
| **Total** | **20** |

## Feature-surface coverage (Axis 0)

| Capability | Directive requirement | Delivered? |
|---|---|---|
| Create note (title + body + optional tags) | Core | Yes — backend full, frontend unverifiable (truncated) |
| Edit existing note | Core | Yes — backend full, frontend unverifiable |
| Delete existing note | Core | Yes — backend full, frontend unverifiable |
| List notes, most-recently-edited first | Core | Yes — backend + SQL correct |
| Markdown preview pane (client-side render) | Core | Partially — `react-markdown` + `remark-gfm` declared in `package.json`; render call in missing `NoteEditor.tsx` |
| Tag-based filtering | Core | Yes — backend full, frontend unverifiable |
| Full-text search (title + body + tags) | Core | Yes — backend full, frontend unverifiable |
| Persistent storage across restarts | Core | Yes — SQLite with `NOTEBOOK_DB_PATH` env override |

Five of the seven React source files listed in the project-structure tree (`main.tsx`, `App.tsx`, `styles.css`, `components/NoteList.tsx`, `components/NoteEditor.tsx`) never received code blocks due to truncation. All frontend capability claims are therefore "backend is present; frontend unverifiable."

## Blockers (substrate-value-claim relevant)

1. **`frontend/src/api.ts:743` — truncated mid-function, entire CRUD client missing.** The `handle<T>` error helper is cut off in the middle of its `try` body (`if (body` — sentence incomplete). None of the API functions that would call it (`getNotes`, `createNote`, `updateNote`, `deleteNote`) appear in the output. The frontend cannot import a working API module; a `tsc && vite build` fails at import resolution or produces a broken module with no exported functions. **App cannot run in a browser.**

2. **`main.tsx`, `App.tsx`, `styles.css`, `components/NoteList.tsx`, `components/NoteEditor.tsx` — five declared files never delivered.** The project-structure tree at output lines 7–37 lists 13 source files. Eight are delivered with code blocks; five frontend source files receive none. `index.html` references `/src/main.tsx`; `main.tsx` is absent. **The frontend build fails at its entry point.**

3. **`frontend/vite.config.ts:697` — `setupFiles: ['./src/test-setup.ts']` references a file never created.** The Vitest configuration at line 697 declares `setupFiles: ['./src/test-setup.ts']`. That file is not in the output. Running `vitest run` crashes immediately with a module-not-found error before any test body executes. The test suite cannot run.

4. **`backend/app/main.py:416` — `@app.on_event("startup")` is deprecated and conditionally non-functional.** FastAPI deprecated `on_event` in 0.93.0 and the decorator may be silently no-op'd in future patch releases. The correct pattern is a `lifespan` context manager. If `_startup` is never called, `init_db()` never runs, the schema is never created, and every route raises `sqlite3.OperationalError: no such table: notes` on first request. Severity is block because the failure mode is silent on startup and catastrophic on first API call — an ops team would see no startup error and would not immediately connect the DB failure to the decorator deprecation.

5. **`backend/tests/test_api.py:576` — `test_list_order_is_most_recently_edited_first` is a timing-dependent flake.** The test creates two notes sequentially, then PUTs the first note to advance its `updated_at`. The PUT issues `UPDATE notes SET updated_at = datetime('now')`. SQLite's `datetime('now')` has one-second resolution. On a fast machine all three operations (two INSERTs + one UPDATE) can complete within a single second, resulting in identical `updated_at` values for both rows after the update. When that happens the `ORDER BY n.updated_at DESC, n.id DESC` tiebreaker places the note with the higher `id` (the "second" note) first — the opposite of the assertion. The test passes in most environments but fails under high-speed CI on every run where wall-clock advances less than one second across the three DB operations. This is the `test_shape / calendar-dependent flake` category Caterpillar flags in every pilot.

## Change-required + notable findings

1. **`backend/app/db.py:118` — `CREATE TABLE IF NOT EXISTS`, no migration story.** Schema is applied as raw DDL on startup with no versioning, no Alembic, no migration table. Adding a column to `notes` in production requires manually ALTERing the live DB. Standard `migration_shape_gap` finding.

2. **`backend/app/main.py:410-413` — CORS locked to `localhost:5173`, no production override.** `allow_origins` is hardcoded to the Vite dev URL with no env-var escape hatch. Deploying the backend to any hostname other than `localhost` breaks all frontend calls immediately. `allow_credentials=False` is correct hygiene; the origin restriction itself is fine for local dev but ships as a production blocker. `change-required` because the README's "git clone + run" success criterion implies the app is usable, and a non-localhost deployment fails silently.

3. **`backend/app/models.py:359-371` — LIKE metacharacter injection in search.** User-supplied `q` is lowercased and embedded in `f"%{q.lower()}%"` before being passed as a parameterized value. The `%` and `_` wildcard characters in LIKE are NOT escaped, so `q="_"` matches every note in the database and `q="%"` also matches all notes. Not an injection that lets the caller read arbitrary tables, but a precision defect: search returns incorrect result sets for any query containing `%` or `_`. `change-required`.

4. **`backend/app/db.py:127-139` — `get_conn()` commits unconditionally on success but swallows the exception type.** The `except Exception: conn.rollback(); raise` pattern is correct, but the bare `except Exception` means `KeyboardInterrupt` and `SystemExit` (which subclass `BaseException`) bypass the rollback. Not a crash risk in production scenarios, but signals the `silent_failure / bare_except` category.

5. **`backend/tests/test_api.py:489-503` — fixture leaks env var on test failure.** The `client` fixture sets `os.environ["NOTEBOOK_DB_PATH"] = path` but cleans it up only via `os.remove(path)` at teardown — it never calls `del os.environ["NOTEBOOK_DB_PATH"]` or restores the prior value. If any test in the session runs after this fixture without using the fixture itself, it may inherit a stale path to a deleted file and see `OperationalError`. The fixture also calls `init_db()` manually after `TestClient(app)` context is entered; `TestClient.__enter__` triggers the `startup` event which calls `init_db()` again — double-init, harmless but indicative of imprecise fixture authorship.

6. **`backend/app/models.py:270-276` — orphan tag cleanup runs inside every `_set_note_tags` call.** The `DELETE FROM tags WHERE id NOT IN (SELECT DISTINCT tag_id FROM note_tags)` cleanup fires on every note save, even when tags didn't change. On a large note corpus this becomes a full-table scan on every edit. The same cleanup also fires in `delete_note` (lines 332-338). Two separate cleanup sites for the same invariant is a maintenance hazard. `suggestion`.

7. **`backend/app/models.py:253-259` — `_ensure_tags` is not atomic.** The `INSERT OR IGNORE` followed by a separate `SELECT id` pattern has a TOCTOU window: in theory two concurrent requests could race between the ignore and the select (one inserts, the other's SELECT still returns the row, but the returned `id` could differ if SQLite's autoincrement interleaved). In practice SQLite's file-level lock prevents this from being exploitable, but the intent is wrong — should use `RETURNING id` on the INSERT or a single `INSERT OR IGNORE ... RETURNING id`. `suggestion`.

8. **`frontend/package.json:619-635` — `react-markdown@^9` declared, XSS surface safe but unverifiable.** `react-markdown` v9 does not use `dangerouslySetInnerHTML` by default; it converts the markdown AST to React elements, which avoids raw HTML injection. The library choice is correct hygiene. However the actual render call (in the missing `NoteEditor.tsx`) cannot be inspected — if the component uses `remarkRehype` with `allowDangerousHtml: true` or passes `rehype-raw` as a plugin, the XSS protection disappears. The choice is correct; the implementation is unverifiable. `note`.

## Bug categories represented

- `test_shape` (2): `test_list_order_is_most_recently_edited_first` timing flake (`test_api.py:576`); fixture env-var leak (`test_api.py:489`)
- `migration_shape_gap` (1): raw `CREATE TABLE IF NOT EXISTS` DDL on startup, no versioning (`db.py:118`)
- `CORS / production config gap` (1): hardcoded `localhost:5173` origin with no override (`main.py:410`)
- `off_by_one / boundary` (1): LIKE metacharacter passthrough in search (`models.py:359`)
- `silent_failure / bare_except` (1): `except Exception` misses `BaseException` subclasses in rollback path (`db.py:133`)
- `ui_affordance` (unverifiable): no loading states, no delete confirmation, no error display — all in missing component files
- `XSS` (unverifiable): `react-markdown` choice is safe; render implementation in missing `NoteEditor.tsx`
- `frontend state-management` (unverifiable): all React component logic in missing files
- `async_await` (1 note): all FastAPI handlers are sync `def`, correct for SQLite sync driver; no async/await misuse in delivered code
- `type_annotation_gaps` (1 note): `health()` returns `dict` without a typed schema; minor

## What didn't ship (truncation accounting)

The model hit `max_tokens=8192` with approximately 40% of the frontend undelivered. Specific files declared in the project-structure tree (output lines 7–37) but never receiving a code block:

- `frontend/src/main.tsx` — React entry point, mounts `<App />` into `#root`
- `frontend/src/App.tsx` — top-level component; contains routing, note selection state, search/filter state, and all fetch orchestration
- `frontend/src/styles.css` — global styles
- `frontend/src/components/NoteList.tsx` — sidebar list component with tag filter UI
- `frontend/src/components/NoteEditor.tsx` — editor + markdown preview pane; the only place the `react-markdown` render call would appear

Additionally, `frontend/src/api.ts` was delivered but truncated after line 12 of its body. The `handle<T>` helper is cut off mid-conditional; all exported API functions (`getNotes`, `createNote`, `updateNote`, `deleteNote`, `searchNotes`, `getTags`) are absent.

`frontend/src/test-setup.ts` was referenced in `vite.config.ts` but never created, crashing the test suite.

In total: **6 source files either absent or incomplete** out of the 15 declared in the project structure (13 source files + 2 config files for tests).

## Notes on the run

The backend half of this output is the strongest single-shot deliverable of all baselines reviewed to date: the FastAPI routes, SQLite schema, Pydantic schemas, and test suite are architecturally sound, use correct patterns (parameterized queries, per-request connections, env-var DB override for tests, proper HTTP status codes), and would pass a basic functional review if run in isolation. The model ran out of tokens before completing roughly 40% of the frontend, which means the delivered artifact is not a runnable app regardless of backend quality. Had the model been given a larger token budget, the backend foundation suggests it would have produced a higher-quality frontend than the Haiku baselines — but the truncation point is exactly where the most review-relevant frontend logic lives (state management, XSS surface, CORS in production), making those categories structurally unverifiable from this output.
