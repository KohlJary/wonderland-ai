import { useEffect, useState } from 'react';
import { listNotes, Note } from './api';

/**
 * useBootNotes — loads persisted notes on app boot for the note list.
 *
 * Contract: ticket-066 (frontend-load-on-boot)
 *
 * On app boot:
 * 1. Fetch GET /notes (all persisted notes from backend, reverse chronological)
 * 2. Return the list for display in the note list sidebar
 * 3. Per-note buffer merging is delegated to the Editor component when a specific note is opened
 *
 * Merge responsibility: Editor component (useBootNotes is global scope; Editor handles per-note scope)
 * Per-note buffer merging is delegated to the Editor component when a specific note is opened because:
 * (1) useBootNotes operates at global scope (entire note list), but merge reconciliation requires
 *     per-note context (which buffer corresponds to which backend note?)
 * (2) Editor has access to both the specific note's server state (from GET /notes) and the
 *     corresponding localStorage buffer (keyed by note ID)
 * (3) this separation of concerns keeps useBootNotes simple (fetch + return) and Editor focused
 *     (load, merge, edit), making each component easier to reason about and test.
 * - When Editor loads a specific note by ID, it checks localStorage for that note's keystroke buffer
 * - If a buffer exists AND is newer than the server version (per timestamp), Editor shows a merge UI
 * - User chooses: keep unsaved changes or load server version
 *
 * Sync status: 'idle' | 'syncing' | 'synced' | 'error'
 *
 * @returns {notes: Note[], syncStatus: string, syncError: string | null}
 */

export interface BootNotesState {
  notes: Note[];
  syncStatus: 'idle' | 'syncing' | 'synced' | 'error';
  syncError: string | null;
}

export function useBootNotes(): BootNotesState {
  const [state, setState] = useState<BootNotesState>({
    notes: [],
    syncStatus: 'idle',
    syncError: null,
  });

  useEffect(() => {
    let isMounted = true;

    const bootSequence = async () => {
      setState((prev) => ({ ...prev, syncStatus: 'syncing', syncError: null }));

      try {
        // Fetch all persisted notes from backend
        const backendNotes = await listNotes();

        if (isMounted) {
          setState({
            notes: backendNotes,
            syncStatus: 'synced',
            syncError: null,
          });
        }
      } catch (err) {
        // Fetch failed; report error
        const errorMsg = err instanceof Error ? err.message : String(err);
        if (isMounted) {
          setState({
            notes: [],
            syncStatus: 'error',
            syncError: errorMsg,
          });
        }
      }
    };

    // Start the boot sequence immediately on mount
    bootSequence();

    // Cleanup: set isMounted flag on unmount
    return () => {
      isMounted = false;
    };
  }, []);

  return state;
}
