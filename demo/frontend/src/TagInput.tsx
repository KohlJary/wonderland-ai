/**
 * TagInput — allows the user to add and remove tags.
 *
 * Features:
 * - Text input + Add button to add a tag
 * - User can press Enter to add (same as clicking Add)
 * - Added tags display as removable chips
 * - Tags are trimmed; empty tags rejected
 * - No duplicate tags
 * - Parent component controls the tag list state
 */

import { useState } from 'react';

interface TagInputProps {
  tags: string[];
  onTagsChange: (tags: string[]) => void;
  disabled?: boolean;
}

export function TagInput({ tags, onTagsChange, disabled = false }: TagInputProps) {
  const [input, setInput] = useState('');

  const handleAddTag = () => {
    const trimmed = input.trim();
    if (!trimmed) {
      return;
    }
    // Avoid duplicates
    if (tags.includes(trimmed)) {
      setInput('');
      return;
    }
    onTagsChange([...tags, trimmed]);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  };

  const handleRemoveTag = (index: number) => {
    onTagsChange(tags.filter((_, i) => i !== index));
  };

  return (
    <div style={styles.container}>
      <div style={styles.inputGroup}>
        <input
          type="text"
          placeholder="Add a tag (press Enter or click Add)"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          style={styles.tagInputField}
        />
        <button onClick={handleAddTag} disabled={disabled} style={styles.addButton}>
          Add
        </button>
      </div>

      {tags.length > 0 && (
        <div style={styles.tagList}>
          {tags.map((tag, index) => (
            <div key={index} style={styles.tagChip}>
              <span>{tag}</span>
              <button
                onClick={() => handleRemoveTag(index)}
                style={styles.removeButton}
                aria-label={`Remove tag ${tag}`}
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const styles = {
  container: {
    marginBottom: '1rem',
  } as const,
  inputGroup: {
    display: 'flex',
    gap: '0.5rem',
    marginBottom: '0.5rem',
  } as const,
  tagInputField: {
    flex: 1,
    padding: '0.75rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '0.95rem',
    fontFamily: 'system-ui, sans-serif',
    boxSizing: 'border-box',
  } as const,
  addButton: {
    padding: '0.75rem 1.25rem',
    backgroundColor: '#28a745',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    fontSize: '0.95rem',
    cursor: 'pointer',
    fontWeight: '500',
  } as const,
  tagList: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '0.5rem',
  } as const,
  tagChip: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.5rem',
    padding: '0.4rem 0.8rem',
    backgroundColor: '#e8f4f8',
    color: '#0066cc',
    borderRadius: '20px',
    fontSize: '0.9rem',
    border: '1px solid #0066cc',
  } as const,
  removeButton: {
    background: 'none',
    border: 'none',
    color: '#0066cc',
    cursor: 'pointer',
    fontSize: '1.2rem',
    padding: '0',
    lineHeight: '1',
    display: 'flex',
    alignItems: 'center',
  } as const,
};

export default TagInput;
