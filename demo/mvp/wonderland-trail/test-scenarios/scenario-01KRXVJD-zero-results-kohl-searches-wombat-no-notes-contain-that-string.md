## Scenario 098: Zero results: Kohl searches 'wombat', no notes contain that string

**GUID:** 01KRXVJD1AD0E3PGKD4RWZHY44
**Severity:** degradation

**Setup:**

App has 5 notes with various titles and bodies. None contain 'wombat'.

**Trigger:**

Kohl types 'wombat'.

**Expected:**

The results list shows a 'no results found' message or an empty state. The search box remains active. Kohl can refine his search.

**Concern:**

A blank results list (no message) is ambiguous: did the search fail? Does the app have no notes? Is the search still loading? Clear messaging is critical.

**Property:**

When search returns zero results, the UI explicitly communicates this to the user.
