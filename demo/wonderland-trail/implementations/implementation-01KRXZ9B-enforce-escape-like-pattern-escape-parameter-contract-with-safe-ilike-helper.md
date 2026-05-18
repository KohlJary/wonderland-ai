## Implementation 052: Enforce _escape_like_pattern() escape-parameter contract with _safe_ilike() helper

**GUID:** 01KRXZ9B2DFW2D3FMZ1DA5KE1T
**Side:** backend
**Ticket:** escape-like-pattern-escape-parameter-contract-is-implicit-not-enforced
**Contract:** search-api/v1 (unchanged — contract remains GET /api/search with case-insensitive LIKE matching and LIKE metacharacter escaping)
**Ready for review:** yes

**Approach:**

Created _safe_ilike(column, pattern) helper that wraps SQLAlchemy's .ilike() and automatically includes escape='\\'. This enforces the contract that escaped patterns must be used with the escape parameter at the call site, preventing bugs where the parameter is forgotten. Enhanced _escape_like_pattern() docstring with CRITICAL warning pointing developers toward the helper. Both call sites in search_notes() now use _safe_ilike() instead of direct .ilike() calls.

**Invariants Enforced:**
- Escaped LIKE patterns are always used with escape='\\' parameter enforced in _safe_ilike()
- User input containing % or _ is escaped and treated as literal characters, not wildcards

**Schema Changes:**

None

**Failure Modes Handled:**
- Future developer adding new LIKE query without escape parameter: structurally impossible if using _safe_ilike()
- Refactoring existing LIKE calls and forgetting escape: docstring + helper guide to correct approach

**Files:**
- src/backend/api/notes.py: Added _safe_ilike() helper, enhanced _escape_like_pattern() docstring, refactored two .ilike() call sites to use helper
