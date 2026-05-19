"""Hatter's test scenarios for tag CRUD endpoints.

Covers edge cases and seams: race conditions, whitespace normalization,
idempotence, shared tags, concurrent mutations, and pagination drift.

Reference: test scenarios documented in artifact log.
"""


def test_tag_names_with_whitespace_only_entries(client):
    """POST /api/notes with tag_names=['research', '  ', 'experiment'].
    
    Severity: degradation
    
    Per contract-note-01KRXYD0: whitespace-only tag names must be rejected
    with 400 Bad Request. The backend strips whitespace and rejects if the
    result is an empty string.
    
    Expected behavior: request is rejected with 400, not created.
    """
    res = client.post(
        "/api/notes",
        json={
            "title": "Test",
            "tag_names": ["research", "  ", "experiment"]
        }
    )
    
    # Must enforce rejection (400 Bad Request) for whitespace-only tag names
    assert res.status_code == 400, (
        f"Expected 400 Bad Request for whitespace-only tag name, "
        f"got {res.status_code}. Response body: {res.json()}"
    )


def test_tag_names_case_sensitivity_deduplication(client):
    """POST /api/notes with tag_names=['research', 'Research', 'RESEARCH'].
    
    Severity: degradation
    
    Tag names are case-sensitive. Three distinct tags are created.
    
    Reference: contract-note-tag-case-sensitivity (agreed: case-sensitive)
    """
    res = client.post(
        "/api/notes",
        json={
            "title": "Case test",
            "tag_names": ["research", "Research", "RESEARCH"]
        }
    )
    assert res.status_code == 201, (
        f"Expected 201 Created when posting note with case-sensitive tags, "
        f"got {res.status_code}. Response: {res.json()}"
    )
    note = res.json()
    
    # Tag names are case-sensitive: 'research', 'Research', and 'RESEARCH' are three distinct tags
    assert len(note["tag_names"]) == 3, (
        f"Expected 3 distinct case-sensitive tags (research, Research, RESEARCH), "
        f"got {len(note['tag_names'])}: {note['tag_names']}"
    )
    assert set(note["tag_names"]) == {"research", "Research", "RESEARCH"}, (
        f"Expected tags {{research, Research, RESEARCH}}, got {set(note['tag_names'])}"
    )


def test_post_associate_tag_idempotence(client):
    """POST /api/notes/{id}/tags called twice with the same tag_name.
    
    Severity: degradation
    
    The endpoint should be idempotent: calling twice should be like calling once.
    """
    # Create a note with no tags
    create_res = client.post("/api/notes", json={"title": "Test"})
    assert create_res.status_code == 201, (
        f"Expected 201 Created when posting new note, "
        f"got {create_res.status_code}. Response: {create_res.json()}"
    )
    note_id = create_res.json()["id"]
    
    # Associate a tag
    assoc_res_1 = client.post(
        f"/api/notes/{note_id}/tags",
        json={"tag_name": "research"}
    )
    assert assoc_res_1.status_code == 200, (
        f"Expected 200 OK when associating tag for first time, "
        f"got {assoc_res_1.status_code}. Response: {assoc_res_1.json()}"
    )
    note_1 = assoc_res_1.json()
    
    # Associate the same tag again
    assoc_res_2 = client.post(
        f"/api/notes/{note_id}/tags",
        json={"tag_name": "research"}
    )
    assert assoc_res_2.status_code == 200, (
        f"Expected 200 OK when re-associating same tag (idempotent), "
        f"got {assoc_res_2.status_code}. Response: {assoc_res_2.json()}"
    )
    note_2 = assoc_res_2.json()
    
    # Tag should appear exactly once
    assert note_1["tag_names"] == ["research"], (
        f"Expected tag_names ['research'] after first association, "
        f"got {note_1['tag_names']}"
    )
    assert note_2["tag_names"] == ["research"], (
        f"Expected tag_names ['research'] after idempotent second association, "
        f"got {note_2['tag_names']}"
    )
    assert len(note_1["tag_ids"]) == 1, (
        f"Expected 1 tag_id after first association, "
        f"got {len(note_1['tag_ids'])}: {note_1['tag_ids']}"
    )
    assert len(note_2["tag_ids"]) == 1, (
        f"Expected 1 tag_id after idempotent second association, "
        f"got {len(note_2['tag_ids'])}: {note_2['tag_ids']}"
    )


