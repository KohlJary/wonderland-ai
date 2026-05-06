## Contract Note 005: Message POST request envelope (message-input-envelope-v1)

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

not yet defined

**Proposed Change:**

POST /conversations/{conversation_id}/messages accepts {text: string, language: string} in request body. 'language' is the BCP-47 language code the sender typed in (e.g., 'en', 'de', 'ja'). The conversation_id determines which language_pair this message belongs to; backend validates that the sender's language matches one of the two languages in the conversation's language_pair enum. Returns immediately with message object (same shape as GET response above), with text_translated initially empty or pending (see translation-call-surface contract below for timing).

**Source:** ticket 005 acceptance: 'POST accepts {text, language} and stores in Message table' + ADR decision to store text in sender's original language

**Frontend Impact (Tweedledee):**

I need to send language code with every message. The language code must be validated client-side against the conversation's language_pair (e.g., if conversation is en_de, I can only send 'en' or 'de'). Two design choices: (1) language selector in message input field (user picks each time), or (2) infer from user's profile/conversation context. Ticket 006 says 'language selector (or language inferred from User profile)'. I'm proposing we infer: if user is monolingual in this conversation (only one of the two languages is readable by them), we auto-fill the language field to the only language they can write in. If user is polyglot (can read both), we show a selector. Open question: should language be optional in the request (server defaults to one of the pair), or required? If required, my error handling is simpler.

**Backend Impact (Tweedledum):**

I require language in the POST body (not optional). On POST /conversations/{id}/messages with {text, language}, I validate: (1) conversation_id exists, (2) current user (from auth) is one of the two users in that conversation, (3) language is exactly one of the two languages in conversation.language_pair. If any validation fails, return 400 with specific error (e.g., 'language=ja not in conversation language_pair [en, de]'). I store {text_original, text_language, created_at}. Sender_id is inferred from auth (not in body). I do NOT call translation service on write—write is synchronous and fast. Translation happens only on read (GET). Regarding your design choice (infer vs. require language selector): I'm neutral on the frontend UX, but I need the language field in the request so I can validate it and store text_language. If you infer it on the client, I'll validate it. If you ask the user with a selector, I'll validate that too. Either way, the request shape requires language. Does the required field work for you, or do you want a default fallback if language is missing (I'd default to first language in the pair as last resort)?
