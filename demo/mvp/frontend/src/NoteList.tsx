/**
 * NoteList — displays all saved notes with tags rendered as badges.
 *
 * Contract: per contract-note-014 (Note model with tag_names and tag_ids in responses)
 * - GET /api/notes: → Note[] (reverse chronological, includes tag_names and tag_ids)
 * - Renders each note with title, body preview, and tag badges
 * - Tags are displayed as small rounded badges below the preview
 * - Notes without tags show no badge section (clean, no clutter)
 * - Clicking a note (future feature) will open it in the editor
 *
 * UI states:
 * - loading: spinner while fetching notes
 * - error: error message with retry option if fetch fails
 * - empty: "no notes created yet" message if the list is empty
 * - results: list of notes with title, preview, tags, date
 *
 * Invariants:
 * - Notes are displayed in reverse chronological order (newest first)
 * - Tag badges are visually distinct (small, rounded, light background, dark text)
 * - Empty tag arrays result in no badge rendering (not an empty placeholder)
 * - Tag names with emoji, unicode, or special characters are rendered correctly
 */

import { Note } from './api';

interface NoteListProps {
  notes: Note[];
  onEdit?: (noteId: number) => void;
  syncStatus?: 'idle' | 'syncing' | 'synced' | 'error';
  syncError?: string | null;
}

export function NoteList({ notes, onEdit, syncStatus = 'idle', syncError = null }: NoteListProps) {
  // Per ticket-066: loading state is managed by App's useBootNotes hook
  // NoteList receives notes directly, no local fetching
  const loading = syncStatus === 'syncing';
  const error = syncStatus === 'error' ? syncError : null;

  // Handle note click (open in editor)
  const handleNoteClick = (noteId: number) => {
    if (onEdit) {
      onEdit(noteId);
    }
  };

  // Render a single note
  const renderNote = (note: Note) => {
    // Preview is first 150 chars of body
    const preview = note.body ? note.body.substring(0, 150) + (note.body.length > 150 ? '…' : '') : '';
    const createdDate = new Date(note.created_at);
    const dateString = createdDate.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });

    return (
      <div
        key={note.id}
        style={styles.noteItem}
        onClick={() => handleNoteClick(note.id)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            handleNoteClick(note.id);
          }
        }}
      >
        <div style={styles.noteTitle}>{note.title}</div>
        {preview && <div style={styles.notePreview}>{preview}</div>}
        {/* Tag badges: only render if tags exist */}
        {note.tag_names && note.tag_names.length > 0 && (
          <div style={styles.noteTags}>
            {note.tag_ids.map((tagId, index) => (
              // Use stable tag ID as key (tag_ids[i] corresponds to tag_names[i])
              <span key={`tag-${tagId}`} style={styles.noteTag}>
                {note.tag_names[index]}
              </span>
            ))}
          </div>
        )}
        <div style={styles.noteDate}>{dateString}</div>
      </div>
    );
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.heading}>My Notes</h2>
      </div>

      {/* Error state */}
      {error && (
        <div style={styles.error}>
          {error}
          <button
            onClick={() => window.location.reload()}
            style={styles.retryButton}
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading state */}
      {loading && <div style={styles.loading}>Loading notes…</div>}

      {/* Empty state */}
      {!loading && notes.length === 0 && (
        <div style={styles.empty}>
          No notes yet. Start by creating your first note in the editor.
        </div>
      )}

      {/* Notes list */}
      {!loading && notes.length > 0 && (
        <div style={styles.notesList}>
          {notes.map(renderNote)}
        </div>
      )}
    </div>
  );
}

const styles = {
  container: {
    flex: 1,
    padding: '2rem',
    overflow: 'auto',
    backgroundColor: '#fff',
  } as const,
  header: {
    marginBottom: '1.5rem',
  } as const,
  heading: {
    margin: '0',
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
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  } as const,
  retryButton: {
    padding: '0.4rem 0.8rem',
    backgroundColor: '#c33',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    fontSize: '0.85rem',
    cursor: 'pointer',
    fontWeight: 'bold',
  } as const,
  loading: {
    padding: '2rem',
    textAlign: 'center',
    color: '#666',
    fontSize: '1rem',
  } as const,
  empty: {
    padding: '2rem',
    textAlign: 'center',
    color: '#666',
    fontSize: '1rem',
    backgroundColor: '#f9f9f9',
    borderRadius: '4px',
  } as const,
  notesList: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
    gap: '1rem',
  } as const,
  noteItem: {
    padding: '1rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    backgroundColor: '#fafafa',
    cursor: 'pointer',
    transition: 'box-shadow 0.2s, transform 0.2s',
    ':hover': {
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      transform: 'translateY(-2px)',
    },
  } as const,
  noteTitle: {
    fontSize: '1rem',
    fontWeight: 'bold',
    color: '#0066cc',
    marginBottom: '0.5rem',
    wordBreak: 'break-word',
  } as const,
  notePreview: {
    fontSize: '0.9rem',
    color: '#666',
    marginBottom: '0.5rem',
    lineHeight: '1.4',
    display: '-webkit-box',
    WebkitLineClamp: 3,
    WebkitBoxOrient: 'vertical',
    overflow: 'hidden',
  } as const,
  noteTags: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '0.4rem',
    marginBottom: '0.5rem',
    marginTop: '0.5rem',
  } as const,
  noteTag: {
    display: 'inline-block',
    padding: '0.2rem 0.6rem',
    backgroundColor: '#e8f4f8',
    color: '#0066cc',
    borderRadius: '12px',
    fontSize: '0.8rem',
    border: '1px solid #0066cc',
    whiteSpace: 'nowrap',
  } as const,
  noteDate: {
    fontSize: '0.85rem',
    color: '#999',
  } as const,
};

export default NoteList;
