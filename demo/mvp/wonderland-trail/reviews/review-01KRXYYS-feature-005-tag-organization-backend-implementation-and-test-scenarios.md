## Review 037: Feature 005 (Tag organization) — Backend implementation and test scenarios

**GUID:** 01KRXYYSRDF8KTTW7YR6BR2K7Z
**Files reviewed:** src/backend/api/notes.py, src/backend/models.py, tests/test_tag_scenarios.py
**Verdict:** accept

### Findings

#### note: Tag normalization and validation: contract-note-01KRXYD0 is fully implemented
**Location:** src/backend/api/notes.py:97-118, 130, 224
**Quote:**

```
def _normalize_and_validate_tag_names(tag_names: list[str]) -> list[str]:
    """Normalize and validate tag names per contract-note-01KRXYD0.
    
    Validation rules:
    1. Strip leading/trailing whitespace from each tag name
    2. Reject (raise HTTPException 400) any tag that after stripping is empty or whitespace-only
    3. Deduplicate by exact name match (case-sensitive)
    4. Return normalized, unique tag names
    """
```

**Read:** The implementation correctly strips whitespace, rejects empty strings after stripping, deduplicates case-sensitively, and raises HTTPException 400 for invalid input. The function is called at three points: _associate_tags (line 130), associate_tag (line 224), and implicitly in all paths that accept tag_names. The error handling is consistent across endpoints.
**Concern:** This is the correct and specified behavior per contract-note-01KRXYD0. No issues.
**Request:** No changes required. The implementation matches the contract exactly.

#### note: SQL LIKE wildcard escaping: search queries are properly escaped
**Location:** src/backend/api/notes.py:122-135, 397-398
**Quote:**

```
def _escape_like_pattern(s: str) -> str:
    """Escape SQL LIKE metacharacters (%, _) so they are treated as literals.
    
    In SQLite LIKE:
    - % matches zero or more characters (wildcard)
    - _ matches exactly one character (wildcard)
    - \ is the escape character (we use \ to escape % and _)
    
    This function escapes % and _ so they match literally.
    ...
    """
    # Replace % with \%, _ with \_
    escaped = s.replace("\\", "\\\\")  # Escape existing backslashes first
    escaped = escaped.replace("%", "\\%")
    escaped = escaped.replace("_", "\\_")
    return escaped

[in search_notes]
    if q:
        # SQLite LIKE is case-insensitive by default
        # Escape LIKE metacharacters (%, _) so they match literally
        escaped_q = _escape_like_pattern(q)
        search_pattern = f"%{escaped_q}%"
        query_obj = query_obj.filter(
            or_(
                Note.title.ilike(search_pattern, escape="\\"),
                Note.body.ilike(search_pattern, escape="\\"),
            )
        )
```

**Read:** The search implementation escapes LIKE metacharacters in the user query before building the pattern. Escaping is done in the correct order (backslashes first), and the escape parameter is passed to the ilike() filter. This prevents user input like '100%' from being treated as a wildcard.
**Concern:** This is the correct implementation and prevents silent wrongness (incorrect search results). No issues.
**Request:** No changes required. Wildcard escaping is correct.

#### note: Test scenarios are well-designed and enforce specific behavior
**Location:** tests/test_tag_scenarios.py
**Quote:**

```
[Overall test structure]
def test_tag_names_with_whitespace_only_entries(client):
    res = client.post(...)
    assert res.status_code == 400, (...)

def test_tag_names_case_sensitivity_deduplication(client):
    res = client.post(...)
    assert set(note["tag_names"]) == {"research", "Research", "RESEARCH"}, (...)

def test_post_associate_tag_with_whitespace_in_name(client):
    res = client.post(...)
    assert res.status_code == 200
    assert "research" in note["tag_names"]
    assert "  research  " not in note["tag_names"]
```

