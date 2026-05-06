## Contract Note 001: Message send request envelope (POST /conversations/{id}/messages)

**State:** proposed
**Contract Version:** (unlocked)

**Current Shape:**

undefined

**Proposed Change:**

POST /conversations/{id}/messages accepts {text: string, language: string} and stores in Message(id, conversation_id, sender_id, text_original, text_language, created_at, deleted_at). Sender is inferred from auth context (not in request body). Response returns {id, sender_id, text_original, text_language, created_at}.

**Source:** ticket-003 (message model) + ticket-005 (endpoints)

**Frontend Impact (Tweedledee):**

Sender provides {text, language} to POST. Language must be one of the two languages in the conversation's language_pair (e.g., 'en' or 'de' if conversation is en_de). Frontend validates this client-side before sending. Sender inferred from auth is correct—no need to send sender_id in request. Response returns {id, sender_id, text_original, text_language, created_at}; I use id to echo the message to the user immediately (optimistic send), and created_at to timestamp it in the UI. Two open questions: (1) Should POST also return text_translated=null in the response, or does the client infer it as null? (I can handle either; explicit is clearer.) (2) Should language be required or optional in the request? If required, I validate against language_pair and show error if mismatch. If optional, I auto-fill based on user profile. I'm proposing language=required, and frontend shows error if invalid. This keeps the contract unambiguous.

**Backend Impact (Tweedledum):**

Validates language code matches conversation's language_pair. Enforces sender is authenticated user. Creates Message row with soft-delete support (deleted_at=NULL). No translation happens on write. Returns created message for echo to frontend.
