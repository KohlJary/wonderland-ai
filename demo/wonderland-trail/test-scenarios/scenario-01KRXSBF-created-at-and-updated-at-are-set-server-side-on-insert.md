## Scenario 003: created_at and updated_at are set server-side on insert

**GUID:** 01KRXSBF5S803EBBPVQ3MVFZ1K
**Severity:** degradation

**Setup:**

Note table exists with created_at and updated_at columns

**Trigger:**

Insert a Note with only title and body; do not provide created_at or updated_at

**Expected:**

Row inserts successfully; created_at and updated_at are populated by the server (via database default or ORM server_default)

**Concern:**

If created_at and updated_at are not set with server-side defaults, the ORM layer has to generate them. But if the Tweedles forget to set them in the insert logic, the columns will be NULL. The frontend will then try to display timestamps that don't exist. This is degradation because the system works but fails to meet the contract.
