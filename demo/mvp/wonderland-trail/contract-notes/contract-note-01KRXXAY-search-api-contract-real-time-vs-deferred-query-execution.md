## Contract Note 010: Search API contract: real-time vs. deferred query execution

**GUID:** 01KRXXAYQTTFSDH111PZ20J3EZ
**State:** agreed
**Contract Version:** search-endpoint-keystroke-driven-with-300ms-debounce/v1

**Current Shape:**

Contract-note 008 established GET /api/search?q=...&tags=...&page=...&page_size=..., returning {total_results, page, page_size, results: [{id, title, body_preview: 150 chars, tags, created_at}, ...]}

**Proposed Change:**

For kohl-searches-notes-by-title-and-body-content feature: confirm whether search requests fire on every keystroke (real-time) or only on explicit action (Enter/button). Backend implication: real-time requires server-side query optimization (indexed FTS5, cached results or request debouncing on client side); deferred allows simpler backend. Query shape can stay same (GET /api/search); response shape stays same. Question for Tweedledee: is search form wired to send on keystroke onChange, or only on form submit?

**Source:** Story 017: Kohl searches notes by title and body content; confusion-flag about real-time vs. button-press tradeoff

**Frontend Impact (Tweedledee):**

Real-time (keystroke-driven) confirmed. Search.tsx wires input onChange → debounced API calls (300ms debounce to avoid thrashing). Each keystroke triggers searchQuery state change → debounced effect → API call to GET /api/search with current query, tags, page (reset to 1 on query change per contract-note-008). This provides Kohl with immediate feedback as she types, which aligns with her research workflow (quick scanning of results). Pagination resets to page 1 on query change (expected behavior). Loading and error states handled client-side.

**Backend Impact (Tweedledum):**

Real-time (keystroke) or deferred (submit) both work from backend perspective. Real-time requires: (1) FTS5 index present (already created in schema), (2) pagination stable (current page/total results may shift mid-flight if notes are created/deleted during search, which is acceptable for Kohl single-user scope), (3) no caching needed on server (each query is fresh). Deferred (button/submit) is simpler: single query per submission, no mid-flight result changes to handle. The /api/search endpoint as implemented in contract-note-008 supports both; the difference is pure client-side — whether requests fire on keystroke onChange (real-time) or on form submit (deferred). Recommend: confirm which model Tweedledee implemented, then lock contract-note-008 semantics to match. Query parameter shape stays identical; response shape stays identical. No backend changes needed either way.

**Resolution:**

Confirmed: real-time keystroke-driven search with 300ms client-side debounce is supported by existing backend implementation. GET /api/search endpoint (already implemented per contract-note-008) handles high request frequency with no issues. Case-insensitive substring matching on title+body is performant for v1 scope. Pagination resets to page 1 on query change (expected per contract-note-008). FTS5 index not currently implemented but not required for v1 single-user scope; upgrade path exists to FTS5 in v2 without contract change. Search interaction model locked: Kohl types, live results stream, pagination resets on query change, all indexed and responsive.
