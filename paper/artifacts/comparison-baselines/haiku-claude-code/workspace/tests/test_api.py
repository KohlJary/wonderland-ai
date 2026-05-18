import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend import models  # Import models to ensure tables are defined
from backend.database import Base, set_session_local
from backend import main

# Use in-memory SQLite for tests
# Important: Use a single shared connection for in-memory SQLite
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=None,  # Disable connection pooling for in-memory SQLite
    # Actually, we need to use NullPool to avoid connection issues
)
from sqlalchemy.pool import StaticPool
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # Use StaticPool to reuse the same connection
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Create all tables in the test database
Base.metadata.create_all(bind=test_engine)

# Override the session factory
set_session_local(TestingSessionLocal)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


client = TestClient(main.app)


@pytest.fixture(autouse=True)
def reset_db():
    """Reset the database before each test."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield


def test_health():
    """Test health endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_note():
    """Test creating a new note."""
    note_data = {
        "title": "Test Note",
        "body": "# This is a test\n\nWith some markdown.",
        "tags": ["testing"],
    }
    response = client.post("/api/notes", json=note_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Note"
    assert data["body"] == "# This is a test\n\nWith some markdown."
    assert len(data["tags"]) == 1
    assert data["tags"][0]["name"] == "testing"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_note_without_tags():
    """Test creating a note without tags."""
    note_data = {
        "title": "No Tags Note",
        "body": "Just some content",
        "tags": [],
    }
    response = client.post("/api/notes", json=note_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "No Tags Note"
    assert len(data["tags"]) == 0


def test_list_notes():
    """Test listing all notes."""
    # Create two notes
    client.post("/api/notes", json={"title": "Note 1", "body": "Body 1", "tags": []})
    client.post("/api/notes", json={"title": "Note 2", "body": "Body 2", "tags": []})

    response = client.get("/api/notes")
    assert response.status_code == 200
    notes = response.json()
    assert len(notes) == 2
    # Most recent first
    assert notes[0]["title"] == "Note 2"
    assert notes[1]["title"] == "Note 1"


def test_list_notes_sorted_by_updated_at():
    """Test that notes are sorted by updated_at descending."""
    # Create first note
    resp1 = client.post("/api/notes", json={"title": "First", "body": "Body 1", "tags": []})
    note1_id = resp1.json()["id"]

    # Create second note
    resp2 = client.post("/api/notes", json={"title": "Second", "body": "Body 2", "tags": []})
    note2_id = resp2.json()["id"]

    # Update first note to make it most recent
    client.put(
        f"/api/notes/{note1_id}",
        json={"title": "First Updated", "body": "Updated body", "tags": []},
    )

    response = client.get("/api/notes")
    notes = response.json()
    assert notes[0]["title"] == "First Updated"
    assert notes[1]["title"] == "Second"


def test_get_note():
    """Test getting a specific note."""
    create_resp = client.post("/api/notes", json={"title": "Test", "body": "Content", "tags": []})
    note_id = create_resp.json()["id"]

    response = client.get(f"/api/notes/{note_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == note_id
    assert data["title"] == "Test"


def test_get_nonexistent_note():
    """Test getting a note that doesn't exist."""
    response = client.get("/api/notes/9999")
    assert response.status_code == 404


def test_update_note():
    """Test updating a note."""
    create_resp = client.post("/api/notes", json={"title": "Original", "body": "Original body", "tags": ["old"]})
    note_id = create_resp.json()["id"]

    update_resp = client.put(
        f"/api/notes/{note_id}",
        json={"title": "Updated", "body": "Updated body", "tags": ["new", "updated"]},
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["title"] == "Updated"
    assert data["body"] == "Updated body"
    assert len(data["tags"]) == 2
    tag_names = {tag["name"] for tag in data["tags"]}
    assert tag_names == {"new", "updated"}


def test_delete_note():
    """Test deleting a note."""
    create_resp = client.post("/api/notes", json={"title": "To Delete", "body": "Content", "tags": []})
    note_id = create_resp.json()["id"]

    response = client.delete(f"/api/notes/{note_id}")
    assert response.status_code == 200

    # Verify it's gone
    get_resp = client.get(f"/api/notes/{note_id}")
    assert get_resp.status_code == 404


def test_filter_by_tag():
    """Test filtering notes by tag."""
    client.post("/api/notes", json={"title": "Python Note", "body": "Python content", "tags": ["python"]})
    client.post("/api/notes", json={"title": "JS Note", "body": "JS content", "tags": ["javascript"]})
    client.post("/api/notes", json={"title": "Both", "body": "Both languages", "tags": ["python", "javascript"]})

    # Filter by python
    response = client.get("/api/notes?tag=python")
    assert response.status_code == 200
    notes = response.json()
    assert len(notes) == 2
    titles = {note["title"] for note in notes}
    assert titles == {"Python Note", "Both"}

    # Filter by javascript
    response = client.get("/api/notes?tag=javascript")
    notes = response.json()
    assert len(notes) == 2
    titles = {note["title"] for note in notes}
    assert titles == {"JS Note", "Both"}


def test_search_by_title():
    """Test searching notes by title."""
    client.post("/api/notes", json={"title": "Python Tutorial", "body": "Content", "tags": []})
    client.post("/api/notes", json={"title": "Django Guide", "body": "Content", "tags": []})

    response = client.get("/api/notes?search=Python")
    assert response.status_code == 200
    notes = response.json()
    assert len(notes) == 1
    assert notes[0]["title"] == "Python Tutorial"


def test_search_by_body():
    """Test searching notes by body content."""
    client.post("/api/notes", json={"title": "Note 1", "body": "This contains kubernetes info", "tags": []})
    client.post("/api/notes", json={"title": "Note 2", "body": "Docker and containers", "tags": []})

    response = client.get("/api/notes?search=kubernetes")
    assert response.status_code == 200
    notes = response.json()
    assert len(notes) == 1
    assert notes[0]["title"] == "Note 1"


def test_search_by_tag():
    """Test searching notes by tag."""
    client.post("/api/notes", json={"title": "Note 1", "body": "Content", "tags": ["devops"]})
    client.post("/api/notes", json={"title": "Note 2", "body": "Content", "tags": ["frontend"]})

    response = client.get("/api/notes?search=devops")
    assert response.status_code == 200
    notes = response.json()
    assert len(notes) == 1
    assert notes[0]["title"] == "Note 1"


def test_search_case_insensitive():
    """Test that search is case-insensitive."""
    client.post("/api/notes", json={"title": "UPPERCASE Title", "body": "Content", "tags": []})

    response = client.get("/api/notes?search=uppercase")
    assert response.status_code == 200
    notes = response.json()
    assert len(notes) == 1
    assert notes[0]["title"] == "UPPERCASE Title"


def test_list_tags():
    """Test listing all tags."""
    client.post("/api/notes", json={"title": "Note 1", "body": "Content", "tags": ["python", "tutorial"]})
    client.post("/api/notes", json={"title": "Note 2", "body": "Content", "tags": ["python", "advanced"]})

    response = client.get("/api/tags")
    assert response.status_code == 200
    tags = response.json()
    assert len(tags) == 3
    tag_names = {tag["name"] for tag in tags}
    assert tag_names == {"python", "tutorial", "advanced"}


def test_tag_reuse():
    """Test that tags are reused across notes."""
    resp1 = client.post("/api/notes", json={"title": "Note 1", "body": "Content", "tags": ["shared"]})
    resp2 = client.post("/api/notes", json={"title": "Note 2", "body": "Content", "tags": ["shared"]})

    # Both notes should reference the same tag
    note1_tag_id = resp1.json()["tags"][0]["id"]
    note2_tag_id = resp2.json()["tags"][0]["id"]
    assert note1_tag_id == note2_tag_id


def test_combined_filter_and_search():
    """Test combining tag filter with search."""
    client.post("/api/notes", json={"title": "Python Guide", "body": "Content", "tags": ["python"]})
    client.post("/api/notes", json={"title": "JS Guide", "body": "Content", "tags": ["javascript"]})
    client.post("/api/notes", json={"title": "Python Tutorial", "body": "Content", "tags": ["javascript"]})

    # Filter by python tag AND search for Guide
    response = client.get("/api/notes?tag=python&search=Guide")
    assert response.status_code == 200
    notes = response.json()
    assert len(notes) == 1
    assert notes[0]["title"] == "Python Guide"
