/**
 * Frontend type definitions aligned to locked contracts.
 * Contract versions referenced:
 * - CN-005: translation gateway (message envelope with translation_status)
 * - CN-006: consent audit trail (per-session consent state)
 * 
 * These types are the frontend's reading of the backend contract.
 * Changes here require Contract Note negotiation with Tweedledum.
 */

export type TranslationStatus = 'completed' | 'failed' | 'pending' | 'not_requested';

export interface MessageEnvelope {
  id: string;
  sender_id: string;
  recipient_id: string;
  conversation_id: string;
  source_language: string;
  original_text: string;
  translated_text: string | null;
  translation_status: TranslationStatus;
  translation_provider: string | null;
  timestamp: number;
  received_at: number | null;
}

export interface SessionState {
  user_id: string;
  session_id: string;
  source_language: string; // user's native/preferred language
  target_language: string; // language for receiving translations
  eu_jurisdiction_detected: boolean;
  eu_consent_given: boolean;
  consent_version: string;
  consent_given_timestamp: number;
  consent_withdrawn: boolean;
  consent_withdrawn_timestamp: number | null;
}

export interface ConsentAuditEntry {
  user_id: string;
  session_id: string;
  consent_version: string;
  eu_jurisdiction_detected: boolean;
  consent_given_timestamp: number;
  consent_given_action: 'UI-accept' | 'programmatic' | 'default';
  consent_withdrawn_timestamp: number | null;
  consent_withdrawn_action: 'user-initiated' | null;
}

export interface APIError {
  code: string;
  message: string;
  status: number;
}
