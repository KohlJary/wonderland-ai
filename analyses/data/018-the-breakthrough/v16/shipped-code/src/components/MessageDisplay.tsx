/**
 * MessageDisplay component — dual original+translation display
 * 
 * Contract: consumes GET /api/messages/{message_id} response shape
 * Schema version: contract-note-003, contract-note-008
 * 
 * Renders a single message with original and translation side-by-side.
 * Handles translation_status states: pending, complete, failed.
 * Manages show_original toggle per-session (not persisted to disk in v1).
 * 
 * UI States Implemented:
 *   - loading: original text visible, translation lane shows spinner
 *   - success: original + translation both visible (or translation only if hidden)
 *   - error-recoverable: original visible, translation lane shows error + retry button
 *   - error-unrecoverable: original visible, translation lane shows 'unsupported language pair'
 *   - pending: original visible, translation lane shows spinner + 'translating...'
 * 
 * Client State: show_original toggle lives on client, keyed by user+thread.
 * Server State: translation_status, translated_text, original_text are source of truth.
 * Reconciliation: UI derives from server state; toggle is UI-only preference.
 */

import React, { useState, useCallback } from 'react';
import { Message, TranslationStatus } from '../types/message';

interface MessageDisplayProps {
  message: Message;
  onRetryTranslation?: (messageId: string) => Promise<void>;
  isRetrying?: boolean;
}

/**
 * Translation status indicator + messaging
 * Maps backend translation_status to user-visible text and styling
 */
const getTranslationStatusDisplay = (
  status: TranslationStatus,
  error?: string | null
): { label: string; icon: React.ReactNode; className: string } => {
  switch (status) {
    case 'pending':
      return {
        label: 'Translating...',
        icon: <SpinnerIcon />,
        className: 'text-gray-500 italic',
      };
    case 'complete':
      return {
        label: 'Translated',
        icon: <CheckIcon />,
        className: 'text-green-600',
      };
    case 'failed':
      return {
        label: error || 'Translation failed',
        icon: <ErrorIcon />,
        className: 'text-red-600',
      };
    default:
      return {
        label: 'Unknown',
        icon: <ErrorIcon />,
        className: 'text-gray-600',
      };
  }
};

/**
 * Determines if the error is recoverable (user can retry)
 * Permanent errors: unsupported_language_pair, invalid_language
 * Recoverable errors: timeout, rate_limit, internal_error
 */
const isRecoverableError = (error?: string | null): boolean => {
  if (!error) return false;
  const permanentErrors = [
    'unsupported_language_pair',
    'invalid_language',
    'validation_error',
  ];
  return !permanentErrors.some((pe) => error.includes(pe));
};

