"""Identity — the operational self-model of an agent.

Per WONDERLAND_SPEC §5. An Identity bundles the constitution (the stable,
character-defining text) with the runtime hooks an agent needs to decide
what to listen to and when to engage. The constitution is invariant; the
interests and engagement_policy are tunable per-agent and may evolve.

The constitution loader reads `constitutions/<name>.md`, parses the small
metadata block at the top (display name, role, lineage/version, license,
optional pair), and returns an Identity ready to be paired with a memory
store and a Caucus subscription.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from wonderland.utterance import AgentIdentity, SpeechAct, Utterance


class AgentMemory(Protocol):
    """Forward-declared memory interface (substantive shape lands in T5)."""


EngagementPolicy = Callable[[Utterance, "AgentMemory | None"], bool]


def default_engagement_policy(interests: frozenset[SpeechAct]) -> EngagementPolicy:
    """Engage with any utterance whose speech_act is in the agent's interests."""

    def _policy(u: Utterance, _memory: AgentMemory | None = None) -> bool:
        return u.speech_act in interests

    return _policy


@dataclass(frozen=True)
class ConstitutionHeader:
    display_name: str
    role: str
    lineage: str
    version: str
    license: str
    pair: str | None = None


@dataclass(frozen=True)
class Identity:
    name: str
    header: ConstitutionHeader
    constitution_text: str
    interests: frozenset[SpeechAct] = field(default_factory=lambda: frozenset(SpeechAct))
    engagement_policy: EngagementPolicy | None = None

    def as_agent_identity(self) -> AgentIdentity:
        return AgentIdentity(name=self.name, constitution_version=self.header.version)

    def should_engage(self, u: Utterance, memory: AgentMemory | None = None) -> bool:
        policy = self.engagement_policy or default_engagement_policy(self.interests)
        return policy(u, memory)


class ConstitutionParseError(ValueError):
    """The file at the given path is not a valid character constitution."""


_HEADER_KV = re.compile(r"^\*\*([A-Z][A-Za-z ]*?):\*\*\s+(.+?)\s*$")
_LINEAGE_VERSION = re.compile(r"v([\d.]+)\s*$")


def parse_constitution_header(text: str) -> ConstitutionHeader:
    """Parse the H1 + key/value lines preceding the first `---` separator."""
    display_name: str | None = None
    fields: dict[str, str] = {}

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line == "---":
            break
        if line.startswith("# "):
            display_name = line[2:].strip()
            continue
        m = _HEADER_KV.match(line)
        if m:
            key, value = m.group(1).strip().lower(), m.group(2).strip()
            fields[key] = value

    if display_name is None:
        raise ConstitutionParseError("missing H1 display name")
    if "role" not in fields:
        raise ConstitutionParseError(
            "missing **Role:** — file appears not to be a character constitution"
        )
    if "lineage" not in fields:
        raise ConstitutionParseError("missing **Lineage:** line")
    if "license" not in fields:
        raise ConstitutionParseError("missing **License:** line")

    version_match = _LINEAGE_VERSION.search(fields["lineage"])
    if not version_match:
        raise ConstitutionParseError(
            f"could not extract version from lineage: {fields['lineage']!r}"
        )

    return ConstitutionHeader(
        display_name=display_name,
        role=fields["role"],
        lineage=fields["lineage"],
        version=version_match.group(1),
        license=fields["license"],
        pair=fields.get("pair"),
    )


def _default_constitutions_root() -> Path:
    # Dev-mode: resolve relative to this module's location in the repo.
    # When the package is installed without the constitutions/ tree alongside,
    # callers should pass `root` explicitly.
    return Path(__file__).resolve().parent.parent.parent / "constitutions"


def load_constitution(name: str, *, root: Path | None = None) -> Identity:
    """Load `<root>/<name>.md` and return an Identity with default interests.

    `name` is the canonical (snake_case) agent name and matches the filename.
    `root` defaults to the wonderland-ai repo's constitutions/ directory.
    """
    root = root or _default_constitutions_root()
    path = root / f"{name}.md"
    if not path.is_file():
        raise FileNotFoundError(f"no constitution at {path}")
    text = path.read_text(encoding="utf-8")
    header = parse_constitution_header(text)
    return Identity(name=name, header=header, constitution_text=text)
