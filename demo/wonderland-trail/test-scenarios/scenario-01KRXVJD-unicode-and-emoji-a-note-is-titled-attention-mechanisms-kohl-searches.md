## Scenario 101: Unicode and emoji: A note is titled '🧠 Attention Mechanisms'; Kohl searches '🧠'

**GUID:** 01KRXVJD1AD0E3PGKD4RWZHY47
**Severity:** degradation

**Setup:**

App has a note titled '🧠 Attention Mechanisms'.

**Trigger:**

Kohl types '🧠' (emoji) into search.

**Expected:**

The note appears in results.

**Concern:**

Emoji are multi-byte UTF-8. Naive substring matching might split them. If the search is done server-side (per tickets), the backend has to handle emoji correctly.

**Property:**

Search works correctly for emoji and non-ASCII characters.
