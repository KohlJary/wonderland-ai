/**
 * App — Features 001 (create/save notes) and 016 (search notes).
 *
 * Manages routing and navigation between Editor, Notes list, and Search views.
 * URL-based routing with query params for search persistence across reloads.
 * App boot sequence: fetches persisted notes from backend, merges with localStorage per Queen ruling-012.
 * 
 * Routes:
 * - / or no pathname → editor view
 * - /notes → notes list view
 * - /search[?q=...&tags=...&page=...] → search view with optional query params
 *
 * Contracts:
 * - ticket-007: Editor pane with title input, markdown body editor, keystroke buffer
 * - ticket-013: Search UI component with text input, tag filter, pagination
 * - ticket-037: Add search route and wire navigation to search view
 * - contract-note-01KRXRTT: Note model and CRUD endpoint contract
 * - search endpoint shape: GET /api/search?q=...&tags=...&page=...&page_size=...
 * - ticket-066: Frontend load-on-boot and localStorage merge reconciliation
 * - ruling-012: Merge strategy for offline localStorage vs. backend on app boot (OPTIMISTIC)
 * 
 * URL contract:
 * - /search?q=foo — search for "foo"
 * - /search?tags=tag1,tag2 — filter by tags (comma-separated)
 * - /search?page=2 — paginated results (1-indexed)
 * - Query params sync to URL on change; URL is the source of truth for search state
 * - Page reload restores search input, selected tags, and page number from URL params
 */

import { useState, useEffect } from 'react';
import EditorLayout from './EditorLayout';
import Search from './Search';
import NoteList from './NoteList';
import { useBootNotes } from './useBootNotes';

export function App() {
  const [view, setView] = useState<'editor' | 'search' | 'list'>('editor');
  const [selectedNoteId, setSelectedNoteId] = useState<number | null>(null);

  // Load persisted notes on app boot (ticket-066)
  const { notes, syncStatus, syncError } = useBootNotes();

  // Initialize view based on URL pathname on mount
  useEffect(() => {
    const pathname = window.location.pathname;
    if (pathname === '/search') {
      setView('search');
    } else if (pathname === '/notes') {
      setView('list');
    } else {
      setView('editor');
    }
  }, []);

  // Update URL pathname when view changes (except for search, which manages its own URL with query params)
  const navigateTo = (newView: 'editor' | 'list' | 'search') => {
    setView(newView);
    if (newView === 'editor') {
      window.history.pushState(null, '', '/');
    } else if (newView === 'list') {
      window.history.pushState(null, '', '/notes');
    } else if (newView === 'search') {
      // Keep existing search query params if navigating to search from elsewhere
      window.history.pushState(null, '', '/search');
    }
  };

  // Handle navigation to editor from note list
  const handleEditNote = (noteId: number) => {
    setSelectedNoteId(noteId);
    navigateTo('editor');
  };

  // Handle save in editor: clear selection and go back to list
  const handleEditorSave = () => {
    setSelectedNoteId(null);
    navigateTo('list');
  };

  // Handle clear search: return to editor
  const handleClearSearch = () => {
    navigateTo('editor');
  };

  return (
    <div style={styles.appContainer}>
      <nav style={styles.navbar}>
        <div style={styles.navButtonsContainer}>
          <button
            onClick={() => navigateTo('editor')}
            style={view === 'editor' ? styles.navButtonActive : styles.navButton}
          >
            ✏️ Editor
          </button>
          <button
            onClick={() => navigateTo('list')}
            style={view === 'list' ? styles.navButtonActive : styles.navButton}
          >
            📋 Notes
          </button>
          <button
            onClick={() => navigateTo('search')}
            style={view === 'search' ? styles.navButtonActive : styles.navButton}
          >
            🔍 Search
          </button>
        </div>
        
        {/* Sync status indicator (ticket-066) */}
        <div style={styles.syncIndicator}>
          {syncStatus === 'syncing' && (
            <span style={styles.syncStatusText}>↻ syncing…</span>
          )}
          {syncStatus === 'synced' && (
            <span style={{ ...styles.syncStatusText, color: '#3a3' }}>✓ synced</span>
          )}
          {syncStatus === 'error' && (
            <span style={{ ...styles.syncStatusText, color: '#c33' }} title={syncError || ''}>
              ✗ error
            </span>
          )}
        </div>
      </nav>

      <div style={styles.viewContainer}>
        {view === 'editor' && <EditorLayout noteId={selectedNoteId} onSave={handleEditorSave} />}
        {view === 'list' && (
          <NoteList notes={notes} onEdit={handleEditNote} syncStatus={syncStatus} />
        )}
        {view === 'search' && <Search onClear={handleClearSearch} onViewNote={handleEditNote} />}
      </div>
    </div>
  );
}

const styles = {
  appContainer: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
  } as const,
  navbar: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '0.5rem',
    padding: '0.5rem 1rem',
    backgroundColor: '#333',
    borderBottom: '1px solid #222',
  } as const,
  navButtonsContainer: {
    display: 'flex',
    gap: '0.5rem',
  } as const,
  navButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#555',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    fontSize: '0.95rem',
    cursor: 'pointer',
    fontWeight: '500',
  } as const,
  navButtonActive: {
    padding: '0.5rem 1rem',
    backgroundColor: '#0066cc',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    fontSize: '0.95rem',
    cursor: 'pointer',
    fontWeight: 'bold',
  } as const,
  syncIndicator: {
    display: 'flex',
    alignItems: 'center',
    fontSize: '0.85rem',
  } as const,
  syncStatusText: {
    color: '#999',
    fontWeight: '500',
  } as const,
  viewContainer: {
    flex: 1,
    display: 'flex',
    minHeight: 0,
    overflow: 'hidden',
  } as const,
};
