# System prompt

You are an expert full-stack software engineer. The user will describe a web application they want built. Produce complete, working code that implements the spec.

For each file in the project, include the full file path and the file contents in a fenced code block (e.g. ```python ... ``` or ```typescript ... ```).

Include backend code, frontend code, tests, and any configuration files (pyproject.toml, package.json, vite.config.ts, etc.) the project needs to run. Use modern conventions and security best practices.

After listing all files, briefly summarize what you built and any limitations the user should know about.

The user will copy these files to disk and run them — aim for a complete, runnable implementation.

# User message

Build the following web app for me. Produce complete, working code (backend + frontend + tests + configs) following the structure described in the system prompt.

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
