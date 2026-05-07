# Review: Backend auth and session management

**Verdict:** block
**Reviewer's pace:** thorough

## Findings

### block: Missing validate_email function
**Location:** src/backend/api/auth.py:13, 49
**Quote:**
```python
from src.backend.auth import (
    generate_alternative_usernames,
    generate_token,
    hash_password,
    validate_email,
    verify_password,
)
```
**Read:** auth.py imports validate_email from src.backend.auth and calls it on line 49 to validate registration email, but validate_email is not defined in src/backend/auth.py.

**Concern:** ImportError at runtime when /api/register is called. The test test_signup_email_validation will fail immediately with an import error before any functional test runs.

**Request:** Add validate_email(email: str) -> bool to src/backend/auth.py. Implement it to return False for invalid formats like 'notanemail' (missing @) and empty strings. A simple regex-based implementation: import re; return bool(re.match(r'^[^@]+@[^@]+\.[^@]+$', email)).

---

### block: Function name mismatch: generate_alternative_usernames
**Location:** src/backend/api/auth.py:13, 70
**Quote:**
```python
from src.backend.auth import (
    generate_alternative_usernames,
    ...
)
...
alternatives = generate_alternative_usernames(request.desired_username, taken)
```
**Read:** auth.py imports and calls generate_alternative_usernames(base, taken), but src/backend/auth.py defines generate_username_alternatives(base, taken_usernames, count) — different name and different parameter order.

**Concern:** ImportError at runtime when a duplicate username is detected. Any registration that conflicts with an existing username will crash when trying to generate suggestions.

**Request:** In src/backend/auth.py, rename generate_username_alternatives to generate_alternative_usernames, and rename the parameter taken_usernames to taken to match the call site in auth.py line 70.

---

### block: homepage.py ignores Authorization token and uses db.query(User).first()
**Location:** src/backend/api/homepage.py:48-73
**Quote:**
```python
    # In v1, we don't have a real token system, so we'll use a hack:
    # the token is just a placeholder. For testing, we'll create a test user.
    # HACK: Get the "current" user from a global test fixture.
    # This is only for v1 testing and should be replaced with proper auth.
    # For now, we'll just assume the first user created in tests is "current".
    current_user = db.query(User).first()
```
**Read:** The create_or_update_homepage endpoint validates that an Authorization header is present, extracts and checks the token value, but then completely ignores it and retrieves the first user in the database by creation order.

**Concern:** In multi-user scenarios, the wrong user's homepage gets updated. If users A and B both POST /api/user/me/homepage, both updates go to whoever was created first (say, A). User B's homepage never gets created. test_basic_journey will fail because user 'jordan_music' will log in and try to create their homepage, but if any prior test created a user, that prior user's homepage gets updated instead. The cascade deletion tests in test_account_deletion.py depend on this working correctly and will fail.

**Request:** Import get_user_id_from_token from session.py. Extract the token from the Authorization header (remove 'Bearer '), look it up in the session store, and fetch the correct user: token = authorization[7:]; user_id = get_user_id_from_token(token); if user_id is None: raise HTTPException(401, 'Invalid token'); current_user = db.query(User).filter(User.id == user_id).first(). See users.py:_get_user_from_token() for the correct pattern.

---

### block: homepage.py create_or_update_homepage has incorrect Authorization parameter syntax
**Location:** src/backend/api/homepage.py:44-47
**Quote:**
```python
@router.post("/user/me/homepage")
def create_or_update_homepage(
    payload: HomepageCreateRequest,
    authorization: Optional[str] = None,
```
**Read:** The authorization parameter is declared as a regular function parameter with default None, not as a FastAPI Header() parameter.

**Concern:** FastAPI will not extract the Authorization HTTP header into this parameter. Instead, it will expect it to be passed as a query parameter or JSON field (or remain None). The Authorization header sent by the test client will be ignored, authorization will always be None, the check on line 56 will fail, and POST /api/user/me/homepage will always return 401. Tests cannot create homepages.

**Request:** Change the parameter declaration to: authorization: Optional[str] = Header(None). This tells FastAPI to extract the Authorization header. Update the import: from fastapi import APIRouter, Depends, HTTPException, Header. See users.py:57 for the correct pattern with Header(None).

---

### block: homepage.py delete_account endpoint should be removed (duplicate in users.py)
**Location:** src/backend/api/homepage.py:119-154
**Quote:**
```python
@router.delete("/user/me")
def delete_account(
    payload: dict,
    authorization: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Delete user account (requires password confirmation)."""
    ...
    current_user = db.query(User).first()
```
**Read:** homepage.py defines DELETE /user/me with a payload: dict parameter and db.query(User).first() logic. The users.py module also defines DELETE /user/me (line 68), uses Header() for authorization, and correctly implements token-to-user lookup.

**Concern:** Two endpoints with the same path registered to the same router will conflict. Only one will be served (whichever was registered last). The homepage.py version has both the token-to-user bug (db.query(User).first()) and the password validation bug (checks password != 'password123' instead of verify_password()). The users.py version is correct.

**Request:** Remove the entire delete_account function from homepage.py (lines 119-154). The users.py module already provides the correct DELETE /user/me endpoint with proper session lookup and password verification.

---

### suggestion: homepage.py's delete_account payload parameter is untyped
**Location:** src/backend/api/homepage.py:124
**Quote:**
```python
def delete_account(
    payload: dict,
```
**Read:** The endpoint accepts payload: dict instead of a Pydantic model, losing type hints and automatic validation.

**Concern:** The body on line 140 (password = payload.get('password')) lacks type safety and validation. This is minor compared to the other issues, but it's inconsistent with users.py which uses DeleteAccountRequest.

**Request:** If this endpoint were kept (which it shouldn't be, per the previous finding), it should accept request: DeleteAccountRequest. Since we're deleting this endpoint entirely, no action needed.

---

## Approvals

- **src/backend/session.py** is well-designed: concise and correct in-memory token storage. The three functions (register_token, get_user_id_from_token, invalidate_token) have clear semantics and will support the v1 tests correctly.
- **src/backend/api/users.py** is correctly structured: Header(None) for auth extraction, proper token lookup via get_user_id_from_token, and verify_password() for validation. This is the pattern homepage.py should follow.
- **src/backend/markdown.py** correctly escapes input with html.escape before applying transformations, preventing direct XSS injection. The sanitize_html function removes script tags, event handlers (on*), and javascript: URLs effectively. The regex patterns for Markdown features are reasonable for v1.

## Cross-domain references

- **Hatter:** test_basic_journey.py will fail at the POST /api/user/me/homepage step because of the missing Header() parameter and the db.query(User).first() bug. All tests in test_account_deletion.py, test_auth_token_expiry.py will fail for the same reasons.
