/**
 * NoteEditor — form for creating or editing a note.
 *
 * Props:
 * - note (optional): if provided, populates the form for editing. If not
 *   provided, form is blank for creation.
 * - onSave (required): callback when a note is successfully saved. Receives
 *   the saved Note object.
 *
 * UI States:
 * - idle: form ready for input
 * - saving: POST/PUT in flight, button disabled
 * - success: brief confirmation message shown
 * - error: error message shown (user can retry)
 *
 * Client State:
 * - title, body, tags: form inputs, persisted in component state only
 *   (not on backend until Save clicked)
 * - saved message: cleared after 2 seconds
 * - error: persists until user dismisses or tries again
 * - preview pane: rendered in real-time as body changes
 */

import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { createNote, updateNote, deleteNote, type Note } from './api';

interface NoteEditorProps {
  note?: Note; // optional, for editing mode
  onSave?: (note: Note) => void; // callback when save succeeds
  onCancel?: () => void; // callback to cancel editing and return to list
  onDelete?: () => void; // callback when delete succeeds
}

export function NoteEditor({ note, onSave, onCancel, onDelete }: NoteEditorProps) {
  // Form state
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [tags, setTags] = useState(''); // comma-separated string, will be split on save

  // UI state
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // If editing an existing note, populate the form
  useEffect(() => {
    if (note) {
      setTitle(note.title);
      setBody(note.body);
      setTags(note.tags.join(', ')); // convert array to comma-separated for display
    } else {
      // Clear form if switching to creation mode
      setTitle('');
      setBody('');
      setTags('');
    }
    setError(null);
    setSaved(false);
  }, [note]);

  // Clear success message after 2 seconds
  useEffect(() => {
    if (saved) {
      const timer = setTimeout(() => setSaved(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [saved]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation: title is required
    if (!title.trim()) {
      setError('Title is required');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      // Parse tags from comma-separated string
      const tagArray = tags
        .split(',')
        .map((t) => t.trim())
        .filter((t) => t.length > 0);

      let savedNote: Note;
      if (note?.id) {
        // Update existing note
        savedNote = await updateNote(note.id, title, body, tagArray);
      } else {
        // Create new note
        savedNote = await createNote(title, body, tagArray);
      }

      // Success: clear form, show confirmation, call callback
      setTitle('');
      setBody('');
      setTags('');
      setSaved(true);
      onSave?.(savedNote);
    } catch (err) {
      // Error: show message to user
      setError(String(err));
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!note?.id) {
      return; // Should not happen — delete only available in edit mode
    }

    setDeleting(true);
    setError(null);

    try {
      await deleteNote(note.id);
      // Success: close dialog, call callback to return to list
      setShowDeleteConfirm(false);
      onDelete?.();
    } catch (err) {
      // Error: show message to user
      setError(`Failed to delete note: ${String(err)}`);
    } finally {
      setDeleting(false);
    }
  };

  const isEditMode = !!note?.id;
  const buttonLabel = isEditMode ? 'Update' : 'Save';

  return (
    <form onSubmit={handleSave} style={styles.form}>
      <h2>{isEditMode ? 'Edit Note' : 'New Note'}</h2>

      {/* Title input — required */}
      <div style={styles.fieldGroup}>
        <label htmlFor="title" style={styles.label}>
          Title <span style={styles.required}>*</span>
        </label>
        <input
          id="title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Note title"
          disabled={saving || deleting}
          style={styles.input}
        />
      </div>

      {/* Body: two-pane layout (textarea on left, preview on right) */}
      <div style={styles.fieldGroup}>
        <label style={styles.label}>Body (Markdown)</label>
        <div style={styles.twoPaneContainer}>
          {/* Left pane: textarea */}
          <textarea
            id="body"
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Markdown body"
            disabled={saving || deleting}
            style={styles.textarea}
            rows={10}
          />
          {/* Right pane: preview */}
          <div style={styles.previewPane}>
            <ReactMarkdown>{body}</ReactMarkdown>
          </div>
        </div>
      </div>

      {/* Tags input — comma-separated */}
      <div style={styles.fieldGroup}>
        <label htmlFor="tags" style={styles.label}>
          Tags
        </label>
        <input
          id="tags"
          type="text"
          value={tags}
          onChange={(e) => setTags(e.target.value)}
          placeholder="tag1, tag2, tag3"
          disabled={saving || deleting}
          style={styles.input}
        />
        <p style={styles.hint}>Separate multiple tags with commas</p>
      </div>

      {/* Error message */}
      {error && (
        <div style={styles.errorBox}>
          <p style={styles.errorText}>{error}</p>
        </div>
      )}

      {/* Success message */}
      {saved && (
        <div style={styles.successBox}>
          <p style={styles.successText}>✓ Note saved</p>
        </div>
      )}

      {/* Save, Cancel, and Delete buttons */}
      <div style={{ display: 'flex', gap: '1em' }}>
        <button
          type="submit"
          disabled={saving || deleting}
          style={{
            ...styles.button,
            opacity: saving || deleting ? 0.6 : 1,
            cursor: saving || deleting ? 'not-allowed' : 'pointer',
            flex: 1,
          }}
        >
          {saving ? 'Saving…' : buttonLabel}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={saving || deleting}
          style={{
            ...styles.button,
            backgroundColor: '#ccc',
            color: '#333',
            opacity: saving || deleting ? 0.6 : 1,
            cursor: saving || deleting ? 'not-allowed' : 'pointer',
            flex: 1,
          }}
        >
          Cancel
        </button>
        {isEditMode && (
          <button
            type="button"
            onClick={() => setShowDeleteConfirm(true)}
            disabled={saving || deleting}
            style={{
              ...styles.button,
              backgroundColor: '#dc3545',
              opacity: saving || deleting ? 0.6 : 1,
              cursor: saving || deleting ? 'not-allowed' : 'pointer',
              flex: 1,
            }}
          >
            Delete
          </button>
        )}
      </div>

      {/* Delete confirmation modal */}
      {showDeleteConfirm && (
        <div style={styles.modalOverlay}>
          <div style={styles.modal}>
            <h3 style={styles.modalTitle}>Delete Note?</h3>
            <p style={styles.modalBody}>
              Are you sure you want to delete this note? This action cannot be undone.
            </p>
            <div style={{ display: 'flex', gap: '1em', justifyContent: 'flex-end' }}>
              <button
                type="button"
                onClick={() => setShowDeleteConfirm(false)}
                disabled={deleting}
                style={{
                  ...styles.button,
                  backgroundColor: '#ccc',
                  color: '#333',
                  flex: 0,
                  minWidth: '100px',
                  cursor: deleting ? 'not-allowed' : 'pointer',
                  opacity: deleting ? 0.6 : 1,
                }}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteConfirm}
                disabled={deleting}
                style={{
                  ...styles.button,
                  backgroundColor: '#dc3545',
                  flex: 0,
                  minWidth: '100px',
                  cursor: deleting ? 'not-allowed' : 'pointer',
                  opacity: deleting ? 0.6 : 1,
                }}
              >
                {deleting ? 'Deleting…' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </form>
  );
}

const styles = {
  form: {
    display: 'flex' as const,
    flexDirection: 'column' as const,
    gap: '1.5rem',
    padding: '2rem',
    maxWidth: '800px',
    fontFamily: 'system-ui',
  },
  fieldGroup: {
    display: 'flex' as const,
    flexDirection: 'column' as const,
    gap: '0.5rem',
  },
  label: {
    fontWeight: 600,
    fontSize: '0.95rem',
    color: '#333',
  },
  required: {
    color: 'crimson',
  },
  input: {
    padding: '0.75rem',
    fontSize: '1rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontFamily: 'system-ui',
  },
  textarea: {
    padding: '0.75rem',
    fontSize: '1rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontFamily: 'monospace',
    lineHeight: 1.5,
    flex: 1,
    resize: 'none' as const,
  },
  hint: {
    fontSize: '0.85rem',
    color: '#999',
    margin: 0,
  },
  errorBox: {
    padding: '1rem',
    backgroundColor: '#ffe6e6',
    border: '1px solid #cc0000',
    borderRadius: '4px',
  },
  errorText: {
    color: '#cc0000',
    margin: 0,
  },
  successBox: {
    padding: '1rem',
    backgroundColor: '#e6ffe6',
    border: '1px solid #00cc00',
    borderRadius: '4px',
  },
  successText: {
    color: '#00cc00',
    margin: 0,
  },
  button: {
    padding: '0.75rem 1.5rem',
    fontSize: '1rem',
    fontWeight: 600,
    backgroundColor: '#0066cc',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    transition: 'background-color 0.2s',
  },
  modalOverlay: {
    position: 'fixed' as const,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  modal: {
    backgroundColor: 'white',
    borderRadius: '8px',
    padding: '2rem',
    maxWidth: '400px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
  },
  modalTitle: {
    margin: '0 0 1rem 0',
    fontSize: '1.25rem',
    fontWeight: 600,
    color: '#333',
  },
  modalBody: {
    margin: '0 0 1.5rem 0',
    color: '#666',
    lineHeight: 1.6,
  },
  twoPaneContainer: {
    display: 'flex',
    gap: '1rem',
    height: '400px',
  },
  previewPane: {
    flex: 1,
    border: '1px solid #ddd',
    borderRadius: '4px',
    padding: '0.75rem',
    backgroundColor: '#f9f9f9',
    overflow: 'auto',
    fontFamily: 'system-ui',
    fontSize: '1rem',
    lineHeight: 1.6,
  },
};
