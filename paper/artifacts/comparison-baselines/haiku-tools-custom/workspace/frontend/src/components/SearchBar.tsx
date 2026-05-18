import { useState } from 'react';
import './SearchBar.css';

interface SearchBarProps {
  onSearch: (query: string) => void;
}

export default function SearchBar({ onSearch }: SearchBarProps) {
  const [query, setQuery] = useState('');

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const newQuery = e.target.value;
    setQuery(newQuery);
    onSearch(newQuery);
  }

  function handleClear() {
    setQuery('');
    onSearch('');
  }

  return (
    <div className="search-bar">
      <input
        type="text"
        placeholder="Search notes..."
        value={query}
        onChange={handleChange}
        className="search-input"
      />
      {query && (
        <button onClick={handleClear} className="search-clear" aria-label="Clear search">
          ✕
        </button>
      )}
    </div>
  );
}
