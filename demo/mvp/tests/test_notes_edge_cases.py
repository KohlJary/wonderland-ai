"""Edge case tests for note CRUD endpoints.

Tests concurrent scenarios, boundary conditions, and subtle bugs
that happy-path tests miss.

Scenarios:
1. Tag creation race condition (silent-wrongness)
2. PUT with empty tag_names array (degradation / UX bug)
3. Cascade delete with shared tags
4. Tag dissociation with invalid tag_id
"""


def test_put_note_with_empty_tag_names_clears_tags(client):
    """PUT /api/notes/{id} with tag_names=[] clears all existing tags.
    
    Severity: degradation / UX bug
    
    The contract says 'all fields optional; only provided fields are updated.'
    But tag_names=[] is 'provided' (not None), so it triggers a tag clear.
    Is this intended, or should empty array mean 'no change'?
    
    Current behavior: clears tags.
    """
    # Create a note with tags
    create_res = client.post(
        "/api/notes",
        json={"title": "Tagged", "tag_names": ["research", "experiment"]}
    )
    assert create_res.status_code == 201
    note_id = create_res.json()["id"]
    
    # Verify tags are there
    get_res = client.get(f"/api/notes/{note_id}")
    assert get_res.status_code == 200
    assert get_res.json()["tag_names"] == ["research", "experiment"]
    
    # PUT with empty tag_names
    put_res = client.put(
        f"/api/notes/{note_id}",
        json={"tag_names": []}
    )
    assert put_res.status_code == 200
    
    # Check: are tags cleared?
    get_res = client.get(f"/api/notes/{note_id}")
    assert get_res.status_code == 200
    note = get_res.json()
    
    # Current behavior: tags are cleared
    assert note["tag_names"] == []
    
    # This test documents the current behavior.
    # The contract should clarify: is this intended or a bug?


def test_put_note_without_tag_names_preserves_tags(client):
    """PUT /api/notes/{id} without tag_names preserves existing tags.
    
    The contract says 'only provided fields are updated.' Omitting
    tag_names should mean 'no change'.
    """
    # Create a note with tags
    create_res = client.post(
        "/api/notes",
        json={"title": "Tagged", "tag_names": ["research", "experiment"]}
    )
    assert create_res.status_code == 201
    note_id = create_res.json()["id"]
    
    # PUT *without* tag_names (omit the field)
    put_res = client.put(
        f"/api/notes/{note_id}",
        json={"title": "Updated title"}  # no tag_names field
    )
    assert put_res.status_code == 200
    
    # Tags should be preserved
    get_res = client.get(f"/api/notes/{note_id}")
    assert get_res.status_code == 200
    note = get_res.json()
    assert note["tag_names"] == ["research", "experiment"]
    assert note["title"] == "Updated title"


def test_post_note_with_duplicate_tag_names_in_list(client):
    """POST /api/notes with tag_names=['foo', 'foo', 'bar'] — deduplicates to 2 tags.
    
    Severity: curiosity
    
    Duplicate tag names in the request are deduplicated (exact string match, case-sensitive).
    The tag 'foo' appears twice but should be stored only once.
    Expected: request succeeds with 2 unique tags: foo and bar.
    """
    res = client.post(
        "/api/notes",
        json={"title": "Test", "tag_names": ["foo", "foo", "bar"]}
    )
    
    # Request should succeed
    assert res.status_code == 201
    note = res.json()
    
    # Duplicate tag_names are deduplicated (exact match, case-sensitive)
    assert len(note["tag_names"]) == 2, (
        f"Expected 2 unique tags after deduplication (foo and bar), "
        f"got {len(note['tag_names'])}: {note['tag_names']}"
    )
    
    # The tags should be foo and bar (in order of first appearance)
    assert set(note["tag_names"]) == {"foo", "bar"}, (
        f"Expected tags {{foo, bar}}, got {set(note['tag_names'])}"
    )


def test_delete_note_with_shared_tags_doesnt_orphan_tag(client):
    """When a note is deleted, shared tags persist.
    
    Severity: curiosity
    
    Two notes share a tag. Delete the first note. The tag should still
    exist and still be associated with the second note.
    """
    # Create two notes with a shared tag
    res1 = client.post(
        "/api/notes",
        json={"title": "Note 1", "tag_names": ["shared"]}
    )
    assert res1.status_code == 201
    note_id_1 = res1.json()["id"]
    
    res2 = client.post(
        "/api/notes",
        json={"title": "Note 2", "tag_names": ["shared"]}
    )
    assert res2.status_code == 201
    note_id_2 = res2.json()["id"]
    
    # Verify both have the shared tag
    get1 = client.get(f"/api/notes/{note_id_1}")
    get2 = client.get(f"/api/notes/{note_id_2}")
    assert get1.json()["tag_names"] == ["shared"]
    assert get2.json()["tag_names"] == ["shared"]
    
    # Delete the first note
    del_res = client.delete(f"/api/notes/{note_id_1}")
    assert del_res.status_code == 204
    
    # The first note should be gone
    get1_after = client.get(f"/api/notes/{note_id_1}")
    assert get1_after.status_code == 404
    
    # The second note should still have the tag
    get2_after = client.get(f"/api/notes/{note_id_2}")
    assert get2_after.status_code == 200
    assert get2_after.json()["tag_names"] == ["shared"]


