/**
 * App — main application shell for the personal markdown notebook.
 *
 * Two-pane layout:
 * - Left pane: NotesList (note list + create form at top)
 * - Right pane: NoteEditor (blank until a note is selected, then shows editor)
 *
 * State management:
 * - selectedNote: tracks which note is being edited (undefined = empty right pane)
 * - showCreateForm: toggles the create form in the left pane
 * - notesRefreshKey: incremented after save/delete to refetch the list
 *
 * State flow:
 * - Clicking "Create New Note" in left pane opens create form
 * - Submitting create form: note created, form closed, right pane shows new note
 * - Clicking a note in left pane: loads it into right pane editor
 * - Clicking "Save" in right pane: note updated, list refreshes
 * - Clicking "Delete" in right pane: note deleted, right pane clears, list refreshes
 * - Clicking "Cancel": right pane clears (selectedNote = undefined)
 *
 * Contract with Tweedledum (backend):
 * - GET /api/notes returns Note[] ordered by updated_at desc
 * - POST /api/notes creates and returns Note
 * - PUT /api/notes/{id} updates and returns Note
 * - DELETE /api/notes/{id} returns 204 No Content
 */

import { useState } from 'react';
import { NotesList } from './NotesList';
import { NoteEditor } from './NoteEditor';
import { type Note } from './api';

export function App() {
  const [selectedNote, setSelectedNote] = useState<Note | undefined>(undefined);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [notesRefreshKey, setNotesRefreshKey] = useState(0);

  const handleEditNote = (note: Note) => {
    setSelectedNote(note);
    setShowCreateForm(false);
  };

  const handleSaveNote = (note: Note) => {
    // After save, close the form and show the saved note in the right pane
    setShowCreateForm(false);
    setSelectedNote(note);
    // Trigger list refetch
    setNotesRefreshKey((prev) => prev + 1);
  };

  const handleCreateFormToggle = (show: boolean) => {
    setShowCreateForm(show);
  };

  const handleDeleteNote = () => {
    // After deletion, clear right pane and refetch list
    setSelectedNote(undefined);
    setNotesRefreshKey((prev) => prev + 1);
  };

  const handleCancel = () => {
    // Cancel editor or create form
    setShowCreateForm(false);
    setSelectedNote(undefined);
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>Markdown Notebook</h1>
      </header>

      <div style={styles.mainLayout}>
        {/* Left pane: Note list and create form */}
        <div style={styles.leftPane}>
          <NotesList
            key={notesRefreshKey}
            showCreateForm={showCreateForm}
            onCreateFormToggle={handleCreateFormToggle}
            onSaveNote={handleSaveNote}
            onEditNote={handleEditNote}
            onDeleteNote={handleDeleteNote}
          />
        </div>

        {/* Right pane: Note editor (empty if no note selected and not creating) */}
        <div style={styles.rightPane}>
          {selectedNote || showCreateForm ? (
            <NoteEditor
              note={selectedNote}
              onSave={handleSaveNote}
              onDelete={handleDeleteNote}
              onCancel={handleCancel}
            />
          ) : (
            <div style={styles.emptyPane}>
              <p style={styles.emptyText}>
                Select a note to view or edit it
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    fontFamily: 'system-ui, -apple-system, sans-serif',
    backgroundColor: '#fafafa',
  },
  header: {
    padding: '1rem',
    borderBottom: '1px solid #ddd',
    backgroundColor: 'white',
  },
  title: {
    margin: 0,
    fontSize: '1.5rem',
    fontWeight: 'bold',
  },
  mainLayout: {
    display: 'flex',
    flex: 1,
    overflow: 'hidden',
  },
  leftPane: {
    flex: '0 0 40%',
    borderRight: '1px solid #ddd',
    overflowY: 'auto',
    backgroundColor: 'white',
  },
  rightPane: {
    flex: '1',
    overflowY: 'auto',
    backgroundColor: '#fafafa',
  },
  emptyPane: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    padding: '2rem',
  },
  emptyText: {
    color: '#999',
    fontSize: '1.1rem',
    textAlign: 'center',
  },
};
