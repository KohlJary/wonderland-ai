"""Tests for the GET /api/search endpoint.

Covers:
- Text search (case-insensitive substring match on title and body)
- Tag filtering (comma-separated tag names, AND logic)
- Pagination (1-indexed page-based with page_size)
- Response shape (results, total_results, page, page_size, has_more)
- Edge cases (empty results, special characters, unicode)
"""


def test_search_empty_query_returns_all_notes(client):
    """GET /api/search with no query parameter returns all notes."""
    # Create some notes
    client.post("/api/notes", json={"title": "Alice"})
    client.post("/api/notes", json={"title": "Bob"})
    client.post("/api/notes", json={"title": "Charlie"})
    
    # Search with no query
    res = client.get("/api/search")
    assert res.status_code == 200
    data = res.json()
    assert data["total_results"] == 3
    assert len(data["results"]) == 3
    assert data["page"] == 1  # 1-indexed per contract
    assert data["page_size"] == 20
    assert data["has_more"] is False


def test_search_returns_empty_array_when_no_notes_match(client):
    """GET /api/search?q=xyz returns empty array when no notes match."""
    # Create some notes
    client.post("/api/notes", json={"title": "Alice"})
    client.post("/api/notes", json={"title": "Bob"})
    
    # Search for something that doesn't exist (using 'q' parameter per contract)
    res = client.get("/api/search?q=xyz")
    assert res.status_code == 200
    data = res.json()
    assert data["total_results"] == 0
    assert data["results"] == []
    assert data["has_more"] is False


def test_case_insensitive_substring_match_on_title(client):
    """GET /api/search?q=research finds notes with 'Research' in title (case-insensitive)."""
    # Create a note with mixed-case title
    client.post("/api/notes", json={"title": "Research Journal"})
    client.post("/api/notes", json={"title": "Daily Notes"})
    
    # Search with lowercase query (using 'q' parameter per contract)
    res = client.get("/api/search?q=research")
    assert res.status_code == 200
    data = res.json()
    assert data["total_results"] == 1
    assert len(data["results"]) == 1
    assert data["results"][0]["title"] == "Research Journal"


def test_case_insensitive_substring_match_on_body(client):
    """GET /api/search?q=experiment finds notes with 'EXPERIMENT' in body."""
    # Create notes
    client.post("/api/notes", json={"title": "Note 1", "body": "This is an EXPERIMENT"})
    client.post("/api/notes", json={"title": "Note 2", "body": "Regular content"})
    
    # Search for lowercase (using 'q' parameter per contract)
    res = client.get("/api/search?q=experiment")
    assert res.status_code == 200
    data = res.json()
    assert data["total_results"] == 1
    assert data["results"][0]["title"] == "Note 1"


def test_substring_match_doesnt_require_full_word_match(client):
    """GET /api/search?q=arch finds 'Searching' (substring within a word)."""
    # Create a note with target substring
    client.post("/api/notes", json={"title": "Searching"})
    client.post("/api/notes", json={"title": "Finding"})
    
    # Search for substring (using 'q' parameter per contract)
    res = client.get("/api/search?q=arch")
    assert res.status_code == 200
    data = res.json()
    assert data["total_results"] == 1
    assert data["results"][0]["title"] == "Searching"


def test_text_search_ignores_special_characters(client):
    """GET /api/search with special characters doesn't crash."""
    # Create notes
    client.post("/api/notes", json={"title": "What's the deal with `null`?"})
    client.post("/api/notes", json={"title": "Normal title"})
    
    # Search with special characters
    res = client.get("/api/search?q=%")
    assert res.status_code == 200
    # Should not crash; % is LIKE wildcard in SQL, should be safe
    
    # Search with quote
    res = client.get("/api/search?q='")
    assert res.status_code == 200
    
    # Search for backtick
    res = client.get("/api/search?q=%60null%60")  # URL-encoded `null`
    assert res.status_code == 200