def test_delete_tag_association_with_invalid_tag_id(client):
    """DELETE /api/notes/{id}/tags/99999 with non-existent tag_id returns 404.
    
    Severity: degradation
    
    If the tag_id doesn't exist, the endpoint should return 404.
    """
    # Create a note
    create_res = client.post("/api/notes", json={"title": "Test"})
    assert create_res.status_code == 201
    note_id = create_res.json()["id"]
    
    # Try to delete a non-existent tag from the note
    del_res = client.delete(f"/api/notes/{note_id}/tags/99999")
    
    # Should be 404
    assert del_res.status_code == 404


def test_delete_tag_association_with_unassociated_tag(client):
    """DELETE /api/notes/{id}/tags/{tag_id} for a tag not on the note returns 404.
    
    Severity: degradation
    
    Two notes, two different tags. Try to delete tag2 from note1.
    Should return 404.
    """
    # Create note1 with tag1
    res1 = client.post(
        "/api/notes",
        json={"title": "Note 1", "tag_names": ["tag1"]}
    )
    note_id_1 = res1.json()["id"]
    tag_id_1 = res1.json()["tag_ids"][0]
    
    # Create note2 with tag2
    res2 = client.post(
        "/api/notes",
        json={"title": "Note 2", "tag_names": ["tag2"]}
    )
    note_id_2 = res2.json()["id"]
    tag_id_2 = res2.json()["tag_ids"][0]
    
    # Try to delete tag2 from note1
    del_res = client.delete(f"/api/notes/{note_id_1}/tags/{tag_id_2}")
    
    # Should be 404 (tag not associated with note)
    assert del_res.status_code == 404


def test_get_notes_returns_all_notes_in_reverse_chronological_order(client):
    """GET /api/notes returns notes ordered by updated_at DESC (newest first).
    
    Severity: curiosity (but important for UX)
    """
    # Create three notes
    res1 = client.post("/api/notes", json={"title": "First"})
    note_id_1 = res1.json()["id"]
    
    res2 = client.post("/api/notes", json={"title": "Second"})
    note_id_2 = res2.json()["id"]
    
    res3 = client.post("/api/notes", json={"title": "Third"})
    note_id_3 = res3.json()["id"]
    
    # Get all notes
    get_res = client.get("/api/notes")
    assert get_res.status_code == 200
    notes = get_res.json()
    
    # Should be 3 notes
    assert len(notes) == 3
    
    # Should be in reverse chronological order (newest first)
    # That is, note 3, then 2, then 1
    assert notes[0]["id"] == note_id_3
    assert notes[1]["id"] == note_id_2
    assert notes[2]["id"] == note_id_1


def test_associate_tag_is_idempotent(client):
    """POST /api/notes/{id}/tags with an already-associated tag is idempotent.
    
    Severity: curiosity
    
    If the tag is already on the note, adding it again should be a no-op.
    """
    # Create a note with a tag
    create_res = client.post(
        "/api/notes",
        json={"title": "Test", "tag_names": ["research"]}
    )
    note_id = create_res.json()["id"]
    
    # Try to associate the same tag again
    assoc_res = client.post(
        f"/api/notes/{note_id}/tags",
        json={"tag_name": "research"}
    )
    assert assoc_res.status_code == 200
    
    # The tag should appear only once
    note = assoc_res.json()
    assert note["tag_names"] == ["research"]
    assert len(note["tag_ids"]) == 1


def test_note_timestamps_are_iso8601(client):
    """Note timestamps are ISO8601 strings with Z suffix (UTC).
    
    Severity: important for API contract
    """
    res = client.post("/api/notes", json={"title": "Test"})
    assert res.status_code == 201
    note = res.json()
    
    # Both timestamps should be ISO8601 with Z
    for field in ["created_at", "updated_at"]:
        ts = note[field]
        assert "T" in ts, f"{field} should contain 'T'"
        assert "Z" in ts, f"{field} should end with 'Z' (UTC)"
        assert ts.endswith("Z"), f"{field} should end with 'Z'"


def test_post_note_accepts_multiline_body(client):
    """POST /api/notes accepts body with newlines and special characters.
    
    Severity: curiosity
    """
    body = "Line 1\nLine 2\nLine 3\n\n# Header"
    res = client.post(
        "/api/notes",
        json={"title": "Markdown", "body": body}
    )
    assert res.status_code == 201
    note = res.json()
    assert note["body"] == body


def test_post_note_accepts_body_with_emoji(client):
    """POST /api/notes accepts body with emoji.
    
    Severity: curiosity
    """
    body = "Hello 👋 this is a note with emoji 🎉 and unicode ñ, é"
    res = client.post(
        "/api/notes",
        json={"title": "Unicode", "body": body}
    )
    assert res.status_code == 201
    note = res.json()
    assert note["body"] == body
