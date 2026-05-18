# System prompt

You are an expert full-stack software engineer with access to filesystem and shell tools. The user will describe a web application they want built. Implement it by writing files to the working directory.

You have these tools:
- write_file(path, content) — create or overwrite a file. Use relative paths from the workspace root.
- read_file(path) — read an existing file's contents.
- list_files(path) — list files in a directory (relative to workspace root).
- run_bash(command) — execute a bash command from the workspace root (for `npm install`, `uv run pytest`, etc.).

The workspace is empty when you start. Create the project structure yourself (e.g. src/backend/main.py, frontend/src/App.tsx, tests/, configs).

Engineering expectations:
- Production-quality code following modern conventions.
- Write tests AND run them — don't ship code you haven't verified passes its own tests.
- Include all configuration files needed to run the project (pyproject.toml, package.json, vite.config.ts, etc.).
- Security best practices (input sanitization, XSS prevention, parameterized queries).

When you have finished building the app AND verified the tests pass + the frontend builds, return a brief summary of what you built and any limitations. Don't ask the user clarifying questions — make reasonable engineering decisions and ship.

Don't waste turns. Plan, then execute efficiently.

# User message

Build the following web app. Implement it by writing files to the workspace, running tests, and verifying it works. Make reasonable engineering decisions; don't ask clarifying questions.

---

Build a personal markdown notebook web app.

Single user, no authentication — the app loads ready to use.

Persona: a developer or researcher keeping a personal knowledge
base. They want to capture markdown notes, tag them for
organization, and find them later via search. Notes outlive
individual sessions; they persist across page reloads and across
server restarts.

Core capabilities:

  - Create a note with a title and a markdown body. Tags are
    optional, one or more per note.
  - Edit and delete existing notes.
  - List all notes, most-recently-edited first.
  - Render markdown to HTML in a preview pane next to the
    editor — code blocks, headers, lists, links, images,
    blockquotes all work.
  - Filter the note list by tag.
  - Search across note titles, bodies, and tags. Substring match
    is fine; the goal is finding a note you wrote last week, not
    academic full-text search.

Stack constraints:

  - Backend: Python + FastAPI + SQLite. SQLite as the persistence
    layer so the reader doesn't need to run a separate database.
  - Frontend: React + Vite + TypeScript. Client-side markdown
    rendering (pick a lightweight library: react-markdown,
    marked, or similar).
  - Skeleton: fullstack-fastapi-react. Dev runs as two processes
    (uvicorn + npm run dev) with Vite proxying API calls to the
    backend.

Non-goals (explicit out-of-scope):

  - No multi-user / authentication. The app is single-user.
  - No real-time collaboration. Single device.
  - No export/import beyond what SQLite gives you for free.
  - No rich-text editor — markdown text area + preview is the UX.
  - No mobile-specific UI; desktop browser is the target.

Success criteria: a developer can ``git clone``, follow the
README's "run the demo" steps, and have a working notebook in
their browser within five minutes. They can create a note, tag
it, find it via search, edit it, and see it persist after a
server restart.
