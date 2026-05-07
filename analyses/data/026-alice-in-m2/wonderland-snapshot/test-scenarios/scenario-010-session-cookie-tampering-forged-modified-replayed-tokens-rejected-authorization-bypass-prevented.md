## Scenario 010: Session cookie tampering: forged/modified/replayed tokens rejected, authorization bypass prevented

**Severity:** breakage

**Setup:**

Session token issued to User A. User B captures token (MITM, XSS, packet sniff) and attempts reuse, forgery, or modification.

**Trigger:**

User B sends request with captured/modified/forged session token.

**Expected:**

Validation fails (401). User B cannot access User A's account. No authorization bypass.

**Concern:**

If tokens lack cryptographic signing or server-side validation, User B can forge tokens (guess user_id), reuse revoked tokens (from logout), or tamper with token contents.

**Property:**

For all tokens T and users U: (1) only U can use T, (2) only server can validate T (clients cannot forge), (3) revoked T returns 401, (4) tampered T returns 401.
