## Implementation 055: _escape_like_pattern() escape-parameter contract enforcement

**GUID:** 01KRXZAE2K9QVJ08FD9AJ18DPT
**Side:** backend
**Ticket:** 01KRXZ5B
**Contract:** search-endpoint-contract-get-api-search-with-pagination/v1 (contract-note-008)
**Ready for review:** yes

**Approach:**

Added CRITICAL docstring warning to _escape_like_pattern() detailing the contract requirement. Created _safe_ilike() helper function that wraps SQLAlchemy's ilike() and enforces escape='\' at the call site, preventing misuse. Updated search_notes() to use _safe_ilike() instead of direct ilike() calls.

**Invariants Enforced:**
- LIKE metacharacter escaping contract: all LIKE patterns used in ilike() calls must specify escape='\' (enforced via _safe_ilike helper)
- SQL injection prevention: user input is escaped before being used in LIKE patterns

**Schema Changes:**

none

**Failure Modes Handled:**
- Future developer forgets escape parameter in ilike() call: prevented via _safe_ilike() helper that enforces it

**Files:**
- src/backend/api/notes.py: Added CRITICAL docstring to _escape_like_pattern() (lines 126-134), added _safe_ilike() helper (lines 151-176), updated search_notes() to use _safe_ilike() (lines 436-439)
- tests/test_tag_scenarios.py: Added detailed assertion failure messages for all test assertions (enables better debugging when tests fail in CI)
