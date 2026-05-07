## Scenario: Authentication — token expiry and refresh-token logic

**Severity:** silent-wrongness + degradation

**Setup:**

The contract says: "Token has expiry (duration TBD). On token expiry, POST /refresh (with token) → { token: string } OR 401. Invalid/expired tokens return 401 and frontend clears session."

Priya is editing her homepage. Her session has been open for a while. Her token has expired.

**Trigger:**

1. Priya clicks "Save Homepage".
2. Frontend includes the expired token in the request.
3. Backend checks the token, sees it's expired, returns 401.
4. Frontend should catch 401 and attempt to refresh.
5. Frontend POSTs to /refresh with the expired token.
6. Backend returns a new token.
7. Frontend retries the original request (Save Homepage) with the new token.
8. Save succeeds.

**Expected:**

From Priya's perspective: the save takes slightly longer (due to the refresh round-trip), but succeeds transparently. No error message. No session wipeout. No data loss.

**Concern:**

Token expiry + refresh is notoriously error-prone. Common failure modes:

1. **No token expiry at all** — token lasts forever. This is a security issue (Queen's domain), but also breaks the refresh logic because it's never tested.
2. **Expiry without refresh** — token expires, user gets logged out abruptly. Priya's half-written homepage is lost.
3. **Refresh loop** — frontend retries forever if refresh itself fails. Priya is stuck.
4. **Silent data loss** — request fails due to expired token, frontend doesn't retry, Priya thinks the save succeeded but it didn't.
5. **Token comparison edge cases** — what counts as "expired"? If token expires at timestamp 1000, does a request at 1001 fail? What about concurrent requests (one uses the token just before expiry, one uses it just after)?
6. **Refresh with expired token** — can you refresh an already-expired token, or do you need to refresh before expiry? Contract is ambiguous.

The most dangerous case is #4: Priya's data silently isn't saved because the error was swallowed.

**Property:**

For a user U with token T that will expire at time E:

1. Requests with T before time E succeed.
2. Requests with T at or after time E fail with 401 (expired token).
3. Before time E, U can POST /refresh (with T) to get a new token T2 that will expire at time E + duration.
4. After time E, POST /refresh (with T) returns 401 or 410 (token too old to refresh).
5. Requests are idempotent with respect to token expiry: if a write request fails due to expired token, retrying it with a fresh token should succeed without duplicating the write (or duplicating safely, with deduplication).

**Implies:**

Implies token schema and expiry validation (Tweedledum's domain). Implies frontend retry logic (Tweedledee's domain). Implies that the contract is complete: what's the actual expiry duration? Can you refresh an expired token, or only before it expires? Does the frontend have access to the expiry time (in a JWT claim), or is it opaque? These matter for implementation.

---

## Notes for Test Implementation

The pytest tests will:

1. Create a token with a known (short) expiry time.
2. Attempt a request with the valid token — should succeed.
3. Wait past the expiry time (or manually mark token as expired in the test).
4. Attempt a request with the expired token — should fail with 401.
5. POST to /refresh with the expired token — should return a new token (or 401 if backend doesn't allow refreshing expired tokens).
6. Attempt the original request with the new token — should succeed.
7. Verify that two GET requests before the token expires return consistent data (no race between expiry checks).

This test will FAIL until token expiry and refresh are implemented.