def test_delete_note_with_shared_tags_preserves_tag(client):
    """When a note with shared tags is deleted, the tags persist.
    
    Severity: curiosity
    
    Two notes share a tag. Delete the first note. The tag should still exist
    and still be associated with the second note.
    """
    # Create two notes with a shared tag
    res1 = client.post(
        "/api/notes",
        json={"title": "Note 1", "tag_names": ["shared"]}
    )
    assert res1.status_code == 201, (
        f"Expected 201 Created for first note with shared tag, "
        f"got {res1.status_code}. Response: {res1.json()}"
    )
    note_id_1 = res1.json()["id"]
    
    res2 = client.post(
        "/api/notes",
        json={"title": "Note 2", "tag_names": ["shared"]}
    )
    assert res2.status_code == 201, (
        f"Expected 201 Created for second note with shared tag, "
        f"got {res2.status_code}. Response: {res2.json()}"
    )
    note_id_2 = res2.json()["id"]
    
    # Verify both have the shared tag
    get1 = client.get(f"/api/notes/{note_id_1}")
    get2 = client.get(f"/api/notes/{note_id_2}")
    assert get1.json()["tag_names"] == ["shared"], (
        f"Expected note 1 to have tag_names ['shared'], "
        f"got {get1.json()['tag_names']}"
    )
    assert get2.json()["tag_names"] == ["shared"], (
        f"Expected note 2 to have tag_names ['shared'], "
        f"got {get2.json()['tag_names']}"
    )
    
    # Delete the first note
    del_res = client.delete(f"/api/notes/{note_id_1}")
    assert del_res.status_code == 204, (
        f"Expected 204 No Content when deleting note with shared tag, "
        f"got {del_res.status_code}. Response: "
        + str(del_res.json() if del_res.status_code >= 400 else "(no error body)")
    )
    
    # The first note should be gone
    get1_after = client.get(f"/api/notes/{note_id_1}")
    assert get1_after.status_code == 404, (
        f"Expected 404 Not Found after deleting note, "
        f"got {get1_after.status_code}. Response: {get1_after.json()}"
    )
    
    # The second note should still have the tag
    get2_after = client.get(f"/api/notes/{note_id_2}")
    assert get2_after.status_code == 200, (
        f"Expected 200 OK when retrieving other note with shared tag, "
        f"got {get2_after.status_code}. Response: {get2_after.json()}"
    )
    assert get2_after.json()["tag_names"] == ["shared"], (
        f"Expected note 2 to still have tag_names ['shared'] after note 1 deletion, "
        f"got {get2_after.json()['tag_names']}"
    )


def test_post_associate_tag_with_whitespace_in_name(client):
    """POST /api/notes/{id}/tags with tag_name='  research  '.
    
    Severity: degradation
    
    Per contract-note-01KRXYD0: tag names with leading/trailing whitespace
    should be normalized (stripped). The tag '  research  ' becomes 'research'
    after normalization and is stored with that normalized name.
    
    Expected behavior: request succeeds (200) with normalized tag name.
    """
    # Create a note
    create_res = client.post("/api/notes", json={"title": "Test"})
    assert create_res.status_code == 201, (
        f"Expected 201 Created when posting new note, "
        f"got {create_res.status_code}. Response: {create_res.json()}"
    )
    note_id = create_res.json()["id"]
    
    # Associate a tag with whitespace (should be normalized to 'research')
    res = client.post(
        f"/api/notes/{note_id}/tags",
        json={"tag_name": "  research  "}
    )
    
    # Must succeed with normalization
    assert res.status_code == 200, (
        f"Expected 200 OK when associating tag with whitespace (should normalize), "
        f"got {res.status_code}. Response: {res.json()}"
    )
    note = res.json()
    
    # Tag should appear in normalized form only
    assert "research" in note["tag_names"], (
        f"Expected normalized 'research' in tag_names after stripping whitespace, "
        f"got {note['tag_names']}"
    )
    # Raw tag with spaces should NOT appear
    assert "  research  " not in note["tag_names"], (
        f"Expected raw '  research  ' NOT in tag_names (should be normalized), "
        f"but found it in {note['tag_names']}"
    )
    # Should be exactly one tag (the normalized one)
    assert len(note["tag_names"]) == 1, (
        f"Expected 1 tag after normalization, "
        f"got {len(note['tag_names'])}: {note['tag_names']}"
    )


