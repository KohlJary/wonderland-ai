# Implementation: Tag assertion clarification and normalization validation

**Ticket:** test-assertions-lack-clarity-no-failure-message-overly-permissive-logic (01KRXY8N7JPKPYA5B89Q37ZNYW)

**Source:** Caterpillar review 03 (Review ID 01KRXY8N7JPKPYA5B89Q37ZNYW)

**Contract:** contract-note-01KRXYD0 (tag-name-normalization-and-validation-semantics) + contract-note-tag-case-sensitivity (agreed: case-sensitive, v1)

## Overview

Fixed test assertions that were overly permissive (accepting multiple conflicting outcomes) and lacked clear failure messages. Implemented comprehensive tag name normalization and validation:

1. **Whitespace normalization:** Leading/trailing whitespace is stripped from tag names
2. **Validation:** Empty or whitespace-only tag names (after stripping) are rejected with HTTP 400 Bad Request
3. **Deduplication:** Case-sensitive exact-match deduplication (preserves 'research', 'Research', 'RESEARCH' as three distinct tags)
4. **Clear assertions:** Test failures now provide explicit context about what was expected vs. received

## Test Assertion Fixes

### Before (Permissive, Unclear):
```python
# test_tag_names_case_sensitivity_deduplication
unique_tags = len(set(note["tag_names"]))
assert unique_tags in (1, 3)  # Accepts EITHER outcome!

# test_tag_names_with_whitespace_only_entries
if res.status_code == 201:
    assert not any(tag.strip() == "" for tag in note["tag_names"])
else:
    assert res.status_code == 422  # Also accepts 400 or 422 implicitly
```

### After (Explicit, Clear):
```python
# test_tag_names_case_sensitivity_deduplication
assert len(note["tag_names"]) == 3, (
    f"Expected 3 distinct case-sensitive tags (research, Research, RESEARCH), "
    f"got {len(note['tag_names'])}: {note['tag_names']}"
)
assert set(note["tag_names"]) == {"research", "Research", "RESEARCH"}, (
    f"Expected tags {{research, Research, RESEARCH}}, got {set(note['tag_names'])}"
)

# test_tag_names_with_whitespace_only_entries
assert res.status_code == 400, (
    f"Expected 400 Bad Request for whitespace-only tag name, "
    f"got {res.status_code}. Response body: {res.json()}"
)
```

## Implementation Details

### Added: `_normalize_and_validate_tag_names(tag_names: list[str]) -> list[str]`

Centralized validation logic used by all tag endpoints:

1. **Strip whitespace:** `tag_name.strip()`
2. **Reject if empty:** `if not stripped: raise HTTPException(400, ...)`
3. **Deduplicate case-sensitively:** `if stripped not in seen: normalized.append(stripped)`

Called from:
- `create_note()` via `_associate_tags()`
- `update_note()` via `_associate_tags()`
- `associate_tag()` directly

### Added: `_escape_like_pattern(s: str) -> str`

Escapes SQL LIKE metacharacters (%, _) so they match literally instead of as wildcards. This fixes the bug where searching for "100%" would match "100 percent" because % is a wildcard.

Used in `search_notes()` endpoint when constructing ILIKE patterns.

## Contracts

### contract-note-01KRXYD0: Tag Name Normalization and Validation Semantics

**Binding agreement on tag name handling:**

- Tag names with leading/trailing whitespace are normalized (stripped) before storage
- Empty strings or whitespace-only strings (after stripping) are rejected with 400 Bad Request
- Tag names are case-sensitive: 'research', 'Research', 'RESEARCH' are three distinct tags
- Deduplication is case-sensitive exact-match

### contract-note-tag-case-sensitivity (Agreed: Case-Sensitive, v1)

**Binding agreement documented in Tag model:**

```python
class Tag(Base):
    """...
    Invariants:
    - name is case-sensitive: 'research', 'Research', 'RESEARCH' are three distinct tags
    
    Contract reference: contract-note-tag-case-sensitivity (agreed: case-sensitive, v1)
    """
```

## Files Modified

| File | Change | Lines |
|------|--------|-------|
| `src/backend/api/notes.py` | Added `_normalize_and_validate_tag_names()` and `_escape_like_pattern()` helper functions; updated `_associate_tags()`, `associate_tag()`, and `search_notes()`; added docstrings with contract references | +150 |
| `src/backend/models.py` | Updated Tag class docstring to document case-sensitivity invariant and contract reference | +4 |
| `tests/test_tag_scenarios.py` | Updated 3 test assertions to be explicit and non-permissive; added clear failure messages; fixed docstrings to document expected behavior | +45 |

## Tests Passing

All three updated test assertions now fail with clear messages if the contract is violated:

1. ✅ `test_tag_names_with_whitespace_only_entries` — expects 400 Bad Request for whitespace-only tags
2. ✅ `test_tag_names_case_sensitivity_deduplication` — expects exactly 3 distinct case-sensitive tags with clear failure message
3. ✅ `test_post_associate_tag_with_whitespace_in_name` — expects 200 with normalized tag name (exact match: no raw spaces, no duplicate entries)

## Known Limitations

None. Implementation is complete per ticket acceptance.

## Cross-Domain Notes

- **Contract clarity:** Tag normalization is now explicit in contract-note-01KRXYD0 and contract-note-tag-case-sensitivity. Future maintainers (and new Tweedles) can reference these contracts to understand the non-negotiable semantics.
- **Search robustness:** The LIKE metacharacter escaping fix in `_escape_like_pattern()` prevents silent wrongness when users search for literals like "100%" or "a_b".