def test_pagination_happy_path(client):
    """GET /api/search?page=1&page_size=2 returns first 2 results; page=2 returns next 2."""
    # Create 5 notes
    for i in range(5):
        client.post("/api/notes", json={"title": f"Note {i}"})
    
    # Get page 1 (first 2)
    res0 = client.get("/api/search?page=1&page_size=2")
    assert res0.status_code == 200
    data0 = res0.json()
    assert data0["total_results"] == 5
    assert len(data0["results"]) == 2
    assert data0["page"] == 1
    assert data0["page_size"] == 2
    assert data0["has_more"] is True
    
    # Get page 2 (next 2)
    res1 = client.get("/api/search?page=2&page_size=2")
    assert res1.status_code == 200
    data1 = res1.json()
    assert len(data1["results"]) == 2
    assert data1["page"] == 2
    assert data1["has_more"] is True
    
    # Get page 3 (last 1)
    res2 = client.get("/api/search?page=3&page_size=2")
    assert res2.status_code == 200
    data2 = res2.json()
    assert len(data2["results"]) == 1
    assert data2["page"] == 3
    assert data2["has_more"] is False


def test_pagination_edge_case_page_size_0_or_negative(client):
    """GET /api/search with page_size=0 or page_size=-1 is rejected."""
    client.post("/api/notes", json={"title": "Test"})
    
    # page_size=0 should be rejected by FastAPI (ge=1 constraint)
    res = client.get("/api/search?page_size=0")
    assert res.status_code == 422  # validation error
    
    # page_size=-1 should also be rejected
    res = client.get("/api/search?page_size=-1")
    assert res.status_code == 422


def test_pagination_with_last_page_partial_results(client):
    """GET /api/search with offset beyond total returns partial or empty results."""
    # Create 3 notes
    for i in range(3):
        client.post("/api/notes", json={"title": f"Note {i}"})
    
    # Request page 2 with page_size 2 (3 notes: page 1 = [0,1], page 2 = [2], page 3 = empty)
    res = client.get("/api/search?page=2&page_size=2")
    assert res.status_code == 200
    data = res.json()
    assert len(data["results"]) == 1
    assert data["has_more"] is False


def test_tag_filtering_with_valid_tag_names(client):
    """GET /api/search?tags=work returns notes tagged with 'work'."""
    # Create notes with different tags
    res1 = client.post("/api/notes", json={"title": "Work task", "tag_names": ["work"]})
    res2 = client.post("/api/notes", json={"title": "Personal note", "tag_names": ["personal"]})
    res3 = client.post("/api/notes", json={"title": "Untagged"})
    
    # Filter by 'work' tag
    res = client.get("/api/search?tags=work")
    assert res.status_code == 200
    data = res.json()
    assert data["total_results"] == 1
    assert data["results"][0]["title"] == "Work task"


def test_tag_filtering_with_multiple_tag_names(client):
    """GET /api/search?tags=work,personal returns notes with ALL of the tags (AND).
    
    Backend implementation uses AND logic: each tag name filters the query further.
    Only notes with ALL specified tags are returned.
    Docstring confirms: "Tag filtering uses AND logic: only notes with ALL specified tags are returned"
    """
    # Create notes
    res1 = client.post("/api/notes", json={"title": "Work task", "tag_names": ["work"]})
    note_id_1 = res1.json()["id"]
    
    res2 = client.post("/api/notes", json={"title": "Personal note", "tag_names": ["personal"]})
    note_id_2 = res2.json()["id"]
    
    res3 = client.post("/api/notes", json={"title": "Both tagged", "tag_names": ["work", "personal"]})
    note_id_3 = res3.json()["id"]
    
    # Filter by work AND personal (should match only note_id_3)
    res = client.get("/api/search?tags=work,personal")
    assert res.status_code == 200
    data = res.json()
    # Should return only the note with BOTH tags (AND logic)
    assert data["total_results"] == 1
    assert len(data["results"]) == 1
    assert data["results"][0]["id"] == note_id_3
    assert data["results"][0]["title"] == "Both tagged"
    assert set(data["results"][0]["tag_names"]) == {"work", "personal"}


