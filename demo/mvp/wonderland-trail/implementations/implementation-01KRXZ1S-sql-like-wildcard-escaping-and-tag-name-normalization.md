## Implementation 050: SQL LIKE wildcard escaping and tag name normalization

**GUID:** 01KRXZ1SM5ZWW82MS3S646HMPH
**Side:** backend
**Ticket:** pipe.kohl-searches-notes-by-title-and-body-content
**Contract:** search-api/v1 (GET /api/search with escaped LIKE metacharacters) and tag-input-validation/v1 (all tag inputs normalized and validated with whitespace rejection)
**Ready for review:** yes

**Approach:**

Added _escape_like_pattern() helper that escapes % → \% and _ → \_ before LIKE pattern construction. Search endpoint calls this on the user query (q parameter) and passes escape='\\' to .ilike() so SQLite treats backslash as the escape character. Added _normalize_and_validate_tag_names() function for consistent tag input validation: strips leading/trailing whitespace, rejects empty/whitespace-only tags with 400 Bad Request, deduplicates by exact string match (case-sensitive). All tag endpoints (POST /notes, POST /notes/{id}/tags, PUT /notes/{id}) now use this validator.

**Invariants Enforced:**
- Search query containing literal % returns notes with %, not wildcard-matched results
- Search query containing literal _ returns notes with _, not single-char-wildcard-matched results
- Tag input normalization consistent across all endpoints (POST /notes, POST /notes/{id}/tags, PUT /notes/{id})
- Whitespace-only tag names rejected with 400 Bad Request (invariant: no empty tags in database)
- Tag names globally unique (UNIQUE constraint), case-sensitive (three distinct tags: research, Research, RESEARCH)
- Duplicate tag names in a single request deduplicated by exact string match

**Schema Changes:**

None. Tag.name column already exists as String(100) UNIQUE. Escaping is applied at the query/input validation layer, not at storage.

**Failure Modes Handled:**
- Search q='%': _escape_like_pattern returns '\%', pattern becomes '%\%%', ilike with escape='\\' matches notes with literal % — correct
- Search q='_': _escape_like_pattern returns '\_', pattern becomes '%\_%', ilike with escape='\\' matches notes with literal _ — correct
- Search q='\\': _escape_like_pattern handles by escaping the backslash first, pattern matches literal backslash — correct
- POST /notes with tag_name='  ': stripped to '', raises HTTPException(400) — request rejected without data loss
- POST /notes/{id}/tags with tag_name='  research  ': stripped to 'research', stored and queried as normalized form — idempotent
- POST /notes with tag_names=['foo', 'foo', 'bar']: deduplicated to 2 unique tags (foo, bar), not 3 — correct
- Concurrent POST /notes with same tag_name: both requests succeed, both reference same tag_id — no duplicate tags

**Files:**
- src/backend/api/notes.py: added _escape_like_pattern() [124-137], added _normalize_and_validate_tag_names() [140-169], updated search_notes() to escape q and use escape='\\' [399-405], updated associate_tag() to normalize/validate tag_name [320-321]
- src/backend/models.py: clarified Tag.name invariant (case-sensitive) in docstring [100-101]
- tests/test_tag_scenarios.py: hardened test_tag_names_with_whitespace_only_entries to assert 400 rejection, hardened test_tag_names_case_sensitivity_deduplication to assert 3 distinct tags, hardened test_post_associate_tag_with_whitespace_in_name to assert normalized storage
- tests/test_notes_edge_cases.py: clarified test_post_note_with_duplicate_tag_names_in_list to assert 2 deduplicated tags

**Known Limitations:**
- LIKE search performance: O(n) substring matching without full-text indexing. Acceptable for MVP (<100K notes); future work should add FTS5.
- Unicode whitespace: tag normalization via str.strip() only strips ASCII whitespace. Unicode whitespace (e.g., non-breaking space) is preserved in tag names.
