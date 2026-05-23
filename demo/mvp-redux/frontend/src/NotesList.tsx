/**
 * NotesList — displays all notes with integrated create form, search, and tag filter.
 * 
 * Two-pane aware:
 * - Displays note list in left pane
 * - Can show create form inline in left pane (toggled by parent via showCreateForm)
 * - Clicking a note calls onEditNote(note) to load it in right pane
 * 
 * UI States:
 * - loading: initial fetch of all notes on mount
 * - loading-results: fetching search or filter results
 * - error: initial fetch failed
 * - error-results: search or filter fetch failed
 * - empty: no notes exist (before search)
 * - empty-search: search returned no results
 * - empty-filter: tag filter returned no results
 * - results: notes displayed
 * - create-form: create form is shown when showCreateForm=true
 * 
 * Client State:
 * - allNotes: the full list of notes fetched on mount (canonical source)
 * - searchTerm: the current search input value (can be combined with selectedTag)
 * - selectedTag: the currently selected tag filter (can be combined with searchTerm)
 * - displayedNotes: the notes shown to user (search + filter results, filter results, search results, or allNotes)
 * - displayedLoading: whether we're fetching search/filter results
 * - displayedError: error from search/filter request
 * - deleteError: transient error state when a delete operation fails
 * - debounceTimer: for debouncing search requests (300ms)
 * 
 * Contract Assumptions (with Tweedledum):
 * - GET /api/notes returns Note[] ordered by updated_at desc
 * - GET /api/notes?q={query} returns search results (substring match, ranked)
 * - GET /api/notes?tag={tag} returns filtered results (exact tag match, ordered by updated_at desc)
 * - GET /api/notes?q={query}&tag={tag} composes both: backend ranks by relevance (exact tag match > title match > body match) then updated_at desc
 * - POST /api/notes creates and returns Note
 * - DELETE /api/notes/{id} returns 204 No Content
 * - Each Note includes id, title, body, tags[], created_at, updated_at
 * - Tags are delivered as an array of strings
 */

import { useEffect, useState, useRef } from 'react';
import { listNotes, deleteNote, searchNotes, filterNotesByTag, type Note } from './api';
import { NoteEditor } from './NoteEditor';

interface NoteListProps {
  showCreateForm: boolean;
  onCreateFormToggle: (show: boolean) => void;
  onSaveNote: (note: Note) => void;
  onEditNote: (note: Note) => void;
  onDeleteNote: () => void;
}

function extractAllTags(notes: Note[]): Array<{ tag: string; count: number }> {
  const tagCounts = new Map<string, number>();
  for (const note of notes) {
    for (const tag of note.tags) {
      tagCounts.set(tag, (tagCounts.get(tag) || 0) + 1);
    }
  }
  // Sort by count descending, then alphabetically
  return Array.from(tagCounts.entries())
    .map(([tag, count]) => ({ tag, count }))
    .sort((a, b) => {
      if (b.count !== a.count) return b.count - a.count;
      return a.tag.localeCompare(b.tag);
    });
}