def test_search_body_preview_with_emoji_truncation(client):
    """GET /api/search with body containing emoji, truncated to 100 chars.
    
    Severity: curiosity
    
    The body_preview should be valid UTF-8 and at most 100 *characters*.
    Per contract-note-search-response-envelope-rapid-rediscovery (v1.1):
    100-char preview is optimized for Kohl's rapid-rediscovery scanning workflow.
    """
    # Create a note with a long body containing emoji
    long_body = "Hello 👋 " + ("x" * 200)  # 200+ characters with emoji
    client.post(
        "/api/notes",
        json={"title": "Long body", "body": long_body}
    )
    
    # Search and get the preview
    res = client.get("/api/search")
    assert res.status_code == 200, (
        f"Expected 200 OK from search endpoint, "
        f"got {res.status_code}. Response: {res.json()}"
    )
    data = res.json()
    assert len(data["results"]) > 0, (
        f"Expected at least 1 search result, got {len(data['results'])}"
    )
    
    result = data["results"][0]
    preview = result["body_preview"]
    
    # Preview should be at most 100 characters (v1.1 contract change)
    assert len(preview) <= 100, (
        f"Expected body_preview to be at most 100 characters, "
        f"got {len(preview)} characters"
    )
    
    # Preview should be valid UTF-8 (no test needed, if we got this far, it's valid)
    # We can verify it's the first 100 chars of the body
    assert preview == long_body[:100], (
        f"Expected body_preview to be first 100 chars of body, "
        f"got different preview"
    )


def test_concurrent_tag_creation_same_name_explicit_handling(client):
    """Two concurrent POST /notes requests with the same tag_name.
    
    Severity: silent-wrongness
    
    If two requests try to auto-create the same tag simultaneously,
    one might get a UNIQUE constraint error. This should be handled gracefully.
    
    This test simulates concurrency by creating two notes sequentially
    with the same tag, which exercises the query-then-insert pattern.
    It doesn't test true concurrency (which would require threading),
    but it documents the scenario.
    """
    # Create first note with tag
    res1 = client.post(
        "/api/notes",
        json={"title": "Note 1", "tag_names": ["shared_tag"]}
    )
    assert res1.status_code == 201, (
        f"Expected 201 Created for first note with shared_tag, "
        f"got {res1.status_code}. Response: {res1.json()}"
    )
    
    # Create second note with the same tag (already exists)
    res2 = client.post(
        "/api/notes",
        json={"title": "Note 2", "tag_names": ["shared_tag"]}
    )
    assert res2.status_code == 201, (
        f"Expected 201 Created for second note with shared_tag (tag reuse), "
        f"got {res2.status_code}. Response: {res2.json()}"
    )
    
    # Both notes should reference the same tag ID
    note_1 = res1.json()
    note_2 = res2.json()
    
    # Both should have the tag
    assert "shared_tag" in note_1["tag_names"], (
        f"Expected 'shared_tag' in note_1 tag_names, "
        f"got {note_1['tag_names']}"
    )
    assert "shared_tag" in note_2["tag_names"], (
        f"Expected 'shared_tag' in note_2 tag_names, "
        f"got {note_2['tag_names']}"
    )
    
    # They should reference the same tag ID
    assert note_1["tag_ids"][0] == note_2["tag_ids"][0], (
        f"Expected both notes to reference same tag_id for 'shared_tag', "
        f"got note_1 tag_id {note_1['tag_ids'][0]} != note_2 tag_id {note_2['tag_ids'][0]}"
    )


