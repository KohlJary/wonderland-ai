/**
 * Search — search notes by title, body, and optional tags.
 *
 * Contract: per contract-note-008 (search-api/v1)
 * - GET /api/search: ?q=...&tags=...&page=...&page_size=... → SearchResponse
 * - Renders search form with text input and tag multiselect filter
 * - Displays paginated results with note title, content preview, tags, and created date
 * - Supports clearing search and returning to main notes view
 * - Searches as user types (debounced to avoid overwhelming the backend)
 *
 * URL contract (ticket-037):
 * - /search[?q=...&tags=...&page=...] — search state persists in URL params
 * - q: search query text (optional)
 * - tags: comma-separated tag filters (optional)
 * - page: current page number, 1-indexed (optional, defaults to 1)
 * - URL params are the source of truth; state restores from URL on component mount
 * - URL updates when search state changes (query, tags, page)
 * - Page reload restores all search parameters from URL
 *
 * Client state:
 * - searchQuery: user's text input for search (local, synced to URL ?q=...)
 * - selectedTags: user's selected tag filters (local, synced to URL ?tags=...)
 * - page: current pagination page (1-indexed, synced to URL ?page=...)
 * - page_size: results per page (fixed at 20)
 * - results: the SearchResponse from the last successful API call
 * - loading: boolean, true while API call in progress
 * - error: error message if last API call failed, null otherwise
 *
 * Invariants:
 * - searchQuery/selectedTags changes trigger debounced API call + URL update (reset to page 1)
 * - page changes trigger API call + URL update (keep query and tags)
 * - URL params are synced on every state change so reload restores state
 * - results are displayed in reverse chronological order (API contracts this)
 * - pagination controls show: previous/next buttons, page number, result count
 * - body_preview is truncated server-side to 150 chars (no client truncation needed)
 * - clearing search returns to editor view (managed by parent App)
 *
 * UI states:
 * - loading: spinner while fetching
 * - error-recoverable: error message with retry option
 * - no-results: "no notes match" message if query produced no matches
 * - results: paginated list of notes with title, preview, tags, date
 * - empty: "no notes created yet" if no notes exist at all (results.total_results === 0 and no query)
 */

import { useEffect, useState, useCallback } from 'react';
import { searchNotes, SearchResponse, SearchResultNote } from './api';

interface SearchProps {
  onClear: () => void;
  onViewNote?: (noteId: number) => void;
}

const DEBOUNCE_MS = 300;

/**
 * Highlights all case-insensitive matches of query in text.
 * Escapes regex special chars to avoid pattern injection.
 * Returns a React fragment with <mark> tags around matches.
 */
function highlightMatches(text: string, query: string): React.ReactNode {
  if (!query || !text) return text;
  
  // Escape regex special characters to avoid injection
  const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  
  try {
    // Case-insensitive match (g flag for global, i flag for case-insensitive)
    const regex = new RegExp(escaped, 'gi');
    const parts: (string | React.ReactNode)[] = [];
    let lastIndex = 0;
    let match;
    
    while ((match = regex.exec(text)) !== null) {
      // Add text before this match
      if (match.index > lastIndex) {
        parts.push(text.substring(lastIndex, match.index));
      }
      // Add the highlighted match
      parts.push(
        <mark key={`${lastIndex}-${match.index}`} style={{ backgroundColor: '#ffeb3b', fontWeight: 'bold' }}>
          {match[0]}
        </mark>
      );
      lastIndex = match.index + match[0].length;
    }
    
    // Add remaining text after last match
    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }
    
    return parts.length > 0 ? parts : text;
  } catch {
    // If regex somehow fails, return unformatted text
    return text;
  }
}

/**
 * Parse URL search params to extract q, tags, and page.
 * Returns default values if params are missing or invalid.
 */
function parseUrlParams(): { q: string; tags: string[]; page: number } {
  const params = new URLSearchParams(window.location.search);
  const q = params.get('q') || '';
  const tagsStr = params.get('tags') || '';
  const tags = tagsStr ? tagsStr.split(',').filter((t) => t.trim()) : [];
  const page = Math.max(1, parseInt(params.get('page') || '1', 10));
  return { q, tags, page };
}

/**
 * Update URL params without full page reload.
 * Pushes new state to history so browser back button works.
 */
