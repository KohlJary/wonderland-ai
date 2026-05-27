#!/usr/bin/env python3
"""Run a single-shot baseline against the notebook directive.

What this does:
    - Loads the API key from ~/.config/wonderland/config.json.
    - Reads the notebook directive's body from
      src/wonderland/closet/directives/notebook.yaml.
    - Sends one inference call to the specified model, with a
      minimal system prompt and the directive as the user message.
    - Captures the full response + token usage + timing.
    - Writes output.md, prompt.md, metadata.json to the target
      directory.

Usage:
    cd /home/jaryk/wonderland-ai
    uv run python paper/artifacts/comparison-baselines/run_single_shot.py \
        --model claude-haiku-4-5-20251001 \
        --out paper/artifacts/comparison-baselines/single-shot-haiku-4-5

The system prompt is intentionally MINIMAL — close to what a
non-Wonderland user opening Claude.ai would naturally encounter.
This is the baseline against which Wonderland's substrate + identity
engineering claims its value-add.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import anthropic
import yaml

# Pricing per /home/jaryk/.claude/projects/-home-jaryk-wonderland-ai/memory/reference_haiku_pricing.md
# Updated 2026-05-05 from https://platform.claude.com/docs/en/docs/about-claude/pricing
PRICING = {
    "claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00, "cache_read": 0.10, "cache_write": 1.25},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00, "cache_read": 0.30, "cache_write": 3.75},
    "claude-sonnet-4-6-20251001": {"input": 3.00, "output": 15.00, "cache_read": 0.30, "cache_write": 3.75},
    "claude-opus-4-7": {"input": 15.00, "output": 75.00, "cache_read": 1.50, "cache_write": 18.75},
    "claude-opus-4-7-20251001": {"input": 15.00, "output": 75.00, "cache_read": 1.50, "cache_write": 18.75},
}

SYSTEM_PROMPT = """\
You are an expert full-stack software engineer. The user will describe a web application they want built. Produce complete, working code that implements the spec.

For each file in the project, include the full file path and the file contents in a fenced code block (e.g. ```python ... ``` or ```typescript ... ```).

Include backend code, frontend code, tests, and any configuration files (pyproject.toml, package.json, vite.config.ts, etc.) the project needs to run. Use modern conventions and security best practices.

After listing all files, briefly summarize what you built and any limitations the user should know about.

The user will copy these files to disk and run them — aim for a complete, runnable implementation."""


def load_api_key() -> str:
    cfg = Path.home() / ".config" / "wonderland" / "config.json"
    if not cfg.exists():
        sys.exit(f"config not found: {cfg}")
    data = json.loads(cfg.read_text())
    key = data.get("anthropic", {}).get("api_key")
    if not key:
        sys.exit(f"no anthropic.api_key in {cfg}")
    return key


def load_directive(repo_root: Path, name: str = "notebook") -> tuple[str, dict]:
    path = repo_root / "src" / "wonderland" / "closet" / "directives" / f"{name}.yaml"
    if not path.exists():
        sys.exit(f"directive not found: {path}")
    data = yaml.safe_load(path.read_text())
    body = data.get("body", "").strip()
    if not body:
        sys.exit(f"directive body empty: {path}")
    return body, data


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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="e.g. claude-haiku-4-5-20251001")
    parser.add_argument("--out", required=True, help="output directory")
    parser.add_argument("--max-tokens", type=int, default=8192, help="max output tokens (default 8192)")
    parser.add_argument("--directive", default="notebook", help="directive name in src/wonderland/closet/directives/ (sans .yaml)")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[3]
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    api_key = load_api_key()
    directive_body, directive_meta = load_directive(repo_root, args.directive)

    user_message = (
        "Build the following web app for me. Produce complete, working code "
        "(backend + frontend + tests + configs) following the structure "
        "described in the system prompt.\n\n"
        f"---\n\n{directive_body}"
    )

    # Save the exact prompt for reproducibility
    (out_dir / "prompt.md").write_text(
        f"# System prompt\n\n{SYSTEM_PROMPT}\n\n"
        f"# User message\n\n{user_message}\n",
        encoding="utf-8",
    )

    print(f"Calling {args.model} with max_tokens={args.max_tokens}...", flush=True)
    client = anthropic.Anthropic(api_key=api_key)
    t0 = time.time()
    response = client.messages.create(
        model=args.model,
        max_tokens=args.max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    elapsed = time.time() - t0

    # Concatenate text blocks (Haiku/Sonnet/Opus typically return a single text block)
    output_text = "".join(b.text for b in response.content if hasattr(b, "text"))

    cost = compute_cost(args.model, response.usage)
    metadata = {
        "model": args.model,
        "stop_reason": response.stop_reason,
        "elapsed_seconds": round(elapsed, 2),
        "directive": {
            "name": directive_meta.get("name"),
            "title": directive_meta.get("title"),
            "suggested_skeleton": directive_meta.get("suggested_skeleton"),
        },
        "usage": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "cache_read_input_tokens": getattr(response.usage, "cache_read_input_tokens", 0),
            "cache_creation_input_tokens": getattr(response.usage, "cache_creation_input_tokens", 0),
        },
        "cost_usd": round(cost, 6),
        "max_tokens_requested": args.max_tokens,
        "system_prompt_chars": len(SYSTEM_PROMPT),
        "user_message_chars": len(user_message),
        "output_chars": len(output_text),
    }

    (out_dir / "output.md").write_text(output_text, encoding="utf-8")
    (out_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )

    # Console summary
    print()
    print(f"  stop_reason       : {response.stop_reason}")
    print(f"  elapsed           : {elapsed:.1f}s")
    print(f"  input_tokens      : {response.usage.input_tokens:,}")
    print(f"  output_tokens     : {response.usage.output_tokens:,}")
    print(f"  output_chars      : {len(output_text):,}")
    print(f"  cost              : ${cost:.4f}")
    print(f"  -> {out_dir}/output.md")
    print(f"  -> {out_dir}/metadata.json")


if __name__ == "__main__":
    main()
