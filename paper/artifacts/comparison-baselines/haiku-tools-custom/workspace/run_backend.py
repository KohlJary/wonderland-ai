#!/usr/bin/env python
"""Quick test script to verify the backend runs"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src", "backend"))

from main import app
from fastapi.testclient import TestClient

if __name__ == "__main__":
    client = TestClient(app)
    
    print("Testing backend...")
    
    # Health check
    resp = client.get("/api/health")
    assert resp.status_code == 200
    print("✓ Health check")
    
    # Create a note
    resp = client.post("/api/notes", json={
        "title": "Test Note",
        "body": "# Markdown Test\n\nThis is a test",
        "tags": ["test", "example"]
    })
    assert resp.status_code == 200
    note_id = resp.json()["id"]
    print(f"✓ Created note (ID: {note_id})")
    
    # List notes
    resp = client.get("/api/notes")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    print(f"✓ Listed {len(resp.json())} note(s)")
    
    # Get tags
    resp = client.get("/api/tags")
    assert resp.status_code == 200
    assert "test" in resp.json()["tags"]
    print(f"✓ Got tags: {resp.json()['tags']}")
    
    # Search
    resp = client.get("/api/notes?search=Markdown")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    print("✓ Search works")
    
    # Filter by tag
    resp = client.get("/api/notes?tag=test")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    print("✓ Tag filter works")
    
    # Update note
    resp = client.put(f"/api/notes/{note_id}", json={
        "title": "Updated Note",
        "body": "Updated content"
    })
    assert resp.status_code == 200
    print("✓ Updated note")
    
    # Delete note
    resp = client.delete(f"/api/notes/{note_id}")
    assert resp.status_code == 200
    print("✓ Deleted note")
    
    # Verify deletion
    resp = client.get("/api/notes")
    assert len(resp.json()) == 0
    print("✓ Verified deletion")
    
    print("\n✅ All backend tests passed!")
