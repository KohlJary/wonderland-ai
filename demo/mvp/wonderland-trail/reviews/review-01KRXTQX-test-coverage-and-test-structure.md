## Review 014: Test coverage and test structure

**GUID:** 01KRXTQXF47YR10VMSRG8DBP3M
**Files reviewed:** tests/test_notes.py, tests/test_notes_edge_cases.py, tests/test_health.py
**Verdict:** accept

### Approvals

- test_notes.py covers the happy paths: POST with minimal input, with body, with tags, with all fields. POST validation errors (empty title, missing title). GET by ID and 404. Timestamp format checks. This is the baseline and it's solid.
- test_notes_edge_cases.py is excellent adversarial work. Each test has a clear docstring explaining the scenario and severity. The tests cover: tag creation race conditions, PUT with empty tag_names vs. omitted tag_names, cascade delete with shared tags, invalid tag IDs, delete association of unassociated tag, list ordering, idempotency of tag association, timestamp ISO8601 format, multiline body, emoji support. This is comprehensive edge-case coverage.
- The conftest.py correctly sets up an in-memory SQLite for each test and overrides FastAPI's get_db dependency. This is the right pattern for unit testing FastAPI.
- test_health.py validates the /health endpoint works. Simple but important for deployment.
