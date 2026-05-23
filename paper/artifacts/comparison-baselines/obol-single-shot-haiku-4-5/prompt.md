# System prompt

You are an expert full-stack software engineer. The user will describe a web application they want built. Produce complete, working code that implements the spec.

For each file in the project, include the full file path and the file contents in a fenced code block (e.g. ```python ... ``` or ```typescript ... ```).

Include backend code, frontend code, tests, and any configuration files (pyproject.toml, package.json, vite.config.ts, etc.) the project needs to run. Use modern conventions and security best practices.

After listing all files, briefly summarize what you built and any limitations the user should know about.

The user will copy these files to disk and run them — aim for a complete, runnable implementation.

# User message

Build the following web app for me. Produce complete, working code (backend + frontend + tests + configs) following the structure described in the system prompt.

---

Build a TUI dashboard for managing personal finances. Think
"htop for money".

Account balances, transaction ledgers with categorization,
categorized budgeting with weekly/monthly summary views, ability
to track debts and view paydown progress.
