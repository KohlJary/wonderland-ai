import { Note } from '../api';
import './NoteList.css';

interface NoteListProps {
  notes: Note[];
  selectedId?: number;
  onSelectNote: (note: Note) => void;
}

export default function NoteList({ notes, selectedId, onSelectNote }: NoteListProps) {
  if (notes.length === 0) {
    return <div className="note-list empty">No notes found</div>;
  }

  return (
    <div className="note-list">
      {notes.map((note) => (
        <div
          key={note.id}
          className={`note-item ${selectedId === note.id ? 'selected' : ''}`}
          onClick={() => onSelectNote(note)}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              onSelectNote(note);
            }
          }}
        >
          <div className="note-item-title">{note.title}</div>
          <div className="note-item-preview">
            {note.body.length > 60 ? note.body.substring(0, 60) + '...' : note.body}
          </div>
          {note.tags.length > 0 && (
            <div className="note-item-tags">
              {note.tags.slice(0, 2).map((tag) => (
                <span key={tag} className="note-item-tag">
                  {tag}
                </span>
              ))}
              {note.tags.length > 2 && <span className="note-item-tag-more">+{note.tags.length - 2}</span>}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
