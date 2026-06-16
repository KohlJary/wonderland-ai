"""Diagram + node IR for the structural build-tracker (P21).

A *diagram* is an Ophanic ``.oph`` layout document under
``.wonderland/diagrams/``. Its *nodes* are the linkable units of
structure — the components a diagram references or defines. Each node
carries a durable GUID (the slug-linkage identity, T-g pattern) so that
tickets/features can point at a node by GUID and survive renames of the
human-readable component name.

``layer`` keeps structural domains separated: ``ui`` for the front-end
component tree, ``db`` for schema structure, etc. The diagram diff (the
hollow-verify killer) compares like-for-like within a layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wonderland.diagrams._ophanic.models import OphanicDocument


# Known structural layers. Not an enum — projects may coin their own —
# but these are the first-class ones the substrate understands.
LAYER_UI = "ui"
LAYER_DB = "db"
DEFAULT_LAYER = LAYER_UI


@dataclass(frozen=True)
class DiagramNode:
    """A linkable unit of structure within a diagram.

    ``guid`` is the durable identity tickets/features link against.
    ``name`` is the mutable display label (the Ophanic component name).
    """

    guid: str
    name: str
    layer: str
    diagram_slug: str
    is_defined: bool = False  # True when the diagram has a ``## ◆Name`` def


@dataclass
class Diagram:
    """A parsed ``.oph`` diagram plus its extracted nodes."""

    guid: str
    slug: str
    layer: str
    path: Path
    title: str | None = None
    nodes: list[DiagramNode] = field(default_factory=list)
    document: "OphanicDocument | None" = None

    def node_by_name(self, name: str) -> DiagramNode | None:
        for n in self.nodes:
            if n.name == name:
                return n
        return None

    def node_by_guid(self, guid: str) -> DiagramNode | None:
        for n in self.nodes:
            if n.guid == guid:
                return n
        return None


__all__ = ["DiagramNode", "Diagram", "LAYER_UI", "LAYER_DB", "DEFAULT_LAYER"]
