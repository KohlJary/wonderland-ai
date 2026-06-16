"""Structural build-tracker (P21) — Ophanic diagrams as a living map of
what's built vs pending, with durable slug-linkage between diagram nodes
and tickets/features.
"""

from wonderland.diagrams.models import (
    DEFAULT_LAYER,
    LAYER_DB,
    LAYER_UI,
    Diagram,
    DiagramNode,
)
from wonderland.diagrams.dedup import (
    DiagramDuplicate,
    consolidate_diagrams,
    find_duplicate_diagrams,
)
from wonderland.diagrams.registry import DIAGRAMS_DIRNAME, DiagramRegistry

__all__ = [
    "DiagramRegistry",
    "DIAGRAMS_DIRNAME",
    "Diagram",
    "DiagramNode",
    "LAYER_UI",
    "LAYER_DB",
    "DEFAULT_LAYER",
    "DiagramDuplicate",
    "find_duplicate_diagrams",
    "consolidate_diagrams",
]
