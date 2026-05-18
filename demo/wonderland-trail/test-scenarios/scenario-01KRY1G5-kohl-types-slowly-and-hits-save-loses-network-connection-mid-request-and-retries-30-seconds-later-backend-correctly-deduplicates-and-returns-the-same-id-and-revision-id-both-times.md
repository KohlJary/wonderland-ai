## Scenario 368: Kohl types slowly and hits Save, loses network connection mid-request, and retries 30 seconds later. Backend correctly deduplicates and returns the same id and revision_id both times.

**GUID:** 01KRY1G5562S7JSHVEXACBHXDY
**Severity:** degradation

**Setup:**

Kohl has note #42 open. She types a few words and clicks Save. The request is in-flight (XMLHttpRequest pending) when her WiFi cuts out. The frontend never receives a 200 or error response — the request times out or hangs. localStorage still contains her keystroke buffer with the unsaved text (title: 'Research Log', body: '# Day 1

Started.', tags: ['research']).

**Trigger:**

After 10 seconds of no response, Kohl's network reconnects. The frontend times out the pending PUT request and shows an error: 'Save failed. Click to retry.' Kohl clicks Retry. A new PUT request is sent with the same payload (title, body, tags, revision_id). This time it completes and returns 200 with id: 42.

**Expected:**

The first (timed-out) PUT may or may not have reached the backend. If it did and was partially written (network dropped before the database write committed), the transaction rolled back and nothing was persisted. If it didn't reach the backend at all, nothing happened. Either way, the backend is clean. When the second PUT arrives (with the same payload), the backend treats it as a fresh update: compares the revision_id, writes the note, computes the new revision_id, returns 200 with id: 42 and a new revision_id (e.g., 'b5e7q2...'). Kohl sees 'Saved' and the keystroke buffer is cleared. Both responses (the first, if it was received, and the second) have the same id and the same or compatible revision semantics (no 409 error on the retry).

**Concern:**

If the backend received the first PUT and wrote it, then the second PUT arrives as a duplicate, it should not double-write or return 409 (which would confuse Kohl — she didn't edit in between, so why is there a conflict?). The backend must be idempotent or have a way to recognize that the retry is the same logical request as the first attempt. Currently, the backend treats every PUT as a fresh attempt. If Kohl's network is unstable and she clicks Retry multiple times, she might trigger multiple writes with slightly different revisions, causing confusion.

**Property:**

Save operation is resilient to transient network failures; retrying produces safe, non-duplicative results.

**Implies:**
- PUT request should ideally include an idempotency key (not yet in contract, deferred to v1.5) so retries are recognized as the same logical request
- For v1, accept that retries may create multiple revisions, but document the assumption (single-user single-device, no multi-device sync in v1, so repeated retries are rare)
- Error message must be clear: 'Save failed — click Retry to try again' (not 'Conflict detected')