function updateUrlParams(q: string, tags: string[], page: number): void {
  const params = new URLSearchParams();
  if (q) params.append('q', q);
  if (tags.length > 0) params.append('tags', tags.join(','));
  if (page > 1) params.append('page', String(page));
  
  const newUrl = params.toString() ? `/search?${params}` : '/search';
  window.history.pushState(null, '', newUrl);
}

export function Search({ onClear, onViewNote }: SearchProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [page, setPage] = useState(1);  // 1-indexed per contract
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [initialized, setInitialized] = useState(false);

  // Initialize state from URL params on mount
  useEffect(() => {
    const { q, tags, page: urlPage } = parseUrlParams();
    setSearchQuery(q);
    setSelectedTags(tags);
    setPage(urlPage);
    setInitialized(true);
  }, []);

  // Debounced search: when user changes query or tags, reset to page 1 and fetch
  useEffect(() => {
    if (!initialized) return;  // Skip until URL params loaded
    
    const timer = setTimeout(async () => {
      const newPage = 1;  // Reset to first page (1-indexed)
      setPage(newPage);
      updateUrlParams(searchQuery, selectedTags, newPage);  // Update URL with new query/tags, page 1
      setLoading(true);
      setError(null);
      try {
        const tagsParam = selectedTags.length > 0 ? selectedTags.join(',') : undefined;
        const response = await searchNotes(searchQuery || undefined, tagsParam, newPage, 20);
        setResults(response);
      } catch (err) {
        setError(`Search failed: ${String(err)}`);
        setResults(null);
      } finally {
        setLoading(false);
      }
    }, DEBOUNCE_MS);

    return () => clearTimeout(timer);
  }, [searchQuery, selectedTags, initialized]);

  // Fetch results when page changes (without debounce)
  useEffect(() => {
    if (!initialized || page === 1) return;  // Skip initial load or when page is 1 (handled by debounced effect above)
    
    const fetchPage = async () => {
      updateUrlParams(searchQuery, selectedTags, page);  // Update URL with new page
      setLoading(true);
      setError(null);
      try {
        const tagsParam = selectedTags.length > 0 ? selectedTags.join(',') : undefined;
        const response = await searchNotes(searchQuery || undefined, tagsParam, page, 20);
        setResults(response);
      } catch (err) {
        setError(`Search failed: ${String(err)}`);
      } finally {
        setLoading(false);
      }
    };

    fetchPage();
  }, [page, initialized, searchQuery, selectedTags]);

  // Handle page change: fetch new page with current query/tags
  const handlePageChange = useCallback(
    (newPage: number) => {
      setPage(newPage);
    },
    []
  );

  // Handle adding a tag filter
  const handleAddTag = (tag: string) => {
    if (!selectedTags.includes(tag)) {
      setSelectedTags([...selectedTags, tag]);
    }
  };

  // Handle removing a tag filter
  const handleRemoveTag = (tagToRemove: string) => {
    setSelectedTags(selectedTags.filter((t) => t !== tagToRemove));
  };

  // Compute all unique tags from results (for suggestion/display)
  const allTags = results
    ? Array.from(new Set(results.results.flatMap((note) => note.tag_names)))
    : [];
  const unselectedTags = allTags.filter((tag) => !selectedTags.includes(tag));

  // Render a single note result
  const renderNoteResult = (note: SearchResultNote) => {
    // body_preview is already truncated server-side to 150 chars
    const preview = note.body_preview;
    const createdDate = new Date(note.created_at);
    const dateString = createdDate.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });

    const handleClick = () => {
      if (onViewNote) {
        onViewNote(note.id);
      }
    };

    return (
      <div
        key={note.id}
        style={styles.resultItem}
        onClick={handleClick}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            handleClick();
          }
        }}
      >
        <div style={styles.resultTitle}>
          {highlightMatches(note.title, searchQuery)}
        </div>
        {preview && (
          <div style={styles.resultPreview}>
            {highlightMatches(preview, searchQuery)}
          </div>
        )}
        {note.tag_names.length > 0 && (
          <div style={styles.resultTags}>
            {note.tag_names.map((tagName) => (
              <span key={tagName} style={styles.resultTag}>
                {tagName}
              </span>
            ))}
          </div>
        )}
        <div style={styles.resultDate}>{dateString}</div>
      </div>
    );
  };

  if (!initialized) {
    return <div style={styles.searchContainer}>Loading search…</div>;
  }

  return (
    <div style={styles.searchContainer}>
      <div style={styles.searchHeader}>
        <h2 style={styles.heading}>Search Notes</h2>
        <button onClick={onClear} style={styles.clearButton}>
          ← Back to Editor
        </button>
      </div>

      {/* Search form */}
      <div style={styles.searchForm}>
        <input
          type="text"
          placeholder="Search by title or content…"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          disabled={loading}
          style={styles.searchInput}
          autoFocus
        />

        {/* Tag filter chips */}
        {selectedTags.length > 0 && (
          <div style={styles.selectedTags}>
            {selectedTags.map((tag) => (
              <span key={tag} style={styles.tagChip}>
                {tag}
                <button
                  onClick={() => handleRemoveTag(tag)}
                  style={styles.tagChipRemove}
                  aria-label={`Remove filter ${tag}`}
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        )}

        {/* Tag suggestions (unselected tags from results) */}
        {unselectedTags.length > 0 && (
          <div style={styles.tagSuggestions}>
            <span style={styles.tagLabel}>Filter by ALL of these tags:</span>
            {unselectedTags.map((tag) => (
              <button
                key={tag}
                onClick={() => handleAddTag(tag)}
                style={styles.tagSuggestion}
              >
                {tag}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Error state */}
      {error && (
        <div style={styles.error}>
          {error}
          <button
            onClick={() => handlePageChange(page)}
            style={styles.retryButton}
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading state */}
      {loading && <div style={styles.loading}>Searching…</div>}

      {/* Results */}
      {!loading && results && results.results.length > 0 && (
        <>
          <div style={styles.resultCount}>
            Found {results.total_results} note{results.total_results !== 1 ? 's' : ''}
            {results.total_results > results.results.length &&
              ` (showing ${results.results.length})`}
          </div>
          <div style={styles.resultsList}>
            {results.results.map(renderNoteResult)}
          </div>

          {/* Pagination controls */}
          {(results.page > 1 || results.has_more) && (
            <div style={styles.pagination}>
              <button
                onClick={() => handlePageChange(results.page - 1)}
                disabled={results.page === 1 || loading}
                style={
                  results.page === 1 ? styles.paginationButtonDisabled : styles.paginationButton
                }
              >
                ← Previous
              </button>
              <span style={styles.pageInfo}>
                Page {results.page}
              </span>
              <button
                onClick={() => handlePageChange(results.page + 1)}
                disabled={!results.has_more || loading}
                style={
                  !results.has_more
                    ? styles.paginationButtonDisabled
                    : styles.paginationButton
                }
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}

      {/* No results state */}
      {!loading && results && results.results.length === 0 && searchQuery && (
        <div style={styles.noResults}>
          No notes match "{searchQuery}"
          {selectedTags.length > 0 && ` with tags: ${selectedTags.join(', ')}`}
        </div>
      )}

      {/* Empty state (no notes at all) */}
      {!loading && results && results.results.length === 0 && !searchQuery && (
        <div style={styles.empty}>
          No notes created yet. Go back to the editor to create your first note.
        </div>
      )}
    </div>
  );
}

const styles = {
  searchContainer: {
    flex: 1,
    padding: '2rem',
    overflow: 'auto',
    backgroundColor: '#fff',
  } as const,
  searchHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1.5rem',
  } as const,
  heading: {
    margin: '0',
    fontSize: '1.5rem',
    color: '#333',
  } as const,
  clearButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#ccc',
    color: '#333',
    border: 'none',
    borderRadius: '4px',
    fontSize: '0.95rem',
    cursor: 'pointer',
    fontWeight: '500',
  } as const,
  searchForm: {
    marginBottom: '1.5rem',
    padding: '1rem',
    backgroundColor: '#f9f9f9',
    borderRadius: '4px',
  } as const,
  searchInput: {
    width: '100%',
    padding: '0.75rem',
    fontSize: '1rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    marginBottom: '0.5rem',
    boxSizing: 'border-box',
    fontFamily: 'system-ui, sans-serif',
  } as const,
  selectedTags: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '0.5rem',
    marginBottom: '0.5rem',
  } as const,
  tagChip: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.5rem',
    padding: '0.4rem 0.8rem',
    backgroundColor: '#0066cc',
    color: '#fff',
    borderRadius: '20px',
    fontSize: '0.9rem',
  } as const,
  tagChipRemove: {
    background: 'none',
    border: 'none',
    color: '#fff',
    cursor: 'pointer',
    fontSize: '1.2rem',
    padding: '0',
    lineHeight: '1',
    display: 'flex',
    alignItems: 'center',
  } as const,
  tagSuggestions: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '0.5rem',
    alignItems: 'center',
  } as const,
  tagLabel: {
    fontSize: '0.9rem',
    color: '#666',
    marginRight: '0.5rem',
  } as const,
  tagSuggestion: {
    padding: '0.4rem 0.8rem',
    backgroundColor: '#f0f0f0',
    color: '#333',
    border: '1px solid #ddd',
    borderRadius: '16px',
    fontSize: '0.85rem',
    cursor: 'pointer',
  } as const,
  error: {
    padding: '0.75rem 1rem',
    marginBottom: '1rem',
    backgroundColor: '#fee',
    color: '#c33',
    borderRadius: '4px',
    fontSize: '0.9rem',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  } as const,
  retryButton: {
    padding: '0.4rem 0.8rem',
    backgroundColor: '#c33',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    fontSize: '0.85rem',
    cursor: 'pointer',
    fontWeight: 'bold',
  } as const,
  loading: {
    padding: '2rem',
    textAlign: 'center',
    color: '#666',
    fontSize: '1rem',
  } as const,
  resultCount: {
    marginBottom: '1rem',
    fontSize: '0.95rem',
    color: '#666',
    fontWeight: '500',
  } as const,
  resultsList: {
    marginBottom: '1.5rem',
  } as const,
  resultItem: {
    padding: '1rem',
    marginBottom: '1rem',
    border: '1px solid #ddd',
    borderRadius: '4px',
    backgroundColor: '#fafafa',
    cursor: 'pointer',
    transition: 'box-shadow 0.2s, transform 0.2s',
  } as const,
  resultTitle: {
    fontSize: '1.1rem',
    fontWeight: 'bold',
    color: '#0066cc',
    marginBottom: '0.5rem',
  } as const,
  resultPreview: {
    fontSize: '0.95rem',
    color: '#666',
    marginBottom: '0.5rem',
    lineHeight: '1.4',
  } as const,
  resultTags: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '0.4rem',
    marginBottom: '0.5rem',
  } as const,
  resultTag: {
    display: 'inline-block',
    padding: '0.2rem 0.6rem',
    backgroundColor: '#e8f4f8',
    color: '#0066cc',
    borderRadius: '12px',
    fontSize: '0.8rem',
    border: '1px solid #0066cc',
  } as const,
  resultDate: {
    fontSize: '0.85rem',
    color: '#999',
  } as const,
  pagination: {
    display: 'flex',
    justifyContent: 'center',
    gap: '1rem',
    alignItems: 'center',
    marginTop: '1.5rem',
    paddingTop: '1rem',
    borderTop: '1px solid #ddd',
  } as const,
  paginationButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#0066cc',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    fontSize: '0.95rem',
    cursor: 'pointer',
    fontWeight: '500',
  } as const,
  paginationButtonDisabled: {
    padding: '0.5rem 1rem',
    backgroundColor: '#ccc',
    color: '#999',
    border: 'none',
    borderRadius: '4px',
    fontSize: '0.95rem',
    cursor: 'not-allowed',
    fontWeight: '500',
  } as const,
  pageInfo: {
    fontSize: '0.95rem',
    color: '#666',
    fontWeight: '500',
  } as const,
  noResults: {
    padding: '2rem',
    textAlign: 'center',
    color: '#666',
    fontSize: '1rem',
    backgroundColor: '#f9f9f9',
    borderRadius: '4px',
  } as const,
  empty: {
    padding: '2rem',
    textAlign: 'center',
    color: '#666',
    fontSize: '1rem',
    backgroundColor: '#f9f9f9',
    borderRadius: '4px',
  } as const,
};

export default Search;
