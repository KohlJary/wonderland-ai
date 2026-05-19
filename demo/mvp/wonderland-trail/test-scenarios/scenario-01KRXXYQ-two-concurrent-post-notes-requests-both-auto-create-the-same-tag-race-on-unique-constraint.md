## Scenario 162: Two concurrent POST /notes requests both auto-create the same tag (race on UNIQUE constraint)

**GUID:** 01KRXXYQD08R1GFPSWEN11326V
**Severity:** silent-wrongness

**Setup:**

Two requests arrive simultaneously with tag_names=['research']. The Tag.name column is globally unique.

**Trigger:**

Both threads execute _associate_tags, both query 'Tag.name == research' and get None, both create Tag(name='research') and flush.

**Expected:**

One Tag with name='research' is created. Both notes are tagged with it. No 500 errors.

**Concern:**

The code pattern is: query for tag, if not found, create and flush. But flush() doesn't acquire a database UNIQUE constraint lock until commit(). If two threads both pass the query check before either commits, both INSERT, and one gets a UNIQUE constraint violation (IntegrityError). The second request returns a 500 error instead of gracefully handling the race. The tag *is* created by the first request, so a retry would work, but the client sees an error.

**Property:**

For all concurrent requests with the same tag_name, at most one tag is created, and both notes are tagged, with no 5xx errors.

**Implies:**
- Implies a transaction isolation or upsert pattern — flag for Cat (architectural decision).
- Implies error handling on concurrent tag creation — flag for Tweedles (implementation).
