## Contract Note 001: Message envelope for polyglot mesh: translation visibility

**State:** agreed
**Contract Version:** v1 (JSONB envelope with per-language status substatus, selective eager-load query pattern, async translation worker with SLA ~5s)

**Current Shape:**

Message envelope assumed: {id, author_id, original_lang, original_text, translated_text, created_at}. This assumes hub routing (one translation per message).

**Proposed Change:**

Mesh model requires the envelope to carry *all* translations the user can see, not just one. Proposed shape: {id, author_id, original_lang, original_text, translations: {lang_code: translated_text}, created_at, translation_status: enum(pending/complete/failed)}. Alternative: translations as array [{lang, text, status}]. Or: translations stored separately with FK relationship and queried on read.

**Source:** ADR-003 (polyglot mesh commitment), story-003 (Yuki expects to see messages in her language without English bridge), story-002 (Marcus needs translation_status to spot where translation is failing)

**Frontend Impact (Tweedledee):**

Message envelope shape locked: {original_language, translations: {lang_code: {text, status}}, translation_status: computed_summary}. Single SELECT returns message + all translations computed so far. Frontend filters for user languages and renders per-language status badge. Loading/error/complete states are per-language, allowing partial-visibility (EN complete, JA still pending). Preference change mid-thread: user sees existing translations or refresh triggers new fetch (lazy-consistency acceptable for v1). Clarifying question: retroactive translation jobs when new user joins—are they enqueued immediately (I render 'loading...') or eventual-batch (I render 'enqueuing...')? Either is fine; I need to know which to design the UI correctly.

**Backend Impact (Tweedledum):**

[Tweedledum's assessment: eventual-consistency envelope with per-language status, sequential DeepL API calls, background worker async updates, 3-retry logic over 5min, JSONB indexing decision for retroactive lookups.]

**Resolution:**

Tweedledee confirmed selective eager-load query pattern (load only requested_languages, not full translations map). Stale translations on preference change acceptable for v1 (user refreshes). Both sides aligned on envelope shape, query pattern, translation timing, and UI states. Contract locked; ready for implementation.
