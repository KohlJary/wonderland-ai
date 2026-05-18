import pytest
import json
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "backend"))

from main import app, Base, NoteModel, get_db

# Test database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_db():
    """Clear database before each test"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_create_note():
    response = client.post(
        "/api/notes",
        json={
            "title": "Test Note",
            "body": "# Heading\n\nSome content",
            "tags": ["python", "notes"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Note"
    assert data["body"] == "# Heading\n\nSome content"
    assert data["tags"] == ["python", "notes"]
    assert data["id"] == 1

def test_create_note_no_tags():
    response = client.post(
        "/api/notes",
        json={
            "title": "Simple Note",
            "body": "Just text"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["tags"] == []

def test_list_notes_empty():
    response = client.get("/api/notes")
    assert response.status_code == 200
    assert response.json() == []

def test_list_notes():
    # Create multiple notes
    client.post(
        "/api/notes",
        json={"title": "First", "body": "Content 1", "tags": ["a"]}
    )
    client.post(
        "/api/notes",
        json={"title": "Second", "body": "Content 2", "tags": ["b"]}
    )
    
    response = client.get("/api/notes")
    assert response.status_code == 200
    notes = response.json()
    assert len(notes) == 2
    # Most recently edited first
    assert notes[0]["title"] == "Second"
    assert notes[1]["title"] == "First"

def test_get_note():
    create_resp = client.post(
        "/api/notes",
        json={"title": "Test", "body": "Body", "tags": ["tag1"]}
    )
    note_id = create_resp.json()["id"]
    
    response = client.get(f"/api/notes/{note_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test"
    assert data["body"] == "Body"
    assert data["tags"] == ["tag1"]

def test_get_note_not_found():
    response = client.get("/api/notes/999")
    assert response.status_code == 404

def test_update_note():
    create_resp = client.post(
        "/api/notes",
        json={"title": "Original", "body": "Original body", "tags": ["old"]}
    )
    note_id = create_resp.json()["id"]
    
    response = client.put(
        f"/api/notes/{note_id}",
        json={"title": "Updated", "tags": ["new", "tag"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated"
    assert data["body"] == "Original body"  # Not updated
    assert data["tags"] == ["new", "tag"]

def test_delete_note():
    create_resp = client.post(
        "/api/notes",
        json={"title": "Delete Me", "body": "Body"}
    )
    note_id = create_resp.json()["id"]
    
    response = client.delete(f"/api/notes/{note_id}")
    assert response.status_code == 200
    
    # Verify it's deleted
    response = client.get(f"/api/notes/{note_id}")
    assert response.status_code == 404

def test_search_notes():
    client.post(
        "/api/notes",
        json={"title": "Python Guide", "body": "Learn Python basics", "tags": ["python"]}
    )
    client.post(
        "/api/notes",
        json={"title": "JavaScript Tips", "body": "JS async patterns", "tags": ["js"]}
    )
    client.post(
        "/api/notes",
        json={"title": "General Notes", "body": "Python and JS", "tags": ["multi"]}
    )
    
    # Search by title
    response = client.get("/api/notes?search=Python")
    notes = response.json()
    assert len(notes) == 2
    titles = [n["title"] for n in notes]
    assert "Python Guide" in titles
    assert "General Notes" in titles
    
    # Search by body
    response = client.get("/api/notes?search=async")
    notes = response.json()
    assert len(notes) == 1
    assert notes[0]["title"] == "JavaScript Tips"
    
    # Search by tag
    response = client.get("/api/notes?search=js")
    notes = response.json()
    assert len(notes) == 2

def test_filter_by_tag():
    client.post(
        "/api/notes",
        json={"title": "Note 1", "body": "Body 1", "tags": ["python", "tutorial"]}
    )
    client.post(
        "/api/notes",
        json={"title": "Note 2", "body": "Body 2", "tags": ["javascript"]}
    )
    client.post(
        "/api/notes",
        json={"title": "Note 3", "body": "Body 3", "tags": ["python", "api"]}
    )
    
    # Filter by python tag
    response = client.get("/api/notes?tag=python")
    notes = response.json()
    assert len(notes) == 2
    assert all("python" in n["tags"] for n in notes)
    
    # Filter by javascript tag
    response = client.get("/api/notes?tag=javascript")
    notes = response.json()
    assert len(notes) == 1
    assert notes[0]["title"] == "Note 2"

def test_get_all_tags():
    client.post(
        "/api/notes",
        json={"title": "Note 1", "body": "Body", "tags": ["python", "tutorial"]}
    )
    client.post(
        "/api/notes",
        json={"title": "Note 2", "body": "Body", "tags": ["javascript", "tutorial"]}
    )
    
    response = client.get("/api/tags")
    assert response.status_code == 200
    data = response.json()
    assert set(data["tags"]) == {"python", "tutorial", "javascript"}

def test_case_insensitive_search():
    client.post(
        "/api/notes",
        json={"title": "Python Notes", "body": "Learning Python"}
    )
    
    response = client.get("/api/notes?search=python")
    notes = response.json()
    assert len(notes) == 1
    
    response = client.get("/api/notes?search=PYTHON")
    notes = response.json()
    assert len(notes) == 1

def test_timestamps():
    response = client.post(
        "/api/notes",
        json={"title": "Test", "body": "Body"}
    )
    data = response.json()
    assert "created_at" in data
    assert "updated_at" in data
    # Verify they're valid ISO strings
    datetime.fromisoformat(data["created_at"])
    datetime.fromisoformat(data["updated_at"])
