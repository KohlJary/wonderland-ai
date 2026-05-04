"""Wonderland — an identity-native multi-agent development system."""

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
    "PROCEDURAL_ACTS",
    "SUBSTANTIVE_ACTS",
    "AffectVector",
    "AgentIdentity",
    "Artifact",
    "SpeechAct",
    "Stance",
    "Utterance",
    "UtteranceContent",
    "__version__",
    "is_procedural",
    "is_substantive",
]
