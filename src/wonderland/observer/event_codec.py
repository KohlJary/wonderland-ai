"""Serialize/deserialize ``RunEvent`` instances to/from JSONL lines.

Used by the detached-process plumbing: the background ``wonderland
run-bg`` subprocess writes one event per line to
``.wonderland/runs/<run_id>/events.jsonl``; the TUI's
``SubprocessRunHandle`` tails the file and reconstructs events.

Wire shape: one line of compact JSON per event.

    {"kind": "MeetingStarted", "data": {...}}

The kind tag is the dataclass class name. The data block carries the
field values, with type-specific encoding:

  - ``datetime`` → ISO-8601 string
  - ``Path`` → absolute path string
  - ``Utterance`` → pydantic ``model_dump`` (already JSON-safe)
  - nested dataclasses (RunSummary, RunMeeting, RunArtifact,
    AgentTelemetry) → field-by-field dict
  - tuple → list (round-tripped back to tuple on decode where the
    field type expects it, e.g. ``PhaseStarted.cast``)

Forward-compat: unknown kind strings during decode raise
``UnknownEventKind`` so callers can surface "this jsonl was written
by a newer wonderland version" cleanly.
"""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from wonderland.observer.events import (
    AgentActed,
    AgentPassed,
    AgentTelemetryDelta,
    ArtifactShipped,
    MeetingEnded,
    MeetingStarted,
    PhaseEnded,
    PhaseStarted,
    PriorityWindowOpened,
    RotationCompleted,
    RunEnded,
    RunStarted,
    UtteranceEmitted,
)
from wonderland.observer.interface import (
    AgentTelemetry,
    RunArtifact,
    RunMeeting,
    RunSummary,
)
from wonderland.utterance import Utterance


_EVENT_KINDS: dict[str, type] = {
    cls.__name__: cls
    for cls in (
        RunStarted,
        MeetingStarted,
        UtteranceEmitted,
        ArtifactShipped,
        AgentTelemetryDelta,
        MeetingEnded,
        RunEnded,
        PhaseStarted,
        PhaseEnded,
        PriorityWindowOpened,
        AgentActed,
        AgentPassed,
        RotationCompleted,
    )
}


# Dataclasses nested inside events that need recursive encoding.
# Names match observer.interface so the decoder can dispatch on them.
_NESTED_DATACLASS_FIELDS: dict[str, type] = {
    "RunSummary": RunSummary,
    "RunMeeting": RunMeeting,
    "RunArtifact": RunArtifact,
    "AgentTelemetry": AgentTelemetry,
}


class UnknownEventKind(ValueError):
    """Raised when ``from_jsonl`` sees a kind tag that doesn't map to
    any known event class. Surfaces forward-compat hazards (newer
    wonderland writing events the running TUI doesn't know about)."""


def _encode_value(value: Any) -> Any:
    """Recursively encode a value to a JSON-safe primitive."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Utterance):
        return value.model_dump(mode="json")
    if isinstance(value, (list, tuple)):
        return [_encode_value(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _encode_value(v) for k, v in value.items()}
    if is_dataclass(value):
        return {
            field.name: _encode_value(getattr(value, field.name))
            for field in fields(value)
        }
    raise TypeError(
        f"event_codec: cannot encode value of type {type(value).__name__}"
    )


def to_jsonl(event: Any) -> str:
    """Serialize a RunEvent to a single-line JSON string (no trailing
    newline — caller adds it when appending to the file)."""
    kind = type(event).__name__
    if kind not in _EVENT_KINDS:
        raise TypeError(
            f"event_codec: {kind} is not a known RunEvent type"
        )
    data = {
        field.name: _encode_value(getattr(event, field.name))
        for field in fields(event)
    }
    return json.dumps({"kind": kind, "data": data}, separators=(",", ":"))


def _decode_dataclass(cls: type, raw: dict[str, Any]) -> Any:
    """Reconstruct a dataclass instance from a primitive dict —
    coercing datetime / Path / nested dataclasses based on the
    field's declared type."""
    kwargs: dict[str, Any] = {}
    for field in fields(cls):
        if field.name not in raw:
            continue
        kwargs[field.name] = _decode_field(field.type, raw[field.name])
    return cls(**kwargs)


def _decode_field(field_type: Any, value: Any) -> Any:
    """Coerce ``value`` to match ``field_type``. Handles the small set
    of types we care about: datetime, Path, Utterance, the nested
    dataclasses, plus container types (tuple, list, dict)."""
    if value is None:
        return None
    type_str = (
        field_type if isinstance(field_type, str) else getattr(
            field_type, "__name__", str(field_type)
        )
    )

    # Optional / union types: peel off the optional layer and recurse.
    # (We don't fully parse Optional[X]; we look at the value shape.)

    if "datetime" in type_str:
        return datetime.fromisoformat(value)
    if type_str == "Path" or "Path" in type_str:
        # str|Path|None — keep None pass-through above; coerce str→Path.
        if isinstance(value, str):
            return Path(value)
        return value
    if "Utterance" in type_str:
        return Utterance.model_validate(value)
    for nested_name, nested_cls in _NESTED_DATACLASS_FIELDS.items():
        if nested_name in type_str:
            if isinstance(value, dict):
                return _decode_dataclass(nested_cls, value)
            return value
    if "tuple" in type_str.lower():
        # Tuples come back as lists from JSON; cast them.
        if isinstance(value, list):
            return tuple(value)
    # dict / list of primitives — pass through.
    return value


def from_jsonl(line: str) -> Any:
    """Reconstruct a RunEvent from a JSONL line. Raises
    UnknownEventKind for unrecognized kind tags."""
    parsed = json.loads(line)
    kind = parsed.get("kind")
    data = parsed.get("data") or {}
    cls = _EVENT_KINDS.get(kind)
    if cls is None:
        raise UnknownEventKind(
            f"unknown RunEvent kind {kind!r}"
        )
    return _decode_dataclass(cls, data)


__all__ = [
    "UnknownEventKind",
    "from_jsonl",
    "to_jsonl",
]
