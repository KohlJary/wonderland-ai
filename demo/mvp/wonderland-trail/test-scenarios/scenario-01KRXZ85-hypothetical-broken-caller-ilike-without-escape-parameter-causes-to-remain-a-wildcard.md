## Scenario 235: Hypothetical broken caller: ilike() without escape parameter causes _ to remain a wildcard

**GUID:** 01KRXZ858SK3B6BPMHNS918V56
**Severity:** silent-wrongness

**Setup:**

Same scenario: future developer forgets escape="\\" parameter. Notes: 'model_v2', 'model_v3', 'model-v2'.

**Trigger:**

Broken caller searches for 'model_v2' using escaped pattern 'model\\_v2' WITHOUT escape parameter.

**Expected:**

Only 'model_v2' should match (literal underscore).

**Concern:**

Without escape='\\', \_ becomes backslash-followed-by-wildcard. The wildcard matches any single character. Result: 'model_v2' AND 'model_v3' both match (v2 and v3 both have one character). User expects only v2.

**Property:**

Equivalent to percent-sign case: escape parameter in ilike() is mandatory for _escape_like_pattern() output to work correctly.
