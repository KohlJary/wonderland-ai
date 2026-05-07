## Story 007: Understand the database schema for future multi-user support

**Persona:** Not a user persona — this is an architectural / domain-modeling story. The team needs to design the database so that adding multi-user later doesn't require a rewrite.

**Situation:**

The directive says 'design with a real database so multi-user can be added later.' Right now it's single-user local, but the database should be structured so that when auth is added, the schema doesn't need to be torn apart.

**Need:**

As a future developer adding multi-user support, I want the current single-user database to already have a `users` table with a foreign key in the `sessions` table, so that adding authentication doesn't require a schema migration.

**Acceptance:**
- The database has at least: `users` table (id, created_at, potentially email/username for future auth), `sessions` table (id, user_id, start_time, session_length_minutes, break_length_minutes, is_break, completed_at)
- The schema has no user-identifying data hard-coded (e.g., all sessions are tagged with user_id, even if there's only ever one user in the local app)
- The Caterpillar and Tweedles review this schema for multi-user extensibility

**Tier:** core

**Confusion-flags:**
- I'm not a database designer, so this story feels slightly outside my domain. But the directive explicitly calls out 'design with a real database for multi-user later,' so the team needs to think about it from the start. I'm flagging this as a story that needs the Cheshire Cat's architectural eye — it's user-adjacent (future users will thank us), but the implementation is the Cat's / Tweedles' domain.
