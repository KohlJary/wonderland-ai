"""Tests for note CRUD endpoints: POST /api/notes, GET /api/notes/{id}.

Covers:
- Create note with title and body
- Create note with tags
- Retrieve note by id
- Error cases: missing title, not found
"""


def test_post_note_minimal(client):
    """POST /api/notes with title only — body and tags optional."""
    res = client.post("/api/notes", json={"title": "My note"})
    assert res.status_code == 201
    note = res.json()
    assert note["title"] == "My note"
    assert note["body"] == ""
    assert note["tag_names"] == []
    assert note["tag_ids"] == []
    assert note["id"] >= 1
    assert "created_at" in note
    assert "updated_at" in note


def test_post_note_with_body(client):
    """POST /api/notes with title and body."""
    res = client.post("/api/notes", json={"title": "Test", "body": "Some content"})
    assert res.status_code == 201
    note = res.json()
    assert note["title"] == "Test"
    assert note["body"] == "Some content"
    assert note["tag_names"] == []
    assert note["tag_ids"] == []
    assert note["id"] >= 1


def test_post_note_with_tags(client):
    """POST /api/notes with title and tags."""
    res = client.post(
        "/api/notes", json={"title": "Tagged note", "tag_names": ["research", "experiment"]}
    )
    assert res.status_code == 201
    note = res.json()
    assert note["title"] == "Tagged note"
    assert note["tag_names"] == ["research", "experiment"]
    assert len(note["tag_ids"]) == 2
    assert all(isinstance(tid, int) for tid in note["tag_ids"])


def test_post_note_with_body_and_tags(client):
    """POST /api/notes with all fields."""
    res = client.post(
        "/api/notes",
        json={
            "title": "Full note",
            "body": "This is the content",
            "tag_names": ["tag1", "tag2"],
        },
    )
    assert res.status_code == 201
    note = res.json()
    assert note["title"] == "Full note"
    assert note["body"] == "This is the content"
    assert note["tag_names"] == ["tag1", "tag2"]
    assert len(note["tag_ids"]) == 2
    assert all(isinstance(tid, int) for tid in note["tag_ids"])


def test_post_note_rejects_empty_title(client):
    """POST /api/notes with empty title — validation error."""
    res = client.post("/api/notes", json={"title": ""})
    assert res.status_code == 422  # pydantic validation


def test_post_note_rejects_missing_title(client):
    """POST /api/notes without title — validation error."""
    res = client.post("/api/notes", json={"body": "no title"})
    assert res.status_code == 422


def test_get_note_by_id(client):
    """GET /api/notes/{id} retrieves a created note."""
    # Create a note
    create_res = client.post("/api/notes", json={"title": "Test", "body": "Content"})
    assert create_res.status_code == 201
    created = create_res.json()
    note_id = created["id"]

    # Retrieve it
    get_res = client.get(f"/api/notes/{note_id}")
    assert get_res.status_code == 200
    retrieved = get_res.json()
    assert retrieved["id"] == note_id
    assert retrieved["title"] == "Test"
    assert retrieved["body"] == "Content"
    assert retrieved["created_at"] == created["created_at"]
    assert retrieved["updated_at"] == created["updated_at"]


def test_get_note_not_found(client):
    """GET /api/notes/{id} with nonexistent id — 404."""
    res = client.get("/api/notes/99999")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_timestamps_iso8601(client):
    """Note timestamps are ISO8601 strings."""
    res = client.post("/api/notes", json={"title": "Test"})
    assert res.status_code == 201
    note = res.json()
    
    # ISO8601 format check: should contain 'T' and end with 'Z' or +/-offset
    assert "T" in note["created_at"]
    assert ("Z" in note["created_at"] or "+" in note["created_at"] or "-" in note["created_at"][-6:])
    assert "T" in note["updated_at"]
    assert ("Z" in note["updated_at"] or "+" in note["updated_at"] or "-" in note["updated_at"][-6:])
