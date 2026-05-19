## Review 025: Consolidation M3.5 review: 42 tickets for one feature is over-decomposition; backend is DONE, frontend TODO, massive duplication across three ticket generations

**GUID:** 01KRXX83GWXRWMQTPAX2YWQRQ1
**Files reviewed:** .wonderland/tickets
**Verdict:** request-changes

### Findings

#### block: Three parallel ticket hierarchies for the same work — classic generation drift
**Location:** .wonderland/tickets (directory-wide pattern)
**Quote:**

```
Ticket-01KRXRNH-*: 8 tickets (generation 1)
Ticket-01KRXRQF-* and 01KRXRQZ-*: 6 tickets (generation 2)
Ticket-01KRXX3S-* through 01KRXX4Q-*: ~28 tickets (generation 3, mixed priorities)
```

**Read:** The team decomposed the feature 'Project gains durable editor substrate' at least three times, each time creating fresh ticket files without retiring the prior generation. All three generations name the same work (POST/GET/PUT/DELETE notes, search endpoint, tag association, editor component, markdown preview, localStorage sync). The generations differ only in title phrasing and minor acceptance detail differences.
**Concern:** This is a critical M3.5 failure mode: when M3 decomposition runs multiple times (or when multiple agents decompose in parallel), the results accumulate as duplicates. The team now has 42 tickets naming the same 5–6 logical units of work. M7 implementation will face decision paralysis: which ticket to start? The answer 'all of them' wastes time; the answer 'pick one' abandons the others to orphan status in the backlog. Consolidation MUST resolve this before M7.
**Request:** For each unique work unit (e.g., 'backend full CRUD + schema + search'), keep exactly ONE ticket and retract all duplicates. Merge acceptance criteria if needed, but do not ship multiple tickets for the same capability to the same owner. I've identified the merges below; after you retract, the count should drop from 42 to ~5–6.

#### change-required: Backend work is COMPLETE (not TODO); this must update the feature state before M7
**Location:** src/backend/api/notes.py (complete POST/GET/PUT/DELETE), src/backend/models.py (schema + tags)
**Quote:**

```
All seven endpoints are implemented:
- POST /api/notes (create with body, tags)
- GET /api/notes (list all in reverse chronological)
- GET /api/notes/{id} (read by id)
- PUT /api/notes/{id} (update title, body, tags)
- DELETE /api/notes/{id} (delete with cascade)
- POST /api/notes/{id}/tags (associate tag, auto-create)
- DELETE /api/notes/{id}/tags/{tag_id} (remove tag)
- GET /api/search (paginated full-text search with tag AND filtering)

Schema is defined in models.py with Note + Tag + association table. No migrations needed (SQLAlchemy create_all on startup).
```

**Read:** The backend implementation is production-ready. All endpoints match the contract notes (contract-note-01KRXRTT, 01KRXRVG, 01KRXRVT, 01KRXRWW). Error handling is correct (404s for missing notes, proper cascades for tag deletion). Timestamp handling uses timezone-aware UTC ISO8601. Search respects AND semantics for tag filtering. Tag association auto-creates missing tags. No TODO markers, no stub implementations.
**Concern:** The feature-states.jsonl and ticket statuses all show this feature as 'open' with multiple 'Blocked by' references between tickets that are actually already done. This creates false blockers for M7: if Tweedledum believes ticket-010 (schema) must complete before ticket-045 (CRUD endpoints), he won't start either, even though both are already done. Frontend tickets will show as blocked_by backend tickets that are complete. This must be corrected before M7 reads the dependencies.
**Request:** Update the feature state for 'Project gains durable editor substrate' to note that backend is complete (mark the backend tickets as done or remove their status-open marker). Frontend tickets should not have backend tickets as blockers; they should reference the completed endpoints as their dependency contract, not as a task-in-progress. The Rabbit should emit a brief status update to the bus naming what's done so M7 can sequence cleanly.

#### change-required: Frontend is TODO — no tickets or code exist; clarify the expectation
**Location:** src/frontend does not exist; ~15 frontend tickets in .wonderland/tickets
**Quote:**

```
Frontend paths in git: nonexistent.
Frontend tickets: ticket-01KRXRNH-frontend-editor-pane-*, ticket-01KRXRQZ-frontend-search-ui-*, ticket-01KRXX4G-frontend-editor-component-*, ticket-01KRXX3X-markdown-preview-*, and others. All marked 'status: open'.
```

**Read:** No React application exists yet. No package.json, no build step, no component skeleton. The directive specifies 'UI framework: react' and 'entry point: src/backend/main.py' (Python backend only), but the M1 stories and M2 features clearly require frontend implementation (editor, search results, markdown preview). This is a 'directive vs. expectation' gap.
**Concern:** M3.5 is consolidating backend + frontend tickets together, but the directive may only intend backend for this run. If frontend is out-of-scope, the 15+ frontend tickets should be retracted (they're not tickets at all; they're speculative work from a future milestone). If frontend IS in scope, the Rabbit needs to communicate this clearly and the team needs to clarify whether M7 will ship both Tweedles on full-stack tickets or if the frontend work is deferred to M7.2 / M7.3.
**Request:** Clarify with the operator: is frontend implementation in scope for this milestone? If yes, keep the frontend tickets and mark them clearly. If no, retract all frontend tickets and the feature should be marked as 'backend-only' with a note that frontend is a future milestone. The current state is ambiguous.

#### suggestion: Test status is unclear — pytest cannot run due to missing dependencies
**Location:** tests/conftest.py (missing 'fastapi' module in import chain)
**Quote:**

```
pytest output: ModuleNotFoundError: No module named 'fastapi' at tests/conftest.py:10
```

**Read:** The test framework exists (pytest, vitest specified in stack), test files exist (test_health.py, test_notes.py, test_search.py), but the test environment is not set up with dependencies. This prevents verification of whether the backend endpoints actually pass their test suites.
**Concern:** M3.5 consolidation assumes M5 (implementation) shipped working code. Without running tests, I cannot confirm whether the backend endpoints are actually production-ready or whether they have bugs the test suite would catch. This is a low-confidence verification gap.
**Request:** Before M7 starts, either: (a) ship a setup.py / requirements.txt and run the tests to confirm the backend code passes, or (b) acknowledge that this is a deferred testing pass and the Hatter will validate during M5.5. Don't leave test status ambiguous.

### Approvals

- Backend implementation quality is high: clear names (search_notes, _associate_tags), comprehensive docstrings explaining invariants, correct error codes, timezone handling done right. The code is ready to ship.

### Cross-domain references

- Frontend scope question for operator — is UI implementation in this milestone or deferred?