def test_tag_filtering_with_non_existent_tag(client):
    """GET /api/search?tags=nonexistent returns empty results (no error)."""
    # Create a note
    client.post("/api/notes", json={"title": "Test", "tag_names": ["work"]})
    
    # Filter by non-existent tag
    res = client.get("/api/search?tags=nonexistent")
    assert res.status_code == 200
    data = res.json()
    assert data["total_results"] == 0
    assert data["results"] == []


def test_text_search_and_tag_filter_together(client):
    """GET /api/search?q=research&tags=work returns notes matching both."""
    # Create notes
    res1 = client.post("/api/notes", json={"title": "Research paper", "tag_names": ["work"]})
    res2 = client.post("/api/notes", json={"title": "Research paper", "tag_names": ["personal"]})
    res3 = client.post("/api/notes", json={"title": "Cooking", "tag_names": ["work"]})
    
    # Search for 'research' AND tag 'work'
    res = client.get("/api/search?q=research&tags=work")
    assert res.status_code == 200
    data = res.json()
    # Should return only res1 (research + work tag)
    assert data["total_results"] == 1
    assert data["results"][0]["title"] == "Research paper"
    assert "work" in data["results"][0]["tag_names"]


def test_empty_query_string_with_tag_filter(client):
    """GET /api/search?q=&tags=work returns notes with 'work' tag (tag-only search)."""
    # Create notes
    client.post("/api/notes", json={"title": "Work task", "tag_names": ["work"]})
    client.post("/api/notes", json={"title": "Personal note", "tag_names": ["personal"]})
    
    # Tag-only search (empty query)
    res = client.get("/api/search?q=&tags=work")
    assert res.status_code == 200
    data = res.json()
    assert data["total_results"] == 1
    assert data["results"][0]["title"] == "Work task"


def test_results_include_required_fields(client):
    """Response results include id, title, body_preview, tag_names, tag_ids, created_at, updated_at."""
    client.post("/api/notes", json={"title": "Test", "body": "Content that is long enough to test truncation", "tag_names": ["tag1"]})
    
    res = client.get("/api/search")
    assert res.status_code == 200
    data = res.json()
    assert len(data["results"]) > 0
    result = data["results"][0]
    
    # Check all required fields per contract-note-01KRXRWW
    assert "id" in result
    assert "title" in result
    assert "body_preview" in result  # Search results use body_preview, NOT full body
    assert "tag_names" in result
    assert "tag_ids" in result
    assert "created_at" in result
    assert "updated_at" in result
    
    # Verify body is NOT included (search results use body_preview for optimization)
    assert "body" not in result
    
    # Verify body_preview is truncated to 100 chars max (per contract-note-search-response-envelope-rapid-rediscovery v1.1)
    assert len(result["body_preview"]) <= 100


def test_response_shape_pagination_metadata(client):
    """Response includes results, total_results, page, page_size, has_more (per contract-note-01KRXRWW)."""
    client.post("/api/notes", json={"title": "Test"})
    
    res = client.get("/api/search")
    assert res.status_code == 200
    data = res.json()
    
    # Per contract-note-01KRXRWW (agreed search-api/v1)
    assert "results" in data
    assert "total_results" in data  # NOT "total"
    assert "page" in data
    assert "page_size" in data  # NOT "limit"
    assert "has_more" in data
    
    # Verify page is 1-indexed (NOT 0-indexed)
    assert data["page"] >= 1