export const MessageDisplay: React.FC<MessageDisplayProps> = ({
  message,
  onRetryTranslation,
  isRetrying = false,
}) => {
  const [showOriginal, setShowOriginal] = useState(() => {
    // Load preference from sessionStorage, keyed by user+thread
    // For v1, user_id and thread_id are placeholders;
    // in production, derive from auth context
    const key = `message-show-original-default`;
    const stored = sessionStorage.getItem(key);
    return stored !== null ? JSON.parse(stored) : true; // default: show original
  });

  const handleToggleOriginal = useCallback(() => {
    setShowOriginal((prev) => {
      const next = !prev;
      sessionStorage.setItem(`message-show-original-default`, JSON.stringify(next));
      return next;
    });
  }, []);

  const handleRetry = useCallback(async () => {
    if (!onRetryTranslation) return;
    try {
      await onRetryTranslation(message.message_id);
    } catch (err) {
      console.error('Retry translation failed:', err);
      // Hatter's test scenarios will cover error display here
    }
  }, [message.message_id, onRetryTranslation]);

  const statusDisplay = getTranslationStatusDisplay(
    message.translation_status,
    message.translation_error
  );
  const canRetry =
    message.translation_status === 'failed' &&
    isRecoverableError(message.translation_error);

  return (
    <div className="message-display border rounded-lg p-4 bg-white shadow-sm">
      {/* Message header: sender, timestamp, language pair */}
      <div className="message-header flex justify-between items-center mb-2">
        <div className="flex items-center gap-2">
          <span className="font-semibold">{message.sender_id}</span>
          <span className="text-xs text-gray-500">
            {new Date(message.created_at).toLocaleTimeString()}
          </span>
          {message.target_language && (
            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
              {message.original_language} → {message.target_language}
            </span>
          )}
        </div>
        {/* Toggle original display */}
        <button
          onClick={handleToggleOriginal}
          className="px-2 py-1 text-xs bg-gray-200 hover:bg-gray-300 rounded transition"
          aria-label={showOriginal ? 'Hide original' : 'Show original'}
        >
          {showOriginal ? 'Hide original' : 'Show original'}
        </button>
      </div>

      {/* Message content: original + translation in dual lanes */}
      <div className="message-content grid grid-cols-2 gap-4">
        {/* Original text lane */}
        {showOriginal && (
          <div className="original-lane border-r pr-4">
            <p className="text-xs font-semibold text-gray-600 mb-2">
              Original ({message.original_language})
            </p>
            <p className="text-base text-gray-900 whitespace-pre-wrap">
              {message.original_text}
            </p>
          </div>
        )}

        {/* Translation lane */}
        <div className={showOriginal ? 'translation-lane' : 'translation-lane-full'}>
          <p className="text-xs font-semibold text-gray-600 mb-2">
            Translation ({message.target_language || 'detecting...'})
          </p>

          {message.translation_status === 'pending' && (
            <div className="flex items-center gap-2 text-gray-500">
              <SpinnerIcon />
              <span>Translating...</span>
            </div>
          )}

          {message.translation_status === 'complete' && message.translated_text && (
            <p className="text-base text-gray-900 whitespace-pre-wrap">
              {message.translated_text}
            </p>
          )}

          {message.translation_status === 'failed' && (
            <div className="error-state">
              <div className="flex items-center gap-2 text-red-600 mb-2">
                <ErrorIcon />
                <span className="text-sm">{statusDisplay.label}</span>
              </div>

              {/* Show original text as fallback when translation fails */}
              <p className="text-sm text-gray-700 italic mb-2">
                Showing original: {message.original_text}
              </p>

              {/* Retry button if error is recoverable */}
              {canRetry && onRetryTranslation && (
                <button
                  onClick={handleRetry}
                  disabled={isRetrying}
                  className="px-3 py-1 text-sm bg-red-100 text-red-700 hover:bg-red-200 rounded transition disabled:opacity-50"
                  aria-label="Retry translation"
                >
                  {isRetrying ? 'Retrying...' : 'Retry translation'}
                </button>
              )}

              {/* Permanent error message */}
              {!canRetry && (
                <p className="text-xs text-red-600">
                  This language pair is not supported. Showing original text.
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Translation metadata (visible in debug mode or for transparency) */}
      {message.translation_model && (
        <div className="message-metadata mt-3 pt-3 border-t">
          <p className="text-xs text-gray-400">
            Model: {message.translation_model} |{' '}
            {message.translation_timestamp &&
              `Translated: ${new Date(message.translation_timestamp).toLocaleString()}`}
          </p>
        </div>
      )}
    </div>
  );
};

/**
 * Simple SVG icons for status display
 * In production, replace with icon library (e.g., react-icons)
 */
const SpinnerIcon = () => (
  <svg
    className="animate-spin h-4 w-4 inline"
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
  >
    <circle
      className="opacity-25"
      cx="12"
      cy="12"
      r="10"
      stroke="currentColor"
      strokeWidth="4"
    />
    <path
      className="opacity-75"
      fill="currentColor"
      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
    />
  </svg>
);

const CheckIcon = () => (
  <svg
    className="h-4 w-4 inline"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
  >
    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
  </svg>
);

const ErrorIcon = () => (
  <svg
    className="h-4 w-4 inline"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
  >
    <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z" />
  </svg>
);
