import { useState, useEffect } from 'react';
import { api, Note } from './api';
import NoteEditor from './components/NoteEditor';
import NoteList from './components/NoteList';
import SearchBar from './components/SearchBar';
import TagFilter from './components/TagFilter';
import './App.css';

function App() {
  const [notes, setNotes] = useState<Note[]>([]);
  const [selectedNote, setSelectedNote] = useState<Note | null>(null);
  const [allTags, setAllTags] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load notes and tags on mount
  useEffect(() => {
    loadData();
  }, []);

  // Load notes when search or tag filter changes
  useEffect(() => {
    loadNotes();
  }, [searchQuery, selectedTag]);

  async function loadData() {
    try {
      setError(null);
      await loadNotes();
      await loadTags();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }

  async function loadNotes() {
    try {
      const loadedNotes = await api.listNotes(searchQuery || undefined, selectedTag || undefined);
      setNotes(loadedNotes);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load notes');
    }
  }

  async function loadTags() {
    try {
      const tags = await api.getAllTags();
      setAllTags(tags);
    } catch (err) {
      console.error('Failed to load tags:', err);
    }
  }

  async function handleCreateNote(title: string, body: string, tags: string[]) {
    try {
      setError(null);
      const newNote = await api.createNote({ title, body, tags });
      setSelectedNote(newNote);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create note');
    }
  }

  async function handleUpdateNote(id: number, title: string, body: string, tags: string[]) {
    try {
      setError(null);
      const updated = await api.updateNote(id, { title, body, tags });
      setSelectedNote(updated);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update note');
    }
  }

  async function handleDeleteNote(id: number) {
    try {
      setError(null);
      await api.deleteNote(id);
      setSelectedNote(null);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete note');
    }
  }

  function handleSelectNote(note: Note) {
    setSelectedNote(note);
  }

  function handleNewNote() {
    setSelectedNote(null);
  }

  function handleSearch(query: string) {
    setSearchQuery(query);
  }

  function handleTagFilter(tag: string | null) {
    setSelectedTag(tag);
  }

  if (loading) {
    return <div className="app loading">Loading...</div>;
  }

  return (
    <div className="app">
      <div className="sidebar">
        <div className="header">
          <h1>📓 Markdown Notebook</h1>
          <button onClick={handleNewNote} className="new-note-btn">
            New Note
          </button>
        </div>

        <SearchBar onSearch={handleSearch} />
        <TagFilter tags={allTags} selectedTag={selectedTag} onSelectTag={handleTagFilter} />

        <NoteList notes={notes} selectedId={selectedNote?.id} onSelectNote={handleSelectNote} />
      </div>

      <div className="main">
        {error && <div className="error-banner">{error}</div>}
        <NoteEditor
          note={selectedNote}
          onSave={selectedNote ? (title, body, tags) => handleUpdateNote(selectedNote.id, title, body, tags) : handleCreateNote}
          onDelete={selectedNote ? () => handleDeleteNote(selectedNote.id) : undefined}
          isNew={!selectedNote}
        />
      </div>
    </div>
  );
}

export default App;