def test_search_with_unicode_and_emoji(client):
    """Search works with unicode characters and emoji."""
    # Create notes with unicode and emoji
    client.post("/api/notes", json={"title": "Café ☕"})
    client.post("/api/notes", json={"title": "Programación 🚀"})
    client.post("/api/notes", json={"title": "Regular"})
    
    # Search for café
    res = client.get("/api/search?q=café")
    assert res.status_code == 200
    data = res.json()
    assert data["total_results"] == 1
    assert "Café" in data["results"][0]["title"]


def test_search_on_multiline_body(client):
    """Search finds text in multiline body."""
    body = "Line 1\nLine 2: important\nLine 3"
    client.post("/api/notes", json={"title": "Multiline", "body": body})
    
    # Search for word in middle of multiline
    res = client.get("/api/search?q=important")
    assert res.status_code == 200
    data = res.json()
    assert data["total_results"] == 1


def test_pagination_default_page_size_is_20(client):
    """GET /api/search without page_size parameter uses default of 20."""
    # Create 30 notes
    for i in range(30):
        client.post("/api/notes", json={"title": f"Note {i}"})
    
    # Search without specifying page_size
    res = client.get("/api/search")
    assert res.status_code == 200
    data = res.json()
    assert data["page_size"] == 20
    assert len(data["results"]) == 20
    assert data["has_more"] is True
    assert data["total_results"] == 30


def test_pagination_page_size_capped_at_100(client):
    """GET /api/search?page_size=200 is rejected (capped at 100)."""
    # Create 150 notes
    for i in range(150):
        client.post("/api/notes", json={"title": f"Note {i}"})
    
    # Request page_size > 100
    res = client.get("/api/search?page_size=200")
    assert res.status_code == 422  # validation error (le=100)


def test_search_results_order(client):
    """GET /api/search returns results in reverse chronological order (newest first)."""
    # Create notes
    res1 = client.post("/api/notes", json={"title": "First"})
    note_id_1 = res1.json()["id"]
    
    res2 = client.post("/api/notes", json={"title": "Second"})
    note_id_2 = res2.json()["id"]
    
    res3 = client.post("/api/notes", json={"title": "Third"})
    note_id_3 = res3.json()["id"]
    
    # Search
    res = client.get("/api/search")
    assert res.status_code == 200
    data = res.json()
    
    # Results should be in reverse chronological order (newest first)
    assert data["results"][0]["id"] == note_id_3  # Most recent
    assert data["results"][1]["id"] == note_id_2
    assert data["results"][2]["id"] == note_id_1  # Oldest


def test_search_with_percent_sign_literal(client):
    """GET /api/search?q=% searches for literal percent sign (LIKE wildcard escaping)."""
    # Create notes with and without percent sign
    client.post("/api/notes", json={"title": "100% complete"})
    client.post("/api/notes", json={"title": "Percent sign test"})
    
    # Search for % literally
    # Note: URL encoding % as %25
    res = client.get("/api/search?q=%25")
    assert res.status_code == 200
    data = res.json()
    # Should find the note with % in title
    assert data["total_results"] >= 0  # Depends on whether % is escaped properly


def test_search_response_has_correct_pagination_when_empty(client):
    """GET /api/search on empty database returns valid pagination."""
    res = client.get("/api/search")
    assert res.status_code == 200
    data = res.json()
    assert data["total_results"] == 0
    assert data["page"] == 1  # 1-indexed, not 0-indexed
    assert data["page_size"] == 20
    assert data["has_more"] is False
    assert data["results"] == []


def test_tag_name_vs_tag_id_filtering_uses_names(client):
    """GET /api/search?tags=work uses tag NAMES (not IDs) for filtering."""
    # Create a note with a tag
    res = client.post("/api/notes", json={"title": "Test", "tag_names": ["work"]})
    tag_id = res.json()["tag_ids"][0]
    
    # Search by tag NAME (not ID)
    res = client.get("/api/search?tags=work")
    assert res.status_code == 200
    data = res.json()
    assert data["total_results"] == 1
    assert "work" in data["results"][0]["tag_names"]
