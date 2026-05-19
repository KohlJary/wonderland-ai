## Review 020: Feature 003: Search endpoint — contract drift on API shape

**GUID:** 01KRXW5Q7BDMK9KT8ERTN5ASZ5
**Files reviewed:** src/backend/api/notes.py, frontend/src/api.ts, frontend/src/Search.tsx, tests/test_search.py
**Verdict:** request-changes

### Findings

#### block: Query parameter name: contract says 'q', implementation says 'query'
**Location:** src/backend/api/notes.py:292
**Quote:**

```
def search_notes(
    query: str | None = Query(default=None, description="Text to search in title and body"),
```

**Read:** The endpoint accepts a query parameter named 'query'. Contract-note-008 explicitly specifies this parameter should be named 'q'. The backend, frontend (api.ts:92), and all tests are internally consistent on 'query', but they drift from the contract.
**Concern:** The contract is the canonical agreement between Tweedles. When code drifts from the contract, there are two conflicting sources of truth. Downstream consumers (third-party clients, documentation, future developers) won't know which to follow. This drift was silent—no review verified that the implementation matched the contract before shipping.
**Request:** Rename the parameter from 'query' to 'q' (line 292). This restores alignment with contract-note-008.

#### block: Response field: contract says 'total_results', implementation says 'total'
**Location:** src/backend/api/notes.py:321
**Quote:**

```
class SearchResponse(BaseModel):
    results: list[NoteResponse]
    total: int
```

**Read:** SearchResponse exports 'total' for the count of matching notes. Contract-note-008 specifies 'total_results'.
**Concern:** Response field names are part of the HTTP API contract. Drift means any client expecting 'total_results' will receive a response with 'total' instead and fail to parse it.
**Request:** Rename the field to 'total_results' (line 321).

#### block: Pagination field: contract says 'page_size', implementation says 'limit'
**Location:** src/backend/api/notes.py:293 (request), 325 (response)
**Quote:**

```
    limit: int = Query(default=20, ge=1, le=100, ...)

class SearchResponse(BaseModel):
    ...
    limit: int
```

**Read:** Both request parameter and response field use 'limit'. Contract-note-008 specifies 'page_size'.
**Concern:** Affects both the request (query parameter name) and response (field name) sides of the contract.
**Request:** Rename request parameter to 'page_size' (line 293) and response field to 'page_size' (line 325).

#### change-required: Response body field: contract says 'body_preview' (150 chars), implementation sends full 'body'
**Location:** src/backend/api/notes.py:321 (NoteResponse reused in search results)
**Quote:**

```
class NoteResponse(BaseModel):
    ...
    body: str
    ...
```

**Read:** NoteResponse includes the full 'body'. Since SearchResponse.results uses [NoteResponse], the full body is sent in search results. Contract-note-008 specifies 'body_preview' (first 150 chars). The frontend works around this by truncating on the client (Search.tsx:153).
**Concern:** Performance: returning full note bodies in paginated search results wastes bandwidth. A search with 100 results sends 100x full bodies instead of 100x previews. The contract's optimization was intentional.
**Request:** Modify the search endpoint to return body_preview (150-char truncation) instead of full body. Either create a SearchResultNote response model (separate from NoteResponse) or conditionally exclude the body field in search results. Update frontend Search.tsx:153 to use note.body_preview.

#### change-required: Pagination indexing: contract says 1-indexed (default 1), implementation says 0-indexed (default 0)
**Location:** src/backend/api/notes.py:293
**Quote:**

```
    page: int = Query(default=0, ge=0, description="Page number (0-indexed)")
```

**Read:** The endpoint defaults page to 0 and requires page >= 0. Contract-note-008 specifies page >= 1, default 1 (1-indexed).
**Concern:** Pagination indexing is part of the contract. The implementation chose 0-indexed without re-negotiating the contract.
**Request:** Change to 'page: int = Query(default=1, ge=1, ...)' and adjust offset calculation from 'page * limit' to '(page - 1) * limit' in the search function.

#### suggestion: App.tsx navigation and Search component wiring is correct
**Location:** frontend/src/App.tsx:35-39
**Quote:**

```
{view === 'editor' ? (
          <EditorLayout />
        ) : (
          <Search onClear={() => setView('editor')} />
        )}
```

**Read:** The navbar toggle switches views. Search is rendered when view==='search', and onClear returns to editor. Integration is correct.
**Concern:** None. This is approval for the wiring pattern.
**Request:** No changes. Once contract drift issues are fixed, the UI integration is complete.

### Approvals

- Text search logic is correct: ilike() provides case-insensitive substring matching on title OR body (lines 305-311), matching the contract's intent.
- Tag filtering uses AND logic (chained .filter() calls, lines 315-321): notes matching ALL specified tags are returned, as the contract specifies.
- Pagination logic is correct: total count computed before pagination (line 325), has_more flag is accurate (offset + limit < total_count, line 333), results ordered by updated_at DESC then id DESC (line 329). The logic is sound.
- Frontend Search UI is well-implemented: debounced search (300ms DEBOUNCE_MS), tag multiselect suggestions, pagination controls with Previous/Next buttons, error recovery with Retry. UX is polished and matches ticket-013.
- Error handling is present: invalid parameter bounds validated by FastAPI constraints (limit must be 1-100, page must be >=0). Frontend displays error messages with retry option.
- Tweedles coordinated correctly on implementation details: backend and frontend are aligned on the same parameter/field names, tag semantics, and pagination logic. The drift is from the contract, not between Tweedles.

### Cross-domain references

- Contract-note-008 is the canonical API contract. Five points of drift (parameter names, response field names, body preview, pagination indexing) indicate the contract was not reviewed before implementation. Recommend: before Tweedles ship, verify that request parameters, response fields, and data types match the contract notes. Silent contract drift like this erodes the team's ability to reason about the code.