export function NotesList({
  showCreateForm,
  onCreateFormToggle,
  onSaveNote,
  onEditNote,
  onDeleteNote,
}: NoteListProps) {
  const [allNotes, setAllNotes] = useState<Note[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [displayedNotes, setDisplayedNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [displayedLoading, setDisplayedLoading] = useState(false);
  const [displayedError, setDisplayedError] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<number | null>(null);
  const debounceTimer = useRef<number | null>(null);
  const abortController = useRef<AbortController | null>(null);

  // Fetch all notes on mount
  useEffect(() => {
    setLoading(true);
    setError(null);
    listNotes()
      .then((notes) => {
        setAllNotes(notes);
        setDisplayedNotes(notes);
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  // Debounced search/filter handler: when searchTerm or selectedTag changes, fetch from server
  useEffect(() => {
    // Clear any pending debounce timer
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    // Cancel any pending fetch from the previous search/filter request
    if (abortController.current) {
      abortController.current.abort();
    }

    // If neither search nor filter is active, show all notes
    if (!searchTerm.trim() && !selectedTag) {
      setDisplayedNotes(allNotes);
      setDisplayedError(null);
      setDisplayedLoading(false);
      return;
    }

    // Set loading state and clear previous error
    setDisplayedLoading(true);
    setDisplayedError(null);

    // Debounce the request (300ms for search, immediate for tag filter)
    const delay = searchTerm.trim() ? 300 : 0;

    debounceTimer.current = window.setTimeout(async () => {
      try {
        // Create a new AbortController for this request
        abortController.current = new AbortController();
        const signal = abortController.current.signal;

        let results: Note[];
        if (searchTerm.trim()) {
          results = await searchNotes(searchTerm, signal);
        } else if (selectedTag) {
          results = await filterNotesByTag(selectedTag, signal);
        } else {
          results = allNotes;
        }

        // Only update state if the request was not aborted
        if (!signal.aborted) {
          setDisplayedNotes(results);
          setDisplayedError(null);
        }
      } catch (e) {
        // Ignore AbortError; it means a new request superseded this one
        if (e instanceof Error && e.name === 'AbortError') {
          return;
        }
        setDisplayedError(String(e));
        setDisplayedNotes([]);
      } finally {
        setDisplayedLoading(false);
      }
    }, delay);

    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
      if (abortController.current) {
        abortController.current.abort();
      }
    };
  }, [searchTerm, selectedTag, allNotes]);



  const handleDeleteClick = async (noteId: number) => {
    setDeleting(noteId);
    setDeleteError(null);
    try {
      await deleteNote(noteId);
      // Update both allNotes and displayedNotes
      const updatedAll = allNotes.filter((n) => n.id !== noteId);
      setAllNotes(updatedAll);
      // Also remove from displayed (handles search/filter case)
      setDisplayedNotes((prev) => prev.filter((n) => n.id !== noteId));
      onDeleteNote();
    } catch (e) {
      setDeleteError(`Failed to delete note: ${String(e)}`);
    } finally {
      setDeleting(null);
    }
  };

  if (loading) {
    return <div style={styles.loadingContainer}>Loading notes…</div>;
  }

  // Extract unique tags from all notes for the tag filter UI
  const availableTags = extractAllTags(allNotes);

  return (
    <div style={styles.listContainer}>
      <div style={styles.listHeader}>
        <h2 style={styles.listTitle}>Notes</h2>
      </div>

      {/* Create form (inline, when toggled on) */}
      {showCreateForm && (
        <div style={styles.createFormContainer}>
          <NoteEditor
            onSave={(newNote) => {
              onSaveNote(newNote);
              onCreateFormToggle(false);
            }}
            onCancel={() => onCreateFormToggle(false)}
          />
        </div>
      )}

      {/* Create New Note button (hidden when form is open) */}
      {!showCreateForm && (
        <button
          onClick={() => onCreateFormToggle(true)}
          style={styles.createButton}
        >
          + Create Note
        </button>
      )}

      {/* Search input */}
      <input
        type="text"
        placeholder="Search notes…"
        value={searchTerm}
        onChange={(e) => {
          const term = e.target.value;
          setSearchTerm(term);
          // Clear tag filter if user types in search
          if (term.trim() && selectedTag) {
            setSelectedTag(null);
          }
        }}
        style={styles.searchInput}
      />

      {/* Tag filter sidebar */}
      {availableTags.length > 0 && (
        <div style={styles.tagFilterContainer}>
          <div style={styles.tagFilterLabel}>Filter by tag:</div>
          {selectedTag && (
            <button
              onClick={() => setSelectedTag(null)}
              style={styles.clearFilterButton}
            >
              Clear filter
            </button>
          )}
          <div style={styles.tagButtonGroup}>
            {availableTags.map(({ tag, count }) => (
              <button
                key={tag}
                onClick={() => {
                  setSelectedTag(tag);
                  setSearchTerm('');
                }}
                style={{
                  ...styles.tagButton,
                  ...(selectedTag === tag ? styles.tagButtonActive : {}),
                }}
              >
                {tag} ({count})
              </button>
            ))}
          </div>
        </div>
      )}

      {error && <p style={styles.errorText}>Error: {error}</p>}
      {deleteError && <p style={styles.errorText}>Delete Error: {deleteError}</p>}
      {displayedLoading && <p style={styles.loadingText}>Loading…</p>}
      {displayedError && <p style={styles.errorText}>Search error: {displayedError}</p>}

      {/* Empty state: no notes at all */}
      {allNotes.length === 0 && !error && (
        <p style={styles.emptyText}>No notes yet. Create one to get started.</p>
      )}

      {/* Empty state: notes exist but search filtered them all out */}
      {allNotes.length > 0 && displayedNotes.length === 0 && (searchTerm.trim() || selectedTag) && (
        <p style={styles.emptyText}>
          {searchTerm.trim() ? `No notes matching "${searchTerm}".` : `No notes with tag "${selectedTag}".`}
        </p>
      )}

      {/* Results */}
      {displayedNotes.length > 0 && (
        <ul style={styles.notesList}>
          {displayedNotes.map((note) => (
            <li key={note.id} style={styles.noteItem}>
              <div
                style={styles.noteClickable}
                onClick={() => onEditNote(note)}
                role="button"
                tabIndex={0}
              >
                <h3 style={styles.noteTitle}>{note.title}</h3>
                {note.body && (
                  <p style={styles.notePreview}>
                    {note.body.substring(0, 80)}
                    {note.body.length > 80 ? '…' : ''}
                  </p>
                )}
                {note.tags.length > 0 && (
                  <div style={styles.tagContainer}>
                    {note.tags.map((tag) => (
                      <span key={tag} style={styles.tag}>
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
                <p style={styles.noteTimestamp}>
                  {new Date(note.updated_at).toLocaleString()}
                </p>
              </div>
              {/* Delete button */}
              <div style={styles.noteActions}>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteClick(note.id);
                  }}
                  disabled={deleting === note.id}
                  style={{
                    ...styles.deleteButton,
                    backgroundColor:
                      deleting === note.id ? '#ccc' : '#dc3545',
                    cursor:
                      deleting === note.id ? 'not-allowed' : 'pointer',
                  }}
                >
                  {deleting === note.id ? 'Deleting…' : 'Delete'}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  loadingContainer: {
    padding: '1rem',
    textAlign: 'center',
    color: '#666',
  },
  listContainer: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
  },
  listHeader: {
    padding: '1rem',
    borderBottom: '1px solid #ddd',
  },
  listTitle: {
    margin: 0,
    fontSize: '1.1rem',
    fontWeight: 'bold',
  },
  createFormContainer: {
    padding: '0.75rem',
    borderBottom: '2px solid #ddd',
    backgroundColor: '#f5f5f5',
    maxHeight: '60%',
    overflowY: 'auto',
  },
  createButton: {
    margin: '0.75rem',
    padding: '0.75rem 1rem',
    fontSize: '0.95rem',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontWeight: 'bold',
    transition: 'background-color 0.2s',
  },
  searchInput: {
    margin: '0 0.75rem 0.75rem 0.75rem',
    padding: '0.5rem',
    fontSize: '0.95rem',
    border: '1px solid #ccc',
    borderRadius: '4px',
    boxSizing: 'border-box',
  },
  errorText: {
    margin: '0 0.75rem',
    color: 'crimson',
    fontSize: '0.9rem',
  },
  loadingText: {
    margin: '0 0.75rem',
    color: '#666',
    fontSize: '0.9rem',
    fontStyle: 'italic',
  },
  emptyText: {
    margin: '1rem 0.75rem',
    color: '#666',
    fontStyle: 'italic',
    fontSize: '0.95rem',
  },
  notesList: {
    listStyle: 'none',
    padding: '0 0.75rem 0.75rem 0.75rem',
    margin: 0,
    overflow: 'auto',
    flex: 1,
  },
  noteItem: {
    display: 'flex',
    alignItems: 'center',
    padding: '0.75rem',
    marginBottom: '0.5rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    backgroundColor: '#fff',
    transition: 'background-color 0.2s',
  },
  noteClickable: {
    flex: 1,
    cursor: 'pointer',
    minWidth: 0,
  },
  noteTitle: {
    margin: '0 0 0.25rem 0',
    fontSize: '0.95rem',
    fontWeight: 'bold',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  notePreview: {
    margin: '0 0 0.25rem 0',
    fontSize: '0.85rem',
    color: '#666',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  tagContainer: {
    marginBottom: '0.25rem',
  },
  tag: {
    display: 'inline-block',
    padding: '0.15rem 0.4rem',
    marginRight: '0.35rem',
    backgroundColor: '#e0e0e0',
    borderRadius: '3px',
    fontSize: '0.75rem',
    fontWeight: '500',
  },
  noteTimestamp: {
    margin: 0,
    fontSize: '0.75rem',
    color: '#999',
  },
  noteActions: {
    flexShrink: 0,
    marginLeft: '0.5rem',
  },
  deleteButton: {
    padding: '0.35rem 0.75rem',
    fontSize: '0.8rem',
    color: 'white',
    border: 'none',
    borderRadius: '3px',
    cursor: 'pointer',
    whiteSpace: 'nowrap',
  },
};
