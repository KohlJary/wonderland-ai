## Scenario 264: Kohl saves a note, the server returns 200 but the body payload is truncated (Connection reset after headers but before body completes)—the frontend parses whatever arrived and updates state with incomplete data

**GUID:** 01KRY19NJ0GS53FVHNDWBCBT8F
**Severity:** silent-wrongness

**Setup:**

Kohl has edited a note. The PUT request is sent. The server processes it, begins sending the response, but the connection is interrupted mid-response.

**Trigger:**

The fetch() call receives HTTP 200 headers successfully. However, the response body is cut short—only the first half of the JSON is received (e.g., {"id": 123, "title": "Exper -- connection reset).

**Expected:**

The fetch API should detect the incomplete response and reject with a JSON parsing error or network error. The frontend should treat this as a save failure, show an error message, and keep the Save button enabled for retry.

**Concern:**

If the fetch error handling is not robust, it might throw an unhandled exception. If the frontend tries to parse incomplete JSON, it will fail, but if it then silently continues (swallowing the error), the user might think the save succeeded when it didn't.

**Property:**

For all fetch operations, the frontend must handle partial/truncated responses as errors, not successes.

**Implies:**
- Implies error handling in the JSON parsing step of the save handler.
