# Relational Memory: Tweedledee

**Agent:** Tweedledee (Frontend)
**Relationship:** Paired implementation partner
**Threads:** design-and-ship (initiating)

## Working Assumptions

- Tweedledee owns frontend, I own backend. The seam between us is the HTTP contract (POST /message, GET /conversation).
- The contract is non-negotiable once agreed — implicit contracts are bugs in the making.
- Arguments on the contract are healthy; we resolve via explicit Contract Notes, not via email or assumptions.
- When he pushes back on a contract, my default is to ask why rather than assert.

## First Negotiation: Message Envelope

**Status:** Just proposed — awaiting his response.

**My side (backend):**
- Storage: Message (original language + text) + Translation (artifacts with provenance) tables
- POST /message: accept sender_id, language_code, original_text; return message_id + empty translations[]
- GET /conversation: return messages with all translations (unfiltered)
- Invariants: original immutable, translations append-only, one original per message
- Failure modes: if translation service fails, message appears with empty translations[] (not blocking)

**His side (frontend) — awaiting:**
- Client caching strategy? (local cache vs. always re-fetch)
- Language preference flow? (query param, localStorage, user profile)
- Rendering when translations lag? (show original, loading spinner, placeholder)
- Moderator visibility? (same GET endpoint with role flag, or different endpoint)

## Next Steps

1. He responds with frontend impact
2. One of us raises edge cases (what if viewing user's language isn't covered?)
3. We either agree + version, or escalate to Cat if architectural question surfaces

## Mirror Log (emerging)

*To be populated as collaboration stabilizes.*
