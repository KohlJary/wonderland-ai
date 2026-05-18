## Scenario 001: Note table can be created, populated, and rolled back cleanly

**GUID:** 01KRXSBF5S803EBBPVQ3MVFZ1H
**Severity:** breakage

**Setup:**

Fresh SQLite database with no tables

**Trigger:**

Apply the Note schema migration; insert a few notes; roll back the migration

**Expected:**

After apply, Note table exists and accepts inserts. After rollback, Note table is gone and inserts fail.

**Concern:**

The ticket says 'migration can be applied and rolled back cleanly.' If the migration file is incomplete (e.g., missing a CREATE TABLE or has a syntax error), this will fail immediately. Even if create_all() works in Python, Alembic migrations have their own requirements and failures.
