/**
 * Message and translation types
 * 
 * Contracts:
 *   - contract-note-001: message envelope schema
 *   - contract-note-005: message schema and persistence model (backend)
 *   - contract-note-008: message read/display contract (GET /api/messages/{message_id})
 * 
 * These types reflect the backend contract exactly.
 * Frontend must treat the backend response as the source of truth.
 */

/**
 * TranslationStatus: backend tracks the state of translation for each message
 * 
 * pending  — message stored, translation in flight
 * complete — message stored, translation successful and available
 * failed   — message stored, translation failed; original visible, user can retry
 */
export type TranslationStatus = 'pending' | 'complete' | 'failed';

/**
 * Message — the complete message record from backend
 * 
 * Matches backend schema contract-note-005.
 * All fields present in backend response (including nullable fields).
 * 
 * Invariants enforced by backend:
 *   - (translation_status = 'complete') ⟺ (translated_text is non-null AND translation_timestamp is non-null)
 *   - message_id is globally unique and immutable
 *   - original_text and original_language are immutable after creation
 * 
 * Client responsibility:
 *   - Display translation_status to determine UI state
 *   - Never mutate original_text or original_language
 *   - Use translation_status as authoritative; do not predict or infer it
 */
export interface Message {
  // Identifiers
  message_id: string; // UUID
  sender_id: string; // FK to users table

  // Content — immutable after creation
  original_text: string; // non-empty, ≤2000 chars
  original_language: string; // enum: EN, DE, JA, etc.

  // Translation — mutable per contract-note-004 (retry flow)
  translated_text: string | null; // non-empty, ≤2000 chars, or null if not yet translated
  target_language: string | null; // enum, nullable if translated_text null

  // Translation metadata
  translation_model: string | null; // e.g., 'claude-haiku-4.5', nullable if not yet translated
  translation_status: TranslationStatus; // backend tracks the state
  translation_timestamp: string | null; // ISO 8601 timestamp, or null if not yet translated
  translation_error: string | null; // error message if translation_status='failed', else null

  // GDPR
  message_retention_flag: string; // e.g., 'ephemeral' | 'persistent', never null

  // Audit
  created_at: string; // ISO 8601 timestamp, immutable
  updated_at?: string; // ISO 8601 timestamp, may not be present in v1
}

/**
 * MessageListRequest — parameters for fetching a list of messages
 * 
 * Contract: GET /api/messages?thread_id=X&limit=20&offset=0
 * (specific pagination shape TBD; this is v1 placeholder)
 */
export interface MessageListRequest {
  thread_id: string;
  limit?: number; // default 20, max 100
  offset?: number; // default 0
}

/**
 * MessageListResponse — paginated list of messages
 */
export interface MessageListResponse {
  messages: Message[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * MessageCreateRequest — payload for POST /api/messages
 * 
 * Contract: contract-note-007
 * Frontend sends this after translate-on-send completes (or fails).
 * 
 * If translated_text is provided (translation succeeded):
 *   backend sets translation_status='complete', translation_timestamp=now()
 * 
 * If translated_text is null (translation failed or not attempted):
 *   backend sets translation_status='pending', translation_timestamp=null
 *   User can retry translation later via PATCH endpoint
 */
export interface MessageCreateRequest {
  original_text: string;
  original_language: string; // enum
  translated_text?: string | null; // nullable; if absent, backend treats as null
  target_language?: string | null; // nullable; must match translated_text
  message_retention_flag: string; // required by backend for GDPR
}

/**
 * MessageCreateResponse — backend response to POST /api/messages
 * 
 * Returns the full message record as stored.
 */
export type MessageCreateResponse = Message;

/**
 * TranslateRequest — payload for POST /api/translate
 * 
 * Contract: contract-note-002, contract-note-006
 * Frontend calls this to get a translation before storing the message.
 * Backend streams response back as JSON lines.
 */
export interface TranslateRequest {
  original_text: string;
  original_language: string; // enum
  target_language: string; // enum
}

/**
 * TranslateChunk — one chunk of the streaming translate response
 * 
 * Contract: contract-note-006 specifies response is JSON lines.
 * Each line is { chunk, done, confidence? }.
 * Frontend buffers chunks into running translated_text.
 * When done=true, translation is complete.
 */
export interface TranslateChunk {
  chunk: string; // partial translation text
  done: boolean; // true on final chunk
  confidence?: number; // 0.0-1.0, optional
}

/**
 * TranslateError — error response from translate service
 * 
 * Contract: contract-note-006
 * Backend returns 4xx/5xx with error detail.
 * 4xx errors are permanent (unsupported_language_pair); 5xx are retryable (timeout).
 */
export interface TranslateError {
  error: string;
  code:
    | 'unsupported_language_pair'
    | 'timeout'
    | 'rate_limit'
    | 'internal_error'
    | 'validation_error';
}

/**
 * ClientMessageState — client-side state for a message during send flow
 * 
 * Used during the compose → translate → save flow.
 * Not persisted; represents in-flight state only.
 */
export interface ClientMessageState {
  // Transient state during send
  isTranslating: boolean;
  translationProgress: number; // 0-1, for UI progress indication
  translationError: string | null;

  // Cached translated text (optimization; server is source of truth)
  cachedTranslation: string | null;
}

/**
 * MessageDraft — what the user is composing (before send)
 * 
 * Not part of the backend contract; client-side only.
 * Used during composition before the message is sent.
 */
export interface MessageDraft {
  original_text: string;
  original_language: string;
  target_language: string;
}
