import React, { useState, useEffect } from 'react'
import { Note } from '../api'
import styles from './NoteEditor.module.css'

interface NoteEditorProps {
  note?: Note
  onSave: (title: string, body: string, tags: string[]) => void
  onCancel: () => void
  onDelete?: () => void
}

export default function NoteEditor({
  note,
  onSave,
  onCancel,
  onDelete,
}: NoteEditorProps) {
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [tagInput, setTagInput] = useState('')
  const [tags, setTags] = useState<string[]>([])

  useEffect(() => {
    if (note) {
      setTitle(note.title)
      setBody(note.body)
      setTags(note.tags.map((t) => t.name))
      setTagInput('')
    } else {
      setTitle('')
      setBody('')
      setTags([])
      setTagInput('')
    }
  }, [note])

  function handleAddTag() {
    const trimmed = tagInput.trim()
    if (trimmed && !tags.includes(trimmed)) {
      setTags([...tags, trimmed])
      setTagInput('')
    }
  }

  function handleRemoveTag(tag: string) {
    setTags(tags.filter((t) => t !== tag))
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleAddTag()
    }
  }

  function handleSave() {
    if (!title.trim()) {
      alert('Please enter a title')
      return
    }
    onSave(title, body, tags)
  }

  return (
    <div className={styles.editor}>
      <div className={styles.editorHeader}>
        <div>
          <h2>{note ? 'Edit Note' : 'New Note'}</h2>
        </div>
        <div className={styles.editorActions}>
          <button className={styles.saveBtn} onClick={handleSave}>
            Save
          </button>
          <button className={styles.cancelBtn} onClick={onCancel}>
            Cancel
          </button>
          {note && onDelete && (
            <button className={styles.deleteBtn} onClick={onDelete}>
              Delete
            </button>
          )}
        </div>
      </div>

      <div className={styles.editorContent}>
        <div className={styles.editSection}>
          <input
            type="text"
            placeholder="Note title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className={styles.titleInput}
            autoFocus
          />

          <div className={styles.tagsInput}>
            <div className={styles.tagsList}>
              {tags.map((tag) => (
                <span key={tag} className={styles.tag}>
                  {tag}
                  <button
                    className={styles.removeTag}
                    onClick={() => handleRemoveTag(tag)}
                  >
                    ×
                  </button>
                </span>
              ))}
              <input
                type="text"
                placeholder="Add tag and press Enter"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={handleKeyDown}
                className={styles.tagInputField}
              />
            </div>
          </div>

          <textarea
            placeholder="Note content (markdown supported)"
            value={body}
            onChange={(e) => setBody(e.target.value)}
            className={styles.bodyInput}
          />
        </div>
      </div>
    </div>
  )
}
