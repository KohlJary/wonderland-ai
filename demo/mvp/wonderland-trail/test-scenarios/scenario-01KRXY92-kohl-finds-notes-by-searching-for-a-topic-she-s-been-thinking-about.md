## Scenario 176: Kohl finds notes by searching for a topic she's been thinking about

**GUID:** 01KRXY92H4EWNSQ2AXJ0WRT1FF
**Severity:** silent-wrongness

**Setup:**

Kohl has 47 notes accumulated over three months. She's been researching 'fermentation' across several notes — some titled 'Kimchi experiments', others with 'fermentation' buried in the body. She opens the search interface.

**Trigger:**

Kohl types 'fermentation' into the search box and hits enter.

**Expected:**

Within 1 second, she sees a list of all notes containing 'fermentation' — both the ones that have it in the title and the ones that have it only in the body. The results show her enough context (title + a line or two from where 'fermentation' appears) that she can remember which note is which without opening each one.

**Concern:**

If the search returns results slowly or misses notes where 'fermentation' appears only in the body, Kohl will think she's lost notes — or worse, will stop trusting search and go back to scrolling. Silent wrongness: the endpoint returns *some* results but not all, and Kohl never knows the gap exists.

**Property:**

Search completeness and responsiveness are invisible to the user until they fail.
