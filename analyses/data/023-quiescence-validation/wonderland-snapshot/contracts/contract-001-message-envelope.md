# Contract Note 001: Message Envelope Shape

**Status:** proposed → **responded**
**Created:** 2025 (current session)
**Last Updated:** responded (tweedledee)
**Negotiation Thread:** design-and-ship

## Current Shape

Legacy `/api/messages` endpoint:
- POST request: `{text: str}`
- POST response: `{id: int, text: str, created_at: ISO8601}`
- GET request: `/api/messages`
- GET response: `[{id, text, created_at}]`

Single-user, no language awareness, no translation support.

## Proposed Change

### POST /message
**Request:**
```json
{
  "sender_id": int,
  "language_code": "en" | "de" | "ja",
  "original_text": string (1..2000 chars)
}
```

**Response:**
```json
{
  "message_id": int,
  "sender_id": int,
  "language_code": "en" | "de" | "ja",
  "original_text": string,
  "created_at": "ISO8601",
  "translations": []
}
```

The `translations` array is initially empty. Once translation service is integrated (separate ticket), this array will populate with translation artifacts.

### GET /conversation/:user_id/:other_user_id
**Query parameters:**
- `language_preference`: "en" | "de" | "ja" (optional; used as a hint for frontend, backend returns all translations and lets frontend decide what to render)
- `before_id`: int (optional; for pagination)

**Response:**
```json
[
  {
    "message_id": int,
    "sender_id": int,
    "language_code": "en" | "de" | "ja",
    "original_text": string,
    "created_at": "ISO8601",
    "translations": [
      {
        "target_language": "en" | "de" | "ja",
        "translated_text": string,
        "service_used": "pending" | "google" | "aws" | "local" (TBD pending routing decision),
        "confidence_score": 0.0..1.0,
        "is_human_verified": bool,
        "created_at": "ISO8601"
      }
    ]
  }
]
```

Ordered by `message_id` ascending (chronological). Backend returns **all translations** for each message; frontend filters/renders based on viewing user's language preference and role.

## Source

- Story 001: Two monolingual users (Maya + Klaus) exchange messages
- Story 002: Polyglot moderator (Jin) sees originals + translations side-by-side
- Story 003: User sees their own message in the language they sent it (no re-translation)
- Story 004: User can see translation provenance (machine vs. human)
- ADR-001: Message + Translation schema (asymmetric visibility model)
- Ticket 001: Define API contract
- Ticket 002: Backend storage + POST/GET endpoints

## Backend Impact

**Storage Layer:**
- `Message` table:
  - `id` (PRIMARY KEY)
  - `sender_id` (FOREIGN KEY → User)
  - `language_code` (ENUM: en, de, ja, ...)
  - `original_text` (TEXT)
  - `created_at` (DATETIME, server-default: now)
  - Immutable: no UPDATE on original_text

- `Translation` table:
  - `id` (PRIMARY KEY)
  - `message_id` (FOREIGN KEY → Message)
  - `target_language` (ENUM: en, de, ja, ...)
  - `translated_text` (TEXT)
  - `service_used` (STR: null during v1 stub)
  - `confidence_score` (FLOAT: null during v1 stub)
  - `is_human_verified` (BOOL: false during v1 stub)
  - `created_at` (DATETIME, server-default: now)
  - Append-only: no UPDATE on translated_text

