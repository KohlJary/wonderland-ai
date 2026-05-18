/**
 * Editor — creates and edits notes with title, body (markdown), and tags.
 *
 * Contract: per ticket-007, ticket-009, and contract-note-01KRXRTT
 * - Title input: text, max 255 chars, validates non-empty on save
 * - Body textarea: markdown, max 16384 chars, optional
 * - Tag input: user can add/remove tags; tags are included in save payload
 * - Save button: POST /api/notes with {title, body, tag_names: string[]}
 * - localStorage: keystroke buffer for title and body, restore on mount, clear after successful save
 * - on error: show error message, preserve state (user can retry)
 * - on success: optionally display saved note, clear editor
 * - Boot reconciliation (ticket-070): on app reload with both localStorage buffer and server state,
 *   compare timestamps and show merge UI if buffer is newer
 *
 * Invariants:
 * - every keystroke in title or body writes to localStorage
 * - on mount, restore from localStorage if present
 * - Save validates title non-empty (1-255 chars)
 * - Save validates body <= 16384 chars
 * - after successful save, localStorage is cleared and tags are reset
 * - error messages displayed to user, state preserved for retry
 * - editor works standalone (does not require preview pane)
 * - on boot with conflict (buffer newer than server), show merge UI and let user choose
 */

import { useEffect, useState } from 'react';
import { createNote, readNote, updateNote, NoteCreateRequest, NoteUpdateRequest, Note } from './api';
import { TagInput } from './TagInput';
import { useLocalStorageDebounce } from './useLocalStorageDebounce';

const LOCALSTORAGE_KEY = 'editor_draft';
const LOCALSTORAGE_TIMESTAMP_KEY = 'editor_draft_timestamp';

interface EditorState {
  title: string;
  body: string;
  tags: string[];
  // revision_id is null for new notes and for buffers whose revision_id is unknown or stale
  // (e.g., restored from localStorage). On successful save, revision_id is set to the server
  // response. On conflict (409), revision_id is set to null because the buffer is in an
  // uncommitted edit state and any cached revision_id may be stale relative to the server.
  // INVARIANT: trust revision_id from server responses (readNote, POST/PUT success) and ignore
  // stale revision_id from localStorage buffers — they may not reflect the note's current state
  // on the server, especially if the note was edited elsewhere (another device/tab/session).
  revision_id: string | null;
}

interface ConflictState {
  serverVersion: Note;
  bufferVersion: EditorState & { lastModified: number };
}

interface EditorProps {
  noteId?: number | null;
  onBodyChange?: (body: string) => void;
  onSave?: () => void;
}

