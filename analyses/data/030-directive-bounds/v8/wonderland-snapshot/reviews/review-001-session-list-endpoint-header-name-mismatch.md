## Review 001: Session list endpoint: header name mismatch

**Files reviewed:** src/backend/api/sessions.py
**Verdict:** request-changes

### Findings

#### block: Header alias 'X-Session-Id' doesn't match frontend's 'X-Session-ID'
**Location:** src/backend/api/sessions.py:245
**Quote:**

```
def list_sessions(
    x_session_id: str | None = Header(None, alias="X-Session-Id"),
```

**Read:** The list_sessions endpoint looks for 'X-Session-Id' (lowercase 'd'), but the frontend and all other endpoints use 'X-Session-ID' (uppercase 'D'). Starlette header matching is case-sensitive when using aliases.
**Concern:** Feature 003 (session history) and Feature 004 (data persistence) depend on this endpoint. The frontend's listSessions() function sends X-Session-ID, but the backend rejects it as missing. Users see empty history, and session isolation breaks.
**Request:** Changed alias to 'X-Session-ID' to match everywhere else.
