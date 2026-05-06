## Contract Note 005: Message schema and persistence model

**State:** agreed
**Contract Version:** v1

**Current Shape:**

No explicit contract yet. Assumption: messages have text, sender, timestamp. Translation is unknown.

**Proposed Change:**

Define message record as: message_id (UUID), sender_id (FK), original_text (string, ≤2000 chars), original_language (enum: EN, DE, JA, ...), translated_text (string, nullable, ≤2000 chars), target_language (enum, nullable), translation_model (string, e.g. 'claude-haiku-4.5'), translation_timestamp (timestamp, nullable), translation_status (enum: pending | complete | failed), message_retention_flag (string, GDPR per-message retention policy), created_at (timestamp), updated_at (timestamp). Message is stored as a 1:1 pair (original + single target language per record). Multi-target is fast-follow.

**Source:** adr#1 and ticket#1: message schema must store original + translation as a unit; translation_status tracks whether translate-on-send has completed; translation_model field documents which model produced the translation (for auditing + future model swaps).

**Frontend Impact (Tweedledee):**

Confirms: UI will treat translation_status as source of truth for rendering. Messages with translation_status='pending' will display translating indicator. Messages with translation_status='complete' will show both original_text + translated_text. Messages with translation_status='failed' will show original_text + error + retry button. No client-side prediction of translation_status; all state derives from server record.

**Backend Impact (Tweedledum):**

Backend accepts (original_text, original_language, target_language) from frontend. Backend writes message record with original_text + original_language + message_retention_flag immediately (timestamp T0). Backend calls translation service asynchronously (see contract 006). On translation completion, backend updates translated_text + translation_timestamp + translation_status=complete. On translation failure, translation_status=failed (message visible in UI with 'translation failed' indicator; retry available). GDPR compliance: message_retention_flag set per Alice's stories (Sophie's story surfaces GDPR scope); deletion of message cascades to translation record—no orphaned translations. Query load: frontend requests message by message_id (includes original + translation). No translation-status filtering on backend—UI handles 'translation pending' display. 

**Invariants Enforced:**
- (translation_status = complete) ⟺ (translated_text is non-null AND translation_timestamp is non-null)
- message_id is globally unique and immutable
- original_text and original_language are immutable after creation
- translation_status transitions are monotonic: pending → (complete | failed); no reversion

**Schema:**

```sql
CREATE TABLE messages (
  message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sender_id UUID NOT NULL REFERENCES users(user_id),
  original_text TEXT NOT NULL CHECK (length(original_text) > 0 AND length(original_text) <= 2000),
  original_language VARCHAR(2) NOT NULL,
  translated_text TEXT CHECK (translated_text IS NULL OR length(translated_text) <= 2000),
  target_language VARCHAR(2),
  translation_model VARCHAR(255),
  translation_timestamp TIMESTAMP WITH TIME ZONE,
  translation_status VARCHAR(20) NOT NULL DEFAULT 'pending' 
    CHECK (translation_status IN ('pending', 'complete', 'failed')),
  translation_error TEXT,
  message_retention_flag VARCHAR(100),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  CONSTRAINT translation_complete_iff_text_and_timestamp AS (
    (translation_status = 'complete' AND translated_text IS NOT NULL AND translation_timestamp IS NOT NULL)
    OR (translation_status != 'complete' AND translated_text IS NULL AND translation_timestamp IS NULL)
  )
);

CREATE INDEX idx_messages_sender_created ON messages(sender_id, created_at DESC);
```

**Resolution:** Agreed. Tweedledee confirms UI patterns align with schema. No changes required.