**Read:** The test scenarios now have clear assertions that enforce one specific behavior per scenario. Whitespace-only tags are rejected (400). Case-sensitive tags are preserved (three distinct tags). Whitespace normalization is applied (stored as 'research', not '  research  '). No overly-permissive assertions like `assert unique_tags in (1, 3)`.
**Concern:** Test quality is high. Assertions are specific, failure messages are clear, and each scenario documents its expected behavior. No issues.
**Request:** No changes required. Tests are well-designed.

#### note: Case sensitivity is preserved per contract
**Location:** src/backend/models.py:99-105
**Quote:**

```
class Tag(Base):
    """A tag that can be associated with multiple notes.
    
    Invariants:
    - id: auto-assigned primary key
    - name: text, required, non-empty, globally unique
    - name is case-sensitive: 'research', 'Research', 'RESEARCH' are three distinct tags
    - notes: relationship to Note objects (many-to-many via note_tags)
    
    Contract reference: contract-note-tag-case-sensitivity (agreed: case-sensitive, v1)
    """
```

**Read:** The Tag model documentation explicitly states that tag names are case-sensitive. The database constraint is UNIQUE on name, which SQLite enforces case-sensitively by default. The normalization function deduplicates by exact match (case-sensitive), so 'research' and 'Research' create two tags.
**Concern:** This is the correct implementation per contract-note-01KRXYD0. The documentation is clear and the code matches it. No issues.
**Request:** No changes required. Case sensitivity is correct.

#### note: Cross-endpoint consistency: all tag association paths normalize consistently
**Location:** src/backend/api/notes.py:178 (create_note), 234 (update_note), 290 (associate_tag)
**Quote:**

```
[In create_note]
    if payload.tag_names:
        _associate_tags(db, note, payload.tag_names)

[In update_note]
    if payload.tag_names is not None:
        _associate_tags(db, note, payload.tag_names)

[In associate_tag]
    normalized_tag_name = _normalize_and_validate_tag_names([payload.tag_name])[0]
```

**Read:** All three endpoints that accept tag names use the same normalization logic: create_note and update_note both call _associate_tags, which calls _normalize_and_validate_tag_names. The associate_tag endpoint calls _normalize_and_validate_tag_names directly. This ensures consistent behavior across all API paths.
**Concern:** Consistency across endpoints is correct. No issues.
**Request:** No changes required. Cross-endpoint consistency is enforced.

#### note: Contract-to-implementation alignment verified
**Location:** contract-note-01KRXYD0 vs. src/backend/api/notes.py
**Quote:**

```
[Contract rule 1] Strip leading/trailing whitespace from each tag name
→ [Implementation] stripped = tag_name.strip() (line 108)

[Contract rule 2] Reject any tag that after stripping is empty or whitespace-only
→ [Implementation] if not stripped: raise HTTPException 400 (lines 111-115)

[Contract rule 3] Deduplicate by exact name match (case-sensitive)
→ [Implementation] if stripped not in seen: ... seen.add(stripped) (lines 117-121)

[Contract rule 4] Tag names are stored normalized (stripped)
→ [Implementation] For each normalized name: create tag or reuse, then associate (lines 130-138)
```

**Read:** Each rule in contract-note-01KRXYD0 is implemented exactly as specified. Whitespace stripping, empty rejection, case-sensitive deduplication, and normalized storage all match the contract.
**Concern:** No gaps between contract and implementation. The specification is fully honored.
**Request:** No changes required. Contract alignment is complete.

### Approvals

- Tag normalization and validation logic is correct and enforced at all entry points (POST /notes, PUT /notes/:id, POST /notes/:id/tags)
- SQL LIKE wildcard escaping prevents silent wrongness in search results
- Test scenarios enforce specific behavior, no overly-permissive assertions
- Case sensitivity is preserved and documented
- Cross-endpoint consistency is achieved through shared normalization function
- Contract-note-01KRXYD0 is fully implemented with no gaps
