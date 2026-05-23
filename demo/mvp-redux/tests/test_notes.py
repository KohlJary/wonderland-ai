"""Test suite for CRUD endpoints: POST, GET, GET/{id}, PUT, DELETE.

Tests verify:
- All five endpoints return correct status codes for valid inputs
- Endpoints reject invalid input (missing title, etc.) with 400 + error message
- GET /notes returns notes in updated_at descending order
- Notes created in one request are retrievable in the next
- DELETE actually removes the note (follow-up GET returns 404)
- Error responses match contract-note-01KSA5NS shape
"""

import json

import pytest
from fastapi.testclient import TestClient


class TestCreateNote:
    """POST /api/notes — create a note."""

    def test_create_note_success(self, client: TestClient):
        """POST /api/notes with valid input returns 201 Created with created note."""
        payload = {
            "title": "My First Note",
            "body": "This is the body.",
            "tags": ["python", "notes"],
        }
        response = client.post("/api/notes", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["title"] == "My First Note"
        assert data["body"] == "This is the body."
        assert data["tags"] == ["python", "notes"]
        assert data["created_at"] is not None
        assert data["updated_at"] is not None

    def test_create_note_minimal(self, client: TestClient):
        """POST /api/notes with only title (body and tags optional) returns 201 Created."""
        payload = {
            "title": "Minimal Note",
        }
        response = client.post("/api/notes", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Minimal Note"
        assert data["body"] == ""
        assert data["tags"] == []

    def test_create_note_missing_title(self, client: TestClient):
        """POST /api/notes without title returns 422 (validation error)."""
        payload = {
            "body": "No title provided",
        }
        response = client.post("/api/notes", json=payload)
        assert response.status_code == 422

    def test_create_note_empty_title(self, client: TestClient):
        """POST /api/notes with empty title returns 422 (min_length=1)."""
        payload = {
            "title": "",
            "body": "Body text",
        }
        response = client.post("/api/notes", json=payload)
        assert response.status_code == 422

    def test_create_note_with_tags(self, client: TestClient):
        """POST /api/notes stores tags as JSON array, returns 201 Created."""
        payload = {
            "title": "Tagged Note",
            "body": "Content",
            "tags": ["tag1", "tag2", "tag3"],
        }
        response = client.post("/api/notes", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["tags"] == ["tag1", "tag2", "tag3"]


class TestGetNotes:
    """GET /api/notes — list all notes."""

    def test_get_notes_empty_list(self, client: TestClient):
        """GET /api/notes on empty database returns empty list."""
        response = client.get("/api/notes")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_notes_single(self, client: TestClient):
        """GET /api/notes with one note."""
        # Create a note
        create_payload = {"title": "Note 1", "body": "Body 1"}
        client.post("/api/notes", json=create_payload)

        # Get all notes
        response = client.get("/api/notes")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Note 1"

    def test_get_notes_ordered_by_updated_at_desc(self, client: TestClient):
        """GET /api/notes returns notes ordered by updated_at descending."""
        # Create multiple notes
        titles = ["Note 1", "Note 2", "Note 3"]
        for title in titles:
            client.post("/api/notes", json={"title": title, "body": f"Body: {title}"})

        # Get all notes
        response = client.get("/api/notes")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Last created should be first in response (updated_at descending)
        assert data[0]["title"] == "Note 3"
        assert data[1]["title"] == "Note 2"
        assert data[2]["title"] == "Note 1"


class TestGetNoteById:
    """GET /api/notes/{id} — fetch a single note by id."""

    def test_get_note_success(self, client: TestClient):
        """GET /api/notes/{id} with valid id returns the note."""
        # Create a note
        create_response = client.post(
            "/api/notes", json={"title": "Test Note", "body": "Test Body"}
        )
        note_id = create_response.json()["id"]

        # Get the note
        response = client.get(f"/api/notes/{note_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == note_id
        assert data["title"] == "Test Note"
        assert data["body"] == "Test Body"

    def test_get_note_not_found(self, client: TestClient):
        """GET /api/notes/{id} with invalid id returns 404."""
        response = client.get("/api/notes/999999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Note not found"

    def test_get_note_preserves_tags(self, client: TestClient):
        """GET /api/notes/{id} returns tags correctly."""
        # Create a note with tags
        create_response = client.post(
            "/api/notes",
            json={"title": "Tagged", "body": "Body", "tags": ["a", "b", "c"]},
        )
        note_id = create_response.json()["id"]

        # Get the note
        response = client.get(f"/api/notes/{note_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["tags"] == ["a", "b", "c"]


class TestUpdateNote:
    """PUT /api/notes/{id} — update a note."""

    def test_update_note_success(self, client: TestClient):
        """PUT /api/notes/{id} with valid input returns updated note."""
        # Create a note
        create_response = client.post(
            "/api/notes", json={"title": "Original", "body": "Original Body"}
        )
        note_id = create_response.json()["id"]

        # Update the note
        update_payload = {
            "title": "Updated Title",
            "body": "Updated Body",
            "tags": ["updated"],
        }
        response = client.put(f"/api/notes/{note_id}", json=update_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == note_id
        assert data["title"] == "Updated Title"
        assert data["body"] == "Updated Body"
        assert data["tags"] == ["updated"]

    def test_update_note_not_found(self, client: TestClient):
        """PUT /api/notes/{id} with invalid id returns 404."""
        payload = {"title": "Updated", "body": "Body"}
        response = client.put("/api/notes/999999", json=payload)
        assert response.status_code == 404
        assert response.json()["detail"] == "Note not found"

    def test_update_note_missing_title(self, client: TestClient):
        """PUT /api/notes/{id} without title returns 422."""
        # Create a note
        create_response = client.post(
            "/api/notes", json={"title": "Original", "body": "Body"}
        )
        note_id = create_response.json()["id"]

        # Try to update without title
        response = client.put(f"/api/notes/{note_id}", json={"body": "New Body"})
        assert response.status_code == 422

    def test_update_note_partial(self, client: TestClient):
        """PUT /api/notes/{id} can update fields independently."""
        # Create a note with tags
        create_response = client.post(
            "/api/notes",
            json={"title": "Original", "body": "Original Body", "tags": ["old"]},
        )
        note_id = create_response.json()["id"]

        # Update only title
        response = client.put(
            f"/api/notes/{note_id}",
            json={"title": "New Title", "body": "Original Body", "tags": ["old"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["body"] == "Original Body"
        assert data["tags"] == ["old"]

    def test_update_note_updates_updated_at(self, client: TestClient):
        """PUT /api/notes/{id} updates the updated_at timestamp."""
        # Create a note
        create_response = client.post(
            "/api/notes", json={"title": "Original", "body": "Body"}
        )
        created_data = create_response.json()
        note_id = created_data["id"]
        original_updated_at = created_data["updated_at"]

        # Update the note
        response = client.put(
            f"/api/notes/{note_id}",
            json={"title": "Updated", "body": "Updated Body"},
        )
        updated_data = response.json()

        # updated_at should be different (later)
        assert updated_data["updated_at"] != original_updated_at
        # created_at should be the same
        assert updated_data["created_at"] == created_data["created_at"]


class TestDeleteNote:
    """DELETE /api/notes/{id} — delete a note."""

    def test_delete_note_success(self, client: TestClient):
        """DELETE /api/notes/{id} with valid id deletes the note."""
        # Create a note
        create_response = client.post(
            "/api/notes", json={"title": "To Delete", "body": "Body"}
        )
        note_id = create_response.json()["id"]

        # Delete the note
        response = client.delete(f"/api/notes/{note_id}")
        assert response.status_code == 204

        # Verify the note is gone
        get_response = client.get(f"/api/notes/{note_id}")
        assert get_response.status_code == 404

    def test_delete_note_not_found(self, client: TestClient):
        """DELETE /api/notes/{id} with invalid id returns 404."""
        response = client.delete("/api/notes/999999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Note not found"

    def test_delete_note_removes_from_list(self, client: TestClient):
        """DELETE removes the note from GET /api/notes list."""
        # Create two notes
        create1 = client.post(
            "/api/notes", json={"title": "Note 1", "body": "Body 1"}
        )
        create2 = client.post(
            "/api/notes", json={"title": "Note 2", "body": "Body 2"}
        )
        note_id_1 = create1.json()["id"]
        note_id_2 = create2.json()["id"]

        # Verify both exist
        list_response = client.get("/api/notes")
        assert len(list_response.json()) == 2

        # Delete the first note
        delete_response = client.delete(f"/api/notes/{note_id_1}")
        assert delete_response.status_code == 204

        # Verify only the second note remains
        list_response = client.get("/api/notes")
        data = list_response.json()
        assert len(data) == 1
        assert data[0]["id"] == note_id_2


class TestCrudFlow:
    """Integration tests for complete CRUD flow."""

    def test_full_lifecycle(self, client: TestClient):
        """Create, read, update, delete a note in sequence."""
        # Create
        create_response = client.post(
            "/api/notes",
            json={
                "title": "Lifecycle Test",
                "body": "Initial body",
                "tags": ["test"],
            },
        )
        assert create_response.status_code == 201
        note = create_response.json()
        note_id = note["id"]
        assert note["title"] == "Lifecycle Test"

        # Read
        get_response = client.get(f"/api/notes/{note_id}")
        assert get_response.status_code == 200
        assert get_response.json()["title"] == "Lifecycle Test"

        # Update
        update_response = client.put(
            f"/api/notes/{note_id}",
            json={
                "title": "Updated Lifecycle Test",
                "body": "Updated body",
                "tags": ["test", "updated"],
            },
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["title"] == "Updated Lifecycle Test"
        assert updated["body"] == "Updated body"
        assert updated["tags"] == ["test", "updated"]

        # Delete
        delete_response = client.delete(f"/api/notes/{note_id}")
        assert delete_response.status_code == 204

        # Verify deleted
        get_response = client.get(f"/api/notes/{note_id}")
        assert get_response.status_code == 404

    def test_multiple_notes_lifecycle(self, client: TestClient):
        """Create multiple notes, verify ordering, update one, delete another."""
        # Create 3 notes
        ids = []
        for i in range(1, 4):
            response = client.post(
                "/api/notes",
                json={"title": f"Note {i}", "body": f"Body {i}", "tags": [f"tag{i}"]},
            )
            ids.append(response.json()["id"])

        # Verify list ordering (most recent first)
        list_response = client.get("/api/notes")
        notes = list_response.json()
        assert len(notes) == 3
        assert notes[0]["id"] == ids[2]  # Last created
        assert notes[1]["id"] == ids[1]
        assert notes[2]["id"] == ids[0]  # First created

        # Update the middle note
        update_response = client.put(
            f"/api/notes/{ids[1]}",
            json={"title": "Note 2 Updated", "body": "Body 2 Updated"},
        )
        assert update_response.status_code == 200

        # Verify list ordering changed (updated note is now most recent)
        list_response = client.get("/api/notes")
        notes = list_response.json()
        assert notes[0]["id"] == ids[1]  # Most recently updated

        # Delete the first note
        delete_response = client.delete(f"/api/notes/{ids[0]}")
        assert delete_response.status_code == 204

        # Verify it's gone
        list_response = client.get("/api/notes")
        notes = list_response.json()
        assert len(notes) == 2
        assert all(note["id"] != ids[0] for note in notes)
