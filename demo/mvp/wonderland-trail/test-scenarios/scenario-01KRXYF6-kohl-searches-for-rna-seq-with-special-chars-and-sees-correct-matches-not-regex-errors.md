## Scenario 219: Kohl searches for 'RNA*seq' (with special chars) and sees correct matches, not regex errors

**GUID:** 01KRXYF6YT5H0S2TNKA6KX1HX8
**Severity:** breakage

**Setup:**

Kohl has notes containing 'RNA*seq', 'RNA seq', and 'RNAseq' (different punctuation variants). She opens Search.

**Trigger:**

Kohl types 'RNA*seq' (with the asterisk) into the search input.

**Expected:**

The search returns only the note(s) containing exactly 'RNA*seq' (or substring match without interpreting * as a regex wildcard). Results display without error. If the backend uses regex for highlighting, the * is escaped so it matches literally.

**Concern:**

If the search or highlighting engine interprets * as a regex operator, it could return wrong results (matching 'RNAseq' when Kohl wanted 'RNA*seq') or crash silently. Kohl sees confusing results or no results when notes do exist.

**Property:**

Query strings with special characters must be treated as literals, not regex syntax.

**Implies:**
- query-escaping-before-regex
- special-char-literal-matching
