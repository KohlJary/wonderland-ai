## Scenario 094: Empty state: Kohl opens the app, hasn't created any notes

**GUID:** 01KRXVJD193RBKVRZVJXEV7JEZ
**Severity:** degradation

**Setup:**

App has zero notes in the database.

**Trigger:**

Kohl navigates to the app and the search UI loads.

**Expected:**

A friendly empty-state message appears. The search box is visible and ready. Kohl can type, but searching returns no results.

**Concern:**

The story doesn't specify how to distinguish 'no notes yet' from 'search returned zero results'. Both show an empty results list. Clear messaging prevents Kohl from thinking the app is broken.

**Property:**

For all note list sizes N >= 0, the UI renders without error and provides appropriate context.

**Implies:**
- Implies empty-state messaging and visibility of search box — flag for Alice.
