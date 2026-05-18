#!/usr/bin/env python3
"""
Integration test that simulates a realistic user workflow
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src", "backend"))

from main import app
from fastapi.testclient import TestClient

def test_user_workflow():
    """Simulate a user's typical workflow"""
    client = TestClient(app)
    
    print("\n🎯 Simulating User Workflow\n")
    print("=" * 50)
    
    # 1. User creates first note about Python
    print("\n1️⃣  Creating first note about Python...")
    resp = client.post("/api/notes", json={
        "title": "Python Best Practices",
        "body": "# Python Best Practices\n\n## Type Hints\nAlways use type hints for clarity.\n\n## Testing\nWrite tests for your code.",
        "tags": ["python", "best-practices"]
    })
    assert resp.status_code == 200
    note1 = resp.json()
    note1_id = note1["id"]
    print(f"   ✓ Created note ID {note1_id}: '{note1['title']}'")
    print(f"   Tags: {', '.join(note1['tags'])}")
    
    # 2. User creates second note about JavaScript
    print("\n2️⃣  Creating second note about JavaScript...")
    resp = client.post("/api/notes", json={
        "title": "JavaScript Async Patterns",
        "body": "# Async Programming\n\n- Promises\n- Async/await\n- Callbacks (avoid!)",
        "tags": ["javascript", "async"]
    })
    assert resp.status_code == 200
    note2 = resp.json()
    note2_id = note2["id"]
    print(f"   ✓ Created note ID {note2_id}: '{note2['title']}'")
    
    # 3. User searches for notes about Python
    print("\n3️⃣  Searching for notes about 'Python'...")
    resp = client.get("/api/notes?search=Python")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    print(f"   ✓ Found {len(results)} note(s)")
    print(f"   Title: {results[0]['title']}")
    
    # 4. User views all tags
    print("\n4️⃣  Viewing all available tags...")
    resp = client.get("/api/tags")
    assert resp.status_code == 200
    tags = resp.json()["tags"]
    print(f"   ✓ Tags: {', '.join(tags)}")
    
    # 5. User filters notes by 'javascript' tag
    print("\n5️⃣  Filtering notes by 'javascript' tag...")
    resp = client.get("/api/notes?tag=javascript")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["id"] == note2_id
    print(f"   ✓ Found {len(results)} note(s) with 'javascript' tag")
    
    # 6. User lists all notes
    print("\n6️⃣  Listing all notes (most recent first)...")
    resp = client.get("/api/notes")
    assert resp.status_code == 200
    notes = resp.json()
    assert len(notes) == 2
    # Most recent first (note2 was created after note1)
    assert notes[0]["id"] == note2_id
    assert notes[1]["id"] == note1_id
    print(f"   ✓ Found {len(notes)} notes, most recent first")
    for i, note in enumerate(notes, 1):
        print(f"     {i}. {note['title']}")
    
    # 7. User edits the first note
    print("\n7️⃣  Editing first note...")
    resp = client.put(f"/api/notes/{note1_id}", json={
        "body": "# Python Best Practices\n\n## Type Hints\nAlways use type hints for clarity.\n\n## Testing\nWrite comprehensive tests for your code.\n\n## Documentation\nDocument your functions and modules."
    })
    assert resp.status_code == 200
    updated = resp.json()
    print(f"   ✓ Updated note ID {note1_id}")
    print(f"   Updated at: {updated['updated_at']}")
    
    # 8. User searches for content across multiple notes
    print("\n8️⃣  Searching for 'best'...")
    resp = client.get("/api/notes?search=best")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1  # Only matches the first note
    print(f"   ✓ Found {len(results)} note(s) containing 'best'")
    
    # 9. User gets full details of a specific note
    print("\n9️⃣  Getting full details of a note...")
    resp = client.get(f"/api/notes/{note1_id}")
    assert resp.status_code == 200
    note = resp.json()
    print(f"   ✓ Title: {note['title']}")
    print(f"   ✓ Tags: {', '.join(note['tags'])}")
    print(f"   ✓ Body length: {len(note['body'])} characters")
    
    # 10. User adds tags to the second note
    print("\n🔟 Adding a 'web' tag to second note...")
    resp = client.put(f"/api/notes/{note2_id}", json={
        "tags": ["javascript", "async", "web"]
    })
    assert resp.status_code == 200
    updated = resp.json()
    print(f"   ✓ Updated tags: {', '.join(updated['tags'])}")
    
    # 11. Verify notes still sorted correctly
    print("\n1️⃣1️⃣  Verifying note order after edits...")
    resp = client.get("/api/notes")
    notes = resp.json()
    # Most recent edit wins - note2 was last updated
    assert notes[0]["id"] == note2_id
    print(f"   ✓ Most recent note is still first")
    
    # 12. User deletes a note
    print("\n1️⃣2️⃣  Deleting a note...")
    resp = client.delete(f"/api/notes/{note1_id}")
    assert resp.status_code == 200
    print(f"   ✓ Deleted note ID {note1_id}")
    
    # 13. Verify note is deleted
    print("\n1️⃣3️⃣  Verifying deletion...")
    resp = client.get(f"/api/notes/{note1_id}")
    assert resp.status_code == 404
    print(f"   ✓ Note no longer exists (404)")
    
    # 14. Final count
    print("\n1️⃣4️⃣  Final note count...")
    resp = client.get("/api/notes")
    notes = resp.json()
    assert len(notes) == 1
    print(f"   ✓ {len(notes)} note remaining")
    
    print("\n" + "=" * 50)
    print("\n✅ User workflow test PASSED!\n")
    print("Summary:")
    print("  ✓ Created notes with markdown and tags")
    print("  ✓ Searched across titles and content")
    print("  ✓ Filtered by tags")
    print("  ✓ Listed notes (sorted by most recent)")
    print("  ✓ Updated notes")
    print("  ✓ Deleted notes")
    print("  ✓ Persistence across operations")
    print()

if __name__ == "__main__":
    test_user_workflow()
