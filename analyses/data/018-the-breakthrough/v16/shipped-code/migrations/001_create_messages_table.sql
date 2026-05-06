-- Migration 001: Create messages table with original + translation as unit
-- Sources: ADR-001, contract-note-005, ticket-001
-- 
-- Invariants enforced:
-- - (translation_status = 'complete') ⟺ (translated_text IS NOT NULL AND translation_timestamp IS NOT NULL)
-- - original_text and original_language are immutable after creation
-- - message_id is globally unique
-- - translation_status transitions: pending → (complete | failed); no reversion

BEGIN;

CREATE TABLE IF NOT EXISTS messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sender_id UUID NOT NULL,
    
    -- Original message (immutable)
    original_text TEXT NOT NULL,
    original_language VARCHAR(2) NOT NULL,
    
    -- Translation (mutable until complete)
    translated_text TEXT,
    target_language VARCHAR(2),
    
    -- Translation metadata
    translation_model VARCHAR(255),
    translation_timestamp TIMESTAMP WITH TIME ZONE,
    translation_status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (translation_status IN ('pending', 'complete', 'failed')),
    translation_error TEXT,
    
    -- GDPR compliance: per-message retention flag
    message_retention_flag VARCHAR(100),
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Constraints enforcing invariants
    CONSTRAINT ck_original_text_length 
        CHECK (length(original_text) > 0 AND length(original_text) <= 2000),
    CONSTRAINT ck_translated_text_length 
        CHECK (translated_text IS NULL OR length(translated_text) <= 2000),
    CONSTRAINT ck_translation_complete_iff_text_and_timestamp 
        CHECK (
            (translation_status = 'complete' AND translated_text IS NOT NULL AND translation_timestamp IS NOT NULL)
            OR (translation_status != 'complete' AND translated_text IS NULL AND translation_timestamp IS NULL)
        )
);

-- Index for query performance: sender + creation order (for message list queries)
CREATE INDEX idx_messages_sender_created 
    ON messages(sender_id, created_at DESC);

-- Index for deduplication window queries: find recent messages by sender + text + languages
CREATE INDEX idx_messages_dedup_window 
    ON messages(sender_id, original_text, original_language, target_language, created_at DESC)
    WHERE created_at > NOW() - INTERVAL '5 seconds';

COMMIT;