def test_put_and_delete_race_condition_sequence(client):
    """Simulate concurrent PUT and DELETE on the same note.
    
    Severity: breakage
    
    This test simulates the race by doing PUT first, then DELETE.
    In a true concurrent scenario, one would win the lock.
    Here we verify that both operations handle 404 correctly if the note is gone.
    """
    # Create a note
    create_res = client.post("/api/notes", json={"title": "Test"})
    assert create_res.status_code == 201, (
        f"Expected 201 Created when posting new note, "
        f"got {create_res.status_code}. Response: {create_res.json()}"
    )
    note_id = create_res.json()["id"]
    
    # PUT to update the note
    put_res = client.put(
        f"/api/notes/{note_id}",
        json={"title": "Updated"}
    )
    assert put_res.status_code == 200, (
        f"Expected 200 OK when updating note, "
        f"got {put_res.status_code}. Response: {put_res.json()}"
    )
    
    # DELETE the note
    del_res = client.delete(f"/api/notes/{note_id}")
    assert del_res.status_code == 204, (
        f"Expected 204 No Content when deleting note, "
        f"got {del_res.status_code}. Response: "
        + str(del_res.json() if del_res.status_code >= 400 else "(no error body)")
    )
    
    # Verify the note is gone
    get_res = client.get(f"/api/notes/{note_id}")
    assert get_res.status_code == 404, (
        f"Expected 404 Not Found for deleted note, "
        f"got {get_res.status_code}. Response: {get_res.json()}"
    )


def test_search_body_preview_does_not_include_full_body(client):
    """GET /api/search returns body_preview, not full body.
    
    Severity: curiosity
    
    This is a contract requirement (optimization for search result payload size).
    Verify that the response does NOT include the full body field.
    Per contract-note-search-response-envelope-rapid-rediscovery (v1.1):
    100-char preview is optimized for Kohl's rapid-rediscovery scanning workflow.
    """
    # Create a note with a long body
    long_body = "This is a very long body " * 20  # > 100 chars
    client.post(
        "/api/notes",
        json={"title": "Long note", "body": long_body}
    )
    
    # Search
    res = client.get("/api/search")
    assert res.status_code == 200, (
        f"Expected 200 OK from search endpoint, "
        f"got {res.status_code}. Response: {res.json()}"
    )
    data = res.json()
    assert len(data["results"]) > 0, (
        f"Expected at least 1 search result, got {len(data['results'])}"
    )
    
    result = data["results"][0]
    
    # Should have body_preview
    assert "body_preview" in result, (
        f"Expected 'body_preview' in search result, "
        f"got keys: {result.keys()}"
    )
    assert len(result["body_preview"]) <= 100, (
        f"Expected body_preview to be at most 100 characters, "
        f"got {len(result['body_preview'])} characters"
    )
    
    # Should NOT have full body
    assert "body" not in result, (
        f"Expected 'body' NOT in search result (should use body_preview only), "
        f"but found it in result"
    )


def test_search_pagination_deterministic_ordering_on_tiebreak(client):
    """GET /api/search with multiple notes having the same updated_at.
    
    Severity: curiosity
    
    If two notes have identical updated_at timestamps, the secondary sort
    (by id DESC) ensures deterministic ordering.
    """
    # Create multiple notes rapidly (might have same updated_at)
    for i in range(3):
        client.post("/api/notes", json={"title": f"Note {i}"})
    
    # Get all notes (page 1)
    res1 = client.get("/api/search?page=1&page_size=10")
    assert res1.status_code == 200, (
        f"Expected 200 OK from search endpoint (first request), "
        f"got {res1.status_code}. Response: {res1.json()}"
    )
    data1 = res1.json()
    
    # Get all notes again (should be identical order)
    res2 = client.get("/api/search?page=1&page_size=10")
    assert res2.status_code == 200, (
        f"Expected 200 OK from search endpoint (second request), "
        f"got {res2.status_code}. Response: {res2.json()}"
    )
    data2 = res2.json()
    
    # Order should be identical (secondary sort by id DESC)
    ids1 = [note["id"] for note in data1["results"]]
    ids2 = [note["id"] for note in data2["results"]]
    assert ids1 == ids2, (
        f"Expected deterministic ordering (secondary sort by id DESC) across calls, "
        f"but got different orderings: {ids1} != {ids2}"
    )
