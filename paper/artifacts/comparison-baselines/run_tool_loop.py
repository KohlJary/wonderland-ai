#!/usr/bin/env python3
"""Run a tool-using agent-loop baseline against the notebook directive.

What this does:
    - Gives the model filesystem tools (write_file, read_file,
      list_files, run_bash) scoped to a workspace directory.
    - Loops: model emits text + tool calls; we execute tools;
      results return as user messages; model continues.
    - Stops when the model returns end_turn without tool calls,
      OR when budget/iteration caps are hit.
    - Captures the final artifact tree + full transcript + cost.

This is the "B baseline" against which Wonderland's substrate +
identity engineering claims its value-add. The previous
no-tools script (run_single_shot.py) is the "A baseline" —
the naive floor. This is the harder rebuttal: would a
tool-using single agent on the same model produce
shape-comparable output?

Usage:
    cd /home/jaryk/wonderland-ai
    uv run python paper/artifacts/comparison-baselines/run_tool_loop.py \
        --model claude-haiku-4-5-20251001 \
        --out paper/artifacts/comparison-baselines/haiku-tools-custom \
        --budget-usd 5.0 \
        --max-iterations 60
"""
from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

import anthropic
import yaml

# Pricing — see reference_haiku_pricing.md
PRICING = {
    "claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00, "cache_read": 0.10, "cache_write": 1.25},
    "claude-sonnet-4-6-20251001": {"input": 3.00, "output": 15.00, "cache_read": 0.30, "cache_write": 3.75},
}

SYSTEM_PROMPT = """\
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

Don't waste turns. Plan, then execute efficiently."""


TOOLS = [
    {
        "name": "write_file",
        "description": "Write content to a file (creates or overwrites). Path is relative to the workspace root.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path from workspace root"},
                "content": {"type": "string", "description": "Full file contents"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "read_file",
        "description": "Read the contents of an existing file. Path relative to workspace root.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "list_files",
        "description": "List files in a directory (relative to workspace root). Use '.' for workspace root.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path (relative); use '.' for workspace root"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "run_bash",
        "description": "Execute a bash command from the workspace root. Use for npm install, uv run pytest, etc. Output is truncated at 4000 chars.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The bash command to execute"},
            },
            "required": ["command"],
        },
    },
]


DANGEROUS_PATTERNS = ["rm -rf /", "rm -rf ~", ":(){:|:&};:", "mkfs", "dd if=/dev/zero", "> /dev/sda"]


def safe_path(workspace: Path, requested: str) -> Path:
    """Resolve a path relative to workspace and refuse escapes."""
    p = (workspace / requested).resolve()
    if not str(p).startswith(str(workspace.resolve())):
        raise ValueError(f"path escapes workspace: {requested}")
    return p


