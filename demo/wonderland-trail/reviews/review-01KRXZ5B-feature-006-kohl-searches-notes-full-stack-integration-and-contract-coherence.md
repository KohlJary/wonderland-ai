## Review 040: Feature 006 (Kohl searches notes) — Full-stack integration and contract coherence

**GUID:** 01KRXZ5BKMPAT9QMNEZ3CSC68D
**Files reviewed:** src/backend/api/notes.py, tests/test_tag_scenarios.py, tests/test_notes_edge_cases.py, src/backend/models.py
**Verdict:** request-changes

### Findings

#### block: _escape_like_pattern() escape-parameter contract is implicit, not enforced
**Location:** src/backend/api/notes.py:133-145
**Quote:**

```
def _escape_like_pattern(s: str) -> str:
    """Escape SQL LIKE metacharacters (%, _) so they are treated as literals.
    In SQLite LIKE:
    - % matches zero or more characters (wildcard)
    - _ matches exactly one character (wildcard)
    - \\ is the escape character (we use \\ to escape % and _)
    This function escapes % and _ so they match literally.
    Used for search queries to ensure user input doesn't accidentally use LIKE wildcards.
    """
    # Replace % with \%, _ with \_
    escaped = s.replace("\\", "\\\\")  # Escape existing backslashes first
    escaped = escaped.replace("%", "\\%")
    escaped = escaped.replace("_", "\\_")
    return escaped
```

**Read:** The function escapes % and _ in user input for SQLite LIKE pattern matching. Lines 408-412 correctly call ilike() with escape="\\" parameter. However, the escape-parameter requirement is implicit—documented but not enforced by the type system or assertion.
**Concern:** If a future developer calls ilike() with the result of _escape_like_pattern() but forgets to include escape="\\" in the ilike() call, the escaping silently fails and % or _ in user input will be treated as wildcards. This is a correctness bug waiting to happen. The contract between _escape_like_pattern() and its callers is unwritten and fragile.
**Request:** Add a runtime assertion or guard to enforce the escape-parameter contract. The cleanest approach: add a docstring note to _escape_like_pattern() stating "CRITICAL: Pattern returned from this function MUST be used with ilike(..., escape='\\\\') or escaping will be ineffective. Failure to include the escape parameter is a security issue." Alternatively, if ilike() is called in more than two places, consider wrapping ilike() in a helper function that enforces escape="\\" at the call site. For v1, a clear docstring is sufficient.

#### change-required: Test assertions lack failure messages for debugging in test_tag_scenarios.py
**Location:** tests/test_tag_scenarios.py:72, 76, 91, 106 (and others)
**Quote:**

```
assert len(note["tag_names"]) == 3
assert set(note["tag_names"]) == {"research", "Research", "RESEARCH"}
```

**Read:** Multiple assertions in test_tag_scenarios.py check contract-enforced behaviors (case-sensitivity, deduplication, whitespace normalization) but lack second-argument messages. When tests fail in CI, the error is just 'AssertionError' without context about expected vs. actual values.
**Concern:** This slows debugging. When a test fails in CI, a developer must re-run locally and add print() statements to understand what went wrong. The comparison file test_notes_edge_cases.py already includes detailed assertion messages; test_tag_scenarios.py should match that standard for consistency.
**Request:** Add failure messages to all assertions in test_tag_scenarios.py that currently lack them. Example: `assert len(note["tag_names"]) == 3, f"Expected 3 distinct tags after normalization, got {len(note['tag_names'])}: {note['tag_names']}"` and `assert set(note["tag_names"]) == {"research", "Research", "RESEARCH"}, f"Expected case-sensitive distinction between research/Research/RESEARCH, got {set(note['tag_names'])}"`  Scope: ~10 minutes, mechanical. Mirrors existing style in test_notes_edge_cases.py.

#### suggestion: Models.py timezone assumption for SQLite datetime is implicit
**Location:** src/backend/models.py:76-85
**Quote:**

```
def ensure_tz_aware(dt: datetime | None) -> str:
    """Convert datetime to UTC ISO8601 string with Z suffix.
    
    If dt is naive (no tzinfo), assume UTC.
    If dt is aware, convert to UTC.
    Always returns ISO8601 with explicit Z suffix for UTC.
    """
    if not dt:
        dt = datetime.now(timezone.utc)
    elif dt.tzinfo is None:
        # Naive datetime: assume UTC (SQLite doesn't track tz)
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        # Timezone-aware: convert to UTC
        dt = dt.astimezone(timezone.utc)
```

