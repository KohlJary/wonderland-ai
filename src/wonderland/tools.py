"""Tools — read/write/list/grep primitives the Tweedles can use to ship code.

Per the P6.T36 prep tool-integration decision (after analysis 014's
cross-meeting composition validated that the Tweedles ship Contract
Notes that imply real implementation work): give the Tweedles a small
sandbox of file primitives so their `implementation` artifacts are
backed by actual code on disk, not just markdown describing what would
ship.

Scope decisions (deliberately minimal — see analysis 014's tooling
follow-up):

- **read_file**, **write_file**, **list_files**, **grep**: covers
  shipping basic code. The Tweedles need to know what's there
  (list/grep) before writing more (read/write).
- **No run_command**: executing arbitrary code is a separate trust
  boundary. Defer until a showcase explicitly needs it.

Path safety: every operation resolves the requested path relative to
``project_root`` and rejects anything that escapes (``..`` symlinks,
absolute paths outside the root, etc.). The Tweedles can't reach
outside their project sandbox even if the LLM tries — the sandbox is
the trust boundary, the Tweedles are inside it.

Anthropic tool-use schema lives next to the implementations so adding
a new tool is one place to edit. ``Tools.tool_definitions()`` returns
the list to pass as ``tools=[...]`` to ``messages.create``.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Hard cap on file size to avoid pulling massive blobs into the LLM context.
# Most source files are well under this; binaries or large assets get truncated
# with a clear marker so the LLM can decide what to do.
MAX_READ_BYTES = 64 * 1024  # 64 KiB

# Hard cap on the number of grep results to avoid context-flood.
MAX_GREP_HITS = 100

# Hard cap on the number of list_files results.
MAX_LIST_ENTRIES = 200


@dataclass(frozen=True)
class ToolError(Exception):
    """Tool execution failed (sandbox violation, missing path, encoding error).

    Raised so the Tweedle's tool-use loop can convert the error into a
    structured tool_result with ``is_error=True`` for the LLM to read
    and recover from.
    """

    message: str

    def __str__(self) -> str:
        return self.message


class Tools:
    """File primitives sandboxed to a project root.

    Construct once per Runner. Pass to the Tweedles' constructor; their
    ``deliberate()`` method runs the tool-use loop with these tools
    available.
    """

    def __init__(self, project_root: Path) -> None:
        self._root = project_root.resolve()

    @property
    def project_root(self) -> Path:
        return self._root

    # ------------------------------------------------------------------ #
    # Path safety
    # ------------------------------------------------------------------ #

    def _resolve(self, requested: str) -> Path:
        """Resolve a path string relative to project_root; reject escapes.

        ``requested`` may be a relative path (interpreted from
        project_root) or an absolute path (must be inside project_root).
        Symlink resolution happens here so an in-tree symlink pointing
        out of the tree gets caught.
        """
        path = (
            (self._root / requested).resolve()
            if not Path(requested).is_absolute()
            else Path(requested).resolve()
        )
        # Use is_relative_to (Python 3.9+) for the sandbox check.
        if not path.is_relative_to(self._root):
            raise ToolError(f"path {requested!r} escapes project root {self._root}")
        return path

    # ------------------------------------------------------------------ #
    # Operations
    # ------------------------------------------------------------------ #

    def read_file(self, path: str) -> str:
        """Read a UTF-8 text file and return its contents.

        Files larger than ``MAX_READ_BYTES`` are truncated with a
        trailing ``[truncated: N more bytes]`` marker so the LLM can
        decide whether to ask for a different range. Binary files
        (UTF-8 decode errors) raise ToolError so the LLM doesn't try
        to reason about garbage.
        """
        full = self._resolve(path)
        if not full.exists():
            raise ToolError(f"file not found: {path}")
        if not full.is_file():
            raise ToolError(f"not a file: {path}")
        try:
            data = full.read_bytes()
        except OSError as exc:
            raise ToolError(f"read failed for {path}: {exc}") from exc
        truncated = len(data) > MAX_READ_BYTES
        if truncated:
            data = data[:MAX_READ_BYTES]
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ToolError(f"file {path} is not valid UTF-8 (cannot read as text): {exc}") from exc
        if truncated:
            remaining = full.stat().st_size - MAX_READ_BYTES
            text += f"\n\n[truncated: {remaining} more bytes]"
        return text

    def write_file(self, path: str, content: str) -> str:
        """Write content to a file (creating parent directories as needed).

        Overwrites existing files. Returns a short acknowledgement so
        the LLM gets a useful tool_result.
        """
        full = self._resolve(path)
        if full.is_dir():
            raise ToolError(f"path is a directory, not a file: {path}")
        try:
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(content, encoding="utf-8")
        except OSError as exc:
            raise ToolError(f"write failed for {path}: {exc}") from exc
        return f"wrote {len(content)} chars to {path}"

    def list_files(self, directory: str = ".", pattern: str | None = None) -> str:
        """List files under ``directory``, optionally matching a glob ``pattern``.

        Recursive when ``pattern`` is supplied (uses Pathlib's rglob);
        flat directory listing when ``pattern`` is None. Results are
        capped at ``MAX_LIST_ENTRIES`` with a trailing marker if more
        exist. Returns one path per line, sorted, relative to
        project_root for portability.
        """
        full = self._resolve(directory)
        if not full.exists():
            raise ToolError(f"directory not found: {directory}")
        if not full.is_dir():
            raise ToolError(f"not a directory: {directory}")
        try:
            if pattern is None:
                entries = sorted(full.iterdir())
            else:
                entries = sorted(full.rglob(pattern))
        except OSError as exc:
            raise ToolError(f"list failed for {directory}: {exc}") from exc

        # Filter to in-sandbox paths (rglob can follow weird symlinks).
        in_sandbox = [p for p in entries if p.resolve().is_relative_to(self._root)]

        truncated = len(in_sandbox) > MAX_LIST_ENTRIES
        if truncated:
            in_sandbox = in_sandbox[:MAX_LIST_ENTRIES]

        rendered = [str(p.relative_to(self._root)) for p in in_sandbox]
        if not rendered:
            return "(no entries)"
        result = "\n".join(rendered)
        if truncated:
            result += f"\n[truncated: {len(entries) - MAX_LIST_ENTRIES} more entries]"
        return result

    def grep(self, pattern: str, path: str = ".", ignore_case: bool = False) -> str:
        """Search for ``pattern`` (regex) in files under ``path``.

        Returns matched lines as ``relative/path:line_number:matched_text``,
        capped at ``MAX_GREP_HITS``. Skips files that aren't valid
        UTF-8. ``path`` may be a single file or a directory (recursive).
        """
        full = self._resolve(path)
        try:
            regex = re.compile(pattern, re.IGNORECASE if ignore_case else 0)
        except re.error as exc:
            raise ToolError(f"invalid regex {pattern!r}: {exc}") from exc

        if not full.exists():
            raise ToolError(f"path not found: {path}")

        candidates: list[Path]
        if full.is_file():
            candidates = [full]
        elif full.is_dir():
            candidates = [p for p in full.rglob("*") if p.is_file()]
        else:
            raise ToolError(f"path is neither file nor directory: {path}")

        hits: list[str] = []
        for fpath in sorted(candidates):
            if not fpath.resolve().is_relative_to(self._root):
                continue
            try:
                with fpath.open(encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        if regex.search(line):
                            rel = fpath.relative_to(self._root)
                            hits.append(f"{rel}:{line_num}:{line.rstrip()}")
                            if len(hits) >= MAX_GREP_HITS:
                                break
            except UnicodeDecodeError:
                # Binary or non-UTF-8 file; skip silently. The LLM
                # gets the hits from text files, doesn't need to
                # know about binaries.
                continue
            except OSError:
                continue
            if len(hits) >= MAX_GREP_HITS:
                break

        if not hits:
            return f"(no matches for {pattern!r})"
        truncated = len(hits) >= MAX_GREP_HITS
        result = "\n".join(hits)
        if truncated:
            result += f"\n[truncated at {MAX_GREP_HITS} hits]"
        return result

    # ------------------------------------------------------------------ #
    # Git operations — the working tree IS the implementation artifact;
    # reviewers read git_diff to find what shipped.
    # ------------------------------------------------------------------ #

    def _run_git(self, args: list[str]) -> str:
        """Run ``git <args>`` in project_root. Returns stdout; raises
        ToolError if git isn't installed, the project isn't a repo, or
        the command failed. Output is capped at MAX_READ_BYTES so a
        diff against a large change doesn't flood the LLM context."""
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=self._root,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
        except FileNotFoundError as exc:
            raise ToolError(
                "git is not installed in this environment — "
                "git_status / git_diff are unavailable"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise ToolError(f"git {' '.join(args)} timed out after 10s") from exc
        if result.returncode != 0:
            stderr = result.stderr.strip() or "(no stderr)"
            if "not a git repository" in stderr.lower():
                raise ToolError(
                    f"project root {self._root} is not a git repository — "
                    "Runner.make_full_cast initializes one at setup; if you "
                    "see this, the project root was not set up via the Runner"
                )
            raise ToolError(f"git {' '.join(args)} failed: {stderr}")
        out = result.stdout
        if len(out.encode("utf-8")) > MAX_READ_BYTES:
            truncated = out[:MAX_READ_BYTES]
            return truncated + f"\n\n[truncated: output exceeded {MAX_READ_BYTES} bytes]"
        return out

    def git_status(self) -> str:
        """Show the working-tree state — files modified, added, deleted,
        or untracked since the last commit. Use this to find what work
        the meeting has produced before diving into specific files."""
        out = self._run_git(["status", "--porcelain=v1"])
        if not out.strip():
            return "(working tree clean — no changes since last commit)"
        return out

    def git_diff(self, path: str | None = None) -> str:
        """Show the diff of working-tree changes against HEAD.

        With no path, shows the full diff (all modified + added files).
        With a path, shows the diff for just that file (relative to
        project root). Includes untracked files via ``--no-index``
        diff against /dev/null when needed.

        Output is capped at MAX_READ_BYTES; use git_status first if
        the diff might be large, then narrow with a path."""
        # `git diff HEAD` shows tracked-file changes; for untracked
        # files we add them to the diff manually via diff --no-index.
        # The simplest path: stage everything to a virtual index, then
        # diff against HEAD. We use `git add -N` (intent-to-add) which
        # doesn't actually stage content but lets diff see new files.
        try:
            subprocess.run(
                ["git", "add", "-N", "."],
                cwd=self._root,
                capture_output=True,
                check=False,
                timeout=10,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # _run_git below will produce the proper error; don't
            # double-handle here.
            pass
        args = ["diff", "HEAD"]
        if path is not None:
            # Resolve path safely; reject escapes.
            self._resolve(path)  # raises ToolError on escape
            args.extend(["--", path])
        out = self._run_git(args)
        if not out.strip():
            return "(no diff — working tree matches HEAD)"
        return out

    # ------------------------------------------------------------------ #
    # Tool-use schema for Anthropic's API
    # ------------------------------------------------------------------ #

    @staticmethod
    def tool_definitions() -> list[dict[str, Any]]:
        """The Anthropic tool-use schema for these tools.

        Pass as ``tools=[...]`` to ``messages.create``. The LLM can
        request these by name; the Tweedle's deliberate() loop
        executes them and feeds the results back.
        """
        return [
            {
                "name": "read_file",
                "description": (
                    "Read the contents of a text file relative to the project "
                    "root. Returns UTF-8 text. Files larger than 64 KiB are "
                    "truncated with a trailing marker. Use this to inspect "
                    "existing code before editing it."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path relative to the project root.",
                        },
                    },
                    "required": ["path"],
                },
            },
            {
                "name": "write_file",
                "description": (
                    "Write content to a text file (overwriting if it exists, "
                    "creating parent directories as needed). Use this to "
                    "ship code as part of an `implementation` artifact. The "
                    "file path you write should match a `files_touched` "
                    "entry in the implementation you're shipping."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path relative to the project root.",
                        },
                        "content": {
                            "type": "string",
                            "description": "Full file content to write.",
                        },
                    },
                    "required": ["path", "content"],
                },
            },
            {
                "name": "list_files",
                "description": (
                    "List files in a directory, optionally matching a glob "
                    "pattern (recursive when a pattern is supplied). Use this "
                    "to discover existing code before adding new files."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "Directory path relative to the project root. Defaults to '.'.",
                        },
                        "pattern": {
                            "type": "string",
                            "description": "Optional glob pattern (e.g. '*.py'). When set, search is recursive.",
                        },
                    },
                    "required": [],
                },
            },
            {
                "name": "grep",
                "description": (
                    "Search for a regex pattern in files under a path "
                    "(recursive when path is a directory). Returns matched "
                    "lines as 'relative/path:line:text'. Use this to find "
                    "where something is defined or referenced before "
                    "deciding what to write."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Python regex pattern to search for.",
                        },
                        "path": {
                            "type": "string",
                            "description": "File or directory to search under. Defaults to '.'.",
                        },
                        "ignore_case": {
                            "type": "boolean",
                            "description": "Case-insensitive match. Defaults to false.",
                        },
                    },
                    "required": ["pattern"],
                },
            },
            {
                "name": "git_status",
                "description": (
                    "Show the working-tree state — files modified, added, "
                    "deleted, or untracked since the last commit. The "
                    "working tree IS the implementation artifact; this "
                    "tool tells you what work the meeting has produced. "
                    "Use it before reaching for git_diff so you know "
                    "which files to focus on."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
            {
                "name": "git_diff",
                "description": (
                    "Show the diff of working-tree changes against HEAD. "
                    "With no path, shows the full diff (all modified and "
                    "added files in unified format). With a path, shows "
                    "the diff for just that file. Reviewers read this to "
                    "find what shipped without consulting separate "
                    "metadata. If the diff would be large, call "
                    "git_status first and narrow with a path."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": (
                                "Optional path (relative to project root) "
                                "to scope the diff to a single file or "
                                "directory."
                            ),
                        },
                    },
                    "required": [],
                },
            },
        ]

    def execute(self, tool_name: str, tool_input: dict[str, Any]) -> str:
        """Dispatch a tool call by name. Raises ToolError on failure.

        The Tweedle's tool-use loop calls this for each tool_use block
        in the LLM's response, then packages the return value (or
        ToolError message) into a tool_result block for the next turn.
        """
        if tool_name == "read_file":
            return self.read_file(tool_input["path"])
        if tool_name == "write_file":
            return self.write_file(tool_input["path"], tool_input["content"])
        if tool_name == "list_files":
            return self.list_files(
                tool_input.get("directory", "."),
                tool_input.get("pattern"),
            )
        if tool_name == "grep":
            return self.grep(
                tool_input["pattern"],
                tool_input.get("path", "."),
                tool_input.get("ignore_case", False),
            )
        if tool_name == "git_status":
            return self.git_status()
        if tool_name == "git_diff":
            return self.git_diff(tool_input.get("path"))
        raise ToolError(f"unknown tool: {tool_name}")


__all__ = ["MAX_GREP_HITS", "MAX_LIST_ENTRIES", "MAX_READ_BYTES", "ToolError", "Tools"]
