import React from 'react'
import { Note } from '../api'
import styles from './NoteList.module.css'

interface NoteListProps {
  notes: Note[]
  selectedNote: Note | null
  onSelectNote: (note: Note) => void
}

export default function NoteList({
  notes,
  selectedNote,
  onSelectNote,
}: NoteListProps) {
  if (notes.length === 0) {
    return (
      <div className={styles.empty}>
        <p>No notes yet</p>
      </div>
    )
  }

  return (
    <div className={styles.list}>
      {notes.map((note) => (
        <button
          key={note.id}
          className={`${styles.item} ${
            selectedNote?.id === note.id ? styles.itemActive : ''
          }`}
          onClick={() => onSelectNote(note)}
        >
          <div className={styles.itemTitle}>{note.title}</div>
          <div className={styles.itemDate}>
            {new Date(note.updated_at).toLocaleDateString()}
          </div>
          {note.tags.length > 0 && (
            <div className={styles.itemTags}>
              {note.tags.slice(0, 2).map((tag) => (
                <span key={tag.id} className={styles.itemTag}>
                  {tag.name}
                </span>
              ))}
              {note.tags.length > 2 && (
                <span className={styles.itemTag}>+{note.tags.length - 2}</span>
              )}
            </div>
          )}
        </button>
      ))}
    </div>
  )
}