**Read:** The function converts datetime objects to UTC ISO8601 for JSON serialization. The key assumption is that SQLite's server_default=func.now() returns naive datetimes in UTC. The code handles three cases: None, naive (assume UTC), and aware (convert to UTC). This is correct and handles all cases, but the SQLite assumption is implicit.
**Concern:** The code is correct today, but the timezone assumption is coupled to SQLite's behavior. If SQLAlchemy or SQLite configuration ever changes, the assumption breaks silently. The comment on line 84 acknowledges this ("SQLite doesn't track tz") but a future maintainer might not see it or understand the contract.
**Request:** Add a contract note or clarifying comment that documents the assumption explicitly. For example, add to the docstring or as a separate comment in models.py: "Contract: This function assumes SQLite's func.now() returns naive UTC datetimes per SQLite convention. If the database configuration changes (e.g., to PostgreSQL or if SQLite is upgraded), this function requires re-migration to correctly handle timezones." This is documentation only; no code change needed.

#### note: _normalize_and_validate_tag_names() correctly enforces contract-note-01KRXYD0
**Location:** src/backend/api/notes.py:160-183
**Quote:**

```
def _normalize_and_validate_tag_names(tag_names: list[str]) -> list[str]:
    """Normalize and validate tag names per contract-note-01KRXYD0.
    
    Validation rules:
    1. Strip leading/trailing whitespace from each tag name
    2. Reject (raise HTTPException 400) any tag that after stripping is empty or whitespace-only
    3. Deduplicate by exact name match (case-sensitive)
    4. Return normalized, unique tag names
    Raises HTTPException 400 if any tag name is invalid.
    """
    normalized = []
    seen = set()
    
    for tag_name in tag_names:
        stripped = tag_name.strip()
        if not stripped:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag names cannot be empty or whitespace-only"
            )
        if stripped not in seen:
            normalized.append(stripped)
            seen.add(stripped)
    
    return normalized
```

**Read:** The function implements the three-step validation pipeline from contract-note-01KRXYD0: strip whitespace, reject empty-after-strip, deduplicate case-sensitive. Applied consistently in _associate_tags() and associate_tag(). The error handling is appropriate (HTTPException 400 with user-facing detail message).
**Concern:** None. This is well-written code that correctly enforces the contract boundary between client input and server storage.
**Request:** No action required. This is clean, correct implementation.

### Approvals

- Tag validation contract enforcement: _normalize_and_validate_tag_names() is a clean, well-decomposed implementation that correctly enforces contract-note-01KRXYD0. The three-step validation (strip, reject-empty, dedup) is the right semantic order and aligns with the binding contract.
- Test suite specificity: The test updates (test_tag_scenarios.py, test_notes_edge_cases.py) moved from uncertain multi-outcome assertions ('either this or that passes') to specific, contract-enforcing assertions. This is exactly right for v1 gate and serves as living documentation of what 'done' means.
- Search endpoint response shape: GET /api/search correctly returns body_preview (150-char truncation) instead of full body, matching the contract-note-008 optimization. Pagination shape, field names, and tag filtering semantics all match the negotiated contract.
- LIKE pattern escaping: User input is correctly escaped for SQLite LIKE matching via _escape_like_pattern(). The escape="\\" parameter usage in ilike() calls is correct (blocking finding above addresses the fragility of this implicit contract).
- Timestamp serialization: Models.py ensure_tz_aware() correctly converts to UTC and returns ISO8601 with Z suffix. Handles all three cases (None, naive, aware) and enforces a consistent serialization contract for the API.

### Cross-domain references

- Frontend Search.tsx should validate tag filter input (reject whitespace-only tag IDs, empty array) to mirror server-side validation. Not a blocker, but consistency between client and server validation rules prevents confusion.
- If tag autocomplete is added in v1.5 (fast-follow to contract-note-005), the autocomplete list should display normalized tag names (whitespace-stripped) to match the contract. Currently not relevant since v1 has no autocomplete, but document for future reference.