**Invariants:**
- Each message has exactly one original (unique sender_id + language_code + created_at for a given sender in a given conversation).
- Each message-target_language pair has at most one translation (UNIQUE constraint on (message_id, target_language)).
- Deletion: when a user deletes their message, originals are soft-deleted (added `deleted_at` column), cascade soft-deletes translations. (Hard vs. soft is pending Queen's ruling; scaffold both for now.)

**Endpoints:**
- `POST /message`: insert into Message, return envelope with empty translations[].
  - Idempotent: message_id in response is stable (not regenerated on retry).
  - Error handling: validation error on sender_id (not found), language_code (not in ENUM), original_text (empty or >2000 chars). Translation service failure (not applicable v1, but when integrated: if translation fails, message appears with empty translations[] rather than blocking the send).

- `GET /conversation/:user_id/:other_user_id`: SELECT from Message JOIN Translation WHERE (sender_id IN (user_id, other_user_id)), ordered by created_at ASC.
  - Query cost: O(n) Message rows × O(m) Translation rows per message (JOIN). At v1 volumes this is fine; at scale we may need query optimization (e.g., materialize "best translation per message per language" to avoid fetching all).
  - Pagination: limit 100 default, use `before_id` param for infinite scroll if needed.
  - Language preference: query parameter is a hint; backend returns all translations, frontend decides what to show.

**Edge Cases:**
- If viewing user's language is not in {original_language, any translation target_language}: frontend gets original + all translations; decides what to show (typically original + all available or best-guess match).
- If translation service is down or slow: message appears immediately with translations[] empty; translations populate asynchronously when service recovers.
- If same message is requested by multiple viewers: all get the same canonical translations[] (no per-viewer translation); consistency is guaranteed.

## Frontend Impact

**Client State & Caching:**
- Conversation list is **cached in React state** (useState) during session; single source of truth is the server.
- Invalidation: on POST /message (optimistic update adds message to local list), on explicit "refresh" action (calls GET /conversation again).
- No persistent client cache (localStorage) for v1; translations arriving late will render as `pending-translation` state. Next full refresh (user closes thread, re-opens) gets canonical state from server.

**Language Preference & User Context:**
- Language preference is **query parameter to GET /conversation** (e.g., `?language_preference=en`). Frontend reads this from:
  - URL state (if conversation is deep-linked, language_preference can be in the URL)
  - User profile / session context (TBD: assumed to exist; not in scope of this contract)
  - Default: user's **browser language** (`navigator.language`) if not explicitly set
- Sending user's language_code is specified in **POST /message** as `language_code` field; this is **user's preferred send language**, not a runtime detection.

**Rendering Rules & UI States:**
The frontend renders **four distinct message views depending on context**:

1. **Monolingual View (Story 001: Maya ↔ Klaus)**
   - Sender's own message: shows `original_text` only. Language code rendered as tag (e.g., "🇩🇪 Deutsch").
   - Other user's message: shows `original_text` + translations[] filtered to **viewer's language_preference**.
     - If translations[] contains `target_language == viewer's language_preference`: show translation below original with light gray text.
     - If translations[] is empty: show `pending-translation` state (loading spinner + original text).
     - If viewer's language not in translations[]: show original text (readable if polyglot, otherwise show "translation not available" + all available target languages as chips).
   - UI state: `message-original-only`, `message-with-translation`, `message-pending-translation`, `message-translation-unavailable`.

2. **Translation Pending State (Story 003: Klaus sees his own outgoing message immediately)**
   - When Klaus sends a message in German, his outgoing POST response has `translations: []` (empty).
   - Frontend immediately renders his message as `language_code: "de"` + original text.
   - No translation requested for own-language view (matches his sending language).
   - Once translation service populates Translation rows, GET /conversation refetch (manual or auto-poll) updates the view for other users' viewing context.

3. **Audit / Moderator View (Story 002: Jin sees originals + all translations)**
   - Moderator role (flag in user profile or JWT claim, TBD) triggers **audit view**.
   - GET /conversation called with `?language_preference=moderator` (or role flag in header, TBD).
   - Renders each message as: `original_text (language_code)` + all translations[] in a table (target_language, translated_text, service_used, confidence_score, is_human_verified).
   - UI state: `message-audit-view`.

4. **Translation Provenance (Story 004: Yuki sees which translations are trusted)**
   - All views include a small metadata chip under the translation: `service_used + confidence_score + human_verified flag`.
   - Tooltip on click shows full `created_at` and service details.
   - UI state: integrated into `message-with-translation` or `message-audit-view`.

**Handling Missing Translations (Error-Recoverable):**
- If translations[] is returned empty (translation service not yet run): show original + `pending-translation` spinner.
- Frontend should **poll or subscribe** to updates:
  - v1 approach: manual "refresh" button in conversation header (user initiates refetch of GET /conversation).
  - v1.5+ approach: WebSocket subscription to message updates (scope deferred to Ticket 005).
- If translation service permanently fails (service_used == "error"): show original + error message "translation failed" (recoverable state; user can retry).
- UI state: `message-pending-translation`, `message-translation-error` (both error-recoverable).

**Pagination & Load Performance:**
- Initial load: GET /conversation (no `before_id`) fetches last 100 messages.
- Scroll to top (infinite scroll): GET /conversation with `before_id=<oldest_message_id>` fetches next 100 older messages.
- Each message in the list renders **all translations[]** from the server response; no re-fetching per translation.
- Client state grows with message count; no pruning (v1 assumption: conversations under 1000 messages fit in session memory).

**Caching & Reconciliation:**
- Optimistic POST: immediately add new message to local list with `sender_id=current_user, language_code=user's send language, translations: []`.
- Reconciliation on GET refetch: compare `message_id`s. If server has an older message missing from client, append it (scroll-back case). If client has a newer message not yet on server, keep it (message in flight). No merge conflict expected (messages are append-only).
- Client state = React useState; no persistence across sessions.

## Answers to Backend Questions

**Q1: Does frontend cache the conversation?**
- Yes, React state (session-duration cache). Invalidated by manual refresh or polling.

**Q2: Language preference — how does frontend determine it?**
- Query parameter to GET /conversation, seeded from user profile / browser language / URL state.

**Q3: What does UI show when translation not available?**
- Loading spinner + original text (state: `pending-translation`). Manual refresh button to retry.

**Q4: Max translations per message?**
- No hard limit enforced on frontend. Backend returns all translations[]; frontend renders all in audit view, best-match in monolingual view.

**Q5: Moderator GET endpoint — same or different?**
- Same endpoint (`/conversation/:user_id/:other_user_id`), role/context flag determines rendering (audit view vs. monolingual).

---

## Resolution

**Operation:** responded (tweedledee → tweedledum)
**Frontend impact filled:** ✓
**Next Step:** Tweedledum reviews frontend answers and confirms no backend constraint conflicts. If all aligned, either side marks contract as `agreed` and we move to implementation.

**Potential backend follow-ups for Tweedledum to address:**
- Does the "manual refresh" on GET /conversation have a rate limit or caching header?
- Should GET /conversation check user's role/permission (who can see which conversations)?
- Is the empty translations[] edge case in POST response the canonical way to indicate "no translations yet," or should the response omit the field?

