# Markdown Notebook

A personal markdown notebook web app for capturing, organizing, and searching your notes.

**Features:**
- Create notes with markdown content
- Tag notes for organization
- Search notes by title, body, or tags
- Filter notes by tag
- Persistent storage (SQLite)
- Full-stack: Python FastAPI backend + React + Vite frontend

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+

### Backend Setup

```bash
# Install Python dependencies
pip install -e '.[dev]'

# Initialize database and run tests
pytest

# Start the backend server
uvicorn backend.main:app --reload
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Running Both

In one terminal:
```bash
uvicorn backend.main:app --reload
```

In another terminal:
```bash
cd frontend
npm run dev
```

Then open `http://localhost:5173` in your browser.

## Usage

1. Click "New Note" to create a note
2. Enter a title and markdown content
3. Add tags separated by pressing Enter for each tag
4. Click "Save" to persist the note
5. Click a note in the sidebar to view it
6. Use the search box to find notes by title, content, or tags
7. Use the tag buttons to filter notes
8. Click "Edit" to modify a note
9. Click "Delete" to remove a note

Notes are automatically saved to the SQLite database and persist across page reloads and server restarts.

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/notes` - List notes (supports `?tag=name` and `?search=query`)
- `GET /api/notes/{id}` - Get specific note
- `POST /api/notes` - Create note
- `PUT /api/notes/{id}` - Update note
- `DELETE /api/notes/{id}` - Delete note
- `GET /api/tags` - List all tags

## Testing

Run backend tests:
```bash
pytest
```

## Project Structure

```
.
├── backend/
│   ├── __init__.py
│   ├── main.py          # FastAPI app and routes
│   ├── models.py        # SQLAlchemy models
│   ├── schemas.py       # Pydantic schemas
│   └── database.py      # Database setup
├── frontend/
│   ├── src/
│   │   ├── App.tsx      # Main React component
│   │   ├── api.ts       # API client
│   │   ├── index.css    # Global styles
│   │   ├── components/  # React components
│   │   └── main.tsx     # Entry point
│   ├── vite.config.ts   # Vite config
│   ├── tsconfig.json    # TypeScript config
│   └── package.json
├── tests/               # Backend tests
├── pyproject.toml       # Python project config
└── README.md
```

## Database

The app uses SQLite for persistence. The database file (`notes.db`) is created automatically in the root directory.

To reset the database, simply delete `notes.db` and restart the server.

## Technology Stack

**Backend:**
- FastAPI - Modern Python web framework
- SQLAlchemy - ORM
- SQLite - Embedded database
- Pydantic - Data validation

**Frontend:**
- React 18 - UI framework
- Vite - Build tool
- TypeScript - Type safety
- react-markdown - Markdown rendering
- Axios - HTTP client

## License

MIT
