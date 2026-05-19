## Implementation 048: SQL LIKE wildcard escaping for search

**GUID:** 01KRXZ0RMYXZHF7GB0NS6ZXGRY
**Side:** backend
**Ticket:** ticket-01KRXYNM-sql-like-wildcard-metacharacters-not-escaped-in-search
**Contract:** ticket-01KRXYNM acceptance: Escape SQL LIKE metacharacters in the user query so that '100%' finds only notes containing literal '100%', not '100' followed by anything. Using SQLite LIKE escape character \ with escape='\\ ' in SQLAlchemy ilike().
**Ready for review:** yes

**Approach:**

Added _escape_like_pattern() helper that escapes SQL LIKE metacharacters (% → \%, _ → \_) with proper backslash escaping. Applied to search_notes() endpoint with SQLAlchemy's escape parameter. User can now search for literal '%' or '_' without those characters acting as wildcards.

**Invariants Enforced:**
- search query text (parameter q) has LIKE metacharacters (%, _) escaped before being used in LIKE pattern: '%' → '\%', '_' → '\_'
- escape character is declared to SQLAlchemy (escape='\\') so SQLite treats \ as the escape character, not a literal backslash
- user-supplied special characters in search do not accidentally trigger LIKE wildcard behavior

**Schema Changes:**

None; escaping happens in application code at query time.

**Failure Modes Handled:**
- User searches for literal '%': correctly escaped and finds only notes containing '%', not used as wildcard
- User searches for literal '_': correctly escaped and finds only notes containing '_', not used as wildcard
- User searches for backslash followed by '%': backslash is escaped (\\) and % is escaped (\%), so pattern matches literal '\%'

**Files:**
- src/backend/api/notes.py: added _escape_like_pattern() helper function (lines 130-143); applied in search_notes() query filter (lines 394-401) with escape parameter on ilike()

**Known Limitations:**
- Test environment cannot run pytest; code is syntactically valid but needs environment fix to verify test_search_with_percent_sign_as_literal_wildcard_bug, test_search_with_underscore_as_literal_wildcard_bug, test_search_with_percent_in_body pass. All tests updated to enforce correct behavior.
