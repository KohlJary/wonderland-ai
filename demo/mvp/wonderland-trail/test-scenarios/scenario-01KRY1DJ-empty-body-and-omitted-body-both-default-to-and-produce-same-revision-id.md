## Scenario 339: empty body ('') and omitted body both default to '' and produce same revision_id

**GUID:** 01KRY1DJHRX8TH9EM6XEXWJ9BG
**Severity:** silent-wrongness

**Setup:**

Contract specifies body is always string, never null. Two ways to create empty body: (1) POST with body='' (explicit), (2) POST with body omitted (should default to '').

**Trigger:**

(1) Fetch note 1, compute revision_id='hash_A'. (2) Fetch note 2, compute revision_id='hash_B'.

**Expected:**

hash_A == hash_B. Both have body='', so identical state, identical revision_id.

**Concern:**

If hash treats '' and null differently, or one path preserves '' and another converts to null, two notes with identical content have different revision_ids. User clears body and tries to save: system reports false collision. If null slips into DB (violating NOT NULL), note becomes corrupted.

**Property:**

For all notes, body is always string (never null). Two notes with identical title, tag_ids, updated_at, and body='' have identical revision_id regardless of how body='' was set.

**Implies:**
- Implies test: create two notes (one with body='', one omitted) and verify identical revision_id.
- Implies test: attempt to insert note with body=null (should fail at constraint), verify API gracefully rejects or raises error (not silent corruption).
