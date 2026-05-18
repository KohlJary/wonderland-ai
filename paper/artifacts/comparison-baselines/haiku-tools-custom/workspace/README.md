# 📓 Markdown Notebook

A personal markdown notebook web app for developers and researchers to capture, organize, and find notes. Single-user, no authentication required — load it and start using it immediately.

## ✨ Features

- **📝 Markdown Editor**: Write notes in markdown with live HTML preview
- **🏷️ Tag Organization**: Tag notes for easy categorization
- **🔍 Full-Text Search**: Search across note titles, bodies, and tags
- **📌 Tag Filtering**: Filter notes by selected tags
- **💾 Persistent Storage**: All notes saved to local SQLite database
- **🌓 Dark/Light Mode**: Respects system color scheme preference
- **⚡ Fast & Responsive**: Split-pane editor and preview

## 🛠️ Tech Stack

- **Backend**: Python 3.9+ / FastAPI / SQLite
- **Frontend**: React 18 / TypeScript / Vite
- **Markdown**: react-markdown with GitHub Flavored Markdown (tables, strikethrough, etc.)

## 🚀 Quick Start (5 minutes)

### Prerequisites

- Python 3.9+
- Node.js 16+ / npm

### Step 1: Clone & Enter Directory

```bash
git clone <repository-url>
cd markdown-notebook
```

### Step 2: Set Up Backend

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install fastapi uvicorn sqlalchemy pydantic
```

### Step 3: Set Up Frontend

```bash
cd frontend
npm install
cd ..
```

### Step 4: Run Backend & Frontend

**Terminal 1 - Backend (port 8000):**
```bash
source .venv/bin/activate
python src/backend/main.py
```

**Terminal 2 - Frontend (port 5173):**
```bash
cd frontend
npm run dev
```

### Step 5: Open in Browser

Visit **http://localhost:5173** and start writing notes!

## 💡 Usage

### Creating a Note
1. Click **"New Note"** in the sidebar
2. Enter a **title**
3. Write **markdown** in the editor (preview updates in real-time)
4. Add **tags** by typing a tag name and pressing Enter
5. Click **Save**

### Finding Notes
- **Search**: Use the search bar to find notes by title, content, or tag (case-insensitive substring match)
- **Filter by Tag**: Click any tag in the "Filter by tag" section to show only notes with that tag
- **Browse**: Notes are sorted by most recently edited first

### Editing & Deleting
- Click a note in the list to open it
- Edit the title, body, or tags
- Click **Delete** to remove the note (with confirmation)

## 📁 Project Structure

```
markdown-notebook/
├── src/backend/
│   ├── __init__.py
│   └── main.py                 # FastAPI app, DB models, routes
├── frontend/
│   ├── src/
│   │   ├── main.tsx           # React entry point
│   │   ├── App.tsx            # Main component
│   │   ├── api.ts             # API client
│   │   ├── index.css
│   │   └── components/        # React components
│   │       ├── NoteEditor.tsx
│   │       ├── MarkdownPreview.tsx
│   │       ├── NoteList.tsx
│   │       ├── SearchBar.tsx
│   │       └── TagFilter.tsx
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   └── index.html
├── tests/
│   └── test_backend.py        # Pytest unit tests
├── pyproject.toml
├── requirements.txt
├── .gitignore
├── .env.example
├── start.sh                   # Quick start script
├── run_backend.py            # Manual backend test
└── README.md
```

## 🧪 Testing

### Backend Tests
```bash
source .venv/bin/activate
pip install pytest httpx
pytest tests/test_backend.py -v
```

All 14 tests cover:
- CRUD operations
- Search & filtering
- Tag management
- Case-insensitive search
- Timestamps

### Frontend Build
```bash
cd frontend
npm run build
```

Output: `frontend/dist/` (ready for production deployment)

## 🗄️ Database Schema

The app uses **SQLite** with a single `notes` table:

```sql
CREATE TABLE notes (
    id INTEGER PRIMARY KEY,
    title VARCHAR,
    body TEXT,
    tags TEXT,           -- JSON array ["tag1", "tag2"]
    created_at DATETIME,
    updated_at DATETIME
);
```

Database file: `./notebook.db` (created automatically on first run)

## 🔌 API Reference

All endpoints return JSON.

### Health
- `GET /api/health` → `{"status": "ok"}`

### Notes
- `POST /api/notes` - Create note
  ```json
  {"title": "...", "body": "...", "tags": [...]}
  ```
- `GET /api/notes` - List all notes (with optional filters)
  - `?search=query` - Search by title/body/tags
  - `?tag=tagname` - Filter by tag
- `GET /api/notes/{id}` - Get a specific note
- `PUT /api/notes/{id}` - Update note (partial update OK)
- `DELETE /api/notes/{id}` - Delete note

### Tags
- `GET /api/tags` → `{"tags": ["tag1", "tag2", ...]}`

## 🎨 Markdown Support

Full support for:
- **Headings**: `# H1`, `## H2`, etc.
- **Lists**: Unordered (`-`, `*`) and ordered (`1.`)
- **Code**: Inline `` `code` `` and blocks with ` ``` `
- **Blockquotes**: `> Quote`
- **Links**: `[text](url)` and inline URLs
- **Images**: `![alt](url)`
- **Tables**: GitHub Flavored Markdown tables
- **Formatting**: Bold, italic, strikethrough, etc.

## 🌐 Deployment

### Building for Production
```bash
cd frontend
npm run build
```

This generates a static site in `frontend/dist/`.

### Environment Variables
Create a `.env` file (copy from `.env.example`):
```bash
# Optional: Change database location
# DATABASE_URL=sqlite:///./notebook.db
```

### Docker (Optional)
To containerize the app:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ src/
COPY frontend/dist/ static/
CMD ["uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🔒 Security

- **No authentication**: Single-user app (suitable for personal use)
- **Input validation**: Pydantic schemas validate all inputs
- **SQL injection protection**: SQLAlchemy ORM prevents SQL injection
- **XSS prevention**: React escapes by default; markdown is sanitized by react-markdown

## ⚙️ Configuration

### Backend
- Runs on `http://localhost:8000`
- Database: SQLite (local file)
- CORS enabled for frontend requests

### Frontend
- Runs on `http://localhost:5173` (Vite dev server)
- API proxy to `http://localhost:8000` (configured in vite.config.ts)
- TypeScript strict mode enabled

## 📝 Notes

- **Single device**: No real-time sync across multiple devices
- **No export/import UI**: Use the SQLite database directly for backups
- **No rich-text editor**: Markdown text + preview is the UX
- **No mobile UI**: Designed for desktop browsers

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Check database file isn't locked
rm notebook.db  # (will recreate on next start)
```

### Frontend won't start
```bash
# Clear node_modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Can't connect backend to frontend
- Ensure backend is running on `http://localhost:8000`
- Check Vite proxy in `frontend/vite.config.ts`
- Check browser console for network errors (F12)

## 📄 License

MIT

## 🙋 Author

Built with ❤️ for personal knowledge management.

---

**Happy note-taking! 📝**
