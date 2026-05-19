## Review 035: Search wildcard escaping & tag validation

**GUID:** 01KRXYMRSJ3G8AZAS0NS799ER9
**Files reviewed:** src/backend/api/notes.py, frontend/src/Search.tsx, frontend/src/NoteList.tsx, frontend/src/Editor.tsx
**Verdict:** request-changes

### Findings

#### block: SQL LIKE wildcard metacharacters not escaped in search
**Location:** src/backend/api/notes.py:346-350
**Quote:**

```
    if q:
        # SQLite LIKE is case-insensitive by default
        search_pattern = f"%{q}%"
        query_obj = query_obj.filter(
            or_(
                Note.title.ilike(search_pattern),
                Note.body.ilike(search_pattern),
            )
        )
```

**Read:** The search endpoint constructs a LIKE pattern by wrapping the user query with % characters. SQLite LIKE treats % (any characters) and _ (single character) as metacharacters. A user searching for '100%' will match '100 percent' because the % is not escaped.
**Concern:** Silent wrongness: users get unexpected search results. A search for '100%' should find only notes containing the literal string '100%', not '100' followed by anything. This is a correctness bug that silently produces wrong data.
**Request:** Escape SQL LIKE metacharacters in the user query. Replace % with %% and _ with _% in the search pattern. Example: `search_pattern = f"%{q.replace('%', '%%').replace('_', '_')}%"`. Verify by running the existing test_search_wildcard_issues.py tests (they currently document the bug and will pass once fixed).

#### change-required: Whitespace-only tag names accepted and stored without normalization
**Location:** src/backend/api/notes.py:135-160
**Quote:**

```
    # Deduplicate tag names (preserve order)
    seen = set()
    unique_tag_names = []
    for tag_name in tag_names:
        if tag_name not in seen:
            unique_tag_names.append(tag_name)
            seen.add(tag_name)
```

**Read:** Tag names are deduplicated but not normalized. A tag_name of '  ' (three spaces) passes the Pydantic validation (min_length=1 in TagCreate and NoteCreate) and gets stored as-is, creating confusing database entries.
**Concern:** Whitespace-only tags are not useful and create confusing UI. If a user accidentally includes '  ' in the tag_names array, it becomes a valid tag distinct from other tags.
**Request:** Normalize tag names before storing: strip leading/trailing whitespace and skip empty strings after stripping. Add this to _associate_tags: `tag_name = tag_name.strip()` and `if not tag_name: continue`. Also add a Pydantic validator to TagCreate and NoteCreate models to reject whitespace-only tag names at the request boundary.

#### suggestion: Tag deduplication and case-sensitivity inconsistent with case-insensitive text search
**Location:** src/backend/api/notes.py:145-150
**Quote:**

```
    for tag_name in tag_names:
        if tag_name not in seen:
            unique_tag_names.append(tag_name)
            seen.add(tag_name)
```

**Read:** Tag deduplication is case-sensitive. A POST request with tag_names=['research', 'Research'] creates two separate tags. But text search (q parameter) is case-insensitive (ILIKE), creating an inconsistency.
**Concern:** UX inconsistency: text search case-insensitive, tags case-sensitive. Users expect consistency. The test_tag_scenarios.py file documents this scenario.
**Request:** Decide on a case-sensitivity model and apply it uniformly. Simplest approach: normalize tag names to lowercase during creation. If you choose this, update _associate_tags to call `tag_name = tag_name.lower()` before storing. This is a design decision; document it in the contract comment.

### Approvals

- Backend CRUD endpoints are well-structured with consistent error handling and validation across all six operations (create, list, read, update, delete).
- Tag association logic is sound: idempotence, shared tag handling, and cascade behavior on note deletion are correctly implemented. The many-to-many relationship design is appropriate.
- Frontend routing in App.tsx correctly initializes from URL pathname and maintains navigation history. The three views (editor, list, search) are cleanly separated with proper callbacks.
- NoteList component renders notes efficiently with responsive grid layout and proper empty/loading/error states. Tag badge rendering is clear and visually distinct.
- Search URL persistence in Search.tsx correctly parses and updates query parameters, enabling page reload to restore state. Debouncing user input is appropriate.
- Editor now supports both create and update workflows. Loading state for fetching notes is handled correctly, and the keystroke buffer (localStorage) pattern is preserved.
- Test scenarios in test_tag_scenarios.py and test_search_wildcard_issues.py are excellent. They document real edge cases with severity classifications and clear explanations. The wildcard test is especially valuable for catching the escaping bug before production.

### Cross-domain references

- The wildcard escaping bug is a silent-correctness issue. Once fixed, verify against the existing test_search_wildcard_issues.py test suite. The Hatter should review whether additional search edge cases need testing.
- Tag name normalization affects deduplication logic across create, update, and associate endpoints. Recommend a brief pair review to ensure all paths are covered consistently.
