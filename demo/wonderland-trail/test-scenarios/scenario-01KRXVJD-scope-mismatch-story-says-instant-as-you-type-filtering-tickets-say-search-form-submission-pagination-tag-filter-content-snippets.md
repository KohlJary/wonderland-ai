## Scenario 099: Scope mismatch: Story says 'instant as-you-type filtering'; tickets say 'search form submission + pagination + tag filter + content snippets'

**GUID:** 01KRXVJD1AD0E3PGKD4RWZHY45
**Severity:** silent-wrongness

**Setup:**

Story describes Kohl typing a search term and the list filtering live. Tickets describe a search form with submission, pagination, and tag multiselect.

**Trigger:**

Implementer reads both story and tickets and has to reconcile them.

**Expected:**

The story and tickets describe the same feature in compatible scope.

**Concern:**

The story is the user need; the tickets are the decomposition. When they diverge, the team ships the tickets and the story goes unfulfilled. Kohl gets a search form with a button to submit instead of instant filtering. Or Kohl gets instant filtering but no pagination (which breaks on large result sets). Or Kohl gets a tag filter he didn't ask for, adding complexity. The story doesn't mention tags, pagination, or submission buttons.

**Property:**

Story and tickets describe compatible scopes. Tickets may add details or structure, but must satisfy the story's core user need.

**Implies:**
- Implies scope reconciliation between story and tickets — flag for Alice and the Rabbit. The story is the source of truth; tickets should be decompositions of the story, not reimaginations.
