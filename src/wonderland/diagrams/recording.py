"""Shared diagram-emission recorder (P21).

Any agent that can author diagrams (White Rabbit, Alice) routes its
``diagram`` decision through here: write each ``.oph`` via DiagramRegistry
and return Artifact pointers. Drops silently when no registry is wired;
skips a malformed ``.oph`` rather than killing the meeting.
"""

from __future__ import annotations

from wonderland.diagrams.payload import DiagramPayload
from wonderland.diagrams.registry import DiagramRegistry
from wonderland.utterance import Artifact


def record_diagrams(
    registry: DiagramRegistry | None,
    payloads: list[DiagramPayload],
) -> list[Artifact]:
    if registry is None:
        return []
    artifacts: list[Artifact] = []
    for payload in payloads:
        try:
            diagram = registry.write(
                payload.name, payload.oph, layer=payload.layer,
            )
        except Exception:  # noqa: BLE001 — a bad .oph mustn't kill the meeting
            continue
        artifacts.append(
            Artifact(
                kind="diagram",
                payload={
                    "slug": diagram.slug,
                    "guid": diagram.guid,
                    "layer": diagram.layer,
                    "title": diagram.title,
                    "path": str(diagram.path),
                    "nodes": [
                        {"guid": n.guid, "name": n.name}
                        for n in diagram.nodes
                    ],
                },
            )
        )
    return artifacts


__all__ = ["record_diagrams"]
