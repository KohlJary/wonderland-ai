/**
 * useMessageList — hook for fetching and managing message list
 * 
 * Handles:
 *   - Fetching message list from GET /api/messages
 *   - Polling for updated translation_status (if needed)
 *   - Optimistic updates when user sends a new message
 *   - Error state management
 * 
 * Contract:
 *   - GET /api/messages/{thread_id}?limit=20&offset=0
 *   - Returns { messages: Message[], total: number, limit: number, offset: number }
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import {
  Message,
  MessageListResponse,
  MessageCreateRequest,
  MessageCreateResponse,
} from '../types/message';

interface UseMessageListOptions {
  threadId: string;
  limit?: number;
  pollIntervalMs?: number; // poll for new translations
}

interface UseMessageListState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  hasMore: boolean;
  total: number;
}

export const useMessageList = ({
  threadId,
  limit = 20,
  pollIntervalMs = 2000, // poll for pending translations
}: UseMessageListOptions) => {
  const [state, setState] = useState<UseMessageListState>({
    messages: [],
    isLoading: false,
    error: null,
    hasMore: false,
    total: 0,
  });

  const [offset, setOffset] = useState(0);
  const pollTimerRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Fetch messages from backend
   * Contract: GET /api/messages
   */
  const fetchMessages = useCallback(
    async (fetchOffset: number = 0) => {
      setState((prev) => ({ ...prev, isLoading: true, error: null }));
      try {
        const response = await fetch(
          `/api/messages?thread_id=${threadId}&limit=${limit}&offset=${fetchOffset}`,
          {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
          }
        );

        if (!response.ok) {
          throw new Error(`Failed to fetch messages: ${response.statusText}`);
        }

        const data: MessageListResponse = await response.json();
        setState((prev) => ({
          ...prev,
          messages: fetchOffset === 0 ? data.messages : [...prev.messages, ...data.messages],
          isLoading: false,
          hasMore: fetchOffset + limit < data.total,
          total: data.total,
        }));
      } catch (err) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: err instanceof Error ? err.message : 'Unknown error',
        }));
      }
    },
    [threadId, limit]
  );

  /**
   * Send a new message with translation
   * 
   * Workflow per contract-note-007:
   *   1. Frontend calls POST /api/translate (contract-note-006)
   *   2. On success, frontend calls POST /api/messages with translated_text
   *   3. On failure, frontend calls POST /api/messages with translated_text=null
   *   4. Backend sets translation_status accordingly
   * 
   * This hook doesn't handle the translate call; that's in the component.
   * This hook handles the save + optimistic update.
   */
  const sendMessage = useCallback(
    async (payload: MessageCreateRequest): Promise<Message> => {
      try {
        const response = await fetch('/api/messages', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          throw new Error(`Failed to send message: ${response.statusText}`);
        }

        const newMessage: MessageCreateResponse = await response.json();

        // Optimistic update: add new message to list
        setState((prev) => ({
          ...prev,
          messages: [newMessage, ...prev.messages],
          total: prev.total + 1,
        }));

        return newMessage;
      } catch (err) {
        throw err instanceof Error ? err : new Error('Unknown error sending message');
      }
    },
    []
  );

  /**
   * Retry translation for a message that failed
   * 
   * Contract: PATCH /api/messages/{message_id}
   * (contract-note-004 specifies the retry flow; PATCH is the update mechanism)
   * 
   * Frontend:
   *   1. User clicks 'Retry' on a failed message
   *   2. Frontend calls POST /api/translate again
   *   3. On success, frontend calls PATCH /api/messages/{message_id} with new translated_text
   *   4. Backend updates translation_status to 'complete'
   */
  const retryTranslation = useCallback(
    async (
      messageId: string,
      translatedText: string
    ): Promise<Message> => {
      try {
        const response = await fetch(`/api/messages/${messageId}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            translated_text: translatedText,
            translation_status: 'complete',
          }),
        });

        if (!response.ok) {
          throw new Error(`Failed to update message: ${response.statusText}`);
        }

        const updatedMessage: Message = await response.json();

        // Optimistic update: replace message in list
        setState((prev) => ({
          ...prev,
          messages: prev.messages.map((m) =>
            m.message_id === messageId ? updatedMessage : m
          ),
        }));

        return updatedMessage;
      } catch (err) {
        throw err instanceof Error ? err : new Error('Unknown error retrying translation');
      }
    },
    []
  );

  /**
   * Poll for pending translations
   * 
   * Messages with translation_status='pending' are polled periodically.
   * When they transition to 'complete' or 'failed', polling stops for that message.
   */
  const startPolling = useCallback(() => {
    if (pollTimerRef.current) return;

    pollTimerRef.current = setInterval(async () => {
      // Check if any messages are still pending
      const hasPending = state.messages.some((m) => m.translation_status === 'pending');
      if (!hasPending) {
        if (pollTimerRef.current) {
          clearInterval(pollTimerRef.current);
          pollTimerRef.current = null;
        }
        return;
      }

      // Re-fetch messages to get latest translation_status
      // This is a simple approach; in production, might poll specific messages only
      await fetchMessages(offset);
    }, pollIntervalMs);
  }, [state.messages, offset, pollIntervalMs, fetchMessages]);

  const stopPolling = useCallback(() => {
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  /**
   * Effect: initial fetch and polling setup
   */
  useEffect(() => {
    fetchMessages(0);
    setOffset(0);
  }, [threadId, fetchMessages]);

  useEffect(() => {
    startPolling();
    return stopPolling;
  }, [startPolling, stopPolling]);

  /**
   * Load more messages (pagination)
   */
  const loadMore = useCallback(() => {
    if (!state.hasMore || state.isLoading) return;
    const nextOffset = offset + limit;
    setOffset(nextOffset);
    fetchMessages(nextOffset);
  }, [offset, limit, state.hasMore, state.isLoading, fetchMessages]);

  return {
    ...state,
    sendMessage,
    retryTranslation,
    loadMore,
    offset,
  };
};
