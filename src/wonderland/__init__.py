"""Wonderland — an identity-native multi-agent development system."""

from wonderland.caucus import (
    DEFAULT_STREAM,
    Caucus,
    InMemoryCaucus,
    RedisCaucus,
)
from wonderland.identity import (
    ConstitutionHeader,
    ConstitutionParseError,
    EngagementPolicy,
    Identity,
    default_engagement_policy,
    load_constitution,
    parse_constitution_header,
)
from wonderland.memory import EpisodicStore
from wonderland.utterance import (
    PROCEDURAL_ACTS,
    SUBSTANTIVE_ACTS,
    AffectVector,
    AgentIdentity,
    Artifact,
    SpeechAct,
    Stance,
    Utterance,
    UtteranceContent,
    is_procedural,
    is_substantive,
)

__version__ = "0.0.1"

__all__ = [
    "DEFAULT_STREAM",
    "PROCEDURAL_ACTS",
    "SUBSTANTIVE_ACTS",
    "AffectVector",
    "AgentIdentity",
    "Artifact",
    "Caucus",
    "ConstitutionHeader",
    "ConstitutionParseError",
    "EngagementPolicy",
    "EpisodicStore",
    "Identity",
    "InMemoryCaucus",
    "RedisCaucus",
    "SpeechAct",
    "Stance",
    "Utterance",
    "UtteranceContent",
    "__version__",
    "default_engagement_policy",
    "is_procedural",
    "is_substantive",
    "load_constitution",
    "parse_constitution_header",
]