def exec_tool(name: str, args: dict, workspace: Path) -> str:
    """Execute one tool call. Return the result string."""
    try:
        if name == "write_file":
            path = safe_path(workspace, args["path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(args["content"], encoding="utf-8")
            return f"wrote {len(args['content'])} chars to {args['path']}"
        elif name == "read_file":
            path = safe_path(workspace, args["path"])
            if not path.exists():
                return f"ERROR: file not found: {args['path']}"
            text = path.read_text(encoding="utf-8")
            # Cap returned content
            if len(text) > 8000:
                return text[:8000] + f"\n\n[truncated, {len(text)} chars total]"
            return text
        elif name == "list_files":
            path = safe_path(workspace, args["path"])
            if not path.exists():
                return f"ERROR: directory not found: {args['path']}"
            if not path.is_dir():
                return f"ERROR: not a directory: {args['path']}"
            entries = sorted(p.name + ("/" if p.is_dir() else "") for p in path.iterdir())
            return "\n".join(entries) if entries else "(empty)"
        elif name == "run_bash":
            cmd = args["command"]
            for pat in DANGEROUS_PATTERNS:
                if pat in cmd:
                    return f"ERROR: blocked dangerous pattern: {pat}"
            # Run in workspace, capture output, cap to 4000 chars, 60s timeout
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    cwd=workspace,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                output = (result.stdout or "") + (result.stderr or "")
                if len(output) > 4000:
                    output = output[:4000] + f"\n\n[truncated, {len(output)} chars total]"
                return f"exit_code={result.returncode}\n{output}"
            except subprocess.TimeoutExpired:
                return f"ERROR: command timed out after 60s: {cmd[:200]}"
        else:
            return f"ERROR: unknown tool: {name}"
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


def load_api_key() -> str:
    cfg = Path.home() / ".config" / "wonderland" / "config.json"
    return json.loads(cfg.read_text())["anthropic"]["api_key"]


def load_directive(repo_root: Path, name: str = "notebook") -> tuple[str, dict]:
    path = repo_root / "src" / "wonderland" / "closet" / "directives" / f"{name}.yaml"
    data = yaml.safe_load(path.read_text())
    return data.get("body", "").strip(), data


def compute_cost(model: str, usage) -> float:
    prices = PRICING.get(model)
    if not prices:
        return 0.0
    return (
        usage.input_tokens * prices["input"] / 1_000_000
        + getattr(usage, "cache_read_input_tokens", 0) * prices["cache_read"] / 1_000_000
        + getattr(usage, "cache_creation_input_tokens", 0) * prices["cache_write"] / 1_000_000
        + usage.output_tokens * prices["output"] / 1_000_000
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--max-tokens", type=int, default=4096, help="max output tokens per turn")
    parser.add_argument("--budget-usd", type=float, default=5.0, help="cumulative cost cap")
    parser.add_argument("--max-iterations", type=int, default=60, help="max model turns")
    parser.add_argument("--directive", default="notebook", help="directive name in src/wonderland/closet/directives/ (sans .yaml)")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[3]
    out_dir = Path(args.out).resolve()
    workspace = out_dir / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    api_key = load_api_key()
    directive_body, directive_meta = load_directive(repo_root, args.directive)

    user_message = (
        "Build the following web app. Implement it by writing files to the workspace, "
        "running tests, and verifying it works. Make reasonable engineering decisions; don't ask clarifying questions.\n\n"
        f"---\n\n{directive_body}"
    )

    # Save the prompt for reproducibility
    (out_dir / "prompt.md").write_text(
        f"# System prompt\n\n{SYSTEM_PROMPT}\n\n# User message\n\n{user_message}\n",
        encoding="utf-8",
    )

    client = anthropic.Anthropic(api_key=api_key)
    messages: list[dict] = [{"role": "user", "content": user_message}]
    transcript: list[dict] = []
    total_cost = 0.0
    iterations = 0
    t0 = time.time()
    stop_reason = None
    stop_detail = None

    while True:
        iterations += 1
        if iterations > args.max_iterations:
            stop_reason = "iteration_cap"
            stop_detail = f"hit max_iterations={args.max_iterations}"
            break
        if total_cost > args.budget_usd:
            stop_reason = "budget_cap"
            stop_detail = f"cumulative cost ${total_cost:.4f} exceeded budget ${args.budget_usd}"
            break

        print(f"\n=== turn {iterations} (cost so far: ${total_cost:.4f}) ===", flush=True)
        try:
            response = client.messages.create(
                model=args.model,
                max_tokens=args.max_tokens,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )
        except anthropic.APIError as e:
            stop_reason = "api_error"
            stop_detail = f"{type(e).__name__}: {e}"
            print(f"API error: {stop_detail}")
            break

        call_cost = compute_cost(args.model, response.usage)
        total_cost += call_cost
        transcript.append({
            "turn": iterations,
            "stop_reason": response.stop_reason,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "cache_read_input_tokens": getattr(response.usage, "cache_read_input_tokens", 0),
                "cache_creation_input_tokens": getattr(response.usage, "cache_creation_input_tokens", 0),
            },
            "cost_usd": round(call_cost, 6),
            "content": [
                {"type": b.type, **({"text": b.text} if hasattr(b, "text") else {"name": b.name, "input": b.input, "id": b.id})}
                for b in response.content
            ],
        })

        # Print a short summary of this turn
        text_blocks = [b.text for b in response.content if b.type == "text"]
        tool_blocks = [b for b in response.content if b.type == "tool_use"]
        if text_blocks:
            preview = text_blocks[0].strip()[:200].replace("\n", " ")
            print(f"  text: {preview}{'...' if len(text_blocks[0]) > 200 else ''}")
        for tb in tool_blocks:
            args_preview = json.dumps(tb.input)[:120].replace("\n", " ")
            print(f"  tool: {tb.name}({args_preview}{'...' if len(args_preview) >= 120 else ''})")
        print(f"  stop_reason: {response.stop_reason} | cost: ${call_cost:.4f}")

        # Add assistant message to conversation
        messages.append({"role": "assistant", "content": response.content})

        # If no tool calls, we're done (or model gave up)
        if response.stop_reason != "tool_use":
            stop_reason = response.stop_reason
            stop_detail = f"model stop_reason={response.stop_reason}"
            break

        # Execute tool calls + build user message with tool_result blocks
        tool_results = []
        for tool_call in tool_blocks:
            result = exec_tool(tool_call.name, tool_call.input, workspace)
            print(f"    -> result: {result[:120].replace(chr(10), ' ')}{'...' if len(result) > 120 else ''}")
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_call.id,
                "content": result,
            })
        messages.append({"role": "user", "content": tool_results})

    elapsed = time.time() - t0

    # Collect workspace inventory
    workspace_files = []
    for p in sorted(workspace.rglob("*")):
        if p.is_file() and not any(part.startswith(".") for part in p.relative_to(workspace).parts):
            if "node_modules" in p.parts or ".venv" in p.parts or "__pycache__" in p.parts or "dist" in p.parts:
                continue
            rel = str(p.relative_to(workspace))
            workspace_files.append({"path": rel, "size": p.stat().st_size, "lines": len(p.read_text(encoding="utf-8", errors="replace").splitlines())})

    metadata = {
        "model": args.model,
        "stop_reason": stop_reason,
        "stop_detail": stop_detail,
        "elapsed_seconds": round(elapsed, 2),
        "iterations": iterations,
        "total_cost_usd": round(total_cost, 6),
        "budget_usd": args.budget_usd,
        "max_iterations": args.max_iterations,
        "max_tokens_per_turn": args.max_tokens,
        "directive": {
            "name": directive_meta.get("name"),
            "title": directive_meta.get("title"),
            "suggested_skeleton": directive_meta.get("suggested_skeleton"),
        },
        "workspace_files_count": len(workspace_files),
        "workspace_files_total_lines": sum(f["lines"] for f in workspace_files),
        "workspace_files": workspace_files,
    }

    (out_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    (out_dir / "transcript.json").write_text(json.dumps(transcript, indent=2) + "\n", encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"STOPPED: {stop_reason} ({stop_detail})")
    print(f"  iterations         : {iterations}")
    print(f"  elapsed            : {elapsed:.1f}s")
    print(f"  total cost         : ${total_cost:.4f}")
    print(f"  workspace files    : {len(workspace_files)}")
    print(f"  workspace total LOC: {sum(f['lines'] for f in workspace_files):,}")
    print(f"  -> {out_dir}/metadata.json")
    print(f"  -> {out_dir}/transcript.json")
    print(f"  -> {workspace}/ (the artifact)")


if __name__ == "__main__":
    main()
