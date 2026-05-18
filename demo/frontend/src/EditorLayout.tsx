/**
 * EditorLayout — wires Editor and Preview side-by-side.
 *
 * Contract: Editor (left) updates local state on keystroke.
 * Preview (right) receives body prop and re-renders on every change.
 * Split layout is left-right at large screens, stacks on mobile (deferred to v2).
 *
 * Invariants:
 * - Editor state is independent of Preview (editor drives preview)
 * - Preview is read-only (no typing in preview pane)
 * - Layout splits 50/50 left-right (adjustable later)
 */

import { useState } from 'react';
import Editor from './Editor';
import Preview from './Preview';

interface EditorLayoutProps {
  noteId?: number | null;
  onSave?: () => void;
}

export function EditorLayout({ noteId, onSave }: EditorLayoutProps) {
  const [previewBody, setPreviewBody] = useState('');

  return (
    <div style={styles.layout}>
      <div style={styles.editorPane}>
        <Editor noteId={noteId} onBodyChange={setPreviewBody} onSave={onSave} />
      </div>
      <div style={styles.previewPane}>
        <h2 style={styles.heading}>Preview</h2>
        <Preview body={previewBody} />
      </div>
    </div>
  );
}

const styles = {
  layout: {
    display: 'flex',
    height: '100vh',
    backgroundColor: '#f0f0f0',
  } as const,
  editorPane: {
    flex: 1,
    minWidth: 0,
    overflow: 'hidden',
  } as const,
  previewPane: {
    flex: 1,
    minWidth: 0,
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#fff',
    borderLeft: '1px solid #ddd',
  } as const,
  heading: {
    margin: '0',
    padding: '1rem',
    fontSize: '1.25rem',
    borderBottom: '1px solid #ddd',
    color: '#333',
  } as const,
};

export default EditorLayout;
