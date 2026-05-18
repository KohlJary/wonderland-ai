## Scenario 005: Note schema can be introspected by frontend for contract validation

**GUID:** 01KRXSBF5S803EBBPVQ3MVFZ1N
**Severity:** curiosity

**Setup:**

Note model is exported from src.backend.models

**Trigger:**

Frontend (or integration test) reads the Note model and extracts field names and types

**Expected:**

Fields are readable: id, title, body, created_at, updated_at. Types are clear (string for title/body, datetime for timestamps)

**Concern:**

The ticket says 'schema is documented in a contract file readable by both backend and frontend.' This might mean a .md file, or it might mean the Python model itself should be clearly readable. I'm curious whether the Tweedles will export a schema introspection function, or if the frontend will just hard-code the field names.