export function Editor({ noteId, onBodyChange, onSave }: EditorProps) {
  const [state, setState] = useState<EditorState>({ title: '', body: '', tags: [], revision_id: null });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [lastSavedId, setLastSavedId] = useState<number | null>(null);
  const [loadingNote, setLoadingNote] = useState(noteId !== null && noteId !== undefined);
  const [bootConflict, setBootConflict] = useState<ConflictState | null>(null);  // boot-time merge detection (buffer vs server on load)
  const [saveConflict, setSaveConflict] = useState<ConflictState | null>(null);  // save-time collision (409 response on save attempt)
  
  // Debounced localStorage write (2 seconds per ticket-068)
  const debouncedSaveToStorage = useLocalStorageDebounce<EditorState>(LOCALSTORAGE_KEY, 2000);

  // Update timestamp in localStorage whenever we save the buffer
  const saveToStorageWithTimestamp = (newState: EditorState) => {
    debouncedSaveToStorage(newState);
    // Write timestamp immediately (not debounced) so we always have a timestamp
    localStorage.setItem(LOCALSTORAGE_TIMESTAMP_KEY, String(Date.now()));
  };

  // Load existing note or restore from localStorage on mount
  useEffect(() => {
    const loadNote = async () => {
      if (noteId !== null && noteId !== undefined) {
        try {
          setLoadingNote(true);
          const serverNote = await readNote(noteId);
          
          // Check for localStorage buffer (boot reconciliation per ticket-070)
          const savedBuffer = localStorage.getItem(LOCALSTORAGE_KEY);
          const savedTimestamp = localStorage.getItem(LOCALSTORAGE_TIMESTAMP_KEY);
          
          if (savedBuffer && savedTimestamp) {
            // Both server and buffer exist: compare timestamps (boot reconciliation)
            try {
              const bufferData = JSON.parse(savedBuffer);
              const bufferTime = parseInt(savedTimestamp, 10);
              
              // Parse server's updated_at to milliseconds
              const serverTime = new Date(serverNote.updated_at).getTime();
              
              if (bufferTime > serverTime) {
                // Buffer is newer: show merge UI (per test scenario 253)
                setBootConflict({
                  serverVersion: serverNote,
                  bufferVersion: {
                    ...bufferData,
                    lastModified: bufferTime,
                  },
                });
                setLoadingNote(false);
                return;
              } else if (bufferTime === serverTime) {
                // Same timestamp: buffer matches server, discard buffer (per test scenario 255)
                localStorage.removeItem(LOCALSTORAGE_KEY);
                localStorage.removeItem(LOCALSTORAGE_TIMESTAMP_KEY);
              }
              // else: serverTime > bufferTime, use server (per test scenario 253)
            } catch (parseErr) {
              console.error('Failed to parse buffer timestamp:', parseErr);
              localStorage.removeItem(LOCALSTORAGE_KEY);
              localStorage.removeItem(LOCALSTORAGE_TIMESTAMP_KEY);
            }
          }
          
          // Use server version (no conflict or server is newer)
          setState({
            title: serverNote.title,
            body: serverNote.body || '',
            tags: serverNote.tag_names || [],
            revision_id: serverNote.revision_id,
          });
          if (onBodyChange) {
            onBodyChange(serverNote.body || '');
          }
        } catch (err) {
          setError(`Failed to load note: ${String(err)}`);
        } finally {
          setLoadingNote(false);
        }
      } else {
        // No noteId: restore from localStorage for new note
        const saved = localStorage.getItem(LOCALSTORAGE_KEY);
        if (saved) {
          try {
            const parsed = JSON.parse(saved);
            setState({
              title: parsed.title || '',
              body: parsed.body || '',
              tags: parsed.tags || [],
              revision_id: parsed.revision_id || null,
            });
            if (onBodyChange) {
              onBodyChange(parsed.body || '');
            }
          } catch (err) {
            console.error('Failed to restore from localStorage:', err);
            localStorage.removeItem(LOCALSTORAGE_KEY);
            localStorage.removeItem(LOCALSTORAGE_TIMESTAMP_KEY);
          }
        }
        setLoadingNote(false);
      }
    };
    loadNote();
  }, [noteId, onBodyChange]);

  // Update local state on keystroke; debounced write to localStorage with timestamp
  const handleTitleChange = (title: string) => {
    const newState = { ...state, title };
    setState(newState);
    saveToStorageWithTimestamp(newState);
  };

  const handleBodyChange = (body: string) => {
    const newState = { ...state, body };
    setState(newState);
    saveToStorageWithTimestamp(newState);
    if (onBodyChange) {
      onBodyChange(body);
    }
  };

  const handleTagsChange = (tags: string[]) => {
    const newState = { ...state, tags };
    setState(newState);
    saveToStorageWithTimestamp(newState);
  };

  // Handle boot-time merge UI: user chooses to keep either buffer version or server version
  const handleBootMergeChoice = (choice: 'keep_buffer' | 'use_server') => {
    if (!bootConflict) return;

    if (choice === 'keep_buffer') {
      // Keep buffer (newer version), load it into editor
      // Note: buffer version may not have revision_id if it was an unsaved draft
      setState({
        title: bootConflict.bufferVersion.title,
        body: bootConflict.bufferVersion.body,
        tags: bootConflict.bufferVersion.tags,
        revision_id: null,  // Buffer doesn't have a revision_id yet; will be assigned on next save
      });
      if (onBodyChange) {
        onBodyChange(bootConflict.bufferVersion.body);
      }
      // Keep localStorage as-is (already the buffer)
    } else {
      // Use server version, overwrite localStorage
      setState({
        title: bootConflict.serverVersion.title,
        body: bootConflict.serverVersion.body || '',
        tags: bootConflict.serverVersion.tag_names || [],
        revision_id: bootConflict.serverVersion.revision_id,
      });
      if (onBodyChange) {
        onBodyChange(bootConflict.serverVersion.body || '');
      }
      // Update localStorage to match server (with server's timestamp)
      const serverData: EditorState = {
        title: bootConflict.serverVersion.title,
        body: bootConflict.serverVersion.body || '',
        tags: bootConflict.serverVersion.tag_names || [],
        revision_id: bootConflict.serverVersion.revision_id,
      };
      localStorage.setItem(LOCALSTORAGE_KEY, JSON.stringify(serverData));
      localStorage.setItem(
        LOCALSTORAGE_TIMESTAMP_KEY,
        String(new Date(bootConflict.serverVersion.updated_at).getTime())
      );
    }

    // Clear boot-time conflict UI
    setBootConflict(null);
  };

  // Handle save-time collision from 409 response: user chooses to keep edits or load server version
  const handleSaveConflictKeepEdits = () => {
    if (!saveConflict) return;
    // Keep local edits: discard the server version and continue editing
    // revision_id stays null/unset until next successful save
    setState({
      title: saveConflict.bufferVersion.title,
      body: saveConflict.bufferVersion.body,
      tags: saveConflict.bufferVersion.tags,
      revision_id: null,  // Will be re-set on next successful save
    });
    setSaveConflict(null);
  };

  const handleSaveConflictLoadServer = () => {
    if (!saveConflict) return;
    // Load server version: overwrite editor with server state
    setState({
      title: saveConflict.serverVersion.title,
      body: saveConflict.serverVersion.body || '',
      tags: saveConflict.serverVersion.tag_names || [],
      revision_id: saveConflict.serverVersion.revision_id,
    });
    if (onBodyChange) {
      onBodyChange(saveConflict.serverVersion.body || '');
    }
    setSaveConflict(null);
  };

  // Validate and save to backend (create or update)
  const handleSave = async () => {
    setError(null);
    setLoading(true);

    // Validate title
    if (!state.title.trim()) {
      setError('Title is required');
      setLoading(false);
      return;
    }
    if (state.title.length > 255) {
      setError('Title must be 255 characters or less');
      setLoading(false);
      return;
    }

    // Validate body
    if (state.body.length > 16384) {
      setError('Body must be 16384 characters or less');
      setLoading(false);
      return;
    }

    try {
      let saved: Note | { conflict: any };
      if (noteId !== null && noteId !== undefined) {
        // Update existing note: include if-match header for collision detection
        const payload: NoteUpdateRequest = {
          title: state.title,
          body: state.body || '',
          tag_names: state.tags,
        };
        saved = await updateNote(noteId, payload, state.revision_id || undefined);
        
        // Handle 409 Conflict response (collision during save)
        if (saved && 'conflict' in saved) {
          const conflictResponse = saved.conflict;
          // Show collision UI with server's current state
          setSaveConflict({
            serverVersion: conflictResponse.server_state,
            bufferVersion: {
              title: state.title,
              body: state.body,
              tags: state.tags,
              revision_id: state.revision_id,
              lastModified: Date.now(),
            },
          });
          setLoading(false);
          return;
        }
      } else {
        // Create new note
        const payload: NoteCreateRequest = {
          title: state.title,
          body: state.body || '',
          tag_names: state.tags,
        };
        saved = await createNote(payload);
      }

      // Success: update state with server response (including new revision_id)
      if (saved && 'revision_id' in saved) {
        setLastSavedId(saved.id);
        // Update state with new revision_id for next collision detection
        setState({
          title: saved.title,
          body: saved.body || '',
          tags: saved.tag_names || [],
          revision_id: saved.revision_id,
        });
      }
      
      localStorage.removeItem(LOCALSTORAGE_KEY);
      localStorage.removeItem(LOCALSTORAGE_TIMESTAMP_KEY);
      setError(null);
      if (onSave) {
        onSave();
      }
    } catch (err) {
      setError(`Save failed: ${String(err)}`);
    } finally {
      setLoading(false);
    }
  };

  // Boot-time merge UI: show when there's a conflict between buffer and server on app load
  if (bootConflict) {
    const bufferDate = new Date(bootConflict.bufferVersion.lastModified).toLocaleString();
    const serverDate = new Date(bootConflict.serverVersion.updated_at).toLocaleString();

    return (
      <div style={styles.editorContainer}>
        <div style={styles.editorPanel}>
          <h2 style={styles.heading}>Unsaved Changes Detected</h2>
          <p style={styles.conflictMessage}>
            You have unsaved changes from {bufferDate}. The server has a newer version from {serverDate}.
          </p>

          <div style={styles.conflictOptions}>
            <div style={styles.versionBox}>
              <h3 style={styles.versionTitle}>Your Unsaved Changes</h3>
              <div style={styles.versionContent}>
                <p><strong>Title:</strong> {bootConflict.bufferVersion.title}</p>
                <p><strong>Body:</strong> {bootConflict.bufferVersion.body.slice(0, 200)}...</p>
              </div>
              <button
                onClick={() => handleBootMergeChoice('keep_buffer')}
                style={styles.chooseButton}
              >
                Keep My Changes
              </button>
            </div>

            <div style={styles.versionBox}>
              <h3 style={styles.versionTitle}>Server Version</h3>
              <div style={styles.versionContent}>
                <p><strong>Title:</strong> {bootConflict.serverVersion.title}</p>
                <p><strong>Body:</strong> {bootConflict.serverVersion.body?.slice(0, 200)}...</p>
              </div>
              <button
                onClick={() => handleBootMergeChoice('use_server')}
                style={styles.chooseButton}
              >
                Use Server Version
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (loadingNote) {
    return (
      <div style={styles.editorContainer}>
        <div style={styles.editorPanel}>
          <div style={styles.loading}>Loading note…</div>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.editorContainer}>
      <div style={styles.editorPanel}>
        <h2 style={styles.heading}>
          {noteId !== null && noteId !== undefined ? `Edit Note #${noteId}` : 'New Note'}
        </h2>

        {error && <div style={styles.error}>{error}</div>}
        {lastSavedId !== null && (
          <div style={styles.success}>✓ Saved (Note #{lastSavedId})</div>
        )}

        {/* Save-time Collision Detection Modal */}
        {saveConflict && (
          <div style={styles.modalOverlay} onClick={() => setSaveConflict(null)}>
            <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
              <h3 style={styles.modalTitle}>⚠ Collision Detected</h3>
              <p style={styles.modalText}>
                This note was modified in another tab or session. Would you like to keep your changes or load the server version?
              </p>
              
              <div style={styles.conflictDetail}>
                <h4>Server Version (Current):</h4>
                <p><strong>Title:</strong> {saveConflict.serverVersion.title}</p>
                <p><strong>Tags:</strong> {saveConflict.serverVersion.tag_names.join(', ') || '(none)'}</p>
                <p><strong>Updated:</strong> {saveConflict.serverVersion.updated_at}</p>
              </div>
              
              <div style={styles.conflictDetail}>
                <h4>Your Local Changes:</h4>
                <p><strong>Title:</strong> {saveConflict.bufferVersion.title}</p>
                <p><strong>Tags:</strong> {saveConflict.bufferVersion.tags.join(', ') || '(none)'}</p>
              </div>
              
              <div style={styles.modalButtons}>
                <button
                  onClick={handleSaveConflictKeepEdits}
                  style={styles.modalButtonPrimary}
                >
                  Keep My Edits
                </button>
                <button
                  onClick={handleSaveConflictLoadServer}
                  style={styles.modalButtonSecondary}
                >
                  Load Server Version
                </button>
              </div>
            </div>
          </div>
        )}

        <input
          type="text"
          placeholder="Title (required, max 255 chars)"
          value={state.title}
          onChange={(e) => handleTitleChange(e.target.value)}
          maxLength={255}
          disabled={loading || saveConflict !== null}
          style={styles.titleInput}
        />

        <textarea
          placeholder="Body (markdown, optional, max 16384 chars)"
          value={state.body}
          onChange={(e) => handleBodyChange(e.target.value)}
          maxLength={16384}
          disabled={loading || saveConflict !== null}
          style={styles.bodyInput}
        />

        <TagInput tags={state.tags} onTagsChange={handleTagsChange} disabled={loading || saveConflict !== null} />

        <div style={styles.buttonGroup}>
          <button onClick={handleSave} disabled={loading || saveConflict !== null} style={styles.saveButton}>
            {loading ? 'Saving…' : 'Save'}
          </button>
          <span style={styles.charCount}>{state.body.length} / 16384 chars</span>
        </div>
      </div>
    </div>
  );
}

const styles = {
  editorContainer: {
    display: 'flex',
    gap: '1rem',
    height: '100vh',
    backgroundColor: '#f9f9f9',
  } as const,
  editorPanel: {
    flex: 1,
    padding: '2rem',
    overflow: 'auto',
    backgroundColor: '#fff',
  } as const,
  heading: {
    margin: '0 0 1rem 0',
    fontSize: '1.5rem',
    color: '#333',
  } as const,
  error: {
    padding: '0.75rem 1rem',
    marginBottom: '1rem',
    backgroundColor: '#fee',
    color: '#c33',
    borderRadius: '4px',
    fontSize: '0.9rem',
  } as const,
  success: {
    padding: '0.75rem 1rem',
    marginBottom: '1rem',
    backgroundColor: '#efe',
    color: '#3a3',
    borderRadius: '4px',
    fontSize: '0.9rem',
  } as const,
  titleInput: {
    display: 'block',
    width: '100%',
    padding: '0.75rem',
    marginBottom: '1rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '1rem',
    fontFamily: 'system-ui, sans-serif',
    boxSizing: 'border-box',
  } as const,
  bodyInput: {
    display: 'block',
    width: '100%',
    height: '400px',
    padding: '0.75rem',
    marginBottom: '1rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '0.95rem',
    fontFamily: 'monospace',
    boxSizing: 'border-box',
    resize: 'vertical',
  } as const,
  buttonGroup: {
    display: 'flex',
    gap: '1rem',
    alignItems: 'center',
  } as const,
  saveButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#0066cc',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    fontSize: '1rem',
    cursor: 'pointer',
    fontWeight: 'bold',
  } as const,
  charCount: {
    fontSize: '0.85rem',
    color: '#666',
  } as const,
  loading: {
    padding: '2rem',
    textAlign: 'center',
    color: '#666',
    fontSize: '1rem',
  } as const,
  conflictMessage: {
    padding: '1rem',
    marginBottom: '2rem',
    backgroundColor: '#fff3cd',
    border: '1px solid #ffc107',
    borderRadius: '4px',
    color: '#856404',
  } as const,
  conflictOptions: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '2rem',
    marginBottom: '2rem',
  } as const,
  versionBox: {
    border: '1px solid #ddd',
    borderRadius: '4px',
    padding: '1rem',
    backgroundColor: '#fafafa',
  } as const,
  versionTitle: {
    margin: '0 0 1rem 0',
    fontSize: '1.1rem',
    color: '#333',
  } as const,
  versionContent: {
    marginBottom: '1rem',
    fontSize: '0.9rem',
    color: '#666',
    maxHeight: '200px',
    overflow: 'auto',
  } as const,
  chooseButton: {
    width: '100%',
    padding: '0.75rem',
    backgroundColor: '#0066cc',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    fontSize: '0.95rem',
    cursor: 'pointer',
    fontWeight: 'bold',
  } as const,
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  } as const,
  modal: {
    backgroundColor: '#fff',
    borderRadius: '8px',
    padding: '2rem',
    maxWidth: '500px',
    width: '90%',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
    maxHeight: '90vh',
    overflow: 'auto',
  } as const,
  modalTitle: {
    margin: '0 0 1rem 0',
    fontSize: '1.3rem',
    color: '#333',
  } as const,
  modalText: {
    margin: '0 0 1.5rem 0',
    fontSize: '0.95rem',
    color: '#666',
    lineHeight: '1.5',
  } as const,
  conflictDetail: {
    marginBottom: '1.5rem',
    padding: '1rem',
    backgroundColor: '#f9f9f9',
    borderRadius: '4px',
    border: '1px solid #eee',
  } as const,
  modalButtons: {
    display: 'flex',
    gap: '1rem',
    justifyContent: 'flex-end',
  } as const,
  modalButtonPrimary: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#0066cc',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    fontSize: '0.95rem',
    cursor: 'pointer',
    fontWeight: 'bold',
  } as const,
  modalButtonSecondary: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#f0f0f0',
    color: '#333',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '0.95rem',
    cursor: 'pointer',
    fontWeight: 'bold',
  } as const,
};

export default Editor;
