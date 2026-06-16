"""Diagram registry over ``.wonderland/diagrams/`` (P21).

Stores Ophanic ``.oph`` diagrams and maintains a durable GUID index so a
node's identity survives renames of its human-readable component name —
the slug-linkage that lets tickets/features point at structure that
outlives the label. Diagram structure lives in the ``.oph`` file (source
of truth); ``index.json`` holds only identity + metadata (guids, layer,
title) keyed by slug, never the structure itself.
"""

from __future__ import annotations

import json
from pathlib import Path

from wonderland.adr import slugify
from wonderland.artifact_guid import new_artifact_guid
from wonderland.diagrams._ophanic import parse as parse_oph
from wonderland.diagrams._ophanic.models import LayoutNode, NodeType
from wonderland.diagrams.models import DEFAULT_LAYER, Diagram, DiagramNode

DIAGRAMS_DIRNAME = "diagrams"
_INDEX_NAME = "index.json"


def _iter_component_refs(node: LayoutNode):
    """Yield every COMPONENT_REF node in a layout tree (depth-first)."""
    if node.type == NodeType.COMPONENT_REF and node.name:
        yield node
    for child in node.children:
        yield from _iter_component_refs(child)


class DiagramRegistry:
    """Read/write registry over ``<project_root>/.wonderland/diagrams/``."""

    def __init__(self, project_root: Path) -> None:
        self._root = project_root / ".wonderland" / DIAGRAMS_DIRNAME
        self._index_path = self._root / _INDEX_NAME

    @property
    def path(self) -> Path:
        return self._root

    # ------------------------------------------------------------------ #
    # Index (durable identity: slug -> {guid, layer, title, nodes})
    # ------------------------------------------------------------------ #

    def _load_index(self) -> dict:
        if not self._index_path.is_file():
            return {"diagrams": {}}
        try:
            return json.loads(self._index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"diagrams": {}}

    def _save_index(self, index: dict) -> None:
        self._root.mkdir(parents=True, exist_ok=True)
        self._index_path.write_text(
            json.dumps(index, indent=2) + "\n", encoding="utf-8"
        )

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #

    def list_slugs(self) -> list[str]:
        if not self._root.is_dir():
            return []
        return sorted(p.stem for p in self._root.glob("*.oph"))

    def read(self, slug: str) -> Diagram | None:
        """Parse a diagram + resolve its nodes' durable GUIDs. Returns
        None when the ``.oph`` file is missing."""
        oph_path = self._root / f"{slug}.oph"
        if not oph_path.is_file():
            return None
        text = oph_path.read_text(encoding="utf-8")
        doc = parse_oph(text)

        index = self._load_index()
        entry = index["diagrams"].setdefault(
            slug,
            {"guid": new_artifact_guid(), "layer": DEFAULT_LAYER,
             "title": doc.title, "nodes": {}},
        )
        entry["title"] = doc.title
        node_guids: dict[str, str] = entry["nodes"]

        # Defined components (## ◆Name) + referenced components (◆Name),
        # including refs nested inside component-definition bodies (a
        # ## ◆Sidebar that references ◆NavLinks).
        defined = {c.name for c in doc.components}
        referenced: set[str] = set()
        for bp in doc.breakpoints:
            for ref in _iter_component_refs(bp.root):
                referenced.add(ref.name)  # type: ignore[arg-type]
        for comp in doc.components:
            for state_root in comp.states.values():
                for ref in _iter_component_refs(state_root):
                    referenced.add(ref.name)  # type: ignore[arg-type]

        names = sorted(defined | referenced)
        nodes: list[DiagramNode] = []
        dirty = False
        for name in names:
            if name not in node_guids:
                node_guids[name] = new_artifact_guid()
                dirty = True
            nodes.append(DiagramNode(
                guid=node_guids[name],
                name=name,
                layer=entry["layer"],
                diagram_slug=slug,
                is_defined=name in defined,
            ))
        # Prune index entries for components no longer present (keeps the
        # index honest, but only for this diagram's namespace).
        for stale in [n for n in node_guids if n not in names]:
            del node_guids[stale]
            dirty = True
        if dirty or slug not in self._load_index()["diagrams"]:
            self._save_index(index)

        return Diagram(
            guid=entry["guid"], slug=slug, layer=entry["layer"],
            path=oph_path, title=doc.title, nodes=nodes, document=doc,
        )

    def nodes(self, slug: str) -> list[DiagramNode]:
        diagram = self.read(slug)
        return diagram.nodes if diagram else []

    def all_nodes(self) -> list[DiagramNode]:
        out: list[DiagramNode] = []
        for slug in self.list_slugs():
            out.extend(self.nodes(slug))
        return out

    def find_node(self, guid: str) -> DiagramNode | None:
        for node in self.all_nodes():
            if node.guid == guid:
                return node
        return None

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #

    def write(
        self, name: str, oph_text: str, *,
        layer: str = DEFAULT_LAYER, slug: str | None = None,
    ) -> Diagram:
        """Create or overwrite a diagram by slug. Preserves the diagram +
        node GUIDs across rewrites (durable identity)."""
        slug = slug or slugify(name)
        self._root.mkdir(parents=True, exist_ok=True)
        (self._root / f"{slug}.oph").write_text(oph_text, encoding="utf-8")
        # Ensure the index entry exists with the requested layer before
        # read() resolves nodes.
        index = self._load_index()
        entry = index["diagrams"].setdefault(
            slug,
            {"guid": new_artifact_guid(), "layer": layer, "title": None,
             "nodes": {}},
        )
        entry["layer"] = layer
        self._save_index(index)
        diagram = self.read(slug)
        assert diagram is not None  # just wrote it
        return diagram

    def rename_node(self, guid: str, new_name: str) -> bool:
        """Rename a node's display label while preserving its GUID — the
        whole point of slug-linkage. Updates the index; the ``.oph`` body
        still carries the old label until the diagram is re-published, but
        links keyed on GUID are unaffected. Returns True if found."""
        index = self._load_index()
        for entry in index["diagrams"].values():
            node_guids = entry["nodes"]
            for name, ng in list(node_guids.items()):
                if ng == guid:
                    del node_guids[name]
                    node_guids[new_name] = guid
                    self._save_index(index)
                    return True
        return False


__all__ = ["DiagramRegistry", "DIAGRAMS_DIRNAME"]
