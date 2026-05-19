## Implementation 025: Query parameter rename: query → q in search endpoint

**GUID:** 01KRXW95KGTTFFYMFHGTJQ7N75
**Side:** backend
**Ticket:** query-parameter-name-contract-says-q-implementation-says-query
**Contract:** search-api/v1 (contract-note-01KRXRWW: q?: str parameter for text search)
**Ready for review:** yes

**Approach:**

Renamed the search_notes function parameter from 'query' to 'q' to match the contract-note-008 specification. Updated all references in the function body (the conditional check and string pattern construction) and the contract description at the top of the file. No functional change — this is pure contract alignment.

**Invariants Enforced:**
- The search endpoint accepts 'q' as the query parameter name, not 'query'

**Schema Changes:**

None — parameter rename only

**Files:**
- src/backend/api/notes.py: renamed parameter query → q (line 293); updated docstring (line 302); updated contract description (line 20); updated function body references (lines 322, 324)
