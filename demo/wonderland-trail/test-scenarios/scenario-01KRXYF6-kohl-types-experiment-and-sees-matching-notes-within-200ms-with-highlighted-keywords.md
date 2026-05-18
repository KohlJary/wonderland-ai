## Scenario 218: Kohl types 'experiment' and sees matching notes within 200ms with highlighted keywords

**GUID:** 01KRXYF6YT5H0S2TNKA6KX1HX7
**Severity:** silent-wrongness

**Setup:**

Kohl has 12 saved notes; 3 contain the word 'experiment' (one in title, two in body). She's on the Search view with an empty input field.

**Trigger:**

Kohl types 'experiment' into the search input and waits for results.

**Expected:**

Within 200ms of the keystroke, the search results pane displays the 3 matching notes. Each result shows the note title and a 150-character excerpt of the body. The word 'experiment' is visibly highlighted (bold, different color, or underline) in both title and excerpt wherever it appears. The result count shows '3 results'.

**Concern:**

If search results don't appear within 200ms, Kohl perceives the feature as broken or unresponsive. If highlights are missing, she can't quickly scan to understand why a note matched. If the word count is wrong, she loses trust in search accuracy.

**Property:**

Search responsiveness and result clarity directly affect Kohl's confidence in using search to rediscover her notes.

**Implies:**
- debounce-fires-query-within-timing-budget
- api-response-under-200ms
- highlight-rendering-is-performant
- result-count-matches-actual-matches
