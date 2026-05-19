## Implementation 054: Defensive documentation and _safe_ilike() helper for SQL LIKE escaping

**GUID:** 01KRXZ9Z9CT1RENJ7DN1P3GGRT
**Side:** backend
**Ticket:** ticket-01KRXZ5BMXQQT03839QCWRZH0M
**Contract:** SQL LIKE escaping contract (escape parameter enforcement)
**Ready for review:** yes

**Approach:**

Added critical docstring to _escape_like_pattern() documenting the implicit contract that escaped patterns MUST be used with escape='\\' in SQLAlchemy's .ilike() calls. Introduced _safe_ilike() helper function that enforces this contract at the call site, preventing bugs where escape parameter is forgotten. Updated search_notes() to use _safe_ilike() instead of bare .ilike() calls.

**Invariants Enforced:**
- SQL LIKE metacharacters (%, _) in user search input are always escaped and matched literally (not as SQL wildcards)

**Schema Changes:**

none

**Failure Modes Handled:**
- Developer forgets escape parameter in .ilike() call: _safe_ilike() enforces it automatically

**Files:**
- src/backend/api/notes.py: added _safe_ilike() helper with contract enforcement; updated _escape_like_pattern() docstring with critical warning; updated search_notes() to use _safe_ilike()
