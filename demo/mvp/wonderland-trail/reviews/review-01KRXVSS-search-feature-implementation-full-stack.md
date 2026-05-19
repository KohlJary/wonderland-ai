## Review 018: Search feature implementation (full-stack)

**GUID:** 01KRXVSS0S0T6KF1MEQ4G2JJD5
**Files reviewed:** frontend/src/App.tsx, frontend/src/Search.tsx, frontend/src/api.ts, src/backend/api/notes.py, tests/test_search.py
**Verdict:** request-changes

### Findings

#### block: Test expects OR tag filtering semantics but implementation uses AND
**Location:** tests/test_search.py:195-210 (test_tag_filtering_with_multiple_tag_names)
**Quote:**

```
def test_tag_filtering_with_multiple_tag_names(client):
    """GET /api/search?tags=work,personal returns notes with ANY of the tags (OR)."""
    # ...
    # Should return all 3 notes (all have at least one of the tags)
    assert data["total"] == 3
```

**Read:** The test creates 3 notes: one with only 'work' tag, one with only 'personal' tag, and one with both. It then queries `/api/search?tags=work,personal` and expects all 3 notes to be returned, which is OR semantics (match any specified tag).
**Concern:** The backend implementation uses AND semantics: notes matching `tags=work,personal` must have BOTH the 'work' tag AND the 'personal' tag. Only the third note satisfies this. The test will fail with a total of 1, not 3. This is a correctness bug that will cause the test suite to fail when run.
**Request:** Fix the test to expect AND semantics: assert data["total"] == 1 (only the 'Both tagged' note matches). Alternatively, if OR semantics are intended, fix the backend implementation to use OR logic instead of AND. The docstring at notes.py line 285 specifies AND ('all tags must match'), so the test should match the implementation and docstring.

#### change-required: Dead code: unused apiQuery and apiTags state variables
**Location:** frontend/src/Search.tsx:54-55
**Quote:**

```
  const [apiQuery, setApiQuery] = useState('');
  const [apiTags, setApiTags] = useState<string[]>([]);
```

**Read:** These variables are initialized and then updated (lines 68, 69) but never read. They appear to have been intended for tracking what query and tags were sent to the API, but the component doesn't use them for any purpose.
**Concern:** Dead code increases cognitive load and suggests incomplete refactoring. Readers may wonder what these variables are for and why they're not used, which wastes their time. Removing unused state clarifies the component's actual concerns.
**Request:** Remove the two unused state declarations (lines 54-55) and remove the corresponding setApiQuery and setApiTags assignments (lines 68-69). If you need to track the API-side query for some reason (e.g., to prevent redundant requests), add a comment explaining why; otherwise, remove it.

#### suggestion: Frontend does not document tag filter semantics to the user
**Location:** frontend/src/Search.tsx:195-210 (tag suggestion buttons)
**Quote:**

```
        {/* Tag suggestions (unselected tags from results) */}
        {unselectedTags.length > 0 && (
          <div style={styles.tagSuggestions}>
            <span style={styles.tagLabel}>Filter by tag:</span>
            {unselectedTags.map((tag) => (
              <button
                key={tag}
                onClick={() => handleAddTag(tag)}
                style={styles.tagSuggestion}
              >
                {tag}
              </button>
            ))}
          </div>
        )}
```

**Read:** The UI shows tag filter buttons and allows users to select multiple tags, but does not indicate whether the filtering logic is AND (all tags must be present) or OR (any tag can be present). The backend implements AND logic, so selecting 'work' and 'personal' returns only notes with both tags.
**Concern:** Users may expect OR semantics (show me notes with 'work' OR 'personal') but experience AND semantics (only notes with both 'work' AND 'personal'). This is a usability mismatch that could frustrate users and make the feature feel broken. The UI should clarify the filtering logic, either by changing the label to 'All of these tags' or by changing the implementation to OR semantics.
**Request:** Either (1) change the label from 'Filter by tag:' to 'Filter by ALL of these tags:' to clarify AND semantics, or (2) consider whether OR semantics would be more intuitive for this feature and, if so, change the backend implementation to match. For an MVP, option 1 (clarify the label) is lower-risk.

#### note: Redundant Query alias parameter
**Location:** src/backend/api/notes.py:328
**Quote:**

```
    query: str | None = Query(default=None, alias="query", description="Text to search in title and body"),
```

**Read:** The FastAPI Query parameter has an alias set to the same name as the parameter itself ('query'). In FastAPI, the alias is used when the URL parameter name differs from the Python parameter name. Here, they're the same, making the alias redundant.
**Concern:** Redundant code is visual noise and may confuse readers about whether there's an intentional mapping happening. It's a style issue, not a functionality issue.
**Request:** Remove the alias parameter: `query: str | None = Query(default=None, description="Text to search in title and body"),` The parameter name already specifies the URL query parameter name.

### Approvals

- The search endpoint's contract is well-documented with clear semantics for query parameters, pagination, and response shape.
- The frontend Search component is well-structured with clear state variables, debounced search, error handling with retry, and pagination controls.
- Tag filtering UI shows selected tags as removable chips and suggests unselected tags as buttons — the interaction model is intuitive.
- Pagination has_more and page calculations are correct; boundary conditions (first page, last page) are handled properly.
- The API response shape (results array, total count, pagination metadata) is clean and matches the contract.
- Frontend code handles all the required UI states: loading, error, no results, empty database, results with pagination.
- The backend implements case-insensitive text search correctly using SQLite's ILIKE, which works across both title and body fields.

### Cross-domain references

- The test suite has a correctness bug (test expects OR semantics, backend implements AND) — the Hatter should review whether the test scenarios need updating or the backend implementation needs changing to match intended behavior.
- Frontend-backend tag filtering semantics mismatch (user expectations vs. implementation) — Alice should consider whether AND semantics align with the user story 'Kohl can find past notes by title or content search', or whether the feature should offer OR semantics instead.
