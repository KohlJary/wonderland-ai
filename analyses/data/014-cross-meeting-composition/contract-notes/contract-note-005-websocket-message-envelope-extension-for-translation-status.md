## Contract Note 005: WebSocket Message Envelope Extension for Translation Status

**State:** agreed
**Contract Version:** message-envelope v2 (translation_status object with enum status and failure_reason; translated_body present only when status=complete)

**Current Shape:**

Current message envelope includes: message_id, user_id, content, created_at, source_language. Translation is not yet in the contract.

**Proposed Change:**

Extend message envelope with: translation_status (enum: pending | in_flight | complete | timeout), translated_body (optional, present only when status=complete), target_language (the language the user requested), source_language (the original message language). Each message event includes these fields. Translation status updates are emitted as separate WebSocket events (`message_translation_status_updated`) rather than re-broadcasting the entire message.

**Source:** Translation MVP story + Cheshire Cat's proposal on on-read translation model + Tweedledum's response on backend delivery constraints.

**Frontend Impact (Tweedledee):**

Frontend subscribes to both `message_received` and `message_translation_status_updated` events. Initial message arrival is pending (no translation yet). Translation status updates flow as events. Client state per message: `translationStatus` + `translatedBody` (cached locally). User's target language is persisted in localStorage (user preference, survives session). UI renders four states based on translation_status. Ready for implementation once backend confirms the event shape.

**Backend Impact (Tweedledum):** _pending_

**Resolution:**

agreed—contract now explicit about translation signal shape and failure-reason handling
