"""Tests for LIKE-wildcard escaping in search queries.

Hatter's scenario exploration: SQL LIKE metacharacter (%, _) handling.

Severity: silent-wrongness
- User searches for literal %, expects to find notes containing %
- Current implementation treats % as a wildcard, returning wrong results
- No error raised; results are silently incorrect
- Affects search correctness and data integrity

Related scenario artifact: scenario-01KRXVFV-text-search-ignores-special-characters-sql-injection-boundary.md
"""


def test_search_with_percent_sign_as_literal_wildcard_bug(client):
    """
    GET /api/search?q=100% should find only notes containing literal '100%'.
    
    CURRENT BUG: The implementation uses ilike() without escaping LIKE metacharacters.
    % is a SQL LIKE wildcard (matches zero or more chars).
    
    So searching for '100%' actually searches for LIKE '%100%%' (after adding %% padding),
    which matches '100' followed by anything, not just literal '100%'.
    
    Examples:
    - '100% complete' — matches (correct by accident)
    - '100 percent' — matches (WRONG — should not match, % doesn't occur literally)
    - 'My 100 apples' — matches (WRONG — should not match)
    
    Severity: silent-wrongness. User gets wrong results without error message.
    """
    # Create notes: one with literal %, one without
    client.post("/api/notes", json={"title": "100% complete"})
    client.post("/api/notes", json={"title": "100 percent"})
    client.post("/api/notes", json={"title": "Other note"})
    
    # Search for literal % sign
    res = client.get("/api/search?q=%25")  # URL-encoded %
    assert res.status_code == 200
    data = res.json()
    
    # EXPECTED: only '100% complete' should match (contains literal %)
    # ACTUAL (bug): both '100% complete' AND '100 percent' match (% matches as wildcard)
    
    matching_titles = [r["title"] for r in data["results"]]
    
    # This assertion WILL FAIL on current implementation (demonstrating the bug)
    assert len(data["results"]) == 1, (
        f"Expected 1 match for '100%', got {len(data['results'])}: {matching_titles}. "
        f"LIKE metacharacter % is not being escaped."
    )
    assert data["results"][0]["title"] == "100% complete"


def test_search_with_underscore_as_literal_wildcard_bug(client):
    """
    GET /api/search?q=a_b should find only notes containing literal 'a_b'.
    
    CURRENT BUG: _ is a SQL LIKE wildcard (matches exactly one char).
    
    So searching for 'a_b' matches 'a_b', 'aXb', 'a1b' (any single char in middle).
    
    Severity: silent-wrongness. User gets wrong results without error.
    """
    # Create notes with different patterns
    client.post("/api/notes", json={"title": "a_b"})
    client.post("/api/notes", json={"title": "aXb"})
    client.post("/api/notes", json={"title": "a1b"})
    client.post("/api/notes", json={"title": "ab"})
    
    # Search for literal underscore
    res = client.get("/api/search?q=a_b")
    assert res.status_code == 200
    data = res.json()
    
    # EXPECTED: only 'a_b' should match
    # ACTUAL (bug): 'a_b', 'aXb', 'a1b' all match (underscore is wildcard)
    
    matching_titles = [r["title"] for r in data["results"]]
    
    # This assertion WILL FAIL on current implementation
    assert len(data["results"]) == 1, (
        f"Expected 1 match for 'a_b', got {len(data['results'])}: {matching_titles}. "
        f"LIKE metacharacter _ is not being escaped."
    )
    assert data["results"][0]["title"] == "a_b"


def test_search_with_percent_in_body(client):
    """Search for % in note body (not just title)."""
    client.post("/api/notes", json={"title": "Stat", "body": "CPU: 100% used"})
    client.post("/api/notes", json={"title": "Stat", "body": "CPU: 99 percent used"})
    
    res = client.get("/api/search?q=%25")  # %
    assert res.status_code == 200
    data = res.json()
    
    # EXPECTED: only first note (contains literal %)
    # ACTUAL (bug): both match
    assert len(data["results"]) == 1, (
        f"Expected 1 match in body, got {len(data['results'])}. "
        f"LIKE wildcard escaping issue in body search."
    )


