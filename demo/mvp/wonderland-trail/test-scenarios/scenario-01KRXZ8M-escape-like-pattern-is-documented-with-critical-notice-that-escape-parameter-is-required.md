## Scenario 240: _escape_like_pattern() is documented with CRITICAL notice that escape parameter is required

**GUID:** 01KRXZ8M0J7CVP08DRGHREWYNW
**Severity:** degradation

**Setup:**

The _escape_like_pattern() function is defined in src/backend/api/notes.py. A future developer reads the function signature and docstring.

**Trigger:**

Future developer calls _escape_like_pattern(user_input) and receives an escaped pattern. They then use the pattern in a new ilike() call elsewhere in the codebase, forgetting to include escape='\'.

**Expected:**

The docstring contains a CRITICAL notice stating: 'Pattern returned from this function MUST be used with ilike(..., escape="\\") or escaping will be ineffective. Failure to include the escape parameter causes wildcard metacharacters in user input to remain unescaped and match incorrectly.' A developer reading this notice before using the function will not make the mistake.

**Concern:**

Without explicit documentation of the escape-parameter requirement, a future developer may use the function incorrectly and introduce a silent correctness bug. The bug would only be caught by tests — if tests are insufficient or the scenario isn't covered, the bug ships to production.

**Property:**

Critical contracts between functions must be documented in docstrings, not just in comments or assumed to be 'obvious'.

**Implies:**
- docstring_includes_critical_notice_about_escape_parameter
