import { useState, useEffect } from 'react';
import { Note } from '../api';
import MarkdownPreview from './MarkdownPreview';
import './NoteEditor.css';

interface NoteEditorProps {
  note: Note | null;
  onSave: (title: string, body: string, tags: string[]) => Promise<void>;
  onDelete?: () => Promise<void>;
  isNew: boolean;
}

export default function NoteEditor({ note, onSave, onDelete, isNew }: NoteEditorProps) {
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [tagInput, setTagInput] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (note) {
      setTitle(note.title);
      setBody(note.body);
      setTags(note.tags);
      setTagInput('');
    } else {
      setTitle('');
      setBody('');
      setTags([]);
      setTagInput('');
    }
  }, [note]);

  async function handleSave() {
    if (!title.trim()) {
      alert('Please enter a title');
      return;
    }
    setSaving(true);
    try {
      await onSave(title, body, tags);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!onDelete) return;
    if (!confirm('Are you sure you want to delete this note?')) return;
    setDeleting(true);
    try {
      await onDelete();
    } finally {
      setDeleting(false);
    }
  }

  function handleAddTag() {
    const tag = tagInput.trim().toLowerCase();
    if (tag && !tags.includes(tag)) {
      setTags([...tags, tag]);
      setTagInput('');
    }
  }

  function handleRemoveTag(tagToRemove: string) {
    setTags(tags.filter(t => t !== tagToRemove));
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  }

  return (
    <div className="note-editor">
      <div className="editor-header">
        <input
          type="text"
          placeholder="Note Title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="title-input"
        />
        <div className="editor-actions">
          <button onClick={handleSave} disabled={saving} className="save-btn">
            {saving ? 'Saving...' : 'Save'}
          </button>
          {!isNew && onDelete && (
            <button onClick={handleDelete} disabled={deleting} className="delete-btn">
              {deleting ? 'Deleting...' : 'Delete'}
            </button>
          )}
        </div>
      </div>

      <div className="tag-section">
        <div className="tag-input-group">
          <input
            type="text"
            placeholder="Add tag and press Enter"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={handleKeyDown}
            className="tag-input"
          />
          <button onClick={handleAddTag} className="tag-add-btn">
            Add
          </button>
        </div>
        <div className="tags">
          {tags.map((tag) => (
            <span key={tag} className="tag">
              {tag}
              <button
                onClick={() => handleRemoveTag(tag)}
                className="tag-remove"
                aria-label="Remove tag"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      </div>

      <div className="editor-content">
        <div className="editor-pane">
          <textarea
            placeholder="Write your markdown here..."
            value={body}
            onChange={(e) => setBody(e.target.value)}
            className="markdown-input"
          />
        </div>
        <div className="preview-pane">
          <MarkdownPreview markdown={body} />
        </div>
      </div>
    </div>
  );
}
