## Scenario 231: Kohl searches with space-separated words and expects all to match

**GUID:** 01KRXYFQH721FMRYBB1WJJ1A0H
**Severity:** silent-wrongness

**Setup:**

Kohl has notes with body 'Experiment on RNA samples' and 'RNA analysis experiments'. She opens search.

**Trigger:**

Kohl types 'RNA experiment' (two words with space).

**Expected:**

Search finds notes where the query string 'RNA experiment' appears as a substring (first note has 'RNA' and 'Experiment' but not 'RNA experiment' as a contiguous phrase; second note has 'RNA' and 'experiments'—both match if searching either word independently, but this scenario tests whether the query is treated as a single substring or split into words).

**Concern:**

Ambiguity: the contract (contract-note-008) specifies 'substring search' but doesn't clarify if 'RNA experiment' (two words) is searched as a single substring or if each word is searched independently. If the implementation treats it as a single substring, 'RNA experiment' won't match 'Experiment on RNA samples' (because 'RNA experiment' doesn't appear contiguously). If it searches each word independently, both notes match. Kohl's expectation is unclear here—she might expect 'either RNA or experiment' (OR) or 'both RNA and experiment' (AND) or 'the phrase RNA experiment together' (phrase search).

**Property:**

Multi-word substring queries are treated as a single contiguous substring match, not split into separate word matches.

**Implies:**
- contract-ambiguity-multi-word-search
