## Scenario 236: Documentation of contract prevents accidental misuse

**GUID:** 01KRXZ858SK3B6BPMHNS918V57
**Severity:** degradation

**Setup:**

After the ticket fix is applied, the _escape_like_pattern() docstring includes a CRITICAL note: 'Pattern returned from this function MUST be used with ilike(..., escape="\\\\")'.

**Trigger:**

A developer reads the docstring before calling the function.

**Expected:**

The developer remembers the requirement and uses escape="\\" correctly. Escaping works. Results are correct.

**Concern:**

Docstring helps but is not foolproof — a developer in a hurry might miss it. A runtime assertion or wrapper function would be stronger. But for v1, docstring is the agreed approach.

**Property:**

Explicit documentation of implicit contracts reduces the likelihood of silent misuse, even if it doesn't eliminate it entirely.

**Implies:**
- Docstring is sufficient for v1 per Rabbit's acceptance criteria.
- Future improvement: wrap ilike() in a helper function (ilike_literal_search) to enforce escape parameter at call site.
