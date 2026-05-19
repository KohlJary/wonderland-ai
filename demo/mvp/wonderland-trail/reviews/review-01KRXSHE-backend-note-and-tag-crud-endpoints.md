## Review 005: Backend: Note and Tag CRUD endpoints

**GUID:** 01KRXSHEQ3KZCTPXSQV3GJ6P2A
**Files reviewed:** src/backend/models.py, src/backend/api/notes.py, src/backend/api/__init__.py, docs/SCHEMA.md, tests/test_notes.py
**Verdict:** request-changes

### Findings

#### block: Acceptance criteria mismatch — incomplete endpoint coverage
**Location:** src/backend/api/notes.py (full file)
**Quote:**

```
Current implementation: POST /api/notes (create), GET /api/notes/{id} (read)
Ticket acceptance criteria also requires:
- GET /api/notes (list all notes)
- PUT /api/notes/{id} (update note)
- DELETE /api/notes/{id} (delete note)
- POST /api/notes/{id}/tags (add tag to note)
- DELETE /api/notes/{id}/tags/{tag_id} (remove tag from note)
```

**Read:** The implementation ships two of seven required endpoints. The other five are absent.
**Concern:** The ticket's acceptance criteria explicitly name seven endpoints. Shipping only two fails the acceptance definition. A caller cannot update a note, delete a note, list all notes, or manage tags — all required by the ticket scope.
**Request:** Either: (a) implement the remaining five endpoints to meet the ticket's stated acceptance criteria, or (b) retract the ticket's overreach and file separate tickets for the missing endpoints with separate estimates. Option (a) is preferred if the estimate buffer allows; option (b) is appropriate if scope was locked and estimates don't account for all seven endpoints. Coordinate with Rabbit to clarify which path the team agreed to.

#### change-required: Schema doc reserves list endpoint for v2, contradicting ticket scope
**Location:** docs/SCHEMA.md, lines 139-148
**Quote:**

```
### GET /api/notes — List Notes (v2 fast-follow, contract reserved)
```

**Read:** The schema document explicitly defers the GET /api/notes endpoint to v2 'fast-follow' status. However, the ticket acceptance criteria includes it as v1 scope.
**Concern:** The contract document and the ticket scope are in conflict. If GET /api/notes is deferred to v2, the ticket acceptance criteria should not require it for v1. If it's v1 scope, the schema doc should not mark it as fast-follow. This ambiguity will cause triage problems downstream (frontend blocked waiting for the endpoint, or confused about when it actually ships).
**Request:** Clarify with the Cat (who owns the contract via the SCHEMA.md document) and the Rabbit (who owns the ticket scope) which is binding. Update one artifact to match the other. If the endpoint is genuinely deferred, remove it from ticket acceptance. If it's v1 scope, move it from 'fast-follow' to 'required' in the schema and implement it.

#### suggestion: Test coverage incomplete for happy-path endpoints
**Location:** tests/test_notes.py (full file)
**Quote:**

```
Current tests: POST (minimal, with body, with tags, with all), GET by id, 404, validation, timestamps
Missing: tests for the endpoints not yet implemented (PUT, DELETE, tag operations)
```

**Read:** The tests that exist cover the implemented endpoints well (happy path + validation + 404). However, they don't cover the endpoints listed in the ticket acceptance but not yet implemented.
**Concern:** Once the missing endpoints are implemented, new tests will need to be written for them. You don't need to write those tests now, but they should be written before those endpoints ship. Documenting this now prevents the gap from being forgotten.
**Request:** After implementing the remaining endpoints (PUT, DELETE, tag operations), add tests for each: happy path, validation errors, 404/not found, and at least one error case per endpoint. The existing test structure (parametrized by operation) is a good model.

#### note: Clarify tag_ids vs tags naming in contract
**Location:** docs/SCHEMA.md, lines 110-113 (request) vs. line 123 (response)
**Quote:**

```
Request: { "tag_ids": [...] }
Response: { "tags": [...] }
```

**Read:** The request body uses 'tag_ids' (a list of tag strings), and the response body uses 'tags' (the stored form). This is intentional — it distinguishes input from output — and the implementation correctly maps between them.
**Concern:** This is deliberate, but it's a minor naming complexity that could confuse frontend developers if they're not careful. The schema doc explains it well (lines 6-7), so no change needed here. Just noting that this distinction is working as intended.
**Request:** No action required. The contract is clear, and the implementation honors it.

### Approvals

- The SCHEMA.md document is well-structured, comprehensive, and clearly explains invariants, migration paths, validation rules, and backward compatibility. It's the right artifact to pin the contract between frontend and backend.
- The Note model correctly represents the schema: non-empty title, optional body (with empty-string default), JSON array for tags (with empty-array default), and server-side timestamps with proper immutability semantics (created_at never changes, updated_at updates on every write).
- The to_dict() method properly serializes the model to JSON with ISO8601 timestamps and defensive fallbacks for nullable columns.
- The POST /api/notes endpoint correctly validates input (title required and non-empty, body and tags optional), creates the model, commits it, and returns a NoteResponse with all required fields.
- The GET /api/notes/{id} endpoint correctly retrieves by id and returns 404 with an appropriate error message when the note is not found.
- The test coverage for the implemented endpoints is solid: happy path with minimal, body-only, tags-only, and all-fields variations; validation rejection for empty and missing title; successful retrieval; 404 handling; and ISO8601 timestamp format verification.
- The cleanup of the placeholder HelloMessage model and messages endpoint is complete — no dangling imports, and the old tests and scaffolding have been removed.
- Static import checks pass; the code has no syntax errors or unresolved names.

### Cross-domain references

- Scope coordination: Rabbit should clarify whether the remaining five endpoints (GET list, PUT, DELETE, POST /tags, DELETE /tags/:id) are v1 scope (in which case the estimate may need revision and implementation continues) or are v2 fast-follow (in which case the ticket acceptance criteria should be retracted). This is a Rabbit domain decision, but it blocks the review verdict.
- Contract consistency: Cat should review the SCHEMA.md document's claim that GET /api/notes is 'v2 fast-follow' and confirm it aligns with the ticket's v1 acceptance criteria. If the endpoint is deferred, the ticket scope is incomplete; if it's v1 scope, the schema doc needs updating. This is a Cat domain decision.
