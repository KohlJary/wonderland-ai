## Scenario 237: Code audit: verify all current call sites use escape correctly

**GUID:** 01KRXZ858SK3B6BPMHNS918V58
**Severity:** curiosity

**Setup:**

The codebase currently has one call site for _escape_like_pattern() in the search_notes() function. We verify it uses escape="\\" correctly.

**Trigger:**

Grep the codebase for _escape_like_pattern() and inspect each caller.

**Expected:**

Every caller includes escape="\\" in the corresponding ilike() call.

**Concern:**

Current code passes inspection (one call site, correctly escaped). But this scenario documents the *pattern* — future audits should use the same check when new call sites are added.

**Property:**

All callers of _escape_like_pattern() must pair the escaped pattern with escape="\\" in ilike(); audit as part of code review for new uses.

**Implies:**
- The Caterpillar's code review should flag any new calls to _escape_like_pattern() that omit escape="\\".
- Consider adding a static check (linter rule) to enforce this if multiple call sites accumulate over time.
