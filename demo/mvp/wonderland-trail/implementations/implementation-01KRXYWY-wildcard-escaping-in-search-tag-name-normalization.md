## Implementation 043: Wildcard escaping in search + tag name normalization

**GUID:** 01KRXYWY26G8CQH66270CJ8BX0
**Side:** backend
**Ticket:** 01KRXY8N7V6MRBHDVCVY0HHH6E
**Contract:** contract-note-01KRXRVT (tag validation), contract-note-01KRXRWW (search endpoint)
**Ready for review:** yes

**Approach:**

Added _escape_like_pattern() to escape SQL LIKE metacharacters (% and _). Updated search_notes() to use it, preventing user queries like '100%' from being interpreted as LIKE wildcards. Added _normalize_and_validate_tag_names() to strip whitespace and reject empty tags at the request boundary across all tag write paths (create, update, associate).

**Files:**
- src/backend/api/notes.py: Added _escape_like_pattern() function; updated search_notes() to escape LIKE metacharacters; added _normalize_and_validate_tag_names() for tag validation in _associate_tags()
