"""JSON-extraction helpers shared by every agent's response parser.

Each agent (Cat, Alice, Rabbit, Tweedles, Hatter, Caterpillar, Queen,
Dormouse, Dodo) has a structured response schema and a parse function
that pulls the LLM's JSON out of the raw text. Until v15 they all
shared the same pattern:

    1. Match a fenced ```json {...}``` block.
    2. If no fence, accept whole text only when it's `{...}`.
    3. Otherwise: raise "no JSON block found".

The third tier is too strict. Live Haiku 4.5 sometimes narrates before
the JSON ("Reading the contract carefully... {decision: ...}") or
appends commentary after. The narration-before-JSON pattern recurred
across the v10-v14 enchilada runs and burned multiple turns to
"no JSON block found" silences.

This module provides:

- ``balanced_json_objects(text)``: scan ``text`` for every brace-balanced
  ``{...}`` substring (string-aware so JSON values containing ``}``
  don't confuse the depth tracker).
- ``extract_and_validate(text, model, error_class)``: try fenced →
  bare-whole-text → embedded-balanced fallbacks against ``model`` and
  return the first one that validates. Raises ``error_class`` with a
  message describing the last failure if none parse.

Each agent's parser is a thin wrapper that fixes the model class and
error type. The fenced-block regex is exported here so individual
agents that want to keep their own parsers can use the same regex.
"""

from __future__ import annotations

import json
import re
from typing import TypeVar

from pydantic import BaseModel, ValidationError

JSON_FENCE_PATTERN: re.Pattern[str] = re.compile(
    r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL
)

_M = TypeVar("_M", bound=BaseModel)


def balanced_json_objects(text: str) -> list[str]:
    """Return every top-level brace-balanced ``{...}`` substring in
    ``text``, in order of appearance. Tracks string contents so a JSON
    value containing ``}`` doesn't terminate the search early."""
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] != "{":
            i += 1
            continue
        depth = 0
        j = i
        in_string = False
        escape = False
        while j < n:
            ch = text[j]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
            else:
                if ch == '"':
                    in_string = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        out.append(text[i : j + 1])
                        break
            j += 1
        if depth != 0:
            break
        i = j + 1
    return out


def extract_and_validate(
    text: str,
    model: type[_M],
    error_class: type[Exception],
) -> _M:
    """Extract JSON from ``text`` and validate against ``model``.

    Tries three strategies in order:
        1. A fenced ``` ```json{...}``` ``` block (the protocol's
           preferred shape).
        2. The whole stripped text if it starts with ``{`` and ends
           with ``}``.
        3. Every brace-balanced ``{...}`` substring; the first one
           that validates against ``model`` wins. This is the
           narration-before-JSON fallback — without it, an LLM that
           emits "Let me think... {...}" loses the turn entirely.

    Raises ``error_class`` with a message describing the failure mode
    if none of the candidates validate. The first candidate's error
    is preserved as ``__cause__`` so callers can inspect it.
    """
    candidates: list[str] = []
    fenced = JSON_FENCE_PATTERN.search(text)
    if fenced:
        candidates.append(fenced.group(1))
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        candidates.append(stripped)
    candidates.extend(balanced_json_objects(text))

    if not candidates:
        # Include a preview of the actual response so the failure mode
        # is diagnosable from the first occurrence — empty string
        # (max-iter exhaustion in the tools loop), pure prose (LLM
        # forgot the schema), truncation, etc.
        preview = (text[:200] if text else "<empty string>").replace("\n", " ")
        raise error_class(
            f"no JSON block found in {model.__name__} response "
            f"(len={len(text)} chars, preview: {preview!r})"
        )

    last_error: Exception | None = None
    for raw in candidates:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            last_error = exc
            continue
        try:
            return model.model_validate(data)
        except ValidationError as exc:
            last_error = exc
            continue

    if isinstance(last_error, ValidationError):
        raise error_class(
            f"{model.__name__} response failed schema validation: {last_error}"
        ) from last_error
    raise error_class(
        f"{model.__name__} response was not valid JSON: {last_error}"
    ) from last_error


__all__ = [
    "JSON_FENCE_PATTERN",
    "balanced_json_objects",
    "extract_and_validate",
]