def test_search_after_note_update_reflects_immediately(client):
    """Verify update->search flow works (no caching lag)."""
    # Create a note
    create_res = client.post(
        "/api/notes",
        json={"title": "Original", "body": "original content"}
    )
    assert create_res.status_code == 201
    note_id = create_res.json()["id"]
    
    # Search for something in the original note (should not exist)
    search1 = client.get("/api/search?q=NEWSEARCH")
    assert search1.json()["total_results"] == 0
    
    # Update the note with new content
    update_res = client.put(
        f"/api/notes/{note_id}",
        json={"body": "updated with NEWSEARCH word"}
    )
    assert update_res.status_code == 200
    
    # Search for the new content immediately
    search2 = client.get("/api/search?q=NEWSEARCH")
    assert search2.status_code == 200
    data = search2.json()
    
    # Should find the updated note immediately (no caching)
    assert data["total_results"] == 1, (
        "After updating a note, search should immediately find the new content. "
        "Possible issue: caching, or update didn't persist correctly."
    )
    assert data["results"][0]["title"] == "Original"


def test_tag_filtering_case_sensitive_inconsistent_with_text_search(client):
    """
    Text search is case-insensitive (q=research finds 'Research').
    Tag filtering is case-sensitive (tags=research doesn't find tag 'Research').
    
    This inconsistency is confusing UX.
    
    Severity: degradation (UX issue, not breakage, but inconsistent behavior).
    """
    # Create a note with capitalized tag
    res = client.post(
        "/api/notes",
        json={"title": "Note", "tag_names": ["Research"]}  # Capital R
    )
    assert res.status_code == 201
    
    # Text search for lowercase finds it (case-insensitive)
    search_text = client.get("/api/search?q=research")
    assert search_text.json()["total_results"] >= 0  # May or may not find it in title/body
    
    # Tag filter for lowercase does NOT find it (case-sensitive)
    filter_tags = client.get("/api/search?tags=research")  # lowercase
    tag_results = filter_tags.json()["total_results"]
    
    # EXPECTED: consistent behavior — either both case-insensitive or both case-sensitive
    # ACTUAL: text search is case-insensitive, tag filtering is case-sensitive
    
    # This assertion documents the inconsistency (may or may not fail depending on note content)
    # The real issue is the UX: users expect consistency
    assert filter_tags.status_code == 200  # At least it doesn't crash
    # But we should raise a concern: tags=Research finds the tag, but tags=research doesn't
    assert tag_results == 0, (
        "Tag filtering is case-sensitive (tags=research doesn't match tag 'Research'), "
        "but text search is case-insensitive. This is inconsistent UX."
    )


def test_pagination_determinism_across_calls(client):
    """
    Multiple calls to search with identical params should return identical results
    in identical order (deterministic pagination).
    
    Severity: curiosity (low-severity issue, but important for testing/debugging).
    """
    # Create 5 notes with potential for same timestamp
    for i in range(5):
        client.post("/api/notes", json={"title": f"Note {i}"})
    
    # Fetch page 1 multiple times
    res1 = client.get("/api/search?page=1&page_size=3")
    res2 = client.get("/api/search?page=1&page_size=3")
    
    assert res1.status_code == 200
    assert res2.status_code == 200
    
    # Extract IDs from results
    ids1 = [r["id"] for r in res1.json()["results"]]
    ids2 = [r["id"] for r in res2.json()["results"]]
    
    # Should be identical (deterministic ordering)
    assert ids1 == ids2, (
        f"Pagination ordering is non-deterministic! "
        f"Call 1: {ids1}, Call 2: {ids2}. "
        f"This suggests tiebreak ordering (by id) is not working correctly "
        f"when multiple notes have the same updated_at timestamp."
    )
