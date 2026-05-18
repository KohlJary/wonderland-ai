import './TagFilter.css';

interface TagFilterProps {
  tags: string[];
  selectedTag: string | null;
  onSelectTag: (tag: string | null) => void;
}

export default function TagFilter({ tags, selectedTag, onSelectTag }: TagFilterProps) {
  if (tags.length === 0) {
    return null;
  }

  return (
    <div className="tag-filter">
      <div className="tag-filter-label">Filter by tag:</div>
      <div className="tag-filter-list">
        <button
          onClick={() => onSelectTag(null)}
          className={`tag-filter-item ${selectedTag === null ? 'active' : ''}`}
        >
          All
        </button>
        {tags.map((tag) => (
          <button
            key={tag}
            onClick={() => onSelectTag(selectedTag === tag ? null : tag)}
            className={`tag-filter-item ${selectedTag === tag ? 'active' : ''}`}
          >
            {tag}
          </button>
        ))}
      </div>
    </div>
  );
}
