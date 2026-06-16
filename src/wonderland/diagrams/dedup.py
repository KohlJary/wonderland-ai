"""Diagram dedup by node-set signature (P21).

Two same-layer diagrams that depict the same surface — Rabbit and Alice
both drawing the dashboard under slightly different slugs (``dashboard``
vs ``dashboard-page``) — are the diagram analog of the cross-author
ticket duplication that surface signatures already kill at design time.
The signature here is the diagram's *node set* (the components it
contains), harvested from raw ``◆`` tokens in the registry so malformed
boxes don't hide it.

Conservative by construction. We only consolidate when the smaller
diagram's components are largely SUBSUMED by the larger one
(containment), and only when at least two *content* components are
shared — a lone shared ``Navbar`` across two otherwise-distinct pages
must not trigger a merge. Title overlap is deliberately NOT a signal
(the lesson from ticket dedup: lexical title similarity false-merges).
Differing naming conventions (``Users`` vs ``UsersTable``) defeat the
signature; that is an accepted false-negative. A missed merge costs a
redundant diagram on disk — a wrong merge destroys a real surface.
"""

from __future__ import annotations

from dataclasses import dataclass

from wonderland.diagrams.links import DiagramLinks
from wonderland.diagrams.registry import DiagramRegistry

# At least this many shared components before two diagrams can be called
# the same surface — guards against a single shared chrome element
# (Navbar/Footer) merging two genuinely-distinct pages.
MIN_SHARED = 2
# |A ∩ B| / min(|A|, |B|): the smaller diagram is "mostly contained" in
# the larger. Calibrated on ldr-ophanic: dashboard⊂dashboard-page = 0.80,
# every distinct pair = 0.00.
CONTAINMENT_THRESHOLD = 0.6


@dataclass(frozen=True)
class DiagramDuplicate:
    """One consolidation: ``removed`` folded into ``survivor``."""

    survivor: str
    removed: str
    layer: str
    shared: tuple[str, ...]
    dropped: tuple[str, ...]  # nodes unique to removed (absent from survivor)
    containment: float

    def summary(self) -> str:
        base = (
            f"[{self.layer}] {self.removed!r} -> {self.survivor!r} "
            f"(containment={self.containment:.2f}, shared={len(self.shared)})"
        )
        if self.dropped:
            base += f"  DROPPED nodes not in survivor: {list(self.dropped)}"
        return base


def _key_set(names: list[str]) -> frozenset[str]:
    return frozenset(n.lower() for n in names)


def find_duplicate_diagrams(
    registry: DiagramRegistry,
) -> list[DiagramDuplicate]:
    """Detect same-surface diagram pairs. Each cluster of duplicates
    elects the richest diagram (most nodes; ties broken alphabetically)
    as survivor; every other member becomes a ``DiagramDuplicate``
    pointing at it. Pure read — no disk mutation."""
    diagrams = []
    for slug in registry.list_slugs():
        d = registry.read(slug)
        if d is None:
            continue
        names = [n.name for n in d.nodes]
        diagrams.append((slug, d.layer, names, _key_set(names)))

    # Pairwise duplicate relation (same layer + containment), then union
    # into clusters so a triple-drawn surface collapses to one survivor.
    parent: dict[str, str] = {s: s for s, _, _, _ in diagrams}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        parent[find(a)] = find(b)

    for i in range(len(diagrams)):
        for j in range(i + 1, len(diagrams)):
            slug_a, layer_a, _, keys_a = diagrams[i]
            slug_b, layer_b, _, keys_b = diagrams[j]
            if layer_a != layer_b:
                continue
            shared = keys_a & keys_b
            smaller = min(len(keys_a), len(keys_b))
            if not smaller:
                continue
            containment = len(shared) / smaller
            if len(shared) >= MIN_SHARED and containment >= CONTAINMENT_THRESHOLD:
                union(slug_a, slug_b)

    by_slug = {s: (layer, names, keys) for s, layer, names, keys in diagrams}
    clusters: dict[str, list[str]] = {}
    for slug, _, _, _ in diagrams:
        clusters.setdefault(find(slug), []).append(slug)

    out: list[DiagramDuplicate] = []
    for members in clusters.values():
        if len(members) < 2:
            continue
        # Survivor: most nodes, then alphabetical slug for determinism.
        survivor = max(members, key=lambda s: (len(by_slug[s][2]), _neg(s)))
        s_layer, _, s_keys = by_slug[survivor]
        for slug in sorted(members):
            if slug == survivor:
                continue
            _, names, keys = by_slug[slug]
            shared = sorted(keys & s_keys)
            dropped = sorted(keys - s_keys)
            smaller = min(len(keys), len(s_keys)) or 1
            out.append(
                DiagramDuplicate(
                    survivor=survivor,
                    removed=slug,
                    layer=s_layer,
                    shared=tuple(shared),
                    dropped=tuple(dropped),
                    containment=len(keys & s_keys) / smaller,
                )
            )
    return out


def _neg(s: str) -> tuple[int, ...]:
    """Sort key that makes ``max`` prefer the alphabetically-FIRST slug on
    a node-count tie (invert codepoints)."""
    return tuple(-ord(c) for c in s)


def consolidate_diagrams(
    project_root,
    *,
    registry: DiagramRegistry | None = None,
    links: DiagramLinks | None = None,
) -> list[DiagramDuplicate]:
    """Detect + apply diagram dedup: migrate the removed diagram's links
    onto the survivor's same-named nodes, then delete the removed
    diagram. Returns the applied ``DiagramDuplicate`` list. Best-effort
    on links — a removed node with no name-match in the survivor (a
    dropped node) has its links carried nowhere and is reported in
    ``DiagramDuplicate.dropped``."""
    registry = registry or DiagramRegistry(project_root)
    links = links or DiagramLinks(project_root)

    dups = find_duplicate_diagrams(registry)
    for dup in dups:
        survivor = registry.read(dup.survivor)
        removed = registry.read(dup.removed)
        if survivor is None or removed is None:
            continue
        survivor_by_key = {n.name.lower(): n.guid for n in survivor.nodes}
        for node in removed.nodes:
            existing = links.links_for_node(node.guid)
            if not existing:
                continue
            target_guid = survivor_by_key.get(node.name.lower())
            for kind, target_slug in existing:
                links.unlink(node.guid, target_slug, kind)
                if target_guid is not None:
                    links.link(target_guid, target_slug, kind)
        registry.remove(dup.removed)
    return dups


__all__ = [
    "DiagramDuplicate",
    "find_duplicate_diagrams",
    "consolidate_diagrams",
    "MIN_SHARED",
    "CONTAINMENT_THRESHOLD",
]
