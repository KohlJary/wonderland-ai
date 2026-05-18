import React, { useState, useEffect } from 'react'
import { notesApi, Note, Tag } from './api'
import NoteEditor from './components/NoteEditor'
import NoteList from './components/NoteList'
import NotePreview from './components/NotePreview'
import styles from './App.module.css'

export default function App() {
  const [notes, setNotes] = useState<Note[]>([])
  const [selectedNote, setSelectedNote] = useState<Note | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [loading, setLoading] = useState(true)
  const [tags, setTags] = useState<Tag[]>([])
  const [selectedTag, setSelectedTag] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')

  // Load notes and tags
  useEffect(() => {
    loadData()
  }, [selectedTag, searchQuery])

  async function loadData() {
    try {
      setLoading(true)
      const filters = {
        tag: selectedTag || undefined,
        search: searchQuery || undefined,
      }
      const notesRes = await notesApi.listNotes(filters)
      setNotes(notesRes.data)

      const tagsRes = await notesApi.listTags()
      setTags(tagsRes.data)
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }

  async function handleCreateNote() {
    setSelectedNote(null)
    setIsEditing(true)
  }

  async function handleSaveNote(title: string, body: string, tagNames: string[]) {
    try {
      if (selectedNote) {
        // Update
        const updated = await notesApi.updateNote(selectedNote.id, {
          title,
          body,
          tags: tagNames,
        })
        setSelectedNote(updated.data)
      } else {
        // Create
        const created = await notesApi.createNote({
          title,
          body,
          tags: tagNames,
        })
        setSelectedNote(created.data)
      }
      setIsEditing(false)
      await loadData()
    } catch (error) {
      console.error('Failed to save note:', error)
    }
  }

  async function handleDeleteNote(noteId: number) {
    try {
      await notesApi.deleteNote(noteId)
      setSelectedNote(null)
      setIsEditing(false)
      await loadData()
    } catch (error) {
      console.error('Failed to delete note:', error)
    }
  }

  function handleSelectNote(note: Note) {
    setSelectedNote(note)
    setIsEditing(false)
  }

  function handleEditNote() {
    setIsEditing(true)
  }

  function handleCancelEdit() {
    setIsEditing(false)
  }

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1>Markdown Notebook</h1>
      </header>

      <div className={styles.main}>
        {/* Sidebar with notes list and filters */}
        <aside className={styles.sidebar}>
          <div className={styles.sidebarContent}>
            <button className={styles.newNoteBtn} onClick={handleCreateNote}>
              + New Note
            </button>

            {/* Search */}
            <input
              type="text"
              placeholder="Search notes..."
              className={styles.searchInput}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />

            {/* Tags filter */}
            <div className={styles.tagsSection}>
              <h3>Tags</h3>
              <button
                className={`${styles.tagButton} ${selectedTag === null ? styles.tagButtonActive : ''}`}
                onClick={() => setSelectedTag(null)}
              >
                All
              </button>
              {tags.map((tag) => (
                <button
                  key={tag.id}
                  className={`${styles.tagButton} ${selectedTag === tag.name ? styles.tagButtonActive : ''}`}
                  onClick={() => setSelectedTag(tag.name)}
                >
                  {tag.name}
                </button>
              ))}
            </div>

            {/* Notes list */}
            {loading ? (
              <div className={styles.loading}>Loading...</div>
            ) : (
              <NoteList
                notes={notes}
                selectedNote={selectedNote}
                onSelectNote={handleSelectNote}
              />
            )}
          </div>
        </aside>

        {/* Main content area */}
        <div className={styles.content}>
          {isEditing && selectedNote !== null ? (
            // Edit existing note
            <NoteEditor
              note={selectedNote}
              onSave={handleSaveNote}
              onCancel={handleCancelEdit}
              onDelete={() => handleDeleteNote(selectedNote.id)}
            />
          ) : isEditing && selectedNote === null ? (
            // Create new note
            <NoteEditor onSave={handleSaveNote} onCancel={handleCancelEdit} />
          ) : selectedNote ? (
            // View note
            <div className={styles.noteView}>
              <div className={styles.noteHeader}>
                <div>
                  <h2>{selectedNote.title}</h2>
                  <div className={styles.noteMeta}>
                    <span className={styles.date}>
                      Last edited: {new Date(selectedNote.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <div className={styles.noteActions}>
                  <button onClick={handleEditNote}>Edit</button>
                  <button
                    className={styles.deleteBtn}
                    onClick={() => handleDeleteNote(selectedNote.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>

              {selectedNote.tags.length > 0 && (
                <div className={styles.noteTags}>
                  {selectedNote.tags.map((tag) => (
                    <span key={tag.id} className={styles.noteTag}>
                      {tag.name}
                    </span>
                  ))}
                </div>
              )}

              <div className={styles.preview}>
                <NotePreview markdown={selectedNote.body} />
              </div>
            </div>
          ) : (
            <div className={styles.noSelection}>
              <p>Select a note or create a new one to get started</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
