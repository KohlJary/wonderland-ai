## Scenario 241: Code audit confirms all current call sites of _escape_like_pattern() include escape parameter

**GUID:** 01KRXZ8M0J7CVP08DRGHREWYNX
**Severity:** breakage

**Setup:**

The codebase currently uses _escape_like_pattern() in the search endpoint. A code reviewer audits all call sites to verify they follow the contract.

**Trigger:**

Reviewer searches for all calls to _escape_like_pattern() and all calls to ilike() that use the escaped pattern.

**Expected:**

Every call to ilike(escaped_pattern, ...) includes the escape='\\' parameter. No call sites pass the escaped pattern to ilike() without the escape parameter. The contract is honored in 100% of cases.

**Concern:**

If even one call site forgets the escape parameter, the escaping is silent-wrongness-broken. The function works, the call succeeds, but user input with % or _ is not correctly escaped. A human code review is the only way to catch this before runtime.

**Property:**

Implicit contracts between functions require human code review to verify all call sites honor the contract.

**Implies:**
- code_audit_all_ilike_call_sites_include_escape_parameter
