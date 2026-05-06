# Contract Note: Message Envelope Shape

**Status:** proposed

## Current Shape
None — this is the initial contract for v1.

## Proposed Change
Define the message envelope shape for POST /conversation/:other_user_id/messages and GET /conversation/:user_id/:other_user_id.

### POST /conversation/{other_user_id}/messages

**Request:**
```json
{
  "language_code": "en",
  "text": "Hello, how are you?"
}
```

**Response (201):**
```json
{
  "id": 1,
  "sender_id": 42,
  "language_code": "en",
  "text": "Hello, how are you?",
  "translation": null,
  "translation_service": null,
  "translation_confidence": null,
  "is_human_verified": null,
  "created_at": "2025-01-15T10:30:00Z"
}
```

**Rationale:**
- `sender_id` is implicit from auth context (not in request, returned in response so client knows who sent what).
- `language_code` is explicit in request so sender can specify their native language.
- `text` is the original message.
- `translation`, `translation_service`, `translation_confidence`, `is_human_verified` are all null on creation (translation happens async or on GET, depending on backend routing).
- `created_at` is server-set.

### GET /conversation/{user_id}/{other_user_id}

**Query params:**
- `limit=50` (pagination; default 50, max 100)
- `offset=0` (pagination)

**Response (200):**
```json
{
  "messages": [
    {
      "id": 1,
      "sender_id": 42,
      "language_code": "de",
      "text": "Hallo, wie geht es dir?",
      "translation": "Hello, how are you?",
      "translation_service": "pending",
      "translation_confidence": null,
      "is_human_verified": false,
      "created_at": "2025-01-15T10:30:00Z"
    },
    {
      "id": 2,
      "sender_id": 99,
      "language_code": "en",
      "text": "I'm doing well, thanks!",
      "translation": null,
      "translation_service": null,
      "translation_confidence": null,
      "is_human_verified": null,
      "created_at": "2025-01-15T10:31:00Z"
    }
  ],
  "total": 2
}
```

**Rationale:**
- Messages are ordered by `created_at` (oldest first, matching Story 001 requirement: "order of messages is preserved").
- Each message includes both original (`language_code` + `text`) and translation fields.
- `translation_service` is "pending" (string) if translation is queued, null if original language matches viewer's language, or the service name ("openai", "google_translate", "local_llm", etc.) if translation is complete.
- `translation_confidence` is only populated when translation is complete (range 0–1).
- `is_human_verified` is a flag (true/false) indicating whether a human has reviewed this translation. Defaults to false for machine translations.

### Scenario Coverage

**Story 001 (Klaus ↔ Maya):**
- Klaus (sender_id=42, language_code="de") sends "Hallo, wie geht es dir?"
  - POST returns message with translation=null, translation_service=null (pending)
  - GET /conversation/:klaus/:maya returns Klaus's message with translation="Hello, how are you?", translation_service="service_name", is_human_verified=false
  - GET /conversation/:maya/:klaus returns Klaus's message same way (both users see same message data)
  - Maya (sender_id=99, language_code="en") sends "I'm doing well, thanks!"
  - POST returns message with translation=null
  - GET /conversation/:maya/:klaus returns Maya's message with translation=null (because it's already in English, her language preference)
  - GET /conversation/:klaus/:maya returns Maya's message with translation="Mir geht es gut, danke!", translation_service="service_name"

**Story 003 (no re-translation):**
- Klaus's message is stored with language_code="de" (original)
- When Klaus GETs /conversation/:klaus/:maya, the backend knows his language is German, so translation=null (message is already in his language)
- When Maya GETs /conversation/:maya/:klaus, the backend knows her language is English, so translation is populated (translation of German → English)

**Story 004 (translation provenance):**
- `translation_service` indicates the service used
- `is_human_verified` indicates whether a human has signed off
- `translation_confidence` indicates machine confidence (0–1)

## Frontend Impact

- `POST /conversation/{other_user_id}/messages`: Client sends `{language_code, text}`, receives full message envelope (needed for immediate UI render with all fields, even if some are null).
- `GET /conversation/{user_id}/{other_user_id}`: Client polls every 2s, renders original + translation fields (translation may be null, placeholder shows "Translating...").
- **UI state machine:** 
  - Pending: `translation_service="pending"` → show "Translating..."
  - Ready: `translation_service!==null and translation!==null` → show translation
  - Same language: `translation===null and language_code===viewer_language` → show original only
  - Error: `translation_service="error"` → show error state (open question: should backend return this or should translation simply remain null?)

## Backend Impact
[Tweedledum fills in]

## Open Questions

1. **Translation service routing:** The field `translation_service` is a string (e.g., "openai", "google_translate", "local_llm"). But where does this get populated? On POST (sync call before response) or on GET (async job that fills it in later)? This is the BLOCKER-translation-routing-decision.
   - If POST is sync: translation happens before response, `translation` + `translation_service` are populated immediately.
   - If async: translation happens in background, POST returns `translation=null`, `translation_service="pending"`, and a background job fills in both fields before the next GET.

2. **Same-language optimization:** When sender and viewer have the same language, should the backend omit translation fields (set to null) or should it not populate them? Current proposal: set to null. This lets frontend know "translation was considered, not needed".

3. **Error handling:** If translation fails (API timeout, service down, bad input), what should `translation_service` be? Proposal: "error" (string), with `translation` remaining null. Frontend shows error state. Alternative: omit the envelope fields, return 500. Preference?

4. **Historical messages:** When viewing a thread, should historical messages get re-translated if translator service changes? Or is translation immutable once created? Proposal: immutable (once created, never re-translated). Keeps audit trail clean per ADR tradeoff discussion.

## Resolution
Proposed — awaiting Tweedledum feedback on backend feasibility and open questions.
