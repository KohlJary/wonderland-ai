"""Baseline test — POST /api/messages echoes a message into the DB,
GET /api/messages lists what's been posted.

============================================================================
SKELETON TEMPLATE — DELETE THIS FILE when shipping real features.

These tests pin the placeholder /api/messages endpoint that ships
with the seed. They exist so the human verifying the skeleton can
run pytest end-to-end before any real work happens.

When you replace messages.py with real endpoints, also delete this
file and replace it with feature-specific tests. Leaving this file
when messages.py is gone causes a collection failure that hides
all your real test signal.
============================================================================
"""


def test_post_and_list_messages(client):
    res = client.post("/api/messages", json={"text": "hello"})
    assert res.status_code == 200
    msg = res.json()
    assert msg["text"] == "hello"
    assert msg["id"] >= 1

    res = client.get("/api/messages")
    assert res.status_code == 200
    rows = res.json()
    assert any(r["text"] == "hello" for r in rows)


def test_post_message_rejects_empty_text(client):
    res = client.post("/api/messages", json={"text": ""})
    assert res.status_code == 422  # pydantic validation


def test_post_message_rejects_text_over_280_chars(client):
    res = client.post("/api/messages", json={"text": "x" * 281})
    assert res.status_code == 422
