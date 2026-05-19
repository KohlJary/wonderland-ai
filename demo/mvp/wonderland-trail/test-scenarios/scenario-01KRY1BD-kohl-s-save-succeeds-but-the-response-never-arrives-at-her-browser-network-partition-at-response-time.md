## Scenario 307: Kohl's save succeeds, but the response never arrives at her browser (network partition at response time)

**GUID:** 01KRY1BD9QYCM0QJV0RZ20601F
**Severity:** degradation

**Setup:**

Kohl clicks Save. The PUT /api/notes/{id} request reaches the server. Server processes it atomically: writes to database, logs audit trail, computes revision_id='v3', prepares 200 response. But the network drops and the response is lost to Kohl's browser (connection timeout).

**Trigger:**

Editor's fetch() timeout fires (~10s default). Frontend receives no response body.

**Expected:**

Frontend displays 'Save request timed out. Retry?' and keeps the Save button enabled. localStorage buffer is preserved (not cleared). Kohl can retry once network is back. On retry, if the server already has revision_id='v3', the second request with the same payload but old If-Match (=v2) will return 409 Conflict (safe conflict warning), NOT a duplicate creation.

**Concern:**

If the timeout error is silent, Kohl thinks her save succeeded when it didn't. If localStorage is cleared prematurely, the keystroke buffer is lost. If the server created a duplicate note on the retry (no idempotency), Kohl has two copies of the same note.

**Property:**

Network timeout handling + retry idempotency
